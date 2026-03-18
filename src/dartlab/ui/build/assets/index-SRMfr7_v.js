var Dd=Object.defineProperty;var si=e=>{throw TypeError(e)};var jd=(e,t,r)=>t in e?Dd(e,t,{enumerable:!0,configurable:!0,writable:!0,value:r}):e[t]=r;var en=(e,t,r)=>jd(e,typeof t!="symbol"?t+"":t,r),Zs=(e,t,r)=>t.has(e)||si("Cannot "+r);var M=(e,t,r)=>(Zs(e,t,"read from private field"),r?r.call(e):t.get(e)),Xe=(e,t,r)=>t.has(e)?si("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,r),je=(e,t,r,a)=>(Zs(e,t,"write to private field"),a?a.call(e,r):t.set(e,r),r),Yt=(e,t,r)=>(Zs(e,t,"access private method"),r);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))a(s);new MutationObserver(s=>{for(const o of s)if(o.type==="childList")for(const i of o.addedNodes)i.tagName==="LINK"&&i.rel==="modulepreload"&&a(i)}).observe(document,{childList:!0,subtree:!0});function r(s){const o={};return s.integrity&&(o.integrity=s.integrity),s.referrerPolicy&&(o.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?o.credentials="include":s.crossOrigin==="anonymous"?o.credentials="omit":o.credentials="same-origin",o}function a(s){if(s.ep)return;s.ep=!0;const o=r(s);fetch(s.href,o)}})();const io=!1;var Po=Array.isArray,Vd=Array.prototype.indexOf,Ua=Array.prototype.includes,Bs=Array.from,Fd=Object.defineProperty,na=Object.getOwnPropertyDescriptor,Fi=Object.getOwnPropertyDescriptors,qd=Object.prototype,Bd=Array.prototype,No=Object.getPrototypeOf,oi=Object.isExtensible;function os(e){return typeof e=="function"}const Gd=()=>{};function Hd(e){return e()}function lo(e){for(var t=0;t<e.length;t++)e[t]()}function qi(){var e,t,r=new Promise((a,s)=>{e=a,t=s});return{promise:r,resolve:e,reject:t}}function Bi(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const r=[];for(const a of e)if(r.push(a),r.length===t)break;return r}const hr=2,Za=4,Ea=8,Gs=1<<24,da=16,ln=32,Ia=64,co=128,Ur=512,vr=1024,pr=2048,on=4096,Cr=8192,_n=16384,es=32768,jn=65536,ii=1<<17,Ud=1<<18,ts=1<<19,Gi=1<<20,xn=1<<25,za=65536,uo=1<<21,$o=1<<22,aa=1<<23,wn=Symbol("$state"),Hi=Symbol("legacy props"),Wd=Symbol(""),ga=new class extends Error{constructor(){super(...arguments);en(this,"name","StaleReactionError");en(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var Di;const Ui=!!((Di=globalThis.document)!=null&&Di.contentType)&&globalThis.document.contentType.includes("xml");function Kd(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function Yd(e,t,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function Xd(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function Jd(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Qd(e){throw new Error("https://svelte.dev/e/effect_orphan")}function Zd(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function ec(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function tc(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function rc(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function nc(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function ac(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const sc=1,oc=2,Wi=4,ic=8,lc=16,dc=1,cc=2,Ki=4,uc=8,fc=16,vc=1,pc=2,tr=Symbol(),Yi="http://www.w3.org/1999/xhtml",Xi="http://www.w3.org/2000/svg",mc="http://www.w3.org/1998/Math/MathML",hc="@attach";function gc(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function xc(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Ji(e){return e===this.v}function bc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function Qi(e){return!bc(e,this.v)}let Cs=!1,_c=!1;function wc(){Cs=!0}let rr=null;function Wa(e){rr=e}function Xr(e,t=!1,r){rr={p:rr,i:!1,c:null,e:null,s:e,x:null,l:Cs&&!t?{s:null,u:null,$:[]}:null}}function Jr(e){var t=rr,r=t.e;if(r!==null){t.e=null;for(var a of r)xl(a)}return t.i=!0,rr=t.p,{}}function Ss(){return!Cs||rr!==null&&rr.l===null}let xa=[];function Zi(){var e=xa;xa=[],lo(e)}function yn(e){if(xa.length===0&&!ps){var t=xa;queueMicrotask(()=>{t===xa&&Zi()})}xa.push(e)}function yc(){for(;xa.length>0;)Zi()}function el(e){var t=Ue;if(t===null)return He.f|=aa,e;if((t.f&es)===0&&(t.f&Za)===0)throw e;ea(e,t)}function ea(e,t){for(;t!==null;){if((t.f&co)!==0){if((t.f&es)===0)throw e;try{t.b.error(e);return}catch(r){e=r}}t=t.parent}throw e}const kc=-7169;function jt(e,t){e.f=e.f&kc|t}function Lo(e){(e.f&Ur)!==0||e.deps===null?jt(e,vr):jt(e,on)}function tl(e){if(e!==null)for(const t of e)(t.f&hr)===0||(t.f&za)===0||(t.f^=za,tl(t.deps))}function rl(e,t,r){(e.f&pr)!==0?t.add(e):(e.f&on)!==0&&r.add(e),tl(e.deps),jt(e,vr)}const Ts=new Set;let Ve=null,fo=null,fr=null,Ar=[],Hs=null,ps=!1,Ka=null,Cc=1;var Jn,Da,wa,ja,Va,Fa,Qn,pn,qa,Pr,vo,po,mo,ho;const Wo=class Wo{constructor(){Xe(this,Pr);en(this,"id",Cc++);en(this,"current",new Map);en(this,"previous",new Map);Xe(this,Jn,new Set);Xe(this,Da,new Set);Xe(this,wa,0);Xe(this,ja,0);Xe(this,Va,null);Xe(this,Fa,new Set);Xe(this,Qn,new Set);Xe(this,pn,new Map);en(this,"is_fork",!1);Xe(this,qa,!1)}skip_effect(t){M(this,pn).has(t)||M(this,pn).set(t,{d:[],m:[]})}unskip_effect(t){var r=M(this,pn).get(t);if(r){M(this,pn).delete(t);for(var a of r.d)jt(a,pr),bn(a);for(a of r.m)jt(a,on),bn(a)}}process(t){var s;Ar=[],this.apply();var r=Ka=[],a=[];for(const o of t)Yt(this,Pr,po).call(this,o,r,a);if(Ka=null,Yt(this,Pr,vo).call(this)){Yt(this,Pr,mo).call(this,a),Yt(this,Pr,mo).call(this,r);for(const[o,i]of M(this,pn))ol(o,i)}else{fo=this,Ve=null;for(const o of M(this,Jn))o(this);M(this,Jn).clear(),M(this,wa)===0&&Yt(this,Pr,ho).call(this),li(a),li(r),M(this,Fa).clear(),M(this,Qn).clear(),fo=null,(s=M(this,Va))==null||s.resolve()}fr=null}capture(t,r){r!==tr&&!this.previous.has(t)&&this.previous.set(t,r),(t.f&aa)===0&&(this.current.set(t,t.v),fr==null||fr.set(t,t.v))}activate(){Ve=this,this.apply()}deactivate(){Ve===this&&(Ve=null,fr=null)}flush(){var t;if(Ar.length>0)Ve=this,nl();else if(M(this,wa)===0&&!this.is_fork){for(const r of M(this,Jn))r(this);M(this,Jn).clear(),Yt(this,Pr,ho).call(this),(t=M(this,Va))==null||t.resolve()}this.deactivate()}discard(){for(const t of M(this,Da))t(this);M(this,Da).clear()}increment(t){je(this,wa,M(this,wa)+1),t&&je(this,ja,M(this,ja)+1)}decrement(t){je(this,wa,M(this,wa)-1),t&&je(this,ja,M(this,ja)-1),!M(this,qa)&&(je(this,qa,!0),yn(()=>{je(this,qa,!1),Yt(this,Pr,vo).call(this)?Ar.length>0&&this.flush():this.revive()}))}revive(){for(const t of M(this,Fa))M(this,Qn).delete(t),jt(t,pr),bn(t);for(const t of M(this,Qn))jt(t,on),bn(t);this.flush()}oncommit(t){M(this,Jn).add(t)}ondiscard(t){M(this,Da).add(t)}settled(){return(M(this,Va)??je(this,Va,qi())).promise}static ensure(){if(Ve===null){const t=Ve=new Wo;Ts.add(Ve),ps||yn(()=>{Ve===t&&t.flush()})}return Ve}apply(){}};Jn=new WeakMap,Da=new WeakMap,wa=new WeakMap,ja=new WeakMap,Va=new WeakMap,Fa=new WeakMap,Qn=new WeakMap,pn=new WeakMap,qa=new WeakMap,Pr=new WeakSet,vo=function(){return this.is_fork||M(this,ja)>0},po=function(t,r,a){t.f^=vr;for(var s=t.first;s!==null;){var o=s.f,i=(o&(ln|Ia))!==0,l=i&&(o&vr)!==0,c=(o&Cr)!==0,f=l||M(this,pn).has(s);if(!f&&s.fn!==null){i?c||(s.f^=vr):(o&Za)!==0?r.push(s):(o&(Ea|Gs))!==0&&c?a.push(s):zs(s)&&(Xa(s),(o&da)!==0&&(M(this,Qn).add(s),c&&jt(s,pr)));var p=s.first;if(p!==null){s=p;continue}}for(;s!==null;){var _=s.next;if(_!==null){s=_;break}s=s.parent}}},mo=function(t){for(var r=0;r<t.length;r+=1)rl(t[r],M(this,Fa),M(this,Qn))},ho=function(){var o;if(Ts.size>1){this.previous.clear();var t=Ve,r=fr,a=!0;for(const i of Ts){if(i===this){a=!1;continue}const l=[];for(const[f,p]of this.current){if(i.current.has(f))if(a&&p!==i.current.get(f))i.current.set(f,p);else continue;l.push(f)}if(l.length===0)continue;const c=[...i.current.keys()].filter(f=>!this.current.has(f));if(c.length>0){var s=Ar;Ar=[];const f=new Set,p=new Map;for(const _ of l)al(_,c,f,p);if(Ar.length>0){Ve=i,i.apply();for(const _ of Ar)Yt(o=i,Pr,po).call(o,_,[],[]);i.deactivate()}Ar=s}}Ve=t,fr=r}M(this,pn).clear(),Ts.delete(this)};let sa=Wo;function Sc(e){var t=ps;ps=!0;try{for(var r;;){if(yc(),Ar.length===0&&(Ve==null||Ve.flush(),Ar.length===0))return Hs=null,r;nl()}}finally{ps=t}}function nl(){var e=null;try{for(var t=0;Ar.length>0;){var r=sa.ensure();if(t++>1e3){var a,s;Mc()}r.process(Ar),oa.clear()}}finally{Ar=[],Hs=null,Ka=null}}function Mc(){try{Zd()}catch(e){ea(e,Hs)}}let tn=null;function li(e){var t=e.length;if(t!==0){for(var r=0;r<t;){var a=e[r++];if((a.f&(_n|Cr))===0&&zs(a)&&(tn=new Set,Xa(a),a.deps===null&&a.first===null&&a.nodes===null&&a.teardown===null&&a.ac===null&&yl(a),(tn==null?void 0:tn.size)>0)){oa.clear();for(const s of tn){if((s.f&(_n|Cr))!==0)continue;const o=[s];let i=s.parent;for(;i!==null;)tn.has(i)&&(tn.delete(i),o.push(i)),i=i.parent;for(let l=o.length-1;l>=0;l--){const c=o[l];(c.f&(_n|Cr))===0&&Xa(c)}}tn.clear()}}tn=null}}function al(e,t,r,a){if(!r.has(e)&&(r.add(e),e.reactions!==null))for(const s of e.reactions){const o=s.f;(o&hr)!==0?al(s,t,r,a):(o&($o|da))!==0&&(o&pr)===0&&sl(s,t,a)&&(jt(s,pr),bn(s))}}function sl(e,t,r){const a=r.get(e);if(a!==void 0)return a;if(e.deps!==null)for(const s of e.deps){if(Ua.call(t,s))return!0;if((s.f&hr)!==0&&sl(s,t,r))return r.set(s,!0),!0}return r.set(e,!1),!1}function bn(e){var t=Hs=e,r=t.b;if(r!=null&&r.is_pending&&(e.f&(Za|Ea|Gs))!==0&&(e.f&es)===0){r.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var a=t.f;if(Ka!==null&&t===Ue&&(e.f&Ea)===0)return;if((a&(Ia|ln))!==0){if((a&vr)===0)return;t.f^=vr}}Ar.push(t)}function ol(e,t){if(!((e.f&ln)!==0&&(e.f&vr)!==0)){(e.f&pr)!==0?t.d.push(e):(e.f&on)!==0&&t.m.push(e),jt(e,vr);for(var r=e.first;r!==null;)ol(r,t),r=r.next}}function Ec(e){let t=0,r=ia(0),a;return()=>{jo()&&(n(r),Fo(()=>(t===0&&(a=Aa(()=>e(()=>hs(r)))),t+=1,()=>{yn(()=>{t-=1,t===0&&(a==null||a(),a=void 0,hs(r))})})))}}var zc=jn|ts;function Ac(e,t,r,a){new Tc(e,t,r,a)}var Hr,Io,mn,ya,zr,hn,Fr,rn,$n,ka,Zn,Ba,Ga,Ha,Ln,Fs,Jt,Ic,Pc,Nc,go,Ls,Os,xo;class Tc{constructor(t,r,a,s){Xe(this,Jt);en(this,"parent");en(this,"is_pending",!1);en(this,"transform_error");Xe(this,Hr);Xe(this,Io,null);Xe(this,mn);Xe(this,ya);Xe(this,zr);Xe(this,hn,null);Xe(this,Fr,null);Xe(this,rn,null);Xe(this,$n,null);Xe(this,ka,0);Xe(this,Zn,0);Xe(this,Ba,!1);Xe(this,Ga,new Set);Xe(this,Ha,new Set);Xe(this,Ln,null);Xe(this,Fs,Ec(()=>(je(this,Ln,ia(M(this,ka))),()=>{je(this,Ln,null)})));var o;je(this,Hr,t),je(this,mn,r),je(this,ya,i=>{var l=Ue;l.b=this,l.f|=co,a(i)}),this.parent=Ue.b,this.transform_error=s??((o=this.parent)==null?void 0:o.transform_error)??(i=>i),je(this,zr,rs(()=>{Yt(this,Jt,go).call(this)},zc))}defer_effect(t){rl(t,M(this,Ga),M(this,Ha))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!M(this,mn).pending}update_pending_count(t){Yt(this,Jt,xo).call(this,t),je(this,ka,M(this,ka)+t),!(!M(this,Ln)||M(this,Ba))&&(je(this,Ba,!0),yn(()=>{je(this,Ba,!1),M(this,Ln)&&Ya(M(this,Ln),M(this,ka))}))}get_effect_pending(){return M(this,Fs).call(this),n(M(this,Ln))}error(t){var r=M(this,mn).onerror;let a=M(this,mn).failed;if(!r&&!a)throw t;M(this,hn)&&(mr(M(this,hn)),je(this,hn,null)),M(this,Fr)&&(mr(M(this,Fr)),je(this,Fr,null)),M(this,rn)&&(mr(M(this,rn)),je(this,rn,null));var s=!1,o=!1;const i=()=>{if(s){xc();return}s=!0,o&&ac(),M(this,rn)!==null&&Sa(M(this,rn),()=>{je(this,rn,null)}),Yt(this,Jt,Os).call(this,()=>{sa.ensure(),Yt(this,Jt,go).call(this)})},l=c=>{try{o=!0,r==null||r(c,i),o=!1}catch(f){ea(f,M(this,zr)&&M(this,zr).parent)}a&&je(this,rn,Yt(this,Jt,Os).call(this,()=>{sa.ensure();try{return Ir(()=>{var f=Ue;f.b=this,f.f|=co,a(M(this,Hr),()=>c,()=>i)})}catch(f){return ea(f,M(this,zr).parent),null}}))};yn(()=>{var c;try{c=this.transform_error(t)}catch(f){ea(f,M(this,zr)&&M(this,zr).parent);return}c!==null&&typeof c=="object"&&typeof c.then=="function"?c.then(l,f=>ea(f,M(this,zr)&&M(this,zr).parent)):l(c)})}}Hr=new WeakMap,Io=new WeakMap,mn=new WeakMap,ya=new WeakMap,zr=new WeakMap,hn=new WeakMap,Fr=new WeakMap,rn=new WeakMap,$n=new WeakMap,ka=new WeakMap,Zn=new WeakMap,Ba=new WeakMap,Ga=new WeakMap,Ha=new WeakMap,Ln=new WeakMap,Fs=new WeakMap,Jt=new WeakSet,Ic=function(){try{je(this,hn,Ir(()=>M(this,ya).call(this,M(this,Hr))))}catch(t){this.error(t)}},Pc=function(t){const r=M(this,mn).failed;r&&je(this,rn,Ir(()=>{r(M(this,Hr),()=>t,()=>()=>{})}))},Nc=function(){const t=M(this,mn).pending;t&&(this.is_pending=!0,je(this,Fr,Ir(()=>t(M(this,Hr)))),yn(()=>{var r=je(this,$n,document.createDocumentFragment()),a=kn();r.append(a),je(this,hn,Yt(this,Jt,Os).call(this,()=>(sa.ensure(),Ir(()=>M(this,ya).call(this,a))))),M(this,Zn)===0&&(M(this,Hr).before(r),je(this,$n,null),Sa(M(this,Fr),()=>{je(this,Fr,null)}),Yt(this,Jt,Ls).call(this))}))},go=function(){try{if(this.is_pending=this.has_pending_snippet(),je(this,Zn,0),je(this,ka,0),je(this,hn,Ir(()=>{M(this,ya).call(this,M(this,Hr))})),M(this,Zn)>0){var t=je(this,$n,document.createDocumentFragment());Go(M(this,hn),t);const r=M(this,mn).pending;je(this,Fr,Ir(()=>r(M(this,Hr))))}else Yt(this,Jt,Ls).call(this)}catch(r){this.error(r)}},Ls=function(){this.is_pending=!1;for(const t of M(this,Ga))jt(t,pr),bn(t);for(const t of M(this,Ha))jt(t,on),bn(t);M(this,Ga).clear(),M(this,Ha).clear()},Os=function(t){var r=Ue,a=He,s=rr;Yr(M(this,zr)),Kr(M(this,zr)),Wa(M(this,zr).ctx);try{return t()}catch(o){return el(o),null}finally{Yr(r),Kr(a),Wa(s)}},xo=function(t){var r;if(!this.has_pending_snippet()){this.parent&&Yt(r=this.parent,Jt,xo).call(r,t);return}je(this,Zn,M(this,Zn)+t),M(this,Zn)===0&&(Yt(this,Jt,Ls).call(this),M(this,Fr)&&Sa(M(this,Fr),()=>{je(this,Fr,null)}),M(this,$n)&&(M(this,Hr).before(M(this,$n)),je(this,$n,null)))};function il(e,t,r,a){const s=Ss()?Ms:Oo;var o=e.filter(_=>!_.settled);if(r.length===0&&o.length===0){a(t.map(s));return}var i=Ue,l=$c(),c=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(_=>_.promise)):null;function f(_){l();try{a(_)}catch(w){(i.f&_n)===0&&ea(w,i)}bo()}if(r.length===0){c.then(()=>f(t.map(s)));return}function p(){l(),Promise.all(r.map(_=>Oc(_))).then(_=>f([...t.map(s),..._])).catch(_=>ea(_,i))}c?c.then(p):p()}function $c(){var e=Ue,t=He,r=rr,a=Ve;return function(o=!0){Yr(e),Kr(t),Wa(r),o&&(a==null||a.activate())}}function bo(e=!0){Yr(null),Kr(null),Wa(null),e&&(Ve==null||Ve.deactivate())}function Lc(){var e=Ue.b,t=Ve,r=e.is_rendered();return e.update_pending_count(1),t.increment(r),()=>{e.update_pending_count(-1),t.decrement(r)}}function Ms(e){var t=hr|pr,r=He!==null&&(He.f&hr)!==0?He:null;return Ue!==null&&(Ue.f|=ts),{ctx:rr,deps:null,effects:null,equals:Ji,f:t,fn:e,reactions:null,rv:0,v:tr,wv:0,parent:r??Ue,ac:null}}function Oc(e,t,r){Ue===null&&Kd();var s=void 0,o=ia(tr),i=!He,l=new Map;return Xc(()=>{var w;var c=qi();s=c.promise;try{Promise.resolve(e()).then(c.resolve,c.reject).finally(bo)}catch(A){c.reject(A),bo()}var f=Ve;if(i){var p=Lc();(w=l.get(f))==null||w.reject(ga),l.delete(f),l.set(f,c)}const _=(A,k=void 0)=>{if(f.activate(),k)k!==ga&&(o.f|=aa,Ya(o,k));else{(o.f&aa)!==0&&(o.f^=aa),Ya(o,A);for(const[P,y]of l){if(l.delete(P),P===f)break;y.reject(ga)}}p&&p()};c.promise.then(_,A=>_(null,A||"unknown"))}),Ws(()=>{for(const c of l.values())c.reject(ga)}),new Promise(c=>{function f(p){function _(){p===s?c(o):f(s)}p.then(_,_)}f(s)})}function U(e){const t=Ms(e);return Sl(t),t}function Oo(e){const t=Ms(e);return t.equals=Qi,t}function Rc(e){var t=e.effects;if(t!==null){e.effects=null;for(var r=0;r<t.length;r+=1)mr(t[r])}}function Dc(e){for(var t=e.parent;t!==null;){if((t.f&hr)===0)return(t.f&_n)===0?t:null;t=t.parent}return null}function Ro(e){var t,r=Ue;Yr(Dc(e));try{e.f&=~za,Rc(e),t=Al(e)}finally{Yr(r)}return t}function ll(e){var t=Ro(e);if(!e.equals(t)&&(e.wv=El(),(!(Ve!=null&&Ve.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){jt(e,vr);return}la||(fr!==null?(jo()||Ve!=null&&Ve.is_fork)&&fr.set(e,t):Lo(e))}function jc(e){var t,r;if(e.effects!==null)for(const a of e.effects)(a.teardown||a.ac)&&((t=a.teardown)==null||t.call(a),(r=a.ac)==null||r.abort(ga),a.teardown=Gd,a.ac=null,ws(a,0),qo(a))}function dl(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&Xa(t)}let _o=new Set;const oa=new Map;let cl=!1;function ia(e,t){var r={f:0,v:e,reactions:null,equals:Ji,rv:0,wv:0};return r}function W(e,t){const r=ia(e);return Sl(r),r}function Vc(e,t=!1,r=!0){var s;const a=ia(e);return t||(a.equals=Qi),Cs&&r&&rr!==null&&rr.l!==null&&((s=rr.l).s??(s.s=[])).push(a),a}function u(e,t,r=!1){He!==null&&(!sn||(He.f&ii)!==0)&&Ss()&&(He.f&(hr|da|$o|ii))!==0&&(Wr===null||!Ua.call(Wr,e))&&nc();let a=r?Pt(t):t;return Ya(e,a)}function Ya(e,t){if(!e.equals(t)){var r=e.v;la?oa.set(e,t):oa.set(e,r),e.v=t;var a=sa.ensure();if(a.capture(e,r),(e.f&hr)!==0){const s=e;(e.f&pr)!==0&&Ro(s),Lo(s)}e.wv=El(),ul(e,pr),Ss()&&Ue!==null&&(Ue.f&vr)!==0&&(Ue.f&(ln|Ia))===0&&(Gr===null?Qc([e]):Gr.push(e)),!a.is_fork&&_o.size>0&&!cl&&Fc()}return t}function Fc(){cl=!1;for(const e of _o)(e.f&vr)!==0&&jt(e,on),zs(e)&&Xa(e);_o.clear()}function ms(e,t=1){var r=n(e),a=t===1?r++:r--;return u(e,r),a}function hs(e){u(e,e.v+1)}function ul(e,t){var r=e.reactions;if(r!==null)for(var a=Ss(),s=r.length,o=0;o<s;o++){var i=r[o],l=i.f;if(!(!a&&i===Ue)){var c=(l&pr)===0;if(c&&jt(i,t),(l&hr)!==0){var f=i;fr==null||fr.delete(f),(l&za)===0&&(l&Ur&&(i.f|=za),ul(f,on))}else c&&((l&da)!==0&&tn!==null&&tn.add(i),bn(i))}}}function Pt(e){if(typeof e!="object"||e===null||wn in e)return e;const t=No(e);if(t!==qd&&t!==Bd)return e;var r=new Map,a=Po(e),s=W(0),o=Ma,i=l=>{if(Ma===o)return l();var c=He,f=Ma;Kr(null),fi(o);var p=l();return Kr(c),fi(f),p};return a&&r.set("length",W(e.length)),new Proxy(e,{defineProperty(l,c,f){(!("value"in f)||f.configurable===!1||f.enumerable===!1||f.writable===!1)&&tc();var p=r.get(c);return p===void 0?i(()=>{var _=W(f.value);return r.set(c,_),_}):u(p,f.value,!0),!0},deleteProperty(l,c){var f=r.get(c);if(f===void 0){if(c in l){const p=i(()=>W(tr));r.set(c,p),hs(s)}}else u(f,tr),hs(s);return!0},get(l,c,f){var A;if(c===wn)return e;var p=r.get(c),_=c in l;if(p===void 0&&(!_||(A=na(l,c))!=null&&A.writable)&&(p=i(()=>{var k=Pt(_?l[c]:tr),P=W(k);return P}),r.set(c,p)),p!==void 0){var w=n(p);return w===tr?void 0:w}return Reflect.get(l,c,f)},getOwnPropertyDescriptor(l,c){var f=Reflect.getOwnPropertyDescriptor(l,c);if(f&&"value"in f){var p=r.get(c);p&&(f.value=n(p))}else if(f===void 0){var _=r.get(c),w=_==null?void 0:_.v;if(_!==void 0&&w!==tr)return{enumerable:!0,configurable:!0,value:w,writable:!0}}return f},has(l,c){var w;if(c===wn)return!0;var f=r.get(c),p=f!==void 0&&f.v!==tr||Reflect.has(l,c);if(f!==void 0||Ue!==null&&(!p||(w=na(l,c))!=null&&w.writable)){f===void 0&&(f=i(()=>{var A=p?Pt(l[c]):tr,k=W(A);return k}),r.set(c,f));var _=n(f);if(_===tr)return!1}return p},set(l,c,f,p){var J;var _=r.get(c),w=c in l;if(a&&c==="length")for(var A=f;A<_.v;A+=1){var k=r.get(A+"");k!==void 0?u(k,tr):A in l&&(k=i(()=>W(tr)),r.set(A+"",k))}if(_===void 0)(!w||(J=na(l,c))!=null&&J.writable)&&(_=i(()=>W(void 0)),u(_,Pt(f)),r.set(c,_));else{w=_.v!==tr;var P=i(()=>Pt(f));u(_,P)}var y=Reflect.getOwnPropertyDescriptor(l,c);if(y!=null&&y.set&&y.set.call(p,f),!w){if(a&&typeof c=="string"){var C=r.get("length"),V=Number(c);Number.isInteger(V)&&V>=C.v&&u(C,V+1)}hs(s)}return!0},ownKeys(l){n(s);var c=Reflect.ownKeys(l).filter(_=>{var w=r.get(_);return w===void 0||w.v!==tr});for(var[f,p]of r)p.v!==tr&&!(f in l)&&c.push(f);return c},setPrototypeOf(){rc()}})}function di(e){try{if(e!==null&&typeof e=="object"&&wn in e)return e[wn]}catch{}return e}function qc(e,t){return Object.is(di(e),di(t))}var wo,fl,vl,pl;function Bc(){if(wo===void 0){wo=window,fl=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,r=Text.prototype;vl=na(t,"firstChild").get,pl=na(t,"nextSibling").get,oi(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),oi(r)&&(r.__t=void 0)}}function kn(e=""){return document.createTextNode(e)}function Rn(e){return vl.call(e)}function Es(e){return pl.call(e)}function d(e,t){return Rn(e)}function ee(e,t=!1){{var r=Rn(e);return r instanceof Comment&&r.data===""?Es(r):r}}function m(e,t=1,r=!1){let a=e;for(;t--;)a=Es(a);return a}function Gc(e){e.textContent=""}function ml(){return!1}function Do(e,t,r){return document.createElementNS(t??Yi,e,void 0)}function hl(e,t){if(t){const r=document.body;e.autofocus=!0,yn(()=>{document.activeElement===r&&e.focus()})}}let ci=!1;function Hc(){ci||(ci=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const r of e.target.elements)(t=r.__on_r)==null||t.call(r)})},{capture:!0}))}function Us(e){var t=He,r=Ue;Kr(null),Yr(null);try{return e()}finally{Kr(t),Yr(r)}}function Uc(e,t,r,a=r){e.addEventListener(t,()=>Us(r));const s=e.__on_r;s?e.__on_r=()=>{s(),a(!0)}:e.__on_r=()=>a(!0),Hc()}function gl(e){Ue===null&&(He===null&&Qd(),Jd()),la&&Xd()}function Wc(e,t){var r=t.last;r===null?t.last=t.first=e:(r.next=e,e.prev=r,t.last=e)}function dn(e,t){var r=Ue;r!==null&&(r.f&Cr)!==0&&(e|=Cr);var a={ctx:rr,deps:null,nodes:null,f:e|pr|Ur,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},s=a;if((e&Za)!==0)Ka!==null?Ka.push(a):bn(a);else if(t!==null){try{Xa(a)}catch(i){throw mr(a),i}s.deps===null&&s.teardown===null&&s.nodes===null&&s.first===s.last&&(s.f&ts)===0&&(s=s.first,(e&da)!==0&&(e&jn)!==0&&s!==null&&(s.f|=jn))}if(s!==null&&(s.parent=r,r!==null&&Wc(s,r),He!==null&&(He.f&hr)!==0&&(e&Ia)===0)){var o=He;(o.effects??(o.effects=[])).push(s)}return a}function jo(){return He!==null&&!sn}function Ws(e){const t=dn(Ea,null);return jt(t,vr),t.teardown=e,t}function ta(e){gl();var t=Ue.f,r=!He&&(t&ln)!==0&&(t&es)===0;if(r){var a=rr;(a.e??(a.e=[])).push(e)}else return xl(e)}function xl(e){return dn(Za|Gi,e)}function Kc(e){return gl(),dn(Ea|Gi,e)}function Yc(e){sa.ensure();const t=dn(Ia|ts,e);return(r={})=>new Promise(a=>{r.outro?Sa(t,()=>{mr(t),a(void 0)}):(mr(t),a(void 0))})}function Vo(e){return dn(Za,e)}function Xc(e){return dn($o|ts,e)}function Fo(e,t=0){return dn(Ea|t,e)}function L(e,t=[],r=[],a=[]){il(a,t,r,s=>{dn(Ea,()=>e(...s.map(n)))})}function rs(e,t=0){var r=dn(da|t,e);return r}function bl(e,t=0){var r=dn(Gs|t,e);return r}function Ir(e){return dn(ln|ts,e)}function _l(e){var t=e.teardown;if(t!==null){const r=la,a=He;ui(!0),Kr(null);try{t.call(null)}finally{ui(r),Kr(a)}}}function qo(e,t=!1){var r=e.first;for(e.first=e.last=null;r!==null;){const s=r.ac;s!==null&&Us(()=>{s.abort(ga)});var a=r.next;(r.f&Ia)!==0?r.parent=null:mr(r,t),r=a}}function Jc(e){for(var t=e.first;t!==null;){var r=t.next;(t.f&ln)===0&&mr(t),t=r}}function mr(e,t=!0){var r=!1;(t||(e.f&Ud)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(wl(e.nodes.start,e.nodes.end),r=!0),qo(e,t&&!r),ws(e,0),jt(e,_n);var a=e.nodes&&e.nodes.t;if(a!==null)for(const o of a)o.stop();_l(e);var s=e.parent;s!==null&&s.first!==null&&yl(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function wl(e,t){for(;e!==null;){var r=e===t?null:Es(e);e.remove(),e=r}}function yl(e){var t=e.parent,r=e.prev,a=e.next;r!==null&&(r.next=a),a!==null&&(a.prev=r),t!==null&&(t.first===e&&(t.first=a),t.last===e&&(t.last=r))}function Sa(e,t,r=!0){var a=[];kl(e,a,!0);var s=()=>{r&&mr(e),t&&t()},o=a.length;if(o>0){var i=()=>--o||s();for(var l of a)l.out(i)}else s()}function kl(e,t,r){if((e.f&Cr)===0){e.f^=Cr;var a=e.nodes&&e.nodes.t;if(a!==null)for(const l of a)(l.is_global||r)&&t.push(l);for(var s=e.first;s!==null;){var o=s.next,i=(s.f&jn)!==0||(s.f&ln)!==0&&(e.f&da)!==0;kl(s,t,i?r:!1),s=o}}}function Bo(e){Cl(e,!0)}function Cl(e,t){if((e.f&Cr)!==0){e.f^=Cr;for(var r=e.first;r!==null;){var a=r.next,s=(r.f&jn)!==0||(r.f&ln)!==0;Cl(r,s?t:!1),r=a}var o=e.nodes&&e.nodes.t;if(o!==null)for(const i of o)(i.is_global||t)&&i.in()}}function Go(e,t){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end;r!==null;){var s=r===a?null:Es(r);t.append(r),r=s}}let Rs=!1,la=!1;function ui(e){la=e}let He=null,sn=!1;function Kr(e){He=e}let Ue=null;function Yr(e){Ue=e}let Wr=null;function Sl(e){He!==null&&(Wr===null?Wr=[e]:Wr.push(e))}let Tr=null,Vr=0,Gr=null;function Qc(e){Gr=e}let Ml=1,ba=0,Ma=ba;function fi(e){Ma=e}function El(){return++Ml}function zs(e){var t=e.f;if((t&pr)!==0)return!0;if(t&hr&&(e.f&=~za),(t&on)!==0){for(var r=e.deps,a=r.length,s=0;s<a;s++){var o=r[s];if(zs(o)&&ll(o),o.wv>e.wv)return!0}(t&Ur)!==0&&fr===null&&jt(e,vr)}return!1}function zl(e,t,r=!0){var a=e.reactions;if(a!==null&&!(Wr!==null&&Ua.call(Wr,e)))for(var s=0;s<a.length;s++){var o=a[s];(o.f&hr)!==0?zl(o,t,!1):t===o&&(r?jt(o,pr):(o.f&vr)!==0&&jt(o,on),bn(o))}}function Al(e){var P;var t=Tr,r=Vr,a=Gr,s=He,o=Wr,i=rr,l=sn,c=Ma,f=e.f;Tr=null,Vr=0,Gr=null,He=(f&(ln|Ia))===0?e:null,Wr=null,Wa(e.ctx),sn=!1,Ma=++ba,e.ac!==null&&(Us(()=>{e.ac.abort(ga)}),e.ac=null);try{e.f|=uo;var p=e.fn,_=p();e.f|=es;var w=e.deps,A=Ve==null?void 0:Ve.is_fork;if(Tr!==null){var k;if(A||ws(e,Vr),w!==null&&Vr>0)for(w.length=Vr+Tr.length,k=0;k<Tr.length;k++)w[Vr+k]=Tr[k];else e.deps=w=Tr;if(jo()&&(e.f&Ur)!==0)for(k=Vr;k<w.length;k++)((P=w[k]).reactions??(P.reactions=[])).push(e)}else!A&&w!==null&&Vr<w.length&&(ws(e,Vr),w.length=Vr);if(Ss()&&Gr!==null&&!sn&&w!==null&&(e.f&(hr|on|pr))===0)for(k=0;k<Gr.length;k++)zl(Gr[k],e);if(s!==null&&s!==e){if(ba++,s.deps!==null)for(let y=0;y<r;y+=1)s.deps[y].rv=ba;if(t!==null)for(const y of t)y.rv=ba;Gr!==null&&(a===null?a=Gr:a.push(...Gr))}return(e.f&aa)!==0&&(e.f^=aa),_}catch(y){return el(y)}finally{e.f^=uo,Tr=t,Vr=r,Gr=a,He=s,Wr=o,Wa(i),sn=l,Ma=c}}function Zc(e,t){let r=t.reactions;if(r!==null){var a=Vd.call(r,e);if(a!==-1){var s=r.length-1;s===0?r=t.reactions=null:(r[a]=r[s],r.pop())}}if(r===null&&(t.f&hr)!==0&&(Tr===null||!Ua.call(Tr,t))){var o=t;(o.f&Ur)!==0&&(o.f^=Ur,o.f&=~za),Lo(o),jc(o),ws(o,0)}}function ws(e,t){var r=e.deps;if(r!==null)for(var a=t;a<r.length;a++)Zc(e,r[a])}function Xa(e){var t=e.f;if((t&_n)===0){jt(e,vr);var r=Ue,a=Rs;Ue=e,Rs=!0;try{(t&(da|Gs))!==0?Jc(e):qo(e),_l(e);var s=Al(e);e.teardown=typeof s=="function"?s:null,e.wv=Ml;var o;io&&_c&&(e.f&pr)!==0&&e.deps}finally{Rs=a,Ue=r}}}async function eu(){await Promise.resolve(),Sc()}function n(e){var t=e.f,r=(t&hr)!==0;if(He!==null&&!sn){var a=Ue!==null&&(Ue.f&_n)!==0;if(!a&&(Wr===null||!Ua.call(Wr,e))){var s=He.deps;if((He.f&uo)!==0)e.rv<ba&&(e.rv=ba,Tr===null&&s!==null&&s[Vr]===e?Vr++:Tr===null?Tr=[e]:Tr.push(e));else{(He.deps??(He.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[He]:Ua.call(o,He)||o.push(He)}}}if(la&&oa.has(e))return oa.get(e);if(r){var i=e;if(la){var l=i.v;return((i.f&vr)===0&&i.reactions!==null||Il(i))&&(l=Ro(i)),oa.set(i,l),l}var c=(i.f&Ur)===0&&!sn&&He!==null&&(Rs||(He.f&Ur)!==0),f=(i.f&es)===0;zs(i)&&(c&&(i.f|=Ur),ll(i)),c&&!f&&(dl(i),Tl(i))}if(fr!=null&&fr.has(e))return fr.get(e);if((e.f&aa)!==0)throw e.v;return e.v}function Tl(e){if(e.f|=Ur,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&hr)!==0&&(t.f&Ur)===0&&(dl(t),Tl(t))}function Il(e){if(e.v===tr)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(oa.has(t)||(t.f&hr)!==0&&Il(t))return!0;return!1}function Aa(e){var t=sn;try{return sn=!0,e()}finally{sn=t}}function ha(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(wn in e)yo(e);else if(!Array.isArray(e))for(let t in e){const r=e[t];typeof r=="object"&&r&&wn in r&&yo(r)}}}function yo(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let a in e)try{yo(e[a],t)}catch{}const r=No(e);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const a=Fi(r);for(let s in a){const o=a[s].get;if(o)try{o.call(e)}catch{}}}}}function tu(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const ru=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function nu(e){return ru.includes(e)}const au={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function su(e){return e=e.toLowerCase(),au[e]??e}const ou=["touchstart","touchmove"];function iu(e){return ou.includes(e)}const _a=Symbol("events"),Pl=new Set,ko=new Set;function Nl(e,t,r,a={}){function s(o){if(a.capture||Co.call(t,o),!o.cancelBubble)return Us(()=>r==null?void 0:r.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?yn(()=>{t.addEventListener(e,s,a)}):t.addEventListener(e,s,a),s}function Ra(e,t,r,a,s){var o={capture:a,passive:s},i=Nl(e,t,r,o);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&Ws(()=>{t.removeEventListener(e,i,o)})}function ne(e,t,r){(t[_a]??(t[_a]={}))[e]=r}function Vn(e){for(var t=0;t<e.length;t++)Pl.add(e[t]);for(var r of ko)r(e)}let vi=null;function Co(e){var y,C;var t=this,r=t.ownerDocument,a=e.type,s=((y=e.composedPath)==null?void 0:y.call(e))||[],o=s[0]||e.target;vi=e;var i=0,l=vi===e&&e[_a];if(l){var c=s.indexOf(l);if(c!==-1&&(t===document||t===window)){e[_a]=t;return}var f=s.indexOf(t);if(f===-1)return;c<=f&&(i=c)}if(o=s[i]||e.target,o!==t){Fd(e,"currentTarget",{configurable:!0,get(){return o||r}});var p=He,_=Ue;Kr(null),Yr(null);try{for(var w,A=[];o!==null;){var k=o.assignedSlot||o.parentNode||o.host||null;try{var P=(C=o[_a])==null?void 0:C[a];P!=null&&(!o.disabled||e.target===o)&&P.call(o,e)}catch(V){w?A.push(V):w=V}if(e.cancelBubble||k===t||k===null)break;o=k}if(w){for(let V of A)queueMicrotask(()=>{throw V});throw w}}finally{e[_a]=t,delete e.currentTarget,Kr(p),Yr(_)}}}var ji;const eo=((ji=globalThis==null?void 0:globalThis.window)==null?void 0:ji.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function lu(e){return(eo==null?void 0:eo.createHTML(e))??e}function $l(e){var t=Do("template");return t.innerHTML=lu(e.replaceAll("<!>","<!---->")),t.content}function Ta(e,t){var r=Ue;r.nodes===null&&(r.nodes={start:e,end:t,a:null,t:null})}function h(e,t){var r=(t&vc)!==0,a=(t&pc)!==0,s,o=!e.startsWith("<!>");return()=>{s===void 0&&(s=$l(o?e:"<!>"+e),r||(s=Rn(s)));var i=a||fl?document.importNode(s,!0):s.cloneNode(!0);if(r){var l=Rn(i),c=i.lastChild;Ta(l,c)}else Ta(i,i);return i}}function du(e,t,r="svg"){var a=!e.startsWith("<!>"),s=`<${r}>${a?e:"<!>"+e}</${r}>`,o;return()=>{if(!o){var i=$l(s),l=Rn(i);o=Rn(l)}var c=o.cloneNode(!0);return Ta(c,c),c}}function cu(e,t){return du(e,t,"svg")}function gs(e=""){{var t=kn(e+"");return Ta(t,t),t}}function ke(){var e=document.createDocumentFragment(),t=document.createComment(""),r=kn();return e.append(t,r),Ta(t,r),e}function v(e,t){e!==null&&e.before(t)}function $(e,t){var r=t==null?"":typeof t=="object"?`${t}`:t;r!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=r,e.nodeValue=`${r}`)}function uu(e,t){return fu(e,t)}const Is=new Map;function fu(e,{target:t,anchor:r,props:a={},events:s,context:o,intro:i=!0,transformError:l}){Bc();var c=void 0,f=Yc(()=>{var p=r??t.appendChild(kn());Ac(p,{pending:()=>{}},A=>{Xr({});var k=rr;o&&(k.c=o),s&&(a.$$events=s),c=e(A,a)||{},Jr()},l);var _=new Set,w=A=>{for(var k=0;k<A.length;k++){var P=A[k];if(!_.has(P)){_.add(P);var y=iu(P);for(const J of[t,document]){var C=Is.get(J);C===void 0&&(C=new Map,Is.set(J,C));var V=C.get(P);V===void 0?(J.addEventListener(P,Co,{passive:y}),C.set(P,1)):C.set(P,V+1)}}}};return w(Bs(Pl)),ko.add(w),()=>{var y;for(var A of _)for(const C of[t,document]){var k=Is.get(C),P=k.get(A);--P==0?(C.removeEventListener(A,Co),k.delete(A),k.size===0&&Is.delete(C)):k.set(A,P)}ko.delete(w),p!==r&&((y=p.parentNode)==null||y.removeChild(p))}});return vu.set(c,f),c}let vu=new WeakMap;var nn,gn,qr,Ca,ys,ks,qs;class Ks{constructor(t,r=!0){en(this,"anchor");Xe(this,nn,new Map);Xe(this,gn,new Map);Xe(this,qr,new Map);Xe(this,Ca,new Set);Xe(this,ys,!0);Xe(this,ks,t=>{if(M(this,nn).has(t)){var r=M(this,nn).get(t),a=M(this,gn).get(r);if(a)Bo(a),M(this,Ca).delete(r);else{var s=M(this,qr).get(r);s&&(s.effect.f&Cr)===0&&(M(this,gn).set(r,s.effect),M(this,qr).delete(r),s.fragment.lastChild.remove(),this.anchor.before(s.fragment),a=s.effect)}for(const[o,i]of M(this,nn)){if(M(this,nn).delete(o),o===t)break;const l=M(this,qr).get(i);l&&(mr(l.effect),M(this,qr).delete(i))}for(const[o,i]of M(this,gn)){if(o===r||M(this,Ca).has(o)||(i.f&Cr)!==0)continue;const l=()=>{if(Array.from(M(this,nn).values()).includes(o)){var f=document.createDocumentFragment();Go(i,f),f.append(kn()),M(this,qr).set(o,{effect:i,fragment:f})}else mr(i);M(this,Ca).delete(o),M(this,gn).delete(o)};M(this,ys)||!a?(M(this,Ca).add(o),Sa(i,l,!1)):l()}}});Xe(this,qs,t=>{M(this,nn).delete(t);const r=Array.from(M(this,nn).values());for(const[a,s]of M(this,qr))r.includes(a)||(mr(s.effect),M(this,qr).delete(a))});this.anchor=t,je(this,ys,r)}ensure(t,r){var a=Ve,s=ml();if(r&&!M(this,gn).has(t)&&!M(this,qr).has(t))if(s){var o=document.createDocumentFragment(),i=kn();o.append(i),M(this,qr).set(t,{effect:Ir(()=>r(i)),fragment:o})}else M(this,gn).set(t,Ir(()=>r(this.anchor)));if(M(this,nn).set(a,t),s){for(const[l,c]of M(this,gn))l===t?a.unskip_effect(c):a.skip_effect(c);for(const[l,c]of M(this,qr))l===t?a.unskip_effect(c.effect):a.skip_effect(c.effect);a.oncommit(M(this,ks)),a.ondiscard(M(this,qs))}else M(this,ks).call(this,a)}}nn=new WeakMap,gn=new WeakMap,qr=new WeakMap,Ca=new WeakMap,ys=new WeakMap,ks=new WeakMap,qs=new WeakMap;function E(e,t,r=!1){var a=new Ks(e),s=r?jn:0;function o(i,l){a.ensure(i,l)}rs(()=>{var i=!1;t((l,c=0)=>{i=!0,o(c,l)}),i||o(-1,null)},s)}function Me(e,t){return t}function pu(e,t,r){for(var a=[],s=t.length,o,i=t.length,l=0;l<s;l++){let _=t[l];Sa(_,()=>{if(o){if(o.pending.delete(_),o.done.add(_),o.pending.size===0){var w=e.outrogroups;So(e,Bs(o.done)),w.delete(o),w.size===0&&(e.outrogroups=null)}}else i-=1},!1)}if(i===0){var c=a.length===0&&r!==null;if(c){var f=r,p=f.parentNode;Gc(p),p.append(f),e.items.clear()}So(e,t,!c)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function So(e,t,r=!0){var a;if(e.pending.size>0){a=new Set;for(const i of e.pending.values())for(const l of i)a.add(e.items.get(l).e)}for(var s=0;s<t.length;s++){var o=t[s];if(a!=null&&a.has(o)){o.f|=xn;const i=document.createDocumentFragment();Go(o,i)}else mr(t[s],r)}}var pi;function Ee(e,t,r,a,s,o=null){var i=e,l=new Map,c=(t&Wi)!==0;if(c){var f=e;i=f.appendChild(kn())}var p=null,_=Oo(()=>{var J=r();return Po(J)?J:J==null?[]:Bs(J)}),w,A=new Map,k=!0;function P(J){(V.effect.f&_n)===0&&(V.pending.delete(J),V.fallback=p,mu(V,w,i,t,a),p!==null&&(w.length===0?(p.f&xn)===0?Bo(p):(p.f^=xn,vs(p,null,i)):Sa(p,()=>{p=null})))}function y(J){V.pending.delete(J)}var C=rs(()=>{w=n(_);for(var J=w.length,S=new Set,G=Ve,ie=ml(),O=0;O<J;O+=1){var b=w[O],Y=a(b,O),te=k?null:l.get(Y);te?(te.v&&Ya(te.v,b),te.i&&Ya(te.i,O),ie&&G.unskip_effect(te.e)):(te=hu(l,k?i:pi??(pi=kn()),b,Y,O,s,t,r),k||(te.e.f|=xn),l.set(Y,te)),S.add(Y)}if(J===0&&o&&!p&&(k?p=Ir(()=>o(i)):(p=Ir(()=>o(pi??(pi=kn()))),p.f|=xn)),J>S.size&&Yd(),!k)if(A.set(G,S),ie){for(const[Z,z]of l)S.has(Z)||G.skip_effect(z.e);G.oncommit(P),G.ondiscard(y)}else P(G);n(_)}),V={effect:C,items:l,pending:A,outrogroups:null,fallback:p};k=!1}function is(e){for(;e!==null&&(e.f&ln)===0;)e=e.next;return e}function mu(e,t,r,a,s){var te,Z,z,oe,we,ye,pe,ze,be;var o=(a&ic)!==0,i=t.length,l=e.items,c=is(e.effect.first),f,p=null,_,w=[],A=[],k,P,y,C;if(o)for(C=0;C<i;C+=1)k=t[C],P=s(k,C),y=l.get(P).e,(y.f&xn)===0&&((Z=(te=y.nodes)==null?void 0:te.a)==null||Z.measure(),(_??(_=new Set)).add(y));for(C=0;C<i;C+=1){if(k=t[C],P=s(k,C),y=l.get(P).e,e.outrogroups!==null)for(const he of e.outrogroups)he.pending.delete(y),he.done.delete(y);if((y.f&xn)!==0)if(y.f^=xn,y===c)vs(y,null,r);else{var V=p?p.next:c;y===e.effect.last&&(e.effect.last=y.prev),y.prev&&(y.prev.next=y.next),y.next&&(y.next.prev=y.prev),Kn(e,p,y),Kn(e,y,V),vs(y,V,r),p=y,w=[],A=[],c=is(p.next);continue}if((y.f&Cr)!==0&&(Bo(y),o&&((oe=(z=y.nodes)==null?void 0:z.a)==null||oe.unfix(),(_??(_=new Set)).delete(y))),y!==c){if(f!==void 0&&f.has(y)){if(w.length<A.length){var J=A[0],S;p=J.prev;var G=w[0],ie=w[w.length-1];for(S=0;S<w.length;S+=1)vs(w[S],J,r);for(S=0;S<A.length;S+=1)f.delete(A[S]);Kn(e,G.prev,ie.next),Kn(e,p,G),Kn(e,ie,J),c=J,p=ie,C-=1,w=[],A=[]}else f.delete(y),vs(y,c,r),Kn(e,y.prev,y.next),Kn(e,y,p===null?e.effect.first:p.next),Kn(e,p,y),p=y;continue}for(w=[],A=[];c!==null&&c!==y;)(f??(f=new Set)).add(c),A.push(c),c=is(c.next);if(c===null)continue}(y.f&xn)===0&&w.push(y),p=y,c=is(y.next)}if(e.outrogroups!==null){for(const he of e.outrogroups)he.pending.size===0&&(So(e,Bs(he.done)),(we=e.outrogroups)==null||we.delete(he));e.outrogroups.size===0&&(e.outrogroups=null)}if(c!==null||f!==void 0){var O=[];if(f!==void 0)for(y of f)(y.f&Cr)===0&&O.push(y);for(;c!==null;)(c.f&Cr)===0&&c!==e.fallback&&O.push(c),c=is(c.next);var b=O.length;if(b>0){var Y=(a&Wi)!==0&&i===0?r:null;if(o){for(C=0;C<b;C+=1)(pe=(ye=O[C].nodes)==null?void 0:ye.a)==null||pe.measure();for(C=0;C<b;C+=1)(be=(ze=O[C].nodes)==null?void 0:ze.a)==null||be.fix()}pu(e,O,Y)}}o&&yn(()=>{var he,K;if(_!==void 0)for(y of _)(K=(he=y.nodes)==null?void 0:he.a)==null||K.apply()})}function hu(e,t,r,a,s,o,i,l){var c=(i&sc)!==0?(i&lc)===0?Vc(r,!1,!1):ia(r):null,f=(i&oc)!==0?ia(s):null;return{v:c,i:f,e:Ir(()=>(o(t,c??r,f??s,l),()=>{e.delete(a)}))}}function vs(e,t,r){if(e.nodes)for(var a=e.nodes.start,s=e.nodes.end,o=t&&(t.f&xn)===0?t.nodes.start:r;a!==null;){var i=Es(a);if(o.before(a),a===s)return;a=i}}function Kn(e,t,r){t===null?e.effect.first=r:t.next=r,r===null?e.effect.last=t:r.prev=t}function ra(e,t,r=!1,a=!1,s=!1){var o=e,i="";L(()=>{var l=Ue;if(i!==(i=t()??"")&&(l.nodes!==null&&(wl(l.nodes.start,l.nodes.end),l.nodes=null),i!=="")){var c=r?Xi:a?mc:void 0,f=Do(r?"svg":a?"math":"template",c);f.innerHTML=i;var p=r||a?f:f.content;if(Ta(Rn(p),p.lastChild),r||a)for(;Rn(p);)o.before(Rn(p));else o.before(p)}})}function Fe(e,t,r,a,s){var l;var o=(l=t.$$slots)==null?void 0:l[r],i=!1;o===!0&&(o=t.children,i=!0),o===void 0||o(e,i?()=>a:a)}function Mo(e,t,...r){var a=new Ks(e);rs(()=>{const s=t()??null;a.ensure(s,s&&(o=>s(o,...r)))},jn)}function gu(e,t,r){var a=new Ks(e);rs(()=>{var s=t()??null;a.ensure(s,s&&(o=>r(o,s)))},jn)}function xu(e,t,r,a,s,o){var i=null,l=e,c=new Ks(l,!1);rs(()=>{const f=t()||null;var p=Xi;if(f===null){c.ensure(null,null);return}return c.ensure(f,_=>{if(f){if(i=Do(f,p),Ta(i,i),a){var w=i.appendChild(kn());a(i,w)}Ue.nodes.end=i,_.before(i)}}),()=>{}},jn),Ws(()=>{})}function bu(e,t){var r=void 0,a;bl(()=>{r!==(r=t())&&(a&&(mr(a),a=null),r&&(a=Ir(()=>{Vo(()=>r(e))})))})}function Ll(e){var t,r,a="";if(typeof e=="string"||typeof e=="number")a+=e;else if(typeof e=="object")if(Array.isArray(e)){var s=e.length;for(t=0;t<s;t++)e[t]&&(r=Ll(e[t]))&&(a&&(a+=" "),a+=r)}else for(r in e)e[r]&&(a&&(a+=" "),a+=r);return a}function Ol(){for(var e,t,r=0,a="",s=arguments.length;r<s;r++)(e=arguments[r])&&(t=Ll(e))&&(a&&(a+=" "),a+=t);return a}function kt(e){return typeof e=="object"?Ol(e):e??""}const mi=[...` 	
\r\f \v\uFEFF`];function _u(e,t,r){var a=e==null?"":""+e;if(t&&(a=a?a+" "+t:t),r){for(var s of Object.keys(r))if(r[s])a=a?a+" "+s:s;else if(a.length)for(var o=s.length,i=0;(i=a.indexOf(s,i))>=0;){var l=i+o;(i===0||mi.includes(a[i-1]))&&(l===a.length||mi.includes(a[l]))?a=(i===0?"":a.substring(0,i))+a.substring(l+1):i=l}}return a===""?null:a}function hi(e,t=!1){var r=t?" !important;":";",a="";for(var s of Object.keys(e)){var o=e[s];o!=null&&o!==""&&(a+=" "+s+": "+o+r)}return a}function to(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function wu(e,t){if(t){var r="",a,s;if(Array.isArray(t)?(a=t[0],s=t[1]):a=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,i=0,l=!1,c=[];a&&c.push(...Object.keys(a).map(to)),s&&c.push(...Object.keys(s).map(to));var f=0,p=-1;const P=e.length;for(var _=0;_<P;_++){var w=e[_];if(l?w==="/"&&e[_-1]==="*"&&(l=!1):o?o===w&&(o=!1):w==="/"&&e[_+1]==="*"?l=!0:w==='"'||w==="'"?o=w:w==="("?i++:w===")"&&i--,!l&&o===!1&&i===0){if(w===":"&&p===-1)p=_;else if(w===";"||_===P-1){if(p!==-1){var A=to(e.substring(f,p).trim());if(!c.includes(A)){w!==";"&&_++;var k=e.substring(f,_).trim();r+=" "+k+";"}}f=_+1,p=-1}}}}return a&&(r+=hi(a)),s&&(r+=hi(s,!0)),r=r.trim(),r===""?null:r}return e==null?null:String(e)}function Te(e,t,r,a,s,o){var i=e.__className;if(i!==r||i===void 0){var l=_u(r,a,o);l==null?e.removeAttribute("class"):t?e.className=l:e.setAttribute("class",l),e.__className=r}else if(o&&s!==o)for(var c in o){var f=!!o[c];(s==null||f!==!!s[c])&&e.classList.toggle(c,f)}return o}function ro(e,t={},r,a){for(var s in r){var o=r[s];t[s]!==o&&(r[s]==null?e.style.removeProperty(s):e.style.setProperty(s,o,a))}}function Eo(e,t,r,a){var s=e.__style;if(s!==t){var o=wu(t,a);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else a&&(Array.isArray(a)?(ro(e,r==null?void 0:r[0],a[0]),ro(e,r==null?void 0:r[1],a[1],"important")):ro(e,r,a));return a}function zo(e,t,r=!1){if(e.multiple){if(t==null)return;if(!Po(t))return gc();for(var a of e.options)a.selected=t.includes(gi(a));return}for(a of e.options){var s=gi(a);if(qc(s,t)){a.selected=!0;return}}(!r||t!==void 0)&&(e.selectedIndex=-1)}function yu(e){var t=new MutationObserver(()=>{zo(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Ws(()=>{t.disconnect()})}function gi(e){return"__value"in e?e.__value:e.value}const ls=Symbol("class"),ds=Symbol("style"),Rl=Symbol("is custom element"),Dl=Symbol("is html"),ku=Ui?"option":"OPTION",Cu=Ui?"select":"SELECT";function Su(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function Dn(e,t,r,a){var s=jl(e);s[t]!==(s[t]=r)&&(t==="loading"&&(e[Wd]=r),r==null?e.removeAttribute(t):typeof r!="string"&&Vl(e).includes(t)?e[t]=r:e.setAttribute(t,r))}function Mu(e,t,r,a,s=!1,o=!1){var i=jl(e),l=i[Rl],c=!i[Dl],f=t||{},p=e.nodeName===ku;for(var _ in t)_ in r||(r[_]=null);r.class?r.class=kt(r.class):r[ls]&&(r.class=null),r[ds]&&(r.style??(r.style=null));var w=Vl(e);for(const S in r){let G=r[S];if(p&&S==="value"&&G==null){e.value=e.__value="",f[S]=G;continue}if(S==="class"){var A=e.namespaceURI==="http://www.w3.org/1999/xhtml";Te(e,A,G,a,t==null?void 0:t[ls],r[ls]),f[S]=G,f[ls]=r[ls];continue}if(S==="style"){Eo(e,G,t==null?void 0:t[ds],r[ds]),f[S]=G,f[ds]=r[ds];continue}var k=f[S];if(!(G===k&&!(G===void 0&&e.hasAttribute(S)))){f[S]=G;var P=S[0]+S[1];if(P!=="$$")if(P==="on"){const ie={},O="$$"+S;let b=S.slice(2);var y=nu(b);if(tu(b)&&(b=b.slice(0,-7),ie.capture=!0),!y&&k){if(G!=null)continue;e.removeEventListener(b,f[O],ie),f[O]=null}if(y)ne(b,e,G),Vn([b]);else if(G!=null){let Y=function(te){f[S].call(this,te)};var J=Y;f[O]=Nl(b,e,Y,ie)}}else if(S==="style")Dn(e,S,G);else if(S==="autofocus")hl(e,!!G);else if(!l&&(S==="__value"||S==="value"&&G!=null))e.value=e.__value=G;else if(S==="selected"&&p)Su(e,G);else{var C=S;c||(C=su(C));var V=C==="defaultValue"||C==="defaultChecked";if(G==null&&!l&&!V)if(i[S]=null,C==="value"||C==="checked"){let ie=e;const O=t===void 0;if(C==="value"){let b=ie.defaultValue;ie.removeAttribute(C),ie.defaultValue=b,ie.value=ie.__value=O?b:null}else{let b=ie.defaultChecked;ie.removeAttribute(C),ie.defaultChecked=b,ie.checked=O?b:!1}}else e.removeAttribute(S);else V||w.includes(C)&&(l||typeof G!="string")?(e[C]=G,C in i&&(i[C]=tr)):typeof G!="function"&&Dn(e,C,G)}}}return f}function Ds(e,t,r=[],a=[],s=[],o,i=!1,l=!1){il(s,r,a,c=>{var f=void 0,p={},_=e.nodeName===Cu,w=!1;if(bl(()=>{var k=t(...c.map(n)),P=Mu(e,f,k,o,i,l);w&&_&&"value"in k&&zo(e,k.value);for(let C of Object.getOwnPropertySymbols(p))k[C]||mr(p[C]);for(let C of Object.getOwnPropertySymbols(k)){var y=k[C];C.description===hc&&(!f||y!==f[C])&&(p[C]&&mr(p[C]),p[C]=Ir(()=>bu(e,()=>y))),P[C]=y}f=P}),_){var A=e;Vo(()=>{zo(A,f.value,!0),yu(A)})}w=!0})}function jl(e){return e.__attributes??(e.__attributes={[Rl]:e.nodeName.includes("-"),[Dl]:e.namespaceURI===Yi})}var xi=new Map;function Vl(e){var t=e.getAttribute("is")||e.nodeName,r=xi.get(t);if(r)return r;xi.set(t,r=[]);for(var a,s=e,o=Element.prototype;o!==s;){a=Fi(s);for(var i in a)a[i].set&&r.push(i);s=No(s)}return r}function Oa(e,t,r=t){var a=new WeakSet;Uc(e,"input",async s=>{var o=s?e.defaultValue:e.value;if(o=no(e)?ao(o):o,r(o),Ve!==null&&a.add(Ve),await eu(),o!==(o=t())){var i=e.selectionStart,l=e.selectionEnd,c=e.value.length;if(e.value=o??"",l!==null){var f=e.value.length;i===l&&l===c&&f>c?(e.selectionStart=f,e.selectionEnd=f):(e.selectionStart=i,e.selectionEnd=Math.min(l,f))}}}),Aa(t)==null&&e.value&&(r(no(e)?ao(e.value):e.value),Ve!==null&&a.add(Ve)),Fo(()=>{var s=t();if(e===document.activeElement){var o=fo??Ve;if(a.has(o))return}no(e)&&s===ao(e.value)||e.type==="date"&&!s&&!e.value||s!==e.value&&(e.value=s??"")})}function no(e){var t=e.type;return t==="number"||t==="range"}function ao(e){return e===""?null:+e}function bi(e,t){return e===t||(e==null?void 0:e[wn])===t}function Ja(e={},t,r,a){return Vo(()=>{var s,o;return Fo(()=>{s=o,o=[],Aa(()=>{e!==r(...o)&&(t(e,...o),s&&bi(r(...s),e)&&t(null,...s))})}),()=>{yn(()=>{o&&bi(r(...o),e)&&t(null,...o)})}}),e}function Eu(e=!1){const t=rr,r=t.l.u;if(!r)return;let a=()=>ha(t.s);if(e){let s=0,o={};const i=Ms(()=>{let l=!1;const c=t.s;for(const f in c)c[f]!==o[f]&&(o[f]=c[f],l=!0);return l&&s++,s});a=()=>n(i)}r.b.length&&Kc(()=>{_i(t,a),lo(r.b)}),ta(()=>{const s=Aa(()=>r.m.map(Hd));return()=>{for(const o of s)typeof o=="function"&&o()}}),r.a.length&&ta(()=>{_i(t,a),lo(r.a)})}function _i(e,t){if(e.l.s)for(const r of e.l.s)n(r);t()}let Ps=!1;function zu(e){var t=Ps;try{return Ps=!1,[e(),Ps]}finally{Ps=t}}const Au={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Tu(e,t,r){return new Proxy({props:e,exclude:t},Au)}const Iu={get(e,t){if(!e.exclude.includes(t))return n(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,r){if(!(t in e.special)){var a=Ue;try{Yr(e.parent_effect),e.special[t]=rt({get[t](){return e.props[t]}},t,Ki)}finally{Yr(a)}}return e.special[t](r),ms(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),ms(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Oe(e,t){return new Proxy({props:e,exclude:t,special:{},version:ia(0),parent_effect:Ue},Iu)}const Pu={get(e,t){let r=e.props.length;for(;r--;){let a=e.props[r];if(os(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a)return a[t]}},set(e,t,r){let a=e.props.length;for(;a--;){let s=e.props[a];os(s)&&(s=s());const o=na(s,t);if(o&&o.set)return o.set(r),!0}return!1},getOwnPropertyDescriptor(e,t){let r=e.props.length;for(;r--;){let a=e.props[r];if(os(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a){const s=na(a,t);return s&&!s.configurable&&(s.configurable=!0),s}}},has(e,t){if(t===wn||t===Hi)return!1;for(let r of e.props)if(os(r)&&(r=r()),r!=null&&t in r)return!0;return!1},ownKeys(e){const t=[];for(let r of e.props)if(os(r)&&(r=r()),!!r){for(const a in r)t.includes(a)||t.push(a);for(const a of Object.getOwnPropertySymbols(r))t.includes(a)||t.push(a)}return t}};function Be(...e){return new Proxy({props:e},Pu)}function rt(e,t,r,a){var J;var s=!Cs||(r&cc)!==0,o=(r&uc)!==0,i=(r&fc)!==0,l=a,c=!0,f=()=>(c&&(c=!1,l=i?Aa(a):a),l),p;if(o){var _=wn in e||Hi in e;p=((J=na(e,t))==null?void 0:J.set)??(_&&t in e?S=>e[t]=S:void 0)}var w,A=!1;o?[w,A]=zu(()=>e[t]):w=e[t],w===void 0&&a!==void 0&&(w=f(),p&&(s&&ec(),p(w)));var k;if(s?k=()=>{var S=e[t];return S===void 0?f():(c=!0,S)}:k=()=>{var S=e[t];return S!==void 0&&(l=void 0),S===void 0?l:S},s&&(r&Ki)===0)return k;if(p){var P=e.$$legacy;return(function(S,G){return arguments.length>0?((!s||!G||P||A)&&p(G?k():S),S):k()})}var y=!1,C=((r&dc)!==0?Ms:Oo)(()=>(y=!1,k()));o&&n(C);var V=Ue;return(function(S,G){if(arguments.length>0){const ie=G?n(C):s&&o?Pt(S):S;return u(C,ie),y=!0,l!==void 0&&(l=ie),S}return la&&y||(V.f&_n)!==0?C.v:n(C)})}const Nu="5";var Vi;typeof window<"u"&&((Vi=window.__svelte??(window.__svelte={})).v??(Vi.v=new Set)).add(Nu);const Cn="";async function $u(){const e=await fetch(`${Cn}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function La(e,t=null,r=null){const a={provider:e};t&&(a.model=t),r&&(a.api_key=r);const s=await fetch(`${Cn}/api/configure`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!s.ok)throw new Error("설정 실패");return s.json()}async function Lu(e){const t=await fetch(`${Cn}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function Ou(e,{onProgress:t,onDone:r,onError:a}){const s=new AbortController;return fetch(`${Cn}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:s.signal}).then(async o=>{if(!o.ok){a==null||a("다운로드 실패");return}const i=o.body.getReader(),l=new TextDecoder;let c="";for(;;){const{done:f,value:p}=await i.read();if(f)break;c+=l.decode(p,{stream:!0});const _=c.split(`
`);c=_.pop()||"";for(const w of _)if(w.startsWith("data:"))try{const A=JSON.parse(w.slice(5).trim());A.total&&A.completed!==void 0?t==null||t({total:A.total,completed:A.completed,status:A.status}):A.status&&(t==null||t({status:A.status}))}catch{}}r==null||r()}).catch(o=>{o.name!=="AbortError"&&(a==null||a(o.message))}),{abort:()=>s.abort()}}async function Ru(){const e=await fetch(`${Cn}/api/codex/logout`,{method:"POST"});if(!e.ok)throw new Error("Codex 로그아웃 실패");return e.json()}async function Du(e,t=null,r=null){let a=`${Cn}/api/export/excel/${encodeURIComponent(e)}`;const s=new URLSearchParams;r?s.set("template_id",r):t&&t.length>0&&s.set("modules",t.join(","));const o=s.toString();o&&(a+=`?${o}`);const i=await fetch(a);if(!i.ok){const w=await i.json().catch(()=>({}));throw new Error(w.detail||"Excel 다운로드 실패")}const l=await i.blob(),f=(i.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),p=f?decodeURIComponent(f[1]):`${e}.xlsx`,_=document.createElement("a");return _.href=URL.createObjectURL(l),_.download=p,_.click(),URL.revokeObjectURL(_.href),p}async function Fl(e){const t=await fetch(`${Cn}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}async function ju(e,t){const r=await fetch(`${Cn}/api/company/${e}/show/${encodeURIComponent(t)}/all`);if(!r.ok)throw new Error("company topic 일괄 조회 실패");return r.json()}async function Vu(e){const t=await fetch(`${Cn}/api/company/${e}/sections`);if(!t.ok)throw new Error("sections 조회 실패");return t.json()}function Fu(e,t,r={},{onMeta:a,onSnapshot:s,onContext:o,onSystemPrompt:i,onToolCall:l,onToolResult:c,onChunk:f,onDone:p,onError:_},w=null){const A={question:t,stream:!0,...r};e&&(A.company=e),w&&w.length>0&&(A.history=w);const k=new AbortController;return fetch(`${Cn}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(A),signal:k.signal}).then(async P=>{if(!P.ok){const G=await P.json().catch(()=>({}));_==null||_(G.detail||"스트리밍 실패");return}const y=P.body.getReader(),C=new TextDecoder;let V="",J=!1,S=null;for(;;){const{done:G,value:ie}=await y.read();if(G)break;V+=C.decode(ie,{stream:!0});const O=V.split(`
`);V=O.pop()||"";for(const b of O)if(b.startsWith("event:"))S=b.slice(6).trim();else if(b.startsWith("data:")&&S){const Y=b.slice(5).trim();try{const te=JSON.parse(Y);S==="meta"?a==null||a(te):S==="snapshot"?s==null||s(te):S==="context"?o==null||o(te):S==="system_prompt"?i==null||i(te):S==="tool_call"?l==null||l(te):S==="tool_result"?c==null||c(te):S==="chunk"?f==null||f(te.text):S==="error"?_==null||_(te.error,te.action,te.detail):S==="done"&&(J||(J=!0,p==null||p()))}catch{}S=null}}J||(J=!0,p==null||p())}).catch(P=>{P.name!=="AbortError"&&(_==null||_(P.message))}),{abort:()=>k.abort()}}const qu=(e,t)=>{const r=new Array(e.length+t.length);for(let a=0;a<e.length;a++)r[a]=e[a];for(let a=0;a<t.length;a++)r[e.length+a]=t[a];return r},Bu=(e,t)=>({classGroupId:e,validator:t}),ql=(e=new Map,t=null,r)=>({nextPart:e,validators:t,classGroupId:r}),js="-",wi=[],Gu="arbitrary..",Hu=e=>{const t=Wu(e),{conflictingClassGroups:r,conflictingClassGroupModifiers:a}=e;return{getClassGroupId:i=>{if(i.startsWith("[")&&i.endsWith("]"))return Uu(i);const l=i.split(js),c=l[0]===""&&l.length>1?1:0;return Bl(l,c,t)},getConflictingClassGroupIds:(i,l)=>{if(l){const c=a[i],f=r[i];return c?f?qu(f,c):c:f||wi}return r[i]||wi}}},Bl=(e,t,r)=>{if(e.length-t===0)return r.classGroupId;const s=e[t],o=r.nextPart.get(s);if(o){const f=Bl(e,t+1,o);if(f)return f}const i=r.validators;if(i===null)return;const l=t===0?e.join(js):e.slice(t).join(js),c=i.length;for(let f=0;f<c;f++){const p=i[f];if(p.validator(l))return p.classGroupId}},Uu=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),r=t.indexOf(":"),a=t.slice(0,r);return a?Gu+a:void 0})(),Wu=e=>{const{theme:t,classGroups:r}=e;return Ku(r,t)},Ku=(e,t)=>{const r=ql();for(const a in e){const s=e[a];Ho(s,r,a,t)}return r},Ho=(e,t,r,a)=>{const s=e.length;for(let o=0;o<s;o++){const i=e[o];Yu(i,t,r,a)}},Yu=(e,t,r,a)=>{if(typeof e=="string"){Xu(e,t,r);return}if(typeof e=="function"){Ju(e,t,r,a);return}Qu(e,t,r,a)},Xu=(e,t,r)=>{const a=e===""?t:Gl(t,e);a.classGroupId=r},Ju=(e,t,r,a)=>{if(Zu(e)){Ho(e(a),t,r,a);return}t.validators===null&&(t.validators=[]),t.validators.push(Bu(r,e))},Qu=(e,t,r,a)=>{const s=Object.entries(e),o=s.length;for(let i=0;i<o;i++){const[l,c]=s[i];Ho(c,Gl(t,l),r,a)}},Gl=(e,t)=>{let r=e;const a=t.split(js),s=a.length;for(let o=0;o<s;o++){const i=a[o];let l=r.nextPart.get(i);l||(l=ql(),r.nextPart.set(i,l)),r=l}return r},Zu=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,ef=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,r=Object.create(null),a=Object.create(null);const s=(o,i)=>{r[o]=i,t++,t>e&&(t=0,a=r,r=Object.create(null))};return{get(o){let i=r[o];if(i!==void 0)return i;if((i=a[o])!==void 0)return s(o,i),i},set(o,i){o in r?r[o]=i:s(o,i)}}},Ao="!",yi=":",tf=[],ki=(e,t,r,a,s)=>({modifiers:e,hasImportantModifier:t,baseClassName:r,maybePostfixModifierPosition:a,isExternal:s}),rf=e=>{const{prefix:t,experimentalParseClassName:r}=e;let a=s=>{const o=[];let i=0,l=0,c=0,f;const p=s.length;for(let P=0;P<p;P++){const y=s[P];if(i===0&&l===0){if(y===yi){o.push(s.slice(c,P)),c=P+1;continue}if(y==="/"){f=P;continue}}y==="["?i++:y==="]"?i--:y==="("?l++:y===")"&&l--}const _=o.length===0?s:s.slice(c);let w=_,A=!1;_.endsWith(Ao)?(w=_.slice(0,-1),A=!0):_.startsWith(Ao)&&(w=_.slice(1),A=!0);const k=f&&f>c?f-c:void 0;return ki(o,A,w,k)};if(t){const s=t+yi,o=a;a=i=>i.startsWith(s)?o(i.slice(s.length)):ki(tf,!1,i,void 0,!0)}if(r){const s=a;a=o=>r({className:o,parseClassName:s})}return a},nf=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((r,a)=>{t.set(r,1e6+a)}),r=>{const a=[];let s=[];for(let o=0;o<r.length;o++){const i=r[o],l=i[0]==="[",c=t.has(i);l||c?(s.length>0&&(s.sort(),a.push(...s),s=[]),a.push(i)):s.push(i)}return s.length>0&&(s.sort(),a.push(...s)),a}},af=e=>({cache:ef(e.cacheSize),parseClassName:rf(e),sortModifiers:nf(e),...Hu(e)}),sf=/\s+/,of=(e,t)=>{const{parseClassName:r,getClassGroupId:a,getConflictingClassGroupIds:s,sortModifiers:o}=t,i=[],l=e.trim().split(sf);let c="";for(let f=l.length-1;f>=0;f-=1){const p=l[f],{isExternal:_,modifiers:w,hasImportantModifier:A,baseClassName:k,maybePostfixModifierPosition:P}=r(p);if(_){c=p+(c.length>0?" "+c:c);continue}let y=!!P,C=a(y?k.substring(0,P):k);if(!C){if(!y){c=p+(c.length>0?" "+c:c);continue}if(C=a(k),!C){c=p+(c.length>0?" "+c:c);continue}y=!1}const V=w.length===0?"":w.length===1?w[0]:o(w).join(":"),J=A?V+Ao:V,S=J+C;if(i.indexOf(S)>-1)continue;i.push(S);const G=s(C,y);for(let ie=0;ie<G.length;++ie){const O=G[ie];i.push(J+O)}c=p+(c.length>0?" "+c:c)}return c},lf=(...e)=>{let t=0,r,a,s="";for(;t<e.length;)(r=e[t++])&&(a=Hl(r))&&(s&&(s+=" "),s+=a);return s},Hl=e=>{if(typeof e=="string")return e;let t,r="";for(let a=0;a<e.length;a++)e[a]&&(t=Hl(e[a]))&&(r&&(r+=" "),r+=t);return r},df=(e,...t)=>{let r,a,s,o;const i=c=>{const f=t.reduce((p,_)=>_(p),e());return r=af(f),a=r.cache.get,s=r.cache.set,o=l,l(c)},l=c=>{const f=a(c);if(f)return f;const p=of(c,r);return s(c,p),p};return o=i,(...c)=>o(lf(...c))},cf=[],Xt=e=>{const t=r=>r[e]||cf;return t.isThemeGetter=!0,t},Ul=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Wl=/^\((?:(\w[\w-]*):)?(.+)\)$/i,uf=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,ff=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,vf=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,pf=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,mf=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,hf=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,Yn=e=>uf.test(e),Le=e=>!!e&&!Number.isNaN(Number(e)),Xn=e=>!!e&&Number.isInteger(Number(e)),so=e=>e.endsWith("%")&&Le(e.slice(0,-1)),Nn=e=>ff.test(e),Kl=()=>!0,gf=e=>vf.test(e)&&!pf.test(e),Uo=()=>!1,xf=e=>mf.test(e),bf=e=>hf.test(e),_f=e=>!re(e)&&!se(e),wf=e=>ca(e,Jl,Uo),re=e=>Ul.test(e),ma=e=>ca(e,Ql,gf),Ci=e=>ca(e,Af,Le),yf=e=>ca(e,ed,Kl),kf=e=>ca(e,Zl,Uo),Si=e=>ca(e,Yl,Uo),Cf=e=>ca(e,Xl,bf),Ns=e=>ca(e,td,xf),se=e=>Wl.test(e),cs=e=>Pa(e,Ql),Sf=e=>Pa(e,Zl),Mi=e=>Pa(e,Yl),Mf=e=>Pa(e,Jl),Ef=e=>Pa(e,Xl),$s=e=>Pa(e,td,!0),zf=e=>Pa(e,ed,!0),ca=(e,t,r)=>{const a=Ul.exec(e);return a?a[1]?t(a[1]):r(a[2]):!1},Pa=(e,t,r=!1)=>{const a=Wl.exec(e);return a?a[1]?t(a[1]):r:!1},Yl=e=>e==="position"||e==="percentage",Xl=e=>e==="image"||e==="url",Jl=e=>e==="length"||e==="size"||e==="bg-size",Ql=e=>e==="length",Af=e=>e==="number",Zl=e=>e==="family-name",ed=e=>e==="number"||e==="weight",td=e=>e==="shadow",Tf=()=>{const e=Xt("color"),t=Xt("font"),r=Xt("text"),a=Xt("font-weight"),s=Xt("tracking"),o=Xt("leading"),i=Xt("breakpoint"),l=Xt("container"),c=Xt("spacing"),f=Xt("radius"),p=Xt("shadow"),_=Xt("inset-shadow"),w=Xt("text-shadow"),A=Xt("drop-shadow"),k=Xt("blur"),P=Xt("perspective"),y=Xt("aspect"),C=Xt("ease"),V=Xt("animate"),J=()=>["auto","avoid","all","avoid-page","page","left","right","column"],S=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],G=()=>[...S(),se,re],ie=()=>["auto","hidden","clip","visible","scroll"],O=()=>["auto","contain","none"],b=()=>[se,re,c],Y=()=>[Yn,"full","auto",...b()],te=()=>[Xn,"none","subgrid",se,re],Z=()=>["auto",{span:["full",Xn,se,re]},Xn,se,re],z=()=>[Xn,"auto",se,re],oe=()=>["auto","min","max","fr",se,re],we=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],ye=()=>["start","end","center","stretch","center-safe","end-safe"],pe=()=>["auto",...b()],ze=()=>[Yn,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...b()],be=()=>[Yn,"screen","full","dvw","lvw","svw","min","max","fit",...b()],he=()=>[Yn,"screen","full","lh","dvh","lvh","svh","min","max","fit",...b()],K=()=>[e,se,re],T=()=>[...S(),Mi,Si,{position:[se,re]}],D=()=>["no-repeat",{repeat:["","x","y","space","round"]}],ae=()=>["auto","cover","contain",Mf,wf,{size:[se,re]}],ce=()=>[so,cs,ma],fe=()=>["","none","full",f,se,re],le=()=>["",Le,cs,ma],q=()=>["solid","dashed","dotted","double"],We=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],Ie=()=>[Le,so,Mi,Si],Gt=()=>["","none",k,se,re],et=()=>["none",Le,se,re],Qt=()=>["none",Le,se,re],nt=()=>[Le,se,re],Pe=()=>[Yn,"full",...b()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Nn],breakpoint:[Nn],color:[Kl],container:[Nn],"drop-shadow":[Nn],ease:["in","out","in-out"],font:[_f],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Nn],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Nn],shadow:[Nn],spacing:["px",Le],text:[Nn],"text-shadow":[Nn],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",Yn,re,se,y]}],container:["container"],columns:[{columns:[Le,re,se,l]}],"break-after":[{"break-after":J()}],"break-before":[{"break-before":J()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:G()}],overflow:[{overflow:ie()}],"overflow-x":[{"overflow-x":ie()}],"overflow-y":[{"overflow-y":ie()}],overscroll:[{overscroll:O()}],"overscroll-x":[{"overscroll-x":O()}],"overscroll-y":[{"overscroll-y":O()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:Y()}],"inset-x":[{"inset-x":Y()}],"inset-y":[{"inset-y":Y()}],start:[{"inset-s":Y(),start:Y()}],end:[{"inset-e":Y(),end:Y()}],"inset-bs":[{"inset-bs":Y()}],"inset-be":[{"inset-be":Y()}],top:[{top:Y()}],right:[{right:Y()}],bottom:[{bottom:Y()}],left:[{left:Y()}],visibility:["visible","invisible","collapse"],z:[{z:[Xn,"auto",se,re]}],basis:[{basis:[Yn,"full","auto",l,...b()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[Le,Yn,"auto","initial","none",re]}],grow:[{grow:["",Le,se,re]}],shrink:[{shrink:["",Le,se,re]}],order:[{order:[Xn,"first","last","none",se,re]}],"grid-cols":[{"grid-cols":te()}],"col-start-end":[{col:Z()}],"col-start":[{"col-start":z()}],"col-end":[{"col-end":z()}],"grid-rows":[{"grid-rows":te()}],"row-start-end":[{row:Z()}],"row-start":[{"row-start":z()}],"row-end":[{"row-end":z()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":oe()}],"auto-rows":[{"auto-rows":oe()}],gap:[{gap:b()}],"gap-x":[{"gap-x":b()}],"gap-y":[{"gap-y":b()}],"justify-content":[{justify:[...we(),"normal"]}],"justify-items":[{"justify-items":[...ye(),"normal"]}],"justify-self":[{"justify-self":["auto",...ye()]}],"align-content":[{content:["normal",...we()]}],"align-items":[{items:[...ye(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...ye(),{baseline:["","last"]}]}],"place-content":[{"place-content":we()}],"place-items":[{"place-items":[...ye(),"baseline"]}],"place-self":[{"place-self":["auto",...ye()]}],p:[{p:b()}],px:[{px:b()}],py:[{py:b()}],ps:[{ps:b()}],pe:[{pe:b()}],pbs:[{pbs:b()}],pbe:[{pbe:b()}],pt:[{pt:b()}],pr:[{pr:b()}],pb:[{pb:b()}],pl:[{pl:b()}],m:[{m:pe()}],mx:[{mx:pe()}],my:[{my:pe()}],ms:[{ms:pe()}],me:[{me:pe()}],mbs:[{mbs:pe()}],mbe:[{mbe:pe()}],mt:[{mt:pe()}],mr:[{mr:pe()}],mb:[{mb:pe()}],ml:[{ml:pe()}],"space-x":[{"space-x":b()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":b()}],"space-y-reverse":["space-y-reverse"],size:[{size:ze()}],"inline-size":[{inline:["auto",...be()]}],"min-inline-size":[{"min-inline":["auto",...be()]}],"max-inline-size":[{"max-inline":["none",...be()]}],"block-size":[{block:["auto",...he()]}],"min-block-size":[{"min-block":["auto",...he()]}],"max-block-size":[{"max-block":["none",...he()]}],w:[{w:[l,"screen",...ze()]}],"min-w":[{"min-w":[l,"screen","none",...ze()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[i]},...ze()]}],h:[{h:["screen","lh",...ze()]}],"min-h":[{"min-h":["screen","lh","none",...ze()]}],"max-h":[{"max-h":["screen","lh",...ze()]}],"font-size":[{text:["base",r,cs,ma]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[a,zf,yf]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",so,re]}],"font-family":[{font:[Sf,kf,t]}],"font-features":[{"font-features":[re]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[s,se,re]}],"line-clamp":[{"line-clamp":[Le,"none",se,Ci]}],leading:[{leading:[o,...b()]}],"list-image":[{"list-image":["none",se,re]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",se,re]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:K()}],"text-color":[{text:K()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...q(),"wavy"]}],"text-decoration-thickness":[{decoration:[Le,"from-font","auto",se,ma]}],"text-decoration-color":[{decoration:K()}],"underline-offset":[{"underline-offset":[Le,"auto",se,re]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:b()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",se,re]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",se,re]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:T()}],"bg-repeat":[{bg:D()}],"bg-size":[{bg:ae()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},Xn,se,re],radial:["",se,re],conic:[Xn,se,re]},Ef,Cf]}],"bg-color":[{bg:K()}],"gradient-from-pos":[{from:ce()}],"gradient-via-pos":[{via:ce()}],"gradient-to-pos":[{to:ce()}],"gradient-from":[{from:K()}],"gradient-via":[{via:K()}],"gradient-to":[{to:K()}],rounded:[{rounded:fe()}],"rounded-s":[{"rounded-s":fe()}],"rounded-e":[{"rounded-e":fe()}],"rounded-t":[{"rounded-t":fe()}],"rounded-r":[{"rounded-r":fe()}],"rounded-b":[{"rounded-b":fe()}],"rounded-l":[{"rounded-l":fe()}],"rounded-ss":[{"rounded-ss":fe()}],"rounded-se":[{"rounded-se":fe()}],"rounded-ee":[{"rounded-ee":fe()}],"rounded-es":[{"rounded-es":fe()}],"rounded-tl":[{"rounded-tl":fe()}],"rounded-tr":[{"rounded-tr":fe()}],"rounded-br":[{"rounded-br":fe()}],"rounded-bl":[{"rounded-bl":fe()}],"border-w":[{border:le()}],"border-w-x":[{"border-x":le()}],"border-w-y":[{"border-y":le()}],"border-w-s":[{"border-s":le()}],"border-w-e":[{"border-e":le()}],"border-w-bs":[{"border-bs":le()}],"border-w-be":[{"border-be":le()}],"border-w-t":[{"border-t":le()}],"border-w-r":[{"border-r":le()}],"border-w-b":[{"border-b":le()}],"border-w-l":[{"border-l":le()}],"divide-x":[{"divide-x":le()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":le()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...q(),"hidden","none"]}],"divide-style":[{divide:[...q(),"hidden","none"]}],"border-color":[{border:K()}],"border-color-x":[{"border-x":K()}],"border-color-y":[{"border-y":K()}],"border-color-s":[{"border-s":K()}],"border-color-e":[{"border-e":K()}],"border-color-bs":[{"border-bs":K()}],"border-color-be":[{"border-be":K()}],"border-color-t":[{"border-t":K()}],"border-color-r":[{"border-r":K()}],"border-color-b":[{"border-b":K()}],"border-color-l":[{"border-l":K()}],"divide-color":[{divide:K()}],"outline-style":[{outline:[...q(),"none","hidden"]}],"outline-offset":[{"outline-offset":[Le,se,re]}],"outline-w":[{outline:["",Le,cs,ma]}],"outline-color":[{outline:K()}],shadow:[{shadow:["","none",p,$s,Ns]}],"shadow-color":[{shadow:K()}],"inset-shadow":[{"inset-shadow":["none",_,$s,Ns]}],"inset-shadow-color":[{"inset-shadow":K()}],"ring-w":[{ring:le()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:K()}],"ring-offset-w":[{"ring-offset":[Le,ma]}],"ring-offset-color":[{"ring-offset":K()}],"inset-ring-w":[{"inset-ring":le()}],"inset-ring-color":[{"inset-ring":K()}],"text-shadow":[{"text-shadow":["none",w,$s,Ns]}],"text-shadow-color":[{"text-shadow":K()}],opacity:[{opacity:[Le,se,re]}],"mix-blend":[{"mix-blend":[...We(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":We()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[Le]}],"mask-image-linear-from-pos":[{"mask-linear-from":Ie()}],"mask-image-linear-to-pos":[{"mask-linear-to":Ie()}],"mask-image-linear-from-color":[{"mask-linear-from":K()}],"mask-image-linear-to-color":[{"mask-linear-to":K()}],"mask-image-t-from-pos":[{"mask-t-from":Ie()}],"mask-image-t-to-pos":[{"mask-t-to":Ie()}],"mask-image-t-from-color":[{"mask-t-from":K()}],"mask-image-t-to-color":[{"mask-t-to":K()}],"mask-image-r-from-pos":[{"mask-r-from":Ie()}],"mask-image-r-to-pos":[{"mask-r-to":Ie()}],"mask-image-r-from-color":[{"mask-r-from":K()}],"mask-image-r-to-color":[{"mask-r-to":K()}],"mask-image-b-from-pos":[{"mask-b-from":Ie()}],"mask-image-b-to-pos":[{"mask-b-to":Ie()}],"mask-image-b-from-color":[{"mask-b-from":K()}],"mask-image-b-to-color":[{"mask-b-to":K()}],"mask-image-l-from-pos":[{"mask-l-from":Ie()}],"mask-image-l-to-pos":[{"mask-l-to":Ie()}],"mask-image-l-from-color":[{"mask-l-from":K()}],"mask-image-l-to-color":[{"mask-l-to":K()}],"mask-image-x-from-pos":[{"mask-x-from":Ie()}],"mask-image-x-to-pos":[{"mask-x-to":Ie()}],"mask-image-x-from-color":[{"mask-x-from":K()}],"mask-image-x-to-color":[{"mask-x-to":K()}],"mask-image-y-from-pos":[{"mask-y-from":Ie()}],"mask-image-y-to-pos":[{"mask-y-to":Ie()}],"mask-image-y-from-color":[{"mask-y-from":K()}],"mask-image-y-to-color":[{"mask-y-to":K()}],"mask-image-radial":[{"mask-radial":[se,re]}],"mask-image-radial-from-pos":[{"mask-radial-from":Ie()}],"mask-image-radial-to-pos":[{"mask-radial-to":Ie()}],"mask-image-radial-from-color":[{"mask-radial-from":K()}],"mask-image-radial-to-color":[{"mask-radial-to":K()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":S()}],"mask-image-conic-pos":[{"mask-conic":[Le]}],"mask-image-conic-from-pos":[{"mask-conic-from":Ie()}],"mask-image-conic-to-pos":[{"mask-conic-to":Ie()}],"mask-image-conic-from-color":[{"mask-conic-from":K()}],"mask-image-conic-to-color":[{"mask-conic-to":K()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:T()}],"mask-repeat":[{mask:D()}],"mask-size":[{mask:ae()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",se,re]}],filter:[{filter:["","none",se,re]}],blur:[{blur:Gt()}],brightness:[{brightness:[Le,se,re]}],contrast:[{contrast:[Le,se,re]}],"drop-shadow":[{"drop-shadow":["","none",A,$s,Ns]}],"drop-shadow-color":[{"drop-shadow":K()}],grayscale:[{grayscale:["",Le,se,re]}],"hue-rotate":[{"hue-rotate":[Le,se,re]}],invert:[{invert:["",Le,se,re]}],saturate:[{saturate:[Le,se,re]}],sepia:[{sepia:["",Le,se,re]}],"backdrop-filter":[{"backdrop-filter":["","none",se,re]}],"backdrop-blur":[{"backdrop-blur":Gt()}],"backdrop-brightness":[{"backdrop-brightness":[Le,se,re]}],"backdrop-contrast":[{"backdrop-contrast":[Le,se,re]}],"backdrop-grayscale":[{"backdrop-grayscale":["",Le,se,re]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[Le,se,re]}],"backdrop-invert":[{"backdrop-invert":["",Le,se,re]}],"backdrop-opacity":[{"backdrop-opacity":[Le,se,re]}],"backdrop-saturate":[{"backdrop-saturate":[Le,se,re]}],"backdrop-sepia":[{"backdrop-sepia":["",Le,se,re]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":b()}],"border-spacing-x":[{"border-spacing-x":b()}],"border-spacing-y":[{"border-spacing-y":b()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",se,re]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[Le,"initial",se,re]}],ease:[{ease:["linear","initial",C,se,re]}],delay:[{delay:[Le,se,re]}],animate:[{animate:["none",V,se,re]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[P,se,re]}],"perspective-origin":[{"perspective-origin":G()}],rotate:[{rotate:et()}],"rotate-x":[{"rotate-x":et()}],"rotate-y":[{"rotate-y":et()}],"rotate-z":[{"rotate-z":et()}],scale:[{scale:Qt()}],"scale-x":[{"scale-x":Qt()}],"scale-y":[{"scale-y":Qt()}],"scale-z":[{"scale-z":Qt()}],"scale-3d":["scale-3d"],skew:[{skew:nt()}],"skew-x":[{"skew-x":nt()}],"skew-y":[{"skew-y":nt()}],transform:[{transform:[se,re,"","none","gpu","cpu"]}],"transform-origin":[{origin:G()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:Pe()}],"translate-x":[{"translate-x":Pe()}],"translate-y":[{"translate-y":Pe()}],"translate-z":[{"translate-z":Pe()}],"translate-none":["translate-none"],accent:[{accent:K()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:K()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",se,re]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":b()}],"scroll-mx":[{"scroll-mx":b()}],"scroll-my":[{"scroll-my":b()}],"scroll-ms":[{"scroll-ms":b()}],"scroll-me":[{"scroll-me":b()}],"scroll-mbs":[{"scroll-mbs":b()}],"scroll-mbe":[{"scroll-mbe":b()}],"scroll-mt":[{"scroll-mt":b()}],"scroll-mr":[{"scroll-mr":b()}],"scroll-mb":[{"scroll-mb":b()}],"scroll-ml":[{"scroll-ml":b()}],"scroll-p":[{"scroll-p":b()}],"scroll-px":[{"scroll-px":b()}],"scroll-py":[{"scroll-py":b()}],"scroll-ps":[{"scroll-ps":b()}],"scroll-pe":[{"scroll-pe":b()}],"scroll-pbs":[{"scroll-pbs":b()}],"scroll-pbe":[{"scroll-pbe":b()}],"scroll-pt":[{"scroll-pt":b()}],"scroll-pr":[{"scroll-pr":b()}],"scroll-pb":[{"scroll-pb":b()}],"scroll-pl":[{"scroll-pl":b()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",se,re]}],fill:[{fill:["none",...K()]}],"stroke-w":[{stroke:[Le,cs,ma,Ci]}],stroke:[{stroke:["none",...K()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},If=df(Tf);function Ct(...e){return If(Ol(e))}const To="dartlab-conversations",Ei=50;function Pf(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function Nf(){try{const e=localStorage.getItem(To);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const $f=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function zi(e){return e.map(t=>({...t,messages:t.messages.map(r=>{if(r.role!=="assistant")return r;const a={};for(const[s,o]of Object.entries(r))$f.includes(s)||(a[s]=o);return a})}))}function Ai(e){try{const t={conversations:zi(e.conversations),activeId:e.activeId};localStorage.setItem(To,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:zi(e.conversations),activeId:e.activeId};localStorage.setItem(To,JSON.stringify(t))}catch{}}}}function Lf(){const e=Nf(),t=e.conversations||[],r=t.find(C=>C.id===e.activeId)?e.activeId:null;let a=W(Pt(t)),s=W(Pt(r)),o=null;function i(){o&&clearTimeout(o),o=setTimeout(()=>{Ai({conversations:n(a),activeId:n(s)}),o=null},300)}function l(){o&&clearTimeout(o),o=null,Ai({conversations:n(a),activeId:n(s)})}function c(){return n(a).find(C=>C.id===n(s))||null}function f(){const C={id:Pf(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return u(a,[C,...n(a)],!0),n(a).length>Ei&&u(a,n(a).slice(0,Ei),!0),u(s,C.id,!0),l(),C.id}function p(C){n(a).find(V=>V.id===C)&&(u(s,C,!0),l())}function _(C,V,J=null){const S=c();if(!S)return;const G={role:C,text:V};J&&(G.meta=J),S.messages=[...S.messages,G],S.updatedAt=Date.now(),S.title==="새 대화"&&C==="user"&&(S.title=V.length>30?V.slice(0,30)+"...":V),u(a,[...n(a)],!0),l()}function w(C){const V=c();if(!V||V.messages.length===0)return;const J=V.messages[V.messages.length-1];Object.assign(J,C),V.updatedAt=Date.now(),u(a,[...n(a)],!0),i()}function A(C){u(a,n(a).filter(V=>V.id!==C),!0),n(s)===C&&u(s,n(a).length>0?n(a)[0].id:null,!0),l()}function k(){const C=c();!C||C.messages.length===0||(C.messages=C.messages.slice(0,-1),C.updatedAt=Date.now(),u(a,[...n(a)],!0),l())}function P(C,V){const J=n(a).find(S=>S.id===C);J&&(J.title=V,u(a,[...n(a)],!0),l())}function y(){u(a,[],!0),u(s,null),l()}return{get conversations(){return n(a)},get activeId(){return n(s)},get active(){return c()},createConversation:f,setActive:p,addMessage:_,updateLastMessage:w,removeLastMessage:k,deleteConversation:A,updateTitle:P,clearAll:y,flush:l}}const rd="dartlab-workspace",Of=6;function nd(){return typeof window<"u"&&typeof localStorage<"u"}function Rf(){if(!nd())return{};try{const e=localStorage.getItem(rd);return e?JSON.parse(e):{}}catch{return{}}}function Df(e){nd()&&localStorage.setItem(rd,JSON.stringify(e))}function jf(){const e=Rf();let t=W(!1),r=W(null),a=W(null),s=W("explore"),o=W(null),i=W(null),l=W(null),c=W(null),f=W(Pt(e.selectedCompany||null)),p=W(Pt(e.recentCompanies||[]));function _(){Df({selectedCompany:n(f),recentCompanies:n(p)})}function w(O){if(!(O!=null&&O.stockCode))return;const b={stockCode:O.stockCode,corpName:O.corpName||O.company||O.stockCode,company:O.company||O.corpName||O.stockCode,market:O.market||""};u(p,[b,...n(p).filter(Y=>Y.stockCode!==b.stockCode)].slice(0,Of),!0)}function A(O){O&&(u(f,O,!0),w(O)),u(r,"viewer"),u(a,null),u(t,!0),_()}function k(O){u(r,"data"),u(a,O,!0),u(t,!0),G("explore")}function P(){u(t,!1)}function y(O){u(f,O,!0),O&&w(O),_()}function C(O,b){var Y,te,Z,z;!(O!=null&&O.company)&&!(O!=null&&O.stockCode)||(u(f,{...n(f)||{},...b||{},corpName:O.company||((Y=n(f))==null?void 0:Y.corpName)||(b==null?void 0:b.corpName)||(b==null?void 0:b.company),company:O.company||((te=n(f))==null?void 0:te.company)||(b==null?void 0:b.company)||(b==null?void 0:b.corpName),stockCode:O.stockCode||((Z=n(f))==null?void 0:Z.stockCode)||(b==null?void 0:b.stockCode),market:((z=n(f))==null?void 0:z.market)||(b==null?void 0:b.market)||""},!0),w(n(f)),_())}function V(O,b){u(l,O,!0),u(c,b||O,!0)}function J(O,b=null){u(r,"data"),u(t,!0),u(s,"evidence"),u(o,O,!0),u(i,Number.isInteger(b)?b:null,!0)}function S(){u(o,null),u(i,null)}function G(O){u(s,O||"explore",!0),n(s)!=="evidence"&&S()}function ie(){return n(t)?n(r)==="viewer"&&n(f)?{type:"viewer",company:n(f),topic:n(l),topicLabel:n(c)}:n(r)==="data"&&n(a)?{type:"data",data:n(a)}:null:null}return{get panelOpen(){return n(t)},get panelMode(){return n(r)},get panelData(){return n(a)},get activeTab(){return n(s)},get activeEvidenceSection(){return n(o)},get selectedEvidenceIndex(){return n(i)},get selectedCompany(){return n(f)},get recentCompanies(){return n(p)},get viewerTopic(){return n(l)},get viewerTopicLabel(){return n(c)},openViewer:A,openData:k,openEvidence:J,closePanel:P,selectCompany:y,setViewerTopic:V,clearEvidenceSelection:S,setTab:G,syncCompanyFromMessage:C,getViewContext:ie}}var Vf=h("<a><!></a>"),Ff=h("<button><!></button>");function qf(e,t){Xr(t,!0);let r=rt(t,"variant",3,"default"),a=rt(t,"size",3,"default"),s=Tu(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const o={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},i={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=ke(),c=ee(l);{var f=_=>{var w=Vf();Ds(w,k=>({class:k,...s}),[()=>Ct("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",o[r()],i[a()],t.class)]);var A=d(w);Mo(A,()=>t.children),v(_,w)},p=_=>{var w=Ff();Ds(w,k=>({class:k,...s}),[()=>Ct("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",o[r()],i[a()],t.class)]);var A=d(w);Mo(A,()=>t.children),v(_,w)};E(c,_=>{t.href?_(f):_(p,-1)})}v(e,l),Jr()}wc();/**
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
 */const Bf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const Gf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const Ti=(...e)=>e.filter((t,r,a)=>!!t&&t.trim()!==""&&a.indexOf(t)===r).join(" ").trim();var Hf=cu("<svg><!><!></svg>");function Ge(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]),a=Oe(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);Xr(t,!1);let s=rt(t,"name",8,void 0),o=rt(t,"color",8,"currentColor"),i=rt(t,"size",8,24),l=rt(t,"strokeWidth",8,2),c=rt(t,"absoluteStrokeWidth",8,!1),f=rt(t,"iconNode",24,()=>[]);Eu();var p=Hf();Ds(p,(A,k,P)=>({...Bf,...A,...a,width:i(),height:i(),stroke:o(),"stroke-width":k,class:P}),[()=>Gf(a)?void 0:{"aria-hidden":"true"},()=>(ha(c()),ha(l()),ha(i()),Aa(()=>c()?Number(l())*24/Number(i()):l())),()=>(ha(Ti),ha(s()),ha(r),Aa(()=>Ti("lucide-icon","lucide",s()?`lucide-${s()}`:"",r.class)))]);var _=d(p);Ee(_,1,f,Me,(A,k)=>{var P=U(()=>Bi(n(k),2));let y=()=>n(P)[0],C=()=>n(P)[1];var V=ke(),J=ee(V);xu(J,y,!0,(S,G)=>{Ds(S,()=>({...C()}))}),v(A,V)});var w=m(_);Fe(w,t,"default",{}),v(e,p),Jr()}function Uf(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];Ge(e,Be({name:"activity"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Wf(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];Ge(e,Be({name:"arrow-up"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Ii(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 7v14"}],["path",{d:"M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"}]];Ge(e,Be({name:"book-open"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function oo(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];Ge(e,Be({name:"brain"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Kf(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]];Ge(e,Be({name:"chart-column"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Yf(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M20 6 9 17l-5-5"}]];Ge(e,Be({name:"check"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Xf(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m6 9 6 6 6-6"}]];Ge(e,Be({name:"chevron-down"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Jf(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m9 18 6-6-6-6"}]];Ge(e,Be({name:"chevron-right"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function us(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];Ge(e,Be({name:"circle-alert"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function xs(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];Ge(e,Be({name:"circle-check"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Qf(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];Ge(e,Be({name:"clock"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Zf(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];Ge(e,Be({name:"code"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ev(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];Ge(e,Be({name:"coffee"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function fs(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];Ge(e,Be({name:"database"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function bs(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];Ge(e,Be({name:"download"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Pi(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];Ge(e,Be({name:"external-link"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function tv(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];Ge(e,Be({name:"eye"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function On(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];Ge(e,Be({name:"file-text"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function rv(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];Ge(e,Be({name:"github"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Ni(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];Ge(e,Be({name:"key"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function an(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];Ge(e,Be({name:"loader-circle"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function nv(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];Ge(e,Be({name:"log-out"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ad(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"m21 3-7 7"}],["path",{d:"m3 21 7-7"}],["path",{d:"M9 21H3v-6"}]];Ge(e,Be({name:"maximize-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function av(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];Ge(e,Be({name:"menu"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function $i(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];Ge(e,Be({name:"message-square"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function sd(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m14 10 7-7"}],["path",{d:"M20 10h-6V4"}],["path",{d:"m3 21 7-7"}],["path",{d:"M4 14h6v6"}]];Ge(e,Be({name:"minimize-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function sv(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];Ge(e,Be({name:"panel-left-close"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Li(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];Ge(e,Be({name:"plus"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ov(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];Ge(e,Be({name:"refresh-cw"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function _s(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];Ge(e,Be({name:"search"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function iv(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];Ge(e,Be({name:"settings"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function lv(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];Ge(e,Be({name:"square"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function dv(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];Ge(e,Be({name:"terminal"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function cv(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];Ge(e,Be({name:"trash-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function uv(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];Ge(e,Be({name:"triangle-alert"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Oi(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];Ge(e,Be({name:"wrench"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Vs(e,t){const r=Oe(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];Ge(e,Be({name:"x"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ke(),l=ee(i);Fe(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}var fv=h("<!> 새 대화",1),vv=h('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),pv=h('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),mv=h('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),hv=h('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40"><span class="text-[10px] text-dl-text-dim font-mono"> </span></div>'),gv=h('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),xv=h("<button><!></button>"),bv=h('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),_v=h("<aside><!></aside>");function wv(e,t){Xr(t,!0);let r=rt(t,"conversations",19,()=>[]),a=rt(t,"activeId",3,null),s=rt(t,"open",3,!0),o=rt(t,"version",3,""),i=W("");function l(k){const P=new Date().setHours(0,0,0,0),y=P-864e5,C=P-7*864e5,V={오늘:[],어제:[],"이번 주":[],이전:[]};for(const S of k)S.updatedAt>=P?V.오늘.push(S):S.updatedAt>=y?V.어제.push(S):S.updatedAt>=C?V["이번 주"].push(S):V.이전.push(S);const J=[];for(const[S,G]of Object.entries(V))G.length>0&&J.push({label:S,items:G});return J}let c=U(()=>n(i).trim()?r().filter(k=>k.title.toLowerCase().includes(n(i).toLowerCase())):r()),f=U(()=>l(n(c)));var p=_v(),_=d(p);{var w=k=>{var P=gv(),y=m(d(P),2),C=d(y);qf(C,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(O,b)=>{var Y=fv(),te=ee(Y);Li(te,{size:16}),v(O,Y)},$$slots:{default:!0}});var V=m(y,2);{var J=O=>{var b=vv(),Y=d(b),te=d(Y);_s(te,{size:12,class:"text-dl-text-dim flex-shrink-0"});var Z=m(te,2);Oa(Z,()=>n(i),z=>u(i,z)),v(O,b)};E(V,O=>{r().length>3&&O(J)})}var S=m(V,2);Ee(S,21,()=>n(f),Me,(O,b)=>{var Y=mv(),te=d(Y),Z=d(te),z=m(te,2);Ee(z,17,()=>n(b).items,Me,(oe,we)=>{var ye=pv(),pe=d(ye),ze=d(pe);$i(ze,{size:14,class:"flex-shrink-0 opacity-50"});var be=m(ze,2),he=d(be),K=m(pe,2),T=d(K);cv(T,{size:12}),L(D=>{Te(ye,1,D),Dn(pe,"aria-current",n(we).id===a()?"true":void 0),$(he,n(we).title),Dn(K,"aria-label",`${n(we).title} 삭제`)},[()=>kt(Ct("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",n(we).id===a()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),ne("click",pe,()=>{var D;return(D=t.onSelect)==null?void 0:D.call(t,n(we).id)}),ne("click",K,D=>{var ae;D.stopPropagation(),(ae=t.onDelete)==null||ae.call(t,n(we).id)}),v(oe,ye)}),L(()=>$(Z,n(b).label)),v(O,Y)});var G=m(S,2);{var ie=O=>{var b=hv(),Y=d(b),te=d(Y);L(()=>$(te,`v${o()??""}`)),v(O,b)};E(G,O=>{o()&&O(ie)})}v(k,P)},A=k=>{var P=bv(),y=m(d(P),2),C=d(y);Li(C,{size:18});var V=m(y,2);Ee(V,21,()=>r().slice(0,10),Me,(J,S)=>{var G=xv(),ie=d(G);$i(ie,{size:16}),L(O=>{Te(G,1,O),Dn(G,"title",n(S).title)},[()=>kt(Ct("p-2 rounded-lg transition-colors w-full flex justify-center",n(S).id===a()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),ne("click",G,()=>{var O;return(O=t.onSelect)==null?void 0:O.call(t,n(S).id)}),v(J,G)}),ne("click",y,function(...J){var S;(S=t.onNewChat)==null||S.apply(this,J)}),v(k,P)};E(_,k=>{s()?k(w):k(A,-1)})}L(k=>Te(p,1,k),[()=>kt(Ct("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",s()?"w-[260px]":"w-[52px]"))]),v(e,p),Jr()}Vn(["click"]);var yv=h('<button class="send-btn active"><!></button>'),kv=h("<button><!></button>"),Cv=h('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),Sv=h('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),Mv=h('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),Ev=h('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function od(e,t){Xr(t,!0);let r=rt(t,"inputText",15,""),a=rt(t,"isLoading",3,!1),s=rt(t,"large",3,!1),o=rt(t,"placeholder",3,"메시지를 입력하세요..."),i=W(Pt([])),l=W(!1),c=W(-1),f=null,p=W(void 0);function _(b){var Y;if(n(l)&&n(i).length>0){if(b.key==="ArrowDown"){b.preventDefault(),u(c,(n(c)+1)%n(i).length);return}if(b.key==="ArrowUp"){b.preventDefault(),u(c,n(c)<=0?n(i).length-1:n(c)-1,!0);return}if(b.key==="Enter"&&n(c)>=0){b.preventDefault(),k(n(i)[n(c)]);return}if(b.key==="Escape"){u(l,!1),u(c,-1);return}}b.key==="Enter"&&!b.shiftKey&&(b.preventDefault(),u(l,!1),(Y=t.onSend)==null||Y.call(t))}function w(b){b.target.style.height="auto",b.target.style.height=Math.min(b.target.scrollHeight,200)+"px"}function A(b){w(b);const Y=r();f&&clearTimeout(f),Y.length>=2&&!/\s/.test(Y.slice(-1))?f=setTimeout(async()=>{var te;try{const Z=await Fl(Y.trim());((te=Z.results)==null?void 0:te.length)>0?(u(i,Z.results.slice(0,6),!0),u(l,!0),u(c,-1)):u(l,!1)}catch{u(l,!1)}},300):u(l,!1)}function k(b){var Y;r(`${b.corpName} `),u(l,!1),u(c,-1),(Y=t.onCompanySelect)==null||Y.call(t,b),n(p)&&n(p).focus()}function P(){setTimeout(()=>{u(l,!1)},200)}var y=Ev(),C=d(y),V=d(C);Ja(V,b=>u(p,b),()=>n(p));var J=m(V,2);{var S=b=>{var Y=yv(),te=d(Y);lv(te,{size:14}),ne("click",Y,function(...Z){var z;(z=t.onStop)==null||z.apply(this,Z)}),v(b,Y)},G=b=>{var Y=kv(),te=d(Y);{let Z=U(()=>s()?18:16);Wf(te,{get size(){return n(Z)},strokeWidth:2.5})}L((Z,z)=>{Te(Y,1,Z),Y.disabled=z},[()=>kt(Ct("send-btn",r().trim()&&"active")),()=>!r().trim()]),ne("click",Y,()=>{var Z;u(l,!1),(Z=t.onSend)==null||Z.call(t)}),v(b,Y)};E(J,b=>{a()&&t.onStop?b(S):b(G,-1)})}var ie=m(C,2);{var O=b=>{var Y=Mv();Ee(Y,21,()=>n(i),Me,(te,Z,z)=>{var oe=Sv(),we=d(oe);_s(we,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var ye=m(we,2),pe=d(ye),ze=d(pe),be=m(pe,2),he=d(be),K=m(ye,2);{var T=D=>{var ae=Cv(),ce=d(ae);L(()=>$(ce,n(Z).sector)),v(D,ae)};E(K,D=>{n(Z).sector&&D(T)})}L(D=>{Te(oe,1,D),$(ze,n(Z).corpName),$(he,`${n(Z).stockCode??""} · ${(n(Z).market||"")??""}`)},[()=>kt(Ct("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",z===n(c)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),ne("mousedown",oe,()=>k(n(Z))),Ra("mouseenter",oe,()=>{u(c,z,!0)}),v(te,oe)}),v(b,Y)};E(ie,b=>{n(l)&&n(i).length>0&&b(O)})}L(b=>{Te(C,1,b),Dn(V,"placeholder",o())},[()=>kt(Ct("input-box",s()&&"large"))]),ne("keydown",V,_),ne("input",V,A),Ra("blur",V,P),Oa(V,r),v(e,y),Jr()}Vn(["keydown","input","click","mousedown"]);var zv=h('<button class="rounded-full border border-dl-border/60 bg-dl-bg-card/40 px-3 py-1.5 text-[12px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"> </button>'),Av=h(`<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[580px] flex flex-col items-center"><div class="relative mb-8"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p> <div class="mb-6 max-w-[520px] rounded-2xl border border-dl-border/50 bg-dl-bg-card/50 px-4 py-3 text-left"><div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">Evidence First</div> <div class="mt-2 text-[13px] leading-relaxed text-dl-text-muted">DartLab은 재무 수치와 서술 텍스트를 함께 읽고, 표준화된 계정과 원문 근거를 같은 흐름에서 확인하도록 설계되어 있습니다.
				DART와 EDGAR를 포함한 40개 모듈 이상의 기능 범위를 먼저 물어본 뒤 바로 탐색을 시작할 수 있습니다.</div></div> <div class="w-full"><!></div> <div class="mt-5 flex w-full flex-wrap justify-center gap-2"></div></div></div>`);function Tv(e,t){Xr(t,!0);let r=rt(t,"inputText",15,"");const a=["지금 dartlab에서 할 수 있는 기능을 먼저 정리해줘","EDGAR에서 추가로 받을 수 있는 데이터와 방법을 알려줘","OpenDart와 OpenEdgar로 가능한 일을 비교해줘","GPT 연결 시 현재 UI에서 가능한 코딩 작업 범위를 알려줘"];var s=Av(),o=d(s),i=m(d(o),8),l=d(i);od(l,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get onCompanySelect(){return t.onCompanySelect},get inputText(){return r()},set inputText(f){r(f)}});var c=m(i,2);Ee(c,21,()=>a,Me,(f,p)=>{var _=zv(),w=d(_);L(()=>$(w,n(p))),ne("click",_,()=>{var A;return(A=t.onSend)==null?void 0:A.call(t,n(p))}),v(f,_)}),v(e,s),Jr()}Vn(["click"]);var Iv=h("<span><!></span>");function Ri(e,t){Xr(t,!0);let r=rt(t,"variant",3,"default");const a={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var s=Iv(),o=d(s);Mo(o,()=>t.children),L(i=>Te(s,1,i),[()=>kt(Ct("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",a[r()],t.class))]),v(e,s),Jr()}function Pv(e){const t=e.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(t)||t==="-"||t==="0"}function Qa(e){if(!e)return"";let t=[],r=[],a=e.replace(/```(\w*)\n([\s\S]*?)```/g,(o,i,l)=>{const c=t.length;return t.push(l.trimEnd()),`
%%CODE_${c}%%
`});a=a.replace(/((?:^\|.+\|$\n?)+)/gm,o=>{const i=o.trim().split(`
`).filter(w=>w.trim());let l=null,c=-1,f=[];for(let w=0;w<i.length;w++)if(i[w].slice(1,-1).split("|").map(k=>k.trim()).every(k=>/^[\-:]+$/.test(k))){c=w;break}c>0?(l=i[c-1],f=i.slice(c+1)):(c===0||(l=i[0]),f=i.slice(1));let p="<table>";if(l){const w=l.slice(1,-1).split("|").map(A=>A.trim());p+="<thead><tr>"+w.map(A=>`<th>${A.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(f.length>0){p+="<tbody>";for(const w of f){const A=w.slice(1,-1).split("|").map(k=>k.trim());p+="<tr>"+A.map(k=>{let P=k.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${Pv(k)?' class="num"':""}>${P}</td>`}).join("")+"</tr>"}p+="</tbody>"}p+="</table>";let _=r.length;return r.push(p),`
%%TABLE_${_}%%
`});let s=a.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");s=s.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,o=>"<ul>"+o.replace(/<br>/g,"")+"</ul>");for(let o=0;o<r.length;o++)s=s.replace(`%%TABLE_${o}%%`,r[o]);for(let o=0;o<t.length;o++){const i=t[o].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");s=s.replace(`%%CODE_${o}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${o}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${i}</code></pre></div>`)}return s=s.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(o,i)=>i.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+s+"</p>"}var Nv=h('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),$v=h('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),Lv=h('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),Ov=h('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),Rv=h('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!></div></div>'),Dv=h('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),jv=h('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),Vv=h('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),Fv=h('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),qv=h("<button><!> </button>"),Bv=h('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),Gv=h('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),Hv=h('<!> <span class="text-dl-text-dim"> </span>',1),Uv=h('<div class="flex items-center gap-2 text-[11px]"><!></div>'),Wv=h('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),Kv=h('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),Yv=h('<div class="message-committed"><!></div>'),Xv=h('<div><div class="message-live-label"> </div> <pre> </pre></div>'),Jv=h('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),Qv=h('<span class="text-dl-accent/60"> </span>'),Zv=h('<span class="text-dl-success/60"> </span>'),ep=h('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),tp=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),rp=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),np=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),ap=h('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),sp=h("<!>  <div><!> <!></div> <!>",1),op=h('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),ip=h('<span class="text-[10px] text-dl-text-dim"> </span>'),lp=h('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),dp=h("<button> </button>"),cp=h('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),up=h("<button>시스템 프롬프트</button>"),fp=h("<button>LLM 입력</button>"),vp=h('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),pp=h('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),mp=h('<span class="text-dl-text"> </span>'),hp=h('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),gp=h('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),xp=h('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),bp=h("<!> <!>",1);function _p(e,t){Xr(t,!0);let r=W(null),a=W("context"),s=W("raw"),o=U(()=>{var T,D,ae,ce,fe,le;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((T=t.message.toolEvents)==null?void 0:T.length)>0){const q=[...t.message.toolEvents].reverse().find(Ie=>Ie.type==="call"),We=((D=q==null?void 0:q.arguments)==null?void 0:D.module)||((ae=q==null?void 0:q.arguments)==null?void 0:ae.keyword)||"";return`도구 실행 중 — ${(q==null?void 0:q.name)||""}${We?` (${We})`:""}`}if(((ce=t.message.contexts)==null?void 0:ce.length)>0){const q=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(q==null?void 0:q.label)||(q==null?void 0:q.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(fe=t.message.meta)!=null&&fe.company?`${t.message.meta.company} 데이터 검색 중`:(le=t.message.meta)!=null&&le.includedModules?"분석 모듈 선택 완료":"생각 중"}),i=U(()=>{var T;return t.message.company||((T=t.message.meta)==null?void 0:T.company)||null}),l=U(()=>{var T,D,ae;return t.message.systemPrompt||t.message.userContent||((T=t.message.contexts)==null?void 0:T.length)>0||((D=t.message.meta)==null?void 0:D.includedModules)||((ae=t.message.toolEvents)==null?void 0:ae.length)>0}),c=U(()=>{var D;const T=(D=t.message.meta)==null?void 0:D.dataYearRange;return T?typeof T=="string"?T:T.min_year&&T.max_year?`${T.min_year}~${T.max_year}년`:null:null});function f(T){if(!T)return 0;const D=(T.match(/[\uac00-\ud7af]/g)||[]).length,ae=T.length-D;return Math.round(D*1.5+ae/3.5)}function p(T){return T>=1e3?(T/1e3).toFixed(1)+"k":String(T)}let _=U(()=>{var D;let T=0;if(t.message.systemPrompt&&(T+=f(t.message.systemPrompt)),t.message.userContent)T+=f(t.message.userContent);else if(((D=t.message.contexts)==null?void 0:D.length)>0)for(const ae of t.message.contexts)T+=f(ae.text);return T}),w=U(()=>f(t.message.text)),A=W(void 0);const k=/^\s*\|.+\|\s*$/;function P(T,D){if(!T)return{committed:"",draft:"",draftType:"none"};if(!D)return{committed:T,draft:"",draftType:"none"};const ae=T.split(`
`);let ce=ae.length;T.endsWith(`
`)||(ce=Math.min(ce,ae.length-1));let fe=0,le=-1;for(let et=0;et<ae.length;et++)ae[et].trim().startsWith("```")&&(fe+=1,le=et);fe%2===1&&le>=0&&(ce=Math.min(ce,le));let q=-1;for(let et=ae.length-1;et>=0;et--){const Qt=ae[et];if(!Qt.trim())break;if(k.test(Qt))q=et;else{q=-1;break}}if(q>=0&&(ce=Math.min(ce,q)),ce<=0)return{committed:"",draft:T,draftType:q===0?"table":fe%2===1?"code":"text"};const We=ae.slice(0,ce).join(`
`),Ie=ae.slice(ce).join(`
`);let Gt="text";return Ie&&q>=ce?Gt="table":Ie&&fe%2===1&&(Gt="code"),{committed:We,draft:Ie,draftType:Gt}}const y='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',C='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function V(T){var fe;const D=T.target.closest(".code-copy-btn");if(!D)return;const ae=D.closest(".code-block-wrap"),ce=((fe=ae==null?void 0:ae.querySelector("code"))==null?void 0:fe.textContent)||"";navigator.clipboard.writeText(ce).then(()=>{D.innerHTML=C,setTimeout(()=>{D.innerHTML=y},2e3)})}function J(T){if(t.onOpenEvidence){t.onOpenEvidence("contexts",T);return}u(r,T,!0),u(a,"context"),u(s,"rendered")}function S(){if(t.onOpenEvidence){t.onOpenEvidence("system");return}u(r,0),u(a,"system"),u(s,"raw")}function G(){if(t.onOpenEvidence){t.onOpenEvidence("snapshot");return}u(r,0),u(a,"snapshot")}function ie(T){var D;if(t.onOpenEvidence){const ae=(D=t.message.toolEvents)==null?void 0:D[T];t.onOpenEvidence((ae==null?void 0:ae.type)==="result"?"tool-results":"tool-calls",T);return}u(r,T,!0),u(a,"tool"),u(s,"raw")}function O(){if(t.onOpenEvidence){t.onOpenEvidence("input");return}u(r,0),u(a,"userContent"),u(s,"raw")}function b(){u(r,null)}function Y(T){var D,ae,ce,fe;return T?T.type==="call"?((D=T.arguments)==null?void 0:D.module)||((ae=T.arguments)==null?void 0:ae.keyword)||((ce=T.arguments)==null?void 0:ce.engine)||((fe=T.arguments)==null?void 0:fe.name)||"":typeof T.result=="string"?T.result.slice(0,120):T.result&&typeof T.result=="object"&&(T.result.module||T.result.status||T.result.name)||"":""}let te=U(()=>(t.message.toolEvents||[]).filter(T=>T.type==="call")),Z=U(()=>(t.message.toolEvents||[]).filter(T=>T.type==="result")),z=U(()=>P(t.message.text||"",t.message.loading)),oe=U(()=>{var D,ae,ce;const T=[];return((ae=(D=t.message.meta)==null?void 0:D.includedModules)==null?void 0:ae.length)>0&&T.push({label:`모듈 ${t.message.meta.includedModules.length}개`,icon:fs}),((ce=t.message.contexts)==null?void 0:ce.length)>0&&T.push({label:`컨텍스트 ${t.message.contexts.length}건`,icon:tv}),n(te).length>0&&T.push({label:`툴 호출 ${n(te).length}건`,icon:Oi}),n(Z).length>0&&T.push({label:`툴 결과 ${n(Z).length}건`,icon:xs}),t.message.systemPrompt&&T.push({label:"시스템 프롬프트",icon:oo}),t.message.userContent&&T.push({label:"LLM 입력",icon:On}),T}),we=U(()=>{var D,ae,ce;if(!t.message.loading)return[];const T=[];return(D=t.message.meta)!=null&&D.company&&T.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&T.push({label:"핵심 수치 확인",done:!0}),(ae=t.message.meta)!=null&&ae.includedModules&&T.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((ce=t.message.contexts)==null?void 0:ce.length)>0&&T.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&T.push({label:"프롬프트 조립",done:!0}),t.message.text?T.push({label:"응답 작성 중",done:!1}):T.push({label:n(o)||"준비 중",done:!1}),T});var ye=bp(),pe=ee(ye);{var ze=T=>{var D=Nv(),ae=m(d(D),2),ce=d(ae),fe=d(ce);L(()=>$(fe,t.message.text)),v(T,D)},be=T=>{var D=op(),ae=m(d(D),2),ce=d(ae);{var fe=nt=>{var Pe=Rv(),ct=d(Pe),nr=d(ct);Uf(nr,{size:11});var St=m(ct,4),vt=d(St);{var ht=F=>{Ri(F,{variant:"muted",children:(Ce,it)=>{var ut=gs();L(()=>$(ut,n(i))),v(Ce,ut)},$$slots:{default:!0}})};E(vt,F=>{n(i)&&F(ht)})}var Ht=m(vt,2);{var Nt=F=>{Ri(F,{variant:"accent",children:(Ce,it)=>{var ut=gs();L(()=>$(ut,n(c))),v(Ce,ut)},$$slots:{default:!0}})};E(Ht,F=>{n(c)&&F(Nt)})}var x=m(Ht,2);{var j=F=>{var Ce=ke(),it=ee(Ce);Ee(it,17,()=>t.message.contexts,Me,(ut,Ke,$t)=>{var Vt=$v(),Nr=d(Vt);fs(Nr,{size:10,class:"flex-shrink-0"});var Sr=m(Nr);L(()=>$(Sr,` ${(n(Ke).label||n(Ke).module)??""}`)),ne("click",Vt,()=>J($t)),v(ut,Vt)}),v(F,Ce)},I=F=>{var Ce=Lv(),it=d(Ce);fs(it,{size:10,class:"flex-shrink-0"});var ut=m(it);L(()=>$(ut,` 모듈 ${t.message.meta.includedModules.length??""}개`)),v(F,Ce)};E(x,F=>{var Ce,it,ut;((Ce=t.message.contexts)==null?void 0:Ce.length)>0?F(j):((ut=(it=t.message.meta)==null?void 0:it.includedModules)==null?void 0:ut.length)>0&&F(I,1)})}var X=m(x,2);Ee(X,17,()=>n(oe),Me,(F,Ce)=>{var it=Ov(),ut=d(it);gu(ut,()=>n(Ce).icon,($t,Vt)=>{Vt($t,{size:10,class:"flex-shrink-0"})});var Ke=m(ut);L(()=>$(Ke,` ${n(Ce).label??""}`)),ne("click",it,()=>{n(Ce).label.startsWith("컨텍스트")?J(0):n(Ce).label.startsWith("툴 호출")?t.onOpenEvidence?t.onOpenEvidence("tool-calls",0):ie(0):n(Ce).label.startsWith("툴 결과")?t.onOpenEvidence?t.onOpenEvidence("tool-results",0):ie((t.message.toolEvents||[]).findIndex($t=>$t.type==="result")):n(Ce).label==="시스템 프롬프트"?S():n(Ce).label==="LLM 입력"&&O()}),v(F,it)}),v(nt,Pe)};E(ce,nt=>{var Pe,ct;(n(i)||n(c)||((Pe=t.message.contexts)==null?void 0:Pe.length)>0||(ct=t.message.meta)!=null&&ct.includedModules||n(oe).length>0)&&nt(fe)})}var le=m(ce,2);{var q=nt=>{var Pe=Fv(),ct=d(Pe);Ee(ct,21,()=>t.message.snapshot.items,Me,(vt,ht)=>{const Ht=U(()=>n(ht).status==="good"?"text-dl-success":n(ht).status==="danger"?"text-dl-primary-light":n(ht).status==="caution"?"text-amber-400":"text-dl-text");var Nt=Dv(),x=d(Nt),j=d(x),I=m(x,2),X=d(I);L(F=>{$(j,n(ht).label),Te(I,1,F),$(X,n(ht).value)},[()=>kt(Ct("text-[14px] font-semibold leading-snug mt-0.5",n(Ht)))]),v(vt,Nt)});var nr=m(ct,2);{var St=vt=>{var ht=Vv();Ee(ht,21,()=>t.message.snapshot.warnings,Me,(Ht,Nt)=>{var x=jv(),j=d(x);uv(j,{size:10});var I=m(j);L(()=>$(I,` ${n(Nt)??""}`)),v(Ht,x)}),v(vt,ht)};E(nr,vt=>{var ht;((ht=t.message.snapshot.warnings)==null?void 0:ht.length)>0&&vt(St)})}ne("click",Pe,G),v(nt,Pe)};E(le,nt=>{var Pe,ct;((ct=(Pe=t.message.snapshot)==null?void 0:Pe.items)==null?void 0:ct.length)>0&&nt(q)})}var We=m(le,2);{var Ie=nt=>{var Pe=Bv(),ct=d(Pe),nr=m(d(ct),4);Ee(nr,21,()=>t.message.toolEvents,Me,(St,vt,ht)=>{const Ht=U(()=>Y(n(vt)));var Nt=qv(),x=d(Nt);{var j=F=>{Oi(F,{size:11})},I=F=>{xs(F,{size:11})};E(x,F=>{n(vt).type==="call"?F(j):F(I,-1)})}var X=m(x);L(F=>{Te(Nt,1,F),$(X,` ${(n(vt).type==="call"?n(vt).name:`${n(vt).name} 결과`)??""}${n(Ht)?`: ${n(Ht)}`:""}`)},[()=>kt(Ct("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",n(vt).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),ne("click",Nt,()=>ie(ht)),v(St,Nt)}),v(nt,Pe)};E(We,nt=>{var Pe;((Pe=t.message.toolEvents)==null?void 0:Pe.length)>0&&nt(Ie)})}var Gt=m(We,2);{var et=nt=>{var Pe=Wv(),ct=d(Pe);Ee(ct,21,()=>n(we),Me,(nr,St)=>{var vt=Uv(),ht=d(vt);{var Ht=x=>{var j=Gv(),I=m(ee(j),2),X=d(I);L(()=>$(X,n(St).label)),v(x,j)},Nt=x=>{var j=Hv(),I=ee(j);an(I,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var X=m(I,2),F=d(X);L(()=>$(F,n(St).label)),v(x,j)};E(ht,x=>{n(St).done?x(Ht):x(Nt,-1)})}v(nr,vt)}),v(nt,Pe)},Qt=nt=>{var Pe=sp(),ct=ee(Pe);{var nr=I=>{var X=Kv(),F=d(X);an(F,{size:12,class:"animate-spin flex-shrink-0"});var Ce=m(F,2),it=d(Ce);L(()=>$(it,n(o))),v(I,X)};E(ct,I=>{t.message.loading&&I(nr)})}var St=m(ct,2),vt=d(St);{var ht=I=>{var X=Yv(),F=d(X);ra(F,()=>Qa(n(z).committed)),v(I,X)};E(vt,I=>{n(z).committed&&I(ht)})}var Ht=m(vt,2);{var Nt=I=>{var X=Xv(),F=d(X),Ce=d(F),it=m(F,2),ut=d(it);L(Ke=>{Te(X,1,Ke),$(Ce,n(z).draftType==="table"?"표 구성 중":n(z).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),$(ut,n(z).draft)},[()=>kt(Ct("message-live-tail",n(z).draftType==="table"&&"message-draft-table",n(z).draftType==="code"&&"message-draft-code"))]),v(I,X)};E(Ht,I=>{n(z).draft&&I(Nt)})}Ja(St,I=>u(A,I),()=>n(A));var x=m(St,2);{var j=I=>{var X=ap(),F=d(X);{var Ce=at=>{var Je=Jv(),Mt=d(Je);Qf(Mt,{size:10});var Q=m(Mt);L(()=>$(Q,` ${t.message.duration??""}초`)),v(at,Je)};E(F,at=>{t.message.duration&&at(Ce)})}var it=m(F,2);{var ut=at=>{var Je=ep(),Mt=d(Je);{var Q=Qe=>{var pt=Qv(),zt=d(pt);L(Ft=>$(zt,`↑${Ft??""}`),[()=>p(n(_))]),v(Qe,pt)};E(Mt,Qe=>{n(_)>0&&Qe(Q)})}var Re=m(Mt,2);{var st=Qe=>{var pt=Zv(),zt=d(pt);L(Ft=>$(zt,`↓${Ft??""}`),[()=>p(n(w))]),v(Qe,pt)};E(Re,Qe=>{n(w)>0&&Qe(st)})}v(at,Je)};E(it,at=>{(n(_)>0||n(w)>0)&&at(ut)})}var Ke=m(it,2);{var $t=at=>{var Je=tp(),Mt=d(Je);ov(Mt,{size:10}),ne("click",Je,()=>{var Q;return(Q=t.onRegenerate)==null?void 0:Q.call(t)}),v(at,Je)};E(Ke,at=>{t.onRegenerate&&at($t)})}var Vt=m(Ke,2);{var Nr=at=>{var Je=rp(),Mt=d(Je);oo(Mt,{size:10}),ne("click",Je,S),v(at,Je)};E(Vt,at=>{t.message.systemPrompt&&at(Nr)})}var Sr=m(Vt,2);{var Sn=at=>{var Je=np(),Mt=d(Je);On(Mt,{size:10});var Q=m(Mt);L((Re,st)=>$(Q,` LLM 입력 (${Re??""}자 · ~${st??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>p(f(t.message.userContent))]),ne("click",Je,O),v(at,Je)};E(Sr,at=>{t.message.userContent&&at(Sn)})}v(I,X)};E(x,I=>{!t.message.loading&&(t.message.duration||n(l)||t.onRegenerate)&&I(j)})}L(I=>Te(St,1,I),[()=>kt(Ct("prose-dartlab message-body text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),ne("click",St,V),v(nt,Pe)};E(Gt,nt=>{t.message.loading&&!t.message.text?nt(et):nt(Qt,-1)})}v(T,D)};E(pe,T=>{t.message.role==="user"?T(ze):T(be,-1)})}var he=m(pe,2);{var K=T=>{const D=U(()=>n(a)==="system"),ae=U(()=>n(a)==="userContent"),ce=U(()=>n(a)==="context"),fe=U(()=>n(a)==="snapshot"),le=U(()=>n(a)==="tool"),q=U(()=>{var Q;return n(ce)?(Q=t.message.contexts)==null?void 0:Q[n(r)]:null}),We=U(()=>{var Q;return n(le)?(Q=t.message.toolEvents)==null?void 0:Q[n(r)]:null}),Ie=U(()=>{var Q,Re,st,Qe,pt;return n(fe)?"핵심 수치 (원본 데이터)":n(D)?"시스템 프롬프트":n(ae)?"LLM에 전달된 입력":n(le)?((Q=n(We))==null?void 0:Q.type)==="call"?`${(Re=n(We))==null?void 0:Re.name} 호출`:`${(st=n(We))==null?void 0:st.name} 결과`:((Qe=n(q))==null?void 0:Qe.label)||((pt=n(q))==null?void 0:pt.module)||""}),Gt=U(()=>{var Q;return n(fe)?JSON.stringify(t.message.snapshot,null,2):n(D)?t.message.systemPrompt:n(ae)?t.message.userContent:n(le)?JSON.stringify(n(We),null,2):(Q=n(q))==null?void 0:Q.text});var et=xp(),Qt=d(et),nt=d(Qt),Pe=d(nt),ct=d(Pe),nr=d(ct);{var St=Q=>{fs(Q,{size:15,class:"text-dl-success flex-shrink-0"})},vt=Q=>{oo(Q,{size:15,class:"text-dl-primary-light flex-shrink-0"})},ht=Q=>{On(Q,{size:15,class:"text-dl-accent flex-shrink-0"})},Ht=Q=>{fs(Q,{size:15,class:"flex-shrink-0"})};E(nr,Q=>{n(fe)?Q(St):n(D)?Q(vt,1):n(ae)?Q(ht,2):Q(Ht,-1)})}var Nt=m(nr,2),x=d(Nt),j=m(Nt,2);{var I=Q=>{var Re=ip(),st=d(Re);L(Qe=>$(st,`(${Qe??""}자)`),[()=>{var Qe,pt;return(pt=(Qe=n(Gt))==null?void 0:Qe.length)==null?void 0:pt.toLocaleString()}]),v(Q,Re)};E(j,Q=>{n(D)&&Q(I)})}var X=m(ct,2),F=d(X);{var Ce=Q=>{var Re=lp(),st=d(Re),Qe=d(st);On(Qe,{size:11});var pt=m(st,2),zt=d(pt);Zf(zt,{size:11}),L((Ft,qe)=>{Te(st,1,Ft),Te(pt,1,qe)},[()=>kt(Ct("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(s)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>kt(Ct("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(s)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),ne("click",st,()=>u(s,"rendered")),ne("click",pt,()=>u(s,"raw")),v(Q,Re)};E(F,Q=>{n(ce)&&Q(Ce)})}var it=m(F,2),ut=d(it);Vs(ut,{size:18});var Ke=m(Pe,2);{var $t=Q=>{var Re=cp(),st=d(Re);Ee(st,21,()=>t.message.contexts,Me,(Qe,pt,zt)=>{var Ft=dp(),qe=d(Ft);L(wt=>{Te(Ft,1,wt),$(qe,t.message.contexts[zt].label||t.message.contexts[zt].module)},[()=>kt(Ct("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",zt===n(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),ne("click",Ft,()=>{u(r,zt,!0)}),v(Qe,Ft)}),v(Q,Re)};E(Ke,Q=>{var Re;n(ce)&&((Re=t.message.contexts)==null?void 0:Re.length)>1&&Q($t)})}var Vt=m(Ke,2);{var Nr=Q=>{var Re=vp(),st=d(Re),Qe=d(st);{var pt=qe=>{var wt=up();L(ar=>Te(wt,1,ar),[()=>kt(Ct("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(D)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),ne("click",wt,()=>{u(a,"system")}),v(qe,wt)};E(Qe,qe=>{t.message.systemPrompt&&qe(pt)})}var zt=m(Qe,2);{var Ft=qe=>{var wt=fp();L(ar=>Te(wt,1,ar),[()=>kt(Ct("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(ae)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),ne("click",wt,()=>{u(a,"userContent")}),v(qe,wt)};E(zt,qe=>{t.message.userContent&&qe(Ft)})}v(Q,Re)};E(Vt,Q=>{!n(ce)&&!n(fe)&&!n(le)&&Q(Nr)})}var Sr=m(nt,2),Sn=d(Sr);{var at=Q=>{var Re=pp(),st=d(Re);ra(st,()=>{var Qe;return Qa((Qe=n(q))==null?void 0:Qe.text)}),v(Q,Re)},Je=Q=>{var Re=hp(),st=d(Re),Qe=m(d(st),2),pt=d(Qe),zt=m(pt);{var Ft=Mr=>{var Mn=mp(),Zt=d(Mn);L(cn=>$(Zt,cn),[()=>Y(n(We))]),v(Mr,Mn)},qe=U(()=>Y(n(We)));E(zt,Mr=>{n(qe)&&Mr(Ft)})}var wt=m(st,2),ar=d(wt);L(()=>{var Mr;$(pt,`${((Mr=n(We))==null?void 0:Mr.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),$(ar,n(Gt))}),v(Q,Re)},Mt=Q=>{var Re=gp(),st=d(Re);L(()=>$(st,n(Gt))),v(Q,Re)};E(Sn,Q=>{n(ce)&&n(s)==="rendered"?Q(at):n(le)?Q(Je,1):Q(Mt,-1)})}L(()=>$(x,n(Ie))),ne("click",et,Q=>{Q.target===Q.currentTarget&&b()}),ne("keydown",et,Q=>{Q.key==="Escape"&&b()}),ne("click",it,b),v(T,et)};E(he,T=>{n(r)!==null&&T(K)})}v(e,ye),Jr()}Vn(["click","keydown"]);var wp=h('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),yp=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),kp=h('<div class="flex justify-end gap-2 mb-1.5"><!></div>'),Cp=h('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8"><!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function Sp(e,t){Xr(t,!0);function r(Z){if(s())return!1;for(let z=a().length-1;z>=0;z--)if(a()[z].role==="assistant"&&!a()[z].error&&a()[z].text)return z===Z;return!1}let a=rt(t,"messages",19,()=>[]),s=rt(t,"isLoading",3,!1),o=rt(t,"inputText",15,""),i=rt(t,"scrollTrigger",3,0);rt(t,"selectedCompany",3,null);function l(Z){return(z,oe)=>{var ye,pe,ze,be;(ye=t.onOpenEvidence)==null||ye.call(t,z,oe);let we;if(z==="contexts")we=(pe=Z.contexts)==null?void 0:pe[oe];else if(z==="snapshot")we={label:"핵심 수치",module:"snapshot",text:JSON.stringify(Z.snapshot,null,2)};else if(z==="system")we={label:"시스템 프롬프트",module:"system",text:Z.systemPrompt};else if(z==="input")we={label:"LLM 입력",module:"input",text:Z.userContent};else if(z==="tool-calls"||z==="tool-results"){const he=(ze=Z.toolEvents)==null?void 0:ze[oe];we={label:`${(he==null?void 0:he.name)||"도구"} ${(he==null?void 0:he.type)==="call"?"호출":"결과"}`,module:"tool",text:JSON.stringify(he,null,2)}}we&&((be=t.onOpenData)==null||be.call(t,we))}}let c,f,p=W(!0),_=W(!1),w=W(!0);function A(){if(!c)return;const{scrollTop:Z,scrollHeight:z,clientHeight:oe}=c;u(w,z-Z-oe<96),n(w)?(u(p,!0),u(_,!1)):(u(p,!1),u(_,!0))}function k(Z="smooth"){f&&(f.scrollIntoView({block:"end",behavior:Z}),u(p,!0),u(_,!1))}ta(()=>{i(),!(!c||!f)&&requestAnimationFrame(()=>{!c||!f||(n(p)||n(w)?(f.scrollIntoView({block:"end",behavior:s()?"auto":"smooth"}),u(_,!1)):u(_,!0))})});var P=Cp(),y=d(P),C=d(y),V=d(C);Ee(V,17,a,Me,(Z,z,oe)=>{{let we=U(()=>r(oe)?t.onRegenerate:void 0),ye=U(()=>t.onOpenData?l(n(z)):void 0);_p(Z,{get message(){return n(z)},get onRegenerate(){return n(we)},get onOpenEvidence(){return n(ye)}})}});var J=m(V,2);Ja(J,Z=>f=Z,()=>f),Ja(y,Z=>c=Z,()=>c);var S=m(y,2);{var G=Z=>{var z=wp(),oe=d(z);ne("click",oe,()=>k("smooth")),v(Z,z)};E(S,Z=>{n(_)&&Z(G)})}var ie=m(S,2),O=d(ie),b=d(O);{var Y=Z=>{var z=kp(),oe=d(z);{var we=ye=>{var pe=yp(),ze=d(pe);bs(ze,{size:10}),ne("click",pe,function(...be){var he;(he=t.onExport)==null||he.apply(this,be)}),v(ye,pe)};E(oe,ye=>{a().length>1&&t.onExport&&ye(we)})}v(Z,z)};E(b,Z=>{s()||Z(Y)})}var te=m(b,2);od(te,{get isLoading(){return s()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get onCompanySelect(){return t.onCompanySelect},get inputText(){return o()},set inputText(Z){o(Z)}}),Ra("scroll",y,A),v(e,P),Jr()}Vn(["click"]);var Mp=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!> <span class="text-[13px]">공시 데이터 로딩 중...</span></div>'),Ep=h('<div class="text-[11px] text-dl-text-dim"> </div>'),zp=h('<button><!> <span class="truncate flex-1"> </span></button>'),Ap=h('<div class="py-0.5"></div>'),Tp=h('<div><button class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] opacity-30 font-normal"> </span></button> <!></div>'),Ip=h('<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50"><div class="px-3 py-2.5 border-b border-dl-border/20"><!></div> <!></nav>'),Pp=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim"><!> <p class="text-[13px]">좌측에서 섹션을 선택하세요</p></div>'),Np=h('<div class="text-[10px] text-dl-text-dim/50 mb-0.5"> </div>'),$p=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!></div>'),Lp=h('<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>'),Op=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Rp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Dp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),jp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Vp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Fp=h('<div class="vw-heading-node svelte-1l2nqwu"><!></div>'),qp=h('<div class="vw-heading-block svelte-1l2nqwu"></div>'),Bp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Gp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Hp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Up=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Wp=h('<button><span class="vw-timeline-label svelte-1l2nqwu"> </span></button>'),Kp=h('<div class="vw-section-timeline svelte-1l2nqwu"></div>'),Yp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Xp=h('<span class="vw-meta-pill svelte-1l2nqwu">비교 없음</span>'),Jp=h('<div class="vw-section-actions svelte-1l2nqwu"><span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span></div>'),Qp=h('<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span> </div>'),Zp=h('<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),em=h('<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),tm=h('<div class="text-[10px] text-dl-text-dim/35 mt-1"> </div>'),rm=h('<div class="vw-digest svelte-1l2nqwu"><div class="flex items-center gap-2 mb-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span></div> <div class="space-y-1"><!> <!> <!> <!></div></div>'),nm=h('<p class="vw-para"> </p>'),am=h('<div class="vw-diff-added svelte-1l2nqwu"> </div>'),sm=h('<div class="vw-diff-deleted svelte-1l2nqwu"> </div>'),om=h('<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow svelte-1l2nqwu"></div>'),im=h('<div class="disclosure-text vw-section-body vw-body-frame svelte-1l2nqwu"><!></div>'),lm=h('<div><!> <div class="vw-section-meta svelte-1l2nqwu"><span> </span> <!> <!> <!> <!></div> <!> <!> <!> <!></div>'),dm=h('<section class="vw-report-shell svelte-1l2nqwu"><div class="vw-report-header svelte-1l2nqwu"><div class="vw-report-badges svelte-1l2nqwu"><!> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <!> <!></div></div> <!></section>'),cm=h('<div class="vw-data-divider svelte-1l2nqwu"><div class="vw-data-kicker svelte-1l2nqwu">Structured Data</div> <div class="vw-data-title svelte-1l2nqwu">표 / 정형 데이터</div></div>'),um=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),fm=h("<th> </th>"),vm=h("<td> </td>"),pm=h("<tr></tr>"),mm=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),hm=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),gm=h("<th> </th>"),xm=h("<td> </td>"),bm=h("<tr></tr>"),_m=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),wm=h("<button> </button>"),ym=h('<span class="text-[9px] text-dl-text-dim/30"> </span>'),km=h('<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto"><!> <!></div>'),Cm=h('<div class="vw-table-wrap bg-dl-bg-card/10 svelte-1l2nqwu"><!> <div class="px-4 py-3"><div class="markdown-table overflow-x-auto svelte-1l2nqwu"><!></div></div></div>'),Sm=h("<th> </th>"),Mm=h("<td> </td>"),Em=h("<tr></tr>"),zm=h('<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02] svelte-1l2nqwu"><div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10"><!> <span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span></div> <div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Am=h('<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card"> </th>'),Tm=h('<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted"> </td>'),Im=h("<tr></tr>"),Pm=h('<div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Nm=h('<article class="py-6 px-8"><!> <!> <!> <!></article>'),$m=h('<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center"><div class="flex-1 min-w-0"><!> <h3 class="text-[16px] font-semibold text-dl-text"> </h3></div> <button class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"><!></button></div> <!>',1),Lm=h('<div class="flex flex-1 overflow-hidden min-h-0"><!> <main class="flex-1 overflow-y-auto min-w-0"><!></main></div>'),Om=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8"><!> <p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p></div>'),Rm=h('<div class="flex flex-col h-full font-sans bg-dl-bg-dark"><!></div>');function Dm(e,t){Xr(t,!0);let r=rt(t,"stockCode",3,null),a=rt(t,"onTopicChange",3,null),s=W(null),o=W(!1),i=W(Pt(new Set)),l=W(null),c=W(null),f=W(Pt([])),p=W(null),_=W(!1),w=W(Pt([])),A=W(Pt(new Map)),k=new Map,P=W(!1),y=W(Pt(new Map));const C={companyOverview:"회사 개요",companyHistory:"회사 연혁",articlesOfIncorporation:"정관 사항",capitalChange:"자본금 변동",shareCapital:"주식 현황",dividend:"배당",productService:"사업 내용",rawMaterial:"원재료",businessOverview:"사업 개요",salesOrder:"매출/수주",riskDerivative:"위험관리/파생",majorContractsAndRnd:"주요 계약/R&D",otherReferences:"기타 참고사항",consolidatedStatements:"연결 재무제표",fsSummary:"재무제표 요약",consolidatedNotes:"연결 주석",financialStatements:"개별 재무제표",financialNotes:"개별 주석",fundraising:"자금조달",BS:"재무상태표",IS:"손익계산서",CIS:"포괄손익계산서",CF:"현금흐름표",SCE:"자본변동표",ratios:"재무비율",audit:"감사 의견",mdna:"경영진 분석(MD&A)",internalControl:"내부통제",auditContract:"감사 계약",nonAuditContract:"비감사 계약",boardOfDirectors:"이사회",shareholderMeeting:"주주총회",auditSystem:"감사 체계",outsideDirector:"사외이사",majorHolder:"주요 주주",majorHolderChange:"주주 변동",minorityHolder:"소수주주",stockTotal:"주식 총수",treasuryStock:"자기주식",employee:"직원 현황",executivePay:"임원 보수",executive:"임원 현황",executivePayAllTotal:"전체 보수 총액",executivePayIndividual:"개인별 보수",topPay:"5억이상 상위 보수",unregisteredExecutivePay:"미등기임원 보수",affiliateGroup:"계열회사",investedCompany:"투자회사",relatedPartyTx:"특수관계 거래",corporateBond:"사채 관리",privateOfferingUsage:"사모자금 사용",publicOfferingUsage:"공모자금 사용",shortTermBond:"단기사채",investorProtection:"투자자 보호",disclosureChanges:"공시변경 사항",contingentLiability:"우발채무",sanction:"제재/조치",subsequentEvents:"후발사건",expertConfirmation:"전문가 확인",subsidiaryDetail:"종속회사 상세",affiliateGroupDetail:"계열회사 상세",investmentInOtherDetail:"타법인 출자 상세",rndDetail:"R&D 상세"},V={I:"I. 회사의 개요",II:"II. 사업의 내용",III:"III. 재무에 관한 사항",IV:"IV. 감사인의 감사의견 등",V:"V. 이사의 경영진단 및 분석의견",VI:"VI. 이사회 등 회사의 기관에 관한 사항",VII:"VII. 주주에 관한 사항",VIII:"VIII. 임원 및 직원 등에 관한 사항",IX:"IX. 계열회사 등에 관한 사항",X:"X. 대주주 등과의 거래내용",XI:"XI. 그 밖에 투자자 보호를 위하여 필요한 사항",XII:"XII. 상세표"},J={I:1,II:2,III:3,IV:4,V:5,VI:6,VII:7,VIII:8,IX:9,X:10,XI:11,XII:12};function S(x){return J[x]??99}function G(x){return C[x]||x}function ie(x){return V[x]||x||"기타"}ta(()=>{r()&&O()});async function O(){var x,j;u(o,!0),u(s,null),u(l,null),u(c,null),u(f,[],!0),u(p,null),k=new Map;try{const I=await Vu(r());u(s,I.payload,!0),(x=n(s))!=null&&x.columns&&u(w,n(s).columns.filter(F=>/^\d{4}(Q[1-4])?$/.test(F)),!0);const X=we((j=n(s))==null?void 0:j.rows);X.length>0&&(u(i,new Set([X[0].chapter]),!0),X[0].topics.length>0&&b(X[0].topics[0].topic,X[0].chapter))}catch(I){console.error("viewer load error:",I)}u(o,!1)}async function b(x,j){var I;if(n(l)!==x){if(u(l,x,!0),u(c,j||null,!0),u(A,new Map,!0),u(y,new Map,!0),(I=a())==null||I(x,G(x)),k.has(x)){const X=k.get(x);u(f,X.blocks||[],!0),u(p,X.textDocument||null,!0);return}u(f,[],!0),u(p,null),u(_,!0);try{const X=await ju(r(),x);u(f,X.blocks||[],!0),u(p,X.textDocument||null,!0),k.set(x,{blocks:n(f),textDocument:n(p)})}catch(X){console.error("topic load error:",X),u(f,[],!0),u(p,null)}u(_,!1)}}function Y(x){const j=new Set(n(i));j.has(x)?j.delete(x):j.add(x),u(i,j,!0)}function te(x,j){const I=new Map(n(A));I.get(x)===j?I.delete(x):I.set(x,j),u(A,I,!0)}function Z(x,j){const I=new Map(n(y));I.set(x,j),u(y,I,!0)}function z(x){return x==="updated"?"최근 수정":x==="new"?"신규":x==="stale"?"과거 유지":"유지"}function oe(x){return x==="updated"?"updated":x==="new"?"new":x==="stale"?"stale":"stable"}function we(x){if(!x)return[];const j=new Map,I=new Set;for(const X of x){const F=X.chapter||"";j.has(F)||j.set(F,{chapter:F,topics:[]}),I.has(X.topic)||(I.add(X.topic),j.get(F).topics.push({topic:X.topic,source:X.source||"docs"}))}return[...j.values()].sort((X,F)=>S(X.chapter)-S(F.chapter))}function ye(x){return String(x).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function pe(x){return String(x||"").replaceAll(" "," ").replace(/\s+/g," ").trim()}function ze(x){return!x||x.length>88?!1:/^\[.+\]$/.test(x)||/^【.+】$/.test(x)||/^[IVX]+\.\s/.test(x)||/^\d+\.\s/.test(x)||/^[가-힣]\.\s/.test(x)||/^\(\d+\)\s/.test(x)||/^\([가-힣]\)\s/.test(x)}function be(x){return/^\(\d+\)\s/.test(x)||/^\([가-힣]\)\s/.test(x)?"h5":"h4"}function he(x){return/^\[.+\]$/.test(x)||/^【.+】$/.test(x)?"vw-h-bracket":/^\(\d+\)\s/.test(x)||/^\([가-힣]\)\s/.test(x)?"vw-h-sub":"vw-h-section"}function K(x){if(!x)return[];if(/^\|.+\|$/m.test(x)||/^#{1,3} /m.test(x)||/```/.test(x))return[{kind:"markdown",text:x}];const j=[];let I=[];const X=()=>{I.length!==0&&(j.push({kind:"paragraph",text:I.join(" ")}),I=[])};for(const F of String(x).split(`
`)){const Ce=pe(F);if(!Ce){X();continue}if(ze(Ce)){X(),j.push({kind:"heading",text:Ce,tag:be(Ce),className:he(Ce)});continue}I.push(Ce)}return X(),j}function T(x){return x?x.kind==="annual"?`${x.year}Q4`:x.year&&x.quarter?`${x.year}Q${x.quarter}`:x.label||"":""}function D(x){var X;const j=K(x);if(j.length===0)return"";if(((X=j[0])==null?void 0:X.kind)==="markdown")return Qa(x);let I="";for(const F of j){if(F.kind==="heading"){I+=`<${F.tag} class="${F.className}">${ye(F.text)}</${F.tag}>`;continue}I+=`<p class="vw-para">${ye(F.text)}</p>`}return I}function ae(x){if(!x)return"";const j=x.trim().split(`
`).filter(X=>X.trim());let I="";for(const X of j){const F=X.trim();/^[가-힣]\.\s/.test(F)||/^\d+[-.]/.test(F)?I+=`<h4 class="vw-h-section">${F}</h4>`:/^\(\d+\)\s/.test(F)||/^\([가-힣]\)\s/.test(F)?I+=`<h5 class="vw-h-sub">${F}</h5>`:/^\[.+\]$/.test(F)||/^【.+】$/.test(F)?I+=`<h4 class="vw-h-bracket">${F}</h4>`:I+=`<h5 class="vw-h-sub">${F}</h5>`}return I}function ce(x){var I;const j=n(A).get(x.id);return j&&((I=x==null?void 0:x.views)!=null&&I[j])?x.views[j]:(x==null?void 0:x.latest)||null}function fe(x,j){var X,F;const I=n(A).get(x.id);return I?I===j:((F=(X=x==null?void 0:x.latest)==null?void 0:X.period)==null?void 0:F.label)===j}function le(x){return n(A).has(x.id)}function q(x){return x==="updated"?"변경 있음":x==="new"?"직전 없음":"직전과 동일"}function We(x){var Ce,it,ut;if(!x)return[];const j=K(x.body);if(j.length===0||((Ce=j[0])==null?void 0:Ce.kind)==="markdown"||!((it=x.prevPeriod)!=null&&it.label)||!((ut=x.diff)!=null&&ut.length))return j;const I=[];for(const Ke of x.diff)for(const $t of Ke.paragraphs||[])I.push({kind:Ke.kind,text:pe($t)});const X=[];let F=0;for(const Ke of j){if(Ke.kind!=="paragraph"){X.push(Ke);continue}for(;F<I.length&&I[F].kind==="removed";)X.push({kind:"removed",text:I[F].text}),F+=1;F<I.length&&["same","added"].includes(I[F].kind)?(X.push({kind:I[F].kind,text:I[F].text||Ke.text}),F+=1):X.push({kind:"same",text:Ke.text})}for(;F<I.length;)X.push({kind:I[F].kind,text:I[F].text}),F+=1;return X}function Ie(x){return x==null?!1:/^-?[\d,.]+%?$/.test(String(x).trim().replace(/,/g,""))}function Gt(x){return x==null?!1:/^-[\d.]+/.test(String(x).trim().replace(/,/g,""))}function et(x,j){if(x==null||x==="")return"";const I=typeof x=="number"?x:Number(String(x).replace(/,/g,""));if(isNaN(I))return String(x);if(j<=1)return I.toLocaleString("ko-KR");const X=I/j;return Number.isInteger(X)?X.toLocaleString("ko-KR"):X.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g,",")}function Qt(x){if(x==null||x==="")return"";const j=String(x).trim();if(j.includes(","))return j;const I=j.match(/^(-?\d+)(\.\d+)?(%?)$/);return I?I[1].replace(/\B(?=(\d{3})+(?!\d))/g,",")+(I[2]||"")+(I[3]||""):j}function nt(x){var j,I;return(j=n(s))!=null&&j.rows&&((I=n(s).rows.find(X=>X.topic===x))==null?void 0:I.chapter)||null}function Pe(x){const j=x.match(/^(\d{4})(Q([1-4]))?$/);if(!j)return"0000_0";const I=j[1],X=j[3]||"5";return`${I}_${X}`}function ct(x){return[...x].sort((j,I)=>Pe(I).localeCompare(Pe(j)))}let nr=U(()=>n(f).filter(x=>x.kind!=="text"));var St=Rm(),vt=d(St);{var ht=x=>{var j=Mp(),I=d(j);an(I,{size:18,class:"animate-spin"}),v(x,j)},Ht=x=>{var j=Lm(),I=d(j);{var X=Ke=>{var $t=Ip(),Vt=d($t),Nr=d(Vt);{var Sr=at=>{var Je=Ep(),Mt=d(Je);L(()=>$(Mt,`${n(w).length??""}개 기간 · ${n(w)[0]??""} ~ ${n(w)[n(w).length-1]??""}`)),v(at,Je)};E(Nr,at=>{n(w).length>0&&at(Sr)})}var Sn=m(Vt,2);Ee(Sn,17,()=>we(n(s).rows),Me,(at,Je)=>{var Mt=Tp(),Q=d(Mt),Re=d(Q);{var st=Zt=>{Xf(Zt,{size:11,class:"flex-shrink-0 opacity-40"})},Qe=U(()=>n(i).has(n(Je).chapter)),pt=Zt=>{Jf(Zt,{size:11,class:"flex-shrink-0 opacity-40"})};E(Re,Zt=>{n(Qe)?Zt(st):Zt(pt,-1)})}var zt=m(Re,2),Ft=d(zt),qe=m(zt,2),wt=d(qe),ar=m(Q,2);{var Mr=Zt=>{var cn=Ap();Ee(cn,21,()=>n(Je).topics,Me,(ua,En)=>{var Rt=zp(),De=d(Rt);{var gr=er=>{Kf(er,{size:11,class:"flex-shrink-0 text-blue-400/40"})},fa=er=>{Ii(er,{size:11,class:"flex-shrink-0 text-emerald-400/40"})},zn=er=>{On(er,{size:11,class:"flex-shrink-0 opacity-30"})};E(De,er=>{n(En).source==="finance"?er(gr):n(En).source==="report"?er(fa,1):er(zn,-1)})}var va=m(De,2),un=d(va);L(er=>{Te(Rt,1,`group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											${n(l)===n(En).topic?"bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]":"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent"}`),$(un,er)},[()=>G(n(En).topic)]),ne("click",Rt,()=>b(n(En).topic,n(Je).chapter)),v(ua,Rt)}),v(Zt,cn)},Mn=U(()=>n(i).has(n(Je).chapter));E(ar,Zt=>{n(Mn)&&Zt(Mr)})}L(Zt=>{$(Ft,Zt),$(wt,n(Je).topics.length)},[()=>ie(n(Je).chapter)]),ne("click",Q,()=>Y(n(Je).chapter)),v(at,Mt)}),v(Ke,$t)};E(I,Ke=>{n(P)||Ke(X)})}var F=m(I,2),Ce=d(F);{var it=Ke=>{var $t=Pp(),Vt=d($t);On(Vt,{size:32,strokeWidth:1,class:"opacity-20"}),v(Ke,$t)},ut=Ke=>{var $t=$m(),Vt=ee($t),Nr=d(Vt),Sr=d(Nr);{var Sn=qe=>{var wt=Np(),ar=d(wt);L(Mr=>$(ar,Mr),[()=>ie(n(c)||nt(n(l)))]),v(qe,wt)},at=U(()=>n(c)||nt(n(l)));E(Sr,qe=>{n(at)&&qe(Sn)})}var Je=m(Sr,2),Mt=d(Je),Q=m(Nr,2),Re=d(Q);{var st=qe=>{sd(qe,{size:15})},Qe=qe=>{ad(qe,{size:15})};E(Re,qe=>{n(P)?qe(st):qe(Qe,-1)})}var pt=m(Vt,2);{var zt=qe=>{var wt=$p(),ar=d(wt);an(ar,{size:16,class:"animate-spin"}),v(qe,wt)},Ft=qe=>{var wt=Nm(),ar=d(wt);{var Mr=Rt=>{var De=Lp();v(Rt,De)};E(ar,Rt=>{var De,gr;n(f).length===0&&!(((gr=(De=n(p))==null?void 0:De.sections)==null?void 0:gr.length)>0)&&Rt(Mr)})}var Mn=m(ar,2);{var Zt=Rt=>{var De=dm(),gr=d(De),fa=d(gr),zn=d(fa);{var va=Ze=>{var ge=Op(),Ne=d(ge);L(tt=>$(Ne,`최신 기준 ${tt??""}`),[()=>T(n(p).latestPeriod)]),v(Ze,ge)};E(zn,Ze=>{n(p).latestPeriod&&Ze(va)})}var un=m(zn,2);{var er=Ze=>{var ge=Rp(),Ne=d(ge);L((tt,xt)=>$(Ne,`커버리지 ${tt??""}~${xt??""}`),[()=>T(n(p).firstPeriod),()=>T(n(p).latestPeriod)]),v(Ze,ge)};E(un,Ze=>{n(p).firstPeriod&&Ze(er)})}var Na=m(un,2),Ut=d(Na),gt=m(Na,2);{var sr=Ze=>{var ge=Dp(),Ne=d(ge);L(()=>$(Ne,`최근 수정 ${n(p).updatedCount??""}개`)),v(Ze,ge)};E(gt,Ze=>{n(p).updatedCount>0&&Ze(sr)})}var qt=m(gt,2);{var or=Ze=>{var ge=jp(),Ne=d(ge);L(()=>$(Ne,`신규 ${n(p).newCount??""}개`)),v(Ze,ge)};E(qt,Ze=>{n(p).newCount>0&&Ze(or)})}var xr=m(qt,2);{var br=Ze=>{var ge=Vp(),Ne=d(ge);L(()=>$(Ne,`과거 유지 ${n(p).staleCount??""}개`)),v(Ze,ge)};E(xr,Ze=>{n(p).staleCount>0&&Ze(br)})}var $r=m(gr,2);Ee($r,17,()=>n(p).sections,Me,(Ze,ge)=>{const Ne=U(()=>ce(n(ge))),tt=U(()=>le(n(ge)));var xt=lm(),ir=d(xt);{var Se=N=>{var B=qp();Ee(B,21,()=>n(ge).headingPath,Me,(de,ve)=>{var dt=Fp(),ft=d(dt);ra(ft,()=>ae(n(ve).text)),v(de,dt)}),v(N,B)};E(ir,N=>{var B;((B=n(ge).headingPath)==null?void 0:B.length)>0&&N(Se)})}var Ye=m(ir,2),lt=d(Ye),At=d(lt),g=m(lt,2);{var R=N=>{var B=Bp(),de=d(B);L(ve=>$(de,`최신 ${ve??""}`),[()=>T(n(ge).latestPeriod)]),v(N,B)};E(g,N=>{var B;(B=n(ge).latestPeriod)!=null&&B.label&&N(R)})}var ue=m(g,2);{var _e=N=>{var B=Gp(),de=d(B);L(ve=>$(de,`최초 ${ve??""}`),[()=>T(n(ge).firstPeriod)]),v(N,B)};E(ue,N=>{var B,de;(B=n(ge).firstPeriod)!=null&&B.label&&n(ge).firstPeriod.label!==((de=n(ge).latestPeriod)==null?void 0:de.label)&&N(_e)})}var xe=m(ue,2);{var Ae=N=>{var B=Hp(),de=d(B);L(()=>$(de,`${n(ge).periodCount??""}기간`)),v(N,B)};E(xe,N=>{n(ge).periodCount>0&&N(Ae)})}var me=m(xe,2);{var $e=N=>{var B=Up(),de=d(B);L(()=>$(de,`최근 변경 ${n(ge).latestChange??""}`)),v(N,B)};E(me,N=>{n(ge).latestChange&&N($e)})}var _r=m(Ye,2);{var lr=N=>{var B=Kp();Ee(B,21,()=>n(ge).timeline,Me,(de,ve)=>{var dt=Wp(),ft=d(dt),mt=d(ft);L((Lt,yt)=>{Te(dt,1,`vw-timeline-chip ${Lt??""}`,"svelte-1l2nqwu"),$(mt,yt)},[()=>fe(n(ge),n(ve).period.label)?"is-active":"",()=>T(n(ve).period)]),ne("click",dt,()=>te(n(ge).id,n(ve).period.label)),v(de,dt)}),v(N,B)};E(_r,N=>{var B;((B=n(ge).timeline)==null?void 0:B.length)>0&&N(lr)})}var An=m(_r,2);{var Fn=N=>{var B=Jp(),de=d(B),ve=d(de),dt=m(de,2);{var ft=Tt=>{var Dt=Yp(),Lr=d(Dt);L(bt=>$(Lr,`비교 ${bt??""}`),[()=>T(n(Ne).prevPeriod)]),v(Tt,Dt)},mt=Tt=>{var Dt=Xp();v(Tt,Dt)};E(dt,Tt=>{var Dt;(Dt=n(Ne).prevPeriod)!=null&&Dt.label?Tt(ft):Tt(mt,-1)})}var Lt=m(dt,2),yt=d(Lt);L((Tt,Dt)=>{$(ve,`선택 ${Tt??""}`),$(yt,Dt)},[()=>T(n(Ne).period),()=>q(n(Ne).status)]),v(N,B)};E(An,N=>{n(tt)&&n(Ne)&&N(Fn)})}var Tn=m(An,2);{var qn=N=>{const B=U(()=>n(Ne).digest);var de=rm(),ve=d(de),dt=d(ve),ft=d(dt),mt=m(ve,2),Lt=d(mt);Ee(Lt,17,()=>n(B).items.filter(bt=>bt.kind==="numeric"),Me,(bt,dr)=>{var Wt=Qp(),It=m(d(Wt));L(()=>$(It,` ${n(dr).text??""}`)),v(bt,Wt)});var yt=m(Lt,2);Ee(yt,17,()=>n(B).items.filter(bt=>bt.kind==="added"),Me,(bt,dr)=>{var Wt=Zp(),It=m(d(Wt),2),Kt=d(It);L(()=>$(Kt,n(dr).text)),v(bt,Wt)});var Tt=m(yt,2);Ee(Tt,17,()=>n(B).items.filter(bt=>bt.kind==="removed"),Me,(bt,dr)=>{var Wt=em(),It=m(d(Wt),2),Kt=d(It);L(()=>$(Kt,n(dr).text)),v(bt,Wt)});var Dt=m(Tt,2);{var Lr=bt=>{var dr=tm(),Wt=d(dr);L(()=>$(Wt,`외 ${n(B).wordingCount??""}건 문구 수정`)),v(bt,dr)};E(Dt,bt=>{n(B).wordingCount>0&&bt(Lr)})}L(()=>$(ft,`${n(B).to??""} vs ${n(B).from??""}`)),v(N,de)};E(Tn,N=>{var B,de,ve;n(tt)&&((ve=(de=(B=n(Ne))==null?void 0:B.digest)==null?void 0:de.items)==null?void 0:ve.length)>0&&N(qn)})}var Bn=m(Tn,2);{var H=N=>{var B=ke(),de=ee(B);{var ve=ft=>{var mt=om();Ee(mt,21,()=>We(n(Ne)),Me,(Lt,yt)=>{var Tt=ke(),Dt=ee(Tt);{var Lr=It=>{var Kt=ke(),In=ee(Kt);ra(In,()=>ae(n(yt).text)),v(It,Kt)},bt=It=>{var Kt=nm(),In=d(Kt);L(()=>$(In,n(yt).text)),v(It,Kt)},dr=It=>{var Kt=am(),In=d(Kt);L(()=>$(In,n(yt).text)),v(It,Kt)},Wt=It=>{var Kt=sm(),In=d(Kt);L(()=>$(In,n(yt).text)),v(It,Kt)};E(Dt,It=>{n(yt).kind==="heading"?It(Lr):n(yt).kind==="same"?It(bt,1):n(yt).kind==="added"?It(dr,2):n(yt).kind==="removed"&&It(Wt,3)})}v(Lt,Tt)}),v(ft,mt)},dt=ft=>{var mt=im(),Lt=d(mt);ra(Lt,()=>D(n(Ne).body)),v(ft,mt)};E(de,ft=>{var mt,Lt;n(tt)&&((mt=n(Ne).prevPeriod)!=null&&mt.label)&&((Lt=n(Ne).diff)==null?void 0:Lt.length)>0?ft(ve):ft(dt,-1)})}v(N,B)};E(Bn,N=>{n(Ne)&&N(H)})}L((N,B)=>{Te(xt,1,`vw-text-section ${n(ge).status==="stale"?"vw-text-section-stale":""}`,"svelte-1l2nqwu"),Te(lt,1,`vw-status-pill ${N??""}`,"svelte-1l2nqwu"),$(At,B)},[()=>oe(n(ge).status),()=>z(n(ge).status)]),v(Ze,xt)}),L(()=>$(Ut,`본문 ${n(p).sectionCount??""}개`)),v(Rt,De)};E(Mn,Rt=>{var De,gr;((gr=(De=n(p))==null?void 0:De.sections)==null?void 0:gr.length)>0&&Rt(Zt)})}var cn=m(Mn,2);{var ua=Rt=>{var De=cm();v(Rt,De)};E(cn,Rt=>{n(nr).length>0&&Rt(ua)})}var En=m(cn,2);Ee(En,17,()=>n(nr),Me,(Rt,De)=>{var gr=ke(),fa=ee(gr);{var zn=Ut=>{const gt=U(()=>{var Se;return((Se=n(De).data)==null?void 0:Se.columns)||[]}),sr=U(()=>{var Se;return((Se=n(De).data)==null?void 0:Se.rows)||[]}),qt=U(()=>n(De).meta||{}),or=U(()=>n(qt).scaleDivisor||1);var xr=mm(),br=ee(xr);{var $r=Se=>{var Ye=um(),lt=d(Ye);L(()=>$(lt,`(단위: ${n(qt).scale??""})`)),v(Se,Ye)};E(br,Se=>{n(qt).scale&&Se($r)})}var Ze=m(br,2),ge=d(Ze),Ne=d(ge),tt=d(Ne),xt=d(tt);Ee(xt,21,()=>n(gt),Me,(Se,Ye,lt)=>{const At=U(()=>/^\d{4}/.test(n(Ye)));var g=fm(),R=d(g);L(()=>{Te(g,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(At)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${lt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),$(R,n(Ye))}),v(Se,g)});var ir=m(tt);Ee(ir,21,()=>n(sr),Me,(Se,Ye,lt)=>{var At=pm();Te(At,1,`hover:bg-white/[0.03] ${lt%2===1?"bg-white/[0.012]":""}`),Ee(At,21,()=>n(gt),Me,(g,R,ue)=>{const _e=U(()=>n(Ye)[n(R)]??""),xe=U(()=>Ie(n(_e))),Ae=U(()=>Gt(n(_e))),me=U(()=>n(xe)?et(n(_e),n(or)):n(_e));var $e=vm(),_r=d($e);L(()=>{Te($e,1,`px-3 py-1.5 border-b border-white/[0.025]
																	${n(xe)?"text-right tabular-nums font-mono text-[11.5px]":"whitespace-nowrap"}
																	${n(Ae)?"text-red-400/60":n(xe)?"text-dl-text/90":""}
																	${ue===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]":"text-dl-text-muted"}
																	${ue===0&&lt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),$(_r,n(me))}),v(g,$e)}),v(Se,At)}),v(Ut,xr)},va=Ut=>{const gt=U(()=>{var Se;return((Se=n(De).data)==null?void 0:Se.columns)||[]}),sr=U(()=>{var Se;return((Se=n(De).data)==null?void 0:Se.rows)||[]}),qt=U(()=>n(De).meta||{}),or=U(()=>n(qt).scaleDivisor||1);var xr=_m(),br=ee(xr);{var $r=Se=>{var Ye=hm(),lt=d(Ye);L(()=>$(lt,`(단위: ${n(qt).scale??""})`)),v(Se,Ye)};E(br,Se=>{n(qt).scale&&Se($r)})}var Ze=m(br,2),ge=d(Ze),Ne=d(ge),tt=d(Ne),xt=d(tt);Ee(xt,21,()=>n(gt),Me,(Se,Ye,lt)=>{const At=U(()=>/^\d{4}/.test(n(Ye)));var g=gm(),R=d(g);L(()=>{Te(g,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(At)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${lt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),$(R,n(Ye))}),v(Se,g)});var ir=m(tt);Ee(ir,21,()=>n(sr),Me,(Se,Ye,lt)=>{var At=bm();Te(At,1,`hover:bg-white/[0.03] ${lt%2===1?"bg-white/[0.012]":""}`),Ee(At,21,()=>n(gt),Me,(g,R,ue)=>{const _e=U(()=>n(Ye)[n(R)]??""),xe=U(()=>Ie(n(_e))),Ae=U(()=>Gt(n(_e))),me=U(()=>n(xe)?n(or)>1?et(n(_e),n(or)):Qt(n(_e)):n(_e));var $e=xm(),_r=d($e);L(()=>{Te($e,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(xe)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(Ae)?"text-red-400/60":n(xe)?"text-dl-text/90":""}
																	${ue===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${ue===0&&lt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),$(_r,n(me))}),v(g,$e)}),v(Se,At)}),v(Ut,xr)},un=Ut=>{const gt=U(()=>ct(Object.keys(n(De).rawMarkdown))),sr=U(()=>n(y).get(n(De).block)??0),qt=U(()=>n(gt)[n(sr)]||n(gt)[0]);var or=Cm(),xr=d(or);{var br=Ne=>{var tt=km(),xt=d(tt);Ee(xt,17,()=>n(gt).slice(0,8),Me,(Ye,lt,At)=>{var g=wm(),R=d(g);L(()=>{Te(g,1,`px-2 py-0.5 rounded text-[10px] transition-colors
															${At===n(sr)?"bg-white/[0.08] text-dl-text font-medium":"text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]"}`),$(R,n(lt))}),ne("click",g,()=>Z(n(De).block,At)),v(Ye,g)});var ir=m(xt,2);{var Se=Ye=>{var lt=ym(),At=d(lt);L(()=>$(At,`외 ${n(gt).length-8}개`)),v(Ye,lt)};E(ir,Ye=>{n(gt).length>8&&Ye(Se)})}v(Ne,tt)};E(xr,Ne=>{n(gt).length>1&&Ne(br)})}var $r=m(xr,2),Ze=d($r),ge=d(Ze);ra(ge,()=>Qa(n(De).rawMarkdown[n(qt)])),v(Ut,or)},er=Ut=>{const gt=U(()=>{var tt;return((tt=n(De).data)==null?void 0:tt.columns)||[]}),sr=U(()=>{var tt;return((tt=n(De).data)==null?void 0:tt.rows)||[]});var qt=zm(),or=d(qt),xr=d(or);Ii(xr,{size:12,class:"text-emerald-400/50"});var br=m(or,2),$r=d(br),Ze=d($r),ge=d(Ze);Ee(ge,21,()=>n(gt),Me,(tt,xt,ir)=>{const Se=U(()=>/^\d{4}/.test(n(xt)));var Ye=Sm(),lt=d(Ye);L(()=>{Te(Ye,1,`px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															${n(Se)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
															${ir===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),$(lt,n(xt))}),v(tt,Ye)});var Ne=m(Ze);Ee(Ne,21,()=>n(sr),Me,(tt,xt,ir)=>{var Se=Em();Te(Se,1,`hover:bg-white/[0.03] ${ir%2===1?"bg-white/[0.012]":""}`),Ee(Se,21,()=>n(gt),Me,(Ye,lt,At)=>{const g=U(()=>n(xt)[n(lt)]??""),R=U(()=>Ie(n(g))),ue=U(()=>Gt(n(g)));var _e=Mm(),xe=d(_e);L(Ae=>{Te(_e,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(R)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(ue)?"text-red-400/60":n(R)?"text-dl-text/90":""}
																	${At===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${At===0&&ir%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),$(xe,Ae)},[()=>n(R)?Qt(n(g)):n(g)]),v(Ye,_e)}),v(tt,Se)}),v(Ut,qt)},Na=Ut=>{const gt=U(()=>n(De).data.columns),sr=U(()=>n(De).data.rows||[]);var qt=Pm(),or=d(qt),xr=d(or),br=d(xr),$r=d(br);Ee($r,21,()=>n(gt),Me,(ge,Ne)=>{var tt=Am(),xt=d(tt);L(()=>$(xt,n(Ne))),v(ge,tt)});var Ze=m(br);Ee(Ze,21,()=>n(sr),Me,(ge,Ne,tt)=>{var xt=Im();Te(xt,1,`hover:bg-white/[0.03] ${tt%2===1?"bg-white/[0.012]":""}`),Ee(xt,21,()=>n(gt),Me,(ir,Se)=>{var Ye=Tm(),lt=d(Ye);L(()=>$(lt,n(Ne)[n(Se)]??"")),v(ir,Ye)}),v(ge,xt)}),v(Ut,qt)};E(fa,Ut=>{var gt,sr;n(De).kind==="finance"?Ut(zn):n(De).kind==="structured"?Ut(va,1):n(De).kind==="raw_markdown"&&n(De).rawMarkdown?Ut(un,2):n(De).kind==="report"?Ut(er,3):((sr=(gt=n(De).data)==null?void 0:gt.columns)==null?void 0:sr.length)>0&&Ut(Na,4)})}v(Rt,gr)}),v(qe,wt)};E(pt,qe=>{n(_)?qe(zt):qe(Ft,-1)})}L(qe=>{$(Mt,qe),Dn(Q,"title",n(P)?"목차 표시":"전체화면")},[()=>G(n(l))]),ne("click",Q,()=>u(P,!n(P))),v(Ke,$t)};E(Ce,Ke=>{n(l)?Ke(ut,-1):Ke(it)})}v(x,j)},Nt=x=>{var j=Om(),I=d(j);On(I,{size:36,strokeWidth:1,class:"opacity-20"}),v(x,j)};E(vt,x=>{var j;n(o)?x(ht):(j=n(s))!=null&&j.rows?x(Ht,1):x(Nt,-1)})}v(e,St),Jr()}Vn(["click"]);var jm=h('<span class="text-[12px] font-semibold text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim"> </span>',1),Vm=h('<span class="text-[12px] font-semibold text-dl-text"> </span>'),Fm=h('<span class="text-[12px] font-semibold text-dl-text">데이터</span>'),qm=h('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" title="Excel 다운로드"><!></button> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button>',1),Bm=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Gm=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed"> </pre>'),Hm=h('<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2"> </div>'),Um=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Wm=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),Km=h("<!> <!>",1),Ym=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),Xm=h('<div class="p-4"><!></div>'),Jm=h('<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">표시할 내용이 없습니다</div>'),Qm=h('<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark"><div class="flex items-center justify-between h-10 mt-8 px-4 border-b border-dl-border/40 flex-shrink-0"><div class="flex items-center gap-2 min-w-0"><!></div> <div class="flex items-center gap-1"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 overflow-auto min-h-0"><!></div></div>');function Zm(e,t){Xr(t,!0);let r=rt(t,"mode",3,null),a=rt(t,"company",3,null),s=rt(t,"data",3,null),o=rt(t,"onTopicChange",3,null),i=rt(t,"onFullscreen",3,null),l=rt(t,"isFullscreen",3,!1),c=W(!1);async function f(){var z;if(!(!((z=a())!=null&&z.stockCode)||n(c))){u(c,!0);try{await Du(a().stockCode)}catch(oe){console.error("Excel download error:",oe)}u(c,!1)}}function p(z){return z?/^\|.+\|$/m.test(z)||/^#{1,3} /m.test(z)||/\*\*[^*]+\*\*/m.test(z)||/```/.test(z):!1}var _=Qm(),w=d(_),A=d(w),k=d(A);{var P=z=>{var oe=jm(),we=ee(oe),ye=d(we),pe=m(we,2),ze=d(pe);L(()=>{$(ye,a().corpName||a().company),$(ze,a().stockCode)}),v(z,oe)},y=z=>{var oe=Vm(),we=d(oe);L(()=>$(we,s().label)),v(z,oe)},C=z=>{var oe=Fm();v(z,oe)};E(k,z=>{var oe;r()==="viewer"&&a()?z(P):r()==="data"&&((oe=s())!=null&&oe.label)?z(y,1):r()==="data"&&z(C,2)})}var V=m(A,2),J=d(V);{var S=z=>{var oe=qm(),we=ee(oe),ye=d(we);{var pe=D=>{an(D,{size:14,class:"animate-spin"})},ze=D=>{bs(D,{size:14})};E(ye,D=>{n(c)?D(pe):D(ze,-1)})}var be=m(we,2),he=d(be);{var K=D=>{sd(D,{size:14})},T=D=>{ad(D,{size:14})};E(he,D=>{l()?D(K):D(T,-1)})}L(()=>{we.disabled=n(c),Dn(be,"title",l()?"패널 모드로":"전체 화면")}),ne("click",we,f),ne("click",be,()=>{var D;return(D=i())==null?void 0:D()}),v(z,oe)};E(J,z=>{var oe;r()==="viewer"&&((oe=a())!=null&&oe.stockCode)&&z(S)})}var G=m(J,2),ie=d(G);Vs(ie,{size:15});var O=m(w,2),b=d(O);{var Y=z=>{Dm(z,{get stockCode(){return a().stockCode},get onTopicChange(){return o()}})},te=z=>{var oe=Xm(),we=d(oe);{var ye=be=>{var he=ke(),K=ee(he);{var T=ce=>{var fe=Bm(),le=d(fe);ra(le,()=>Qa(s())),v(ce,fe)},D=U(()=>p(s())),ae=ce=>{var fe=Gm(),le=d(fe);L(()=>$(le,s())),v(ce,fe)};E(K,ce=>{n(D)?ce(T):ce(ae,-1)})}v(be,he)},pe=be=>{var he=Km(),K=ee(he);{var T=le=>{var q=Hm(),We=d(q);L(()=>$(We,s().module)),v(le,q)};E(K,le=>{s().module&&le(T)})}var D=m(K,2);{var ae=le=>{var q=Um(),We=d(q);ra(We,()=>Qa(s().text)),v(le,q)},ce=U(()=>p(s().text)),fe=le=>{var q=Wm(),We=d(q);L(()=>$(We,s().text)),v(le,q)};E(D,le=>{n(ce)?le(ae):le(fe,-1)})}v(be,he)},ze=be=>{var he=Ym(),K=d(he);L(T=>$(K,T),[()=>JSON.stringify(s(),null,2)]),v(be,he)};E(we,be=>{var he;typeof s()=="string"?be(ye):(he=s())!=null&&he.text?be(pe,1):be(ze,-1)})}v(z,oe)},Z=z=>{var oe=Jm();v(z,oe)};E(b,z=>{r()==="viewer"&&a()?z(Y):r()==="data"&&s()?z(te,1):z(Z,-1)})}ne("click",G,()=>{var z;return(z=t.onClose)==null?void 0:z.call(t)}),v(e,_),Jr()}Vn(["click"]);var eh=h('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),th=h("<!> <span>확인 중...</span>",1),rh=h("<!> <span>설정 필요</span>",1),nh=h('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),ah=h('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!>',1),sh=h('<div class="flex-shrink-0 border-l border-dl-border/30 transition-all duration-300"><!></div>'),oh=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),ih=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),lh=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),dh=h('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),ch=h('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),uh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),fh=h('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),vh=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),ph=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),mh=h('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),hh=h('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),gh=h('<div class="text-[10px] text-dl-text-dim mt-2"> </div>'),xh=h('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex login</div></div></div></div> <!> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),bh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2"> </div></div>'),_h=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 계정 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),wh=h('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),yh=h("<button> <!></button>"),kh=h('<div class="flex flex-wrap gap-1.5"></div>'),Ch=h('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),Sh=h('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),Mh=h('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),Eh=h('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),zh=h('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),Ah=h('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),Th=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),Ih=h("<!> <!> <!> <!> <!> <!>",1),Ph=h('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),Nh=h('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),$h=h('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),Lh=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><span class="text-[10px] text-dl-text-dim">공시 보기</span> <!></div></button>'),Oh=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div></div> <!>',1),Rh=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div></button>'),Dh=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div></div> <!>',1),jh=h('<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),Vh=h('<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim"><!> <div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div> <div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div></div>'),Fh=h('<div class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn" role="presentation"><div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"><div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"/> <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div> <div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim"><span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span></div></div></div>'),qh=h('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),Bh=h('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-2 left-3 z-20 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="종목 검색 (Ctrl+K)"><!></button> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <button><!> <!></button></div> <div class="flex flex-1 min-h-0"><div class="min-w-0 flex-1 flex flex-col"><!></div> <!></div></div></div>  <!> <!> <!> <!>',1);function Gh(e,t){Xr(t,!0);let r=W(""),a=W(!1),s=W(null),o=W(Pt({})),i=W(Pt({})),l=W(null),c=W(null),f=W(Pt([])),p=W(!1),_=W(0),w=W(!0),A=W(""),k=W(!1),P=W(null),y=W(Pt({})),C=W(Pt({})),V=W(""),J=W(!1),S=W(null),G=W(""),ie=W(!1),O=W(""),b=W(0),Y=W(null),te=W(null),Z=W(null);const z=jf();let oe=W(!1),we=U(()=>n(oe)?"100%":z.panelMode==="viewer"?"65%":"50%"),ye=W(!1),pe=W(""),ze=W(Pt([])),be=W(-1),he=null,K=W(!1);function T(){u(K,window.innerWidth<=768),n(K)&&(u(p,!1),z.closePanel())}ta(()=>(T(),window.addEventListener("resize",T),()=>window.removeEventListener("resize",T))),ta(()=>{!n(k)||!n(te)||requestAnimationFrame(()=>{var g;return(g=n(te))==null?void 0:g.focus()})}),ta(()=>{!n(D)||!n(Z)||requestAnimationFrame(()=>{var g;return(g=n(Z))==null?void 0:g.focus()})});let D=W(null),ae=W(""),ce=W("error"),fe=W(!1);function le(g,R="error",ue=4e3){u(ae,g,!0),u(ce,R,!0),u(fe,!0),setTimeout(()=>{u(fe,!1)},ue)}const q=Lf();ta(()=>{Gt()});let We=W(Pt({}));function Ie(g){return g==="chatgpt"?"codex":g}async function Gt(){var g,R,ue;u(w,!0);try{const _e=await $u();u(o,_e.providers||{},!0),u(i,_e.ollama||{},!0),u(We,_e.codex||{},!0),_e.version&&u(A,_e.version,!0);const xe=Ie(localStorage.getItem("dartlab-provider")),Ae=localStorage.getItem("dartlab-model");if(xe&&((g=n(o)[xe])!=null&&g.available)){u(l,xe,!0),u(P,xe,!0),await La(xe,Ae),await et(xe);const me=n(y)[xe]||[];Ae&&me.includes(Ae)?u(c,Ae,!0):me.length>0&&(u(c,me[0],!0),localStorage.setItem("dartlab-model",n(c))),u(f,me,!0),u(w,!1);return}if(xe&&n(o)[xe]){u(l,xe,!0),u(P,xe,!0),await et(xe);const me=n(y)[xe]||[];u(f,me,!0),Ae&&me.includes(Ae)?u(c,Ae,!0):me.length>0&&u(c,me[0],!0),u(w,!1);return}for(const me of["codex","ollama","openai"])if((R=n(o)[me])!=null&&R.available){u(l,me,!0),u(P,me,!0),await La(me),await et(me);const $e=n(y)[me]||[];u(f,$e,!0),u(c,((ue=n(o)[me])==null?void 0:ue.model)||($e.length>0?$e[0]:null),!0),n(c)&&localStorage.setItem("dartlab-model",n(c));break}}catch{}u(w,!1)}async function et(g){g=Ie(g),u(C,{...n(C),[g]:!0},!0);try{const R=await Lu(g);u(y,{...n(y),[g]:R.models||[]},!0)}catch{u(y,{...n(y),[g]:[]},!0)}u(C,{...n(C),[g]:!1},!0)}async function Qt(g){var ue;g=Ie(g),u(l,g,!0),u(c,null),u(P,g,!0),localStorage.setItem("dartlab-provider",g),localStorage.removeItem("dartlab-model"),u(V,""),u(S,null);try{await La(g)}catch{}await et(g);const R=n(y)[g]||[];if(u(f,R,!0),R.length>0){u(c,((ue=n(o)[g])==null?void 0:ue.model)||R[0],!0),localStorage.setItem("dartlab-model",n(c));try{await La(g,n(c))}catch{}}}async function nt(g){u(c,g,!0),localStorage.setItem("dartlab-model",g);try{await La(Ie(n(l)),g)}catch{}}function Pe(g){g=Ie(g),n(P)===g?u(P,null):(u(P,g,!0),et(g))}async function ct(){const g=n(V).trim();if(!(!g||!n(l))){u(J,!0),u(S,null);try{const R=await La(Ie(n(l)),n(c),g);R.available?(u(S,"success"),n(o)[n(l)]={...n(o)[n(l)],available:!0,model:R.model},!n(c)&&R.model&&u(c,R.model,!0),await et(n(l)),u(f,n(y)[n(l)]||[],!0),le("API 키 인증 성공","success")):u(S,"error")}catch{u(S,"error")}u(J,!1)}}async function nr(){try{await Ru(),n(l)==="codex"&&u(o,{...n(o),codex:{...n(o).codex,available:!1}},!0),le("Codex 계정 로그아웃 완료","success"),await Gt()}catch{le("로그아웃 실패")}}function St(){const g=n(G).trim();!g||n(ie)||(u(ie,!0),u(O,"준비 중..."),u(b,0),u(Y,Ou(g,{onProgress(R){R.total&&R.completed!==void 0?(u(b,Math.round(R.completed/R.total*100),!0),u(O,`다운로드 중... ${n(b)}%`)):R.status&&u(O,R.status,!0)},async onDone(){u(ie,!1),u(Y,null),u(G,""),u(O,""),u(b,0),le(`${g} 다운로드 완료`,"success"),await et("ollama"),u(f,n(y).ollama||[],!0),n(f).includes(g)&&await nt(g)},onError(R){u(ie,!1),u(Y,null),u(O,""),u(b,0),le(`다운로드 실패: ${R}`)}}),!0))}function vt(){n(Y)&&(n(Y).abort(),u(Y,null)),u(ie,!1),u(G,""),u(O,""),u(b,0)}function ht(){u(p,!n(p))}function Ht(g){z.openData(g)}function Nt(g,R=null){z.openEvidence(g,R)}function x(g){z.openViewer(g)}function j(){if(u(V,""),u(S,null),n(l))u(P,n(l),!0);else{const g=Object.keys(n(o));u(P,g.length>0?g[0]:null,!0)}u(k,!0),n(P)&&et(n(P))}function I(g){var R,ue,_e,xe;if(g)for(let Ae=g.messages.length-1;Ae>=0;Ae--){const me=g.messages[Ae];if(me.role==="assistant"&&((R=me.meta)!=null&&R.stockCode||(ue=me.meta)!=null&&ue.company||me.company)){z.syncCompanyFromMessage({company:((_e=me.meta)==null?void 0:_e.company)||me.company,stockCode:(xe=me.meta)==null?void 0:xe.stockCode},z.selectedCompany);return}}}function X(){q.createConversation(),u(r,""),u(a,!1),n(s)&&(n(s).abort(),u(s,null))}function F(g){q.setActive(g),I(q.active),u(r,""),u(a,!1),n(s)&&(n(s).abort(),u(s,null))}function Ce(g){u(D,g,!0)}function it(){n(D)&&(q.deleteConversation(n(D)),u(D,null))}function ut(){var R;const g=q.active;if(!g)return null;for(let ue=g.messages.length-1;ue>=0;ue--){const _e=g.messages[ue];if(_e.role==="assistant"&&((R=_e.meta)!=null&&R.stockCode))return _e.meta.stockCode}return null}async function Ke(g=null){var Fn,Tn,qn,Bn;const R=(g??n(r)).trim();if(!R||n(a))return;if(!n(l)||!((Fn=n(o)[n(l)])!=null&&Fn.available)){le("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),j();return}q.activeId||q.createConversation();const ue=q.activeId;q.addMessage("user",R),u(r,""),u(a,!0),q.addMessage("assistant",""),q.updateLastMessage({loading:!0,startedAt:Date.now()}),ms(_);const _e=q.active,xe=[];let Ae=null;if(_e){const H=_e.messages.slice(0,-2);for(const N of H)if((N.role==="user"||N.role==="assistant")&&N.text&&N.text.trim()&&!N.error&&!N.loading){const B={role:N.role,text:N.text};N.role==="assistant"&&((Tn=N.meta)!=null&&Tn.stockCode)&&(B.meta={company:N.meta.company||N.company,stockCode:N.meta.stockCode,modules:N.meta.includedModules||null},Ae=N.meta.stockCode),xe.push(B)}}const me=((qn=z.selectedCompany)==null?void 0:qn.stockCode)||Ae||ut(),$e=z.getViewContext();let _r=R;if(($e==null?void 0:$e.type)==="viewer"&&$e.company){let H=`
[사용자가 현재 ${$e.company.corpName}(${$e.company.stockCode}) 공시를 보고 있습니다`;$e.topic&&(H+=` — 현재 섹션: ${$e.topicLabel||$e.topic}(${$e.topic})`),H+="]",_r+=H}else($e==null?void 0:$e.type)==="data"&&((Bn=$e.data)!=null&&Bn.label)&&(_r+=`
[사용자가 현재 "${$e.data.label}" 데이터를 보고 있습니다]`);function lr(){return q.activeId!==ue}const An=Fu(me,_r,{provider:n(l),model:n(c)},{onMeta(H){var dt;if(lr())return;const N=q.active,B=N==null?void 0:N.messages[N.messages.length-1],ve={meta:{...(B==null?void 0:B.meta)||{},...H}};H.company&&(ve.company=H.company,q.activeId&&((dt=q.active)==null?void 0:dt.title)==="새 대화"&&q.updateTitle(q.activeId,H.company)),H.stockCode&&(ve.stockCode=H.stockCode),(H.company||H.stockCode)&&z.syncCompanyFromMessage(H,z.selectedCompany),q.updateLastMessage(ve)},onSnapshot(H){lr()||q.updateLastMessage({snapshot:H})},onContext(H){if(lr())return;const N=q.active;if(!N)return;const B=N.messages[N.messages.length-1],de=(B==null?void 0:B.contexts)||[];q.updateLastMessage({contexts:[...de,{module:H.module,label:H.label,text:H.text}]})},onSystemPrompt(H){lr()||q.updateLastMessage({systemPrompt:H.text,userContent:H.userContent||null})},onToolCall(H){if(lr())return;const N=q.active;if(!N)return;const B=N.messages[N.messages.length-1],de=(B==null?void 0:B.toolEvents)||[];q.updateLastMessage({toolEvents:[...de,{type:"call",name:H.name,arguments:H.arguments}]})},onToolResult(H){if(lr())return;const N=q.active;if(!N)return;const B=N.messages[N.messages.length-1],de=(B==null?void 0:B.toolEvents)||[];q.updateLastMessage({toolEvents:[...de,{type:"result",name:H.name,result:H.result}]})},onChunk(H){if(lr())return;const N=q.active;if(!N)return;const B=N.messages[N.messages.length-1];q.updateLastMessage({text:((B==null?void 0:B.text)||"")+H}),ms(_)},onDone(){if(lr())return;const H=q.active,N=H==null?void 0:H.messages[H.messages.length-1],B=N!=null&&N.startedAt?((Date.now()-N.startedAt)/1e3).toFixed(1):null;q.updateLastMessage({loading:!1,duration:B}),q.flush(),u(a,!1),u(s,null),ms(_)},onError(H,N,B){lr()||(q.updateLastMessage({text:`오류: ${H}`,loading:!1,error:!0}),q.flush(),N==="login"?(le(`${H} — 설정에서 Codex 로그인을 확인하세요`),j()):N==="install"?(le(`${H} — 설정에서 Codex 설치 안내를 확인하세요`),j()):le(H),u(a,!1),u(s,null))}},xe);u(s,An,!0)}function $t(){n(s)&&(n(s).abort(),u(s,null),u(a,!1),q.updateLastMessage({loading:!1}),q.flush())}function Vt(){const g=q.active;if(!g||g.messages.length<2)return;let R="";for(let ue=g.messages.length-1;ue>=0;ue--)if(g.messages[ue].role==="user"){R=g.messages[ue].text;break}R&&(q.removeLastMessage(),q.removeLastMessage(),u(r,R,!0),requestAnimationFrame(()=>{Ke()}))}function Nr(){const g=q.active;if(!g)return;let R=`# ${g.title}

`;for(const Ae of g.messages)Ae.role==="user"?R+=`## You

${Ae.text}

`:Ae.role==="assistant"&&Ae.text&&(R+=`## DartLab

${Ae.text}

`);const ue=new Blob([R],{type:"text/markdown;charset=utf-8"}),_e=URL.createObjectURL(ue),xe=document.createElement("a");xe.href=_e,xe.download=`${g.title||"dartlab-chat"}.md`,xe.click(),URL.revokeObjectURL(_e),le("대화가 마크다운으로 내보내졌습니다","success")}function Sr(){u(ye,!0),u(pe,""),u(ze,[],!0),u(be,-1)}function Sn(g){(g.metaKey||g.ctrlKey)&&g.key==="n"&&(g.preventDefault(),X()),(g.metaKey||g.ctrlKey)&&g.key==="k"&&(g.preventDefault(),Sr()),(g.metaKey||g.ctrlKey)&&g.shiftKey&&g.key==="S"&&(g.preventDefault(),ht()),g.key==="Escape"&&n(ye)?u(ye,!1):g.key==="Escape"&&n(k)?u(k,!1):g.key==="Escape"&&n(D)?u(D,null):g.key==="Escape"&&z.panelOpen&&z.closePanel()}let at=U(()=>{var g;return((g=q.active)==null?void 0:g.messages)||[]}),Je=U(()=>q.active&&q.active.messages.length>0),Mt=U(()=>{var g;return!n(w)&&(!n(l)||!((g=n(o)[n(l)])!=null&&g.available))});const Q=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var Re=Bh();Ra("keydown",wo,Sn);var st=ee(Re),Qe=d(st);{var pt=g=>{var R=eh();ne("click",R,()=>{u(p,!1)}),v(g,R)};E(Qe,g=>{n(K)&&n(p)&&g(pt)})}var zt=m(Qe,2),Ft=d(zt);{let g=U(()=>n(K)?!0:n(p));wv(Ft,{get conversations(){return q.conversations},get activeId(){return q.activeId},get open(){return n(g)},get version(){return n(A)},onNewChat:()=>{X(),n(K)&&u(p,!1)},onSelect:R=>{F(R),n(K)&&u(p,!1)},onDelete:Ce,onOpenSearch:Sr})}var qe=m(zt,2),wt=d(qe),ar=d(wt),Mr=d(ar);{var Mn=g=>{sv(g,{size:18})},Zt=g=>{av(g,{size:18})};E(Mr,g=>{n(p)?g(Mn):g(Zt,-1)})}var cn=m(wt,2),ua=d(cn),En=d(ua);_s(En,{size:14});var Rt=m(ua,2),De=d(Rt);On(De,{size:14});var gr=m(Rt,2),fa=d(gr);rv(fa,{size:14});var zn=m(gr,2),va=d(zn);ev(va,{size:14});var un=m(zn,2),er=d(un);{var Na=g=>{var R=th(),ue=ee(R);an(ue,{size:12,class:"animate-spin"}),v(g,R)},Ut=g=>{var R=rh(),ue=ee(R);us(ue,{size:12}),v(g,R)},gt=g=>{var R=ah(),ue=m(ee(R),2),_e=d(ue),xe=m(ue,2);{var Ae=me=>{var $e=nh(),_r=m(ee($e),2),lr=d(_r);L(()=>$(lr,n(c))),v(me,$e)};E(xe,me=>{n(c)&&me(Ae)})}L(()=>$(_e,n(l))),v(g,R)};E(er,g=>{n(w)?g(Na):n(Mt)?g(Ut,1):g(gt,-1)})}var sr=m(er,2);iv(sr,{size:12});var qt=m(cn,2),or=d(qt),xr=d(or);{var br=g=>{Sp(g,{get messages(){return n(at)},get isLoading(){return n(a)},get scrollTrigger(){return n(_)},get selectedCompany(){return z.selectedCompany},onSend:Ke,onStop:$t,onRegenerate:Vt,onExport:Nr,onOpenData:Ht,onOpenEvidence:Nt,onCompanySelect:x,get inputText(){return n(r)},set inputText(R){u(r,R,!0)}})},$r=g=>{Tv(g,{onSend:Ke,onCompanySelect:x,get inputText(){return n(r)},set inputText(R){u(r,R,!0)}})};E(xr,g=>{n(Je)?g(br):g($r,-1)})}var Ze=m(or,2);{var ge=g=>{var R=sh(),ue=d(R);Zm(ue,{get mode(){return z.panelMode},get company(){return z.selectedCompany},get data(){return z.panelData},onClose:()=>{u(oe,!1),z.closePanel()},onTopicChange:(_e,xe)=>z.setViewerTopic(_e,xe),onFullscreen:()=>{u(oe,!n(oe))},get isFullscreen(){return n(oe)}}),L(()=>Eo(R,`width: ${n(we)??""}; min-width: 360px; ${n(oe)?"":"max-width: 75vw;"}`)),v(g,R)};E(Ze,g=>{!n(K)&&z.panelOpen&&g(ge)})}var Ne=m(st,2);{var tt=g=>{var R=Nh(),ue=d(R),_e=d(ue),xe=d(_e),Ae=m(d(xe),2),me=d(Ae);Vs(me,{size:18});var $e=m(_e,2),_r=d($e);Ee(_r,21,()=>Object.entries(n(o)),Me,(H,N)=>{var B=U(()=>Bi(n(N),2));let de=()=>n(B)[0],ve=()=>n(B)[1];const dt=U(()=>de()===n(l)),ft=U(()=>n(P)===de()),mt=U(()=>ve().auth==="api_key"),Lt=U(()=>ve().auth==="cli"),yt=U(()=>n(y)[de()]||[]),Tt=U(()=>n(C)[de()]);var Dt=Ph(),Lr=d(Dt),bt=d(Lr),dr=m(bt,2),Wt=d(dr),It=d(Wt),Kt=d(It),In=m(It,2);{var id=Ot=>{var yr=oh();v(Ot,yr)};E(In,Ot=>{n(dt)&&Ot(id)})}var ld=m(Wt,2),dd=d(ld),cd=m(dr,2),ud=d(cd);{var fd=Ot=>{xs(Ot,{size:16,class:"text-dl-success"})},vd=Ot=>{var yr=ih(),Gn=ee(yr);Ni(Gn,{size:14,class:"text-amber-400"}),v(Ot,yr)},pd=Ot=>{var yr=lh(),Gn=ee(yr);us(Gn,{size:14,class:"text-amber-400"}),v(Ot,yr)},md=Ot=>{var yr=dh(),Gn=ee(yr);dv(Gn,{size:14,class:"text-dl-text-dim"}),v(Ot,yr)};E(ud,Ot=>{ve().available?Ot(fd):n(mt)?Ot(vd,1):n(Lt)&&de()==="codex"&&n(We).installed?Ot(pd,2):n(Lt)&&!ve().available&&Ot(md,3)})}var hd=m(Lr,2);{var gd=Ot=>{var yr=Ih(),Gn=ee(yr);{var xd=_t=>{var Bt=uh(),cr=d(Bt),kr=d(cr),Br=m(cr,2),wr=d(Br),Or=m(wr,2),Hn=d(Or);{var Un=ot=>{an(ot,{size:12,class:"animate-spin"})},Rr=ot=>{Ni(ot,{size:12})};E(Hn,ot=>{n(J)?ot(Un):ot(Rr,-1)})}var Qr=m(Br,2);{var Et=ot=>{var Dr=ch(),ur=d(Dr);us(ur,{size:12}),v(ot,Dr)};E(Qr,ot=>{n(S)==="error"&&ot(Et)})}L(ot=>{$(kr,ve().envKey?`환경변수 ${ve().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),Dn(wr,"placeholder",de()==="openai"?"sk-...":de()==="claude"?"sk-ant-...":"API Key"),Or.disabled=ot},[()=>!n(V).trim()||n(J)]),ne("keydown",wr,ot=>{ot.key==="Enter"&&ct()}),Oa(wr,()=>n(V),ot=>u(V,ot)),ne("click",Or,ct),v(_t,Bt)};E(Gn,_t=>{n(mt)&&!ve().available&&_t(xd)})}var Ko=m(Gn,2);{var bd=_t=>{var Bt=vh(),cr=d(Bt),kr=d(cr);xs(kr,{size:13,class:"text-dl-success"});var Br=m(cr,2),wr=d(Br),Or=m(wr,2);{var Hn=Rr=>{var Qr=fh(),Et=d(Qr);{var ot=ur=>{an(ur,{size:10,class:"animate-spin"})},Dr=ur=>{var fn=gs("변경");v(ur,fn)};E(Et,ur=>{n(J)?ur(ot):ur(Dr,-1)})}L(()=>Qr.disabled=n(J)),ne("click",Qr,ct),v(Rr,Qr)},Un=U(()=>n(V).trim());E(Or,Rr=>{n(Un)&&Rr(Hn)})}ne("keydown",wr,Rr=>{Rr.key==="Enter"&&ct()}),Oa(wr,()=>n(V),Rr=>u(V,Rr)),v(_t,Bt)};E(Ko,_t=>{n(mt)&&ve().available&&_t(bd)})}var Yo=m(Ko,2);{var _d=_t=>{var Bt=ph(),cr=m(d(Bt),2),kr=d(cr);bs(kr,{size:14});var Br=m(kr,2);Pi(Br,{size:10,class:"ml-auto"}),v(_t,Bt)},wd=_t=>{var Bt=mh(),cr=d(Bt),kr=d(cr);us(kr,{size:14}),v(_t,Bt)};E(Yo,_t=>{de()==="ollama"&&!n(i).installed?_t(_d):de()==="ollama"&&n(i).installed&&!n(i).running&&_t(wd,1)})}var Xo=m(Yo,2);{var yd=_t=>{var Bt=bh(),cr=d(Bt);{var kr=Or=>{var Hn=xh(),Un=ee(Hn),Rr=d(Un),Qr=m(Un,2),Et=d(Qr);{var ot=jr=>{var vn=hh();v(jr,vn)};E(Et,jr=>{n(We).installed||jr(ot)})}var Dr=m(Et,2),ur=d(Dr),fn=d(ur),pa=m(Qr,2);{var ns=jr=>{var vn=gh(),Wn=d(vn);L(()=>$(Wn,n(We).loginStatus)),v(jr,vn)};E(pa,jr=>{n(We).loginStatus&&jr(ns)})}var as=m(pa,2),Er=d(as);us(Er,{size:12,class:"text-amber-400 flex-shrink-0"}),L(()=>{$(Rr,n(We).installed?"Codex CLI가 설치되었지만 로그인이 필요합니다":"Codex CLI 설치가 필요합니다"),$(fn,n(We).installed?"1.":"2.")}),v(Or,Hn)};E(cr,Or=>{de()==="codex"&&Or(kr)})}var Br=m(cr,2),wr=d(Br);L(()=>$(wr,n(We).installed?"로그인 완료 후 새로고침하세요":"설치 완료 후 새로고침하세요")),v(_t,Bt)};E(Xo,_t=>{n(Lt)&&!ve().available&&_t(yd)})}var Jo=m(Xo,2);{var kd=_t=>{var Bt=_h(),cr=d(Bt),kr=d(cr),Br=d(kr);xs(Br,{size:13,class:"text-dl-success"});var wr=m(kr,2),Or=d(wr);nv(Or,{size:11}),ne("click",wr,nr),v(_t,Bt)};E(Jo,_t=>{de()==="codex"&&ve().available&&_t(kd)})}var Cd=m(Jo,2);{var Sd=_t=>{var Bt=Th(),cr=d(Bt),kr=m(d(cr),2);{var Br=Et=>{an(Et,{size:12,class:"animate-spin text-dl-text-dim"})};E(kr,Et=>{n(Tt)&&Et(Br)})}var wr=m(cr,2);{var Or=Et=>{var ot=wh(),Dr=d(ot);an(Dr,{size:14,class:"animate-spin"}),v(Et,ot)},Hn=Et=>{var ot=kh();Ee(ot,21,()=>n(yt),Me,(Dr,ur)=>{var fn=yh(),pa=d(fn),ns=m(pa);{var as=Er=>{Yf(Er,{size:10,class:"inline ml-1"})};E(ns,Er=>{n(ur)===n(c)&&n(dt)&&Er(as)})}L(Er=>{Te(fn,1,Er),$(pa,`${n(ur)??""} `)},[()=>kt(Ct("px-3 py-1.5 rounded-lg text-[11px] border transition-all",n(ur)===n(c)&&n(dt)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),ne("click",fn,()=>{de()!==n(l)&&Qt(de()),nt(n(ur))}),v(Dr,fn)}),v(Et,ot)},Un=Et=>{var ot=Ch();v(Et,ot)};E(wr,Et=>{n(Tt)&&n(yt).length===0?Et(Or):n(yt).length>0?Et(Hn,1):Et(Un,-1)})}var Rr=m(wr,2);{var Qr=Et=>{var ot=Ah(),Dr=d(ot),ur=m(d(Dr),2),fn=m(d(ur));Pi(fn,{size:9});var pa=m(Dr,2);{var ns=Er=>{var jr=Sh(),vn=d(jr),Wn=d(vn),ss=d(Wn);an(ss,{size:12,class:"animate-spin text-dl-primary-light"});var Ys=m(Wn,2),As=m(vn,2),Pn=d(As),Zr=m(As,2),Xs=d(Zr);L(()=>{Eo(Pn,`width: ${n(b)??""}%`),$(Xs,n(O))}),ne("click",Ys,vt),v(Er,jr)},as=Er=>{var jr=zh(),vn=ee(jr),Wn=d(vn),ss=m(Wn,2),Ys=d(ss);bs(Ys,{size:12});var As=m(vn,2);Ee(As,21,()=>Q,Me,(Pn,Zr)=>{const Xs=U(()=>n(yt).some($a=>$a===n(Zr).name||$a===n(Zr).name.split(":")[0]));var Qo=ke(),Md=ee(Qo);{var Ed=$a=>{var Js=Eh(),Zo=d(Js),ei=d(Zo),ti=d(ei),zd=d(ti),ri=m(ti,2),Ad=d(ri),Td=m(ri,2);{var Id=Qs=>{var ai=Mh(),Rd=d(ai);L(()=>$(Rd,n(Zr).tag)),v(Qs,ai)};E(Td,Qs=>{n(Zr).tag&&Qs(Id)})}var Pd=m(ei,2),Nd=d(Pd),$d=m(Zo,2),ni=d($d),Ld=d(ni),Od=m(ni,2);bs(Od,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),L(()=>{$(zd,n(Zr).name),$(Ad,n(Zr).size),$(Nd,n(Zr).desc),$(Ld,`${n(Zr).gb??""} GB`)}),ne("click",Js,()=>{u(G,n(Zr).name,!0),St()}),v($a,Js)};E(Md,$a=>{n(Xs)||$a(Ed)})}v(Pn,Qo)}),L(Pn=>ss.disabled=Pn,[()=>!n(G).trim()]),ne("keydown",Wn,Pn=>{Pn.key==="Enter"&&St()}),Oa(Wn,()=>n(G),Pn=>u(G,Pn)),ne("click",ss,St),v(Er,jr)};E(pa,Er=>{n(ie)?Er(ns):Er(as,-1)})}v(Et,ot)};E(Rr,Et=>{de()==="ollama"&&Et(Qr)})}v(_t,Bt)};E(Cd,_t=>{(ve().available||n(mt)||n(Lt))&&_t(Sd)})}v(Ot,yr)};E(hd,Ot=>{(n(ft)||n(dt))&&Ot(gd)})}L((Ot,yr)=>{Te(Dt,1,Ot),Te(bt,1,yr),$(Kt,ve().label||de()),$(dd,ve().desc||"")},[()=>kt(Ct("rounded-xl border transition-all",n(dt)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>kt(Ct("w-2.5 h-2.5 rounded-full flex-shrink-0",ve().available?"bg-dl-success":n(mt)?"bg-amber-400":"bg-dl-text-dim"))]),ne("click",Lr,()=>{ve().available||n(mt)?de()===n(l)?Pe(de()):Qt(de()):Pe(de())}),v(H,Dt)});var lr=m($e,2),An=d(lr),Fn=d(An);{var Tn=H=>{var N=gs();L(()=>{var B;return $(N,`현재: ${(((B=n(o)[n(l)])==null?void 0:B.label)||n(l))??""} / ${n(c)??""}`)}),v(H,N)},qn=H=>{var N=gs();L(()=>{var B;return $(N,`현재: ${(((B=n(o)[n(l)])==null?void 0:B.label)||n(l))??""}`)}),v(H,N)};E(Fn,H=>{n(l)&&n(c)?H(Tn):n(l)&&H(qn,1)})}var Bn=m(An,2);Ja(ue,H=>u(te,H),()=>n(te)),ne("click",R,H=>{H.target===H.currentTarget&&u(k,!1)}),ne("click",Ae,()=>u(k,!1)),ne("click",Bn,()=>u(k,!1)),v(g,R)};E(Ne,g=>{n(k)&&g(tt)})}var xt=m(Ne,2);{var ir=g=>{var R=$h(),ue=d(R),_e=m(d(ue),4),xe=d(_e),Ae=m(xe,2);Ja(ue,me=>u(Z,me),()=>n(Z)),ne("click",R,me=>{me.target===me.currentTarget&&u(D,null)}),ne("click",xe,()=>u(D,null)),ne("click",Ae,it),v(g,R)};E(xt,g=>{n(D)&&g(ir)})}var Se=m(xt,2);{var Ye=g=>{const R=U(()=>z.recentCompanies||[]);var ue=Fh(),_e=d(ue),xe=d(_e),Ae=d(xe);_s(Ae,{size:18,class:"text-dl-text-dim flex-shrink-0"});var me=m(Ae,2);hl(me,!0);var $e=m(xe,2),_r=d($e);{var lr=H=>{var N=Oh(),B=m(ee(N),2);Ee(B,17,()=>n(ze),Me,(de,ve,dt)=>{var ft=Lh(),mt=d(ft),Lt=d(mt),yt=m(mt,2),Tt=d(yt),Dt=d(Tt),Lr=m(Tt,2),bt=d(Lr),dr=m(yt,2),Wt=m(d(dr),2);On(Wt,{size:14,class:"text-dl-text-dim"}),L((It,Kt)=>{Te(ft,1,It),$(Lt,Kt),$(Dt,n(ve).corpName),$(bt,`${n(ve).stockCode??""} · ${(n(ve).market||"")??""}${n(ve).sector?` · ${n(ve).sector}`:""}`)},[()=>kt(Ct("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",dt===n(be)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(ve).corpName||"?").charAt(0)]),ne("click",ft,()=>{u(ye,!1),u(pe,""),u(ze,[],!0),u(be,-1),x(n(ve))}),Ra("mouseenter",ft,()=>{u(be,dt,!0)}),v(de,ft)}),v(H,N)},An=H=>{var N=Dh(),B=m(ee(N),2);Ee(B,17,()=>n(R),Me,(de,ve,dt)=>{var ft=Rh(),mt=d(ft),Lt=d(mt),yt=m(mt,2),Tt=d(yt),Dt=d(Tt),Lr=m(Tt,2),bt=d(Lr);L((dr,Wt)=>{Te(ft,1,dr),$(Lt,Wt),$(Dt,n(ve).corpName),$(bt,`${n(ve).stockCode??""} · ${(n(ve).market||"")??""}`)},[()=>kt(Ct("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",dt===n(be)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(ve).corpName||"?").charAt(0)]),ne("click",ft,()=>{u(ye,!1),u(pe,""),u(be,-1),x(n(ve))}),Ra("mouseenter",ft,()=>{u(be,dt,!0)}),v(de,ft)}),v(H,N)},Fn=U(()=>n(pe).trim().length===0&&n(R).length>0),Tn=H=>{var N=jh();v(H,N)},qn=U(()=>n(pe).trim().length>0),Bn=H=>{var N=Vh(),B=d(N);_s(B,{size:24,class:"mb-2 opacity-40"}),v(H,N)};E(_r,H=>{n(ze).length>0?H(lr):n(Fn)?H(An,1):n(qn)?H(Tn,2):H(Bn,-1)})}ne("click",ue,H=>{H.target===H.currentTarget&&u(ye,!1)}),ne("input",me,()=>{he&&clearTimeout(he),n(pe).trim().length>=1?he=setTimeout(async()=>{var H;try{const N=await Fl(n(pe).trim());u(ze,((H=N.results)==null?void 0:H.slice(0,8))||[],!0)}catch{u(ze,[],!0)}},250):u(ze,[],!0)}),ne("keydown",me,H=>{const N=n(ze).length>0?n(ze):n(R);if(H.key==="ArrowDown")H.preventDefault(),u(be,Math.min(n(be)+1,N.length-1),!0);else if(H.key==="ArrowUp")H.preventDefault(),u(be,Math.max(n(be)-1,-1),!0);else if(H.key==="Enter"&&n(be)>=0&&N[n(be)]){H.preventDefault();const B=N[n(be)];u(ye,!1),u(pe,""),u(ze,[],!0),u(be,-1),x(B)}else H.key==="Escape"&&u(ye,!1)}),Oa(me,()=>n(pe),H=>u(pe,H)),v(g,ue)};E(Se,g=>{n(ye)&&g(Ye)})}var lt=m(Se,2);{var At=g=>{var R=qh(),ue=d(R),_e=d(ue),xe=d(_e),Ae=m(_e,2),me=d(Ae);Vs(me,{size:14}),L($e=>{Te(ue,1,$e),$(xe,n(ae))},[()=>kt(Ct("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",n(ce)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":n(ce)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),ne("click",Ae,()=>{u(fe,!1)}),v(g,R)};E(lt,g=>{n(fe)&&g(At)})}L(g=>{Te(zt,1,kt(n(K)?n(p)?"sidebar-mobile":"hidden":"")),Te(un,1,g)},[()=>kt(Ct("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",n(w)?"text-dl-text-dim":n(Mt)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),ne("click",ar,ht),ne("click",ua,Sr),ne("click",un,()=>j()),v(e,Re),Jr()}Vn(["click","keydown","input"]);uu(Gh,{target:document.getElementById("app")});
