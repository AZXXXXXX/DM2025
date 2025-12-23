drop database if exists order_system;
create database if not exists order_system;
use order_system;

create table customer
(
    customer_id    varchar(64)  not null
        primary key,
    company_name   varchar(200) not null,
    customer_type  int          null,
    contact_person varchar(50)  null,
    contact_phone  varchar(20)  null,
    contact_email  varchar(100) null,
    address        varchar(500) null,
    city           varchar(50)  null,
    province       varchar(50)  null,
    postal_code    varchar(10)  null,
    tax_id         varchar(50)  null,
    credit_level   int          null,
    notes          text         null,
    is_active      tinyint(1)   null,
    created_at     datetime     null,
    updated_at     datetime     null,
    constraint ix_customer_company_name
        unique (company_name)
);

create table inventory
(
    product_id       varchar(64)  not null
        primary key,
    product_type     varchar(100) not null,
    manufacturer     varchar(200) not null,
    product_name     varchar(200) not null,
    product_model    varchar(100) null,
    stock_quantity   int          null,
    sold_quantity    int          null,
    status           int          null,
    expected_arrival datetime     null,
    created_at       datetime     null,
    updated_at       datetime     null
);

create index ix_inventory_product_name
    on inventory (product_name);

create table user
(
    user_id       varchar(64)  not null
        primary key,
    username      varchar(50)  not null,
    password_hash varchar(128) not null,
    display_name  varchar(100) null,
    role          int          null,
    department    varchar(100) null,
    email         varchar(100) null,
    phone         varchar(20)  null,
    is_active     tinyint(1)   null,
    created_at    datetime     null,
    updated_at    datetime     null,
    last_login_at datetime     null,
    constraint ix_user_username
        unique (username)
);

create table return_request
(
    return_request_id varchar(64)  not null
        primary key,
    order_id          varchar(50)  not null,
    product_id        varchar(64)  not null,
    quantity          int          not null,
    reason            int          not null,
    description       text         null,
    status            int          null,
    customer_name     varchar(200) not null,
    reviewer_id       varchar(64)  null,
    review_comment    text         null,
    reviewed_at       datetime     null,
    created_at        datetime     null,
    updated_at        datetime     null,
    constraint fk_return_request_product_id
        foreign key (product_id) references inventory (product_id),
    constraint fk_return_request_reviewer_id
        foreign key (reviewer_id) references user (user_id)
);

create index ix_return_request_order_id
    on return_request (order_id);

create table `order`
(
    Hash              varchar(64)  not null
        primary key,
    customer_type     int          null,
    customer_name     varchar(200) not null,
    sales             varchar(100) not null,
    order_id          varchar(50)  not null,
    tracking_number   varchar(100) null,
    status            int          not null,
    order_time        datetime     not null,
    payment_time      datetime     null,
    ship_deadline     datetime     null,
    product_id        varchar(64)  not null,
    quantity          int          not null,
    return_request_id varchar(64)  null,
    customer_id       varchar(64)  null,
    created_by_id     varchar(64)  null,
    return_applied    tinyint(1)   null,
    created_at        datetime     null,
    updated_at        datetime     null,
    constraint fk_order_customer_id
        foreign key (customer_id) references customer (customer_id),
    constraint fk_order_product_id
        foreign key (product_id) references inventory (product_id),
    constraint fk_order_created_by_id
        foreign key (created_by_id) references user (user_id)
);

create index ix_order_created_by_id
    on `order` (created_by_id);

create index ix_order_customer_id
    on `order` (customer_id);

create index ix_order_order_id
    on `order` (order_id);

create index ix_order_return_request_id
    on `order` (return_request_id);