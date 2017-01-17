# mping

并发 ping 多个主机，找出其中连接最快的。

## 安装方法

    pip3 install -U mping

## 使用方法

看看哪个主机最快:

```shell
mping host1.com host2.com host3.com
```

Ping 文件中的主机列表:

```shell
mping -p PATH/TO/THE/FILE.txt
```

> 阅读下方的 **输入文件** 了解过多细节。

结果大概会像这样:

```
host      | count, loss%, min/avg/max
----------|--------------------------
host1.com | 99, 0.0%, 5.4/6.8/14.1
host2.com | 90, 0.0%, 23.8/33.5/39.5
host3.com | 77, 0.4%, 37.4/39.1/43.6
```

> `count` 数表示每个主机返回了多少个 ping 回复。

查看说明，了解更多:

```shell
mping -h
```

## 输入文件

可以使用纯文本文件，或 Json 文件，来用于 `-p` / `--path` 参数.


**纯文本文件**

当使用纯文本文件时，只要把每个主机放在单独一行即可。

例如:

```
host1.com
host2.com
host3.com
```

**Json 文件**

你也可以使用一个 Json 文件来作为输入的主机列表，这里有两种模式:
 
 把主机放进一个列表:
 
 ```json
[
    "host1.com",
    "host2.com",
    "host3.com"
]
```
 
把主机放进一个对象(字典)，并为主机命名:
 
 ```json
{
    "S1": "host1.com",
    "S2": "host3.com",
    "S3": "host3.com"
}
```

> 主机名称将会在结果中被打印出来。
