<script setup>
import { computed, onMounted, ref } from 'vue'
import { delJSON, getJSON, putJSON } from '../api'

const props = defineProps({ id: String })
const room = ref(null)
const tiles = ref([])
const prefTileId = ref(null)
const err = ref('')

// 系统默认砖：首个质量正常的砖（种子数据里即 600x600）
const systemDefaultTile = computed(() => tiles.value[0] ?? null)

onMounted(async () => {
  room.value = await getJSON(`/api/rooms/${props.id}`)
  tiles.value = (await getJSON('/api/tiles')).items.filter(t => t.data_quality === 'clean')
  const usable = tiles.value.some(t => t.id === room.value.preferred_tile_id)
  prefTileId.value = usable ? room.value.preferred_tile_id : (systemDefaultTile.value?.id ?? null)
})

async function savePref() {
  err.value = ''
  try {
    room.value = await putJSON(`/api/rooms/${props.id}/preferred-tile`, { tile_id: prefTileId.value })
  } catch (e) {
    err.value = e.message
  }
}

async function clearPref() {
  err.value = ''
  try {
    room.value = await delJSON(`/api/rooms/${props.id}/preferred-tile`)
    prefTileId.value = systemDefaultTile.value?.id ?? null
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
      <dt>默认砖</dt>
      <dd v-if="room.preferred_tile_id">偏好 {{ room.preferred_tile_name }}</dd>
      <dd v-else class="muted">未设置（下单台使用系统默认{{ systemDefaultTile ? `：${systemDefaultTile.name}` : '' }}）</dd>
    </dl>
    <section>
      <h2>默认砖偏好</h2>
      <label>偏好砖型
        <select v-model.number="prefTileId">
          <option v-for="t in tiles" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
      </label>
      <button :disabled="!prefTileId" @click="savePref">保存偏好</button>
      <button v-if="room.preferred_tile_id" @click="clearPref">清除偏好（恢复系统默认）</button>
      <p v-if="err" class="alert">{{ err }}</p>
    </section>
    <router-link :to="`/bench?room=${room.id}`">去测算</router-link>
  </div>
</template>
