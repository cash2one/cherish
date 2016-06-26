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

    db:set_timeout(1000)  -- 1 sec

    local ip = resolver.find_ip_by_host("db")
    if not ip then
        ngx.log(ngx.ERR, "failed to found ip addr")
    end

    local ok, err, errno, sqlstate = db:connect{
        host = ip,
        port = 3306,
        database = 'account_center',
        user = 'mysql',
        password = 'account_center123',
        max_packet_size = 1024 * 1024}

    if not ok then
        ngx.log(ngx.ERR, "failed to connect: " .. err .. ": " .. errno .. " " .. sqlstate)
    end

    ngx.ctx['db_conn'] = db
    return ngx.ctx['db_conn']
end

function _M.close()
    if ngx.ctx['db_conn'] then
        ngx.ctx['db_conn']:set_keepalive(0, 100)
        -- ngx.ctx['db_conn'] = nil
    end
end

return _M
