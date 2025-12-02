--
-- PostgreSQL database dump
--

\restrict shQMf1BQqmxpYDuOj7AQY0AGj5iL4SvLQKCihD3EHXtA559qV2WCBAcjHHhjosW

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

-- Started on 2025-12-03 00:51:21

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 224 (class 1259 OID 16497)
-- Name: clients; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.clients (
    id integer NOT NULL,
    first_name character varying(50) NOT NULL,
    last_name character varying(50) NOT NULL,
    email character varying(100),
    phone character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.clients OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16496)
-- Name: clients_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.clients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.clients_id_seq OWNER TO postgres;

--
-- TOC entry 4983 (class 0 OID 0)
-- Dependencies: 223
-- Name: clients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.clients_id_seq OWNED BY public.clients.id;


--
-- TOC entry 222 (class 1259 OID 16482)
-- Name: minibus; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.minibus (
    id integer NOT NULL,
    capacity integer NOT NULL,
    license_plate character varying(20),
    current_passengers integer DEFAULT 0,
    status character varying(20) DEFAULT 'available'::character varying,
    last_maintenance date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT minibus_capacity_check CHECK (((capacity >= 10) AND (capacity <= 30)))
);


ALTER TABLE public.minibus OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16481)
-- Name: minibus_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.minibus_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.minibus_id_seq OWNER TO postgres;

--
-- TOC entry 4984 (class 0 OID 0)
-- Dependencies: 221
-- Name: minibus_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.minibus_id_seq OWNED BY public.minibus.id;


--
-- TOC entry 228 (class 1259 OID 16536)
-- Name: optimized_routes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.optimized_routes (
    id integer NOT NULL,
    minibus_id integer,
    station_sequence jsonb,
    total_distance numeric(10,2),
    total_passengers integer,
    calculation_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.optimized_routes OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16535)
-- Name: optimized_routes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.optimized_routes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.optimized_routes_id_seq OWNER TO postgres;

--
-- TOC entry 4985 (class 0 OID 0)
-- Dependencies: 227
-- Name: optimized_routes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.optimized_routes_id_seq OWNED BY public.optimized_routes.id;


--
-- TOC entry 226 (class 1259 OID 16510)
-- Name: reservations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reservations (
    id integer NOT NULL,
    client_id integer,
    pickup_station_id integer,
    dropoff_station_id integer,
    number_of_people integer NOT NULL,
    desired_time time without time zone,
    status character varying(20) DEFAULT 'pending'::character varying,
    CONSTRAINT reservations_number_of_people_check CHECK ((number_of_people > 0))
);


ALTER TABLE public.reservations OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16509)
-- Name: reservations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reservations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reservations_id_seq OWNER TO postgres;

--
-- TOC entry 4986 (class 0 OID 0)
-- Dependencies: 225
-- Name: reservations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reservations_id_seq OWNED BY public.reservations.id;


--
-- TOC entry 220 (class 1259 OID 16471)
-- Name: stations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.stations (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL
);


ALTER TABLE public.stations OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16470)
-- Name: stations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.stations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.stations_id_seq OWNER TO postgres;

--
-- TOC entry 4987 (class 0 OID 0)
-- Dependencies: 219
-- Name: stations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.stations_id_seq OWNED BY public.stations.id;


--
-- TOC entry 230 (class 1259 OID 16560)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password character varying(255) NOT NULL,
    role character varying(20),
    chauffeur_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp without time zone,
    is_active boolean DEFAULT true,
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'chauffeur'::character varying])::text[])))
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 16559)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- TOC entry 4988 (class 0 OID 0)
-- Dependencies: 229
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 4785 (class 2604 OID 16500)
-- Name: clients id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients ALTER COLUMN id SET DEFAULT nextval('public.clients_id_seq'::regclass);


--
-- TOC entry 4781 (class 2604 OID 16485)
-- Name: minibus id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.minibus ALTER COLUMN id SET DEFAULT nextval('public.minibus_id_seq'::regclass);


--
-- TOC entry 4789 (class 2604 OID 16539)
-- Name: optimized_routes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimized_routes ALTER COLUMN id SET DEFAULT nextval('public.optimized_routes_id_seq'::regclass);


--
-- TOC entry 4787 (class 2604 OID 16513)
-- Name: reservations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reservations ALTER COLUMN id SET DEFAULT nextval('public.reservations_id_seq'::regclass);


--
-- TOC entry 4780 (class 2604 OID 16474)
-- Name: stations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stations ALTER COLUMN id SET DEFAULT nextval('public.stations_id_seq'::regclass);


--
-- TOC entry 4791 (class 2604 OID 16563)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 4971 (class 0 OID 16497)
-- Dependencies: 224
-- Data for Name: clients; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.clients (id, first_name, last_name, email, phone, created_at) FROM stdin;
1	Ahmed	Alaoui	ahmed.alaoui@email.com	+212-600-123456	2025-11-26 23:11:51.29776
2	Fatima	Benali	fatima.benali@email.com	+212-600-234567	2025-11-26 23:11:51.29776
3	Mehdi	Chraibi	mehdi.chraibi@email.com	+212-600-345678	2025-11-26 23:11:51.29776
4	Khadija	Mansouri	khadija.mansouri@email.com	+212-600-456789	2025-11-26 23:11:51.29776
5	Youssef	El Fassi	youssef.elfassi@email.com	+212-600-567890	2025-11-26 23:11:51.29776
6	Nadia	Saidi	nadia.saidi@email.com	+212-600-678901	2025-11-26 23:11:51.29776
7	Ahmed	Alaoui	admin@test.com	+212-600-123456	2025-12-02 17:59:31.206253
8	Khalid	Bensaid	khalid.bensaid@email.com	+212-600-789012	2025-12-02 17:59:31.206253
9	Test	Client	test.client@email.com	+212 600 000 000	2025-12-02 22:31:35.363418
11	Test	User	test.b63275@test.com	+212600000000	2025-12-02 23:01:24.074929
12	Test	User	test.5ec93f@test.com	+212600000000	2025-12-02 23:17:44.939234
13	Test	User	test.8daf2f@test.com	+212600000000	2025-12-02 23:19:02.877064
14	Test	User	test.b5c564@test.com	+212600000000	2025-12-03 00:48:53.412967
\.


--
-- TOC entry 4969 (class 0 OID 16482)
-- Dependencies: 222
-- Data for Name: minibus; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.minibus (id, capacity, license_plate, current_passengers, status, last_maintenance, created_at) FROM stdin;
1	20	M-1234-AB	0	available	2024-11-01	2025-11-26 23:11:51.29776
2	18	M-5678-CD	0	available	2024-10-15	2025-11-26 23:11:51.29776
3	22	M-9012-EF	0	available	2024-11-10	2025-11-26 23:11:51.29776
4	16	M-3456-GH	0	available	2024-10-25	2025-11-26 23:11:51.29776
5	20	M-7890-IJ	0	available	2024-11-05	2025-11-26 23:11:51.29776
\.


--
-- TOC entry 4975 (class 0 OID 16536)
-- Dependencies: 228
-- Data for Name: optimized_routes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.optimized_routes (id, minibus_id, station_sequence, total_distance, total_passengers, calculation_time) FROM stdin;
1	1	[1, 3, 5, 2]	15.50	8	2025-12-02 23:19:02.841692
2	1	[1, 3, 5, 2]	15.50	8	2025-12-03 00:48:53.368608
\.


--
-- TOC entry 4973 (class 0 OID 16510)
-- Dependencies: 226
-- Data for Name: reservations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reservations (id, client_id, pickup_station_id, dropoff_station_id, number_of_people, desired_time, status) FROM stdin;
1	1	1	7	3	08:00:00	pending
2	2	2	7	2	08:30:00	pending
3	3	8	4	4	09:00:00	pending
4	4	8	1	2	09:15:00	pending
5	5	4	2	1	17:00:00	pending
6	6	3	5	2	17:30:00	pending
7	1	1	2	2	10:00:00	pending
8	1	1	2	2	10:00:00	pending
\.


--
-- TOC entry 4967 (class 0 OID 16471)
-- Dependencies: 220
-- Data for Name: stations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.stations (id, name, latitude, longitude) FROM stdin;
1	Jamaâ El Fna	31.6258	-7.9891
2	Gare Marrakech	31.6308	-8.0027
3	Ménara	31.6111	-8.0292
4	Gueliz	31.6364	-8.0103
5	Palmeraie	31.6708	-7.9736
6	Médina	31.625	-7.9914
7	Aéroport Marrakech	31.6069	-8.0363
8	Université Cadi Ayyad	31.6417	-8.0089
\.


--
-- TOC entry 4977 (class 0 OID 16560)
-- Dependencies: 230
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, password, role, chauffeur_id, created_at, last_login, is_active) FROM stdin;
2	chauffeur@transport.com	chauffeur123	chauffeur	\N	2025-12-02 18:22:02.07339	2025-12-02 22:40:05.09361	t
1	admin@test.com	admin123	admin	\N	2025-12-02 18:22:02.07339	2025-12-03 00:48:53.40658	t
\.


--
-- TOC entry 4989 (class 0 OID 0)
-- Dependencies: 223
-- Name: clients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.clients_id_seq', 14, true);


--
-- TOC entry 4990 (class 0 OID 0)
-- Dependencies: 221
-- Name: minibus_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.minibus_id_seq', 5, true);


--
-- TOC entry 4991 (class 0 OID 0)
-- Dependencies: 227
-- Name: optimized_routes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.optimized_routes_id_seq', 2, true);


--
-- TOC entry 4992 (class 0 OID 0)
-- Dependencies: 225
-- Name: reservations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reservations_id_seq', 8, true);


--
-- TOC entry 4993 (class 0 OID 0)
-- Dependencies: 219
-- Name: stations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.stations_id_seq', 8, true);


--
-- TOC entry 4994 (class 0 OID 0)
-- Dependencies: 229
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- TOC entry 4804 (class 2606 OID 16508)
-- Name: clients clients_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_email_key UNIQUE (email);


--
-- TOC entry 4806 (class 2606 OID 16506)
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- TOC entry 4800 (class 2606 OID 16495)
-- Name: minibus minibus_license_plate_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.minibus
    ADD CONSTRAINT minibus_license_plate_key UNIQUE (license_plate);


--
-- TOC entry 4802 (class 2606 OID 16493)
-- Name: minibus minibus_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.minibus
    ADD CONSTRAINT minibus_pkey PRIMARY KEY (id);


--
-- TOC entry 4810 (class 2606 OID 16545)
-- Name: optimized_routes optimized_routes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimized_routes
    ADD CONSTRAINT optimized_routes_pkey PRIMARY KEY (id);


--
-- TOC entry 4808 (class 2606 OID 16519)
-- Name: reservations reservations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reservations
    ADD CONSTRAINT reservations_pkey PRIMARY KEY (id);


--
-- TOC entry 4798 (class 2606 OID 16480)
-- Name: stations stations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stations
    ADD CONSTRAINT stations_pkey PRIMARY KEY (id);


--
-- TOC entry 4812 (class 2606 OID 16575)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4814 (class 2606 OID 16573)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4818 (class 2606 OID 16546)
-- Name: optimized_routes optimized_routes_minibus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimized_routes
    ADD CONSTRAINT optimized_routes_minibus_id_fkey FOREIGN KEY (minibus_id) REFERENCES public.minibus(id);


--
-- TOC entry 4815 (class 2606 OID 16520)
-- Name: reservations reservations_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reservations
    ADD CONSTRAINT reservations_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE CASCADE;


--
-- TOC entry 4816 (class 2606 OID 16530)
-- Name: reservations reservations_dropoff_station_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reservations
    ADD CONSTRAINT reservations_dropoff_station_id_fkey FOREIGN KEY (dropoff_station_id) REFERENCES public.stations(id) ON DELETE CASCADE;


--
-- TOC entry 4817 (class 2606 OID 16525)
-- Name: reservations reservations_pickup_station_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reservations
    ADD CONSTRAINT reservations_pickup_station_id_fkey FOREIGN KEY (pickup_station_id) REFERENCES public.stations(id) ON DELETE CASCADE;


-- Completed on 2025-12-03 00:51:21

--
-- PostgreSQL database dump complete
--

\unrestrict shQMf1BQqmxpYDuOj7AQY0AGj5iL4SvLQKCihD3EHXtA559qV2WCBAcjHHhjosW

