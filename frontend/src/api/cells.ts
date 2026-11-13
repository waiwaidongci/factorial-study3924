import {request} from './client';import type {Cell} from '../types/domain';export const getCells=(study:number)=>request<Cell[]>('/cells?study_id='+study);
