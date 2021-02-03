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
    html='<!DOCTYPE html><html><head><meta charset="utf-8"><title>处理中</title></head><body><h1><strong>服务器正在处理你的请求，请不要关闭页面，音乐将在倒计数结束前抵达。。</strong></h1><p id="demo"></p><h1 id="show" name="n1" ></h1><img src="https://qn.xieqifei.com/tipps.png" alt="tipps" width="300"/><script>var xhr=new XMLHttpRequest();xhr.onload=function(){window.location.replace(xhr.responseText);};xhr.onerror=function(){document.getElementById("demo").innerHTML="请求出错"};xhr.open("GET","https://asia-east2-youtube-search-303517.cloudfunctions.net/music/'+musicname+'",true);xhr.send();function countdown() {var n = 60;var interval;if (n > 0) {interval = setInterval(() => {n--;document.getElementById("show").innerHTML = n;if (n<= 0) {clearInterval(interval)}}, 1000)} } countdown();</script></body></html>'
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {'Content-Type': 'text/html','Access-Control-Allow-Origin':'*'},
        "body": html
    }

