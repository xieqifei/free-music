# 1：使用手册

一个基于 python，搭建在 Serverless 云函数上的免费音乐下载程序。可剥离云函数本地运行。
通过构造形如`[https://m.sci.ci/](https://m.sci.ci/)音乐相关信息`这样的网址，就可在浏览器上下载喜欢的音乐了。

## demo

简单的例子，想听爱的供养？

尝试在浏览器地址栏输入`m.sci.ci/爱的供养`

现在试试 👉[m.sci.ci/爱的供养](https://m.sci.ci/%E7%88%B1%E7%9A%84%E4%BE%9B%E5%85%BB)

返回的音乐文件是杨幂版本的，不喜欢？

尝试重新构造链接`m.sci.ci/张靓颖张杰爱的供养`

现在返回的就是张杰和张靓颖合唱版啦！

歌曲下载链接仅能保存一天！音乐文件以你的搜索内容为名。比如`张靓颖张杰爱的供养.mp3`而不是原来的名称，文件中歌曲的专辑、歌词等相关信息也是没有的。

# 2：搭建自己的服务

Serverless 又称无服务、云函数，可通过一个 api 触发你写好的程序，并返回数据给请求者。
项目地址：[https://github.com/xieqifei/free-music](https://github.com/xieqifei/free-music)

## 2.1 依赖

1.  `youtube-dl`  提供通过 youtube 视频 url，下载视频或 mp3 音乐文件
1.  `qiniu`  提供音乐储存服务
1.  `requests`  发送网络请求
1.  `json`  解析 json 数据

需要在谷歌云函数 `requrements.txt`  中填写

```
qiniu==7.3.1
requests==2.22.0
youtube-dl==2021.1.16
```

## 2.2 音频提取和储存

以下程序运行在谷歌 Serverless 服务上。需要在代码中添加自己的七牛云储存桶，如果有必要，可以使用谷歌提供的免费 youtube api 获取搜索结果，程序会优先使用爬虫获取搜索结果，当程序频繁运行时，爬虫会失效，为了提高容错，建议添加谷歌 api，此 api 每天可以发起 100 次请求来获取 youtube 搜索结果。以下程序保存在`lambda_function.py` 中

```python
# -*- encoding: utf-8 -*-
'''
@file_name    :lambda_function.py
@description  :
@time         :2021/02/02 22:20:14
@author       :Qifei
@version      :1.0
'''

import requests
import youtube_dl
from qiniu import Auth
import json
import re
from qiniu.services.storage.bucket import BucketManager
import os

#七牛云对象储存AK和SK，以及储存桶名
access_key = ''
secret_key = ''
bucket_name = ''

#谷歌api，用于获取youtube搜索结果
google_appKey=""

q = Auth(access_key, secret_key)

def handler(request):
    musicname =  request.url.split("/")[-1]
    video_url = get_video_url_in_youtube_from_crawler(musicname)

    #遵循同源cors协议，可跨域访问
    headers = {
        'Access-Control-Allow-Origin': '*'
    }
    if video_url == 500:
        #爬虫失效，切换api
        video_url = get_video_url_in_youtube_form_api(google_appKey,musicname)
        if video_url == 500:
            return ("error",400,headers)
    filename = dl_mp3(musicname,video_url)
    localpath = "/tmp"
    dl_url = uploadfile(localpath,filename)
    return (dl_url, 200, headers)

#将文件上传到七牛
def uploadfile(localpath,filename):
    #上传后保存的文件名
    key = filename
    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)
    url = 'https://upload-z2.qiniup.com'
    files = {'file': open(localpath+"/"+filename, 'rb')}
    data = {'token':token,'fileName':filename,'key':key}
    response = requests.post(url, files=files, data=data)
    set_liftime(filename)
    url="https://qn.xieqifei.com/"+filename
    delete_tmp(filename)
    return url

#设置保存在七牛云上的音乐文件1天后自动删除
def set_liftime(musicname):
    #初始化BucketManager
    bucket = BucketManager(q)
    #你要测试的空间， 并且这个key在你空间中存在
    key = musicname
    #您要更新的生命周期
    days = '1'
    ret, info = bucket.delete_after_days(bucket_name, key, days)
    print(info)

##下载mp3格式文件
def dl_mp3(musicname,url):
    ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': '/tmp/{}.mp3'.format(musicname),
    'quiet': False
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        # info = ydl.extract_info(url, download=False)
        filename = "{}.mp3".format(musicname)
    return filename

#调用谷歌api获取youtube搜索结果，返回匹配度最高的视频链接
def get_video_url_in_youtube_form_api(appKey,music_name):
    print("从google api获取数据")
    url = "https://youtube.googleapis.com/youtube/v3/search?q="+music_name+"&key="+appKey
    resp = requests.get(url)
    resp_json = resp.json()
    if resp.status_code ==200:
        return "https://www.youtube.com/watch?v="+resp_json['items'][0]['id']['videoId']
    else:
        return 500

#利用爬虫获取youtube搜索结果
def get_video_url_in_youtube_from_crawler(keyword):
    url="https://m.youtube.com/results?search_query="+keyword
    print("通过爬虫获取数据")
    resp = requests.get(url)
    if resp.status_code==200:
        result_json = re.findall(r'ytInitialData = (.*);</script>', resp.text)[0]
        result_obj = json.loads(result_json)
        try:
            video_url = "https://www.youtube.com/watch?v="+result_obj['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['videoRenderer']['videoId']
        except KeyError:
            return 500
        return video_url
    else:
        return 500

def delete_tmp(filename):
    os.system("rm -f  /tmp/"+filename)
    print("从tmp删除"+filename)
```

上述代码，会提取谷歌请求路径中的最后一个地址作为搜索内容，比如 `https://service-azkac26i-1258461674.hk.apigw.tencentcs.com/release/APIGWH-1612290368/爱的供养`  那么爱的供养将作为搜索关键词，下载爱的供养最匹配的视频的音频 ，再保存到七牛云对象储存桶中。

> 此代码仅能用于谷歌 serverless，由于权限问题，在其他 serverless，比如腾讯、亚马逊上，在将下载的视频提取音频时，ffmpeg 没有对视频的写权限，只有谷歌无服务框架支持。所以只能在谷歌上运行。

由于谷歌 Serverless 不支持自定义 api 网址，而谷歌的域名在国内又无法访问，因此，我们需要利用腾讯的香港 serverless 再构建一个云函数。腾讯云函数支持自定义 api。
我相信通过一定的代码修改，ffmpeg 是有办法处理下载的视频文件的，但是由于时间关系，我不愿意再去做尝试；额，这里就直接用了谷歌 Serverless 做视频处理，再通过腾讯 serverless 自定义 api 并返回给用户一个网页，网页里提示用户等待音频处理，并发送一个异步请求给谷歌云函数，当音频处理完毕，谷歌云函数返回给网页，音频文件在七牛云储存桶的保存地址。

## 2.3 网页构建

```python
# -*- encoding: utf-8 -*-
'''
@file_name    :scf.py
@description  :用于腾讯云函数，自定义域名，返回一个静态页面，页面异步请求谷歌云函数，谷歌下载并处理音乐。然后返回链接给静态页面
@time         :2021/02/03 00:49:36
@author       :Qifei
@version      :1.0
'''


def handler(event,context):
    musicname =  event['path'].split("/")[-1]
    html='<!DOCTYPE html><html><head><meta charset="utf-8"><title>处理中</title></head><body><h1><strong>服务器正在处理你的请求，请不要关闭页面，音乐将在倒计数结束前抵达。。</strong></h1><p id="demo"></p><h1 id="show" name="n1" ></h1><img src="https://qn.xieqifei.com/tipps.png" alt="tipps" width="300"/><script>var xhr=new XMLHttpRequest();xhr.onload=function(){window.location.replace(xhr.responseText);};xhr.onerror=function(){document.getElementById("demo").innerHTML="请求出错"};xhr.open("GET","https://service-azkac26i-1258461674.hk.apigw.tencentcs.com/release/APIGWHtmlDemo-1612290368/'+musicname+'",true);xhr.send();function countdown() {var n = 20;var interval;if (n > 0) {interval = setInterval(() => {n--;document.getElementById("show").innerHTML = n;if (n<= 0) {clearInterval(interval)}}, 1000)} } countdown();</script></body></html>'
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {'Content-Type': 'text/html','Access-Control-Allow-Origin':'*'},
        "body": html
    }


```

来看看网页部分，也就是上述代码中的 html 变量，格式化后

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>处理中</title>
  </head>
  <body>
    <h1>
      <strong
        >服务器正在处理你的请求，请不要关闭页面，音乐将在倒计数结束前抵达。。</strong
      >
    </h1>
    <p id="demo"></p>
    <h1 id="show" name="n1"></h1>
    <img src="https://qn.xieqifei.com/tipps.png" alt="tipps" width="300" />
    <script>
      var xhr = new XMLHttpRequest();
      xhr.onload = function() {
          window.location.replace(xhr.responseText);
      };
      xhr.onerror = function() {
          document.getElementById("demo").innerHTML = "请求出错"
      };
      xhr.open("GET", "https://service-azkac26i-1258461674.hk.apigw.tencentcs.com/release/APIGWH12290368/'+musicname+'", true);
      xhr.send();
      function countdown() {
          var n = 20;
          var interval;
          if (n > 0) {
              interval = setInterval(() = >{
                  n--;
                  document.getElementById("show").innerHTML = n;
                  if (n <= 0) {
                      clearInterval(interval)
                  }
              },
              1000)
          }
      }
      countdown();
    </script>
  </body>
</html>
```

网页会有一个文字提醒，并有一个 20 秒倒计时的标签，通常视频的下载和处理都会在十几秒内完成，当谷歌上的云函数处理完音频后，会直接返回给网页音频地址，而网页通过 js 直接跳转到音乐的储存链接，可以直接播放，也可以下载。
