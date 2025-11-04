-- ============================================
-- CLEAN TEST DATABASE WITH POPULATED DATA
-- ============================================

-- Drop tables if they already exist
drop table if exists orderlines;
drop table if exists orders;
drop table if exists cart;
drop table if exists search;
drop table if exists viewedProduct;
drop table if exists sessions;
drop table if exists products;
drop table if exists customers;
drop table if exists users;

-- ============================================
-- USERS
-- ============================================
create table users (
  uid		int,
  pwd		text,
  role		text check (role in ('customer', 'sales')),
  primary key (uid)
);

insert into users values
(1, 'pass123', 'customer'),
(2, 'mypass', 'customer'),
(3, 'secure!', 'customer'),
(4, 'sales', 'sales'),
(5, 'guestpw', 'customer');

-- ============================================
-- CUSTOMERS
-- ============================================
create table customers (
  cid		int,
  name		text, 
  email		text,
  primary key (cid),
  foreign key (cid) references users
);

insert into customers values
(1, 'Alice Johnson', 'alice@example.com'),
(2, 'Bob Smith', 'bob@example.com'),
(3, 'Charlie Kim', 'charlie@example.com'),
(5, 'Dana Lee', 'dana@example.com');

-- ============================================
-- PRODUCTS
-- ============================================
create table products (
  pid		int, 
  name		text, 
  category	text, 
  price		float, 
  stock_count	int, 
  descr		text,
  primary key (pid)
);

insert into products values
(101, 'Laptop Pro 15"', 'Electronics', 1299.99, 12, 'High-end laptop with 16GB RAM, 512GB SSD'),
(102, 'Wireless Mouse', 'Accessories', 29.99, 50, 'Ergonomic wireless mouse with USB receiver'),
(103, 'Bluetooth Headphones', 'Audio', 79.95, 30, 'Noise-cancelling over-ear headphones'),
(104, '4K Monitor', 'Electronics', 399.00, 20, '27-inch 4K UHD monitor with HDR'),
(105, 'Gaming Keyboard', 'Accessories', 89.99, 25, 'Mechanical keyboard with RGB lighting'),
(106, 'Office Chair', 'Furniture', 199.99, 10, 'Ergonomic office chair with lumbar support');

-- ============================================
-- SESSIONS
-- ============================================
create table sessions (
  cid		int,
  sessionNo	int, 
  start_time	datetime, 
  end_time	datetime,
  primary key (cid, sessionNo),
  foreign key (cid) references customers on delete cascade
);

insert into sessions values
(1, 1, '2025-10-01 09:00:00', '2025-10-01 10:15:00'),
(1, 2, '2025-10-10 15:00:00', '2025-10-10 15:45:00'),
(2, 1, '2025-10-03 18:00:00', '2025-10-03 19:00:00'),
(3, 1, '2025-10-05 08:30:00', '2025-10-05 09:15:00'),
(5, 1, '2025-10-07 20:00:00', '2025-10-07 21:00:00');

-- ============================================
-- VIEWED PRODUCT
-- ============================================
create table viewedProduct (
  cid		int, 
  sessionNo	int, 
  ts		timestamp, 
  pid		int,
  primary key (cid, sessionNo, ts),
  foreign key (cid, sessionNo) references sessions,
  foreign key (pid) references products
);

insert into viewedProduct values
(1, 1, '2025-10-01 09:10:00', 101),
(1, 1, '2025-10-01 09:20:00', 104),
(1, 2, '2025-10-10 15:10:00', 105),
(2, 1, '2025-10-03 18:15:00', 103),
(2, 1, '2025-10-03 18:30:00', 102),
(3, 1, '2025-10-05 08:45:00', 106),
(5, 1, '2025-10-07 20:15:00', 101),
(5, 1, '2025-10-07 20:25:00', 103);

-- ============================================
-- SEARCH
-- ============================================
create table search (
  cid		int, 
  sessionNo	int, 
  ts		timestamp, 
  query		text,
  primary key (cid, sessionNo, ts),
  foreign key (cid, sessionNo) references sessions
);

insert into search values
(1, 1, '2025-10-01 09:05:00', 'laptop 16gb ram'),
(1, 2, '2025-10-10 15:05:00', 'mechanical keyboard'),
(2, 1, '2025-10-03 18:05:00', 'bluetooth headphones'),
(3, 1, '2025-10-05 08:35:00', 'office chair ergonomic'),
(5, 1, '2025-10-07 20:05:00', 'cheap laptop');

-- ============================================
-- CART
-- ============================================
create table cart (
  cid		int, 
  sessionNo	int, 
  pid		int,
  qty		int,
  primary key (cid, sessionNo, pid),
  foreign key (cid, sessionNo) references sessions,
  foreign key (pid) references products
);

insert into cart values
(1, 1, 101, 1),
(1, 2, 105, 1),
(2, 1, 103, 2),
(3, 1, 106, 1),
(5, 1, 101, 1),
(5, 1, 102, 1);

-- ============================================
-- ORDERS
-- ============================================
create table orders (
  ono		int, 
  cid		int,
  sessionNo	int,
  odate		date, 
  shipping_address text,
  primary key (ono),
  foreign key (cid, sessionNo) references sessions
);

insert into orders values
(5001, 1, 1, '2025-10-01', '123 Maple St, Springfield'),
(5002, 2, 1, '2025-10-03', '45 Oak Ave, Riverdale'),
(5003, 3, 1, '2025-10-05', '78 Pine Rd, Centerville'),
(5004, 5, 1, '2025-10-07', '12 Birch Ln, Lakeside');

-- ============================================
-- ORDERLINES
-- ============================================
create table orderlines (
  ono		int, 
  lineNo	int, 
  pid		int, 
  qty		int, 
  uprice	float, 
  primary key (ono, lineNo),
  foreign key (ono) references orders on delete cascade
);

insert into orderlines values
(5001, 1, 101, 1, 1299.99),
(5001, 2, 104, 1, 399.00),
(5002, 1, 103, 2, 79.95),
(5003, 1, 106, 1, 199.99),
(5004, 1, 101, 1, 1299.99),
(5004, 2, 102, 1, 29.99);
