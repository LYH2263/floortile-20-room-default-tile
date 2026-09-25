<script setup>
import { computed, onMounted, ref } from 'vue'
import { getJSON, putJSON } from '../api'

const props = defineProps({ id: String })
const room = ref(null)
const tiles = ref([])
const settings = ref({})
const picked = ref('') // '' 表示未设置
const msg = ref('')
const err = ref('')

onMounted(async () => {
  const [r, t, s] = await Promise.all([
    getJSON(`/api/rooms/${props.id}`),
    getJSON('/api/tiles'),
    getJSON('/api/settings'),
  ])
  room.value = r
  tiles.value = t.items.filter(x => x.data_quality === 'clean')
  settings.value = s
  picked.value = r.preferred_tile_id ?? ''
})

const defaultTileName = computed(() => {
  const id = Number(settings.value.default_tile_id)
  return tiles.value.find(t => t.id === id)?.name || tiles.value[0]?.name || ''
})

async function savePref() {
  err.value = ''
  msg.value = ''
  try {
    room.value = await putJSON(`/api/rooms/${props.id}/preferred-tile`, {
      tile_id: picked.value === '' ? null : Number(picked.value),
    })
    msg.value = room.value.preferred_tile_id == null
      ? `未设偏好，测算时将使用系统默认砖${defaultTileName.value ? `（${defaultTileName.value}）` : ''}`
      : '偏好已保存'
  } catch (e) {
    err.value = e.message
  }
}

async function clearPref() {
  err.value = ''
  msg.value = ''
  try {
    room.value = await putJSON(`/api/rooms/${props.id}/preferred-tile`, { tile_id: null })
    picked.value = ''
    msg.value = `已清除偏好，恢复系统默认砖${defaultTileName.value ? `（${defaultTileName.value}）` : ''}`
  } catch (e) {
    err.value = e.message
  }
}
</script>
<template>
  <div class="page" v-if="room">
    <h1>{{ room.name }}</h1>
    <div v-if="room.data_quality === 'dirty'" class="alert">该房间尺寸异常：{{ room.note }}</div>
    <dl>
      <dt>长度</dt><dd>{{ room.length }} m</dd>
      <dt>宽度</dt><dd>{{ room.width }} m</dd>
      <dt>面积</dt><dd>{{ (room.length * room.width).toFixed(2) }} m²</dd>
      <dt>偏好砖型</dt>
      <dd>
        <template v-if="room.preferred_tile_id != null">{{ room.preferred_tile_name || `#${room.preferred_tile_id}` }}</template>
        <template v-else>未设置（跟随系统默认{{ defaultTileName ? `：${defaultTileName}` : '' }}）</template>
      </dd>
    </dl>
    <div class="pref-editor">
      <label>默认砖型
        <select v-model="picked">
          <option value="">未设置（跟随系统默认）</option>
          <option v-for="t in tiles" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
      </label>
      <button @click="savePref">保存偏好</button>
      <button v-if="room.preferred_tile_id != null" @click="clearPref">清除偏好（恢复系统默认）</button>
      <p v-if="msg" class="hint">{{ msg }}</p>
      <p v-if="err" class="alert">{{ err }}</p>
    </div>
    <router-link to="/bench">去测算</router-link>
  </div>
</template>
