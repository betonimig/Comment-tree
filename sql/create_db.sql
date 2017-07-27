--- пользователи
CREATE TABLE "users_tbl" (
	"id" serial NOT NULL PRIMARY KEY,
	"username" varchar(30) NOT NULL
);

--- комментарии
CREATE TABLE "comments_tbl" (
	"id" bigserial NOT NULL PRIMARY KEY,
    "entity_type" varchar(30) NOT NULL,
    "entity_id" bigint NOT NULL,
    "parent_id" bigint REFERENCES "comments_tbl" ("id") DEFERRABLE INITIALLY DEFERRED,
    "user_id" integer NOT NULL REFERENCES "users_tbl" ("id") DEFERRABLE INITIALLY DEFERRED,
    "text" text NOT NULL,
    "created_dt" timestamp with time zone NOT NULL DEFAULT now(),
    "is_removed" boolean NOT NULL DEFAULT false,
    "ltree_path" LTREE
);

CREATE INDEX "comments_parent_id_idx" ON "comments_tbl" ("parent_id");
CREATE INDEX "comments_user_id_idx" ON "comments_tbl" ("user_id");
--- B-дерево по значениям ltree: <, <=, =, >=, >
CREATE INDEX "path_idx" ON "comments_tbl" USING BTREE ("ltree_path");
--- GiST по значениям ltree: <, <=, =, >=, >, @>, <@, @, ~, ?
CREATE INDEX "path_gist_idx" ON "comments_tbl" USING GIST ("ltree_path");
---CREATE INDEX "comments_object_id_type" 

--- обновляет material path у новых комментариев
CREATE OR REPLACE FUNCTION update_path() RETURNS TRIGGER AS
$$
DECLARE
    path ltree;
BEGIN
	IF NEW.id IS NULL THEN
		NEW.id = nextval('comments_tbl_id_seq');
	END IF;

    --- если не задан родитель, то все просто - он корневой
	IF NEW.parent_id IS NULL THEN
        path = NEW.id::text::ltree;
    ELSE
		SELECT (ltree_path || NEW.id::text)::ltree FROM comments_tbl WHERE id = NEW.parent_id INTO path;
	    IF path IS NULL THEN
	        RAISE EXCEPTION 'Invalid parent_id %', NEW.parent_id;
	    END IF;
	END IF;
	NEW.ltree_path = path;
  	RETURN NEW;
END
$$
LANGUAGE 'plpgsql';

CREATE TRIGGER trig_update_path BEFORE INSERT ON comments_tbl FOR EACH ROW
    EXECUTE PROCEDURE update_path();

--- вставляем пользователей
INSERT INTO "users_tbl" VALUES (1, 'test1'), (2, 'test2'), (3, 'test3');

ALTER SEQUENCE comments_tbl_id_seq restart ;
DELETE FROM comments_tbl ;

--- Заявки на генерацию файлов
CREATE TABLE export_request_tbl (
    id UUID NOT NULL PRIMARY KEY,
    format varchar(5) NOT NULL,
    data json NOT NULL,
    created_dt timestamp without time zone NOT NULL DEFAULT(now()),
    file_path varchar(255)
);

--- История модификаций комментариев
CREATE TABLE comment_history_tbl (
    id bigserial NOT NULL PRIMARY KEY,
    comment_id bigint REFERENCES "comments_tbl" ("id") DEFERRABLE INITIALLY DEFERRED,
    dt timestamp with time zone NOT NULL DEFAULT now(),
    user_id integer NOT NULL REFERENCES "users_tbl" ("id") DEFERRABLE INITIALLY DEFERRED,
    action varchar(10) NOT NULL,
    diff text
);
CREATE INDEX "chistory_comment_id_idx" ON "comment_history_tbl" ("comment_id");
CREATE INDEX "chistory_user_id_idx" ON "comment_history_tbl" ("user_id");
