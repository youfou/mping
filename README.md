[中文说明](https://github.com/youfou/mping/blob/master/README_ZHCN.md)

# mping

Ping multiple hosts concurrently and find the fastest to you.

## Installation

    pip3 install -U mping

## Usages

Just tell which host is the fastest:

```shell
mping host1.com host2.com host3.com
```

Get hosts from a file, and ping them:

```shell
mping -p PATH/TO/THE/FILE.txt
```

> Read **Input File** section below for more details.

The results will be like this:

```
host      | count, loss%, min/avg/max
----------|--------------------------
host1.com | 99, 0.0%, 5.4/6.8/14.1
host2.com | 90, 0.0%, 23.8/33.5/39.5
host3.com | 77, 0.4%, 37.4/39.1/43.6
```

> The `count` number represents how many replies returned from each host.

Also check out the help stuff for more instructions:

```shell
mping -h
```

## Input File

You can use either a plain text file or a Json file as the `-p` / `--path` argument.


**Plain Text File**

When use a plain text file, just place each host in a line.

For example:

```
host1.com
host2.com
host3.com
```

**Json File**

You can also use a json file as the input hosts, and below is the 2 modes:
 
 Put hosts in a list:
 
 ```json
[
    "host1.com",
    "host2.com",
    "host3.com"
]
```
 
Or in an object (dict) with names:
 
 ```json
{
    "S1": "host1.com",
    "S2": "host3.com",
    "S3": "host3.com"
}
```

> The names will be printed in the results.
