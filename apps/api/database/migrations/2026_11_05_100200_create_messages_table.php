<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

/**
 * The message mirror. A row is identified by (folder, uid) under the folder's stored UIDVALIDITY.
 * Column names avoid SQL reserved words (to, references) so raw search SQL stays simple.
 * `search_text` is Arabic-normalized, lower-cased text; `search_vector` indexes it (GIN).
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('messages', function (Blueprint $table) {
            $table->ulid('id')->primary();
            $table->foreignUlid('account_id')->constrained('mail_accounts')->cascadeOnDelete();
            $table->foreignUlid('folder_id')->constrained('mail_folders')->cascadeOnDelete();
            $table->bigInteger('uid');
            $table->text('message_id')->nullable();
            $table->text('in_reply_to')->nullable();
            $table->jsonb('reference_ids')->nullable();
            $table->ulid('thread_id')->nullable()->index();
            $table->text('subject')->nullable();
            $table->text('normalized_subject')->nullable();
            $table->text('from_name')->nullable();
            $table->text('from_email')->nullable();
            $table->jsonb('to_list')->nullable();
            $table->jsonb('cc_list')->nullable();
            $table->jsonb('bcc_list')->nullable();
            $table->jsonb('reply_to_list')->nullable();
            $table->timestampTz('sent_at')->nullable();
            $table->timestampTz('received_at');
            $table->unsignedInteger('size')->default(0);
            $table->boolean('is_seen')->default(false);
            $table->boolean('is_flagged')->default(false);
            $table->boolean('is_answered')->default(false);
            $table->boolean('is_forwarded')->default(false);
            $table->boolean('is_draft')->default(false);
            $table->boolean('is_deleted')->default(false);
            $table->jsonb('keywords')->nullable();
            $table->boolean('has_attachments')->default(false);
            $table->text('preview')->nullable();
            $table->float('junk_score')->nullable();
            $table->string('junk_reason', 32)->nullable();
            $table->string('junk_trained', 8)->nullable();
            $table->text('search_text')->nullable();
            $table->timestampsTz();

            $table->unique(['folder_id', 'uid']);
            $table->index(['folder_id', 'received_at']);
            $table->index(['account_id', 'received_at']);
            $table->index(['account_id', 'message_id']);
        });

        DB::statement("ALTER TABLE messages ADD COLUMN search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', coalesce(search_text, ''))) STORED");
        DB::statement('CREATE INDEX messages_search_vector_index ON messages USING gin (search_vector)');

        Schema::create('message_bodies', function (Blueprint $table) {
            $table->foreignUlid('message_id')->primary()->constrained('messages')->cascadeOnDelete();
            $table->longText('text_body')->nullable();
            $table->longText('html_body')->nullable();
            $table->longText('html_body_remote')->nullable();
            $table->boolean('has_remote_content')->default(false);
            $table->unsignedInteger('tracking_pixels')->default(0);
            $table->jsonb('mismatched_links')->nullable();
            $table->jsonb('parts')->nullable();
            $table->jsonb('calendar')->nullable();
            $table->jsonb('headers')->nullable();
            $table->jsonb('warnings')->nullable();
            $table->jsonb('defects')->nullable();
            $table->string('source_path')->nullable();
            $table->timestampsTz();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('message_bodies');
        Schema::dropIfExists('messages');
    }
};
