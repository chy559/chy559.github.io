# 模块一：用户管理

![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-14-15-56-51-image.png)

总体概述

![派聪明整体设计方案](https://cdn.tobebetterjavaer.com/paicoding/2c734062025198919a138d6227b102ce.jpeg)

![](https://cdn.tobebetterjavaer.com/paicoding/c23df394db15a018c2216c71bc028285.png)

___

## 用户管理模块（安全私有）

### 用户注册（register)

1.后端与前端交互的ResponseEntity:![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-14-19-44-03-image.png)

密码 加密：BCrypt

检查用户是否存在->不存在则开始业务，

用jpa的repositry访问数据库修改用户内容，

同时还要调用org的mapper层添加组织的信息，

把组织的信息写入redis缓存之中

____

### 用户登录(login)

1.现在service中调用mapper和passwordUtil比对密码，正确则返回username

2.通过user获取claims生成两个jwt token令牌，token保存进入redis<String,Map<s,o>>结构jwts.builder

将token发给前端，前端再发送带有authorization的请求头，这样就可以在securityConfig中设置jwt的过滤器

3.过滤器逻辑：取token，检查token是否有效(JwtUtil.validate):从claims中取出tokenid，先去reids中查看缓存(jwt:valid:tokenid),Redis验证通过，再验证JWT签名,有效则刷新token，无效则验证是否在宽限期中，是则刷新

<img title="" src="file:///C:/Users/陈%20华%20宇/AppData/Roaming/marktext/images/2026-03-15-14-35-32-image.png" alt="" width="292"><img title="" src="file:///C:/Users/陈%20华%20宇/AppData/Roaming/marktext/images/2026-03-15-15-16-37-image.png" alt="" width="356">

4.前端此时再发带有Authorization头的请求，此时通过filiter过滤即可

___

### 管理admin操作

1.查询所有用户：简单的JPA

2.分配组织：更新数据库中user的组织，保留私人组织，主组织没有优先为私人组织，同时更新缓存(org_tags和primary_tag)

3.设置主组织：JPA.确保主组织是user的所属组织

___

### 获取用户的组织：

1.先尝试从缓存里面取，没有再去数据库并且更新缓存

2.返回的数据结构：map:    orgTags:List orgId     primary_org:orgId  orgInfo: map<string,string>(存的一些基本的信息)

____

### 更新组织

1.更新父标签的细节：必须存在并且不能成环

2.清除所有的有效tag缓存

___

### 删除组织

1.删除组织细节：特殊标签，有子标签的，有用户在用的标签，有文档再用的不能删，不能删

2.清除tag的有效缓存

___

### 查询组织树

递归调用：

![](C:\Users\陈%20华%20宇\AppData\Roaming\marktext\images\2026-03-15-16-34-00-image.png)

___

JPA分页查询：new PageInpl<>(list<>,pageable,size):pageable中定义了表的页码和一页的大小

stream操作很重要
