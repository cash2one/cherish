local _M = {}

local pg = require "common.postgres"
local resolver = require "common.resolver"

function _M.get_connection()
    if ngx.ctx['db_conn'] then
        return ngx.ctx['db_conn']
    end

    local db, err = pg:new()
    if not db then
        ngx.log(ngx.ERR, "failed to instantiate postgres: ", err)
    end

    db:set_timeout(os.getenv("DB_CONN_TIMEOUT"))

    local ip = resolver.find_ip_by_host(os.getenv("POSTGRES_HOST"))
    if not ip then
        ngx.log(ngx.ERR, "failed to found ip addr")
    end

    local ok, err = db:connect({
        host = ip,
        port = os.getenv("POSTGRES_PORT"),
        database = os.getenv("POSTGRES_DATABASE"),
        user = os.getenv("POSTGRES_USER"),
        password = os.getenv("POSTGRES_PASSWORD"),
        compact=false})

    if not ok then
        ngx.log(ngx.ERR, "failed to connect: " .. err)
    end

    ngx.ctx['db_conn'] = db
    return ngx.ctx['db_conn']
end

function _M.close()
    if ngx.ctx['db_conn'] then
        ngx.ctx['db_conn']:set_keepalive()
    end
end

return _M
