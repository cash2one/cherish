local cjson = require "cjson"
local memc = require "common.memc"
local db = require "common.db"

local token_type = nil
local access_token = nil
local err = nil
local key = "X-TECHU-AUTH"

ngx.req.clear_header("X-TECHU-USER")

-- find token in headers
local headers = ngx.req.get_headers()
local v = headers[key]
if v == nil or v:find(" ") == nil then
    err = "no Authorization header found"
    ngx.log(ngx.INFO, err)
else
    local divider = v:find(" ")
    access_token = v:sub(divider+1)
end

-- find token in cookies
local var_name = "cookie_" .. key
local field = ngx.var[var_name]
if not field then
    err = "no Authorization cookie found"
    ngx.log(ngx.ERR, err)
else
    token_type, access_token = field:match("([^,]+) ([^,]+)")
end

-- if not found access_token return 403
if access_token == nil then
    err = "no access token value found"
    ngx.log(ngx.ERR, err)
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
    if not res or 0 == table.getn(res) then
        err = "bad result: ", err, ": ", errno, ": ", sqlstate, "."
        ngx.log(ngx.ERR, err)
        ngx.exit(403)
    else
        local expires = res[1].expires
        local pattern = "(%d+)-(%d+)-(%d+) (%d+):(%d+):(%d+)(.*)"
        local y, m, d, h, min, s, ms = expires:match(pattern)
        local expires_timestamp = os.time({year = y, month = m, day = d, hour = h, min = min, sec = s})
        if expires_timestamp < os.time() then
            ngx.exit(403)
        end
        local exp_time = expires_timestamp - os.time()
        ngx.log(ngx.ERR, "Exp_time: " .. exp_time)
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
