AOP 面向切面编程，简单点说就是把一些通用的功能从业务代码里抽取出来，统一处理。比如说[技术派](https://javabetter.cn/zhishixingqiu/paicoding.html)中的 `@MdcDot` 注解的作用是配合 AOP 在日志中加入 MDC 信息，方便进行日志追踪。

IoC 控制反转是一种设计思想，它的主要作用是将**对象的创建和对象之间的调用过程交给 Spring 容器**来管理。比如说在[技术派](https://javabetter.cn/zhishixingqiu/paicoding.html)项目当中，`@PostConstruct` 注解表明这个方法由 Spring 容器在 Bean 初始化完成后自动调用，我们不需要手动调用 init 方法。

#### 设计模式：工厂模式(BeanFactory),单例模式，代理模式(Aop)，模版模式(template)

#### Spring如何实现单例模式？

Spring 在启动的时候会把所有的 Bean 定义信息加载进来，然后在 DefaultSingletonBeanRegistry 这个类里面维护了一个叫 **singletonObjects 的 ConcurrentHashMap**，这个 Map 就是用来存储单例 Bean 的。key 是 Bean 的名称，value 就是 Bean 的实例对象。

Bean 本质上就是由 Spring 容器管理的 Java 对象，但它和普通的 Java 对象有很大区别。普通的 Java 对象我们是通过 new 关键字创建的。而 Bean 是交给 Spring 容器来管理的，从创建到销毁都由容器负责。

生命周期：实例化->属性赋值->初始化(@PostConstruct,@Bean)->工作->销毁

### Spring怎么解决循环依赖呢？

Spring 通过三级缓存机制来解决循环依赖：

1. 一级缓存：存放完全初始化好的单例 Bean。
2. 二级缓存：存放提前暴露的 Bean，实例化完成，但未初始化完成。
3. 三级缓存：存放 Bean 工厂，用于生成提前暴露的 Bean。

### IOC

IoC 的思想是把**对象创建和依赖关系的控制权由业务代码转移给 Spring 容器**。这是一个比较抽象的概念，告诉我们应该怎么去设计系统架构。

它降低了对象之间的耦合度，让每个对象只关注自己的业务实现，不关心其他对象是怎么创建的。

### 项目启动时Spring的IoC会做什么？

第一件事是扫描和注册 Bean。IoC 容器会根据我们的配置，比如 `@ComponentScan` 指定的包路径，去扫描所有标注了 `@Component`、`@Service`、`@Controller` 这些注解的类。然后把这些类的元信息包装成 BeanDefinition 对象，注册到容器的 BeanDefinitionRegistry 中。

第二件事是 Bean 的实例化和注入。这是最核心的过程，IoC 容器会按照依赖关系的顺序开始创建 Bean 实例。对于单例 Bean，容器会通过反射调用构造方法创建实例，然后进行属性注入，最后执行初始化回调方法。

### 说说什么是 AOP？

AOP，也就是面向切面编程，简单点说，**AOP 就是把一些业务逻辑中的相同代码抽取到一个独立的模块中**，让业务逻辑更加清爽。

从技术实现上来说，AOP 主要是通过动态代理来实现的。如果目标类实现了接口，就用 JDK 动态代理；如果没有实现接口，就用 CGLIB 来创建子类代理。代理对象会在方法执行前后插入我们定义的切面逻辑。

## Mapper 配合 Wrapper 可以**动态拼接查询条件**，无需手写 XML 与原生 SQL，

支持单条、列表、分页、统计、条件修改、条件删除，

Lambda 写法避免字段硬编码错误，维护更安全。
