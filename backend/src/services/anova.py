import numpy as np
from scipy.stats import f,t
from src.services.design import validate_design
from src.services.contrasts import simple_effects
def analyze_factorial(rows,a_levels,b_levels,alpha=.05):
    if not 0<alpha<1:raise ValueError('alpha必须在0和1之间')
    n=validate_design(rows,a_levels,b_levels);a=len(a_levels);b=len(b_levels)
    groups={(x,z):np.array([r['strength_mpa'] for r in rows if r['temperature']==x and r['glaze']==z],float) for x in a_levels for z in b_levels}
    means={key:float(values.mean()) for key,values in groups.items()};grand=float(np.mean(list(means.values())))
    ma={x:float(np.mean([means[(x,z)] for z in b_levels])) for x in a_levels};mb={z:float(np.mean([means[(x,z)] for x in a_levels])) for z in b_levels}
    ssa=b*n*sum((v-grand)**2 for v in ma.values());ssb=a*n*sum((v-grand)**2 for v in mb.values())
    ssab=n*sum((means[(x,z)]-ma[x]-mb[z]+grand)**2 for x,z in groups)
    sse=float(sum(np.sum((values-means[key])**2) for key,values in groups.items()));sst=float(sum(np.sum((values-grand)**2) for values in groups.values()))
    dfe=a*b*(n-1);mse=sse/dfe
    if not np.isfinite(mse) or sse<=100*len(rows)*(np.finfo(float).eps*max(1.,max(abs(r['strength_mpa']) for r in rows)))**2:raise ValueError('零或数值上不可分辨的残差方差：F检验和t区间不可估')
    table=[]
    for key,label,ss,df in [('A','温度主效应',ssa,a-1),('B','釉层主效应',ssb,b-1),('AB','温度×釉层交互',ssab,(a-1)*(b-1))]:
        ms=ss/df;stat=ms/mse;p=float(f.sf(stat,df,dfe));table.append({'term':key,'label':label,'ss':float(ss),'df':df,'ms':float(ms),'f':float(stat),'p':p})
    table.extend([{'term':'E','label':'格内残差','ss':sse,'df':dfe,'ms':mse,'f':None,'p':None},{'term':'T','label':'校正总计','ss':sst,'df':len(rows)-1,'ms':None,'f':None,'p':None}])
    critical=float(t.ppf(1-alpha/2,dfe));cells=[]
    for x,z in groups:
        mean=means[(x,z)];half=critical*np.sqrt(mse/n);cells.append({'temperature':x,'glaze':z,'n':n,'mean':mean,'std':float(groups[(x,z)].std(ddof=1)),'ci_low':float(mean-half),'ci_high':float(mean+half)})
    contrasts=simple_effects(means,a_levels,b_levels,n,mse,dfe,alpha)
    residuals=[{'specimen_code':r['specimen_code'],'fitted':means[(r['temperature'],r['glaze'])],'residual':r['strength_mpa']-means[(r['temperature'],r['glaze'])]} for r in rows]
    return {'n':len(rows),'per_cell':n,'a_levels':a_levels,'b_levels':b_levels,'grand_mean':grand,'mse':mse,'df_error':dfe,'alpha':alpha,'anova':table,'cells':cells,'contrasts':contrasts,'family_size':len(contrasts),'interaction_detected':bool(table[2]['p']<alpha),'holm_rejections':sum(r['reject_holm'] for r in contrasts),'ss_partition_error':float(sst-ssa-ssb-ssab-sse),'residuals':residuals}
