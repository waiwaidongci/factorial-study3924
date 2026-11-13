from itertools import combinations
import math
from scipy.stats import t
def holm_adjust(pvalues):
    m=len(pvalues);order=sorted(range(m),key=lambda i:(pvalues[i],i));adjusted=[0.]*m;running=0.
    for rank,i in enumerate(order):
        running=max(running,(m-rank)*pvalues[i]);adjusted[i]=min(1.,running)
    return adjusted
def simple_effects(means,a_levels,b_levels,n,mse,df_error,alpha):
    # Entire family is declared before examining outcomes: all A pairs within B,
    # followed by all B pairs within A. No significance-based selection.
    specs=[]
    for b in b_levels:
        for left,right in combinations(a_levels,2):specs.append(('温度','釉层',b,left,right,means[(left,b)]-means[(right,b)]))
    for a in a_levels:
        for left,right in combinations(b_levels,2):specs.append(('釉层','温度',a,left,right,means[(a,left)]-means[(a,right)]))
    se=math.sqrt(2*mse/n);critical=float(t.ppf(1-alpha/2,df_error));result=[]
    for i,(factor,condition_factor,condition,left,right,estimate) in enumerate(specs):
        statistic=estimate/se;p=float(2*t.sf(abs(statistic),df_error))
        result.append({'index':i+1,'factor':factor,'condition_factor':condition_factor,'condition':condition,'left':left,'right':right,'estimate':float(estimate),'se':se,'t':float(statistic),'p_raw':p,'ci_low':float(estimate-critical*se),'ci_high':float(estimate+critical*se)})
    for row,p in zip(result,holm_adjust([r['p_raw'] for r in result])):row.update(p_holm=p,reject_holm=bool(p<alpha))
    return result
