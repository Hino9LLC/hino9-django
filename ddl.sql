CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    email_id VARCHAR(255) UNIQUE,
    subject TEXT,
    sender TEXT,
    recipient TEXT,
    date TIMESTAMP WITH TIME ZONE,
    body_text TEXT,
    body_html TEXT,
    raw_email TEXT,
    source VARCHAR(255),  -- Newsletter source
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    processed_at TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
);

-- Create the urls table
CREATE TABLE IF NOT EXISTS urls (
    id SERIAL PRIMARY KEY,
    original_url VARCHAR(2048) NOT NULL,
    final_url VARCHAR(2048),
    cleaned_url VARCHAR(2048),
    email_id VARCHAR(255) NOT NULL,
    url_text TEXT,
    content_text TEXT,
    domain VARCHAR(255),
    site_name VARCHAR(255),
    image_url VARCHAR(2048),
    image_base64 TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    title VARCHAR(512),
    summary TEXT,
    FOREIGN KEY (email_id) REFERENCES emails(email_id),
    UNIQUE(original_url, email_id)
);

-- Create the email_fetch_log table
CREATE TABLE IF NOT EXISTS email_fetch_log (
    id SERIAL PRIMARY KEY,
    email_uid VARCHAR(255) NOT NULL,
    source VARCHAR(255),
    fetch_status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    attempt_count INT DEFAULT 0,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    last_attempt TIMESTAMP WITH TIME ZONE,
    UNIQUE(email_uid)
);

-- Create the attachments table
CREATE TABLE IF NOT EXISTS attachments (
    id SERIAL PRIMARY KEY,
    email_id INTEGER REFERENCES emails(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    filepath TEXT,
    content_type VARCHAR(100),
    file_size BIGINT,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
);

CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    article_date TIMESTAMP WITH TIME ZONE,
    title VARCHAR(512),
    summary TEXT,
    llm_headline TEXT,
    llm_summary TEXT,
    llm_bullets TEXT[],
    llm_tags TEXT[],
    domain VARCHAR(255),
    site_name VARCHAR(255),
    image_url VARCHAR(2048),
    url VARCHAR(2048),
    article_id INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    content_text TEXT,
    content_embedding VECTOR(768), -- pgvector: matches nomic-embed-text-v1.5
    ts_vector_content TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(content_text, ''))
    ) STORED,
    
    -- Constraints
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    UNIQUE(article_id)
);

-- Create the articles table
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    article_date TIMESTAMP WITH TIME ZONE,
    title VARCHAR(512),
    summary TEXT,
    domain VARCHAR(255),
    site_name VARCHAR(255),
    image_url VARCHAR(2048),
    url VARCHAR(2048),
    url_id INTEGER,
    email_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    tags TEXT[],
    metadata JSONB,
    content_text TEXT,
    content_embedding VECTOR(768), -- pgvector: matches nomic-embed-text-v1.5
    ts_vector_content TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(content_text, ''))
    ) STORED,
    
    -- Constraints
    FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE,
    FOREIGN KEY (email_id) REFERENCES emails(email_id) ON DELETE SET NULL,
    UNIQUE(url_id, article_date)
);

CREATE TABLE article_insights (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE UNIQUE,
    summary TEXT,                     -- abstract/summary of the article
    tags TEXT[],                      -- keywords or topical tags
    key_points TEXT[],                -- bullet-style highlights
    qa_pairs JSONB,                   -- optional: list of generated Q&A pairs
    sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative')),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),  -- when the insight was generated
    model_used TEXT                   -- to record which LLM model/version was used
);

-- Emails table indexes
CREATE INDEX IF NOT EXISTS idx_email_id ON emails(email_id);
CREATE INDEX IF NOT EXISTS idx_email_status ON emails(status);
CREATE INDEX IF NOT EXISTS idx_email_source ON emails(source);
CREATE INDEX IF NOT EXISTS idx_email_date ON emails(date);
CREATE INDEX IF NOT EXISTS idx_email_sender ON emails(sender);
CREATE INDEX IF NOT EXISTS idx_email_recipient ON emails(recipient);

-- URLs table indexes
CREATE INDEX IF NOT EXISTS idx_url_status ON urls(status);
CREATE INDEX IF NOT EXISTS idx_url_email_id ON urls(email_id);
CREATE INDEX IF NOT EXISTS idx_url_created_at ON urls(created_at);

-- Email fetch log table indexes
CREATE INDEX IF NOT EXISTS idx_fetch_status ON email_fetch_log(fetch_status);
CREATE INDEX IF NOT EXISTS idx_fetch_source ON email_fetch_log(source);
CREATE INDEX IF NOT EXISTS idx_fetch_uid ON email_fetch_log(email_uid);

-- Attachments table indexes
CREATE INDEX IF NOT EXISTS idx_attachment_email_id ON attachments(email_id);
CREATE INDEX IF NOT EXISTS idx_attachment_filename ON attachments(filename);
CREATE INDEX IF NOT EXISTS idx_attachment_status ON attachments(status);

-- Articles table indexes
CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_article_date ON articles(article_date);
CREATE INDEX IF NOT EXISTS idx_articles_domain ON articles(domain);
CREATE INDEX IF NOT EXISTS idx_articles_site_name ON articles(site_name);
CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title);
CREATE INDEX IF NOT EXISTS idx_articles_content_embedding ON articles USING ivfflat (content_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_articles_ts_vector_content ON articles USING GIN (ts_vector_content);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at);
CREATE INDEX IF NOT EXISTS idx_articles_processed_at ON articles(processed_at);
CREATE INDEX IF NOT EXISTS idx_articles_deleted_at ON articles(deleted_at);

-- Article insights table indexes
CREATE INDEX IF NOT EXISTS idx_article_insights_article_id ON article_insights(article_id);
CREATE INDEX IF NOT EXISTS idx_article_insights_sentiment ON article_insights(sentiment);
CREATE INDEX IF NOT EXISTS idx_article_insights_generated_at ON article_insights(generated_at);
CREATE INDEX IF NOT EXISTS idx_article_insights_model_used ON article_insights(model_used);

-- News table indexes
CREATE INDEX IF NOT EXISTS idx_news_status ON news(status);
CREATE INDEX IF NOT EXISTS idx_news_created_at ON news(created_at);
CREATE INDEX IF NOT EXISTS idx_news_processed_at ON news(processed_at);
CREATE INDEX IF NOT EXISTS idx_news_article_date ON news(article_date);
CREATE INDEX IF NOT EXISTS idx_news_domain ON news(domain);
CREATE INDEX IF NOT EXISTS idx_news_site_name ON news(site_name);
CREATE INDEX IF NOT EXISTS idx_news_title ON news(title);
CREATE INDEX IF NOT EXISTS idx_news_llm_headline ON news(llm_headline);
CREATE INDEX IF NOT EXISTS idx_news_llm_summary ON news(llm_summary);
CREATE INDEX IF NOT EXISTS idx_news_llm_bullets ON news(llm_bullets);
CREATE INDEX IF NOT EXISTS idx_news_llm_tags ON news(llm_tags);
CREATE INDEX IF NOT EXISTS idx_news_url ON news(url);
CREATE INDEX IF NOT EXISTS idx_news_content_embedding ON news USING ivfflat (content_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_news_ts_vector_content ON news USING GIN (ts_vector_content);

-- Create the tweets table
CREATE TABLE IF NOT EXISTS tweets (
    id SERIAL PRIMARY KEY,
    news_id INTEGER NOT NULL REFERENCES news(id) ON DELETE CASCADE,
    tweet_text TEXT NOT NULL,
    tweet_id VARCHAR(255) UNIQUE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
    error_message TEXT,
    tweeted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    UNIQUE(news_id)
);

-- Tweets table indexes
CREATE INDEX IF NOT EXISTS idx_tweets_news_id ON tweets(news_id);
CREATE INDEX IF NOT EXISTS idx_tweets_status ON tweets(status);
CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at);
CREATE INDEX IF NOT EXISTS idx_tweets_tweeted_at ON tweets(tweeted_at);
CREATE INDEX IF NOT EXISTS idx_tweets_tweet_id ON tweets(tweet_id);
