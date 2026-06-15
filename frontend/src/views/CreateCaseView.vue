<template>
  <div class="create-case-wizard">
    <CreateWizardRail :steps="steps" :current-step="currentStep" :progress-percent="progressPercent" />

    <main class="wizard-main">
      <div class="wizard-breadcrumb">
        <span class="bc-parent">创建案例</span>
        <span class="bc-chevron" aria-hidden="true">›</span>
        <span class="bc-current">{{ steps[currentStep].label }}</span>
      </div>

      <h1 class="wizard-title">{{ stepMeta.title }}</h1>
      <p class="wizard-desc">{{ stepMeta.desc }}</p>

      <div v-if="!isAuthenticated" class="login-required-card">
        <div class="login-required-icon" aria-hidden="true"></div>
        <h3>请先登录</h3>
        <p>创建案例需要登录账号。请先登录后再继续。</p>
      </div>

      <div v-else class="wizard-form">
        <CreateBasicStep
          v-if="currentStep === 0"
          :form="form"
          :errors="errors"
          :display-author="displayAuthor"
          @touch="touch"
        />
        <CreateContentStep
          v-if="currentStep === 1"
          :form="form"
          :errors="errors"
          :word-count="wordCount"
          :reading-time="readingTime"
          @touch="touch"
        />
        <CreateClassifyStep
          v-if="currentStep === 2"
          :form="form"
          :errors="errors"
          :constants="constants"
          @touch="touch"
        />
        <CreateReviewStep
          v-if="currentStep === 3"
          :ai-review-items="aiReviewItems"
          :ai-review-state="aiReviewState"
          :ai-prompt-load-error="aiPromptLoadError"
          :ai-running-all="aiRunningAll"
          :can-run-ai-review="canRunAiReview"
          :ai-review-progress="aiReviewProgress"
          @run-all="runAllAiReviews"
          @run-item="runAiReview"
        />
        <CreateSubmitStep
          v-if="currentStep === 4"
          :form="form"
          :constants="constants"
          :can-submit="canSubmit"
          :submitting="submitting"
          :content-summary="contentSummary"
          @submit="handleFormalSubmit"
        />

        <CreateWizardActions
          :current-step="currentStep"
          :saving="saving"
          @prev="prevStep"
          @save="handleSaveDraft"
          @next="nextStep"
          @edit="currentStep = 1"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from "vue";
import { currentUser, isLoggedIn } from "../api/auth.js";
import { createCase, updateCase, submitCaseById } from "../api/cases.js";
import { notify } from "../utils/toast.js";
import CreateWizardRail from "../components/create/CreateWizardRail.vue";
import CreateWizardActions from "../components/create/CreateWizardActions.vue";
import CreateBasicStep from "../components/create/CreateBasicStep.vue";
import CreateContentStep from "../components/create/CreateContentStep.vue";
import CreateClassifyStep from "../components/create/CreateClassifyStep.vue";
import CreateReviewStep from "../components/create/CreateReviewStep.vue";
import CreateSubmitStep from "../components/create/CreateSubmitStep.vue";
import { useCaseDraft } from "../composables/useCaseDraft.js";
import { useCaseForm } from "../composables/useCaseForm.js";
import { useAiReview } from "../composables/useAiReview.js";

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
const latestReviewVersionId = ref(null);

const {
  form, touched, constants, isAuthenticated, displayAuthor,
  wordCount, readingTime, contentSummary, errors, canSubmit,
  touch, validateStep, resetForm: resetCaseForm, loadConstants,
} = useCaseForm();

const { persistDraft, loadDraft, clearDraft } = useCaseDraft({
  form,
  caseId,
  latestReviewVersionId,
  getCurrentUser: currentUser,
});

const {
  aiReviewItems, aiReviewState, aiPromptLoadError, aiRunningAll,
  canRunAiReview, aiReviewProgress, resetAllAiReviews,
  loadAiPrompts, runAiReview, runAllAiReviews, collectAiReviews,
  hasAiReviewWarning, confirmAiReviewWarning,
} = useAiReview({
  form,
  isAuthenticated,
  caseId,
  latestReviewVersionId,
  persistDraft,
  displayAuthor,
});

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

function appendAiReviews(payload) {
  const reviews = collectAiReviews();
  if (reviews.length) {
    payload.ai_reviews = JSON.stringify(reviews);
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
  appendAiReviews(payload);
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
      appendAiReviews(payload);
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
      appendAiReviews(payload);
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
    resetWizard();
  } catch (err) {
    notify(err.message || "提交失败，请稍后重试", "error");
  } finally {
    submitting.value = false;
  }
}

function resetWizard() {
  resetCaseForm();
  resetAllAiReviews();
  caseId.value = null;
  latestReviewVersionId.value = null;
  currentStep.value = 0;
}

function currentDraftQueryId() {
  const hash = window.location.hash.replace("#", "");
  const [viewId, query = ""] = hash.split("?");
  if (viewId !== "create") return "";
  return new URLSearchParams(query).get("draft");
}

onMounted(async () => {
  const user = currentUser();
  form.author = user?.nickname || user?.username || "";
  loadDraft();

  const draftId = currentDraftQueryId();
  if (!draftId) {
    caseId.value = null;
    latestReviewVersionId.value = null;
  }

  await loadConstants();
  if (isAuthenticated.value) {
    await loadAiPrompts();
  }
});

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
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - var(--header-height));
  background: var(--color-bg);
}

.wizard-main {
  flex: 1;
  width: 100%;
  min-width: 0;
  padding: 24px 16px 40px;
  max-width: 960px;
}

.wizard-breadcrumb {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 12px;
}

.bc-current {
  color: var(--color-brand);
  font-weight: 600;
}

.bc-chevron {
  margin: 0 6px;
}

.wizard-title {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
}

.wizard-desc {
  margin: 0 0 24px;
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.wizard-form {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 20px;
}

.login-required-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  text-align: center;
}

.login-required-card h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text);
}

.login-required-card p {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
  max-width: 360px;
}

.login-required-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  position: relative;
  background: var(--color-brand-light);
  color: var(--color-brand);
}

.login-required-icon::before {
  content: "";
  position: absolute;
  left: 12px;
  top: 17px;
  width: 16px;
  height: 12px;
  border: 2px solid currentColor;
  border-radius: 3px;
}

.login-required-icon::after {
  content: "";
  position: absolute;
  left: 15px;
  top: 9px;
  width: 10px;
  height: 12px;
  border: 2px solid currentColor;
  border-bottom: 0;
  border-radius: 8px 8px 0 0;
}

@media (min-width: 860px) {
  .create-case-wizard {
    flex-direction: row;
  }

  .wizard-main {
    padding: 32px 40px 48px;
  }

  .wizard-title {
    font-size: 28px;
  }

  .wizard-form {
    padding: 28px;
  }
}
</style>
