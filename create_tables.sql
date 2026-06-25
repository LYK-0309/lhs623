-- 影视影评分享系统 - 建表SQL
-- 生成时间: 2026-06-24

SET NAMES utf8mb4;

-- admin
DROP TABLE IF EXISTS admin;

CREATE TABLE admin (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(64) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (username)
);

-- user
DROP TABLE IF EXISTS user;

CREATE TABLE user (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	email VARCHAR(128) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	nickname VARCHAR(64) NOT NULL, 
	avatar VARCHAR(256), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

-- category
DROP TABLE IF EXISTS category;

CREATE TABLE category (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;

-- movie
DROP TABLE IF EXISTS movie;

CREATE TABLE movie (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	title VARCHAR(128) NOT NULL, 
	intro TEXT, 
	actors VARCHAR(256), 
	release_date DATE, 
	rating FLOAT, 
	poster_url VARCHAR(512), 
	trailer_url VARCHAR(512), 
	created_at DATETIME, 
	likes INTEGER, 
	category_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES category (id)
)

;

-- comment
DROP TABLE IF EXISTS comment;

CREATE TABLE comment (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	content TEXT NOT NULL, 
	author VARCHAR(64), 
	created_at DATETIME, 
	movie_id INTEGER NOT NULL, 
	user_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(movie_id) REFERENCES movie (id)
);
