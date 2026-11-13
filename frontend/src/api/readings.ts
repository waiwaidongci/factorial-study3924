import {request} from './client';import type {Reading,AggregatedReading} from '../types/domain';
export const getReadings=(study:number,cell=0,offset=0,view:'raw'|'aggregated'='raw')=>request<{total:number;rows:(Reading|AggregatedReading)[];view:string}>(`/readings?study_id=${study}&offset=${offset}&limit=20&view=${view}${cell?'&cell_id='+cell:''}`);
