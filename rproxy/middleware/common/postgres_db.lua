local _M = {}

local pg = require "common.postgres"
local service_resolver = require "dns.resolver"

function _M.get_connection()
    if ngx.ctx['db_conn'] then
        return ngx.ctx['db_conn']
    end

    local db, err = pg:new()
    if not db then
        ngx.log(ngx.ERR, "failed to instantiate postgres: ", err)
    end

    db:set_timeout(os.getenv("DB_CONN_TIMEOUT"))

    local service= service_resolver.resolve_service(os.getenv("DB_SERVICE"))
    ip, port = service:match("(.+):(%d+)")
    if not (ip and port) then
        ngx.log(ngx.ERR, "failed to found ip addr")
    end

    local ok, err = db:connect({
        host = ip,
        port = port,
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
