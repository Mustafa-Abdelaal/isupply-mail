<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Message rules (R-19), Thunderbird-style: ordered, enabled per rule, all/any conditions, actions,
 * optional "stop processing more rules". Conditions and actions are validated JSON (FilterRequest).
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('mail_filters', function (Blueprint $table) {
            $table->ulid('id')->primary();
            $table->foreignUlid('account_id')->constrained('mail_accounts')->cascadeOnDelete();
            $table->string('name');
            $table->boolean('is_enabled')->default(true);
            $table->unsignedInteger('position')->default(0);
            $table->string('match', 8)->default('all');
            $table->jsonb('conditions');
            $table->jsonb('actions');
            $table->boolean('stop_processing')->default(false);
            $table->timestampsTz();

            $table->index(['account_id', 'position']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('mail_filters');
    }
};
