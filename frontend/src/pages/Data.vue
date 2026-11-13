<script setup lang="ts">
import {ref,onMounted,watch,computed} from 'vue';
import {useResearch} from '../stores/research';
import {useSamples} from '../stores/samples';
import {useAuth} from '../stores/auth';
import {createStudy} from '../api/studies';
import {useTask} from '../hooks/useTask';
import {number} from '../utils/format';
import PageHeading from '../components/common/PageHeading.vue';
import ErrorNotice from '../components/common/ErrorNotice.vue';
import StudySelect from '../components/StudySelect.vue';
import CellMatrix from '../components/CellMatrix.vue';
import type {Reading,AggregatedReading} from '../types/domain';

const lab=useResearch(),samples=useSamples(),auth=useAuth();
const selected=ref(0),cell=ref(0),offset=ref(0),show=ref(false);
const data=ref({code:'',name:'',source_file:'bh-new-trials.csv',a_levels:'1180,1220,1260',b_levels:'薄釉,厚釉',csv_text:'specimen_code,temperature,glaze,strength_mpa,measure_no\n'});
const {busy,error,perform}=useTask();
const study=computed(()=>lab.studies.find(s=>s.id===selected.value));
const pageSize=20;

async function load(){if(selected.value)await samples.load(selected.value,cell.value,offset.value);}
function switchView(v:'raw'|'aggregated'){samples.view=v;offset.value=0;perform(load);}
onMounted(()=>perform(async()=>{await lab.load();selected.value=lab.studies[0]?.id||0;await load();}));
watch(selected,()=>{cell.value=0;offset.value=0;perform(load);});
watch(cell,()=>{offset.value=0;perform(load);});
function submit(){
  perform(async()=>{
    const result=await createStudy({...data.value,a_levels:data.value.a_levels.split(',').map(x=>x.trim()),b_levels:data.value.b_levels.split(',').map(x=>x.trim()),note:'团队导入的随机独立试片试验（支持仪器复测测次）'});
    await lab.load();selected.value=result.id;show.value=false;
  });
}
function isAggregated(r:Reading|AggregatedReading):r is AggregatedReading{return 'measure_count' in r;}
const total=computed(()=>samples.view==='raw'?samples.rawTotal:samples.specimenTotal);
</script>

<template>
  <PageHeading index="02" title="每个处理格，都有独立试片" text="同片仪器复测先按试片取均值再分析，样本数按独立试片计；原始读数与聚合依据均可核对。">
    <button v-if="auth.canEdit" class="outline" @click="show=!show">{{show?'收起导入':'导入独立试验 +'}}</button>
  </PageHeading>
  <ErrorNotice :message="error" @retry="perform(load)"/>

  <form v-if="show" class="research-form import-form" @submit.prevent="submit">
    <h2>导入完整平衡试验</h2>
    <div class="form-grid">
      <label>试验编号<input v-model="data.code" required minlength="2"></label>
      <label>试验名称<input v-model="data.name" required minlength="2"></label>
      <label>温度水平 / 英文逗号<input v-model="data.a_levels" required></label>
      <label>釉层水平 / 英文逗号<input v-model="data.b_levels" required></label>
    </div>
    <label>CSV内容<textarea v-model="data.csv_text" rows="8" required></textarea></label>
    <p class="input-note">
      表头支持 <b>specimen_code,temperature,glaze,strength_mpa,measure_no</b>；旧表无 measure_no 列时默认第 1 测次，可直接导入。<br>
      同一试片多个测次先取算术均值，每格至少 3 个独立试片且各格试片数相同，原始读数最多 3000 条，强度为有限正数。<br>
      同片同测次完全同值的重复登记自动去重；同测次异值、或同一试片跨处理格将整份拒收且不保留任何数据。
    </p>
    <button class="primary" :disabled="busy">校验并保存试验 →</button>
  </form>

  <div class="data-toolbar">
    <StudySelect v-model="selected" :studies="lab.studies"/>
    <label>处理格
      <select v-model="cell">
        <option :value="0">全部处理格</option>
        <option v-for="c in samples.cells" :key="c.id" :value="c.id">{{c.temperature}}°C / {{c.glaze}} / {{c.n}}片</option>
      </select>
    </label>
  </div>
  <p class="source-note">{{study?.source_file}} <span>{{study?.note}}</span></p>
  <CellMatrix :cells="samples.cells" :a="study?.a_levels||[]" :b="study?.b_levels||[]"/>

  <div class="view-switch">
    <button :class="{active:samples.view==='raw'}" @click="switchView('raw')">原始读数 / 含测次号</button>
    <button :class="{active:samples.view==='aggregated'}" @click="switchView('aggregated')">试片聚合 / 均值依据</button>
  </div>

  <div class="table-wrap readings-table">
    <table v-if="samples.view==='raw'">
      <thead><tr><th>独立试片</th><th>测次号</th><th>温度 °C</th><th>釉层</th><th>抗折强度 MPa</th></tr></thead>
      <tbody>
        <tr v-for="r in samples.rawRows" :key="(r as Reading).id">
          <td><b>{{r.specimen_code}}</b></td>
          <td>{{(r as Reading).measure_no??1}}</td>
          <td>{{r.temperature}}</td>
          <td>{{r.glaze}}</td>
          <td>{{number(r.strength_mpa,5)}}</td>
        </tr>
      </tbody>
    </table>
    <table v-else>
      <thead><tr><th>独立试片</th><th>测次数</th><th>测次号</th><th>各测次原始读数 MPa</th><th>试片均值 MPa</th></tr></thead>
      <tbody>
        <tr v-for="r in samples.aggregatedRows" :key="r.specimen_code">
          <td><b>{{r.specimen_code}}</b></td>
          <td>{{r.measure_count}}</td>
          <td>{{r.measure_nos.join(' / ')}}</td>
          <td class="raw-values">{{r.raw_values.map(v=>number(v,5)).join('  ·  ')}}</td>
          <td><b>{{number(r.strength_mpa,5)}}</b></td>
        </tr>
      </tbody>
    </table>
  </div>
  <div class="pagination">
    <span>{{samples.view==='raw'?'共'+total+'条原始读数':'共'+total+'片独立试片'}} / {{offset+1}}—{{Math.min(offset+pageSize,total)}}</span>
    <div>
      <button :disabled="offset===0" @click="offset-=pageSize;perform(load)">← 前{{pageSize}}条</button>
      <button :disabled="offset+pageSize>=total" @click="offset+=pageSize;perform(load)">后{{pageSize}}条 →</button>
    </div>
  </div>
</template>
