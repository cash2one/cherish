local cjson = require "cjson"
local memc = require "common.memc"
local db = require "common.db"

local cookie_name = "X-TECHU-AUTH"
local var_name = "cookie_" .. cookie_name
local field = ngx.var[var_name]
if not field then
    ngx.log(ngx.ERR, err)
    ngx.exit(403)
end

local token_type, access_token = field:match("([^,]+) ([^,]+)")

if access_token == nil then
    err = "no access token value found"
    ngx.log(ngx.ERR, err)
    ngx.exit(403)
end

local res = nil
local memc_conn = memc:get_connection()

local ok, err = memc_conn:flush_all()
local v, flags, err = memc_conn:get(access_token)
if err then
    ngx.log(ngx.ERR, "failed to get " .. access_token .. ": " .. err)
end

if not v then
    local db_conn = db:get_connection()
    res, err, errno, sqlstate =
        db_conn:query(string.format([[select * from cats where name = %s]],
                                    ngx.quote_sql_str(access_token)))
    db_conn:close()
    if not res or 0 == table.getn(res) then
        err = "bad result: ", err, ": ", errno, ": ", sqlstate, "."
        ngx.log(ngx.ERR, err)
        ngx.exit(403)
    else
        --local ok, err = memc_conn:set(access_token, cjson.encode(res), res[1].expires)
        local ok, err = memc_conn:set(access_token, cjson.encode(res))
        if err then
            ngx.log(ngx.ERR, "failed to set " .. access_token .. ": " .. err)
        end
    end
else
    res = cjson.decode(v)
end

memc_conn:close()

if res then
    --ngx.req.set_header("X-TECHU-USER", res[1].user_id)
    ngx.req.set_header("X-TECHU-USER", res[1].id)
else
    ngx.log(ngx.ERR, "failed to auth token: " .. access_token)
    ngx.exit(403)
end
