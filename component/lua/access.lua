local cjson = require "cjson"
local memc = require "common.memc"
local db = require "common.mysql_db"

function separate_token(v, from)
    local token_type = nil
    local access_token = nil

    if v == nil or v:find(" ") == nil then
        ngx.log(ngx.WARN, "no Authorization " .. from .. " found")
    else
        token_type, access_token = v:match("([^,]+) ([^,]+)")
    end

    return token_type, access_token
end

function find_token_type_and_access_token()
    local key = "X-TECHU-AUTH"
    local v = nil
    local token_type = nil
    local access_token = nil
    local headers = ngx.req.get_headers()

    v = headers[key]
    token_type, access_token = separate_token(v, 'header')

    if token_type == nil or access_token == nil then
        v = ngx.var["cookie_" .. key]
        token_type, access_token = separate_token(v, 'cookie')
    end

    return token_type, access_token
end

function main()
    local token_type = nil
    local access_token = nil
    local err = nil

    ngx.req.clear_header("X-TECHU-USER")

    token_type, access_token = find_token_type_and_access_token()

    -- if not found access_token return 403
    if token_type == nil or access_token == nil then
        ngx.exit(403)
    end

    local memc_conn = nil
    local db_conn = nil
    local res = nil
    local errno = nil
    local sqlstate = nil
    local v = nil
    local flag = nil

    memc_conn = memc:get_connection()
    v, flags, err = memc_conn:get(access_token)
    if err then
        ngx.log(ngx.ERR, "failed to get " .. access_token .. ": " .. err)
    end

    if not v then
        db_conn = db:get_connection()
        res, err, errno, sqlstate =
            db_conn:query(string.format([[select * from oauth2_provider_accesstoken where token = %s]],
                                        ngx.quote_sql_str(access_token)))
        db_conn:close()
        if not res or 0 == table.getn(res) or table.getn(res) > 1 then
            err = "bad result: ", err, ": ", errno, ": ", sqlstate, "."
            ngx.log(ngx.ERR, err)
            ngx.exit(403)
        else
            local expires = res[1].expires
            local pattern = "(%d+)-(%d+)-(%d+) (%d+):(%d+):(%d+)(.*)"
            local y, m, d, h, min, s, ms = expires:match(pattern)
            local expires_timestamp = os.time({year = y, month = m, day = d, hour = h, min = min, sec = s})
            if expires_timestamp < os.time() then
                err = "token has expired"
                ngx.log(ngx.ERR, err)
                ngx.exit(403)
            end
            local exp_time = expires_timestamp - os.time()
            ngx.log(ngx.DEBUG, "Exp_time: " .. exp_time)
            local ok, err = memc_conn:set(access_token, cjson.encode(res), exp_time)
            if not ok then
                ngx.log(ngx.ERR, "failed to set " .. access_token .. ": " .. err)
            end
        end
    else
        ngx.log(ngx.INFO, "Hit memc access_token: " .. access_token)
        res = cjson.decode(v)
    end

    memc_conn:close()

    if res then
        ngx.req.set_header("X-TECHU-USER", res[1].user_id)
    else
        ngx.log(ngx.ERR, "failed to auth token: " .. access_token)
        ngx.exit(403)
    end
end

main()
