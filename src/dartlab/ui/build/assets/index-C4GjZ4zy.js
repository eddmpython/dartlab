var _d=Object.defineProperty;var Bo=e=>{throw TypeError(e)};var yd=(e,t,r)=>t in e?_d(e,t,{enumerable:!0,configurable:!0,writable:!0,value:r}):e[t]=r;var kr=(e,t,r)=>yd(e,typeof t!="symbol"?t+"":t,r),zs=(e,t,r)=>t.has(e)||Bo("Cannot "+r);var S=(e,t,r)=>(zs(e,t,"read from private field"),r?r.call(e):t.get(e)),$e=(e,t,r)=>t.has(e)?Bo("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,r),he=(e,t,r,n)=>(zs(e,t,"write to private field"),n?n.call(e,r):t.set(e,r),r),Mt=(e,t,r)=>(zs(e,t,"access private method"),r);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const a of document.querySelectorAll('link[rel="modulepreload"]'))n(a);new MutationObserver(a=>{for(const i of a)if(i.type==="childList")for(const o of i.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&n(o)}).observe(document,{childList:!0,subtree:!0});function r(a){const i={};return a.integrity&&(i.integrity=a.integrity),a.referrerPolicy&&(i.referrerPolicy=a.referrerPolicy),a.crossOrigin==="use-credentials"?i.credentials="include":a.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function n(a){if(a.ep)return;a.ep=!0;const i=r(a);fetch(a.href,i)}})();const Ps=!1;var ro=Array.isArray,wd=Array.prototype.indexOf,pa=Array.prototype.includes,vs=Array.from,kd=Object.defineProperty,xn=Object.getOwnPropertyDescriptor,Mi=Object.getOwnPropertyDescriptors,Sd=Object.prototype,zd=Array.prototype,no=Object.getPrototypeOf,Vo=Object.isExtensible;function Ea(e){return typeof e=="function"}const Md=()=>{};function Ad(e){return e()}function Is(e){for(var t=0;t<e.length;t++)e[t]()}function Ai(){var e,t,r=new Promise((n,a)=>{e=n,t=a});return{promise:r,resolve:e,reject:t}}function is(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const r=[];for(const n of e)if(r.push(n),r.length===t)break;return r}const Gt=2,ba=4,Un=8,ps=1<<24,zn=16,Er=32,Yn=64,Ls=128,mr=512,Ft=1024,Bt=2048,Cr=4096,qt=8192,Gr=16384,_a=32768,wn=65536,Go=1<<17,Cd=1<<18,ya=1<<19,Ci=1<<20,Br=1<<25,Kn=65536,Os=1<<21,ao=1<<22,bn=1<<23,Hr=Symbol("$state"),Ei=Symbol("legacy props"),Ed=Symbol(""),Ln=new class extends Error{constructor(){super(...arguments);kr(this,"name","StaleReactionError");kr(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var ki;const Ti=!!((ki=globalThis.document)!=null&&ki.contentType)&&globalThis.document.contentType.includes("xml");function Td(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function $d(e,t,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function Nd(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function Pd(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Id(e){throw new Error("https://svelte.dev/e/effect_orphan")}function Ld(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function Od(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function Rd(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function jd(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function Dd(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function Fd(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const Bd=1,Vd=2,$i=4,Gd=8,Hd=16,Ud=1,Kd=2,Ni=4,Wd=8,qd=16,Yd=1,Jd=2,It=Symbol(),Pi="http://www.w3.org/1999/xhtml",Ii="http://www.w3.org/2000/svg",Xd="http://www.w3.org/1998/Math/MathML",Zd="@attach";function Qd(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function ec(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Li(e){return e===this.v}function tc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function Oi(e){return!tc(e,this.v)}let Ua=!1,rc=!1;function nc(){Ua=!0}let Lt=null;function ma(e){Lt=e}function Tr(e,t=!1,r){Lt={p:Lt,i:!1,c:null,e:null,s:e,x:null,l:Ua&&!t?{s:null,u:null,$:[]}:null}}function $r(e){var t=Lt,r=t.e;if(r!==null){t.e=null;for(var n of r)tl(n)}return t.i=!0,Lt=t.p,{}}function Ka(){return!Ua||Lt!==null&&Lt.l===null}let On=[];function Ri(){var e=On;On=[],Is(e)}function Ur(e){if(On.length===0&&!La){var t=On;queueMicrotask(()=>{t===On&&Ri()})}On.push(e)}function ac(){for(;On.length>0;)Ri()}function ji(e){var t=Ae;if(t===null)return Me.f|=bn,e;if((t.f&_a)===0&&(t.f&ba)===0)throw e;hn(e,t)}function hn(e,t){for(;t!==null;){if((t.f&Ls)!==0){if((t.f&_a)===0)throw e;try{t.b.error(e);return}catch(r){e=r}}t=t.parent}throw e}const sc=-7169;function gt(e,t){e.f=e.f&sc|t}function so(e){(e.f&mr)!==0||e.deps===null?gt(e,Ft):gt(e,Cr)}function Di(e){if(e!==null)for(const t of e)(t.f&Gt)===0||(t.f&Kn)===0||(t.f^=Kn,Di(t.deps))}function Fi(e,t,r){(e.f&Bt)!==0?t.add(e):(e.f&Cr)!==0&&r.add(e),Di(e.deps),gt(e,Ft)}const Qa=new Set;let ge=null,Rs=null,Dt=null,Zt=[],ms=null,La=!1,ha=null,oc=1;var vn,oa,Dn,ia,la,da,pn,Rr,ca,tr,js,Ds,Fs,Bs;const ko=class ko{constructor(){$e(this,tr);kr(this,"id",oc++);kr(this,"current",new Map);kr(this,"previous",new Map);$e(this,vn,new Set);$e(this,oa,new Set);$e(this,Dn,0);$e(this,ia,0);$e(this,la,null);$e(this,da,new Set);$e(this,pn,new Set);$e(this,Rr,new Map);kr(this,"is_fork",!1);$e(this,ca,!1)}skip_effect(t){S(this,Rr).has(t)||S(this,Rr).set(t,{d:[],m:[]})}unskip_effect(t){var r=S(this,Rr).get(t);if(r){S(this,Rr).delete(t);for(var n of r.d)gt(n,Bt),Vr(n);for(n of r.m)gt(n,Cr),Vr(n)}}process(t){var a;Zt=[],this.apply();var r=ha=[],n=[];for(const i of t)Mt(this,tr,Ds).call(this,i,r,n);if(ha=null,Mt(this,tr,js).call(this)){Mt(this,tr,Fs).call(this,n),Mt(this,tr,Fs).call(this,r);for(const[i,o]of S(this,Rr))Hi(i,o)}else{Rs=this,ge=null;for(const i of S(this,vn))i(this);S(this,vn).clear(),S(this,Dn)===0&&Mt(this,tr,Bs).call(this),Ho(n),Ho(r),S(this,da).clear(),S(this,pn).clear(),Rs=null,(a=S(this,la))==null||a.resolve()}Dt=null}capture(t,r){r!==It&&!this.previous.has(t)&&this.previous.set(t,r),(t.f&bn)===0&&(this.current.set(t,t.v),Dt==null||Dt.set(t,t.v))}activate(){ge=this,this.apply()}deactivate(){ge===this&&(ge=null,Dt=null)}flush(){var t;if(Zt.length>0)ge=this,Bi();else if(S(this,Dn)===0&&!this.is_fork){for(const r of S(this,vn))r(this);S(this,vn).clear(),Mt(this,tr,Bs).call(this),(t=S(this,la))==null||t.resolve()}this.deactivate()}discard(){for(const t of S(this,oa))t(this);S(this,oa).clear()}increment(t){he(this,Dn,S(this,Dn)+1),t&&he(this,ia,S(this,ia)+1)}decrement(t){he(this,Dn,S(this,Dn)-1),t&&he(this,ia,S(this,ia)-1),!S(this,ca)&&(he(this,ca,!0),Ur(()=>{he(this,ca,!1),Mt(this,tr,js).call(this)?Zt.length>0&&this.flush():this.revive()}))}revive(){for(const t of S(this,da))S(this,pn).delete(t),gt(t,Bt),Vr(t);for(const t of S(this,pn))gt(t,Cr),Vr(t);this.flush()}oncommit(t){S(this,vn).add(t)}ondiscard(t){S(this,oa).add(t)}settled(){return(S(this,la)??he(this,la,Ai())).promise}static ensure(){if(ge===null){const t=ge=new ko;Qa.add(ge),La||Ur(()=>{ge===t&&t.flush()})}return ge}apply(){}};vn=new WeakMap,oa=new WeakMap,Dn=new WeakMap,ia=new WeakMap,la=new WeakMap,da=new WeakMap,pn=new WeakMap,Rr=new WeakMap,ca=new WeakMap,tr=new WeakSet,js=function(){return this.is_fork||S(this,ia)>0},Ds=function(t,r,n){t.f^=Ft;for(var a=t.first;a!==null;){var i=a.f,o=(i&(Er|Yn))!==0,l=o&&(i&Ft)!==0,d=(i&qt)!==0,u=l||S(this,Rr).has(a);if(!u&&a.fn!==null){o?d||(a.f^=Ft):(i&ba)!==0?r.push(a):(i&(Un|ps))!==0&&d?n.push(a):Ja(a)&&(xa(a),(i&zn)!==0&&(S(this,pn).add(a),d&&gt(a,Bt)));var p=a.first;if(p!==null){a=p;continue}}for(;a!==null;){var v=a.next;if(v!==null){a=v;break}a=a.parent}}},Fs=function(t){for(var r=0;r<t.length;r+=1)Fi(t[r],S(this,da),S(this,pn))},Bs=function(){var i;if(Qa.size>1){this.previous.clear();var t=ge,r=Dt,n=!0;for(const o of Qa){if(o===this){n=!1;continue}const l=[];for(const[u,p]of this.current){if(o.current.has(u))if(n&&p!==o.current.get(u))o.current.set(u,p);else continue;l.push(u)}if(l.length===0)continue;const d=[...o.current.keys()].filter(u=>!this.current.has(u));if(d.length>0){var a=Zt;Zt=[];const u=new Set,p=new Map;for(const v of l)Vi(v,d,u,p);if(Zt.length>0){ge=o,o.apply();for(const v of Zt)Mt(i=o,tr,Ds).call(i,v,[],[]);o.deactivate()}Zt=a}}ge=t,Dt=r}S(this,Rr).clear(),Qa.delete(this)};let _n=ko;function ic(e){var t=La;La=!0;try{for(var r;;){if(ac(),Zt.length===0&&(ge==null||ge.flush(),Zt.length===0))return ms=null,r;Bi()}}finally{La=t}}function Bi(){var e=null;try{for(var t=0;Zt.length>0;){var r=_n.ensure();if(t++>1e3){var n,a;lc()}r.process(Zt),yn.clear()}}finally{Zt=[],ms=null,ha=null}}function lc(){try{Ld()}catch(e){hn(e,ms)}}let Sr=null;function Ho(e){var t=e.length;if(t!==0){for(var r=0;r<t;){var n=e[r++];if((n.f&(Gr|qt))===0&&Ja(n)&&(Sr=new Set,xa(n),n.deps===null&&n.first===null&&n.nodes===null&&n.teardown===null&&n.ac===null&&sl(n),(Sr==null?void 0:Sr.size)>0)){yn.clear();for(const a of Sr){if((a.f&(Gr|qt))!==0)continue;const i=[a];let o=a.parent;for(;o!==null;)Sr.has(o)&&(Sr.delete(o),i.push(o)),o=o.parent;for(let l=i.length-1;l>=0;l--){const d=i[l];(d.f&(Gr|qt))===0&&xa(d)}}Sr.clear()}}Sr=null}}function Vi(e,t,r,n){if(!r.has(e)&&(r.add(e),e.reactions!==null))for(const a of e.reactions){const i=a.f;(i&Gt)!==0?Vi(a,t,r,n):(i&(ao|zn))!==0&&(i&Bt)===0&&Gi(a,t,n)&&(gt(a,Bt),Vr(a))}}function Gi(e,t,r){const n=r.get(e);if(n!==void 0)return n;if(e.deps!==null)for(const a of e.deps){if(pa.call(t,a))return!0;if((a.f&Gt)!==0&&Gi(a,t,r))return r.set(a,!0),!0}return r.set(e,!1),!1}function Vr(e){var t=ms=e,r=t.b;if(r!=null&&r.is_pending&&(e.f&(ba|Un|ps))!==0&&(e.f&_a)===0){r.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var n=t.f;if(ha!==null&&t===Ae&&(e.f&Un)===0)return;if((n&(Yn|Er))!==0){if((n&Ft)===0)return;t.f^=Ft}}Zt.push(t)}function Hi(e,t){if(!((e.f&Er)!==0&&(e.f&Ft)!==0)){(e.f&Bt)!==0?t.d.push(e):(e.f&Cr)!==0&&t.m.push(e),gt(e,Ft);for(var r=e.first;r!==null;)Hi(r,t),r=r.next}}function dc(e){let t=0,r=kn(0),n;return()=>{co()&&(s(r),fo(()=>(t===0&&(n=Wn(()=>e(()=>Ra(r)))),t+=1,()=>{Ur(()=>{t-=1,t===0&&(n==null||n(),n=void 0,Ra(r))})})))}}var cc=wn|ya;function uc(e,t,r,n){new fc(e,t,r,n)}var pr,to,jr,Fn,Xt,Dr,ir,zr,Xr,Bn,mn,ua,fa,va,Zr,us,Et,vc,pc,mc,Vs,as,ss,Gs;class fc{constructor(t,r,n,a){$e(this,Et);kr(this,"parent");kr(this,"is_pending",!1);kr(this,"transform_error");$e(this,pr);$e(this,to,null);$e(this,jr);$e(this,Fn);$e(this,Xt);$e(this,Dr,null);$e(this,ir,null);$e(this,zr,null);$e(this,Xr,null);$e(this,Bn,0);$e(this,mn,0);$e(this,ua,!1);$e(this,fa,new Set);$e(this,va,new Set);$e(this,Zr,null);$e(this,us,dc(()=>(he(this,Zr,kn(S(this,Bn))),()=>{he(this,Zr,null)})));var i;he(this,pr,t),he(this,jr,r),he(this,Fn,o=>{var l=Ae;l.b=this,l.f|=Ls,n(o)}),this.parent=Ae.b,this.transform_error=a??((i=this.parent)==null?void 0:i.transform_error)??(o=>o),he(this,Xt,Ya(()=>{Mt(this,Et,Vs).call(this)},cc))}defer_effect(t){Fi(t,S(this,fa),S(this,va))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!S(this,jr).pending}update_pending_count(t){Mt(this,Et,Gs).call(this,t),he(this,Bn,S(this,Bn)+t),!(!S(this,Zr)||S(this,ua))&&(he(this,ua,!0),Ur(()=>{he(this,ua,!1),S(this,Zr)&&ga(S(this,Zr),S(this,Bn))}))}get_effect_pending(){return S(this,us).call(this),s(S(this,Zr))}error(t){var r=S(this,jr).onerror;let n=S(this,jr).failed;if(!r&&!n)throw t;S(this,Dr)&&(Vt(S(this,Dr)),he(this,Dr,null)),S(this,ir)&&(Vt(S(this,ir)),he(this,ir,null)),S(this,zr)&&(Vt(S(this,zr)),he(this,zr,null));var a=!1,i=!1;const o=()=>{if(a){ec();return}a=!0,i&&Fd(),S(this,zr)!==null&&Gn(S(this,zr),()=>{he(this,zr,null)}),Mt(this,Et,ss).call(this,()=>{_n.ensure(),Mt(this,Et,Vs).call(this)})},l=d=>{try{i=!0,r==null||r(d,o),i=!1}catch(u){hn(u,S(this,Xt)&&S(this,Xt).parent)}n&&he(this,zr,Mt(this,Et,ss).call(this,()=>{_n.ensure();try{return er(()=>{var u=Ae;u.b=this,u.f|=Ls,n(S(this,pr),()=>d,()=>o)})}catch(u){return hn(u,S(this,Xt).parent),null}}))};Ur(()=>{var d;try{d=this.transform_error(t)}catch(u){hn(u,S(this,Xt)&&S(this,Xt).parent);return}d!==null&&typeof d=="object"&&typeof d.then=="function"?d.then(l,u=>hn(u,S(this,Xt)&&S(this,Xt).parent)):l(d)})}}pr=new WeakMap,to=new WeakMap,jr=new WeakMap,Fn=new WeakMap,Xt=new WeakMap,Dr=new WeakMap,ir=new WeakMap,zr=new WeakMap,Xr=new WeakMap,Bn=new WeakMap,mn=new WeakMap,ua=new WeakMap,fa=new WeakMap,va=new WeakMap,Zr=new WeakMap,us=new WeakMap,Et=new WeakSet,vc=function(){try{he(this,Dr,er(()=>S(this,Fn).call(this,S(this,pr))))}catch(t){this.error(t)}},pc=function(t){const r=S(this,jr).failed;r&&he(this,zr,er(()=>{r(S(this,pr),()=>t,()=>()=>{})}))},mc=function(){const t=S(this,jr).pending;t&&(this.is_pending=!0,he(this,ir,er(()=>t(S(this,pr)))),Ur(()=>{var r=he(this,Xr,document.createDocumentFragment()),n=Kr();r.append(n),he(this,Dr,Mt(this,Et,ss).call(this,()=>(_n.ensure(),er(()=>S(this,Fn).call(this,n))))),S(this,mn)===0&&(S(this,pr).before(r),he(this,Xr,null),Gn(S(this,ir),()=>{he(this,ir,null)}),Mt(this,Et,as).call(this))}))},Vs=function(){try{if(this.is_pending=this.has_pending_snippet(),he(this,mn,0),he(this,Bn,0),he(this,Dr,er(()=>{S(this,Fn).call(this,S(this,pr))})),S(this,mn)>0){var t=he(this,Xr,document.createDocumentFragment());mo(S(this,Dr),t);const r=S(this,jr).pending;he(this,ir,er(()=>r(S(this,pr))))}else Mt(this,Et,as).call(this)}catch(r){this.error(r)}},as=function(){this.is_pending=!1;for(const t of S(this,fa))gt(t,Bt),Vr(t);for(const t of S(this,va))gt(t,Cr),Vr(t);S(this,fa).clear(),S(this,va).clear()},ss=function(t){var r=Ae,n=Me,a=Lt;xr(S(this,Xt)),gr(S(this,Xt)),ma(S(this,Xt).ctx);try{return t()}catch(i){return ji(i),null}finally{xr(r),gr(n),ma(a)}},Gs=function(t){var r;if(!this.has_pending_snippet()){this.parent&&Mt(r=this.parent,Et,Gs).call(r,t);return}he(this,mn,S(this,mn)+t),S(this,mn)===0&&(Mt(this,Et,as).call(this),S(this,ir)&&Gn(S(this,ir),()=>{he(this,ir,null)}),S(this,Xr)&&(S(this,pr).before(S(this,Xr)),he(this,Xr,null)))};function Ui(e,t,r,n){const a=Ka()?Wa:oo;var i=e.filter(v=>!v.settled);if(r.length===0&&i.length===0){n(t.map(a));return}var o=Ae,l=hc(),d=i.length===1?i[0].promise:i.length>1?Promise.all(i.map(v=>v.promise)):null;function u(v){l();try{n(v)}catch(_){(o.f&Gr)===0&&hn(_,o)}Hs()}if(r.length===0){d.then(()=>u(t.map(a)));return}function p(){l(),Promise.all(r.map(v=>xc(v))).then(v=>u([...t.map(a),...v])).catch(v=>hn(v,o))}d?d.then(p):p()}function hc(){var e=Ae,t=Me,r=Lt,n=ge;return function(i=!0){xr(e),gr(t),ma(r),i&&(n==null||n.activate())}}function Hs(e=!0){xr(null),gr(null),ma(null),e&&(ge==null||ge.deactivate())}function gc(){var e=Ae.b,t=ge,r=e.is_rendered();return e.update_pending_count(1),t.increment(r),()=>{e.update_pending_count(-1),t.decrement(r)}}function Wa(e){var t=Gt|Bt,r=Me!==null&&(Me.f&Gt)!==0?Me:null;return Ae!==null&&(Ae.f|=ya),{ctx:Lt,deps:null,effects:null,equals:Li,f:t,fn:e,reactions:null,rv:0,v:It,wv:0,parent:r??Ae,ac:null}}function xc(e,t,r){Ae===null&&Td();var a=void 0,i=kn(It),o=!Me,l=new Map;return Pc(()=>{var _;var d=Ai();a=d.promise;try{Promise.resolve(e()).then(d.resolve,d.reject).finally(Hs)}catch(E){d.reject(E),Hs()}var u=ge;if(o){var p=gc();(_=l.get(u))==null||_.reject(Ln),l.delete(u),l.set(u,d)}const v=(E,k=void 0)=>{if(u.activate(),k)k!==Ln&&(i.f|=bn,ga(i,k));else{(i.f&bn)!==0&&(i.f^=bn),ga(i,E);for(const[z,g]of l){if(l.delete(z),z===u)break;g.reject(Ln)}}p&&p()};d.promise.then(v,E=>v(null,E||"unknown"))}),gs(()=>{for(const d of l.values())d.reject(Ln)}),new Promise(d=>{function u(p){function v(){p===a?d(i):u(a)}p.then(v,v)}u(a)})}function ne(e){const t=Wa(e);return ll(t),t}function oo(e){const t=Wa(e);return t.equals=Oi,t}function bc(e){var t=e.effects;if(t!==null){e.effects=null;for(var r=0;r<t.length;r+=1)Vt(t[r])}}function _c(e){for(var t=e.parent;t!==null;){if((t.f&Gt)===0)return(t.f&Gr)===0?t:null;t=t.parent}return null}function io(e){var t,r=Ae;xr(_c(e));try{e.f&=~Kn,bc(e),t=fl(e)}finally{xr(r)}return t}function Ki(e){var t=io(e);if(!e.equals(t)&&(e.wv=cl(),(!(ge!=null&&ge.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){gt(e,Ft);return}Sn||(Dt!==null?(co()||ge!=null&&ge.is_fork)&&Dt.set(e,t):so(e))}function yc(e){var t,r;if(e.effects!==null)for(const n of e.effects)(n.teardown||n.ac)&&((t=n.teardown)==null||t.call(n),(r=n.ac)==null||r.abort(Ln),n.teardown=Md,n.ac=null,Ba(n,0),vo(n))}function Wi(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&xa(t)}let Us=new Set;const yn=new Map;let qi=!1;function kn(e,t){var r={f:0,v:e,reactions:null,equals:Li,rv:0,wv:0};return r}function V(e,t){const r=kn(e);return ll(r),r}function wc(e,t=!1,r=!0){var a;const n=kn(e);return t||(n.equals=Oi),Ua&&r&&Lt!==null&&Lt.l!==null&&((a=Lt.l).s??(a.s=[])).push(n),n}function f(e,t,r=!1){Me!==null&&(!Ar||(Me.f&Go)!==0)&&Ka()&&(Me.f&(Gt|zn|ao|Go))!==0&&(hr===null||!pa.call(hr,e))&&Dd();let n=r?Ct(t):t;return ga(e,n)}function ga(e,t){if(!e.equals(t)){var r=e.v;Sn?yn.set(e,t):yn.set(e,r),e.v=t;var n=_n.ensure();if(n.capture(e,r),(e.f&Gt)!==0){const a=e;(e.f&Bt)!==0&&io(a),so(a)}e.wv=cl(),Yi(e,Bt),Ka()&&Ae!==null&&(Ae.f&Ft)!==0&&(Ae.f&(Er|Yn))===0&&(vr===null?Lc([e]):vr.push(e)),!n.is_fork&&Us.size>0&&!qi&&kc()}return t}function kc(){qi=!1;for(const e of Us)(e.f&Ft)!==0&&gt(e,Cr),Ja(e)&&xa(e);Us.clear()}function Oa(e,t=1){var r=s(e),n=t===1?r++:r--;return f(e,r),n}function Ra(e){f(e,e.v+1)}function Yi(e,t){var r=e.reactions;if(r!==null)for(var n=Ka(),a=r.length,i=0;i<a;i++){var o=r[i],l=o.f;if(!(!n&&o===Ae)){var d=(l&Bt)===0;if(d&&gt(o,t),(l&Gt)!==0){var u=o;Dt==null||Dt.delete(u),(l&Kn)===0&&(l&mr&&(o.f|=Kn),Yi(u,Cr))}else d&&((l&zn)!==0&&Sr!==null&&Sr.add(o),Vr(o))}}}function Ct(e){if(typeof e!="object"||e===null||Hr in e)return e;const t=no(e);if(t!==Sd&&t!==zd)return e;var r=new Map,n=ro(e),a=V(0),i=Hn,o=l=>{if(Hn===i)return l();var d=Me,u=Hn;gr(null),qo(i);var p=l();return gr(d),qo(u),p};return n&&r.set("length",V(e.length)),new Proxy(e,{defineProperty(l,d,u){(!("value"in u)||u.configurable===!1||u.enumerable===!1||u.writable===!1)&&Rd();var p=r.get(d);return p===void 0?o(()=>{var v=V(u.value);return r.set(d,v),v}):f(p,u.value,!0),!0},deleteProperty(l,d){var u=r.get(d);if(u===void 0){if(d in l){const p=o(()=>V(It));r.set(d,p),Ra(a)}}else f(u,It),Ra(a);return!0},get(l,d,u){var E;if(d===Hr)return e;var p=r.get(d),v=d in l;if(p===void 0&&(!v||(E=xn(l,d))!=null&&E.writable)&&(p=o(()=>{var k=Ct(v?l[d]:It),z=V(k);return z}),r.set(d,p)),p!==void 0){var _=s(p);return _===It?void 0:_}return Reflect.get(l,d,u)},getOwnPropertyDescriptor(l,d){var u=Reflect.getOwnPropertyDescriptor(l,d);if(u&&"value"in u){var p=r.get(d);p&&(u.value=s(p))}else if(u===void 0){var v=r.get(d),_=v==null?void 0:v.v;if(v!==void 0&&_!==It)return{enumerable:!0,configurable:!0,value:_,writable:!0}}return u},has(l,d){var _;if(d===Hr)return!0;var u=r.get(d),p=u!==void 0&&u.v!==It||Reflect.has(l,d);if(u!==void 0||Ae!==null&&(!p||(_=xn(l,d))!=null&&_.writable)){u===void 0&&(u=o(()=>{var E=p?Ct(l[d]):It,k=V(E);return k}),r.set(d,u));var v=s(u);if(v===It)return!1}return p},set(l,d,u,p){var L;var v=r.get(d),_=d in l;if(n&&d==="length")for(var E=u;E<v.v;E+=1){var k=r.get(E+"");k!==void 0?f(k,It):E in l&&(k=o(()=>V(It)),r.set(E+"",k))}if(v===void 0)(!_||(L=xn(l,d))!=null&&L.writable)&&(v=o(()=>V(void 0)),f(v,Ct(u)),r.set(d,v));else{_=v.v!==It;var z=o(()=>Ct(u));f(v,z)}var g=Reflect.getOwnPropertyDescriptor(l,d);if(g!=null&&g.set&&g.set.call(p,u),!_){if(n&&typeof d=="string"){var A=r.get("length"),$=Number(d);Number.isInteger($)&&$>=A.v&&f(A,$+1)}Ra(a)}return!0},ownKeys(l){s(a);var d=Reflect.ownKeys(l).filter(v=>{var _=r.get(v);return _===void 0||_.v!==It});for(var[u,p]of r)p.v!==It&&!(u in l)&&d.push(u);return d},setPrototypeOf(){jd()}})}function Uo(e){try{if(e!==null&&typeof e=="object"&&Hr in e)return e[Hr]}catch{}return e}function Sc(e,t){return Object.is(Uo(e),Uo(t))}var Ks,Ji,Xi,Zi;function zc(){if(Ks===void 0){Ks=window,Ji=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,r=Text.prototype;Xi=xn(t,"firstChild").get,Zi=xn(t,"nextSibling").get,Vo(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Vo(r)&&(r.__t=void 0)}}function Kr(e=""){return document.createTextNode(e)}function Qr(e){return Xi.call(e)}function qa(e){return Zi.call(e)}function c(e,t){return Qr(e)}function G(e,t=!1){{var r=Qr(e);return r instanceof Comment&&r.data===""?qa(r):r}}function h(e,t=1,r=!1){let n=e;for(;t--;)n=qa(n);return n}function Mc(e){e.textContent=""}function Qi(){return!1}function lo(e,t,r){return document.createElementNS(t??Pi,e,void 0)}function Ac(e,t){if(t){const r=document.body;e.autofocus=!0,Ur(()=>{document.activeElement===r&&e.focus()})}}let Ko=!1;function Cc(){Ko||(Ko=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const r of e.target.elements)(t=r.__on_r)==null||t.call(r)})},{capture:!0}))}function hs(e){var t=Me,r=Ae;gr(null),xr(null);try{return e()}finally{gr(t),xr(r)}}function Ec(e,t,r,n=r){e.addEventListener(t,()=>hs(r));const a=e.__on_r;a?e.__on_r=()=>{a(),n(!0)}:e.__on_r=()=>n(!0),Cc()}function el(e){Ae===null&&(Me===null&&Id(),Pd()),Sn&&Nd()}function Tc(e,t){var r=t.last;r===null?t.last=t.first=e:(r.next=e,e.prev=r,t.last=e)}function Nr(e,t){var r=Ae;r!==null&&(r.f&qt)!==0&&(e|=qt);var n={ctx:Lt,deps:null,nodes:null,f:e|Bt|mr,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},a=n;if((e&ba)!==0)ha!==null?ha.push(n):Vr(n);else if(t!==null){try{xa(n)}catch(o){throw Vt(n),o}a.deps===null&&a.teardown===null&&a.nodes===null&&a.first===a.last&&(a.f&ya)===0&&(a=a.first,(e&zn)!==0&&(e&wn)!==0&&a!==null&&(a.f|=wn))}if(a!==null&&(a.parent=r,r!==null&&Tc(a,r),Me!==null&&(Me.f&Gt)!==0&&(e&Yn)===0)){var i=Me;(i.effects??(i.effects=[])).push(a)}return n}function co(){return Me!==null&&!Ar}function gs(e){const t=Nr(Un,null);return gt(t,Ft),t.teardown=e,t}function Fa(e){el();var t=Ae.f,r=!Me&&(t&Er)!==0&&(t&_a)===0;if(r){var n=Lt;(n.e??(n.e=[])).push(e)}else return tl(e)}function tl(e){return Nr(ba|Ci,e)}function $c(e){return el(),Nr(Un|Ci,e)}function Nc(e){_n.ensure();const t=Nr(Yn|ya,e);return(r={})=>new Promise(n=>{r.outro?Gn(t,()=>{Vt(t),n(void 0)}):(Vt(t),n(void 0))})}function uo(e){return Nr(ba,e)}function Pc(e){return Nr(ao|ya,e)}function fo(e,t=0){return Nr(Un|t,e)}function j(e,t=[],r=[],n=[]){Ui(n,t,r,a=>{Nr(Un,()=>e(...a.map(s)))})}function Ya(e,t=0){var r=Nr(zn|t,e);return r}function rl(e,t=0){var r=Nr(ps|t,e);return r}function er(e){return Nr(Er|ya,e)}function nl(e){var t=e.teardown;if(t!==null){const r=Sn,n=Me;Wo(!0),gr(null);try{t.call(null)}finally{Wo(r),gr(n)}}}function vo(e,t=!1){var r=e.first;for(e.first=e.last=null;r!==null;){const a=r.ac;a!==null&&hs(()=>{a.abort(Ln)});var n=r.next;(r.f&Yn)!==0?r.parent=null:Vt(r,t),r=n}}function Ic(e){for(var t=e.first;t!==null;){var r=t.next;(t.f&Er)===0&&Vt(t),t=r}}function Vt(e,t=!0){var r=!1;(t||(e.f&Cd)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(al(e.nodes.start,e.nodes.end),r=!0),vo(e,t&&!r),Ba(e,0),gt(e,Gr);var n=e.nodes&&e.nodes.t;if(n!==null)for(const i of n)i.stop();nl(e);var a=e.parent;a!==null&&a.first!==null&&sl(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function al(e,t){for(;e!==null;){var r=e===t?null:qa(e);e.remove(),e=r}}function sl(e){var t=e.parent,r=e.prev,n=e.next;r!==null&&(r.next=n),n!==null&&(n.prev=r),t!==null&&(t.first===e&&(t.first=n),t.last===e&&(t.last=r))}function Gn(e,t,r=!0){var n=[];ol(e,n,!0);var a=()=>{r&&Vt(e),t&&t()},i=n.length;if(i>0){var o=()=>--i||a();for(var l of n)l.out(o)}else a()}function ol(e,t,r){if((e.f&qt)===0){e.f^=qt;var n=e.nodes&&e.nodes.t;if(n!==null)for(const l of n)(l.is_global||r)&&t.push(l);for(var a=e.first;a!==null;){var i=a.next,o=(a.f&wn)!==0||(a.f&Er)!==0&&(e.f&zn)!==0;ol(a,t,o?r:!1),a=i}}}function po(e){il(e,!0)}function il(e,t){if((e.f&qt)!==0){e.f^=qt;for(var r=e.first;r!==null;){var n=r.next,a=(r.f&wn)!==0||(r.f&Er)!==0;il(r,a?t:!1),r=n}var i=e.nodes&&e.nodes.t;if(i!==null)for(const o of i)(o.is_global||t)&&o.in()}}function mo(e,t){if(e.nodes)for(var r=e.nodes.start,n=e.nodes.end;r!==null;){var a=r===n?null:qa(r);t.append(r),r=a}}let os=!1,Sn=!1;function Wo(e){Sn=e}let Me=null,Ar=!1;function gr(e){Me=e}let Ae=null;function xr(e){Ae=e}let hr=null;function ll(e){Me!==null&&(hr===null?hr=[e]:hr.push(e))}let Qt=null,or=0,vr=null;function Lc(e){vr=e}let dl=1,Rn=0,Hn=Rn;function qo(e){Hn=e}function cl(){return++dl}function Ja(e){var t=e.f;if((t&Bt)!==0)return!0;if(t&Gt&&(e.f&=~Kn),(t&Cr)!==0){for(var r=e.deps,n=r.length,a=0;a<n;a++){var i=r[a];if(Ja(i)&&Ki(i),i.wv>e.wv)return!0}(t&mr)!==0&&Dt===null&&gt(e,Ft)}return!1}function ul(e,t,r=!0){var n=e.reactions;if(n!==null&&!(hr!==null&&pa.call(hr,e)))for(var a=0;a<n.length;a++){var i=n[a];(i.f&Gt)!==0?ul(i,t,!1):t===i&&(r?gt(i,Bt):(i.f&Ft)!==0&&gt(i,Cr),Vr(i))}}function fl(e){var z;var t=Qt,r=or,n=vr,a=Me,i=hr,o=Lt,l=Ar,d=Hn,u=e.f;Qt=null,or=0,vr=null,Me=(u&(Er|Yn))===0?e:null,hr=null,ma(e.ctx),Ar=!1,Hn=++Rn,e.ac!==null&&(hs(()=>{e.ac.abort(Ln)}),e.ac=null);try{e.f|=Os;var p=e.fn,v=p();e.f|=_a;var _=e.deps,E=ge==null?void 0:ge.is_fork;if(Qt!==null){var k;if(E||Ba(e,or),_!==null&&or>0)for(_.length=or+Qt.length,k=0;k<Qt.length;k++)_[or+k]=Qt[k];else e.deps=_=Qt;if(co()&&(e.f&mr)!==0)for(k=or;k<_.length;k++)((z=_[k]).reactions??(z.reactions=[])).push(e)}else!E&&_!==null&&or<_.length&&(Ba(e,or),_.length=or);if(Ka()&&vr!==null&&!Ar&&_!==null&&(e.f&(Gt|Cr|Bt))===0)for(k=0;k<vr.length;k++)ul(vr[k],e);if(a!==null&&a!==e){if(Rn++,a.deps!==null)for(let g=0;g<r;g+=1)a.deps[g].rv=Rn;if(t!==null)for(const g of t)g.rv=Rn;vr!==null&&(n===null?n=vr:n.push(...vr))}return(e.f&bn)!==0&&(e.f^=bn),v}catch(g){return ji(g)}finally{e.f^=Os,Qt=t,or=r,vr=n,Me=a,hr=i,ma(o),Ar=l,Hn=d}}function Oc(e,t){let r=t.reactions;if(r!==null){var n=wd.call(r,e);if(n!==-1){var a=r.length-1;a===0?r=t.reactions=null:(r[n]=r[a],r.pop())}}if(r===null&&(t.f&Gt)!==0&&(Qt===null||!pa.call(Qt,t))){var i=t;(i.f&mr)!==0&&(i.f^=mr,i.f&=~Kn),so(i),yc(i),Ba(i,0)}}function Ba(e,t){var r=e.deps;if(r!==null)for(var n=t;n<r.length;n++)Oc(e,r[n])}function xa(e){var t=e.f;if((t&Gr)===0){gt(e,Ft);var r=Ae,n=os;Ae=e,os=!0;try{(t&(zn|ps))!==0?Ic(e):vo(e),nl(e);var a=fl(e);e.teardown=typeof a=="function"?a:null,e.wv=dl;var i;Ps&&rc&&(e.f&Bt)!==0&&e.deps}finally{os=n,Ae=r}}}async function Rc(){await Promise.resolve(),ic()}function s(e){var t=e.f,r=(t&Gt)!==0;if(Me!==null&&!Ar){var n=Ae!==null&&(Ae.f&Gr)!==0;if(!n&&(hr===null||!pa.call(hr,e))){var a=Me.deps;if((Me.f&Os)!==0)e.rv<Rn&&(e.rv=Rn,Qt===null&&a!==null&&a[or]===e?or++:Qt===null?Qt=[e]:Qt.push(e));else{(Me.deps??(Me.deps=[])).push(e);var i=e.reactions;i===null?e.reactions=[Me]:pa.call(i,Me)||i.push(Me)}}}if(Sn&&yn.has(e))return yn.get(e);if(r){var o=e;if(Sn){var l=o.v;return((o.f&Ft)===0&&o.reactions!==null||pl(o))&&(l=io(o)),yn.set(o,l),l}var d=(o.f&mr)===0&&!Ar&&Me!==null&&(os||(Me.f&mr)!==0),u=(o.f&_a)===0;Ja(o)&&(d&&(o.f|=mr),Ki(o)),d&&!u&&(Wi(o),vl(o))}if(Dt!=null&&Dt.has(e))return Dt.get(e);if((e.f&bn)!==0)throw e.v;return e.v}function vl(e){if(e.f|=mr,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&Gt)!==0&&(t.f&mr)===0&&(Wi(t),vl(t))}function pl(e){if(e.v===It)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(yn.has(t)||(t.f&Gt)!==0&&pl(t))return!0;return!1}function Wn(e){var t=Ar;try{return Ar=!0,e()}finally{Ar=t}}function In(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(Hr in e)Ws(e);else if(!Array.isArray(e))for(let t in e){const r=e[t];typeof r=="object"&&r&&Hr in r&&Ws(r)}}}function Ws(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let n in e)try{Ws(e[n],t)}catch{}const r=no(e);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const n=Mi(r);for(let a in n){const i=n[a].get;if(i)try{i.call(e)}catch{}}}}}function jc(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const Dc=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function Fc(e){return Dc.includes(e)}const Bc={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function Vc(e){return e=e.toLowerCase(),Bc[e]??e}const Gc=["touchstart","touchmove"];function Hc(e){return Gc.includes(e)}const jn=Symbol("events"),ml=new Set,qs=new Set;function hl(e,t,r,n={}){function a(i){if(n.capture||Ys.call(t,i),!i.cancelBubble)return hs(()=>r==null?void 0:r.call(this,i))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Ur(()=>{t.addEventListener(e,a,n)}):t.addEventListener(e,a,n),a}function ls(e,t,r,n,a){var i={capture:n,passive:a},o=hl(e,t,r,i);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&gs(()=>{t.removeEventListener(e,o,i)})}function W(e,t,r){(t[jn]??(t[jn]={}))[e]=r}function Mn(e){for(var t=0;t<e.length;t++)ml.add(e[t]);for(var r of qs)r(e)}let Yo=null;function Ys(e){var g,A;var t=this,r=t.ownerDocument,n=e.type,a=((g=e.composedPath)==null?void 0:g.call(e))||[],i=a[0]||e.target;Yo=e;var o=0,l=Yo===e&&e[jn];if(l){var d=a.indexOf(l);if(d!==-1&&(t===document||t===window)){e[jn]=t;return}var u=a.indexOf(t);if(u===-1)return;d<=u&&(o=d)}if(i=a[o]||e.target,i!==t){kd(e,"currentTarget",{configurable:!0,get(){return i||r}});var p=Me,v=Ae;gr(null),xr(null);try{for(var _,E=[];i!==null;){var k=i.assignedSlot||i.parentNode||i.host||null;try{var z=(A=i[jn])==null?void 0:A[n];z!=null&&(!i.disabled||e.target===i)&&z.call(i,e)}catch($){_?E.push($):_=$}if(e.cancelBubble||k===t||k===null)break;i=k}if(_){for(let $ of E)queueMicrotask(()=>{throw $});throw _}}finally{e[jn]=t,delete e.currentTarget,gr(p),xr(v)}}}var Si;const Ms=((Si=globalThis==null?void 0:globalThis.window)==null?void 0:Si.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function Uc(e){return(Ms==null?void 0:Ms.createHTML(e))??e}function gl(e){var t=lo("template");return t.innerHTML=Uc(e.replaceAll("<!>","<!---->")),t.content}function qn(e,t){var r=Ae;r.nodes===null&&(r.nodes={start:e,end:t,a:null,t:null})}function w(e,t){var r=(t&Yd)!==0,n=(t&Jd)!==0,a,i=!e.startsWith("<!>");return()=>{a===void 0&&(a=gl(i?e:"<!>"+e),r||(a=Qr(a)));var o=n||Ji?document.importNode(a,!0):a.cloneNode(!0);if(r){var l=Qr(o),d=o.lastChild;qn(l,d)}else qn(o,o);return o}}function Kc(e,t,r="svg"){var n=!e.startsWith("<!>"),a=`<${r}>${n?e:"<!>"+e}</${r}>`,i;return()=>{if(!i){var o=gl(a),l=Qr(o);i=Qr(l)}var d=i.cloneNode(!0);return qn(d,d),d}}function Wc(e,t){return Kc(e,t,"svg")}function ja(e=""){{var t=Kr(e+"");return qn(t,t),t}}function ce(){var e=document.createDocumentFragment(),t=document.createComment(""),r=Kr();return e.append(t,r),qn(t,r),e}function m(e,t){e!==null&&e.before(t)}function D(e,t){var r=t==null?"":typeof t=="object"?`${t}`:t;r!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=r,e.nodeValue=`${r}`)}function qc(e,t){return Yc(e,t)}const es=new Map;function Yc(e,{target:t,anchor:r,props:n={},events:a,context:i,intro:o=!0,transformError:l}){zc();var d=void 0,u=Nc(()=>{var p=r??t.appendChild(Kr());uc(p,{pending:()=>{}},E=>{Tr({});var k=Lt;i&&(k.c=i),a&&(n.$$events=a),d=e(E,n)||{},$r()},l);var v=new Set,_=E=>{for(var k=0;k<E.length;k++){var z=E[k];if(!v.has(z)){v.add(z);var g=Hc(z);for(const L of[t,document]){var A=es.get(L);A===void 0&&(A=new Map,es.set(L,A));var $=A.get(z);$===void 0?(L.addEventListener(z,Ys,{passive:g}),A.set(z,1)):A.set(z,$+1)}}}};return _(vs(ml)),qs.add(_),()=>{var g;for(var E of v)for(const A of[t,document]){var k=es.get(A),z=k.get(E);--z==0?(A.removeEventListener(E,Ys),k.delete(E),k.size===0&&es.delete(A)):k.set(E,z)}qs.delete(_),p!==r&&((g=p.parentNode)==null||g.removeChild(p))}});return Jc.set(d,u),d}let Jc=new WeakMap;var Mr,Fr,lr,Vn,Ga,Ha,fs;class ho{constructor(t,r=!0){kr(this,"anchor");$e(this,Mr,new Map);$e(this,Fr,new Map);$e(this,lr,new Map);$e(this,Vn,new Set);$e(this,Ga,!0);$e(this,Ha,t=>{if(S(this,Mr).has(t)){var r=S(this,Mr).get(t),n=S(this,Fr).get(r);if(n)po(n),S(this,Vn).delete(r);else{var a=S(this,lr).get(r);a&&(a.effect.f&qt)===0&&(S(this,Fr).set(r,a.effect),S(this,lr).delete(r),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),n=a.effect)}for(const[i,o]of S(this,Mr)){if(S(this,Mr).delete(i),i===t)break;const l=S(this,lr).get(o);l&&(Vt(l.effect),S(this,lr).delete(o))}for(const[i,o]of S(this,Fr)){if(i===r||S(this,Vn).has(i)||(o.f&qt)!==0)continue;const l=()=>{if(Array.from(S(this,Mr).values()).includes(i)){var u=document.createDocumentFragment();mo(o,u),u.append(Kr()),S(this,lr).set(i,{effect:o,fragment:u})}else Vt(o);S(this,Vn).delete(i),S(this,Fr).delete(i)};S(this,Ga)||!n?(S(this,Vn).add(i),Gn(o,l,!1)):l()}}});$e(this,fs,t=>{S(this,Mr).delete(t);const r=Array.from(S(this,Mr).values());for(const[n,a]of S(this,lr))r.includes(n)||(Vt(a.effect),S(this,lr).delete(n))});this.anchor=t,he(this,Ga,r)}ensure(t,r){var n=ge,a=Qi();if(r&&!S(this,Fr).has(t)&&!S(this,lr).has(t))if(a){var i=document.createDocumentFragment(),o=Kr();i.append(o),S(this,lr).set(t,{effect:er(()=>r(o)),fragment:i})}else S(this,Fr).set(t,er(()=>r(this.anchor)));if(S(this,Mr).set(n,t),a){for(const[l,d]of S(this,Fr))l===t?n.unskip_effect(d):n.skip_effect(d);for(const[l,d]of S(this,lr))l===t?n.unskip_effect(d.effect):n.skip_effect(d.effect);n.oncommit(S(this,Ha)),n.ondiscard(S(this,fs))}else S(this,Ha).call(this,n)}}Mr=new WeakMap,Fr=new WeakMap,lr=new WeakMap,Vn=new WeakMap,Ga=new WeakMap,Ha=new WeakMap,fs=new WeakMap;function T(e,t,r=!1){var n=new ho(e),a=r?wn:0;function i(o,l){n.ensure(o,l)}Ya(()=>{var o=!1;t((l,d=0)=>{o=!0,i(d,l)}),o||i(-1,null)},a)}function tt(e,t){return t}function Xc(e,t,r){for(var n=[],a=t.length,i,o=t.length,l=0;l<a;l++){let v=t[l];Gn(v,()=>{if(i){if(i.pending.delete(v),i.done.add(v),i.pending.size===0){var _=e.outrogroups;Js(e,vs(i.done)),_.delete(i),_.size===0&&(e.outrogroups=null)}}else o-=1},!1)}if(o===0){var d=n.length===0&&r!==null;if(d){var u=r,p=u.parentNode;Mc(p),p.append(u),e.items.clear()}Js(e,t,!d)}else i={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(i)}function Js(e,t,r=!0){var n;if(e.pending.size>0){n=new Set;for(const o of e.pending.values())for(const l of o)n.add(e.items.get(l).e)}for(var a=0;a<t.length;a++){var i=t[a];if(n!=null&&n.has(i)){i.f|=Br;const o=document.createDocumentFragment();mo(i,o)}else Vt(t[a],r)}}var Jo;function rt(e,t,r,n,a,i=null){var o=e,l=new Map,d=(t&$i)!==0;if(d){var u=e;o=u.appendChild(Kr())}var p=null,v=oo(()=>{var L=r();return ro(L)?L:L==null?[]:vs(L)}),_,E=new Map,k=!0;function z(L){($.effect.f&Gr)===0&&($.pending.delete(L),$.fallback=p,Zc($,_,o,t,n),p!==null&&(_.length===0?(p.f&Br)===0?po(p):(p.f^=Br,Ia(p,null,o)):Gn(p,()=>{p=null})))}function g(L){$.pending.delete(L)}var A=Ya(()=>{_=s(v);for(var L=_.length,M=new Set,O=ge,J=Qi(),q=0;q<L;q+=1){var x=_[q],F=n(x,q),Y=k?null:l.get(F);Y?(Y.v&&ga(Y.v,x),Y.i&&ga(Y.i,q),J&&O.unskip_effect(Y.e)):(Y=Qc(l,k?o:Jo??(Jo=Kr()),x,F,q,a,t,r),k||(Y.e.f|=Br),l.set(F,Y)),M.add(F)}if(L===0&&i&&!p&&(k?p=er(()=>i(o)):(p=er(()=>i(Jo??(Jo=Kr()))),p.f|=Br)),L>M.size&&$d(),!k)if(E.set(O,M),J){for(const[fe,we]of l)M.has(fe)||O.skip_effect(we.e);O.oncommit(z),O.ondiscard(g)}else z(O);s(v)}),$={effect:A,items:l,pending:E,outrogroups:null,fallback:p};k=!1}function Ta(e){for(;e!==null&&(e.f&Er)===0;)e=e.next;return e}function Zc(e,t,r,n,a){var Y,fe,we,He,P,R,X,ae,de;var i=(n&Gd)!==0,o=t.length,l=e.items,d=Ta(e.effect.first),u,p=null,v,_=[],E=[],k,z,g,A;if(i)for(A=0;A<o;A+=1)k=t[A],z=a(k,A),g=l.get(z).e,(g.f&Br)===0&&((fe=(Y=g.nodes)==null?void 0:Y.a)==null||fe.measure(),(v??(v=new Set)).add(g));for(A=0;A<o;A+=1){if(k=t[A],z=a(k,A),g=l.get(z).e,e.outrogroups!==null)for(const H of e.outrogroups)H.pending.delete(g),H.done.delete(g);if((g.f&Br)!==0)if(g.f^=Br,g===d)Ia(g,null,r);else{var $=p?p.next:d;g===e.effect.last&&(e.effect.last=g.prev),g.prev&&(g.prev.next=g.next),g.next&&(g.next.prev=g.prev),cn(e,p,g),cn(e,g,$),Ia(g,$,r),p=g,_=[],E=[],d=Ta(p.next);continue}if((g.f&qt)!==0&&(po(g),i&&((He=(we=g.nodes)==null?void 0:we.a)==null||He.unfix(),(v??(v=new Set)).delete(g))),g!==d){if(u!==void 0&&u.has(g)){if(_.length<E.length){var L=E[0],M;p=L.prev;var O=_[0],J=_[_.length-1];for(M=0;M<_.length;M+=1)Ia(_[M],L,r);for(M=0;M<E.length;M+=1)u.delete(E[M]);cn(e,O.prev,J.next),cn(e,p,O),cn(e,J,L),d=L,p=J,A-=1,_=[],E=[]}else u.delete(g),Ia(g,d,r),cn(e,g.prev,g.next),cn(e,g,p===null?e.effect.first:p.next),cn(e,p,g),p=g;continue}for(_=[],E=[];d!==null&&d!==g;)(u??(u=new Set)).add(d),E.push(d),d=Ta(d.next);if(d===null)continue}(g.f&Br)===0&&_.push(g),p=g,d=Ta(g.next)}if(e.outrogroups!==null){for(const H of e.outrogroups)H.pending.size===0&&(Js(e,vs(H.done)),(P=e.outrogroups)==null||P.delete(H));e.outrogroups.size===0&&(e.outrogroups=null)}if(d!==null||u!==void 0){var q=[];if(u!==void 0)for(g of u)(g.f&qt)===0&&q.push(g);for(;d!==null;)(d.f&qt)===0&&d!==e.fallback&&q.push(d),d=Ta(d.next);var x=q.length;if(x>0){var F=(n&$i)!==0&&o===0?r:null;if(i){for(A=0;A<x;A+=1)(X=(R=q[A].nodes)==null?void 0:R.a)==null||X.measure();for(A=0;A<x;A+=1)(de=(ae=q[A].nodes)==null?void 0:ae.a)==null||de.fix()}Xc(e,q,F)}}i&&Ur(()=>{var H,y;if(v!==void 0)for(g of v)(y=(H=g.nodes)==null?void 0:H.a)==null||y.apply()})}function Qc(e,t,r,n,a,i,o,l){var d=(o&Bd)!==0?(o&Hd)===0?wc(r,!1,!1):kn(r):null,u=(o&Vd)!==0?kn(a):null;return{v:d,i:u,e:er(()=>(i(t,d??r,u??a,l),()=>{e.delete(n)}))}}function Ia(e,t,r){if(e.nodes)for(var n=e.nodes.start,a=e.nodes.end,i=t&&(t.f&Br)===0?t.nodes.start:r;n!==null;){var o=qa(n);if(i.before(n),n===a)return;n=o}}function cn(e,t,r){t===null?e.effect.first=r:t.next=r,r===null?e.effect.last=t:r.prev=t}function Xo(e,t,r=!1,n=!1,a=!1){var i=e,o="";j(()=>{var l=Ae;if(o!==(o=t()??"")&&(l.nodes!==null&&(al(l.nodes.start,l.nodes.end),l.nodes=null),o!=="")){var d=r?Ii:n?Xd:void 0,u=lo(r?"svg":n?"math":"template",d);u.innerHTML=o;var p=r||n?u:u.content;if(qn(Qr(p),p.lastChild),r||n)for(;Qr(p);)i.before(Qr(p));else i.before(p)}})}function Ce(e,t,r,n,a){var l;var i=(l=t.$$slots)==null?void 0:l[r],o=!1;i===!0&&(i=t.children,o=!0),i===void 0||i(e,o?()=>n:n)}function Xs(e,t,...r){var n=new ho(e);Ya(()=>{const a=t()??null;n.ensure(a,a&&(i=>a(i,...r)))},wn)}function eu(e,t,r,n,a,i){var o=null,l=e,d=new ho(l,!1);Ya(()=>{const u=t()||null;var p=Ii;if(u===null){d.ensure(null,null);return}return d.ensure(u,v=>{if(u){if(o=lo(u,p),qn(o,o),n){var _=o.appendChild(Kr());n(o,_)}Ae.nodes.end=o,v.before(o)}}),()=>{}},wn),gs(()=>{})}function tu(e,t){var r=void 0,n;rl(()=>{r!==(r=t())&&(n&&(Vt(n),n=null),r&&(n=er(()=>{uo(()=>r(e))})))})}function xl(e){var t,r,n="";if(typeof e=="string"||typeof e=="number")n+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(r=xl(e[t]))&&(n&&(n+=" "),n+=r)}else for(r in e)e[r]&&(n&&(n+=" "),n+=r);return n}function bl(){for(var e,t,r=0,n="",a=arguments.length;r<a;r++)(e=arguments[r])&&(t=xl(e))&&(n&&(n+=" "),n+=t);return n}function Xe(e){return typeof e=="object"?bl(e):e??""}const Zo=[...` 	
\r\f \v\uFEFF`];function ru(e,t,r){var n=e==null?"":""+e;if(r){for(var a of Object.keys(r))if(r[a])n=n?n+" "+a:a;else if(n.length)for(var i=a.length,o=0;(o=n.indexOf(a,o))>=0;){var l=o+i;(o===0||Zo.includes(n[o-1]))&&(l===n.length||Zo.includes(n[l]))?n=(o===0?"":n.substring(0,o))+n.substring(l+1):o=l}}return n===""?null:n}function Qo(e,t=!1){var r=t?" !important;":";",n="";for(var a of Object.keys(e)){var i=e[a];i!=null&&i!==""&&(n+=" "+a+": "+i+r)}return n}function As(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function nu(e,t){if(t){var r="",n,a;if(Array.isArray(t)?(n=t[0],a=t[1]):n=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var i=!1,o=0,l=!1,d=[];n&&d.push(...Object.keys(n).map(As)),a&&d.push(...Object.keys(a).map(As));var u=0,p=-1;const z=e.length;for(var v=0;v<z;v++){var _=e[v];if(l?_==="/"&&e[v-1]==="*"&&(l=!1):i?i===_&&(i=!1):_==="/"&&e[v+1]==="*"?l=!0:_==='"'||_==="'"?i=_:_==="("?o++:_===")"&&o--,!l&&i===!1&&o===0){if(_===":"&&p===-1)p=v;else if(_===";"||v===z-1){if(p!==-1){var E=As(e.substring(u,p).trim());if(!d.includes(E)){_!==";"&&v++;var k=e.substring(u,v).trim();r+=" "+k+";"}}u=v+1,p=-1}}}}return n&&(r+=Qo(n)),a&&(r+=Qo(a,!0)),r=r.trim(),r===""?null:r}return e==null?null:String(e)}function Ze(e,t,r,n,a,i){var o=e.__className;if(o!==r||o===void 0){var l=ru(r,n,i);l==null?e.removeAttribute("class"):t?e.className=l:e.setAttribute("class",l),e.__className=r}else if(i&&a!==i)for(var d in i){var u=!!i[d];(a==null||u!==!!a[d])&&e.classList.toggle(d,u)}return i}function Cs(e,t={},r,n){for(var a in r){var i=r[a];t[a]!==i&&(r[a]==null?e.style.removeProperty(a):e.style.setProperty(a,i,n))}}function go(e,t,r,n){var a=e.__style;if(a!==t){var i=nu(t,n);i==null?e.removeAttribute("style"):e.style.cssText=i,e.__style=t}else n&&(Array.isArray(n)?(Cs(e,r==null?void 0:r[0],n[0]),Cs(e,r==null?void 0:r[1],n[1],"important")):Cs(e,r,n));return n}function Zs(e,t,r=!1){if(e.multiple){if(t==null)return;if(!ro(t))return Qd();for(var n of e.options)n.selected=t.includes(ei(n));return}for(n of e.options){var a=ei(n);if(Sc(a,t)){n.selected=!0;return}}(!r||t!==void 0)&&(e.selectedIndex=-1)}function au(e){var t=new MutationObserver(()=>{Zs(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),gs(()=>{t.disconnect()})}function ei(e){return"__value"in e?e.__value:e.value}const $a=Symbol("class"),Na=Symbol("style"),_l=Symbol("is custom element"),yl=Symbol("is html"),su=Ti?"option":"OPTION",ou=Ti?"select":"SELECT";function iu(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function Va(e,t,r,n){var a=wl(e);a[t]!==(a[t]=r)&&(t==="loading"&&(e[Ed]=r),r==null?e.removeAttribute(t):typeof r!="string"&&kl(e).includes(t)?e[t]=r:e.setAttribute(t,r))}function lu(e,t,r,n,a=!1,i=!1){var o=wl(e),l=o[_l],d=!o[yl],u=t||{},p=e.nodeName===su;for(var v in t)v in r||(r[v]=null);r.class?r.class=Xe(r.class):r[$a]&&(r.class=null),r[Na]&&(r.style??(r.style=null));var _=kl(e);for(const M in r){let O=r[M];if(p&&M==="value"&&O==null){e.value=e.__value="",u[M]=O;continue}if(M==="class"){var E=e.namespaceURI==="http://www.w3.org/1999/xhtml";Ze(e,E,O,n,t==null?void 0:t[$a],r[$a]),u[M]=O,u[$a]=r[$a];continue}if(M==="style"){go(e,O,t==null?void 0:t[Na],r[Na]),u[M]=O,u[Na]=r[Na];continue}var k=u[M];if(!(O===k&&!(O===void 0&&e.hasAttribute(M)))){u[M]=O;var z=M[0]+M[1];if(z!=="$$")if(z==="on"){const J={},q="$$"+M;let x=M.slice(2);var g=Fc(x);if(jc(x)&&(x=x.slice(0,-7),J.capture=!0),!g&&k){if(O!=null)continue;e.removeEventListener(x,u[q],J),u[q]=null}if(g)W(x,e,O),Mn([x]);else if(O!=null){let F=function(Y){u[M].call(this,Y)};var L=F;u[q]=hl(x,e,F,J)}}else if(M==="style")Va(e,M,O);else if(M==="autofocus")Ac(e,!!O);else if(!l&&(M==="__value"||M==="value"&&O!=null))e.value=e.__value=O;else if(M==="selected"&&p)iu(e,O);else{var A=M;d||(A=Vc(A));var $=A==="defaultValue"||A==="defaultChecked";if(O==null&&!l&&!$)if(o[M]=null,A==="value"||A==="checked"){let J=e;const q=t===void 0;if(A==="value"){let x=J.defaultValue;J.removeAttribute(A),J.defaultValue=x,J.value=J.__value=q?x:null}else{let x=J.defaultChecked;J.removeAttribute(A),J.defaultChecked=x,J.checked=q?x:!1}}else e.removeAttribute(M);else $||_.includes(A)&&(l||typeof O!="string")?(e[A]=O,A in o&&(o[A]=It)):typeof O!="function"&&Va(e,A,O)}}}return u}function ds(e,t,r=[],n=[],a=[],i,o=!1,l=!1){Ui(a,r,n,d=>{var u=void 0,p={},v=e.nodeName===ou,_=!1;if(rl(()=>{var k=t(...d.map(s)),z=lu(e,u,k,i,o,l);_&&v&&"value"in k&&Zs(e,k.value);for(let A of Object.getOwnPropertySymbols(p))k[A]||Vt(p[A]);for(let A of Object.getOwnPropertySymbols(k)){var g=k[A];A.description===Zd&&(!u||g!==u[A])&&(p[A]&&Vt(p[A]),p[A]=er(()=>tu(e,()=>g))),z[A]=g}u=z}),v){var E=e;uo(()=>{Zs(E,u.value,!0),au(E)})}_=!0})}function wl(e){return e.__attributes??(e.__attributes={[_l]:e.nodeName.includes("-"),[yl]:e.namespaceURI===Pi})}var ti=new Map;function kl(e){var t=e.getAttribute("is")||e.nodeName,r=ti.get(t);if(r)return r;ti.set(t,r=[]);for(var n,a=e,i=Element.prototype;i!==a;){n=Mi(a);for(var o in n)n[o].set&&r.push(o);a=no(a)}return r}function aa(e,t,r=t){var n=new WeakSet;Ec(e,"input",async a=>{var i=a?e.defaultValue:e.value;if(i=Es(e)?Ts(i):i,r(i),ge!==null&&n.add(ge),await Rc(),i!==(i=t())){var o=e.selectionStart,l=e.selectionEnd,d=e.value.length;if(e.value=i??"",l!==null){var u=e.value.length;o===l&&l===d&&u>d?(e.selectionStart=u,e.selectionEnd=u):(e.selectionStart=o,e.selectionEnd=Math.min(l,u))}}}),Wn(t)==null&&e.value&&(r(Es(e)?Ts(e.value):e.value),ge!==null&&n.add(ge)),fo(()=>{var a=t();if(e===document.activeElement){var i=Rs??ge;if(n.has(i))return}Es(e)&&a===Ts(e.value)||e.type==="date"&&!a&&!e.value||a!==e.value&&(e.value=a??"")})}function Es(e){var t=e.type;return t==="number"||t==="range"}function Ts(e){return e===""?null:+e}function ri(e,t){return e===t||(e==null?void 0:e[Hr])===t}function xo(e={},t,r,n){return uo(()=>{var a,i;return fo(()=>{a=i,i=[],Wn(()=>{e!==r(...i)&&(t(e,...i),a&&ri(r(...a),e)&&t(null,...a))})}),()=>{Ur(()=>{i&&ri(r(...i),e)&&t(null,...i)})}}),e}function du(e=!1){const t=Lt,r=t.l.u;if(!r)return;let n=()=>In(t.s);if(e){let a=0,i={};const o=Wa(()=>{let l=!1;const d=t.s;for(const u in d)d[u]!==i[u]&&(i[u]=d[u],l=!0);return l&&a++,a});n=()=>s(o)}r.b.length&&$c(()=>{ni(t,n),Is(r.b)}),Fa(()=>{const a=Wn(()=>r.m.map(Ad));return()=>{for(const i of a)typeof i=="function"&&i()}}),r.a.length&&Fa(()=>{ni(t,n),Is(r.a)})}function ni(e,t){if(e.l.s)for(const r of e.l.s)s(r);t()}let ts=!1;function cu(e){var t=ts;try{return ts=!1,[e(),ts]}finally{ts=t}}const uu={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function fu(e,t,r){return new Proxy({props:e,exclude:t},uu)}const vu={get(e,t){if(!e.exclude.includes(t))return s(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,r){if(!(t in e.special)){var n=Ae;try{xr(e.parent_effect),e.special[t]=dt({get[t](){return e.props[t]}},t,Ni)}finally{xr(n)}}return e.special[t](r),Oa(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),Oa(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function ye(e,t){return new Proxy({props:e,exclude:t,special:{},version:kn(0),parent_effect:Ae},vu)}const pu={get(e,t){let r=e.props.length;for(;r--;){let n=e.props[r];if(Ea(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n)return n[t]}},set(e,t,r){let n=e.props.length;for(;n--;){let a=e.props[n];Ea(a)&&(a=a());const i=xn(a,t);if(i&&i.set)return i.set(r),!0}return!1},getOwnPropertyDescriptor(e,t){let r=e.props.length;for(;r--;){let n=e.props[r];if(Ea(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n){const a=xn(n,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===Hr||t===Ei)return!1;for(let r of e.props)if(Ea(r)&&(r=r()),r!=null&&t in r)return!0;return!1},ownKeys(e){const t=[];for(let r of e.props)if(Ea(r)&&(r=r()),!!r){for(const n in r)t.includes(n)||t.push(n);for(const n of Object.getOwnPropertySymbols(r))t.includes(n)||t.push(n)}return t}};function Ne(...e){return new Proxy({props:e},pu)}function dt(e,t,r,n){var L;var a=!Ua||(r&Kd)!==0,i=(r&Wd)!==0,o=(r&qd)!==0,l=n,d=!0,u=()=>(d&&(d=!1,l=o?Wn(n):n),l),p;if(i){var v=Hr in e||Ei in e;p=((L=xn(e,t))==null?void 0:L.set)??(v&&t in e?M=>e[t]=M:void 0)}var _,E=!1;i?[_,E]=cu(()=>e[t]):_=e[t],_===void 0&&n!==void 0&&(_=u(),p&&(a&&Od(),p(_)));var k;if(a?k=()=>{var M=e[t];return M===void 0?u():(d=!0,M)}:k=()=>{var M=e[t];return M!==void 0&&(l=void 0),M===void 0?l:M},a&&(r&Ni)===0)return k;if(p){var z=e.$$legacy;return(function(M,O){return arguments.length>0?((!a||!O||z||E)&&p(O?k():M),M):k()})}var g=!1,A=((r&Ud)!==0?Wa:oo)(()=>(g=!1,k()));i&&s(A);var $=Ae;return(function(M,O){if(arguments.length>0){const J=O?s(A):a&&i?Ct(M):M;return f(A,J),g=!0,l!==void 0&&(l=J),M}return Sn&&g||($.f&Gr)!==0?A.v:s(A)})}const mu="5";var zi;typeof window<"u"&&((zi=window.__svelte??(window.__svelte={})).v??(zi.v=new Set)).add(mu);const br="";async function hu(){const e=await fetch(`${br}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function na(e,t=null,r=null){const n={provider:e};t&&(n.model=t),r&&(n.api_key=r);const a=await fetch(`${br}/api/configure`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)});if(!a.ok)throw new Error("설정 실패");return a.json()}async function gu(e){const t=await fetch(`${br}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function xu(e,{onProgress:t,onDone:r,onError:n}){const a=new AbortController;return fetch(`${br}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:a.signal}).then(async i=>{if(!i.ok){n==null||n("다운로드 실패");return}const o=i.body.getReader(),l=new TextDecoder;let d="";for(;;){const{done:u,value:p}=await o.read();if(u)break;d+=l.decode(p,{stream:!0});const v=d.split(`
`);d=v.pop()||"";for(const _ of v)if(_.startsWith("data:"))try{const E=JSON.parse(_.slice(5).trim());E.total&&E.completed!==void 0?t==null||t({total:E.total,completed:E.completed,status:E.status}):E.status&&(t==null||t({status:E.status}))}catch{}}r==null||r()}).catch(i=>{i.name!=="AbortError"&&(n==null||n(i.message))}),{abort:()=>a.abort()}}async function bu(){const e=await fetch(`${br}/api/oauth/authorize`);if(!e.ok)throw new Error("OAuth 인증 시작 실패");return e.json()}async function _u(){const e=await fetch(`${br}/api/oauth/status`);return e.ok?e.json():{done:!1}}async function yu(){const e=await fetch(`${br}/api/oauth/logout`,{method:"POST"});if(!e.ok)throw new Error("로그아웃 실패");return e.json()}async function ai(e,t=null,r=null){let n=`${br}/api/export/excel/${encodeURIComponent(e)}`;const a=new URLSearchParams;r?a.set("template_id",r):t&&t.length>0&&a.set("modules",t.join(","));const i=a.toString();i&&(n+=`?${i}`);const o=await fetch(n);if(!o.ok){const _=await o.json().catch(()=>({}));throw new Error(_.detail||"Excel 다운로드 실패")}const l=await o.blob(),u=(o.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),p=u?decodeURIComponent(u[1]):`${e}.xlsx`,v=document.createElement("a");return v.href=URL.createObjectURL(l),v.download=p,v.click(),URL.revokeObjectURL(v.href),p}async function wu(e){const t=await fetch(`${br}/api/data/sources/${encodeURIComponent(e)}`);if(!t.ok)throw new Error("소스 목록 조회 실패");return t.json()}async function ku(e,t,r=50){const n=new URLSearchParams;r!==50&&n.set("max_rows",String(r));const a=n.toString(),i=`${br}/api/data/preview/${encodeURIComponent(e)}/${encodeURIComponent(t)}${a?"?"+a:""}`,o=await fetch(i);if(!o.ok){const l=await o.json().catch(()=>({}));throw new Error(l.detail||"미리보기 실패")}return o.json()}async function Sl(e){const t=await fetch(`${br}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}function Su(e,t,r={},{onMeta:n,onSnapshot:a,onContext:i,onSystemPrompt:o,onToolCall:l,onToolResult:d,onChunk:u,onDone:p,onError:v},_=null){const E={question:t,stream:!0,...r};e&&(E.company=e),_&&_.length>0&&(E.history=_);const k=new AbortController;return fetch(`${br}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(E),signal:k.signal}).then(async z=>{if(!z.ok){const O=await z.json().catch(()=>({}));v==null||v(O.detail||"스트리밍 실패");return}const g=z.body.getReader(),A=new TextDecoder;let $="",L=!1,M=null;for(;;){const{done:O,value:J}=await g.read();if(O)break;$+=A.decode(J,{stream:!0});const q=$.split(`
`);$=q.pop()||"";for(const x of q)if(x.startsWith("event:"))M=x.slice(6).trim();else if(x.startsWith("data:")&&M){const F=x.slice(5).trim();try{const Y=JSON.parse(F);M==="meta"?n==null||n(Y):M==="snapshot"?a==null||a(Y):M==="context"?i==null||i(Y):M==="system_prompt"?o==null||o(Y):M==="tool_call"?l==null||l(Y):M==="tool_result"?d==null||d(Y):M==="chunk"?u==null||u(Y.text):M==="error"?v==null||v(Y.error,Y.action,Y.detail):M==="done"&&(L||(L=!0,p==null||p()))}catch{}M=null}}L||(L=!0,p==null||p())}).catch(z=>{z.name!=="AbortError"&&(v==null||v(z.message))}),{abort:()=>k.abort()}}const zu=(e,t)=>{const r=new Array(e.length+t.length);for(let n=0;n<e.length;n++)r[n]=e[n];for(let n=0;n<t.length;n++)r[e.length+n]=t[n];return r},Mu=(e,t)=>({classGroupId:e,validator:t}),zl=(e=new Map,t=null,r)=>({nextPart:e,validators:t,classGroupId:r}),cs="-",si=[],Au="arbitrary..",Cu=e=>{const t=Tu(e),{conflictingClassGroups:r,conflictingClassGroupModifiers:n}=e;return{getClassGroupId:o=>{if(o.startsWith("[")&&o.endsWith("]"))return Eu(o);const l=o.split(cs),d=l[0]===""&&l.length>1?1:0;return Ml(l,d,t)},getConflictingClassGroupIds:(o,l)=>{if(l){const d=n[o],u=r[o];return d?u?zu(u,d):d:u||si}return r[o]||si}}},Ml=(e,t,r)=>{if(e.length-t===0)return r.classGroupId;const a=e[t],i=r.nextPart.get(a);if(i){const u=Ml(e,t+1,i);if(u)return u}const o=r.validators;if(o===null)return;const l=t===0?e.join(cs):e.slice(t).join(cs),d=o.length;for(let u=0;u<d;u++){const p=o[u];if(p.validator(l))return p.classGroupId}},Eu=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),r=t.indexOf(":"),n=t.slice(0,r);return n?Au+n:void 0})(),Tu=e=>{const{theme:t,classGroups:r}=e;return $u(r,t)},$u=(e,t)=>{const r=zl();for(const n in e){const a=e[n];bo(a,r,n,t)}return r},bo=(e,t,r,n)=>{const a=e.length;for(let i=0;i<a;i++){const o=e[i];Nu(o,t,r,n)}},Nu=(e,t,r,n)=>{if(typeof e=="string"){Pu(e,t,r);return}if(typeof e=="function"){Iu(e,t,r,n);return}Lu(e,t,r,n)},Pu=(e,t,r)=>{const n=e===""?t:Al(t,e);n.classGroupId=r},Iu=(e,t,r,n)=>{if(Ou(e)){bo(e(n),t,r,n);return}t.validators===null&&(t.validators=[]),t.validators.push(Mu(r,e))},Lu=(e,t,r,n)=>{const a=Object.entries(e),i=a.length;for(let o=0;o<i;o++){const[l,d]=a[o];bo(d,Al(t,l),r,n)}},Al=(e,t)=>{let r=e;const n=t.split(cs),a=n.length;for(let i=0;i<a;i++){const o=n[i];let l=r.nextPart.get(o);l||(l=zl(),r.nextPart.set(o,l)),r=l}return r},Ou=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,Ru=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,r=Object.create(null),n=Object.create(null);const a=(i,o)=>{r[i]=o,t++,t>e&&(t=0,n=r,r=Object.create(null))};return{get(i){let o=r[i];if(o!==void 0)return o;if((o=n[i])!==void 0)return a(i,o),o},set(i,o){i in r?r[i]=o:a(i,o)}}},Qs="!",oi=":",ju=[],ii=(e,t,r,n,a)=>({modifiers:e,hasImportantModifier:t,baseClassName:r,maybePostfixModifierPosition:n,isExternal:a}),Du=e=>{const{prefix:t,experimentalParseClassName:r}=e;let n=a=>{const i=[];let o=0,l=0,d=0,u;const p=a.length;for(let z=0;z<p;z++){const g=a[z];if(o===0&&l===0){if(g===oi){i.push(a.slice(d,z)),d=z+1;continue}if(g==="/"){u=z;continue}}g==="["?o++:g==="]"?o--:g==="("?l++:g===")"&&l--}const v=i.length===0?a:a.slice(d);let _=v,E=!1;v.endsWith(Qs)?(_=v.slice(0,-1),E=!0):v.startsWith(Qs)&&(_=v.slice(1),E=!0);const k=u&&u>d?u-d:void 0;return ii(i,E,_,k)};if(t){const a=t+oi,i=n;n=o=>o.startsWith(a)?i(o.slice(a.length)):ii(ju,!1,o,void 0,!0)}if(r){const a=n;n=i=>r({className:i,parseClassName:a})}return n},Fu=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((r,n)=>{t.set(r,1e6+n)}),r=>{const n=[];let a=[];for(let i=0;i<r.length;i++){const o=r[i],l=o[0]==="[",d=t.has(o);l||d?(a.length>0&&(a.sort(),n.push(...a),a=[]),n.push(o)):a.push(o)}return a.length>0&&(a.sort(),n.push(...a)),n}},Bu=e=>({cache:Ru(e.cacheSize),parseClassName:Du(e),sortModifiers:Fu(e),...Cu(e)}),Vu=/\s+/,Gu=(e,t)=>{const{parseClassName:r,getClassGroupId:n,getConflictingClassGroupIds:a,sortModifiers:i}=t,o=[],l=e.trim().split(Vu);let d="";for(let u=l.length-1;u>=0;u-=1){const p=l[u],{isExternal:v,modifiers:_,hasImportantModifier:E,baseClassName:k,maybePostfixModifierPosition:z}=r(p);if(v){d=p+(d.length>0?" "+d:d);continue}let g=!!z,A=n(g?k.substring(0,z):k);if(!A){if(!g){d=p+(d.length>0?" "+d:d);continue}if(A=n(k),!A){d=p+(d.length>0?" "+d:d);continue}g=!1}const $=_.length===0?"":_.length===1?_[0]:i(_).join(":"),L=E?$+Qs:$,M=L+A;if(o.indexOf(M)>-1)continue;o.push(M);const O=a(A,g);for(let J=0;J<O.length;++J){const q=O[J];o.push(L+q)}d=p+(d.length>0?" "+d:d)}return d},Hu=(...e)=>{let t=0,r,n,a="";for(;t<e.length;)(r=e[t++])&&(n=Cl(r))&&(a&&(a+=" "),a+=n);return a},Cl=e=>{if(typeof e=="string")return e;let t,r="";for(let n=0;n<e.length;n++)e[n]&&(t=Cl(e[n]))&&(r&&(r+=" "),r+=t);return r},Uu=(e,...t)=>{let r,n,a,i;const o=d=>{const u=t.reduce((p,v)=>v(p),e());return r=Bu(u),n=r.cache.get,a=r.cache.set,i=l,l(d)},l=d=>{const u=n(d);if(u)return u;const p=Gu(d,r);return a(d,p),p};return i=o,(...d)=>i(Hu(...d))},Ku=[],At=e=>{const t=r=>r[e]||Ku;return t.isThemeGetter=!0,t},El=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Tl=/^\((?:(\w[\w-]*):)?(.+)\)$/i,Wu=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,qu=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,Yu=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,Ju=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,Xu=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,Zu=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,un=e=>Wu.test(e),me=e=>!!e&&!Number.isNaN(Number(e)),fn=e=>!!e&&Number.isInteger(Number(e)),$s=e=>e.endsWith("%")&&me(e.slice(0,-1)),Jr=e=>qu.test(e),$l=()=>!0,Qu=e=>Yu.test(e)&&!Ju.test(e),_o=()=>!1,ef=e=>Xu.test(e),tf=e=>Zu.test(e),rf=e=>!U(e)&&!K(e),nf=e=>An(e,Il,_o),U=e=>El.test(e),Nn=e=>An(e,Ll,Qu),li=e=>An(e,ff,me),af=e=>An(e,Rl,$l),sf=e=>An(e,Ol,_o),di=e=>An(e,Nl,_o),of=e=>An(e,Pl,tf),rs=e=>An(e,jl,ef),K=e=>Tl.test(e),Pa=e=>Jn(e,Ll),lf=e=>Jn(e,Ol),ci=e=>Jn(e,Nl),df=e=>Jn(e,Il),cf=e=>Jn(e,Pl),ns=e=>Jn(e,jl,!0),uf=e=>Jn(e,Rl,!0),An=(e,t,r)=>{const n=El.exec(e);return n?n[1]?t(n[1]):r(n[2]):!1},Jn=(e,t,r=!1)=>{const n=Tl.exec(e);return n?n[1]?t(n[1]):r:!1},Nl=e=>e==="position"||e==="percentage",Pl=e=>e==="image"||e==="url",Il=e=>e==="length"||e==="size"||e==="bg-size",Ll=e=>e==="length",ff=e=>e==="number",Ol=e=>e==="family-name",Rl=e=>e==="number"||e==="weight",jl=e=>e==="shadow",vf=()=>{const e=At("color"),t=At("font"),r=At("text"),n=At("font-weight"),a=At("tracking"),i=At("leading"),o=At("breakpoint"),l=At("container"),d=At("spacing"),u=At("radius"),p=At("shadow"),v=At("inset-shadow"),_=At("text-shadow"),E=At("drop-shadow"),k=At("blur"),z=At("perspective"),g=At("aspect"),A=At("ease"),$=At("animate"),L=()=>["auto","avoid","all","avoid-page","page","left","right","column"],M=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],O=()=>[...M(),K,U],J=()=>["auto","hidden","clip","visible","scroll"],q=()=>["auto","contain","none"],x=()=>[K,U,d],F=()=>[un,"full","auto",...x()],Y=()=>[fn,"none","subgrid",K,U],fe=()=>["auto",{span:["full",fn,K,U]},fn,K,U],we=()=>[fn,"auto",K,U],He=()=>["auto","min","max","fr",K,U],P=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],R=()=>["start","end","center","stretch","center-safe","end-safe"],X=()=>["auto",...x()],ae=()=>[un,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...x()],de=()=>[un,"screen","full","dvw","lvw","svw","min","max","fit",...x()],H=()=>[un,"screen","full","lh","dvh","lvh","svh","min","max","fit",...x()],y=()=>[e,K,U],ke=()=>[...M(),ci,di,{position:[K,U]}],ve=()=>["no-repeat",{repeat:["","x","y","space","round"]}],ct=()=>["auto","cover","contain",df,nf,{size:[K,U]}],We=()=>[$s,Pa,Nn],Ve=()=>["","none","full",u,K,U],Z=()=>["",me,Pa,Nn],se=()=>["solid","dashed","dotted","double"],ue=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],Se=()=>[me,$s,ci,di],Fe=()=>["","none",k,K,U],C=()=>["none",me,K,U],N=()=>["none",me,K,U],re=()=>[me,K,U],oe=()=>[un,"full",...x()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Jr],breakpoint:[Jr],color:[$l],container:[Jr],"drop-shadow":[Jr],ease:["in","out","in-out"],font:[rf],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Jr],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Jr],shadow:[Jr],spacing:["px",me],text:[Jr],"text-shadow":[Jr],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",un,U,K,g]}],container:["container"],columns:[{columns:[me,U,K,l]}],"break-after":[{"break-after":L()}],"break-before":[{"break-before":L()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:O()}],overflow:[{overflow:J()}],"overflow-x":[{"overflow-x":J()}],"overflow-y":[{"overflow-y":J()}],overscroll:[{overscroll:q()}],"overscroll-x":[{"overscroll-x":q()}],"overscroll-y":[{"overscroll-y":q()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:F()}],"inset-x":[{"inset-x":F()}],"inset-y":[{"inset-y":F()}],start:[{"inset-s":F(),start:F()}],end:[{"inset-e":F(),end:F()}],"inset-bs":[{"inset-bs":F()}],"inset-be":[{"inset-be":F()}],top:[{top:F()}],right:[{right:F()}],bottom:[{bottom:F()}],left:[{left:F()}],visibility:["visible","invisible","collapse"],z:[{z:[fn,"auto",K,U]}],basis:[{basis:[un,"full","auto",l,...x()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[me,un,"auto","initial","none",U]}],grow:[{grow:["",me,K,U]}],shrink:[{shrink:["",me,K,U]}],order:[{order:[fn,"first","last","none",K,U]}],"grid-cols":[{"grid-cols":Y()}],"col-start-end":[{col:fe()}],"col-start":[{"col-start":we()}],"col-end":[{"col-end":we()}],"grid-rows":[{"grid-rows":Y()}],"row-start-end":[{row:fe()}],"row-start":[{"row-start":we()}],"row-end":[{"row-end":we()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":He()}],"auto-rows":[{"auto-rows":He()}],gap:[{gap:x()}],"gap-x":[{"gap-x":x()}],"gap-y":[{"gap-y":x()}],"justify-content":[{justify:[...P(),"normal"]}],"justify-items":[{"justify-items":[...R(),"normal"]}],"justify-self":[{"justify-self":["auto",...R()]}],"align-content":[{content:["normal",...P()]}],"align-items":[{items:[...R(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...R(),{baseline:["","last"]}]}],"place-content":[{"place-content":P()}],"place-items":[{"place-items":[...R(),"baseline"]}],"place-self":[{"place-self":["auto",...R()]}],p:[{p:x()}],px:[{px:x()}],py:[{py:x()}],ps:[{ps:x()}],pe:[{pe:x()}],pbs:[{pbs:x()}],pbe:[{pbe:x()}],pt:[{pt:x()}],pr:[{pr:x()}],pb:[{pb:x()}],pl:[{pl:x()}],m:[{m:X()}],mx:[{mx:X()}],my:[{my:X()}],ms:[{ms:X()}],me:[{me:X()}],mbs:[{mbs:X()}],mbe:[{mbe:X()}],mt:[{mt:X()}],mr:[{mr:X()}],mb:[{mb:X()}],ml:[{ml:X()}],"space-x":[{"space-x":x()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":x()}],"space-y-reverse":["space-y-reverse"],size:[{size:ae()}],"inline-size":[{inline:["auto",...de()]}],"min-inline-size":[{"min-inline":["auto",...de()]}],"max-inline-size":[{"max-inline":["none",...de()]}],"block-size":[{block:["auto",...H()]}],"min-block-size":[{"min-block":["auto",...H()]}],"max-block-size":[{"max-block":["none",...H()]}],w:[{w:[l,"screen",...ae()]}],"min-w":[{"min-w":[l,"screen","none",...ae()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[o]},...ae()]}],h:[{h:["screen","lh",...ae()]}],"min-h":[{"min-h":["screen","lh","none",...ae()]}],"max-h":[{"max-h":["screen","lh",...ae()]}],"font-size":[{text:["base",r,Pa,Nn]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[n,uf,af]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",$s,U]}],"font-family":[{font:[lf,sf,t]}],"font-features":[{"font-features":[U]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[a,K,U]}],"line-clamp":[{"line-clamp":[me,"none",K,li]}],leading:[{leading:[i,...x()]}],"list-image":[{"list-image":["none",K,U]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",K,U]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:y()}],"text-color":[{text:y()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...se(),"wavy"]}],"text-decoration-thickness":[{decoration:[me,"from-font","auto",K,Nn]}],"text-decoration-color":[{decoration:y()}],"underline-offset":[{"underline-offset":[me,"auto",K,U]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:x()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",K,U]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",K,U]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:ke()}],"bg-repeat":[{bg:ve()}],"bg-size":[{bg:ct()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},fn,K,U],radial:["",K,U],conic:[fn,K,U]},cf,of]}],"bg-color":[{bg:y()}],"gradient-from-pos":[{from:We()}],"gradient-via-pos":[{via:We()}],"gradient-to-pos":[{to:We()}],"gradient-from":[{from:y()}],"gradient-via":[{via:y()}],"gradient-to":[{to:y()}],rounded:[{rounded:Ve()}],"rounded-s":[{"rounded-s":Ve()}],"rounded-e":[{"rounded-e":Ve()}],"rounded-t":[{"rounded-t":Ve()}],"rounded-r":[{"rounded-r":Ve()}],"rounded-b":[{"rounded-b":Ve()}],"rounded-l":[{"rounded-l":Ve()}],"rounded-ss":[{"rounded-ss":Ve()}],"rounded-se":[{"rounded-se":Ve()}],"rounded-ee":[{"rounded-ee":Ve()}],"rounded-es":[{"rounded-es":Ve()}],"rounded-tl":[{"rounded-tl":Ve()}],"rounded-tr":[{"rounded-tr":Ve()}],"rounded-br":[{"rounded-br":Ve()}],"rounded-bl":[{"rounded-bl":Ve()}],"border-w":[{border:Z()}],"border-w-x":[{"border-x":Z()}],"border-w-y":[{"border-y":Z()}],"border-w-s":[{"border-s":Z()}],"border-w-e":[{"border-e":Z()}],"border-w-bs":[{"border-bs":Z()}],"border-w-be":[{"border-be":Z()}],"border-w-t":[{"border-t":Z()}],"border-w-r":[{"border-r":Z()}],"border-w-b":[{"border-b":Z()}],"border-w-l":[{"border-l":Z()}],"divide-x":[{"divide-x":Z()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":Z()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...se(),"hidden","none"]}],"divide-style":[{divide:[...se(),"hidden","none"]}],"border-color":[{border:y()}],"border-color-x":[{"border-x":y()}],"border-color-y":[{"border-y":y()}],"border-color-s":[{"border-s":y()}],"border-color-e":[{"border-e":y()}],"border-color-bs":[{"border-bs":y()}],"border-color-be":[{"border-be":y()}],"border-color-t":[{"border-t":y()}],"border-color-r":[{"border-r":y()}],"border-color-b":[{"border-b":y()}],"border-color-l":[{"border-l":y()}],"divide-color":[{divide:y()}],"outline-style":[{outline:[...se(),"none","hidden"]}],"outline-offset":[{"outline-offset":[me,K,U]}],"outline-w":[{outline:["",me,Pa,Nn]}],"outline-color":[{outline:y()}],shadow:[{shadow:["","none",p,ns,rs]}],"shadow-color":[{shadow:y()}],"inset-shadow":[{"inset-shadow":["none",v,ns,rs]}],"inset-shadow-color":[{"inset-shadow":y()}],"ring-w":[{ring:Z()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:y()}],"ring-offset-w":[{"ring-offset":[me,Nn]}],"ring-offset-color":[{"ring-offset":y()}],"inset-ring-w":[{"inset-ring":Z()}],"inset-ring-color":[{"inset-ring":y()}],"text-shadow":[{"text-shadow":["none",_,ns,rs]}],"text-shadow-color":[{"text-shadow":y()}],opacity:[{opacity:[me,K,U]}],"mix-blend":[{"mix-blend":[...ue(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":ue()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[me]}],"mask-image-linear-from-pos":[{"mask-linear-from":Se()}],"mask-image-linear-to-pos":[{"mask-linear-to":Se()}],"mask-image-linear-from-color":[{"mask-linear-from":y()}],"mask-image-linear-to-color":[{"mask-linear-to":y()}],"mask-image-t-from-pos":[{"mask-t-from":Se()}],"mask-image-t-to-pos":[{"mask-t-to":Se()}],"mask-image-t-from-color":[{"mask-t-from":y()}],"mask-image-t-to-color":[{"mask-t-to":y()}],"mask-image-r-from-pos":[{"mask-r-from":Se()}],"mask-image-r-to-pos":[{"mask-r-to":Se()}],"mask-image-r-from-color":[{"mask-r-from":y()}],"mask-image-r-to-color":[{"mask-r-to":y()}],"mask-image-b-from-pos":[{"mask-b-from":Se()}],"mask-image-b-to-pos":[{"mask-b-to":Se()}],"mask-image-b-from-color":[{"mask-b-from":y()}],"mask-image-b-to-color":[{"mask-b-to":y()}],"mask-image-l-from-pos":[{"mask-l-from":Se()}],"mask-image-l-to-pos":[{"mask-l-to":Se()}],"mask-image-l-from-color":[{"mask-l-from":y()}],"mask-image-l-to-color":[{"mask-l-to":y()}],"mask-image-x-from-pos":[{"mask-x-from":Se()}],"mask-image-x-to-pos":[{"mask-x-to":Se()}],"mask-image-x-from-color":[{"mask-x-from":y()}],"mask-image-x-to-color":[{"mask-x-to":y()}],"mask-image-y-from-pos":[{"mask-y-from":Se()}],"mask-image-y-to-pos":[{"mask-y-to":Se()}],"mask-image-y-from-color":[{"mask-y-from":y()}],"mask-image-y-to-color":[{"mask-y-to":y()}],"mask-image-radial":[{"mask-radial":[K,U]}],"mask-image-radial-from-pos":[{"mask-radial-from":Se()}],"mask-image-radial-to-pos":[{"mask-radial-to":Se()}],"mask-image-radial-from-color":[{"mask-radial-from":y()}],"mask-image-radial-to-color":[{"mask-radial-to":y()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":M()}],"mask-image-conic-pos":[{"mask-conic":[me]}],"mask-image-conic-from-pos":[{"mask-conic-from":Se()}],"mask-image-conic-to-pos":[{"mask-conic-to":Se()}],"mask-image-conic-from-color":[{"mask-conic-from":y()}],"mask-image-conic-to-color":[{"mask-conic-to":y()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:ke()}],"mask-repeat":[{mask:ve()}],"mask-size":[{mask:ct()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",K,U]}],filter:[{filter:["","none",K,U]}],blur:[{blur:Fe()}],brightness:[{brightness:[me,K,U]}],contrast:[{contrast:[me,K,U]}],"drop-shadow":[{"drop-shadow":["","none",E,ns,rs]}],"drop-shadow-color":[{"drop-shadow":y()}],grayscale:[{grayscale:["",me,K,U]}],"hue-rotate":[{"hue-rotate":[me,K,U]}],invert:[{invert:["",me,K,U]}],saturate:[{saturate:[me,K,U]}],sepia:[{sepia:["",me,K,U]}],"backdrop-filter":[{"backdrop-filter":["","none",K,U]}],"backdrop-blur":[{"backdrop-blur":Fe()}],"backdrop-brightness":[{"backdrop-brightness":[me,K,U]}],"backdrop-contrast":[{"backdrop-contrast":[me,K,U]}],"backdrop-grayscale":[{"backdrop-grayscale":["",me,K,U]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[me,K,U]}],"backdrop-invert":[{"backdrop-invert":["",me,K,U]}],"backdrop-opacity":[{"backdrop-opacity":[me,K,U]}],"backdrop-saturate":[{"backdrop-saturate":[me,K,U]}],"backdrop-sepia":[{"backdrop-sepia":["",me,K,U]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":x()}],"border-spacing-x":[{"border-spacing-x":x()}],"border-spacing-y":[{"border-spacing-y":x()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",K,U]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[me,"initial",K,U]}],ease:[{ease:["linear","initial",A,K,U]}],delay:[{delay:[me,K,U]}],animate:[{animate:["none",$,K,U]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[z,K,U]}],"perspective-origin":[{"perspective-origin":O()}],rotate:[{rotate:C()}],"rotate-x":[{"rotate-x":C()}],"rotate-y":[{"rotate-y":C()}],"rotate-z":[{"rotate-z":C()}],scale:[{scale:N()}],"scale-x":[{"scale-x":N()}],"scale-y":[{"scale-y":N()}],"scale-z":[{"scale-z":N()}],"scale-3d":["scale-3d"],skew:[{skew:re()}],"skew-x":[{"skew-x":re()}],"skew-y":[{"skew-y":re()}],transform:[{transform:[K,U,"","none","gpu","cpu"]}],"transform-origin":[{origin:O()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:oe()}],"translate-x":[{"translate-x":oe()}],"translate-y":[{"translate-y":oe()}],"translate-z":[{"translate-z":oe()}],"translate-none":["translate-none"],accent:[{accent:y()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:y()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",K,U]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":x()}],"scroll-mx":[{"scroll-mx":x()}],"scroll-my":[{"scroll-my":x()}],"scroll-ms":[{"scroll-ms":x()}],"scroll-me":[{"scroll-me":x()}],"scroll-mbs":[{"scroll-mbs":x()}],"scroll-mbe":[{"scroll-mbe":x()}],"scroll-mt":[{"scroll-mt":x()}],"scroll-mr":[{"scroll-mr":x()}],"scroll-mb":[{"scroll-mb":x()}],"scroll-ml":[{"scroll-ml":x()}],"scroll-p":[{"scroll-p":x()}],"scroll-px":[{"scroll-px":x()}],"scroll-py":[{"scroll-py":x()}],"scroll-ps":[{"scroll-ps":x()}],"scroll-pe":[{"scroll-pe":x()}],"scroll-pbs":[{"scroll-pbs":x()}],"scroll-pbe":[{"scroll-pbe":x()}],"scroll-pt":[{"scroll-pt":x()}],"scroll-pr":[{"scroll-pr":x()}],"scroll-pb":[{"scroll-pb":x()}],"scroll-pl":[{"scroll-pl":x()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",K,U]}],fill:[{fill:["none",...y()]}],"stroke-w":[{stroke:[me,Pa,Nn,li]}],stroke:[{stroke:["none",...y()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},pf=Uu(vf);function Qe(...e){return pf(bl(e))}const eo="dartlab-conversations",ui=50;function mf(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function hf(){try{const e=localStorage.getItem(eo);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const gf=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function fi(e){return e.map(t=>({...t,messages:t.messages.map(r=>{if(r.role!=="assistant")return r;const n={};for(const[a,i]of Object.entries(r))gf.includes(a)||(n[a]=i);return n})}))}function vi(e){try{const t={conversations:fi(e.conversations),activeId:e.activeId};localStorage.setItem(eo,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:fi(e.conversations),activeId:e.activeId};localStorage.setItem(eo,JSON.stringify(t))}catch{}}}}function xf(){const e=hf();let t=V(Ct(e.conversations)),r=V(Ct(e.activeId));s(r)&&!s(t).find(z=>z.id===s(r))&&f(r,null);let n=null;function a(){n&&clearTimeout(n),n=setTimeout(()=>{vi({conversations:s(t),activeId:s(r)}),n=null},300)}function i(){n&&clearTimeout(n),n=null,vi({conversations:s(t),activeId:s(r)})}function o(){return s(t).find(z=>z.id===s(r))||null}function l(){const z={id:mf(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return f(t,[z,...s(t)],!0),s(t).length>ui&&f(t,s(t).slice(0,ui),!0),f(r,z.id,!0),i(),z.id}function d(z){s(t).find(g=>g.id===z)&&(f(r,z,!0),i())}function u(z,g,A=null){const $=o();if(!$)return;const L={role:z,text:g};A&&(L.meta=A),$.messages=[...$.messages,L],$.updatedAt=Date.now(),$.title==="새 대화"&&z==="user"&&($.title=g.length>30?g.slice(0,30)+"...":g),f(t,[...s(t)],!0),i()}function p(z){const g=o();if(!g||g.messages.length===0)return;const A=g.messages[g.messages.length-1];Object.assign(A,z),g.updatedAt=Date.now(),f(t,[...s(t)],!0),a()}function v(z){f(t,s(t).filter(g=>g.id!==z),!0),s(r)===z&&f(r,s(t).length>0?s(t)[0].id:null,!0),i()}function _(){const z=o();!z||z.messages.length===0||(z.messages=z.messages.slice(0,-1),z.updatedAt=Date.now(),f(t,[...s(t)],!0),i())}function E(z,g){const A=s(t).find($=>$.id===z);A&&(A.title=g,f(t,[...s(t)],!0),i())}function k(){f(t,[],!0),f(r,null),i()}return{get conversations(){return s(t)},get activeId(){return s(r)},get active(){return o()},createConversation:l,setActive:d,addMessage:u,updateLastMessage:p,removeLastMessage:_,deleteConversation:v,updateTitle:E,clearAll:k,flush:i}}var bf=w("<a><!></a>"),_f=w("<button><!></button>");function yf(e,t){Tr(t,!0);let r=dt(t,"variant",3,"default"),n=dt(t,"size",3,"default"),a=fu(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const i={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},o={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=ce(),d=G(l);{var u=v=>{var _=bf();ds(_,k=>({class:k,...a}),[()=>Qe("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",i[r()],o[n()],t.class)]);var E=c(_);Xs(E,()=>t.children),m(v,_)},p=v=>{var _=_f();ds(_,k=>({class:k,...a}),[()=>Qe("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",i[r()],o[n()],t.class)]);var E=c(_);Xs(E,()=>t.children),m(v,_)};T(d,v=>{t.href?v(u):v(p,-1)})}m(e,l),$r()}nc();/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const wf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const kf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const pi=(...e)=>e.filter((t,r,n)=>!!t&&t.trim()!==""&&n.indexOf(t)===r).join(" ").trim();var Sf=Wc("<svg><!><!></svg>");function Pe(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]),n=ye(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);Tr(t,!1);let a=dt(t,"name",8,void 0),i=dt(t,"color",8,"currentColor"),o=dt(t,"size",8,24),l=dt(t,"strokeWidth",8,2),d=dt(t,"absoluteStrokeWidth",8,!1),u=dt(t,"iconNode",24,()=>[]);du();var p=Sf();ds(p,(E,k,z)=>({...wf,...E,...n,width:o(),height:o(),stroke:i(),"stroke-width":k,class:z}),[()=>kf(n)?void 0:{"aria-hidden":"true"},()=>(In(d()),In(l()),In(o()),Wn(()=>d()?Number(l())*24/Number(o()):l())),()=>(In(pi),In(a()),In(r),Wn(()=>pi("lucide-icon","lucide",a()?`lucide-${a()}`:"",r.class)))]);var v=c(p);rt(v,1,u,tt,(E,k)=>{var z=ne(()=>is(s(k),2));let g=()=>s(z)[0],A=()=>s(z)[1];var $=ce(),L=G($);eu(L,g,!0,(M,O)=>{ds(M,()=>({...A()}))}),m(E,$)});var _=h(v);Ce(_,t,"default",{}),m(e,p),$r()}function zf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m12 19-7-7 7-7"}],["path",{d:"M19 12H5"}]];Pe(e,Ne({name:"arrow-left"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Mf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];Pe(e,Ne({name:"arrow-up"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function mi(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];Pe(e,Ne({name:"brain"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Af(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M20 6 9 17l-5-5"}]];Pe(e,Ne({name:"check"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Cf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m6 9 6 6 6-6"}]];Pe(e,Ne({name:"chevron-down"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function hi(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m9 18 6-6-6-6"}]];Pe(e,Ne({name:"chevron-right"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Pn(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];Pe(e,Ne({name:"circle-alert"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Ns(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];Pe(e,Ne({name:"circle-check"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Ef(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];Pe(e,Ne({name:"clock"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Tf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];Pe(e,Ne({name:"code"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function $f(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];Pe(e,Ne({name:"coffee"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function gn(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];Pe(e,Ne({name:"database"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function sa(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];Pe(e,Ne({name:"download"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function gi(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];Pe(e,Ne({name:"external-link"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Da(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];Pe(e,Ne({name:"file-text"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Nf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];Pe(e,Ne({name:"github"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function xi(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];Pe(e,Ne({name:"key"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Pf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m5 8 6 6"}],["path",{d:"m4 14 6-6 2-3"}],["path",{d:"M2 5h12"}],["path",{d:"M7 2h1"}],["path",{d:"m22 22-5-10-5 10"}],["path",{d:"M14 18h6"}]];Pe(e,Ne({name:"languages"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Wt(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];Pe(e,Ne({name:"loader-circle"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function If(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m10 17 5-5-5-5"}],["path",{d:"M15 12H3"}],["path",{d:"M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"}]];Pe(e,Ne({name:"log-in"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Lf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];Pe(e,Ne({name:"log-out"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Of(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];Pe(e,Ne({name:"menu"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function bi(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];Pe(e,Ne({name:"message-square"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Rf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];Pe(e,Ne({name:"panel-left-close"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function _i(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];Pe(e,Ne({name:"plus"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function jf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];Pe(e,Ne({name:"refresh-cw"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function yo(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];Pe(e,Ne({name:"search"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Df(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];Pe(e,Ne({name:"settings"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Ff(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];Pe(e,Ne({name:"square"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function yi(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];Pe(e,Ne({name:"table-2"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Bf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];Pe(e,Ne({name:"terminal"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Vf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];Pe(e,Ne({name:"trash-2"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Gf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];Pe(e,Ne({name:"triangle-alert"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Hf(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];Pe(e,Ne({name:"wrench"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function wo(e,t){const r=ye(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];Pe(e,Ne({name:"x"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ce(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}var Uf=w("<!> 새 대화",1),Kf=w('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-dl-bg-card border border-dl-border"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),Wf=w('<div role="button" tabindex="0"><!> <span class="flex-1 truncate"> </span> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),qf=w('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),Yf=w('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/50 text-[10px] text-dl-text-dim"> </div>'),Jf=w('<div class="flex flex-col h-full min-w-[260px]"><div class="flex items-center gap-2.5 px-4 pt-4 pb-2"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <span class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</span></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 space-y-4"></div> <!></div>'),Xf=w("<button><!></button>"),Zf=w('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),Qf=w("<aside><!></aside>");function ev(e,t){Tr(t,!0);let r=dt(t,"conversations",19,()=>[]),n=dt(t,"activeId",3,null),a=dt(t,"open",3,!0),i=dt(t,"version",3,""),o=V("");function l(k){const z=new Date().setHours(0,0,0,0),g=z-864e5,A=z-7*864e5,$={오늘:[],어제:[],"이번 주":[],이전:[]};for(const M of k)M.updatedAt>=z?$.오늘.push(M):M.updatedAt>=g?$.어제.push(M):M.updatedAt>=A?$["이번 주"].push(M):$.이전.push(M);const L=[];for(const[M,O]of Object.entries($))O.length>0&&L.push({label:M,items:O});return L}let d=ne(()=>s(o).trim()?r().filter(k=>k.title.toLowerCase().includes(s(o).toLowerCase())):r()),u=ne(()=>l(s(d)));var p=Qf(),v=c(p);{var _=k=>{var z=Jf(),g=h(c(z),2),A=c(g);yf(A,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(q,x)=>{var F=Uf(),Y=G(F);_i(Y,{size:16}),m(q,F)},$$slots:{default:!0}});var $=h(g,2);{var L=q=>{var x=Kf(),F=c(x),Y=c(F);yo(Y,{size:12,class:"text-dl-text-dim flex-shrink-0"});var fe=h(Y,2);aa(fe,()=>s(o),we=>f(o,we)),m(q,x)};T($,q=>{r().length>3&&q(L)})}var M=h($,2);rt(M,21,()=>s(u),tt,(q,x)=>{var F=qf(),Y=c(F),fe=c(Y),we=h(Y,2);rt(we,17,()=>s(x).items,tt,(He,P)=>{var R=Wf(),X=c(R);bi(X,{size:14,class:"flex-shrink-0 opacity-50"});var ae=h(X,2),de=c(ae),H=h(ae,2),y=c(H);Vf(y,{size:12}),j(ke=>{Ze(R,1,ke),D(de,s(P).title)},[()=>Xe(Qe("w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-[13px] transition-colors group cursor-pointer",s(P).id===n()?"bg-dl-bg-card text-dl-text border-l-2 border-dl-primary":"text-dl-text-muted hover:bg-dl-bg-card/50 hover:text-dl-text border-l-2 border-transparent"))]),W("click",R,()=>{var ke;return(ke=t.onSelect)==null?void 0:ke.call(t,s(P).id)}),W("keydown",R,ke=>{var ve;ke.key==="Enter"&&((ve=t.onSelect)==null||ve.call(t,s(P).id))}),W("click",H,ke=>{var ve;ke.stopPropagation(),(ve=t.onDelete)==null||ve.call(t,s(P).id)}),m(He,R)}),j(()=>D(fe,s(x).label)),m(q,F)});var O=h(M,2);{var J=q=>{var x=Yf(),F=c(x);j(()=>D(F,`DartLab v${i()??""}`)),m(q,x)};T(O,q=>{i()&&q(J)})}m(k,z)},E=k=>{var z=Zf(),g=h(c(z),2),A=c(g);_i(A,{size:18});var $=h(g,2);rt($,21,()=>r().slice(0,10),tt,(L,M)=>{var O=Xf(),J=c(O);bi(J,{size:16}),j(q=>{Ze(O,1,q),Va(O,"title",s(M).title)},[()=>Xe(Qe("p-2 rounded-lg transition-colors w-full flex justify-center",s(M).id===n()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),W("click",O,()=>{var q;return(q=t.onSelect)==null?void 0:q.call(t,s(M).id)}),m(L,O)}),W("click",g,function(...L){var M;(M=t.onNewChat)==null||M.apply(this,L)}),m(k,z)};T(v,k=>{a()?k(_):k(E,-1)})}j(k=>Ze(p,1,k),[()=>Xe(Qe("flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",a()?"w-[260px]":"w-[52px]"))]),m(e,p),$r()}Mn(["click","keydown"]);var tv=w('<button class="send-btn active"><!></button>'),rv=w("<button><!></button>"),nv=w('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),av=w('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),sv=w('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),ov=w('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function Dl(e,t){Tr(t,!0);let r=dt(t,"inputText",15,""),n=dt(t,"isLoading",3,!1),a=dt(t,"large",3,!1),i=dt(t,"placeholder",3,"메시지를 입력하세요..."),o=V(Ct([])),l=V(!1),d=V(-1),u=null,p=V(void 0);function v(x){var F;if(s(l)&&s(o).length>0){if(x.key==="ArrowDown"){x.preventDefault(),f(d,(s(d)+1)%s(o).length);return}if(x.key==="ArrowUp"){x.preventDefault(),f(d,s(d)<=0?s(o).length-1:s(d)-1,!0);return}if(x.key==="Enter"&&s(d)>=0){x.preventDefault(),k(s(o)[s(d)]);return}if(x.key==="Escape"){f(l,!1),f(d,-1);return}}x.key==="Enter"&&!x.shiftKey&&(x.preventDefault(),f(l,!1),(F=t.onSend)==null||F.call(t))}function _(x){x.target.style.height="auto",x.target.style.height=Math.min(x.target.scrollHeight,200)+"px"}function E(x){_(x);const F=r();u&&clearTimeout(u),F.length>=2&&!/\s/.test(F.slice(-1))?u=setTimeout(async()=>{var Y;try{const fe=await Sl(F.trim());((Y=fe.results)==null?void 0:Y.length)>0?(f(o,fe.results.slice(0,6),!0),f(l,!0),f(d,-1)):f(l,!1)}catch{f(l,!1)}},300):f(l,!1)}function k(x){r(`${x.corpName} `),f(l,!1),f(d,-1),s(p)&&s(p).focus()}function z(){setTimeout(()=>{f(l,!1)},200)}var g=ov(),A=c(g),$=c(A);xo($,x=>f(p,x),()=>s(p));var L=h($,2);{var M=x=>{var F=tv(),Y=c(F);Ff(Y,{size:14}),W("click",F,function(...fe){var we;(we=t.onStop)==null||we.apply(this,fe)}),m(x,F)},O=x=>{var F=rv(),Y=c(F);{let fe=ne(()=>a()?18:16);Mf(Y,{get size(){return s(fe)},strokeWidth:2.5})}j((fe,we)=>{Ze(F,1,fe),F.disabled=we},[()=>Xe(Qe("send-btn",r().trim()&&"active")),()=>!r().trim()]),W("click",F,()=>{var fe;f(l,!1),(fe=t.onSend)==null||fe.call(t)}),m(x,F)};T(L,x=>{n()&&t.onStop?x(M):x(O,-1)})}var J=h(A,2);{var q=x=>{var F=sv();rt(F,21,()=>s(o),tt,(Y,fe,we)=>{var He=av(),P=c(He);yo(P,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var R=h(P,2),X=c(R),ae=c(X),de=h(X,2),H=c(de),y=h(R,2);{var ke=ve=>{var ct=nv(),We=c(ct);j(()=>D(We,s(fe).sector)),m(ve,ct)};T(y,ve=>{s(fe).sector&&ve(ke)})}j(ve=>{Ze(He,1,ve),D(ae,s(fe).corpName),D(H,`${s(fe).stockCode??""} · ${(s(fe).market||"")??""}`)},[()=>Xe(Qe("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",we===s(d)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),W("mousedown",He,()=>k(s(fe))),ls("mouseenter",He,()=>{f(d,we,!0)}),m(Y,He)}),m(x,F)};T(J,x=>{s(l)&&s(o).length>0&&x(q)})}j(x=>{Ze(A,1,x),Va($,"placeholder",i())},[()=>Xe(Qe("input-box",a()&&"large"))]),W("keydown",$,v),W("input",$,E),ls("blur",$,z),aa($,r),m(e,g),$r()}Mn(["keydown","input","click","mousedown"]);var iv=w('<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[720px] flex flex-col items-center"><div class="relative mb-6"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-8">종목명과 질문을 입력하거나, 자유롭게 대화하세요</p> <div class="w-full"><!></div> <div class="mt-5 w-full"><button class="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/30 text-[13px] text-dl-text-dim hover:text-dl-text-muted hover:border-dl-primary/30 hover:bg-dl-bg-card/50 transition-all duration-200"><!> 데이터 탐색</button></div></div></div>');function lv(e,t){Tr(t,!0);let r=dt(t,"inputText",15,"");var n=iv(),a=c(n),i=h(c(a),6),o=c(i);Dl(o,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get inputText(){return r()},set inputText(p){r(p)}});var l=h(i,2),d=c(l),u=c(d);gn(u,{size:14}),W("click",d,()=>{var p;return(p=t.onOpenExplorer)==null?void 0:p.call(t)}),m(e,n),$r()}Mn(["click"]);var dv=w("<span><!></span>");function wi(e,t){Tr(t,!0);let r=dt(t,"variant",3,"default");const n={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var a=dv(),i=c(a);Xs(i,()=>t.children),j(o=>Ze(a,1,o),[()=>Xe(Qe("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",n[r()],t.class))]),m(e,a),$r()}var cv=w('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),uv=w('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),fv=w('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),vv=w('<div class="flex flex-wrap items-center gap-1.5 mb-2"><!> <!> <!></div>'),pv=w('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),mv=w('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),hv=w('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),gv=w('<button class="mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),xv=w('<span class="flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-dl-accent/30 bg-dl-accent/[0.06] text-[11px] text-dl-accent"><!> </span>'),bv=w('<div class="mb-3"><div class="flex flex-wrap items-center gap-1.5"></div></div>'),_v=w('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),yv=w('<!> <span class="text-dl-text-dim"> </span>',1),wv=w('<div class="flex items-center gap-2 text-[11px]"><!></div>'),kv=w('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),Sv=w('<div class="flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),zv=w('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),Mv=w('<span class="text-dl-accent/60"> </span>'),Av=w('<span class="text-dl-success/60"> </span>'),Cv=w('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),Ev=w('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),Tv=w('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),$v=w('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),Nv=w('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),Pv=w("<!>  <div><!></div> <!>",1),Iv=w('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),Lv=w('<span class="text-[10px] text-dl-text-dim"> </span>'),Ov=w('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),Rv=w("<button> </button>"),jv=w('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),Dv=w("<button>시스템 프롬프트</button>"),Fv=w("<button>LLM 입력</button>"),Bv=w('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),Vv=w('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),Gv=w('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),Hv=w('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Uv=w("<!> <!>",1);function Kv(e,t){Tr(t,!0);let r=V(null),n=V("context"),a=V("raw"),i=ne(()=>{var P,R,X,ae,de,H;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((P=t.message.toolEvents)==null?void 0:P.length)>0){const y=[...t.message.toolEvents].reverse().find(ve=>ve.type==="call"),ke=((R=y==null?void 0:y.arguments)==null?void 0:R.module)||((X=y==null?void 0:y.arguments)==null?void 0:X.keyword)||"";return`도구 실행 중 — ${(y==null?void 0:y.name)||""}${ke?` (${ke})`:""}`}if(((ae=t.message.contexts)==null?void 0:ae.length)>0){const y=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(y==null?void 0:y.label)||(y==null?void 0:y.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(de=t.message.meta)!=null&&de.company?`${t.message.meta.company} 데이터 검색 중`:(H=t.message.meta)!=null&&H.includedModules?"분석 모듈 선택 완료":"생각 중"}),o=ne(()=>{var P;return t.message.company||((P=t.message.meta)==null?void 0:P.company)||null}),l=ne(()=>{var P,R;return t.message.systemPrompt||((P=t.message.contexts)==null?void 0:P.length)>0||((R=t.message.meta)==null?void 0:R.includedModules)}),d=ne(()=>{var R;const P=(R=t.message.meta)==null?void 0:R.dataYearRange;return P?typeof P=="string"?P:P.min_year&&P.max_year?`${P.min_year}~${P.max_year}년`:null:null});function u(P){if(!P)return 0;const R=(P.match(/[\uac00-\ud7af]/g)||[]).length,X=P.length-R;return Math.round(R*1.5+X/3.5)}function p(P){return P>=1e3?(P/1e3).toFixed(1)+"k":String(P)}let v=ne(()=>{var R;let P=0;if(t.message.systemPrompt&&(P+=u(t.message.systemPrompt)),t.message.userContent)P+=u(t.message.userContent);else if(((R=t.message.contexts)==null?void 0:R.length)>0)for(const X of t.message.contexts)P+=u(X.text);return P}),_=ne(()=>u(t.message.text));function E(P){const R=P.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(R)||R==="-"||R==="0"}function k(P){if(!P)return"";let R=[],X=[],ae=P.replace(/```(\w*)\n([\s\S]*?)```/g,(H,y,ke)=>{const ve=R.length;return R.push(ke.trimEnd()),`
%%CODE_${ve}%%
`});ae=ae.replace(/((?:^\|.+\|$\n?)+)/gm,H=>{const y=H.trim().split(`
`).filter(Z=>Z.trim());let ke=null,ve=-1,ct=[];for(let Z=0;Z<y.length;Z++)if(y[Z].slice(1,-1).split("|").map(ue=>ue.trim()).every(ue=>/^[\-:]+$/.test(ue))){ve=Z;break}ve>0?(ke=y[ve-1],ct=y.slice(ve+1)):(ve===0||(ke=y[0]),ct=y.slice(1));let We="<table>";if(ke){const Z=ke.slice(1,-1).split("|").map(se=>se.trim());We+="<thead><tr>"+Z.map(se=>`<th>${se.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(ct.length>0){We+="<tbody>";for(const Z of ct){const se=Z.slice(1,-1).split("|").map(ue=>ue.trim());We+="<tr>"+se.map(ue=>{let Se=ue.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${E(ue)?' class="num"':""}>${Se}</td>`}).join("")+"</tr>"}We+="</tbody>"}We+="</table>";let Ve=X.length;return X.push(We),`
%%TABLE_${Ve}%%
`});let de=ae.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");de=de.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,H=>"<ul>"+H.replace(/<br>/g,"")+"</ul>");for(let H=0;H<X.length;H++)de=de.replace(`%%TABLE_${H}%%`,X[H]);for(let H=0;H<R.length;H++){const y=R[H].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");de=de.replace(`%%CODE_${H}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${H}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${y}</code></pre></div>`)}return de=de.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(H,y)=>y.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+de+"</p>"}let z=V(void 0);const g='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',A='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function $(P){var de;const R=P.target.closest(".code-copy-btn");if(!R)return;const X=R.closest(".code-block-wrap"),ae=((de=X==null?void 0:X.querySelector("code"))==null?void 0:de.textContent)||"";navigator.clipboard.writeText(ae).then(()=>{R.innerHTML=A,setTimeout(()=>{R.innerHTML=g},2e3)})}function L(P){f(r,P,!0),f(n,"context"),f(a,"rendered")}function M(){f(r,0),f(n,"system"),f(a,"raw")}function O(){f(r,0),f(n,"snapshot")}function J(){f(r,null)}let q=ne(()=>{var R,X,ae;if(!t.message.loading)return[];const P=[];return(R=t.message.meta)!=null&&R.company&&P.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&P.push({label:"핵심 수치 확인",done:!0}),(X=t.message.meta)!=null&&X.includedModules&&P.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((ae=t.message.contexts)==null?void 0:ae.length)>0&&P.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&P.push({label:"프롬프트 조립",done:!0}),t.message.text?P.push({label:"응답 작성 중",done:!1}):P.push({label:s(i)||"준비 중",done:!1}),P});var x=Uv(),F=G(x);{var Y=P=>{var R=cv(),X=h(c(R),2),ae=c(X),de=c(ae);j(()=>D(de,t.message.text)),m(P,R)},fe=P=>{var R=Iv(),X=h(c(R),2),ae=c(X);{var de=Z=>{var se=vv(),ue=c(se);{var Se=ee=>{wi(ee,{variant:"muted",children:(te,xe)=>{var Ee=ja();j(()=>D(Ee,s(o))),m(te,Ee)},$$slots:{default:!0}})};T(ue,ee=>{s(o)&&ee(Se)})}var Fe=h(ue,2);{var C=ee=>{wi(ee,{variant:"accent",children:(te,xe)=>{var Ee=ja();j(()=>D(Ee,s(d))),m(te,Ee)},$$slots:{default:!0}})};T(Fe,ee=>{s(d)&&ee(C)})}var N=h(Fe,2);{var re=ee=>{var te=ce(),xe=G(te);rt(xe,17,()=>t.message.contexts,tt,(Ee,at,bt)=>{var _t=uv(),Ie=c(_t);gn(Ie,{size:10,class:"flex-shrink-0"});var nt=h(Ie);j(()=>D(nt,` ${(s(at).label||s(at).module)??""}`)),W("click",_t,()=>L(bt)),m(Ee,_t)}),m(ee,te)},oe=ee=>{var te=fv(),xe=c(te);gn(xe,{size:10,class:"flex-shrink-0"});var Ee=h(xe);j(()=>D(Ee,` 모듈 ${t.message.meta.includedModules.length??""}개`)),m(ee,te)};T(N,ee=>{var te,xe,Ee;((te=t.message.contexts)==null?void 0:te.length)>0?ee(re):((Ee=(xe=t.message.meta)==null?void 0:xe.includedModules)==null?void 0:Ee.length)>0&&ee(oe,1)})}m(Z,se)};T(ae,Z=>{var se,ue;(s(o)||s(d)||((se=t.message.contexts)==null?void 0:se.length)>0||(ue=t.message.meta)!=null&&ue.includedModules)&&Z(de)})}var H=h(ae,2);{var y=Z=>{var se=gv(),ue=c(se);rt(ue,21,()=>t.message.snapshot.items,tt,(C,N)=>{const re=ne(()=>s(N).status==="good"?"text-dl-success":s(N).status==="danger"?"text-dl-primary-light":s(N).status==="caution"?"text-amber-400":"text-dl-text");var oe=pv(),ee=c(oe),te=c(ee),xe=h(ee,2),Ee=c(xe);j(at=>{D(te,s(N).label),Ze(xe,1,at),D(Ee,s(N).value)},[()=>Xe(Qe("text-[14px] font-semibold leading-snug mt-0.5",s(re)))]),m(C,oe)});var Se=h(ue,2);{var Fe=C=>{var N=hv();rt(N,21,()=>t.message.snapshot.warnings,tt,(re,oe)=>{var ee=mv(),te=c(ee);Gf(te,{size:10});var xe=h(te);j(()=>D(xe,` ${s(oe)??""}`)),m(re,ee)}),m(C,N)};T(Se,C=>{var N;((N=t.message.snapshot.warnings)==null?void 0:N.length)>0&&C(Fe)})}W("click",se,O),m(Z,se)};T(H,Z=>{var se,ue;((ue=(se=t.message.snapshot)==null?void 0:se.items)==null?void 0:ue.length)>0&&Z(y)})}var ke=h(H,2);{var ve=Z=>{var se=bv(),ue=c(se);rt(ue,21,()=>t.message.toolEvents,tt,(Se,Fe)=>{var C=ce(),N=G(C);{var re=oe=>{const ee=ne(()=>{var at,bt,_t,Ie;return((at=s(Fe).arguments)==null?void 0:at.module)||((bt=s(Fe).arguments)==null?void 0:bt.keyword)||((_t=s(Fe).arguments)==null?void 0:_t.engine)||((Ie=s(Fe).arguments)==null?void 0:Ie.name)||""});var te=xv(),xe=c(te);Hf(xe,{size:11});var Ee=h(xe);j(()=>D(Ee,` ${s(Fe).name??""}${s(ee)?`: ${s(ee)}`:""}`)),m(oe,te)};T(N,oe=>{s(Fe).type==="call"&&oe(re)})}m(Se,C)}),m(Z,se)};T(ke,Z=>{var se;((se=t.message.toolEvents)==null?void 0:se.length)>0&&Z(ve)})}var ct=h(ke,2);{var We=Z=>{var se=kv(),ue=c(se);rt(ue,21,()=>s(q),tt,(Se,Fe)=>{var C=wv(),N=c(C);{var re=ee=>{var te=_v(),xe=h(G(te),2),Ee=c(xe);j(()=>D(Ee,s(Fe).label)),m(ee,te)},oe=ee=>{var te=yv(),xe=G(te);Wt(xe,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var Ee=h(xe,2),at=c(Ee);j(()=>D(at,s(Fe).label)),m(ee,te)};T(N,ee=>{s(Fe).done?ee(re):ee(oe,-1)})}m(Se,C)}),m(Z,se)},Ve=Z=>{var se=Pv(),ue=G(se);{var Se=oe=>{var ee=Sv(),te=c(ee);Wt(te,{size:12,class:"animate-spin flex-shrink-0"});var xe=h(te,2),Ee=c(xe);j(()=>D(Ee,s(i))),m(oe,ee)};T(ue,oe=>{t.message.loading&&oe(Se)})}var Fe=h(ue,2),C=c(Fe);Xo(C,()=>k(t.message.text)),xo(Fe,oe=>f(z,oe),()=>s(z));var N=h(Fe,2);{var re=oe=>{var ee=Nv(),te=c(ee);{var xe=Re=>{var ze=zv(),qe=c(ze);Ef(qe,{size:10});var B=h(qe);j(()=>D(B,` ${t.message.duration??""}초`)),m(Re,ze)};T(te,Re=>{t.message.duration&&Re(xe)})}var Ee=h(te,2);{var at=Re=>{var ze=Cv(),qe=c(ze);{var B=je=>{var Je=Mv(),ft=c(Je);j(xt=>D(ft,`↑${xt??""}`),[()=>p(s(v))]),m(je,Je)};T(qe,je=>{s(v)>0&&je(B)})}var be=h(qe,2);{var Ue=je=>{var Je=Av(),ft=c(Je);j(xt=>D(ft,`↓${xt??""}`),[()=>p(s(_))]),m(je,Je)};T(be,je=>{s(_)>0&&je(Ue)})}m(Re,ze)};T(Ee,Re=>{(s(v)>0||s(_)>0)&&Re(at)})}var bt=h(Ee,2);{var _t=Re=>{var ze=Ev(),qe=c(ze);jf(qe,{size:10}),W("click",ze,()=>{var B;return(B=t.onRegenerate)==null?void 0:B.call(t)}),m(Re,ze)};T(bt,Re=>{t.onRegenerate&&Re(_t)})}var Ie=h(bt,2);{var nt=Re=>{var ze=Tv(),qe=c(ze);mi(qe,{size:10}),W("click",ze,M),m(Re,ze)};T(Ie,Re=>{t.message.systemPrompt&&Re(nt)})}var Le=h(Ie,2);{var ut=Re=>{var ze=$v(),qe=c(ze);Da(qe,{size:10});var B=h(qe);j((be,Ue)=>D(B,` LLM 입력 (${be??""}자 · ~${Ue??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>p(u(t.message.userContent))]),W("click",ze,()=>{f(r,0),f(n,"userContent"),f(a,"raw")}),m(Re,ze)};T(Le,Re=>{t.message.userContent&&Re(ut)})}m(oe,ee)};T(N,oe=>{!t.message.loading&&(t.message.duration||s(l)||t.onRegenerate)&&oe(re)})}j(oe=>Ze(Fe,1,oe),[()=>Xe(Qe("prose-dartlab text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),W("click",Fe,$),m(Z,se)};T(ct,Z=>{t.message.loading&&!t.message.text?Z(We):Z(Ve,-1)})}m(P,R)};T(F,P=>{t.message.role==="user"?P(Y):P(fe,-1)})}var we=h(F,2);{var He=P=>{const R=ne(()=>s(n)==="system"),X=ne(()=>s(n)==="userContent"),ae=ne(()=>s(n)==="context"),de=ne(()=>s(n)==="snapshot"),H=ne(()=>{var B;return s(ae)?(B=t.message.contexts)==null?void 0:B[s(r)]:null}),y=ne(()=>{var B,be;return s(de)?"핵심 수치 (원본 데이터)":s(R)?"시스템 프롬프트":s(X)?"LLM에 전달된 입력":((B=s(H))==null?void 0:B.label)||((be=s(H))==null?void 0:be.module)||""}),ke=ne(()=>{var B;return s(de)?JSON.stringify(t.message.snapshot,null,2):s(R)?t.message.systemPrompt:s(X)?t.message.userContent:(B=s(H))==null?void 0:B.text});var ve=Hv(),ct=c(ve),We=c(ct),Ve=c(We),Z=c(Ve),se=c(Z);{var ue=B=>{gn(B,{size:15,class:"text-dl-success flex-shrink-0"})},Se=B=>{mi(B,{size:15,class:"text-dl-primary-light flex-shrink-0"})},Fe=B=>{Da(B,{size:15,class:"text-dl-accent flex-shrink-0"})},C=B=>{gn(B,{size:15,class:"flex-shrink-0"})};T(se,B=>{s(de)?B(ue):s(R)?B(Se,1):s(X)?B(Fe,2):B(C,-1)})}var N=h(se,2),re=c(N),oe=h(N,2);{var ee=B=>{var be=Lv(),Ue=c(be);j(je=>D(Ue,`(${je??""}자)`),[()=>{var je,Je;return(Je=(je=s(ke))==null?void 0:je.length)==null?void 0:Je.toLocaleString()}]),m(B,be)};T(oe,B=>{s(R)&&B(ee)})}var te=h(Z,2),xe=c(te);{var Ee=B=>{var be=Ov(),Ue=c(be),je=c(Ue);Da(je,{size:11});var Je=h(Ue,2),ft=c(Je);Tf(ft,{size:11}),j((xt,vt)=>{Ze(Ue,1,xt),Ze(Je,1,vt)},[()=>Xe(Qe("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",s(a)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>Xe(Qe("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",s(a)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),W("click",Ue,()=>f(a,"rendered")),W("click",Je,()=>f(a,"raw")),m(B,be)};T(xe,B=>{s(ae)&&B(Ee)})}var at=h(xe,2),bt=c(at);wo(bt,{size:18});var _t=h(Ve,2);{var Ie=B=>{var be=jv(),Ue=c(be);rt(Ue,21,()=>t.message.contexts,tt,(je,Je,ft)=>{var xt=Rv(),vt=c(xt);j(yt=>{Ze(xt,1,yt),D(vt,t.message.contexts[ft].label||t.message.contexts[ft].module)},[()=>Xe(Qe("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",ft===s(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),W("click",xt,()=>{f(r,ft,!0)}),m(je,xt)}),m(B,be)};T(_t,B=>{var be;s(ae)&&((be=t.message.contexts)==null?void 0:be.length)>1&&B(Ie)})}var nt=h(_t,2);{var Le=B=>{var be=Bv(),Ue=c(be),je=c(Ue);{var Je=vt=>{var yt=Dv();j(rr=>Ze(yt,1,rr),[()=>Xe(Qe("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",s(R)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),W("click",yt,()=>{f(n,"system")}),m(vt,yt)};T(je,vt=>{t.message.systemPrompt&&vt(Je)})}var ft=h(je,2);{var xt=vt=>{var yt=Fv();j(rr=>Ze(yt,1,rr),[()=>Xe(Qe("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",s(X)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),W("click",yt,()=>{f(n,"userContent")}),m(vt,yt)};T(ft,vt=>{t.message.userContent&&vt(xt)})}m(B,be)};T(nt,B=>{!s(ae)&&!s(de)&&B(Le)})}var ut=h(We,2),Re=c(ut);{var ze=B=>{var be=Vv(),Ue=c(be);Xo(Ue,()=>{var je;return k((je=s(H))==null?void 0:je.text)}),m(B,be)},qe=B=>{var be=Gv(),Ue=c(be);j(()=>D(Ue,s(ke))),m(B,be)};T(Re,B=>{s(ae)&&s(a)==="rendered"?B(ze):B(qe,-1)})}j(()=>D(re,s(y))),W("click",ve,B=>{B.target===B.currentTarget&&J()}),W("keydown",ve,B=>{B.key==="Escape"&&J()}),W("click",at,J),m(P,ve)};T(we,P=>{s(r)!==null&&P(He)})}m(e,x),$r()}Mn(["click","keydown"]);var Wv=w('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),qv=w('<div class="flex justify-end gap-2 mb-1.5"><button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 데이터</button> <!></div>'),Yv=w('<div class="flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="max-w-[720px] mx-auto px-5 pt-14 pb-8 space-y-8"></div></div> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function Jv(e,t){Tr(t,!0);function r($){if(a())return!1;for(let L=n().length-1;L>=0;L--)if(n()[L].role==="assistant"&&!n()[L].error&&n()[L].text)return L===$;return!1}let n=dt(t,"messages",19,()=>[]),a=dt(t,"isLoading",3,!1),i=dt(t,"inputText",15,""),o=dt(t,"scrollTrigger",3,0),l,d=!1;function u(){if(!l)return;const{scrollTop:$,scrollHeight:L,clientHeight:M}=l;d=L-$-M>80}Fa(()=>{o(),!(!l||d)&&requestAnimationFrame(()=>{l&&(l.scrollTop=l.scrollHeight)})});var p=Yv(),v=c(p),_=c(v);rt(_,21,n,tt,($,L,M)=>{{let O=ne(()=>r(M)?t.onRegenerate:void 0);Kv($,{get message(){return s(L)},get onRegenerate(){return s(O)}})}}),xo(v,$=>l=$,()=>l);var E=h(v,2),k=c(E),z=c(k);{var g=$=>{var L=qv(),M=c(L),O=c(M);gn(O,{size:10});var J=h(M,2);{var q=x=>{var F=Wv(),Y=c(F);sa(Y,{size:10}),W("click",F,function(...fe){var we;(we=t.onExport)==null||we.apply(this,fe)}),m(x,F)};T(J,x=>{n().length>1&&t.onExport&&x(q)})}W("click",M,()=>{var x;return(x=t.onOpenExplorer)==null?void 0:x.call(t)}),m($,L)};T(z,$=>{a()||$(g)})}var A=h(z,2);Dl(A,{get isLoading(){return a()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get inputText(){return i()},set inputText($){i($)}}),ls("scroll",v,u),m(e,p),$r()}Mn(["click"]);var Xv=w('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="w-8 h-8 rounded-lg bg-dl-primary/15 flex items-center justify-center flex-shrink-0"><span class="text-[13px] font-bold text-dl-primary-light"> </span></div> <div><div class="text-[14px] font-semibold text-dl-text"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div>',1),Zv=w('<!> <div class="text-[15px] font-semibold text-dl-text">데이터 탐색</div>',1),Qv=w('<button class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-dl-success/15 text-dl-success text-[11px] font-medium hover:bg-dl-success/25 transition-colors disabled:opacity-40"><!> 전체 Excel</button>'),ep=w('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),tp=w('<button class="flex items-center gap-3 w-full px-4 py-3 rounded-xl border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all"><div class="w-8 h-8 rounded-lg bg-dl-primary/10 flex items-center justify-center flex-shrink-0"><span class="text-[12px] font-bold text-dl-primary-light"> </span></div> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium text-dl-text"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!> <!></button>'),rp=w('<div class="space-y-1"></div>'),np=w('<div class="text-center py-16 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),ap=w('<div class="text-center py-24"><!> <div class="text-[14px] text-dl-text-muted mb-1">종목을 검색하여 데이터를 탐색하세요</div> <div class="text-[12px] text-dl-text-dim/70">재무제표, 정기보고서, 공시 데이터를 직접 확인하고 Excel로 내보낼 수 있습니다</div></div>'),sp=w('<div class="flex-1 overflow-y-auto px-5 py-8"><div class="max-w-lg mx-auto"><div class="relative mb-4"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="w-full pl-9 pr-4 py-3 bg-dl-bg-card border border-dl-border rounded-xl text-[13px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/40 transition-colors"/> <!></div> <!></div></div>'),op=w('<div class="flex items-center justify-center py-12 gap-2 text-[12px] text-dl-text-dim"><!> 탐색 중...</div>'),ip=w('<button><!> <span class="flex-1 min-w-0 truncate"> </span></button>'),lp=w('<div class="ml-2 border-l border-dl-border/30 pl-1"></div>'),dp=w('<div class="mx-2 mb-0.5"><button class="flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-left hover:bg-white/[0.03] transition-colors"><!> <span class="text-[11px] font-medium text-dl-text-muted flex-1"> </span> <span class="text-[9px] text-dl-text-dim"> </span></button> <!></div>'),cp=w('<div class="flex items-center justify-center h-full text-center"><div><!> <div class="text-[13px] text-dl-text-dim">좌측에서 모듈을 선택하세요</div></div></div>'),up=w('<div class="flex items-center justify-center h-full gap-2 text-[13px] text-dl-text-dim"><!> </div>'),fp=w('<span class="text-[10px] text-dl-text-dim"> </span>'),vp=w('<span class="px-1.5 py-0.5 rounded bg-dl-border/50 text-[9px] text-dl-text-dim"> </span>'),pp=w("<button><!> </button>"),mp=w('<button class="flex items-center gap-1 px-2 py-1 rounded-lg bg-dl-success/10 text-dl-success text-[10px] hover:bg-dl-success/20 transition-colors"><!> Excel</button>'),hp=w('<th class="px-3 py-2 text-right text-dl-text-muted font-medium bg-dl-bg-darker border-b border-dl-border/30 whitespace-nowrap text-[10px] min-w-[100px]"> </th>'),gp=w("<td> </td>"),xp=w('<tr class="hover:bg-white/[0.02]"><td> </td><!></tr>'),bp=w('<div class="px-4 py-1.5 text-[10px] text-dl-warning border-t border-dl-border/20 flex-shrink-0"> </div>'),_p=w('<div class="flex-1 overflow-auto min-h-0"><table class="text-[11px] border-collapse"><thead class="sticky top-0 z-[5]"><tr><th class="sticky left-0 z-[10] px-3 py-2 text-left text-dl-text-muted font-medium bg-dl-bg-darker border-b border-r border-dl-border/30 whitespace-nowrap text-[10px] min-w-[180px]">계정명</th><!></tr></thead><tbody></tbody></table></div> <!>',1),yp=w('<th class="px-3 py-2 text-left text-dl-text-muted font-medium bg-dl-bg-darker border-b border-dl-border/30 whitespace-nowrap text-[10px]"> </th>'),wp=w("<td> </td>"),kp=w('<tr class="hover:bg-white/[0.02]"></tr>'),Sp=w('<div class="px-4 py-1.5 text-[10px] text-dl-warning border-t border-dl-border/20 flex-shrink-0"> </div>'),zp=w('<div class="flex-1 overflow-auto min-h-0"><table class="w-full text-[11px] border-collapse"><thead class="sticky top-0 z-[5]"><tr></tr></thead><tbody></tbody></table></div> <!>',1),Mp=w('<div class="flex gap-3 px-3 py-2 rounded-lg bg-dl-bg-card/50"><span class="text-[11px] text-dl-text-muted font-medium min-w-[160px] flex-shrink-0"> </span> <span class="text-[11px] text-dl-text-dim break-all"> </span></div>'),Ap=w('<div class="flex-1 overflow-auto min-h-0 p-4 space-y-1.5"></div>'),Cp=w('<div class="mt-2 text-[10px] text-dl-warning">내용이 잘려서 표시됩니다</div>'),Ep=w('<div class="flex-1 overflow-auto min-h-0 p-4"><pre class="text-[11px] text-dl-text-muted whitespace-pre-wrap leading-relaxed"> </pre> <!></div>'),Tp=w('<div class="flex items-center justify-center h-full text-[13px] text-dl-primary-light"> </div>'),$p=w('<div class="flex-1 overflow-auto min-h-0 p-4"><pre class="text-[11px] text-dl-text-muted whitespace-pre-wrap"> </pre></div>'),Np=w('<div class="flex items-center justify-between px-4 py-2 flex-shrink-0 border-b border-dl-border/30 bg-dl-bg-card/50"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!> <!></div> <div class="flex items-center gap-1.5"><!> <!></div></div> <!>',1),Pp=w('<div class="w-[240px] flex-shrink-0 border-r border-dl-border/50 overflow-y-auto bg-dl-bg-card/30"><!></div> <div class="flex-1 flex flex-col min-w-0 min-h-0"><!></div>',1),Ip=w('<div class="fixed inset-0 z-[200] flex flex-col bg-dl-bg-dark animate-fadeIn"><div class="flex items-center justify-between px-5 py-3 flex-shrink-0 border-b border-dl-border/50 bg-dl-bg-card/80 backdrop-blur-sm"><div class="flex items-center gap-3"><!></div> <div class="flex items-center gap-2"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 flex min-h-0"><!></div></div>');function Lp(e,t){Tr(t,!0);let r=V(""),n=V(Ct([])),a=V(!1),i=null,o=V(null),l=V(null),d=V(!1),u=V(Ct(new Set)),p=V(null),v=V(null),_=V(!1),E=V(!1),k=V(!0);function z(){const C=s(r).trim();if(i&&clearTimeout(i),C.length<2){f(n,[],!0);return}f(a,!0),i=setTimeout(async()=>{var N;try{const re=await Sl(C);f(n,((N=re.results)==null?void 0:N.slice(0,8))||[],!0)}catch{f(n,[],!0)}f(a,!1)},300)}async function g(C){f(o,C,!0),f(r,""),f(n,[],!0),f(d,!0),f(p,null),f(v,null);try{f(l,await wu(C.stockCode),!0);const N=Object.keys(s(l).categories||{});f(u,new Set(N.slice(0,2)),!0)}catch{f(l,null)}f(d,!1)}function A(){f(o,null),f(l,null),f(p,null),f(v,null)}async function $(C){if(C.available){f(p,C,!0),f(_,!0),f(v,null);try{f(v,await ku(s(o).stockCode,C.name,200),!0)}catch(N){f(v,{type:"error",error:N.message},!0)}f(_,!1)}}function L(C){const N=new Set(s(u));N.has(C)?N.delete(C):N.add(C),f(u,N,!0)}async function M(){if(s(o)){f(E,!0);try{await ai(s(o).stockCode)}catch{}f(E,!1)}}const O={finance:"재무제표",report:"정기보고서",disclosure:"공시 서술",notes:"K-IFRS 주석",analysis:"분석",raw:"원본 데이터"};function J(C){return O[C]||C}function q(C){return`${C.filter(re=>re.available).length}/${C.length}`}function x(C){var N,re;return!((re=(N=s(v))==null?void 0:N.meta)!=null&&re.labels)||!s(k)?C:s(v).meta.labels[C]||C}function F(C){var N,re;return(re=(N=s(v))==null?void 0:N.meta)!=null&&re.levels&&s(v).meta.levels[C]||1}function Y(C){if(C==null)return"-";if(typeof C!="number")return String(C);if(C===0)return"0";const N=Math.abs(C),re=C<0?"-":"";return N>=1e12?`${re}${(N/1e12).toLocaleString("ko-KR",{maximumFractionDigits:1})}조`:N>=1e8?`${re}${Math.round(N/1e8).toLocaleString("ko-KR")}억`:N>=1e4?`${re}${Math.round(N/1e4).toLocaleString("ko-KR")}만`:C.toLocaleString("ko-KR")}function fe(C){return Number.isInteger(C)&&C>=1900&&C<=2100}function we(C,N){if(C==null)return"-";if(typeof C=="number"){if(fe(C))return String(C);if(N==="원"||N==="백만원")return N==="백만원"&&(C=C*1e6),Y(C);if(Number.isInteger(C)&&Math.abs(C)>=1e3)return C.toLocaleString("ko-KR");if(!Number.isInteger(C))return C.toLocaleString("ko-KR",{maximumFractionDigits:2})}return String(C)}function He(){var C,N,re;return(N=(C=s(v))==null?void 0:C.meta)!=null&&N.unit?s(v).meta.unit:(re=s(v))!=null&&re.unit?s(v).unit:""}function P(){var C,N;return!!((N=(C=s(v))==null?void 0:C.meta)!=null&&N.labels)}function R(){var C;return(C=s(v))!=null&&C.columns?s(v).columns.filter(N=>N!=="계정명"):[]}var X=Ip(),ae=c(X),de=c(ae),H=c(de);{var y=C=>{var N=Xv(),re=G(N),oe=c(re);zf(oe,{size:16});var ee=h(re,2),te=c(ee),xe=c(te),Ee=h(ee,2),at=c(Ee),bt=c(at),_t=h(at,2),Ie=c(_t);j(()=>{D(xe,s(o).corpName[0]),D(bt,s(o).corpName),D(Ie,`${s(o).stockCode??""}${s(l)?` · ${s(l).availableSources}개 데이터`:""}`)}),W("click",re,A),m(C,N)},ke=C=>{var N=Zv(),re=G(N);gn(re,{size:18,class:"text-dl-primary-light"}),m(C,N)};T(H,C=>{s(o)?C(y):C(ke,-1)})}var ve=h(de,2),ct=c(ve);{var We=C=>{var N=Qv(),re=c(N);{var oe=te=>{Wt(te,{size:12,class:"animate-spin"})},ee=te=>{sa(te,{size:12})};T(re,te=>{s(E)?te(oe):te(ee,-1)})}j(()=>N.disabled=s(E)),W("click",N,M),m(C,N)};T(ct,C=>{s(o)&&!s(p)&&C(We)})}var Ve=h(ct,2),Z=c(Ve);wo(Z,{size:16});var se=h(ae,2),ue=c(se);{var Se=C=>{var N=sp(),re=c(N),oe=c(re),ee=c(oe);yo(ee,{size:14,class:"absolute left-3 top-1/2 -translate-y-1/2 text-dl-text-dim pointer-events-none"});var te=h(ee,2),xe=h(te,2);{var Ee=Le=>{Wt(Le,{size:14,class:"absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-dl-text-dim"})};T(xe,Le=>{s(a)&&Le(Ee)})}var at=h(oe,2);{var bt=Le=>{var ut=rp();rt(ut,21,()=>s(n),tt,(Re,ze)=>{var qe=tp(),B=c(qe),be=c(B),Ue=c(be),je=h(B,2),Je=c(je),ft=c(Je),xt=h(Je,2),vt=c(xt),yt=h(je,2);{var rr=Wr=>{var en=ep(),En=c(en);j(()=>D(En,s(ze).sector)),m(Wr,en)};T(yt,Wr=>{s(ze).sector&&Wr(rr)})}var Cn=h(yt,2);hi(Cn,{size:14,class:"text-dl-text-dim flex-shrink-0"}),j(()=>{D(Ue,s(ze).corpName[0]),D(ft,s(ze).corpName),D(vt,`${s(ze).stockCode??""} · ${(s(ze).market||"")??""}`)}),W("click",qe,()=>g(s(ze))),m(Re,qe)}),m(Le,ut)},_t=Le=>{var ut=np();m(Le,ut)},Ie=ne(()=>s(r).trim().length>=2&&!s(a)),nt=Le=>{var ut=ap(),Re=c(ut);gn(Re,{size:40,class:"mx-auto mb-4 text-dl-text-dim/30"}),m(Le,ut)};T(at,Le=>{s(n).length>0?Le(bt):s(Ie)?Le(_t,1):Le(nt,-1)})}W("input",te,z),aa(te,()=>s(r),Le=>f(r,Le)),m(C,N)},Fe=C=>{var N=Pp(),re=G(N),oe=c(re);{var ee=Ie=>{var nt=op(),Le=c(nt);Wt(Le,{size:14,class:"animate-spin"}),m(Ie,nt)},te=Ie=>{var nt=ce(),Le=G(nt);rt(Le,17,()=>Object.entries(s(l).categories),tt,(ut,Re)=>{var ze=ne(()=>is(s(Re),2));let qe=()=>s(ze)[0],B=()=>s(ze)[1];var be=dp(),Ue=c(be),je=c(Ue);{var Je=Ot=>{Cf(Ot,{size:12,class:"text-dl-text-dim flex-shrink-0"})},ft=ne(()=>s(u).has(qe())),xt=Ot=>{hi(Ot,{size:12,class:"text-dl-text-dim flex-shrink-0"})};T(je,Ot=>{s(ft)?Ot(Je):Ot(xt,-1)})}var vt=h(je,2),yt=c(vt),rr=h(vt,2),Cn=c(rr),Wr=h(Ue,2);{var en=Ot=>{var tn=lp();rt(tn,21,B,tt,(Xn,Yt)=>{var le=ip(),_e=c(le);{var Ke=st=>{yi(st,{size:10,class:"flex-shrink-0"})},Tt=st=>{Da(st,{size:10,class:"flex-shrink-0"})};T(_e,st=>{s(Yt).dataType==="timeseries"||s(Yt).dataType==="table"||s(Yt).dataType==="dataframe"?st(Ke):st(Tt,-1)})}var $t=h(_e,2),_r=c($t);j(st=>{Ze(le,1,st),le.disabled=!s(Yt).available,D(_r,s(Yt).label)},[()=>{var st;return Xe(Qe("flex items-center gap-1.5 w-full px-2 py-1 rounded-lg text-left text-[11px] transition-colors",!s(Yt).available&&"opacity-30 cursor-default",s(Yt).available&&((st=s(p))==null?void 0:st.name)===s(Yt).name?"bg-dl-primary/10 text-dl-primary-light":s(Yt).available?"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text":""))}]),W("click",le,()=>$(s(Yt))),m(Xn,le)}),m(Ot,tn)},En=ne(()=>s(u).has(qe()));T(Wr,Ot=>{s(En)&&Ot(en)})}j((Ot,tn)=>{D(yt,Ot),D(Cn,tn)},[()=>J(qe()),()=>q(B())]),W("click",Ue,()=>L(qe())),m(ut,be)}),m(Ie,nt)};T(oe,Ie=>{s(d)?Ie(ee):s(l)&&Ie(te,1)})}var xe=h(re,2),Ee=c(xe);{var at=Ie=>{var nt=cp(),Le=c(nt),ut=c(Le);yi(ut,{size:36,class:"mx-auto mb-3 text-dl-text-dim/20"}),m(Ie,nt)},bt=Ie=>{var nt=up(),Le=c(nt);Wt(Le,{size:16,class:"animate-spin"});var ut=h(Le);j(()=>D(ut,` ${s(p).label??""} 로딩 중...`)),m(Ie,nt)},_t=Ie=>{var nt=Np(),Le=G(nt),ut=c(Le),Re=c(ut),ze=c(Re),qe=h(Re,2);{var B=le=>{var _e=fp(),Ke=c(_e);j(()=>D(Ke,`${s(v).totalRows??""}행 × ${s(v).columns.length??""}열`)),m(le,_e)};T(qe,le=>{s(v).type==="table"&&le(B)})}var be=h(qe,2);{var Ue=le=>{var _e=vp(),Ke=c(_e);j(Tt=>D(Ke,Tt),[()=>He()==="원"?"원":He()]),m(le,_e)},je=ne(()=>He());T(be,le=>{s(je)&&le(Ue)})}var Je=h(ut,2),ft=c(Je);{var xt=le=>{var _e=pp(),Ke=c(_e);Pf(Ke,{size:11});var Tt=h(Ke);j($t=>{Ze(_e,1,$t),D(Tt,` ${s(k)?"한글":"EN"}`)},[()=>Xe(Qe("flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] transition-colors",s(k)?"bg-dl-primary/15 text-dl-primary-light":"text-dl-text-dim hover:text-dl-text hover:bg-white/5"))]),W("click",_e,()=>f(k,!s(k))),m(le,_e)},vt=ne(()=>P());T(ft,le=>{s(vt)&&le(xt)})}var yt=h(ft,2);{var rr=le=>{var _e=mp(),Ke=c(_e);sa(Ke,{size:10}),W("click",_e,async()=>{try{await ai(s(o).stockCode,[s(p).name])}catch{}}),m(le,_e)};T(yt,le=>{s(o)&&le(rr)})}var Cn=h(Le,2);{var Wr=le=>{var _e=_p(),Ke=G(_e),Tt=c(Ke),$t=c(Tt),_r=c($t),st=h(c(_r));rt(st,17,R,tt,(Nt,wt)=>{var ar=hp(),Ir=c(ar);j(()=>D(Ir,s(wt))),m(Nt,ar)});var Pr=h($t);rt(Pr,21,()=>s(v).rows,tt,(Nt,wt)=>{const ar=ne(()=>s(wt).계정명),Ir=ne(()=>F(s(ar)));var nn=xp(),Lr=c(nn),Zn=c(Lr),wa=h(Lr);rt(wa,17,R,tt,(an,ka)=>{const Tn=ne(()=>s(wt)[s(ka)]);var Sa=gp(),b=c(Sa);j((I,ie)=>{Ze(Sa,1,I),D(b,ie)},[()=>Xe(Qe("px-3 py-1.5 border-b border-dl-border/10 whitespace-nowrap text-right font-mono text-[10px]",s(Tn)===null||s(Tn)===void 0?"text-dl-text-dim/30":typeof s(Tn)=="number"&&s(Tn)<0?"text-dl-primary-light":"text-dl-accent-light")),()=>we(s(Tn),He())]),m(an,Sa)}),j((an,ka)=>{Ze(Lr,1,an),go(Lr,`padding-left: ${8+(s(Ir)-1)*12}px`),D(Zn,ka)},[()=>Xe(Qe("sticky left-0 z-[1] px-3 py-1.5 border-b border-r border-dl-border/10 whitespace-nowrap bg-dl-bg-dark/95",s(Ir)===1&&"font-semibold text-dl-text",s(Ir)===2&&"text-dl-text-muted",s(Ir)===3&&"text-dl-text-dim")),()=>x(s(ar))]),m(Nt,nn)});var rn=h(Ke,2);{var nr=Nt=>{var wt=bp(),ar=c(wt);j(()=>D(ar,`상위 ${s(v).rows.length??""}행만 표시 (전체 ${s(v).totalRows??""}행)`)),m(Nt,wt)};T(rn,Nt=>{s(v).truncated&&Nt(nr)})}m(le,_e)},en=ne(()=>s(v).type==="table"&&P()),En=le=>{var _e=zp(),Ke=G(_e),Tt=c(Ke),$t=c(Tt),_r=c($t);rt(_r,21,()=>s(v).columns,tt,(nr,Nt)=>{var wt=yp(),ar=c(wt);j(()=>D(ar,s(Nt))),m(nr,wt)});var st=h($t);rt(st,21,()=>s(v).rows,tt,(nr,Nt)=>{var wt=kp();rt(wt,21,()=>s(v).columns,tt,(ar,Ir)=>{const nn=ne(()=>s(Nt)[s(Ir)]);var Lr=wp(),Zn=c(Lr);j((wa,an)=>{Ze(Lr,1,wa),D(Zn,an)},[()=>Xe(Qe("px-3 py-1.5 border-b border-dl-border/10 whitespace-nowrap",typeof s(nn)=="number"?"text-right font-mono text-dl-accent-light text-[10px]":"text-dl-text-muted")),()=>we(s(nn),He())]),m(ar,Lr)}),m(nr,wt)});var Pr=h(Ke,2);{var rn=nr=>{var Nt=Sp(),wt=c(Nt);j(()=>D(wt,`상위 ${s(v).rows.length??""}행만 표시 (전체 ${s(v).totalRows??""}행)`)),m(nr,Nt)};T(Pr,nr=>{s(v).truncated&&nr(rn)})}m(le,_e)},Ot=le=>{var _e=Ap();rt(_e,21,()=>Object.entries(s(v).data),tt,(Ke,Tt)=>{var $t=ne(()=>is(s(Tt),2));let _r=()=>s($t)[0],st=()=>s($t)[1];var Pr=Mp(),rn=c(Pr),nr=c(rn),Nt=h(rn,2),wt=c(Nt);j(()=>{D(nr,_r()),D(wt,st()??"-")}),m(Ke,Pr)}),m(le,_e)},tn=le=>{var _e=Ep(),Ke=c(_e),Tt=c(Ke),$t=h(Ke,2);{var _r=st=>{var Pr=Cp();m(st,Pr)};T($t,st=>{s(v).truncated&&st(_r)})}j(()=>D(Tt,s(v).text)),m(le,_e)},Xn=le=>{var _e=Tp(),Ke=c(_e);j(()=>D(Ke,s(v).error||"데이터를 불러올 수 없습니다")),m(le,_e)},Yt=le=>{var _e=$p(),Ke=c(_e),Tt=c(Ke);j($t=>D(Tt,$t),[()=>s(v).data||JSON.stringify(s(v),null,2)]),m(le,_e)};T(Cn,le=>{s(en)?le(Wr):s(v).type==="table"?le(En,1):s(v).type==="dict"?le(Ot,2):s(v).type==="text"?le(tn,3):s(v).type==="error"?le(Xn,4):le(Yt,-1)})}j(()=>D(ze,s(p).label)),m(Ie,nt)};T(Ee,Ie=>{s(p)?s(_)?Ie(bt,1):s(v)&&Ie(_t,2):Ie(at)})}m(C,N)};T(ue,C=>{s(o)?C(Fe,-1):C(Se)})}W("keydown",X,C=>{var N;C.key==="Escape"&&((N=t.onClose)==null||N.call(t))}),W("click",Ve,()=>{var C;return(C=t.onClose)==null?void 0:C.call(t)}),m(e,X),$r()}Mn(["keydown","click","input"]);var Op=w('<div class="sidebar-overlay"></div>'),Rp=w("<!> <span>확인 중...</span>",1),jp=w("<!> <span>설정 필요</span>",1),Dp=w('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),Fp=w('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!> <!>',1),Bp=w('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/80 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text-muted">AI Provider 확인 중...</div></div></div>'),Vp=w('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-primary/30 bg-dl-primary/5 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text">AI Provider가 설정되지 않았습니다</div> <div class="text-[11px] text-dl-text-muted mt-0.5">대화를 시작하려면 Provider를 설정해주세요</div></div> <button class="px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors flex-shrink-0">설정하기</button></div>'),Gp=w('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),Hp=w('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),Up=w('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),Kp=w('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),Wp=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),qp=w('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),Yp=w('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),Jp=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),Xp=w('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),Zp=w('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),Qp=w('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),em=w('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @anthropic-ai/claude-code</div></div></div>'),tm=w('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">인증</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">claude auth login</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">Claude Pro 또는 Max 구독이 필요합니다</span></div>',1),rm=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2">설치 완료 후 새로고침하세요</div></div>'),nm=w("<!> 브라우저에서 로그인 중...",1),am=w("<!> OpenAI 계정으로 로그인",1),sm=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2.5">ChatGPT 계정으로 로그인하여 사용하세요</div> <button class="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div></div>'),om=w('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),im=w('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),lm=w("<button> <!></button>"),dm=w('<div class="flex flex-wrap gap-1.5"></div>'),cm=w('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),um=w('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),fm=w('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),vm=w('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),pm=w('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),mm=w('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),hm=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),gm=w("<!> <!> <!> <!> <!> <!> <!>",1),xm=w('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),bm=w('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden"><div class="flex items-center justify-between px-6 pt-5 pb-3"><div class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),_m=w('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5"><div class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),ym=w('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn"><div> </div></div>'),wm=w('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-0 left-0 right-0 z-10 pointer-events-none"><div class="flex items-center justify-between px-3 h-11 pointer-events-auto" style="background: linear-gradient(to bottom, rgba(5,8,17,0.92) 40%, transparent);"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center gap-1"><a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <div class="w-px h-4 bg-dl-border mx-1"></div> <button><!> <!></button></div></div> <!></div> <!></div></div>  <!> <!> <!> <!>',1);function km(e,t){Tr(t,!0);let r=V(""),n=V(!1),a=V(null),i=V(Ct({})),o=V(Ct({})),l=V(null),d=V(null),u=V(Ct([])),p=V(!0),v=V(0),_=V(!0),E=V(""),k=V(!1),z=V(null),g=V(Ct({})),A=V(Ct({})),$=V(""),L=V(!1),M=V(null),O=V(""),J=V(!1),q=V(""),x=V(0),F=V(null),Y=V(!1),fe=V(Ct({})),we=V(!1),He=V(!1);function P(){f(He,window.innerWidth<=768),s(He)&&f(p,!1)}Fa(()=>(P(),window.addEventListener("resize",P),()=>window.removeEventListener("resize",P)));let R=V(null),X=V(""),ae=V("error"),de=V(!1);function H(b,I="error",ie=4e3){f(X,b,!0),f(ae,I,!0),f(de,!0),setTimeout(()=>{f(de,!1)},ie)}const y=xf();Fa(()=>{ct()});let ke=V(Ct({})),ve=V(Ct({}));async function ct(){var b,I,ie;f(_,!0);try{const De=await hu();f(i,De.providers||{},!0),f(o,De.ollama||{},!0),f(ke,De.codex||{},!0),f(ve,De.claudeCode||{},!0),f(fe,De.chatgpt||{},!0),De.version&&f(E,De.version,!0);const Be=localStorage.getItem("dartlab-provider"),pt=localStorage.getItem("dartlab-model");if(Be&&((b=s(i)[Be])!=null&&b.available)){f(l,Be,!0),f(z,Be,!0),await na(Be,pt),await We(Be);const Te=s(g)[Be]||[];pt&&Te.includes(pt)?f(d,pt,!0):Te.length>0&&(f(d,Te[0],!0),localStorage.setItem("dartlab-model",s(d))),f(u,Te,!0),f(_,!1);return}if(Be&&s(i)[Be]){f(l,Be,!0),f(z,Be,!0),await We(Be);const Te=s(g)[Be]||[];f(u,Te,!0),pt&&Te.includes(pt)?f(d,pt,!0):Te.length>0&&f(d,Te[0],!0),f(_,!1);return}for(const Te of["chatgpt","codex","ollama"])if((I=s(i)[Te])!=null&&I.available){f(l,Te,!0),f(z,Te,!0),await na(Te),await We(Te);const qr=s(g)[Te]||[];f(u,qr,!0),f(d,((ie=s(i)[Te])==null?void 0:ie.model)||(qr.length>0?qr[0]:null),!0),s(d)&&localStorage.setItem("dartlab-model",s(d));break}}catch{}f(_,!1)}async function We(b){f(A,{...s(A),[b]:!0},!0);try{const I=await gu(b);f(g,{...s(g),[b]:I.models||[]},!0)}catch{f(g,{...s(g),[b]:[]},!0)}f(A,{...s(A),[b]:!1},!0)}async function Ve(b){var ie;f(l,b,!0),f(d,null),f(z,b,!0),localStorage.setItem("dartlab-provider",b),localStorage.removeItem("dartlab-model"),f($,""),f(M,null);try{await na(b)}catch{}await We(b);const I=s(g)[b]||[];if(f(u,I,!0),I.length>0){f(d,((ie=s(i)[b])==null?void 0:ie.model)||I[0],!0),localStorage.setItem("dartlab-model",s(d));try{await na(b,s(d))}catch{}}}async function Z(b){f(d,b,!0),localStorage.setItem("dartlab-model",b);try{await na(s(l),b)}catch{}}function se(b){s(z)===b?f(z,null):(f(z,b,!0),We(b))}async function ue(){const b=s($).trim();if(!(!b||!s(l))){f(L,!0),f(M,null);try{const I=await na(s(l),s(d),b);I.available?(f(M,"success"),s(i)[s(l)]={...s(i)[s(l)],available:!0,model:I.model},!s(d)&&I.model&&f(d,I.model,!0),await We(s(l)),f(u,s(g)[s(l)]||[],!0),H("API 키 인증 성공","success")):f(M,"error")}catch{f(M,"error")}f(L,!1)}}async function Se(){if(!s(Y)){f(Y,!0);try{const{authUrl:b}=await bu();window.open(b,"dartlab-oauth","width=600,height=700");const I=setInterval(async()=>{var ie;try{const De=await _u();De.done&&(clearInterval(I),f(Y,!1),De.error?H(`인증 실패: ${De.error}`):(H("ChatGPT 인증 성공","success"),await ct(),(ie=s(i).chatgpt)!=null&&ie.available&&await Ve("chatgpt")))}catch{clearInterval(I),f(Y,!1)}},2e3);setTimeout(()=>{clearInterval(I),s(Y)&&(f(Y,!1),H("인증 시간이 초과되었습니다. 다시 시도해주세요."))},12e4)}catch(b){f(Y,!1),H(`OAuth 시작 실패: ${b.message}`)}}}async function Fe(){try{await yu(),f(fe,{authenticated:!1},!0),s(l)==="chatgpt"&&f(i,{...s(i),chatgpt:{...s(i).chatgpt,available:!1}},!0),H("ChatGPT 로그아웃 완료","success"),await ct()}catch{H("로그아웃 실패")}}function C(){const b=s(O).trim();!b||s(J)||(f(J,!0),f(q,"준비 중..."),f(x,0),f(F,xu(b,{onProgress(I){I.total&&I.completed!==void 0?(f(x,Math.round(I.completed/I.total*100),!0),f(q,`다운로드 중... ${s(x)}%`)):I.status&&f(q,I.status,!0)},async onDone(){f(J,!1),f(F,null),f(O,""),f(q,""),f(x,0),H(`${b} 다운로드 완료`,"success"),await We("ollama"),f(u,s(g).ollama||[],!0),s(u).includes(b)&&await Z(b)},onError(I){f(J,!1),f(F,null),f(q,""),f(x,0),H(`다운로드 실패: ${I}`)}}),!0))}function N(){s(F)&&(s(F).abort(),f(F,null)),f(J,!1),f(O,""),f(q,""),f(x,0)}function re(){f(p,!s(p))}function oe(){if(f($,""),f(M,null),s(l))f(z,s(l),!0);else{const b=Object.keys(s(i));f(z,b.length>0?b[0]:null,!0)}f(k,!0),s(z)&&We(s(z))}function ee(){y.createConversation(),f(r,""),f(n,!1),s(a)&&(s(a).abort(),f(a,null))}function te(b){y.setActive(b),f(r,""),f(n,!1),s(a)&&(s(a).abort(),f(a,null))}function xe(b){f(R,b,!0)}function Ee(){s(R)&&(y.deleteConversation(s(R)),f(R,null))}function at(){var I;const b=y.active;if(!b)return null;for(let ie=b.messages.length-1;ie>=0;ie--){const De=b.messages[ie];if(De.role==="assistant"&&((I=De.meta)!=null&&I.stockCode))return De.meta.stockCode}return null}async function bt(){var dr,sn;const b=s(r).trim();if(!b||s(n))return;if(!s(l)||!((dr=s(i)[s(l)])!=null&&dr.available)){H("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),oe();return}y.activeId||y.createConversation();const I=y.activeId;y.addMessage("user",b),f(r,""),f(n,!0),y.addMessage("assistant",""),y.updateLastMessage({loading:!0,startedAt:Date.now()}),Oa(v);const ie=y.active,De=[];let Be=null;if(ie){const pe=ie.messages.slice(0,-2);for(const Q of pe)if((Q.role==="user"||Q.role==="assistant")&&Q.text&&Q.text.trim()&&!Q.error&&!Q.loading){const Ye={role:Q.role,text:Q.text};Q.role==="assistant"&&((sn=Q.meta)!=null&&sn.stockCode)&&(Ye.meta={company:Q.meta.company||Q.company,stockCode:Q.meta.stockCode,modules:Q.meta.includedModules||null},Be=Q.meta.stockCode),De.push(Ye)}}const pt=Be||at();function Te(){return y.activeId!==I}const qr=Su(pt,b,{provider:s(l),model:s(d)},{onMeta(pe){var Or;if(Te())return;const Q=y.active,Ye=Q==null?void 0:Q.messages[Q.messages.length-1],Ut={meta:{...(Ye==null?void 0:Ye.meta)||{},...pe}};pe.company&&(Ut.company=pe.company,y.activeId&&((Or=y.active)==null?void 0:Or.title)==="새 대화"&&y.updateTitle(y.activeId,pe.company)),pe.stockCode&&(Ut.stockCode=pe.stockCode),y.updateLastMessage(Ut)},onSnapshot(pe){Te()||y.updateLastMessage({snapshot:pe})},onContext(pe){if(Te())return;const Q=y.active;if(!Q)return;const Ye=Q.messages[Q.messages.length-1],on=(Ye==null?void 0:Ye.contexts)||[];y.updateLastMessage({contexts:[...on,{module:pe.module,label:pe.label,text:pe.text}]})},onSystemPrompt(pe){Te()||y.updateLastMessage({systemPrompt:pe.text,userContent:pe.userContent||null})},onToolCall(pe){if(Te())return;const Q=y.active;if(!Q)return;const Ye=Q.messages[Q.messages.length-1],on=(Ye==null?void 0:Ye.toolEvents)||[];y.updateLastMessage({toolEvents:[...on,{type:"call",name:pe.name,arguments:pe.arguments}]})},onToolResult(pe){if(Te())return;const Q=y.active;if(!Q)return;const Ye=Q.messages[Q.messages.length-1],on=(Ye==null?void 0:Ye.toolEvents)||[];y.updateLastMessage({toolEvents:[...on,{type:"result",name:pe.name,result:pe.result}]})},onChunk(pe){if(Te())return;const Q=y.active;if(!Q)return;const Ye=Q.messages[Q.messages.length-1];y.updateLastMessage({text:((Ye==null?void 0:Ye.text)||"")+pe}),Oa(v)},onDone(){if(Te())return;const pe=y.active,Q=pe==null?void 0:pe.messages[pe.messages.length-1],Ye=Q!=null&&Q.startedAt?((Date.now()-Q.startedAt)/1e3).toFixed(1):null;y.updateLastMessage({loading:!1,duration:Ye}),y.flush(),f(n,!1),f(a,null),Oa(v)},onError(pe,Q,Ye){Te()||(y.updateLastMessage({text:`오류: ${pe}`,loading:!1,error:!0}),y.flush(),Q==="relogin"||Q==="login"?(H(`${pe} — 설정에서 재로그인하세요`),oe()):H(Q==="check_headers"||Q==="check_endpoint"||Q==="check_client_id"?`${pe} — ChatGPT API 변경 감지. 업데이트를 확인하세요`:Q==="rate_limit"?"요청이 너무 많습니다. 잠시 후 다시 시도해주세요":pe),f(n,!1),f(a,null))}},De);f(a,qr,!0)}function _t(){s(a)&&(s(a).abort(),f(a,null),f(n,!1),y.updateLastMessage({loading:!1}),y.flush())}function Ie(){const b=y.active;if(!b||b.messages.length<2)return;let I="";for(let ie=b.messages.length-1;ie>=0;ie--)if(b.messages[ie].role==="user"){I=b.messages[ie].text;break}I&&(y.removeLastMessage(),y.removeLastMessage(),f(r,I,!0),requestAnimationFrame(()=>{bt()}))}function nt(){const b=y.active;if(!b)return;let I=`# ${b.title}

`;for(const pt of b.messages)pt.role==="user"?I+=`## You

${pt.text}

`:pt.role==="assistant"&&pt.text&&(I+=`## DartLab

${pt.text}

`);const ie=new Blob([I],{type:"text/markdown;charset=utf-8"}),De=URL.createObjectURL(ie),Be=document.createElement("a");Be.href=De,Be.download=`${b.title||"dartlab-chat"}.md`,Be.click(),URL.revokeObjectURL(De),H("대화가 마크다운으로 내보내졌습니다","success")}function Le(b){(b.metaKey||b.ctrlKey)&&b.key==="n"&&(b.preventDefault(),ee()),(b.metaKey||b.ctrlKey)&&b.shiftKey&&b.key==="S"&&(b.preventDefault(),re()),b.key==="Escape"&&s(R)?f(R,null):b.key==="Escape"&&s(we)?f(we,!1):b.key==="Escape"&&s(k)&&f(k,!1)}let ut=ne(()=>{var b;return((b=y.active)==null?void 0:b.messages)||[]}),Re=ne(()=>y.active&&y.active.messages.length>0),ze=ne(()=>{var b;return!s(_)&&(!s(l)||!((b=s(i)[s(l)])!=null&&b.available))});const qe=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var B=wm();ls("keydown",Ks,Le);var be=G(B),Ue=c(be);{var je=b=>{var I=Op();W("click",I,()=>{f(p,!1)}),W("keydown",I,()=>{}),m(b,I)};T(Ue,b=>{s(He)&&s(p)&&b(je)})}var Je=h(Ue,2),ft=c(Je);{let b=ne(()=>s(He)?!0:s(p));ev(ft,{get conversations(){return y.conversations},get activeId(){return y.activeId},get open(){return s(b)},get version(){return s(E)},onNewChat:()=>{ee(),s(He)&&f(p,!1)},onSelect:I=>{te(I),s(He)&&f(p,!1)},onDelete:xe})}var xt=h(Je,2),vt=c(xt),yt=c(vt),rr=c(yt),Cn=c(rr);{var Wr=b=>{Rf(b,{size:18})},en=b=>{Of(b,{size:18})};T(Cn,b=>{s(p)?b(Wr):b(en,-1)})}var En=h(rr,2),Ot=c(En),tn=c(Ot);$f(tn,{size:15});var Xn=h(Ot,2),Yt=c(Xn);Da(Yt,{size:15});var le=h(Xn,2),_e=c(le);Nf(_e,{size:15});var Ke=h(le,4),Tt=c(Ke);{var $t=b=>{var I=Rp(),ie=G(I);Wt(ie,{size:12,class:"animate-spin"}),m(b,I)},_r=b=>{var I=jp(),ie=G(I);Pn(ie,{size:12}),m(b,I)},st=b=>{var I=Fp(),ie=h(G(I),2),De=c(ie),Be=h(ie,2);{var pt=dr=>{var sn=Dp(),pe=h(G(sn),2),Q=c(pe);j(()=>D(Q,s(d))),m(dr,sn)};T(Be,dr=>{s(d)&&dr(pt)})}var Te=h(Be,2);{var qr=dr=>{Wt(dr,{size:10,class:"animate-spin text-dl-primary-light"})};T(Te,dr=>{s(J)&&dr(qr)})}j(()=>D(De,s(l))),m(b,I)};T(Tt,b=>{s(_)?b($t):s(ze)?b(_r,1):b(st,-1)})}var Pr=h(Tt,2);Df(Pr,{size:12});var rn=h(yt,2);{var nr=b=>{var I=Bp(),ie=c(I);Wt(ie,{size:16,class:"text-dl-text-dim animate-spin flex-shrink-0"}),m(b,I)},Nt=b=>{var I=Vp(),ie=c(I);Pn(ie,{size:16,class:"text-dl-primary-light flex-shrink-0"});var De=h(ie,4);W("click",De,()=>oe()),m(b,I)};T(rn,b=>{s(_)&&!s(k)?b(nr):s(ze)&&!s(k)&&b(Nt,1)})}var wt=h(vt,2);{var ar=b=>{Jv(b,{get messages(){return s(ut)},get isLoading(){return s(n)},get scrollTrigger(){return s(v)},onSend:bt,onStop:_t,onRegenerate:Ie,onExport:nt,onOpenExplorer:()=>f(we,!0),get inputText(){return s(r)},set inputText(I){f(r,I,!0)}})},Ir=b=>{lv(b,{onSend:bt,onOpenExplorer:()=>f(we,!0),get inputText(){return s(r)},set inputText(I){f(r,I,!0)}})};T(wt,b=>{s(Re)?b(ar):b(Ir,-1)})}var nn=h(be,2);{var Lr=b=>{var I=bm(),ie=c(I),De=c(ie),Be=h(c(De),2),pt=c(Be);wo(pt,{size:18});var Te=h(De,2),qr=c(Te);rt(qr,21,()=>Object.entries(s(i)),tt,(Ut,Or)=>{var ln=ne(()=>is(s(Or),2));let mt=()=>s(ln)[0],kt=()=>s(ln)[1];const za=ne(()=>mt()===s(l)),Fl=ne(()=>s(z)===mt()),Qn=ne(()=>kt().auth==="api_key"),xs=ne(()=>kt().auth==="cli"),Xa=ne(()=>s(g)[mt()]||[]),So=ne(()=>s(A)[mt()]);var bs=xm(),_s=c(bs),zo=c(_s),Mo=h(zo,2),Ao=c(Mo),Co=c(Ao),Bl=c(Co),Vl=h(Co,2);{var Gl=St=>{var cr=Gp();m(St,cr)};T(Vl,St=>{s(za)&&St(Gl)})}var Hl=h(Ao,2),Ul=c(Hl),Kl=h(Mo,2),Wl=c(Kl);{var ql=St=>{Ns(St,{size:16,class:"text-dl-success"})},Yl=St=>{var cr=Hp(),ea=G(cr);xi(ea,{size:14,class:"text-amber-400"}),m(St,cr)},Jl=St=>{var cr=Up(),ea=G(cr);Bf(ea,{size:14,class:"text-dl-text-dim"}),m(St,cr)};T(Wl,St=>{kt().available?St(ql):s(Qn)?St(Yl,1):s(xs)&&!kt().available&&St(Jl,2)})}var Xl=h(_s,2);{var Zl=St=>{var cr=gm(),ea=G(cr);{var Ql=Ge=>{var ot=Wp(),ht=c(ot),Rt=c(ht),Jt=h(ht,2),it=c(Jt),jt=h(it,2),sr=c(jt);{var Ht=Oe=>{Wt(Oe,{size:12,class:"animate-spin"})},lt=Oe=>{xi(Oe,{size:12})};T(sr,Oe=>{s(L)?Oe(Ht):Oe(lt,-1)})}var Pt=h(Jt,2);{var et=Oe=>{var Kt=Kp(),zt=c(Kt);Pn(zt,{size:12}),m(Oe,Kt)};T(Pt,Oe=>{s(M)==="error"&&Oe(et)})}j(Oe=>{D(Rt,kt().envKey?`환경변수 ${kt().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),Va(it,"placeholder",mt()==="openai"?"sk-...":mt()==="claude"?"sk-ant-...":"API Key"),jt.disabled=Oe},[()=>!s($).trim()||s(L)]),W("keydown",it,Oe=>{Oe.key==="Enter"&&ue()}),aa(it,()=>s($),Oe=>f($,Oe)),W("click",jt,ue),m(Ge,ot)};T(ea,Ge=>{s(Qn)&&!kt().available&&Ge(Ql)})}var Eo=h(ea,2);{var ed=Ge=>{var ot=Yp(),ht=c(ot),Rt=c(ht);Ns(Rt,{size:13,class:"text-dl-success"});var Jt=h(ht,2),it=c(Jt),jt=h(it,2);{var sr=lt=>{var Pt=qp(),et=c(Pt);{var Oe=zt=>{Wt(zt,{size:10,class:"animate-spin"})},Kt=zt=>{var ur=ja("변경");m(zt,ur)};T(et,zt=>{s(L)?zt(Oe):zt(Kt,-1)})}j(()=>Pt.disabled=s(L)),W("click",Pt,ue),m(lt,Pt)},Ht=ne(()=>s($).trim());T(jt,lt=>{s(Ht)&&lt(sr)})}W("keydown",it,lt=>{lt.key==="Enter"&&ue()}),aa(it,()=>s($),lt=>f($,lt)),m(Ge,ot)};T(Eo,Ge=>{s(Qn)&&kt().available&&Ge(ed)})}var To=h(Eo,2);{var td=Ge=>{var ot=Jp(),ht=h(c(ot),2),Rt=c(ht);sa(Rt,{size:14});var Jt=h(Rt,2);gi(Jt,{size:10,class:"ml-auto"}),m(Ge,ot)},rd=Ge=>{var ot=Xp(),ht=c(ot),Rt=c(ht);Pn(Rt,{size:14}),m(Ge,ot)};T(To,Ge=>{mt()==="ollama"&&!s(o).installed?Ge(td):mt()==="ollama"&&s(o).installed&&!s(o).running&&Ge(rd,1)})}var $o=h(To,2);{var nd=Ge=>{var ot=rm(),ht=c(ot);{var Rt=it=>{var jt=Qp(),sr=G(jt),Ht=c(sr),lt=h(sr,2),Pt=c(lt);{var et=yr=>{var $n=Zp();m(yr,$n)};T(Pt,yr=>{s(ke).installed||yr(et)})}var Oe=h(Pt,2),Kt=c(Oe),zt=c(Kt),ur=h(lt,2),dn=c(ur);Pn(dn,{size:12,class:"text-amber-400 flex-shrink-0"}),j(()=>{D(Ht,s(ke).installed?"Codex CLI가 설치되었지만 인증이 필요합니다":"Codex CLI 설치가 필요합니다"),D(zt,s(ke).installed?"1.":"2.")}),m(it,jt)},Jt=it=>{var jt=tm(),sr=G(jt),Ht=c(sr),lt=h(sr,2),Pt=c(lt);{var et=yr=>{var $n=em();m(yr,$n)};T(Pt,yr=>{s(ve).installed||yr(et)})}var Oe=h(Pt,2),Kt=c(Oe),zt=c(Kt),ur=h(lt,2),dn=c(ur);Pn(dn,{size:12,class:"text-amber-400 flex-shrink-0"}),j(()=>{D(Ht,s(ve).installed&&!s(ve).authenticated?"Claude Code가 설치되었지만 인증이 필요합니다":"Claude Code CLI 설치가 필요합니다"),D(zt,s(ve).installed?"1.":"2.")}),m(it,jt)};T(ht,it=>{mt()==="codex"?it(Rt):mt()==="claude-code"&&it(Jt,1)})}m(Ge,ot)};T($o,Ge=>{s(xs)&&!kt().available&&Ge(nd)})}var No=h($o,2);{var ad=Ge=>{var ot=sm(),ht=h(c(ot),2),Rt=c(ht);{var Jt=Ht=>{var lt=nm(),Pt=G(lt);Wt(Pt,{size:14,class:"animate-spin"}),m(Ht,lt)},it=Ht=>{var lt=am(),Pt=G(lt);If(Pt,{size:14}),m(Ht,lt)};T(Rt,Ht=>{s(Y)?Ht(Jt):Ht(it,-1)})}var jt=h(ht,2),sr=c(jt);Pn(sr,{size:12,class:"text-amber-400 flex-shrink-0"}),j(()=>ht.disabled=s(Y)),W("click",ht,Se),m(Ge,ot)};T(No,Ge=>{kt().auth==="oauth"&&!kt().available&&Ge(ad)})}var Po=h(No,2);{var sd=Ge=>{var ot=om(),ht=c(ot),Rt=c(ht),Jt=c(Rt);Ns(Jt,{size:13,class:"text-dl-success"});var it=h(Rt,2),jt=c(it);Lf(jt,{size:11}),W("click",it,Fe),m(Ge,ot)};T(Po,Ge=>{kt().auth==="oauth"&&kt().available&&Ge(sd)})}var od=h(Po,2);{var id=Ge=>{var ot=hm(),ht=c(ot),Rt=h(c(ht),2);{var Jt=et=>{Wt(et,{size:12,class:"animate-spin text-dl-text-dim"})};T(Rt,et=>{s(So)&&et(Jt)})}var it=h(ht,2);{var jt=et=>{var Oe=im(),Kt=c(Oe);Wt(Kt,{size:14,class:"animate-spin"}),m(et,Oe)},sr=et=>{var Oe=dm();rt(Oe,21,()=>s(Xa),tt,(Kt,zt)=>{var ur=lm(),dn=c(ur),yr=h(dn);{var $n=fr=>{Af(fr,{size:10,class:"inline ml-1"})};T(yr,fr=>{s(zt)===s(d)&&s(za)&&fr($n)})}j(fr=>{Ze(ur,1,fr),D(dn,`${s(zt)??""} `)},[()=>Xe(Qe("px-3 py-1.5 rounded-lg text-[11px] border transition-all",s(zt)===s(d)&&s(za)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),W("click",ur,()=>{mt()!==s(l)&&Ve(mt()),Z(s(zt))}),m(Kt,ur)}),m(et,Oe)},Ht=et=>{var Oe=cm();m(et,Oe)};T(it,et=>{s(So)&&s(Xa).length===0?et(jt):s(Xa).length>0?et(sr,1):et(Ht,-1)})}var lt=h(it,2);{var Pt=et=>{var Oe=mm(),Kt=c(Oe),zt=h(c(Kt),2),ur=h(c(zt));gi(ur,{size:9});var dn=h(Kt,2);{var yr=fr=>{var Ma=um(),Aa=c(Ma),ta=c(Aa),Ca=c(ta);Wt(Ca,{size:12,class:"animate-spin text-dl-primary-light"});var ys=h(ta,2),Za=h(Aa,2),Yr=c(Za),wr=h(Za,2),ws=c(wr);j(()=>{go(Yr,`width: ${s(x)??""}%`),D(ws,s(q))}),W("click",ys,N),m(fr,Ma)},$n=fr=>{var Ma=pm(),Aa=G(Ma),ta=c(Aa),Ca=h(ta,2),ys=c(Ca);sa(ys,{size:12});var Za=h(Aa,2);rt(Za,21,()=>qe,tt,(Yr,wr)=>{const ws=ne(()=>s(Xa).some(ra=>ra===s(wr).name||ra===s(wr).name.split(":")[0]));var Io=ce(),ld=G(Io);{var dd=ra=>{var ks=vm(),Lo=c(ks),Oo=c(Lo),Ro=c(Oo),cd=c(Ro),jo=h(Ro,2),ud=c(jo),fd=h(jo,2);{var vd=Ss=>{var Fo=fm(),bd=c(Fo);j(()=>D(bd,s(wr).tag)),m(Ss,Fo)};T(fd,Ss=>{s(wr).tag&&Ss(vd)})}var pd=h(Oo,2),md=c(pd),hd=h(Lo,2),Do=c(hd),gd=c(Do),xd=h(Do,2);sa(xd,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),j(()=>{D(cd,s(wr).name),D(ud,s(wr).size),D(md,s(wr).desc),D(gd,`${s(wr).gb??""} GB`)}),W("click",ks,()=>{f(O,s(wr).name,!0),C()}),m(ra,ks)};T(ld,ra=>{s(ws)||ra(dd)})}m(Yr,Io)}),j(Yr=>Ca.disabled=Yr,[()=>!s(O).trim()]),W("keydown",ta,Yr=>{Yr.key==="Enter"&&C()}),aa(ta,()=>s(O),Yr=>f(O,Yr)),W("click",Ca,C),m(fr,Ma)};T(dn,fr=>{s(J)?fr(yr):fr($n,-1)})}m(et,Oe)};T(lt,et=>{mt()==="ollama"&&et(Pt)})}m(Ge,ot)};T(od,Ge=>{(kt().available||s(Qn)||s(xs)||kt().auth==="oauth")&&Ge(id)})}m(St,cr)};T(Xl,St=>{(s(Fl)||s(za))&&St(Zl)})}j((St,cr)=>{Ze(bs,1,St),Ze(zo,1,cr),D(Bl,kt().label||mt()),D(Ul,kt().desc||"")},[()=>Xe(Qe("rounded-xl border transition-all",s(za)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>Xe(Qe("w-2.5 h-2.5 rounded-full flex-shrink-0",kt().available?"bg-dl-success":s(Qn)?"bg-amber-400":"bg-dl-text-dim"))]),W("click",_s,()=>{kt().available||s(Qn)?mt()===s(l)?se(mt()):Ve(mt()):se(mt())}),m(Ut,bs)});var dr=h(Te,2),sn=c(dr),pe=c(sn);{var Q=Ut=>{var Or=ja();j(()=>{var ln;return D(Or,`현재: ${(((ln=s(i)[s(l)])==null?void 0:ln.label)||s(l))??""} / ${s(d)??""}`)}),m(Ut,Or)},Ye=Ut=>{var Or=ja();j(()=>{var ln;return D(Or,`현재: ${(((ln=s(i)[s(l)])==null?void 0:ln.label)||s(l))??""}`)}),m(Ut,Or)};T(pe,Ut=>{s(l)&&s(d)?Ut(Q):s(l)&&Ut(Ye,1)})}var on=h(sn,2);W("click",I,Ut=>{Ut.target===Ut.currentTarget&&f(k,!1)}),W("keydown",I,()=>{}),W("click",Be,()=>f(k,!1)),W("click",on,()=>f(k,!1)),m(b,I)};T(nn,b=>{s(k)&&b(Lr)})}var Zn=h(nn,2);{var wa=b=>{Lp(b,{onClose:()=>f(we,!1)})};T(Zn,b=>{s(we)&&b(wa)})}var an=h(Zn,2);{var ka=b=>{var I=_m(),ie=c(I),De=h(c(ie),4),Be=c(De),pt=h(Be,2);W("click",I,Te=>{Te.target===Te.currentTarget&&f(R,null)}),W("keydown",I,()=>{}),W("click",Be,()=>f(R,null)),W("click",pt,Ee),m(b,I)};T(an,b=>{s(R)&&b(ka)})}var Tn=h(an,2);{var Sa=b=>{var I=ym(),ie=c(I),De=c(ie);j(Be=>{Ze(ie,1,Be),D(De,s(X))},[()=>Xe(Qe("px-4 py-3 rounded-xl border text-[13px] shadow-2xl max-w-sm",s(ae)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":s(ae)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),m(b,I)};T(Tn,b=>{s(de)&&b(Sa)})}j(b=>{Ze(Je,1,Xe(s(He)?s(p)?"sidebar-mobile":"hidden":"")),Ze(Ke,1,b)},[()=>Xe(Qe("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",s(_)?"text-dl-text-dim":s(ze)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),W("click",rr,re),W("click",Ke,()=>oe()),m(e,B),$r()}Mn(["click","keydown"]);qc(km,{target:document.getElementById("app")});
