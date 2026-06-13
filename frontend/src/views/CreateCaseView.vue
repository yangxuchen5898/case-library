<template>
  <div class="create-case-wizard">
    <!-- Mobile step summary -->
    <div class="wizard-rail-mobile">
      <div class="mobile-progress-header">
        <span class="mobile-progress-title">进度</span>
        <span class="mobile-progress-percent">{{ progressPercent }}% 完成</span>
      </div>
      <div class="mobile-progress-bar-track">
        <div class="mobile-progress-bar" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <div class="mobile-steps">
        <div
          v-for="(step, idx) in steps"
          :key="step.id"
          :class="[
            'mobile-step',
            { active: idx === currentStep, completed: idx < currentStep },
          ]"
        >
          <span class="mobile-step-dot" aria-hidden="true">
            <svg v-if="idx < currentStep" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <template v-else>{{ idx + 1 }}</template>
          </span>
          <span class="mobile-step-label">{{ step.label }}</span>
        </div>
      </div>
    </div>

    <!-- Desktop progress rail -->
    <aside class="wizard-rail">
      <div class="rail-header">
        <div class="progress-header">进度</div>
        <div class="progress-text">{{ progressPercent }}% 完成</div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
      </div>
      <nav class="step-list" aria-label="创建步骤">
        <div
          v-for="(step, idx) in steps"
          :key="step.id"
          :class="[
            'step-item',
            { current: idx === currentStep, done: idx < currentStep, todo: idx > currentStep },
          ]"
        >
          <div class="step-icon" aria-hidden="true">
            <svg v-if="idx < currentStep" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <svg v-else-if="idx === currentStep" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <circle cx="12" cy="12" r="10"></circle>
            </svg>
            <template v-else>{{ idx + 1 }}</template>
          </div>
          <div class="step-info">
            <div class="step-title">{{ step.label }}</div>
            <div class="step-desc">
              <template v-if="step.id === 'basic'">填写标题与作者</template>
              <template v-else-if="step.id === 'content'">撰写案例正文</template>
              <template v-else-if="step.id === 'classify'">选择案例分类</template>
              <template v-else-if="step.id === 'review'">智能内容审核</template>
              <template v-else>确认并提交</template>
            </div>
          </div>
        </div>
      </nav>
    </aside>

    <main class="wizard-main">
      <nav class="wizard-breadcrumb">
        <a href="#library">案例库</a>
        <span class="breadcrumb-sep">›</span>
        <span class="breadcrumb-static">创建新案例</span>
        <span class="breadcrumb-sep">›</span>
        <span class="breadcrumb-current">{{ steps[currentStep].label }}</span>
      </nav>

      <h1 class="wizard-title">{{ stepMeta.title }}</h1>
      <p class="wizard-desc">{{ stepMeta.desc }}</p>

      <!-- Unauthenticated notice -->
      <div v-if="!isAuthenticated" class="login-required-card">
        <div class="login-required-icon" aria-hidden="true"></div>
        <h3>请先登录</h3>
        <p>创建案例需要登录账号。请先登录后再继续。</p>
      </div>

      <div v-else class="wizard-form">
        <!-- Step 1: 基本信息 -->
        <template v-if="currentStep === 0">
          <div class="form-section">
            <label class="form-label" for="ccf-title">案例标题 <span class="required" aria-hidden="true">*</span></label>
            <input
              id="ccf-title"
              v-model="form.title"
              type="text"
              class="form-input"
              placeholder="输入具有学术性与引领性的标题"
              :aria-invalid="!!errors.title"
              @blur="touch('title')"
            />
            <p class="form-hint">建议标题长度在 15-30 字之间，包含核心教学知识点。</p>
            <div v-if="errors.title" class="field-error" role="alert">{{ errors.title }}</div>
          </div>

          <div class="form-row">
            <div class="form-section">
              <label class="form-label" for="ccf-author">作者姓名</label>
              <input
                id="ccf-author"
                :value="displayAuthor"
                type="text"
                class="form-input readonly"
                readonly
                aria-describedby="ccf-author-tip"
              />
              <p id="ccf-author-tip" class="form-hint">取自当前登录账号信息</p>
            </div>
            <div class="form-section">
              <label class="form-label" for="ccf-department">
                所属部门/学院 <span class="required" aria-hidden="true">*</span>
              </label>
              <input
                id="ccf-department"
                v-model="form.department"
                type="text"
                class="form-input"
                placeholder="例如：马克思主义学院"
                :aria-invalid="!!errors.department"
                @blur="touch('department')"
              />
              <div v-if="errors.department" class="field-error" role="alert">{{ errors.department }}</div>
            </div>
          </div>

          <div class="tip-card">
            <svg class="tip-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M12 16v-4"></path>
              <path d="M12 8h.01"></path>
            </svg>
            <div>
              <div class="tip-title">编写小贴士</div>
              <div class="tip-text">
                优秀的思政案例应当将价值引领与知识传授有机融合。在"基本信息"阶段，请确保所有参与作者的姓名拼写正确，并使用官方的全称来标注所属学院。
              </div>
            </div>
          </div>
        </template>

        <!-- Step 2: 案例内容 -->
        <template v-if="currentStep === 1">
          <div class="form-section">
            <label class="form-label" for="ccf-content">案例正文 <span class="required" aria-hidden="true">*</span></label>
            <div class="editor-wrapper">
              <div class="editor-toolbar">
                <button type="button" class="toolbar-btn" title="加粗" aria-label="加粗">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/><path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/></svg>
                </button>
                <button type="button" class="toolbar-btn" title="斜体" aria-label="斜体">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="19" y1="4" x2="10" y2="4"/><line x1="14" y1="20" x2="5" y2="20"/><line x1="15" y1="4" x2="9" y2="20"/></svg>
                </button>
                <button type="button" class="toolbar-btn" title="下划线" aria-label="下划线">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"/><line x1="4" y1="21" x2="20" y2="21"/></svg>
                </button>
                <span class="toolbar-divider"></span>
                <button type="button" class="toolbar-btn" title="无序列表" aria-label="无序列表">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                </button>
                <button type="button" class="toolbar-btn" title="有序列表" aria-label="有序列表">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="10" y1="6" x2="21" y2="6"/><line x1="10" y1="12" x2="21" y2="12"/><line x1="10" y1="18" x2="21" y2="18"/><path d="M4 6h1v4"/><path d="M4 10h2"/><path d="M6 18H4c0-1 2-2 2-3s-1-1.5-2-1"/></svg>
                </button>
              </div>
              <textarea
                id="ccf-content"
                v-model="form.content"
                class="editor-textarea"
                rows="14"
                placeholder="请使用 Markdown 格式编写案例正文，建议包含背景、问题、分析、反思等部分。"
                :aria-invalid="!!errors.content"
                @blur="touch('content')"
              ></textarea>
            </div>
            <div class="textarea-meta">
              <span>当前字数：{{ wordCount }}</span>
              <span>预计阅读时间：{{ readingTime }} 分钟</span>
            </div>
            <div v-if="errors.content" class="field-error" role="alert">{{ errors.content }}</div>
          </div>

          <div class="form-section">
            <label class="form-label" for="ccf-source">来源材料</label>
            <textarea
              id="ccf-source"
              v-model="form.source_material"
              class="form-input"
              rows="8"
              placeholder="可粘贴新闻链接、公众号正文、活动记录、访谈纪要或其他支撑材料。"
            ></textarea>
            <p class="form-hint">来源材料会随版本快照保存，公开案例仅展示正文和来源材料，不展示审核批注。</p>
          </div>

          <div class="tip-card">
            <svg class="tip-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M12 16v-4"></path>
              <path d="M12 8h.01"></path>
            </svg>
            <div>
              <div class="tip-title">写作小贴士</div>
              <div class="tip-text">
                优秀的思政案例应当叙事生动、逻辑清晰、价值导向明确。建议在撰写过程中注重真实性与典型性，善用具体数据和场景描写增强说服力。案例字数建议控制在 2000–5000 字之间。
              </div>
            </div>
          </div>
        </template>

        <!-- Step 3: 分类选择 -->
        <template v-if="currentStep === 2">
          <div class="hint-banner">
            <span class="hint-icon" aria-hidden="true"></span>
            <span>不确定分类？可点击右下角 AI 助手，根据已填写内容获取一次本地建议。</span>
          </div>

          <div class="tag-section">
            <div class="tag-section-title">
              案例类型 <span class="required">*</span>
            </div>
            <div class="tag-grid">
              <div
                v-for="(label, key) in constants.case_types"
                :key="key"
                :class="['tag-chip', { selected: form.type === key }]"
                @click="form.type = form.type === key ? '' : key; touch('type')"
                role="button"
                tabindex="0"
                :aria-pressed="form.type === key"
              >
                <div class="tag-checkbox">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </div>
                <span class="tag-label">{{ label }}</span>
              </div>
            </div>
            <p class="form-hint">类型决定案例在库中的展示分类与主要使用场景。</p>
            <div v-if="errors.type" class="field-error" role="alert">{{ errors.type }}</div>
          </div>

          <div class="tag-section">
            <div class="tag-section-title">
              案例主题 <span class="required">*</span>
            </div>
            <div class="tag-grid">
              <div
                v-for="t in constants.themes"
                :key="t"
                :class="['tag-chip', { selected: form.theme === t }]"
                @click="form.theme = form.theme === t ? '' : t; touch('theme')"
                role="button"
                tabindex="0"
                :aria-pressed="form.theme === t"
              >
                <div class="tag-checkbox">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </div>
                <span class="tag-label">{{ t }}</span>
              </div>
            </div>
            <p class="form-hint">主题用于跨类型的关键词聚合与检索。</p>
            <div v-if="errors.theme" class="field-error" role="alert">{{ errors.theme }}</div>
          </div>

          <!-- Transient local helper panel -->
          <div v-if="showHelper" class="helper-panel" role="dialog" aria-modal="true" aria-labelledby="helper-title">
            <div class="helper-header">
              <span id="helper-title">AI 分类助手（本地建议）</span>
              <button type="button" class="helper-close-btn" aria-label="关闭" @click="showHelper = false">×</button>
            </div>
            <div class="helper-body">
              <p class="helper-desc">请输入您想咨询的问题，例如："帮我推荐案例类型和主题"。</p>
              <input
                v-model="helperInput"
                type="text"
                placeholder="输入问题…"
                @keyup.enter="runHelper"
              />
              <button type="button" class="btn-helper" :disabled="!helperInput.trim()" @click="runHelper">
                获取建议
              </button>
              <div v-if="helperResponse" class="helper-response" role="status" aria-live="polite">
                {{ helperResponse }}
              </div>
            </div>
          </div>

          <button
            type="button"
            class="fab-helper"
            aria-label="打开 AI 分类助手"
            @click="showHelper = true"
          >
            <span class="helper-label-desktop">AI</span>
            <span class="helper-label-mobile">AI 建议</span>
          </button>
        </template>

        <!-- Step 4: AI 审核 -->
        <template v-if="currentStep === 3">
          <div class="review-panel">
            <div class="review-panel-header">
              <div class="review-panel-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
              </div>
              <div class="review-panel-title-wrap">
                <div class="review-panel-title">AI 自查</div>
                <div class="review-panel-subtitle">生成只读审核版本，并按段落给出作者侧修改建议</div>
              </div>
            </div>
            <div class="review-panel-body">
              <div class="review-header">
                <span class="review-badge">AI 自查</span>
                <span class="review-percent">{{ aiReviewProgress }}% 已完成</span>
              </div>
              <div class="review-progress-track">
                <div class="review-progress-bar" :style="{ width: aiReviewProgress + '%' }"></div>
              </div>
              <p class="review-note">
                以下结果来自后端 AI 自查接口，仅作为作者提交前参考，不代表专家审核结论。
              </p>

              <div v-if="aiPromptLoadError" class="ai-unavailable-banner" role="status">
                {{ aiPromptLoadError }}
              </div>

              <div class="ai-review-toolbar">
                <button
                  type="button"
                  class="btn-primary"
                  :disabled="aiRunningAll || !canRunAiReview"
                  @click="runAllAiReviews"
                >
                  {{ aiRunningAll ? '生成中…' : '生成只读审核版本' }}
                </button>
                <span class="ai-toolbar-note">
                  需要先填写标题、正文、类型和主题。AI 会生成段落级批注版本，不会给出审批结论。
                </span>
              </div>

              <div class="review-grid">
                <div v-for="item in aiReviewItems" :key="item.id" class="review-card ai-review-card">
                  <div class="review-card-top">
                    <div>
                      <div class="review-card-title">{{ item.name }}</div>
                      <div class="review-card-desc">{{ item.description }}</div>
                    </div>
                    <span class="ai-status-pill" :class="aiReviewState[item.id].status">
                      {{ aiStatusLabel(aiReviewState[item.id].status) }}
                    </span>
                  </div>

                  <div v-if="aiReviewState[item.id].status === 'idle'" class="ai-placeholder">
                    尚未运行。点击下方按钮获取作者侧自查建议。
                  </div>

                  <div v-else-if="aiReviewState[item.id].status === 'loading'" class="ai-placeholder">
                    正在请求后端 AI 自查…
                  </div>

                  <div v-else-if="aiReviewState[item.id].status === 'error'" class="ai-error">
                    {{ aiReviewState[item.id].error }}
                  </div>

                  <div v-else class="ai-result">
                    <div v-if="aiReviewState[item.id].parsed" class="ai-result-body">
                      <div v-if="aiReviewState[item.id].parsed.detail" class="ai-detail">
                        {{ aiReviewState[item.id].parsed.detail }}
                      </div>
                      <div v-if="aiReviewState[item.id].parsed.score != null" class="ai-score">
                        评分 {{ aiReviewState[item.id].parsed.score }}
                      </div>
                      <ul
                        v-if="Array.isArray(aiReviewState[item.id].parsed.suggestions) && aiReviewState[item.id].parsed.suggestions.length"
                        class="ai-suggestions"
                      >
                        <li v-for="suggestion in aiReviewState[item.id].parsed.suggestions" :key="suggestion">
                          {{ suggestion }}
                        </li>
                      </ul>
                      <ul
                        v-if="Array.isArray(aiReviewState[item.id].comments) && aiReviewState[item.id].comments.length && !hasAnnotationPreview(aiReviewState[item.id])"
                        class="ai-suggestions"
                      >
                        <li v-for="comment in aiReviewState[item.id].comments" :key="comment.id || comment.message">
                          {{ comment.paragraph_id }}：{{ comment.message }}
                        </li>
                      </ul>
                      <div
                        v-if="hasAnnotationPreview(aiReviewState[item.id])"
                        class="ai-annotation-preview"
                      >
                        <div class="annotation-copy">
                          <strong>版本正文</strong>
                          <p
                            v-for="paragraph in aiReviewState[item.id].version.paragraphs"
                            :key="paragraph.paragraph_id"
                            :class="{ highlighted: commentsForParagraph(aiReviewState[item.id], paragraph.paragraph_id).length }"
                          >
                            <span>{{ paragraph.paragraph_id }}</span>
                            {{ paragraph.text }}
                          </p>
                        </div>
                        <aside class="annotation-comments" aria-label="AI 段落批注">
                          <strong>AI 批注</strong>
                          <div
                            v-for="comment in aiReviewState[item.id].comments"
                            :key="comment.id || `${comment.paragraph_id}-${comment.message}`"
                            class="annotation-comment"
                          >
                            <strong>{{ comment.paragraph_id }}</strong>
                            <p>{{ comment.message }}</p>
                            <small v-if="comment.suggestion">{{ comment.suggestion }}</small>
                          </div>
                        </aside>
                      </div>
                    </div>
                    <pre v-else class="ai-answer">{{ aiReviewState[item.id].answer }}</pre>
                    <div v-if="aiReviewState[item.id].parse_error" class="ai-parse-warning">
                      {{ aiReviewState[item.id].parse_error }}
                    </div>
                  </div>

                  <button
                    type="button"
                    class="btn-secondary ai-run-btn"
                    :disabled="aiReviewState[item.id].status === 'loading' || !canRunAiReview"
                    @click="runAiReview(item.id)"
                  >
                    {{ aiReviewState[item.id].status === 'loading' ? '运行中…' : '运行此项' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- Step 5: 提交确认 -->
        <template v-if="currentStep === 4">
          <div class="summary-card">
            <div class="summary-header">
              <div class="summary-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
              </div>
              <div>
                <div class="summary-title">案例信息汇总</div>
                <div class="summary-subtitle">提交前请再次确认以下内容</div>
              </div>
            </div>

            <div class="field-row">
              <div class="field-label">案例标题</div>
              <div class="field-value">{{ form.title || '—（请填写）' }}</div>
            </div>
            <div class="field-row">
              <div class="field-label">作者姓名</div>
              <div class="field-value">{{ displayAuthor || '—' }}</div>
            </div>
            <div class="field-row">
              <div class="field-label">所属学院</div>
              <div class="field-value">{{ form.department || '—' }}</div>
            </div>
            <div class="field-row">
              <div class="field-label">案例类型</div>
              <div class="field-value">
                <span v-if="form.type" class="field-tag">{{ constants.case_types[form.type] }}</span>
                <template v-else>—</template>
              </div>
            </div>
            <div class="field-row">
              <div class="field-label">案例主题</div>
              <div class="field-value">
                <span v-if="form.theme" class="field-tag">{{ form.theme }}</span>
                <template v-else>—</template>
              </div>
            </div>
            <div class="field-row">
              <div class="field-label">案例正文</div>
              <div class="field-value">{{ contentSummary }}</div>
            </div>
          </div>

          <div class="confirm-box">
            <div class="confirm-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
            </div>
            <div class="confirm-title">准备提交</div>
            <div class="confirm-text">
              提交后案例将进入专家人工审核流程，请耐心等待。
            </div>
          </div>

          <div class="tip-card">
            <svg class="tip-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M12 16v-4"></path>
              <path d="M12 8h.01"></path>
            </svg>
            <div>
              <div class="tip-title">提交后须知</div>
              <div class="tip-text">
                案例提交后不可修改，如需调整请在审核结果出具前撤回并重新编辑。审核期间您可以在"我的提交"中查看当前进度。
              </div>
            </div>
          </div>
        </template>

        <!-- Bottom actions -->
        <div class="wizard-actions">
          <div class="wizard-actions-left">
            <template v-if="currentStep > 0 && currentStep < 4">
              <button type="button" class="btn-secondary" @click="prevStep">上一步</button>
            </template>
            <template v-if="currentStep < 4">
              <button type="button" class="btn-secondary" :disabled="saving" @click="handleSaveDraft">
                {{ saving ? '保存中…' : '保存草稿' }}
              </button>
            </template>
            <template v-if="currentStep === 4">
              <button type="button" class="btn-secondary" @click="currentStep = 1">返回修改</button>
            </template>
          </div>
          <div class="wizard-actions-right">
            <template v-if="currentStep < 4">
              <button type="button" class="btn-primary" @click="nextStep">
                继续 <span class="arrow" aria-hidden="true">→</span>
              </button>
            </template>
            <template v-if="currentStep === 4">
              <button
                type="button"
                class="btn-primary"
                :disabled="submitting || !canSubmit"
                @click="handleFormalSubmit"
              >
                <span>{{ submitting ? '提交中…' : '确认提交' }}</span>
                <svg class="icon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                  <path fill="currentColor" d="M2 21l21-9L2 3v7l15 2-15 2v7z"></path>
                </svg>
              </button>
            </template>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from "vue";
import { currentUser, isLoggedIn } from "../api/auth.js";
import {
  fetchCaseConstants,
  createCase,
  updateCase,
  submitCaseById,
} from "../api/cases.js";
import { listPrompts, runParagraphReview } from "../api/ai.js";
import { notify } from "../utils/toast.js";

const DRAFT_KEY = "case_library_create_case_draft";

const steps = [
  { id: "basic", label: "基本信息" },
  { id: "content", label: "案例内容" },
  { id: "classify", label: "分类选择" },
  { id: "review", label: "提交前自查" },
  { id: "confirm", label: "提交确认" },
];

const currentStep = ref(0);
const saving = ref(false);
const submitting = ref(false);
const caseId = ref(null);

const form = reactive({
  title: "",
  author: "",
  department: "",
  content: "",
  source_material: "",
  type: "",
  theme: "",
});

const touched = reactive({
  title: false,
  department: false,
  content: false,
  type: false,
  theme: false,
});

const constants = reactive({
  case_types: {
    TYPE_A: "思政课教学案例",
    TYPE_B: "课程思政共享资源案例",
    TYPE_C: "实践育人案例",
  },
  themes: ["强国建设", "实践育人", "数字赋能", "铸魂育人"],
  statuses: {
    draft: "草稿",
    pending_review: "待审核",
    approved: "已通过",
    needs_revision: "退回修改",
  },
});

const showHelper = ref(false);
const helperInput = ref("");
const helperResponse = ref("");
const aiPromptLoadError = ref("");
const aiRunningAll = ref(false);
const latestReviewVersionId = ref(null);

const DEFAULT_AI_REVIEW_ITEMS = [
  {
    id: "alpha/paragraph-review",
    name: "段落批注自查",
    description: "生成只读版本，并按段落给出作者侧修改建议。",
    variables: ["title", "content", "source_material", "type", "theme"],
  },
];

const aiReviewItems = ref([...DEFAULT_AI_REVIEW_ITEMS]);
const aiReviewState = reactive(
  Object.fromEntries(
    DEFAULT_AI_REVIEW_ITEMS.map((item) => [
      item.id,
      {
        status: "idle",
        answer: "",
        parsed: null,
        parse_error: null,
        error: "",
        comments: [],
        version: null,
      },
    ])
  )
);

const displayAuthor = computed(() => {
  const user = currentUser();
  return user?.nickname || user?.username || form.author || "";
});

const wordCount = computed(() => {
  const text = form.content || "";
  // Simple CJK + word token count
  const cjk = (text.match(/[一-龥]/g) || []).length;
  const words = (text.replace(/[一-龥]/g, "").match(/\b[a-zA-Z0-9_]+\b/g) || []).length;
  return cjk + words;
});

const readingTime = computed(() => {
  const wpm = 300;
  return Math.max(1, Math.ceil(wordCount.value / wpm));
});

const contentSummary = computed(() => {
  const text = form.content || "";
  if (!text) return "未填写";
  const snippet = text.replace(/\s+/g, " ").slice(0, 60);
  return text.length > 60 ? snippet + "…" : snippet;
});

const isAuthenticated = computed(() => isLoggedIn());

const progressPercent = computed(() => {
  return Math.round(((currentStep.value + 1) / steps.length) * 100);
});

const stepMeta = computed(() => {
  const metas = [
    { title: "填写基本信息", desc: "完善案例标题、作者与所属部门，为后续编写打好基础。" },
    { title: "编写案例内容", desc: "在下方编辑器中撰写案例正文，支持 Markdown 格式。" },
    { title: "选择案例分类", desc: "选择案例类型与主题，便于检索与推荐。" },
    { title: "提交前自查", desc: "根据已填写内容进行自查，确认必填项完整后再提交。" },
    { title: "确认并提交", desc: "核对填写内容，确认后提交至专家审核。" },
  ];
  return metas[currentStep.value];
});

const errors = computed(() => {
  const e = {};
  if (touched.title && !form.title.trim()) e.title = "请输入案例标题";
  if (touched.department && !form.department.trim()) e.department = "请输入所属部门/学院";
  if (touched.content && !form.content.trim()) e.content = "请输入案例正文";
  if (touched.type && !form.type) e.type = "请选择案例类型";
  if (touched.theme && !form.theme) e.theme = "请选择案例主题";
  return e;
});

const checklist = computed(() => {
  return {
    structure: !!(form.title.trim() && form.department.trim() && form.content.trim()),
    classification: !!(form.type && form.theme),
    expression: form.content.trim().length >= 50 && form.title.trim().length >= 4,
  };
});

const reviewScore = computed(() => {
  let score = 0;
  if (form.title.trim()) score += 20;
  if (form.department.trim()) score += 15;
  if (form.content.trim()) score += 25;
  if (form.type) score += 20;
  if (form.theme) score += 20;
  return score;
});

const canSubmit = computed(() => {
  return (
    !!form.title.trim() &&
    !!form.department.trim() &&
    !!form.content.trim() &&
    !!form.type &&
    !!form.theme
  );
});

const canRunAiReview = computed(() => {
  return !!(
    form.title.trim() &&
    form.content.trim() &&
    form.type &&
    form.theme &&
    isAuthenticated.value
  );
});

const aiReviewProgress = computed(() => {
  const total = aiReviewItems.value.length || 1;
  const done = aiReviewItems.value.filter((item) => aiReviewState[item.id].status === "success").length;
  return Math.round((done / total) * 100);
});

function touch(field) {
  touched[field] = true;
}

function validateStep(step) {
  if (step === 0) {
    touched.title = true;
    touched.department = true;
    return !errors.value.title && !errors.value.department;
  }
  if (step === 1) {
    touched.content = true;
    return !errors.value.content;
  }
  if (step === 2) {
    touched.type = true;
    touched.theme = true;
    return !errors.value.type && !errors.value.theme;
  }
  return true;
}

function nextStep() {
  if (!validateStep(currentStep.value)) return;
  if (currentStep.value === 3 && hasAiReviewWarning() && !confirmAiReviewWarning()) {
    return;
  }
  if (currentStep.value < steps.length - 1) {
    currentStep.value += 1;
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value -= 1;
  }
}

function buildPayload(status) {
  const payload = {
    title: form.title.trim(),
    content: form.content.trim(),
    source_material: form.source_material.trim(),
    department: form.department.trim(),
    type: form.type,
    theme: form.theme,
    status,
  };
  appendAiReviewsPayload(payload);
  return payload;
}

function appendAiReviewsPayload(payload) {
  const reviews = collectAiReviews();
  if (reviews.length) {
    payload.ai_reviews = JSON.stringify(reviews);
  }
  return payload;
}

async function handleSaveDraft() {
  if (!isAuthenticated.value) {
    notify("请先登录后再保存草稿", "error");
    return;
  }
  saving.value = true;
  try {
    if (caseId.value) {
      const payload = {
        title: form.title.trim(),
        content: form.content.trim(),
        source_material: form.source_material.trim(),
        author: displayAuthor.value,
        department: form.department.trim(),
        type: form.type,
        theme: form.theme,
        change_reason: "保存草稿",
      };
      appendAiReviewsPayload(payload);
      await updateCase(caseId.value, payload);
    } else {
      const res = await createCase(buildPayload("draft"));
      if (res && res.case_id) {
        caseId.value = res.case_id;
      }
    }
    persistDraft();
    notify("草稿已保存", "success");
  } catch (err) {
    notify(err.message || "保存草稿失败，请稍后重试", "error");
  } finally {
    saving.value = false;
  }
}

async function handleFormalSubmit() {
  if (!canSubmit.value) {
    notify("请完善所有必填项后再提交", "error");
    return;
  }
  if (!isAuthenticated.value) {
    notify("请先登录后再提交案例", "error");
    return;
  }
  submitting.value = true;
  try {
    if (caseId.value) {
      // Update existing draft with latest form data before submitting
      const payload = {
        title: form.title.trim(),
        content: form.content.trim(),
        source_material: form.source_material.trim(),
        author: displayAuthor.value,
        department: form.department.trim(),
        type: form.type,
        theme: form.theme,
        change_reason: "提交前更新",
      };
      appendAiReviewsPayload(payload);
      await updateCase(caseId.value, payload);
      await submitCaseById(caseId.value, latestReviewVersionId.value);
    } else {
      const res = await createCase(buildPayload("draft"));
      if (res && res.case_id) {
        caseId.value = res.case_id;
        await submitCaseById(caseId.value, latestReviewVersionId.value);
      }
    }
    clearDraft();
    notify("案例提交成功，请等待专家审核", "success");
    resetForm();
    currentStep.value = 0;
  } catch (err) {
    notify(err.message || "提交失败，请稍后重试", "error");
  } finally {
    submitting.value = false;
  }
}

function persistDraft() {
  try {
    const user = currentUser();
    const payload = {
      username: user?.username || "",
      form: {
        title: form.title,
        author: form.author,
        department: form.department,
        content: form.content,
        source_material: form.source_material,
        type: form.type,
        theme: form.theme,
      },
      caseId: caseId.value,
      latestReviewVersionId: latestReviewVersionId.value,
      savedAt: Date.now(),
    };
    localStorage.setItem(DRAFT_KEY, JSON.stringify(payload));
  } catch {
    // Ignore storage errors
  }
}

function loadDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    const user = currentUser();
    const sameUser = !saved.username || saved.username === user?.username;
    if (saved && saved.form) {
      Object.assign(form, saved.form);
    }
    if (sameUser && saved && saved.caseId) {
      caseId.value = saved.caseId;
    }
    if (sameUser && saved && saved.latestReviewVersionId) {
      latestReviewVersionId.value = saved.latestReviewVersionId;
    }
    if (!sameUser) {
      caseId.value = null;
      latestReviewVersionId.value = null;
    }
  } catch {
    // Ignore malformed storage
  }
}

function clearDraft() {
  try {
    localStorage.removeItem(DRAFT_KEY);
  } catch {
    // Ignore
  }
}

function resetForm() {
  form.title = "";
  form.author = "";
  form.department = "";
  form.content = "";
  form.source_material = "";
  form.type = "";
  form.theme = "";
  caseId.value = null;
  latestReviewVersionId.value = null;
  currentStep.value = 0;
  touched.title = false;
  touched.department = false;
  touched.content = false;
  touched.type = false;
  touched.theme = false;
  for (const item of aiReviewItems.value) {
    resetAiReviewItem(item.id);
  }
}

function ensureAiReviewState(promptId) {
  if (!aiReviewState[promptId]) {
    aiReviewState[promptId] = {
      status: "idle",
      answer: "",
      parsed: null,
      parse_error: null,
      error: "",
      comments: [],
      version: null,
    };
  }
  return aiReviewState[promptId];
}

function resetAiReviewItem(promptId) {
  const state = ensureAiReviewState(promptId);
  state.status = "idle";
  state.answer = "";
  state.parsed = null;
  state.parse_error = null;
  state.error = "";
  state.comments = [];
  state.version = null;
}

function commentsForParagraph(state, paragraphId) {
  return (state.comments || []).filter((comment) => comment.paragraph_id === paragraphId);
}

function hasAnnotationPreview(state) {
  return Boolean(state?.version?.paragraphs?.length && state?.comments?.length);
}

function aiStatusLabel(status) {
  if (status === "loading") return "运行中";
  if (status === "success") return "已完成";
  if (status === "error") return "不可用";
  return "待运行";
}

function buildAiVariables() {
  return {
    title: form.title.trim(),
    content: form.content.trim(),
    source_material: form.source_material.trim(),
    type: form.type,
    theme: form.theme,
  };
}

async function ensureDraftCase() {
  const payload = buildPayload("draft");
  if (caseId.value) {
    await updateCase(caseId.value, {
      ...payload,
      author: displayAuthor.value,
      change_reason: "AI 审核前更新",
    });
    return caseId.value;
  }
  const res = await createCase(payload);
  if (!res || !res.case_id) {
    throw new Error("保存草稿失败，无法创建 AI 审核版本");
  }
  caseId.value = res.case_id;
  persistDraft();
  return caseId.value;
}

function collectAiReviews() {
  return aiReviewItems.value
    .map((item) => {
      const state = aiReviewState[item.id];
      if (!state || state.status !== "success") return null;
      return {
        prompt_id: item.id,
        name: item.name,
        answer: state.answer,
        parsed: state.parsed,
        parse_error: state.parse_error,
        reviewed_at: new Date().toISOString(),
      };
    })
    .filter(Boolean)
    .slice(-3);
}

function hasAiReviewWarning() {
  return aiReviewItems.value.some((item) => {
    const parsed = aiReviewState[item.id]?.parsed;
    if (!parsed || typeof parsed !== "object") return false;
    if (parsed.pass === false) return true;
    if (parsed.score != null) {
      const score = Number(parsed.score);
      return Number.isFinite(score) && score < 70;
    }
    return false;
  });
}

function confirmAiReviewWarning() {
  notify(
    "AI 自查提示当前案例可能还需要修改；结果仅供参考，不会阻止提交专家审核。",
    "info"
  );
  return true;
}

async function loadAiPrompts() {
  aiPromptLoadError.value = "";
  try {
    const prompts = await listPrompts("alpha");
    const mapped = DEFAULT_AI_REVIEW_ITEMS.map((fallback) => {
      const prompt = prompts.find((item) => item.id === fallback.id);
      return prompt
        ? {
            id: prompt.id,
            name: prompt.name || fallback.name,
            description: prompt.description || fallback.description,
            variables: prompt.variables || fallback.variables,
          }
        : fallback;
    });
    aiReviewItems.value = mapped;
    for (const item of mapped) ensureAiReviewState(item.id);
  } catch (err) {
    aiPromptLoadError.value = err.message || "AI 自查提示词暂不可用";
  }
}

async function runAiReview(promptId) {
  if (!canRunAiReview.value) {
    aiPromptLoadError.value = "请先登录并填写标题、正文、类型和主题后再运行 AI 自查。";
    return;
  }
  const state = ensureAiReviewState(promptId);
  state.status = "loading";
  state.answer = "";
  state.parsed = null;
  state.parse_error = null;
  state.error = "";
  state.comments = [];
  state.version = null;
  try {
    const activeCaseId = await ensureDraftCase();
    const data = await runParagraphReview(activeCaseId);
    const result = data?.data || {};
    const version = result.version || {};
    latestReviewVersionId.value = version.id || null;
    state.status = "success";
    state.comments = result.comments || [];
    state.version = version || null;
    state.answer = state.comments.map((comment) => comment.message).join("\n") || "AI 未返回段落批注。";
    const summarySuggestions = Array.from(new Set(result.summary?.suggested_next_steps || []));
    state.parsed = {
      detail: `已生成 v${version.version_number || ""} 只读审核版本，包含 ${state.comments.length} 条段落批注。`,
      suggestions: hasAnnotationPreview(state) ? summarySuggestions : summarySuggestions.concat(
        state.comments.map((comment) => comment.suggestion).filter(Boolean)
      ),
    };
    state.parse_error = null;
    persistDraft();
  } catch (err) {
    state.status = "error";
    state.error = err.data?.detail || err.message || "AI 自查暂不可用";
  }
}

async function runAllAiReviews() {
  if (!canRunAiReview.value || aiRunningAll.value) return;
  aiRunningAll.value = true;
  try {
    await runAiReview(aiReviewItems.value[0]?.id || DEFAULT_AI_REVIEW_ITEMS[0].id);
  } finally {
    aiRunningAll.value = false;
  }
}

function runHelper() {
  const q = helperInput.value.trim();
  if (!q) return;
  const text = (form.title + " " + form.content).toLowerCase();
  let type = "TYPE_A";
  let theme = "铸魂育人";
  if (text.includes("课程") || text.includes("教学")) type = "TYPE_A";
  if (text.includes("共享") || text.includes("资源")) type = "TYPE_B";
  if (text.includes("实践") || text.includes("活动") || text.includes("社会")) type = "TYPE_C";
  if (text.includes("强国")) theme = "强国建设";
  else if (text.includes("实践") || text.includes("育人")) theme = "实践育人";
  else if (text.includes("数字") || text.includes("技术") || text.includes("网络")) theme = "数字赋能";
  const typeLabel = constants.case_types[type] || type;
  helperResponse.value = `根据当前内容，建议类型为「${typeLabel}」，主题选择「${theme}」。您也可以结合自身判断手动调整。`;
}

onMounted(async () => {
  const user = currentUser();
  form.author = user?.nickname || user?.username || "";
  loadDraft();
  try {
    const data = await fetchCaseConstants();
    if (data) {
      if (data.case_types) constants.case_types = data.case_types;
      if (Array.isArray(data.themes)) constants.themes = data.themes;
      if (data.statuses) constants.statuses = data.statuses;
    }
  } catch {
    // Safe fallbacks already set
  }
  if (isAuthenticated.value) {
    await loadAiPrompts();
  }
});

// Persist form changes locally as the user types
watch(
  () => ({
    title: form.title,
    author: form.author,
    department: form.department,
    content: form.content,
    source_material: form.source_material,
    type: form.type,
    theme: form.theme,
  }),
  () => persistDraft(),
  { deep: true }
);

watch(currentStep, (step) => {
  if (step === 3 && isAuthenticated.value) {
    loadAiPrompts();
  }
});

// Reset scroll to the top of the page whenever the wizard step changes
watch(currentStep, () => {
  nextTick(() => {
    const wizardTop = document.querySelector(".create-case-wizard")?.getBoundingClientRect().top || 0;
    const headerHeight = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--header-height")) || 0;
    window.scrollTo({
      top: Math.max(0, window.scrollY + wizardTop - headerHeight),
      behavior: "auto",
    });
  });
});
</script>
<style scoped>
.create-case-wizard {
  /* Design tokens */
  --accent: #c41e3a;
  --accent-soft: #fef2f2;
  --accent-dark: #a01830;
  --success: #22c55e;
  --fg: #1a1a1a;
  --muted: #666666;
  --border: #e5e5e5;
  --gray-bg: #f5f5f5;
  --gray-bg-dark: #f0f0f0;
  --gray-border: #e5e5e5;
  --gray-text: #bbb;
  --gray-text-light: #ccc;
  --gray-hint: #999;
  --gray-input: #f9f9f9;
  --font-display: 'Noto Serif SC', 'Source Han Serif SC', 'STSong', 'SimSun', 'Iowan Old Style', 'Charter', Georgia, serif;

  display: flex;
  flex-direction: column;
  min-height: calc(100vh - var(--header-height));
  background: #ffffff;
}

/* Desktop rail */
.wizard-rail {
  display: none;
  width: 260px;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid var(--border);
  padding: 32px 20px;
}

.rail-header {
  margin-bottom: 24px;
}

.progress-header {
  font-size: 12px;
  font-weight: 600;
  color: var(--fg);
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.progress-bar {
  height: 4px;
  background: var(--gray-bg-dark);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 11px;
  color: var(--muted);
}

.step-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  position: relative;
  transition: background 0.15s ease;
}

.step-item.current {
  background: var(--accent-soft);
}

.step-item.current::before {
  content: '';
  position: absolute;
  left: 0;
  top: 12px;
  bottom: 12px;
  width: 3px;
  background: var(--accent);
  border-radius: 0 2px 2px 0;
}

.step-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 50%;
  margin-top: 1px;
  font-size: 11px;
  font-weight: 700;
}

.step-item.done .step-icon {
  background: var(--accent);
  color: #fff;
}

.step-item.current .step-icon {
  background: var(--accent-soft);
  color: var(--accent);
  border: 1.5px solid var(--accent);
}

.step-item.todo .step-icon {
  background: var(--gray-bg);
  color: var(--gray-text);
  border: 1.5px solid var(--gray-border);
}

.step-icon svg {
  width: 12px;
  height: 12px;
}

.step-info {
  flex: 1;
}

.step-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--fg);
  line-height: 1.4;
}

.step-item.current .step-title {
  color: var(--accent);
  font-weight: 600;
}

.step-item.todo .step-title {
  color: var(--gray-text);
}

.step-desc {
  font-size: 11px;
  color: var(--muted);
  margin-top: 2px;
}

.step-item.todo .step-desc {
  color: var(--gray-text-light);
}

/* Mobile rail */
.wizard-rail-mobile {
  display: block;
  background: #ffffff;
  border-bottom: 1px solid var(--border);
  padding: 16px;
}

.mobile-progress-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8px;
}

.mobile-progress-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--fg);
}

.mobile-progress-percent {
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
}

.mobile-progress-bar-track {
  height: 4px;
  background: var(--gray-bg-dark);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 12px;
}

.mobile-progress-bar {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.mobile-steps {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
}

.mobile-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: var(--gray-text);
  flex: 1;
  min-width: 0;
}

.mobile-step.active {
  color: var(--accent);
}

.mobile-step.completed {
  color: var(--accent);
}

.mobile-step-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1.5px solid currentColor;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

.mobile-step.completed .mobile-step-dot {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.mobile-step-dot svg {
  width: 12px;
  height: 12px;
}

.mobile-step-label {
  font-size: 11px;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

/* Main workspace */
.wizard-main {
  flex: 1;
  width: 100%;
  min-width: 0;
  padding: 32px 16px 48px;
  max-width: 1100px;
  margin: 0 auto;
}

.wizard-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 24px;
}

.wizard-breadcrumb a {
  color: var(--muted);
  text-decoration: none;
  transition: color 0.15s;
}

.wizard-breadcrumb a:hover {
  color: var(--fg);
}

.breadcrumb-sep {
  color: var(--gray-text-light);
}

.breadcrumb-current {
  color: var(--accent);
  font-weight: 500;
}

.breadcrumb-static {
  color: var(--muted);
}

.wizard-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--fg);
  margin: 0 0 8px;
  letter-spacing: 1px;
}

.wizard-desc {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.7;
  margin: 0 0 32px;
}

.wizard-form {
  /* Content sits directly on the white background */
}

.form-section {
  margin-bottom: 28px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--fg);
  margin-bottom: 8px;
}

.form-label .required {
  color: var(--accent);
  margin-left: 2px;
}

.form-input,
input[type="text"],
select,
textarea {
  width: 100%;
  padding: 11px 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #ffffff;
  font-size: 14px;
  color: var(--fg);
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  font-family: inherit;
}

.form-input::placeholder,
input[type="text"]::placeholder,
select::placeholder,
textarea::placeholder {
  color: var(--gray-text);
}

.form-input:focus,
input[type="text"]:focus,
select:focus,
textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.form-input.readonly,
input.readonly {
  background: var(--gray-bg);
  color: var(--muted);
}

.form-hint {
  font-size: 11px;
  color: var(--gray-hint);
  margin-top: 6px;
}

.field-error {
  margin-top: 6px;
  font-size: 12px;
  color: var(--accent);
  background: var(--accent-soft);
  padding: 6px 8px;
  border-radius: 4px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
}

/* Tip card */
.tip-card {
  display: flex;
  gap: 12px;
  background: var(--accent-soft);
  border-radius: 8px;
  padding: 16px 20px;
  margin: 24px 0;
}

.tip-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: var(--accent);
  margin-top: 2px;
}

.tip-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--fg);
  margin-bottom: 4px;
}

.tip-text {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.7;
}

/* Buttons */
.wizard-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}

.wizard-actions-left {
  display: flex;
  gap: 12px;
}

.wizard-actions-right {
  display: flex;
  gap: 12px;
}

.btn-primary,
.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.btn-primary:hover {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.btn-secondary {
  background: #fff;
  color: var(--fg);
  border-color: var(--border);
}

.btn-secondary:hover {
  border-color: var(--fg);
  background: var(--gray-bg);
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary svg,
.btn-secondary svg {
  width: 14px;
  height: 14px;
}

.arrow {
  margin-left: 2px;
}

/* Step 2 editor */
.editor-wrapper {
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
  margin-bottom: 8px;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: var(--gray-bg);
  border-bottom: 1px solid var(--border);
}

.toolbar-btn {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.toolbar-btn:hover {
  background: var(--gray-bg-dark);
  color: var(--fg);
}

.toolbar-btn svg {
  width: 16px;
  height: 16px;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: var(--border);
  margin: 0 4px;
}

.editor-textarea {
  width: 100%;
  min-height: 320px;
  padding: 16px;
  border: none;
  background: #fff;
  font-size: 14px;
  line-height: 1.8;
  resize: vertical;
  outline: none;
}

.editor-textarea::placeholder {
  color: var(--gray-text);
}

#ccf-source {
  min-height: 180px;
}

.textarea-meta {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--gray-hint);
}

/* Step 3 hint banner */
.hint-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: #fefce8;
  border: 1px solid #fde047;
  border-radius: 6px;
  margin-bottom: 18px;
  font-size: 13px;
  color: #713f12;
}

.hint-icon {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid currentColor;
  position: relative;
  flex-shrink: 0;
}

.hint-icon::before,
.hint-icon::after {
  content: '';
  position: absolute;
  background: currentColor;
  border-radius: 1px;
}

.hint-icon::before {
  left: 7px;
  top: 3px;
  width: 2px;
  height: 8px;
}

.hint-icon::after {
  left: 7px;
  top: 12px;
  width: 2px;
  height: 2px;
}

/* Tag chips */
.tag-section {
  margin-bottom: 32px;
}

.tag-section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--fg);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tag-section-title .required {
  color: var(--accent);
  font-size: 12px;
  font-weight: 500;
}

.tag-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.tag-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}

.tag-chip:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.tag-chip.selected {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.tag-checkbox {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  border-radius: 50%;
  border: 1.5px solid var(--gray-text-light);
  display: grid;
  place-items: center;
  transition: all 0.15s ease;
}

.tag-chip.selected .tag-checkbox {
  background: var(--accent);
  border-color: var(--accent);
}

.tag-checkbox svg {
  width: 10px;
  height: 10px;
  color: #fff;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.tag-chip.selected .tag-checkbox svg {
  opacity: 1;
}

.tag-label {
  font-size: 13px;
  color: var(--fg);
  line-height: 1.4;
}

/* Helper panel */
.helper-panel {
  position: fixed;
  right: 16px;
  bottom: 80px;
  width: min(92vw, 360px);
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  z-index: 110;
}

.helper-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
  font-weight: 700;
  color: var(--fg);
}

.helper-close-btn {
  background: transparent;
  border: 0;
  font-size: 20px;
  line-height: 1;
  color: var(--gray-hint);
  cursor: pointer;
}

.helper-body {
  padding: 14px;
}

.helper-desc {
  margin: 0 0 10px;
  font-size: 12px;
  color: var(--muted);
}

.helper-body input[type="text"] {
  margin-bottom: 10px;
}

.btn-helper {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  background: var(--accent);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.btn-helper:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.helper-response {
  margin-top: 10px;
  padding: 10px;
  background: var(--gray-bg);
  border-radius: 6px;
  font-size: 13px;
  color: var(--fg);
  line-height: 1.5;
}

.fab-helper {
  position: fixed;
  right: 16px;
  bottom: 24px;
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: var(--accent);
  color: #fff;
  border: 0;
  font-size: 20px;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(196, 30, 58, 0.25);
  z-index: 105;
}

.helper-label-mobile {
  display: none;
}

/* Review panel */
.review-panel {
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #fff;
  overflow: hidden;
  margin-bottom: 24px;
}

.review-panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
}

.review-panel-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--accent-soft);
  color: var(--accent);
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.review-panel-icon svg {
  width: 20px;
  height: 20px;
}

.review-panel-title-wrap {
  flex: 1;
}

.review-panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--fg);
  margin-bottom: 2px;
}

.review-panel-subtitle {
  font-size: 12px;
  color: var(--muted);
}

.review-panel-body {
  padding: 24px;
}

.review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.review-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 4px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
}

.review-percent {
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
}

.review-progress-track {
  height: 8px;
  background: var(--accent-soft);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.review-progress-bar {
  height: 100%;
  background: var(--accent);
  border-radius: 4px;
}

.review-note {
  font-size: 13px;
  color: var(--muted);
  margin: 0 0 18px;
}

.ai-unavailable-banner {
  padding: 12px 14px;
  border: 1px solid #f59e0b;
  border-radius: 6px;
  background: #fffbeb;
  color: #92400e;
  font-size: 13px;
  margin-bottom: 14px;
}

.ai-review-toolbar {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 16px;
}

.ai-toolbar-note {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}

.review-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-bottom: 8px;
}

.review-card {
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #fff;
}

.ai-review-card {
  display: flex;
  flex-direction: column;
  min-height: 210px;
}

.review-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.ai-status-pill {
  flex-shrink: 0;
  padding: 4px 8px;
  border-radius: 999px;
  background: var(--gray-bg);
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

.ai-status-pill.loading {
  background: #dbeafe;
  color: #1e40af;
}

.ai-status-pill.success {
  background: #dcfce7;
  color: #15803d;
}

.ai-status-pill.error {
  background: var(--accent-soft);
  color: var(--accent);
}

.ai-placeholder,
.ai-error,
.ai-result {
  flex: 1;
  margin: 4px 0 14px;
  font-size: 13px;
  line-height: 1.6;
}

.ai-placeholder {
  color: var(--gray-hint);
}

.ai-error {
  color: var(--accent);
}

.ai-detail {
  color: var(--fg);
  margin-bottom: 8px;
}

.ai-score {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 8px;
}

.ai-suggestions {
  margin: 0;
  padding-left: 18px;
  color: var(--muted);
}

.ai-annotation-preview {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.annotation-copy,
.annotation-comments {
  display: grid;
  gap: 8px;
  min-width: 0;
  align-content: start;
}

.annotation-copy > strong,
.annotation-comments > strong {
  font-size: 12px;
  color: var(--gray-hint);
  letter-spacing: 0;
}

.annotation-copy p {
  margin: 0;
  padding: 9px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--muted);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.annotation-copy p.highlighted {
  border-color: rgba(196, 30, 58, 0.35);
  background: var(--accent-soft);
  color: var(--fg);
}

.annotation-copy span {
  display: inline-flex;
  margin-right: 6px;
  font-weight: 700;
  color: var(--accent);
}

.annotation-comment {
  padding: 9px 10px;
  border: 1px solid rgba(196, 30, 58, 0.22);
  border-left: 3px solid var(--accent);
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 8px 20px rgba(196, 30, 58, 0.06);
}

.annotation-comment > strong {
  display: block;
  margin-bottom: 4px;
  color: var(--accent);
}

.annotation-comment p,
.annotation-comment small {
  display: block;
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
  word-break: break-word;
}

.annotation-comment small {
  margin-top: 4px;
  color: var(--gray-hint);
}

.ai-answer {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  margin: 0;
  font: inherit;
  color: var(--muted);
}

.ai-parse-warning {
  margin-top: 8px;
  color: #92400e;
  font-size: 12px;
}

.ai-run-btn {
  align-self: flex-start;
}

/* Submit confirmation */
.summary-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 28px;
  background: #fff;
  margin-bottom: 20px;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--gray-bg-dark);
}

.summary-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--accent-soft);
  color: var(--accent);
}

.summary-icon svg {
  width: 20px;
  height: 20px;
}

.summary-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--fg);
}

.summary-subtitle {
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}

.field-row {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid var(--gray-bg);
}

.field-row:last-child {
  border-bottom: none;
}

.field-label {
  width: 120px;
  flex-shrink: 0;
  font-size: 13px;
  color: var(--muted);
  font-weight: 500;
}

.field-value {
  flex: 1;
  font-size: 13px;
  color: var(--fg);
}

.field-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 4px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 500;
  margin-right: 6px;
  margin-bottom: 4px;
}

.confirm-box {
  border: 1.5px solid var(--accent);
  border-radius: 10px;
  padding: 24px;
  background: var(--accent-soft);
  text-align: center;
  margin: 28px 0;
}

.confirm-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  margin: 0 auto 16px;
  animation: popIn 0.5s ease;
}

.confirm-icon svg {
  width: 28px;
  height: 28px;
}

.confirm-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 8px;
}

.confirm-text {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.7;
  max-width: 480px;
  margin: 0 auto;
}

@keyframes popIn {
  0% { transform: scale(0.8); opacity: 0; }
  60% { transform: scale(1.05); }
  100% { transform: scale(1); opacity: 1; }
}

/* Login required */
.login-required-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px 24px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  text-align: center;
}

.login-required-card h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--fg);
}

.login-required-card p {
  margin: 0;
  font-size: 14px;
  color: var(--muted);
  max-width: 360px;
}

.login-required-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  position: relative;
  background: var(--accent-soft);
  color: var(--accent);
}

.login-required-icon::before {
  content: '';
  position: absolute;
  left: 12px;
  top: 17px;
  width: 16px;
  height: 12px;
  border: 2px solid currentColor;
  border-radius: 3px;
}

.login-required-icon::after {
  content: '';
  position: absolute;
  left: 15px;
  top: 9px;
  width: 10px;
  height: 12px;
  border: 2px solid currentColor;
  border-bottom: 0;
  border-radius: 8px 8px 0 0;
}

/* Responsive desktop */
@media (min-width: 860px) {
  .create-case-wizard {
    flex-direction: row;
  }

  .wizard-rail {
    display: block;
  }

  .wizard-rail-mobile {
    display: none;
  }

  .wizard-main {
    padding: 32px 48px 48px;
  }

  .wizard-title {
    font-size: 28px;
  }

  .form-row {
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }

  .tag-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .ai-review-toolbar {
    flex-direction: row;
    align-items: center;
  }

  .ai-annotation-preview {
    grid-template-columns: minmax(0, 1fr) minmax(220px, 0.65fr);
  }
}

@media (max-width: 859px) {
  .wizard-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .wizard-actions-left,
  .wizard-actions-right {
    justify-content: center;
  }

  .fab-helper {
    position: static;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 12px 0 0 auto;
    width: auto;
    min-width: 88px;
    height: 38px;
    padding: 0 14px;
    border: 1px solid rgba(196, 30, 58, 0.22);
    background: var(--accent-soft);
    color: var(--accent);
    font-size: 14px;
    font-weight: 700;
    border-radius: 7px;
    box-shadow: none;
  }

  .helper-label-desktop {
    display: none;
  }

  .helper-label-mobile {
    display: inline;
  }
}

@media (max-width: 640px) {
  .wizard-main {
    padding: 20px 16px;
  }

  .wizard-title {
    font-size: 22px;
  }

  .tag-grid {
    grid-template-columns: 1fr;
  }

  .field-label {
    width: 90px;
  }

  .review-panel-body,
  .summary-card {
    padding: 20px 16px;
  }

  .summary-header {
    padding-bottom: 12px;
  }
}
</style>
