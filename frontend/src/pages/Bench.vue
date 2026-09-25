<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON, postJSON } from '../api'
import OrderSummary from '../components/OrderSummary.vue'
import TileGridPreview from '../components/TileGridPreview.vue'

const route = useRoute()
const rooms = ref([])
const tiles = ref([])
const roomId = ref(null)
const tileId = ref(null)
const persist = ref(false)
const result = ref(null)
const err = ref('')

// 系统默认砖：首个质量正常的砖（种子数据里即 600x600）
const systemDefaultTile = computed(() => tiles.value[0] ?? null)
const currentRoom = computed(() => rooms.value.find(r => r.id === roomId.value) ?? null)
// 仅当房间确实设了偏好、且偏好砖在可选列表里时才认偏好，否则视为无偏好
const preferredTile = computed(() => {
  const pid = currentRoom.value?.preferred_tile_id
  if (pid == null) return null
  return tiles.value.find(t => t.id === pid) ?? null
})
const usingPreference = computed(() => preferredTile.value != null && tileId.value === preferredTile.value.id)

onMounted(async () => {
  rooms.value = (await getJSON('/api/rooms')).items.filter(r => r.data_quality === 'clean')
  tiles.value = (await getJSON('/api/tiles')).items.filter(t => t.data_quality === 'clean')
  const q = Number(route.query.room)
  roomId.value = rooms.value.some(r => r.id === q) ? q : (rooms.value[0]?.id ?? null)
  applyRoomTileDefault()
})

// 切换房间：砖型跟随新房间的偏好（无偏好则回系统默认砖），绝不沿用上一房的砖
watch(roomId, () => {
  applyRoomTileDefault()
  result.value = null
  err.value = ''
})

// 手动改选砖型后，旧结果不再对应当前输入，清掉避免误读
watch(tileId, () => {
  result.value = null
  err.value = ''
})

function applyRoomTileDefault() {
  tileId.value = preferredTile.value?.id ?? systemDefaultTile.value?.id ?? null
}

async function runEstimate() {
  err.value = ''
  try {
    // 只有勾选“落库保存”才允许后端产生新的测算记录
    result.value = await postJSON('/api/estimate', {
      room_id: roomId.value,
      tile_id: tileId.value,
      save: persist.value,
      note: persist.value ? '前端保存' : '',
    })
  } catch (e) {
    err.value = e.message
    result.value = null
  }
}
</script>
<template>
  <div class="page">
    <h1>下单测算</h1>
    <label>房间 <select v-model.number="roomId"><option v-for="r in rooms" :key="r.id" :value="r.id">{{ r.name }}</option></select></label>
    <label>砖型 <select v-model.number="tileId"><option v-for="t in tiles" :key="t.id" :value="t.id">{{ t.name }}</option></select></label>
    <p v-if="usingPreference" class="pref-hint">已按房间偏好选中：{{ preferredTile.name }}</p>
    <p v-else-if="preferredTile" class="muted">该房偏好砖为 {{ preferredTile.name }}，当前已手动改选其他砖型</p>
    <p v-else class="muted">该房未设偏好砖，使用系统默认{{ systemDefaultTile ? `：${systemDefaultTile.name}` : '' }}</p>
    <label class="inline"><input v-model="persist" type="checkbox" /> 测算后落库保存</label>
    <button :disabled="!roomId || !tileId" @click="runEstimate">测算</button>
    <p v-if="err" class="alert">{{ err }}</p>
    <p v-if="result?.run_id" class="pref-hint">已落库，记录 #{{ result.run_id }}</p>
    <OrderSummary :result="result" />
    <TileGridPreview v-if="result?.layout" :cols="result.layout.cols" :rows="result.layout.rows" :grid-count="result.layout.grid_count" />
  </div>
</template>
