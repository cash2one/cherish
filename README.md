# auth_center

中心用户系统

## 功能

1. 用户操作（注册、登录、账号找回）
2. OAuth第三方应用授权管理
3. 用户账号资源API（用于授权第三方应用访问用户信息）

### 用户操作页面接口

#### /accounts/register/

新用户注册

#### /accounts/login/

用户登陆

#### /accounts/password_reset/

用户密码重置（需要用户提供注册邮箱）


### 应用管理页面接口

#### /oauth/applications/

列出当前用户注册的应用

#### /oauth/applications/register/

为当前用户注册新应用

#### /oauth/authorized_tokens/

查看当前用户已经授权的有效token


### 应用授权API

---
#### ^/oauth/applications/(?P<pk>\d+)/$

HTTP Method: GET
查看应用授权详情

> pk为应用ID

---
#### ^/oauth/applications/(?P<pk>\d+)/delete/$

HTTP Method: DELETE
删除应用授权

> pk为应用ID

---
#### ^/oauth/applications/(?P<pk>\d+)/update/$

HTTP Method: PUT
更新应用授权信息

> pk为应用ID

---
#### ^oauth/authorized_tokens/(?P<pk>\d+)/delete/$

HTTP Method: DELETE
删除指定授权token

> pk为应用ID

### 资源API

#### ^accounts/resource/user/(?P<pk>[0-9]+)/$
#### ^accounts/resource/user/(?P<pk>[0-9]+)\.(?P<format>[a-z0-9]+)/?$

HTTP Method: GET
获取平台用户详情接口

> pk为应用ID
> format为格式设置，可取值: json, html 

> 注意：该接口只能获取到授权用户信息

#### ^accounts/resource/group/(?P<pk>[0-9]+)/$
#### ^accounts/resource/group/(?P<pk>[0-9]+)\.(?P<format>[a-z0-9]+)/?$

HTTP Method: GET
获取平台用户组详情接口

> pk为应用ID
> format为格式设置，可取值: json, html 

## OAuth角色

* Resource Owner
* Client
* Resource Server
* Authorization Server

### Resource Owner: User
The resource owner is the user who authorizes an application to access their account. The application's access to the user's account is limited to the "scope" of the authorization granted (e.g. read or write access).

### Resource / Authorization Server: API
The resource server hosts the protected user accounts, and the authorization server verifies the identity of the user then issues access tokens to the application.
From an application developer's point of view, a service's API fulfills both the resource and authorization server roles. We will refer to both of these roles combined, as the Service or API role.

### Client: Application
The client is the application that wants to access the user's account. Before it may do so, it must be authorized by the user, and the authorization must be validated by the API.

## Abstract Protocol Flow

![abstract protocol flow](https://assets.digitalocean.com/articles/oauth/abstract_flow.png)

Here is a more detailed explanation of the steps in the diagram:

	1. The application requests authorization to access service resources from the user
	2. If the user authorized the request, the application receives an authorization grant
	3. The application requests an access token from the authorization server (API) by presenting authentication of its own identity, and the authorization grant
	4. If the application identity is authenticated and the authorization grant is valid, the authorization server (API) issues an access token to the application. Authorization is complete.
	5. The application requests the resource from the resource server (API) and presents the access token for authentication
	6. If the access token is valid, the resource server (API) serves the resource to the application


## OAuth2的几种授权方式(grant type)

* Authorization code: 用于服务器端应用
* Implicit: 用于移动端或Web端应用（应用运行在用户设备）
* Resource owner password-based: 用于信任应用（如授权中心自身的服务）
* Client credentials: 用于应用自身API访问

### Authorization Code
---
The `authorization code` grant type is the most commonly used because it is optimized for server-side applications, where source code is not publicly exposed, and Client Secret confidentiality can be maintained. This is a redirection-based flow, which means that the application must be capable of interacting with the user-agent (i.e. the user's web browser) and receiving API authorization codes that are routed through the user-agent.

1. Authorization Code Link
2. User Authorizes Application
3. Application Receives Authorization Code
4. Application Requests Access Token

### Implicit
---
The `implicit` grant type is used for mobile apps and web applications (i.e. applications that run in a web browser), where the client secret confidentiality is not guaranteed. The implicit grant type is also a redirection-based flow but the access token is given to the user-agent to forward to the application, so it may be exposed to the user and other applications on the user's device. Also, this flow does not authenticate the identity of the application, and relies on the redirect URI (that was registered with the service) to serve this purpose.

> NOTICE : The implicit grant type does not support refresh tokens.

1. Implicit Authorization Link
2. User Authorizes Application
3. User-agent Receives Access Token with Redirect URI
4. User-agent Follows the Redirect URI
5. Application Sends Access Token Extraction Script
6. Access Token Passed to Application


### Resource Owner Password Credentials
---
With the `resource owner password credentials` grant type, the user provides their service credentials (username and password) directly to the application, which uses the credentials to obtain an access token from the service. This grant type should only be enabled on the authorization server if other flows are not viable. Also, it should only be used if the application is trusted by the user (e.g. it is owned by the service, or the user's desktop OS).

After the user gives their credentials to the application, the application will then request an access token from the authorization server.


### Client Credentials
---
The `client credentials` grant type provides an application a way to access its own service account. Examples of when this might be useful include if an application wants to update its registered description or redirect URI, or access other data stored in its service account via the API.

The application requests an access token by sending its credentials, its client ID and client secret, to the authorization server.

## 参考

* [an introduction to oauth2](https://www.digitalocean.com/community/tutorials/an-introduction-to-oauth-2)
