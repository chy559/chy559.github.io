# JUC实战

## 创建线程的方式

Thread继承、实现Runnable接口、Callable+Future、Lambda四种创建方式

   Callable<String> callable = ()->{

            return "方式3 - Callable返回结果，线程名：" + Thread.currentThread().getName();

        };

        FutureTask<String> futureTask = new FutureTask<>(callable);

        //futuretask本质上也是一个runnable接口

        Thread thread3 = new Thread(futureTask);

        thread3.start();

## 线程安全的计数器

使用synchronized，AtomicInteger,ReentranLock 可以用工厂模式解耦

工厂模式：**Map:全局唯一，不带状态**   **有状态、需要多份独立计数、多组隔离统计** → 工厂**每次 new 新实例**

## 生产-消费者模型(sychronized+wait+notifyall)

1. synchronized(lock) { // 同一把锁
    while(条件不满足) wait(); // 等待
    执行业务逻辑; // 生产/消费
    notifyAll(); // 唤醒别人
   }

2. 方式2：使用BlockingQueue实现

## 互斥锁:交替进行某一个事情 用flag来实现(synchronized,wait,notifyall)

flag:

synchronized { // 同一把锁 while(不能执行) 

{ // 条件不满足就等待 wait(); 

// 等待，释放锁 } 打印业务;

 // 干活 切换flag; 

// 让对方可以干 notifyAll(); // 唤醒对方 }

## countDownLautch实现同步

await()：等到减为0   countDown():-1

  
