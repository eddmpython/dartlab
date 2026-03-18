var Fd=Object.defineProperty;var ii=e=>{throw TypeError(e)};var qd=(e,t,r)=>t in e?Fd(e,t,{enumerable:!0,configurable:!0,writable:!0,value:r}):e[t]=r;var on=(e,t,r)=>qd(e,typeof t!="symbol"?t+"":t,r),eo=(e,t,r)=>t.has(e)||ii("Cannot "+r);var E=(e,t,r)=>(eo(e,t,"read from private field"),r?r.call(e):t.get(e)),Xe=(e,t,r)=>t.has(e)?ii("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,r),qe=(e,t,r,a)=>(eo(e,t,"write to private field"),a?a.call(e,r):t.set(e,r),r),er=(e,t,r)=>(eo(e,t,"access private method"),r);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))a(s);new MutationObserver(s=>{for(const i of s)if(i.type==="childList")for(const o of i.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&a(o)}).observe(document,{childList:!0,subtree:!0});function r(s){const i={};return s.integrity&&(i.integrity=s.integrity),s.referrerPolicy&&(i.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?i.credentials="include":s.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function a(s){if(s.ep)return;s.ep=!0;const i=r(s);fetch(s.href,i)}})();const lo=!1;var Po=Array.isArray,Bd=Array.prototype.indexOf,Ua=Array.prototype.includes,Bs=Array.from,Gd=Object.defineProperty,ta=Object.getOwnPropertyDescriptor,Bi=Object.getOwnPropertyDescriptors,Hd=Object.prototype,Ud=Array.prototype,No=Object.getPrototypeOf,li=Object.isExtensible;function is(e){return typeof e=="function"}const Wd=()=>{};function Kd(e){return e()}function co(e){for(var t=0;t<e.length;t++)e[t]()}function Gi(){var e,t,r=new Promise((a,s)=>{e=a,t=s});return{promise:r,resolve:e,reject:t}}function Hi(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const r=[];for(const a of e)if(r.push(a),r.length===t)break;return r}const wr=2,Za=4,Sa=8,Gs=1<<24,ia=16,vn=32,Aa=64,uo=128,Jr=512,xr=1024,br=2048,fn=4096,Ar=8192,Cn=16384,es=32768,Vn=65536,di=1<<17,Yd=1<<18,ts=1<<19,Ui=1<<20,yn=1<<25,Ma=65536,fo=1<<21,Lo=1<<22,ra=1<<23,Sn=Symbol("$state"),Wi=Symbol("legacy props"),Xd=Symbol(""),ma=new class extends Error{constructor(){super(...arguments);on(this,"name","StaleReactionError");on(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var Vi;const Ki=!!((Vi=globalThis.document)!=null&&Vi.contentType)&&globalThis.document.contentType.includes("xml");function Jd(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function Qd(e,t,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function Zd(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function ec(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function tc(e){throw new Error("https://svelte.dev/e/effect_orphan")}function rc(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function nc(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function ac(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function sc(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function oc(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function ic(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const lc=1,dc=2,Yi=4,cc=8,uc=16,fc=1,vc=2,Xi=4,pc=8,mc=16,hc=1,gc=2,lr=Symbol(),Ji="http://www.w3.org/1999/xhtml",Qi="http://www.w3.org/2000/svg",xc="http://www.w3.org/1998/Math/MathML",bc="@attach";function _c(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function wc(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Zi(e){return e===this.v}function yc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function el(e){return!yc(e,this.v)}let Cs=!1,kc=!1;function Cc(){Cs=!0}let dr=null;function Wa(e){dr=e}function tn(e,t=!1,r){dr={p:dr,i:!1,c:null,e:null,s:e,x:null,l:Cs&&!t?{s:null,u:null,$:[]}:null}}function rn(e){var t=dr,r=t.e;if(r!==null){t.e=null;for(var a of r)_l(a)}return t.i=!0,dr=t.p,{}}function Ss(){return!Cs||dr!==null&&dr.l===null}let ha=[];function tl(){var e=ha;ha=[],co(e)}function Mn(e){if(ha.length===0&&!ps){var t=ha;queueMicrotask(()=>{t===ha&&tl()})}ha.push(e)}function Sc(){for(;ha.length>0;)tl()}function rl(e){var t=Ke;if(t===null)return We.f|=ra,e;if((t.f&es)===0&&(t.f&Za)===0)throw e;Qn(e,t)}function Qn(e,t){for(;t!==null;){if((t.f&uo)!==0){if((t.f&es)===0)throw e;try{t.b.error(e);return}catch(r){e=r}}t=t.parent}throw e}const Mc=-7169;function Ht(e,t){e.f=e.f&Mc|t}function Oo(e){(e.f&Jr)!==0||e.deps===null?Ht(e,xr):Ht(e,fn)}function nl(e){if(e!==null)for(const t of e)(t.f&wr)===0||(t.f&Ma)===0||(t.f^=Ma,nl(t.deps))}function al(e,t,r){(e.f&br)!==0?t.add(e):(e.f&fn)!==0&&r.add(e),nl(e.deps),Ht(e,xr)}const Ts=new Set;let Be=null,vo=null,gr=null,Pr=[],Hs=null,ps=!1,Ka=null,Ec=1;var Yn,Da,ba,ja,Va,Fa,Xn,xn,qa,Or,po,mo,ho,go;const Ko=class Ko{constructor(){Xe(this,Or);on(this,"id",Ec++);on(this,"current",new Map);on(this,"previous",new Map);Xe(this,Yn,new Set);Xe(this,Da,new Set);Xe(this,ba,0);Xe(this,ja,0);Xe(this,Va,null);Xe(this,Fa,new Set);Xe(this,Xn,new Set);Xe(this,xn,new Map);on(this,"is_fork",!1);Xe(this,qa,!1)}skip_effect(t){E(this,xn).has(t)||E(this,xn).set(t,{d:[],m:[]})}unskip_effect(t){var r=E(this,xn).get(t);if(r){E(this,xn).delete(t);for(var a of r.d)Ht(a,br),kn(a);for(a of r.m)Ht(a,fn),kn(a)}}process(t){var s;Pr=[],this.apply();var r=Ka=[],a=[];for(const i of t)er(this,Or,mo).call(this,i,r,a);if(Ka=null,er(this,Or,po).call(this)){er(this,Or,ho).call(this,a),er(this,Or,ho).call(this,r);for(const[i,o]of E(this,xn))ll(i,o)}else{vo=this,Be=null;for(const i of E(this,Yn))i(this);E(this,Yn).clear(),E(this,ba)===0&&er(this,Or,go).call(this),ci(a),ci(r),E(this,Fa).clear(),E(this,Xn).clear(),vo=null,(s=E(this,Va))==null||s.resolve()}gr=null}capture(t,r){r!==lr&&!this.previous.has(t)&&this.previous.set(t,r),(t.f&ra)===0&&(this.current.set(t,t.v),gr==null||gr.set(t,t.v))}activate(){Be=this,this.apply()}deactivate(){Be===this&&(Be=null,gr=null)}flush(){var t;if(Pr.length>0)Be=this,sl();else if(E(this,ba)===0&&!this.is_fork){for(const r of E(this,Yn))r(this);E(this,Yn).clear(),er(this,Or,go).call(this),(t=E(this,Va))==null||t.resolve()}this.deactivate()}discard(){for(const t of E(this,Da))t(this);E(this,Da).clear()}increment(t){qe(this,ba,E(this,ba)+1),t&&qe(this,ja,E(this,ja)+1)}decrement(t){qe(this,ba,E(this,ba)-1),t&&qe(this,ja,E(this,ja)-1),!E(this,qa)&&(qe(this,qa,!0),Mn(()=>{qe(this,qa,!1),er(this,Or,po).call(this)?Pr.length>0&&this.flush():this.revive()}))}revive(){for(const t of E(this,Fa))E(this,Xn).delete(t),Ht(t,br),kn(t);for(const t of E(this,Xn))Ht(t,fn),kn(t);this.flush()}oncommit(t){E(this,Yn).add(t)}ondiscard(t){E(this,Da).add(t)}settled(){return(E(this,Va)??qe(this,Va,Gi())).promise}static ensure(){if(Be===null){const t=Be=new Ko;Ts.add(Be),ps||Mn(()=>{Be===t&&t.flush()})}return Be}apply(){}};Yn=new WeakMap,Da=new WeakMap,ba=new WeakMap,ja=new WeakMap,Va=new WeakMap,Fa=new WeakMap,Xn=new WeakMap,xn=new WeakMap,qa=new WeakMap,Or=new WeakSet,po=function(){return this.is_fork||E(this,ja)>0},mo=function(t,r,a){t.f^=xr;for(var s=t.first;s!==null;){var i=s.f,o=(i&(vn|Aa))!==0,l=o&&(i&xr)!==0,c=(i&Ar)!==0,v=l||E(this,xn).has(s);if(!v&&s.fn!==null){o?c||(s.f^=xr):(i&Za)!==0?r.push(s):(i&(Sa|Gs))!==0&&c?a.push(s):zs(s)&&(Xa(s),(i&ia)!==0&&(E(this,Xn).add(s),c&&Ht(s,br)));var p=s.first;if(p!==null){s=p;continue}}for(;s!==null;){var _=s.next;if(_!==null){s=_;break}s=s.parent}}},ho=function(t){for(var r=0;r<t.length;r+=1)al(t[r],E(this,Fa),E(this,Xn))},go=function(){var i;if(Ts.size>1){this.previous.clear();var t=Be,r=gr,a=!0;for(const o of Ts){if(o===this){a=!1;continue}const l=[];for(const[v,p]of this.current){if(o.current.has(v))if(a&&p!==o.current.get(v))o.current.set(v,p);else continue;l.push(v)}if(l.length===0)continue;const c=[...o.current.keys()].filter(v=>!this.current.has(v));if(c.length>0){var s=Pr;Pr=[];const v=new Set,p=new Map;for(const _ of l)ol(_,c,v,p);if(Pr.length>0){Be=o,o.apply();for(const _ of Pr)er(i=o,Or,mo).call(i,_,[],[]);o.deactivate()}Pr=s}}Be=t,gr=r}E(this,xn).clear(),Ts.delete(this)};let na=Ko;function zc(e){var t=ps;ps=!0;try{for(var r;;){if(Sc(),Pr.length===0&&(Be==null||Be.flush(),Pr.length===0))return Hs=null,r;sl()}}finally{ps=t}}function sl(){var e=null;try{for(var t=0;Pr.length>0;){var r=na.ensure();if(t++>1e3){var a,s;Ac()}r.process(Pr),aa.clear()}}finally{Pr=[],Hs=null,Ka=null}}function Ac(){try{rc()}catch(e){Qn(e,Hs)}}let ln=null;function ci(e){var t=e.length;if(t!==0){for(var r=0;r<t;){var a=e[r++];if((a.f&(Cn|Ar))===0&&zs(a)&&(ln=new Set,Xa(a),a.deps===null&&a.first===null&&a.nodes===null&&a.teardown===null&&a.ac===null&&Cl(a),(ln==null?void 0:ln.size)>0)){aa.clear();for(const s of ln){if((s.f&(Cn|Ar))!==0)continue;const i=[s];let o=s.parent;for(;o!==null;)ln.has(o)&&(ln.delete(o),i.push(o)),o=o.parent;for(let l=i.length-1;l>=0;l--){const c=i[l];(c.f&(Cn|Ar))===0&&Xa(c)}}ln.clear()}}ln=null}}function ol(e,t,r,a){if(!r.has(e)&&(r.add(e),e.reactions!==null))for(const s of e.reactions){const i=s.f;(i&wr)!==0?ol(s,t,r,a):(i&(Lo|ia))!==0&&(i&br)===0&&il(s,t,a)&&(Ht(s,br),kn(s))}}function il(e,t,r){const a=r.get(e);if(a!==void 0)return a;if(e.deps!==null)for(const s of e.deps){if(Ua.call(t,s))return!0;if((s.f&wr)!==0&&il(s,t,r))return r.set(s,!0),!0}return r.set(e,!1),!1}function kn(e){var t=Hs=e,r=t.b;if(r!=null&&r.is_pending&&(e.f&(Za|Sa|Gs))!==0&&(e.f&es)===0){r.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var a=t.f;if(Ka!==null&&t===Ke&&(e.f&Sa)===0)return;if((a&(Aa|vn))!==0){if((a&xr)===0)return;t.f^=xr}}Pr.push(t)}function ll(e,t){if(!((e.f&vn)!==0&&(e.f&xr)!==0)){(e.f&br)!==0?t.d.push(e):(e.f&fn)!==0&&t.m.push(e),Ht(e,xr);for(var r=e.first;r!==null;)ll(r,t),r=r.next}}function Tc(e){let t=0,r=sa(0),a;return()=>{Vo()&&(n(r),qo(()=>(t===0&&(a=Ea(()=>e(()=>hs(r)))),t+=1,()=>{Mn(()=>{t-=1,t===0&&(a==null||a(),a=void 0,hs(r))})})))}}var $c=Vn|ts;function Ic(e,t,r,a){new Pc(e,t,r,a)}var Yr,Io,bn,_a,Ir,_n,Fr,dn,Ln,wa,Jn,Ba,Ga,Ha,On,Fs,rr,Nc,Lc,Oc,xo,Ls,Os,bo;class Pc{constructor(t,r,a,s){Xe(this,rr);on(this,"parent");on(this,"is_pending",!1);on(this,"transform_error");Xe(this,Yr);Xe(this,Io,null);Xe(this,bn);Xe(this,_a);Xe(this,Ir);Xe(this,_n,null);Xe(this,Fr,null);Xe(this,dn,null);Xe(this,Ln,null);Xe(this,wa,0);Xe(this,Jn,0);Xe(this,Ba,!1);Xe(this,Ga,new Set);Xe(this,Ha,new Set);Xe(this,On,null);Xe(this,Fs,Tc(()=>(qe(this,On,sa(E(this,wa))),()=>{qe(this,On,null)})));var i;qe(this,Yr,t),qe(this,bn,r),qe(this,_a,o=>{var l=Ke;l.b=this,l.f|=uo,a(o)}),this.parent=Ke.b,this.transform_error=s??((i=this.parent)==null?void 0:i.transform_error)??(o=>o),qe(this,Ir,rs(()=>{er(this,rr,xo).call(this)},$c))}defer_effect(t){al(t,E(this,Ga),E(this,Ha))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!E(this,bn).pending}update_pending_count(t){er(this,rr,bo).call(this,t),qe(this,wa,E(this,wa)+t),!(!E(this,On)||E(this,Ba))&&(qe(this,Ba,!0),Mn(()=>{qe(this,Ba,!1),E(this,On)&&Ya(E(this,On),E(this,wa))}))}get_effect_pending(){return E(this,Fs).call(this),n(E(this,On))}error(t){var r=E(this,bn).onerror;let a=E(this,bn).failed;if(!r&&!a)throw t;E(this,_n)&&(_r(E(this,_n)),qe(this,_n,null)),E(this,Fr)&&(_r(E(this,Fr)),qe(this,Fr,null)),E(this,dn)&&(_r(E(this,dn)),qe(this,dn,null));var s=!1,i=!1;const o=()=>{if(s){wc();return}s=!0,i&&ic(),E(this,dn)!==null&&ka(E(this,dn),()=>{qe(this,dn,null)}),er(this,rr,Os).call(this,()=>{na.ensure(),er(this,rr,xo).call(this)})},l=c=>{try{i=!0,r==null||r(c,o),i=!1}catch(v){Qn(v,E(this,Ir)&&E(this,Ir).parent)}a&&qe(this,dn,er(this,rr,Os).call(this,()=>{na.ensure();try{return Lr(()=>{var v=Ke;v.b=this,v.f|=uo,a(E(this,Yr),()=>c,()=>o)})}catch(v){return Qn(v,E(this,Ir).parent),null}}))};Mn(()=>{var c;try{c=this.transform_error(t)}catch(v){Qn(v,E(this,Ir)&&E(this,Ir).parent);return}c!==null&&typeof c=="object"&&typeof c.then=="function"?c.then(l,v=>Qn(v,E(this,Ir)&&E(this,Ir).parent)):l(c)})}}Yr=new WeakMap,Io=new WeakMap,bn=new WeakMap,_a=new WeakMap,Ir=new WeakMap,_n=new WeakMap,Fr=new WeakMap,dn=new WeakMap,Ln=new WeakMap,wa=new WeakMap,Jn=new WeakMap,Ba=new WeakMap,Ga=new WeakMap,Ha=new WeakMap,On=new WeakMap,Fs=new WeakMap,rr=new WeakSet,Nc=function(){try{qe(this,_n,Lr(()=>E(this,_a).call(this,E(this,Yr))))}catch(t){this.error(t)}},Lc=function(t){const r=E(this,bn).failed;r&&qe(this,dn,Lr(()=>{r(E(this,Yr),()=>t,()=>()=>{})}))},Oc=function(){const t=E(this,bn).pending;t&&(this.is_pending=!0,qe(this,Fr,Lr(()=>t(E(this,Yr)))),Mn(()=>{var r=qe(this,Ln,document.createDocumentFragment()),a=En();r.append(a),qe(this,_n,er(this,rr,Os).call(this,()=>(na.ensure(),Lr(()=>E(this,_a).call(this,a))))),E(this,Jn)===0&&(E(this,Yr).before(r),qe(this,Ln,null),ka(E(this,Fr),()=>{qe(this,Fr,null)}),er(this,rr,Ls).call(this))}))},xo=function(){try{if(this.is_pending=this.has_pending_snippet(),qe(this,Jn,0),qe(this,wa,0),qe(this,_n,Lr(()=>{E(this,_a).call(this,E(this,Yr))})),E(this,Jn)>0){var t=qe(this,Ln,document.createDocumentFragment());Ho(E(this,_n),t);const r=E(this,bn).pending;qe(this,Fr,Lr(()=>r(E(this,Yr))))}else er(this,rr,Ls).call(this)}catch(r){this.error(r)}},Ls=function(){this.is_pending=!1;for(const t of E(this,Ga))Ht(t,br),kn(t);for(const t of E(this,Ha))Ht(t,fn),kn(t);E(this,Ga).clear(),E(this,Ha).clear()},Os=function(t){var r=Ke,a=We,s=dr;en(E(this,Ir)),Zr(E(this,Ir)),Wa(E(this,Ir).ctx);try{return t()}catch(i){return rl(i),null}finally{en(r),Zr(a),Wa(s)}},bo=function(t){var r;if(!this.has_pending_snippet()){this.parent&&er(r=this.parent,rr,bo).call(r,t);return}qe(this,Jn,E(this,Jn)+t),E(this,Jn)===0&&(er(this,rr,Ls).call(this),E(this,Fr)&&ka(E(this,Fr),()=>{qe(this,Fr,null)}),E(this,Ln)&&(E(this,Yr).before(E(this,Ln)),qe(this,Ln,null)))};function dl(e,t,r,a){const s=Ss()?Ms:Ro;var i=e.filter(_=>!_.settled);if(r.length===0&&i.length===0){a(t.map(s));return}var o=Ke,l=Rc(),c=i.length===1?i[0].promise:i.length>1?Promise.all(i.map(_=>_.promise)):null;function v(_){l();try{a(_)}catch(w){(o.f&Cn)===0&&Qn(w,o)}_o()}if(r.length===0){c.then(()=>v(t.map(s)));return}function p(){l(),Promise.all(r.map(_=>jc(_))).then(_=>v([...t.map(s),..._])).catch(_=>Qn(_,o))}c?c.then(p):p()}function Rc(){var e=Ke,t=We,r=dr,a=Be;return function(i=!0){en(e),Zr(t),Wa(r),i&&(a==null||a.activate())}}function _o(e=!0){en(null),Zr(null),Wa(null),e&&(Be==null||Be.deactivate())}function Dc(){var e=Ke.b,t=Be,r=e.is_rendered();return e.update_pending_count(1),t.increment(r),()=>{e.update_pending_count(-1),t.decrement(r)}}function Ms(e){var t=wr|br,r=We!==null&&(We.f&wr)!==0?We:null;return Ke!==null&&(Ke.f|=ts),{ctx:dr,deps:null,effects:null,equals:Zi,f:t,fn:e,reactions:null,rv:0,v:lr,wv:0,parent:r??Ke,ac:null}}function jc(e,t,r){Ke===null&&Jd();var s=void 0,i=sa(lr),o=!We,l=new Map;return Zc(()=>{var w;var c=Gi();s=c.promise;try{Promise.resolve(e()).then(c.resolve,c.reject).finally(_o)}catch($){c.reject($),_o()}var v=Be;if(o){var p=Dc();(w=l.get(v))==null||w.reject(ma),l.delete(v),l.set(v,c)}const _=($,C=void 0)=>{if(v.activate(),C)C!==ma&&(i.f|=ra,Ya(i,C));else{(i.f&ra)!==0&&(i.f^=ra),Ya(i,$);for(const[P,y]of l){if(l.delete(P),P===v)break;y.reject(ma)}}p&&p()};c.promise.then(_,$=>_(null,$||"unknown"))}),Ws(()=>{for(const c of l.values())c.reject(ma)}),new Promise(c=>{function v(p){function _(){p===s?c(i):v(s)}p.then(_,_)}v(s)})}function G(e){const t=Ms(e);return El(t),t}function Ro(e){const t=Ms(e);return t.equals=el,t}function Vc(e){var t=e.effects;if(t!==null){e.effects=null;for(var r=0;r<t.length;r+=1)_r(t[r])}}function Fc(e){for(var t=e.parent;t!==null;){if((t.f&wr)===0)return(t.f&Cn)===0?t:null;t=t.parent}return null}function Do(e){var t,r=Ke;en(Fc(e));try{e.f&=~Ma,Vc(e),t=$l(e)}finally{en(r)}return t}function cl(e){var t=Do(e);if(!e.equals(t)&&(e.wv=Al(),(!(Be!=null&&Be.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){Ht(e,xr);return}oa||(gr!==null?(Vo()||Be!=null&&Be.is_fork)&&gr.set(e,t):Oo(e))}function qc(e){var t,r;if(e.effects!==null)for(const a of e.effects)(a.teardown||a.ac)&&((t=a.teardown)==null||t.call(a),(r=a.ac)==null||r.abort(ma),a.teardown=Wd,a.ac=null,ws(a,0),Bo(a))}function ul(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&Xa(t)}let wo=new Set;const aa=new Map;let fl=!1;function sa(e,t){var r={f:0,v:e,reactions:null,equals:Zi,rv:0,wv:0};return r}function U(e,t){const r=sa(e);return El(r),r}function Bc(e,t=!1,r=!0){var s;const a=sa(e);return t||(a.equals=el),Cs&&r&&dr!==null&&dr.l!==null&&((s=dr.l).s??(s.s=[])).push(a),a}function u(e,t,r=!1){We!==null&&(!un||(We.f&di)!==0)&&Ss()&&(We.f&(wr|ia|Lo|di))!==0&&(Qr===null||!Ua.call(Qr,e))&&oc();let a=r?St(t):t;return Ya(e,a)}function Ya(e,t){if(!e.equals(t)){var r=e.v;oa?aa.set(e,t):aa.set(e,r),e.v=t;var a=na.ensure();if(a.capture(e,r),(e.f&wr)!==0){const s=e;(e.f&br)!==0&&Do(s),Oo(s)}e.wv=Al(),vl(e,br),Ss()&&Ke!==null&&(Ke.f&xr)!==0&&(Ke.f&(vn|Aa))===0&&(Kr===null?tu([e]):Kr.push(e)),!a.is_fork&&wo.size>0&&!fl&&Gc()}return t}function Gc(){fl=!1;for(const e of wo)(e.f&xr)!==0&&Ht(e,fn),zs(e)&&Xa(e);wo.clear()}function ms(e,t=1){var r=n(e),a=t===1?r++:r--;return u(e,r),a}function hs(e){u(e,e.v+1)}function vl(e,t){var r=e.reactions;if(r!==null)for(var a=Ss(),s=r.length,i=0;i<s;i++){var o=r[i],l=o.f;if(!(!a&&o===Ke)){var c=(l&br)===0;if(c&&Ht(o,t),(l&wr)!==0){var v=o;gr==null||gr.delete(v),(l&Ma)===0&&(l&Jr&&(o.f|=Ma),vl(v,fn))}else c&&((l&ia)!==0&&ln!==null&&ln.add(o),kn(o))}}}function St(e){if(typeof e!="object"||e===null||Sn in e)return e;const t=No(e);if(t!==Hd&&t!==Ud)return e;var r=new Map,a=Po(e),s=U(0),i=Ca,o=l=>{if(Ca===i)return l();var c=We,v=Ca;Zr(null),pi(i);var p=l();return Zr(c),pi(v),p};return a&&r.set("length",U(e.length)),new Proxy(e,{defineProperty(l,c,v){(!("value"in v)||v.configurable===!1||v.enumerable===!1||v.writable===!1)&&ac();var p=r.get(c);return p===void 0?o(()=>{var _=U(v.value);return r.set(c,_),_}):u(p,v.value,!0),!0},deleteProperty(l,c){var v=r.get(c);if(v===void 0){if(c in l){const p=o(()=>U(lr));r.set(c,p),hs(s)}}else u(v,lr),hs(s);return!0},get(l,c,v){var $;if(c===Sn)return e;var p=r.get(c),_=c in l;if(p===void 0&&(!_||($=ta(l,c))!=null&&$.writable)&&(p=o(()=>{var C=St(_?l[c]:lr),P=U(C);return P}),r.set(c,p)),p!==void 0){var w=n(p);return w===lr?void 0:w}return Reflect.get(l,c,v)},getOwnPropertyDescriptor(l,c){var v=Reflect.getOwnPropertyDescriptor(l,c);if(v&&"value"in v){var p=r.get(c);p&&(v.value=n(p))}else if(v===void 0){var _=r.get(c),w=_==null?void 0:_.v;if(_!==void 0&&w!==lr)return{enumerable:!0,configurable:!0,value:w,writable:!0}}return v},has(l,c){var w;if(c===Sn)return!0;var v=r.get(c),p=v!==void 0&&v.v!==lr||Reflect.has(l,c);if(v!==void 0||Ke!==null&&(!p||(w=ta(l,c))!=null&&w.writable)){v===void 0&&(v=o(()=>{var $=p?St(l[c]):lr,C=U($);return C}),r.set(c,v));var _=n(v);if(_===lr)return!1}return p},set(l,c,v,p){var H;var _=r.get(c),w=c in l;if(a&&c==="length")for(var $=v;$<_.v;$+=1){var C=r.get($+"");C!==void 0?u(C,lr):$ in l&&(C=o(()=>U(lr)),r.set($+"",C))}if(_===void 0)(!w||(H=ta(l,c))!=null&&H.writable)&&(_=o(()=>U(void 0)),u(_,St(v)),r.set(c,_));else{w=_.v!==lr;var P=o(()=>St(v));u(_,P)}var y=Reflect.getOwnPropertyDescriptor(l,c);if(y!=null&&y.set&&y.set.call(p,v),!w){if(a&&typeof c=="string"){var x=r.get("length"),T=Number(c);Number.isInteger(T)&&T>=x.v&&u(x,T+1)}hs(s)}return!0},ownKeys(l){n(s);var c=Reflect.ownKeys(l).filter(_=>{var w=r.get(_);return w===void 0||w.v!==lr});for(var[v,p]of r)p.v!==lr&&!(v in l)&&c.push(v);return c},setPrototypeOf(){sc()}})}function ui(e){try{if(e!==null&&typeof e=="object"&&Sn in e)return e[Sn]}catch{}return e}function Hc(e,t){return Object.is(ui(e),ui(t))}var yo,pl,ml,hl;function Uc(){if(yo===void 0){yo=window,pl=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,r=Text.prototype;ml=ta(t,"firstChild").get,hl=ta(t,"nextSibling").get,li(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),li(r)&&(r.__t=void 0)}}function En(e=""){return document.createTextNode(e)}function Dn(e){return ml.call(e)}function Es(e){return hl.call(e)}function d(e,t){return Dn(e)}function Q(e,t=!1){{var r=Dn(e);return r instanceof Comment&&r.data===""?Es(r):r}}function m(e,t=1,r=!1){let a=e;for(;t--;)a=Es(a);return a}function Wc(e){e.textContent=""}function gl(){return!1}function jo(e,t,r){return document.createElementNS(t??Ji,e,void 0)}function xl(e,t){if(t){const r=document.body;e.autofocus=!0,Mn(()=>{document.activeElement===r&&e.focus()})}}let fi=!1;function Kc(){fi||(fi=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const r of e.target.elements)(t=r.__on_r)==null||t.call(r)})},{capture:!0}))}function Us(e){var t=We,r=Ke;Zr(null),en(null);try{return e()}finally{Zr(t),en(r)}}function Yc(e,t,r,a=r){e.addEventListener(t,()=>Us(r));const s=e.__on_r;s?e.__on_r=()=>{s(),a(!0)}:e.__on_r=()=>a(!0),Kc()}function bl(e){Ke===null&&(We===null&&tc(),ec()),oa&&Zd()}function Xc(e,t){var r=t.last;r===null?t.last=t.first=e:(r.next=e,e.prev=r,t.last=e)}function pn(e,t){var r=Ke;r!==null&&(r.f&Ar)!==0&&(e|=Ar);var a={ctx:dr,deps:null,nodes:null,f:e|br|Jr,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},s=a;if((e&Za)!==0)Ka!==null?Ka.push(a):kn(a);else if(t!==null){try{Xa(a)}catch(o){throw _r(a),o}s.deps===null&&s.teardown===null&&s.nodes===null&&s.first===s.last&&(s.f&ts)===0&&(s=s.first,(e&ia)!==0&&(e&Vn)!==0&&s!==null&&(s.f|=Vn))}if(s!==null&&(s.parent=r,r!==null&&Xc(s,r),We!==null&&(We.f&wr)!==0&&(e&Aa)===0)){var i=We;(i.effects??(i.effects=[])).push(s)}return a}function Vo(){return We!==null&&!un}function Ws(e){const t=pn(Sa,null);return Ht(t,xr),t.teardown=e,t}function Zn(e){bl();var t=Ke.f,r=!We&&(t&vn)!==0&&(t&es)===0;if(r){var a=dr;(a.e??(a.e=[])).push(e)}else return _l(e)}function _l(e){return pn(Za|Ui,e)}function Jc(e){return bl(),pn(Sa|Ui,e)}function Qc(e){na.ensure();const t=pn(Aa|ts,e);return(r={})=>new Promise(a=>{r.outro?ka(t,()=>{_r(t),a(void 0)}):(_r(t),a(void 0))})}function Fo(e){return pn(Za,e)}function Zc(e){return pn(Lo|ts,e)}function qo(e,t=0){return pn(Sa|t,e)}function L(e,t=[],r=[],a=[]){dl(a,t,r,s=>{pn(Sa,()=>e(...s.map(n)))})}function rs(e,t=0){var r=pn(ia|t,e);return r}function wl(e,t=0){var r=pn(Gs|t,e);return r}function Lr(e){return pn(vn|ts,e)}function yl(e){var t=e.teardown;if(t!==null){const r=oa,a=We;vi(!0),Zr(null);try{t.call(null)}finally{vi(r),Zr(a)}}}function Bo(e,t=!1){var r=e.first;for(e.first=e.last=null;r!==null;){const s=r.ac;s!==null&&Us(()=>{s.abort(ma)});var a=r.next;(r.f&Aa)!==0?r.parent=null:_r(r,t),r=a}}function eu(e){for(var t=e.first;t!==null;){var r=t.next;(t.f&vn)===0&&_r(t),t=r}}function _r(e,t=!0){var r=!1;(t||(e.f&Yd)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(kl(e.nodes.start,e.nodes.end),r=!0),Bo(e,t&&!r),ws(e,0),Ht(e,Cn);var a=e.nodes&&e.nodes.t;if(a!==null)for(const i of a)i.stop();yl(e);var s=e.parent;s!==null&&s.first!==null&&Cl(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function kl(e,t){for(;e!==null;){var r=e===t?null:Es(e);e.remove(),e=r}}function Cl(e){var t=e.parent,r=e.prev,a=e.next;r!==null&&(r.next=a),a!==null&&(a.prev=r),t!==null&&(t.first===e&&(t.first=a),t.last===e&&(t.last=r))}function ka(e,t,r=!0){var a=[];Sl(e,a,!0);var s=()=>{r&&_r(e),t&&t()},i=a.length;if(i>0){var o=()=>--i||s();for(var l of a)l.out(o)}else s()}function Sl(e,t,r){if((e.f&Ar)===0){e.f^=Ar;var a=e.nodes&&e.nodes.t;if(a!==null)for(const l of a)(l.is_global||r)&&t.push(l);for(var s=e.first;s!==null;){var i=s.next,o=(s.f&Vn)!==0||(s.f&vn)!==0&&(e.f&ia)!==0;Sl(s,t,o?r:!1),s=i}}}function Go(e){Ml(e,!0)}function Ml(e,t){if((e.f&Ar)!==0){e.f^=Ar;for(var r=e.first;r!==null;){var a=r.next,s=(r.f&Vn)!==0||(r.f&vn)!==0;Ml(r,s?t:!1),r=a}var i=e.nodes&&e.nodes.t;if(i!==null)for(const o of i)(o.is_global||t)&&o.in()}}function Ho(e,t){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end;r!==null;){var s=r===a?null:Es(r);t.append(r),r=s}}let Rs=!1,oa=!1;function vi(e){oa=e}let We=null,un=!1;function Zr(e){We=e}let Ke=null;function en(e){Ke=e}let Qr=null;function El(e){We!==null&&(Qr===null?Qr=[e]:Qr.push(e))}let Nr=null,Vr=0,Kr=null;function tu(e){Kr=e}let zl=1,ga=0,Ca=ga;function pi(e){Ca=e}function Al(){return++zl}function zs(e){var t=e.f;if((t&br)!==0)return!0;if(t&wr&&(e.f&=~Ma),(t&fn)!==0){for(var r=e.deps,a=r.length,s=0;s<a;s++){var i=r[s];if(zs(i)&&cl(i),i.wv>e.wv)return!0}(t&Jr)!==0&&gr===null&&Ht(e,xr)}return!1}function Tl(e,t,r=!0){var a=e.reactions;if(a!==null&&!(Qr!==null&&Ua.call(Qr,e)))for(var s=0;s<a.length;s++){var i=a[s];(i.f&wr)!==0?Tl(i,t,!1):t===i&&(r?Ht(i,br):(i.f&xr)!==0&&Ht(i,fn),kn(i))}}function $l(e){var P;var t=Nr,r=Vr,a=Kr,s=We,i=Qr,o=dr,l=un,c=Ca,v=e.f;Nr=null,Vr=0,Kr=null,We=(v&(vn|Aa))===0?e:null,Qr=null,Wa(e.ctx),un=!1,Ca=++ga,e.ac!==null&&(Us(()=>{e.ac.abort(ma)}),e.ac=null);try{e.f|=fo;var p=e.fn,_=p();e.f|=es;var w=e.deps,$=Be==null?void 0:Be.is_fork;if(Nr!==null){var C;if($||ws(e,Vr),w!==null&&Vr>0)for(w.length=Vr+Nr.length,C=0;C<Nr.length;C++)w[Vr+C]=Nr[C];else e.deps=w=Nr;if(Vo()&&(e.f&Jr)!==0)for(C=Vr;C<w.length;C++)((P=w[C]).reactions??(P.reactions=[])).push(e)}else!$&&w!==null&&Vr<w.length&&(ws(e,Vr),w.length=Vr);if(Ss()&&Kr!==null&&!un&&w!==null&&(e.f&(wr|fn|br))===0)for(C=0;C<Kr.length;C++)Tl(Kr[C],e);if(s!==null&&s!==e){if(ga++,s.deps!==null)for(let y=0;y<r;y+=1)s.deps[y].rv=ga;if(t!==null)for(const y of t)y.rv=ga;Kr!==null&&(a===null?a=Kr:a.push(...Kr))}return(e.f&ra)!==0&&(e.f^=ra),_}catch(y){return rl(y)}finally{e.f^=fo,Nr=t,Vr=r,Kr=a,We=s,Qr=i,Wa(o),un=l,Ca=c}}function ru(e,t){let r=t.reactions;if(r!==null){var a=Bd.call(r,e);if(a!==-1){var s=r.length-1;s===0?r=t.reactions=null:(r[a]=r[s],r.pop())}}if(r===null&&(t.f&wr)!==0&&(Nr===null||!Ua.call(Nr,t))){var i=t;(i.f&Jr)!==0&&(i.f^=Jr,i.f&=~Ma),Oo(i),qc(i),ws(i,0)}}function ws(e,t){var r=e.deps;if(r!==null)for(var a=t;a<r.length;a++)ru(e,r[a])}function Xa(e){var t=e.f;if((t&Cn)===0){Ht(e,xr);var r=Ke,a=Rs;Ke=e,Rs=!0;try{(t&(ia|Gs))!==0?eu(e):Bo(e),yl(e);var s=$l(e);e.teardown=typeof s=="function"?s:null,e.wv=zl;var i;lo&&kc&&(e.f&br)!==0&&e.deps}finally{Rs=a,Ke=r}}}async function nu(){await Promise.resolve(),zc()}function n(e){var t=e.f,r=(t&wr)!==0;if(We!==null&&!un){var a=Ke!==null&&(Ke.f&Cn)!==0;if(!a&&(Qr===null||!Ua.call(Qr,e))){var s=We.deps;if((We.f&fo)!==0)e.rv<ga&&(e.rv=ga,Nr===null&&s!==null&&s[Vr]===e?Vr++:Nr===null?Nr=[e]:Nr.push(e));else{(We.deps??(We.deps=[])).push(e);var i=e.reactions;i===null?e.reactions=[We]:Ua.call(i,We)||i.push(We)}}}if(oa&&aa.has(e))return aa.get(e);if(r){var o=e;if(oa){var l=o.v;return((o.f&xr)===0&&o.reactions!==null||Pl(o))&&(l=Do(o)),aa.set(o,l),l}var c=(o.f&Jr)===0&&!un&&We!==null&&(Rs||(We.f&Jr)!==0),v=(o.f&es)===0;zs(o)&&(c&&(o.f|=Jr),cl(o)),c&&!v&&(ul(o),Il(o))}if(gr!=null&&gr.has(e))return gr.get(e);if((e.f&ra)!==0)throw e.v;return e.v}function Il(e){if(e.f|=Jr,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&wr)!==0&&(t.f&Jr)===0&&(ul(t),Il(t))}function Pl(e){if(e.v===lr)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(aa.has(t)||(t.f&wr)!==0&&Pl(t))return!0;return!1}function Ea(e){var t=un;try{return un=!0,e()}finally{un=t}}function pa(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(Sn in e)ko(e);else if(!Array.isArray(e))for(let t in e){const r=e[t];typeof r=="object"&&r&&Sn in r&&ko(r)}}}function ko(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let a in e)try{ko(e[a],t)}catch{}const r=No(e);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const a=Bi(r);for(let s in a){const i=a[s].get;if(i)try{i.call(e)}catch{}}}}}function au(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const su=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function ou(e){return su.includes(e)}const iu={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function lu(e){return e=e.toLowerCase(),iu[e]??e}const du=["touchstart","touchmove"];function cu(e){return du.includes(e)}const xa=Symbol("events"),Nl=new Set,Co=new Set;function Ll(e,t,r,a={}){function s(i){if(a.capture||So.call(t,i),!i.cancelBubble)return Us(()=>r==null?void 0:r.call(this,i))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Mn(()=>{t.addEventListener(e,s,a)}):t.addEventListener(e,s,a),s}function Ra(e,t,r,a,s){var i={capture:a,passive:s},o=Ll(e,t,r,i);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&Ws(()=>{t.removeEventListener(e,o,i)})}function oe(e,t,r){(t[xa]??(t[xa]={}))[e]=r}function la(e){for(var t=0;t<e.length;t++)Nl.add(e[t]);for(var r of Co)r(e)}let mi=null;function So(e){var y,x;var t=this,r=t.ownerDocument,a=e.type,s=((y=e.composedPath)==null?void 0:y.call(e))||[],i=s[0]||e.target;mi=e;var o=0,l=mi===e&&e[xa];if(l){var c=s.indexOf(l);if(c!==-1&&(t===document||t===window)){e[xa]=t;return}var v=s.indexOf(t);if(v===-1)return;c<=v&&(o=c)}if(i=s[o]||e.target,i!==t){Gd(e,"currentTarget",{configurable:!0,get(){return i||r}});var p=We,_=Ke;Zr(null),en(null);try{for(var w,$=[];i!==null;){var C=i.assignedSlot||i.parentNode||i.host||null;try{var P=(x=i[xa])==null?void 0:x[a];P!=null&&(!i.disabled||e.target===i)&&P.call(i,e)}catch(T){w?$.push(T):w=T}if(e.cancelBubble||C===t||C===null)break;i=C}if(w){for(let T of $)queueMicrotask(()=>{throw T});throw w}}finally{e[xa]=t,delete e.currentTarget,Zr(p),en(_)}}}var Fi;const to=((Fi=globalThis==null?void 0:globalThis.window)==null?void 0:Fi.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function uu(e){return(to==null?void 0:to.createHTML(e))??e}function Ol(e){var t=jo("template");return t.innerHTML=uu(e.replaceAll("<!>","<!---->")),t.content}function za(e,t){var r=Ke;r.nodes===null&&(r.nodes={start:e,end:t,a:null,t:null})}function h(e,t){var r=(t&hc)!==0,a=(t&gc)!==0,s,i=!e.startsWith("<!>");return()=>{s===void 0&&(s=Ol(i?e:"<!>"+e),r||(s=Dn(s)));var o=a||pl?document.importNode(s,!0):s.cloneNode(!0);if(r){var l=Dn(o),c=o.lastChild;za(l,c)}else za(o,o);return o}}function fu(e,t,r="svg"){var a=!e.startsWith("<!>"),s=`<${r}>${a?e:"<!>"+e}</${r}>`,i;return()=>{if(!i){var o=Ol(s),l=Dn(o);i=Dn(l)}var c=i.cloneNode(!0);return za(c,c),c}}function vu(e,t){return fu(e,t,"svg")}function gs(e=""){{var t=En(e+"");return za(t,t),t}}function be(){var e=document.createDocumentFragment(),t=document.createComment(""),r=En();return e.append(t,r),za(t,r),e}function f(e,t){e!==null&&e.before(t)}function N(e,t){var r=t==null?"":typeof t=="object"?`${t}`:t;r!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=r,e.nodeValue=`${r}`)}function pu(e,t){return mu(e,t)}const $s=new Map;function mu(e,{target:t,anchor:r,props:a={},events:s,context:i,intro:o=!0,transformError:l}){Uc();var c=void 0,v=Qc(()=>{var p=r??t.appendChild(En());Ic(p,{pending:()=>{}},$=>{tn({});var C=dr;i&&(C.c=i),s&&(a.$$events=s),c=e($,a)||{},rn()},l);var _=new Set,w=$=>{for(var C=0;C<$.length;C++){var P=$[C];if(!_.has(P)){_.add(P);var y=cu(P);for(const H of[t,document]){var x=$s.get(H);x===void 0&&(x=new Map,$s.set(H,x));var T=x.get(P);T===void 0?(H.addEventListener(P,So,{passive:y}),x.set(P,1)):x.set(P,T+1)}}}};return w(Bs(Nl)),Co.add(w),()=>{var y;for(var $ of _)for(const x of[t,document]){var C=$s.get(x),P=C.get($);--P==0?(x.removeEventListener($,So),C.delete($),C.size===0&&$s.delete(x)):C.set($,P)}Co.delete(w),p!==r&&((y=p.parentNode)==null||y.removeChild(p))}});return hu.set(c,v),c}let hu=new WeakMap;var cn,wn,qr,ya,ys,ks,qs;class Ks{constructor(t,r=!0){on(this,"anchor");Xe(this,cn,new Map);Xe(this,wn,new Map);Xe(this,qr,new Map);Xe(this,ya,new Set);Xe(this,ys,!0);Xe(this,ks,t=>{if(E(this,cn).has(t)){var r=E(this,cn).get(t),a=E(this,wn).get(r);if(a)Go(a),E(this,ya).delete(r);else{var s=E(this,qr).get(r);s&&(s.effect.f&Ar)===0&&(E(this,wn).set(r,s.effect),E(this,qr).delete(r),s.fragment.lastChild.remove(),this.anchor.before(s.fragment),a=s.effect)}for(const[i,o]of E(this,cn)){if(E(this,cn).delete(i),i===t)break;const l=E(this,qr).get(o);l&&(_r(l.effect),E(this,qr).delete(o))}for(const[i,o]of E(this,wn)){if(i===r||E(this,ya).has(i)||(o.f&Ar)!==0)continue;const l=()=>{if(Array.from(E(this,cn).values()).includes(i)){var v=document.createDocumentFragment();Ho(o,v),v.append(En()),E(this,qr).set(i,{effect:o,fragment:v})}else _r(o);E(this,ya).delete(i),E(this,wn).delete(i)};E(this,ys)||!a?(E(this,ya).add(i),ka(o,l,!1)):l()}}});Xe(this,qs,t=>{E(this,cn).delete(t);const r=Array.from(E(this,cn).values());for(const[a,s]of E(this,qr))r.includes(a)||(_r(s.effect),E(this,qr).delete(a))});this.anchor=t,qe(this,ys,r)}ensure(t,r){var a=Be,s=gl();if(r&&!E(this,wn).has(t)&&!E(this,qr).has(t))if(s){var i=document.createDocumentFragment(),o=En();i.append(o),E(this,qr).set(t,{effect:Lr(()=>r(o)),fragment:i})}else E(this,wn).set(t,Lr(()=>r(this.anchor)));if(E(this,cn).set(a,t),s){for(const[l,c]of E(this,wn))l===t?a.unskip_effect(c):a.skip_effect(c);for(const[l,c]of E(this,qr))l===t?a.unskip_effect(c.effect):a.skip_effect(c.effect);a.oncommit(E(this,ks)),a.ondiscard(E(this,qs))}else E(this,ks).call(this,a)}}cn=new WeakMap,wn=new WeakMap,qr=new WeakMap,ya=new WeakMap,ys=new WeakMap,ks=new WeakMap,qs=new WeakMap;function z(e,t,r=!1){var a=new Ks(e),s=r?Vn:0;function i(o,l){a.ensure(o,l)}rs(()=>{var o=!1;t((l,c=0)=>{o=!0,i(c,l)}),o||i(-1,null)},s)}function Te(e,t){return t}function gu(e,t,r){for(var a=[],s=t.length,i,o=t.length,l=0;l<s;l++){let _=t[l];ka(_,()=>{if(i){if(i.pending.delete(_),i.done.add(_),i.pending.size===0){var w=e.outrogroups;Mo(e,Bs(i.done)),w.delete(i),w.size===0&&(e.outrogroups=null)}}else o-=1},!1)}if(o===0){var c=a.length===0&&r!==null;if(c){var v=r,p=v.parentNode;Wc(p),p.append(v),e.items.clear()}Mo(e,t,!c)}else i={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(i)}function Mo(e,t,r=!0){var a;if(e.pending.size>0){a=new Set;for(const o of e.pending.values())for(const l of o)a.add(e.items.get(l).e)}for(var s=0;s<t.length;s++){var i=t[s];if(a!=null&&a.has(i)){i.f|=yn;const o=document.createDocumentFragment();Ho(i,o)}else _r(t[s],r)}}var hi;function $e(e,t,r,a,s,i=null){var o=e,l=new Map,c=(t&Yi)!==0;if(c){var v=e;o=v.appendChild(En())}var p=null,_=Ro(()=>{var H=r();return Po(H)?H:H==null?[]:Bs(H)}),w,$=new Map,C=!0;function P(H){(T.effect.f&Cn)===0&&(T.pending.delete(H),T.fallback=p,xu(T,w,o,t,a),p!==null&&(w.length===0?(p.f&yn)===0?Go(p):(p.f^=yn,vs(p,null,o)):ka(p,()=>{p=null})))}function y(H){T.pending.delete(H)}var x=rs(()=>{w=n(_);for(var H=w.length,M=new Set,q=Be,ce=gl(),ne=0;ne<H;ne+=1){var k=w[ne],X=a(k,ne),ee=C?null:l.get(X);ee?(ee.v&&Ya(ee.v,k),ee.i&&Ya(ee.i,ne),ce&&q.unskip_effect(ee.e)):(ee=bu(l,C?o:hi??(hi=En()),k,X,ne,s,t,r),C||(ee.e.f|=yn),l.set(X,ee)),M.add(X)}if(H===0&&i&&!p&&(C?p=Lr(()=>i(o)):(p=Lr(()=>i(hi??(hi=En()))),p.f|=yn)),H>M.size&&Qd(),!C)if($.set(q,M),ce){for(const[Z,O]of l)M.has(Z)||q.skip_effect(O.e);q.oncommit(P),q.ondiscard(y)}else P(q);n(_)}),T={effect:x,items:l,pending:$,outrogroups:null,fallback:p};C=!1}function ls(e){for(;e!==null&&(e.f&vn)===0;)e=e.next;return e}function xu(e,t,r,a,s){var ee,Z,O,ue,te,we,ke,Ie,ge;var i=(a&cc)!==0,o=t.length,l=e.items,c=ls(e.effect.first),v,p=null,_,w=[],$=[],C,P,y,x;if(i)for(x=0;x<o;x+=1)C=t[x],P=s(C,x),y=l.get(P).e,(y.f&yn)===0&&((Z=(ee=y.nodes)==null?void 0:ee.a)==null||Z.measure(),(_??(_=new Set)).add(y));for(x=0;x<o;x+=1){if(C=t[x],P=s(C,x),y=l.get(P).e,e.outrogroups!==null)for(const xe of e.outrogroups)xe.pending.delete(y),xe.done.delete(y);if((y.f&yn)!==0)if(y.f^=yn,y===c)vs(y,null,r);else{var T=p?p.next:c;y===e.effect.last&&(e.effect.last=y.prev),y.prev&&(y.prev.next=y.next),y.next&&(y.next.prev=y.prev),Un(e,p,y),Un(e,y,T),vs(y,T,r),p=y,w=[],$=[],c=ls(p.next);continue}if((y.f&Ar)!==0&&(Go(y),i&&((ue=(O=y.nodes)==null?void 0:O.a)==null||ue.unfix(),(_??(_=new Set)).delete(y))),y!==c){if(v!==void 0&&v.has(y)){if(w.length<$.length){var H=$[0],M;p=H.prev;var q=w[0],ce=w[w.length-1];for(M=0;M<w.length;M+=1)vs(w[M],H,r);for(M=0;M<$.length;M+=1)v.delete($[M]);Un(e,q.prev,ce.next),Un(e,p,q),Un(e,ce,H),c=H,p=ce,x-=1,w=[],$=[]}else v.delete(y),vs(y,c,r),Un(e,y.prev,y.next),Un(e,y,p===null?e.effect.first:p.next),Un(e,p,y),p=y;continue}for(w=[],$=[];c!==null&&c!==y;)(v??(v=new Set)).add(c),$.push(c),c=ls(c.next);if(c===null)continue}(y.f&yn)===0&&w.push(y),p=y,c=ls(y.next)}if(e.outrogroups!==null){for(const xe of e.outrogroups)xe.pending.size===0&&(Mo(e,Bs(xe.done)),(te=e.outrogroups)==null||te.delete(xe));e.outrogroups.size===0&&(e.outrogroups=null)}if(c!==null||v!==void 0){var ne=[];if(v!==void 0)for(y of v)(y.f&Ar)===0&&ne.push(y);for(;c!==null;)(c.f&Ar)===0&&c!==e.fallback&&ne.push(c),c=ls(c.next);var k=ne.length;if(k>0){var X=(a&Yi)!==0&&o===0?r:null;if(i){for(x=0;x<k;x+=1)(ke=(we=ne[x].nodes)==null?void 0:we.a)==null||ke.measure();for(x=0;x<k;x+=1)(ge=(Ie=ne[x].nodes)==null?void 0:Ie.a)==null||ge.fix()}gu(e,ne,X)}}i&&Mn(()=>{var xe,F;if(_!==void 0)for(y of _)(F=(xe=y.nodes)==null?void 0:xe.a)==null||F.apply()})}function bu(e,t,r,a,s,i,o,l){var c=(o&lc)!==0?(o&uc)===0?Bc(r,!1,!1):sa(r):null,v=(o&dc)!==0?sa(s):null;return{v:c,i:v,e:Lr(()=>(i(t,c??r,v??s,l),()=>{e.delete(a)}))}}function vs(e,t,r){if(e.nodes)for(var a=e.nodes.start,s=e.nodes.end,i=t&&(t.f&yn)===0?t.nodes.start:r;a!==null;){var o=Es(a);if(i.before(a),a===s)return;a=o}}function Un(e,t,r){t===null?e.effect.first=r:t.next=r,r===null?e.effect.last=t:r.prev=t}function ea(e,t,r=!1,a=!1,s=!1){var i=e,o="";L(()=>{var l=Ke;if(o!==(o=t()??"")&&(l.nodes!==null&&(kl(l.nodes.start,l.nodes.end),l.nodes=null),o!=="")){var c=r?Qi:a?xc:void 0,v=jo(r?"svg":a?"math":"template",c);v.innerHTML=o;var p=r||a?v:v.content;if(za(Dn(p),p.lastChild),r||a)for(;Dn(p);)i.before(Dn(p));else i.before(p)}})}function De(e,t,r,a,s){var l;var i=(l=t.$$slots)==null?void 0:l[r],o=!1;i===!0&&(i=t.children,o=!0),i===void 0||i(e,o?()=>a:a)}function Eo(e,t,...r){var a=new Ks(e);rs(()=>{const s=t()??null;a.ensure(s,s&&(i=>s(i,...r)))},Vn)}function _u(e,t,r){var a=new Ks(e);rs(()=>{var s=t()??null;a.ensure(s,s&&(i=>r(i,s)))},Vn)}function wu(e,t,r,a,s,i){var o=null,l=e,c=new Ks(l,!1);rs(()=>{const v=t()||null;var p=Qi;if(v===null){c.ensure(null,null);return}return c.ensure(v,_=>{if(v){if(o=jo(v,p),za(o,o),a){var w=o.appendChild(En());a(o,w)}Ke.nodes.end=o,_.before(o)}}),()=>{}},Vn),Ws(()=>{})}function yu(e,t){var r=void 0,a;wl(()=>{r!==(r=t())&&(a&&(_r(a),a=null),r&&(a=Lr(()=>{Fo(()=>r(e))})))})}function Rl(e){var t,r,a="";if(typeof e=="string"||typeof e=="number")a+=e;else if(typeof e=="object")if(Array.isArray(e)){var s=e.length;for(t=0;t<s;t++)e[t]&&(r=Rl(e[t]))&&(a&&(a+=" "),a+=r)}else for(r in e)e[r]&&(a&&(a+=" "),a+=r);return a}function Dl(){for(var e,t,r=0,a="",s=arguments.length;r<s;r++)(e=arguments[r])&&(t=Rl(e))&&(a&&(a+=" "),a+=t);return a}function Mt(e){return typeof e=="object"?Dl(e):e??""}const gi=[...` 	
\r\f \v\uFEFF`];function ku(e,t,r){var a=e==null?"":""+e;if(t&&(a=a?a+" "+t:t),r){for(var s of Object.keys(r))if(r[s])a=a?a+" "+s:s;else if(a.length)for(var i=s.length,o=0;(o=a.indexOf(s,o))>=0;){var l=o+i;(o===0||gi.includes(a[o-1]))&&(l===a.length||gi.includes(a[l]))?a=(o===0?"":a.substring(0,o))+a.substring(l+1):o=l}}return a===""?null:a}function xi(e,t=!1){var r=t?" !important;":";",a="";for(var s of Object.keys(e)){var i=e[s];i!=null&&i!==""&&(a+=" "+s+": "+i+r)}return a}function ro(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Cu(e,t){if(t){var r="",a,s;if(Array.isArray(t)?(a=t[0],s=t[1]):a=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var i=!1,o=0,l=!1,c=[];a&&c.push(...Object.keys(a).map(ro)),s&&c.push(...Object.keys(s).map(ro));var v=0,p=-1;const P=e.length;for(var _=0;_<P;_++){var w=e[_];if(l?w==="/"&&e[_-1]==="*"&&(l=!1):i?i===w&&(i=!1):w==="/"&&e[_+1]==="*"?l=!0:w==='"'||w==="'"?i=w:w==="("?o++:w===")"&&o--,!l&&i===!1&&o===0){if(w===":"&&p===-1)p=_;else if(w===";"||_===P-1){if(p!==-1){var $=ro(e.substring(v,p).trim());if(!c.includes($)){w!==";"&&_++;var C=e.substring(v,_).trim();r+=" "+C+";"}}v=_+1,p=-1}}}}return a&&(r+=xi(a)),s&&(r+=xi(s,!0)),r=r.trim(),r===""?null:r}return e==null?null:String(e)}function Ne(e,t,r,a,s,i){var o=e.__className;if(o!==r||o===void 0){var l=ku(r,a,i);l==null?e.removeAttribute("class"):t?e.className=l:e.setAttribute("class",l),e.__className=r}else if(i&&s!==i)for(var c in i){var v=!!i[c];(s==null||v!==!!s[c])&&e.classList.toggle(c,v)}return i}function no(e,t={},r,a){for(var s in r){var i=r[s];t[s]!==i&&(r[s]==null?e.style.removeProperty(s):e.style.setProperty(s,i,a))}}function zo(e,t,r,a){var s=e.__style;if(s!==t){var i=Cu(t,a);i==null?e.removeAttribute("style"):e.style.cssText=i,e.__style=t}else a&&(Array.isArray(a)?(no(e,r==null?void 0:r[0],a[0]),no(e,r==null?void 0:r[1],a[1],"important")):no(e,r,a));return a}function Ao(e,t,r=!1){if(e.multiple){if(t==null)return;if(!Po(t))return _c();for(var a of e.options)a.selected=t.includes(bi(a));return}for(a of e.options){var s=bi(a);if(Hc(s,t)){a.selected=!0;return}}(!r||t!==void 0)&&(e.selectedIndex=-1)}function Su(e){var t=new MutationObserver(()=>{Ao(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Ws(()=>{t.disconnect()})}function bi(e){return"__value"in e?e.__value:e.value}const ds=Symbol("class"),cs=Symbol("style"),jl=Symbol("is custom element"),Vl=Symbol("is html"),Mu=Ki?"option":"OPTION",Eu=Ki?"select":"SELECT";function zu(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function jn(e,t,r,a){var s=Fl(e);s[t]!==(s[t]=r)&&(t==="loading"&&(e[Xd]=r),r==null?e.removeAttribute(t):typeof r!="string"&&ql(e).includes(t)?e[t]=r:e.setAttribute(t,r))}function Au(e,t,r,a,s=!1,i=!1){var o=Fl(e),l=o[jl],c=!o[Vl],v=t||{},p=e.nodeName===Mu;for(var _ in t)_ in r||(r[_]=null);r.class?r.class=Mt(r.class):r[ds]&&(r.class=null),r[cs]&&(r.style??(r.style=null));var w=ql(e);for(const M in r){let q=r[M];if(p&&M==="value"&&q==null){e.value=e.__value="",v[M]=q;continue}if(M==="class"){var $=e.namespaceURI==="http://www.w3.org/1999/xhtml";Ne(e,$,q,a,t==null?void 0:t[ds],r[ds]),v[M]=q,v[ds]=r[ds];continue}if(M==="style"){zo(e,q,t==null?void 0:t[cs],r[cs]),v[M]=q,v[cs]=r[cs];continue}var C=v[M];if(!(q===C&&!(q===void 0&&e.hasAttribute(M)))){v[M]=q;var P=M[0]+M[1];if(P!=="$$")if(P==="on"){const ce={},ne="$$"+M;let k=M.slice(2);var y=ou(k);if(au(k)&&(k=k.slice(0,-7),ce.capture=!0),!y&&C){if(q!=null)continue;e.removeEventListener(k,v[ne],ce),v[ne]=null}if(y)oe(k,e,q),la([k]);else if(q!=null){let X=function(ee){v[M].call(this,ee)};var H=X;v[ne]=Ll(k,e,X,ce)}}else if(M==="style")jn(e,M,q);else if(M==="autofocus")xl(e,!!q);else if(!l&&(M==="__value"||M==="value"&&q!=null))e.value=e.__value=q;else if(M==="selected"&&p)zu(e,q);else{var x=M;c||(x=lu(x));var T=x==="defaultValue"||x==="defaultChecked";if(q==null&&!l&&!T)if(o[M]=null,x==="value"||x==="checked"){let ce=e;const ne=t===void 0;if(x==="value"){let k=ce.defaultValue;ce.removeAttribute(x),ce.defaultValue=k,ce.value=ce.__value=ne?k:null}else{let k=ce.defaultChecked;ce.removeAttribute(x),ce.defaultChecked=k,ce.checked=ne?k:!1}}else e.removeAttribute(M);else T||w.includes(x)&&(l||typeof q!="string")?(e[x]=q,x in o&&(o[x]=lr)):typeof q!="function"&&jn(e,x,q)}}}return v}function Ds(e,t,r=[],a=[],s=[],i,o=!1,l=!1){dl(s,r,a,c=>{var v=void 0,p={},_=e.nodeName===Eu,w=!1;if(wl(()=>{var C=t(...c.map(n)),P=Au(e,v,C,i,o,l);w&&_&&"value"in C&&Ao(e,C.value);for(let x of Object.getOwnPropertySymbols(p))C[x]||_r(p[x]);for(let x of Object.getOwnPropertySymbols(C)){var y=C[x];x.description===bc&&(!v||y!==v[x])&&(p[x]&&_r(p[x]),p[x]=Lr(()=>yu(e,()=>y))),P[x]=y}v=P}),_){var $=e;Fo(()=>{Ao($,v.value,!0),Su($)})}w=!0})}function Fl(e){return e.__attributes??(e.__attributes={[jl]:e.nodeName.includes("-"),[Vl]:e.namespaceURI===Ji})}var _i=new Map;function ql(e){var t=e.getAttribute("is")||e.nodeName,r=_i.get(t);if(r)return r;_i.set(t,r=[]);for(var a,s=e,i=Element.prototype;i!==s;){a=Bi(s);for(var o in a)a[o].set&&r.push(o);s=No(s)}return r}function Oa(e,t,r=t){var a=new WeakSet;Yc(e,"input",async s=>{var i=s?e.defaultValue:e.value;if(i=ao(e)?so(i):i,r(i),Be!==null&&a.add(Be),await nu(),i!==(i=t())){var o=e.selectionStart,l=e.selectionEnd,c=e.value.length;if(e.value=i??"",l!==null){var v=e.value.length;o===l&&l===c&&v>c?(e.selectionStart=v,e.selectionEnd=v):(e.selectionStart=o,e.selectionEnd=Math.min(l,v))}}}),Ea(t)==null&&e.value&&(r(ao(e)?so(e.value):e.value),Be!==null&&a.add(Be)),qo(()=>{var s=t();if(e===document.activeElement){var i=vo??Be;if(a.has(i))return}ao(e)&&s===so(e.value)||e.type==="date"&&!s&&!e.value||s!==e.value&&(e.value=s??"")})}function ao(e){var t=e.type;return t==="number"||t==="range"}function so(e){return e===""?null:+e}function wi(e,t){return e===t||(e==null?void 0:e[Sn])===t}function Ja(e={},t,r,a){return Fo(()=>{var s,i;return qo(()=>{s=i,i=[],Ea(()=>{e!==r(...i)&&(t(e,...i),s&&wi(r(...s),e)&&t(null,...s))})}),()=>{Mn(()=>{i&&wi(r(...i),e)&&t(null,...i)})}}),e}function Tu(e=!1){const t=dr,r=t.l.u;if(!r)return;let a=()=>pa(t.s);if(e){let s=0,i={};const o=Ms(()=>{let l=!1;const c=t.s;for(const v in c)c[v]!==i[v]&&(i[v]=c[v],l=!0);return l&&s++,s});a=()=>n(o)}r.b.length&&Jc(()=>{yi(t,a),co(r.b)}),Zn(()=>{const s=Ea(()=>r.m.map(Kd));return()=>{for(const i of s)typeof i=="function"&&i()}}),r.a.length&&Zn(()=>{yi(t,a),co(r.a)})}function yi(e,t){if(e.l.s)for(const r of e.l.s)n(r);t()}let Is=!1;function $u(e){var t=Is;try{return Is=!1,[e(),Is]}finally{Is=t}}const Iu={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Pu(e,t,r){return new Proxy({props:e,exclude:t},Iu)}const Nu={get(e,t){if(!e.exclude.includes(t))return n(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,r){if(!(t in e.special)){var a=Ke;try{en(e.parent_effect),e.special[t]=at({get[t](){return e.props[t]}},t,Xi)}finally{en(a)}}return e.special[t](r),ms(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),ms(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Le(e,t){return new Proxy({props:e,exclude:t,special:{},version:sa(0),parent_effect:Ke},Nu)}const Lu={get(e,t){let r=e.props.length;for(;r--;){let a=e.props[r];if(is(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a)return a[t]}},set(e,t,r){let a=e.props.length;for(;a--;){let s=e.props[a];is(s)&&(s=s());const i=ta(s,t);if(i&&i.set)return i.set(r),!0}return!1},getOwnPropertyDescriptor(e,t){let r=e.props.length;for(;r--;){let a=e.props[r];if(is(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a){const s=ta(a,t);return s&&!s.configurable&&(s.configurable=!0),s}}},has(e,t){if(t===Sn||t===Wi)return!1;for(let r of e.props)if(is(r)&&(r=r()),r!=null&&t in r)return!0;return!1},ownKeys(e){const t=[];for(let r of e.props)if(is(r)&&(r=r()),!!r){for(const a in r)t.includes(a)||t.push(a);for(const a of Object.getOwnPropertySymbols(r))t.includes(a)||t.push(a)}return t}};function Ge(...e){return new Proxy({props:e},Lu)}function at(e,t,r,a){var H;var s=!Cs||(r&vc)!==0,i=(r&pc)!==0,o=(r&mc)!==0,l=a,c=!0,v=()=>(c&&(c=!1,l=o?Ea(a):a),l),p;if(i){var _=Sn in e||Wi in e;p=((H=ta(e,t))==null?void 0:H.set)??(_&&t in e?M=>e[t]=M:void 0)}var w,$=!1;i?[w,$]=$u(()=>e[t]):w=e[t],w===void 0&&a!==void 0&&(w=v(),p&&(s&&nc(),p(w)));var C;if(s?C=()=>{var M=e[t];return M===void 0?v():(c=!0,M)}:C=()=>{var M=e[t];return M!==void 0&&(l=void 0),M===void 0?l:M},s&&(r&Xi)===0)return C;if(p){var P=e.$$legacy;return(function(M,q){return arguments.length>0?((!s||!q||P||$)&&p(q?C():M),M):C()})}var y=!1,x=((r&fc)!==0?Ms:Ro)(()=>(y=!1,C()));i&&n(x);var T=Ke;return(function(M,q){if(arguments.length>0){const ce=q?n(x):s&&i?St(M):M;return u(x,ce),y=!0,l!==void 0&&(l=ce),M}return oa&&y||(T.f&Cn)!==0?x.v:n(x)})}const Ou="5";var qi;typeof window<"u"&&((qi=window.__svelte??(window.__svelte={})).v??(qi.v=new Set)).add(Ou);const nn="";async function Ru(){const e=await fetch(`${nn}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function Na(e,t=null,r=null){const a={provider:e};t&&(a.model=t),r&&(a.api_key=r);const s=await fetch(`${nn}/api/configure`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!s.ok)throw new Error("설정 실패");return s.json()}async function Du(e){const t=await fetch(`${nn}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function ju(e,{onProgress:t,onDone:r,onError:a}){const s=new AbortController;return fetch(`${nn}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:s.signal}).then(async i=>{if(!i.ok){a==null||a("다운로드 실패");return}const o=i.body.getReader(),l=new TextDecoder;let c="";for(;;){const{done:v,value:p}=await o.read();if(v)break;c+=l.decode(p,{stream:!0});const _=c.split(`
`);c=_.pop()||"";for(const w of _)if(w.startsWith("data:"))try{const $=JSON.parse(w.slice(5).trim());$.total&&$.completed!==void 0?t==null||t({total:$.total,completed:$.completed,status:$.status}):$.status&&(t==null||t({status:$.status}))}catch{}}r==null||r()}).catch(i=>{i.name!=="AbortError"&&(a==null||a(i.message))}),{abort:()=>s.abort()}}async function Vu(){const e=await fetch(`${nn}/api/oauth/authorize`);if(!e.ok)throw new Error("OAuth 인증 시작 실패");return e.json()}async function Fu(){const e=await fetch(`${nn}/api/oauth/status`);return e.ok?e.json():{done:!1}}async function qu(){const e=await fetch(`${nn}/api/oauth/logout`,{method:"POST"});if(!e.ok)throw new Error("로그아웃 실패");return e.json()}async function Bu(e,t=null,r=null){let a=`${nn}/api/export/excel/${encodeURIComponent(e)}`;const s=new URLSearchParams;r?s.set("template_id",r):t&&t.length>0&&s.set("modules",t.join(","));const i=s.toString();i&&(a+=`?${i}`);const o=await fetch(a);if(!o.ok){const w=await o.json().catch(()=>({}));throw new Error(w.detail||"Excel 다운로드 실패")}const l=await o.blob(),v=(o.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),p=v?decodeURIComponent(v[1]):`${e}.xlsx`,_=document.createElement("a");return _.href=URL.createObjectURL(l),_.download=p,_.click(),URL.revokeObjectURL(_.href),p}async function Bl(e){const t=await fetch(`${nn}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}async function Gu(e,t){const r=await fetch(`${nn}/api/company/${e}/show/${encodeURIComponent(t)}/all`);if(!r.ok)throw new Error("company topic 일괄 조회 실패");return r.json()}async function Hu(e){const t=await fetch(`${nn}/api/company/${e}/sections`);if(!t.ok)throw new Error("sections 조회 실패");return t.json()}function Uu(e,t,r={},{onMeta:a,onSnapshot:s,onContext:i,onSystemPrompt:o,onToolCall:l,onToolResult:c,onChunk:v,onDone:p,onError:_},w=null){const $={question:t,stream:!0,...r};e&&($.company=e),w&&w.length>0&&($.history=w);const C=new AbortController;return fetch(`${nn}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify($),signal:C.signal}).then(async P=>{if(!P.ok){const q=await P.json().catch(()=>({}));_==null||_(q.detail||"스트리밍 실패");return}const y=P.body.getReader(),x=new TextDecoder;let T="",H=!1,M=null;for(;;){const{done:q,value:ce}=await y.read();if(q)break;T+=x.decode(ce,{stream:!0});const ne=T.split(`
`);T=ne.pop()||"";for(const k of ne)if(k.startsWith("event:"))M=k.slice(6).trim();else if(k.startsWith("data:")&&M){const X=k.slice(5).trim();try{const ee=JSON.parse(X);M==="meta"?a==null||a(ee):M==="snapshot"?s==null||s(ee):M==="context"?i==null||i(ee):M==="system_prompt"?o==null||o(ee):M==="tool_call"?l==null||l(ee):M==="tool_result"?c==null||c(ee):M==="chunk"?v==null||v(ee.text):M==="error"?_==null||_(ee.error,ee.action,ee.detail):M==="done"&&(H||(H=!0,p==null||p()))}catch{}M=null}}H||(H=!0,p==null||p())}).catch(P=>{P.name!=="AbortError"&&(_==null||_(P.message))}),{abort:()=>C.abort()}}const Wu=(e,t)=>{const r=new Array(e.length+t.length);for(let a=0;a<e.length;a++)r[a]=e[a];for(let a=0;a<t.length;a++)r[e.length+a]=t[a];return r},Ku=(e,t)=>({classGroupId:e,validator:t}),Gl=(e=new Map,t=null,r)=>({nextPart:e,validators:t,classGroupId:r}),js="-",ki=[],Yu="arbitrary..",Xu=e=>{const t=Qu(e),{conflictingClassGroups:r,conflictingClassGroupModifiers:a}=e;return{getClassGroupId:o=>{if(o.startsWith("[")&&o.endsWith("]"))return Ju(o);const l=o.split(js),c=l[0]===""&&l.length>1?1:0;return Hl(l,c,t)},getConflictingClassGroupIds:(o,l)=>{if(l){const c=a[o],v=r[o];return c?v?Wu(v,c):c:v||ki}return r[o]||ki}}},Hl=(e,t,r)=>{if(e.length-t===0)return r.classGroupId;const s=e[t],i=r.nextPart.get(s);if(i){const v=Hl(e,t+1,i);if(v)return v}const o=r.validators;if(o===null)return;const l=t===0?e.join(js):e.slice(t).join(js),c=o.length;for(let v=0;v<c;v++){const p=o[v];if(p.validator(l))return p.classGroupId}},Ju=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),r=t.indexOf(":"),a=t.slice(0,r);return a?Yu+a:void 0})(),Qu=e=>{const{theme:t,classGroups:r}=e;return Zu(r,t)},Zu=(e,t)=>{const r=Gl();for(const a in e){const s=e[a];Uo(s,r,a,t)}return r},Uo=(e,t,r,a)=>{const s=e.length;for(let i=0;i<s;i++){const o=e[i];ef(o,t,r,a)}},ef=(e,t,r,a)=>{if(typeof e=="string"){tf(e,t,r);return}if(typeof e=="function"){rf(e,t,r,a);return}nf(e,t,r,a)},tf=(e,t,r)=>{const a=e===""?t:Ul(t,e);a.classGroupId=r},rf=(e,t,r,a)=>{if(af(e)){Uo(e(a),t,r,a);return}t.validators===null&&(t.validators=[]),t.validators.push(Ku(r,e))},nf=(e,t,r,a)=>{const s=Object.entries(e),i=s.length;for(let o=0;o<i;o++){const[l,c]=s[o];Uo(c,Ul(t,l),r,a)}},Ul=(e,t)=>{let r=e;const a=t.split(js),s=a.length;for(let i=0;i<s;i++){const o=a[i];let l=r.nextPart.get(o);l||(l=Gl(),r.nextPart.set(o,l)),r=l}return r},af=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,sf=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,r=Object.create(null),a=Object.create(null);const s=(i,o)=>{r[i]=o,t++,t>e&&(t=0,a=r,r=Object.create(null))};return{get(i){let o=r[i];if(o!==void 0)return o;if((o=a[i])!==void 0)return s(i,o),o},set(i,o){i in r?r[i]=o:s(i,o)}}},To="!",Ci=":",of=[],Si=(e,t,r,a,s)=>({modifiers:e,hasImportantModifier:t,baseClassName:r,maybePostfixModifierPosition:a,isExternal:s}),lf=e=>{const{prefix:t,experimentalParseClassName:r}=e;let a=s=>{const i=[];let o=0,l=0,c=0,v;const p=s.length;for(let P=0;P<p;P++){const y=s[P];if(o===0&&l===0){if(y===Ci){i.push(s.slice(c,P)),c=P+1;continue}if(y==="/"){v=P;continue}}y==="["?o++:y==="]"?o--:y==="("?l++:y===")"&&l--}const _=i.length===0?s:s.slice(c);let w=_,$=!1;_.endsWith(To)?(w=_.slice(0,-1),$=!0):_.startsWith(To)&&(w=_.slice(1),$=!0);const C=v&&v>c?v-c:void 0;return Si(i,$,w,C)};if(t){const s=t+Ci,i=a;a=o=>o.startsWith(s)?i(o.slice(s.length)):Si(of,!1,o,void 0,!0)}if(r){const s=a;a=i=>r({className:i,parseClassName:s})}return a},df=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((r,a)=>{t.set(r,1e6+a)}),r=>{const a=[];let s=[];for(let i=0;i<r.length;i++){const o=r[i],l=o[0]==="[",c=t.has(o);l||c?(s.length>0&&(s.sort(),a.push(...s),s=[]),a.push(o)):s.push(o)}return s.length>0&&(s.sort(),a.push(...s)),a}},cf=e=>({cache:sf(e.cacheSize),parseClassName:lf(e),sortModifiers:df(e),...Xu(e)}),uf=/\s+/,ff=(e,t)=>{const{parseClassName:r,getClassGroupId:a,getConflictingClassGroupIds:s,sortModifiers:i}=t,o=[],l=e.trim().split(uf);let c="";for(let v=l.length-1;v>=0;v-=1){const p=l[v],{isExternal:_,modifiers:w,hasImportantModifier:$,baseClassName:C,maybePostfixModifierPosition:P}=r(p);if(_){c=p+(c.length>0?" "+c:c);continue}let y=!!P,x=a(y?C.substring(0,P):C);if(!x){if(!y){c=p+(c.length>0?" "+c:c);continue}if(x=a(C),!x){c=p+(c.length>0?" "+c:c);continue}y=!1}const T=w.length===0?"":w.length===1?w[0]:i(w).join(":"),H=$?T+To:T,M=H+x;if(o.indexOf(M)>-1)continue;o.push(M);const q=s(x,y);for(let ce=0;ce<q.length;++ce){const ne=q[ce];o.push(H+ne)}c=p+(c.length>0?" "+c:c)}return c},vf=(...e)=>{let t=0,r,a,s="";for(;t<e.length;)(r=e[t++])&&(a=Wl(r))&&(s&&(s+=" "),s+=a);return s},Wl=e=>{if(typeof e=="string")return e;let t,r="";for(let a=0;a<e.length;a++)e[a]&&(t=Wl(e[a]))&&(r&&(r+=" "),r+=t);return r},pf=(e,...t)=>{let r,a,s,i;const o=c=>{const v=t.reduce((p,_)=>_(p),e());return r=cf(v),a=r.cache.get,s=r.cache.set,i=l,l(c)},l=c=>{const v=a(c);if(v)return v;const p=ff(c,r);return s(c,p),p};return i=o,(...c)=>i(vf(...c))},mf=[],tr=e=>{const t=r=>r[e]||mf;return t.isThemeGetter=!0,t},Kl=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Yl=/^\((?:(\w[\w-]*):)?(.+)\)$/i,hf=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,gf=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,xf=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,bf=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,_f=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,wf=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,Wn=e=>hf.test(e),Re=e=>!!e&&!Number.isNaN(Number(e)),Kn=e=>!!e&&Number.isInteger(Number(e)),oo=e=>e.endsWith("%")&&Re(e.slice(0,-1)),Nn=e=>gf.test(e),Xl=()=>!0,yf=e=>xf.test(e)&&!bf.test(e),Wo=()=>!1,kf=e=>_f.test(e),Cf=e=>wf.test(e),Sf=e=>!se(e)&&!le(e),Mf=e=>da(e,Zl,Wo),se=e=>Kl.test(e),va=e=>da(e,ed,yf),Mi=e=>da(e,Nf,Re),Ef=e=>da(e,rd,Xl),zf=e=>da(e,td,Wo),Ei=e=>da(e,Jl,Wo),Af=e=>da(e,Ql,Cf),Ps=e=>da(e,nd,kf),le=e=>Yl.test(e),us=e=>Ta(e,ed),Tf=e=>Ta(e,td),zi=e=>Ta(e,Jl),$f=e=>Ta(e,Zl),If=e=>Ta(e,Ql),Ns=e=>Ta(e,nd,!0),Pf=e=>Ta(e,rd,!0),da=(e,t,r)=>{const a=Kl.exec(e);return a?a[1]?t(a[1]):r(a[2]):!1},Ta=(e,t,r=!1)=>{const a=Yl.exec(e);return a?a[1]?t(a[1]):r:!1},Jl=e=>e==="position"||e==="percentage",Ql=e=>e==="image"||e==="url",Zl=e=>e==="length"||e==="size"||e==="bg-size",ed=e=>e==="length",Nf=e=>e==="number",td=e=>e==="family-name",rd=e=>e==="number"||e==="weight",nd=e=>e==="shadow",Lf=()=>{const e=tr("color"),t=tr("font"),r=tr("text"),a=tr("font-weight"),s=tr("tracking"),i=tr("leading"),o=tr("breakpoint"),l=tr("container"),c=tr("spacing"),v=tr("radius"),p=tr("shadow"),_=tr("inset-shadow"),w=tr("text-shadow"),$=tr("drop-shadow"),C=tr("blur"),P=tr("perspective"),y=tr("aspect"),x=tr("ease"),T=tr("animate"),H=()=>["auto","avoid","all","avoid-page","page","left","right","column"],M=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],q=()=>[...M(),le,se],ce=()=>["auto","hidden","clip","visible","scroll"],ne=()=>["auto","contain","none"],k=()=>[le,se,c],X=()=>[Wn,"full","auto",...k()],ee=()=>[Kn,"none","subgrid",le,se],Z=()=>["auto",{span:["full",Kn,le,se]},Kn,le,se],O=()=>[Kn,"auto",le,se],ue=()=>["auto","min","max","fr",le,se],te=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],we=()=>["start","end","center","stretch","center-safe","end-safe"],ke=()=>["auto",...k()],Ie=()=>[Wn,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...k()],ge=()=>[Wn,"screen","full","dvw","lvw","svw","min","max","fit",...k()],xe=()=>[Wn,"screen","full","lh","dvh","lvh","svh","min","max","fit",...k()],F=()=>[e,le,se],A=()=>[...M(),zi,Ei,{position:[le,se]}],D=()=>["no-repeat",{repeat:["","x","y","space","round"]}],ae=()=>["auto","cover","contain",$f,Mf,{size:[le,se]}],ie=()=>[oo,us,va],ve=()=>["","none","full",v,le,se],fe=()=>["",Re,us,va],pe=()=>["solid","dashed","dotted","double"],Ee=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],K=()=>[Re,oo,zi,Ei],qt=()=>["","none",C,le,se],ot=()=>["none",Re,le,se],nr=()=>["none",Re,le,se],Ue=()=>[Re,le,se],Pe=()=>[Wn,"full",...k()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Nn],breakpoint:[Nn],color:[Xl],container:[Nn],"drop-shadow":[Nn],ease:["in","out","in-out"],font:[Sf],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Nn],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Nn],shadow:[Nn],spacing:["px",Re],text:[Nn],"text-shadow":[Nn],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",Wn,se,le,y]}],container:["container"],columns:[{columns:[Re,se,le,l]}],"break-after":[{"break-after":H()}],"break-before":[{"break-before":H()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:q()}],overflow:[{overflow:ce()}],"overflow-x":[{"overflow-x":ce()}],"overflow-y":[{"overflow-y":ce()}],overscroll:[{overscroll:ne()}],"overscroll-x":[{"overscroll-x":ne()}],"overscroll-y":[{"overscroll-y":ne()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:X()}],"inset-x":[{"inset-x":X()}],"inset-y":[{"inset-y":X()}],start:[{"inset-s":X(),start:X()}],end:[{"inset-e":X(),end:X()}],"inset-bs":[{"inset-bs":X()}],"inset-be":[{"inset-be":X()}],top:[{top:X()}],right:[{right:X()}],bottom:[{bottom:X()}],left:[{left:X()}],visibility:["visible","invisible","collapse"],z:[{z:[Kn,"auto",le,se]}],basis:[{basis:[Wn,"full","auto",l,...k()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[Re,Wn,"auto","initial","none",se]}],grow:[{grow:["",Re,le,se]}],shrink:[{shrink:["",Re,le,se]}],order:[{order:[Kn,"first","last","none",le,se]}],"grid-cols":[{"grid-cols":ee()}],"col-start-end":[{col:Z()}],"col-start":[{"col-start":O()}],"col-end":[{"col-end":O()}],"grid-rows":[{"grid-rows":ee()}],"row-start-end":[{row:Z()}],"row-start":[{"row-start":O()}],"row-end":[{"row-end":O()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":ue()}],"auto-rows":[{"auto-rows":ue()}],gap:[{gap:k()}],"gap-x":[{"gap-x":k()}],"gap-y":[{"gap-y":k()}],"justify-content":[{justify:[...te(),"normal"]}],"justify-items":[{"justify-items":[...we(),"normal"]}],"justify-self":[{"justify-self":["auto",...we()]}],"align-content":[{content:["normal",...te()]}],"align-items":[{items:[...we(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...we(),{baseline:["","last"]}]}],"place-content":[{"place-content":te()}],"place-items":[{"place-items":[...we(),"baseline"]}],"place-self":[{"place-self":["auto",...we()]}],p:[{p:k()}],px:[{px:k()}],py:[{py:k()}],ps:[{ps:k()}],pe:[{pe:k()}],pbs:[{pbs:k()}],pbe:[{pbe:k()}],pt:[{pt:k()}],pr:[{pr:k()}],pb:[{pb:k()}],pl:[{pl:k()}],m:[{m:ke()}],mx:[{mx:ke()}],my:[{my:ke()}],ms:[{ms:ke()}],me:[{me:ke()}],mbs:[{mbs:ke()}],mbe:[{mbe:ke()}],mt:[{mt:ke()}],mr:[{mr:ke()}],mb:[{mb:ke()}],ml:[{ml:ke()}],"space-x":[{"space-x":k()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":k()}],"space-y-reverse":["space-y-reverse"],size:[{size:Ie()}],"inline-size":[{inline:["auto",...ge()]}],"min-inline-size":[{"min-inline":["auto",...ge()]}],"max-inline-size":[{"max-inline":["none",...ge()]}],"block-size":[{block:["auto",...xe()]}],"min-block-size":[{"min-block":["auto",...xe()]}],"max-block-size":[{"max-block":["none",...xe()]}],w:[{w:[l,"screen",...Ie()]}],"min-w":[{"min-w":[l,"screen","none",...Ie()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[o]},...Ie()]}],h:[{h:["screen","lh",...Ie()]}],"min-h":[{"min-h":["screen","lh","none",...Ie()]}],"max-h":[{"max-h":["screen","lh",...Ie()]}],"font-size":[{text:["base",r,us,va]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[a,Pf,Ef]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",oo,se]}],"font-family":[{font:[Tf,zf,t]}],"font-features":[{"font-features":[se]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[s,le,se]}],"line-clamp":[{"line-clamp":[Re,"none",le,Mi]}],leading:[{leading:[i,...k()]}],"list-image":[{"list-image":["none",le,se]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",le,se]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:F()}],"text-color":[{text:F()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...pe(),"wavy"]}],"text-decoration-thickness":[{decoration:[Re,"from-font","auto",le,va]}],"text-decoration-color":[{decoration:F()}],"underline-offset":[{"underline-offset":[Re,"auto",le,se]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:k()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",le,se]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",le,se]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:A()}],"bg-repeat":[{bg:D()}],"bg-size":[{bg:ae()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},Kn,le,se],radial:["",le,se],conic:[Kn,le,se]},If,Af]}],"bg-color":[{bg:F()}],"gradient-from-pos":[{from:ie()}],"gradient-via-pos":[{via:ie()}],"gradient-to-pos":[{to:ie()}],"gradient-from":[{from:F()}],"gradient-via":[{via:F()}],"gradient-to":[{to:F()}],rounded:[{rounded:ve()}],"rounded-s":[{"rounded-s":ve()}],"rounded-e":[{"rounded-e":ve()}],"rounded-t":[{"rounded-t":ve()}],"rounded-r":[{"rounded-r":ve()}],"rounded-b":[{"rounded-b":ve()}],"rounded-l":[{"rounded-l":ve()}],"rounded-ss":[{"rounded-ss":ve()}],"rounded-se":[{"rounded-se":ve()}],"rounded-ee":[{"rounded-ee":ve()}],"rounded-es":[{"rounded-es":ve()}],"rounded-tl":[{"rounded-tl":ve()}],"rounded-tr":[{"rounded-tr":ve()}],"rounded-br":[{"rounded-br":ve()}],"rounded-bl":[{"rounded-bl":ve()}],"border-w":[{border:fe()}],"border-w-x":[{"border-x":fe()}],"border-w-y":[{"border-y":fe()}],"border-w-s":[{"border-s":fe()}],"border-w-e":[{"border-e":fe()}],"border-w-bs":[{"border-bs":fe()}],"border-w-be":[{"border-be":fe()}],"border-w-t":[{"border-t":fe()}],"border-w-r":[{"border-r":fe()}],"border-w-b":[{"border-b":fe()}],"border-w-l":[{"border-l":fe()}],"divide-x":[{"divide-x":fe()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":fe()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...pe(),"hidden","none"]}],"divide-style":[{divide:[...pe(),"hidden","none"]}],"border-color":[{border:F()}],"border-color-x":[{"border-x":F()}],"border-color-y":[{"border-y":F()}],"border-color-s":[{"border-s":F()}],"border-color-e":[{"border-e":F()}],"border-color-bs":[{"border-bs":F()}],"border-color-be":[{"border-be":F()}],"border-color-t":[{"border-t":F()}],"border-color-r":[{"border-r":F()}],"border-color-b":[{"border-b":F()}],"border-color-l":[{"border-l":F()}],"divide-color":[{divide:F()}],"outline-style":[{outline:[...pe(),"none","hidden"]}],"outline-offset":[{"outline-offset":[Re,le,se]}],"outline-w":[{outline:["",Re,us,va]}],"outline-color":[{outline:F()}],shadow:[{shadow:["","none",p,Ns,Ps]}],"shadow-color":[{shadow:F()}],"inset-shadow":[{"inset-shadow":["none",_,Ns,Ps]}],"inset-shadow-color":[{"inset-shadow":F()}],"ring-w":[{ring:fe()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:F()}],"ring-offset-w":[{"ring-offset":[Re,va]}],"ring-offset-color":[{"ring-offset":F()}],"inset-ring-w":[{"inset-ring":fe()}],"inset-ring-color":[{"inset-ring":F()}],"text-shadow":[{"text-shadow":["none",w,Ns,Ps]}],"text-shadow-color":[{"text-shadow":F()}],opacity:[{opacity:[Re,le,se]}],"mix-blend":[{"mix-blend":[...Ee(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":Ee()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[Re]}],"mask-image-linear-from-pos":[{"mask-linear-from":K()}],"mask-image-linear-to-pos":[{"mask-linear-to":K()}],"mask-image-linear-from-color":[{"mask-linear-from":F()}],"mask-image-linear-to-color":[{"mask-linear-to":F()}],"mask-image-t-from-pos":[{"mask-t-from":K()}],"mask-image-t-to-pos":[{"mask-t-to":K()}],"mask-image-t-from-color":[{"mask-t-from":F()}],"mask-image-t-to-color":[{"mask-t-to":F()}],"mask-image-r-from-pos":[{"mask-r-from":K()}],"mask-image-r-to-pos":[{"mask-r-to":K()}],"mask-image-r-from-color":[{"mask-r-from":F()}],"mask-image-r-to-color":[{"mask-r-to":F()}],"mask-image-b-from-pos":[{"mask-b-from":K()}],"mask-image-b-to-pos":[{"mask-b-to":K()}],"mask-image-b-from-color":[{"mask-b-from":F()}],"mask-image-b-to-color":[{"mask-b-to":F()}],"mask-image-l-from-pos":[{"mask-l-from":K()}],"mask-image-l-to-pos":[{"mask-l-to":K()}],"mask-image-l-from-color":[{"mask-l-from":F()}],"mask-image-l-to-color":[{"mask-l-to":F()}],"mask-image-x-from-pos":[{"mask-x-from":K()}],"mask-image-x-to-pos":[{"mask-x-to":K()}],"mask-image-x-from-color":[{"mask-x-from":F()}],"mask-image-x-to-color":[{"mask-x-to":F()}],"mask-image-y-from-pos":[{"mask-y-from":K()}],"mask-image-y-to-pos":[{"mask-y-to":K()}],"mask-image-y-from-color":[{"mask-y-from":F()}],"mask-image-y-to-color":[{"mask-y-to":F()}],"mask-image-radial":[{"mask-radial":[le,se]}],"mask-image-radial-from-pos":[{"mask-radial-from":K()}],"mask-image-radial-to-pos":[{"mask-radial-to":K()}],"mask-image-radial-from-color":[{"mask-radial-from":F()}],"mask-image-radial-to-color":[{"mask-radial-to":F()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":M()}],"mask-image-conic-pos":[{"mask-conic":[Re]}],"mask-image-conic-from-pos":[{"mask-conic-from":K()}],"mask-image-conic-to-pos":[{"mask-conic-to":K()}],"mask-image-conic-from-color":[{"mask-conic-from":F()}],"mask-image-conic-to-color":[{"mask-conic-to":F()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:A()}],"mask-repeat":[{mask:D()}],"mask-size":[{mask:ae()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",le,se]}],filter:[{filter:["","none",le,se]}],blur:[{blur:qt()}],brightness:[{brightness:[Re,le,se]}],contrast:[{contrast:[Re,le,se]}],"drop-shadow":[{"drop-shadow":["","none",$,Ns,Ps]}],"drop-shadow-color":[{"drop-shadow":F()}],grayscale:[{grayscale:["",Re,le,se]}],"hue-rotate":[{"hue-rotate":[Re,le,se]}],invert:[{invert:["",Re,le,se]}],saturate:[{saturate:[Re,le,se]}],sepia:[{sepia:["",Re,le,se]}],"backdrop-filter":[{"backdrop-filter":["","none",le,se]}],"backdrop-blur":[{"backdrop-blur":qt()}],"backdrop-brightness":[{"backdrop-brightness":[Re,le,se]}],"backdrop-contrast":[{"backdrop-contrast":[Re,le,se]}],"backdrop-grayscale":[{"backdrop-grayscale":["",Re,le,se]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[Re,le,se]}],"backdrop-invert":[{"backdrop-invert":["",Re,le,se]}],"backdrop-opacity":[{"backdrop-opacity":[Re,le,se]}],"backdrop-saturate":[{"backdrop-saturate":[Re,le,se]}],"backdrop-sepia":[{"backdrop-sepia":["",Re,le,se]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":k()}],"border-spacing-x":[{"border-spacing-x":k()}],"border-spacing-y":[{"border-spacing-y":k()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",le,se]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[Re,"initial",le,se]}],ease:[{ease:["linear","initial",x,le,se]}],delay:[{delay:[Re,le,se]}],animate:[{animate:["none",T,le,se]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[P,le,se]}],"perspective-origin":[{"perspective-origin":q()}],rotate:[{rotate:ot()}],"rotate-x":[{"rotate-x":ot()}],"rotate-y":[{"rotate-y":ot()}],"rotate-z":[{"rotate-z":ot()}],scale:[{scale:nr()}],"scale-x":[{"scale-x":nr()}],"scale-y":[{"scale-y":nr()}],"scale-z":[{"scale-z":nr()}],"scale-3d":["scale-3d"],skew:[{skew:Ue()}],"skew-x":[{"skew-x":Ue()}],"skew-y":[{"skew-y":Ue()}],transform:[{transform:[le,se,"","none","gpu","cpu"]}],"transform-origin":[{origin:q()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:Pe()}],"translate-x":[{"translate-x":Pe()}],"translate-y":[{"translate-y":Pe()}],"translate-z":[{"translate-z":Pe()}],"translate-none":["translate-none"],accent:[{accent:F()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:F()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",le,se]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":k()}],"scroll-mx":[{"scroll-mx":k()}],"scroll-my":[{"scroll-my":k()}],"scroll-ms":[{"scroll-ms":k()}],"scroll-me":[{"scroll-me":k()}],"scroll-mbs":[{"scroll-mbs":k()}],"scroll-mbe":[{"scroll-mbe":k()}],"scroll-mt":[{"scroll-mt":k()}],"scroll-mr":[{"scroll-mr":k()}],"scroll-mb":[{"scroll-mb":k()}],"scroll-ml":[{"scroll-ml":k()}],"scroll-p":[{"scroll-p":k()}],"scroll-px":[{"scroll-px":k()}],"scroll-py":[{"scroll-py":k()}],"scroll-ps":[{"scroll-ps":k()}],"scroll-pe":[{"scroll-pe":k()}],"scroll-pbs":[{"scroll-pbs":k()}],"scroll-pbe":[{"scroll-pbe":k()}],"scroll-pt":[{"scroll-pt":k()}],"scroll-pr":[{"scroll-pr":k()}],"scroll-pb":[{"scroll-pb":k()}],"scroll-pl":[{"scroll-pl":k()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",le,se]}],fill:[{fill:["none",...F()]}],"stroke-w":[{stroke:[Re,us,va,Mi]}],stroke:[{stroke:["none",...F()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},Of=pf(Lf);function Et(...e){return Of(Dl(e))}const $o="dartlab-conversations",Ai=50;function Rf(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function Df(){try{const e=localStorage.getItem($o);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const jf=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function Ti(e){return e.map(t=>({...t,messages:t.messages.map(r=>{if(r.role!=="assistant")return r;const a={};for(const[s,i]of Object.entries(r))jf.includes(s)||(a[s]=i);return a})}))}function $i(e){try{const t={conversations:Ti(e.conversations),activeId:e.activeId};localStorage.setItem($o,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:Ti(e.conversations),activeId:e.activeId};localStorage.setItem($o,JSON.stringify(t))}catch{}}}}function Vf(){const e=Df(),t=e.conversations||[],r=t.find(x=>x.id===e.activeId)?e.activeId:null;let a=U(St(t)),s=U(St(r)),i=null;function o(){i&&clearTimeout(i),i=setTimeout(()=>{$i({conversations:n(a),activeId:n(s)}),i=null},300)}function l(){i&&clearTimeout(i),i=null,$i({conversations:n(a),activeId:n(s)})}function c(){return n(a).find(x=>x.id===n(s))||null}function v(){const x={id:Rf(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return u(a,[x,...n(a)],!0),n(a).length>Ai&&u(a,n(a).slice(0,Ai),!0),u(s,x.id,!0),l(),x.id}function p(x){n(a).find(T=>T.id===x)&&(u(s,x,!0),l())}function _(x,T,H=null){const M=c();if(!M)return;const q={role:x,text:T};H&&(q.meta=H),M.messages=[...M.messages,q],M.updatedAt=Date.now(),M.title==="새 대화"&&x==="user"&&(M.title=T.length>30?T.slice(0,30)+"...":T),u(a,[...n(a)],!0),l()}function w(x){const T=c();if(!T||T.messages.length===0)return;const H=T.messages[T.messages.length-1];Object.assign(H,x),T.updatedAt=Date.now(),u(a,[...n(a)],!0),o()}function $(x){u(a,n(a).filter(T=>T.id!==x),!0),n(s)===x&&u(s,n(a).length>0?n(a)[0].id:null,!0),l()}function C(){const x=c();!x||x.messages.length===0||(x.messages=x.messages.slice(0,-1),x.updatedAt=Date.now(),u(a,[...n(a)],!0),l())}function P(x,T){const H=n(a).find(M=>M.id===x);H&&(H.title=T,u(a,[...n(a)],!0),l())}function y(){u(a,[],!0),u(s,null),l()}return{get conversations(){return n(a)},get activeId(){return n(s)},get active(){return c()},createConversation:v,setActive:p,addMessage:_,updateLastMessage:w,removeLastMessage:C,deleteConversation:$,updateTitle:P,clearAll:y,flush:l}}const ad="dartlab-workspace",Ff=6;function sd(){return typeof window<"u"&&typeof localStorage<"u"}function qf(){if(!sd())return{};try{const e=localStorage.getItem(ad);return e?JSON.parse(e):{}}catch{return{}}}function Bf(e){sd()&&localStorage.setItem(ad,JSON.stringify(e))}function Gf(){const e=qf();let t=U(!1),r=U(null),a=U(null),s=U(null),i=U(null),o=U(St(e.selectedCompany||null)),l=U(St(e.recentCompanies||[]));function c(){Bf({selectedCompany:n(o),recentCompanies:n(l)})}function v(x){if(!(x!=null&&x.stockCode))return;const T={stockCode:x.stockCode,corpName:x.corpName||x.company||x.stockCode,company:x.company||x.corpName||x.stockCode,market:x.market||""};u(l,[T,...n(l).filter(H=>H.stockCode!==T.stockCode)].slice(0,Ff),!0)}function p(x){x&&(u(o,x,!0),v(x)),u(r,"viewer"),u(a,null),u(t,!0),c()}function _(x){u(r,"data"),u(a,x,!0),u(t,!0)}function w(){u(t,!1)}function $(x){u(o,x,!0),x&&v(x),c()}function C(x,T){var H,M,q,ce;!(x!=null&&x.company)&&!(x!=null&&x.stockCode)||(u(o,{...n(o)||{},...T||{},corpName:x.company||((H=n(o))==null?void 0:H.corpName)||(T==null?void 0:T.corpName)||(T==null?void 0:T.company),company:x.company||((M=n(o))==null?void 0:M.company)||(T==null?void 0:T.company)||(T==null?void 0:T.corpName),stockCode:x.stockCode||((q=n(o))==null?void 0:q.stockCode)||(T==null?void 0:T.stockCode),market:((ce=n(o))==null?void 0:ce.market)||(T==null?void 0:T.market)||""},!0),v(n(o)),c())}function P(x,T){u(s,x,!0),u(i,T||x,!0)}function y(){return n(t)?n(r)==="viewer"&&n(o)?{type:"viewer",company:n(o),topic:n(s),topicLabel:n(i)}:n(r)==="data"&&n(a)?{type:"data",data:n(a)}:null:null}return{get panelOpen(){return n(t)},get panelMode(){return n(r)},get panelData(){return n(a)},get selectedCompany(){return n(o)},get recentCompanies(){return n(l)},get viewerTopic(){return n(s)},get viewerTopicLabel(){return n(i)},openViewer:p,openData:_,closePanel:w,selectCompany:$,setViewerTopic:P,syncCompanyFromMessage:C,getViewContext:y}}var Hf=h("<a><!></a>"),Uf=h("<button><!></button>");function Wf(e,t){tn(t,!0);let r=at(t,"variant",3,"default"),a=at(t,"size",3,"default"),s=Pu(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const i={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},o={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=be(),c=Q(l);{var v=_=>{var w=Hf();Ds(w,C=>({class:C,...s}),[()=>Et("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",i[r()],o[a()],t.class)]);var $=d(w);Eo($,()=>t.children),f(_,w)},p=_=>{var w=Uf();Ds(w,C=>({class:C,...s}),[()=>Et("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",i[r()],o[a()],t.class)]);var $=d(w);Eo($,()=>t.children),f(_,w)};z(c,_=>{t.href?_(v):_(p,-1)})}f(e,l),rn()}Cc();/**
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
 */const Kf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const Yf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const Ii=(...e)=>e.filter((t,r,a)=>!!t&&t.trim()!==""&&a.indexOf(t)===r).join(" ").trim();var Xf=vu("<svg><!><!></svg>");function He(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]),a=Le(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);tn(t,!1);let s=at(t,"name",8,void 0),i=at(t,"color",8,"currentColor"),o=at(t,"size",8,24),l=at(t,"strokeWidth",8,2),c=at(t,"absoluteStrokeWidth",8,!1),v=at(t,"iconNode",24,()=>[]);Tu();var p=Xf();Ds(p,($,C,P)=>({...Kf,...$,...a,width:o(),height:o(),stroke:i(),"stroke-width":C,class:P}),[()=>Yf(a)?void 0:{"aria-hidden":"true"},()=>(pa(c()),pa(l()),pa(o()),Ea(()=>c()?Number(l())*24/Number(o()):l())),()=>(pa(Ii),pa(s()),pa(r),Ea(()=>Ii("lucide-icon","lucide",s()?`lucide-${s()}`:"",r.class)))]);var _=d(p);$e(_,1,v,Te,($,C)=>{var P=G(()=>Hi(n(C),2));let y=()=>n(P)[0],x=()=>n(P)[1];var T=be(),H=Q(T);wu(H,y,!0,(M,q)=>{Ds(M,()=>({...x()}))}),f($,T)});var w=m(_);De(w,t,"default",{}),f(e,p),rn()}function Jf(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];He(e,Ge({name:"activity"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function Qf(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];He(e,Ge({name:"arrow-up"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function Pi(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 7v14"}],["path",{d:"M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"}]];He(e,Ge({name:"book-open"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function io(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];He(e,Ge({name:"brain"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function Zf(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]];He(e,Ge({name:"chart-column"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function ev(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M20 6 9 17l-5-5"}]];He(e,Ge({name:"check"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function tv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m6 9 6 6 6-6"}]];He(e,Ge({name:"chevron-down"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function rv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m9 18 6-6-6-6"}]];He(e,Ge({name:"chevron-right"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function La(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];He(e,Ge({name:"circle-alert"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function xs(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];He(e,Ge({name:"circle-check"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function nv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];He(e,Ge({name:"clock"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function av(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];He(e,Ge({name:"code"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function sv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];He(e,Ge({name:"coffee"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function fs(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];He(e,Ge({name:"database"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function bs(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];He(e,Ge({name:"download"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function Ni(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];He(e,Ge({name:"external-link"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function ov(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];He(e,Ge({name:"eye"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function Rn(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];He(e,Ge({name:"file-text"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function iv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];He(e,Ge({name:"github"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function Li(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];He(e,Ge({name:"key"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function Xr(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];He(e,Ge({name:"loader-circle"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function lv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m10 17 5-5-5-5"}],["path",{d:"M15 12H3"}],["path",{d:"M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"}]];He(e,Ge({name:"log-in"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function dv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];He(e,Ge({name:"log-out"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function od(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"m21 3-7 7"}],["path",{d:"m3 21 7-7"}],["path",{d:"M9 21H3v-6"}]];He(e,Ge({name:"maximize-2"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function cv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];He(e,Ge({name:"menu"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function Oi(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];He(e,Ge({name:"message-square"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function id(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m14 10 7-7"}],["path",{d:"M20 10h-6V4"}],["path",{d:"m3 21 7-7"}],["path",{d:"M4 14h6v6"}]];He(e,Ge({name:"minimize-2"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function uv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];He(e,Ge({name:"panel-left-close"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function Ri(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];He(e,Ge({name:"plus"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function fv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];He(e,Ge({name:"refresh-cw"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function _s(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];He(e,Ge({name:"search"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function vv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];He(e,Ge({name:"settings"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function pv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];He(e,Ge({name:"square"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function mv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];He(e,Ge({name:"terminal"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function hv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];He(e,Ge({name:"trash-2"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function gv(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];He(e,Ge({name:"triangle-alert"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function Di(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];He(e,Ge({name:"wrench"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}function Vs(e,t){const r=Le(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];He(e,Ge({name:"x"},()=>r,{get iconNode(){return a},children:(s,i)=>{var o=be(),l=Q(o);De(l,t,"default",{}),f(s,o)},$$slots:{default:!0}}))}var xv=h("<!> 새 대화",1),bv=h('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),_v=h('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),wv=h('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),yv=h('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40"><span class="text-[10px] text-dl-text-dim font-mono"> </span></div>'),kv=h('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),Cv=h("<button><!></button>"),Sv=h('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),Mv=h("<aside><!></aside>");function Ev(e,t){tn(t,!0);let r=at(t,"conversations",19,()=>[]),a=at(t,"activeId",3,null),s=at(t,"open",3,!0),i=at(t,"version",3,""),o=U("");function l(C){const P=new Date().setHours(0,0,0,0),y=P-864e5,x=P-7*864e5,T={오늘:[],어제:[],"이번 주":[],이전:[]};for(const M of C)M.updatedAt>=P?T.오늘.push(M):M.updatedAt>=y?T.어제.push(M):M.updatedAt>=x?T["이번 주"].push(M):T.이전.push(M);const H=[];for(const[M,q]of Object.entries(T))q.length>0&&H.push({label:M,items:q});return H}let c=G(()=>n(o).trim()?r().filter(C=>C.title.toLowerCase().includes(n(o).toLowerCase())):r()),v=G(()=>l(n(c)));var p=Mv(),_=d(p);{var w=C=>{var P=kv(),y=m(d(P),2),x=d(y);Wf(x,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(ne,k)=>{var X=xv(),ee=Q(X);Ri(ee,{size:16}),f(ne,X)},$$slots:{default:!0}});var T=m(y,2);{var H=ne=>{var k=bv(),X=d(k),ee=d(X);_s(ee,{size:12,class:"text-dl-text-dim flex-shrink-0"});var Z=m(ee,2);Oa(Z,()=>n(o),O=>u(o,O)),f(ne,k)};z(T,ne=>{r().length>3&&ne(H)})}var M=m(T,2);$e(M,21,()=>n(v),Te,(ne,k)=>{var X=wv(),ee=d(X),Z=d(ee),O=m(ee,2);$e(O,17,()=>n(k).items,Te,(ue,te)=>{var we=_v(),ke=d(we),Ie=d(ke);Oi(Ie,{size:14,class:"flex-shrink-0 opacity-50"});var ge=m(Ie,2),xe=d(ge),F=m(ke,2),A=d(F);hv(A,{size:12}),L(D=>{Ne(we,1,D),jn(ke,"aria-current",n(te).id===a()?"true":void 0),N(xe,n(te).title),jn(F,"aria-label",`${n(te).title} 삭제`)},[()=>Mt(Et("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",n(te).id===a()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),oe("click",ke,()=>{var D;return(D=t.onSelect)==null?void 0:D.call(t,n(te).id)}),oe("click",F,D=>{var ae;D.stopPropagation(),(ae=t.onDelete)==null||ae.call(t,n(te).id)}),f(ue,we)}),L(()=>N(Z,n(k).label)),f(ne,X)});var q=m(M,2);{var ce=ne=>{var k=yv(),X=d(k),ee=d(X);L(()=>N(ee,`v${i()??""}`)),f(ne,k)};z(q,ne=>{i()&&ne(ce)})}f(C,P)},$=C=>{var P=Sv(),y=m(d(P),2),x=d(y);Ri(x,{size:18});var T=m(y,2);$e(T,21,()=>r().slice(0,10),Te,(H,M)=>{var q=Cv(),ce=d(q);Oi(ce,{size:16}),L(ne=>{Ne(q,1,ne),jn(q,"title",n(M).title)},[()=>Mt(Et("p-2 rounded-lg transition-colors w-full flex justify-center",n(M).id===a()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),oe("click",q,()=>{var ne;return(ne=t.onSelect)==null?void 0:ne.call(t,n(M).id)}),f(H,q)}),oe("click",y,function(...H){var M;(M=t.onNewChat)==null||M.apply(this,H)}),f(C,P)};z(_,C=>{s()?C(w):C($,-1)})}L(C=>Ne(p,1,C),[()=>Mt(Et("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",s()?"w-[260px]":"w-[52px]"))]),f(e,p),rn()}la(["click"]);var zv=h('<button class="send-btn active"><!></button>'),Av=h("<button><!></button>"),Tv=h('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),$v=h('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),Iv=h('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),Pv=h('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function ld(e,t){tn(t,!0);let r=at(t,"inputText",15,""),a=at(t,"isLoading",3,!1),s=at(t,"large",3,!1),i=at(t,"placeholder",3,"메시지를 입력하세요..."),o=U(St([])),l=U(!1),c=U(-1),v=null,p=U(void 0);function _(k){var X;if(n(l)&&n(o).length>0){if(k.key==="ArrowDown"){k.preventDefault(),u(c,(n(c)+1)%n(o).length);return}if(k.key==="ArrowUp"){k.preventDefault(),u(c,n(c)<=0?n(o).length-1:n(c)-1,!0);return}if(k.key==="Enter"&&n(c)>=0){k.preventDefault(),C(n(o)[n(c)]);return}if(k.key==="Escape"){u(l,!1),u(c,-1);return}}k.key==="Enter"&&!k.shiftKey&&(k.preventDefault(),u(l,!1),(X=t.onSend)==null||X.call(t))}function w(k){k.target.style.height="auto",k.target.style.height=Math.min(k.target.scrollHeight,200)+"px"}function $(k){w(k);const X=r();v&&clearTimeout(v),X.length>=2&&!/\s/.test(X.slice(-1))?v=setTimeout(async()=>{var ee;try{const Z=await Bl(X.trim());((ee=Z.results)==null?void 0:ee.length)>0?(u(o,Z.results.slice(0,6),!0),u(l,!0),u(c,-1)):u(l,!1)}catch{u(l,!1)}},300):u(l,!1)}function C(k){var X;r(`${k.corpName} `),u(l,!1),u(c,-1),(X=t.onCompanySelect)==null||X.call(t,k),n(p)&&n(p).focus()}function P(){setTimeout(()=>{u(l,!1)},200)}var y=Pv(),x=d(y),T=d(x);Ja(T,k=>u(p,k),()=>n(p));var H=m(T,2);{var M=k=>{var X=zv(),ee=d(X);pv(ee,{size:14}),oe("click",X,function(...Z){var O;(O=t.onStop)==null||O.apply(this,Z)}),f(k,X)},q=k=>{var X=Av(),ee=d(X);{let Z=G(()=>s()?18:16);Qf(ee,{get size(){return n(Z)},strokeWidth:2.5})}L((Z,O)=>{Ne(X,1,Z),X.disabled=O},[()=>Mt(Et("send-btn",r().trim()&&"active")),()=>!r().trim()]),oe("click",X,()=>{var Z;u(l,!1),(Z=t.onSend)==null||Z.call(t)}),f(k,X)};z(H,k=>{a()&&t.onStop?k(M):k(q,-1)})}var ce=m(x,2);{var ne=k=>{var X=Iv();$e(X,21,()=>n(o),Te,(ee,Z,O)=>{var ue=$v(),te=d(ue);_s(te,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var we=m(te,2),ke=d(we),Ie=d(ke),ge=m(ke,2),xe=d(ge),F=m(we,2);{var A=D=>{var ae=Tv(),ie=d(ae);L(()=>N(ie,n(Z).sector)),f(D,ae)};z(F,D=>{n(Z).sector&&D(A)})}L(D=>{Ne(ue,1,D),N(Ie,n(Z).corpName),N(xe,`${n(Z).stockCode??""} · ${(n(Z).market||"")??""}`)},[()=>Mt(Et("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",O===n(c)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),oe("mousedown",ue,()=>C(n(Z))),Ra("mouseenter",ue,()=>{u(c,O,!0)}),f(ee,ue)}),f(k,X)};z(ce,k=>{n(l)&&n(o).length>0&&k(ne)})}L(k=>{Ne(x,1,k),jn(T,"placeholder",i())},[()=>Mt(Et("input-box",s()&&"large"))]),oe("keydown",T,_),oe("input",T,$),Ra("blur",T,P),Oa(T,r),f(e,y),rn()}la(["keydown","input","click","mousedown"]);var Nv=h('<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[580px] flex flex-col items-center"><div class="relative mb-8"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p> <div class="w-full"><!></div></div></div>');function Lv(e,t){tn(t,!0);let r=at(t,"inputText",15,"");var a=Nv(),s=d(a),i=m(d(s),6),o=d(i);ld(o,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get onCompanySelect(){return t.onCompanySelect},get inputText(){return r()},set inputText(l){r(l)}}),f(e,a),rn()}var Ov=h("<span><!></span>");function ji(e,t){tn(t,!0);let r=at(t,"variant",3,"default");const a={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var s=Ov(),i=d(s);Eo(i,()=>t.children),L(o=>Ne(s,1,o),[()=>Mt(Et("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",a[r()],t.class))]),f(e,s),rn()}function Rv(e){const t=e.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(t)||t==="-"||t==="0"}function Qa(e){if(!e)return"";let t=[],r=[],a=e.replace(/```(\w*)\n([\s\S]*?)```/g,(i,o,l)=>{const c=t.length;return t.push(l.trimEnd()),`
%%CODE_${c}%%
`});a=a.replace(/((?:^\|.+\|$\n?)+)/gm,i=>{const o=i.trim().split(`
`).filter(w=>w.trim());let l=null,c=-1,v=[];for(let w=0;w<o.length;w++)if(o[w].slice(1,-1).split("|").map(C=>C.trim()).every(C=>/^[\-:]+$/.test(C))){c=w;break}c>0?(l=o[c-1],v=o.slice(c+1)):(c===0||(l=o[0]),v=o.slice(1));let p="<table>";if(l){const w=l.slice(1,-1).split("|").map($=>$.trim());p+="<thead><tr>"+w.map($=>`<th>${$.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(v.length>0){p+="<tbody>";for(const w of v){const $=w.slice(1,-1).split("|").map(C=>C.trim());p+="<tr>"+$.map(C=>{let P=C.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${Rv(C)?' class="num"':""}>${P}</td>`}).join("")+"</tr>"}p+="</tbody>"}p+="</table>";let _=r.length;return r.push(p),`
%%TABLE_${_}%%
`});let s=a.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");s=s.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,i=>"<ul>"+i.replace(/<br>/g,"")+"</ul>");for(let i=0;i<r.length;i++)s=s.replace(`%%TABLE_${i}%%`,r[i]);for(let i=0;i<t.length;i++){const o=t[i].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");s=s.replace(`%%CODE_${i}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${i}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${o}</code></pre></div>`)}return s=s.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(i,o)=>o.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+s+"</p>"}var Dv=h('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),jv=h('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),Vv=h('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),Fv=h('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),qv=h('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!></div></div>'),Bv=h('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),Gv=h('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),Hv=h('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),Uv=h('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),Wv=h("<button><!> </button>"),Kv=h('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),Yv=h('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),Xv=h('<!> <span class="text-dl-text-dim"> </span>',1),Jv=h('<div class="flex items-center gap-2 text-[11px]"><!></div>'),Qv=h('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),Zv=h('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),ep=h('<div class="message-committed"><!></div>'),tp=h('<div><div class="message-live-label"> </div> <pre> </pre></div>'),rp=h('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),np=h('<span class="text-dl-accent/60"> </span>'),ap=h('<span class="text-dl-success/60"> </span>'),sp=h('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),op=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),ip=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),lp=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),dp=h('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),cp=h("<!>  <div><!> <!></div> <!>",1),up=h('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),fp=h('<span class="text-[10px] text-dl-text-dim"> </span>'),vp=h('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),pp=h("<button> </button>"),mp=h('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),hp=h("<button>시스템 프롬프트</button>"),gp=h("<button>LLM 입력</button>"),xp=h('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),bp=h('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),_p=h('<span class="text-dl-text"> </span>'),wp=h('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),yp=h('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),kp=h('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Cp=h("<!> <!>",1);function Sp(e,t){tn(t,!0);let r=U(null),a=U("context"),s=U("raw"),i=G(()=>{var A,D,ae,ie,ve,fe;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((A=t.message.toolEvents)==null?void 0:A.length)>0){const pe=[...t.message.toolEvents].reverse().find(K=>K.type==="call"),Ee=((D=pe==null?void 0:pe.arguments)==null?void 0:D.module)||((ae=pe==null?void 0:pe.arguments)==null?void 0:ae.keyword)||"";return`도구 실행 중 — ${(pe==null?void 0:pe.name)||""}${Ee?` (${Ee})`:""}`}if(((ie=t.message.contexts)==null?void 0:ie.length)>0){const pe=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(pe==null?void 0:pe.label)||(pe==null?void 0:pe.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(ve=t.message.meta)!=null&&ve.company?`${t.message.meta.company} 데이터 검색 중`:(fe=t.message.meta)!=null&&fe.includedModules?"분석 모듈 선택 완료":"생각 중"}),o=G(()=>{var A;return t.message.company||((A=t.message.meta)==null?void 0:A.company)||null}),l=G(()=>{var A,D,ae;return t.message.systemPrompt||t.message.userContent||((A=t.message.contexts)==null?void 0:A.length)>0||((D=t.message.meta)==null?void 0:D.includedModules)||((ae=t.message.toolEvents)==null?void 0:ae.length)>0}),c=G(()=>{var D;const A=(D=t.message.meta)==null?void 0:D.dataYearRange;return A?typeof A=="string"?A:A.min_year&&A.max_year?`${A.min_year}~${A.max_year}년`:null:null});function v(A){if(!A)return 0;const D=(A.match(/[\uac00-\ud7af]/g)||[]).length,ae=A.length-D;return Math.round(D*1.5+ae/3.5)}function p(A){return A>=1e3?(A/1e3).toFixed(1)+"k":String(A)}let _=G(()=>{var D;let A=0;if(t.message.systemPrompt&&(A+=v(t.message.systemPrompt)),t.message.userContent)A+=v(t.message.userContent);else if(((D=t.message.contexts)==null?void 0:D.length)>0)for(const ae of t.message.contexts)A+=v(ae.text);return A}),w=G(()=>v(t.message.text)),$=U(void 0);const C=/^\s*\|.+\|\s*$/;function P(A,D){if(!A)return{committed:"",draft:"",draftType:"none"};if(!D)return{committed:A,draft:"",draftType:"none"};const ae=A.split(`
`);let ie=ae.length;A.endsWith(`
`)||(ie=Math.min(ie,ae.length-1));let ve=0,fe=-1;for(let ot=0;ot<ae.length;ot++)ae[ot].trim().startsWith("```")&&(ve+=1,fe=ot);ve%2===1&&fe>=0&&(ie=Math.min(ie,fe));let pe=-1;for(let ot=ae.length-1;ot>=0;ot--){const nr=ae[ot];if(!nr.trim())break;if(C.test(nr))pe=ot;else{pe=-1;break}}if(pe>=0&&(ie=Math.min(ie,pe)),ie<=0)return{committed:"",draft:A,draftType:pe===0?"table":ve%2===1?"code":"text"};const Ee=ae.slice(0,ie).join(`
`),K=ae.slice(ie).join(`
`);let qt="text";return K&&pe>=ie?qt="table":K&&ve%2===1&&(qt="code"),{committed:Ee,draft:K,draftType:qt}}const y='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',x='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function T(A){var ve;const D=A.target.closest(".code-copy-btn");if(!D)return;const ae=D.closest(".code-block-wrap"),ie=((ve=ae==null?void 0:ae.querySelector("code"))==null?void 0:ve.textContent)||"";navigator.clipboard.writeText(ie).then(()=>{D.innerHTML=x,setTimeout(()=>{D.innerHTML=y},2e3)})}function H(A){if(t.onOpenEvidence){t.onOpenEvidence("contexts",A);return}u(r,A,!0),u(a,"context"),u(s,"rendered")}function M(){if(t.onOpenEvidence){t.onOpenEvidence("system");return}u(r,0),u(a,"system"),u(s,"raw")}function q(){if(t.onOpenEvidence){t.onOpenEvidence("snapshot");return}u(r,0),u(a,"snapshot")}function ce(A){var D;if(t.onOpenEvidence){const ae=(D=t.message.toolEvents)==null?void 0:D[A];t.onOpenEvidence((ae==null?void 0:ae.type)==="result"?"tool-results":"tool-calls",A);return}u(r,A,!0),u(a,"tool"),u(s,"raw")}function ne(){if(t.onOpenEvidence){t.onOpenEvidence("input");return}u(r,0),u(a,"userContent"),u(s,"raw")}function k(){u(r,null)}function X(A){var D,ae,ie,ve;return A?A.type==="call"?((D=A.arguments)==null?void 0:D.module)||((ae=A.arguments)==null?void 0:ae.keyword)||((ie=A.arguments)==null?void 0:ie.engine)||((ve=A.arguments)==null?void 0:ve.name)||"":typeof A.result=="string"?A.result.slice(0,120):A.result&&typeof A.result=="object"&&(A.result.module||A.result.status||A.result.name)||"":""}let ee=G(()=>(t.message.toolEvents||[]).filter(A=>A.type==="call")),Z=G(()=>(t.message.toolEvents||[]).filter(A=>A.type==="result")),O=G(()=>P(t.message.text||"",t.message.loading)),ue=G(()=>{var D,ae,ie;const A=[];return((ae=(D=t.message.meta)==null?void 0:D.includedModules)==null?void 0:ae.length)>0&&A.push({label:`모듈 ${t.message.meta.includedModules.length}개`,icon:fs}),((ie=t.message.contexts)==null?void 0:ie.length)>0&&A.push({label:`컨텍스트 ${t.message.contexts.length}건`,icon:ov}),n(ee).length>0&&A.push({label:`툴 호출 ${n(ee).length}건`,icon:Di}),n(Z).length>0&&A.push({label:`툴 결과 ${n(Z).length}건`,icon:xs}),t.message.systemPrompt&&A.push({label:"시스템 프롬프트",icon:io}),t.message.userContent&&A.push({label:"LLM 입력",icon:Rn}),A}),te=G(()=>{var D,ae,ie;if(!t.message.loading)return[];const A=[];return(D=t.message.meta)!=null&&D.company&&A.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&A.push({label:"핵심 수치 확인",done:!0}),(ae=t.message.meta)!=null&&ae.includedModules&&A.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((ie=t.message.contexts)==null?void 0:ie.length)>0&&A.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&A.push({label:"프롬프트 조립",done:!0}),t.message.text?A.push({label:"응답 작성 중",done:!1}):A.push({label:n(i)||"준비 중",done:!1}),A});var we=Cp(),ke=Q(we);{var Ie=A=>{var D=Dv(),ae=m(d(D),2),ie=d(ae),ve=d(ie);L(()=>N(ve,t.message.text)),f(A,D)},ge=A=>{var D=up(),ae=m(d(D),2),ie=d(ae);{var ve=Ue=>{var Pe=qv(),ht=d(Pe),Yt=d(ht);Jf(Yt,{size:11});var wt=m(ht,4),vt=d(wt);{var yt=j=>{ji(j,{variant:"muted",children:(Ce,it)=>{var ct=gs();L(()=>N(ct,n(o))),f(Ce,ct)},$$slots:{default:!0}})};z(vt,j=>{n(o)&&j(yt)})}var Bt=m(vt,2);{var Lt=j=>{ji(j,{variant:"accent",children:(Ce,it)=>{var ct=gs();L(()=>N(ct,n(c))),f(Ce,ct)},$$slots:{default:!0}})};z(Bt,j=>{n(c)&&j(Lt)})}var g=m(Bt,2);{var V=j=>{var Ce=be(),it=Q(Ce);$e(it,17,()=>t.message.contexts,Te,(ct,et,Ot)=>{var Rt=jv(),Rr=d(Rt);fs(Rr,{size:10,class:"flex-shrink-0"});var Br=m(Rr);L(()=>N(Br,` ${(n(et).label||n(et).module)??""}`)),oe("click",Rt,()=>H(Ot)),f(ct,Rt)}),f(j,Ce)},I=j=>{var Ce=Vv(),it=d(Ce);fs(it,{size:10,class:"flex-shrink-0"});var ct=m(it);L(()=>N(ct,` 모듈 ${t.message.meta.includedModules.length??""}개`)),f(j,Ce)};z(g,j=>{var Ce,it,ct;((Ce=t.message.contexts)==null?void 0:Ce.length)>0?j(V):((ct=(it=t.message.meta)==null?void 0:it.includedModules)==null?void 0:ct.length)>0&&j(I,1)})}var W=m(g,2);$e(W,17,()=>n(ue),Te,(j,Ce)=>{var it=Fv(),ct=d(it);_u(ct,()=>n(Ce).icon,(Ot,Rt)=>{Rt(Ot,{size:10,class:"flex-shrink-0"})});var et=m(ct);L(()=>N(et,` ${n(Ce).label??""}`)),oe("click",it,()=>{n(Ce).label.startsWith("컨텍스트")?H(0):n(Ce).label.startsWith("툴 호출")?t.onOpenEvidence?t.onOpenEvidence("tool-calls",0):ce(0):n(Ce).label.startsWith("툴 결과")?t.onOpenEvidence?t.onOpenEvidence("tool-results",0):ce((t.message.toolEvents||[]).findIndex(Ot=>Ot.type==="result")):n(Ce).label==="시스템 프롬프트"?M():n(Ce).label==="LLM 입력"&&ne()}),f(j,it)}),f(Ue,Pe)};z(ie,Ue=>{var Pe,ht;(n(o)||n(c)||((Pe=t.message.contexts)==null?void 0:Pe.length)>0||(ht=t.message.meta)!=null&&ht.includedModules||n(ue).length>0)&&Ue(ve)})}var fe=m(ie,2);{var pe=Ue=>{var Pe=Uv(),ht=d(Pe);$e(ht,21,()=>t.message.snapshot.items,Te,(vt,yt)=>{const Bt=G(()=>n(yt).status==="good"?"text-dl-success":n(yt).status==="danger"?"text-dl-primary-light":n(yt).status==="caution"?"text-amber-400":"text-dl-text");var Lt=Bv(),g=d(Lt),V=d(g),I=m(g,2),W=d(I);L(j=>{N(V,n(yt).label),Ne(I,1,j),N(W,n(yt).value)},[()=>Mt(Et("text-[14px] font-semibold leading-snug mt-0.5",n(Bt)))]),f(vt,Lt)});var Yt=m(ht,2);{var wt=vt=>{var yt=Hv();$e(yt,21,()=>t.message.snapshot.warnings,Te,(Bt,Lt)=>{var g=Gv(),V=d(g);gv(V,{size:10});var I=m(V);L(()=>N(I,` ${n(Lt)??""}`)),f(Bt,g)}),f(vt,yt)};z(Yt,vt=>{var yt;((yt=t.message.snapshot.warnings)==null?void 0:yt.length)>0&&vt(wt)})}oe("click",Pe,q),f(Ue,Pe)};z(fe,Ue=>{var Pe,ht;((ht=(Pe=t.message.snapshot)==null?void 0:Pe.items)==null?void 0:ht.length)>0&&Ue(pe)})}var Ee=m(fe,2);{var K=Ue=>{var Pe=Kv(),ht=d(Pe),Yt=m(d(ht),4);$e(Yt,21,()=>t.message.toolEvents,Te,(wt,vt,yt)=>{const Bt=G(()=>X(n(vt)));var Lt=Wv(),g=d(Lt);{var V=j=>{Di(j,{size:11})},I=j=>{xs(j,{size:11})};z(g,j=>{n(vt).type==="call"?j(V):j(I,-1)})}var W=m(g);L(j=>{Ne(Lt,1,j),N(W,` ${(n(vt).type==="call"?n(vt).name:`${n(vt).name} 결과`)??""}${n(Bt)?`: ${n(Bt)}`:""}`)},[()=>Mt(Et("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",n(vt).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),oe("click",Lt,()=>ce(yt)),f(wt,Lt)}),f(Ue,Pe)};z(Ee,Ue=>{var Pe;((Pe=t.message.toolEvents)==null?void 0:Pe.length)>0&&Ue(K)})}var qt=m(Ee,2);{var ot=Ue=>{var Pe=Qv(),ht=d(Pe);$e(ht,21,()=>n(te),Te,(Yt,wt)=>{var vt=Jv(),yt=d(vt);{var Bt=g=>{var V=Yv(),I=m(Q(V),2),W=d(I);L(()=>N(W,n(wt).label)),f(g,V)},Lt=g=>{var V=Xv(),I=Q(V);Xr(I,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var W=m(I,2),j=d(W);L(()=>N(j,n(wt).label)),f(g,V)};z(yt,g=>{n(wt).done?g(Bt):g(Lt,-1)})}f(Yt,vt)}),f(Ue,Pe)},nr=Ue=>{var Pe=cp(),ht=Q(Pe);{var Yt=I=>{var W=Zv(),j=d(W);Xr(j,{size:12,class:"animate-spin flex-shrink-0"});var Ce=m(j,2),it=d(Ce);L(()=>N(it,n(i))),f(I,W)};z(ht,I=>{t.message.loading&&I(Yt)})}var wt=m(ht,2),vt=d(wt);{var yt=I=>{var W=ep(),j=d(W);ea(j,()=>Qa(n(O).committed)),f(I,W)};z(vt,I=>{n(O).committed&&I(yt)})}var Bt=m(vt,2);{var Lt=I=>{var W=tp(),j=d(W),Ce=d(j),it=m(j,2),ct=d(it);L(et=>{Ne(W,1,et),N(Ce,n(O).draftType==="table"?"표 구성 중":n(O).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),N(ct,n(O).draft)},[()=>Mt(Et("message-live-tail",n(O).draftType==="table"&&"message-draft-table",n(O).draftType==="code"&&"message-draft-code"))]),f(I,W)};z(Bt,I=>{n(O).draft&&I(Lt)})}Ja(wt,I=>u($,I),()=>n($));var g=m(wt,2);{var V=I=>{var W=dp(),j=d(W);{var Ce=tt=>{var Je=rp(),At=d(Je);nv(At,{size:10});var J=m(At);L(()=>N(J,` ${t.message.duration??""}초`)),f(tt,Je)};z(j,tt=>{t.message.duration&&tt(Ce)})}var it=m(j,2);{var ct=tt=>{var Je=sp(),At=d(Je);{var J=Qe=>{var ut=np(),Dt=d(ut);L(Ut=>N(Dt,`↑${Ut??""}`),[()=>p(n(_))]),f(Qe,ut)};z(At,Qe=>{n(_)>0&&Qe(J)})}var je=m(At,2);{var lt=Qe=>{var ut=ap(),Dt=d(ut);L(Ut=>N(Dt,`↓${Ut??""}`),[()=>p(n(w))]),f(Qe,ut)};z(je,Qe=>{n(w)>0&&Qe(lt)})}f(tt,Je)};z(it,tt=>{(n(_)>0||n(w)>0)&&tt(ct)})}var et=m(it,2);{var Ot=tt=>{var Je=op(),At=d(Je);fv(At,{size:10}),oe("click",Je,()=>{var J;return(J=t.onRegenerate)==null?void 0:J.call(t)}),f(tt,Je)};z(et,tt=>{t.onRegenerate&&tt(Ot)})}var Rt=m(et,2);{var Rr=tt=>{var Je=ip(),At=d(Je);io(At,{size:10}),oe("click",Je,M),f(tt,Je)};z(Rt,tt=>{t.message.systemPrompt&&tt(Rr)})}var Br=m(Rt,2);{var zn=tt=>{var Je=lp(),At=d(Je);Rn(At,{size:10});var J=m(At);L((je,lt)=>N(J,` LLM 입력 (${je??""}자 · ~${lt??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>p(v(t.message.userContent))]),oe("click",Je,ne),f(tt,Je)};z(Br,tt=>{t.message.userContent&&tt(zn)})}f(I,W)};z(g,I=>{!t.message.loading&&(t.message.duration||n(l)||t.onRegenerate)&&I(V)})}L(I=>Ne(wt,1,I),[()=>Mt(Et("prose-dartlab message-body text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),oe("click",wt,T),f(Ue,Pe)};z(qt,Ue=>{t.message.loading&&!t.message.text?Ue(ot):Ue(nr,-1)})}f(A,D)};z(ke,A=>{t.message.role==="user"?A(Ie):A(ge,-1)})}var xe=m(ke,2);{var F=A=>{const D=G(()=>n(a)==="system"),ae=G(()=>n(a)==="userContent"),ie=G(()=>n(a)==="context"),ve=G(()=>n(a)==="snapshot"),fe=G(()=>n(a)==="tool"),pe=G(()=>{var J;return n(ie)?(J=t.message.contexts)==null?void 0:J[n(r)]:null}),Ee=G(()=>{var J;return n(fe)?(J=t.message.toolEvents)==null?void 0:J[n(r)]:null}),K=G(()=>{var J,je,lt,Qe,ut;return n(ve)?"핵심 수치 (원본 데이터)":n(D)?"시스템 프롬프트":n(ae)?"LLM에 전달된 입력":n(fe)?((J=n(Ee))==null?void 0:J.type)==="call"?`${(je=n(Ee))==null?void 0:je.name} 호출`:`${(lt=n(Ee))==null?void 0:lt.name} 결과`:((Qe=n(pe))==null?void 0:Qe.label)||((ut=n(pe))==null?void 0:ut.module)||""}),qt=G(()=>{var J;return n(ve)?JSON.stringify(t.message.snapshot,null,2):n(D)?t.message.systemPrompt:n(ae)?t.message.userContent:n(fe)?JSON.stringify(n(Ee),null,2):(J=n(pe))==null?void 0:J.text});var ot=kp(),nr=d(ot),Ue=d(nr),Pe=d(Ue),ht=d(Pe),Yt=d(ht);{var wt=J=>{fs(J,{size:15,class:"text-dl-success flex-shrink-0"})},vt=J=>{io(J,{size:15,class:"text-dl-primary-light flex-shrink-0"})},yt=J=>{Rn(J,{size:15,class:"text-dl-accent flex-shrink-0"})},Bt=J=>{fs(J,{size:15,class:"flex-shrink-0"})};z(Yt,J=>{n(ve)?J(wt):n(D)?J(vt,1):n(ae)?J(yt,2):J(Bt,-1)})}var Lt=m(Yt,2),g=d(Lt),V=m(Lt,2);{var I=J=>{var je=fp(),lt=d(je);L(Qe=>N(lt,`(${Qe??""}자)`),[()=>{var Qe,ut;return(ut=(Qe=n(qt))==null?void 0:Qe.length)==null?void 0:ut.toLocaleString()}]),f(J,je)};z(V,J=>{n(D)&&J(I)})}var W=m(ht,2),j=d(W);{var Ce=J=>{var je=vp(),lt=d(je),Qe=d(lt);Rn(Qe,{size:11});var ut=m(lt,2),Dt=d(ut);av(Dt,{size:11}),L((Ut,Oe)=>{Ne(lt,1,Ut),Ne(ut,1,Oe)},[()=>Mt(Et("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(s)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>Mt(Et("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(s)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),oe("click",lt,()=>u(s,"rendered")),oe("click",ut,()=>u(s,"raw")),f(J,je)};z(j,J=>{n(ie)&&J(Ce)})}var it=m(j,2),ct=d(it);Vs(ct,{size:18});var et=m(Pe,2);{var Ot=J=>{var je=mp(),lt=d(je);$e(lt,21,()=>t.message.contexts,Te,(Qe,ut,Dt)=>{var Ut=pp(),Oe=d(Ut);L(zt=>{Ne(Ut,1,zt),N(Oe,t.message.contexts[Dt].label||t.message.contexts[Dt].module)},[()=>Mt(Et("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",Dt===n(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),oe("click",Ut,()=>{u(r,Dt,!0)}),f(Qe,Ut)}),f(J,je)};z(et,J=>{var je;n(ie)&&((je=t.message.contexts)==null?void 0:je.length)>1&&J(Ot)})}var Rt=m(et,2);{var Rr=J=>{var je=xp(),lt=d(je),Qe=d(lt);{var ut=Oe=>{var zt=hp();L(yr=>Ne(zt,1,yr),[()=>Mt(Et("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(D)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),oe("click",zt,()=>{u(a,"system")}),f(Oe,zt)};z(Qe,Oe=>{t.message.systemPrompt&&Oe(ut)})}var Dt=m(Qe,2);{var Ut=Oe=>{var zt=gp();L(yr=>Ne(zt,1,yr),[()=>Mt(Et("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(ae)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),oe("click",zt,()=>{u(a,"userContent")}),f(Oe,zt)};z(Dt,Oe=>{t.message.userContent&&Oe(Ut)})}f(J,je)};z(Rt,J=>{!n(ie)&&!n(ve)&&!n(fe)&&J(Rr)})}var Br=m(Ue,2),zn=d(Br);{var tt=J=>{var je=bp(),lt=d(je);ea(lt,()=>{var Qe;return Qa((Qe=n(pe))==null?void 0:Qe.text)}),f(J,je)},Je=J=>{var je=wp(),lt=d(je),Qe=m(d(lt),2),ut=d(Qe),Dt=m(ut);{var Ut=Er=>{var mn=_p(),ar=d(mn);L(An=>N(ar,An),[()=>X(n(Ee))]),f(Er,mn)},Oe=G(()=>X(n(Ee)));z(Dt,Er=>{n(Oe)&&Er(Ut)})}var zt=m(lt,2),yr=d(zt);L(()=>{var Er;N(ut,`${((Er=n(Ee))==null?void 0:Er.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),N(yr,n(qt))}),f(J,je)},At=J=>{var je=yp(),lt=d(je);L(()=>N(lt,n(qt))),f(J,je)};z(zn,J=>{n(ie)&&n(s)==="rendered"?J(tt):n(fe)?J(Je,1):J(At,-1)})}L(()=>N(g,n(K))),oe("click",ot,J=>{J.target===J.currentTarget&&k()}),oe("keydown",ot,J=>{J.key==="Escape"&&k()}),oe("click",it,k),f(A,ot)};z(xe,A=>{n(r)!==null&&A(F)})}f(e,we),rn()}la(["click","keydown"]);var Mp=h('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),Ep=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),zp=h('<div class="flex justify-end gap-2 mb-1.5"><!></div>'),Ap=h('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8"><!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function Tp(e,t){tn(t,!0);function r(Z){if(s())return!1;for(let O=a().length-1;O>=0;O--)if(a()[O].role==="assistant"&&!a()[O].error&&a()[O].text)return O===Z;return!1}let a=at(t,"messages",19,()=>[]),s=at(t,"isLoading",3,!1),i=at(t,"inputText",15,""),o=at(t,"scrollTrigger",3,0);at(t,"selectedCompany",3,null);function l(Z){return(O,ue)=>{var we,ke,Ie;let te;if(O==="contexts")te=(we=Z.contexts)==null?void 0:we[ue];else if(O==="snapshot")te={label:"핵심 수치",module:"snapshot",text:JSON.stringify(Z.snapshot,null,2)};else if(O==="system")te={label:"시스템 프롬프트",module:"system",text:Z.systemPrompt};else if(O==="input")te={label:"LLM 입력",module:"input",text:Z.userContent};else if(O==="tool-calls"||O==="tool-results"){const ge=(ke=Z.toolEvents)==null?void 0:ke[ue];te={label:`${(ge==null?void 0:ge.name)||"도구"} ${(ge==null?void 0:ge.type)==="call"?"호출":"결과"}`,module:"tool",text:JSON.stringify(ge,null,2)}}te&&((Ie=t.onOpenData)==null||Ie.call(t,te))}}let c,v,p=U(!0),_=U(!1),w=U(!0);function $(){if(!c)return;const{scrollTop:Z,scrollHeight:O,clientHeight:ue}=c;u(w,O-Z-ue<96),n(w)?(u(p,!0),u(_,!1)):(u(p,!1),u(_,!0))}function C(Z="smooth"){v&&(v.scrollIntoView({block:"end",behavior:Z}),u(p,!0),u(_,!1))}Zn(()=>{o(),!(!c||!v)&&requestAnimationFrame(()=>{!c||!v||(n(p)||n(w)?(v.scrollIntoView({block:"end",behavior:s()?"auto":"smooth"}),u(_,!1)):u(_,!0))})});var P=Ap(),y=d(P),x=d(y),T=d(x);$e(T,17,a,Te,(Z,O,ue)=>{{let te=G(()=>r(ue)?t.onRegenerate:void 0),we=G(()=>t.onOpenData?l(n(O)):void 0);Sp(Z,{get message(){return n(O)},get onRegenerate(){return n(te)},get onOpenEvidence(){return n(we)}})}});var H=m(T,2);Ja(H,Z=>v=Z,()=>v),Ja(y,Z=>c=Z,()=>c);var M=m(y,2);{var q=Z=>{var O=Mp(),ue=d(O);oe("click",ue,()=>C("smooth")),f(Z,O)};z(M,Z=>{n(_)&&Z(q)})}var ce=m(M,2),ne=d(ce),k=d(ne);{var X=Z=>{var O=zp(),ue=d(O);{var te=we=>{var ke=Ep(),Ie=d(ke);bs(Ie,{size:10}),oe("click",ke,function(...ge){var xe;(xe=t.onExport)==null||xe.apply(this,ge)}),f(we,ke)};z(ue,we=>{a().length>1&&t.onExport&&we(te)})}f(Z,O)};z(k,Z=>{s()||Z(X)})}var ee=m(k,2);ld(ee,{get isLoading(){return s()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get onCompanySelect(){return t.onCompanySelect},get inputText(){return i()},set inputText(Z){i(Z)}}),Ra("scroll",y,$),f(e,P),rn()}la(["click"]);var $p=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!> <span class="text-[13px]">공시 데이터 로딩 중...</span></div>'),Ip=h('<div class="text-[11px] text-dl-text-dim"> </div>'),Pp=h('<button><!> <span class="truncate flex-1"> </span></button>'),Np=h('<div class="py-0.5"></div>'),Lp=h('<div><button class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] opacity-30 font-normal"> </span></button> <!></div>'),Op=h('<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50"><div class="px-3 py-2.5 border-b border-dl-border/20"><!></div> <!></nav>'),Rp=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim"><!> <p class="text-[13px]">좌측에서 섹션을 선택하세요</p></div>'),Dp=h('<div class="text-[10px] text-dl-text-dim/50 mb-0.5"> </div>'),jp=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!></div>'),Vp=h('<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>'),Fp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),qp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Bp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Gp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Hp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Up=h('<div class="vw-heading-node svelte-1l2nqwu"><!></div>'),Wp=h('<div class="vw-heading-block svelte-1l2nqwu"></div>'),Kp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Yp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Xp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Jp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Qp=h('<button><span class="vw-timeline-label svelte-1l2nqwu"> </span></button>'),Zp=h('<div class="vw-section-timeline svelte-1l2nqwu"></div>'),em=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),tm=h('<span class="vw-meta-pill svelte-1l2nqwu">비교 없음</span>'),rm=h('<div class="vw-section-actions svelte-1l2nqwu"><span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span></div>'),nm=h('<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span> </div>'),am=h('<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),sm=h('<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),om=h('<div class="text-[10px] text-dl-text-dim/35 mt-1"> </div>'),im=h('<div class="vw-digest svelte-1l2nqwu"><div class="flex items-center gap-2 mb-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span></div> <div class="space-y-1"><!> <!> <!> <!></div></div>'),lm=h('<p class="vw-para"> </p>'),dm=h('<div class="vw-diff-added svelte-1l2nqwu"> </div>'),cm=h('<div class="vw-diff-deleted svelte-1l2nqwu"> </div>'),um=h('<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow svelte-1l2nqwu"></div>'),fm=h('<div class="disclosure-text vw-section-body vw-body-frame svelte-1l2nqwu"><!></div>'),vm=h('<div><!> <div class="vw-section-meta svelte-1l2nqwu"><span> </span> <!> <!> <!> <!></div> <!> <!> <!> <!></div>'),pm=h('<section class="vw-report-shell svelte-1l2nqwu"><div class="vw-report-header svelte-1l2nqwu"><div class="vw-report-badges svelte-1l2nqwu"><!> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <!> <!></div></div> <!></section>'),mm=h('<div class="vw-data-divider svelte-1l2nqwu"><div class="vw-data-kicker svelte-1l2nqwu">Structured Data</div> <div class="vw-data-title svelte-1l2nqwu">표 / 정형 데이터</div></div>'),hm=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),gm=h("<th> </th>"),xm=h("<td> </td>"),bm=h("<tr></tr>"),_m=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),wm=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),ym=h("<th> </th>"),km=h("<td> </td>"),Cm=h("<tr></tr>"),Sm=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),Mm=h("<button> </button>"),Em=h('<span class="text-[9px] text-dl-text-dim/30"> </span>'),zm=h('<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto"><!> <!></div>'),Am=h('<div class="vw-table-wrap bg-dl-bg-card/10 svelte-1l2nqwu"><!> <div class="px-4 py-3"><div class="markdown-table overflow-x-auto svelte-1l2nqwu"><!></div></div></div>'),Tm=h("<th> </th>"),$m=h("<td> </td>"),Im=h("<tr></tr>"),Pm=h('<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02] svelte-1l2nqwu"><div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10"><!> <span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span></div> <div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Nm=h('<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card"> </th>'),Lm=h('<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted"> </td>'),Om=h("<tr></tr>"),Rm=h('<div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Dm=h('<article class="py-6 px-8"><!> <!> <!> <!></article>'),jm=h('<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center"><div class="flex-1 min-w-0"><!> <h3 class="text-[16px] font-semibold text-dl-text"> </h3></div> <button class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"><!></button></div> <!>',1),Vm=h('<div class="flex flex-1 overflow-hidden min-h-0"><!> <main class="flex-1 overflow-y-auto min-w-0"><!></main></div>'),Fm=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8"><!> <p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p></div>'),qm=h('<div class="flex flex-col h-full font-sans bg-dl-bg-dark"><!></div>');function Bm(e,t){tn(t,!0);let r=at(t,"stockCode",3,null),a=at(t,"onTopicChange",3,null),s=U(null),i=U(!1),o=U(St(new Set)),l=U(null),c=U(null),v=U(St([])),p=U(null),_=U(!1),w=U(St([])),$=U(St(new Map)),C=new Map,P=U(!1),y=U(St(new Map));const x={companyOverview:"회사 개요",companyHistory:"회사 연혁",articlesOfIncorporation:"정관 사항",capitalChange:"자본금 변동",shareCapital:"주식 현황",dividend:"배당",productService:"사업 내용",rawMaterial:"원재료",businessOverview:"사업 개요",salesOrder:"매출/수주",riskDerivative:"위험관리/파생",majorContractsAndRnd:"주요 계약/R&D",otherReferences:"기타 참고사항",consolidatedStatements:"연결 재무제표",fsSummary:"재무제표 요약",consolidatedNotes:"연결 주석",financialStatements:"개별 재무제표",financialNotes:"개별 주석",fundraising:"자금조달",BS:"재무상태표",IS:"손익계산서",CIS:"포괄손익계산서",CF:"현금흐름표",SCE:"자본변동표",ratios:"재무비율",audit:"감사 의견",mdna:"경영진 분석(MD&A)",internalControl:"내부통제",auditContract:"감사 계약",nonAuditContract:"비감사 계약",boardOfDirectors:"이사회",shareholderMeeting:"주주총회",auditSystem:"감사 체계",outsideDirector:"사외이사",majorHolder:"주요 주주",majorHolderChange:"주주 변동",minorityHolder:"소수주주",stockTotal:"주식 총수",treasuryStock:"자기주식",employee:"직원 현황",executivePay:"임원 보수",executive:"임원 현황",executivePayAllTotal:"전체 보수 총액",executivePayIndividual:"개인별 보수",topPay:"5억이상 상위 보수",unregisteredExecutivePay:"미등기임원 보수",affiliateGroup:"계열회사",investedCompany:"투자회사",relatedPartyTx:"특수관계 거래",corporateBond:"사채 관리",privateOfferingUsage:"사모자금 사용",publicOfferingUsage:"공모자금 사용",shortTermBond:"단기사채",investorProtection:"투자자 보호",disclosureChanges:"공시변경 사항",contingentLiability:"우발채무",sanction:"제재/조치",subsequentEvents:"후발사건",expertConfirmation:"전문가 확인",subsidiaryDetail:"종속회사 상세",affiliateGroupDetail:"계열회사 상세",investmentInOtherDetail:"타법인 출자 상세",rndDetail:"R&D 상세"},T={I:"I. 회사의 개요",II:"II. 사업의 내용",III:"III. 재무에 관한 사항",IV:"IV. 감사인의 감사의견 등",V:"V. 이사의 경영진단 및 분석의견",VI:"VI. 이사회 등 회사의 기관에 관한 사항",VII:"VII. 주주에 관한 사항",VIII:"VIII. 임원 및 직원 등에 관한 사항",IX:"IX. 계열회사 등에 관한 사항",X:"X. 대주주 등과의 거래내용",XI:"XI. 그 밖에 투자자 보호를 위하여 필요한 사항",XII:"XII. 상세표"},H={I:1,II:2,III:3,IV:4,V:5,VI:6,VII:7,VIII:8,IX:9,X:10,XI:11,XII:12};function M(g){return H[g]??99}function q(g){return x[g]||g}function ce(g){return T[g]||g||"기타"}Zn(()=>{r()&&ne()});async function ne(){var g,V;u(i,!0),u(s,null),u(l,null),u(c,null),u(v,[],!0),u(p,null),C=new Map;try{const I=await Hu(r());u(s,I.payload,!0),(g=n(s))!=null&&g.columns&&u(w,n(s).columns.filter(j=>/^\d{4}(Q[1-4])?$/.test(j)),!0);const W=te((V=n(s))==null?void 0:V.rows);W.length>0&&(u(o,new Set([W[0].chapter]),!0),W[0].topics.length>0&&k(W[0].topics[0].topic,W[0].chapter))}catch(I){console.error("viewer load error:",I)}u(i,!1)}async function k(g,V){var I;if(n(l)!==g){if(u(l,g,!0),u(c,V||null,!0),u($,new Map,!0),u(y,new Map,!0),(I=a())==null||I(g,q(g)),C.has(g)){const W=C.get(g);u(v,W.blocks||[],!0),u(p,W.textDocument||null,!0);return}u(v,[],!0),u(p,null),u(_,!0);try{const W=await Gu(r(),g);u(v,W.blocks||[],!0),u(p,W.textDocument||null,!0),C.set(g,{blocks:n(v),textDocument:n(p)})}catch(W){console.error("topic load error:",W),u(v,[],!0),u(p,null)}u(_,!1)}}function X(g){const V=new Set(n(o));V.has(g)?V.delete(g):V.add(g),u(o,V,!0)}function ee(g,V){const I=new Map(n($));I.get(g)===V?I.delete(g):I.set(g,V),u($,I,!0)}function Z(g,V){const I=new Map(n(y));I.set(g,V),u(y,I,!0)}function O(g){return g==="updated"?"최근 수정":g==="new"?"신규":g==="stale"?"과거 유지":"유지"}function ue(g){return g==="updated"?"updated":g==="new"?"new":g==="stale"?"stale":"stable"}function te(g){if(!g)return[];const V=new Map,I=new Set;for(const W of g){const j=W.chapter||"";V.has(j)||V.set(j,{chapter:j,topics:[]}),I.has(W.topic)||(I.add(W.topic),V.get(j).topics.push({topic:W.topic,source:W.source||"docs"}))}return[...V.values()].sort((W,j)=>M(W.chapter)-M(j.chapter))}function we(g){return String(g).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function ke(g){return String(g||"").replaceAll(" "," ").replace(/\s+/g," ").trim()}function Ie(g){return!g||g.length>88?!1:/^\[.+\]$/.test(g)||/^【.+】$/.test(g)||/^[IVX]+\.\s/.test(g)||/^\d+\.\s/.test(g)||/^[가-힣]\.\s/.test(g)||/^\(\d+\)\s/.test(g)||/^\([가-힣]\)\s/.test(g)}function ge(g){return/^\(\d+\)\s/.test(g)||/^\([가-힣]\)\s/.test(g)?"h5":"h4"}function xe(g){return/^\[.+\]$/.test(g)||/^【.+】$/.test(g)?"vw-h-bracket":/^\(\d+\)\s/.test(g)||/^\([가-힣]\)\s/.test(g)?"vw-h-sub":"vw-h-section"}function F(g){if(!g)return[];if(/^\|.+\|$/m.test(g)||/^#{1,3} /m.test(g)||/```/.test(g))return[{kind:"markdown",text:g}];const V=[];let I=[];const W=()=>{I.length!==0&&(V.push({kind:"paragraph",text:I.join(" ")}),I=[])};for(const j of String(g).split(`
`)){const Ce=ke(j);if(!Ce){W();continue}if(Ie(Ce)){W(),V.push({kind:"heading",text:Ce,tag:ge(Ce),className:xe(Ce)});continue}I.push(Ce)}return W(),V}function A(g){return g?g.kind==="annual"?`${g.year}Q4`:g.year&&g.quarter?`${g.year}Q${g.quarter}`:g.label||"":""}function D(g){var W;const V=F(g);if(V.length===0)return"";if(((W=V[0])==null?void 0:W.kind)==="markdown")return Qa(g);let I="";for(const j of V){if(j.kind==="heading"){I+=`<${j.tag} class="${j.className}">${we(j.text)}</${j.tag}>`;continue}I+=`<p class="vw-para">${we(j.text)}</p>`}return I}function ae(g){if(!g)return"";const V=g.trim().split(`
`).filter(W=>W.trim());let I="";for(const W of V){const j=W.trim();/^[가-힣]\.\s/.test(j)||/^\d+[-.]/.test(j)?I+=`<h4 class="vw-h-section">${j}</h4>`:/^\(\d+\)\s/.test(j)||/^\([가-힣]\)\s/.test(j)?I+=`<h5 class="vw-h-sub">${j}</h5>`:/^\[.+\]$/.test(j)||/^【.+】$/.test(j)?I+=`<h4 class="vw-h-bracket">${j}</h4>`:I+=`<h5 class="vw-h-sub">${j}</h5>`}return I}function ie(g){var I;const V=n($).get(g.id);return V&&((I=g==null?void 0:g.views)!=null&&I[V])?g.views[V]:(g==null?void 0:g.latest)||null}function ve(g,V){var W,j;const I=n($).get(g.id);return I?I===V:((j=(W=g==null?void 0:g.latest)==null?void 0:W.period)==null?void 0:j.label)===V}function fe(g){return n($).has(g.id)}function pe(g){return g==="updated"?"변경 있음":g==="new"?"직전 없음":"직전과 동일"}function Ee(g){var Ce,it,ct;if(!g)return[];const V=F(g.body);if(V.length===0||((Ce=V[0])==null?void 0:Ce.kind)==="markdown"||!((it=g.prevPeriod)!=null&&it.label)||!((ct=g.diff)!=null&&ct.length))return V;const I=[];for(const et of g.diff)for(const Ot of et.paragraphs||[])I.push({kind:et.kind,text:ke(Ot)});const W=[];let j=0;for(const et of V){if(et.kind!=="paragraph"){W.push(et);continue}for(;j<I.length&&I[j].kind==="removed";)W.push({kind:"removed",text:I[j].text}),j+=1;j<I.length&&["same","added"].includes(I[j].kind)?(W.push({kind:I[j].kind,text:I[j].text||et.text}),j+=1):W.push({kind:"same",text:et.text})}for(;j<I.length;)W.push({kind:I[j].kind,text:I[j].text}),j+=1;return W}function K(g){return g==null?!1:/^-?[\d,.]+%?$/.test(String(g).trim().replace(/,/g,""))}function qt(g){return g==null?!1:/^-[\d.]+/.test(String(g).trim().replace(/,/g,""))}function ot(g,V){if(g==null||g==="")return"";const I=typeof g=="number"?g:Number(String(g).replace(/,/g,""));if(isNaN(I))return String(g);if(V<=1)return I.toLocaleString("ko-KR");const W=I/V;return Number.isInteger(W)?W.toLocaleString("ko-KR"):W.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g,",")}function nr(g){if(g==null||g==="")return"";const V=String(g).trim();if(V.includes(","))return V;const I=V.match(/^(-?\d+)(\.\d+)?(%?)$/);return I?I[1].replace(/\B(?=(\d{3})+(?!\d))/g,",")+(I[2]||"")+(I[3]||""):V}function Ue(g){var V,I;return(V=n(s))!=null&&V.rows&&((I=n(s).rows.find(W=>W.topic===g))==null?void 0:I.chapter)||null}function Pe(g){const V=g.match(/^(\d{4})(Q([1-4]))?$/);if(!V)return"0000_0";const I=V[1],W=V[3]||"5";return`${I}_${W}`}function ht(g){return[...g].sort((V,I)=>Pe(I).localeCompare(Pe(V)))}let Yt=G(()=>n(v).filter(g=>g.kind!=="text"));var wt=qm(),vt=d(wt);{var yt=g=>{var V=$p(),I=d(V);Xr(I,{size:18,class:"animate-spin"}),f(g,V)},Bt=g=>{var V=Vm(),I=d(V);{var W=et=>{var Ot=Op(),Rt=d(Ot),Rr=d(Rt);{var Br=tt=>{var Je=Ip(),At=d(Je);L(()=>N(At,`${n(w).length??""}개 기간 · ${n(w)[0]??""} ~ ${n(w)[n(w).length-1]??""}`)),f(tt,Je)};z(Rr,tt=>{n(w).length>0&&tt(Br)})}var zn=m(Rt,2);$e(zn,17,()=>te(n(s).rows),Te,(tt,Je)=>{var At=Lp(),J=d(At),je=d(J);{var lt=ar=>{tv(ar,{size:11,class:"flex-shrink-0 opacity-40"})},Qe=G(()=>n(o).has(n(Je).chapter)),ut=ar=>{rv(ar,{size:11,class:"flex-shrink-0 opacity-40"})};z(je,ar=>{n(Qe)?ar(lt):ar(ut,-1)})}var Dt=m(je,2),Ut=d(Dt),Oe=m(Dt,2),zt=d(Oe),yr=m(J,2);{var Er=ar=>{var An=Np();$e(An,21,()=>n(Je).topics,Te,(ns,hn)=>{var jt=Pp(),Ve=d(jt);{var kr=cr=>{Zf(cr,{size:11,class:"flex-shrink-0 text-blue-400/40"})},ca=cr=>{Pi(cr,{size:11,class:"flex-shrink-0 text-emerald-400/40"})},Tn=cr=>{Rn(cr,{size:11,class:"flex-shrink-0 opacity-30"})};z(Ve,cr=>{n(hn).source==="finance"?cr(kr):n(hn).source==="report"?cr(ca,1):cr(Tn,-1)})}var ua=m(Ve,2),$n=d(ua);L(cr=>{Ne(jt,1,`group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											${n(l)===n(hn).topic?"bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]":"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent"}`),N($n,cr)},[()=>q(n(hn).topic)]),oe("click",jt,()=>k(n(hn).topic,n(Je).chapter)),f(ns,jt)}),f(ar,An)},mn=G(()=>n(o).has(n(Je).chapter));z(yr,ar=>{n(mn)&&ar(Er)})}L(ar=>{N(Ut,ar),N(zt,n(Je).topics.length)},[()=>ce(n(Je).chapter)]),oe("click",J,()=>X(n(Je).chapter)),f(tt,At)}),f(et,Ot)};z(I,et=>{n(P)||et(W)})}var j=m(I,2),Ce=d(j);{var it=et=>{var Ot=Rp(),Rt=d(Ot);Rn(Rt,{size:32,strokeWidth:1,class:"opacity-20"}),f(et,Ot)},ct=et=>{var Ot=jm(),Rt=Q(Ot),Rr=d(Rt),Br=d(Rr);{var zn=Oe=>{var zt=Dp(),yr=d(zt);L(Er=>N(yr,Er),[()=>ce(n(c)||Ue(n(l)))]),f(Oe,zt)},tt=G(()=>n(c)||Ue(n(l)));z(Br,Oe=>{n(tt)&&Oe(zn)})}var Je=m(Br,2),At=d(Je),J=m(Rr,2),je=d(J);{var lt=Oe=>{id(Oe,{size:15})},Qe=Oe=>{od(Oe,{size:15})};z(je,Oe=>{n(P)?Oe(lt):Oe(Qe,-1)})}var ut=m(Rt,2);{var Dt=Oe=>{var zt=jp(),yr=d(zt);Xr(yr,{size:16,class:"animate-spin"}),f(Oe,zt)},Ut=Oe=>{var zt=Dm(),yr=d(zt);{var Er=jt=>{var Ve=Vp();f(jt,Ve)};z(yr,jt=>{var Ve,kr;n(v).length===0&&!(((kr=(Ve=n(p))==null?void 0:Ve.sections)==null?void 0:kr.length)>0)&&jt(Er)})}var mn=m(yr,2);{var ar=jt=>{var Ve=pm(),kr=d(Ve),ca=d(kr),Tn=d(ca);{var ua=Ze=>{var he=Fp(),Fe=d(he);L(rt=>N(Fe,`최신 기준 ${rt??""}`),[()=>A(n(p).latestPeriod)]),f(Ze,he)};z(Tn,Ze=>{n(p).latestPeriod&&Ze(ua)})}var $n=m(Tn,2);{var cr=Ze=>{var he=qp(),Fe=d(he);L((rt,xt)=>N(Fe,`커버리지 ${rt??""}~${xt??""}`),[()=>A(n(p).firstPeriod),()=>A(n(p).latestPeriod)]),f(Ze,he)};z($n,Ze=>{n(p).firstPeriod&&Ze(cr)})}var Fn=m($n,2),Wt=d(Fn),gt=m(Fn,2);{var ur=Ze=>{var he=Bp(),Fe=d(he);L(()=>N(Fe,`최근 수정 ${n(p).updatedCount??""}개`)),f(Ze,he)};z(gt,Ze=>{n(p).updatedCount>0&&Ze(ur)})}var Kt=m(gt,2);{var Cr=Ze=>{var he=Gp(),Fe=d(he);L(()=>N(Fe,`신규 ${n(p).newCount??""}개`)),f(Ze,he)};z(Kt,Ze=>{n(p).newCount>0&&Ze(Cr)})}var Sr=m(Kt,2);{var fr=Ze=>{var he=Hp(),Fe=d(he);L(()=>N(Fe,`과거 유지 ${n(p).staleCount??""}개`)),f(Ze,he)};z(Sr,Ze=>{n(p).staleCount>0&&Ze(fr)})}var Dr=m(kr,2);$e(Dr,17,()=>n(p).sections,Te,(Ze,he)=>{const Fe=G(()=>ie(n(he))),rt=G(()=>fe(n(he)));var xt=vm(),vr=d(xt);{var ze=B=>{var S=Wp();$e(S,21,()=>n(he).headingPath,Te,(Y,Me)=>{var ye=Up(),me=d(ye);ea(me,()=>ae(n(Me).text)),f(Y,ye)}),f(B,S)};z(vr,B=>{var S;((S=n(he).headingPath)==null?void 0:S.length)>0&&B(ze)})}var Ye=m(vr,2),st=d(Ye),Tt=d(st),bt=m(st,2);{var pr=B=>{var S=Kp(),Y=d(S);L(Me=>N(Y,`최신 ${Me??""}`),[()=>A(n(he).latestPeriod)]),f(B,S)};z(bt,B=>{var S;(S=n(he).latestPeriod)!=null&&S.label&&B(pr)})}var b=m(bt,2);{var R=B=>{var S=Yp(),Y=d(S);L(Me=>N(Y,`최초 ${Me??""}`),[()=>A(n(he).firstPeriod)]),f(B,S)};z(b,B=>{var S,Y;(S=n(he).firstPeriod)!=null&&S.label&&n(he).firstPeriod.label!==((Y=n(he).latestPeriod)==null?void 0:Y.label)&&B(R)})}var de=m(b,2);{var _e=B=>{var S=Xp(),Y=d(S);L(()=>N(Y,`${n(he).periodCount??""}기간`)),f(B,S)};z(de,B=>{n(he).periodCount>0&&B(_e)})}var Se=m(de,2);{var Ae=B=>{var S=Jp(),Y=d(S);L(()=>N(Y,`최근 변경 ${n(he).latestChange??""}`)),f(B,S)};z(Se,B=>{n(he).latestChange&&B(Ae)})}var re=m(Ye,2);{var Xt=B=>{var S=Zp();$e(S,21,()=>n(he).timeline,Te,(Y,Me)=>{var ye=Qp(),me=d(ye),_t=d(me);L((pt,ft)=>{Ne(ye,1,`vw-timeline-chip ${pt??""}`,"svelte-1l2nqwu"),N(_t,ft)},[()=>ve(n(he),n(Me).period.label)?"is-active":"",()=>A(n(Me).period)]),oe("click",ye,()=>ee(n(he).id,n(Me).period.label)),f(Y,ye)}),f(B,S)};z(re,B=>{var S;((S=n(he).timeline)==null?void 0:S.length)>0&&B(Xt)})}var sr=m(re,2);{var In=B=>{var S=rm(),Y=d(S),Me=d(Y),ye=m(Y,2);{var me=Vt=>{var $t=em(),Tr=d($t);L(mt=>N(Tr,`비교 ${mt??""}`),[()=>A(n(Fe).prevPeriod)]),f(Vt,$t)},_t=Vt=>{var $t=tm();f(Vt,$t)};z(ye,Vt=>{var $t;($t=n(Fe).prevPeriod)!=null&&$t.label?Vt(me):Vt(_t,-1)})}var pt=m(ye,2),ft=d(pt);L((Vt,$t)=>{N(Me,`선택 ${Vt??""}`),N(ft,$t)},[()=>A(n(Fe).period),()=>pe(n(Fe).status)]),f(B,S)};z(sr,B=>{n(rt)&&n(Fe)&&B(In)})}var gn=m(sr,2);{var qn=B=>{const S=G(()=>n(Fe).digest);var Y=im(),Me=d(Y),ye=d(Me),me=d(ye),_t=m(Me,2),pt=d(_t);$e(pt,17,()=>n(S).items.filter(mt=>mt.kind==="numeric"),Te,(mt,or)=>{var Jt=nm(),kt=m(d(Jt));L(()=>N(kt,` ${n(or).text??""}`)),f(mt,Jt)});var ft=m(pt,2);$e(ft,17,()=>n(S).items.filter(mt=>mt.kind==="added"),Te,(mt,or)=>{var Jt=am(),kt=m(d(Jt),2),Ft=d(kt);L(()=>N(Ft,n(or).text)),f(mt,Jt)});var Vt=m(ft,2);$e(Vt,17,()=>n(S).items.filter(mt=>mt.kind==="removed"),Te,(mt,or)=>{var Jt=sm(),kt=m(d(Jt),2),Ft=d(kt);L(()=>N(Ft,n(or).text)),f(mt,Jt)});var $t=m(Vt,2);{var Tr=mt=>{var or=om(),Jt=d(or);L(()=>N(Jt,`외 ${n(S).wordingCount??""}건 문구 수정`)),f(mt,or)};z($t,mt=>{n(S).wordingCount>0&&mt(Tr)})}L(()=>N(me,`${n(S).to??""} vs ${n(S).from??""}`)),f(B,Y)};z(gn,B=>{var S,Y,Me;n(rt)&&((Me=(Y=(S=n(Fe))==null?void 0:S.digest)==null?void 0:Y.items)==null?void 0:Me.length)>0&&B(qn)})}var Bn=m(gn,2);{var Gn=B=>{var S=be(),Y=Q(S);{var Me=me=>{var _t=um();$e(_t,21,()=>Ee(n(Fe)),Te,(pt,ft)=>{var Vt=be(),$t=Q(Vt);{var Tr=kt=>{var Ft=be(),Gr=Q(Ft);ea(Gr,()=>ae(n(ft).text)),f(kt,Ft)},mt=kt=>{var Ft=lm(),Gr=d(Ft);L(()=>N(Gr,n(ft).text)),f(kt,Ft)},or=kt=>{var Ft=dm(),Gr=d(Ft);L(()=>N(Gr,n(ft).text)),f(kt,Ft)},Jt=kt=>{var Ft=cm(),Gr=d(Ft);L(()=>N(Gr,n(ft).text)),f(kt,Ft)};z($t,kt=>{n(ft).kind==="heading"?kt(Tr):n(ft).kind==="same"?kt(mt,1):n(ft).kind==="added"?kt(or,2):n(ft).kind==="removed"&&kt(Jt,3)})}f(pt,Vt)}),f(me,_t)},ye=me=>{var _t=fm(),pt=d(_t);ea(pt,()=>D(n(Fe).body)),f(me,_t)};z(Y,me=>{var _t,pt;n(rt)&&((_t=n(Fe).prevPeriod)!=null&&_t.label)&&((pt=n(Fe).diff)==null?void 0:pt.length)>0?me(Me):me(ye,-1)})}f(B,S)};z(Bn,B=>{n(Fe)&&B(Gn)})}L((B,S)=>{Ne(xt,1,`vw-text-section ${n(he).status==="stale"?"vw-text-section-stale":""}`,"svelte-1l2nqwu"),Ne(st,1,`vw-status-pill ${B??""}`,"svelte-1l2nqwu"),N(Tt,S)},[()=>ue(n(he).status),()=>O(n(he).status)]),f(Ze,xt)}),L(()=>N(Wt,`본문 ${n(p).sectionCount??""}개`)),f(jt,Ve)};z(mn,jt=>{var Ve,kr;((kr=(Ve=n(p))==null?void 0:Ve.sections)==null?void 0:kr.length)>0&&jt(ar)})}var An=m(mn,2);{var ns=jt=>{var Ve=mm();f(jt,Ve)};z(An,jt=>{n(Yt).length>0&&jt(ns)})}var hn=m(An,2);$e(hn,17,()=>n(Yt),Te,(jt,Ve)=>{var kr=be(),ca=Q(kr);{var Tn=Wt=>{const gt=G(()=>{var ze;return((ze=n(Ve).data)==null?void 0:ze.columns)||[]}),ur=G(()=>{var ze;return((ze=n(Ve).data)==null?void 0:ze.rows)||[]}),Kt=G(()=>n(Ve).meta||{}),Cr=G(()=>n(Kt).scaleDivisor||1);var Sr=_m(),fr=Q(Sr);{var Dr=ze=>{var Ye=hm(),st=d(Ye);L(()=>N(st,`(단위: ${n(Kt).scale??""})`)),f(ze,Ye)};z(fr,ze=>{n(Kt).scale&&ze(Dr)})}var Ze=m(fr,2),he=d(Ze),Fe=d(he),rt=d(Fe),xt=d(rt);$e(xt,21,()=>n(gt),Te,(ze,Ye,st)=>{const Tt=G(()=>/^\d{4}/.test(n(Ye)));var bt=gm(),pr=d(bt);L(()=>{Ne(bt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(Tt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${st===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),N(pr,n(Ye))}),f(ze,bt)});var vr=m(rt);$e(vr,21,()=>n(ur),Te,(ze,Ye,st)=>{var Tt=bm();Ne(Tt,1,`hover:bg-white/[0.03] ${st%2===1?"bg-white/[0.012]":""}`),$e(Tt,21,()=>n(gt),Te,(bt,pr,b)=>{const R=G(()=>n(Ye)[n(pr)]??""),de=G(()=>K(n(R))),_e=G(()=>qt(n(R))),Se=G(()=>n(de)?ot(n(R),n(Cr)):n(R));var Ae=xm(),re=d(Ae);L(()=>{Ne(Ae,1,`px-3 py-1.5 border-b border-white/[0.025]
																	${n(de)?"text-right tabular-nums font-mono text-[11.5px]":"whitespace-nowrap"}
																	${n(_e)?"text-red-400/60":n(de)?"text-dl-text/90":""}
																	${b===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]":"text-dl-text-muted"}
																	${b===0&&st%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),N(re,n(Se))}),f(bt,Ae)}),f(ze,Tt)}),f(Wt,Sr)},ua=Wt=>{const gt=G(()=>{var ze;return((ze=n(Ve).data)==null?void 0:ze.columns)||[]}),ur=G(()=>{var ze;return((ze=n(Ve).data)==null?void 0:ze.rows)||[]}),Kt=G(()=>n(Ve).meta||{}),Cr=G(()=>n(Kt).scaleDivisor||1);var Sr=Sm(),fr=Q(Sr);{var Dr=ze=>{var Ye=wm(),st=d(Ye);L(()=>N(st,`(단위: ${n(Kt).scale??""})`)),f(ze,Ye)};z(fr,ze=>{n(Kt).scale&&ze(Dr)})}var Ze=m(fr,2),he=d(Ze),Fe=d(he),rt=d(Fe),xt=d(rt);$e(xt,21,()=>n(gt),Te,(ze,Ye,st)=>{const Tt=G(()=>/^\d{4}/.test(n(Ye)));var bt=ym(),pr=d(bt);L(()=>{Ne(bt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(Tt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${st===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),N(pr,n(Ye))}),f(ze,bt)});var vr=m(rt);$e(vr,21,()=>n(ur),Te,(ze,Ye,st)=>{var Tt=Cm();Ne(Tt,1,`hover:bg-white/[0.03] ${st%2===1?"bg-white/[0.012]":""}`),$e(Tt,21,()=>n(gt),Te,(bt,pr,b)=>{const R=G(()=>n(Ye)[n(pr)]??""),de=G(()=>K(n(R))),_e=G(()=>qt(n(R))),Se=G(()=>n(de)?n(Cr)>1?ot(n(R),n(Cr)):nr(n(R)):n(R));var Ae=km(),re=d(Ae);L(()=>{Ne(Ae,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(de)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(_e)?"text-red-400/60":n(de)?"text-dl-text/90":""}
																	${b===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${b===0&&st%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),N(re,n(Se))}),f(bt,Ae)}),f(ze,Tt)}),f(Wt,Sr)},$n=Wt=>{const gt=G(()=>ht(Object.keys(n(Ve).rawMarkdown))),ur=G(()=>n(y).get(n(Ve).block)??0),Kt=G(()=>n(gt)[n(ur)]||n(gt)[0]);var Cr=Am(),Sr=d(Cr);{var fr=Fe=>{var rt=zm(),xt=d(rt);$e(xt,17,()=>n(gt).slice(0,8),Te,(Ye,st,Tt)=>{var bt=Mm(),pr=d(bt);L(()=>{Ne(bt,1,`px-2 py-0.5 rounded text-[10px] transition-colors
															${Tt===n(ur)?"bg-white/[0.08] text-dl-text font-medium":"text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]"}`),N(pr,n(st))}),oe("click",bt,()=>Z(n(Ve).block,Tt)),f(Ye,bt)});var vr=m(xt,2);{var ze=Ye=>{var st=Em(),Tt=d(st);L(()=>N(Tt,`외 ${n(gt).length-8}개`)),f(Ye,st)};z(vr,Ye=>{n(gt).length>8&&Ye(ze)})}f(Fe,rt)};z(Sr,Fe=>{n(gt).length>1&&Fe(fr)})}var Dr=m(Sr,2),Ze=d(Dr),he=d(Ze);ea(he,()=>Qa(n(Ve).rawMarkdown[n(Kt)])),f(Wt,Cr)},cr=Wt=>{const gt=G(()=>{var rt;return((rt=n(Ve).data)==null?void 0:rt.columns)||[]}),ur=G(()=>{var rt;return((rt=n(Ve).data)==null?void 0:rt.rows)||[]});var Kt=Pm(),Cr=d(Kt),Sr=d(Cr);Pi(Sr,{size:12,class:"text-emerald-400/50"});var fr=m(Cr,2),Dr=d(fr),Ze=d(Dr),he=d(Ze);$e(he,21,()=>n(gt),Te,(rt,xt,vr)=>{const ze=G(()=>/^\d{4}/.test(n(xt)));var Ye=Tm(),st=d(Ye);L(()=>{Ne(Ye,1,`px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															${n(ze)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
															${vr===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),N(st,n(xt))}),f(rt,Ye)});var Fe=m(Ze);$e(Fe,21,()=>n(ur),Te,(rt,xt,vr)=>{var ze=Im();Ne(ze,1,`hover:bg-white/[0.03] ${vr%2===1?"bg-white/[0.012]":""}`),$e(ze,21,()=>n(gt),Te,(Ye,st,Tt)=>{const bt=G(()=>n(xt)[n(st)]??""),pr=G(()=>K(n(bt))),b=G(()=>qt(n(bt)));var R=$m(),de=d(R);L(_e=>{Ne(R,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(pr)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(b)?"text-red-400/60":n(pr)?"text-dl-text/90":""}
																	${Tt===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Tt===0&&vr%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),N(de,_e)},[()=>n(pr)?nr(n(bt)):n(bt)]),f(Ye,R)}),f(rt,ze)}),f(Wt,Kt)},Fn=Wt=>{const gt=G(()=>n(Ve).data.columns),ur=G(()=>n(Ve).data.rows||[]);var Kt=Rm(),Cr=d(Kt),Sr=d(Cr),fr=d(Sr),Dr=d(fr);$e(Dr,21,()=>n(gt),Te,(he,Fe)=>{var rt=Nm(),xt=d(rt);L(()=>N(xt,n(Fe))),f(he,rt)});var Ze=m(fr);$e(Ze,21,()=>n(ur),Te,(he,Fe,rt)=>{var xt=Om();Ne(xt,1,`hover:bg-white/[0.03] ${rt%2===1?"bg-white/[0.012]":""}`),$e(xt,21,()=>n(gt),Te,(vr,ze)=>{var Ye=Lm(),st=d(Ye);L(()=>N(st,n(Fe)[n(ze)]??"")),f(vr,Ye)}),f(he,xt)}),f(Wt,Kt)};z(ca,Wt=>{var gt,ur;n(Ve).kind==="finance"?Wt(Tn):n(Ve).kind==="structured"?Wt(ua,1):n(Ve).kind==="raw_markdown"&&n(Ve).rawMarkdown?Wt($n,2):n(Ve).kind==="report"?Wt(cr,3):((ur=(gt=n(Ve).data)==null?void 0:gt.columns)==null?void 0:ur.length)>0&&Wt(Fn,4)})}f(jt,kr)}),f(Oe,zt)};z(ut,Oe=>{n(_)?Oe(Dt):Oe(Ut,-1)})}L(Oe=>{N(At,Oe),jn(J,"title",n(P)?"목차 표시":"전체화면")},[()=>q(n(l))]),oe("click",J,()=>u(P,!n(P))),f(et,Ot)};z(Ce,et=>{n(l)?et(ct,-1):et(it)})}f(g,V)},Lt=g=>{var V=Fm(),I=d(V);Rn(I,{size:36,strokeWidth:1,class:"opacity-20"}),f(g,V)};z(vt,g=>{var V;n(i)?g(yt):(V=n(s))!=null&&V.rows?g(Bt,1):g(Lt,-1)})}f(e,wt),rn()}la(["click"]);var Gm=h('<span class="text-[12px] font-semibold text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim"> </span>',1),Hm=h('<span class="text-[12px] font-semibold text-dl-text"> </span>'),Um=h('<span class="text-[12px] font-semibold text-dl-text">데이터</span>'),Wm=h('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" title="Excel 다운로드"><!></button> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button>',1),Km=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Ym=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed"> </pre>'),Xm=h('<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2"> </div>'),Jm=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Qm=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),Zm=h("<!> <!>",1),eh=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),th=h('<div class="p-4"><!></div>'),rh=h('<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">표시할 내용이 없습니다</div>'),nh=h('<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark"><div class="flex items-center justify-between h-10 mt-8 px-4 border-b border-dl-border/40 flex-shrink-0"><div class="flex items-center gap-2 min-w-0"><!></div> <div class="flex items-center gap-1"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 overflow-auto min-h-0"><!></div></div>');function ah(e,t){tn(t,!0);let r=at(t,"mode",3,null),a=at(t,"company",3,null),s=at(t,"data",3,null),i=at(t,"onTopicChange",3,null),o=at(t,"onFullscreen",3,null),l=at(t,"isFullscreen",3,!1),c=U(!1);async function v(){var O;if(!(!((O=a())!=null&&O.stockCode)||n(c))){u(c,!0);try{await Bu(a().stockCode)}catch(ue){console.error("Excel download error:",ue)}u(c,!1)}}function p(O){return O?/^\|.+\|$/m.test(O)||/^#{1,3} /m.test(O)||/\*\*[^*]+\*\*/m.test(O)||/```/.test(O):!1}var _=nh(),w=d(_),$=d(w),C=d($);{var P=O=>{var ue=Gm(),te=Q(ue),we=d(te),ke=m(te,2),Ie=d(ke);L(()=>{N(we,a().corpName||a().company),N(Ie,a().stockCode)}),f(O,ue)},y=O=>{var ue=Hm(),te=d(ue);L(()=>N(te,s().label)),f(O,ue)},x=O=>{var ue=Um();f(O,ue)};z(C,O=>{var ue;r()==="viewer"&&a()?O(P):r()==="data"&&((ue=s())!=null&&ue.label)?O(y,1):r()==="data"&&O(x,2)})}var T=m($,2),H=d(T);{var M=O=>{var ue=Wm(),te=Q(ue),we=d(te);{var ke=D=>{Xr(D,{size:14,class:"animate-spin"})},Ie=D=>{bs(D,{size:14})};z(we,D=>{n(c)?D(ke):D(Ie,-1)})}var ge=m(te,2),xe=d(ge);{var F=D=>{id(D,{size:14})},A=D=>{od(D,{size:14})};z(xe,D=>{l()?D(F):D(A,-1)})}L(()=>{te.disabled=n(c),jn(ge,"title",l()?"패널 모드로":"전체 화면")}),oe("click",te,v),oe("click",ge,()=>{var D;return(D=o())==null?void 0:D()}),f(O,ue)};z(H,O=>{var ue;r()==="viewer"&&((ue=a())!=null&&ue.stockCode)&&O(M)})}var q=m(H,2),ce=d(q);Vs(ce,{size:15});var ne=m(w,2),k=d(ne);{var X=O=>{Bm(O,{get stockCode(){return a().stockCode},get onTopicChange(){return i()}})},ee=O=>{var ue=th(),te=d(ue);{var we=ge=>{var xe=be(),F=Q(xe);{var A=ie=>{var ve=Km(),fe=d(ve);ea(fe,()=>Qa(s())),f(ie,ve)},D=G(()=>p(s())),ae=ie=>{var ve=Ym(),fe=d(ve);L(()=>N(fe,s())),f(ie,ve)};z(F,ie=>{n(D)?ie(A):ie(ae,-1)})}f(ge,xe)},ke=ge=>{var xe=Zm(),F=Q(xe);{var A=fe=>{var pe=Xm(),Ee=d(pe);L(()=>N(Ee,s().module)),f(fe,pe)};z(F,fe=>{s().module&&fe(A)})}var D=m(F,2);{var ae=fe=>{var pe=Jm(),Ee=d(pe);ea(Ee,()=>Qa(s().text)),f(fe,pe)},ie=G(()=>p(s().text)),ve=fe=>{var pe=Qm(),Ee=d(pe);L(()=>N(Ee,s().text)),f(fe,pe)};z(D,fe=>{n(ie)?fe(ae):fe(ve,-1)})}f(ge,xe)},Ie=ge=>{var xe=eh(),F=d(xe);L(A=>N(F,A),[()=>JSON.stringify(s(),null,2)]),f(ge,xe)};z(te,ge=>{var xe;typeof s()=="string"?ge(we):(xe=s())!=null&&xe.text?ge(ke,1):ge(Ie,-1)})}f(O,ue)},Z=O=>{var ue=rh();f(O,ue)};z(k,O=>{r()==="viewer"&&a()?O(X):r()==="data"&&s()?O(ee,1):O(Z,-1)})}oe("click",q,()=>{var O;return(O=t.onClose)==null?void 0:O.call(t)}),f(e,_),rn()}la(["click"]);var sh=h('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),oh=h("<!> <span>확인 중...</span>",1),ih=h("<!> <span>설정 필요</span>",1),lh=h('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),dh=h('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!>',1),ch=h('<div class="flex-shrink-0 border-l border-dl-border/30 transition-all duration-300"><!></div>'),uh=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),fh=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),vh=h('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),ph=h('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),mh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),hh=h('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),gh=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),xh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),bh=h('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),_h=h('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),wh=h('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),yh=h('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @anthropic-ai/claude-code</div></div></div>'),kh=h('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">인증</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">claude auth login</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">Claude Pro 또는 Max 구독이 필요합니다</span></div>',1),Ch=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2">설치 완료 후 새로고침하세요</div></div>'),Sh=h("<!> 브라우저에서 로그인 중...",1),Mh=h("<!> OpenAI 계정으로 로그인",1),Eh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2.5">ChatGPT 계정으로 로그인하여 사용하세요</div> <button class="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div></div>'),zh=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),Ah=h('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),Th=h("<button> <!></button>"),$h=h('<div class="flex flex-wrap gap-1.5"></div>'),Ih=h('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),Ph=h('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),Nh=h('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),Lh=h('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),Oh=h('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),Rh=h('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),Dh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),jh=h("<!> <!> <!> <!> <!> <!> <!>",1),Vh=h('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),Fh=h('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),qh=h('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),Bh=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><span class="text-[10px] text-dl-text-dim">공시 보기</span> <!></div></button>'),Gh=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div></div> <!>',1),Hh=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div></button>'),Uh=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div></div> <!>',1),Wh=h('<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),Kh=h('<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim"><!> <div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div> <div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div></div>'),Yh=h('<div class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn" role="presentation"><div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"><div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"/> <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div> <div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim"><span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span></div></div></div>'),Xh=h('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),Jh=h('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-2 left-3 z-20 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="종목 검색 (Ctrl+K)"><!></button> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <button><!> <!></button></div> <div class="flex flex-1 min-h-0"><div class="min-w-0 flex-1 flex flex-col"><!></div> <!></div></div></div>  <!> <!> <!> <!>',1);function Qh(e,t){tn(t,!0);let r=U(""),a=U(!1),s=U(null),i=U(St({})),o=U(St({})),l=U(null),c=U(null),v=U(St([])),p=U(!1),_=U(0),w=U(!0),$=U(""),C=U(!1),P=U(null),y=U(St({})),x=U(St({})),T=U(""),H=U(!1),M=U(null),q=U(""),ce=U(!1),ne=U(""),k=U(0),X=U(null),ee=U(!1),Z=U(St({})),O=U(null),ue=U(null);const te=Gf();let we=U(!1),ke=G(()=>n(we)?"100%":te.panelMode==="viewer"?"65%":"50%"),Ie=U(!1),ge=U(""),xe=U(St([])),F=U(-1),A=null,D=U(!1);function ae(){u(D,window.innerWidth<=768),n(D)&&(u(p,!1),te.closePanel())}Zn(()=>(ae(),window.addEventListener("resize",ae),()=>window.removeEventListener("resize",ae))),Zn(()=>{!n(C)||!n(O)||requestAnimationFrame(()=>{var b;return(b=n(O))==null?void 0:b.focus()})}),Zn(()=>{!n(ie)||!n(ue)||requestAnimationFrame(()=>{var b;return(b=n(ue))==null?void 0:b.focus()})});let ie=U(null),ve=U(""),fe=U("error"),pe=U(!1);function Ee(b,R="error",de=4e3){u(ve,b,!0),u(fe,R,!0),u(pe,!0),setTimeout(()=>{u(pe,!1)},de)}const K=Vf();Zn(()=>{nr()});let qt=U(St({})),ot=U(St({}));async function nr(){var b,R,de;u(w,!0);try{const _e=await Ru();u(i,_e.providers||{},!0),u(o,_e.ollama||{},!0),u(qt,_e.codex||{},!0),u(ot,_e.claudeCode||{},!0),u(Z,_e.chatgpt||{},!0),_e.version&&u($,_e.version,!0);const Se=localStorage.getItem("dartlab-provider"),Ae=localStorage.getItem("dartlab-model");if(Se&&((b=n(i)[Se])!=null&&b.available)){u(l,Se,!0),u(P,Se,!0),await Na(Se,Ae),await Ue(Se);const re=n(y)[Se]||[];Ae&&re.includes(Ae)?u(c,Ae,!0):re.length>0&&(u(c,re[0],!0),localStorage.setItem("dartlab-model",n(c))),u(v,re,!0),u(w,!1);return}if(Se&&n(i)[Se]){u(l,Se,!0),u(P,Se,!0),await Ue(Se);const re=n(y)[Se]||[];u(v,re,!0),Ae&&re.includes(Ae)?u(c,Ae,!0):re.length>0&&u(c,re[0],!0),u(w,!1);return}for(const re of["chatgpt","codex","ollama"])if((R=n(i)[re])!=null&&R.available){u(l,re,!0),u(P,re,!0),await Na(re),await Ue(re);const Xt=n(y)[re]||[];u(v,Xt,!0),u(c,((de=n(i)[re])==null?void 0:de.model)||(Xt.length>0?Xt[0]:null),!0),n(c)&&localStorage.setItem("dartlab-model",n(c));break}}catch{}u(w,!1)}async function Ue(b){u(x,{...n(x),[b]:!0},!0);try{const R=await Du(b);u(y,{...n(y),[b]:R.models||[]},!0)}catch{u(y,{...n(y),[b]:[]},!0)}u(x,{...n(x),[b]:!1},!0)}async function Pe(b){var de;u(l,b,!0),u(c,null),u(P,b,!0),localStorage.setItem("dartlab-provider",b),localStorage.removeItem("dartlab-model"),u(T,""),u(M,null);try{await Na(b)}catch{}await Ue(b);const R=n(y)[b]||[];if(u(v,R,!0),R.length>0){u(c,((de=n(i)[b])==null?void 0:de.model)||R[0],!0),localStorage.setItem("dartlab-model",n(c));try{await Na(b,n(c))}catch{}}}async function ht(b){u(c,b,!0),localStorage.setItem("dartlab-model",b);try{await Na(n(l),b)}catch{}}function Yt(b){n(P)===b?u(P,null):(u(P,b,!0),Ue(b))}async function wt(){const b=n(T).trim();if(!(!b||!n(l))){u(H,!0),u(M,null);try{const R=await Na(n(l),n(c),b);R.available?(u(M,"success"),n(i)[n(l)]={...n(i)[n(l)],available:!0,model:R.model},!n(c)&&R.model&&u(c,R.model,!0),await Ue(n(l)),u(v,n(y)[n(l)]||[],!0),Ee("API 키 인증 성공","success")):u(M,"error")}catch{u(M,"error")}u(H,!1)}}async function vt(){if(!n(ee)){u(ee,!0);try{const{authUrl:b}=await Vu();window.open(b,"dartlab-oauth","width=600,height=700");const R=setInterval(async()=>{var de;try{const _e=await Fu();_e.done&&(clearInterval(R),u(ee,!1),_e.error?Ee(`인증 실패: ${_e.error}`):(Ee("ChatGPT 인증 성공","success"),await nr(),(de=n(i).chatgpt)!=null&&de.available&&await Pe("chatgpt")))}catch{clearInterval(R),u(ee,!1)}},2e3);setTimeout(()=>{clearInterval(R),n(ee)&&(u(ee,!1),Ee("인증 시간이 초과되었습니다. 다시 시도해주세요."))},12e4)}catch(b){u(ee,!1),Ee(`OAuth 시작 실패: ${b.message}`)}}}async function yt(){try{await qu(),u(Z,{authenticated:!1},!0),n(l)==="chatgpt"&&u(i,{...n(i),chatgpt:{...n(i).chatgpt,available:!1}},!0),Ee("ChatGPT 로그아웃 완료","success"),await nr()}catch{Ee("로그아웃 실패")}}function Bt(){const b=n(q).trim();!b||n(ce)||(u(ce,!0),u(ne,"준비 중..."),u(k,0),u(X,ju(b,{onProgress(R){R.total&&R.completed!==void 0?(u(k,Math.round(R.completed/R.total*100),!0),u(ne,`다운로드 중... ${n(k)}%`)):R.status&&u(ne,R.status,!0)},async onDone(){u(ce,!1),u(X,null),u(q,""),u(ne,""),u(k,0),Ee(`${b} 다운로드 완료`,"success"),await Ue("ollama"),u(v,n(y).ollama||[],!0),n(v).includes(b)&&await ht(b)},onError(R){u(ce,!1),u(X,null),u(ne,""),u(k,0),Ee(`다운로드 실패: ${R}`)}}),!0))}function Lt(){n(X)&&(n(X).abort(),u(X,null)),u(ce,!1),u(q,""),u(ne,""),u(k,0)}function g(){u(p,!n(p))}function V(b){te.openData(b)}function I(b){te.openViewer(b)}function W(){if(u(T,""),u(M,null),n(l))u(P,n(l),!0);else{const b=Object.keys(n(i));u(P,b.length>0?b[0]:null,!0)}u(C,!0),n(P)&&Ue(n(P))}function j(b){var R,de,_e,Se;if(b)for(let Ae=b.messages.length-1;Ae>=0;Ae--){const re=b.messages[Ae];if(re.role==="assistant"&&((R=re.meta)!=null&&R.stockCode||(de=re.meta)!=null&&de.company||re.company)){te.syncCompanyFromMessage({company:((_e=re.meta)==null?void 0:_e.company)||re.company,stockCode:(Se=re.meta)==null?void 0:Se.stockCode},te.selectedCompany);return}}}function Ce(){K.createConversation(),u(r,""),u(a,!1),n(s)&&(n(s).abort(),u(s,null))}function it(b){K.setActive(b),j(K.active),u(r,""),u(a,!1),n(s)&&(n(s).abort(),u(s,null))}function ct(b){u(ie,b,!0)}function et(){n(ie)&&(K.deleteConversation(n(ie)),u(ie,null))}function Ot(){var R;const b=K.active;if(!b)return null;for(let de=b.messages.length-1;de>=0;de--){const _e=b.messages[de];if(_e.role==="assistant"&&((R=_e.meta)!=null&&R.stockCode))return _e.meta.stockCode}return null}async function Rt(){var gn,qn,Bn,Gn;const b=n(r).trim();if(!b||n(a))return;if(!n(l)||!((gn=n(i)[n(l)])!=null&&gn.available)){Ee("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),W();return}K.activeId||K.createConversation();const R=K.activeId;K.addMessage("user",b),u(r,""),u(a,!0),K.addMessage("assistant",""),K.updateLastMessage({loading:!0,startedAt:Date.now()}),ms(_);const de=K.active,_e=[];let Se=null;if(de){const B=de.messages.slice(0,-2);for(const S of B)if((S.role==="user"||S.role==="assistant")&&S.text&&S.text.trim()&&!S.error&&!S.loading){const Y={role:S.role,text:S.text};S.role==="assistant"&&((qn=S.meta)!=null&&qn.stockCode)&&(Y.meta={company:S.meta.company||S.company,stockCode:S.meta.stockCode,modules:S.meta.includedModules||null},Se=S.meta.stockCode),_e.push(Y)}}const Ae=((Bn=te.selectedCompany)==null?void 0:Bn.stockCode)||Se||Ot(),re=te.getViewContext();let Xt=b;if((re==null?void 0:re.type)==="viewer"&&re.company){let B=`
[사용자가 현재 ${re.company.corpName}(${re.company.stockCode}) 공시를 보고 있습니다`;re.topic&&(B+=` — 현재 섹션: ${re.topicLabel||re.topic}(${re.topic})`),B+="]",Xt+=B}else(re==null?void 0:re.type)==="data"&&((Gn=re.data)!=null&&Gn.label)&&(Xt+=`
[사용자가 현재 "${re.data.label}" 데이터를 보고 있습니다]`);function sr(){return K.activeId!==R}const In=Uu(Ae,Xt,{provider:n(l),model:n(c)},{onMeta(B){var me;if(sr())return;const S=K.active,Y=S==null?void 0:S.messages[S.messages.length-1],ye={meta:{...(Y==null?void 0:Y.meta)||{},...B}};B.company&&(ye.company=B.company,K.activeId&&((me=K.active)==null?void 0:me.title)==="새 대화"&&K.updateTitle(K.activeId,B.company)),B.stockCode&&(ye.stockCode=B.stockCode),(B.company||B.stockCode)&&te.syncCompanyFromMessage(B,te.selectedCompany),K.updateLastMessage(ye)},onSnapshot(B){sr()||K.updateLastMessage({snapshot:B})},onContext(B){if(sr())return;const S=K.active;if(!S)return;const Y=S.messages[S.messages.length-1],Me=(Y==null?void 0:Y.contexts)||[];K.updateLastMessage({contexts:[...Me,{module:B.module,label:B.label,text:B.text}]})},onSystemPrompt(B){sr()||K.updateLastMessage({systemPrompt:B.text,userContent:B.userContent||null})},onToolCall(B){if(sr())return;const S=K.active;if(!S)return;const Y=S.messages[S.messages.length-1],Me=(Y==null?void 0:Y.toolEvents)||[];K.updateLastMessage({toolEvents:[...Me,{type:"call",name:B.name,arguments:B.arguments}]})},onToolResult(B){if(sr())return;const S=K.active;if(!S)return;const Y=S.messages[S.messages.length-1],Me=(Y==null?void 0:Y.toolEvents)||[];K.updateLastMessage({toolEvents:[...Me,{type:"result",name:B.name,result:B.result}]})},onChunk(B){if(sr())return;const S=K.active;if(!S)return;const Y=S.messages[S.messages.length-1];K.updateLastMessage({text:((Y==null?void 0:Y.text)||"")+B}),ms(_)},onDone(){if(sr())return;const B=K.active,S=B==null?void 0:B.messages[B.messages.length-1],Y=S!=null&&S.startedAt?((Date.now()-S.startedAt)/1e3).toFixed(1):null;K.updateLastMessage({loading:!1,duration:Y}),K.flush(),u(a,!1),u(s,null),ms(_)},onError(B,S,Y){sr()||(K.updateLastMessage({text:`오류: ${B}`,loading:!1,error:!0}),K.flush(),S==="relogin"||S==="login"?(Ee(`${B} — 설정에서 재로그인하세요`),W()):Ee(S==="check_headers"||S==="check_endpoint"||S==="check_client_id"?`${B} — ChatGPT API 변경 감지. 업데이트를 확인하세요`:S==="rate_limit"?"요청이 너무 많습니다. 잠시 후 다시 시도해주세요":B),u(a,!1),u(s,null))}},_e);u(s,In,!0)}function Rr(){n(s)&&(n(s).abort(),u(s,null),u(a,!1),K.updateLastMessage({loading:!1}),K.flush())}function Br(){const b=K.active;if(!b||b.messages.length<2)return;let R="";for(let de=b.messages.length-1;de>=0;de--)if(b.messages[de].role==="user"){R=b.messages[de].text;break}R&&(K.removeLastMessage(),K.removeLastMessage(),u(r,R,!0),requestAnimationFrame(()=>{Rt()}))}function zn(){const b=K.active;if(!b)return;let R=`# ${b.title}

`;for(const Ae of b.messages)Ae.role==="user"?R+=`## You

${Ae.text}

`:Ae.role==="assistant"&&Ae.text&&(R+=`## DartLab

${Ae.text}

`);const de=new Blob([R],{type:"text/markdown;charset=utf-8"}),_e=URL.createObjectURL(de),Se=document.createElement("a");Se.href=_e,Se.download=`${b.title||"dartlab-chat"}.md`,Se.click(),URL.revokeObjectURL(_e),Ee("대화가 마크다운으로 내보내졌습니다","success")}function tt(){u(Ie,!0),u(ge,""),u(xe,[],!0),u(F,-1)}function Je(b){(b.metaKey||b.ctrlKey)&&b.key==="n"&&(b.preventDefault(),Ce()),(b.metaKey||b.ctrlKey)&&b.key==="k"&&(b.preventDefault(),tt()),(b.metaKey||b.ctrlKey)&&b.shiftKey&&b.key==="S"&&(b.preventDefault(),g()),b.key==="Escape"&&n(Ie)?u(Ie,!1):b.key==="Escape"&&n(C)?u(C,!1):b.key==="Escape"&&n(ie)?u(ie,null):b.key==="Escape"&&te.panelOpen&&te.closePanel()}let At=G(()=>{var b;return((b=K.active)==null?void 0:b.messages)||[]}),J=G(()=>K.active&&K.active.messages.length>0),je=G(()=>{var b;return!n(w)&&(!n(l)||!((b=n(i)[n(l)])!=null&&b.available))});const lt=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var Qe=Jh();Ra("keydown",yo,Je);var ut=Q(Qe),Dt=d(ut);{var Ut=b=>{var R=sh();oe("click",R,()=>{u(p,!1)}),f(b,R)};z(Dt,b=>{n(D)&&n(p)&&b(Ut)})}var Oe=m(Dt,2),zt=d(Oe);{let b=G(()=>n(D)?!0:n(p));Ev(zt,{get conversations(){return K.conversations},get activeId(){return K.activeId},get open(){return n(b)},get version(){return n($)},onNewChat:()=>{Ce(),n(D)&&u(p,!1)},onSelect:R=>{it(R),n(D)&&u(p,!1)},onDelete:ct,onOpenSearch:tt})}var yr=m(Oe,2),Er=d(yr),mn=d(Er),ar=d(mn);{var An=b=>{uv(b,{size:18})},ns=b=>{cv(b,{size:18})};z(ar,b=>{n(p)?b(An):b(ns,-1)})}var hn=m(Er,2),jt=d(hn),Ve=d(jt);_s(Ve,{size:14});var kr=m(jt,2),ca=d(kr);Rn(ca,{size:14});var Tn=m(kr,2),ua=d(Tn);iv(ua,{size:14});var $n=m(Tn,2),cr=d($n);sv(cr,{size:14});var Fn=m($n,2),Wt=d(Fn);{var gt=b=>{var R=oh(),de=Q(R);Xr(de,{size:12,class:"animate-spin"}),f(b,R)},ur=b=>{var R=ih(),de=Q(R);La(de,{size:12}),f(b,R)},Kt=b=>{var R=dh(),de=m(Q(R),2),_e=d(de),Se=m(de,2);{var Ae=re=>{var Xt=lh(),sr=m(Q(Xt),2),In=d(sr);L(()=>N(In,n(c))),f(re,Xt)};z(Se,re=>{n(c)&&re(Ae)})}L(()=>N(_e,n(l))),f(b,R)};z(Wt,b=>{n(w)?b(gt):n(je)?b(ur,1):b(Kt,-1)})}var Cr=m(Wt,2);vv(Cr,{size:12});var Sr=m(hn,2),fr=d(Sr),Dr=d(fr);{var Ze=b=>{Tp(b,{get messages(){return n(At)},get isLoading(){return n(a)},get scrollTrigger(){return n(_)},get selectedCompany(){return te.selectedCompany},onSend:Rt,onStop:Rr,onRegenerate:Br,onExport:zn,onOpenData:V,onCompanySelect:I,get inputText(){return n(r)},set inputText(R){u(r,R,!0)}})},he=b=>{Lv(b,{onSend:Rt,onCompanySelect:I,get inputText(){return n(r)},set inputText(R){u(r,R,!0)}})};z(Dr,b=>{n(J)?b(Ze):b(he,-1)})}var Fe=m(fr,2);{var rt=b=>{var R=ch(),de=d(R);ah(de,{get mode(){return te.panelMode},get company(){return te.selectedCompany},get data(){return te.panelData},onClose:()=>{u(we,!1),te.closePanel()},onTopicChange:(_e,Se)=>te.setViewerTopic(_e,Se),onFullscreen:()=>{u(we,!n(we))},get isFullscreen(){return n(we)}}),L(()=>zo(R,`width: ${n(ke)??""}; min-width: 360px; ${n(we)?"":"max-width: 75vw;"}`)),f(b,R)};z(Fe,b=>{!n(D)&&te.panelOpen&&b(rt)})}var xt=m(ut,2);{var vr=b=>{var R=Fh(),de=d(R),_e=d(de),Se=d(_e),Ae=m(d(Se),2),re=d(Ae);Vs(re,{size:18});var Xt=m(_e,2),sr=d(Xt);$e(sr,21,()=>Object.entries(n(i)),Te,(S,Y)=>{var Me=G(()=>Hi(n(Y),2));let ye=()=>n(Me)[0],me=()=>n(Me)[1];const _t=G(()=>ye()===n(l)),pt=G(()=>n(P)===ye()),ft=G(()=>me().auth==="api_key"),Vt=G(()=>me().auth==="cli"),$t=G(()=>n(y)[ye()]||[]),Tr=G(()=>n(x)[ye()]);var mt=Vh(),or=d(mt),Jt=d(or),kt=m(Jt,2),Ft=d(kt),Gr=d(Ft),Ys=d(Gr),dd=m(Gr,2);{var cd=Qt=>{var Hr=uh();f(Qt,Hr)};z(dd,Qt=>{n(_t)&&Qt(cd)})}var ud=m(Ft,2),fd=d(ud),vd=m(kt,2),pd=d(vd);{var md=Qt=>{xs(Qt,{size:16,class:"text-dl-success"})},hd=Qt=>{var Hr=fh(),$a=Q(Hr);Li($a,{size:14,class:"text-amber-400"}),f(Qt,Hr)},gd=Qt=>{var Hr=vh(),$a=Q(Hr);mv($a,{size:14,class:"text-dl-text-dim"}),f(Qt,Hr)};z(pd,Qt=>{me().available?Qt(md):n(ft)?Qt(hd,1):n(Vt)&&!me().available&&Qt(gd,2)})}var xd=m(or,2);{var bd=Qt=>{var Hr=jh(),$a=Q(Hr);{var _d=dt=>{var It=mh(),Gt=d(It),mr=d(Gt),$r=m(Gt,2),Pt=d($r),hr=m(Pt,2),jr=d(hr);{var Mr=nt=>{Xr(nt,{size:12,class:"animate-spin"})},Nt=nt=>{Li(nt,{size:12})};z(jr,nt=>{n(H)?nt(Mr):nt(Nt,-1)})}var ir=m($r,2);{var Ct=nt=>{var zr=ph(),Zt=d(zr);La(Zt,{size:12}),f(nt,zr)};z(ir,nt=>{n(M)==="error"&&nt(Ct)})}L(nt=>{N(mr,me().envKey?`환경변수 ${me().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),jn(Pt,"placeholder",ye()==="openai"?"sk-...":ye()==="claude"?"sk-ant-...":"API Key"),hr.disabled=nt},[()=>!n(T).trim()||n(H)]),oe("keydown",Pt,nt=>{nt.key==="Enter"&&wt()}),Oa(Pt,()=>n(T),nt=>u(T,nt)),oe("click",hr,wt),f(dt,It)};z($a,dt=>{n(ft)&&!me().available&&dt(_d)})}var Yo=m($a,2);{var wd=dt=>{var It=gh(),Gt=d(It),mr=d(Gt);xs(mr,{size:13,class:"text-dl-success"});var $r=m(Gt,2),Pt=d($r),hr=m(Pt,2);{var jr=Nt=>{var ir=hh(),Ct=d(ir);{var nt=Zt=>{Xr(Zt,{size:10,class:"animate-spin"})},zr=Zt=>{var Ur=gs("변경");f(Zt,Ur)};z(Ct,Zt=>{n(H)?Zt(nt):Zt(zr,-1)})}L(()=>ir.disabled=n(H)),oe("click",ir,wt),f(Nt,ir)},Mr=G(()=>n(T).trim());z(hr,Nt=>{n(Mr)&&Nt(jr)})}oe("keydown",Pt,Nt=>{Nt.key==="Enter"&&wt()}),Oa(Pt,()=>n(T),Nt=>u(T,Nt)),f(dt,It)};z(Yo,dt=>{n(ft)&&me().available&&dt(wd)})}var Xo=m(Yo,2);{var yd=dt=>{var It=xh(),Gt=m(d(It),2),mr=d(Gt);bs(mr,{size:14});var $r=m(mr,2);Ni($r,{size:10,class:"ml-auto"}),f(dt,It)},kd=dt=>{var It=bh(),Gt=d(It),mr=d(Gt);La(mr,{size:14}),f(dt,It)};z(Xo,dt=>{ye()==="ollama"&&!n(o).installed?dt(yd):ye()==="ollama"&&n(o).installed&&!n(o).running&&dt(kd,1)})}var Jo=m(Xo,2);{var Cd=dt=>{var It=Ch(),Gt=d(It);{var mr=Pt=>{var hr=wh(),jr=Q(hr),Mr=d(jr),Nt=m(jr,2),ir=d(Nt);{var Ct=an=>{var fa=_h();f(an,fa)};z(ir,an=>{n(qt).installed||an(Ct)})}var nt=m(ir,2),zr=d(nt),Zt=d(zr),Ur=m(Nt,2),Hn=d(Ur);La(Hn,{size:12,class:"text-amber-400 flex-shrink-0"}),L(()=>{N(Mr,n(qt).installed?"Codex CLI가 설치되었지만 인증이 필요합니다":"Codex CLI 설치가 필요합니다"),N(Zt,n(qt).installed?"1.":"2.")}),f(Pt,hr)},$r=Pt=>{var hr=kh(),jr=Q(hr),Mr=d(jr),Nt=m(jr,2),ir=d(Nt);{var Ct=an=>{var fa=yh();f(an,fa)};z(ir,an=>{n(ot).installed||an(Ct)})}var nt=m(ir,2),zr=d(nt),Zt=d(zr),Ur=m(Nt,2),Hn=d(Ur);La(Hn,{size:12,class:"text-amber-400 flex-shrink-0"}),L(()=>{N(Mr,n(ot).installed&&!n(ot).authenticated?"Claude Code가 설치되었지만 인증이 필요합니다":"Claude Code CLI 설치가 필요합니다"),N(Zt,n(ot).installed?"1.":"2.")}),f(Pt,hr)};z(Gt,Pt=>{ye()==="codex"?Pt(mr):ye()==="claude-code"&&Pt($r,1)})}f(dt,It)};z(Jo,dt=>{n(Vt)&&!me().available&&dt(Cd)})}var Qo=m(Jo,2);{var Sd=dt=>{var It=Eh(),Gt=m(d(It),2),mr=d(Gt);{var $r=Mr=>{var Nt=Sh(),ir=Q(Nt);Xr(ir,{size:14,class:"animate-spin"}),f(Mr,Nt)},Pt=Mr=>{var Nt=Mh(),ir=Q(Nt);lv(ir,{size:14}),f(Mr,Nt)};z(mr,Mr=>{n(ee)?Mr($r):Mr(Pt,-1)})}var hr=m(Gt,2),jr=d(hr);La(jr,{size:12,class:"text-amber-400 flex-shrink-0"}),L(()=>Gt.disabled=n(ee)),oe("click",Gt,vt),f(dt,It)};z(Qo,dt=>{me().auth==="oauth"&&!me().available&&dt(Sd)})}var Zo=m(Qo,2);{var Md=dt=>{var It=zh(),Gt=d(It),mr=d(Gt),$r=d(mr);xs($r,{size:13,class:"text-dl-success"});var Pt=m(mr,2),hr=d(Pt);dv(hr,{size:11}),oe("click",Pt,yt),f(dt,It)};z(Zo,dt=>{me().auth==="oauth"&&me().available&&dt(Md)})}var Ed=m(Zo,2);{var zd=dt=>{var It=Dh(),Gt=d(It),mr=m(d(Gt),2);{var $r=Ct=>{Xr(Ct,{size:12,class:"animate-spin text-dl-text-dim"})};z(mr,Ct=>{n(Tr)&&Ct($r)})}var Pt=m(Gt,2);{var hr=Ct=>{var nt=Ah(),zr=d(nt);Xr(zr,{size:14,class:"animate-spin"}),f(Ct,nt)},jr=Ct=>{var nt=$h();$e(nt,21,()=>n($t),Te,(zr,Zt)=>{var Ur=Th(),Hn=d(Ur),an=m(Hn);{var fa=Wr=>{ev(Wr,{size:10,class:"inline ml-1"})};z(an,Wr=>{n(Zt)===n(c)&&n(_t)&&Wr(fa)})}L(Wr=>{Ne(Ur,1,Wr),N(Hn,`${n(Zt)??""} `)},[()=>Mt(Et("px-3 py-1.5 rounded-lg text-[11px] border transition-all",n(Zt)===n(c)&&n(_t)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),oe("click",Ur,()=>{ye()!==n(l)&&Pe(ye()),ht(n(Zt))}),f(zr,Ur)}),f(Ct,nt)},Mr=Ct=>{var nt=Ih();f(Ct,nt)};z(Pt,Ct=>{n(Tr)&&n($t).length===0?Ct(hr):n($t).length>0?Ct(jr,1):Ct(Mr,-1)})}var Nt=m(Pt,2);{var ir=Ct=>{var nt=Rh(),zr=d(nt),Zt=m(d(zr),2),Ur=m(d(Zt));Ni(Ur,{size:9});var Hn=m(zr,2);{var an=Wr=>{var as=Ph(),ss=d(as),Ia=d(ss),os=d(Ia);Xr(os,{size:12,class:"animate-spin text-dl-primary-light"});var Xs=m(Ia,2),As=m(ss,2),Pn=d(As),sn=m(As,2),Js=d(sn);L(()=>{zo(Pn,`width: ${n(k)??""}%`),N(Js,n(ne))}),oe("click",Xs,Lt),f(Wr,as)},fa=Wr=>{var as=Oh(),ss=Q(as),Ia=d(ss),os=m(Ia,2),Xs=d(os);bs(Xs,{size:12});var As=m(ss,2);$e(As,21,()=>lt,Te,(Pn,sn)=>{const Js=G(()=>n($t).some(Pa=>Pa===n(sn).name||Pa===n(sn).name.split(":")[0]));var ei=be(),Ad=Q(ei);{var Td=Pa=>{var Qs=Lh(),ti=d(Qs),ri=d(ti),ni=d(ri),$d=d(ni),ai=m(ni,2),Id=d(ai),Pd=m(ai,2);{var Nd=Zs=>{var oi=Nh(),Vd=d(oi);L(()=>N(Vd,n(sn).tag)),f(Zs,oi)};z(Pd,Zs=>{n(sn).tag&&Zs(Nd)})}var Ld=m(ri,2),Od=d(Ld),Rd=m(ti,2),si=d(Rd),Dd=d(si),jd=m(si,2);bs(jd,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),L(()=>{N($d,n(sn).name),N(Id,n(sn).size),N(Od,n(sn).desc),N(Dd,`${n(sn).gb??""} GB`)}),oe("click",Qs,()=>{u(q,n(sn).name,!0),Bt()}),f(Pa,Qs)};z(Ad,Pa=>{n(Js)||Pa(Td)})}f(Pn,ei)}),L(Pn=>os.disabled=Pn,[()=>!n(q).trim()]),oe("keydown",Ia,Pn=>{Pn.key==="Enter"&&Bt()}),Oa(Ia,()=>n(q),Pn=>u(q,Pn)),oe("click",os,Bt),f(Wr,as)};z(Hn,Wr=>{n(ce)?Wr(an):Wr(fa,-1)})}f(Ct,nt)};z(Nt,Ct=>{ye()==="ollama"&&Ct(ir)})}f(dt,It)};z(Ed,dt=>{(me().available||n(ft)||n(Vt)||me().auth==="oauth")&&dt(zd)})}f(Qt,Hr)};z(xd,Qt=>{(n(pt)||n(_t))&&Qt(bd)})}L((Qt,Hr)=>{Ne(mt,1,Qt),Ne(Jt,1,Hr),N(Ys,me().label||ye()),N(fd,me().desc||"")},[()=>Mt(Et("rounded-xl border transition-all",n(_t)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>Mt(Et("w-2.5 h-2.5 rounded-full flex-shrink-0",me().available?"bg-dl-success":n(ft)?"bg-amber-400":"bg-dl-text-dim"))]),oe("click",or,()=>{me().available||n(ft)?ye()===n(l)?Yt(ye()):Pe(ye()):Yt(ye())}),f(S,mt)});var In=m(Xt,2),gn=d(In),qn=d(gn);{var Bn=S=>{var Y=gs();L(()=>{var Me;return N(Y,`현재: ${(((Me=n(i)[n(l)])==null?void 0:Me.label)||n(l))??""} / ${n(c)??""}`)}),f(S,Y)},Gn=S=>{var Y=gs();L(()=>{var Me;return N(Y,`현재: ${(((Me=n(i)[n(l)])==null?void 0:Me.label)||n(l))??""}`)}),f(S,Y)};z(qn,S=>{n(l)&&n(c)?S(Bn):n(l)&&S(Gn,1)})}var B=m(gn,2);Ja(de,S=>u(O,S),()=>n(O)),oe("click",R,S=>{S.target===S.currentTarget&&u(C,!1)}),oe("click",Ae,()=>u(C,!1)),oe("click",B,()=>u(C,!1)),f(b,R)};z(xt,b=>{n(C)&&b(vr)})}var ze=m(xt,2);{var Ye=b=>{var R=qh(),de=d(R),_e=m(d(de),4),Se=d(_e),Ae=m(Se,2);Ja(de,re=>u(ue,re),()=>n(ue)),oe("click",R,re=>{re.target===re.currentTarget&&u(ie,null)}),oe("click",Se,()=>u(ie,null)),oe("click",Ae,et),f(b,R)};z(ze,b=>{n(ie)&&b(Ye)})}var st=m(ze,2);{var Tt=b=>{const R=G(()=>te.recentCompanies||[]);var de=Yh(),_e=d(de),Se=d(_e),Ae=d(Se);_s(Ae,{size:18,class:"text-dl-text-dim flex-shrink-0"});var re=m(Ae,2);xl(re,!0);var Xt=m(Se,2),sr=d(Xt);{var In=S=>{var Y=Gh(),Me=m(Q(Y),2);$e(Me,17,()=>n(xe),Te,(ye,me,_t)=>{var pt=Bh(),ft=d(pt),Vt=d(ft),$t=m(ft,2),Tr=d($t),mt=d(Tr),or=m(Tr,2),Jt=d(or),kt=m($t,2),Ft=m(d(kt),2);Rn(Ft,{size:14,class:"text-dl-text-dim"}),L((Gr,Ys)=>{Ne(pt,1,Gr),N(Vt,Ys),N(mt,n(me).corpName),N(Jt,`${n(me).stockCode??""} · ${(n(me).market||"")??""}${n(me).sector?` · ${n(me).sector}`:""}`)},[()=>Mt(Et("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",_t===n(F)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(me).corpName||"?").charAt(0)]),oe("click",pt,()=>{u(Ie,!1),u(ge,""),u(xe,[],!0),u(F,-1),I(n(me))}),Ra("mouseenter",pt,()=>{u(F,_t,!0)}),f(ye,pt)}),f(S,Y)},gn=S=>{var Y=Uh(),Me=m(Q(Y),2);$e(Me,17,()=>n(R),Te,(ye,me,_t)=>{var pt=Hh(),ft=d(pt),Vt=d(ft),$t=m(ft,2),Tr=d($t),mt=d(Tr),or=m(Tr,2),Jt=d(or);L((kt,Ft)=>{Ne(pt,1,kt),N(Vt,Ft),N(mt,n(me).corpName),N(Jt,`${n(me).stockCode??""} · ${(n(me).market||"")??""}`)},[()=>Mt(Et("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",_t===n(F)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(me).corpName||"?").charAt(0)]),oe("click",pt,()=>{u(Ie,!1),u(ge,""),u(F,-1),I(n(me))}),Ra("mouseenter",pt,()=>{u(F,_t,!0)}),f(ye,pt)}),f(S,Y)},qn=G(()=>n(ge).trim().length===0&&n(R).length>0),Bn=S=>{var Y=Wh();f(S,Y)},Gn=G(()=>n(ge).trim().length>0),B=S=>{var Y=Kh(),Me=d(Y);_s(Me,{size:24,class:"mb-2 opacity-40"}),f(S,Y)};z(sr,S=>{n(xe).length>0?S(In):n(qn)?S(gn,1):n(Gn)?S(Bn,2):S(B,-1)})}oe("click",de,S=>{S.target===S.currentTarget&&u(Ie,!1)}),oe("input",re,()=>{A&&clearTimeout(A),n(ge).trim().length>=1?A=setTimeout(async()=>{var S;try{const Y=await Bl(n(ge).trim());u(xe,((S=Y.results)==null?void 0:S.slice(0,8))||[],!0)}catch{u(xe,[],!0)}},250):u(xe,[],!0)}),oe("keydown",re,S=>{const Y=n(xe).length>0?n(xe):n(R);if(S.key==="ArrowDown")S.preventDefault(),u(F,Math.min(n(F)+1,Y.length-1),!0);else if(S.key==="ArrowUp")S.preventDefault(),u(F,Math.max(n(F)-1,-1),!0);else if(S.key==="Enter"&&n(F)>=0&&Y[n(F)]){S.preventDefault();const Me=Y[n(F)];u(Ie,!1),u(ge,""),u(xe,[],!0),u(F,-1),I(Me)}else S.key==="Escape"&&u(Ie,!1)}),Oa(re,()=>n(ge),S=>u(ge,S)),f(b,de)};z(st,b=>{n(Ie)&&b(Tt)})}var bt=m(st,2);{var pr=b=>{var R=Xh(),de=d(R),_e=d(de),Se=d(_e),Ae=m(_e,2),re=d(Ae);Vs(re,{size:14}),L(Xt=>{Ne(de,1,Xt),N(Se,n(ve))},[()=>Mt(Et("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",n(fe)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":n(fe)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),oe("click",Ae,()=>{u(pe,!1)}),f(b,R)};z(bt,b=>{n(pe)&&b(pr)})}L(b=>{Ne(Oe,1,Mt(n(D)?n(p)?"sidebar-mobile":"hidden":"")),Ne(Fn,1,b)},[()=>Mt(Et("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",n(w)?"text-dl-text-dim":n(je)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),oe("click",mn,g),oe("click",jt,tt),oe("click",Fn,()=>W()),f(e,Qe),rn()}la(["click","keydown","input"]);pu(Qh,{target:document.getElementById("app")});
