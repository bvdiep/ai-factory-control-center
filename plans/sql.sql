create user 'aifactory'@'%' identified by 'Aifactory123456';

create database if not exists aifactory;
grant all privileges on aifactory.* to 'aifactory'@'%' with grant option;
flush privileges;