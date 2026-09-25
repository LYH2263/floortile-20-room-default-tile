<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { getJSON, postJSON } from '../api'
import OrderSummary from '../components/OrderSummary.vue'
import TileGridPreview from '../components/TileGridPreview.vue'

const rooms = ref([])
const tiles = ref([])
const settings = ref({})
const roomId = ref(null)
const tileId = ref(null)
const tileSource = ref('') // 'pref' | 'default' | 'manual'
const saveToDb = ref(false)
const result = ref(null)
const err = ref('')

const currentRoom = computed(() => rooms.value.find(r => r.id === roomId.value))

// 系统默认砖：设置里的 default_tile_id（种子为 600x600），兜底第一种干净砖
const systemDefaultTileId = computed(() => {
  const configured = Number(settings.value.default_tile_id)
  if (tiles.value.some(t => t.id === configured)) return configured
  return tiles.value.length ? tiles.value[0].id : null
})

// 选中房间后落到该房偏好砖；无偏好则回系统默认砖，绝不沿用上一房的砖
function applyRoomPreference() {
  const pref = currentRoom.value?.preferred_tile_id
  if (pref != null && tiles.value.some(t => t.id === pref)) {
    tileId.value = pref
    tileSource.value = 'pref'
  } else {
    tileId.value = systemDefaultTileId.value
    tileSource.value = 'default'
  }
}

watch(roomId, () => {
  result.value = null
  err.value = ''
  applyRoomPreference()
})

onMounted(async () => {
  const [roomRes, tileRes, s] = await Promise.all([
    getJSON('/api/rooms'),
    getJSON('/api/tiles'),
    getJSON('/api/settings'),
  ])
  rooms.value = roomRes.items.filter(r => r.data_quality === 'clean')
  tiles.value = tileRes.items.filter(t => t.data_quality === 'clean')
  settings.value = s
  if (rooms.value.length) roomId.value = rooms.value[0].id
})

function onTilePicked() {
  tileSource.value = 'manual'
}

async function calc() {
  err.value = ''
  if (roomId.value == null || tileId.value == null) {
    err.value = '没有可用的房间或砖型，无法测算'
    return
  }
  try {
    if (saveToDb.value) {
      result.value = await postJSON('/api/estimate', {
        room_id: roomId.value,
        tile_id: tileId.value,
        save: true,
        note: '前端测算落库',
      })
    } else {
      result.value = await getJSON(`/api/estimate?room_id=${roomId.value}&tile_id=${tileId.value}`)
    }
  } catch (e) {
    err.value = e.message
    result.value = null
  }
}

const sourceLabel = computed(() => (
  { pref: '房间偏好', default: '系统默认', manual: '手动选择' }[tileSource.value] || ''
))
</script>
<template>
  <div class="page">
    <h1>下单测算</h1>
    <label>房间 <select v-model.number="roomId"><option v-for="r in rooms" :key="r.id" :value="r.id">{{ r.name }}</option></select></label>
    <label>砖型 <select v-model.number="tileId" @change="onTilePicked"><option v-for="t in tiles" :key="t.id" :value="t.id">{{ t.name }}</option></select></label>
    <p v-if="tileId != null" class="hint">
      砖型来源：{{ sourceLabel }}<template v-if="tileSource === 'default'">（该房未设偏好）</template>
    </p>
    <label>落库 <input type="checkbox" v-model="saveToDb" /> 勾选后测算会保存一条记录</label>
    <button :disabled="tileId == null || roomId == null" @click="calc">测算</button>
    <p v-if="err" class="alert">{{ err }}</p>
    <OrderSummary :result="result" />
    <TileGridPreview v-if="result?.layout" :cols="result.layout.cols" :rows="result.layout.rows" :grid-count="result.layout.grid_count" />
  </div>
</template>
