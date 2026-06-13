<template>
  <div class="app">
    <!-- Header -->
    <header class="topnav">
      <div class="topnav-inner">
        <!-- Branding -->
        <div class="topnav-left">
          <div class="logo-badge">强</div>
          <div class="logo-text">强国有我 思政案例库</div>
        </div>

        <!-- Navigation -->
        <nav class="topnav-nav">
          <a
            v-for="item in visibleNavItems"
            :key="item.id"
            :class="['nav-link', { active: currentView === item.id }]"
            href="javascript:void(0)"
            @click="navigate(item.id)"
          >
            {{ item.label }}
          </a>
        </nav>

        <!-- Right cluster -->
        <div class="topnav-right">
          <form class="search-box" @submit.prevent="submitHeaderSearch">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="7" cy="7" r="5" />
              <path d="M11 11l3.5 3.5" />
            </svg>
            <input
              v-model="headerSearchInput"
              type="text"
              placeholder="搜索学术资源…"
              aria-label="搜索案例"
            />
          </form>

          <button type="button" class="icon-btn" aria-label="通知">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </button>

          <template v-if="isLoggedIn()">
            <div class="avatar" :title="displayName">{{ userInitials }}</div>
            <button type="button" class="icon-btn" @click="handleLogout" aria-label="退出登录">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <path d="M21 12H9" />
              </svg>
            </button>
          </template>
          <template v-else>
            <button type="button" class="icon-btn" @click="showLogin = true" aria-label="登录">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                <polyline points="10 17 15 12 10 7" />
                <path d="M15 12H3" />
              </svg>
            </button>
          </template>
        </div>
      </div>
    </header>

    <!-- Main content -->
    <main class="app-main">
      <HomeView v-if="currentView === 'home'" />
      <CaseLibraryView v-else-if="currentView === 'library'" :search-trigger="searchTrigger" />
      <CreateCaseView v-else-if="currentView === 'create'" />
      <MySubmissionsView v-else-if="currentView === 'submissions'" />
      <AdminReviewView v-else-if="currentView === 'admin'" />
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <p>© 上海大学 思政案例库</p>
    </footer>

    <!-- Login Modal -->
    <LoginModal v-if="showLogin" @close="showLogin = false" @success="onLoginSuccess" />

    <!-- Forced Password Change Modal (cannot dismiss) -->
    <PasswordChangeModal v-if="showPasswordChange" @success="onPasswordChanged" />

    <div class="toast-stack" aria-live="polite" aria-atomic="true">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="['toast', `toast-${toast.type}`]"
      >
        {{ toast.message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import {
  auth,
  isLoggedIn,
  isAdmin,
  mustChangePassword,
  currentUser,
  logout,
} from "./api/auth.js";
import LoginModal from "./components/LoginModal.vue";
import PasswordChangeModal from "./components/PasswordChangeModal.vue";
import HomeView from "./views/HomeView.vue";
import CaseLibraryView from "./views/CaseLibraryView.vue";
import CreateCaseView from "./views/CreateCaseView.vue";
import MySubmissionsView from "./views/MySubmissionsView.vue";
import AdminReviewView from "./views/AdminReviewView.vue";
import { TOAST_EVENT } from "./utils/toast.js";

const currentView = ref("home");
const showLogin = ref(false);
const toasts = ref([]);
let toastSeq = 0;

// Global header search state (passed to CaseLibraryView via prop)
const searchTrigger = ref({ keyword: "", nonce: 0 });
const headerSearchInput = ref("");

function submitHeaderSearch() {
  const kw = headerSearchInput.value.trim();
  searchTrigger.value = {
    keyword: kw,
    nonce: searchTrigger.value.nonce + 1,
  };
  headerSearchInput.value = "";
  navigate("library");
}

const showPasswordChange = computed(() => {
  return isLoggedIn() && mustChangePassword();
});

const displayName = computed(() => {
  const user = currentUser();
  return user?.nickname || user?.username || "";
});

const userInitials = computed(() => {
  const name = displayName.value;
  if (!name) return "?";
  return name.slice(0, 1).toUpperCase();
});

const allNavItems = [
  { id: "home", label: "首页", public: true },
  { id: "library", label: "案例库", public: true },
  { id: "create", label: "创建案例", public: false },
  { id: "submissions", label: "我的提交", public: false },
  { id: "admin", label: "审核管理", public: false, admin: true },
];

const visibleNavItems = computed(() => {
  return allNavItems.filter((item) => {
    if (item.admin && !isAdmin()) return false;
    if (!item.public && !isLoggedIn()) return false;
    return true;
  });
});

function navigate(viewId) {
  const item = allNavItems.find((i) => i.id === viewId);
  if (item && !item.public && !isLoggedIn()) {
    showLogin.value = true;
    return;
  }
  if (item && item.admin && !isAdmin()) {
    return;
  }
  currentView.value = viewId;
}

function onLoginSuccess() {
  showLogin.value = false;
}

function onPasswordChanged() {
  // Modal closes automatically via computed
}

function handleLogout() {
  logout();
  currentView.value = "home";
}

function handleToast(event) {
  const message = event.detail?.message || "";
  if (!message) return;
  const toast = {
    id: ++toastSeq,
    message,
    type: event.detail?.type || "info",
  };
  toasts.value = [...toasts.value, toast].slice(-4);
  window.setTimeout(() => {
    toasts.value = toasts.value.filter((item) => item.id !== toast.id);
  }, 3200);
}

// Optional: sync with hash for basic URL state
function readHash() {
  const hash = window.location.hash.replace("#", "");
  const item = allNavItems.find((i) => i.id === hash);
  if (item) {
    navigate(hash);
  }
}

watch(currentView, (view) => {
  window.location.hash = view;
});

window.addEventListener("hashchange", readHash);
readHash();

onMounted(() => {
  window.addEventListener(TOAST_EVENT, handleToast);
});

onBeforeUnmount(() => {
  window.removeEventListener(TOAST_EVENT, handleToast);
  window.removeEventListener("hashchange", readHash);
});
</script>
