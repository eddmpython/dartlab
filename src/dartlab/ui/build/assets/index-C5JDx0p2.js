var md=Object.defineProperty;var mo=e=>{throw TypeError(e)};var hd=(e,t,r)=>t in e?md(e,t,{enumerable:!0,configurable:!0,writable:!0,value:r}):e[t]=r;var lr=(e,t,r)=>hd(e,typeof t!="symbol"?t+"":t,r),Ya=(e,t,r)=>t.has(e)||mo("Cannot "+r);var w=(e,t,r)=>(Ya(e,t,"read from private field"),r?r.call(e):t.get(e)),ze=(e,t,r)=>t.has(e)?mo("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,r),pe=(e,t,r,n)=>(Ya(e,t,"write to private field"),n?n.call(e,r):t.set(e,r),r),dt=(e,t,r)=>(Ya(e,t,"access private method"),r);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const a of document.querySelectorAll('link[rel="modulepreload"]'))n(a);new MutationObserver(a=>{for(const s of a)if(s.type==="childList")for(const i of s.addedNodes)i.tagName==="LINK"&&i.rel==="modulepreload"&&n(i)}).observe(document,{childList:!0,subtree:!0});function r(a){const s={};return a.integrity&&(s.integrity=a.integrity),a.referrerPolicy&&(s.referrerPolicy=a.referrerPolicy),a.crossOrigin==="use-credentials"?s.credentials="include":a.crossOrigin==="anonymous"?s.credentials="omit":s.credentials="same-origin",s}function n(a){if(a.ep)return;a.ep=!0;const s=r(a);fetch(a.href,s)}})();const ns=!1;var zs=Array.isArray,gd=Array.prototype.indexOf,Rn=Array.prototype.includes,Oa=Array.from,bd=Object.defineProperty,qr=Object.getOwnPropertyDescriptor,Xo=Object.getOwnPropertyDescriptors,xd=Object.prototype,_d=Array.prototype,As=Object.getPrototypeOf,ho=Object.isExtensible;function Xn(e){return typeof e=="function"}const yd=()=>{};function wd(e){return e()}function as(e){for(var t=0;t<e.length;t++)e[t]()}function Zo(){var e,t,r=new Promise((n,a)=>{e=n,t=a});return{promise:r,resolve:e,reject:t}}function Qo(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const r=[];for(const n of e)if(r.push(n),r.length===t)break;return r}const zt=2,Gn=4,bn=8,Ra=1<<24,en=16,pr=32,wn=64,ss=128,rr=512,kt=1024,St=2048,vr=4096,Nt=8192,zr=16384,Hn=32768,Xr=65536,go=1<<17,kd=1<<18,Un=1<<19,ei=1<<20,Sr=1<<25,xn=65536,os=1<<21,Cs=1<<22,Kr=1<<23,Ar=Symbol("$state"),ti=Symbol("legacy props"),Sd=Symbol(""),ln=new class extends Error{constructor(){super(...arguments);lr(this,"name","StaleReactionError");lr(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var Ko;const ri=!!((Ko=globalThis.document)!=null&&Ko.contentType)&&globalThis.document.contentType.includes("xml");function Md(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function zd(e,t,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function Ad(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function Cd(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Ed(e){throw new Error("https://svelte.dev/e/effect_orphan")}function $d(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function Td(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function Pd(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function Nd(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function Id(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function Ld(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const Od=1,Rd=2,ni=4,jd=8,Dd=16,Fd=1,Bd=2,ai=4,Vd=8,Gd=16,Hd=1,Ud=2,gt=Symbol(),si="http://www.w3.org/1999/xhtml",oi="http://www.w3.org/2000/svg",Wd="http://www.w3.org/1998/Math/MathML",qd="@attach";function Kd(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function Yd(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function ii(e){return e===this.v}function Jd(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function li(e){return!Jd(e,this.v)}let va=!1,Xd=!1;function Zd(){va=!0}let bt=null;function jn(e){bt=e}function mr(e,t=!1,r){bt={p:bt,i:!1,c:null,e:null,s:e,x:null,l:va&&!t?{s:null,u:null,$:[]}:null}}function hr(e){var t=bt,r=t.e;if(r!==null){t.e=null;for(var n of r)Ai(n)}return t.i=!0,bt=t.p,{}}function pa(){return!va||bt!==null&&bt.l===null}let dn=[];function di(){var e=dn;dn=[],as(e)}function Cr(e){if(dn.length===0&&!na){var t=dn;queueMicrotask(()=>{t===dn&&di()})}dn.push(e)}function Qd(){for(;dn.length>0;)di()}function ci(e){var t=we;if(t===null)return ye.f|=Kr,e;if((t.f&Hn)===0&&(t.f&Gn)===0)throw e;Wr(e,t)}function Wr(e,t){for(;t!==null;){if((t.f&ss)!==0){if((t.f&Hn)===0)throw e;try{t.b.error(e);return}catch(r){e=r}}t=t.parent}throw e}const ec=-7169;function at(e,t){e.f=e.f&ec|t}function Es(e){(e.f&rr)!==0||e.deps===null?at(e,kt):at(e,vr)}function ui(e){if(e!==null)for(const t of e)(t.f&zt)===0||(t.f&xn)===0||(t.f^=xn,ui(t.deps))}function fi(e,t,r){(e.f&St)!==0?t.add(e):(e.f&vr)!==0&&r.add(e),ui(e.deps),at(e,kt)}const ya=new Set;let me=null,is=null,wt=null,jt=[],ja=null,na=!1,Dn=null,tc=1;var Gr,En,fn,$n,Tn,Pn,Hr,_r,Nn,Bt,ls,ds,cs,us;const Hs=class Hs{constructor(){ze(this,Bt);lr(this,"id",tc++);lr(this,"current",new Map);lr(this,"previous",new Map);ze(this,Gr,new Set);ze(this,En,new Set);ze(this,fn,0);ze(this,$n,0);ze(this,Tn,null);ze(this,Pn,new Set);ze(this,Hr,new Set);ze(this,_r,new Map);lr(this,"is_fork",!1);ze(this,Nn,!1)}skip_effect(t){w(this,_r).has(t)||w(this,_r).set(t,{d:[],m:[]})}unskip_effect(t){var r=w(this,_r).get(t);if(r){w(this,_r).delete(t);for(var n of r.d)at(n,St),Mr(n);for(n of r.m)at(n,vr),Mr(n)}}process(t){var a;jt=[],this.apply();var r=Dn=[],n=[];for(const s of t)dt(this,Bt,ds).call(this,s,r,n);if(Dn=null,dt(this,Bt,ls).call(this)){dt(this,Bt,cs).call(this,n),dt(this,Bt,cs).call(this,r);for(const[s,i]of w(this,_r))hi(s,i)}else{is=this,me=null;for(const s of w(this,Gr))s(this);w(this,Gr).clear(),w(this,fn)===0&&dt(this,Bt,us).call(this),bo(n),bo(r),w(this,Pn).clear(),w(this,Hr).clear(),is=null,(a=w(this,Tn))==null||a.resolve()}wt=null}capture(t,r){r!==gt&&!this.previous.has(t)&&this.previous.set(t,r),(t.f&Kr)===0&&(this.current.set(t,t.v),wt==null||wt.set(t,t.v))}activate(){me=this,this.apply()}deactivate(){me===this&&(me=null,wt=null)}flush(){var t;if(jt.length>0)me=this,vi();else if(w(this,fn)===0&&!this.is_fork){for(const r of w(this,Gr))r(this);w(this,Gr).clear(),dt(this,Bt,us).call(this),(t=w(this,Tn))==null||t.resolve()}this.deactivate()}discard(){for(const t of w(this,En))t(this);w(this,En).clear()}increment(t){pe(this,fn,w(this,fn)+1),t&&pe(this,$n,w(this,$n)+1)}decrement(t){pe(this,fn,w(this,fn)-1),t&&pe(this,$n,w(this,$n)-1),!w(this,Nn)&&(pe(this,Nn,!0),Cr(()=>{pe(this,Nn,!1),dt(this,Bt,ls).call(this)?jt.length>0&&this.flush():this.revive()}))}revive(){for(const t of w(this,Pn))w(this,Hr).delete(t),at(t,St),Mr(t);for(const t of w(this,Hr))at(t,vr),Mr(t);this.flush()}oncommit(t){w(this,Gr).add(t)}ondiscard(t){w(this,En).add(t)}settled(){return(w(this,Tn)??pe(this,Tn,Zo())).promise}static ensure(){if(me===null){const t=me=new Hs;ya.add(me),na||Cr(()=>{me===t&&t.flush()})}return me}apply(){}};Gr=new WeakMap,En=new WeakMap,fn=new WeakMap,$n=new WeakMap,Tn=new WeakMap,Pn=new WeakMap,Hr=new WeakMap,_r=new WeakMap,Nn=new WeakMap,Bt=new WeakSet,ls=function(){return this.is_fork||w(this,$n)>0},ds=function(t,r,n){t.f^=kt;for(var a=t.first;a!==null;){var s=a.f,i=(s&(pr|wn))!==0,l=i&&(s&kt)!==0,d=(s&Nt)!==0,c=l||w(this,_r).has(a);if(!c&&a.fn!==null){i?d||(a.f^=kt):(s&Gn)!==0?r.push(a):(s&(bn|Ra))!==0&&d?n.push(a):ba(a)&&(Vn(a),(s&en)!==0&&(w(this,Hr).add(a),d&&at(a,St)));var v=a.first;if(v!==null){a=v;continue}}for(;a!==null;){var h=a.next;if(h!==null){a=h;break}a=a.parent}}},cs=function(t){for(var r=0;r<t.length;r+=1)fi(t[r],w(this,Pn),w(this,Hr))},us=function(){var s;if(ya.size>1){this.previous.clear();var t=me,r=wt,n=!0;for(const i of ya){if(i===this){n=!1;continue}const l=[];for(const[c,v]of this.current){if(i.current.has(c))if(n&&v!==i.current.get(c))i.current.set(c,v);else continue;l.push(c)}if(l.length===0)continue;const d=[...i.current.keys()].filter(c=>!this.current.has(c));if(d.length>0){var a=jt;jt=[];const c=new Set,v=new Map;for(const h of l)pi(h,d,c,v);if(jt.length>0){me=i,i.apply();for(const h of jt)dt(s=i,Bt,ds).call(s,h,[],[]);i.deactivate()}jt=a}}me=t,wt=r}w(this,_r).clear(),ya.delete(this)};let Yr=Hs;function rc(e){var t=na;na=!0;try{for(var r;;){if(Qd(),jt.length===0&&(me==null||me.flush(),jt.length===0))return ja=null,r;vi()}}finally{na=t}}function vi(){var e=null;try{for(var t=0;jt.length>0;){var r=Yr.ensure();if(t++>1e3){var n,a;nc()}r.process(jt),Jr.clear()}}finally{jt=[],ja=null,Dn=null}}function nc(){try{$d()}catch(e){Wr(e,ja)}}let dr=null;function bo(e){var t=e.length;if(t!==0){for(var r=0;r<t;){var n=e[r++];if((n.f&(zr|Nt))===0&&ba(n)&&(dr=new Set,Vn(n),n.deps===null&&n.first===null&&n.nodes===null&&n.teardown===null&&n.ac===null&&Ti(n),(dr==null?void 0:dr.size)>0)){Jr.clear();for(const a of dr){if((a.f&(zr|Nt))!==0)continue;const s=[a];let i=a.parent;for(;i!==null;)dr.has(i)&&(dr.delete(i),s.push(i)),i=i.parent;for(let l=s.length-1;l>=0;l--){const d=s[l];(d.f&(zr|Nt))===0&&Vn(d)}}dr.clear()}}dr=null}}function pi(e,t,r,n){if(!r.has(e)&&(r.add(e),e.reactions!==null))for(const a of e.reactions){const s=a.f;(s&zt)!==0?pi(a,t,r,n):(s&(Cs|en))!==0&&(s&St)===0&&mi(a,t,n)&&(at(a,St),Mr(a))}}function mi(e,t,r){const n=r.get(e);if(n!==void 0)return n;if(e.deps!==null)for(const a of e.deps){if(Rn.call(t,a))return!0;if((a.f&zt)!==0&&mi(a,t,r))return r.set(a,!0),!0}return r.set(e,!1),!1}function Mr(e){var t=ja=e,r=t.b;if(r!=null&&r.is_pending&&(e.f&(Gn|bn|Ra))!==0&&(e.f&Hn)===0){r.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var n=t.f;if(Dn!==null&&t===we&&(e.f&bn)===0)return;if((n&(wn|pr))!==0){if((n&kt)===0)return;t.f^=kt}}jt.push(t)}function hi(e,t){if(!((e.f&pr)!==0&&(e.f&kt)!==0)){(e.f&St)!==0?t.d.push(e):(e.f&vr)!==0&&t.m.push(e),at(e,kt);for(var r=e.first;r!==null;)hi(r,t),r=r.next}}function ac(e){let t=0,r=Zr(0),n;return()=>{Ns()&&(o(r),Ls(()=>(t===0&&(n=_n(()=>e(()=>sa(r)))),t+=1,()=>{Cr(()=>{t-=1,t===0&&(n==null||n(),n=void 0,sa(r))})})))}}var sc=Xr|Un;function oc(e,t,r,n){new ic(e,t,r,n)}var tr,Ms,yr,vn,Rt,wr,Wt,cr,Nr,pn,Ur,In,Ln,On,Ir,Ia,pt,lc,dc,cc,fs,Aa,Ca,vs;class ic{constructor(t,r,n,a){ze(this,pt);lr(this,"parent");lr(this,"is_pending",!1);lr(this,"transform_error");ze(this,tr);ze(this,Ms,null);ze(this,yr);ze(this,vn);ze(this,Rt);ze(this,wr,null);ze(this,Wt,null);ze(this,cr,null);ze(this,Nr,null);ze(this,pn,0);ze(this,Ur,0);ze(this,In,!1);ze(this,Ln,new Set);ze(this,On,new Set);ze(this,Ir,null);ze(this,Ia,ac(()=>(pe(this,Ir,Zr(w(this,pn))),()=>{pe(this,Ir,null)})));var s;pe(this,tr,t),pe(this,yr,r),pe(this,vn,i=>{var l=we;l.b=this,l.f|=ss,n(i)}),this.parent=we.b,this.transform_error=a??((s=this.parent)==null?void 0:s.transform_error)??(i=>i),pe(this,Rt,ga(()=>{dt(this,pt,fs).call(this)},sc))}defer_effect(t){fi(t,w(this,Ln),w(this,On))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!w(this,yr).pending}update_pending_count(t){dt(this,pt,vs).call(this,t),pe(this,pn,w(this,pn)+t),!(!w(this,Ir)||w(this,In))&&(pe(this,In,!0),Cr(()=>{pe(this,In,!1),w(this,Ir)&&Fn(w(this,Ir),w(this,pn))}))}get_effect_pending(){return w(this,Ia).call(this),o(w(this,Ir))}error(t){var r=w(this,yr).onerror;let n=w(this,yr).failed;if(!r&&!n)throw t;w(this,wr)&&(Mt(w(this,wr)),pe(this,wr,null)),w(this,Wt)&&(Mt(w(this,Wt)),pe(this,Wt,null)),w(this,cr)&&(Mt(w(this,cr)),pe(this,cr,null));var a=!1,s=!1;const i=()=>{if(a){Yd();return}a=!0,s&&Ld(),w(this,cr)!==null&&hn(w(this,cr),()=>{pe(this,cr,null)}),dt(this,pt,Ca).call(this,()=>{Yr.ensure(),dt(this,pt,fs).call(this)})},l=d=>{try{s=!0,r==null||r(d,i),s=!1}catch(c){Wr(c,w(this,Rt)&&w(this,Rt).parent)}n&&pe(this,cr,dt(this,pt,Ca).call(this,()=>{Yr.ensure();try{return Ft(()=>{var c=we;c.b=this,c.f|=ss,n(w(this,tr),()=>d,()=>i)})}catch(c){return Wr(c,w(this,Rt).parent),null}}))};Cr(()=>{var d;try{d=this.transform_error(t)}catch(c){Wr(c,w(this,Rt)&&w(this,Rt).parent);return}d!==null&&typeof d=="object"&&typeof d.then=="function"?d.then(l,c=>Wr(c,w(this,Rt)&&w(this,Rt).parent)):l(d)})}}tr=new WeakMap,Ms=new WeakMap,yr=new WeakMap,vn=new WeakMap,Rt=new WeakMap,wr=new WeakMap,Wt=new WeakMap,cr=new WeakMap,Nr=new WeakMap,pn=new WeakMap,Ur=new WeakMap,In=new WeakMap,Ln=new WeakMap,On=new WeakMap,Ir=new WeakMap,Ia=new WeakMap,pt=new WeakSet,lc=function(){try{pe(this,wr,Ft(()=>w(this,vn).call(this,w(this,tr))))}catch(t){this.error(t)}},dc=function(t){const r=w(this,yr).failed;r&&pe(this,cr,Ft(()=>{r(w(this,tr),()=>t,()=>()=>{})}))},cc=function(){const t=w(this,yr).pending;t&&(this.is_pending=!0,pe(this,Wt,Ft(()=>t(w(this,tr)))),Cr(()=>{var r=pe(this,Nr,document.createDocumentFragment()),n=Er();r.append(n),pe(this,wr,dt(this,pt,Ca).call(this,()=>(Yr.ensure(),Ft(()=>w(this,vn).call(this,n))))),w(this,Ur)===0&&(w(this,tr).before(r),pe(this,Nr,null),hn(w(this,Wt),()=>{pe(this,Wt,null)}),dt(this,pt,Aa).call(this))}))},fs=function(){try{if(this.is_pending=this.has_pending_snippet(),pe(this,Ur,0),pe(this,pn,0),pe(this,wr,Ft(()=>{w(this,vn).call(this,w(this,tr))})),w(this,Ur)>0){var t=pe(this,Nr,document.createDocumentFragment());js(w(this,wr),t);const r=w(this,yr).pending;pe(this,Wt,Ft(()=>r(w(this,tr))))}else dt(this,pt,Aa).call(this)}catch(r){this.error(r)}},Aa=function(){this.is_pending=!1;for(const t of w(this,Ln))at(t,St),Mr(t);for(const t of w(this,On))at(t,vr),Mr(t);w(this,Ln).clear(),w(this,On).clear()},Ca=function(t){var r=we,n=ye,a=bt;sr(w(this,Rt)),ar(w(this,Rt)),jn(w(this,Rt).ctx);try{return t()}catch(s){return ci(s),null}finally{sr(r),ar(n),jn(a)}},vs=function(t){var r;if(!this.has_pending_snippet()){this.parent&&dt(r=this.parent,pt,vs).call(r,t);return}pe(this,Ur,w(this,Ur)+t),w(this,Ur)===0&&(dt(this,pt,Aa).call(this),w(this,Wt)&&hn(w(this,Wt),()=>{pe(this,Wt,null)}),w(this,Nr)&&(w(this,tr).before(w(this,Nr)),pe(this,Nr,null)))};function gi(e,t,r,n){const a=pa()?ma:$s;var s=e.filter(h=>!h.settled);if(r.length===0&&s.length===0){n(t.map(a));return}var i=we,l=uc(),d=s.length===1?s[0].promise:s.length>1?Promise.all(s.map(h=>h.promise)):null;function c(h){l();try{n(h)}catch(b){(i.f&zr)===0&&Wr(b,i)}ps()}if(r.length===0){d.then(()=>c(t.map(a)));return}function v(){l(),Promise.all(r.map(h=>vc(h))).then(h=>c([...t.map(a),...h])).catch(h=>Wr(h,i))}d?d.then(v):v()}function uc(){var e=we,t=ye,r=bt,n=me;return function(s=!0){sr(e),ar(t),jn(r),s&&(n==null||n.activate())}}function ps(e=!0){sr(null),ar(null),jn(null),e&&(me==null||me.deactivate())}function fc(){var e=we.b,t=me,r=e.is_rendered();return e.update_pending_count(1),t.increment(r),()=>{e.update_pending_count(-1),t.decrement(r)}}function ma(e){var t=zt|St,r=ye!==null&&(ye.f&zt)!==0?ye:null;return we!==null&&(we.f|=Un),{ctx:bt,deps:null,effects:null,equals:ii,f:t,fn:e,reactions:null,rv:0,v:gt,wv:0,parent:r??we,ac:null}}function vc(e,t,r){we===null&&Md();var a=void 0,s=Zr(gt),i=!ye,l=new Map;return Cc(()=>{var b;var d=Zo();a=d.promise;try{Promise.resolve(e()).then(d.resolve,d.reject).finally(ps)}catch(A){d.reject(A),ps()}var c=me;if(i){var v=fc();(b=l.get(c))==null||b.reject(ln),l.delete(c),l.set(c,d)}const h=(A,y=void 0)=>{if(c.activate(),y)y!==ln&&(s.f|=Kr,Fn(s,y));else{(s.f&Kr)!==0&&(s.f^=Kr),Fn(s,A);for(const[k,g]of l){if(l.delete(k),k===c)break;g.reject(ln)}}v&&v()};d.promise.then(h,A=>h(null,A||"unknown"))}),Fa(()=>{for(const d of l.values())d.reject(ln)}),new Promise(d=>{function c(v){function h(){v===a?d(s):c(a)}v.then(h,h)}c(a)})}function ce(e){const t=ma(e);return Ii(t),t}function $s(e){const t=ma(e);return t.equals=li,t}function pc(e){var t=e.effects;if(t!==null){e.effects=null;for(var r=0;r<t.length;r+=1)Mt(t[r])}}function mc(e){for(var t=e.parent;t!==null;){if((t.f&zt)===0)return(t.f&zr)===0?t:null;t=t.parent}return null}function Ts(e){var t,r=we;sr(mc(e));try{e.f&=~xn,pc(e),t=ji(e)}finally{sr(r)}return t}function bi(e){var t=Ts(e);if(!e.equals(t)&&(e.wv=Oi(),(!(me!=null&&me.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){at(e,kt);return}Qr||(wt!==null?(Ns()||me!=null&&me.is_fork)&&wt.set(e,t):Es(e))}function hc(e){var t,r;if(e.effects!==null)for(const n of e.effects)(n.teardown||n.ac)&&((t=n.teardown)==null||t.call(n),(r=n.ac)==null||r.abort(ln),n.teardown=yd,n.ac=null,da(n,0),Os(n))}function xi(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&Vn(t)}let ms=new Set;const Jr=new Map;let _i=!1;function Zr(e,t){var r={f:0,v:e,reactions:null,equals:ii,rv:0,wv:0};return r}function Y(e,t){const r=Zr(e);return Ii(r),r}function gc(e,t=!1,r=!0){var a;const n=Zr(e);return t||(n.equals=li),va&&r&&bt!==null&&bt.l!==null&&((a=bt.l).s??(a.s=[])).push(n),n}function u(e,t,r=!1){ye!==null&&(!fr||(ye.f&go)!==0)&&pa()&&(ye.f&(zt|en|Cs|go))!==0&&(nr===null||!Rn.call(nr,e))&&Id();let n=r?ut(t):t;return Fn(e,n)}function Fn(e,t){if(!e.equals(t)){var r=e.v;Qr?Jr.set(e,t):Jr.set(e,r),e.v=t;var n=Yr.ensure();if(n.capture(e,r),(e.f&zt)!==0){const a=e;(e.f&St)!==0&&Ts(a),Es(a)}e.wv=Oi(),yi(e,St),pa()&&we!==null&&(we.f&kt)!==0&&(we.f&(pr|wn))===0&&(er===null?$c([e]):er.push(e)),!n.is_fork&&ms.size>0&&!_i&&bc()}return t}function bc(){_i=!1;for(const e of ms)(e.f&kt)!==0&&at(e,vr),ba(e)&&Vn(e);ms.clear()}function aa(e,t=1){var r=o(e),n=t===1?r++:r--;return u(e,r),n}function sa(e){u(e,e.v+1)}function yi(e,t){var r=e.reactions;if(r!==null)for(var n=pa(),a=r.length,s=0;s<a;s++){var i=r[s],l=i.f;if(!(!n&&i===we)){var d=(l&St)===0;if(d&&at(i,t),(l&zt)!==0){var c=i;wt==null||wt.delete(c),(l&xn)===0&&(l&rr&&(i.f|=xn),yi(c,vr))}else d&&((l&en)!==0&&dr!==null&&dr.add(i),Mr(i))}}}function ut(e){if(typeof e!="object"||e===null||Ar in e)return e;const t=As(e);if(t!==xd&&t!==_d)return e;var r=new Map,n=zs(e),a=Y(0),s=gn,i=l=>{if(gn===s)return l();var d=ye,c=gn;ar(null),wo(s);var v=l();return ar(d),wo(c),v};return n&&r.set("length",Y(e.length)),new Proxy(e,{defineProperty(l,d,c){(!("value"in c)||c.configurable===!1||c.enumerable===!1||c.writable===!1)&&Pd();var v=r.get(d);return v===void 0?i(()=>{var h=Y(c.value);return r.set(d,h),h}):u(v,c.value,!0),!0},deleteProperty(l,d){var c=r.get(d);if(c===void 0){if(d in l){const v=i(()=>Y(gt));r.set(d,v),sa(a)}}else u(c,gt),sa(a);return!0},get(l,d,c){var A;if(d===Ar)return e;var v=r.get(d),h=d in l;if(v===void 0&&(!h||(A=qr(l,d))!=null&&A.writable)&&(v=i(()=>{var y=ut(h?l[d]:gt),k=Y(y);return k}),r.set(d,v)),v!==void 0){var b=o(v);return b===gt?void 0:b}return Reflect.get(l,d,c)},getOwnPropertyDescriptor(l,d){var c=Reflect.getOwnPropertyDescriptor(l,d);if(c&&"value"in c){var v=r.get(d);v&&(c.value=o(v))}else if(c===void 0){var h=r.get(d),b=h==null?void 0:h.v;if(h!==void 0&&b!==gt)return{enumerable:!0,configurable:!0,value:b,writable:!0}}return c},has(l,d){var b;if(d===Ar)return!0;var c=r.get(d),v=c!==void 0&&c.v!==gt||Reflect.has(l,d);if(c!==void 0||we!==null&&(!v||(b=qr(l,d))!=null&&b.writable)){c===void 0&&(c=i(()=>{var A=v?ut(l[d]):gt,y=Y(A);return y}),r.set(d,c));var h=o(c);if(h===gt)return!1}return v},set(l,d,c,v){var D;var h=r.get(d),b=d in l;if(n&&d==="length")for(var A=c;A<h.v;A+=1){var y=r.get(A+"");y!==void 0?u(y,gt):A in l&&(y=i(()=>Y(gt)),r.set(A+"",y))}if(h===void 0)(!b||(D=qr(l,d))!=null&&D.writable)&&(h=i(()=>Y(void 0)),u(h,ut(c)),r.set(d,h));else{b=h.v!==gt;var k=i(()=>ut(c));u(h,k)}var g=Reflect.getOwnPropertyDescriptor(l,d);if(g!=null&&g.set&&g.set.call(v,c),!b){if(n&&typeof d=="string"){var z=r.get("length"),L=Number(d);Number.isInteger(L)&&L>=z.v&&u(z,L+1)}sa(a)}return!0},ownKeys(l){o(a);var d=Reflect.ownKeys(l).filter(h=>{var b=r.get(h);return b===void 0||b.v!==gt});for(var[c,v]of r)v.v!==gt&&!(c in l)&&d.push(c);return d},setPrototypeOf(){Nd()}})}function xo(e){try{if(e!==null&&typeof e=="object"&&Ar in e)return e[Ar]}catch{}return e}function xc(e,t){return Object.is(xo(e),xo(t))}var hs,wi,ki,Si;function _c(){if(hs===void 0){hs=window,wi=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,r=Text.prototype;ki=qr(t,"firstChild").get,Si=qr(t,"nextSibling").get,ho(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),ho(r)&&(r.__t=void 0)}}function Er(e=""){return document.createTextNode(e)}function Lr(e){return ki.call(e)}function ha(e){return Si.call(e)}function f(e,t){return Lr(e)}function q(e,t=!1){{var r=Lr(e);return r instanceof Comment&&r.data===""?ha(r):r}}function x(e,t=1,r=!1){let n=e;for(;t--;)n=ha(n);return n}function yc(e){e.textContent=""}function Mi(){return!1}function Ps(e,t,r){return document.createElementNS(t??si,e,void 0)}function wc(e,t){if(t){const r=document.body;e.autofocus=!0,Cr(()=>{document.activeElement===r&&e.focus()})}}let _o=!1;function kc(){_o||(_o=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const r of e.target.elements)(t=r.__on_r)==null||t.call(r)})},{capture:!0}))}function Da(e){var t=ye,r=we;ar(null),sr(null);try{return e()}finally{ar(t),sr(r)}}function Sc(e,t,r,n=r){e.addEventListener(t,()=>Da(r));const a=e.__on_r;a?e.__on_r=()=>{a(),n(!0)}:e.__on_r=()=>n(!0),kc()}function zi(e){we===null&&(ye===null&&Ed(),Cd()),Qr&&Ad()}function Mc(e,t){var r=t.last;r===null?t.last=t.first=e:(r.next=e,e.prev=r,t.last=e)}function gr(e,t){var r=we;r!==null&&(r.f&Nt)!==0&&(e|=Nt);var n={ctx:bt,deps:null,nodes:null,f:e|St|rr,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},a=n;if((e&Gn)!==0)Dn!==null?Dn.push(n):Mr(n);else if(t!==null){try{Vn(n)}catch(i){throw Mt(n),i}a.deps===null&&a.teardown===null&&a.nodes===null&&a.first===a.last&&(a.f&Un)===0&&(a=a.first,(e&en)!==0&&(e&Xr)!==0&&a!==null&&(a.f|=Xr))}if(a!==null&&(a.parent=r,r!==null&&Mc(a,r),ye!==null&&(ye.f&zt)!==0&&(e&wn)===0)){var s=ye;(s.effects??(s.effects=[])).push(a)}return n}function Ns(){return ye!==null&&!fr}function Fa(e){const t=gr(bn,null);return at(t,kt),t.teardown=e,t}function Bn(e){zi();var t=we.f,r=!ye&&(t&pr)!==0&&(t&Hn)===0;if(r){var n=bt;(n.e??(n.e=[])).push(e)}else return Ai(e)}function Ai(e){return gr(Gn|ei,e)}function zc(e){return zi(),gr(bn|ei,e)}function Ac(e){Yr.ensure();const t=gr(wn|Un,e);return(r={})=>new Promise(n=>{r.outro?hn(t,()=>{Mt(t),n(void 0)}):(Mt(t),n(void 0))})}function Is(e){return gr(Gn,e)}function Cc(e){return gr(Cs|Un,e)}function Ls(e,t=0){return gr(bn|t,e)}function W(e,t=[],r=[],n=[]){gi(n,t,r,a=>{gr(bn,()=>e(...a.map(o)))})}function ga(e,t=0){var r=gr(en|t,e);return r}function Ci(e,t=0){var r=gr(Ra|t,e);return r}function Ft(e){return gr(pr|Un,e)}function Ei(e){var t=e.teardown;if(t!==null){const r=Qr,n=ye;yo(!0),ar(null);try{t.call(null)}finally{yo(r),ar(n)}}}function Os(e,t=!1){var r=e.first;for(e.first=e.last=null;r!==null;){const a=r.ac;a!==null&&Da(()=>{a.abort(ln)});var n=r.next;(r.f&wn)!==0?r.parent=null:Mt(r,t),r=n}}function Ec(e){for(var t=e.first;t!==null;){var r=t.next;(t.f&pr)===0&&Mt(t),t=r}}function Mt(e,t=!0){var r=!1;(t||(e.f&kd)!==0)&&e.nodes!==null&&e.nodes.end!==null&&($i(e.nodes.start,e.nodes.end),r=!0),Os(e,t&&!r),da(e,0),at(e,zr);var n=e.nodes&&e.nodes.t;if(n!==null)for(const s of n)s.stop();Ei(e);var a=e.parent;a!==null&&a.first!==null&&Ti(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function $i(e,t){for(;e!==null;){var r=e===t?null:ha(e);e.remove(),e=r}}function Ti(e){var t=e.parent,r=e.prev,n=e.next;r!==null&&(r.next=n),n!==null&&(n.prev=r),t!==null&&(t.first===e&&(t.first=n),t.last===e&&(t.last=r))}function hn(e,t,r=!0){var n=[];Pi(e,n,!0);var a=()=>{r&&Mt(e),t&&t()},s=n.length;if(s>0){var i=()=>--s||a();for(var l of n)l.out(i)}else a()}function Pi(e,t,r){if((e.f&Nt)===0){e.f^=Nt;var n=e.nodes&&e.nodes.t;if(n!==null)for(const l of n)(l.is_global||r)&&t.push(l);for(var a=e.first;a!==null;){var s=a.next,i=(a.f&Xr)!==0||(a.f&pr)!==0&&(e.f&en)!==0;Pi(a,t,i?r:!1),a=s}}}function Rs(e){Ni(e,!0)}function Ni(e,t){if((e.f&Nt)!==0){e.f^=Nt;for(var r=e.first;r!==null;){var n=r.next,a=(r.f&Xr)!==0||(r.f&pr)!==0;Ni(r,a?t:!1),r=n}var s=e.nodes&&e.nodes.t;if(s!==null)for(const i of s)(i.is_global||t)&&i.in()}}function js(e,t){if(e.nodes)for(var r=e.nodes.start,n=e.nodes.end;r!==null;){var a=r===n?null:ha(r);t.append(r),r=a}}let Ea=!1,Qr=!1;function yo(e){Qr=e}let ye=null,fr=!1;function ar(e){ye=e}let we=null;function sr(e){we=e}let nr=null;function Ii(e){ye!==null&&(nr===null?nr=[e]:nr.push(e))}let Dt=null,Ut=0,er=null;function $c(e){er=e}let Li=1,cn=0,gn=cn;function wo(e){gn=e}function Oi(){return++Li}function ba(e){var t=e.f;if((t&St)!==0)return!0;if(t&zt&&(e.f&=~xn),(t&vr)!==0){for(var r=e.deps,n=r.length,a=0;a<n;a++){var s=r[a];if(ba(s)&&bi(s),s.wv>e.wv)return!0}(t&rr)!==0&&wt===null&&at(e,kt)}return!1}function Ri(e,t,r=!0){var n=e.reactions;if(n!==null&&!(nr!==null&&Rn.call(nr,e)))for(var a=0;a<n.length;a++){var s=n[a];(s.f&zt)!==0?Ri(s,t,!1):t===s&&(r?at(s,St):(s.f&kt)!==0&&at(s,vr),Mr(s))}}function ji(e){var k;var t=Dt,r=Ut,n=er,a=ye,s=nr,i=bt,l=fr,d=gn,c=e.f;Dt=null,Ut=0,er=null,ye=(c&(pr|wn))===0?e:null,nr=null,jn(e.ctx),fr=!1,gn=++cn,e.ac!==null&&(Da(()=>{e.ac.abort(ln)}),e.ac=null);try{e.f|=os;var v=e.fn,h=v();e.f|=Hn;var b=e.deps,A=me==null?void 0:me.is_fork;if(Dt!==null){var y;if(A||da(e,Ut),b!==null&&Ut>0)for(b.length=Ut+Dt.length,y=0;y<Dt.length;y++)b[Ut+y]=Dt[y];else e.deps=b=Dt;if(Ns()&&(e.f&rr)!==0)for(y=Ut;y<b.length;y++)((k=b[y]).reactions??(k.reactions=[])).push(e)}else!A&&b!==null&&Ut<b.length&&(da(e,Ut),b.length=Ut);if(pa()&&er!==null&&!fr&&b!==null&&(e.f&(zt|vr|St))===0)for(y=0;y<er.length;y++)Ri(er[y],e);if(a!==null&&a!==e){if(cn++,a.deps!==null)for(let g=0;g<r;g+=1)a.deps[g].rv=cn;if(t!==null)for(const g of t)g.rv=cn;er!==null&&(n===null?n=er:n.push(...er))}return(e.f&Kr)!==0&&(e.f^=Kr),h}catch(g){return ci(g)}finally{e.f^=os,Dt=t,Ut=r,er=n,ye=a,nr=s,jn(i),fr=l,gn=d}}function Tc(e,t){let r=t.reactions;if(r!==null){var n=gd.call(r,e);if(n!==-1){var a=r.length-1;a===0?r=t.reactions=null:(r[n]=r[a],r.pop())}}if(r===null&&(t.f&zt)!==0&&(Dt===null||!Rn.call(Dt,t))){var s=t;(s.f&rr)!==0&&(s.f^=rr,s.f&=~xn),Es(s),hc(s),da(s,0)}}function da(e,t){var r=e.deps;if(r!==null)for(var n=t;n<r.length;n++)Tc(e,r[n])}function Vn(e){var t=e.f;if((t&zr)===0){at(e,kt);var r=we,n=Ea;we=e,Ea=!0;try{(t&(en|Ra))!==0?Ec(e):Os(e),Ei(e);var a=ji(e);e.teardown=typeof a=="function"?a:null,e.wv=Li;var s;ns&&Xd&&(e.f&St)!==0&&e.deps}finally{Ea=n,we=r}}}async function Pc(){await Promise.resolve(),rc()}function o(e){var t=e.f,r=(t&zt)!==0;if(ye!==null&&!fr){var n=we!==null&&(we.f&zr)!==0;if(!n&&(nr===null||!Rn.call(nr,e))){var a=ye.deps;if((ye.f&os)!==0)e.rv<cn&&(e.rv=cn,Dt===null&&a!==null&&a[Ut]===e?Ut++:Dt===null?Dt=[e]:Dt.push(e));else{(ye.deps??(ye.deps=[])).push(e);var s=e.reactions;s===null?e.reactions=[ye]:Rn.call(s,ye)||s.push(ye)}}}if(Qr&&Jr.has(e))return Jr.get(e);if(r){var i=e;if(Qr){var l=i.v;return((i.f&kt)===0&&i.reactions!==null||Fi(i))&&(l=Ts(i)),Jr.set(i,l),l}var d=(i.f&rr)===0&&!fr&&ye!==null&&(Ea||(ye.f&rr)!==0),c=(i.f&Hn)===0;ba(i)&&(d&&(i.f|=rr),bi(i)),d&&!c&&(xi(i),Di(i))}if(wt!=null&&wt.has(e))return wt.get(e);if((e.f&Kr)!==0)throw e.v;return e.v}function Di(e){if(e.f|=rr,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&zt)!==0&&(t.f&rr)===0&&(xi(t),Di(t))}function Fi(e){if(e.v===gt)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(Jr.has(t)||(t.f&zt)!==0&&Fi(t))return!0;return!1}function _n(e){var t=fr;try{return fr=!0,e()}finally{fr=t}}function on(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(Ar in e)gs(e);else if(!Array.isArray(e))for(let t in e){const r=e[t];typeof r=="object"&&r&&Ar in r&&gs(r)}}}function gs(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let n in e)try{gs(e[n],t)}catch{}const r=As(e);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const n=Xo(r);for(let a in n){const s=n[a].get;if(s)try{s.call(e)}catch{}}}}}function Nc(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const Ic=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function Lc(e){return Ic.includes(e)}const Oc={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function Rc(e){return e=e.toLowerCase(),Oc[e]??e}const jc=["touchstart","touchmove"];function Dc(e){return jc.includes(e)}const un=Symbol("events"),Bi=new Set,bs=new Set;function Vi(e,t,r,n={}){function a(s){if(n.capture||xs.call(t,s),!s.cancelBubble)return Da(()=>r==null?void 0:r.call(this,s))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Cr(()=>{t.addEventListener(e,a,n)}):t.addEventListener(e,a,n),a}function Ta(e,t,r,n,a){var s={capture:n,passive:a},i=Vi(e,t,r,s);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&Fa(()=>{t.removeEventListener(e,i,s)})}function U(e,t,r){(t[un]??(t[un]={}))[e]=r}function tn(e){for(var t=0;t<e.length;t++)Bi.add(e[t]);for(var r of bs)r(e)}let ko=null;function xs(e){var g,z;var t=this,r=t.ownerDocument,n=e.type,a=((g=e.composedPath)==null?void 0:g.call(e))||[],s=a[0]||e.target;ko=e;var i=0,l=ko===e&&e[un];if(l){var d=a.indexOf(l);if(d!==-1&&(t===document||t===window)){e[un]=t;return}var c=a.indexOf(t);if(c===-1)return;d<=c&&(i=d)}if(s=a[i]||e.target,s!==t){bd(e,"currentTarget",{configurable:!0,get(){return s||r}});var v=ye,h=we;ar(null),sr(null);try{for(var b,A=[];s!==null;){var y=s.assignedSlot||s.parentNode||s.host||null;try{var k=(z=s[un])==null?void 0:z[n];k!=null&&(!s.disabled||e.target===s)&&k.call(s,e)}catch(L){b?A.push(L):b=L}if(e.cancelBubble||y===t||y===null)break;s=y}if(b){for(let L of A)queueMicrotask(()=>{throw L});throw b}}finally{e[un]=t,delete e.currentTarget,ar(v),sr(h)}}}var Yo;const Ja=((Yo=globalThis==null?void 0:globalThis.window)==null?void 0:Yo.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function Fc(e){return(Ja==null?void 0:Ja.createHTML(e))??e}function Gi(e){var t=Ps("template");return t.innerHTML=Fc(e.replaceAll("<!>","<!---->")),t.content}function yn(e,t){var r=we;r.nodes===null&&(r.nodes={start:e,end:t,a:null,t:null})}function S(e,t){var r=(t&Hd)!==0,n=(t&Ud)!==0,a,s=!e.startsWith("<!>");return()=>{a===void 0&&(a=Gi(s?e:"<!>"+e),r||(a=Lr(a)));var i=n||wi?document.importNode(a,!0):a.cloneNode(!0);if(r){var l=Lr(i),d=i.lastChild;yn(l,d)}else yn(i,i);return i}}function Bc(e,t,r="svg"){var n=!e.startsWith("<!>"),a=`<${r}>${n?e:"<!>"+e}</${r}>`,s;return()=>{if(!s){var i=Gi(a),l=Lr(i);s=Lr(l)}var d=s.cloneNode(!0);return yn(d,d),d}}function Vc(e,t){return Bc(e,t,"svg")}function oa(e=""){{var t=Er(e+"");return yn(t,t),t}}function ue(){var e=document.createDocumentFragment(),t=document.createComment(""),r=Er();return e.append(t,r),yn(t,r),e}function p(e,t){e!==null&&e.before(t)}function Z(e,t){var r=t==null?"":typeof t=="object"?`${t}`:t;r!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=r,e.nodeValue=`${r}`)}function Gc(e,t){return Hc(e,t)}const wa=new Map;function Hc(e,{target:t,anchor:r,props:n={},events:a,context:s,intro:i=!0,transformError:l}){_c();var d=void 0,c=Ac(()=>{var v=r??t.appendChild(Er());oc(v,{pending:()=>{}},A=>{mr({});var y=bt;s&&(y.c=s),a&&(n.$$events=a),d=e(A,n)||{},hr()},l);var h=new Set,b=A=>{for(var y=0;y<A.length;y++){var k=A[y];if(!h.has(k)){h.add(k);var g=Dc(k);for(const D of[t,document]){var z=wa.get(D);z===void 0&&(z=new Map,wa.set(D,z));var L=z.get(k);L===void 0?(D.addEventListener(k,xs,{passive:g}),z.set(k,1)):z.set(k,L+1)}}}};return b(Oa(Bi)),bs.add(b),()=>{var g;for(var A of h)for(const z of[t,document]){var y=wa.get(z),k=y.get(A);--k==0?(z.removeEventListener(A,xs),y.delete(A),y.size===0&&wa.delete(z)):y.set(A,k)}bs.delete(b),v!==r&&((g=v.parentNode)==null||g.removeChild(v))}});return Uc.set(d,c),d}let Uc=new WeakMap;var ur,kr,qt,mn,ua,fa,La;class Ds{constructor(t,r=!0){lr(this,"anchor");ze(this,ur,new Map);ze(this,kr,new Map);ze(this,qt,new Map);ze(this,mn,new Set);ze(this,ua,!0);ze(this,fa,t=>{if(w(this,ur).has(t)){var r=w(this,ur).get(t),n=w(this,kr).get(r);if(n)Rs(n),w(this,mn).delete(r);else{var a=w(this,qt).get(r);a&&(a.effect.f&Nt)===0&&(w(this,kr).set(r,a.effect),w(this,qt).delete(r),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),n=a.effect)}for(const[s,i]of w(this,ur)){if(w(this,ur).delete(s),s===t)break;const l=w(this,qt).get(i);l&&(Mt(l.effect),w(this,qt).delete(i))}for(const[s,i]of w(this,kr)){if(s===r||w(this,mn).has(s)||(i.f&Nt)!==0)continue;const l=()=>{if(Array.from(w(this,ur).values()).includes(s)){var c=document.createDocumentFragment();js(i,c),c.append(Er()),w(this,qt).set(s,{effect:i,fragment:c})}else Mt(i);w(this,mn).delete(s),w(this,kr).delete(s)};w(this,ua)||!n?(w(this,mn).add(s),hn(i,l,!1)):l()}}});ze(this,La,t=>{w(this,ur).delete(t);const r=Array.from(w(this,ur).values());for(const[n,a]of w(this,qt))r.includes(n)||(Mt(a.effect),w(this,qt).delete(n))});this.anchor=t,pe(this,ua,r)}ensure(t,r){var n=me,a=Mi();if(r&&!w(this,kr).has(t)&&!w(this,qt).has(t))if(a){var s=document.createDocumentFragment(),i=Er();s.append(i),w(this,qt).set(t,{effect:Ft(()=>r(i)),fragment:s})}else w(this,kr).set(t,Ft(()=>r(this.anchor)));if(w(this,ur).set(n,t),a){for(const[l,d]of w(this,kr))l===t?n.unskip_effect(d):n.skip_effect(d);for(const[l,d]of w(this,qt))l===t?n.unskip_effect(d.effect):n.skip_effect(d.effect);n.oncommit(w(this,fa)),n.ondiscard(w(this,La))}else w(this,fa).call(this,n)}}ur=new WeakMap,kr=new WeakMap,qt=new WeakMap,mn=new WeakMap,ua=new WeakMap,fa=new WeakMap,La=new WeakMap;function T(e,t,r=!1){var n=new Ds(e),a=r?Xr:0;function s(i,l){n.ensure(i,l)}ga(()=>{var i=!1;t((l,d=0)=>{i=!0,s(d,l)}),i||s(-1,null)},a)}function ft(e,t){return t}function Wc(e,t,r){for(var n=[],a=t.length,s,i=t.length,l=0;l<a;l++){let h=t[l];hn(h,()=>{if(s){if(s.pending.delete(h),s.done.add(h),s.pending.size===0){var b=e.outrogroups;_s(e,Oa(s.done)),b.delete(s),b.size===0&&(e.outrogroups=null)}}else i-=1},!1)}if(i===0){var d=n.length===0&&r!==null;if(d){var c=r,v=c.parentNode;yc(v),v.append(c),e.items.clear()}_s(e,t,!d)}else s={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(s)}function _s(e,t,r=!0){var n;if(e.pending.size>0){n=new Set;for(const i of e.pending.values())for(const l of i)n.add(e.items.get(l).e)}for(var a=0;a<t.length;a++){var s=t[a];if(n!=null&&n.has(s)){s.f|=Sr;const i=document.createDocumentFragment();js(s,i)}else Mt(t[a],r)}}var So;function vt(e,t,r,n,a,s=null){var i=e,l=new Map,d=(t&ni)!==0;if(d){var c=e;i=c.appendChild(Er())}var v=null,h=$s(()=>{var D=r();return zs(D)?D:D==null?[]:Oa(D)}),b,A=new Map,y=!0;function k(D){(L.effect.f&zr)===0&&(L.pending.delete(D),L.fallback=v,qc(L,b,i,t,n),v!==null&&(b.length===0?(v.f&Sr)===0?Rs(v):(v.f^=Sr,ra(v,null,i)):hn(v,()=>{v=null})))}function g(D){L.pending.delete(D)}var z=ga(()=>{b=o(h);for(var D=b.length,M=new Set,R=me,X=Mi(),P=0;P<D;P+=1){var m=b[P],N=n(m,P),B=y?null:l.get(N);B?(B.v&&Fn(B.v,m),B.i&&Fn(B.i,P),X&&R.unskip_effect(B.e)):(B=Kc(l,y?i:So??(So=Er()),m,N,P,a,t,r),y||(B.e.f|=Sr),l.set(N,B)),M.add(N)}if(D===0&&s&&!v&&(y?v=Ft(()=>s(i)):(v=Ft(()=>s(So??(So=Er()))),v.f|=Sr)),D>M.size&&zd(),!y)if(A.set(R,M),X){for(const[ie,Se]of l)M.has(ie)||R.skip_effect(Se.e);R.oncommit(k),R.ondiscard(g)}else k(R);o(h)}),L={effect:z,items:l,pending:A,outrogroups:null,fallback:v};y=!1}function Zn(e){for(;e!==null&&(e.f&pr)===0;)e=e.next;return e}function qc(e,t,r,n,a){var B,ie,Se,Fe,E,j,J,re,Q;var s=(n&jd)!==0,i=t.length,l=e.items,d=Zn(e.effect.first),c,v=null,h,b=[],A=[],y,k,g,z;if(s)for(z=0;z<i;z+=1)y=t[z],k=a(y,z),g=l.get(k).e,(g.f&Sr)===0&&((ie=(B=g.nodes)==null?void 0:B.a)==null||ie.measure(),(h??(h=new Set)).add(g));for(z=0;z<i;z+=1){if(y=t[z],k=a(y,z),g=l.get(k).e,e.outrogroups!==null)for(const $ of e.outrogroups)$.pending.delete(g),$.done.delete(g);if((g.f&Sr)!==0)if(g.f^=Sr,g===d)ra(g,null,r);else{var L=v?v.next:d;g===e.effect.last&&(e.effect.last=g.prev),g.prev&&(g.prev.next=g.next),g.next&&(g.next.prev=g.prev),Fr(e,v,g),Fr(e,g,L),ra(g,L,r),v=g,b=[],A=[],d=Zn(v.next);continue}if((g.f&Nt)!==0&&(Rs(g),s&&((Fe=(Se=g.nodes)==null?void 0:Se.a)==null||Fe.unfix(),(h??(h=new Set)).delete(g))),g!==d){if(c!==void 0&&c.has(g)){if(b.length<A.length){var D=A[0],M;v=D.prev;var R=b[0],X=b[b.length-1];for(M=0;M<b.length;M+=1)ra(b[M],D,r);for(M=0;M<A.length;M+=1)c.delete(A[M]);Fr(e,R.prev,X.next),Fr(e,v,R),Fr(e,X,D),d=D,v=X,z-=1,b=[],A=[]}else c.delete(g),ra(g,d,r),Fr(e,g.prev,g.next),Fr(e,g,v===null?e.effect.first:v.next),Fr(e,v,g),v=g;continue}for(b=[],A=[];d!==null&&d!==g;)(c??(c=new Set)).add(d),A.push(d),d=Zn(d.next);if(d===null)continue}(g.f&Sr)===0&&b.push(g),v=g,d=Zn(g.next)}if(e.outrogroups!==null){for(const $ of e.outrogroups)$.pending.size===0&&(_s(e,Oa($.done)),(E=e.outrogroups)==null||E.delete($));e.outrogroups.size===0&&(e.outrogroups=null)}if(d!==null||c!==void 0){var P=[];if(c!==void 0)for(g of c)(g.f&Nt)===0&&P.push(g);for(;d!==null;)(d.f&Nt)===0&&d!==e.fallback&&P.push(d),d=Zn(d.next);var m=P.length;if(m>0){var N=(n&ni)!==0&&i===0?r:null;if(s){for(z=0;z<m;z+=1)(J=(j=P[z].nodes)==null?void 0:j.a)==null||J.measure();for(z=0;z<m;z+=1)(Q=(re=P[z].nodes)==null?void 0:re.a)==null||Q.fix()}Wc(e,P,N)}}s&&Cr(()=>{var $,C;if(h!==void 0)for(g of h)(C=($=g.nodes)==null?void 0:$.a)==null||C.apply()})}function Kc(e,t,r,n,a,s,i,l){var d=(i&Od)!==0?(i&Dd)===0?gc(r,!1,!1):Zr(r):null,c=(i&Rd)!==0?Zr(a):null;return{v:d,i:c,e:Ft(()=>(s(t,d??r,c??a,l),()=>{e.delete(n)}))}}function ra(e,t,r){if(e.nodes)for(var n=e.nodes.start,a=e.nodes.end,s=t&&(t.f&Sr)===0?t.nodes.start:r;n!==null;){var i=ha(n);if(s.before(n),n===a)return;n=i}}function Fr(e,t,r){t===null?e.effect.first=r:t.next=r,r===null?e.effect.last=t:r.prev=t}function Mo(e,t,r=!1,n=!1,a=!1){var s=e,i="";W(()=>{var l=we;if(i!==(i=t()??"")&&(l.nodes!==null&&($i(l.nodes.start,l.nodes.end),l.nodes=null),i!=="")){var d=r?oi:n?Wd:void 0,c=Ps(r?"svg":n?"math":"template",d);c.innerHTML=i;var v=r||n?c:c.content;if(yn(Lr(v),v.lastChild),r||n)for(;Lr(v);)s.before(Lr(v));else s.before(v)}})}function Ae(e,t,r,n,a){var l;var s=(l=t.$$slots)==null?void 0:l[r],i=!1;s===!0&&(s=t.children,i=!0),s===void 0||s(e,i?()=>n:n)}function ys(e,t,...r){var n=new Ds(e);ga(()=>{const a=t()??null;n.ensure(a,a&&(s=>a(s,...r)))},Xr)}function Yc(e,t,r,n,a,s){var i=null,l=e,d=new Ds(l,!1);ga(()=>{const c=t()||null;var v=oi;if(c===null){d.ensure(null,null);return}return d.ensure(c,h=>{if(c){if(i=Ps(c,v),yn(i,i),n){var b=i.appendChild(Er());n(i,b)}we.nodes.end=i,h.before(i)}}),()=>{}},Xr),Fa(()=>{})}function Jc(e,t){var r=void 0,n;Ci(()=>{r!==(r=t())&&(n&&(Mt(n),n=null),r&&(n=Ft(()=>{Is(()=>r(e))})))})}function Hi(e){var t,r,n="";if(typeof e=="string"||typeof e=="number")n+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(r=Hi(e[t]))&&(n&&(n+=" "),n+=r)}else for(r in e)e[r]&&(n&&(n+=" "),n+=r);return n}function Ui(){for(var e,t,r=0,n="",a=arguments.length;r<a;r++)(e=arguments[r])&&(t=Hi(e))&&(n&&(n+=" "),n+=t);return n}function Ue(e){return typeof e=="object"?Ui(e):e??""}const zo=[...` 	
\r\f \v\uFEFF`];function Xc(e,t,r){var n=e==null?"":""+e;if(r){for(var a of Object.keys(r))if(r[a])n=n?n+" "+a:a;else if(n.length)for(var s=a.length,i=0;(i=n.indexOf(a,i))>=0;){var l=i+s;(i===0||zo.includes(n[i-1]))&&(l===n.length||zo.includes(n[l]))?n=(i===0?"":n.substring(0,i))+n.substring(l+1):i=l}}return n===""?null:n}function Ao(e,t=!1){var r=t?" !important;":";",n="";for(var a of Object.keys(e)){var s=e[a];s!=null&&s!==""&&(n+=" "+a+": "+s+r)}return n}function Xa(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Zc(e,t){if(t){var r="",n,a;if(Array.isArray(t)?(n=t[0],a=t[1]):n=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var s=!1,i=0,l=!1,d=[];n&&d.push(...Object.keys(n).map(Xa)),a&&d.push(...Object.keys(a).map(Xa));var c=0,v=-1;const k=e.length;for(var h=0;h<k;h++){var b=e[h];if(l?b==="/"&&e[h-1]==="*"&&(l=!1):s?s===b&&(s=!1):b==="/"&&e[h+1]==="*"?l=!0:b==='"'||b==="'"?s=b:b==="("?i++:b===")"&&i--,!l&&s===!1&&i===0){if(b===":"&&v===-1)v=h;else if(b===";"||h===k-1){if(v!==-1){var A=Xa(e.substring(c,v).trim());if(!d.includes(A)){b!==";"&&h++;var y=e.substring(c,h).trim();r+=" "+y+";"}}c=h+1,v=-1}}}}return n&&(r+=Ao(n)),a&&(r+=Ao(a,!0)),r=r.trim(),r===""?null:r}return e==null?null:String(e)}function We(e,t,r,n,a,s){var i=e.__className;if(i!==r||i===void 0){var l=Xc(r,n,s);l==null?e.removeAttribute("class"):t?e.className=l:e.setAttribute("class",l),e.__className=r}else if(s&&a!==s)for(var d in s){var c=!!s[d];(a==null||c!==!!a[d])&&e.classList.toggle(d,c)}return s}function Za(e,t={},r,n){for(var a in r){var s=r[a];t[a]!==s&&(r[a]==null?e.style.removeProperty(a):e.style.setProperty(a,s,n))}}function Wi(e,t,r,n){var a=e.__style;if(a!==t){var s=Zc(t,n);s==null?e.removeAttribute("style"):e.style.cssText=s,e.__style=t}else n&&(Array.isArray(n)?(Za(e,r==null?void 0:r[0],n[0]),Za(e,r==null?void 0:r[1],n[1],"important")):Za(e,r,n));return n}function ws(e,t,r=!1){if(e.multiple){if(t==null)return;if(!zs(t))return Kd();for(var n of e.options)n.selected=t.includes(Co(n));return}for(n of e.options){var a=Co(n);if(xc(a,t)){n.selected=!0;return}}(!r||t!==void 0)&&(e.selectedIndex=-1)}function Qc(e){var t=new MutationObserver(()=>{ws(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Fa(()=>{t.disconnect()})}function Co(e){return"__value"in e?e.__value:e.value}const Qn=Symbol("class"),ea=Symbol("style"),qi=Symbol("is custom element"),Ki=Symbol("is html"),eu=ri?"option":"OPTION",tu=ri?"select":"SELECT";function ru(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function ca(e,t,r,n){var a=Yi(e);a[t]!==(a[t]=r)&&(t==="loading"&&(e[Sd]=r),r==null?e.removeAttribute(t):typeof r!="string"&&Ji(e).includes(t)?e[t]=r:e.setAttribute(t,r))}function nu(e,t,r,n,a=!1,s=!1){var i=Yi(e),l=i[qi],d=!i[Ki],c=t||{},v=e.nodeName===eu;for(var h in t)h in r||(r[h]=null);r.class?r.class=Ue(r.class):r[Qn]&&(r.class=null),r[ea]&&(r.style??(r.style=null));var b=Ji(e);for(const M in r){let R=r[M];if(v&&M==="value"&&R==null){e.value=e.__value="",c[M]=R;continue}if(M==="class"){var A=e.namespaceURI==="http://www.w3.org/1999/xhtml";We(e,A,R,n,t==null?void 0:t[Qn],r[Qn]),c[M]=R,c[Qn]=r[Qn];continue}if(M==="style"){Wi(e,R,t==null?void 0:t[ea],r[ea]),c[M]=R,c[ea]=r[ea];continue}var y=c[M];if(!(R===y&&!(R===void 0&&e.hasAttribute(M)))){c[M]=R;var k=M[0]+M[1];if(k!=="$$")if(k==="on"){const X={},P="$$"+M;let m=M.slice(2);var g=Lc(m);if(Nc(m)&&(m=m.slice(0,-7),X.capture=!0),!g&&y){if(R!=null)continue;e.removeEventListener(m,c[P],X),c[P]=null}if(g)U(m,e,R),tn([m]);else if(R!=null){let N=function(B){c[M].call(this,B)};var D=N;c[P]=Vi(m,e,N,X)}}else if(M==="style")ca(e,M,R);else if(M==="autofocus")wc(e,!!R);else if(!l&&(M==="__value"||M==="value"&&R!=null))e.value=e.__value=R;else if(M==="selected"&&v)ru(e,R);else{var z=M;d||(z=Rc(z));var L=z==="defaultValue"||z==="defaultChecked";if(R==null&&!l&&!L)if(i[M]=null,z==="value"||z==="checked"){let X=e;const P=t===void 0;if(z==="value"){let m=X.defaultValue;X.removeAttribute(z),X.defaultValue=m,X.value=X.__value=P?m:null}else{let m=X.defaultChecked;X.removeAttribute(z),X.defaultChecked=m,X.checked=P?m:!1}}else e.removeAttribute(M);else L||b.includes(z)&&(l||typeof R!="string")?(e[z]=R,z in i&&(i[z]=gt)):typeof R!="function"&&ca(e,z,R)}}}return c}function Pa(e,t,r=[],n=[],a=[],s,i=!1,l=!1){gi(a,r,n,d=>{var c=void 0,v={},h=e.nodeName===tu,b=!1;if(Ci(()=>{var y=t(...d.map(o)),k=nu(e,c,y,s,i,l);b&&h&&"value"in y&&ws(e,y.value);for(let z of Object.getOwnPropertySymbols(v))y[z]||Mt(v[z]);for(let z of Object.getOwnPropertySymbols(y)){var g=y[z];z.description===qd&&(!c||g!==c[z])&&(v[z]&&Mt(v[z]),v[z]=Ft(()=>Jc(e,()=>g))),k[z]=g}c=k}),h){var A=e;Is(()=>{ws(A,c.value,!0),Qc(A)})}b=!0})}function Yi(e){return e.__attributes??(e.__attributes={[qi]:e.nodeName.includes("-"),[Ki]:e.namespaceURI===si})}var Eo=new Map;function Ji(e){var t=e.getAttribute("is")||e.nodeName,r=Eo.get(t);if(r)return r;Eo.set(t,r=[]);for(var n,a=e,s=Element.prototype;s!==a;){n=Xo(a);for(var i in n)n[i].set&&r.push(i);a=As(a)}return r}function ia(e,t,r=t){var n=new WeakSet;Sc(e,"input",async a=>{var s=a?e.defaultValue:e.value;if(s=Qa(e)?es(s):s,r(s),me!==null&&n.add(me),await Pc(),s!==(s=t())){var i=e.selectionStart,l=e.selectionEnd,d=e.value.length;if(e.value=s??"",l!==null){var c=e.value.length;i===l&&l===d&&c>d?(e.selectionStart=c,e.selectionEnd=c):(e.selectionStart=i,e.selectionEnd=Math.min(l,c))}}}),_n(t)==null&&e.value&&(r(Qa(e)?es(e.value):e.value),me!==null&&n.add(me)),Ls(()=>{var a=t();if(e===document.activeElement){var s=is??me;if(n.has(s))return}Qa(e)&&a===es(e.value)||e.type==="date"&&!a&&!e.value||a!==e.value&&(e.value=a??"")})}function Qa(e){var t=e.type;return t==="number"||t==="range"}function es(e){return e===""?null:+e}function $o(e,t){return e===t||(e==null?void 0:e[Ar])===t}function Fs(e={},t,r,n){return Is(()=>{var a,s;return Ls(()=>{a=s,s=[],_n(()=>{e!==r(...s)&&(t(e,...s),a&&$o(r(...a),e)&&t(null,...a))})}),()=>{Cr(()=>{s&&$o(r(...s),e)&&t(null,...s)})}}),e}function au(e=!1){const t=bt,r=t.l.u;if(!r)return;let n=()=>on(t.s);if(e){let a=0,s={};const i=ma(()=>{let l=!1;const d=t.s;for(const c in d)d[c]!==s[c]&&(s[c]=d[c],l=!0);return l&&a++,a});n=()=>o(i)}r.b.length&&zc(()=>{To(t,n),as(r.b)}),Bn(()=>{const a=_n(()=>r.m.map(wd));return()=>{for(const s of a)typeof s=="function"&&s()}}),r.a.length&&Bn(()=>{To(t,n),as(r.a)})}function To(e,t){if(e.l.s)for(const r of e.l.s)o(r);t()}let ka=!1;function su(e){var t=ka;try{return ka=!1,[e(),ka]}finally{ka=t}}const ou={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function iu(e,t,r){return new Proxy({props:e,exclude:t},ou)}const lu={get(e,t){if(!e.exclude.includes(t))return o(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,r){if(!(t in e.special)){var n=we;try{sr(e.parent_effect),e.special[t]=Ke({get[t](){return e.props[t]}},t,ai)}finally{sr(n)}}return e.special[t](r),aa(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),aa(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function ke(e,t){return new Proxy({props:e,exclude:t,special:{},version:Zr(0),parent_effect:we},lu)}const du={get(e,t){let r=e.props.length;for(;r--;){let n=e.props[r];if(Xn(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n)return n[t]}},set(e,t,r){let n=e.props.length;for(;n--;){let a=e.props[n];Xn(a)&&(a=a());const s=qr(a,t);if(s&&s.set)return s.set(r),!0}return!1},getOwnPropertyDescriptor(e,t){let r=e.props.length;for(;r--;){let n=e.props[r];if(Xn(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n){const a=qr(n,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===Ar||t===ti)return!1;for(let r of e.props)if(Xn(r)&&(r=r()),r!=null&&t in r)return!0;return!1},ownKeys(e){const t=[];for(let r of e.props)if(Xn(r)&&(r=r()),!!r){for(const n in r)t.includes(n)||t.push(n);for(const n of Object.getOwnPropertySymbols(r))t.includes(n)||t.push(n)}return t}};function Ee(...e){return new Proxy({props:e},du)}function Ke(e,t,r,n){var D;var a=!va||(r&Bd)!==0,s=(r&Vd)!==0,i=(r&Gd)!==0,l=n,d=!0,c=()=>(d&&(d=!1,l=i?_n(n):n),l),v;if(s){var h=Ar in e||ti in e;v=((D=qr(e,t))==null?void 0:D.set)??(h&&t in e?M=>e[t]=M:void 0)}var b,A=!1;s?[b,A]=su(()=>e[t]):b=e[t],b===void 0&&n!==void 0&&(b=c(),v&&(a&&Td(),v(b)));var y;if(a?y=()=>{var M=e[t];return M===void 0?c():(d=!0,M)}:y=()=>{var M=e[t];return M!==void 0&&(l=void 0),M===void 0?l:M},a&&(r&ai)===0)return y;if(v){var k=e.$$legacy;return(function(M,R){return arguments.length>0?((!a||!R||k||A)&&v(R?y():M),M):y()})}var g=!1,z=((r&Fd)!==0?ma:$s)(()=>(g=!1,y()));s&&o(z);var L=we;return(function(M,R){if(arguments.length>0){const X=R?o(z):a&&s?ut(M):M;return u(z,X),g=!0,l!==void 0&&(l=X),M}return Qr&&g||(L.f&zr)!==0?z.v:o(z)})}const cu="5";var Jo;typeof window<"u"&&((Jo=window.__svelte??(window.__svelte={})).v??(Jo.v=new Set)).add(cu);const br="";async function uu(){const e=await fetch(`${br}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function Cn(e,t=null,r=null){const n={provider:e};t&&(n.model=t),r&&(n.api_key=r);const a=await fetch(`${br}/api/configure`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)});if(!a.ok)throw new Error("설정 실패");return a.json()}async function fu(e){const t=await fetch(`${br}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function vu(e,{onProgress:t,onDone:r,onError:n}){const a=new AbortController;return fetch(`${br}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:a.signal}).then(async s=>{if(!s.ok){n==null||n("다운로드 실패");return}const i=s.body.getReader(),l=new TextDecoder;let d="";for(;;){const{done:c,value:v}=await i.read();if(c)break;d+=l.decode(v,{stream:!0});const h=d.split(`
`);d=h.pop()||"";for(const b of h)if(b.startsWith("data:"))try{const A=JSON.parse(b.slice(5).trim());A.total&&A.completed!==void 0?t==null||t({total:A.total,completed:A.completed,status:A.status}):A.status&&(t==null||t({status:A.status}))}catch{}}r==null||r()}).catch(s=>{s.name!=="AbortError"&&(n==null||n(s.message))}),{abort:()=>a.abort()}}async function pu(){const e=await fetch(`${br}/api/oauth/authorize`);if(!e.ok)throw new Error("OAuth 인증 시작 실패");return e.json()}async function mu(){const e=await fetch(`${br}/api/oauth/status`);return e.ok?e.json():{done:!1}}async function hu(){const e=await fetch(`${br}/api/oauth/logout`,{method:"POST"});if(!e.ok)throw new Error("로그아웃 실패");return e.json()}async function gu(e){const t=await fetch(`${br}/api/export/modules/${encodeURIComponent(e)}`);if(!t.ok)throw new Error("모듈 목록 조회 실패");return t.json()}async function bu(e,t=null){let r=`${br}/api/export/excel/${encodeURIComponent(e)}`;t&&t.length>0&&(r+=`?modules=${encodeURIComponent(t.join(","))}`);const n=await fetch(r);if(!n.ok){const c=await n.json().catch(()=>({}));throw new Error(c.detail||"Excel 다운로드 실패")}const a=await n.blob(),i=(n.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),l=i?decodeURIComponent(i[1]):`${e}.xlsx`,d=document.createElement("a");return d.href=URL.createObjectURL(a),d.download=l,d.click(),URL.revokeObjectURL(d.href),l}async function xu(e){const t=await fetch(`${br}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}function _u(e,t,r={},{onMeta:n,onSnapshot:a,onContext:s,onSystemPrompt:i,onToolCall:l,onToolResult:d,onChunk:c,onDone:v,onError:h},b=null){const A={question:t,stream:!0,...r};e&&(A.company=e),b&&b.length>0&&(A.history=b);const y=new AbortController;return fetch(`${br}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(A),signal:y.signal}).then(async k=>{if(!k.ok){const R=await k.json().catch(()=>({}));h==null||h(R.detail||"스트리밍 실패");return}const g=k.body.getReader(),z=new TextDecoder;let L="",D=!1,M=null;for(;;){const{done:R,value:X}=await g.read();if(R)break;L+=z.decode(X,{stream:!0});const P=L.split(`
`);L=P.pop()||"";for(const m of P)if(m.startsWith("event:"))M=m.slice(6).trim();else if(m.startsWith("data:")&&M){const N=m.slice(5).trim();try{const B=JSON.parse(N);M==="meta"?n==null||n(B):M==="snapshot"?a==null||a(B):M==="context"?s==null||s(B):M==="system_prompt"?i==null||i(B):M==="tool_call"?l==null||l(B):M==="tool_result"?d==null||d(B):M==="chunk"?c==null||c(B.text):M==="error"?h==null||h(B.error,B.action,B.detail):M==="done"&&(D||(D=!0,v==null||v()))}catch{}M=null}}D||(D=!0,v==null||v())}).catch(k=>{k.name!=="AbortError"&&(h==null||h(k.message))}),{abort:()=>y.abort()}}const yu=(e,t)=>{const r=new Array(e.length+t.length);for(let n=0;n<e.length;n++)r[n]=e[n];for(let n=0;n<t.length;n++)r[e.length+n]=t[n];return r},wu=(e,t)=>({classGroupId:e,validator:t}),Xi=(e=new Map,t=null,r)=>({nextPart:e,validators:t,classGroupId:r}),Na="-",Po=[],ku="arbitrary..",Su=e=>{const t=zu(e),{conflictingClassGroups:r,conflictingClassGroupModifiers:n}=e;return{getClassGroupId:i=>{if(i.startsWith("[")&&i.endsWith("]"))return Mu(i);const l=i.split(Na),d=l[0]===""&&l.length>1?1:0;return Zi(l,d,t)},getConflictingClassGroupIds:(i,l)=>{if(l){const d=n[i],c=r[i];return d?c?yu(c,d):d:c||Po}return r[i]||Po}}},Zi=(e,t,r)=>{if(e.length-t===0)return r.classGroupId;const a=e[t],s=r.nextPart.get(a);if(s){const c=Zi(e,t+1,s);if(c)return c}const i=r.validators;if(i===null)return;const l=t===0?e.join(Na):e.slice(t).join(Na),d=i.length;for(let c=0;c<d;c++){const v=i[c];if(v.validator(l))return v.classGroupId}},Mu=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),r=t.indexOf(":"),n=t.slice(0,r);return n?ku+n:void 0})(),zu=e=>{const{theme:t,classGroups:r}=e;return Au(r,t)},Au=(e,t)=>{const r=Xi();for(const n in e){const a=e[n];Bs(a,r,n,t)}return r},Bs=(e,t,r,n)=>{const a=e.length;for(let s=0;s<a;s++){const i=e[s];Cu(i,t,r,n)}},Cu=(e,t,r,n)=>{if(typeof e=="string"){Eu(e,t,r);return}if(typeof e=="function"){$u(e,t,r,n);return}Tu(e,t,r,n)},Eu=(e,t,r)=>{const n=e===""?t:Qi(t,e);n.classGroupId=r},$u=(e,t,r,n)=>{if(Pu(e)){Bs(e(n),t,r,n);return}t.validators===null&&(t.validators=[]),t.validators.push(wu(r,e))},Tu=(e,t,r,n)=>{const a=Object.entries(e),s=a.length;for(let i=0;i<s;i++){const[l,d]=a[i];Bs(d,Qi(t,l),r,n)}},Qi=(e,t)=>{let r=e;const n=t.split(Na),a=n.length;for(let s=0;s<a;s++){const i=n[s];let l=r.nextPart.get(i);l||(l=Xi(),r.nextPart.set(i,l)),r=l}return r},Pu=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,Nu=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,r=Object.create(null),n=Object.create(null);const a=(s,i)=>{r[s]=i,t++,t>e&&(t=0,n=r,r=Object.create(null))};return{get(s){let i=r[s];if(i!==void 0)return i;if((i=n[s])!==void 0)return a(s,i),i},set(s,i){s in r?r[s]=i:a(s,i)}}},ks="!",No=":",Iu=[],Io=(e,t,r,n,a)=>({modifiers:e,hasImportantModifier:t,baseClassName:r,maybePostfixModifierPosition:n,isExternal:a}),Lu=e=>{const{prefix:t,experimentalParseClassName:r}=e;let n=a=>{const s=[];let i=0,l=0,d=0,c;const v=a.length;for(let k=0;k<v;k++){const g=a[k];if(i===0&&l===0){if(g===No){s.push(a.slice(d,k)),d=k+1;continue}if(g==="/"){c=k;continue}}g==="["?i++:g==="]"?i--:g==="("?l++:g===")"&&l--}const h=s.length===0?a:a.slice(d);let b=h,A=!1;h.endsWith(ks)?(b=h.slice(0,-1),A=!0):h.startsWith(ks)&&(b=h.slice(1),A=!0);const y=c&&c>d?c-d:void 0;return Io(s,A,b,y)};if(t){const a=t+No,s=n;n=i=>i.startsWith(a)?s(i.slice(a.length)):Io(Iu,!1,i,void 0,!0)}if(r){const a=n;n=s=>r({className:s,parseClassName:a})}return n},Ou=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((r,n)=>{t.set(r,1e6+n)}),r=>{const n=[];let a=[];for(let s=0;s<r.length;s++){const i=r[s],l=i[0]==="[",d=t.has(i);l||d?(a.length>0&&(a.sort(),n.push(...a),a=[]),n.push(i)):a.push(i)}return a.length>0&&(a.sort(),n.push(...a)),n}},Ru=e=>({cache:Nu(e.cacheSize),parseClassName:Lu(e),sortModifiers:Ou(e),...Su(e)}),ju=/\s+/,Du=(e,t)=>{const{parseClassName:r,getClassGroupId:n,getConflictingClassGroupIds:a,sortModifiers:s}=t,i=[],l=e.trim().split(ju);let d="";for(let c=l.length-1;c>=0;c-=1){const v=l[c],{isExternal:h,modifiers:b,hasImportantModifier:A,baseClassName:y,maybePostfixModifierPosition:k}=r(v);if(h){d=v+(d.length>0?" "+d:d);continue}let g=!!k,z=n(g?y.substring(0,k):y);if(!z){if(!g){d=v+(d.length>0?" "+d:d);continue}if(z=n(y),!z){d=v+(d.length>0?" "+d:d);continue}g=!1}const L=b.length===0?"":b.length===1?b[0]:s(b).join(":"),D=A?L+ks:L,M=D+z;if(i.indexOf(M)>-1)continue;i.push(M);const R=a(z,g);for(let X=0;X<R.length;++X){const P=R[X];i.push(D+P)}d=v+(d.length>0?" "+d:d)}return d},Fu=(...e)=>{let t=0,r,n,a="";for(;t<e.length;)(r=e[t++])&&(n=el(r))&&(a&&(a+=" "),a+=n);return a},el=e=>{if(typeof e=="string")return e;let t,r="";for(let n=0;n<e.length;n++)e[n]&&(t=el(e[n]))&&(r&&(r+=" "),r+=t);return r},Bu=(e,...t)=>{let r,n,a,s;const i=d=>{const c=t.reduce((v,h)=>h(v),e());return r=Ru(c),n=r.cache.get,a=r.cache.set,s=l,l(d)},l=d=>{const c=n(d);if(c)return c;const v=Du(d,r);return a(d,v),v};return s=i,(...d)=>s(Fu(...d))},Vu=[],ct=e=>{const t=r=>r[e]||Vu;return t.isThemeGetter=!0,t},tl=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,rl=/^\((?:(\w[\w-]*):)?(.+)\)$/i,Gu=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,Hu=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,Uu=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,Wu=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,qu=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,Ku=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,Br=e=>Gu.test(e),de=e=>!!e&&!Number.isNaN(Number(e)),Vr=e=>!!e&&Number.isInteger(Number(e)),ts=e=>e.endsWith("%")&&de(e.slice(0,-1)),Pr=e=>Hu.test(e),nl=()=>!0,Yu=e=>Uu.test(e)&&!Wu.test(e),Vs=()=>!1,Ju=e=>qu.test(e),Xu=e=>Ku.test(e),Zu=e=>!G(e)&&!H(e),Qu=e=>rn(e,ol,Vs),G=e=>tl.test(e),an=e=>rn(e,il,Yu),Lo=e=>rn(e,lf,de),ef=e=>rn(e,dl,nl),tf=e=>rn(e,ll,Vs),Oo=e=>rn(e,al,Vs),rf=e=>rn(e,sl,Xu),Sa=e=>rn(e,cl,Ju),H=e=>rl.test(e),ta=e=>kn(e,il),nf=e=>kn(e,ll),Ro=e=>kn(e,al),af=e=>kn(e,ol),sf=e=>kn(e,sl),Ma=e=>kn(e,cl,!0),of=e=>kn(e,dl,!0),rn=(e,t,r)=>{const n=tl.exec(e);return n?n[1]?t(n[1]):r(n[2]):!1},kn=(e,t,r=!1)=>{const n=rl.exec(e);return n?n[1]?t(n[1]):r:!1},al=e=>e==="position"||e==="percentage",sl=e=>e==="image"||e==="url",ol=e=>e==="length"||e==="size"||e==="bg-size",il=e=>e==="length",lf=e=>e==="number",ll=e=>e==="family-name",dl=e=>e==="number"||e==="weight",cl=e=>e==="shadow",df=()=>{const e=ct("color"),t=ct("font"),r=ct("text"),n=ct("font-weight"),a=ct("tracking"),s=ct("leading"),i=ct("breakpoint"),l=ct("container"),d=ct("spacing"),c=ct("radius"),v=ct("shadow"),h=ct("inset-shadow"),b=ct("text-shadow"),A=ct("drop-shadow"),y=ct("blur"),k=ct("perspective"),g=ct("aspect"),z=ct("ease"),L=ct("animate"),D=()=>["auto","avoid","all","avoid-page","page","left","right","column"],M=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],R=()=>[...M(),H,G],X=()=>["auto","hidden","clip","visible","scroll"],P=()=>["auto","contain","none"],m=()=>[H,G,d],N=()=>[Br,"full","auto",...m()],B=()=>[Vr,"none","subgrid",H,G],ie=()=>["auto",{span:["full",Vr,H,G]},Vr,H,G],Se=()=>[Vr,"auto",H,G],Fe=()=>["auto","min","max","fr",H,G],E=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],j=()=>["start","end","center","stretch","center-safe","end-safe"],J=()=>["auto",...m()],re=()=>[Br,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...m()],Q=()=>[Br,"screen","full","dvw","lvw","svw","min","max","fit",...m()],$=()=>[Br,"screen","full","lh","dvh","lvh","svh","min","max","fit",...m()],C=()=>[e,H,G],he=()=>[...M(),Ro,Oo,{position:[H,G]}],I=()=>["no-repeat",{repeat:["","x","y","space","round"]}],K=()=>["auto","cover","contain",af,Qu,{size:[H,G]}],oe=()=>[ts,ta,an],ge=()=>["","none","full",c,H,G],V=()=>["",de,ta,an],ne=()=>["solid","dashed","dotted","double"],be=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],xe=()=>[de,ts,Ro,Oo],Ce=()=>["","none",y,H,G],Ve=()=>["none",de,H,G],Le=()=>["none",de,H,G],Ye=()=>[de,H,G],_e=()=>[Br,"full",...m()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Pr],breakpoint:[Pr],color:[nl],container:[Pr],"drop-shadow":[Pr],ease:["in","out","in-out"],font:[Zu],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Pr],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Pr],shadow:[Pr],spacing:["px",de],text:[Pr],"text-shadow":[Pr],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",Br,G,H,g]}],container:["container"],columns:[{columns:[de,G,H,l]}],"break-after":[{"break-after":D()}],"break-before":[{"break-before":D()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:R()}],overflow:[{overflow:X()}],"overflow-x":[{"overflow-x":X()}],"overflow-y":[{"overflow-y":X()}],overscroll:[{overscroll:P()}],"overscroll-x":[{"overscroll-x":P()}],"overscroll-y":[{"overscroll-y":P()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:N()}],"inset-x":[{"inset-x":N()}],"inset-y":[{"inset-y":N()}],start:[{"inset-s":N(),start:N()}],end:[{"inset-e":N(),end:N()}],"inset-bs":[{"inset-bs":N()}],"inset-be":[{"inset-be":N()}],top:[{top:N()}],right:[{right:N()}],bottom:[{bottom:N()}],left:[{left:N()}],visibility:["visible","invisible","collapse"],z:[{z:[Vr,"auto",H,G]}],basis:[{basis:[Br,"full","auto",l,...m()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[de,Br,"auto","initial","none",G]}],grow:[{grow:["",de,H,G]}],shrink:[{shrink:["",de,H,G]}],order:[{order:[Vr,"first","last","none",H,G]}],"grid-cols":[{"grid-cols":B()}],"col-start-end":[{col:ie()}],"col-start":[{"col-start":Se()}],"col-end":[{"col-end":Se()}],"grid-rows":[{"grid-rows":B()}],"row-start-end":[{row:ie()}],"row-start":[{"row-start":Se()}],"row-end":[{"row-end":Se()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":Fe()}],"auto-rows":[{"auto-rows":Fe()}],gap:[{gap:m()}],"gap-x":[{"gap-x":m()}],"gap-y":[{"gap-y":m()}],"justify-content":[{justify:[...E(),"normal"]}],"justify-items":[{"justify-items":[...j(),"normal"]}],"justify-self":[{"justify-self":["auto",...j()]}],"align-content":[{content:["normal",...E()]}],"align-items":[{items:[...j(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...j(),{baseline:["","last"]}]}],"place-content":[{"place-content":E()}],"place-items":[{"place-items":[...j(),"baseline"]}],"place-self":[{"place-self":["auto",...j()]}],p:[{p:m()}],px:[{px:m()}],py:[{py:m()}],ps:[{ps:m()}],pe:[{pe:m()}],pbs:[{pbs:m()}],pbe:[{pbe:m()}],pt:[{pt:m()}],pr:[{pr:m()}],pb:[{pb:m()}],pl:[{pl:m()}],m:[{m:J()}],mx:[{mx:J()}],my:[{my:J()}],ms:[{ms:J()}],me:[{me:J()}],mbs:[{mbs:J()}],mbe:[{mbe:J()}],mt:[{mt:J()}],mr:[{mr:J()}],mb:[{mb:J()}],ml:[{ml:J()}],"space-x":[{"space-x":m()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":m()}],"space-y-reverse":["space-y-reverse"],size:[{size:re()}],"inline-size":[{inline:["auto",...Q()]}],"min-inline-size":[{"min-inline":["auto",...Q()]}],"max-inline-size":[{"max-inline":["none",...Q()]}],"block-size":[{block:["auto",...$()]}],"min-block-size":[{"min-block":["auto",...$()]}],"max-block-size":[{"max-block":["none",...$()]}],w:[{w:[l,"screen",...re()]}],"min-w":[{"min-w":[l,"screen","none",...re()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[i]},...re()]}],h:[{h:["screen","lh",...re()]}],"min-h":[{"min-h":["screen","lh","none",...re()]}],"max-h":[{"max-h":["screen","lh",...re()]}],"font-size":[{text:["base",r,ta,an]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[n,of,ef]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",ts,G]}],"font-family":[{font:[nf,tf,t]}],"font-features":[{"font-features":[G]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[a,H,G]}],"line-clamp":[{"line-clamp":[de,"none",H,Lo]}],leading:[{leading:[s,...m()]}],"list-image":[{"list-image":["none",H,G]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",H,G]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:C()}],"text-color":[{text:C()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...ne(),"wavy"]}],"text-decoration-thickness":[{decoration:[de,"from-font","auto",H,an]}],"text-decoration-color":[{decoration:C()}],"underline-offset":[{"underline-offset":[de,"auto",H,G]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:m()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",H,G]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",H,G]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:he()}],"bg-repeat":[{bg:I()}],"bg-size":[{bg:K()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},Vr,H,G],radial:["",H,G],conic:[Vr,H,G]},sf,rf]}],"bg-color":[{bg:C()}],"gradient-from-pos":[{from:oe()}],"gradient-via-pos":[{via:oe()}],"gradient-to-pos":[{to:oe()}],"gradient-from":[{from:C()}],"gradient-via":[{via:C()}],"gradient-to":[{to:C()}],rounded:[{rounded:ge()}],"rounded-s":[{"rounded-s":ge()}],"rounded-e":[{"rounded-e":ge()}],"rounded-t":[{"rounded-t":ge()}],"rounded-r":[{"rounded-r":ge()}],"rounded-b":[{"rounded-b":ge()}],"rounded-l":[{"rounded-l":ge()}],"rounded-ss":[{"rounded-ss":ge()}],"rounded-se":[{"rounded-se":ge()}],"rounded-ee":[{"rounded-ee":ge()}],"rounded-es":[{"rounded-es":ge()}],"rounded-tl":[{"rounded-tl":ge()}],"rounded-tr":[{"rounded-tr":ge()}],"rounded-br":[{"rounded-br":ge()}],"rounded-bl":[{"rounded-bl":ge()}],"border-w":[{border:V()}],"border-w-x":[{"border-x":V()}],"border-w-y":[{"border-y":V()}],"border-w-s":[{"border-s":V()}],"border-w-e":[{"border-e":V()}],"border-w-bs":[{"border-bs":V()}],"border-w-be":[{"border-be":V()}],"border-w-t":[{"border-t":V()}],"border-w-r":[{"border-r":V()}],"border-w-b":[{"border-b":V()}],"border-w-l":[{"border-l":V()}],"divide-x":[{"divide-x":V()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":V()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...ne(),"hidden","none"]}],"divide-style":[{divide:[...ne(),"hidden","none"]}],"border-color":[{border:C()}],"border-color-x":[{"border-x":C()}],"border-color-y":[{"border-y":C()}],"border-color-s":[{"border-s":C()}],"border-color-e":[{"border-e":C()}],"border-color-bs":[{"border-bs":C()}],"border-color-be":[{"border-be":C()}],"border-color-t":[{"border-t":C()}],"border-color-r":[{"border-r":C()}],"border-color-b":[{"border-b":C()}],"border-color-l":[{"border-l":C()}],"divide-color":[{divide:C()}],"outline-style":[{outline:[...ne(),"none","hidden"]}],"outline-offset":[{"outline-offset":[de,H,G]}],"outline-w":[{outline:["",de,ta,an]}],"outline-color":[{outline:C()}],shadow:[{shadow:["","none",v,Ma,Sa]}],"shadow-color":[{shadow:C()}],"inset-shadow":[{"inset-shadow":["none",h,Ma,Sa]}],"inset-shadow-color":[{"inset-shadow":C()}],"ring-w":[{ring:V()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:C()}],"ring-offset-w":[{"ring-offset":[de,an]}],"ring-offset-color":[{"ring-offset":C()}],"inset-ring-w":[{"inset-ring":V()}],"inset-ring-color":[{"inset-ring":C()}],"text-shadow":[{"text-shadow":["none",b,Ma,Sa]}],"text-shadow-color":[{"text-shadow":C()}],opacity:[{opacity:[de,H,G]}],"mix-blend":[{"mix-blend":[...be(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":be()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[de]}],"mask-image-linear-from-pos":[{"mask-linear-from":xe()}],"mask-image-linear-to-pos":[{"mask-linear-to":xe()}],"mask-image-linear-from-color":[{"mask-linear-from":C()}],"mask-image-linear-to-color":[{"mask-linear-to":C()}],"mask-image-t-from-pos":[{"mask-t-from":xe()}],"mask-image-t-to-pos":[{"mask-t-to":xe()}],"mask-image-t-from-color":[{"mask-t-from":C()}],"mask-image-t-to-color":[{"mask-t-to":C()}],"mask-image-r-from-pos":[{"mask-r-from":xe()}],"mask-image-r-to-pos":[{"mask-r-to":xe()}],"mask-image-r-from-color":[{"mask-r-from":C()}],"mask-image-r-to-color":[{"mask-r-to":C()}],"mask-image-b-from-pos":[{"mask-b-from":xe()}],"mask-image-b-to-pos":[{"mask-b-to":xe()}],"mask-image-b-from-color":[{"mask-b-from":C()}],"mask-image-b-to-color":[{"mask-b-to":C()}],"mask-image-l-from-pos":[{"mask-l-from":xe()}],"mask-image-l-to-pos":[{"mask-l-to":xe()}],"mask-image-l-from-color":[{"mask-l-from":C()}],"mask-image-l-to-color":[{"mask-l-to":C()}],"mask-image-x-from-pos":[{"mask-x-from":xe()}],"mask-image-x-to-pos":[{"mask-x-to":xe()}],"mask-image-x-from-color":[{"mask-x-from":C()}],"mask-image-x-to-color":[{"mask-x-to":C()}],"mask-image-y-from-pos":[{"mask-y-from":xe()}],"mask-image-y-to-pos":[{"mask-y-to":xe()}],"mask-image-y-from-color":[{"mask-y-from":C()}],"mask-image-y-to-color":[{"mask-y-to":C()}],"mask-image-radial":[{"mask-radial":[H,G]}],"mask-image-radial-from-pos":[{"mask-radial-from":xe()}],"mask-image-radial-to-pos":[{"mask-radial-to":xe()}],"mask-image-radial-from-color":[{"mask-radial-from":C()}],"mask-image-radial-to-color":[{"mask-radial-to":C()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":M()}],"mask-image-conic-pos":[{"mask-conic":[de]}],"mask-image-conic-from-pos":[{"mask-conic-from":xe()}],"mask-image-conic-to-pos":[{"mask-conic-to":xe()}],"mask-image-conic-from-color":[{"mask-conic-from":C()}],"mask-image-conic-to-color":[{"mask-conic-to":C()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:he()}],"mask-repeat":[{mask:I()}],"mask-size":[{mask:K()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",H,G]}],filter:[{filter:["","none",H,G]}],blur:[{blur:Ce()}],brightness:[{brightness:[de,H,G]}],contrast:[{contrast:[de,H,G]}],"drop-shadow":[{"drop-shadow":["","none",A,Ma,Sa]}],"drop-shadow-color":[{"drop-shadow":C()}],grayscale:[{grayscale:["",de,H,G]}],"hue-rotate":[{"hue-rotate":[de,H,G]}],invert:[{invert:["",de,H,G]}],saturate:[{saturate:[de,H,G]}],sepia:[{sepia:["",de,H,G]}],"backdrop-filter":[{"backdrop-filter":["","none",H,G]}],"backdrop-blur":[{"backdrop-blur":Ce()}],"backdrop-brightness":[{"backdrop-brightness":[de,H,G]}],"backdrop-contrast":[{"backdrop-contrast":[de,H,G]}],"backdrop-grayscale":[{"backdrop-grayscale":["",de,H,G]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[de,H,G]}],"backdrop-invert":[{"backdrop-invert":["",de,H,G]}],"backdrop-opacity":[{"backdrop-opacity":[de,H,G]}],"backdrop-saturate":[{"backdrop-saturate":[de,H,G]}],"backdrop-sepia":[{"backdrop-sepia":["",de,H,G]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":m()}],"border-spacing-x":[{"border-spacing-x":m()}],"border-spacing-y":[{"border-spacing-y":m()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",H,G]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[de,"initial",H,G]}],ease:[{ease:["linear","initial",z,H,G]}],delay:[{delay:[de,H,G]}],animate:[{animate:["none",L,H,G]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[k,H,G]}],"perspective-origin":[{"perspective-origin":R()}],rotate:[{rotate:Ve()}],"rotate-x":[{"rotate-x":Ve()}],"rotate-y":[{"rotate-y":Ve()}],"rotate-z":[{"rotate-z":Ve()}],scale:[{scale:Le()}],"scale-x":[{"scale-x":Le()}],"scale-y":[{"scale-y":Le()}],"scale-z":[{"scale-z":Le()}],"scale-3d":["scale-3d"],skew:[{skew:Ye()}],"skew-x":[{"skew-x":Ye()}],"skew-y":[{"skew-y":Ye()}],transform:[{transform:[H,G,"","none","gpu","cpu"]}],"transform-origin":[{origin:R()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:_e()}],"translate-x":[{"translate-x":_e()}],"translate-y":[{"translate-y":_e()}],"translate-z":[{"translate-z":_e()}],"translate-none":["translate-none"],accent:[{accent:C()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:C()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",H,G]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":m()}],"scroll-mx":[{"scroll-mx":m()}],"scroll-my":[{"scroll-my":m()}],"scroll-ms":[{"scroll-ms":m()}],"scroll-me":[{"scroll-me":m()}],"scroll-mbs":[{"scroll-mbs":m()}],"scroll-mbe":[{"scroll-mbe":m()}],"scroll-mt":[{"scroll-mt":m()}],"scroll-mr":[{"scroll-mr":m()}],"scroll-mb":[{"scroll-mb":m()}],"scroll-ml":[{"scroll-ml":m()}],"scroll-p":[{"scroll-p":m()}],"scroll-px":[{"scroll-px":m()}],"scroll-py":[{"scroll-py":m()}],"scroll-ps":[{"scroll-ps":m()}],"scroll-pe":[{"scroll-pe":m()}],"scroll-pbs":[{"scroll-pbs":m()}],"scroll-pbe":[{"scroll-pbe":m()}],"scroll-pt":[{"scroll-pt":m()}],"scroll-pr":[{"scroll-pr":m()}],"scroll-pb":[{"scroll-pb":m()}],"scroll-pl":[{"scroll-pl":m()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",H,G]}],fill:[{fill:["none",...C()]}],"stroke-w":[{stroke:[de,ta,an,Lo]}],stroke:[{stroke:["none",...C()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},cf=Bu(df);function qe(...e){return cf(Ui(e))}const Ss="dartlab-conversations",jo=50;function uf(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function ff(){try{const e=localStorage.getItem(Ss);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const vf=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function Do(e){return e.map(t=>({...t,messages:t.messages.map(r=>{if(r.role!=="assistant")return r;const n={};for(const[a,s]of Object.entries(r))vf.includes(a)||(n[a]=s);return n})}))}function Fo(e){try{const t={conversations:Do(e.conversations),activeId:e.activeId};localStorage.setItem(Ss,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:Do(e.conversations),activeId:e.activeId};localStorage.setItem(Ss,JSON.stringify(t))}catch{}}}}function pf(){const e=ff();let t=Y(ut(e.conversations)),r=Y(ut(e.activeId));o(r)&&!o(t).find(k=>k.id===o(r))&&u(r,null);let n=null;function a(){n&&clearTimeout(n),n=setTimeout(()=>{Fo({conversations:o(t),activeId:o(r)}),n=null},300)}function s(){n&&clearTimeout(n),n=null,Fo({conversations:o(t),activeId:o(r)})}function i(){return o(t).find(k=>k.id===o(r))||null}function l(){const k={id:uf(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return u(t,[k,...o(t)],!0),o(t).length>jo&&u(t,o(t).slice(0,jo),!0),u(r,k.id,!0),s(),k.id}function d(k){o(t).find(g=>g.id===k)&&(u(r,k,!0),s())}function c(k,g,z=null){const L=i();if(!L)return;const D={role:k,text:g};z&&(D.meta=z),L.messages=[...L.messages,D],L.updatedAt=Date.now(),L.title==="새 대화"&&k==="user"&&(L.title=g.length>30?g.slice(0,30)+"...":g),u(t,[...o(t)],!0),s()}function v(k){const g=i();if(!g||g.messages.length===0)return;const z=g.messages[g.messages.length-1];Object.assign(z,k),g.updatedAt=Date.now(),u(t,[...o(t)],!0),a()}function h(k){u(t,o(t).filter(g=>g.id!==k),!0),o(r)===k&&u(r,o(t).length>0?o(t)[0].id:null,!0),s()}function b(){const k=i();!k||k.messages.length===0||(k.messages=k.messages.slice(0,-1),k.updatedAt=Date.now(),u(t,[...o(t)],!0),s())}function A(k,g){const z=o(t).find(L=>L.id===k);z&&(z.title=g,u(t,[...o(t)],!0),s())}function y(){u(t,[],!0),u(r,null),s()}return{get conversations(){return o(t)},get activeId(){return o(r)},get active(){return i()},createConversation:l,setActive:d,addMessage:c,updateLastMessage:v,removeLastMessage:b,deleteConversation:h,updateTitle:A,clearAll:y,flush:s}}var mf=S("<a><!></a>"),hf=S("<button><!></button>");function gf(e,t){mr(t,!0);let r=Ke(t,"variant",3,"default"),n=Ke(t,"size",3,"default"),a=iu(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const s={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},i={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=ue(),d=q(l);{var c=h=>{var b=mf();Pa(b,y=>({class:y,...a}),[()=>qe("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",s[r()],i[n()],t.class)]);var A=f(b);ys(A,()=>t.children),p(h,b)},v=h=>{var b=hf();Pa(b,y=>({class:y,...a}),[()=>qe("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",s[r()],i[n()],t.class)]);var A=f(b);ys(A,()=>t.children),p(h,b)};T(d,h=>{t.href?h(c):h(v,-1)})}p(e,l),hr()}Zd();/**
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
 */const bf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const xf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const Bo=(...e)=>e.filter((t,r,n)=>!!t&&t.trim()!==""&&n.indexOf(t)===r).join(" ").trim();var _f=Vc("<svg><!><!></svg>");function $e(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]),n=ke(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);mr(t,!1);let a=Ke(t,"name",8,void 0),s=Ke(t,"color",8,"currentColor"),i=Ke(t,"size",8,24),l=Ke(t,"strokeWidth",8,2),d=Ke(t,"absoluteStrokeWidth",8,!1),c=Ke(t,"iconNode",24,()=>[]);au();var v=_f();Pa(v,(A,y,k)=>({...bf,...A,...n,width:i(),height:i(),stroke:s(),"stroke-width":y,class:k}),[()=>xf(n)?void 0:{"aria-hidden":"true"},()=>(on(d()),on(l()),on(i()),_n(()=>d()?Number(l())*24/Number(i()):l())),()=>(on(Bo),on(a()),on(r),_n(()=>Bo("lucide-icon","lucide",a()?`lucide-${a()}`:"",r.class)))]);var h=f(v);vt(h,1,c,ft,(A,y)=>{var k=ce(()=>Qo(o(y),2));let g=()=>o(k)[0],z=()=>o(k)[1];var L=ue(),D=q(L);Yc(D,g,!0,(M,R)=>{Pa(M,()=>({...z()}))}),p(A,L)});var b=x(h);Ae(b,t,"default",{}),p(e,v),hr()}function yf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];$e(e,Ee({name:"arrow-up"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Vo(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];$e(e,Ee({name:"brain"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function wf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M20 6 9 17l-5-5"}]];$e(e,Ee({name:"check"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function kf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m6 9 6 6 6-6"}]];$e(e,Ee({name:"chevron-down"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Sf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m18 15-6-6-6 6"}]];$e(e,Ee({name:"chevron-up"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function sn(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];$e(e,Ee({name:"circle-alert"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function rs(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];$e(e,Ee({name:"circle-check"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Mf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];$e(e,Ee({name:"clock"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function zf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];$e(e,Ee({name:"code"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Af(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];$e(e,Ee({name:"coffee"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function za(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];$e(e,Ee({name:"database"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function la(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];$e(e,Ee({name:"download"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Go(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];$e(e,Ee({name:"external-link"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function ul(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M8 13h2"}],["path",{d:"M14 13h2"}],["path",{d:"M8 17h2"}],["path",{d:"M14 17h2"}]];$e(e,Ee({name:"file-spreadsheet"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function $a(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];$e(e,Ee({name:"file-text"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Cf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];$e(e,Ee({name:"github"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Ho(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];$e(e,Ee({name:"key"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Kt(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];$e(e,Ee({name:"loader-circle"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Ef(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m10 17 5-5-5-5"}],["path",{d:"M15 12H3"}],["path",{d:"M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"}]];$e(e,Ee({name:"log-in"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function $f(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];$e(e,Ee({name:"log-out"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Tf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];$e(e,Ee({name:"menu"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Uo(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];$e(e,Ee({name:"message-square"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Pf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];$e(e,Ee({name:"panel-left-close"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Wo(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];$e(e,Ee({name:"plus"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Nf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];$e(e,Ee({name:"refresh-cw"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function fl(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];$e(e,Ee({name:"search"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function If(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];$e(e,Ee({name:"settings"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Lf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M21 10.656V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h12.344"}],["path",{d:"m9 11 3 3L22 4"}]];$e(e,Ee({name:"square-check-big"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function vl(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];$e(e,Ee({name:"square"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Of(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];$e(e,Ee({name:"terminal"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Rf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];$e(e,Ee({name:"trash-2"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function jf(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];$e(e,Ee({name:"triangle-alert"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Df(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];$e(e,Ee({name:"wrench"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}function Gs(e,t){const r=ke(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const n=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];$e(e,Ee({name:"x"},()=>r,{get iconNode(){return n},children:(a,s)=>{var i=ue(),l=q(i);Ae(l,t,"default",{}),p(a,i)},$$slots:{default:!0}}))}var Ff=S("<!> 새 대화",1),Bf=S('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-dl-bg-card border border-dl-border"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),Vf=S('<div role="button" tabindex="0"><!> <span class="flex-1 truncate"> </span> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),Gf=S('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),Hf=S('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/50 text-[10px] text-dl-text-dim"> </div>'),Uf=S('<div class="flex flex-col h-full min-w-[260px]"><div class="flex items-center gap-2.5 px-4 pt-4 pb-2"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <span class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</span></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 space-y-4"></div> <!></div>'),Wf=S("<button><!></button>"),qf=S('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),Kf=S("<aside><!></aside>");function Yf(e,t){mr(t,!0);let r=Ke(t,"conversations",19,()=>[]),n=Ke(t,"activeId",3,null),a=Ke(t,"open",3,!0),s=Ke(t,"version",3,""),i=Y("");function l(y){const k=new Date().setHours(0,0,0,0),g=k-864e5,z=k-7*864e5,L={오늘:[],어제:[],"이번 주":[],이전:[]};for(const M of y)M.updatedAt>=k?L.오늘.push(M):M.updatedAt>=g?L.어제.push(M):M.updatedAt>=z?L["이번 주"].push(M):L.이전.push(M);const D=[];for(const[M,R]of Object.entries(L))R.length>0&&D.push({label:M,items:R});return D}let d=ce(()=>o(i).trim()?r().filter(y=>y.title.toLowerCase().includes(o(i).toLowerCase())):r()),c=ce(()=>l(o(d)));var v=Kf(),h=f(v);{var b=y=>{var k=Uf(),g=x(f(k),2),z=f(g);gf(z,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(P,m)=>{var N=Ff(),B=q(N);Wo(B,{size:16}),p(P,N)},$$slots:{default:!0}});var L=x(g,2);{var D=P=>{var m=Bf(),N=f(m),B=f(N);fl(B,{size:12,class:"text-dl-text-dim flex-shrink-0"});var ie=x(B,2);ia(ie,()=>o(i),Se=>u(i,Se)),p(P,m)};T(L,P=>{r().length>3&&P(D)})}var M=x(L,2);vt(M,21,()=>o(c),ft,(P,m)=>{var N=Gf(),B=f(N),ie=f(B),Se=x(B,2);vt(Se,17,()=>o(m).items,ft,(Fe,E)=>{var j=Vf(),J=f(j);Uo(J,{size:14,class:"flex-shrink-0 opacity-50"});var re=x(J,2),Q=f(re),$=x(re,2),C=f($);Rf(C,{size:12}),W(he=>{We(j,1,he),Z(Q,o(E).title)},[()=>Ue(qe("w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-[13px] transition-colors group cursor-pointer",o(E).id===n()?"bg-dl-bg-card text-dl-text border-l-2 border-dl-primary":"text-dl-text-muted hover:bg-dl-bg-card/50 hover:text-dl-text border-l-2 border-transparent"))]),U("click",j,()=>{var he;return(he=t.onSelect)==null?void 0:he.call(t,o(E).id)}),U("keydown",j,he=>{var I;he.key==="Enter"&&((I=t.onSelect)==null||I.call(t,o(E).id))}),U("click",$,he=>{var I;he.stopPropagation(),(I=t.onDelete)==null||I.call(t,o(E).id)}),p(Fe,j)}),W(()=>Z(ie,o(m).label)),p(P,N)});var R=x(M,2);{var X=P=>{var m=Hf(),N=f(m);W(()=>Z(N,`DartLab v${s()??""}`)),p(P,m)};T(R,P=>{s()&&P(X)})}p(y,k)},A=y=>{var k=qf(),g=x(f(k),2),z=f(g);Wo(z,{size:18});var L=x(g,2);vt(L,21,()=>r().slice(0,10),ft,(D,M)=>{var R=Wf(),X=f(R);Uo(X,{size:16}),W(P=>{We(R,1,P),ca(R,"title",o(M).title)},[()=>Ue(qe("p-2 rounded-lg transition-colors w-full flex justify-center",o(M).id===n()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),U("click",R,()=>{var P;return(P=t.onSelect)==null?void 0:P.call(t,o(M).id)}),p(D,R)}),U("click",g,function(...D){var M;(M=t.onNewChat)==null||M.apply(this,D)}),p(y,k)};T(h,y=>{a()?y(b):y(A,-1)})}W(y=>We(v,1,y),[()=>Ue(qe("flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",a()?"w-[260px]":"w-[52px]"))]),p(e,v),hr()}tn(["click","keydown"]);var Jf=S('<button class="send-btn active"><!></button>'),Xf=S("<button><!></button>"),Zf=S('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),Qf=S('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),ev=S('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),tv=S('<div class="relative"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function pl(e,t){mr(t,!0);let r=Ke(t,"inputText",15,""),n=Ke(t,"isLoading",3,!1),a=Ke(t,"large",3,!1),s=Ke(t,"placeholder",3,"메시지를 입력하세요..."),i=Y(ut([])),l=Y(!1),d=Y(-1),c=null,v=Y(void 0);function h(m){var N;if(o(l)&&o(i).length>0){if(m.key==="ArrowDown"){m.preventDefault(),u(d,(o(d)+1)%o(i).length);return}if(m.key==="ArrowUp"){m.preventDefault(),u(d,o(d)<=0?o(i).length-1:o(d)-1,!0);return}if(m.key==="Enter"&&o(d)>=0){m.preventDefault(),y(o(i)[o(d)]);return}if(m.key==="Escape"){u(l,!1),u(d,-1);return}}m.key==="Enter"&&!m.shiftKey&&(m.preventDefault(),u(l,!1),(N=t.onSend)==null||N.call(t))}function b(m){m.target.style.height="auto",m.target.style.height=Math.min(m.target.scrollHeight,200)+"px"}function A(m){b(m);const N=r();c&&clearTimeout(c),N.length>=2&&!/\s/.test(N.slice(-1))?c=setTimeout(async()=>{var B;try{const ie=await xu(N.trim());((B=ie.results)==null?void 0:B.length)>0?(u(i,ie.results.slice(0,6),!0),u(l,!0),u(d,-1)):u(l,!1)}catch{u(l,!1)}},300):u(l,!1)}function y(m){r(`${m.corpName} `),u(l,!1),u(d,-1),o(v)&&o(v).focus()}function k(){setTimeout(()=>{u(l,!1)},200)}var g=tv(),z=f(g),L=f(z);Fs(L,m=>u(v,m),()=>o(v));var D=x(L,2);{var M=m=>{var N=Jf(),B=f(N);vl(B,{size:14}),U("click",N,function(...ie){var Se;(Se=t.onStop)==null||Se.apply(this,ie)}),p(m,N)},R=m=>{var N=Xf(),B=f(N);{let ie=ce(()=>a()?18:16);yf(B,{get size(){return o(ie)},strokeWidth:2.5})}W((ie,Se)=>{We(N,1,ie),N.disabled=Se},[()=>Ue(qe("send-btn",r().trim()&&"active")),()=>!r().trim()]),U("click",N,()=>{var ie;u(l,!1),(ie=t.onSend)==null||ie.call(t)}),p(m,N)};T(D,m=>{n()&&t.onStop?m(M):m(R,-1)})}var X=x(z,2);{var P=m=>{var N=ev();vt(N,21,()=>o(i),ft,(B,ie,Se)=>{var Fe=Qf(),E=f(Fe);fl(E,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var j=x(E,2),J=f(j),re=f(J),Q=x(J,2),$=f(Q),C=x(j,2);{var he=I=>{var K=Zf(),oe=f(K);W(()=>Z(oe,o(ie).sector)),p(I,K)};T(C,I=>{o(ie).sector&&I(he)})}W(I=>{We(Fe,1,I),Z(re,o(ie).corpName),Z($,`${o(ie).stockCode??""} · ${(o(ie).market||"")??""}`)},[()=>Ue(qe("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",Se===o(d)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),U("mousedown",Fe,()=>y(o(ie))),Ta("mouseenter",Fe,()=>{u(d,Se,!0)}),p(B,Fe)}),p(m,N)};T(X,m=>{o(l)&&o(i).length>0&&m(P)})}W(m=>{We(z,1,m),ca(L,"placeholder",s())},[()=>Ue(qe("input-box",a()&&"large"))]),U("keydown",L,h),U("input",L,A),Ta("blur",L,k),ia(L,r),p(e,g),hr()}tn(["keydown","input","click","mousedown"]);var rv=S('<button class="text-left px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/50 text-[13px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-bg-card hover:-translate-y-0.5 hover:shadow-lg hover:shadow-dl-primary/5 transition-all duration-200 cursor-pointer"> </button>'),nv=S('<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[620px] flex flex-col items-center"><img src="/avatar.png" alt="DartLab" class="w-16 h-16 rounded-full mb-5" style="filter: drop-shadow(0 0 24px rgba(234,70,71,0.3));"/> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-8">종목명과 질문을 입력하거나, 자유롭게 대화하세요</p> <!> <div class="grid grid-cols-2 gap-2.5 mt-6 w-full max-w-[520px]"></div></div></div>');function av(e,t){mr(t,!0);let r=Ke(t,"inputText",15,"");const n=["삼성전자 재무 건전성 분석해줘","LG에너지솔루션 배당 추세는?","카카오 부채 리스크 평가해줘","현대차 영업이익률 추이 분석"];function a(c){r(c)}var s=nv(),i=f(s),l=x(f(i),6);pl(l,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get inputText(){return r()},set inputText(c){r(c)}});var d=x(l,2);vt(d,21,()=>n,ft,(c,v)=>{var h=rv(),b=f(h);W(()=>Z(b,o(v))),U("click",h,()=>a(o(v))),p(c,h)}),p(e,s),hr()}tn(["click"]);var sv=S("<span><!></span>");function qo(e,t){mr(t,!0);let r=Ke(t,"variant",3,"default");const n={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var a=sv(),s=f(a);ys(s,()=>t.children),W(i=>We(a,1,i),[()=>Ue(qe("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",n[r()],t.class))]),p(e,a),hr()}var ov=S('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),iv=S('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),lv=S('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),dv=S('<div class="flex flex-wrap items-center gap-1.5 mb-2"><!> <!> <!></div>'),cv=S('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),uv=S('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),fv=S('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),vv=S('<button class="mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),pv=S('<span class="flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-dl-accent/30 bg-dl-accent/[0.06] text-[11px] text-dl-accent"><!> </span>'),mv=S('<div class="mb-3"><div class="flex flex-wrap items-center gap-1.5"></div></div>'),hv=S('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),gv=S('<!> <span class="text-dl-text-dim"> </span>',1),bv=S('<div class="flex items-center gap-2 text-[11px]"><!></div>'),xv=S('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),_v=S('<div class="flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),yv=S('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),wv=S('<span class="text-dl-accent/60"> </span>'),kv=S('<span class="text-dl-success/60"> </span>'),Sv=S('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),Mv=S('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),zv=S('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),Av=S('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),Cv=S('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),Ev=S("<!>  <div><!></div> <!>",1),$v=S('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),Tv=S('<span class="text-[10px] text-dl-text-dim"> </span>'),Pv=S('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),Nv=S("<button> </button>"),Iv=S('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),Lv=S("<button>시스템 프롬프트</button>"),Ov=S("<button>LLM 입력</button>"),Rv=S('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),jv=S('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),Dv=S('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),Fv=S('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Bv=S("<!> <!>",1);function Vv(e,t){mr(t,!0);let r=Y(null),n=Y("context"),a=Y("raw"),s=ce(()=>{var E,j,J,re,Q,$;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((E=t.message.toolEvents)==null?void 0:E.length)>0){const C=[...t.message.toolEvents].reverse().find(I=>I.type==="call"),he=((j=C==null?void 0:C.arguments)==null?void 0:j.module)||((J=C==null?void 0:C.arguments)==null?void 0:J.keyword)||"";return`도구 실행 중 — ${(C==null?void 0:C.name)||""}${he?` (${he})`:""}`}if(((re=t.message.contexts)==null?void 0:re.length)>0){const C=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(C==null?void 0:C.label)||(C==null?void 0:C.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(Q=t.message.meta)!=null&&Q.company?`${t.message.meta.company} 데이터 검색 중`:($=t.message.meta)!=null&&$.includedModules?"분석 모듈 선택 완료":"생각 중"}),i=ce(()=>{var E;return t.message.company||((E=t.message.meta)==null?void 0:E.company)||null}),l=ce(()=>{var E,j;return t.message.systemPrompt||((E=t.message.contexts)==null?void 0:E.length)>0||((j=t.message.meta)==null?void 0:j.includedModules)}),d=ce(()=>{var j;const E=(j=t.message.meta)==null?void 0:j.dataYearRange;return E?typeof E=="string"?E:E.min_year&&E.max_year?`${E.min_year}~${E.max_year}년`:null:null});function c(E){if(!E)return 0;const j=(E.match(/[\uac00-\ud7af]/g)||[]).length,J=E.length-j;return Math.round(j*1.5+J/3.5)}function v(E){return E>=1e3?(E/1e3).toFixed(1)+"k":String(E)}let h=ce(()=>{var j;let E=0;if(t.message.systemPrompt&&(E+=c(t.message.systemPrompt)),t.message.userContent)E+=c(t.message.userContent);else if(((j=t.message.contexts)==null?void 0:j.length)>0)for(const J of t.message.contexts)E+=c(J.text);return E}),b=ce(()=>c(t.message.text));function A(E){const j=E.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(j)||j==="-"||j==="0"}function y(E){if(!E)return"";let j=[],J=[],re=E.replace(/```(\w*)\n([\s\S]*?)```/g,($,C,he)=>{const I=j.length;return j.push(he.trimEnd()),`
%%CODE_${I}%%
`});re=re.replace(/((?:^\|.+\|$\n?)+)/gm,$=>{const C=$.trim().split(`
`).filter(V=>V.trim());let he=null,I=-1,K=[];for(let V=0;V<C.length;V++)if(C[V].slice(1,-1).split("|").map(be=>be.trim()).every(be=>/^[\-:]+$/.test(be))){I=V;break}I>0?(he=C[I-1],K=C.slice(I+1)):(I===0||(he=C[0]),K=C.slice(1));let oe="<table>";if(he){const V=he.slice(1,-1).split("|").map(ne=>ne.trim());oe+="<thead><tr>"+V.map(ne=>`<th>${ne.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(K.length>0){oe+="<tbody>";for(const V of K){const ne=V.slice(1,-1).split("|").map(be=>be.trim());oe+="<tr>"+ne.map(be=>{let xe=be.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${A(be)?' class="num"':""}>${xe}</td>`}).join("")+"</tr>"}oe+="</tbody>"}oe+="</table>";let ge=J.length;return J.push(oe),`
%%TABLE_${ge}%%
`});let Q=re.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");Q=Q.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,$=>"<ul>"+$.replace(/<br>/g,"")+"</ul>");for(let $=0;$<J.length;$++)Q=Q.replace(`%%TABLE_${$}%%`,J[$]);for(let $=0;$<j.length;$++){const C=j[$].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");Q=Q.replace(`%%CODE_${$}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${$}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${C}</code></pre></div>`)}return Q=Q.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),($,C)=>C.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+Q+"</p>"}let k=Y(void 0);const g='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',z='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function L(E){var Q;const j=E.target.closest(".code-copy-btn");if(!j)return;const J=j.closest(".code-block-wrap"),re=((Q=J==null?void 0:J.querySelector("code"))==null?void 0:Q.textContent)||"";navigator.clipboard.writeText(re).then(()=>{j.innerHTML=z,setTimeout(()=>{j.innerHTML=g},2e3)})}function D(E){u(r,E,!0),u(n,"context"),u(a,"rendered")}function M(){u(r,0),u(n,"system"),u(a,"raw")}function R(){u(r,0),u(n,"snapshot")}function X(){u(r,null)}let P=ce(()=>{var j,J,re;if(!t.message.loading)return[];const E=[];return(j=t.message.meta)!=null&&j.company&&E.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&E.push({label:"핵심 수치 확인",done:!0}),(J=t.message.meta)!=null&&J.includedModules&&E.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((re=t.message.contexts)==null?void 0:re.length)>0&&E.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&E.push({label:"프롬프트 조립",done:!0}),t.message.text?E.push({label:"응답 작성 중",done:!1}):E.push({label:o(s)||"준비 중",done:!1}),E});var m=Bv(),N=q(m);{var B=E=>{var j=ov(),J=x(f(j),2),re=f(J),Q=f(re);W(()=>Z(Q,t.message.text)),p(E,j)},ie=E=>{var j=$v(),J=x(f(j),2),re=f(J);{var Q=V=>{var ne=dv(),be=f(ne);{var xe=se=>{qo(se,{variant:"muted",children:(fe,Te)=>{var te=oa();W(()=>Z(te,o(i))),p(fe,te)},$$slots:{default:!0}})};T(be,se=>{o(i)&&se(xe)})}var Ce=x(be,2);{var Ve=se=>{qo(se,{variant:"accent",children:(fe,Te)=>{var te=oa();W(()=>Z(te,o(d))),p(fe,te)},$$slots:{default:!0}})};T(Ce,se=>{o(d)&&se(Ve)})}var Le=x(Ce,2);{var Ye=se=>{var fe=ue(),Te=q(fe);vt(Te,17,()=>t.message.contexts,ft,(te,Je,mt)=>{var xt=iv(),At=f(xt);za(At,{size:10,class:"flex-shrink-0"});var Vt=x(At);W(()=>Z(Vt,` ${(o(Je).label||o(Je).module)??""}`)),U("click",xt,()=>D(mt)),p(te,xt)}),p(se,fe)},_e=se=>{var fe=lv(),Te=f(fe);za(Te,{size:10,class:"flex-shrink-0"});var te=x(Te);W(()=>Z(te,` 모듈 ${t.message.meta.includedModules.length??""}개`)),p(se,fe)};T(Le,se=>{var fe,Te,te;((fe=t.message.contexts)==null?void 0:fe.length)>0?se(Ye):((te=(Te=t.message.meta)==null?void 0:Te.includedModules)==null?void 0:te.length)>0&&se(_e,1)})}p(V,ne)};T(re,V=>{var ne,be;(o(i)||o(d)||((ne=t.message.contexts)==null?void 0:ne.length)>0||(be=t.message.meta)!=null&&be.includedModules)&&V(Q)})}var $=x(re,2);{var C=V=>{var ne=vv(),be=f(ne);vt(be,21,()=>t.message.snapshot.items,ft,(Ve,Le)=>{const Ye=ce(()=>o(Le).status==="good"?"text-dl-success":o(Le).status==="danger"?"text-dl-primary-light":o(Le).status==="caution"?"text-amber-400":"text-dl-text");var _e=cv(),se=f(_e),fe=f(se),Te=x(se,2),te=f(Te);W(Je=>{Z(fe,o(Le).label),We(Te,1,Je),Z(te,o(Le).value)},[()=>Ue(qe("text-[14px] font-semibold leading-snug mt-0.5",o(Ye)))]),p(Ve,_e)});var xe=x(be,2);{var Ce=Ve=>{var Le=fv();vt(Le,21,()=>t.message.snapshot.warnings,ft,(Ye,_e)=>{var se=uv(),fe=f(se);jf(fe,{size:10});var Te=x(fe);W(()=>Z(Te,` ${o(_e)??""}`)),p(Ye,se)}),p(Ve,Le)};T(xe,Ve=>{var Le;((Le=t.message.snapshot.warnings)==null?void 0:Le.length)>0&&Ve(Ce)})}U("click",ne,R),p(V,ne)};T($,V=>{var ne,be;((be=(ne=t.message.snapshot)==null?void 0:ne.items)==null?void 0:be.length)>0&&V(C)})}var he=x($,2);{var I=V=>{var ne=mv(),be=f(ne);vt(be,21,()=>t.message.toolEvents,ft,(xe,Ce)=>{var Ve=ue(),Le=q(Ve);{var Ye=_e=>{const se=ce(()=>{var Je,mt,xt,At;return((Je=o(Ce).arguments)==null?void 0:Je.module)||((mt=o(Ce).arguments)==null?void 0:mt.keyword)||((xt=o(Ce).arguments)==null?void 0:xt.engine)||((At=o(Ce).arguments)==null?void 0:At.name)||""});var fe=pv(),Te=f(fe);Df(Te,{size:11});var te=x(Te);W(()=>Z(te,` ${o(Ce).name??""}${o(se)?`: ${o(se)}`:""}`)),p(_e,fe)};T(Le,_e=>{o(Ce).type==="call"&&_e(Ye)})}p(xe,Ve)}),p(V,ne)};T(he,V=>{var ne;((ne=t.message.toolEvents)==null?void 0:ne.length)>0&&V(I)})}var K=x(he,2);{var oe=V=>{var ne=xv(),be=f(ne);vt(be,21,()=>o(P),ft,(xe,Ce)=>{var Ve=bv(),Le=f(Ve);{var Ye=se=>{var fe=hv(),Te=x(q(fe),2),te=f(Te);W(()=>Z(te,o(Ce).label)),p(se,fe)},_e=se=>{var fe=gv(),Te=q(fe);Kt(Te,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var te=x(Te,2),Je=f(te);W(()=>Z(Je,o(Ce).label)),p(se,fe)};T(Le,se=>{o(Ce).done?se(Ye):se(_e,-1)})}p(xe,Ve)}),p(V,ne)},ge=V=>{var ne=Ev(),be=q(ne);{var xe=_e=>{var se=_v(),fe=f(se);Kt(fe,{size:12,class:"animate-spin flex-shrink-0"});var Te=x(fe,2),te=f(Te);W(()=>Z(te,o(s))),p(_e,se)};T(be,_e=>{t.message.loading&&_e(xe)})}var Ce=x(be,2),Ve=f(Ce);Mo(Ve,()=>y(t.message.text)),Fs(Ce,_e=>u(k,_e),()=>o(k));var Le=x(Ce,2);{var Ye=_e=>{var se=Cv(),fe=f(se);{var Te=Pe=>{var Ge=yv(),Xe=f(Ge);Mf(Xe,{size:10});var F=x(Xe);W(()=>Z(F,` ${t.message.duration??""}초`)),p(Pe,Ge)};T(fe,Pe=>{t.message.duration&&Pe(Te)})}var te=x(fe,2);{var Je=Pe=>{var Ge=Sv(),Xe=f(Ge);{var F=Ne=>{var st=wv(),Ct=f(st);W($t=>Z(Ct,`↑${$t??""}`),[()=>v(o(h))]),p(Ne,st)};T(Xe,Ne=>{o(h)>0&&Ne(F)})}var ve=x(Xe,2);{var je=Ne=>{var st=kv(),Ct=f(st);W($t=>Z(Ct,`↓${$t??""}`),[()=>v(o(b))]),p(Ne,st)};T(ve,Ne=>{o(b)>0&&Ne(je)})}p(Pe,Ge)};T(te,Pe=>{(o(h)>0||o(b)>0)&&Pe(Je)})}var mt=x(te,2);{var xt=Pe=>{var Ge=Mv(),Xe=f(Ge);Nf(Xe,{size:10}),U("click",Ge,()=>{var F;return(F=t.onRegenerate)==null?void 0:F.call(t)}),p(Pe,Ge)};T(mt,Pe=>{t.onRegenerate&&Pe(xt)})}var At=x(mt,2);{var Vt=Pe=>{var Ge=zv(),Xe=f(Ge);Vo(Xe,{size:10}),U("click",Ge,M),p(Pe,Ge)};T(At,Pe=>{t.message.systemPrompt&&Pe(Vt)})}var Yt=x(At,2);{var It=Pe=>{var Ge=Av(),Xe=f(Ge);$a(Xe,{size:10});var F=x(Xe);W((ve,je)=>Z(F,` LLM 입력 (${ve??""}자 · ~${je??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>v(c(t.message.userContent))]),U("click",Ge,()=>{u(r,0),u(n,"userContent"),u(a,"raw")}),p(Pe,Ge)};T(Yt,Pe=>{t.message.userContent&&Pe(It)})}p(_e,se)};T(Le,_e=>{!t.message.loading&&(t.message.duration||o(l)||t.onRegenerate)&&_e(Ye)})}W(_e=>We(Ce,1,_e),[()=>Ue(qe("prose-dartlab text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),U("click",Ce,L),p(V,ne)};T(K,V=>{t.message.loading&&!t.message.text?V(oe):V(ge,-1)})}p(E,j)};T(N,E=>{t.message.role==="user"?E(B):E(ie,-1)})}var Se=x(N,2);{var Fe=E=>{const j=ce(()=>o(n)==="system"),J=ce(()=>o(n)==="userContent"),re=ce(()=>o(n)==="context"),Q=ce(()=>o(n)==="snapshot"),$=ce(()=>{var F;return o(re)?(F=t.message.contexts)==null?void 0:F[o(r)]:null}),C=ce(()=>{var F,ve;return o(Q)?"핵심 수치 (원본 데이터)":o(j)?"시스템 프롬프트":o(J)?"LLM에 전달된 입력":((F=o($))==null?void 0:F.label)||((ve=o($))==null?void 0:ve.module)||""}),he=ce(()=>{var F;return o(Q)?JSON.stringify(t.message.snapshot,null,2):o(j)?t.message.systemPrompt:o(J)?t.message.userContent:(F=o($))==null?void 0:F.text});var I=Fv(),K=f(I),oe=f(K),ge=f(oe),V=f(ge),ne=f(V);{var be=F=>{za(F,{size:15,class:"text-dl-success flex-shrink-0"})},xe=F=>{Vo(F,{size:15,class:"text-dl-primary-light flex-shrink-0"})},Ce=F=>{$a(F,{size:15,class:"text-dl-accent flex-shrink-0"})},Ve=F=>{za(F,{size:15,class:"flex-shrink-0"})};T(ne,F=>{o(Q)?F(be):o(j)?F(xe,1):o(J)?F(Ce,2):F(Ve,-1)})}var Le=x(ne,2),Ye=f(Le),_e=x(Le,2);{var se=F=>{var ve=Tv(),je=f(ve);W(Ne=>Z(je,`(${Ne??""}자)`),[()=>{var Ne,st;return(st=(Ne=o(he))==null?void 0:Ne.length)==null?void 0:st.toLocaleString()}]),p(F,ve)};T(_e,F=>{o(j)&&F(se)})}var fe=x(V,2),Te=f(fe);{var te=F=>{var ve=Pv(),je=f(ve),Ne=f(je);$a(Ne,{size:11});var st=x(je,2),Ct=f(st);zf(Ct,{size:11}),W(($t,Lt)=>{We(je,1,$t),We(st,1,Lt)},[()=>Ue(qe("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",o(a)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>Ue(qe("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",o(a)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),U("click",je,()=>u(a,"rendered")),U("click",st,()=>u(a,"raw")),p(F,ve)};T(Te,F=>{o(re)&&F(te)})}var Je=x(Te,2),mt=f(Je);Gs(mt,{size:18});var xt=x(ge,2);{var At=F=>{var ve=Iv(),je=f(ve);vt(je,21,()=>t.message.contexts,ft,(Ne,st,Ct)=>{var $t=Nv(),Lt=f($t);W(Gt=>{We($t,1,Gt),Z(Lt,t.message.contexts[Ct].label||t.message.contexts[Ct].module)},[()=>Ue(qe("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",Ct===o(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),U("click",$t,()=>{u(r,Ct,!0)}),p(Ne,$t)}),p(F,ve)};T(xt,F=>{var ve;o(re)&&((ve=t.message.contexts)==null?void 0:ve.length)>1&&F(At)})}var Vt=x(xt,2);{var Yt=F=>{var ve=Rv(),je=f(ve),Ne=f(je);{var st=Lt=>{var Gt=Lv();W(Wn=>We(Gt,1,Wn),[()=>Ue(qe("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",o(j)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),U("click",Gt,()=>{u(n,"system")}),p(Lt,Gt)};T(Ne,Lt=>{t.message.systemPrompt&&Lt(st)})}var Ct=x(Ne,2);{var $t=Lt=>{var Gt=Ov();W(Wn=>We(Gt,1,Wn),[()=>Ue(qe("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",o(J)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),U("click",Gt,()=>{u(n,"userContent")}),p(Lt,Gt)};T(Ct,Lt=>{t.message.userContent&&Lt($t)})}p(F,ve)};T(Vt,F=>{!o(re)&&!o(Q)&&F(Yt)})}var It=x(oe,2),Pe=f(It);{var Ge=F=>{var ve=jv(),je=f(ve);Mo(je,()=>{var Ne;return y((Ne=o($))==null?void 0:Ne.text)}),p(F,ve)},Xe=F=>{var ve=Dv(),je=f(ve);W(()=>Z(je,o(he))),p(F,ve)};T(Pe,F=>{o(re)&&o(a)==="rendered"?F(Ge):F(Xe,-1)})}W(()=>Z(Ye,o(C))),U("click",I,F=>{F.target===F.currentTarget&&X()}),U("keydown",I,F=>{F.key==="Escape"&&X()}),U("click",Je,X),p(E,I)};T(Se,E=>{o(r)!==null&&E(Fe)})}p(e,m),hr()}tn(["click","keydown"]);var Gv=S('<span class="text-[11px] text-dl-text-dim"> </span>'),Hv=S("<!> 다운로드 중",1),Uv=S("<!> ",1),Wv=S('<button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button>'),qv=S('<div class="flex items-center gap-2 py-4 justify-center text-[12px] text-dl-text-dim"><!> 모듈 목록 로드 중...</div>'),Kv=S('<div class="text-[12px] text-dl-primary-light py-2"> </div>'),Yv=S("<button> </button>"),Jv=S('<div class="mb-2"><button class="text-[10px] text-dl-text-dim mb-1 hover:text-dl-text-muted transition-colors">재무제표</button> <div class="flex flex-wrap gap-1"></div></div>'),Xv=S("<button> </button>"),Zv=S('<div class="flex flex-wrap gap-1"></div>'),Qv=S("<button> </button>"),ep=S('<button class="px-2 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"> </button>'),tp=S('<div class="flex flex-wrap gap-1"><!> <!></div>'),rp=S('<div><button class="text-[10px] text-dl-text-dim mb-1 hover:text-dl-text-muted transition-colors"> </button> <!></div>'),np=S('<div class="flex items-center justify-between mb-2"><button class="flex items-center gap-1.5 text-[11px] text-dl-text-muted hover:text-dl-text transition-colors"><!> 전체 선택</button> <button class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"> <!></button></div> <!> <!>',1),ap=S('<div class="text-[12px] text-dl-text-dim py-2">내보낼 수 있는 데이터가 없습니다</div>'),sp=S('<div class="rounded-xl border border-dl-border bg-dl-bg-card/60 backdrop-blur-sm overflow-hidden animate-fadeIn"><div class="flex items-center justify-between px-4 py-3 border-b border-dl-border/50"><div class="flex items-center gap-2"><!> <span class="text-[13px] font-medium text-dl-text">Excel 내보내기</span> <!></div> <div class="flex items-center gap-1.5"><button class="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-dl-success/15 text-dl-success text-[11px] font-medium hover:bg-dl-success/25 transition-colors disabled:opacity-40"><!></button> <!></div></div> <div class="px-4 py-3"><!></div></div>');function op(e,t){mr(t,!0);let r=Ke(t,"stockCode",3,null),n=Ke(t,"corpName",3,""),a=Y(ut([])),s=Y(ut(new Set)),i=Y(!1),l=Y(!1),d=Y(""),c=Y(!1);const v=new Set(["IS","BS","CF","ratios"]);let h=ce(()=>o(a).filter(I=>v.has(I.name))),b=ce(()=>o(a).filter(I=>!v.has(I.name))),A=ce(()=>o(s).size===o(a).length&&o(a).length>0);Bn(()=>{r()&&y()});async function y(){u(i,!0),u(d,"");try{const I=await gu(r());u(a,I.modules||[],!0),u(s,new Set(o(a).map(K=>K.name)),!0)}catch(I){u(d,I.message,!0)}u(i,!1)}function k(I){const K=new Set(o(s));K.has(I)?K.delete(I):K.add(I),u(s,K,!0)}function g(){o(A)?u(s,new Set,!0):u(s,new Set(o(a).map(I=>I.name)),!0)}function z(I){const K=I.map(V=>V.name),oe=K.every(V=>o(s).has(V)),ge=new Set(o(s));if(oe)for(const V of K)ge.delete(V);else for(const V of K)ge.add(V);u(s,ge,!0)}async function L(){if(!(o(s).size===0||o(l))){u(l,!0),u(d,"");try{const I=o(A)?null:[...o(s)];await bu(r(),I)}catch(I){u(d,I.message,!0)}u(l,!1)}}var D=sp(),M=f(D),R=f(M),X=f(R);ul(X,{size:16,class:"text-dl-success"});var P=x(X,4);{var m=I=>{var K=Gv(),oe=f(K);W(()=>Z(oe,`— ${n()??""}`)),p(I,K)};T(P,I=>{n()&&I(m)})}var N=x(R,2),B=f(N),ie=f(B);{var Se=I=>{var K=Hv(),oe=q(K);Kt(oe,{size:12,class:"animate-spin"}),p(I,K)},Fe=I=>{var K=Uv(),oe=q(K);la(oe,{size:12});var ge=x(oe);W(()=>Z(ge,` 다운로드 (${o(s).size??""})`)),p(I,K)};T(ie,I=>{o(l)?I(Se):I(Fe,-1)})}var E=x(B,2);{var j=I=>{var K=Wv(),oe=f(K);Gs(oe,{size:16}),U("click",K,function(...ge){var V;(V=t.onClose)==null||V.apply(this,ge)}),p(I,K)};T(E,I=>{t.onClose&&I(j)})}var J=x(M,2),re=f(J);{var Q=I=>{var K=qv(),oe=f(K);Kt(oe,{size:14,class:"animate-spin"}),p(I,K)},$=I=>{var K=Kv(),oe=f(K);W(()=>Z(oe,o(d))),p(I,K)},C=I=>{var K=np(),oe=q(K),ge=f(oe),V=f(ge);{var ne=te=>{Lf(te,{size:13,class:"text-dl-success"})},be=te=>{vl(te,{size:13})};T(V,te=>{o(A)?te(ne):te(be,-1)})}var xe=x(ge,2),Ce=f(xe),Ve=x(Ce);{var Le=te=>{Sf(te,{size:12})},Ye=te=>{kf(te,{size:12})};T(Ve,te=>{o(c)?te(Le):te(Ye,-1)})}var _e=x(oe,2);{var se=te=>{var Je=Jv(),mt=f(Je),xt=x(mt,2);vt(xt,21,()=>o(h),ft,(At,Vt)=>{var Yt=Yv(),It=f(Yt);W(Pe=>{We(Yt,1,Pe),Z(It,o(Vt).label)},[()=>Ue(qe("px-2.5 py-1 rounded-lg text-[11px] border transition-all",o(s).has(o(Vt).name)?"border-dl-success/40 bg-dl-success/10 text-dl-success":"border-dl-border text-dl-text-dim hover:border-dl-border hover:text-dl-text-muted"))]),U("click",Yt,()=>k(o(Vt).name)),p(At,Yt)}),U("click",mt,()=>z(o(h))),p(te,Je)};T(_e,te=>{o(h).length>0&&te(se)})}var fe=x(_e,2);{var Te=te=>{var Je=rp(),mt=f(Je),xt=f(mt),At=x(mt,2);{var Vt=It=>{var Pe=Zv();vt(Pe,21,()=>o(b),ft,(Ge,Xe)=>{var F=Xv(),ve=f(F);W(je=>{We(F,1,je),Z(ve,o(Xe).label)},[()=>Ue(qe("px-2.5 py-1 rounded-lg text-[11px] border transition-all",o(s).has(o(Xe).name)?"border-dl-success/40 bg-dl-success/10 text-dl-success":"border-dl-border text-dl-text-dim hover:border-dl-border hover:text-dl-text-muted"))]),U("click",F,()=>k(o(Xe).name)),p(Ge,F)}),p(It,Pe)},Yt=It=>{var Pe=tp(),Ge=f(Pe);vt(Ge,17,()=>o(b).slice(0,6),ft,(ve,je)=>{var Ne=Qv(),st=f(Ne);W(Ct=>{We(Ne,1,Ct),Z(st,o(je).label)},[()=>Ue(qe("px-2.5 py-1 rounded-lg text-[11px] border transition-all",o(s).has(o(je).name)?"border-dl-success/40 bg-dl-success/10 text-dl-success":"border-dl-border text-dl-text-dim hover:border-dl-border hover:text-dl-text-muted"))]),U("click",Ne,()=>k(o(je).name)),p(ve,Ne)});var Xe=x(Ge,2);{var F=ve=>{var je=ep(),Ne=f(je);W(()=>Z(Ne,`+${o(b).length-6}개 더`)),U("click",je,()=>u(c,!0)),p(ve,je)};T(Xe,ve=>{o(b).length>6&&ve(F)})}p(It,Pe)};T(At,It=>{o(c)?It(Vt):It(Yt,-1)})}W(()=>Z(xt,`보고서/공시 (${o(b).length??""})`)),U("click",mt,()=>z(o(b))),p(te,Je)};T(fe,te=>{o(b).length>0&&te(Te)})}W(()=>Z(Ce,`${o(c)?"접기":"펼치기"} `)),U("click",ge,g),U("click",xe,()=>u(c,!o(c))),p(I,K)},he=I=>{var K=ap();p(I,K)};T(re,I=>{o(i)?I(Q):o(d)?I($,1):o(a).length>0?I(C,2):I(he,-1)})}W(()=>B.disabled=o(s).size===0||o(l)||o(i)),U("click",B,L),p(e,D),hr()}tn(["click"]);var ip=S("<button><!> Excel</button>"),lp=S('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),dp=S('<div class="flex justify-end gap-2 mb-1.5"><!> <!></div>'),cp=S('<div class="mb-2"><!></div>'),up=S('<div class="flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="max-w-[720px] mx-auto px-5 pt-14 pb-8 space-y-8"></div></div> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!> <!></div></div></div>');function fp(e,t){mr(t,!0);function r(P){if(a())return!1;for(let m=n().length-1;m>=0;m--)if(n()[m].role==="assistant"&&!n()[m].error&&n()[m].text)return m===P;return!1}let n=Ke(t,"messages",19,()=>[]),a=Ke(t,"isLoading",3,!1),s=Ke(t,"inputText",15,""),i=Ke(t,"scrollTrigger",3,0),l=Y(!1),d=ce(()=>{var P;for(let m=n().length-1;m>=0;m--){const N=n()[m];if(N.role==="assistant"&&((P=N.meta)!=null&&P.stockCode))return N.meta.stockCode}return null}),c=ce(()=>{var P;for(let m=n().length-1;m>=0;m--){const N=n()[m];if(N.role==="assistant"&&((P=N.meta)!=null&&P.company))return N.meta.company}return""}),v,h=!1;function b(){if(!v)return;const{scrollTop:P,scrollHeight:m,clientHeight:N}=v;h=m-P-N>80}Bn(()=>{i(),!(!v||h)&&requestAnimationFrame(()=>{v&&(v.scrollTop=v.scrollHeight)})});var A=up(),y=f(A),k=f(y);vt(k,21,n,ft,(P,m,N)=>{{let B=ce(()=>r(N)?t.onRegenerate:void 0);Vv(P,{get message(){return o(m)},get onRegenerate(){return o(B)}})}}),Fs(y,P=>v=P,()=>v);var g=x(y,2),z=f(g),L=f(z);{var D=P=>{var m=dp(),N=f(m);{var B=Fe=>{var E=ip(),j=f(E);ul(j,{size:10}),W(J=>We(E,1,J),[()=>Ue(qe("flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] transition-colors",o(l)?"text-dl-success bg-dl-success/10":"text-dl-text-dim hover:text-dl-success"))]),U("click",E,()=>u(l,!o(l))),p(Fe,E)};T(N,Fe=>{o(d)&&Fe(B)})}var ie=x(N,2);{var Se=Fe=>{var E=lp(),j=f(E);la(j,{size:10}),U("click",E,function(...J){var re;(re=t.onExport)==null||re.apply(this,J)}),p(Fe,E)};T(ie,Fe=>{t.onExport&&Fe(Se)})}p(P,m)};T(L,P=>{n().length>1&&!a()&&P(D)})}var M=x(L,2);{var R=P=>{var m=cp(),N=f(m);op(N,{get stockCode(){return o(d)},get corpName(){return o(c)},onClose:()=>u(l,!1)}),p(P,m)};T(M,P=>{o(l)&&o(d)&&P(R)})}var X=x(M,2);pl(X,{get isLoading(){return a()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get inputText(){return s()},set inputText(P){s(P)}}),Ta("scroll",y,b),p(e,A),hr()}tn(["click"]);var vp=S('<div class="sidebar-overlay"></div>'),pp=S("<!> <span>확인 중...</span>",1),mp=S("<!> <span>설정 필요</span>",1),hp=S('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),gp=S('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!> <!>',1),bp=S('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/80 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text-muted">AI Provider 확인 중...</div></div></div>'),xp=S('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-primary/30 bg-dl-primary/5 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text">AI Provider가 설정되지 않았습니다</div> <div class="text-[11px] text-dl-text-muted mt-0.5">대화를 시작하려면 Provider를 설정해주세요</div></div> <button class="px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors flex-shrink-0">설정하기</button></div>'),_p=S('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),yp=S('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),wp=S('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),kp=S('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),Sp=S('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),Mp=S('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),zp=S('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),Ap=S('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),Cp=S('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),Ep=S('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),$p=S('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),Tp=S('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @anthropic-ai/claude-code</div></div></div>'),Pp=S('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">인증</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">claude auth login</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">Claude Pro 또는 Max 구독이 필요합니다</span></div>',1),Np=S('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2">설치 완료 후 새로고침하세요</div></div>'),Ip=S("<!> 브라우저에서 로그인 중...",1),Lp=S("<!> OpenAI 계정으로 로그인",1),Op=S('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2.5">ChatGPT 계정으로 로그인하여 사용하세요</div> <button class="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div></div>'),Rp=S('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),jp=S('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),Dp=S("<button> <!></button>"),Fp=S('<div class="flex flex-wrap gap-1.5"></div>'),Bp=S('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),Vp=S('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),Gp=S('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),Hp=S('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),Up=S('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),Wp=S('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),qp=S('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),Kp=S("<!> <!> <!> <!> <!> <!> <!>",1),Yp=S('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),Jp=S('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden"><div class="flex items-center justify-between px-6 pt-5 pb-3"><div class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),Xp=S('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5"><div class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),Zp=S('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn"><div> </div></div>'),Qp=S('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-0 left-0 right-0 z-10 pointer-events-none"><div class="flex items-center justify-between px-3 h-11 pointer-events-auto" style="background: linear-gradient(to bottom, rgba(5,8,17,0.92) 40%, transparent);"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center gap-1"><a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <div class="w-px h-4 bg-dl-border mx-1"></div> <button><!> <!></button></div></div> <!></div> <!></div></div>  <!> <!> <!>',1);function em(e,t){mr(t,!0);let r=Y(""),n=Y(!1),a=Y(null),s=Y(ut({})),i=Y(ut({})),l=Y(null),d=Y(null),c=Y(ut([])),v=Y(!0),h=Y(0),b=Y(!0),A=Y(""),y=Y(!1),k=Y(null),g=Y(ut({})),z=Y(ut({})),L=Y(""),D=Y(!1),M=Y(null),R=Y(""),X=Y(!1),P=Y(""),m=Y(0),N=Y(null),B=Y(!1),ie=Y(ut({})),Se=Y(!1);function Fe(){u(Se,window.innerWidth<=768),o(Se)&&u(v,!1)}Bn(()=>(Fe(),window.addEventListener("resize",Fe),()=>window.removeEventListener("resize",Fe)));let E=Y(null),j=Y(""),J=Y("error"),re=Y(!1);function Q(_,O="error",ae=4e3){u(j,_,!0),u(J,O,!0),u(re,!0),setTimeout(()=>{u(re,!1)},ae)}const $=pf();Bn(()=>{I()});let C=Y(ut({})),he=Y(ut({}));async function I(){var _,O,ae;u(b,!0);try{const Oe=await uu();u(s,Oe.providers||{},!0),u(i,Oe.ollama||{},!0),u(C,Oe.codex||{},!0),u(he,Oe.claudeCode||{},!0),u(ie,Oe.chatgpt||{},!0),Oe.version&&u(A,Oe.version,!0);const Re=localStorage.getItem("dartlab-provider"),tt=localStorage.getItem("dartlab-model");if(Re&&((_=o(s)[Re])!=null&&_.available)){u(l,Re,!0),u(k,Re,!0),await Cn(Re,tt),await K(Re);const Me=o(g)[Re]||[];tt&&Me.includes(tt)?u(d,tt,!0):Me.length>0&&(u(d,Me[0],!0),localStorage.setItem("dartlab-model",o(d))),u(c,Me,!0),u(b,!1);return}if(Re&&o(s)[Re]){u(l,Re,!0),u(k,Re,!0),await K(Re);const Me=o(g)[Re]||[];u(c,Me,!0),tt&&Me.includes(tt)?u(d,tt,!0):Me.length>0&&u(d,Me[0],!0),u(b,!1);return}for(const Me of["chatgpt","codex","ollama"])if((O=o(s)[Me])!=null&&O.available){u(l,Me,!0),u(k,Me,!0),await Cn(Me),await K(Me);const $r=o(g)[Me]||[];u(c,$r,!0),u(d,((ae=o(s)[Me])==null?void 0:ae.model)||($r.length>0?$r[0]:null),!0),o(d)&&localStorage.setItem("dartlab-model",o(d));break}}catch{}u(b,!1)}async function K(_){u(z,{...o(z),[_]:!0},!0);try{const O=await fu(_);u(g,{...o(g),[_]:O.models||[]},!0)}catch{u(g,{...o(g),[_]:[]},!0)}u(z,{...o(z),[_]:!1},!0)}async function oe(_){var ae;u(l,_,!0),u(d,null),u(k,_,!0),localStorage.setItem("dartlab-provider",_),localStorage.removeItem("dartlab-model"),u(L,""),u(M,null);try{await Cn(_)}catch{}await K(_);const O=o(g)[_]||[];if(u(c,O,!0),O.length>0){u(d,((ae=o(s)[_])==null?void 0:ae.model)||O[0],!0),localStorage.setItem("dartlab-model",o(d));try{await Cn(_,o(d))}catch{}}}async function ge(_){u(d,_,!0),localStorage.setItem("dartlab-model",_);try{await Cn(o(l),_)}catch{}}function V(_){o(k)===_?u(k,null):(u(k,_,!0),K(_))}async function ne(){const _=o(L).trim();if(!(!_||!o(l))){u(D,!0),u(M,null);try{const O=await Cn(o(l),o(d),_);O.available?(u(M,"success"),o(s)[o(l)]={...o(s)[o(l)],available:!0,model:O.model},!o(d)&&O.model&&u(d,O.model,!0),await K(o(l)),u(c,o(g)[o(l)]||[],!0),Q("API 키 인증 성공","success")):u(M,"error")}catch{u(M,"error")}u(D,!1)}}async function be(){if(!o(B)){u(B,!0);try{const{authUrl:_}=await pu();window.open(_,"dartlab-oauth","width=600,height=700");const O=setInterval(async()=>{var ae;try{const Oe=await mu();Oe.done&&(clearInterval(O),u(B,!1),Oe.error?Q(`인증 실패: ${Oe.error}`):(Q("ChatGPT 인증 성공","success"),await I(),(ae=o(s).chatgpt)!=null&&ae.available&&await oe("chatgpt")))}catch{clearInterval(O),u(B,!1)}},2e3);setTimeout(()=>{clearInterval(O),o(B)&&(u(B,!1),Q("인증 시간이 초과되었습니다. 다시 시도해주세요."))},12e4)}catch(_){u(B,!1),Q(`OAuth 시작 실패: ${_.message}`)}}}async function xe(){try{await hu(),u(ie,{authenticated:!1},!0),o(l)==="chatgpt"&&u(s,{...o(s),chatgpt:{...o(s).chatgpt,available:!1}},!0),Q("ChatGPT 로그아웃 완료","success"),await I()}catch{Q("로그아웃 실패")}}function Ce(){const _=o(R).trim();!_||o(X)||(u(X,!0),u(P,"준비 중..."),u(m,0),u(N,vu(_,{onProgress(O){O.total&&O.completed!==void 0?(u(m,Math.round(O.completed/O.total*100),!0),u(P,`다운로드 중... ${o(m)}%`)):O.status&&u(P,O.status,!0)},async onDone(){u(X,!1),u(N,null),u(R,""),u(P,""),u(m,0),Q(`${_} 다운로드 완료`,"success"),await K("ollama"),u(c,o(g).ollama||[],!0),o(c).includes(_)&&await ge(_)},onError(O){u(X,!1),u(N,null),u(P,""),u(m,0),Q(`다운로드 실패: ${O}`)}}),!0))}function Ve(){o(N)&&(o(N).abort(),u(N,null)),u(X,!1),u(R,""),u(P,""),u(m,0)}function Le(){u(v,!o(v))}function Ye(){if(u(L,""),u(M,null),o(l))u(k,o(l),!0);else{const _=Object.keys(o(s));u(k,_.length>0?_[0]:null,!0)}u(y,!0),o(k)&&K(o(k))}function _e(){$.createConversation(),u(r,""),u(n,!1),o(a)&&(o(a).abort(),u(a,null))}function se(_){$.setActive(_),u(r,""),u(n,!1),o(a)&&(o(a).abort(),u(a,null))}function fe(_){u(E,_,!0)}function Te(){o(E)&&($.deleteConversation(o(E)),u(E,null))}function te(){var O;const _=$.active;if(!_)return null;for(let ae=_.messages.length-1;ae>=0;ae--){const Oe=_.messages[ae];if(Oe.role==="assistant"&&((O=Oe.meta)!=null&&O.stockCode))return Oe.meta.stockCode}return null}async function Je(){var Jt,Or;const _=o(r).trim();if(!_||o(n))return;if(!o(l)||!((Jt=o(s)[o(l)])!=null&&Jt.available)){Q("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),Ye();return}$.activeId||$.createConversation();const O=$.activeId;$.addMessage("user",_),u(r,""),u(n,!0),$.addMessage("assistant",""),$.updateLastMessage({loading:!0,startedAt:Date.now()}),aa(h);const ae=$.active,Oe=[];let Re=null;if(ae){const le=ae.messages.slice(0,-2);for(const ee of le)if((ee.role==="user"||ee.role==="assistant")&&ee.text&&ee.text.trim()&&!ee.error&&!ee.loading){const Be={role:ee.role,text:ee.text};ee.role==="assistant"&&((Or=ee.meta)!=null&&Or.stockCode)&&(Be.meta={company:ee.meta.company||ee.company,stockCode:ee.meta.stockCode,modules:ee.meta.includedModules||null},Re=ee.meta.stockCode),Oe.push(Be)}}const tt=Re||te();function Me(){return $.activeId!==O}const $r=_u(tt,_,{provider:o(l),model:o(d)},{onMeta(le){var xr;if(Me())return;const ee=$.active,Be=ee==null?void 0:ee.messages[ee.messages.length-1],Tt={meta:{...(Be==null?void 0:Be.meta)||{},...le}};le.company&&(Tt.company=le.company,$.activeId&&((xr=$.active)==null?void 0:xr.title)==="새 대화"&&$.updateTitle($.activeId,le.company)),le.stockCode&&(Tt.stockCode=le.stockCode),$.updateLastMessage(Tt)},onSnapshot(le){Me()||$.updateLastMessage({snapshot:le})},onContext(le){if(Me())return;const ee=$.active;if(!ee)return;const Be=ee.messages[ee.messages.length-1],Rr=(Be==null?void 0:Be.contexts)||[];$.updateLastMessage({contexts:[...Rr,{module:le.module,label:le.label,text:le.text}]})},onSystemPrompt(le){Me()||$.updateLastMessage({systemPrompt:le.text,userContent:le.userContent||null})},onToolCall(le){if(Me())return;const ee=$.active;if(!ee)return;const Be=ee.messages[ee.messages.length-1],Rr=(Be==null?void 0:Be.toolEvents)||[];$.updateLastMessage({toolEvents:[...Rr,{type:"call",name:le.name,arguments:le.arguments}]})},onToolResult(le){if(Me())return;const ee=$.active;if(!ee)return;const Be=ee.messages[ee.messages.length-1],Rr=(Be==null?void 0:Be.toolEvents)||[];$.updateLastMessage({toolEvents:[...Rr,{type:"result",name:le.name,result:le.result}]})},onChunk(le){if(Me())return;const ee=$.active;if(!ee)return;const Be=ee.messages[ee.messages.length-1];$.updateLastMessage({text:((Be==null?void 0:Be.text)||"")+le}),aa(h)},onDone(){if(Me())return;const le=$.active,ee=le==null?void 0:le.messages[le.messages.length-1],Be=ee!=null&&ee.startedAt?((Date.now()-ee.startedAt)/1e3).toFixed(1):null;$.updateLastMessage({loading:!1,duration:Be}),$.flush(),u(n,!1),u(a,null),aa(h)},onError(le,ee,Be){Me()||($.updateLastMessage({text:`오류: ${le}`,loading:!1,error:!0}),$.flush(),ee==="relogin"||ee==="login"?(Q(`${le} — 설정에서 재로그인하세요`),Ye()):Q(ee==="check_headers"||ee==="check_endpoint"||ee==="check_client_id"?`${le} — ChatGPT API 변경 감지. 업데이트를 확인하세요`:ee==="rate_limit"?"요청이 너무 많습니다. 잠시 후 다시 시도해주세요":le),u(n,!1),u(a,null))}},Oe);u(a,$r,!0)}function mt(){o(a)&&(o(a).abort(),u(a,null),u(n,!1),$.updateLastMessage({loading:!1}),$.flush())}function xt(){const _=$.active;if(!_||_.messages.length<2)return;let O="";for(let ae=_.messages.length-1;ae>=0;ae--)if(_.messages[ae].role==="user"){O=_.messages[ae].text;break}O&&($.removeLastMessage(),$.removeLastMessage(),u(r,O,!0),requestAnimationFrame(()=>{Je()}))}function At(){const _=$.active;if(!_)return;let O=`# ${_.title}

`;for(const tt of _.messages)tt.role==="user"?O+=`## You

${tt.text}

`:tt.role==="assistant"&&tt.text&&(O+=`## DartLab

${tt.text}

`);const ae=new Blob([O],{type:"text/markdown;charset=utf-8"}),Oe=URL.createObjectURL(ae),Re=document.createElement("a");Re.href=Oe,Re.download=`${_.title||"dartlab-chat"}.md`,Re.click(),URL.revokeObjectURL(Oe),Q("대화가 마크다운으로 내보내졌습니다","success")}function Vt(_){(_.metaKey||_.ctrlKey)&&_.key==="n"&&(_.preventDefault(),_e()),(_.metaKey||_.ctrlKey)&&_.shiftKey&&_.key==="S"&&(_.preventDefault(),Le()),_.key==="Escape"&&o(E)?u(E,null):_.key==="Escape"&&o(y)&&u(y,!1)}let Yt=ce(()=>{var _;return((_=$.active)==null?void 0:_.messages)||[]}),It=ce(()=>$.active&&$.active.messages.length>0),Pe=ce(()=>{var _;return!o(b)&&(!o(l)||!((_=o(s)[o(l)])!=null&&_.available))});const Ge=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var Xe=Qp();Ta("keydown",hs,Vt);var F=q(Xe),ve=f(F);{var je=_=>{var O=vp();U("click",O,()=>{u(v,!1)}),U("keydown",O,()=>{}),p(_,O)};T(ve,_=>{o(Se)&&o(v)&&_(je)})}var Ne=x(ve,2),st=f(Ne);{let _=ce(()=>o(Se)?!0:o(v));Yf(st,{get conversations(){return $.conversations},get activeId(){return $.activeId},get open(){return o(_)},get version(){return o(A)},onNewChat:()=>{_e(),o(Se)&&u(v,!1)},onSelect:O=>{se(O),o(Se)&&u(v,!1)},onDelete:fe})}var Ct=x(Ne,2),$t=f(Ct),Lt=f($t),Gt=f(Lt),Wn=f(Gt);{var ml=_=>{Pf(_,{size:18})},hl=_=>{Tf(_,{size:18})};T(Wn,_=>{o(v)?_(ml):_(hl,-1)})}var gl=x(Gt,2),Us=f(gl),bl=f(Us);Af(bl,{size:15});var Ws=x(Us,2),xl=f(Ws);$a(xl,{size:15});var qs=x(Ws,2),_l=f(qs);Cf(_l,{size:15});var Ba=x(qs,4),Ks=f(Ba);{var yl=_=>{var O=pp(),ae=q(O);Kt(ae,{size:12,class:"animate-spin"}),p(_,O)},wl=_=>{var O=mp(),ae=q(O);sn(ae,{size:12}),p(_,O)},kl=_=>{var O=gp(),ae=x(q(O),2),Oe=f(ae),Re=x(ae,2);{var tt=Jt=>{var Or=hp(),le=x(q(Or),2),ee=f(le);W(()=>Z(ee,o(d))),p(Jt,Or)};T(Re,Jt=>{o(d)&&Jt(tt)})}var Me=x(Re,2);{var $r=Jt=>{Kt(Jt,{size:10,class:"animate-spin text-dl-primary-light"})};T(Me,Jt=>{o(X)&&Jt($r)})}W(()=>Z(Oe,o(l))),p(_,O)};T(Ks,_=>{o(b)?_(yl):o(Pe)?_(wl,1):_(kl,-1)})}var Sl=x(Ks,2);If(Sl,{size:12});var Ml=x(Lt,2);{var zl=_=>{var O=bp(),ae=f(O);Kt(ae,{size:16,class:"text-dl-text-dim animate-spin flex-shrink-0"}),p(_,O)},Al=_=>{var O=xp(),ae=f(O);sn(ae,{size:16,class:"text-dl-primary-light flex-shrink-0"});var Oe=x(ae,4);U("click",Oe,()=>Ye()),p(_,O)};T(Ml,_=>{o(b)&&!o(y)?_(zl):o(Pe)&&!o(y)&&_(Al,1)})}var Cl=x($t,2);{var El=_=>{fp(_,{get messages(){return o(Yt)},get isLoading(){return o(n)},get scrollTrigger(){return o(h)},onSend:Je,onStop:mt,onRegenerate:xt,onExport:At,get inputText(){return o(r)},set inputText(O){u(r,O,!0)}})},$l=_=>{av(_,{onSend:Je,get inputText(){return o(r)},set inputText(O){u(r,O,!0)}})};T(Cl,_=>{o(It)?_(El):_($l,-1)})}var Ys=x(F,2);{var Tl=_=>{var O=Jp(),ae=f(O),Oe=f(ae),Re=x(f(Oe),2),tt=f(Re);Gs(tt,{size:18});var Me=x(Oe,2),$r=f(Me);vt($r,21,()=>Object.entries(o(s)),ft,(Tt,xr)=>{var jr=ce(()=>Qo(o(xr),2));let rt=()=>o(jr)[0],ot=()=>o(jr)[1];const qn=ce(()=>rt()===o(l)),Ll=ce(()=>o(k)===rt()),Sn=ce(()=>ot().auth==="api_key"),Va=ce(()=>ot().auth==="cli"),xa=ce(()=>o(g)[rt()]||[]),Xs=ce(()=>o(z)[rt()]);var Ga=Yp(),Ha=f(Ga),Zs=f(Ha),Qs=x(Zs,2),eo=f(Qs),to=f(eo),Ol=f(to),Rl=x(to,2);{var jl=it=>{var Xt=_p();p(it,Xt)};T(Rl,it=>{o(qn)&&it(jl)})}var Dl=x(eo,2),Fl=f(Dl),Bl=x(Qs,2),Vl=f(Bl);{var Gl=it=>{rs(it,{size:16,class:"text-dl-success"})},Hl=it=>{var Xt=yp(),Mn=q(Xt);Ho(Mn,{size:14,class:"text-amber-400"}),p(it,Xt)},Ul=it=>{var Xt=wp(),Mn=q(Xt);Of(Mn,{size:14,class:"text-dl-text-dim"}),p(it,Xt)};T(Vl,it=>{ot().available?it(Gl):o(Sn)?it(Hl,1):o(Va)&&!ot().available&&it(Ul,2)})}var Wl=x(Ha,2);{var ql=it=>{var Xt=Kp(),Mn=q(Xt);{var Kl=De=>{var Ze=Sp(),nt=f(Ze),_t=f(nt),Ot=x(nt,2),Qe=f(Ot),yt=x(Qe,2),Ht=f(yt);{var Et=Ie=>{Kt(Ie,{size:12,class:"animate-spin"})},et=Ie=>{Ho(Ie,{size:12})};T(Ht,Ie=>{o(D)?Ie(Et):Ie(et,-1)})}var ht=x(Ot,2);{var He=Ie=>{var Pt=kp(),lt=f(Pt);sn(lt,{size:12}),p(Ie,Pt)};T(ht,Ie=>{o(M)==="error"&&Ie(He)})}W(Ie=>{Z(_t,ot().envKey?`환경변수 ${ot().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),ca(Qe,"placeholder",rt()==="openai"?"sk-...":rt()==="claude"?"sk-ant-...":"API Key"),yt.disabled=Ie},[()=>!o(L).trim()||o(D)]),U("keydown",Qe,Ie=>{Ie.key==="Enter"&&ne()}),ia(Qe,()=>o(L),Ie=>u(L,Ie)),U("click",yt,ne),p(De,Ze)};T(Mn,De=>{o(Sn)&&!ot().available&&De(Kl)})}var ro=x(Mn,2);{var Yl=De=>{var Ze=zp(),nt=f(Ze),_t=f(nt);rs(_t,{size:13,class:"text-dl-success"});var Ot=x(nt,2),Qe=f(Ot),yt=x(Qe,2);{var Ht=et=>{var ht=Mp(),He=f(ht);{var Ie=lt=>{Kt(lt,{size:10,class:"animate-spin"})},Pt=lt=>{var Zt=oa("변경");p(lt,Zt)};T(He,lt=>{o(D)?lt(Ie):lt(Pt,-1)})}W(()=>ht.disabled=o(D)),U("click",ht,ne),p(et,ht)},Et=ce(()=>o(L).trim());T(yt,et=>{o(Et)&&et(Ht)})}U("keydown",Qe,et=>{et.key==="Enter"&&ne()}),ia(Qe,()=>o(L),et=>u(L,et)),p(De,Ze)};T(ro,De=>{o(Sn)&&ot().available&&De(Yl)})}var no=x(ro,2);{var Jl=De=>{var Ze=Ap(),nt=x(f(Ze),2),_t=f(nt);la(_t,{size:14});var Ot=x(_t,2);Go(Ot,{size:10,class:"ml-auto"}),p(De,Ze)},Xl=De=>{var Ze=Cp(),nt=f(Ze),_t=f(nt);sn(_t,{size:14}),p(De,Ze)};T(no,De=>{rt()==="ollama"&&!o(i).installed?De(Jl):rt()==="ollama"&&o(i).installed&&!o(i).running&&De(Xl,1)})}var ao=x(no,2);{var Zl=De=>{var Ze=Np(),nt=f(Ze);{var _t=Qe=>{var yt=$p(),Ht=q(yt),Et=f(Ht),et=x(Ht,2),ht=f(et);{var He=or=>{var nn=Ep();p(or,nn)};T(ht,or=>{o(C).installed||or(He)})}var Ie=x(ht,2),Pt=f(Ie),lt=f(Pt),Zt=x(et,2),Dr=f(Zt);sn(Dr,{size:12,class:"text-amber-400 flex-shrink-0"}),W(()=>{Z(Et,o(C).installed?"Codex CLI가 설치되었지만 인증이 필요합니다":"Codex CLI 설치가 필요합니다"),Z(lt,o(C).installed?"1.":"2.")}),p(Qe,yt)},Ot=Qe=>{var yt=Pp(),Ht=q(yt),Et=f(Ht),et=x(Ht,2),ht=f(et);{var He=or=>{var nn=Tp();p(or,nn)};T(ht,or=>{o(he).installed||or(He)})}var Ie=x(ht,2),Pt=f(Ie),lt=f(Pt),Zt=x(et,2),Dr=f(Zt);sn(Dr,{size:12,class:"text-amber-400 flex-shrink-0"}),W(()=>{Z(Et,o(he).installed&&!o(he).authenticated?"Claude Code가 설치되었지만 인증이 필요합니다":"Claude Code CLI 설치가 필요합니다"),Z(lt,o(he).installed?"1.":"2.")}),p(Qe,yt)};T(nt,Qe=>{rt()==="codex"?Qe(_t):rt()==="claude-code"&&Qe(Ot,1)})}p(De,Ze)};T(ao,De=>{o(Va)&&!ot().available&&De(Zl)})}var so=x(ao,2);{var Ql=De=>{var Ze=Op(),nt=x(f(Ze),2),_t=f(nt);{var Ot=Et=>{var et=Ip(),ht=q(et);Kt(ht,{size:14,class:"animate-spin"}),p(Et,et)},Qe=Et=>{var et=Lp(),ht=q(et);Ef(ht,{size:14}),p(Et,et)};T(_t,Et=>{o(B)?Et(Ot):Et(Qe,-1)})}var yt=x(nt,2),Ht=f(yt);sn(Ht,{size:12,class:"text-amber-400 flex-shrink-0"}),W(()=>nt.disabled=o(B)),U("click",nt,be),p(De,Ze)};T(so,De=>{ot().auth==="oauth"&&!ot().available&&De(Ql)})}var oo=x(so,2);{var ed=De=>{var Ze=Rp(),nt=f(Ze),_t=f(nt),Ot=f(_t);rs(Ot,{size:13,class:"text-dl-success"});var Qe=x(_t,2),yt=f(Qe);$f(yt,{size:11}),U("click",Qe,xe),p(De,Ze)};T(oo,De=>{ot().auth==="oauth"&&ot().available&&De(ed)})}var td=x(oo,2);{var rd=De=>{var Ze=qp(),nt=f(Ze),_t=x(f(nt),2);{var Ot=He=>{Kt(He,{size:12,class:"animate-spin text-dl-text-dim"})};T(_t,He=>{o(Xs)&&He(Ot)})}var Qe=x(nt,2);{var yt=He=>{var Ie=jp(),Pt=f(Ie);Kt(Pt,{size:14,class:"animate-spin"}),p(He,Ie)},Ht=He=>{var Ie=Fp();vt(Ie,21,()=>o(xa),ft,(Pt,lt)=>{var Zt=Dp(),Dr=f(Zt),or=x(Dr);{var nn=Qt=>{wf(Qt,{size:10,class:"inline ml-1"})};T(or,Qt=>{o(lt)===o(d)&&o(qn)&&Qt(nn)})}W(Qt=>{We(Zt,1,Qt),Z(Dr,`${o(lt)??""} `)},[()=>Ue(qe("px-3 py-1.5 rounded-lg text-[11px] border transition-all",o(lt)===o(d)&&o(qn)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),U("click",Zt,()=>{rt()!==o(l)&&oe(rt()),ge(o(lt))}),p(Pt,Zt)}),p(He,Ie)},Et=He=>{var Ie=Bp();p(He,Ie)};T(Qe,He=>{o(Xs)&&o(xa).length===0?He(yt):o(xa).length>0?He(Ht,1):He(Et,-1)})}var et=x(Qe,2);{var ht=He=>{var Ie=Wp(),Pt=f(Ie),lt=x(f(Pt),2),Zt=x(f(lt));Go(Zt,{size:9});var Dr=x(Pt,2);{var or=Qt=>{var Kn=Vp(),Yn=f(Kn),zn=f(Yn),Jn=f(zn);Kt(Jn,{size:12,class:"animate-spin text-dl-primary-light"});var Ua=x(zn,2),_a=x(Yn,2),Tr=f(_a),ir=x(_a,2),Wa=f(ir);W(()=>{Wi(Tr,`width: ${o(m)??""}%`),Z(Wa,o(P))}),U("click",Ua,Ve),p(Qt,Kn)},nn=Qt=>{var Kn=Up(),Yn=q(Kn),zn=f(Yn),Jn=x(zn,2),Ua=f(Jn);la(Ua,{size:12});var _a=x(Yn,2);vt(_a,21,()=>Ge,ft,(Tr,ir)=>{const Wa=ce(()=>o(xa).some(An=>An===o(ir).name||An===o(ir).name.split(":")[0]));var io=ue(),nd=q(io);{var ad=An=>{var qa=Hp(),lo=f(qa),co=f(lo),uo=f(co),sd=f(uo),fo=x(uo,2),od=f(fo),id=x(fo,2);{var ld=Ka=>{var po=Gp(),pd=f(po);W(()=>Z(pd,o(ir).tag)),p(Ka,po)};T(id,Ka=>{o(ir).tag&&Ka(ld)})}var dd=x(co,2),cd=f(dd),ud=x(lo,2),vo=f(ud),fd=f(vo),vd=x(vo,2);la(vd,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),W(()=>{Z(sd,o(ir).name),Z(od,o(ir).size),Z(cd,o(ir).desc),Z(fd,`${o(ir).gb??""} GB`)}),U("click",qa,()=>{u(R,o(ir).name,!0),Ce()}),p(An,qa)};T(nd,An=>{o(Wa)||An(ad)})}p(Tr,io)}),W(Tr=>Jn.disabled=Tr,[()=>!o(R).trim()]),U("keydown",zn,Tr=>{Tr.key==="Enter"&&Ce()}),ia(zn,()=>o(R),Tr=>u(R,Tr)),U("click",Jn,Ce),p(Qt,Kn)};T(Dr,Qt=>{o(X)?Qt(or):Qt(nn,-1)})}p(He,Ie)};T(et,He=>{rt()==="ollama"&&He(ht)})}p(De,Ze)};T(td,De=>{(ot().available||o(Sn)||o(Va)||ot().auth==="oauth")&&De(rd)})}p(it,Xt)};T(Wl,it=>{(o(Ll)||o(qn))&&it(ql)})}W((it,Xt)=>{We(Ga,1,it),We(Zs,1,Xt),Z(Ol,ot().label||rt()),Z(Fl,ot().desc||"")},[()=>Ue(qe("rounded-xl border transition-all",o(qn)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>Ue(qe("w-2.5 h-2.5 rounded-full flex-shrink-0",ot().available?"bg-dl-success":o(Sn)?"bg-amber-400":"bg-dl-text-dim"))]),U("click",Ha,()=>{ot().available||o(Sn)?rt()===o(l)?V(rt()):oe(rt()):V(rt())}),p(Tt,Ga)});var Jt=x(Me,2),Or=f(Jt),le=f(Or);{var ee=Tt=>{var xr=oa();W(()=>{var jr;return Z(xr,`현재: ${(((jr=o(s)[o(l)])==null?void 0:jr.label)||o(l))??""} / ${o(d)??""}`)}),p(Tt,xr)},Be=Tt=>{var xr=oa();W(()=>{var jr;return Z(xr,`현재: ${(((jr=o(s)[o(l)])==null?void 0:jr.label)||o(l))??""}`)}),p(Tt,xr)};T(le,Tt=>{o(l)&&o(d)?Tt(ee):o(l)&&Tt(Be,1)})}var Rr=x(Or,2);U("click",O,Tt=>{Tt.target===Tt.currentTarget&&u(y,!1)}),U("keydown",O,()=>{}),U("click",Re,()=>u(y,!1)),U("click",Rr,()=>u(y,!1)),p(_,O)};T(Ys,_=>{o(y)&&_(Tl)})}var Js=x(Ys,2);{var Pl=_=>{var O=Xp(),ae=f(O),Oe=x(f(ae),4),Re=f(Oe),tt=x(Re,2);U("click",O,Me=>{Me.target===Me.currentTarget&&u(E,null)}),U("keydown",O,()=>{}),U("click",Re,()=>u(E,null)),U("click",tt,Te),p(_,O)};T(Js,_=>{o(E)&&_(Pl)})}var Nl=x(Js,2);{var Il=_=>{var O=Zp(),ae=f(O),Oe=f(ae);W(Re=>{We(ae,1,Re),Z(Oe,o(j))},[()=>Ue(qe("px-4 py-3 rounded-xl border text-[13px] shadow-2xl max-w-sm",o(J)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":o(J)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),p(_,O)};T(Nl,_=>{o(re)&&_(Il)})}W(_=>{We(Ne,1,Ue(o(Se)?o(v)?"sidebar-mobile":"hidden":"")),We(Ba,1,_)},[()=>Ue(qe("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",o(b)?"text-dl-text-dim":o(Pe)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),U("click",Gt,Le),U("click",Ba,()=>Ye()),p(e,Xe),hr()}tn(["click","keydown"]);Gc(em,{target:document.getElementById("app")});
