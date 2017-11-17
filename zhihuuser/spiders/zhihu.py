# -*- coding: utf-8 -*-
import json

import scrapy
from scrapy import Spider,Request

from zhihuuser.items import UserItem


class ZhihuSpider(Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    #第一个用户的别名
    start_user='excited-vczh'
    #构造每一个之乎用户json信息的url
    user_url='https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query='allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'
    #构造关注者的json列表url
    follow_url='https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    follows_query='data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'
    #粉丝列表
    followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    def start_requests(self):
        #请求知乎用户信息
        yield Request(self.user_url.format(user=self.start_user,include=self.user_query),self.parse_user)
        #请求关注者列表
        yield scrapy.Request(self.follow_url.format(user=self.start_user,include=self.follows_query,offset=2,limit=20),callback=self.parse_follows)
        #请求粉丝列表
        yield scrapy.Request(self.followers_url.format(user=self.start_user, include=self.followers_query, offset=2, limit=20),callback=self.parse_followers)

    #解析用户请求
    def parse_user(self, response):
        #转化成json格式
        result=json.loads(response.text)
        item=UserItem()
        #为items字段中每一个属性获取值
        for field in item.fields:
            if field in result.keys():
                item[field]=result.get(field)
        yield item
        #请求当前用户的关注列表和粉丝列表
        yield Request(self.follow_url.format(user=result.get('url_token'),include=self.follows_query,offset=0,limit=20),self.parse_follows)
        yield Request(self.followers_url.format(user=result.get('url_token'), include=self.followers_query, offset=0, limit=20),self.parse_followers)
    #解析关注者请求
    def parse_follows(self, response):
        results=json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                #请求关注着列表中每个用户的详细信息
                yield Request(self.user_url.format(user=result.get('url_token'),include=self.user_query),callback=self.parse_user)
        #判断是否是最后一页，不是最后一页的话，翻页继续爬取
        if 'paging' in results.keys() and results.get('paging').get('is_end')==False:
            next_page=results.get('paging').get('next')
            yield Request(next_page,self.parse_follows)

    #解析对粉丝列表的请求
    def parse_followers(self, response):
        results=json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                # 请求粉丝列表中每个用户的详细信息
                yield Request(self.user_url.format(user=result.get('url_token'),include=self.user_query),callback=self.parse_user)
        #尾页判断
        if 'paging' in results.keys() and results.get('paging').get('is_end')==False:
            next_page=results.get('paging').get('next')
            yield Request(next_page,self.parse_followers)
