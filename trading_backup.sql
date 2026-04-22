--
-- PostgreSQL database dump
--

\restrict nqEG0cuVMS3upNKtlr3LY7idecGNo9e4a4sDqlCQZd6YPaq5Xc7ZJdfxDisCNcF

-- Dumped from database version 16.13
-- Dumped by pg_dump version 16.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- Name: equity_snapshots; Type: TABLE; Schema: public; Owner: trader
--

CREATE TABLE public.equity_snapshots (
    id integer NOT NULL,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    equity numeric(20,2) NOT NULL,
    cash numeric(20,2),
    open_positions integer,
    drawdown_pct numeric(10,4)
);


ALTER TABLE public.equity_snapshots OWNER TO trader;

--
-- Name: equity_snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: trader
--

CREATE SEQUENCE public.equity_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.equity_snapshots_id_seq OWNER TO trader;

--
-- Name: equity_snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trader
--

ALTER SEQUENCE public.equity_snapshots_id_seq OWNED BY public.equity_snapshots.id;


--
-- Name: journal; Type: TABLE; Schema: public; Owner: trader
--

CREATE TABLE public.journal (
    id integer NOT NULL,
    date date NOT NULL,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    entry_type character varying(30),
    content text,
    emotion character varying(20),
    focus_score integer,
    discipline_score integer,
    lessons text,
    tags character varying(255)
);


ALTER TABLE public.journal OWNER TO trader;

--
-- Name: journal_id_seq; Type: SEQUENCE; Schema: public; Owner: trader
--

CREATE SEQUENCE public.journal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.journal_id_seq OWNER TO trader;

--
-- Name: journal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trader
--

ALTER SEQUENCE public.journal_id_seq OWNED BY public.journal.id;


--
-- Name: snapshots; Type: TABLE; Schema: public; Owner: trader
--

CREATE TABLE public.snapshots (
    id integer NOT NULL,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    equity numeric(20,2),
    cash numeric(20,2),
    open_positions integer,
    open_exposure numeric(20,2),
    drawdown_pct numeric(10,4),
    daily_pnl numeric(20,2)
);


ALTER TABLE public.snapshots OWNER TO trader;

--
-- Name: snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: trader
--

CREATE SEQUENCE public.snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.snapshots_id_seq OWNER TO trader;

--
-- Name: snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trader
--

ALTER SEQUENCE public.snapshots_id_seq OWNED BY public.snapshots.id;


--
-- Name: trades; Type: TABLE; Schema: public; Owner: trader
--

CREATE TABLE public.trades (
    id integer NOT NULL,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    symbol character varying(20) NOT NULL,
    strategy character varying(50),
    side character varying(10),
    entry_price numeric(20,8),
    exit_price numeric(20,8),
    size numeric(20,8),
    pnl numeric(20,2),
    pnl_pct numeric(10,4),
    holding_bars integer,
    exit_reason character varying(50),
    stop_price numeric(20,8),
    target_price numeric(20,8),
    reasoning text,
    emotion_before character varying(20),
    emotion_after character varying(20),
    market_regime character varying(20),
    notes text,
    tags character varying(255),
    raw_metadata jsonb
);


ALTER TABLE public.trades OWNER TO trader;

--
-- Name: trades_id_seq; Type: SEQUENCE; Schema: public; Owner: trader
--

CREATE SEQUENCE public.trades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.trades_id_seq OWNER TO trader;

--
-- Name: trades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trader
--

ALTER SEQUENCE public.trades_id_seq OWNED BY public.trades.id;


--
-- Name: wiki_feedback; Type: TABLE; Schema: public; Owner: trader
--

CREATE TABLE public.wiki_feedback (
    id integer NOT NULL,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    symbol character varying(20) NOT NULL,
    regime character varying(20),
    side character varying(10),
    strategy character varying(50),
    wiki_action character varying(20),
    alignment_score numeric(5,4),
    min_alignment numeric(5,4),
    outcome character varying(10),
    pnl numeric(20,2),
    pnl_pct numeric(10,4),
    top_concepts text,
    context_summary text
);


ALTER TABLE public.wiki_feedback OWNER TO trader;

--
-- Name: wiki_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: trader
--

CREATE SEQUENCE public.wiki_feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wiki_feedback_id_seq OWNER TO trader;

--
-- Name: wiki_feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trader
--

ALTER SEQUENCE public.wiki_feedback_id_seq OWNED BY public.wiki_feedback.id;


--
-- Name: equity_snapshots id; Type: DEFAULT; Schema: public; Owner: trader
--

ALTER TABLE ONLY public.equity_snapshots ALTER COLUMN id SET DEFAULT nextval('public.equity_snapshots_id_seq'::regclass);


--
-- Name: journal id; Type: DEFAULT; Schema: public; Owner: trader
--

ALTER TABLE ONLY public.journal ALTER COLUMN id SET DEFAULT nextval('public.journal_id_seq'::regclass);


--
-- Name: snapshots id; Type: DEFAULT; Schema: public; Owner: trader
--

ALTER TABLE ONLY public.snapshots ALTER COLUMN id SET DEFAULT nextval('public.snapshots_id_seq'::regclass);


--
-- Name: trades id; Type: DEFAULT; Schema: public; Owner: trader
--

ALTER TABLE ONLY public.trades ALTER COLUMN id SET DEFAULT nextval('public.trades_id_seq'::regclass);


--
-- Name: wiki_feedback id; Type: DEFAULT; Schema: public; Owner: trader
--

ALTER TABLE ONLY public.wiki_feedback ALTER COLUMN id SET DEFAULT nextval('public.wiki_feedback_id_seq'::regclass);


--
-- Data for Name: equity_snapshots; Type: TABLE DATA; Schema: public; Owner: trader
--

COPY public.equity_snapshots (id, "timestamp", equity, cash, open_positions, drawdown_pct) FROM stdin;
\.


--
-- Data for Name: journal; Type: TABLE DATA; Schema: public; Owner: trader
--

COPY public.journal (id, date, "timestamp", entry_type, content, emotion, focus_score, discipline_score, lessons, tags) FROM stdin;
\.


--
-- Data for Name: snapshots; Type: TABLE DATA; Schema: public; Owner: trader
--

COPY public.snapshots (id, "timestamp", equity, cash, open_positions, open_exposure, drawdown_pct, daily_pnl) FROM stdin;
1	2026-04-22 14:02:25.298789	100000.00	100000.00	0	0.00	0.0000	0.00
2	2026-04-22 14:12:25.4647	100000.00	100000.00	0	0.00	0.0000	0.00
3	2026-04-22 14:22:25.928837	100000.00	100000.00	0	0.00	0.0000	0.00
4	2026-04-22 14:32:26.079951	100000.00	100000.00	0	0.00	0.0000	0.00
5	2026-04-22 14:42:26.272602	100000.00	100000.00	0	0.00	0.0000	0.00
6	2026-04-22 14:52:26.396453	100000.00	100000.00	0	0.00	0.0000	0.00
7	2026-04-22 14:55:12.603979	100000.00	100000.00	0	0.00	0.0000	0.00
8	2026-04-22 15:05:12.781665	100000.00	100000.00	0	0.00	0.0000	0.00
9	2026-04-22 15:15:12.931306	100000.00	100000.00	0	0.00	0.0000	0.00
10	2026-04-22 15:25:13.075409	100000.00	100000.00	0	0.00	0.0000	0.00
11	2026-04-22 15:35:13.244801	100000.00	100000.00	0	0.00	0.0000	0.00
12	2026-04-22 15:45:13.373563	100000.00	100000.00	0	0.00	0.0000	0.00
13	2026-04-22 15:55:13.549363	100000.00	100000.00	0	0.00	0.0000	0.00
14	2026-04-22 13:58:59.6896	100000.00	95000.00	1	0.00	0.0000	0.00
15	2026-04-22 14:13:59.6896	100150.00	95000.00	0	0.00	0.0000	0.00
16	2026-04-22 14:28:59.6896	100320.00	95000.00	0	0.00	0.0000	0.00
17	2026-04-22 14:43:59.6896	100180.00	95000.00	1	0.00	0.0000	0.00
18	2026-04-22 14:58:59.6896	100450.00	95000.00	0	0.00	0.0000	0.00
19	2026-04-22 15:13:59.6896	100280.00	95000.00	0	0.00	0.0000	0.00
20	2026-04-22 15:28:59.6896	100600.00	95000.00	1	0.00	0.0000	0.00
21	2026-04-22 15:43:59.6896	100750.00	95000.00	0	0.00	0.0000	0.00
22	2026-04-22 16:04:43.9098	100000.00	100000.00	0	0.00	0.0000	0.00
23	2026-04-22 16:14:44.109805	100000.00	100000.00	0	0.00	0.0000	0.00
24	2026-04-22 16:24:44.272611	100000.00	100000.00	0	0.00	0.0000	0.00
25	2026-04-22 16:34:44.453668	100000.00	100000.00	0	0.00	0.0000	0.00
26	2026-04-22 16:42:03.586035	100000.00	100000.00	0	0.00	0.0000	0.00
27	2026-04-22 16:48:32.875631	100000.00	100000.00	0	0.00	0.0000	0.00
28	2026-04-22 16:52:09.246305	100000.00	100000.00	0	0.00	0.0000	0.00
29	2026-04-22 17:01:25.662861	100000.00	100000.00	0	0.00	0.0000	0.00
30	2026-04-22 17:05:24.15793	100000.00	100000.00	0	0.00	0.0000	0.00
31	2026-04-22 17:08:28.949256	100000.00	100000.00	0	0.00	0.0000	0.00
32	2026-04-22 17:18:31.924729	100000.00	100000.00	0	0.00	0.0000	0.00
33	2026-04-22 17:23:35.508151	100000.00	100000.00	0	0.00	0.0000	0.00
\.


--
-- Data for Name: trades; Type: TABLE DATA; Schema: public; Owner: trader
--

COPY public.trades (id, "timestamp", symbol, strategy, side, entry_price, exit_price, size, pnl, pnl_pct, holding_bars, exit_reason, stop_price, target_price, reasoning, emotion_before, emotion_after, market_regime, notes, tags, raw_metadata) FROM stdin;
1	2026-04-22 15:58:41.713172	BTC/USDT	RegimeEnsemble	long	78000.00000000	79500.00000000	0.50000000	750.00	0.0192	12	take_profit	\N	\N		calm	confident	bull			\N
\.


--
-- Data for Name: wiki_feedback; Type: TABLE DATA; Schema: public; Owner: trader
--

COPY public.wiki_feedback (id, "timestamp", symbol, regime, side, strategy, wiki_action, alignment_score, min_alignment, outcome, pnl, pnl_pct, top_concepts, context_summary) FROM stdin;
\.


--
-- Name: equity_snapshots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: trader
--

SELECT pg_catalog.setval('public.equity_snapshots_id_seq', 1, false);


--
-- Name: journal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: trader
--

SELECT pg_catalog.setval('public.journal_id_seq', 1, false);


--
-- Name: snapshots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: trader
--

SELECT pg_catalog.setval('public.snapshots_id_seq', 33, true);


--
-- Name: trades_id_seq; Type: SEQUENCE SET; Schema: public; Owner: trader
--

SELECT pg_catalog.setval('public.trades_id_seq', 1, true);


--
-- Name: wiki_feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: trader
--

SELECT pg_catalog.setval('public.wiki_feedback_id_seq', 1, false);


--
-- Name: equity_snapshots equity_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: trader
--

ALTER TABLE ONLY public.equity_snapshots
    ADD CONSTRAINT equity_snapshots_pkey PRIMARY KEY (id);


--
-- Name: journal journal_pkey; Type: CONSTRAINT; Schema: public; Owner: trader
--

ALTER TABLE ONLY public.journal
    ADD CONSTRAINT journal_pkey PRIMARY KEY (id);


--
-- Name: snapshots snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: trader
--

ALTER TABLE ONLY public.snapshots
    ADD CONSTRAINT snapshots_pkey PRIMARY KEY (id);


--
-- Name: trades trades_pkey; Type: CONSTRAINT; Schema: public; Owner: trader
--

ALTER TABLE ONLY public.trades
    ADD CONSTRAINT trades_pkey PRIMARY KEY (id);


--
-- Name: wiki_feedback wiki_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: trader
--

ALTER TABLE ONLY public.wiki_feedback
    ADD CONSTRAINT wiki_feedback_pkey PRIMARY KEY (id);


--
-- Name: idx_equity_timestamp; Type: INDEX; Schema: public; Owner: trader
--

CREATE INDEX idx_equity_timestamp ON public.equity_snapshots USING btree ("timestamp");


--
-- Name: idx_journal_date; Type: INDEX; Schema: public; Owner: trader
--

CREATE INDEX idx_journal_date ON public.journal USING btree (date);


--
-- Name: idx_snapshots_timestamp; Type: INDEX; Schema: public; Owner: trader
--

CREATE INDEX idx_snapshots_timestamp ON public.snapshots USING btree ("timestamp");


--
-- Name: idx_trades_exit_reason; Type: INDEX; Schema: public; Owner: trader
--

CREATE INDEX idx_trades_exit_reason ON public.trades USING btree (exit_reason);


--
-- Name: idx_trades_strategy; Type: INDEX; Schema: public; Owner: trader
--

CREATE INDEX idx_trades_strategy ON public.trades USING btree (strategy);


--
-- Name: idx_trades_symbol; Type: INDEX; Schema: public; Owner: trader
--

CREATE INDEX idx_trades_symbol ON public.trades USING btree (symbol);


--
-- Name: idx_trades_timestamp; Type: INDEX; Schema: public; Owner: trader
--

CREATE INDEX idx_trades_timestamp ON public.trades USING btree ("timestamp");


--
-- Name: idx_wiki_outcome; Type: INDEX; Schema: public; Owner: trader
--

CREATE INDEX idx_wiki_outcome ON public.wiki_feedback USING btree (outcome);


--
-- Name: idx_wiki_symbol; Type: INDEX; Schema: public; Owner: trader
--

CREATE INDEX idx_wiki_symbol ON public.wiki_feedback USING btree (symbol);


--
-- PostgreSQL database dump complete
--

\unrestrict nqEG0cuVMS3upNKtlr3LY7idecGNo9e4a4sDqlCQZd6YPaq5Xc7ZJdfxDisCNcF

