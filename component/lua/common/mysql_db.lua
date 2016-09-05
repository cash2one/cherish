local _M = {}

local mysql = require "resty.mysql"
local resolver = require "common.resolver"

function _M.get_connection()
    if ngx.ctx['db_conn'] then
        return ngx.ctx['db_conn']
    end

    local db, err = mysql:new()
    if not db then
        ngx.log(ngx.ERR, "failed to instantiate mysql: ", err)
    end

    db:set_timeout(os.getenv("DB_CONN_TIMEOUT"))

    local ip = resolver.find_ip_by_host(os.getenv("MYSQL_HOST"))
    if not ip then
        ngx.log(ngx.ERR, "failed to found ip addr")
    end

    local ok, err, errno, sqlstate = db:connect{
        host = ip,
        port = os.getenv("MYSQL_PORT"),
        database = os.getenv("MYSQL_DATABASE"),
        user = os.getenv("MYSQL_USER"),
        password = os.getenv("MYSQL_PASSWORD"),
        max_packet_size = 1024 * 1024}

    if not ok then
        ngx.log(ngx.ERR, "failed to connect: " .. err .. ": " .. errno .. " " .. sqlstate)
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
