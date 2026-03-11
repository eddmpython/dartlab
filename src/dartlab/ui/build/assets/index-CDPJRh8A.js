var _d=Object.defineProperty;var Bo=e=>{throw TypeError(e)};var yd=(e,t,r)=>t in e?_d(e,t,{enumerable:!0,configurable:!0,writable:!0,value:r}):e[t]=r;var Sr=(e,t,r)=>yd(e,typeof t!="symbol"?t+"":t,r),zs=(e,t,r)=>t.has(e)||Bo("Cannot "+r);var S=(e,t,r)=>(zs(e,t,"read from private field"),r?r.call(e):t.get(e)),Pe=(e,t,r)=>t.has(e)?Bo("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,r),be=(e,t,r,n)=>(zs(e,t,"write to private field"),n?n.call(e,r):t.set(e,r),r),Mt=(e,t,r)=>(zs(e,t,"access private method"),r);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const a of document.querySelectorAll('link[rel="modulepreload"]'))n(a);new MutationObserver(a=>{for(const i of a)if(i.type==="childList")for(const o of i.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&n(o)}).observe(document,{childList:!0,subtree:!0});function r(a){const i={};return a.integrity&&(i.integrity=a.integrity),a.referrerPolicy&&(i.referrerPolicy=a.referrerPolicy),a.crossOrigin==="use-credentials"?i.credentials="include":a.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function n(a){if(a.ep)return;a.ep=!0;const i=r(a);fetch(a.href,i)}})();const Ps=!1;var ro=Array.isArray,wd=Array.prototype.indexOf,va=Array.prototype.includes,fs=Array.from,kd=Object.defineProperty,hn=Object.getOwnPropertyDescriptor,Mi=Object.getOwnPropertyDescriptors,Sd=Object.prototype,zd=Array.prototype,no=Object.getPrototypeOf,Vo=Object.isExtensible;function Ca(e){return typeof e=="function"}const Md=()=>{};function Ad(e){return e()}function Is(e){for(var t=0;t<e.length;t++)e[t]()}function Ai(){var e,t,r=new Promise((n,a)=>{e=n,t=a});return{promise:r,resolve:e,reject:t}}function os(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const r=[];for(const n of e)if(r.push(n),r.length===t)break;return r}const Bt=2,xa=4,Hn=8,vs=1<<24,kn=16,Tr=32,qn=64,Ls=128,mr=512,jt=1024,Dt=2048,Er=4096,qt=8192,Gr=16384,ba=32768,_n=65536,Go=1<<17,Cd=1<<18,_a=1<<19,Ci=1<<20,Br=1<<25,Un=65536,Os=1<<21,ao=1<<22,gn=1<<23,Hr=Symbol("$state"),Ei=Symbol("legacy props"),Ed=Symbol(""),In=new class extends Error{constructor(){super(...arguments);Sr(this,"name","StaleReactionError");Sr(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var ki;const Ti=!!((ki=globalThis.document)!=null&&ki.contentType)&&globalThis.document.contentType.includes("xml");function Td(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function $d(e,t,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function Nd(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function Pd(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Id(e){throw new Error("https://svelte.dev/e/effect_orphan")}function Ld(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function Od(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function Rd(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function jd(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function Dd(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function Fd(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const Bd=1,Vd=2,$i=4,Gd=8,Hd=16,Ud=1,Kd=2,Ni=4,Wd=8,qd=16,Yd=1,Jd=2,Pt=Symbol(),Pi="http://www.w3.org/1999/xhtml",Ii="http://www.w3.org/2000/svg",Xd="http://www.w3.org/1998/Math/MathML",Zd="@attach";function Qd(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function ec(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Li(e){return e===this.v}function tc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function Oi(e){return!tc(e,this.v)}let Ha=!1,rc=!1;function nc(){Ha=!0}let It=null;function pa(e){It=e}function $r(e,t=!1,r){It={p:It,i:!1,c:null,e:null,s:e,x:null,l:Ha&&!t?{s:null,u:null,$:[]}:null}}function Nr(e){var t=It,r=t.e;if(r!==null){t.e=null;for(var n of r)tl(n)}return t.i=!0,It=t.p,{}}function Ua(){return!Ha||It!==null&&It.l===null}let Ln=[];function Ri(){var e=Ln;Ln=[],Is(e)}function Ur(e){if(Ln.length===0&&!Ia){var t=Ln;queueMicrotask(()=>{t===Ln&&Ri()})}Ln.push(e)}function ac(){for(;Ln.length>0;)Ri()}function ji(e){var t=Ce;if(t===null)return Ae.f|=gn,e;if((t.f&ba)===0&&(t.f&xa)===0)throw e;pn(e,t)}function pn(e,t){for(;t!==null;){if((t.f&Ls)!==0){if((t.f&ba)===0)throw e;try{t.b.error(e);return}catch(r){e=r}}t=t.parent}throw e}const sc=-7169;function gt(e,t){e.f=e.f&sc|t}function so(e){(e.f&mr)!==0||e.deps===null?gt(e,jt):gt(e,Er)}function Di(e){if(e!==null)for(const t of e)(t.f&Bt)===0||(t.f&Un)===0||(t.f^=Un,Di(t.deps))}function Fi(e,t,r){(e.f&Dt)!==0?t.add(e):(e.f&Er)!==0&&r.add(e),Di(e.deps),gt(e,jt)}const Za=new Set;let _e=null,Rs=null,Rt=null,Zt=[],ps=null,Ia=!1,ma=null,oc=1;var un,sa,jn,oa,ia,la,fn,Rr,da,tr,js,Ds,Fs,Bs;const ko=class ko{constructor(){Pe(this,tr);Sr(this,"id",oc++);Sr(this,"current",new Map);Sr(this,"previous",new Map);Pe(this,un,new Set);Pe(this,sa,new Set);Pe(this,jn,0);Pe(this,oa,0);Pe(this,ia,null);Pe(this,la,new Set);Pe(this,fn,new Set);Pe(this,Rr,new Map);Sr(this,"is_fork",!1);Pe(this,da,!1)}skip_effect(t){S(this,Rr).has(t)||S(this,Rr).set(t,{d:[],m:[]})}unskip_effect(t){var r=S(this,Rr).get(t);if(r){S(this,Rr).delete(t);for(var n of r.d)gt(n,Dt),Vr(n);for(n of r.m)gt(n,Er),Vr(n)}}process(t){var a;Zt=[],this.apply();var r=ma=[],n=[];for(const i of t)Mt(this,tr,Ds).call(this,i,r,n);if(ma=null,Mt(this,tr,js).call(this)){Mt(this,tr,Fs).call(this,n),Mt(this,tr,Fs).call(this,r);for(const[i,o]of S(this,Rr))Hi(i,o)}else{Rs=this,_e=null;for(const i of S(this,un))i(this);S(this,un).clear(),S(this,jn)===0&&Mt(this,tr,Bs).call(this),Ho(n),Ho(r),S(this,la).clear(),S(this,fn).clear(),Rs=null,(a=S(this,ia))==null||a.resolve()}Rt=null}capture(t,r){r!==Pt&&!this.previous.has(t)&&this.previous.set(t,r),(t.f&gn)===0&&(this.current.set(t,t.v),Rt==null||Rt.set(t,t.v))}activate(){_e=this,this.apply()}deactivate(){_e===this&&(_e=null,Rt=null)}flush(){var t;if(Zt.length>0)_e=this,Bi();else if(S(this,jn)===0&&!this.is_fork){for(const r of S(this,un))r(this);S(this,un).clear(),Mt(this,tr,Bs).call(this),(t=S(this,ia))==null||t.resolve()}this.deactivate()}discard(){for(const t of S(this,sa))t(this);S(this,sa).clear()}increment(t){be(this,jn,S(this,jn)+1),t&&be(this,oa,S(this,oa)+1)}decrement(t){be(this,jn,S(this,jn)-1),t&&be(this,oa,S(this,oa)-1),!S(this,da)&&(be(this,da,!0),Ur(()=>{be(this,da,!1),Mt(this,tr,js).call(this)?Zt.length>0&&this.flush():this.revive()}))}revive(){for(const t of S(this,la))S(this,fn).delete(t),gt(t,Dt),Vr(t);for(const t of S(this,fn))gt(t,Er),Vr(t);this.flush()}oncommit(t){S(this,un).add(t)}ondiscard(t){S(this,sa).add(t)}settled(){return(S(this,ia)??be(this,ia,Ai())).promise}static ensure(){if(_e===null){const t=_e=new ko;Za.add(_e),Ia||Ur(()=>{_e===t&&t.flush()})}return _e}apply(){}};un=new WeakMap,sa=new WeakMap,jn=new WeakMap,oa=new WeakMap,ia=new WeakMap,la=new WeakMap,fn=new WeakMap,Rr=new WeakMap,da=new WeakMap,tr=new WeakSet,js=function(){return this.is_fork||S(this,oa)>0},Ds=function(t,r,n){t.f^=jt;for(var a=t.first;a!==null;){var i=a.f,o=(i&(Tr|qn))!==0,l=o&&(i&jt)!==0,d=(i&qt)!==0,u=l||S(this,Rr).has(a);if(!u&&a.fn!==null){o?d||(a.f^=jt):(i&xa)!==0?r.push(a):(i&(Hn|vs))!==0&&d?n.push(a):Ya(a)&&(ga(a),(i&kn)!==0&&(S(this,fn).add(a),d&&gt(a,Dt)));var p=a.first;if(p!==null){a=p;continue}}for(;a!==null;){var v=a.next;if(v!==null){a=v;break}a=a.parent}}},Fs=function(t){for(var r=0;r<t.length;r+=1)Fi(t[r],S(this,la),S(this,fn))},Bs=function(){var i;if(Za.size>1){this.previous.clear();var t=_e,r=Rt,n=!0;for(const o of Za){if(o===this){n=!1;continue}const l=[];for(const[u,p]of this.current){if(o.current.has(u))if(n&&p!==o.current.get(u))o.current.set(u,p);else continue;l.push(u)}if(l.length===0)continue;const d=[...o.current.keys()].filter(u=>!this.current.has(u));if(d.length>0){var a=Zt;Zt=[];const u=new Set,p=new Map;for(const v of l)Vi(v,d,u,p);if(Zt.length>0){_e=o,o.apply();for(const v of Zt)Mt(i=o,tr,Ds).call(i,v,[],[]);o.deactivate()}Zt=a}}_e=t,Rt=r}S(this,Rr).clear(),Za.delete(this)};let xn=ko;function ic(e){var t=Ia;Ia=!0;try{for(var r;;){if(ac(),Zt.length===0&&(_e==null||_e.flush(),Zt.length===0))return ps=null,r;Bi()}}finally{Ia=t}}function Bi(){var e=null;try{for(var t=0;Zt.length>0;){var r=xn.ensure();if(t++>1e3){var n,a;lc()}r.process(Zt),bn.clear()}}finally{Zt=[],ps=null,ma=null}}function lc(){try{Ld()}catch(e){pn(e,ps)}}let zr=null;function Ho(e){var t=e.length;if(t!==0){for(var r=0;r<t;){var n=e[r++];if((n.f&(Gr|qt))===0&&Ya(n)&&(zr=new Set,ga(n),n.deps===null&&n.first===null&&n.nodes===null&&n.teardown===null&&n.ac===null&&sl(n),(zr==null?void 0:zr.size)>0)){bn.clear();for(const a of zr){if((a.f&(Gr|qt))!==0)continue;const i=[a];let o=a.parent;for(;o!==null;)zr.has(o)&&(zr.delete(o),i.push(o)),o=o.parent;for(let l=i.length-1;l>=0;l--){const d=i[l];(d.f&(Gr|qt))===0&&ga(d)}}zr.clear()}}zr=null}}function Vi(e,t,r,n){if(!r.has(e)&&(r.add(e),e.reactions!==null))for(const a of e.reactions){const i=a.f;(i&Bt)!==0?Vi(a,t,r,n):(i&(ao|kn))!==0&&(i&Dt)===0&&Gi(a,t,n)&&(gt(a,Dt),Vr(a))}}function Gi(e,t,r){const n=r.get(e);if(n!==void 0)return n;if(e.deps!==null)for(const a of e.deps){if(va.call(t,a))return!0;if((a.f&Bt)!==0&&Gi(a,t,r))return r.set(a,!0),!0}return r.set(e,!1),!1}function Vr(e){var t=ps=e,r=t.b;if(r!=null&&r.is_pending&&(e.f&(xa|Hn|vs))!==0&&(e.f&ba)===0){r.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var n=t.f;if(ma!==null&&t===Ce&&(e.f&Hn)===0)return;if((n&(qn|Tr))!==0){if((n&jt)===0)return;t.f^=jt}}Zt.push(t)}function Hi(e,t){if(!((e.f&Tr)!==0&&(e.f&jt)!==0)){(e.f&Dt)!==0?t.d.push(e):(e.f&Er)!==0&&t.m.push(e),gt(e,jt);for(var r=e.first;r!==null;)Hi(r,t),r=r.next}}function dc(e){let t=0,r=yn(0),n;return()=>{co()&&(s(r),fo(()=>(t===0&&(n=Kn(()=>e(()=>Oa(r)))),t+=1,()=>{Ur(()=>{t-=1,t===0&&(n==null||n(),n=void 0,Oa(r))})})))}}var cc=_n|_a;function uc(e,t,r,n){new fc(e,t,r,n)}var pr,to,jr,Dn,Xt,Dr,ir,Mr,Zr,Fn,vn,ca,ua,fa,Qr,cs,Et,vc,pc,mc,Vs,ns,as,Gs;class fc{constructor(t,r,n,a){Pe(this,Et);Sr(this,"parent");Sr(this,"is_pending",!1);Sr(this,"transform_error");Pe(this,pr);Pe(this,to,null);Pe(this,jr);Pe(this,Dn);Pe(this,Xt);Pe(this,Dr,null);Pe(this,ir,null);Pe(this,Mr,null);Pe(this,Zr,null);Pe(this,Fn,0);Pe(this,vn,0);Pe(this,ca,!1);Pe(this,ua,new Set);Pe(this,fa,new Set);Pe(this,Qr,null);Pe(this,cs,dc(()=>(be(this,Qr,yn(S(this,Fn))),()=>{be(this,Qr,null)})));var i;be(this,pr,t),be(this,jr,r),be(this,Dn,o=>{var l=Ce;l.b=this,l.f|=Ls,n(o)}),this.parent=Ce.b,this.transform_error=a??((i=this.parent)==null?void 0:i.transform_error)??(o=>o),be(this,Xt,qa(()=>{Mt(this,Et,Vs).call(this)},cc))}defer_effect(t){Fi(t,S(this,ua),S(this,fa))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!S(this,jr).pending}update_pending_count(t){Mt(this,Et,Gs).call(this,t),be(this,Fn,S(this,Fn)+t),!(!S(this,Qr)||S(this,ca))&&(be(this,ca,!0),Ur(()=>{be(this,ca,!1),S(this,Qr)&&ha(S(this,Qr),S(this,Fn))}))}get_effect_pending(){return S(this,cs).call(this),s(S(this,Qr))}error(t){var r=S(this,jr).onerror;let n=S(this,jr).failed;if(!r&&!n)throw t;S(this,Dr)&&(Ft(S(this,Dr)),be(this,Dr,null)),S(this,ir)&&(Ft(S(this,ir)),be(this,ir,null)),S(this,Mr)&&(Ft(S(this,Mr)),be(this,Mr,null));var a=!1,i=!1;const o=()=>{if(a){ec();return}a=!0,i&&Fd(),S(this,Mr)!==null&&Vn(S(this,Mr),()=>{be(this,Mr,null)}),Mt(this,Et,as).call(this,()=>{xn.ensure(),Mt(this,Et,Vs).call(this)})},l=d=>{try{i=!0,r==null||r(d,o),i=!1}catch(u){pn(u,S(this,Xt)&&S(this,Xt).parent)}n&&be(this,Mr,Mt(this,Et,as).call(this,()=>{xn.ensure();try{return er(()=>{var u=Ce;u.b=this,u.f|=Ls,n(S(this,pr),()=>d,()=>o)})}catch(u){return pn(u,S(this,Xt).parent),null}}))};Ur(()=>{var d;try{d=this.transform_error(t)}catch(u){pn(u,S(this,Xt)&&S(this,Xt).parent);return}d!==null&&typeof d=="object"&&typeof d.then=="function"?d.then(l,u=>pn(u,S(this,Xt)&&S(this,Xt).parent)):l(d)})}}pr=new WeakMap,to=new WeakMap,jr=new WeakMap,Dn=new WeakMap,Xt=new WeakMap,Dr=new WeakMap,ir=new WeakMap,Mr=new WeakMap,Zr=new WeakMap,Fn=new WeakMap,vn=new WeakMap,ca=new WeakMap,ua=new WeakMap,fa=new WeakMap,Qr=new WeakMap,cs=new WeakMap,Et=new WeakSet,vc=function(){try{be(this,Dr,er(()=>S(this,Dn).call(this,S(this,pr))))}catch(t){this.error(t)}},pc=function(t){const r=S(this,jr).failed;r&&be(this,Mr,er(()=>{r(S(this,pr),()=>t,()=>()=>{})}))},mc=function(){const t=S(this,jr).pending;t&&(this.is_pending=!0,be(this,ir,er(()=>t(S(this,pr)))),Ur(()=>{var r=be(this,Zr,document.createDocumentFragment()),n=Kr();r.append(n),be(this,Dr,Mt(this,Et,as).call(this,()=>(xn.ensure(),er(()=>S(this,Dn).call(this,n))))),S(this,vn)===0&&(S(this,pr).before(r),be(this,Zr,null),Vn(S(this,ir),()=>{be(this,ir,null)}),Mt(this,Et,ns).call(this))}))},Vs=function(){try{if(this.is_pending=this.has_pending_snippet(),be(this,vn,0),be(this,Fn,0),be(this,Dr,er(()=>{S(this,Dn).call(this,S(this,pr))})),S(this,vn)>0){var t=be(this,Zr,document.createDocumentFragment());mo(S(this,Dr),t);const r=S(this,jr).pending;be(this,ir,er(()=>r(S(this,pr))))}else Mt(this,Et,ns).call(this)}catch(r){this.error(r)}},ns=function(){this.is_pending=!1;for(const t of S(this,ua))gt(t,Dt),Vr(t);for(const t of S(this,fa))gt(t,Er),Vr(t);S(this,ua).clear(),S(this,fa).clear()},as=function(t){var r=Ce,n=Ae,a=It;xr(S(this,Xt)),gr(S(this,Xt)),pa(S(this,Xt).ctx);try{return t()}catch(i){return ji(i),null}finally{xr(r),gr(n),pa(a)}},Gs=function(t){var r;if(!this.has_pending_snippet()){this.parent&&Mt(r=this.parent,Et,Gs).call(r,t);return}be(this,vn,S(this,vn)+t),S(this,vn)===0&&(Mt(this,Et,ns).call(this),S(this,ir)&&Vn(S(this,ir),()=>{be(this,ir,null)}),S(this,Zr)&&(S(this,pr).before(S(this,Zr)),be(this,Zr,null)))};function Ui(e,t,r,n){const a=Ua()?Ka:oo;var i=e.filter(v=>!v.settled);if(r.length===0&&i.length===0){n(t.map(a));return}var o=Ce,l=hc(),d=i.length===1?i[0].promise:i.length>1?Promise.all(i.map(v=>v.promise)):null;function u(v){l();try{n(v)}catch(_){(o.f&Gr)===0&&pn(_,o)}Hs()}if(r.length===0){d.then(()=>u(t.map(a)));return}function p(){l(),Promise.all(r.map(v=>xc(v))).then(v=>u([...t.map(a),...v])).catch(v=>pn(v,o))}d?d.then(p):p()}function hc(){var e=Ce,t=Ae,r=It,n=_e;return function(i=!0){xr(e),gr(t),pa(r),i&&(n==null||n.activate())}}function Hs(e=!0){xr(null),gr(null),pa(null),e&&(_e==null||_e.deactivate())}function gc(){var e=Ce.b,t=_e,r=e.is_rendered();return e.update_pending_count(1),t.increment(r),()=>{e.update_pending_count(-1),t.decrement(r)}}function Ka(e){var t=Bt|Dt,r=Ae!==null&&(Ae.f&Bt)!==0?Ae:null;return Ce!==null&&(Ce.f|=_a),{ctx:It,deps:null,effects:null,equals:Li,f:t,fn:e,reactions:null,rv:0,v:Pt,wv:0,parent:r??Ce,ac:null}}function xc(e,t,r){Ce===null&&Td();var a=void 0,i=yn(Pt),o=!Ae,l=new Map;return Pc(()=>{var _;var d=Ai();a=d.promise;try{Promise.resolve(e()).then(d.resolve,d.reject).finally(Hs)}catch(E){d.reject(E),Hs()}var u=_e;if(o){var p=gc();(_=l.get(u))==null||_.reject(In),l.delete(u),l.set(u,d)}const v=(E,k=void 0)=>{if(u.activate(),k)k!==In&&(i.f|=gn,ha(i,k));else{(i.f&gn)!==0&&(i.f^=gn),ha(i,E);for(const[z,g]of l){if(l.delete(z),z===u)break;g.reject(In)}}p&&p()};d.promise.then(v,E=>v(null,E||"unknown"))}),hs(()=>{for(const d of l.values())d.reject(In)}),new Promise(d=>{function u(p){function v(){p===a?d(i):u(a)}p.then(v,v)}u(a)})}function ne(e){const t=Ka(e);return ll(t),t}function oo(e){const t=Ka(e);return t.equals=Oi,t}function bc(e){var t=e.effects;if(t!==null){e.effects=null;for(var r=0;r<t.length;r+=1)Ft(t[r])}}function _c(e){for(var t=e.parent;t!==null;){if((t.f&Bt)===0)return(t.f&Gr)===0?t:null;t=t.parent}return null}function io(e){var t,r=Ce;xr(_c(e));try{e.f&=~Un,bc(e),t=fl(e)}finally{xr(r)}return t}function Ki(e){var t=io(e);if(!e.equals(t)&&(e.wv=cl(),(!(_e!=null&&_e.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){gt(e,jt);return}wn||(Rt!==null?(co()||_e!=null&&_e.is_fork)&&Rt.set(e,t):so(e))}function yc(e){var t,r;if(e.effects!==null)for(const n of e.effects)(n.teardown||n.ac)&&((t=n.teardown)==null||t.call(n),(r=n.ac)==null||r.abort(In),n.teardown=Md,n.ac=null,Fa(n,0),vo(n))}function Wi(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&ga(t)}let Us=new Set;const bn=new Map;let qi=!1;function yn(e,t){var r={f:0,v:e,reactions:null,equals:Li,rv:0,wv:0};return r}function V(e,t){const r=yn(e);return ll(r),r}function wc(e,t=!1,r=!0){var a;const n=yn(e);return t||(n.equals=Oi),Ha&&r&&It!==null&&It.l!==null&&((a=It.l).s??(a.s=[])).push(n),n}function f(e,t,r=!1){Ae!==null&&(!Cr||(Ae.f&Go)!==0)&&Ua()&&(Ae.f&(Bt|kn|ao|Go))!==0&&(hr===null||!va.call(hr,e))&&Dd();let n=r?Ct(t):t;return ha(e,n)}function ha(e,t){if(!e.equals(t)){var r=e.v;wn?bn.set(e,t):bn.set(e,r),e.v=t;var n=xn.ensure();if(n.capture(e,r),(e.f&Bt)!==0){const a=e;(e.f&Dt)!==0&&io(a),so(a)}e.wv=cl(),Yi(e,Dt),Ua()&&Ce!==null&&(Ce.f&jt)!==0&&(Ce.f&(Tr|qn))===0&&(vr===null?Lc([e]):vr.push(e)),!n.is_fork&&Us.size>0&&!qi&&kc()}return t}function kc(){qi=!1;for(const e of Us)(e.f&jt)!==0&&gt(e,Er),Ya(e)&&ga(e);Us.clear()}function La(e,t=1){var r=s(e),n=t===1?r++:r--;return f(e,r),n}function Oa(e){f(e,e.v+1)}function Yi(e,t){var r=e.reactions;if(r!==null)for(var n=Ua(),a=r.length,i=0;i<a;i++){var o=r[i],l=o.f;if(!(!n&&o===Ce)){var d=(l&Dt)===0;if(d&&gt(o,t),(l&Bt)!==0){var u=o;Rt==null||Rt.delete(u),(l&Un)===0&&(l&mr&&(o.f|=Un),Yi(u,Er))}else d&&((l&kn)!==0&&zr!==null&&zr.add(o),Vr(o))}}}function Ct(e){if(typeof e!="object"||e===null||Hr in e)return e;const t=no(e);if(t!==Sd&&t!==zd)return e;var r=new Map,n=ro(e),a=V(0),i=Gn,o=l=>{if(Gn===i)return l();var d=Ae,u=Gn;gr(null),qo(i);var p=l();return gr(d),qo(u),p};return n&&r.set("length",V(e.length)),new Proxy(e,{defineProperty(l,d,u){(!("value"in u)||u.configurable===!1||u.enumerable===!1||u.writable===!1)&&Rd();var p=r.get(d);return p===void 0?o(()=>{var v=V(u.value);return r.set(d,v),v}):f(p,u.value,!0),!0},deleteProperty(l,d){var u=r.get(d);if(u===void 0){if(d in l){const p=o(()=>V(Pt));r.set(d,p),Oa(a)}}else f(u,Pt),Oa(a);return!0},get(l,d,u){var E;if(d===Hr)return e;var p=r.get(d),v=d in l;if(p===void 0&&(!v||(E=hn(l,d))!=null&&E.writable)&&(p=o(()=>{var k=Ct(v?l[d]:Pt),z=V(k);return z}),r.set(d,p)),p!==void 0){var _=s(p);return _===Pt?void 0:_}return Reflect.get(l,d,u)},getOwnPropertyDescriptor(l,d){var u=Reflect.getOwnPropertyDescriptor(l,d);if(u&&"value"in u){var p=r.get(d);p&&(u.value=s(p))}else if(u===void 0){var v=r.get(d),_=v==null?void 0:v.v;if(v!==void 0&&_!==Pt)return{enumerable:!0,configurable:!0,value:_,writable:!0}}return u},has(l,d){var _;if(d===Hr)return!0;var u=r.get(d),p=u!==void 0&&u.v!==Pt||Reflect.has(l,d);if(u!==void 0||Ce!==null&&(!p||(_=hn(l,d))!=null&&_.writable)){u===void 0&&(u=o(()=>{var E=p?Ct(l[d]):Pt,k=V(E);return k}),r.set(d,u));var v=s(u);if(v===Pt)return!1}return p},set(l,d,u,p){var L;var v=r.get(d),_=d in l;if(n&&d==="length")for(var E=u;E<v.v;E+=1){var k=r.get(E+"");k!==void 0?f(k,Pt):E in l&&(k=o(()=>V(Pt)),r.set(E+"",k))}if(v===void 0)(!_||(L=hn(l,d))!=null&&L.writable)&&(v=o(()=>V(void 0)),f(v,Ct(u)),r.set(d,v));else{_=v.v!==Pt;var z=o(()=>Ct(u));f(v,z)}var g=Reflect.getOwnPropertyDescriptor(l,d);if(g!=null&&g.set&&g.set.call(p,u),!_){if(n&&typeof d=="string"){var A=r.get("length"),$=Number(d);Number.isInteger($)&&$>=A.v&&f(A,$+1)}Oa(a)}return!0},ownKeys(l){s(a);var d=Reflect.ownKeys(l).filter(v=>{var _=r.get(v);return _===void 0||_.v!==Pt});for(var[u,p]of r)p.v!==Pt&&!(u in l)&&d.push(u);return d},setPrototypeOf(){jd()}})}function Uo(e){try{if(e!==null&&typeof e=="object"&&Hr in e)return e[Hr]}catch{}return e}function Sc(e,t){return Object.is(Uo(e),Uo(t))}var Ks,Ji,Xi,Zi;function zc(){if(Ks===void 0){Ks=window,Ji=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,r=Text.prototype;Xi=hn(t,"firstChild").get,Zi=hn(t,"nextSibling").get,Vo(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Vo(r)&&(r.__t=void 0)}}function Kr(e=""){return document.createTextNode(e)}function en(e){return Xi.call(e)}function Wa(e){return Zi.call(e)}function c(e,t){return en(e)}function G(e,t=!1){{var r=en(e);return r instanceof Comment&&r.data===""?Wa(r):r}}function h(e,t=1,r=!1){let n=e;for(;t--;)n=Wa(n);return n}function Mc(e){e.textContent=""}function Qi(){return!1}function lo(e,t,r){return document.createElementNS(t??Pi,e,void 0)}function Ac(e,t){if(t){const r=document.body;e.autofocus=!0,Ur(()=>{document.activeElement===r&&e.focus()})}}let Ko=!1;function Cc(){Ko||(Ko=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const r of e.target.elements)(t=r.__on_r)==null||t.call(r)})},{capture:!0}))}function ms(e){var t=Ae,r=Ce;gr(null),xr(null);try{return e()}finally{gr(t),xr(r)}}function Ec(e,t,r,n=r){e.addEventListener(t,()=>ms(r));const a=e.__on_r;a?e.__on_r=()=>{a(),n(!0)}:e.__on_r=()=>n(!0),Cc()}function el(e){Ce===null&&(Ae===null&&Id(),Pd()),wn&&Nd()}function Tc(e,t){var r=t.last;r===null?t.last=t.first=e:(r.next=e,e.prev=r,t.last=e)}function Pr(e,t){var r=Ce;r!==null&&(r.f&qt)!==0&&(e|=qt);var n={ctx:It,deps:null,nodes:null,f:e|Dt|mr,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},a=n;if((e&xa)!==0)ma!==null?ma.push(n):Vr(n);else if(t!==null){try{ga(n)}catch(o){throw Ft(n),o}a.deps===null&&a.teardown===null&&a.nodes===null&&a.first===a.last&&(a.f&_a)===0&&(a=a.first,(e&kn)!==0&&(e&_n)!==0&&a!==null&&(a.f|=_n))}if(a!==null&&(a.parent=r,r!==null&&Tc(a,r),Ae!==null&&(Ae.f&Bt)!==0&&(e&qn)===0)){var i=Ae;(i.effects??(i.effects=[])).push(a)}return n}function co(){return Ae!==null&&!Cr}function hs(e){const t=Pr(Hn,null);return gt(t,jt),t.teardown=e,t}function Da(e){el();var t=Ce.f,r=!Ae&&(t&Tr)!==0&&(t&ba)===0;if(r){var n=It;(n.e??(n.e=[])).push(e)}else return tl(e)}function tl(e){return Pr(xa|Ci,e)}function $c(e){return el(),Pr(Hn|Ci,e)}function Nc(e){xn.ensure();const t=Pr(qn|_a,e);return(r={})=>new Promise(n=>{r.outro?Vn(t,()=>{Ft(t),n(void 0)}):(Ft(t),n(void 0))})}function uo(e){return Pr(xa,e)}function Pc(e){return Pr(ao|_a,e)}function fo(e,t=0){return Pr(Hn|t,e)}function j(e,t=[],r=[],n=[]){Ui(n,t,r,a=>{Pr(Hn,()=>e(...a.map(s)))})}function qa(e,t=0){var r=Pr(kn|t,e);return r}function rl(e,t=0){var r=Pr(vs|t,e);return r}function er(e){return Pr(Tr|_a,e)}function nl(e){var t=e.teardown;if(t!==null){const r=wn,n=Ae;Wo(!0),gr(null);try{t.call(null)}finally{Wo(r),gr(n)}}}function vo(e,t=!1){var r=e.first;for(e.first=e.last=null;r!==null;){const a=r.ac;a!==null&&ms(()=>{a.abort(In)});var n=r.next;(r.f&qn)!==0?r.parent=null:Ft(r,t),r=n}}function Ic(e){for(var t=e.first;t!==null;){var r=t.next;(t.f&Tr)===0&&Ft(t),t=r}}function Ft(e,t=!0){var r=!1;(t||(e.f&Cd)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(al(e.nodes.start,e.nodes.end),r=!0),vo(e,t&&!r),Fa(e,0),gt(e,Gr);var n=e.nodes&&e.nodes.t;if(n!==null)for(const i of n)i.stop();nl(e);var a=e.parent;a!==null&&a.first!==null&&sl(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function al(e,t){for(;e!==null;){var r=e===t?null:Wa(e);e.remove(),e=r}}function sl(e){var t=e.parent,r=e.prev,n=e.next;r!==null&&(r.next=n),n!==null&&(n.prev=r),t!==null&&(t.first===e&&(t.first=n),t.last===e&&(t.last=r))}function Vn(e,t,r=!0){var n=[];ol(e,n,!0);var a=()=>{r&&Ft(e),t&&t()},i=n.length;if(i>0){var o=()=>--i||a();for(var l of n)l.out(o)}else a()}function ol(e,t,r){if((e.f&qt)===0){e.f^=qt;var n=e.nodes&&e.nodes.t;if(n!==null)for(const l of n)(l.is_global||r)&&t.push(l);for(var a=e.first;a!==null;){var i=a.next,o=(a.f&_n)!==0||(a.f&Tr)!==0&&(e.f&kn)!==0;ol(a,t,o?r:!1),a=i}}}function po(e){il(e,!0)}function il(e,t){if((e.f&qt)!==0){e.f^=qt;for(var r=e.first;r!==null;){var n=r.next,a=(r.f&_n)!==0||(r.f&Tr)!==0;il(r,a?t:!1),r=n}var i=e.nodes&&e.nodes.t;if(i!==null)for(const o of i)(o.is_global||t)&&o.in()}}function mo(e,t){if(e.nodes)for(var r=e.nodes.start,n=e.nodes.end;r!==null;){var a=r===n?null:Wa(r);t.append(r),r=a}}let ss=!1,wn=!1;function Wo(e){wn=e}let Ae=null,Cr=!1;function gr(e){Ae=e}let Ce=null;function xr(e){Ce=e}let hr=null;function ll(e){Ae!==null&&(hr===null?hr=[e]:hr.push(e))}let Qt=null,or=0,vr=null;function Lc(e){vr=e}let dl=1,On=0,Gn=On;function qo(e){Gn=e}function cl(){return++dl}function Ya(e){var t=e.f;if((t&Dt)!==0)return!0;if(t&Bt&&(e.f&=~Un),(t&Er)!==0){for(var r=e.deps,n=r.length,a=0;a<n;a++){var i=r[a];if(Ya(i)&&Ki(i),i.wv>e.wv)return!0}(t&mr)!==0&&Rt===null&&gt(e,jt)}return!1}function ul(e,t,r=!0){var n=e.reactions;if(n!==null&&!(hr!==null&&va.call(hr,e)))for(var a=0;a<n.length;a++){var i=n[a];(i.f&Bt)!==0?ul(i,t,!1):t===i&&(r?gt(i,Dt):(i.f&jt)!==0&&gt(i,Er),Vr(i))}}function fl(e){var z;var t=Qt,r=or,n=vr,a=Ae,i=hr,o=It,l=Cr,d=Gn,u=e.f;Qt=null,or=0,vr=null,Ae=(u&(Tr|qn))===0?e:null,hr=null,pa(e.ctx),Cr=!1,Gn=++On,e.ac!==null&&(ms(()=>{e.ac.abort(In)}),e.ac=null);try{e.f|=Os;var p=e.fn,v=p();e.f|=ba;var _=e.deps,E=_e==null?void 0:_e.is_fork;if(Qt!==null){var k;if(E||Fa(e,or),_!==null&&or>0)for(_.length=or+Qt.length,k=0;k<Qt.length;k++)_[or+k]=Qt[k];else e.deps=_=Qt;if(co()&&(e.f&mr)!==0)for(k=or;k<_.length;k++)((z=_[k]).reactions??(z.reactions=[])).push(e)}else!E&&_!==null&&or<_.length&&(Fa(e,or),_.length=or);if(Ua()&&vr!==null&&!Cr&&_!==null&&(e.f&(Bt|Er|Dt))===0)for(k=0;k<vr.length;k++)ul(vr[k],e);if(a!==null&&a!==e){if(On++,a.deps!==null)for(let g=0;g<r;g+=1)a.deps[g].rv=On;if(t!==null)for(const g of t)g.rv=On;vr!==null&&(n===null?n=vr:n.push(...vr))}return(e.f&gn)!==0&&(e.f^=gn),v}catch(g){return ji(g)}finally{e.f^=Os,Qt=t,or=r,vr=n,Ae=a,hr=i,pa(o),Cr=l,Gn=d}}function Oc(e,t){let r=t.reactions;if(r!==null){var n=wd.call(r,e);if(n!==-1){var a=r.length-1;a===0?r=t.reactions=null:(r[n]=r[a],r.pop())}}if(r===null&&(t.f&Bt)!==0&&(Qt===null||!va.call(Qt,t))){var i=t;(i.f&mr)!==0&&(i.f^=mr,i.f&=~Un),so(i),yc(i),Fa(i,0)}}function Fa(e,t){var r=e.deps;if(r!==null)for(var n=t;n<r.length;n++)Oc(e,r[n])}function ga(e){var t=e.f;if((t&Gr)===0){gt(e,jt);var r=Ce,n=ss;Ce=e,ss=!0;try{(t&(kn|vs))!==0?Ic(e):vo(e),nl(e);var a=fl(e);e.teardown=typeof a=="function"?a:null,e.wv=dl;var i;Ps&&rc&&(e.f&Dt)!==0&&e.deps}finally{ss=n,Ce=r}}}async function Rc(){await Promise.resolve(),ic()}function s(e){var t=e.f,r=(t&Bt)!==0;if(Ae!==null&&!Cr){var n=Ce!==null&&(Ce.f&Gr)!==0;if(!n&&(hr===null||!va.call(hr,e))){var a=Ae.deps;if((Ae.f&Os)!==0)e.rv<On&&(e.rv=On,Qt===null&&a!==null&&a[or]===e?or++:Qt===null?Qt=[e]:Qt.push(e));else{(Ae.deps??(Ae.deps=[])).push(e);var i=e.reactions;i===null?e.reactions=[Ae]:va.call(i,Ae)||i.push(Ae)}}}if(wn&&bn.has(e))return bn.get(e);if(r){var o=e;if(wn){var l=o.v;return((o.f&jt)===0&&o.reactions!==null||pl(o))&&(l=io(o)),bn.set(o,l),l}var d=(o.f&mr)===0&&!Cr&&Ae!==null&&(ss||(Ae.f&mr)!==0),u=(o.f&ba)===0;Ya(o)&&(d&&(o.f|=mr),Ki(o)),d&&!u&&(Wi(o),vl(o))}if(Rt!=null&&Rt.has(e))return Rt.get(e);if((e.f&gn)!==0)throw e.v;return e.v}function vl(e){if(e.f|=mr,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&Bt)!==0&&(t.f&mr)===0&&(Wi(t),vl(t))}function pl(e){if(e.v===Pt)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(bn.has(t)||(t.f&Bt)!==0&&pl(t))return!0;return!1}function Kn(e){var t=Cr;try{return Cr=!0,e()}finally{Cr=t}}function Pn(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(Hr in e)Ws(e);else if(!Array.isArray(e))for(let t in e){const r=e[t];typeof r=="object"&&r&&Hr in r&&Ws(r)}}}function Ws(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let n in e)try{Ws(e[n],t)}catch{}const r=no(e);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const n=Mi(r);for(let a in n){const i=n[a].get;if(i)try{i.call(e)}catch{}}}}}function jc(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const Dc=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function Fc(e){return Dc.includes(e)}const Bc={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function Vc(e){return e=e.toLowerCase(),Bc[e]??e}const Gc=["touchstart","touchmove"];function Hc(e){return Gc.includes(e)}const Rn=Symbol("events"),ml=new Set,qs=new Set;function hl(e,t,r,n={}){function a(i){if(n.capture||Ys.call(t,i),!i.cancelBubble)return ms(()=>r==null?void 0:r.call(this,i))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Ur(()=>{t.addEventListener(e,a,n)}):t.addEventListener(e,a,n),a}function is(e,t,r,n,a){var i={capture:n,passive:a},o=hl(e,t,r,i);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&hs(()=>{t.removeEventListener(e,o,i)})}function W(e,t,r){(t[Rn]??(t[Rn]={}))[e]=r}function Sn(e){for(var t=0;t<e.length;t++)ml.add(e[t]);for(var r of qs)r(e)}let Yo=null;function Ys(e){var g,A;var t=this,r=t.ownerDocument,n=e.type,a=((g=e.composedPath)==null?void 0:g.call(e))||[],i=a[0]||e.target;Yo=e;var o=0,l=Yo===e&&e[Rn];if(l){var d=a.indexOf(l);if(d!==-1&&(t===document||t===window)){e[Rn]=t;return}var u=a.indexOf(t);if(u===-1)return;d<=u&&(o=d)}if(i=a[o]||e.target,i!==t){kd(e,"currentTarget",{configurable:!0,get(){return i||r}});var p=Ae,v=Ce;gr(null),xr(null);try{for(var _,E=[];i!==null;){var k=i.assignedSlot||i.parentNode||i.host||null;try{var z=(A=i[Rn])==null?void 0:A[n];z!=null&&(!i.disabled||e.target===i)&&z.call(i,e)}catch($){_?E.push($):_=$}if(e.cancelBubble||k===t||k===null)break;i=k}if(_){for(let $ of E)queueMicrotask(()=>{throw $});throw _}}finally{e[Rn]=t,delete e.currentTarget,gr(p),xr(v)}}}var Si;const Ms=((Si=globalThis==null?void 0:globalThis.window)==null?void 0:Si.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function Uc(e){return(Ms==null?void 0:Ms.createHTML(e))??e}function gl(e){var t=lo("template");return t.innerHTML=Uc(e.replaceAll("<!>","<!---->")),t.content}function Wn(e,t){var r=Ce;r.nodes===null&&(r.nodes={start:e,end:t,a:null,t:null})}function w(e,t){var r=(t&Yd)!==0,n=(t&Jd)!==0,a,i=!e.startsWith("<!>");return()=>{a===void 0&&(a=gl(i?e:"<!>"+e),r||(a=en(a)));var o=n||Ji?document.importNode(a,!0):a.cloneNode(!0);if(r){var l=en(o),d=o.lastChild;Wn(l,d)}else Wn(o,o);return o}}function Kc(e,t,r="svg"){var n=!e.startsWith("<!>"),a=`<${r}>${n?e:"<!>"+e}</${r}>`,i;return()=>{if(!i){var o=gl(a),l=en(o);i=en(l)}var d=i.cloneNode(!0);return Wn(d,d),d}}function Wc(e,t){return Kc(e,t,"svg")}function Ra(e=""){{var t=Kr(e+"");return Wn(t,t),t}}function ce(){var e=document.createDocumentFragment(),t=document.createComment(""),r=Kr();return e.append(t,r),Wn(t,r),e}function m(e,t){e!==null&&e.before(t)}function D(e,t){var r=t==null?"":typeof t=="object"?`${t}`:t;r!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=r,e.nodeValue=`${r}`)}function qc(e,t){return Yc(e,t)}const Qa=new Map;function Yc(e,{target:t,anchor:r,props:n={},events:a,context:i,intro:o=!0,transformError:l}){zc();var d=void 0,u=Nc(()=>{var p=r??t.appendChild(Kr());uc(p,{pending:()=>{}},E=>{$r({});var k=It;i&&(k.c=i),a&&(n.$$events=a),d=e(E,n)||{},Nr()},l);var v=new Set,_=E=>{for(var k=0;k<E.length;k++){var z=E[k];if(!v.has(z)){v.add(z);var g=Hc(z);for(const L of[t,document]){var A=Qa.get(L);A===void 0&&(A=new Map,Qa.set(L,A));var $=A.get(z);$===void 0?(L.addEventListener(z,Ys,{passive:g}),A.set(z,1)):A.set(z,$+1)}}}};return _(fs(ml)),qs.add(_),()=>{var g;for(var E of v)for(const A of[t,document]){var k=Qa.get(A),z=k.get(E);--z==0?(A.removeEventListener(E,Ys),k.delete(E),k.size===0&&Qa.delete(A)):k.set(E,z)}qs.delete(_),p!==r&&((g=p.parentNode)==null||g.removeChild(p))}});return Jc.set(d,u),d}let Jc=new WeakMap;var Ar,Fr,lr,Bn,Va,Ga,us;class ho{constructor(t,r=!0){Sr(this,"anchor");Pe(this,Ar,new Map);Pe(this,Fr,new Map);Pe(this,lr,new Map);Pe(this,Bn,new Set);Pe(this,Va,!0);Pe(this,Ga,t=>{if(S(this,Ar).has(t)){var r=S(this,Ar).get(t),n=S(this,Fr).get(r);if(n)po(n),S(this,Bn).delete(r);else{var a=S(this,lr).get(r);a&&(a.effect.f&qt)===0&&(S(this,Fr).set(r,a.effect),S(this,lr).delete(r),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),n=a.effect)}for(const[i,o]of S(this,Ar)){if(S(this,Ar).delete(i),i===t)break;const l=S(this,lr).get(o);l&&(Ft(l.effect),S(this,lr).delete(o))}for(const[i,o]of S(this,Fr)){if(i===r||S(this,Bn).has(i)||(o.f&qt)!==0)continue;const l=()=>{if(Array.from(S(this,Ar).values()).includes(i)){var u=document.createDocumentFragment();mo(o,u),u.append(Kr()),S(this,lr).set(i,{effect:o,fragment:u})}else Ft(o);S(this,Bn).delete(i),S(this,Fr).delete(i)};S(this,Va)||!n?(S(this,Bn).add(i),Vn(o,l,!1)):l()}}});Pe(this,us,t=>{S(this,Ar).delete(t);const r=Array.from(S(this,Ar).values());for(const[n,a]of S(this,lr))r.includes(n)||(Ft(a.effect),S(this,lr).delete(n))});this.anchor=t,be(this,Va,r)}ensure(t,r){var n=_e,a=Qi();if(r&&!S(this,Fr).has(t)&&!S(this,lr).has(t))if(a){var i=document.createDocumentFragment(),o=Kr();i.append(o),S(this,lr).set(t,{effect:er(()=>r(o)),fragment:i})}else S(this,Fr).set(t,er(()=>r(this.anchor)));if(S(this,Ar).set(n,t),a){for(const[l,d]of S(this,Fr))l===t?n.unskip_effect(d):n.skip_effect(d);for(const[l,d]of S(this,lr))l===t?n.unskip_effect(d.effect):n.skip_effect(d.effect);n.oncommit(S(this,Ga)),n.ondiscard(S(this,us))}else S(this,Ga).call(this,n)}}Ar=new WeakMap,Fr=new WeakMap,lr=new WeakMap,Bn=new WeakMap,Va=new WeakMap,Ga=new WeakMap,us=new WeakMap;function T(e,t,r=!1){var n=new ho(e),a=r?_n:0;function i(o,l){n.ensure(o,l)}qa(()=>{var o=!1;t((l,d=0)=>{o=!0,i(d,l)}),o||i(-1,null)},a)}function tt(e,t){return t}function Xc(e,t,r){for(var n=[],a=t.length,i,o=t.length,l=0;l<a;l++){let v=t[l];Vn(v,()=>{if(i){if(i.pending.delete(v),i.done.add(v),i.pending.size===0){var _=e.outrogroups;Js(e,fs(i.done)),_.delete(i),_.size===0&&(e.outrogroups=null)}}else o-=1},!1)}if(o===0){var d=n.length===0&&r!==null;if(d){var u=r,p=u.parentNode;Mc(p),p.append(u),e.items.clear()}Js(e,t,!d)}else i={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(i)}function Js(e,t,r=!0){var n;if(e.pending.size>0){n=new Set;for(const o of e.pending.values())for(const l of o)n.add(e.items.get(l).e)}for(var a=0;a<t.length;a++){var i=t[a];if(n!=null&&n.has(i)){i.f|=Br;const o=document.createDocumentFragment();mo(i,o)}else Ft(t[a],r)}}var Jo;function rt(e,t,r,n,a,i=null){var o=e,l=new Map,d=(t&$i)!==0;if(d){var u=e;o=u.appendChild(Kr())}var p=null,v=oo(()=>{var L=r();return ro(L)?L:L==null?[]:fs(L)}),_,E=new Map,k=!0;function z(L){($.effect.f&Gr)===0&&($.pending.delete(L),$.fallback=p,Zc($,_,o,t,n),p!==null&&(_.length===0?(p.f&Br)===0?po(p):(p.f^=Br,Pa(p,null,o)):Vn(p,()=>{p=null})))}function g(L){$.pending.delete(L)}var A=qa(()=>{_=s(v);for(var L=_.length,M=new Set,O=_e,Z=Qi(),q=0;q<L;q+=1){var x=_[q],F=n(x,q),Y=k?null:l.get(F);Y?(Y.v&&ha(Y.v,x),Y.i&&ha(Y.i,q),Z&&O.unskip_effect(Y.e)):(Y=Qc(l,k?o:Jo??(Jo=Kr()),x,F,q,a,t,r),k||(Y.e.f|=Br),l.set(F,Y)),M.add(F)}if(L===0&&i&&!p&&(k?p=er(()=>i(o)):(p=er(()=>i(Jo??(Jo=Kr()))),p.f|=Br)),L>M.size&&$d(),!k)if(E.set(O,M),Z){for(const[ue,pe]of l)M.has(ue)||O.skip_effect(pe.e);O.oncommit(z),O.ondiscard(g)}else z(O);s(v)}),$={effect:A,items:l,pending:E,outrogroups:null,fallback:p};k=!1}function Ea(e){for(;e!==null&&(e.f&Tr)===0;)e=e.next;return e}function Zc(e,t,r,n,a){var Y,ue,pe,Ye,P,R,Q,ae,de;var i=(n&Gd)!==0,o=t.length,l=e.items,d=Ea(e.effect.first),u,p=null,v,_=[],E=[],k,z,g,A;if(i)for(A=0;A<o;A+=1)k=t[A],z=a(k,A),g=l.get(z).e,(g.f&Br)===0&&((ue=(Y=g.nodes)==null?void 0:Y.a)==null||ue.measure(),(v??(v=new Set)).add(g));for(A=0;A<o;A+=1){if(k=t[A],z=a(k,A),g=l.get(z).e,e.outrogroups!==null)for(const H of e.outrogroups)H.pending.delete(g),H.done.delete(g);if((g.f&Br)!==0)if(g.f^=Br,g===d)Pa(g,null,r);else{var $=p?p.next:d;g===e.effect.last&&(e.effect.last=g.prev),g.prev&&(g.prev.next=g.next),g.next&&(g.next.prev=g.prev),ln(e,p,g),ln(e,g,$),Pa(g,$,r),p=g,_=[],E=[],d=Ea(p.next);continue}if((g.f&qt)!==0&&(po(g),i&&((Ye=(pe=g.nodes)==null?void 0:pe.a)==null||Ye.unfix(),(v??(v=new Set)).delete(g))),g!==d){if(u!==void 0&&u.has(g)){if(_.length<E.length){var L=E[0],M;p=L.prev;var O=_[0],Z=_[_.length-1];for(M=0;M<_.length;M+=1)Pa(_[M],L,r);for(M=0;M<E.length;M+=1)u.delete(E[M]);ln(e,O.prev,Z.next),ln(e,p,O),ln(e,Z,L),d=L,p=Z,A-=1,_=[],E=[]}else u.delete(g),Pa(g,d,r),ln(e,g.prev,g.next),ln(e,g,p===null?e.effect.first:p.next),ln(e,p,g),p=g;continue}for(_=[],E=[];d!==null&&d!==g;)(u??(u=new Set)).add(d),E.push(d),d=Ea(d.next);if(d===null)continue}(g.f&Br)===0&&_.push(g),p=g,d=Ea(g.next)}if(e.outrogroups!==null){for(const H of e.outrogroups)H.pending.size===0&&(Js(e,fs(H.done)),(P=e.outrogroups)==null||P.delete(H));e.outrogroups.size===0&&(e.outrogroups=null)}if(d!==null||u!==void 0){var q=[];if(u!==void 0)for(g of u)(g.f&qt)===0&&q.push(g);for(;d!==null;)(d.f&qt)===0&&d!==e.fallback&&q.push(d),d=Ea(d.next);var x=q.length;if(x>0){var F=(n&$i)!==0&&o===0?r:null;if(i){for(A=0;A<x;A+=1)(Q=(R=q[A].nodes)==null?void 0:R.a)==null||Q.measure();for(A=0;A<x;A+=1)(de=(ae=q[A].nodes)==null?void 0:ae.a)==null||de.fix()}Xc(e,q,F)}}i&&Ur(()=>{var H,y;if(v!==void 0)for(g of v)(y=(H=g.nodes)==null?void 0:H.a)==null||y.apply()})}function Qc(e,t,r,n,a,i,o,l){var d=(o&Bd)!==0?(o&Hd)===0?wc(r,!1,!1):yn(r):null,u=(o&Vd)!==0?yn(a):null;return{v:d,i:u,e:er(()=>(i(t,d??r,u??a,l),()=>{e.delete(n)}))}}function Pa(e,t,r){if(e.nodes)for(var n=e.nodes.start,a=e.nodes.end,i=t&&(t.f&Br)===0?t.nodes.start:r;n!==null;){var o=Wa(n);if(i.before(n),n===a)return;n=o}}function ln(e,t,r){t===null?e.effect.first=r:t.next=r,r===null?e.effect.last=t:r.prev=t}function Xo(e,t,r=!1,n=!1,a=!1){var i=e,o="";j(()=>{var l=Ce;if(o!==(o=t()??"")&&(l.nodes!==null&&(al(l.nodes.start,l.nodes.end),l.nodes=null),o!=="")){var d=r?Ii:n?Xd:void 0,u=lo(r?"svg":n?"math":"template",d);u.innerHTML=o;var p=r||n?u:u.content;if(Wn(en(p),p.lastChild),r||n)for(;en(p);)i.before(en(p));else i.before(p)}})}function Ee(e,t,r,n,a){var l;var i=(l=t.$$slots)==null?void 0:l[r],o=!1;i===!0&&(i=t.children,o=!0),i===void 0||i(e,o?()=>n:n)}function Xs(e,t,...r){var n=new ho(e);qa(()=>{const a=t()??null;n.ensure(a,a&&(i=>a(i,...r)))},_n)}function eu(e,t,r,n,a,i){var o=null,l=e,d=new ho(l,!1);qa(()=>{const u=t()||null;var p=Ii;if(u===null){d.ensure(null,null);return}return d.ensure(u,v=>{if(u){if(o=lo(u,p),Wn(o,o),n){var _=o.appendChild(Kr());n(o,_)}Ce.nodes.end=o,v.before(o)}}),()=>{}},_n),hs(()=>{})}function tu(e,t){var r=void 0,n;rl(()=>{r!==(r=t())&&(n&&(Ft(n),n=null),r&&(n=er(()=>{uo(()=>r(e))})))})}function xl(e){var t,r,n="";if(typeof e=="string"||typeof e=="number")n+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(r=xl(e[t]))&&(n&&(n+=" "),n+=r)}else for(r in e)e[r]&&(n&&(n+=" "),n+=r);return n}function bl(){for(var e,t,r=0,n="",a=arguments.length;r<a;r++)(e=arguments[r])&&(t=xl(e))&&(n&&(n+=" "),n+=t);return n}function Xe(e){return typeof e=="object"?bl(e):e??""}const Zo=[...` 	
\r\f \v\uFEFF`];function ru(e,t,r){var n=e==null?"":""+e;if(r){for(var a of Object.keys(r))if(r[a])n=n?n+" "+a:a;else if(n.length)for(var i=a.length,o=0;(o=n.indexOf(a,o))>=0;){var l=o+i;(o===0||Zo.includes(n[o-1]))&&(l===n.length||Zo.includes(n[l]))?n=(o===0?"":n.substring(0,o))+n.substring(l+1):o=l}}return n===""?null:n}function Qo(e,t=!1){var r=t?" !important;":";",n="";for(var a of Object.keys(e)){var i=e[a];i!=null&&i!==""&&(n+=" "+a+": "+i+r)}return n}function As(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function nu(e,t){if(t){var r="",n,a;if(Array.isArray(t)?(n=t[0],a=t[1]):n=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var i=!1,o=0,l=!1,d=[];n&&d.push(...Object.keys(n).map(As)),a&&d.push(...Object.keys(a).map(As));var u=0,p=-1;const z=e.length;for(var v=0;v<z;v++){var _=e[v];if(l?_==="/"&&e[v-1]==="*"&&(l=!1):i?i===_&&(i=!1):_==="/"&&e[v+1]==="*"?l=!0:_==='"'||_==="'"?i=_:_==="("?o++:_===")"&&o--,!l&&i===!1&&o===0){if(_===":"&&p===-1)p=v;else if(_===";"||v===z-1){if(p!==-1){var E=As(e.substring(u,p).trim());if(!d.includes(E)){_!==";"&&v++;var k=e.substring(u,v).trim();r+=" "+k+";"}}u=v+1,p=-1}}}}return n&&(r+=Qo(n)),a&&(r+=Qo(a,!0)),r=r.trim(),r===""?null:r}return e==null?null:String(e)}function Ze(e,t,r,n,a,i){var o=e.__className;if(o!==r||o===void 0){var l=ru(r,n,i);l==null?e.removeAttribute("class"):t?e.className=l:e.setAttribute("class",l),e.__className=r}else if(i&&a!==i)for(var d in i){var u=!!i[d];(a==null||u!==!!a[d])&&e.classList.toggle(d,u)}return i}function Cs(e,t={},r,n){for(var a in r){var i=r[a];t[a]!==i&&(r[a]==null?e.style.removeProperty(a):e.style.setProperty(a,i,n))}}function go(e,t,r,n){var a=e.__style;if(a!==t){var i=nu(t,n);i==null?e.removeAttribute("style"):e.style.cssText=i,e.__style=t}else n&&(Array.isArray(n)?(Cs(e,r==null?void 0:r[0],n[0]),Cs(e,r==null?void 0:r[1],n[1],"important")):Cs(e,r,n));return n}function Zs(e,t,r=!1){if(e.multiple){if(t==null)return;if(!ro(t))return Qd();for(var n of e.options)n.selected=t.includes(ei(n));return}for(n of e.options){var a=ei(n);if(Sc(a,t)){n.selected=!0;return}}(!r||t!==void 0)&&(e.selectedIndex=-1)}function au(e){var t=new MutationObserver(()=>{Zs(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),hs(()=>{t.disconnect()})}function ei(e){return"__value"in e?e.__value:e.value}const Ta=Symbol("class"),$a=Symbol("style"),_l=Symbol("is custom element"),yl=Symbol("is html"),su=Ti?"option":"OPTION",ou=Ti?"select":"SELECT";function iu(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function Ba(e,t,r,n){var a=wl(e);a[t]!==(a[t]=r)&&(t==="loading"&&(e[Ed]=r),r==null?e.removeAttribute(t):typeof r!="string"&&kl(e).includes(t)?e[t]=r:e.setAttribute(t,r))}function lu(e,t,r,n,a=!1,i=!1){var o=wl(e),l=o[_l],d=!o[yl],u=t||{},p=e.nodeName===su;for(var v in t)v in r||(r[v]=null);r.class?r.class=Xe(r.class):r[Ta]&&(r.class=null),r[$a]&&(r.style??(r.style=null));var _=kl(e);for(const M in r){let O=r[M];if(p&&M==="value"&&O==null){e.value=e.__value="",u[M]=O;continue}if(M==="class"){var E=e.namespaceURI==="http://www.w3.org/1999/xhtml";Ze(e,E,O,n,t==null?void 0:t[Ta],r[Ta]),u[M]=O,u[Ta]=r[Ta];continue}if(M==="style"){go(e,O,t==null?void 0:t[$a],r[$a]),u[M]=O,u[$a]=r[$a];continue}var k=u[M];if(!(O===k&&!(O===void 0&&e.hasAttribute(M)))){u[M]=O;var z=M[0]+M[1];if(z!=="$$")if(z==="on"){const Z={},q="$$"+M;let x=M.slice(2);var g=Fc(x);if(jc(x)&&(x=x.slice(0,-7),Z.capture=!0),!g&&k){if(O!=null)continue;e.removeEventListener(x,u[q],Z),u[q]=null}if(g)W(x,e,O),Sn([x]);else if(O!=null){let F=function(Y){u[M].call(this,Y)};var L=F;u[q]=hl(x,e,F,Z)}}else if(M==="style")Ba(e,M,O);else if(M==="autofocus")Ac(e,!!O);else if(!l&&(M==="__value"||M==="value"&&O!=null))e.value=e.__value=O;else if(M==="selected"&&p)iu(e,O);else{var A=M;d||(A=Vc(A));var $=A==="defaultValue"||A==="defaultChecked";if(O==null&&!l&&!$)if(o[M]=null,A==="value"||A==="checked"){let Z=e;const q=t===void 0;if(A==="value"){let x=Z.defaultValue;Z.removeAttribute(A),Z.defaultValue=x,Z.value=Z.__value=q?x:null}else{let x=Z.defaultChecked;Z.removeAttribute(A),Z.defaultChecked=x,Z.checked=q?x:!1}}else e.removeAttribute(M);else $||_.includes(A)&&(l||typeof O!="string")?(e[A]=O,A in o&&(o[A]=Pt)):typeof O!="function"&&Ba(e,A,O)}}}return u}function ls(e,t,r=[],n=[],a=[],i,o=!1,l=!1){Ui(a,r,n,d=>{var u=void 0,p={},v=e.nodeName===ou,_=!1;if(rl(()=>{var k=t(...d.map(s)),z=lu(e,u,k,i,o,l);_&&v&&"value"in k&&Zs(e,k.value);for(let A of Object.getOwnPropertySymbols(p))k[A]||Ft(p[A]);for(let A of Object.getOwnPropertySymbols(k)){var g=k[A];A.description===Zd&&(!u||g!==u[A])&&(p[A]&&Ft(p[A]),p[A]=er(()=>tu(e,()=>g))),z[A]=g}u=z}),v){var E=e;uo(()=>{Zs(E,u.value,!0),au(E)})}_=!0})}function wl(e){return e.__attributes??(e.__attributes={[_l]:e.nodeName.includes("-"),[yl]:e.namespaceURI===Pi})}var ti=new Map;function kl(e){var t=e.getAttribute("is")||e.nodeName,r=ti.get(t);if(r)return r;ti.set(t,r=[]);for(var n,a=e,i=Element.prototype;i!==a;){n=Mi(a);for(var o in n)n[o].set&&r.push(o);a=no(a)}return r}function na(e,t,r=t){var n=new WeakSet;Ec(e,"input",async a=>{var i=a?e.defaultValue:e.value;if(i=Es(e)?Ts(i):i,r(i),_e!==null&&n.add(_e),await Rc(),i!==(i=t())){var o=e.selectionStart,l=e.selectionEnd,d=e.value.length;if(e.value=i??"",l!==null){var u=e.value.length;o===l&&l===d&&u>d?(e.selectionStart=u,e.selectionEnd=u):(e.selectionStart=o,e.selectionEnd=Math.min(l,u))}}}),Kn(t)==null&&e.value&&(r(Es(e)?Ts(e.value):e.value),_e!==null&&n.add(_e)),fo(()=>{var a=t();if(e===document.activeElement){var i=Rs??_e;if(n.has(i))return}Es(e)&&a===Ts(e.value)||e.type==="date"&&!a&&!e.value||a!==e.value&&(e.value=a??"")})}function Es(e){var t=e.type;return t==="number"||t==="range"}function Ts(e){return e===""?null:+e}function ri(e,t){return e===t||(e==null?void 0:e[Hr])===t}function xo(e={},t,r,n){return uo(()=>{var a,i;return fo(()=>{a=i,i=[],Kn(()=>{e!==r(...i)&&(t(e,...i),a&&ri(r(...a),e)&&t(null,...a))})}),()=>{Ur(()=>{i&&ri(r(...i),e)&&t(null,...i)})}}),e}function du(e=!1){const t=It,r=t.l.u;if(!r)return;let n=()=>Pn(t.s);if(e){let a=0,i={};const o=Ka(()=>{let l=!1;const d=t.s;for(const u in d)d[u]!==i[u]&&(i[u]=d[u],l=!0);return l&&a++,a});n=()=>s(o)}r.b.length&&$c(()=>{ni(t,n),Is(r.b)}),Da(()=>{const a=Kn(()=>r.m.map(Ad));return()=>{for(const i of a)typeof i=="function"&&i()}}),r.a.length&&Da(()=>{ni(t,n),Is(r.a)})}function ni(e,t){if(e.l.s)for(const r of e.l.s)s(r);t()}let es=!1;function cu(e){var t=es;try{return es=!1,[e(),es]}finally{es=t}}const uu={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function fu(e,t,r){return new Proxy({props:e,exclude:t},uu)}const vu={get(e,t){if(!e.exclude.includes(t))return s(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,r){if(!(t in e.special)){var n=Ce;try{xr(e.parent_effect),e.special[t]=lt({get[t](){return e.props[t]}},t,Ni)}finally{xr(n)}}return e.special[t](r),La(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),La(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function we(e,t){return new Proxy({props:e,exclude:t,special:{},version:yn(0),parent_effect:Ce},vu)}const pu={get(e,t){let r=e.props.length;for(;r--;){let n=e.props[r];if(Ca(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n)return n[t]}},set(e,t,r){let n=e.props.length;for(;n--;){let a=e.props[n];Ca(a)&&(a=a());const i=hn(a,t);if(i&&i.set)return i.set(r),!0}return!1},getOwnPropertyDescriptor(e,t){let r=e.props.length;for(;r--;){let n=e.props[r];if(Ca(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n){const a=hn(n,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===Hr||t===Ei)return!1;for(let r of e.props)if(Ca(r)&&(r=r()),r!=null&&t in r)return!0;return!1},ownKeys(e){const t=[];for(let r of e.props)if(Ca(r)&&(r=r()),!!r){for(const n in r)t.includes(n)||t.push(n);for(const n of Object.getOwnPropertySymbols(r))t.includes(n)||t.push(n)}return t}};function Ie(...e){return new Proxy({props:e},pu)}function lt(e,t,r,n){var L;var a=!Ha||(r&Kd)!==0,i=(r&Wd)!==0,o=(r&qd)!==0,l=n,d=!0,u=()=>(d&&(d=!1,l=o?Kn(n):n),l),p;if(i){var v=Hr in e||Ei in e;p=((L=hn(e,t))==null?void 0:L.set)??(v&&t in e?M=>e[t]=M:void 0)}var _,E=!1;i?[_,E]=cu(()=>e[t]):_=e[t],_===void 0&&n!==void 0&&(_=u(),p&&(a&&Od(),p(_)));var k;if(a?k=()=>{var M=e[t];return M===void 0?u():(d=!0,M)}:k=()=>{var M=e[t];return M!==void 0&&(l=void 0),M===void 0?l:M},a&&(r&Ni)===0)return k;if(p){var z=e.$$legacy;return(function(M,O){return arguments.length>0?((!a||!O||z||E)&&p(O?k():M),M):k()})}var g=!1,A=((r&Ud)!==0?Ka:oo)(()=>(g=!1,k()));i&&s(A);var $=Ce;return(function(M,O){if(arguments.length>0){const Z=O?s(A):a&&i?Ct(M):M;return f(A,Z),g=!0,l!==void 0&&(l=Z),M}return wn&&g||($.f&Gr)!==0?A.v:s(A)})}const mu="5";var zi;typeof window<"u"&&((zi=window.__svelte??(window.__svelte={})).v??(zi.v=new Set)).add(mu);const br="";async function hu(){const e=await fetch(`${br}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function ra(e,t=null,r=null){const n={provider:e};t&&(n.model=t),r&&(n.api_key=r);const a=await fetch(`${br}/api/configure`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)});if(!a.ok)throw new Error("설정 실패");return a.json()}async function gu(e){const t=await fetch(`${br}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function xu(e,{onProgress:t,onDone:r,onError:n}){const a=new AbortController;return fetch(`${br}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:a.signal}).then(async i=>{if(!i.ok){n==null||n("다운로드 실패");return}const o=i.body.getReader(),l=new TextDecoder;let d="";for(;;){const{done:u,value:p}=await o.read();if(u)break;d+=l.decode(p,{stream:!0});const v=d.split(`
`);d=v.pop()||"";for(const _ of v)if(_.startsWith("data:"))try{const E=JSON.parse(_.slice(5).trim());E.total&&E.completed!==void 0?t==null||t({total:E.total,completed:E.completed,status:E.status}):E.status&&(t==null||t({status:E.status}))}catch{}}r==null||r()}).catch(i=>{i.name!=="AbortError"&&(n==null||n(i.message))}),{abort:()=>a.abort()}}async function bu(){const e=await fetch(`${br}/api/oauth/authorize`);if(!e.ok)throw new Error("OAuth 인증 시작 실패");return e.json()}async function _u(){const e=await fetch(`${br}/api/oauth/status`);return e.ok?e.json():{done:!1}}async function yu(){const e=await fetch(`${br}/api/oauth/logout`,{method:"POST"});if(!e.ok)throw new Error("로그아웃 실패");return e.json()}async function ai(e,t=null,r=null){let n=`${br}/api/export/excel/${encodeURIComponent(e)}`;const a=new URLSearchParams;r?a.set("template_id",r):t&&t.length>0&&a.set("modules",t.join(","));const i=a.toString();i&&(n+=`?${i}`);const o=await fetch(n);if(!o.ok){const _=await o.json().catch(()=>({}));throw new Error(_.detail||"Excel 다운로드 실패")}const l=await o.blob(),u=(o.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),p=u?decodeURIComponent(u[1]):`${e}.xlsx`,v=document.createElement("a");return v.href=URL.createObjectURL(l),v.download=p,v.click(),URL.revokeObjectURL(v.href),p}async function wu(e){const t=await fetch(`${br}/api/data/sources/${encodeURIComponent(e)}`);if(!t.ok)throw new Error("소스 목록 조회 실패");return t.json()}async function ku(e,t,r=50){const n=new URLSearchParams;r!==50&&n.set("max_rows",String(r));const a=n.toString(),i=`${br}/api/data/preview/${encodeURIComponent(e)}/${encodeURIComponent(t)}${a?"?"+a:""}`,o=await fetch(i);if(!o.ok){const l=await o.json().catch(()=>({}));throw new Error(l.detail||"미리보기 실패")}return o.json()}async function Sl(e){const t=await fetch(`${br}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}function Su(e,t,r={},{onMeta:n,onSnapshot:a,onContext:i,onSystemPrompt:o,onToolCall:l,onToolResult:d,onChunk:u,onDone:p,onError:v},_=null){const E={question:t,stream:!0,...r};e&&(E.company=e),_&&_.length>0&&(E.history=_);const k=new AbortController;return fetch(`${br}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(E),signal:k.signal}).then(async z=>{if(!z.ok){const O=await z.json().catch(()=>({}));v==null||v(O.detail||"스트리밍 실패");return}const g=z.body.getReader(),A=new TextDecoder;let $="",L=!1,M=null;for(;;){const{done:O,value:Z}=await g.read();if(O)break;$+=A.decode(Z,{stream:!0});const q=$.split(`
`);$=q.pop()||"";for(const x of q)if(x.startsWith("event:"))M=x.slice(6).trim();else if(x.startsWith("data:")&&M){const F=x.slice(5).trim();try{const Y=JSON.parse(F);M==="meta"?n==null||n(Y):M==="snapshot"?a==null||a(Y):M==="context"?i==null||i(Y):M==="system_prompt"?o==null||o(Y):M==="tool_call"?l==null||l(Y):M==="tool_result"?d==null||d(Y):M==="chunk"?u==null||u(Y.text):M==="error"?v==null||v(Y.error,Y.action,Y.detail):M==="done"&&(L||(L=!0,p==null||p()))}catch{}M=null}}L||(L=!0,p==null||p())}).catch(z=>{z.name!=="AbortError"&&(v==null||v(z.message))}),{abort:()=>k.abort()}}const zu=(e,t)=>{const r=new Array(e.length+t.length);for(let n=0;n<e.length;n++)r[n]=e[n];for(let n=0;n<t.length;n++)r[e.length+n]=t[n];return r},Mu=(e,t)=>({classGroupId:e,validator:t}),zl=(e=new Map,t=null,r)=>({nextPart:e,validators:t,classGroupId:r}),ds="-",si=[],Au="arbitrary..",Cu=e=>{const t=Tu(e),{conflictingClassGroups:r,conflictingClassGroupModifiers:n}=e;return{getClassGroupId:o=>{if(o.startsWith("[")&&o.endsWith("]"))return Eu(o);const l=o.split(ds),d=l[0]===""&&l.length>1?1:0;return Ml(l,d,t)},getConflictingClassGroupIds:(o,l)=>{if(l){const d=n[o],u=r[o];return d?u?zu(u,d):d:u||si}return r[o]||si}}},Ml=(e,t,r)=>{if(e.length-t===0)return r.classGroupId;const a=e[t],i=r.nextPart.get(a);if(i){const u=Ml(e,t+1,i);if(u)return u}const o=r.validators;if(o===null)return;const l=t===0?e.join(ds):e.slice(t).join(ds),d=o.length;for(let u=0;u<d;u++){const p=o[u];if(p.validator(l))return p.classGroupId}},Eu=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),r=t.indexOf(":"),n=t.slice(0,r);return n?Au+n:void 0})(),Tu=e=>{const{theme:t,classGroups:r}=e;return $u(r,t)},$u=(e,t)=>{const r=zl();for(const n in e){const a=e[n];bo(a,r,n,t)}return r},bo=(e,t,r,n)=>{const a=e.length;for(let i=0;i<a;i++){const o=e[i];Nu(o,t,r,n)}},Nu=(e,t,r,n)=>{if(typeof e=="string"){Pu(e,t,r);return}if(typeof e=="function"){Iu(e,t,r,n);return}Lu(e,t,r,n)},Pu=(e,t,r)=>{const n=e===""?t:Al(t,e);n.classGroupId=r},Iu=(e,t,r,n)=>{if(Ou(e)){bo(e(n),t,r,n);return}t.validators===null&&(t.validators=[]),t.validators.push(Mu(r,e))},Lu=(e,t,r,n)=>{const a=Object.entries(e),i=a.length;for(let o=0;o<i;o++){const[l,d]=a[o];bo(d,Al(t,l),r,n)}},Al=(e,t)=>{let r=e;const n=t.split(ds),a=n.length;for(let i=0;i<a;i++){const o=n[i];let l=r.nextPart.get(o);l||(l=zl(),r.nextPart.set(o,l)),r=l}return r},Ou=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,Ru=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,r=Object.create(null),n=Object.create(null);const a=(i,o)=>{r[i]=o,t++,t>e&&(t=0,n=r,r=Object.create(null))};return{get(i){let o=r[i];if(o!==void 0)return o;if((o=n[i])!==void 0)return a(i,o),o},set(i,o){i in r?r[i]=o:a(i,o)}}},Qs="!",oi=":",ju=[],ii=(e,t,r,n,a)=>({modifiers:e,hasImportantModifier:t,baseClassName:r,maybePostfixModifierPosition:n,isExternal:a}),Du=e=>{const{prefix:t,experimentalParseClassName:r}=e;let n=a=>{const i=[];let o=0,l=0,d=0,u;const p=a.length;for(let z=0;z<p;z++){const g=a[z];if(o===0&&l===0){if(g===oi){i.push(a.slice(d,z)),d=z+1;continue}if(g==="/"){u=z;continue}}g==="["?o++:g==="]"?o--:g==="("?l++:g===")"&&l--}const v=i.length===0?a:a.slice(d);let _=v,E=!1;v.endsWith(Qs)?(_=v.slice(0,-1),E=!0):v.startsWith(Qs)&&(_=v.slice(1),E=!0);const k=u&&u>d?u-d:void 0;return ii(i,E,_,k)};if(t){const a=t+oi,i=n;n=o=>o.startsWith(a)?i(o.slice(a.length)):ii(ju,!1,o,void 0,!0)}if(r){const a=n;n=i=>r({className:i,parseClassName:a})}return n},Fu=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((r,n)=>{t.set(r,1e6+n)}),r=>{const n=[];let a=[];for(let i=0;i<r.length;i++){const o=r[i],l=o[0]==="[",d=t.has(o);l||d?(a.length>0&&(a.sort(),n.push(...a),a=[]),n.push(o)):a.push(o)}return a.length>0&&(a.sort(),n.push(...a)),n}},Bu=e=>({cache:Ru(e.cacheSize),parseClassName:Du(e),sortModifiers:Fu(e),...Cu(e)}),Vu=/\s+/,Gu=(e,t)=>{const{parseClassName:r,getClassGroupId:n,getConflictingClassGroupIds:a,sortModifiers:i}=t,o=[],l=e.trim().split(Vu);let d="";for(let u=l.length-1;u>=0;u-=1){const p=l[u],{isExternal:v,modifiers:_,hasImportantModifier:E,baseClassName:k,maybePostfixModifierPosition:z}=r(p);if(v){d=p+(d.length>0?" "+d:d);continue}let g=!!z,A=n(g?k.substring(0,z):k);if(!A){if(!g){d=p+(d.length>0?" "+d:d);continue}if(A=n(k),!A){d=p+(d.length>0?" "+d:d);continue}g=!1}const $=_.length===0?"":_.length===1?_[0]:i(_).join(":"),L=E?$+Qs:$,M=L+A;if(o.indexOf(M)>-1)continue;o.push(M);const O=a(A,g);for(let Z=0;Z<O.length;++Z){const q=O[Z];o.push(L+q)}d=p+(d.length>0?" "+d:d)}return d},Hu=(...e)=>{let t=0,r,n,a="";for(;t<e.length;)(r=e[t++])&&(n=Cl(r))&&(a&&(a+=" "),a+=n);return a},Cl=e=>{if(typeof e=="string")return e;let t,r="";for(let n=0;n<e.length;n++)e[n]&&(t=Cl(e[n]))&&(r&&(r+=" "),r+=t);return r},Uu=(e,...t)=>{let r,n,a,i;const o=d=>{const u=t.reduce((p,v)=>v(p),e());return r=Bu(u),n=r.cache.get,a=r.cache.set,i=l,l(d)},l=d=>{const u=n(d);if(u)return u;const p=Gu(d,r);return a(d,p),p};return i=o,(...d)=>i(Hu(...d))},Ku=[],At=e=>{const t=r=>r[e]||Ku;return t.isThemeGetter=!0,t},El=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Tl=/^\((?:(\w[\w-]*):)?(.+)\)$/i,Wu=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,qu=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,Yu=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,Ju=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,Xu=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,Zu=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,dn=e=>Wu.test(e),he=e=>!!e&&!Number.isNaN(Number(e)),cn=e=>!!e&&Number.isInteger(Number(e)),$s=e=>e.endsWith("%")&&he(e.slice(0,-1)),Xr=e=>qu.test(e),$l=()=>!0,Qu=e=>Yu.test(e)&&!Ju.test(e),_o=()=>!1,ef=e=>Xu.test(e),tf=e=>Zu.test(e),rf=e=>!U(e)&&!K(e),nf=e=>zn(e,Il,_o),U=e=>El.test(e),$n=e=>zn(e,Ll,Qu),li=e=>zn(e,ff,he),af=e=>zn(e,Rl,$l),sf=e=>zn(e,Ol,_o),di=e=>zn(e,Nl,_o),of=e=>zn(e,Pl,tf),ts=e=>zn(e,jl,ef),K=e=>Tl.test(e),Na=e=>Yn(e,Ll),lf=e=>Yn(e,Ol),ci=e=>Yn(e,Nl),df=e=>Yn(e,Il),cf=e=>Yn(e,Pl),rs=e=>Yn(e,jl,!0),uf=e=>Yn(e,Rl,!0),zn=(e,t,r)=>{const n=El.exec(e);return n?n[1]?t(n[1]):r(n[2]):!1},Yn=(e,t,r=!1)=>{const n=Tl.exec(e);return n?n[1]?t(n[1]):r:!1},Nl=e=>e==="position"||e==="percentage",Pl=e=>e==="image"||e==="url",Il=e=>e==="length"||e==="size"||e==="bg-size",Ll=e=>e==="length",ff=e=>e==="number",Ol=e=>e==="family-name",Rl=e=>e==="number"||e==="weight",jl=e=>e==="shadow",vf=()=>{const e=At("color"),t=At("font"),r=At("text"),n=At("font-weight"),a=At("tracking"),i=At("leading"),o=At("breakpoint"),l=At("container"),d=At("spacing"),u=At("radius"),p=At("shadow"),v=At("inset-shadow"),_=At("text-shadow"),E=At("drop-shadow"),k=At("blur"),z=At("perspective"),g=At("aspect"),A=At("ease"),$=At("animate"),L=()=>["auto","avoid","all","avoid-page","page","left","right","column"],M=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],O=()=>[...M(),K,U],Z=()=>["auto","hidden","clip","visible","scroll"],q=()=>["auto","contain","none"],x=()=>[K,U,d],F=()=>[dn,"full","auto",...x()],Y=()=>[cn,"none","subgrid",K,U],ue=()=>["auto",{span:["full",cn,K,U]},cn,K,U],pe=()=>[cn,"auto",K,U],Ye=()=>["auto","min","max","fr",K,U],P=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],R=()=>["start","end","center","stretch","center-safe","end-safe"],Q=()=>["auto",...x()],ae=()=>[dn,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...x()],de=()=>[dn,"screen","full","dvw","lvw","svw","min","max","fit",...x()],H=()=>[dn,"screen","full","lh","dvh","lvh","svh","min","max","fit",...x()],y=()=>[e,K,U],ke=()=>[...M(),ci,di,{position:[K,U]}],fe=()=>["no-repeat",{repeat:["","x","y","space","round"]}],ut=()=>["auto","cover","contain",df,nf,{size:[K,U]}],Ve=()=>[$s,Na,$n],Ge=()=>["","none","full",u,K,U],ee=()=>["",he,Na,$n],se=()=>["solid","dashed","dotted","double"],ve=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],Se=()=>[he,$s,ci,di],C=()=>["","none",k,K,U],N=()=>["none",he,K,U],J=()=>["none",he,K,U],He=()=>[he,K,U],re=()=>[dn,"full",...x()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Xr],breakpoint:[Xr],color:[$l],container:[Xr],"drop-shadow":[Xr],ease:["in","out","in-out"],font:[rf],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Xr],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Xr],shadow:[Xr],spacing:["px",he],text:[Xr],"text-shadow":[Xr],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",dn,U,K,g]}],container:["container"],columns:[{columns:[he,U,K,l]}],"break-after":[{"break-after":L()}],"break-before":[{"break-before":L()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:O()}],overflow:[{overflow:Z()}],"overflow-x":[{"overflow-x":Z()}],"overflow-y":[{"overflow-y":Z()}],overscroll:[{overscroll:q()}],"overscroll-x":[{"overscroll-x":q()}],"overscroll-y":[{"overscroll-y":q()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:F()}],"inset-x":[{"inset-x":F()}],"inset-y":[{"inset-y":F()}],start:[{"inset-s":F(),start:F()}],end:[{"inset-e":F(),end:F()}],"inset-bs":[{"inset-bs":F()}],"inset-be":[{"inset-be":F()}],top:[{top:F()}],right:[{right:F()}],bottom:[{bottom:F()}],left:[{left:F()}],visibility:["visible","invisible","collapse"],z:[{z:[cn,"auto",K,U]}],basis:[{basis:[dn,"full","auto",l,...x()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[he,dn,"auto","initial","none",U]}],grow:[{grow:["",he,K,U]}],shrink:[{shrink:["",he,K,U]}],order:[{order:[cn,"first","last","none",K,U]}],"grid-cols":[{"grid-cols":Y()}],"col-start-end":[{col:ue()}],"col-start":[{"col-start":pe()}],"col-end":[{"col-end":pe()}],"grid-rows":[{"grid-rows":Y()}],"row-start-end":[{row:ue()}],"row-start":[{"row-start":pe()}],"row-end":[{"row-end":pe()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":Ye()}],"auto-rows":[{"auto-rows":Ye()}],gap:[{gap:x()}],"gap-x":[{"gap-x":x()}],"gap-y":[{"gap-y":x()}],"justify-content":[{justify:[...P(),"normal"]}],"justify-items":[{"justify-items":[...R(),"normal"]}],"justify-self":[{"justify-self":["auto",...R()]}],"align-content":[{content:["normal",...P()]}],"align-items":[{items:[...R(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...R(),{baseline:["","last"]}]}],"place-content":[{"place-content":P()}],"place-items":[{"place-items":[...R(),"baseline"]}],"place-self":[{"place-self":["auto",...R()]}],p:[{p:x()}],px:[{px:x()}],py:[{py:x()}],ps:[{ps:x()}],pe:[{pe:x()}],pbs:[{pbs:x()}],pbe:[{pbe:x()}],pt:[{pt:x()}],pr:[{pr:x()}],pb:[{pb:x()}],pl:[{pl:x()}],m:[{m:Q()}],mx:[{mx:Q()}],my:[{my:Q()}],ms:[{ms:Q()}],me:[{me:Q()}],mbs:[{mbs:Q()}],mbe:[{mbe:Q()}],mt:[{mt:Q()}],mr:[{mr:Q()}],mb:[{mb:Q()}],ml:[{ml:Q()}],"space-x":[{"space-x":x()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":x()}],"space-y-reverse":["space-y-reverse"],size:[{size:ae()}],"inline-size":[{inline:["auto",...de()]}],"min-inline-size":[{"min-inline":["auto",...de()]}],"max-inline-size":[{"max-inline":["none",...de()]}],"block-size":[{block:["auto",...H()]}],"min-block-size":[{"min-block":["auto",...H()]}],"max-block-size":[{"max-block":["none",...H()]}],w:[{w:[l,"screen",...ae()]}],"min-w":[{"min-w":[l,"screen","none",...ae()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[o]},...ae()]}],h:[{h:["screen","lh",...ae()]}],"min-h":[{"min-h":["screen","lh","none",...ae()]}],"max-h":[{"max-h":["screen","lh",...ae()]}],"font-size":[{text:["base",r,Na,$n]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[n,uf,af]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",$s,U]}],"font-family":[{font:[lf,sf,t]}],"font-features":[{"font-features":[U]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[a,K,U]}],"line-clamp":[{"line-clamp":[he,"none",K,li]}],leading:[{leading:[i,...x()]}],"list-image":[{"list-image":["none",K,U]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",K,U]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:y()}],"text-color":[{text:y()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...se(),"wavy"]}],"text-decoration-thickness":[{decoration:[he,"from-font","auto",K,$n]}],"text-decoration-color":[{decoration:y()}],"underline-offset":[{"underline-offset":[he,"auto",K,U]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:x()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",K,U]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",K,U]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:ke()}],"bg-repeat":[{bg:fe()}],"bg-size":[{bg:ut()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},cn,K,U],radial:["",K,U],conic:[cn,K,U]},cf,of]}],"bg-color":[{bg:y()}],"gradient-from-pos":[{from:Ve()}],"gradient-via-pos":[{via:Ve()}],"gradient-to-pos":[{to:Ve()}],"gradient-from":[{from:y()}],"gradient-via":[{via:y()}],"gradient-to":[{to:y()}],rounded:[{rounded:Ge()}],"rounded-s":[{"rounded-s":Ge()}],"rounded-e":[{"rounded-e":Ge()}],"rounded-t":[{"rounded-t":Ge()}],"rounded-r":[{"rounded-r":Ge()}],"rounded-b":[{"rounded-b":Ge()}],"rounded-l":[{"rounded-l":Ge()}],"rounded-ss":[{"rounded-ss":Ge()}],"rounded-se":[{"rounded-se":Ge()}],"rounded-ee":[{"rounded-ee":Ge()}],"rounded-es":[{"rounded-es":Ge()}],"rounded-tl":[{"rounded-tl":Ge()}],"rounded-tr":[{"rounded-tr":Ge()}],"rounded-br":[{"rounded-br":Ge()}],"rounded-bl":[{"rounded-bl":Ge()}],"border-w":[{border:ee()}],"border-w-x":[{"border-x":ee()}],"border-w-y":[{"border-y":ee()}],"border-w-s":[{"border-s":ee()}],"border-w-e":[{"border-e":ee()}],"border-w-bs":[{"border-bs":ee()}],"border-w-be":[{"border-be":ee()}],"border-w-t":[{"border-t":ee()}],"border-w-r":[{"border-r":ee()}],"border-w-b":[{"border-b":ee()}],"border-w-l":[{"border-l":ee()}],"divide-x":[{"divide-x":ee()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":ee()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...se(),"hidden","none"]}],"divide-style":[{divide:[...se(),"hidden","none"]}],"border-color":[{border:y()}],"border-color-x":[{"border-x":y()}],"border-color-y":[{"border-y":y()}],"border-color-s":[{"border-s":y()}],"border-color-e":[{"border-e":y()}],"border-color-bs":[{"border-bs":y()}],"border-color-be":[{"border-be":y()}],"border-color-t":[{"border-t":y()}],"border-color-r":[{"border-r":y()}],"border-color-b":[{"border-b":y()}],"border-color-l":[{"border-l":y()}],"divide-color":[{divide:y()}],"outline-style":[{outline:[...se(),"none","hidden"]}],"outline-offset":[{"outline-offset":[he,K,U]}],"outline-w":[{outline:["",he,Na,$n]}],"outline-color":[{outline:y()}],shadow:[{shadow:["","none",p,rs,ts]}],"shadow-color":[{shadow:y()}],"inset-shadow":[{"inset-shadow":["none",v,rs,ts]}],"inset-shadow-color":[{"inset-shadow":y()}],"ring-w":[{ring:ee()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:y()}],"ring-offset-w":[{"ring-offset":[he,$n]}],"ring-offset-color":[{"ring-offset":y()}],"inset-ring-w":[{"inset-ring":ee()}],"inset-ring-color":[{"inset-ring":y()}],"text-shadow":[{"text-shadow":["none",_,rs,ts]}],"text-shadow-color":[{"text-shadow":y()}],opacity:[{opacity:[he,K,U]}],"mix-blend":[{"mix-blend":[...ve(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":ve()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[he]}],"mask-image-linear-from-pos":[{"mask-linear-from":Se()}],"mask-image-linear-to-pos":[{"mask-linear-to":Se()}],"mask-image-linear-from-color":[{"mask-linear-from":y()}],"mask-image-linear-to-color":[{"mask-linear-to":y()}],"mask-image-t-from-pos":[{"mask-t-from":Se()}],"mask-image-t-to-pos":[{"mask-t-to":Se()}],"mask-image-t-from-color":[{"mask-t-from":y()}],"mask-image-t-to-color":[{"mask-t-to":y()}],"mask-image-r-from-pos":[{"mask-r-from":Se()}],"mask-image-r-to-pos":[{"mask-r-to":Se()}],"mask-image-r-from-color":[{"mask-r-from":y()}],"mask-image-r-to-color":[{"mask-r-to":y()}],"mask-image-b-from-pos":[{"mask-b-from":Se()}],"mask-image-b-to-pos":[{"mask-b-to":Se()}],"mask-image-b-from-color":[{"mask-b-from":y()}],"mask-image-b-to-color":[{"mask-b-to":y()}],"mask-image-l-from-pos":[{"mask-l-from":Se()}],"mask-image-l-to-pos":[{"mask-l-to":Se()}],"mask-image-l-from-color":[{"mask-l-from":y()}],"mask-image-l-to-color":[{"mask-l-to":y()}],"mask-image-x-from-pos":[{"mask-x-from":Se()}],"mask-image-x-to-pos":[{"mask-x-to":Se()}],"mask-image-x-from-color":[{"mask-x-from":y()}],"mask-image-x-to-color":[{"mask-x-to":y()}],"mask-image-y-from-pos":[{"mask-y-from":Se()}],"mask-image-y-to-pos":[{"mask-y-to":Se()}],"mask-image-y-from-color":[{"mask-y-from":y()}],"mask-image-y-to-color":[{"mask-y-to":y()}],"mask-image-radial":[{"mask-radial":[K,U]}],"mask-image-radial-from-pos":[{"mask-radial-from":Se()}],"mask-image-radial-to-pos":[{"mask-radial-to":Se()}],"mask-image-radial-from-color":[{"mask-radial-from":y()}],"mask-image-radial-to-color":[{"mask-radial-to":y()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":M()}],"mask-image-conic-pos":[{"mask-conic":[he]}],"mask-image-conic-from-pos":[{"mask-conic-from":Se()}],"mask-image-conic-to-pos":[{"mask-conic-to":Se()}],"mask-image-conic-from-color":[{"mask-conic-from":y()}],"mask-image-conic-to-color":[{"mask-conic-to":y()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:ke()}],"mask-repeat":[{mask:fe()}],"mask-size":[{mask:ut()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",K,U]}],filter:[{filter:["","none",K,U]}],blur:[{blur:C()}],brightness:[{brightness:[he,K,U]}],contrast:[{contrast:[he,K,U]}],"drop-shadow":[{"drop-shadow":["","none",E,rs,ts]}],"drop-shadow-color":[{"drop-shadow":y()}],grayscale:[{grayscale:["",he,K,U]}],"hue-rotate":[{"hue-rotate":[he,K,U]}],invert:[{invert:["",he,K,U]}],saturate:[{saturate:[he,K,U]}],sepia:[{sepia:["",he,K,U]}],"backdrop-filter":[{"backdrop-filter":["","none",K,U]}],"backdrop-blur":[{"backdrop-blur":C()}],"backdrop-brightness":[{"backdrop-brightness":[he,K,U]}],"backdrop-contrast":[{"backdrop-contrast":[he,K,U]}],"backdrop-grayscale":[{"backdrop-grayscale":["",he,K,U]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[he,K,U]}],"backdrop-invert":[{"backdrop-invert":["",he,K,U]}],"backdrop-opacity":[{"backdrop-opacity":[he,K,U]}],"backdrop-saturate":[{"backdrop-saturate":[he,K,U]}],"backdrop-sepia":[{"backdrop-sepia":["",he,K,U]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":x()}],"border-spacing-x":[{"border-spacing-x":x()}],"border-spacing-y":[{"border-spacing-y":x()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",K,U]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[he,"initial",K,U]}],ease:[{ease:["linear","initial",A,K,U]}],delay:[{delay:[he,K,U]}],animate:[{animate:["none",$,K,U]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[z,K,U]}],"perspective-origin":[{"perspective-origin":O()}],rotate:[{rotate:N()}],"rotate-x":[{"rotate-x":N()}],"rotate-y":[{"rotate-y":N()}],"rotate-z":[{"rotate-z":N()}],scale:[{scale:J()}],"scale-x":[{"scale-x":J()}],"scale-y":[{"scale-y":J()}],"scale-z":[{"scale-z":J()}],"scale-3d":["scale-3d"],skew:[{skew:He()}],"skew-x":[{"skew-x":He()}],"skew-y":[{"skew-y":He()}],transform:[{transform:[K,U,"","none","gpu","cpu"]}],"transform-origin":[{origin:O()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:re()}],"translate-x":[{"translate-x":re()}],"translate-y":[{"translate-y":re()}],"translate-z":[{"translate-z":re()}],"translate-none":["translate-none"],accent:[{accent:y()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:y()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",K,U]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":x()}],"scroll-mx":[{"scroll-mx":x()}],"scroll-my":[{"scroll-my":x()}],"scroll-ms":[{"scroll-ms":x()}],"scroll-me":[{"scroll-me":x()}],"scroll-mbs":[{"scroll-mbs":x()}],"scroll-mbe":[{"scroll-mbe":x()}],"scroll-mt":[{"scroll-mt":x()}],"scroll-mr":[{"scroll-mr":x()}],"scroll-mb":[{"scroll-mb":x()}],"scroll-ml":[{"scroll-ml":x()}],"scroll-p":[{"scroll-p":x()}],"scroll-px":[{"scroll-px":x()}],"scroll-py":[{"scroll-py":x()}],"scroll-ps":[{"scroll-ps":x()}],"scroll-pe":[{"scroll-pe":x()}],"scroll-pbs":[{"scroll-pbs":x()}],"scroll-pbe":[{"scroll-pbe":x()}],"scroll-pt":[{"scroll-pt":x()}],"scroll-pr":[{"scroll-pr":x()}],"scroll-pb":[{"scroll-pb":x()}],"scroll-pl":[{"scroll-pl":x()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",K,U]}],fill:[{fill:["none",...y()]}],"stroke-w":[{stroke:[he,Na,$n,li]}],stroke:[{stroke:["none",...y()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},pf=Uu(vf);function Qe(...e){return pf(bl(e))}const eo="dartlab-conversations",ui=50;function mf(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function hf(){try{const e=localStorage.getItem(eo);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const gf=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function fi(e){return e.map(t=>({...t,messages:t.messages.map(r=>{if(r.role!=="assistant")return r;const n={};for(const[a,i]of Object.entries(r))gf.includes(a)||(n[a]=i);return n})}))}function vi(e){try{const t={conversations:fi(e.conversations),activeId:e.activeId};localStorage.setItem(eo,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:fi(e.conversations),activeId:e.activeId};localStorage.setItem(eo,JSON.stringify(t))}catch{}}}}function xf(){const e=hf();let t=V(Ct(e.conversations)),r=V(Ct(e.activeId));s(r)&&!s(t).find(z=>z.id===s(r))&&f(r,null);let n=null;function a(){n&&clearTimeout(n),n=setTimeout(()=>{vi({conversations:s(t),activeId:s(r)}),n=null},300)}function i(){n&&clearTimeout(n),n=null,vi({conversations:s(t),activeId:s(r)})}function o(){return s(t).find(z=>z.id===s(r))||null}function l(){const z={id:mf(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return f(t,[z,...s(t)],!0),s(t).length>ui&&f(t,s(t).slice(0,ui),!0),f(r,z.id,!0),i(),z.id}function d(z){s(t).find(g=>g.id===z)&&(f(r,z,!0),i())}function u(z,g,A=null){const $=o();if(!$)return;const L={role:z,text:g};A&&(L.meta=A),$.messages=[...$.messages,L],$.updatedAt=Date.now(),$.title==="새 대화"&&z==="user"&&($.title=g.length>30?g.slice(0,30)+"...":g),f(t,[...s(t)],!0),i()}function p(z){const g=o();if(!g||g.messages.length===0)return;const A=g.messages[g.messages.length-1];Object.assign(A,z),g.updatedAt=Date.now(),f(t,[...s(t)],!0),a()}function v(z){f(t,s(t).filter(g=>g.id!==z),!0),s(r)===z&&f(r,s(t).length>0?s(t)[0].id:null,!0),i()}function _(){const z=o();!z||z.messages.length===0||(z.messages=z.messages.slice(0,-1),z.updatedAt=Date.now(),f(t,[...s(t)],!0),i())}function E(z,g){const A=s(t).find($=>$.id===z);A&&(A.title=g,f(t,[...s(t)],!0),i())}function k(){f(t,[],!0),f(r,null),i()}return{get conversations(){return s(t)},get activeId(){return s(r)},get active(){return o()},createConversation:l,setActive:d,addMessage:u,updateLastMessage:p,removeLastMessage:_,deleteConversation:v,updateTitle:E,clearAll:k,flush:i}}var bf=w("<a><!></a>"),_f=w("<button><!></button>");function yf(e,t){$r(t,!0);let r=lt(t,"variant",3,"default"),n=lt(t,"size",3,"default"),a=fu(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const i={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},o={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=ce(),d=G(l);{var u=v=>{var _=bf();ls(_,k=>({class:k,...a}),[()=>Qe("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",i[r()],o[n()],t.class)]);var E=c(_);Xs(E,()=>t.children),m(v,_)},p=v=>{var _=_f();ls(_,k=>({class:k,...a}),[()=>Qe("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",i[r()],o[n()],t.class)]);var E=c(_);Xs(E,()=>t.children),m(v,_)};T(d,v=>{t.href?v(u):v(p,-1)})}m(e,l),Nr()}nc();/**
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
 */const pi=(...e)=>e.filter((t,r,n)=>!!t&&t.trim()!==""&&n.indexOf(t)===r).join(" ").trim();var Sf=Wc("<svg><!><!></svg>");function Le(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]),n=we(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);$r(t,!1);let a=lt(t,"name",8,void 0),i=lt(t,"color",8,"currentColor"),o=lt(t,"size",8,24),l=lt(t,"strokeWidth",8,2),d=lt(t,"absoluteStrokeWidth",8,!1),u=lt(t,"iconNode",24,()=>[]);du();var p=Sf();ls(p,(E,k,z)=>({...wf,...E,...n,width:o(),height:o(),stroke:i(),"stroke-width":k,class:z}),[()=>kf(n)?void 0:{"aria-hidden":"true"},()=>(Pn(d()),Pn(l()),Pn(o()),Kn(()=>d()?Number(l())*24/Number(o()):l())),()=>(Pn(pi),Pn(a()),Pn(r),Kn(()=>pi("lucide-icon","lucide",a()?`lucide-${a()}`:"",r.class)))]);var v=c(p);rt(v,1,u,tt,(E,k)=>{var z=ne(()=>os(s(k),2));let g=()=>s(z)[0],A=()=>s(z)[1];var $=ce(),L=G($);eu(L,g,!0,(M,O)=>{ls(M,()=>({...A()}))}),m(E,$)});var _=h(v);Ee(_,t,"default",{}),m(e,p),Nr()}function zf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m12 19-7-7 7-7"}],["path",{d:"M19 12H5"}]];Le(e,Ie({name:"arrow-left"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Mf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];Le(e,Ie({name:"arrow-up"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function mi(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];Le(e,Ie({name:"brain"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Af(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M20 6 9 17l-5-5"}]];Le(e,Ie({name:"check"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Cf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m6 9 6 6 6-6"}]];Le(e,Ie({name:"chevron-down"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function hi(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m9 18 6-6-6-6"}]];Le(e,Ie({name:"chevron-right"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Nn(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];Le(e,Ie({name:"circle-alert"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Ns(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];Le(e,Ie({name:"circle-check"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Ef(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];Le(e,Ie({name:"clock"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Tf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];Le(e,Ie({name:"code"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function $f(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];Le(e,Ie({name:"coffee"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function mn(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];Le(e,Ie({name:"database"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function aa(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];Le(e,Ie({name:"download"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function gi(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];Le(e,Ie({name:"external-link"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function ja(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];Le(e,Ie({name:"file-text"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Nf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];Le(e,Ie({name:"github"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function xi(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];Le(e,Ie({name:"key"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Pf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m5 8 6 6"}],["path",{d:"m4 14 6-6 2-3"}],["path",{d:"M2 5h12"}],["path",{d:"M7 2h1"}],["path",{d:"m22 22-5-10-5 10"}],["path",{d:"M14 18h6"}]];Le(e,Ie({name:"languages"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Wt(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];Le(e,Ie({name:"loader-circle"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function If(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m10 17 5-5-5-5"}],["path",{d:"M15 12H3"}],["path",{d:"M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"}]];Le(e,Ie({name:"log-in"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Lf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];Le(e,Ie({name:"log-out"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Of(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];Le(e,Ie({name:"menu"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function bi(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];Le(e,Ie({name:"message-square"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Rf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];Le(e,Ie({name:"panel-left-close"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function _i(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];Le(e,Ie({name:"plus"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function jf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];Le(e,Ie({name:"refresh-cw"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function yo(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];Le(e,Ie({name:"search"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Df(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];Le(e,Ie({name:"settings"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Ff(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];Le(e,Ie({name:"square"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function yi(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];Le(e,Ie({name:"table-2"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Bf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];Le(e,Ie({name:"terminal"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Vf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];Le(e,Ie({name:"trash-2"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Gf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];Le(e,Ie({name:"triangle-alert"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function Hf(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];Le(e,Ie({name:"wrench"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}function wo(e,t){const r=we(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];Le(e,Ie({name:"x"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=ce(),l=G(o);Ee(l,t,"default",{}),m(a,o)},$$slots:{default:!0}}))}var Uf=w("<!> 새 대화",1),Kf=w('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-dl-bg-card border border-dl-border"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),Wf=w('<div role="button" tabindex="0"><!> <span class="flex-1 truncate"> </span> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),qf=w('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),Yf=w('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/50 text-[10px] text-dl-text-dim"> </div>'),Jf=w('<div class="flex flex-col h-full min-w-[260px]"><div class="flex items-center gap-2.5 px-4 pt-4 pb-2"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <span class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</span></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 space-y-4"></div> <!></div>'),Xf=w("<button><!></button>"),Zf=w('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),Qf=w("<aside><!></aside>");function ev(e,t){$r(t,!0);let r=lt(t,"conversations",19,()=>[]),n=lt(t,"activeId",3,null),a=lt(t,"open",3,!0),i=lt(t,"version",3,""),o=V("");function l(k){const z=new Date().setHours(0,0,0,0),g=z-864e5,A=z-7*864e5,$={오늘:[],어제:[],"이번 주":[],이전:[]};for(const M of k)M.updatedAt>=z?$.오늘.push(M):M.updatedAt>=g?$.어제.push(M):M.updatedAt>=A?$["이번 주"].push(M):$.이전.push(M);const L=[];for(const[M,O]of Object.entries($))O.length>0&&L.push({label:M,items:O});return L}let d=ne(()=>s(o).trim()?r().filter(k=>k.title.toLowerCase().includes(s(o).toLowerCase())):r()),u=ne(()=>l(s(d)));var p=Qf(),v=c(p);{var _=k=>{var z=Jf(),g=h(c(z),2),A=c(g);yf(A,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(q,x)=>{var F=Uf(),Y=G(F);_i(Y,{size:16}),m(q,F)},$$slots:{default:!0}});var $=h(g,2);{var L=q=>{var x=Kf(),F=c(x),Y=c(F);yo(Y,{size:12,class:"text-dl-text-dim flex-shrink-0"});var ue=h(Y,2);na(ue,()=>s(o),pe=>f(o,pe)),m(q,x)};T($,q=>{r().length>3&&q(L)})}var M=h($,2);rt(M,21,()=>s(u),tt,(q,x)=>{var F=qf(),Y=c(F),ue=c(Y),pe=h(Y,2);rt(pe,17,()=>s(x).items,tt,(Ye,P)=>{var R=Wf(),Q=c(R);bi(Q,{size:14,class:"flex-shrink-0 opacity-50"});var ae=h(Q,2),de=c(ae),H=h(ae,2),y=c(H);Vf(y,{size:12}),j(ke=>{Ze(R,1,ke),D(de,s(P).title)},[()=>Xe(Qe("w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-[13px] transition-colors group cursor-pointer",s(P).id===n()?"bg-dl-bg-card text-dl-text border-l-2 border-dl-primary":"text-dl-text-muted hover:bg-dl-bg-card/50 hover:text-dl-text border-l-2 border-transparent"))]),W("click",R,()=>{var ke;return(ke=t.onSelect)==null?void 0:ke.call(t,s(P).id)}),W("keydown",R,ke=>{var fe;ke.key==="Enter"&&((fe=t.onSelect)==null||fe.call(t,s(P).id))}),W("click",H,ke=>{var fe;ke.stopPropagation(),(fe=t.onDelete)==null||fe.call(t,s(P).id)}),m(Ye,R)}),j(()=>D(ue,s(x).label)),m(q,F)});var O=h(M,2);{var Z=q=>{var x=Yf(),F=c(x);j(()=>D(F,`DartLab v${i()??""}`)),m(q,x)};T(O,q=>{i()&&q(Z)})}m(k,z)},E=k=>{var z=Zf(),g=h(c(z),2),A=c(g);_i(A,{size:18});var $=h(g,2);rt($,21,()=>r().slice(0,10),tt,(L,M)=>{var O=Xf(),Z=c(O);bi(Z,{size:16}),j(q=>{Ze(O,1,q),Ba(O,"title",s(M).title)},[()=>Xe(Qe("p-2 rounded-lg transition-colors w-full flex justify-center",s(M).id===n()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),W("click",O,()=>{var q;return(q=t.onSelect)==null?void 0:q.call(t,s(M).id)}),m(L,O)}),W("click",g,function(...L){var M;(M=t.onNewChat)==null||M.apply(this,L)}),m(k,z)};T(v,k=>{a()?k(_):k(E,-1)})}j(k=>Ze(p,1,k),[()=>Xe(Qe("flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",a()?"w-[260px]":"w-[52px]"))]),m(e,p),Nr()}Sn(["click","keydown"]);var tv=w('<button class="send-btn active"><!></button>'),rv=w("<button><!></button>"),nv=w('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),av=w('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),sv=w('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),ov=w('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function Dl(e,t){$r(t,!0);let r=lt(t,"inputText",15,""),n=lt(t,"isLoading",3,!1),a=lt(t,"large",3,!1),i=lt(t,"placeholder",3,"메시지를 입력하세요..."),o=V(Ct([])),l=V(!1),d=V(-1),u=null,p=V(void 0);function v(x){var F;if(s(l)&&s(o).length>0){if(x.key==="ArrowDown"){x.preventDefault(),f(d,(s(d)+1)%s(o).length);return}if(x.key==="ArrowUp"){x.preventDefault(),f(d,s(d)<=0?s(o).length-1:s(d)-1,!0);return}if(x.key==="Enter"&&s(d)>=0){x.preventDefault(),k(s(o)[s(d)]);return}if(x.key==="Escape"){f(l,!1),f(d,-1);return}}x.key==="Enter"&&!x.shiftKey&&(x.preventDefault(),f(l,!1),(F=t.onSend)==null||F.call(t))}function _(x){x.target.style.height="auto",x.target.style.height=Math.min(x.target.scrollHeight,200)+"px"}function E(x){_(x);const F=r();u&&clearTimeout(u),F.length>=2&&!/\s/.test(F.slice(-1))?u=setTimeout(async()=>{var Y;try{const ue=await Sl(F.trim());((Y=ue.results)==null?void 0:Y.length)>0?(f(o,ue.results.slice(0,6),!0),f(l,!0),f(d,-1)):f(l,!1)}catch{f(l,!1)}},300):f(l,!1)}function k(x){r(`${x.corpName} `),f(l,!1),f(d,-1),s(p)&&s(p).focus()}function z(){setTimeout(()=>{f(l,!1)},200)}var g=ov(),A=c(g),$=c(A);xo($,x=>f(p,x),()=>s(p));var L=h($,2);{var M=x=>{var F=tv(),Y=c(F);Ff(Y,{size:14}),W("click",F,function(...ue){var pe;(pe=t.onStop)==null||pe.apply(this,ue)}),m(x,F)},O=x=>{var F=rv(),Y=c(F);{let ue=ne(()=>a()?18:16);Mf(Y,{get size(){return s(ue)},strokeWidth:2.5})}j((ue,pe)=>{Ze(F,1,ue),F.disabled=pe},[()=>Xe(Qe("send-btn",r().trim()&&"active")),()=>!r().trim()]),W("click",F,()=>{var ue;f(l,!1),(ue=t.onSend)==null||ue.call(t)}),m(x,F)};T(L,x=>{n()&&t.onStop?x(M):x(O,-1)})}var Z=h(A,2);{var q=x=>{var F=sv();rt(F,21,()=>s(o),tt,(Y,ue,pe)=>{var Ye=av(),P=c(Ye);yo(P,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var R=h(P,2),Q=c(R),ae=c(Q),de=h(Q,2),H=c(de),y=h(R,2);{var ke=fe=>{var ut=nv(),Ve=c(ut);j(()=>D(Ve,s(ue).sector)),m(fe,ut)};T(y,fe=>{s(ue).sector&&fe(ke)})}j(fe=>{Ze(Ye,1,fe),D(ae,s(ue).corpName),D(H,`${s(ue).stockCode??""} · ${(s(ue).market||"")??""}`)},[()=>Xe(Qe("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",pe===s(d)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),W("mousedown",Ye,()=>k(s(ue))),is("mouseenter",Ye,()=>{f(d,pe,!0)}),m(Y,Ye)}),m(x,F)};T(Z,x=>{s(l)&&s(o).length>0&&x(q)})}j(x=>{Ze(A,1,x),Ba($,"placeholder",i())},[()=>Xe(Qe("input-box",a()&&"large"))]),W("keydown",$,v),W("input",$,E),is("blur",$,z),na($,r),m(e,g),Nr()}Sn(["keydown","input","click","mousedown"]);var iv=w('<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[720px] flex flex-col items-center"><div class="relative mb-6"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-8">종목명과 질문을 입력하거나, 자유롭게 대화하세요</p> <div class="w-full"><!></div> <div class="mt-5 w-full"><button class="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/30 text-[13px] text-dl-text-dim hover:text-dl-text-muted hover:border-dl-primary/30 hover:bg-dl-bg-card/50 transition-all duration-200"><!> 데이터 탐색</button></div></div></div>');function lv(e,t){$r(t,!0);let r=lt(t,"inputText",15,"");var n=iv(),a=c(n),i=h(c(a),6),o=c(i);Dl(o,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get inputText(){return r()},set inputText(p){r(p)}});var l=h(i,2),d=c(l),u=c(d);mn(u,{size:14}),W("click",d,()=>{var p;return(p=t.onOpenExplorer)==null?void 0:p.call(t)}),m(e,n),Nr()}Sn(["click"]);var dv=w("<span><!></span>");function wi(e,t){$r(t,!0);let r=lt(t,"variant",3,"default");const n={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var a=dv(),i=c(a);Xs(i,()=>t.children),j(o=>Ze(a,1,o),[()=>Xe(Qe("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",n[r()],t.class))]),m(e,a),Nr()}var cv=w('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),uv=w('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),fv=w('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),vv=w('<div class="flex flex-wrap items-center gap-1.5 mb-2"><!> <!> <!></div>'),pv=w('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),mv=w('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),hv=w('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),gv=w('<button class="mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),xv=w('<span class="flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-dl-accent/30 bg-dl-accent/[0.06] text-[11px] text-dl-accent"><!> </span>'),bv=w('<div class="mb-3"><div class="flex flex-wrap items-center gap-1.5"></div></div>'),_v=w('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),yv=w('<!> <span class="text-dl-text-dim"> </span>',1),wv=w('<div class="flex items-center gap-2 text-[11px]"><!></div>'),kv=w('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),Sv=w('<div class="flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),zv=w('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),Mv=w('<span class="text-dl-accent/60"> </span>'),Av=w('<span class="text-dl-success/60"> </span>'),Cv=w('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),Ev=w('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),Tv=w('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),$v=w('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),Nv=w('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),Pv=w("<!>  <div><!></div> <!>",1),Iv=w('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),Lv=w('<span class="text-[10px] text-dl-text-dim"> </span>'),Ov=w('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),Rv=w("<button> </button>"),jv=w('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),Dv=w("<button>시스템 프롬프트</button>"),Fv=w("<button>LLM 입력</button>"),Bv=w('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),Vv=w('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),Gv=w('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),Hv=w('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Uv=w("<!> <!>",1);function Kv(e,t){$r(t,!0);let r=V(null),n=V("context"),a=V("raw"),i=ne(()=>{var P,R,Q,ae,de,H;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((P=t.message.toolEvents)==null?void 0:P.length)>0){const y=[...t.message.toolEvents].reverse().find(fe=>fe.type==="call"),ke=((R=y==null?void 0:y.arguments)==null?void 0:R.module)||((Q=y==null?void 0:y.arguments)==null?void 0:Q.keyword)||"";return`도구 실행 중 — ${(y==null?void 0:y.name)||""}${ke?` (${ke})`:""}`}if(((ae=t.message.contexts)==null?void 0:ae.length)>0){const y=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(y==null?void 0:y.label)||(y==null?void 0:y.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(de=t.message.meta)!=null&&de.company?`${t.message.meta.company} 데이터 검색 중`:(H=t.message.meta)!=null&&H.includedModules?"분석 모듈 선택 완료":"생각 중"}),o=ne(()=>{var P;return t.message.company||((P=t.message.meta)==null?void 0:P.company)||null}),l=ne(()=>{var P,R;return t.message.systemPrompt||((P=t.message.contexts)==null?void 0:P.length)>0||((R=t.message.meta)==null?void 0:R.includedModules)}),d=ne(()=>{var R;const P=(R=t.message.meta)==null?void 0:R.dataYearRange;return P?typeof P=="string"?P:P.min_year&&P.max_year?`${P.min_year}~${P.max_year}년`:null:null});function u(P){if(!P)return 0;const R=(P.match(/[\uac00-\ud7af]/g)||[]).length,Q=P.length-R;return Math.round(R*1.5+Q/3.5)}function p(P){return P>=1e3?(P/1e3).toFixed(1)+"k":String(P)}let v=ne(()=>{var R;let P=0;if(t.message.systemPrompt&&(P+=u(t.message.systemPrompt)),t.message.userContent)P+=u(t.message.userContent);else if(((R=t.message.contexts)==null?void 0:R.length)>0)for(const Q of t.message.contexts)P+=u(Q.text);return P}),_=ne(()=>u(t.message.text));function E(P){const R=P.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(R)||R==="-"||R==="0"}function k(P){if(!P)return"";let R=[],Q=[],ae=P.replace(/```(\w*)\n([\s\S]*?)```/g,(H,y,ke)=>{const fe=R.length;return R.push(ke.trimEnd()),`
%%CODE_${fe}%%
`});ae=ae.replace(/((?:^\|.+\|$\n?)+)/gm,H=>{const y=H.trim().split(`
`).filter(ee=>ee.trim());let ke=null,fe=-1,ut=[];for(let ee=0;ee<y.length;ee++)if(y[ee].slice(1,-1).split("|").map(ve=>ve.trim()).every(ve=>/^[\-:]+$/.test(ve))){fe=ee;break}fe>0?(ke=y[fe-1],ut=y.slice(fe+1)):(fe===0||(ke=y[0]),ut=y.slice(1));let Ve="<table>";if(ke){const ee=ke.slice(1,-1).split("|").map(se=>se.trim());Ve+="<thead><tr>"+ee.map(se=>`<th>${se.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(ut.length>0){Ve+="<tbody>";for(const ee of ut){const se=ee.slice(1,-1).split("|").map(ve=>ve.trim());Ve+="<tr>"+se.map(ve=>{let Se=ve.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${E(ve)?' class="num"':""}>${Se}</td>`}).join("")+"</tr>"}Ve+="</tbody>"}Ve+="</table>";let Ge=Q.length;return Q.push(Ve),`
%%TABLE_${Ge}%%
`});let de=ae.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");de=de.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,H=>"<ul>"+H.replace(/<br>/g,"")+"</ul>");for(let H=0;H<Q.length;H++)de=de.replace(`%%TABLE_${H}%%`,Q[H]);for(let H=0;H<R.length;H++){const y=R[H].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");de=de.replace(`%%CODE_${H}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${H}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${y}</code></pre></div>`)}return de=de.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(H,y)=>y.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+de+"</p>"}let z=V(void 0);const g='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',A='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function $(P){var de;const R=P.target.closest(".code-copy-btn");if(!R)return;const Q=R.closest(".code-block-wrap"),ae=((de=Q==null?void 0:Q.querySelector("code"))==null?void 0:de.textContent)||"";navigator.clipboard.writeText(ae).then(()=>{R.innerHTML=A,setTimeout(()=>{R.innerHTML=g},2e3)})}function L(P){f(r,P,!0),f(n,"context"),f(a,"rendered")}function M(){f(r,0),f(n,"system"),f(a,"raw")}function O(){f(r,0),f(n,"snapshot")}function Z(){f(r,null)}let q=ne(()=>{var R,Q,ae;if(!t.message.loading)return[];const P=[];return(R=t.message.meta)!=null&&R.company&&P.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&P.push({label:"핵심 수치 확인",done:!0}),(Q=t.message.meta)!=null&&Q.includedModules&&P.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((ae=t.message.contexts)==null?void 0:ae.length)>0&&P.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&P.push({label:"프롬프트 조립",done:!0}),t.message.text?P.push({label:"응답 작성 중",done:!1}):P.push({label:s(i)||"준비 중",done:!1}),P});var x=Uv(),F=G(x);{var Y=P=>{var R=cv(),Q=h(c(R),2),ae=c(Q),de=c(ae);j(()=>D(de,t.message.text)),m(P,R)},ue=P=>{var R=Iv(),Q=h(c(R),2),ae=c(Q);{var de=ee=>{var se=vv(),ve=c(se);{var Se=X=>{wi(X,{variant:"muted",children:(ie,ye)=>{var ze=Ra();j(()=>D(ze,s(o))),m(ie,ze)},$$slots:{default:!0}})};T(ve,X=>{s(o)&&X(Se)})}var C=h(ve,2);{var N=X=>{wi(X,{variant:"accent",children:(ie,ye)=>{var ze=Ra();j(()=>D(ze,s(d))),m(ie,ze)},$$slots:{default:!0}})};T(C,X=>{s(d)&&X(N)})}var J=h(C,2);{var He=X=>{var ie=ce(),ye=G(ie);rt(ye,17,()=>t.message.contexts,tt,(ze,dt,bt)=>{var Oe=uv(),Ue=c(Oe);mn(Ue,{size:10,class:"flex-shrink-0"});var Te=h(Ue);j(()=>D(Te,` ${(s(dt).label||s(dt).module)??""}`)),W("click",Oe,()=>L(bt)),m(ze,Oe)}),m(X,ie)},re=X=>{var ie=fv(),ye=c(ie);mn(ye,{size:10,class:"flex-shrink-0"});var ze=h(ye);j(()=>D(ze,` 모듈 ${t.message.meta.includedModules.length??""}개`)),m(X,ie)};T(J,X=>{var ie,ye,ze;((ie=t.message.contexts)==null?void 0:ie.length)>0?X(He):((ze=(ye=t.message.meta)==null?void 0:ye.includedModules)==null?void 0:ze.length)>0&&X(re,1)})}m(ee,se)};T(ae,ee=>{var se,ve;(s(o)||s(d)||((se=t.message.contexts)==null?void 0:se.length)>0||(ve=t.message.meta)!=null&&ve.includedModules)&&ee(de)})}var H=h(ae,2);{var y=ee=>{var se=gv(),ve=c(se);rt(ve,21,()=>t.message.snapshot.items,tt,(N,J)=>{const He=ne(()=>s(J).status==="good"?"text-dl-success":s(J).status==="danger"?"text-dl-primary-light":s(J).status==="caution"?"text-amber-400":"text-dl-text");var re=pv(),X=c(re),ie=c(X),ye=h(X,2),ze=c(ye);j(dt=>{D(ie,s(J).label),Ze(ye,1,dt),D(ze,s(J).value)},[()=>Xe(Qe("text-[14px] font-semibold leading-snug mt-0.5",s(He)))]),m(N,re)});var Se=h(ve,2);{var C=N=>{var J=hv();rt(J,21,()=>t.message.snapshot.warnings,tt,(He,re)=>{var X=mv(),ie=c(X);Gf(ie,{size:10});var ye=h(ie);j(()=>D(ye,` ${s(re)??""}`)),m(He,X)}),m(N,J)};T(Se,N=>{var J;((J=t.message.snapshot.warnings)==null?void 0:J.length)>0&&N(C)})}W("click",se,O),m(ee,se)};T(H,ee=>{var se,ve;((ve=(se=t.message.snapshot)==null?void 0:se.items)==null?void 0:ve.length)>0&&ee(y)})}var ke=h(H,2);{var fe=ee=>{var se=bv(),ve=c(se);rt(ve,21,()=>t.message.toolEvents,tt,(Se,C)=>{var N=ce(),J=G(N);{var He=re=>{const X=ne(()=>{var dt,bt,Oe,Ue;return((dt=s(C).arguments)==null?void 0:dt.module)||((bt=s(C).arguments)==null?void 0:bt.keyword)||((Oe=s(C).arguments)==null?void 0:Oe.engine)||((Ue=s(C).arguments)==null?void 0:Ue.name)||""});var ie=xv(),ye=c(ie);Hf(ye,{size:11});var ze=h(ye);j(()=>D(ze,` ${s(C).name??""}${s(X)?`: ${s(X)}`:""}`)),m(re,ie)};T(J,re=>{s(C).type==="call"&&re(He)})}m(Se,N)}),m(ee,se)};T(ke,ee=>{var se;((se=t.message.toolEvents)==null?void 0:se.length)>0&&ee(fe)})}var ut=h(ke,2);{var Ve=ee=>{var se=kv(),ve=c(se);rt(ve,21,()=>s(q),tt,(Se,C)=>{var N=wv(),J=c(N);{var He=X=>{var ie=_v(),ye=h(G(ie),2),ze=c(ye);j(()=>D(ze,s(C).label)),m(X,ie)},re=X=>{var ie=yv(),ye=G(ie);Wt(ye,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var ze=h(ye,2),dt=c(ze);j(()=>D(dt,s(C).label)),m(X,ie)};T(J,X=>{s(C).done?X(He):X(re,-1)})}m(Se,N)}),m(ee,se)},Ge=ee=>{var se=Pv(),ve=G(se);{var Se=re=>{var X=Sv(),ie=c(X);Wt(ie,{size:12,class:"animate-spin flex-shrink-0"});var ye=h(ie,2),ze=c(ye);j(()=>D(ze,s(i))),m(re,X)};T(ve,re=>{t.message.loading&&re(Se)})}var C=h(ve,2),N=c(C);Xo(N,()=>k(t.message.text)),xo(C,re=>f(z,re),()=>s(z));var J=h(C,2);{var He=re=>{var X=Nv(),ie=c(X);{var ye=Me=>{var $e=zv(),nt=c($e);Ef(nt,{size:10});var B=h(nt);j(()=>D(B,` ${t.message.duration??""}초`)),m(Me,$e)};T(ie,Me=>{t.message.duration&&Me(ye)})}var ze=h(ie,2);{var dt=Me=>{var $e=Cv(),nt=c($e);{var B=De=>{var Je=Mv(),xt=c(Je);j(ft=>D(xt,`↑${ft??""}`),[()=>p(s(v))]),m(De,Je)};T(nt,De=>{s(v)>0&&De(B)})}var ge=h(nt,2);{var Ke=De=>{var Je=Av(),xt=c(Je);j(ft=>D(xt,`↓${ft??""}`),[()=>p(s(_))]),m(De,Je)};T(ge,De=>{s(_)>0&&De(Ke)})}m(Me,$e)};T(ze,Me=>{(s(v)>0||s(_)>0)&&Me(dt)})}var bt=h(ze,2);{var Oe=Me=>{var $e=Ev(),nt=c($e);jf(nt,{size:10}),W("click",$e,()=>{var B;return(B=t.onRegenerate)==null?void 0:B.call(t)}),m(Me,$e)};T(bt,Me=>{t.onRegenerate&&Me(Oe)})}var Ue=h(bt,2);{var Te=Me=>{var $e=Tv(),nt=c($e);mi(nt,{size:10}),W("click",$e,M),m(Me,$e)};T(Ue,Me=>{t.message.systemPrompt&&Me(Te)})}var ct=h(Ue,2);{var Yt=Me=>{var $e=$v(),nt=c($e);ja(nt,{size:10});var B=h(nt);j((ge,Ke)=>D(B,` LLM 입력 (${ge??""}자 · ~${Ke??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>p(u(t.message.userContent))]),W("click",$e,()=>{f(r,0),f(n,"userContent"),f(a,"raw")}),m(Me,$e)};T(ct,Me=>{t.message.userContent&&Me(Yt)})}m(re,X)};T(J,re=>{!t.message.loading&&(t.message.duration||s(l)||t.onRegenerate)&&re(He)})}j(re=>Ze(C,1,re),[()=>Xe(Qe("prose-dartlab text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),W("click",C,$),m(ee,se)};T(ut,ee=>{t.message.loading&&!t.message.text?ee(Ve):ee(Ge,-1)})}m(P,R)};T(F,P=>{t.message.role==="user"?P(Y):P(ue,-1)})}var pe=h(F,2);{var Ye=P=>{const R=ne(()=>s(n)==="system"),Q=ne(()=>s(n)==="userContent"),ae=ne(()=>s(n)==="context"),de=ne(()=>s(n)==="snapshot"),H=ne(()=>{var B;return s(ae)?(B=t.message.contexts)==null?void 0:B[s(r)]:null}),y=ne(()=>{var B,ge;return s(de)?"핵심 수치 (원본 데이터)":s(R)?"시스템 프롬프트":s(Q)?"LLM에 전달된 입력":((B=s(H))==null?void 0:B.label)||((ge=s(H))==null?void 0:ge.module)||""}),ke=ne(()=>{var B;return s(de)?JSON.stringify(t.message.snapshot,null,2):s(R)?t.message.systemPrompt:s(Q)?t.message.userContent:(B=s(H))==null?void 0:B.text});var fe=Hv(),ut=c(fe),Ve=c(ut),Ge=c(Ve),ee=c(Ge),se=c(ee);{var ve=B=>{mn(B,{size:15,class:"text-dl-success flex-shrink-0"})},Se=B=>{mi(B,{size:15,class:"text-dl-primary-light flex-shrink-0"})},C=B=>{ja(B,{size:15,class:"text-dl-accent flex-shrink-0"})},N=B=>{mn(B,{size:15,class:"flex-shrink-0"})};T(se,B=>{s(de)?B(ve):s(R)?B(Se,1):s(Q)?B(C,2):B(N,-1)})}var J=h(se,2),He=c(J),re=h(J,2);{var X=B=>{var ge=Lv(),Ke=c(ge);j(De=>D(Ke,`(${De??""}자)`),[()=>{var De,Je;return(Je=(De=s(ke))==null?void 0:De.length)==null?void 0:Je.toLocaleString()}]),m(B,ge)};T(re,B=>{s(R)&&B(X)})}var ie=h(ee,2),ye=c(ie);{var ze=B=>{var ge=Ov(),Ke=c(ge),De=c(Ke);ja(De,{size:11});var Je=h(Ke,2),xt=c(Je);Tf(xt,{size:11}),j((ft,vt)=>{Ze(Ke,1,ft),Ze(Je,1,vt)},[()=>Xe(Qe("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",s(a)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>Xe(Qe("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",s(a)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),W("click",Ke,()=>f(a,"rendered")),W("click",Je,()=>f(a,"raw")),m(B,ge)};T(ye,B=>{s(ae)&&B(ze)})}var dt=h(ye,2),bt=c(dt);wo(bt,{size:18});var Oe=h(Ge,2);{var Ue=B=>{var ge=jv(),Ke=c(ge);rt(Ke,21,()=>t.message.contexts,tt,(De,Je,xt)=>{var ft=Rv(),vt=c(ft);j(Tt=>{Ze(ft,1,Tt),D(vt,t.message.contexts[xt].label||t.message.contexts[xt].module)},[()=>Xe(Qe("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",xt===s(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),W("click",ft,()=>{f(r,xt,!0)}),m(De,ft)}),m(B,ge)};T(Oe,B=>{var ge;s(ae)&&((ge=t.message.contexts)==null?void 0:ge.length)>1&&B(Ue)})}var Te=h(Oe,2);{var ct=B=>{var ge=Bv(),Ke=c(ge),De=c(Ke);{var Je=vt=>{var Tt=Dv();j(rr=>Ze(Tt,1,rr),[()=>Xe(Qe("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",s(R)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),W("click",Tt,()=>{f(n,"system")}),m(vt,Tt)};T(De,vt=>{t.message.systemPrompt&&vt(Je)})}var xt=h(De,2);{var ft=vt=>{var Tt=Fv();j(rr=>Ze(Tt,1,rr),[()=>Xe(Qe("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",s(Q)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),W("click",Tt,()=>{f(n,"userContent")}),m(vt,Tt)};T(xt,vt=>{t.message.userContent&&vt(ft)})}m(B,ge)};T(Te,B=>{!s(ae)&&!s(de)&&B(ct)})}var Yt=h(Ve,2),Me=c(Yt);{var $e=B=>{var ge=Vv(),Ke=c(ge);Xo(Ke,()=>{var De;return k((De=s(H))==null?void 0:De.text)}),m(B,ge)},nt=B=>{var ge=Gv(),Ke=c(ge);j(()=>D(Ke,s(ke))),m(B,ge)};T(Me,B=>{s(ae)&&s(a)==="rendered"?B($e):B(nt,-1)})}j(()=>D(He,s(y))),W("click",fe,B=>{B.target===B.currentTarget&&Z()}),W("keydown",fe,B=>{B.key==="Escape"&&Z()}),W("click",dt,Z),m(P,fe)};T(pe,P=>{s(r)!==null&&P(Ye)})}m(e,x),Nr()}Sn(["click","keydown"]);var Wv=w('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),qv=w('<div class="flex justify-end gap-2 mb-1.5"><button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 데이터</button> <!></div>'),Yv=w('<div class="flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="max-w-[720px] mx-auto px-5 pt-14 pb-8 space-y-8"></div></div> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function Jv(e,t){$r(t,!0);function r($){if(a())return!1;for(let L=n().length-1;L>=0;L--)if(n()[L].role==="assistant"&&!n()[L].error&&n()[L].text)return L===$;return!1}let n=lt(t,"messages",19,()=>[]),a=lt(t,"isLoading",3,!1),i=lt(t,"inputText",15,""),o=lt(t,"scrollTrigger",3,0),l,d=!1;function u(){if(!l)return;const{scrollTop:$,scrollHeight:L,clientHeight:M}=l;d=L-$-M>80}Da(()=>{o(),!(!l||d)&&requestAnimationFrame(()=>{l&&(l.scrollTop=l.scrollHeight)})});var p=Yv(),v=c(p),_=c(v);rt(_,21,n,tt,($,L,M)=>{{let O=ne(()=>r(M)?t.onRegenerate:void 0);Kv($,{get message(){return s(L)},get onRegenerate(){return s(O)}})}}),xo(v,$=>l=$,()=>l);var E=h(v,2),k=c(E),z=c(k);{var g=$=>{var L=qv(),M=c(L),O=c(M);mn(O,{size:10});var Z=h(M,2);{var q=x=>{var F=Wv(),Y=c(F);aa(Y,{size:10}),W("click",F,function(...ue){var pe;(pe=t.onExport)==null||pe.apply(this,ue)}),m(x,F)};T(Z,x=>{n().length>1&&t.onExport&&x(q)})}W("click",M,()=>{var x;return(x=t.onOpenExplorer)==null?void 0:x.call(t)}),m($,L)};T(z,$=>{a()||$(g)})}var A=h(z,2);Dl(A,{get isLoading(){return a()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get inputText(){return i()},set inputText($){i($)}}),is("scroll",v,u),m(e,p),Nr()}Sn(["click"]);var Xv=w('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="w-8 h-8 rounded-lg bg-dl-primary/15 flex items-center justify-center flex-shrink-0"><span class="text-[13px] font-bold text-dl-primary-light"> </span></div> <div><div class="text-[14px] font-semibold text-dl-text"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div>',1),Zv=w('<!> <div class="text-[15px] font-semibold text-dl-text">데이터 탐색</div>',1),Qv=w('<button class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-dl-success/15 text-dl-success text-[11px] font-medium hover:bg-dl-success/25 transition-colors disabled:opacity-40"><!> Excel</button>'),ep=w('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),tp=w('<button class="flex items-center gap-3 w-full px-4 py-3 rounded-xl border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all"><div class="w-8 h-8 rounded-lg bg-dl-primary/10 flex items-center justify-center flex-shrink-0"><span class="text-[12px] font-bold text-dl-primary-light"> </span></div> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium text-dl-text"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!> <!></button>'),rp=w('<div class="space-y-1"></div>'),np=w('<div class="text-center py-16 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),ap=w('<div class="text-center py-24"><!> <div class="text-[14px] text-dl-text-muted mb-1">종목을 검색하여 데이터를 탐색하세요</div> <div class="text-[12px] text-dl-text-dim/70">재무제표, 정기보고서, 공시 데이터를 직접 확인하고 Excel로 내보낼 수 있습니다</div></div>'),sp=w('<div class="flex-1 overflow-y-auto px-5 py-8"><div class="max-w-lg mx-auto"><div class="relative mb-4"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="w-full pl-9 pr-4 py-3 bg-dl-bg-card border border-dl-border rounded-xl text-[13px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/40 transition-colors"/> <!></div> <!></div></div>'),op=w('<div class="flex items-center justify-center py-12 gap-2 text-[12px] text-dl-text-dim"><!> 탐색 중...</div>'),ip=w('<button><!> <span class="flex-1 min-w-0 truncate"> </span></button>'),lp=w('<div class="ml-2 border-l border-dl-border/30 pl-1"></div>'),dp=w('<div class="mx-2 mb-0.5"><button class="flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-left hover:bg-white/[0.03] transition-colors"><!> <span class="text-[11px] font-medium text-dl-text-muted flex-1"> </span> <span class="text-[9px] text-dl-text-dim"> </span></button> <!></div>'),cp=w('<div class="flex items-center justify-center h-full text-center"><div><!> <div class="text-[13px] text-dl-text-dim">좌측에서 모듈을 선택하세요</div></div></div>'),up=w('<div class="flex items-center justify-center h-full gap-2 text-[13px] text-dl-text-dim"><!> </div>'),fp=w('<span class="text-[10px] text-dl-text-dim"> </span>'),vp=w('<span class="px-1.5 py-0.5 rounded bg-dl-border/50 text-[9px] text-dl-text-dim"> </span>'),pp=w("<button><!> </button>"),mp=w('<button class="flex items-center gap-1 px-2 py-1 rounded-lg bg-dl-success/10 text-dl-success text-[10px] hover:bg-dl-success/20 transition-colors"><!> Excel</button>'),hp=w('<th class="px-3 py-2 text-right text-dl-text-muted font-medium bg-dl-bg-darker border-b border-dl-border/30 whitespace-nowrap text-[10px] min-w-[100px]"> </th>'),gp=w("<td> </td>"),xp=w('<tr class="hover:bg-white/[0.02]"><td> </td><!></tr>'),bp=w('<div class="px-4 py-1.5 text-[10px] text-dl-warning border-t border-dl-border/20 flex-shrink-0"> </div>'),_p=w('<div class="flex-1 overflow-auto min-h-0"><table class="text-[11px] border-collapse"><thead class="sticky top-0 z-[5]"><tr><th class="sticky left-0 z-[10] px-3 py-2 text-left text-dl-text-muted font-medium bg-dl-bg-darker border-b border-r border-dl-border/30 whitespace-nowrap text-[10px] min-w-[180px]">계정명</th><!></tr></thead><tbody></tbody></table></div> <!>',1),yp=w('<th class="px-3 py-2 text-left text-dl-text-muted font-medium bg-dl-bg-darker border-b border-dl-border/30 whitespace-nowrap text-[10px]"> </th>'),wp=w("<td> </td>"),kp=w('<tr class="hover:bg-white/[0.02]"></tr>'),Sp=w('<div class="px-4 py-1.5 text-[10px] text-dl-warning border-t border-dl-border/20 flex-shrink-0"> </div>'),zp=w('<div class="flex-1 overflow-auto min-h-0"><table class="w-full text-[11px] border-collapse"><thead class="sticky top-0 z-[5]"><tr></tr></thead><tbody></tbody></table></div> <!>',1),Mp=w('<div class="flex gap-3 px-3 py-2 rounded-lg bg-dl-bg-card/50"><span class="text-[11px] text-dl-text-muted font-medium min-w-[160px] flex-shrink-0"> </span> <span class="text-[11px] text-dl-text-dim break-all"> </span></div>'),Ap=w('<div class="flex-1 overflow-auto min-h-0 p-4 space-y-1.5"></div>'),Cp=w('<div class="mt-2 text-[10px] text-dl-warning">내용이 잘려서 표시됩니다</div>'),Ep=w('<div class="flex-1 overflow-auto min-h-0 p-4"><pre class="text-[11px] text-dl-text-muted whitespace-pre-wrap leading-relaxed"> </pre> <!></div>'),Tp=w('<div class="flex items-center justify-center h-full text-[13px] text-dl-primary-light"> </div>'),$p=w('<div class="flex-1 overflow-auto min-h-0 p-4"><pre class="text-[11px] text-dl-text-muted whitespace-pre-wrap"> </pre></div>'),Np=w('<div class="flex items-center justify-between px-4 py-2 flex-shrink-0 border-b border-dl-border/30 bg-dl-bg-card/50"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!> <!></div> <div class="flex items-center gap-1.5"><!> <!></div></div> <!>',1),Pp=w('<div class="w-[240px] flex-shrink-0 border-r border-dl-border/50 overflow-y-auto bg-dl-bg-card/30"><!></div> <div class="flex-1 flex flex-col min-w-0 min-h-0"><!></div>',1),Ip=w('<div class="fixed inset-0 z-[200] flex flex-col bg-dl-bg-dark animate-fadeIn"><div class="flex items-center justify-between px-5 py-3 flex-shrink-0 border-b border-dl-border/50 bg-dl-bg-card/80 backdrop-blur-sm"><div class="flex items-center gap-3"><!></div> <div class="flex items-center gap-2"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 flex min-h-0"><!></div></div>');function Lp(e,t){$r(t,!0);let r=V(""),n=V(Ct([])),a=V(!1),i=null,o=V(null),l=V(null),d=V(!1),u=V(Ct(new Set)),p=V(null),v=V(null),_=V(!1),E=V(!1),k=V(!0);function z(){const C=s(r).trim();if(i&&clearTimeout(i),C.length<2){f(n,[],!0);return}f(a,!0),i=setTimeout(async()=>{var N;try{const J=await Sl(C);f(n,((N=J.results)==null?void 0:N.slice(0,8))||[],!0)}catch{f(n,[],!0)}f(a,!1)},300)}async function g(C){f(o,C,!0),f(r,""),f(n,[],!0),f(d,!0),f(p,null),f(v,null);try{f(l,await wu(C.stockCode),!0);const N=Object.keys(s(l).categories||{});f(u,new Set(N.slice(0,2)),!0)}catch{f(l,null)}f(d,!1)}function A(){f(o,null),f(l,null),f(p,null),f(v,null)}async function $(C){if(C.available){f(p,C,!0),f(_,!0),f(v,null);try{f(v,await ku(s(o).stockCode,C.name,200),!0)}catch(N){f(v,{type:"error",error:N.message},!0)}f(_,!1)}}function L(C){const N=new Set(s(u));N.has(C)?N.delete(C):N.add(C),f(u,N,!0)}async function M(){if(s(o)){f(E,!0);try{await ai(s(o).stockCode)}catch{}f(E,!1)}}const O={finance:"재무제표",report:"정기보고서",disclosure:"공시 서술",notes:"K-IFRS 주석",analysis:"분석",raw:"원본 데이터"};function Z(C){return O[C]||C}function q(C){return`${C.filter(J=>J.available).length}/${C.length}`}function x(C){var N,J;return!((J=(N=s(v))==null?void 0:N.meta)!=null&&J.labels)||!s(k)?C:s(v).meta.labels[C]||C}function F(C){var N,J;return(J=(N=s(v))==null?void 0:N.meta)!=null&&J.levels&&s(v).meta.levels[C]||1}function Y(C){if(C==null)return"-";if(typeof C!="number")return String(C);if(C===0)return"0";const N=Math.abs(C),J=C<0?"-":"";return N>=1e12?`${J}${(N/1e12).toLocaleString("ko-KR",{maximumFractionDigits:1})}조`:N>=1e8?`${J}${Math.round(N/1e8).toLocaleString("ko-KR")}억`:N>=1e4?`${J}${Math.round(N/1e4).toLocaleString("ko-KR")}만`:C.toLocaleString("ko-KR")}function ue(C,N){if(C==null)return"-";if(typeof C=="number"){if(N==="원"||N==="백만원")return N==="백만원"&&(C=C*1e6),Y(C);if(Number.isInteger(C)&&Math.abs(C)>=1e3)return C.toLocaleString("ko-KR");if(!Number.isInteger(C))return C.toLocaleString("ko-KR",{maximumFractionDigits:2})}return String(C)}function pe(){var C,N,J;return(N=(C=s(v))==null?void 0:C.meta)!=null&&N.unit?s(v).meta.unit:(J=s(v))!=null&&J.unit?s(v).unit:""}function Ye(){var C,N;return!!((N=(C=s(v))==null?void 0:C.meta)!=null&&N.labels)}function P(){var C;return(C=s(v))!=null&&C.columns?s(v).columns.filter(N=>N!=="계정명"):[]}var R=Ip(),Q=c(R),ae=c(Q),de=c(ae);{var H=C=>{var N=Xv(),J=G(N),He=c(J);zf(He,{size:16});var re=h(J,2),X=c(re),ie=c(X),ye=h(re,2),ze=c(ye),dt=c(ze),bt=h(ze,2),Oe=c(bt);j(()=>{D(ie,s(o).corpName[0]),D(dt,s(o).corpName),D(Oe,`${s(o).stockCode??""}${s(l)?` · ${s(l).availableSources}개 데이터`:""}`)}),W("click",J,A),m(C,N)},y=C=>{var N=Zv(),J=G(N);mn(J,{size:18,class:"text-dl-primary-light"}),m(C,N)};T(de,C=>{s(o)?C(H):C(y,-1)})}var ke=h(ae,2),fe=c(ke);{var ut=C=>{var N=Qv(),J=c(N);{var He=X=>{Wt(X,{size:12,class:"animate-spin"})},re=X=>{aa(X,{size:12})};T(J,X=>{s(E)?X(He):X(re,-1)})}j(()=>N.disabled=s(E)),W("click",N,M),m(C,N)};T(fe,C=>{s(o)&&C(ut)})}var Ve=h(fe,2),Ge=c(Ve);wo(Ge,{size:16});var ee=h(Q,2),se=c(ee);{var ve=C=>{var N=sp(),J=c(N),He=c(J),re=c(He);yo(re,{size:14,class:"absolute left-3 top-1/2 -translate-y-1/2 text-dl-text-dim pointer-events-none"});var X=h(re,2),ie=h(X,2);{var ye=Te=>{Wt(Te,{size:14,class:"absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-dl-text-dim"})};T(ie,Te=>{s(a)&&Te(ye)})}var ze=h(He,2);{var dt=Te=>{var ct=rp();rt(ct,21,()=>s(n),tt,(Yt,Me)=>{var $e=tp(),nt=c($e),B=c(nt),ge=c(B),Ke=h(nt,2),De=c(Ke),Je=c(De),xt=h(De,2),ft=c(xt),vt=h(Ke,2);{var Tt=Wr=>{var tn=ep(),Mn=c(tn);j(()=>D(Mn,s(Me).sector)),m(Wr,tn)};T(vt,Wr=>{s(Me).sector&&Wr(Tt)})}var rr=h(vt,2);hi(rr,{size:14,class:"text-dl-text-dim flex-shrink-0"}),j(()=>{D(ge,s(Me).corpName[0]),D(Je,s(Me).corpName),D(ft,`${s(Me).stockCode??""} · ${(s(Me).market||"")??""}`)}),W("click",$e,()=>g(s(Me))),m(Yt,$e)}),m(Te,ct)},bt=Te=>{var ct=np();m(Te,ct)},Oe=ne(()=>s(r).trim().length>=2&&!s(a)),Ue=Te=>{var ct=ap(),Yt=c(ct);mn(Yt,{size:40,class:"mx-auto mb-4 text-dl-text-dim/30"}),m(Te,ct)};T(ze,Te=>{s(n).length>0?Te(dt):s(Oe)?Te(bt,1):Te(Ue,-1)})}W("input",X,z),na(X,()=>s(r),Te=>f(r,Te)),m(C,N)},Se=C=>{var N=Pp(),J=G(N),He=c(J);{var re=Oe=>{var Ue=op(),Te=c(Ue);Wt(Te,{size:14,class:"animate-spin"}),m(Oe,Ue)},X=Oe=>{var Ue=ce(),Te=G(Ue);rt(Te,17,()=>Object.entries(s(l).categories),tt,(ct,Yt)=>{var Me=ne(()=>os(s(Yt),2));let $e=()=>s(Me)[0],nt=()=>s(Me)[1];var B=dp(),ge=c(B),Ke=c(ge);{var De=Vt=>{Cf(Vt,{size:12,class:"text-dl-text-dim flex-shrink-0"})},Je=ne(()=>s(u).has($e())),xt=Vt=>{hi(Vt,{size:12,class:"text-dl-text-dim flex-shrink-0"})};T(Ke,Vt=>{s(Je)?Vt(De):Vt(xt,-1)})}var ft=h(Ke,2),vt=c(ft),Tt=h(ft,2),rr=c(Tt),Wr=h(ge,2);{var tn=Vt=>{var qr=lp();rt(qr,21,nt,tt,(ya,Ht)=>{var le=ip(),xe=c(le);{var We=at=>{yi(at,{size:10,class:"flex-shrink-0"})},_t=at=>{ja(at,{size:10,class:"flex-shrink-0"})};T(xe,at=>{s(Ht).dataType==="timeseries"||s(Ht).dataType==="table"||s(Ht).dataType==="dataframe"?at(We):at(_t,-1)})}var yt=h(xe,2),_r=c(yt);j(at=>{Ze(le,1,at),le.disabled=!s(Ht).available,D(_r,s(Ht).label)},[()=>{var at;return Xe(Qe("flex items-center gap-1.5 w-full px-2 py-1 rounded-lg text-left text-[11px] transition-colors",!s(Ht).available&&"opacity-30 cursor-default",s(Ht).available&&((at=s(p))==null?void 0:at.name)===s(Ht).name?"bg-dl-primary/10 text-dl-primary-light":s(Ht).available?"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text":""))}]),W("click",le,()=>$(s(Ht))),m(ya,le)}),m(Vt,qr)},Mn=ne(()=>s(u).has($e()));T(Wr,Vt=>{s(Mn)&&Vt(tn)})}j((Vt,qr)=>{D(vt,Vt),D(rr,qr)},[()=>Z($e()),()=>q(nt())]),W("click",ge,()=>L($e())),m(ct,B)}),m(Oe,Ue)};T(He,Oe=>{s(d)?Oe(re):s(l)&&Oe(X,1)})}var ie=h(J,2),ye=c(ie);{var ze=Oe=>{var Ue=cp(),Te=c(Ue),ct=c(Te);yi(ct,{size:36,class:"mx-auto mb-3 text-dl-text-dim/20"}),m(Oe,Ue)},dt=Oe=>{var Ue=up(),Te=c(Ue);Wt(Te,{size:16,class:"animate-spin"});var ct=h(Te);j(()=>D(ct,` ${s(p).label??""} 로딩 중...`)),m(Oe,Ue)},bt=Oe=>{var Ue=Np(),Te=G(Ue),ct=c(Te),Yt=c(ct),Me=c(Yt),$e=h(Yt,2);{var nt=le=>{var xe=fp(),We=c(xe);j(()=>D(We,`${s(v).totalRows??""}행 × ${s(v).columns.length??""}열`)),m(le,xe)};T($e,le=>{s(v).type==="table"&&le(nt)})}var B=h($e,2);{var ge=le=>{var xe=vp(),We=c(xe);j(_t=>D(We,_t),[()=>pe()==="원"?"원":pe()]),m(le,xe)},Ke=ne(()=>pe());T(B,le=>{s(Ke)&&le(ge)})}var De=h(ct,2),Je=c(De);{var xt=le=>{var xe=pp(),We=c(xe);Pf(We,{size:11});var _t=h(We);j(yt=>{Ze(xe,1,yt),D(_t,` ${s(k)?"한글":"EN"}`)},[()=>Xe(Qe("flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] transition-colors",s(k)?"bg-dl-primary/15 text-dl-primary-light":"text-dl-text-dim hover:text-dl-text hover:bg-white/5"))]),W("click",xe,()=>f(k,!s(k))),m(le,xe)},ft=ne(()=>Ye());T(Je,le=>{s(ft)&&le(xt)})}var vt=h(Je,2);{var Tt=le=>{var xe=mp(),We=c(xe);aa(We,{size:10}),W("click",xe,async()=>{try{await ai(s(o).stockCode,[s(p).name])}catch{}}),m(le,xe)};T(vt,le=>{s(o)&&le(Tt)})}var rr=h(Te,2);{var Wr=le=>{var xe=_p(),We=G(xe),_t=c(We),yt=c(_t),_r=c(yt),at=h(c(_r));rt(at,17,P,tt,($t,wt)=>{var ar=hp(),Lr=c(ar);j(()=>D(Lr,s(wt))),m($t,ar)});var Ir=h(yt);rt(Ir,21,()=>s(v).rows,tt,($t,wt)=>{const ar=ne(()=>s(wt).계정명),Lr=ne(()=>F(s(ar)));var An=xp(),yr=c(An),wa=c(yr),Jn=h(yr);rt(Jn,17,P,tt,(Cn,Xn)=>{const En=ne(()=>s(wt)[s(Xn)]);var ka=gp(),gs=c(ka);j((b,I)=>{Ze(ka,1,b),D(gs,I)},[()=>Xe(Qe("px-3 py-1.5 border-b border-dl-border/10 whitespace-nowrap text-right font-mono text-[10px]",s(En)===null||s(En)===void 0?"text-dl-text-dim/30":typeof s(En)=="number"&&s(En)<0?"text-dl-primary-light":"text-dl-accent-light")),()=>ue(s(En),pe())]),m(Cn,ka)}),j((Cn,Xn)=>{Ze(yr,1,Cn),go(yr,`padding-left: ${8+(s(Lr)-1)*12}px`),D(wa,Xn)},[()=>Xe(Qe("sticky left-0 z-[1] px-3 py-1.5 border-b border-r border-dl-border/10 whitespace-nowrap bg-dl-bg-dark/95",s(Lr)===1&&"font-semibold text-dl-text",s(Lr)===2&&"text-dl-text-muted",s(Lr)===3&&"text-dl-text-dim")),()=>x(s(ar))]),m($t,An)});var rn=h(We,2);{var nr=$t=>{var wt=bp(),ar=c(wt);j(()=>D(ar,`상위 ${s(v).rows.length??""}행만 표시 (전체 ${s(v).totalRows??""}행)`)),m($t,wt)};T(rn,$t=>{s(v).truncated&&$t(nr)})}m(le,xe)},tn=ne(()=>s(v).type==="table"&&Ye()),Mn=le=>{var xe=zp(),We=G(xe),_t=c(We),yt=c(_t),_r=c(yt);rt(_r,21,()=>s(v).columns,tt,(nr,$t)=>{var wt=yp(),ar=c(wt);j(()=>D(ar,s($t))),m(nr,wt)});var at=h(yt);rt(at,21,()=>s(v).rows,tt,(nr,$t)=>{var wt=kp();rt(wt,21,()=>s(v).columns,tt,(ar,Lr)=>{const An=ne(()=>s($t)[s(Lr)]);var yr=wp(),wa=c(yr);j((Jn,Cn)=>{Ze(yr,1,Jn),D(wa,Cn)},[()=>Xe(Qe("px-3 py-1.5 border-b border-dl-border/10 whitespace-nowrap",typeof s(An)=="number"?"text-right font-mono text-dl-accent-light text-[10px]":"text-dl-text-muted")),()=>ue(s(An),pe())]),m(ar,yr)}),m(nr,wt)});var Ir=h(We,2);{var rn=nr=>{var $t=Sp(),wt=c($t);j(()=>D(wt,`상위 ${s(v).rows.length??""}행만 표시 (전체 ${s(v).totalRows??""}행)`)),m(nr,$t)};T(Ir,nr=>{s(v).truncated&&nr(rn)})}m(le,xe)},Vt=le=>{var xe=Ap();rt(xe,21,()=>Object.entries(s(v).data),tt,(We,_t)=>{var yt=ne(()=>os(s(_t),2));let _r=()=>s(yt)[0],at=()=>s(yt)[1];var Ir=Mp(),rn=c(Ir),nr=c(rn),$t=h(rn,2),wt=c($t);j(()=>{D(nr,_r()),D(wt,at()??"-")}),m(We,Ir)}),m(le,xe)},qr=le=>{var xe=Ep(),We=c(xe),_t=c(We),yt=h(We,2);{var _r=at=>{var Ir=Cp();m(at,Ir)};T(yt,at=>{s(v).truncated&&at(_r)})}j(()=>D(_t,s(v).text)),m(le,xe)},ya=le=>{var xe=Tp(),We=c(xe);j(()=>D(We,s(v).error||"데이터를 불러올 수 없습니다")),m(le,xe)},Ht=le=>{var xe=$p(),We=c(xe),_t=c(We);j(yt=>D(_t,yt),[()=>s(v).data||JSON.stringify(s(v),null,2)]),m(le,xe)};T(rr,le=>{s(tn)?le(Wr):s(v).type==="table"?le(Mn,1):s(v).type==="dict"?le(Vt,2):s(v).type==="text"?le(qr,3):s(v).type==="error"?le(ya,4):le(Ht,-1)})}j(()=>D(Me,s(p).label)),m(Oe,Ue)};T(ye,Oe=>{s(p)?s(_)?Oe(dt,1):s(v)&&Oe(bt,2):Oe(ze)})}m(C,N)};T(se,C=>{s(o)?C(Se,-1):C(ve)})}W("keydown",R,C=>{var N;C.key==="Escape"&&((N=t.onClose)==null||N.call(t))}),W("click",Ve,()=>{var C;return(C=t.onClose)==null?void 0:C.call(t)}),m(e,R),Nr()}Sn(["keydown","click","input"]);var Op=w('<div class="sidebar-overlay"></div>'),Rp=w("<!> <span>확인 중...</span>",1),jp=w("<!> <span>설정 필요</span>",1),Dp=w('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),Fp=w('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!> <!>',1),Bp=w('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/80 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text-muted">AI Provider 확인 중...</div></div></div>'),Vp=w('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-primary/30 bg-dl-primary/5 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text">AI Provider가 설정되지 않았습니다</div> <div class="text-[11px] text-dl-text-muted mt-0.5">대화를 시작하려면 Provider를 설정해주세요</div></div> <button class="px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors flex-shrink-0">설정하기</button></div>'),Gp=w('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),Hp=w('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),Up=w('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),Kp=w('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),Wp=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),qp=w('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),Yp=w('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),Jp=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),Xp=w('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),Zp=w('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),Qp=w('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),em=w('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @anthropic-ai/claude-code</div></div></div>'),tm=w('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">인증</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">claude auth login</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">Claude Pro 또는 Max 구독이 필요합니다</span></div>',1),rm=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2">설치 완료 후 새로고침하세요</div></div>'),nm=w("<!> 브라우저에서 로그인 중...",1),am=w("<!> OpenAI 계정으로 로그인",1),sm=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2.5">ChatGPT 계정으로 로그인하여 사용하세요</div> <button class="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div></div>'),om=w('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),im=w('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),lm=w("<button> <!></button>"),dm=w('<div class="flex flex-wrap gap-1.5"></div>'),cm=w('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),um=w('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),fm=w('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),vm=w('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),pm=w('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),mm=w('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),hm=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),gm=w("<!> <!> <!> <!> <!> <!> <!>",1),xm=w('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),bm=w('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden"><div class="flex items-center justify-between px-6 pt-5 pb-3"><div class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),_m=w('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5"><div class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),ym=w('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn"><div> </div></div>'),wm=w('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-0 left-0 right-0 z-10 pointer-events-none"><div class="flex items-center justify-between px-3 h-11 pointer-events-auto" style="background: linear-gradient(to bottom, rgba(5,8,17,0.92) 40%, transparent);"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center gap-1"><a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <div class="w-px h-4 bg-dl-border mx-1"></div> <button><!> <!></button></div></div> <!></div> <!></div></div>  <!> <!> <!> <!>',1);function km(e,t){$r(t,!0);let r=V(""),n=V(!1),a=V(null),i=V(Ct({})),o=V(Ct({})),l=V(null),d=V(null),u=V(Ct([])),p=V(!0),v=V(0),_=V(!0),E=V(""),k=V(!1),z=V(null),g=V(Ct({})),A=V(Ct({})),$=V(""),L=V(!1),M=V(null),O=V(""),Z=V(!1),q=V(""),x=V(0),F=V(null),Y=V(!1),ue=V(Ct({})),pe=V(!1),Ye=V(!1);function P(){f(Ye,window.innerWidth<=768),s(Ye)&&f(p,!1)}Da(()=>(P(),window.addEventListener("resize",P),()=>window.removeEventListener("resize",P)));let R=V(null),Q=V(""),ae=V("error"),de=V(!1);function H(b,I="error",oe=4e3){f(Q,b,!0),f(ae,I,!0),f(de,!0),setTimeout(()=>{f(de,!1)},oe)}const y=xf();Da(()=>{ut()});let ke=V(Ct({})),fe=V(Ct({}));async function ut(){var b,I,oe;f(_,!0);try{const je=await hu();f(i,je.providers||{},!0),f(o,je.ollama||{},!0),f(ke,je.codex||{},!0),f(fe,je.claudeCode||{},!0),f(ue,je.chatgpt||{},!0),je.version&&f(E,je.version,!0);const Fe=localStorage.getItem("dartlab-provider"),pt=localStorage.getItem("dartlab-model");if(Fe&&((b=s(i)[Fe])!=null&&b.available)){f(l,Fe,!0),f(z,Fe,!0),await ra(Fe,pt),await Ve(Fe);const Ne=s(g)[Fe]||[];pt&&Ne.includes(pt)?f(d,pt,!0):Ne.length>0&&(f(d,Ne[0],!0),localStorage.setItem("dartlab-model",s(d))),f(u,Ne,!0),f(_,!1);return}if(Fe&&s(i)[Fe]){f(l,Fe,!0),f(z,Fe,!0),await Ve(Fe);const Ne=s(g)[Fe]||[];f(u,Ne,!0),pt&&Ne.includes(pt)?f(d,pt,!0):Ne.length>0&&f(d,Ne[0],!0),f(_,!1);return}for(const Ne of["chatgpt","codex","ollama"])if((I=s(i)[Ne])!=null&&I.available){f(l,Ne,!0),f(z,Ne,!0),await ra(Ne),await Ve(Ne);const Yr=s(g)[Ne]||[];f(u,Yr,!0),f(d,((oe=s(i)[Ne])==null?void 0:oe.model)||(Yr.length>0?Yr[0]:null),!0),s(d)&&localStorage.setItem("dartlab-model",s(d));break}}catch{}f(_,!1)}async function Ve(b){f(A,{...s(A),[b]:!0},!0);try{const I=await gu(b);f(g,{...s(g),[b]:I.models||[]},!0)}catch{f(g,{...s(g),[b]:[]},!0)}f(A,{...s(A),[b]:!1},!0)}async function Ge(b){var oe;f(l,b,!0),f(d,null),f(z,b,!0),localStorage.setItem("dartlab-provider",b),localStorage.removeItem("dartlab-model"),f($,""),f(M,null);try{await ra(b)}catch{}await Ve(b);const I=s(g)[b]||[];if(f(u,I,!0),I.length>0){f(d,((oe=s(i)[b])==null?void 0:oe.model)||I[0],!0),localStorage.setItem("dartlab-model",s(d));try{await ra(b,s(d))}catch{}}}async function ee(b){f(d,b,!0),localStorage.setItem("dartlab-model",b);try{await ra(s(l),b)}catch{}}function se(b){s(z)===b?f(z,null):(f(z,b,!0),Ve(b))}async function ve(){const b=s($).trim();if(!(!b||!s(l))){f(L,!0),f(M,null);try{const I=await ra(s(l),s(d),b);I.available?(f(M,"success"),s(i)[s(l)]={...s(i)[s(l)],available:!0,model:I.model},!s(d)&&I.model&&f(d,I.model,!0),await Ve(s(l)),f(u,s(g)[s(l)]||[],!0),H("API 키 인증 성공","success")):f(M,"error")}catch{f(M,"error")}f(L,!1)}}async function Se(){if(!s(Y)){f(Y,!0);try{const{authUrl:b}=await bu();window.open(b,"dartlab-oauth","width=600,height=700");const I=setInterval(async()=>{var oe;try{const je=await _u();je.done&&(clearInterval(I),f(Y,!1),je.error?H(`인증 실패: ${je.error}`):(H("ChatGPT 인증 성공","success"),await ut(),(oe=s(i).chatgpt)!=null&&oe.available&&await Ge("chatgpt")))}catch{clearInterval(I),f(Y,!1)}},2e3);setTimeout(()=>{clearInterval(I),s(Y)&&(f(Y,!1),H("인증 시간이 초과되었습니다. 다시 시도해주세요."))},12e4)}catch(b){f(Y,!1),H(`OAuth 시작 실패: ${b.message}`)}}}async function C(){try{await yu(),f(ue,{authenticated:!1},!0),s(l)==="chatgpt"&&f(i,{...s(i),chatgpt:{...s(i).chatgpt,available:!1}},!0),H("ChatGPT 로그아웃 완료","success"),await ut()}catch{H("로그아웃 실패")}}function N(){const b=s(O).trim();!b||s(Z)||(f(Z,!0),f(q,"준비 중..."),f(x,0),f(F,xu(b,{onProgress(I){I.total&&I.completed!==void 0?(f(x,Math.round(I.completed/I.total*100),!0),f(q,`다운로드 중... ${s(x)}%`)):I.status&&f(q,I.status,!0)},async onDone(){f(Z,!1),f(F,null),f(O,""),f(q,""),f(x,0),H(`${b} 다운로드 완료`,"success"),await Ve("ollama"),f(u,s(g).ollama||[],!0),s(u).includes(b)&&await ee(b)},onError(I){f(Z,!1),f(F,null),f(q,""),f(x,0),H(`다운로드 실패: ${I}`)}}),!0))}function J(){s(F)&&(s(F).abort(),f(F,null)),f(Z,!1),f(O,""),f(q,""),f(x,0)}function He(){f(p,!s(p))}function re(){if(f($,""),f(M,null),s(l))f(z,s(l),!0);else{const b=Object.keys(s(i));f(z,b.length>0?b[0]:null,!0)}f(k,!0),s(z)&&Ve(s(z))}function X(){y.createConversation(),f(r,""),f(n,!1),s(a)&&(s(a).abort(),f(a,null))}function ie(b){y.setActive(b),f(r,""),f(n,!1),s(a)&&(s(a).abort(),f(a,null))}function ye(b){f(R,b,!0)}function ze(){s(R)&&(y.deleteConversation(s(R)),f(R,null))}function dt(){var I;const b=y.active;if(!b)return null;for(let oe=b.messages.length-1;oe>=0;oe--){const je=b.messages[oe];if(je.role==="assistant"&&((I=je.meta)!=null&&I.stockCode))return je.meta.stockCode}return null}async function bt(){var dr,nn;const b=s(r).trim();if(!b||s(n))return;if(!s(l)||!((dr=s(i)[s(l)])!=null&&dr.available)){H("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),re();return}y.activeId||y.createConversation();const I=y.activeId;y.addMessage("user",b),f(r,""),f(n,!0),y.addMessage("assistant",""),y.updateLastMessage({loading:!0,startedAt:Date.now()}),La(v);const oe=y.active,je=[];let Fe=null;if(oe){const me=oe.messages.slice(0,-2);for(const te of me)if((te.role==="user"||te.role==="assistant")&&te.text&&te.text.trim()&&!te.error&&!te.loading){const qe={role:te.role,text:te.text};te.role==="assistant"&&((nn=te.meta)!=null&&nn.stockCode)&&(qe.meta={company:te.meta.company||te.company,stockCode:te.meta.stockCode,modules:te.meta.includedModules||null},Fe=te.meta.stockCode),je.push(qe)}}const pt=Fe||dt();function Ne(){return y.activeId!==I}const Yr=Su(pt,b,{provider:s(l),model:s(d)},{onMeta(me){var Or;if(Ne())return;const te=y.active,qe=te==null?void 0:te.messages[te.messages.length-1],Ut={meta:{...(qe==null?void 0:qe.meta)||{},...me}};me.company&&(Ut.company=me.company,y.activeId&&((Or=y.active)==null?void 0:Or.title)==="새 대화"&&y.updateTitle(y.activeId,me.company)),me.stockCode&&(Ut.stockCode=me.stockCode),y.updateLastMessage(Ut)},onSnapshot(me){Ne()||y.updateLastMessage({snapshot:me})},onContext(me){if(Ne())return;const te=y.active;if(!te)return;const qe=te.messages[te.messages.length-1],an=(qe==null?void 0:qe.contexts)||[];y.updateLastMessage({contexts:[...an,{module:me.module,label:me.label,text:me.text}]})},onSystemPrompt(me){Ne()||y.updateLastMessage({systemPrompt:me.text,userContent:me.userContent||null})},onToolCall(me){if(Ne())return;const te=y.active;if(!te)return;const qe=te.messages[te.messages.length-1],an=(qe==null?void 0:qe.toolEvents)||[];y.updateLastMessage({toolEvents:[...an,{type:"call",name:me.name,arguments:me.arguments}]})},onToolResult(me){if(Ne())return;const te=y.active;if(!te)return;const qe=te.messages[te.messages.length-1],an=(qe==null?void 0:qe.toolEvents)||[];y.updateLastMessage({toolEvents:[...an,{type:"result",name:me.name,result:me.result}]})},onChunk(me){if(Ne())return;const te=y.active;if(!te)return;const qe=te.messages[te.messages.length-1];y.updateLastMessage({text:((qe==null?void 0:qe.text)||"")+me}),La(v)},onDone(){if(Ne())return;const me=y.active,te=me==null?void 0:me.messages[me.messages.length-1],qe=te!=null&&te.startedAt?((Date.now()-te.startedAt)/1e3).toFixed(1):null;y.updateLastMessage({loading:!1,duration:qe}),y.flush(),f(n,!1),f(a,null),La(v)},onError(me,te,qe){Ne()||(y.updateLastMessage({text:`오류: ${me}`,loading:!1,error:!0}),y.flush(),te==="relogin"||te==="login"?(H(`${me} — 설정에서 재로그인하세요`),re()):H(te==="check_headers"||te==="check_endpoint"||te==="check_client_id"?`${me} — ChatGPT API 변경 감지. 업데이트를 확인하세요`:te==="rate_limit"?"요청이 너무 많습니다. 잠시 후 다시 시도해주세요":me),f(n,!1),f(a,null))}},je);f(a,Yr,!0)}function Oe(){s(a)&&(s(a).abort(),f(a,null),f(n,!1),y.updateLastMessage({loading:!1}),y.flush())}function Ue(){const b=y.active;if(!b||b.messages.length<2)return;let I="";for(let oe=b.messages.length-1;oe>=0;oe--)if(b.messages[oe].role==="user"){I=b.messages[oe].text;break}I&&(y.removeLastMessage(),y.removeLastMessage(),f(r,I,!0),requestAnimationFrame(()=>{bt()}))}function Te(){const b=y.active;if(!b)return;let I=`# ${b.title}

`;for(const pt of b.messages)pt.role==="user"?I+=`## You

${pt.text}

`:pt.role==="assistant"&&pt.text&&(I+=`## DartLab

${pt.text}

`);const oe=new Blob([I],{type:"text/markdown;charset=utf-8"}),je=URL.createObjectURL(oe),Fe=document.createElement("a");Fe.href=je,Fe.download=`${b.title||"dartlab-chat"}.md`,Fe.click(),URL.revokeObjectURL(je),H("대화가 마크다운으로 내보내졌습니다","success")}function ct(b){(b.metaKey||b.ctrlKey)&&b.key==="n"&&(b.preventDefault(),X()),(b.metaKey||b.ctrlKey)&&b.shiftKey&&b.key==="S"&&(b.preventDefault(),He()),b.key==="Escape"&&s(R)?f(R,null):b.key==="Escape"&&s(pe)?f(pe,!1):b.key==="Escape"&&s(k)&&f(k,!1)}let Yt=ne(()=>{var b;return((b=y.active)==null?void 0:b.messages)||[]}),Me=ne(()=>y.active&&y.active.messages.length>0),$e=ne(()=>{var b;return!s(_)&&(!s(l)||!((b=s(i)[s(l)])!=null&&b.available))});const nt=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var B=wm();is("keydown",Ks,ct);var ge=G(B),Ke=c(ge);{var De=b=>{var I=Op();W("click",I,()=>{f(p,!1)}),W("keydown",I,()=>{}),m(b,I)};T(Ke,b=>{s(Ye)&&s(p)&&b(De)})}var Je=h(Ke,2),xt=c(Je);{let b=ne(()=>s(Ye)?!0:s(p));ev(xt,{get conversations(){return y.conversations},get activeId(){return y.activeId},get open(){return s(b)},get version(){return s(E)},onNewChat:()=>{X(),s(Ye)&&f(p,!1)},onSelect:I=>{ie(I),s(Ye)&&f(p,!1)},onDelete:ye})}var ft=h(Je,2),vt=c(ft),Tt=c(vt),rr=c(Tt),Wr=c(rr);{var tn=b=>{Rf(b,{size:18})},Mn=b=>{Of(b,{size:18})};T(Wr,b=>{s(p)?b(tn):b(Mn,-1)})}var Vt=h(rr,2),qr=c(Vt),ya=c(qr);$f(ya,{size:15});var Ht=h(qr,2),le=c(Ht);ja(le,{size:15});var xe=h(Ht,2),We=c(xe);Nf(We,{size:15});var _t=h(xe,4),yt=c(_t);{var _r=b=>{var I=Rp(),oe=G(I);Wt(oe,{size:12,class:"animate-spin"}),m(b,I)},at=b=>{var I=jp(),oe=G(I);Nn(oe,{size:12}),m(b,I)},Ir=b=>{var I=Fp(),oe=h(G(I),2),je=c(oe),Fe=h(oe,2);{var pt=dr=>{var nn=Dp(),me=h(G(nn),2),te=c(me);j(()=>D(te,s(d))),m(dr,nn)};T(Fe,dr=>{s(d)&&dr(pt)})}var Ne=h(Fe,2);{var Yr=dr=>{Wt(dr,{size:10,class:"animate-spin text-dl-primary-light"})};T(Ne,dr=>{s(Z)&&dr(Yr)})}j(()=>D(je,s(l))),m(b,I)};T(yt,b=>{s(_)?b(_r):s($e)?b(at,1):b(Ir,-1)})}var rn=h(yt,2);Df(rn,{size:12});var nr=h(Tt,2);{var $t=b=>{var I=Bp(),oe=c(I);Wt(oe,{size:16,class:"text-dl-text-dim animate-spin flex-shrink-0"}),m(b,I)},wt=b=>{var I=Vp(),oe=c(I);Nn(oe,{size:16,class:"text-dl-primary-light flex-shrink-0"});var je=h(oe,4);W("click",je,()=>re()),m(b,I)};T(nr,b=>{s(_)&&!s(k)?b($t):s($e)&&!s(k)&&b(wt,1)})}var ar=h(vt,2);{var Lr=b=>{Jv(b,{get messages(){return s(Yt)},get isLoading(){return s(n)},get scrollTrigger(){return s(v)},onSend:bt,onStop:Oe,onRegenerate:Ue,onExport:Te,onOpenExplorer:()=>f(pe,!0),get inputText(){return s(r)},set inputText(I){f(r,I,!0)}})},An=b=>{lv(b,{onSend:bt,onOpenExplorer:()=>f(pe,!0),get inputText(){return s(r)},set inputText(I){f(r,I,!0)}})};T(ar,b=>{s(Me)?b(Lr):b(An,-1)})}var yr=h(ge,2);{var wa=b=>{var I=bm(),oe=c(I),je=c(oe),Fe=h(c(je),2),pt=c(Fe);wo(pt,{size:18});var Ne=h(je,2),Yr=c(Ne);rt(Yr,21,()=>Object.entries(s(i)),tt,(Ut,Or)=>{var sn=ne(()=>os(s(Or),2));let mt=()=>s(sn)[0],kt=()=>s(sn)[1];const Sa=ne(()=>mt()===s(l)),Fl=ne(()=>s(z)===mt()),Zn=ne(()=>kt().auth==="api_key"),xs=ne(()=>kt().auth==="cli"),Ja=ne(()=>s(g)[mt()]||[]),So=ne(()=>s(A)[mt()]);var bs=xm(),_s=c(bs),zo=c(_s),Mo=h(zo,2),Ao=c(Mo),Co=c(Ao),Bl=c(Co),Vl=h(Co,2);{var Gl=St=>{var cr=Gp();m(St,cr)};T(Vl,St=>{s(Sa)&&St(Gl)})}var Hl=h(Ao,2),Ul=c(Hl),Kl=h(Mo,2),Wl=c(Kl);{var ql=St=>{Ns(St,{size:16,class:"text-dl-success"})},Yl=St=>{var cr=Hp(),Qn=G(cr);xi(Qn,{size:14,class:"text-amber-400"}),m(St,cr)},Jl=St=>{var cr=Up(),Qn=G(cr);Bf(Qn,{size:14,class:"text-dl-text-dim"}),m(St,cr)};T(Wl,St=>{kt().available?St(ql):s(Zn)?St(Yl,1):s(xs)&&!kt().available&&St(Jl,2)})}var Xl=h(_s,2);{var Zl=St=>{var cr=gm(),Qn=G(cr);{var Ql=Be=>{var st=Wp(),ht=c(st),Lt=c(ht),Jt=h(ht,2),ot=c(Jt),Ot=h(ot,2),sr=c(Ot);{var Gt=Re=>{Wt(Re,{size:12,class:"animate-spin"})},it=Re=>{xi(Re,{size:12})};T(sr,Re=>{s(L)?Re(Gt):Re(it,-1)})}var Nt=h(Jt,2);{var et=Re=>{var Kt=Kp(),zt=c(Kt);Nn(zt,{size:12}),m(Re,Kt)};T(Nt,Re=>{s(M)==="error"&&Re(et)})}j(Re=>{D(Lt,kt().envKey?`환경변수 ${kt().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),Ba(ot,"placeholder",mt()==="openai"?"sk-...":mt()==="claude"?"sk-ant-...":"API Key"),Ot.disabled=Re},[()=>!s($).trim()||s(L)]),W("keydown",ot,Re=>{Re.key==="Enter"&&ve()}),na(ot,()=>s($),Re=>f($,Re)),W("click",Ot,ve),m(Be,st)};T(Qn,Be=>{s(Zn)&&!kt().available&&Be(Ql)})}var Eo=h(Qn,2);{var ed=Be=>{var st=Yp(),ht=c(st),Lt=c(ht);Ns(Lt,{size:13,class:"text-dl-success"});var Jt=h(ht,2),ot=c(Jt),Ot=h(ot,2);{var sr=it=>{var Nt=qp(),et=c(Nt);{var Re=zt=>{Wt(zt,{size:10,class:"animate-spin"})},Kt=zt=>{var ur=Ra("변경");m(zt,ur)};T(et,zt=>{s(L)?zt(Re):zt(Kt,-1)})}j(()=>Nt.disabled=s(L)),W("click",Nt,ve),m(it,Nt)},Gt=ne(()=>s($).trim());T(Ot,it=>{s(Gt)&&it(sr)})}W("keydown",ot,it=>{it.key==="Enter"&&ve()}),na(ot,()=>s($),it=>f($,it)),m(Be,st)};T(Eo,Be=>{s(Zn)&&kt().available&&Be(ed)})}var To=h(Eo,2);{var td=Be=>{var st=Jp(),ht=h(c(st),2),Lt=c(ht);aa(Lt,{size:14});var Jt=h(Lt,2);gi(Jt,{size:10,class:"ml-auto"}),m(Be,st)},rd=Be=>{var st=Xp(),ht=c(st),Lt=c(ht);Nn(Lt,{size:14}),m(Be,st)};T(To,Be=>{mt()==="ollama"&&!s(o).installed?Be(td):mt()==="ollama"&&s(o).installed&&!s(o).running&&Be(rd,1)})}var $o=h(To,2);{var nd=Be=>{var st=rm(),ht=c(st);{var Lt=ot=>{var Ot=Qp(),sr=G(Ot),Gt=c(sr),it=h(sr,2),Nt=c(it);{var et=wr=>{var Tn=Zp();m(wr,Tn)};T(Nt,wr=>{s(ke).installed||wr(et)})}var Re=h(Nt,2),Kt=c(Re),zt=c(Kt),ur=h(it,2),on=c(ur);Nn(on,{size:12,class:"text-amber-400 flex-shrink-0"}),j(()=>{D(Gt,s(ke).installed?"Codex CLI가 설치되었지만 인증이 필요합니다":"Codex CLI 설치가 필요합니다"),D(zt,s(ke).installed?"1.":"2.")}),m(ot,Ot)},Jt=ot=>{var Ot=tm(),sr=G(Ot),Gt=c(sr),it=h(sr,2),Nt=c(it);{var et=wr=>{var Tn=em();m(wr,Tn)};T(Nt,wr=>{s(fe).installed||wr(et)})}var Re=h(Nt,2),Kt=c(Re),zt=c(Kt),ur=h(it,2),on=c(ur);Nn(on,{size:12,class:"text-amber-400 flex-shrink-0"}),j(()=>{D(Gt,s(fe).installed&&!s(fe).authenticated?"Claude Code가 설치되었지만 인증이 필요합니다":"Claude Code CLI 설치가 필요합니다"),D(zt,s(fe).installed?"1.":"2.")}),m(ot,Ot)};T(ht,ot=>{mt()==="codex"?ot(Lt):mt()==="claude-code"&&ot(Jt,1)})}m(Be,st)};T($o,Be=>{s(xs)&&!kt().available&&Be(nd)})}var No=h($o,2);{var ad=Be=>{var st=sm(),ht=h(c(st),2),Lt=c(ht);{var Jt=Gt=>{var it=nm(),Nt=G(it);Wt(Nt,{size:14,class:"animate-spin"}),m(Gt,it)},ot=Gt=>{var it=am(),Nt=G(it);If(Nt,{size:14}),m(Gt,it)};T(Lt,Gt=>{s(Y)?Gt(Jt):Gt(ot,-1)})}var Ot=h(ht,2),sr=c(Ot);Nn(sr,{size:12,class:"text-amber-400 flex-shrink-0"}),j(()=>ht.disabled=s(Y)),W("click",ht,Se),m(Be,st)};T(No,Be=>{kt().auth==="oauth"&&!kt().available&&Be(ad)})}var Po=h(No,2);{var sd=Be=>{var st=om(),ht=c(st),Lt=c(ht),Jt=c(Lt);Ns(Jt,{size:13,class:"text-dl-success"});var ot=h(Lt,2),Ot=c(ot);Lf(Ot,{size:11}),W("click",ot,C),m(Be,st)};T(Po,Be=>{kt().auth==="oauth"&&kt().available&&Be(sd)})}var od=h(Po,2);{var id=Be=>{var st=hm(),ht=c(st),Lt=h(c(ht),2);{var Jt=et=>{Wt(et,{size:12,class:"animate-spin text-dl-text-dim"})};T(Lt,et=>{s(So)&&et(Jt)})}var ot=h(ht,2);{var Ot=et=>{var Re=im(),Kt=c(Re);Wt(Kt,{size:14,class:"animate-spin"}),m(et,Re)},sr=et=>{var Re=dm();rt(Re,21,()=>s(Ja),tt,(Kt,zt)=>{var ur=lm(),on=c(ur),wr=h(on);{var Tn=fr=>{Af(fr,{size:10,class:"inline ml-1"})};T(wr,fr=>{s(zt)===s(d)&&s(Sa)&&fr(Tn)})}j(fr=>{Ze(ur,1,fr),D(on,`${s(zt)??""} `)},[()=>Xe(Qe("px-3 py-1.5 rounded-lg text-[11px] border transition-all",s(zt)===s(d)&&s(Sa)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),W("click",ur,()=>{mt()!==s(l)&&Ge(mt()),ee(s(zt))}),m(Kt,ur)}),m(et,Re)},Gt=et=>{var Re=cm();m(et,Re)};T(ot,et=>{s(So)&&s(Ja).length===0?et(Ot):s(Ja).length>0?et(sr,1):et(Gt,-1)})}var it=h(ot,2);{var Nt=et=>{var Re=mm(),Kt=c(Re),zt=h(c(Kt),2),ur=h(c(zt));gi(ur,{size:9});var on=h(Kt,2);{var wr=fr=>{var za=um(),Ma=c(za),ea=c(Ma),Aa=c(ea);Wt(Aa,{size:12,class:"animate-spin text-dl-primary-light"});var ys=h(ea,2),Xa=h(Ma,2),Jr=c(Xa),kr=h(Xa,2),ws=c(kr);j(()=>{go(Jr,`width: ${s(x)??""}%`),D(ws,s(q))}),W("click",ys,J),m(fr,za)},Tn=fr=>{var za=pm(),Ma=G(za),ea=c(Ma),Aa=h(ea,2),ys=c(Aa);aa(ys,{size:12});var Xa=h(Ma,2);rt(Xa,21,()=>nt,tt,(Jr,kr)=>{const ws=ne(()=>s(Ja).some(ta=>ta===s(kr).name||ta===s(kr).name.split(":")[0]));var Io=ce(),ld=G(Io);{var dd=ta=>{var ks=vm(),Lo=c(ks),Oo=c(Lo),Ro=c(Oo),cd=c(Ro),jo=h(Ro,2),ud=c(jo),fd=h(jo,2);{var vd=Ss=>{var Fo=fm(),bd=c(Fo);j(()=>D(bd,s(kr).tag)),m(Ss,Fo)};T(fd,Ss=>{s(kr).tag&&Ss(vd)})}var pd=h(Oo,2),md=c(pd),hd=h(Lo,2),Do=c(hd),gd=c(Do),xd=h(Do,2);aa(xd,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),j(()=>{D(cd,s(kr).name),D(ud,s(kr).size),D(md,s(kr).desc),D(gd,`${s(kr).gb??""} GB`)}),W("click",ks,()=>{f(O,s(kr).name,!0),N()}),m(ta,ks)};T(ld,ta=>{s(ws)||ta(dd)})}m(Jr,Io)}),j(Jr=>Aa.disabled=Jr,[()=>!s(O).trim()]),W("keydown",ea,Jr=>{Jr.key==="Enter"&&N()}),na(ea,()=>s(O),Jr=>f(O,Jr)),W("click",Aa,N),m(fr,za)};T(on,fr=>{s(Z)?fr(wr):fr(Tn,-1)})}m(et,Re)};T(it,et=>{mt()==="ollama"&&et(Nt)})}m(Be,st)};T(od,Be=>{(kt().available||s(Zn)||s(xs)||kt().auth==="oauth")&&Be(id)})}m(St,cr)};T(Xl,St=>{(s(Fl)||s(Sa))&&St(Zl)})}j((St,cr)=>{Ze(bs,1,St),Ze(zo,1,cr),D(Bl,kt().label||mt()),D(Ul,kt().desc||"")},[()=>Xe(Qe("rounded-xl border transition-all",s(Sa)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>Xe(Qe("w-2.5 h-2.5 rounded-full flex-shrink-0",kt().available?"bg-dl-success":s(Zn)?"bg-amber-400":"bg-dl-text-dim"))]),W("click",_s,()=>{kt().available||s(Zn)?mt()===s(l)?se(mt()):Ge(mt()):se(mt())}),m(Ut,bs)});var dr=h(Ne,2),nn=c(dr),me=c(nn);{var te=Ut=>{var Or=Ra();j(()=>{var sn;return D(Or,`현재: ${(((sn=s(i)[s(l)])==null?void 0:sn.label)||s(l))??""} / ${s(d)??""}`)}),m(Ut,Or)},qe=Ut=>{var Or=Ra();j(()=>{var sn;return D(Or,`현재: ${(((sn=s(i)[s(l)])==null?void 0:sn.label)||s(l))??""}`)}),m(Ut,Or)};T(me,Ut=>{s(l)&&s(d)?Ut(te):s(l)&&Ut(qe,1)})}var an=h(nn,2);W("click",I,Ut=>{Ut.target===Ut.currentTarget&&f(k,!1)}),W("keydown",I,()=>{}),W("click",Fe,()=>f(k,!1)),W("click",an,()=>f(k,!1)),m(b,I)};T(yr,b=>{s(k)&&b(wa)})}var Jn=h(yr,2);{var Cn=b=>{Lp(b,{onClose:()=>f(pe,!1)})};T(Jn,b=>{s(pe)&&b(Cn)})}var Xn=h(Jn,2);{var En=b=>{var I=_m(),oe=c(I),je=h(c(oe),4),Fe=c(je),pt=h(Fe,2);W("click",I,Ne=>{Ne.target===Ne.currentTarget&&f(R,null)}),W("keydown",I,()=>{}),W("click",Fe,()=>f(R,null)),W("click",pt,ze),m(b,I)};T(Xn,b=>{s(R)&&b(En)})}var ka=h(Xn,2);{var gs=b=>{var I=ym(),oe=c(I),je=c(oe);j(Fe=>{Ze(oe,1,Fe),D(je,s(Q))},[()=>Xe(Qe("px-4 py-3 rounded-xl border text-[13px] shadow-2xl max-w-sm",s(ae)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":s(ae)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),m(b,I)};T(ka,b=>{s(de)&&b(gs)})}j(b=>{Ze(Je,1,Xe(s(Ye)?s(p)?"sidebar-mobile":"hidden":"")),Ze(_t,1,b)},[()=>Xe(Qe("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",s(_)?"text-dl-text-dim":s($e)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),W("click",rr,He),W("click",_t,()=>re()),m(e,B),Nr()}Sn(["click","keydown"]);qc(km,{target:document.getElementById("app")});
