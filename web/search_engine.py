# -*- coding: utf-8 -*-
'''
Created on Thursday 21st, December, 2017
@auther: REBOOT
'''

import jieba
import math
import operator
import sqlite3
import configparser
from datetime import *

class SearchEngine:
	stop_words = set()

	config_path = ''
	config_encoding = ''

	K1 = 0
	B = 0
	N = 0
	AVG_L = 0

	conn = None

	def __init__(self, config_path, config_encoding):
		self.config_path = config_path
		self.config_encoding = config_encoding
		config = configparser.ConfigParser()
		config.read(config_path, config_encoding)

		f = open(config['DEFAULT']['stop_words_path'], encoding = config['DEFAULT']['stop_words_encoding'])
		words = f.read()
		self.stop_words = set(words.split('\n'))
		self.conn = sqlite3.connect(config['DEFAULT']['db_path'])
		self.K1 = float(config['DEFAULT']['k1'])
		self.B = float(config['DEFAULT']['b'])
		self.N = int(config['DEFAULT']['n'])
		self.AVG_L = float(config['DEFAULT']['avg_l'])

	def __del__(self):
		self.conn.close()

	def is_number(self, s):
		try:
			float(s)
			return True
		except ValueError:
			return False

	def clean_list(self, seg_list):
		cleaned_dict = {}
		n = 0
		for i in seg_list:
			i = i.strip().lower()
			if i != '' and not self.is_number(i) and i not in self.stop_words:
				n = n + 1
				if i in cleaned_dict:
					cleaned_dict[i] = cleaned_dict[i] + 1
				else:
					cleaned_dict[i] = 1
		return n, cleaned_dict

	def fetch_from_db(self, term):
		c = self.conn.cursor()
		c.execute('SELECT * FROM postings WHERE term=?', (term,))
		return (c.fetchone())

	def result_by_BM25(self, sentence):
		# seg_list = jieba.lcut(sentence, cut_all = False)
		n, cleaned_dict = self.clean_list(sentence)
		BM25_scores = {}
		for term in cleaned_dict.keys():
			r = self.fetch_from_db(term)
			if r is None:
				continue
			df = r[1]
			w = math.log2((self.N - df + 0.5) / (df + 0.5))
			docs = r[2].split('\n')
			for doc in docs:
				docid, date_time, comment_num, comment_joinnum, tf, ld = doc.split('\t')
				docid = int(docid)
				comment_num = int(comment_num)
				comment_joinnum = int(comment_joinnum)
				tf = int(tf)
				ld = int(ld)
				s = (self.K1 * tf * w) / (tf + self.K1 * (1 - self.B + self.B * ld / self.AVG_L))
				if docid in BM25_scores:
					BM25_scores[docid] = BM25_scores[docid] + s
				else:
					BM25_scores[docid] = s
		BM25_scores = sorted(BM25_scores.items(), key = operator.itemgetter(1))
		BM25_scores.reverse()
		if len(BM25_scores) == 0:
			return 0, []
		else:
			return 1, BM25_scores

	def result_by_time(self, sentence):
		# seg_list = jieba.lcut(sentence, cut_all=False)
		n, cleaned_dict = self.clean_list(sentence)
		time_scores = {}
		for term in cleaned_dict.keys():
			r = self.fetch_from_db(term)
			if r is None:
				continue
			docs = r[2].split('\n')
			for doc in docs:
				docid, date_time, comment_num, comment_joinnum, tf, ld = doc.split('\t')
				if docid in time_scores:
					continue
				news_datetime = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
				now_datetime = datetime.now()
				td = now_datetime - news_datetime
				docid = int(docid)
				td = (timedelta.total_seconds(td) / 3600) # hour
				time_scores[docid] = td
		time_scores = sorted(time_scores.items(), key = operator.itemgetter(1))
		if len(time_scores) == 0:
			return 0, []
		else:
			return 1, time_scores

	def result_by_hot(self, sentence):
		print("klklklklklklkl")
		# seg_list = jieba.lcut(sentence, cut_all=False)
		n, cleaned_dict = self.clean_list(sentence)
		hot_scores = {}
		print("ququququuquququq")
		for term in cleaned_dict.keys():
			r = self.fetch_from_db(term)
			if r is None:
				continue
			df = r[1]
			w = math.log2((self.N - df + 0.5) / (df + 0.5))
			docs = r[2].split('\n')
			print("outer loop: ")
			for doc in docs:
				docid, date_time, comment_num, comment_joinnum, tf, ld = doc.split('\t')
				docid = int(docid)
				comment_num = int(comment_num)
				comment_joinnum = int(comment_joinnum)
				tf = int(tf)
				ld = int(ld)
				print("inner loop: ")
				news_datetime = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
				now_datetime = datetime.now()
				td = now_datetime - news_datetime
				print("after get time: ")
				BM25_score = (self.K1 * tf * w) / (tf + self.K1 * (1 - self.B + self.B * ld / self.AVG_L))
				td = (timedelta.total_seconds(td) / 3600) # hour
				# print(math.log(math.sqrt((20000+20000) / 2), 10))
				hot_score = math.log(BM25_score) + 1 / td + math.log(math.sqrt(comment_num*0.7+comment_joinnum*0.3) + 0.5, 200)
				print("hot_score: %f"%(hot_score))
				if docid in hot_scores:
					hot_scores[docid] = hot_scores[docid] + hot_score
				else:
					hot_scores[docid] = hot_score
		hot_scores = sorted(hot_scores.items(), key = operator.itemgetter(1))
		hot_scores.reverse()
		if len(hot_scores) == 0:
			return 0, []
		else:
			return 1, hot_scores

	def search(self, sentence, sort_type = 0):
		print("enter search: ")
		print("sort_type: %d"%(sort_type))
		if sort_type == 0:
			return self.result_by_BM25(sentence)
		elif sort_type == 1:
			return self.result_by_time(sentence)
		elif sort_type == 2:
			return self.result_by_hot(sentence)

if __name__ == "__main__":
	se = SearchEngine('../config.ini', 'utf-8')
	flag, rs = se.search('八宝山革命', 2)
	print(rs[:10])


