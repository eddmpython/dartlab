var Fd=Object.defineProperty;var ii=e=>{throw TypeError(e)};var qd=(e,t,r)=>t in e?Fd(e,t,{enumerable:!0,configurable:!0,writable:!0,value:r}):e[t]=r;var an=(e,t,r)=>qd(e,typeof t!="symbol"?t+"":t,r),eo=(e,t,r)=>t.has(e)||ii("Cannot "+r);var E=(e,t,r)=>(eo(e,t,"read from private field"),r?r.call(e):t.get(e)),Ye=(e,t,r)=>t.has(e)?ii("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,r),qe=(e,t,r,a)=>(eo(e,t,"write to private field"),a?a.call(e,r):t.set(e,r),r),er=(e,t,r)=>(eo(e,t,"access private method"),r);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))a(s);new MutationObserver(s=>{for(const o of s)if(o.type==="childList")for(const i of o.addedNodes)i.tagName==="LINK"&&i.rel==="modulepreload"&&a(i)}).observe(document,{childList:!0,subtree:!0});function r(s){const o={};return s.integrity&&(o.integrity=s.integrity),s.referrerPolicy&&(o.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?o.credentials="include":s.crossOrigin==="anonymous"?o.credentials="omit":o.credentials="same-origin",o}function a(s){if(s.ep)return;s.ep=!0;const o=r(s);fetch(s.href,o)}})();const lo=!1;var $o=Array.isArray,Bd=Array.prototype.indexOf,Ba=Array.prototype.includes,qs=Array.from,Gd=Object.defineProperty,ta=Object.getOwnPropertyDescriptor,Bi=Object.getOwnPropertyDescriptors,Hd=Object.prototype,Ud=Array.prototype,No=Object.getPrototypeOf,li=Object.isExtensible;function ss(e){return typeof e=="function"}const Wd=()=>{};function Kd(e){return e()}function co(e){for(var t=0;t<e.length;t++)e[t]()}function Gi(){var e,t,r=new Promise((a,s)=>{e=a,t=s});return{promise:r,resolve:e,reject:t}}function Hi(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const r=[];for(const a of e)if(r.push(a),r.length===t)break;return r}const br=2,Xa=4,ka=8,Bs=1<<24,ia=16,un=32,Ea=64,uo=128,Xr=512,hr=1024,gr=2048,cn=4096,Er=8192,yn=16384,Ja=32768,jn=65536,di=1<<17,Yd=1<<18,Qa=1<<19,Ui=1<<20,_n=1<<25,Ca=65536,fo=1<<21,Oo=1<<22,ra=1<<23,kn=Symbol("$state"),Wi=Symbol("legacy props"),Xd=Symbol(""),va=new class extends Error{constructor(){super(...arguments);an(this,"name","StaleReactionError");an(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var Vi;const Ki=!!((Vi=globalThis.document)!=null&&Vi.contentType)&&globalThis.document.contentType.includes("xml");function Jd(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function Qd(e,t,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function Zd(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function ec(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function tc(e){throw new Error("https://svelte.dev/e/effect_orphan")}function rc(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function nc(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function ac(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function sc(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function oc(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function ic(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const lc=1,dc=2,Yi=4,cc=8,uc=16,fc=1,vc=2,Xi=4,pc=8,mc=16,hc=1,gc=2,sr=Symbol(),Ji="http://www.w3.org/1999/xhtml",Qi="http://www.w3.org/2000/svg",xc="http://www.w3.org/1998/Math/MathML",bc="@attach";function _c(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function wc(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Zi(e){return e===this.v}function yc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function el(e){return!yc(e,this.v)}let ks=!1,kc=!1;function Cc(){ks=!0}let or=null;function Ga(e){or=e}function en(e,t=!1,r){or={p:or,i:!1,c:null,e:null,s:e,x:null,l:ks&&!t?{s:null,u:null,$:[]}:null}}function tn(e){var t=or,r=t.e;if(r!==null){t.e=null;for(var a of r)_l(a)}return t.i=!0,or=t.p,{}}function Cs(){return!ks||or!==null&&or.l===null}let pa=[];function tl(){var e=pa;pa=[],co(e)}function Cn(e){if(pa.length===0&&!vs){var t=pa;queueMicrotask(()=>{t===pa&&tl()})}pa.push(e)}function Sc(){for(;pa.length>0;)tl()}function rl(e){var t=We;if(t===null)return Ue.f|=ra,e;if((t.f&Ja)===0&&(t.f&Xa)===0)throw e;Qn(e,t)}function Qn(e,t){for(;t!==null;){if((t.f&uo)!==0){if((t.f&Ja)===0)throw e;try{t.b.error(e);return}catch(r){e=r}}t=t.parent}throw e}const Mc=-7169;function Gt(e,t){e.f=e.f&Mc|t}function Lo(e){(e.f&Xr)!==0||e.deps===null?Gt(e,hr):Gt(e,cn)}function nl(e){if(e!==null)for(const t of e)(t.f&br)===0||(t.f&Ca)===0||(t.f^=Ca,nl(t.deps))}function al(e,t,r){(e.f&gr)!==0?t.add(e):(e.f&cn)!==0&&r.add(e),nl(e.deps),Gt(e,hr)}const As=new Set;let Be=null,vo=null,mr=null,Pr=[],Gs=null,vs=!1,Ha=null,Ec=1;var Yn,Oa,ga,La,Ra,Da,Xn,hn,ja,Or,po,mo,ho,go;const Ko=class Ko{constructor(){Ye(this,Or);an(this,"id",Ec++);an(this,"current",new Map);an(this,"previous",new Map);Ye(this,Yn,new Set);Ye(this,Oa,new Set);Ye(this,ga,0);Ye(this,La,0);Ye(this,Ra,null);Ye(this,Da,new Set);Ye(this,Xn,new Set);Ye(this,hn,new Map);an(this,"is_fork",!1);Ye(this,ja,!1)}skip_effect(t){E(this,hn).has(t)||E(this,hn).set(t,{d:[],m:[]})}unskip_effect(t){var r=E(this,hn).get(t);if(r){E(this,hn).delete(t);for(var a of r.d)Gt(a,gr),wn(a);for(a of r.m)Gt(a,cn),wn(a)}}process(t){var s;Pr=[],this.apply();var r=Ha=[],a=[];for(const o of t)er(this,Or,mo).call(this,o,r,a);if(Ha=null,er(this,Or,po).call(this)){er(this,Or,ho).call(this,a),er(this,Or,ho).call(this,r);for(const[o,i]of E(this,hn))ll(o,i)}else{vo=this,Be=null;for(const o of E(this,Yn))o(this);E(this,Yn).clear(),E(this,ga)===0&&er(this,Or,go).call(this),ci(a),ci(r),E(this,Da).clear(),E(this,Xn).clear(),vo=null,(s=E(this,Ra))==null||s.resolve()}mr=null}capture(t,r){r!==sr&&!this.previous.has(t)&&this.previous.set(t,r),(t.f&ra)===0&&(this.current.set(t,t.v),mr==null||mr.set(t,t.v))}activate(){Be=this,this.apply()}deactivate(){Be===this&&(Be=null,mr=null)}flush(){var t;if(Pr.length>0)Be=this,sl();else if(E(this,ga)===0&&!this.is_fork){for(const r of E(this,Yn))r(this);E(this,Yn).clear(),er(this,Or,go).call(this),(t=E(this,Ra))==null||t.resolve()}this.deactivate()}discard(){for(const t of E(this,Oa))t(this);E(this,Oa).clear()}increment(t){qe(this,ga,E(this,ga)+1),t&&qe(this,La,E(this,La)+1)}decrement(t){qe(this,ga,E(this,ga)-1),t&&qe(this,La,E(this,La)-1),!E(this,ja)&&(qe(this,ja,!0),Cn(()=>{qe(this,ja,!1),er(this,Or,po).call(this)?Pr.length>0&&this.flush():this.revive()}))}revive(){for(const t of E(this,Da))E(this,Xn).delete(t),Gt(t,gr),wn(t);for(const t of E(this,Xn))Gt(t,cn),wn(t);this.flush()}oncommit(t){E(this,Yn).add(t)}ondiscard(t){E(this,Oa).add(t)}settled(){return(E(this,Ra)??qe(this,Ra,Gi())).promise}static ensure(){if(Be===null){const t=Be=new Ko;As.add(Be),vs||Cn(()=>{Be===t&&t.flush()})}return Be}apply(){}};Yn=new WeakMap,Oa=new WeakMap,ga=new WeakMap,La=new WeakMap,Ra=new WeakMap,Da=new WeakMap,Xn=new WeakMap,hn=new WeakMap,ja=new WeakMap,Or=new WeakSet,po=function(){return this.is_fork||E(this,La)>0},mo=function(t,r,a){t.f^=hr;for(var s=t.first;s!==null;){var o=s.f,i=(o&(un|Ea))!==0,l=i&&(o&hr)!==0,c=(o&Er)!==0,f=l||E(this,hn).has(s);if(!f&&s.fn!==null){i?c||(s.f^=hr):(o&Xa)!==0?r.push(s):(o&(ka|Bs))!==0&&c?a.push(s):Es(s)&&(Wa(s),(o&ia)!==0&&(E(this,Xn).add(s),c&&Gt(s,gr)));var p=s.first;if(p!==null){s=p;continue}}for(;s!==null;){var b=s.next;if(b!==null){s=b;break}s=s.parent}}},ho=function(t){for(var r=0;r<t.length;r+=1)al(t[r],E(this,Da),E(this,Xn))},go=function(){var o;if(As.size>1){this.previous.clear();var t=Be,r=mr,a=!0;for(const i of As){if(i===this){a=!1;continue}const l=[];for(const[f,p]of this.current){if(i.current.has(f))if(a&&p!==i.current.get(f))i.current.set(f,p);else continue;l.push(f)}if(l.length===0)continue;const c=[...i.current.keys()].filter(f=>!this.current.has(f));if(c.length>0){var s=Pr;Pr=[];const f=new Set,p=new Map;for(const b of l)ol(b,c,f,p);if(Pr.length>0){Be=i,i.apply();for(const b of Pr)er(o=i,Or,mo).call(o,b,[],[]);i.deactivate()}Pr=s}}Be=t,mr=r}E(this,hn).clear(),As.delete(this)};let na=Ko;function zc(e){var t=vs;vs=!0;try{for(var r;;){if(Sc(),Pr.length===0&&(Be==null||Be.flush(),Pr.length===0))return Gs=null,r;sl()}}finally{vs=t}}function sl(){var e=null;try{for(var t=0;Pr.length>0;){var r=na.ensure();if(t++>1e3){var a,s;Ac()}r.process(Pr),aa.clear()}}finally{Pr=[],Gs=null,Ha=null}}function Ac(){try{rc()}catch(e){Qn(e,Gs)}}let sn=null;function ci(e){var t=e.length;if(t!==0){for(var r=0;r<t;){var a=e[r++];if((a.f&(yn|Er))===0&&Es(a)&&(sn=new Set,Wa(a),a.deps===null&&a.first===null&&a.nodes===null&&a.teardown===null&&a.ac===null&&Cl(a),(sn==null?void 0:sn.size)>0)){aa.clear();for(const s of sn){if((s.f&(yn|Er))!==0)continue;const o=[s];let i=s.parent;for(;i!==null;)sn.has(i)&&(sn.delete(i),o.push(i)),i=i.parent;for(let l=o.length-1;l>=0;l--){const c=o[l];(c.f&(yn|Er))===0&&Wa(c)}}sn.clear()}}sn=null}}function ol(e,t,r,a){if(!r.has(e)&&(r.add(e),e.reactions!==null))for(const s of e.reactions){const o=s.f;(o&br)!==0?ol(s,t,r,a):(o&(Oo|ia))!==0&&(o&gr)===0&&il(s,t,a)&&(Gt(s,gr),wn(s))}}function il(e,t,r){const a=r.get(e);if(a!==void 0)return a;if(e.deps!==null)for(const s of e.deps){if(Ba.call(t,s))return!0;if((s.f&br)!==0&&il(s,t,r))return r.set(s,!0),!0}return r.set(e,!1),!1}function wn(e){var t=Gs=e,r=t.b;if(r!=null&&r.is_pending&&(e.f&(Xa|ka|Bs))!==0&&(e.f&Ja)===0){r.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var a=t.f;if(Ha!==null&&t===We&&(e.f&ka)===0)return;if((a&(Ea|un))!==0){if((a&hr)===0)return;t.f^=hr}}Pr.push(t)}function ll(e,t){if(!((e.f&un)!==0&&(e.f&hr)!==0)){(e.f&gr)!==0?t.d.push(e):(e.f&cn)!==0&&t.m.push(e),Gt(e,hr);for(var r=e.first;r!==null;)ll(r,t),r=r.next}}function Tc(e){let t=0,r=sa(0),a;return()=>{Vo()&&(n(r),qo(()=>(t===0&&(a=Sa(()=>e(()=>ms(r)))),t+=1,()=>{Cn(()=>{t-=1,t===0&&(a==null||a(),a=void 0,ms(r))})})))}}var Ic=jn|Qa;function Pc(e,t,r,a){new $c(e,t,r,a)}var Kr,Po,gn,xa,Ir,xn,Vr,on,Nn,ba,Jn,Va,Fa,qa,On,Vs,rr,Nc,Oc,Lc,xo,Ns,Os,bo;class $c{constructor(t,r,a,s){Ye(this,rr);an(this,"parent");an(this,"is_pending",!1);an(this,"transform_error");Ye(this,Kr);Ye(this,Po,null);Ye(this,gn);Ye(this,xa);Ye(this,Ir);Ye(this,xn,null);Ye(this,Vr,null);Ye(this,on,null);Ye(this,Nn,null);Ye(this,ba,0);Ye(this,Jn,0);Ye(this,Va,!1);Ye(this,Fa,new Set);Ye(this,qa,new Set);Ye(this,On,null);Ye(this,Vs,Tc(()=>(qe(this,On,sa(E(this,ba))),()=>{qe(this,On,null)})));var o;qe(this,Kr,t),qe(this,gn,r),qe(this,xa,i=>{var l=We;l.b=this,l.f|=uo,a(i)}),this.parent=We.b,this.transform_error=s??((o=this.parent)==null?void 0:o.transform_error)??(i=>i),qe(this,Ir,Za(()=>{er(this,rr,xo).call(this)},Ic))}defer_effect(t){al(t,E(this,Fa),E(this,qa))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!E(this,gn).pending}update_pending_count(t){er(this,rr,bo).call(this,t),qe(this,ba,E(this,ba)+t),!(!E(this,On)||E(this,Va))&&(qe(this,Va,!0),Cn(()=>{qe(this,Va,!1),E(this,On)&&Ua(E(this,On),E(this,ba))}))}get_effect_pending(){return E(this,Vs).call(this),n(E(this,On))}error(t){var r=E(this,gn).onerror;let a=E(this,gn).failed;if(!r&&!a)throw t;E(this,xn)&&(xr(E(this,xn)),qe(this,xn,null)),E(this,Vr)&&(xr(E(this,Vr)),qe(this,Vr,null)),E(this,on)&&(xr(E(this,on)),qe(this,on,null));var s=!1,o=!1;const i=()=>{if(s){wc();return}s=!0,o&&ic(),E(this,on)!==null&&wa(E(this,on),()=>{qe(this,on,null)}),er(this,rr,Os).call(this,()=>{na.ensure(),er(this,rr,xo).call(this)})},l=c=>{try{o=!0,r==null||r(c,i),o=!1}catch(f){Qn(f,E(this,Ir)&&E(this,Ir).parent)}a&&qe(this,on,er(this,rr,Os).call(this,()=>{na.ensure();try{return Nr(()=>{var f=We;f.b=this,f.f|=uo,a(E(this,Kr),()=>c,()=>i)})}catch(f){return Qn(f,E(this,Ir).parent),null}}))};Cn(()=>{var c;try{c=this.transform_error(t)}catch(f){Qn(f,E(this,Ir)&&E(this,Ir).parent);return}c!==null&&typeof c=="object"&&typeof c.then=="function"?c.then(l,f=>Qn(f,E(this,Ir)&&E(this,Ir).parent)):l(c)})}}Kr=new WeakMap,Po=new WeakMap,gn=new WeakMap,xa=new WeakMap,Ir=new WeakMap,xn=new WeakMap,Vr=new WeakMap,on=new WeakMap,Nn=new WeakMap,ba=new WeakMap,Jn=new WeakMap,Va=new WeakMap,Fa=new WeakMap,qa=new WeakMap,On=new WeakMap,Vs=new WeakMap,rr=new WeakSet,Nc=function(){try{qe(this,xn,Nr(()=>E(this,xa).call(this,E(this,Kr))))}catch(t){this.error(t)}},Oc=function(t){const r=E(this,gn).failed;r&&qe(this,on,Nr(()=>{r(E(this,Kr),()=>t,()=>()=>{})}))},Lc=function(){const t=E(this,gn).pending;t&&(this.is_pending=!0,qe(this,Vr,Nr(()=>t(E(this,Kr)))),Cn(()=>{var r=qe(this,Nn,document.createDocumentFragment()),a=Sn();r.append(a),qe(this,xn,er(this,rr,Os).call(this,()=>(na.ensure(),Nr(()=>E(this,xa).call(this,a))))),E(this,Jn)===0&&(E(this,Kr).before(r),qe(this,Nn,null),wa(E(this,Vr),()=>{qe(this,Vr,null)}),er(this,rr,Ns).call(this))}))},xo=function(){try{if(this.is_pending=this.has_pending_snippet(),qe(this,Jn,0),qe(this,ba,0),qe(this,xn,Nr(()=>{E(this,xa).call(this,E(this,Kr))})),E(this,Jn)>0){var t=qe(this,Nn,document.createDocumentFragment());Ho(E(this,xn),t);const r=E(this,gn).pending;qe(this,Vr,Nr(()=>r(E(this,Kr))))}else er(this,rr,Ns).call(this)}catch(r){this.error(r)}},Ns=function(){this.is_pending=!1;for(const t of E(this,Fa))Gt(t,gr),wn(t);for(const t of E(this,qa))Gt(t,cn),wn(t);E(this,Fa).clear(),E(this,qa).clear()},Os=function(t){var r=We,a=Ue,s=or;Zr(E(this,Ir)),Qr(E(this,Ir)),Ga(E(this,Ir).ctx);try{return t()}catch(o){return rl(o),null}finally{Zr(r),Qr(a),Ga(s)}},bo=function(t){var r;if(!this.has_pending_snippet()){this.parent&&er(r=this.parent,rr,bo).call(r,t);return}qe(this,Jn,E(this,Jn)+t),E(this,Jn)===0&&(er(this,rr,Ns).call(this),E(this,Vr)&&wa(E(this,Vr),()=>{qe(this,Vr,null)}),E(this,Nn)&&(E(this,Kr).before(E(this,Nn)),qe(this,Nn,null)))};function dl(e,t,r,a){const s=Cs()?Ss:Ro;var o=e.filter(b=>!b.settled);if(r.length===0&&o.length===0){a(t.map(s));return}var i=We,l=Rc(),c=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(b=>b.promise)):null;function f(b){l();try{a(b)}catch(w){(i.f&yn)===0&&Qn(w,i)}_o()}if(r.length===0){c.then(()=>f(t.map(s)));return}function p(){l(),Promise.all(r.map(b=>jc(b))).then(b=>f([...t.map(s),...b])).catch(b=>Qn(b,i))}c?c.then(p):p()}function Rc(){var e=We,t=Ue,r=or,a=Be;return function(o=!0){Zr(e),Qr(t),Ga(r),o&&(a==null||a.activate())}}function _o(e=!0){Zr(null),Qr(null),Ga(null),e&&(Be==null||Be.deactivate())}function Dc(){var e=We.b,t=Be,r=e.is_rendered();return e.update_pending_count(1),t.increment(r),()=>{e.update_pending_count(-1),t.decrement(r)}}function Ss(e){var t=br|gr,r=Ue!==null&&(Ue.f&br)!==0?Ue:null;return We!==null&&(We.f|=Qa),{ctx:or,deps:null,effects:null,equals:Zi,f:t,fn:e,reactions:null,rv:0,v:sr,wv:0,parent:r??We,ac:null}}function jc(e,t,r){We===null&&Jd();var s=void 0,o=sa(sr),i=!Ue,l=new Map;return Zc(()=>{var w;var c=Gi();s=c.promise;try{Promise.resolve(e()).then(c.resolve,c.reject).finally(_o)}catch(A){c.reject(A),_o()}var f=Be;if(i){var p=Dc();(w=l.get(f))==null||w.reject(va),l.delete(f),l.set(f,c)}const b=(A,k=void 0)=>{if(f.activate(),k)k!==va&&(o.f|=ra,Ua(o,k));else{(o.f&ra)!==0&&(o.f^=ra),Ua(o,A);for(const[P,y]of l){if(l.delete(P),P===f)break;y.reject(va)}}p&&p()};c.promise.then(b,A=>b(null,A||"unknown"))}),Us(()=>{for(const c of l.values())c.reject(va)}),new Promise(c=>{function f(p){function b(){p===s?c(o):f(s)}p.then(b,b)}f(s)})}function U(e){const t=Ss(e);return El(t),t}function Ro(e){const t=Ss(e);return t.equals=el,t}function Vc(e){var t=e.effects;if(t!==null){e.effects=null;for(var r=0;r<t.length;r+=1)xr(t[r])}}function Fc(e){for(var t=e.parent;t!==null;){if((t.f&br)===0)return(t.f&yn)===0?t:null;t=t.parent}return null}function Do(e){var t,r=We;Zr(Fc(e));try{e.f&=~Ca,Vc(e),t=Il(e)}finally{Zr(r)}return t}function cl(e){var t=Do(e);if(!e.equals(t)&&(e.wv=Al(),(!(Be!=null&&Be.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){Gt(e,hr);return}oa||(mr!==null?(Vo()||Be!=null&&Be.is_fork)&&mr.set(e,t):Lo(e))}function qc(e){var t,r;if(e.effects!==null)for(const a of e.effects)(a.teardown||a.ac)&&((t=a.teardown)==null||t.call(a),(r=a.ac)==null||r.abort(va),a.teardown=Wd,a.ac=null,_s(a,0),Bo(a))}function ul(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&Wa(t)}let wo=new Set;const aa=new Map;let fl=!1;function sa(e,t){var r={f:0,v:e,reactions:null,equals:Zi,rv:0,wv:0};return r}function H(e,t){const r=sa(e);return El(r),r}function Bc(e,t=!1,r=!0){var s;const a=sa(e);return t||(a.equals=el),ks&&r&&or!==null&&or.l!==null&&((s=or.l).s??(s.s=[])).push(a),a}function u(e,t,r=!1){Ue!==null&&(!dn||(Ue.f&di)!==0)&&Cs()&&(Ue.f&(br|ia|Oo|di))!==0&&(Jr===null||!Ba.call(Jr,e))&&oc();let a=r?Et(t):t;return Ua(e,a)}function Ua(e,t){if(!e.equals(t)){var r=e.v;oa?aa.set(e,t):aa.set(e,r),e.v=t;var a=na.ensure();if(a.capture(e,r),(e.f&br)!==0){const s=e;(e.f&gr)!==0&&Do(s),Lo(s)}e.wv=Al(),vl(e,gr),Cs()&&We!==null&&(We.f&hr)!==0&&(We.f&(un|Ea))===0&&(Wr===null?tu([e]):Wr.push(e)),!a.is_fork&&wo.size>0&&!fl&&Gc()}return t}function Gc(){fl=!1;for(const e of wo)(e.f&hr)!==0&&Gt(e,cn),Es(e)&&Wa(e);wo.clear()}function ps(e,t=1){var r=n(e),a=t===1?r++:r--;return u(e,r),a}function ms(e){u(e,e.v+1)}function vl(e,t){var r=e.reactions;if(r!==null)for(var a=Cs(),s=r.length,o=0;o<s;o++){var i=r[o],l=i.f;if(!(!a&&i===We)){var c=(l&gr)===0;if(c&&Gt(i,t),(l&br)!==0){var f=i;mr==null||mr.delete(f),(l&Ca)===0&&(l&Xr&&(i.f|=Ca),vl(f,cn))}else c&&((l&ia)!==0&&sn!==null&&sn.add(i),wn(i))}}}function Et(e){if(typeof e!="object"||e===null||kn in e)return e;const t=No(e);if(t!==Hd&&t!==Ud)return e;var r=new Map,a=$o(e),s=H(0),o=ya,i=l=>{if(ya===o)return l();var c=Ue,f=ya;Qr(null),pi(o);var p=l();return Qr(c),pi(f),p};return a&&r.set("length",H(e.length)),new Proxy(e,{defineProperty(l,c,f){(!("value"in f)||f.configurable===!1||f.enumerable===!1||f.writable===!1)&&ac();var p=r.get(c);return p===void 0?i(()=>{var b=H(f.value);return r.set(c,b),b}):u(p,f.value,!0),!0},deleteProperty(l,c){var f=r.get(c);if(f===void 0){if(c in l){const p=i(()=>H(sr));r.set(c,p),ms(s)}}else u(f,sr),ms(s);return!0},get(l,c,f){var A;if(c===kn)return e;var p=r.get(c),b=c in l;if(p===void 0&&(!b||(A=ta(l,c))!=null&&A.writable)&&(p=i(()=>{var k=Et(b?l[c]:sr),P=H(k);return P}),r.set(c,p)),p!==void 0){var w=n(p);return w===sr?void 0:w}return Reflect.get(l,c,f)},getOwnPropertyDescriptor(l,c){var f=Reflect.getOwnPropertyDescriptor(l,c);if(f&&"value"in f){var p=r.get(c);p&&(f.value=n(p))}else if(f===void 0){var b=r.get(c),w=b==null?void 0:b.v;if(b!==void 0&&w!==sr)return{enumerable:!0,configurable:!0,value:w,writable:!0}}return f},has(l,c){var w;if(c===kn)return!0;var f=r.get(c),p=f!==void 0&&f.v!==sr||Reflect.has(l,c);if(f!==void 0||We!==null&&(!p||(w=ta(l,c))!=null&&w.writable)){f===void 0&&(f=i(()=>{var A=p?Et(l[c]):sr,k=H(A);return k}),r.set(c,f));var b=n(f);if(b===sr)return!1}return p},set(l,c,f,p){var Y;var b=r.get(c),w=c in l;if(a&&c==="length")for(var A=f;A<b.v;A+=1){var k=r.get(A+"");k!==void 0?u(k,sr):A in l&&(k=i(()=>H(sr)),r.set(A+"",k))}if(b===void 0)(!w||(Y=ta(l,c))!=null&&Y.writable)&&(b=i(()=>H(void 0)),u(b,Et(f)),r.set(c,b));else{w=b.v!==sr;var P=i(()=>Et(f));u(b,P)}var y=Reflect.getOwnPropertyDescriptor(l,c);if(y!=null&&y.set&&y.set.call(p,f),!w){if(a&&typeof c=="string"){var C=r.get("length"),j=Number(c);Number.isInteger(j)&&j>=C.v&&u(C,j+1)}ms(s)}return!0},ownKeys(l){n(s);var c=Reflect.ownKeys(l).filter(b=>{var w=r.get(b);return w===void 0||w.v!==sr});for(var[f,p]of r)p.v!==sr&&!(f in l)&&c.push(f);return c},setPrototypeOf(){sc()}})}function ui(e){try{if(e!==null&&typeof e=="object"&&kn in e)return e[kn]}catch{}return e}function Hc(e,t){return Object.is(ui(e),ui(t))}var yo,pl,ml,hl;function Uc(){if(yo===void 0){yo=window,pl=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,r=Text.prototype;ml=ta(t,"firstChild").get,hl=ta(t,"nextSibling").get,li(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),li(r)&&(r.__t=void 0)}}function Sn(e=""){return document.createTextNode(e)}function Rn(e){return ml.call(e)}function Ms(e){return hl.call(e)}function d(e,t){return Rn(e)}function Q(e,t=!1){{var r=Rn(e);return r instanceof Comment&&r.data===""?Ms(r):r}}function m(e,t=1,r=!1){let a=e;for(;t--;)a=Ms(a);return a}function Wc(e){e.textContent=""}function gl(){return!1}function jo(e,t,r){return document.createElementNS(t??Ji,e,void 0)}function xl(e,t){if(t){const r=document.body;e.autofocus=!0,Cn(()=>{document.activeElement===r&&e.focus()})}}let fi=!1;function Kc(){fi||(fi=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const r of e.target.elements)(t=r.__on_r)==null||t.call(r)})},{capture:!0}))}function Hs(e){var t=Ue,r=We;Qr(null),Zr(null);try{return e()}finally{Qr(t),Zr(r)}}function Yc(e,t,r,a=r){e.addEventListener(t,()=>Hs(r));const s=e.__on_r;s?e.__on_r=()=>{s(),a(!0)}:e.__on_r=()=>a(!0),Kc()}function bl(e){We===null&&(Ue===null&&tc(),ec()),oa&&Zd()}function Xc(e,t){var r=t.last;r===null?t.last=t.first=e:(r.next=e,e.prev=r,t.last=e)}function fn(e,t){var r=We;r!==null&&(r.f&Er)!==0&&(e|=Er);var a={ctx:or,deps:null,nodes:null,f:e|gr|Xr,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},s=a;if((e&Xa)!==0)Ha!==null?Ha.push(a):wn(a);else if(t!==null){try{Wa(a)}catch(i){throw xr(a),i}s.deps===null&&s.teardown===null&&s.nodes===null&&s.first===s.last&&(s.f&Qa)===0&&(s=s.first,(e&ia)!==0&&(e&jn)!==0&&s!==null&&(s.f|=jn))}if(s!==null&&(s.parent=r,r!==null&&Xc(s,r),Ue!==null&&(Ue.f&br)!==0&&(e&Ea)===0)){var o=Ue;(o.effects??(o.effects=[])).push(s)}return a}function Vo(){return Ue!==null&&!dn}function Us(e){const t=fn(ka,null);return Gt(t,hr),t.teardown=e,t}function Zn(e){bl();var t=We.f,r=!Ue&&(t&un)!==0&&(t&Ja)===0;if(r){var a=or;(a.e??(a.e=[])).push(e)}else return _l(e)}function _l(e){return fn(Xa|Ui,e)}function Jc(e){return bl(),fn(ka|Ui,e)}function Qc(e){na.ensure();const t=fn(Ea|Qa,e);return(r={})=>new Promise(a=>{r.outro?wa(t,()=>{xr(t),a(void 0)}):(xr(t),a(void 0))})}function Fo(e){return fn(Xa,e)}function Zc(e){return fn(Oo|Qa,e)}function qo(e,t=0){return fn(ka|t,e)}function O(e,t=[],r=[],a=[]){dl(a,t,r,s=>{fn(ka,()=>e(...s.map(n)))})}function Za(e,t=0){var r=fn(ia|t,e);return r}function wl(e,t=0){var r=fn(Bs|t,e);return r}function Nr(e){return fn(un|Qa,e)}function yl(e){var t=e.teardown;if(t!==null){const r=oa,a=Ue;vi(!0),Qr(null);try{t.call(null)}finally{vi(r),Qr(a)}}}function Bo(e,t=!1){var r=e.first;for(e.first=e.last=null;r!==null;){const s=r.ac;s!==null&&Hs(()=>{s.abort(va)});var a=r.next;(r.f&Ea)!==0?r.parent=null:xr(r,t),r=a}}function eu(e){for(var t=e.first;t!==null;){var r=t.next;(t.f&un)===0&&xr(t),t=r}}function xr(e,t=!0){var r=!1;(t||(e.f&Yd)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(kl(e.nodes.start,e.nodes.end),r=!0),Bo(e,t&&!r),_s(e,0),Gt(e,yn);var a=e.nodes&&e.nodes.t;if(a!==null)for(const o of a)o.stop();yl(e);var s=e.parent;s!==null&&s.first!==null&&Cl(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function kl(e,t){for(;e!==null;){var r=e===t?null:Ms(e);e.remove(),e=r}}function Cl(e){var t=e.parent,r=e.prev,a=e.next;r!==null&&(r.next=a),a!==null&&(a.prev=r),t!==null&&(t.first===e&&(t.first=a),t.last===e&&(t.last=r))}function wa(e,t,r=!0){var a=[];Sl(e,a,!0);var s=()=>{r&&xr(e),t&&t()},o=a.length;if(o>0){var i=()=>--o||s();for(var l of a)l.out(i)}else s()}function Sl(e,t,r){if((e.f&Er)===0){e.f^=Er;var a=e.nodes&&e.nodes.t;if(a!==null)for(const l of a)(l.is_global||r)&&t.push(l);for(var s=e.first;s!==null;){var o=s.next,i=(s.f&jn)!==0||(s.f&un)!==0&&(e.f&ia)!==0;Sl(s,t,i?r:!1),s=o}}}function Go(e){Ml(e,!0)}function Ml(e,t){if((e.f&Er)!==0){e.f^=Er;for(var r=e.first;r!==null;){var a=r.next,s=(r.f&jn)!==0||(r.f&un)!==0;Ml(r,s?t:!1),r=a}var o=e.nodes&&e.nodes.t;if(o!==null)for(const i of o)(i.is_global||t)&&i.in()}}function Ho(e,t){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end;r!==null;){var s=r===a?null:Ms(r);t.append(r),r=s}}let Ls=!1,oa=!1;function vi(e){oa=e}let Ue=null,dn=!1;function Qr(e){Ue=e}let We=null;function Zr(e){We=e}let Jr=null;function El(e){Ue!==null&&(Jr===null?Jr=[e]:Jr.push(e))}let $r=null,jr=0,Wr=null;function tu(e){Wr=e}let zl=1,ma=0,ya=ma;function pi(e){ya=e}function Al(){return++zl}function Es(e){var t=e.f;if((t&gr)!==0)return!0;if(t&br&&(e.f&=~Ca),(t&cn)!==0){for(var r=e.deps,a=r.length,s=0;s<a;s++){var o=r[s];if(Es(o)&&cl(o),o.wv>e.wv)return!0}(t&Xr)!==0&&mr===null&&Gt(e,hr)}return!1}function Tl(e,t,r=!0){var a=e.reactions;if(a!==null&&!(Jr!==null&&Ba.call(Jr,e)))for(var s=0;s<a.length;s++){var o=a[s];(o.f&br)!==0?Tl(o,t,!1):t===o&&(r?Gt(o,gr):(o.f&hr)!==0&&Gt(o,cn),wn(o))}}function Il(e){var P;var t=$r,r=jr,a=Wr,s=Ue,o=Jr,i=or,l=dn,c=ya,f=e.f;$r=null,jr=0,Wr=null,Ue=(f&(un|Ea))===0?e:null,Jr=null,Ga(e.ctx),dn=!1,ya=++ma,e.ac!==null&&(Hs(()=>{e.ac.abort(va)}),e.ac=null);try{e.f|=fo;var p=e.fn,b=p();e.f|=Ja;var w=e.deps,A=Be==null?void 0:Be.is_fork;if($r!==null){var k;if(A||_s(e,jr),w!==null&&jr>0)for(w.length=jr+$r.length,k=0;k<$r.length;k++)w[jr+k]=$r[k];else e.deps=w=$r;if(Vo()&&(e.f&Xr)!==0)for(k=jr;k<w.length;k++)((P=w[k]).reactions??(P.reactions=[])).push(e)}else!A&&w!==null&&jr<w.length&&(_s(e,jr),w.length=jr);if(Cs()&&Wr!==null&&!dn&&w!==null&&(e.f&(br|cn|gr))===0)for(k=0;k<Wr.length;k++)Tl(Wr[k],e);if(s!==null&&s!==e){if(ma++,s.deps!==null)for(let y=0;y<r;y+=1)s.deps[y].rv=ma;if(t!==null)for(const y of t)y.rv=ma;Wr!==null&&(a===null?a=Wr:a.push(...Wr))}return(e.f&ra)!==0&&(e.f^=ra),b}catch(y){return rl(y)}finally{e.f^=fo,$r=t,jr=r,Wr=a,Ue=s,Jr=o,Ga(i),dn=l,ya=c}}function ru(e,t){let r=t.reactions;if(r!==null){var a=Bd.call(r,e);if(a!==-1){var s=r.length-1;s===0?r=t.reactions=null:(r[a]=r[s],r.pop())}}if(r===null&&(t.f&br)!==0&&($r===null||!Ba.call($r,t))){var o=t;(o.f&Xr)!==0&&(o.f^=Xr,o.f&=~Ca),Lo(o),qc(o),_s(o,0)}}function _s(e,t){var r=e.deps;if(r!==null)for(var a=t;a<r.length;a++)ru(e,r[a])}function Wa(e){var t=e.f;if((t&yn)===0){Gt(e,hr);var r=We,a=Ls;We=e,Ls=!0;try{(t&(ia|Bs))!==0?eu(e):Bo(e),yl(e);var s=Il(e);e.teardown=typeof s=="function"?s:null,e.wv=zl;var o;lo&&kc&&(e.f&gr)!==0&&e.deps}finally{Ls=a,We=r}}}async function nu(){await Promise.resolve(),zc()}function n(e){var t=e.f,r=(t&br)!==0;if(Ue!==null&&!dn){var a=We!==null&&(We.f&yn)!==0;if(!a&&(Jr===null||!Ba.call(Jr,e))){var s=Ue.deps;if((Ue.f&fo)!==0)e.rv<ma&&(e.rv=ma,$r===null&&s!==null&&s[jr]===e?jr++:$r===null?$r=[e]:$r.push(e));else{(Ue.deps??(Ue.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[Ue]:Ba.call(o,Ue)||o.push(Ue)}}}if(oa&&aa.has(e))return aa.get(e);if(r){var i=e;if(oa){var l=i.v;return((i.f&hr)===0&&i.reactions!==null||$l(i))&&(l=Do(i)),aa.set(i,l),l}var c=(i.f&Xr)===0&&!dn&&Ue!==null&&(Ls||(Ue.f&Xr)!==0),f=(i.f&Ja)===0;Es(i)&&(c&&(i.f|=Xr),cl(i)),c&&!f&&(ul(i),Pl(i))}if(mr!=null&&mr.has(e))return mr.get(e);if((e.f&ra)!==0)throw e.v;return e.v}function Pl(e){if(e.f|=Xr,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&br)!==0&&(t.f&Xr)===0&&(ul(t),Pl(t))}function $l(e){if(e.v===sr)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(aa.has(t)||(t.f&br)!==0&&$l(t))return!0;return!1}function Sa(e){var t=dn;try{return dn=!0,e()}finally{dn=t}}function fa(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(kn in e)ko(e);else if(!Array.isArray(e))for(let t in e){const r=e[t];typeof r=="object"&&r&&kn in r&&ko(r)}}}function ko(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let a in e)try{ko(e[a],t)}catch{}const r=No(e);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const a=Bi(r);for(let s in a){const o=a[s].get;if(o)try{o.call(e)}catch{}}}}}function au(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const su=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function ou(e){return su.includes(e)}const iu={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function lu(e){return e=e.toLowerCase(),iu[e]??e}const du=["touchstart","touchmove"];function cu(e){return du.includes(e)}const ha=Symbol("events"),Nl=new Set,Co=new Set;function Ol(e,t,r,a={}){function s(o){if(a.capture||So.call(t,o),!o.cancelBubble)return Hs(()=>r==null?void 0:r.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Cn(()=>{t.addEventListener(e,s,a)}):t.addEventListener(e,s,a),s}function Na(e,t,r,a,s){var o={capture:a,passive:s},i=Ol(e,t,r,o);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&Us(()=>{t.removeEventListener(e,i,o)})}function re(e,t,r){(t[ha]??(t[ha]={}))[e]=r}function Vn(e){for(var t=0;t<e.length;t++)Nl.add(e[t]);for(var r of Co)r(e)}let mi=null;function So(e){var y,C;var t=this,r=t.ownerDocument,a=e.type,s=((y=e.composedPath)==null?void 0:y.call(e))||[],o=s[0]||e.target;mi=e;var i=0,l=mi===e&&e[ha];if(l){var c=s.indexOf(l);if(c!==-1&&(t===document||t===window)){e[ha]=t;return}var f=s.indexOf(t);if(f===-1)return;c<=f&&(i=c)}if(o=s[i]||e.target,o!==t){Gd(e,"currentTarget",{configurable:!0,get(){return o||r}});var p=Ue,b=We;Qr(null),Zr(null);try{for(var w,A=[];o!==null;){var k=o.assignedSlot||o.parentNode||o.host||null;try{var P=(C=o[ha])==null?void 0:C[a];P!=null&&(!o.disabled||e.target===o)&&P.call(o,e)}catch(j){w?A.push(j):w=j}if(e.cancelBubble||k===t||k===null)break;o=k}if(w){for(let j of A)queueMicrotask(()=>{throw j});throw w}}finally{e[ha]=t,delete e.currentTarget,Qr(p),Zr(b)}}}var Fi;const to=((Fi=globalThis==null?void 0:globalThis.window)==null?void 0:Fi.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function uu(e){return(to==null?void 0:to.createHTML(e))??e}function Ll(e){var t=jo("template");return t.innerHTML=uu(e.replaceAll("<!>","<!---->")),t.content}function Ma(e,t){var r=We;r.nodes===null&&(r.nodes={start:e,end:t,a:null,t:null})}function h(e,t){var r=(t&hc)!==0,a=(t&gc)!==0,s,o=!e.startsWith("<!>");return()=>{s===void 0&&(s=Ll(o?e:"<!>"+e),r||(s=Rn(s)));var i=a||pl?document.importNode(s,!0):s.cloneNode(!0);if(r){var l=Rn(i),c=i.lastChild;Ma(l,c)}else Ma(i,i);return i}}function fu(e,t,r="svg"){var a=!e.startsWith("<!>"),s=`<${r}>${a?e:"<!>"+e}</${r}>`,o;return()=>{if(!o){var i=Ll(s),l=Rn(i);o=Rn(l)}var c=o.cloneNode(!0);return Ma(c,c),c}}function vu(e,t){return fu(e,t,"svg")}function hs(e=""){{var t=Sn(e+"");return Ma(t,t),t}}function xe(){var e=document.createDocumentFragment(),t=document.createComment(""),r=Sn();return e.append(t,r),Ma(t,r),e}function v(e,t){e!==null&&e.before(t)}function N(e,t){var r=t==null?"":typeof t=="object"?`${t}`:t;r!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=r,e.nodeValue=`${r}`)}function pu(e,t){return mu(e,t)}const Ts=new Map;function mu(e,{target:t,anchor:r,props:a={},events:s,context:o,intro:i=!0,transformError:l}){Uc();var c=void 0,f=Qc(()=>{var p=r??t.appendChild(Sn());Pc(p,{pending:()=>{}},A=>{en({});var k=or;o&&(k.c=o),s&&(a.$$events=s),c=e(A,a)||{},tn()},l);var b=new Set,w=A=>{for(var k=0;k<A.length;k++){var P=A[k];if(!b.has(P)){b.add(P);var y=cu(P);for(const Y of[t,document]){var C=Ts.get(Y);C===void 0&&(C=new Map,Ts.set(Y,C));var j=C.get(P);j===void 0?(Y.addEventListener(P,So,{passive:y}),C.set(P,1)):C.set(P,j+1)}}}};return w(qs(Nl)),Co.add(w),()=>{var y;for(var A of b)for(const C of[t,document]){var k=Ts.get(C),P=k.get(A);--P==0?(C.removeEventListener(A,So),k.delete(A),k.size===0&&Ts.delete(C)):k.set(A,P)}Co.delete(w),p!==r&&((y=p.parentNode)==null||y.removeChild(p))}});return hu.set(c,f),c}let hu=new WeakMap;var ln,bn,Fr,_a,ws,ys,Fs;class Ws{constructor(t,r=!0){an(this,"anchor");Ye(this,ln,new Map);Ye(this,bn,new Map);Ye(this,Fr,new Map);Ye(this,_a,new Set);Ye(this,ws,!0);Ye(this,ys,t=>{if(E(this,ln).has(t)){var r=E(this,ln).get(t),a=E(this,bn).get(r);if(a)Go(a),E(this,_a).delete(r);else{var s=E(this,Fr).get(r);s&&(s.effect.f&Er)===0&&(E(this,bn).set(r,s.effect),E(this,Fr).delete(r),s.fragment.lastChild.remove(),this.anchor.before(s.fragment),a=s.effect)}for(const[o,i]of E(this,ln)){if(E(this,ln).delete(o),o===t)break;const l=E(this,Fr).get(i);l&&(xr(l.effect),E(this,Fr).delete(i))}for(const[o,i]of E(this,bn)){if(o===r||E(this,_a).has(o)||(i.f&Er)!==0)continue;const l=()=>{if(Array.from(E(this,ln).values()).includes(o)){var f=document.createDocumentFragment();Ho(i,f),f.append(Sn()),E(this,Fr).set(o,{effect:i,fragment:f})}else xr(i);E(this,_a).delete(o),E(this,bn).delete(o)};E(this,ws)||!a?(E(this,_a).add(o),wa(i,l,!1)):l()}}});Ye(this,Fs,t=>{E(this,ln).delete(t);const r=Array.from(E(this,ln).values());for(const[a,s]of E(this,Fr))r.includes(a)||(xr(s.effect),E(this,Fr).delete(a))});this.anchor=t,qe(this,ws,r)}ensure(t,r){var a=Be,s=gl();if(r&&!E(this,bn).has(t)&&!E(this,Fr).has(t))if(s){var o=document.createDocumentFragment(),i=Sn();o.append(i),E(this,Fr).set(t,{effect:Nr(()=>r(i)),fragment:o})}else E(this,bn).set(t,Nr(()=>r(this.anchor)));if(E(this,ln).set(a,t),s){for(const[l,c]of E(this,bn))l===t?a.unskip_effect(c):a.skip_effect(c);for(const[l,c]of E(this,Fr))l===t?a.unskip_effect(c.effect):a.skip_effect(c.effect);a.oncommit(E(this,ys)),a.ondiscard(E(this,Fs))}else E(this,ys).call(this,a)}}ln=new WeakMap,bn=new WeakMap,Fr=new WeakMap,_a=new WeakMap,ws=new WeakMap,ys=new WeakMap,Fs=new WeakMap;function z(e,t,r=!1){var a=new Ws(e),s=r?jn:0;function o(i,l){a.ensure(i,l)}Za(()=>{var i=!1;t((l,c=0)=>{i=!0,o(c,l)}),i||o(-1,null)},s)}function Te(e,t){return t}function gu(e,t,r){for(var a=[],s=t.length,o,i=t.length,l=0;l<s;l++){let b=t[l];wa(b,()=>{if(o){if(o.pending.delete(b),o.done.add(b),o.pending.size===0){var w=e.outrogroups;Mo(e,qs(o.done)),w.delete(o),w.size===0&&(e.outrogroups=null)}}else i-=1},!1)}if(i===0){var c=a.length===0&&r!==null;if(c){var f=r,p=f.parentNode;Wc(p),p.append(f),e.items.clear()}Mo(e,t,!c)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function Mo(e,t,r=!0){var a;if(e.pending.size>0){a=new Set;for(const i of e.pending.values())for(const l of i)a.add(e.items.get(l).e)}for(var s=0;s<t.length;s++){var o=t[s];if(a!=null&&a.has(o)){o.f|=_n;const i=document.createDocumentFragment();Ho(o,i)}else xr(t[s],r)}}var hi;function Ie(e,t,r,a,s,o=null){var i=e,l=new Map,c=(t&Yi)!==0;if(c){var f=e;i=f.appendChild(Sn())}var p=null,b=Ro(()=>{var Y=r();return $o(Y)?Y:Y==null?[]:qs(Y)}),w,A=new Map,k=!0;function P(Y){(j.effect.f&yn)===0&&(j.pending.delete(Y),j.fallback=p,xu(j,w,i,t,a),p!==null&&(w.length===0?(p.f&_n)===0?Go(p):(p.f^=_n,fs(p,null,i)):wa(p,()=>{p=null})))}function y(Y){j.pending.delete(Y)}var C=Za(()=>{w=n(b);for(var Y=w.length,M=new Set,G=Be,de=gl(),$=0;$<Y;$+=1){var g=w[$],K=a(g,$),ee=k?null:l.get(K);ee?(ee.v&&Ua(ee.v,g),ee.i&&Ua(ee.i,$),de&&G.unskip_effect(ee.e)):(ee=bu(l,k?i:hi??(hi=Sn()),g,K,$,s,t,r),k||(ee.e.f|=_n),l.set(K,ee)),M.add(K)}if(Y===0&&o&&!p&&(k?p=Nr(()=>o(i)):(p=Nr(()=>o(hi??(hi=Sn()))),p.f|=_n)),Y>M.size&&Qd(),!k)if(A.set(G,M),de){for(const[Z,L]of l)M.has(Z)||G.skip_effect(L.e);G.oncommit(P),G.ondiscard(y)}else P(G);n(b)}),j={effect:C,items:l,pending:A,outrogroups:null,fallback:p};k=!1}function os(e){for(;e!==null&&(e.f&un)===0;)e=e.next;return e}function xu(e,t,r,a,s){var ee,Z,L,ce,te,we,Ce,Pe,ye;var o=(a&cc)!==0,i=t.length,l=e.items,c=os(e.effect.first),f,p=null,b,w=[],A=[],k,P,y,C;if(o)for(C=0;C<i;C+=1)k=t[C],P=s(k,C),y=l.get(P).e,(y.f&_n)===0&&((Z=(ee=y.nodes)==null?void 0:ee.a)==null||Z.measure(),(b??(b=new Set)).add(y));for(C=0;C<i;C+=1){if(k=t[C],P=s(k,C),y=l.get(P).e,e.outrogroups!==null)for(const ue of e.outrogroups)ue.pending.delete(y),ue.done.delete(y);if((y.f&_n)!==0)if(y.f^=_n,y===c)fs(y,null,r);else{var j=p?p.next:c;y===e.effect.last&&(e.effect.last=y.prev),y.prev&&(y.prev.next=y.next),y.next&&(y.next.prev=y.prev),Un(e,p,y),Un(e,y,j),fs(y,j,r),p=y,w=[],A=[],c=os(p.next);continue}if((y.f&Er)!==0&&(Go(y),o&&((ce=(L=y.nodes)==null?void 0:L.a)==null||ce.unfix(),(b??(b=new Set)).delete(y))),y!==c){if(f!==void 0&&f.has(y)){if(w.length<A.length){var Y=A[0],M;p=Y.prev;var G=w[0],de=w[w.length-1];for(M=0;M<w.length;M+=1)fs(w[M],Y,r);for(M=0;M<A.length;M+=1)f.delete(A[M]);Un(e,G.prev,de.next),Un(e,p,G),Un(e,de,Y),c=Y,p=de,C-=1,w=[],A=[]}else f.delete(y),fs(y,c,r),Un(e,y.prev,y.next),Un(e,y,p===null?e.effect.first:p.next),Un(e,p,y),p=y;continue}for(w=[],A=[];c!==null&&c!==y;)(f??(f=new Set)).add(c),A.push(c),c=os(c.next);if(c===null)continue}(y.f&_n)===0&&w.push(y),p=y,c=os(y.next)}if(e.outrogroups!==null){for(const ue of e.outrogroups)ue.pending.size===0&&(Mo(e,qs(ue.done)),(te=e.outrogroups)==null||te.delete(ue));e.outrogroups.size===0&&(e.outrogroups=null)}if(c!==null||f!==void 0){var $=[];if(f!==void 0)for(y of f)(y.f&Er)===0&&$.push(y);for(;c!==null;)(c.f&Er)===0&&c!==e.fallback&&$.push(c),c=os(c.next);var g=$.length;if(g>0){var K=(a&Yi)!==0&&i===0?r:null;if(o){for(C=0;C<g;C+=1)(Ce=(we=$[C].nodes)==null?void 0:we.a)==null||Ce.measure();for(C=0;C<g;C+=1)(ye=(Pe=$[C].nodes)==null?void 0:Pe.a)==null||ye.fix()}gu(e,$,K)}}o&&Cn(()=>{var ue,B;if(b!==void 0)for(y of b)(B=(ue=y.nodes)==null?void 0:ue.a)==null||B.apply()})}function bu(e,t,r,a,s,o,i,l){var c=(i&lc)!==0?(i&uc)===0?Bc(r,!1,!1):sa(r):null,f=(i&dc)!==0?sa(s):null;return{v:c,i:f,e:Nr(()=>(o(t,c??r,f??s,l),()=>{e.delete(a)}))}}function fs(e,t,r){if(e.nodes)for(var a=e.nodes.start,s=e.nodes.end,o=t&&(t.f&_n)===0?t.nodes.start:r;a!==null;){var i=Ms(a);if(o.before(a),a===s)return;a=i}}function Un(e,t,r){t===null?e.effect.first=r:t.next=r,r===null?e.effect.last=t:r.prev=t}function ea(e,t,r=!1,a=!1,s=!1){var o=e,i="";O(()=>{var l=We;if(i!==(i=t()??"")&&(l.nodes!==null&&(kl(l.nodes.start,l.nodes.end),l.nodes=null),i!=="")){var c=r?Qi:a?xc:void 0,f=jo(r?"svg":a?"math":"template",c);f.innerHTML=i;var p=r||a?f:f.content;if(Ma(Rn(p),p.lastChild),r||a)for(;Rn(p);)o.before(Rn(p));else o.before(p)}})}function Re(e,t,r,a,s){var l;var o=(l=t.$$slots)==null?void 0:l[r],i=!1;o===!0&&(o=t.children,i=!0),o===void 0||o(e,i?()=>a:a)}function Eo(e,t,...r){var a=new Ws(e);Za(()=>{const s=t()??null;a.ensure(s,s&&(o=>s(o,...r)))},jn)}function _u(e,t,r){var a=new Ws(e);Za(()=>{var s=t()??null;a.ensure(s,s&&(o=>r(o,s)))},jn)}function wu(e,t,r,a,s,o){var i=null,l=e,c=new Ws(l,!1);Za(()=>{const f=t()||null;var p=Qi;if(f===null){c.ensure(null,null);return}return c.ensure(f,b=>{if(f){if(i=jo(f,p),Ma(i,i),a){var w=i.appendChild(Sn());a(i,w)}We.nodes.end=i,b.before(i)}}),()=>{}},jn),Us(()=>{})}function yu(e,t){var r=void 0,a;wl(()=>{r!==(r=t())&&(a&&(xr(a),a=null),r&&(a=Nr(()=>{Fo(()=>r(e))})))})}function Rl(e){var t,r,a="";if(typeof e=="string"||typeof e=="number")a+=e;else if(typeof e=="object")if(Array.isArray(e)){var s=e.length;for(t=0;t<s;t++)e[t]&&(r=Rl(e[t]))&&(a&&(a+=" "),a+=r)}else for(r in e)e[r]&&(a&&(a+=" "),a+=r);return a}function Dl(){for(var e,t,r=0,a="",s=arguments.length;r<s;r++)(e=arguments[r])&&(t=Rl(e))&&(a&&(a+=" "),a+=t);return a}function Ct(e){return typeof e=="object"?Dl(e):e??""}const gi=[...` 	
\r\f \v\uFEFF`];function ku(e,t,r){var a=e==null?"":""+e;if(t&&(a=a?a+" "+t:t),r){for(var s of Object.keys(r))if(r[s])a=a?a+" "+s:s;else if(a.length)for(var o=s.length,i=0;(i=a.indexOf(s,i))>=0;){var l=i+o;(i===0||gi.includes(a[i-1]))&&(l===a.length||gi.includes(a[l]))?a=(i===0?"":a.substring(0,i))+a.substring(l+1):i=l}}return a===""?null:a}function xi(e,t=!1){var r=t?" !important;":";",a="";for(var s of Object.keys(e)){var o=e[s];o!=null&&o!==""&&(a+=" "+s+": "+o+r)}return a}function ro(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Cu(e,t){if(t){var r="",a,s;if(Array.isArray(t)?(a=t[0],s=t[1]):a=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,i=0,l=!1,c=[];a&&c.push(...Object.keys(a).map(ro)),s&&c.push(...Object.keys(s).map(ro));var f=0,p=-1;const P=e.length;for(var b=0;b<P;b++){var w=e[b];if(l?w==="/"&&e[b-1]==="*"&&(l=!1):o?o===w&&(o=!1):w==="/"&&e[b+1]==="*"?l=!0:w==='"'||w==="'"?o=w:w==="("?i++:w===")"&&i--,!l&&o===!1&&i===0){if(w===":"&&p===-1)p=b;else if(w===";"||b===P-1){if(p!==-1){var A=ro(e.substring(f,p).trim());if(!c.includes(A)){w!==";"&&b++;var k=e.substring(f,b).trim();r+=" "+k+";"}}f=b+1,p=-1}}}}return a&&(r+=xi(a)),s&&(r+=xi(s,!0)),r=r.trim(),r===""?null:r}return e==null?null:String(e)}function $e(e,t,r,a,s,o){var i=e.__className;if(i!==r||i===void 0){var l=ku(r,a,o);l==null?e.removeAttribute("class"):t?e.className=l:e.setAttribute("class",l),e.__className=r}else if(o&&s!==o)for(var c in o){var f=!!o[c];(s==null||f!==!!s[c])&&e.classList.toggle(c,f)}return o}function no(e,t={},r,a){for(var s in r){var o=r[s];t[s]!==o&&(r[s]==null?e.style.removeProperty(s):e.style.setProperty(s,o,a))}}function zo(e,t,r,a){var s=e.__style;if(s!==t){var o=Cu(t,a);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else a&&(Array.isArray(a)?(no(e,r==null?void 0:r[0],a[0]),no(e,r==null?void 0:r[1],a[1],"important")):no(e,r,a));return a}function Ao(e,t,r=!1){if(e.multiple){if(t==null)return;if(!$o(t))return _c();for(var a of e.options)a.selected=t.includes(bi(a));return}for(a of e.options){var s=bi(a);if(Hc(s,t)){a.selected=!0;return}}(!r||t!==void 0)&&(e.selectedIndex=-1)}function Su(e){var t=new MutationObserver(()=>{Ao(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Us(()=>{t.disconnect()})}function bi(e){return"__value"in e?e.__value:e.value}const is=Symbol("class"),ls=Symbol("style"),jl=Symbol("is custom element"),Vl=Symbol("is html"),Mu=Ki?"option":"OPTION",Eu=Ki?"select":"SELECT";function zu(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function Dn(e,t,r,a){var s=Fl(e);s[t]!==(s[t]=r)&&(t==="loading"&&(e[Xd]=r),r==null?e.removeAttribute(t):typeof r!="string"&&ql(e).includes(t)?e[t]=r:e.setAttribute(t,r))}function Au(e,t,r,a,s=!1,o=!1){var i=Fl(e),l=i[jl],c=!i[Vl],f=t||{},p=e.nodeName===Mu;for(var b in t)b in r||(r[b]=null);r.class?r.class=Ct(r.class):r[is]&&(r.class=null),r[ls]&&(r.style??(r.style=null));var w=ql(e);for(const M in r){let G=r[M];if(p&&M==="value"&&G==null){e.value=e.__value="",f[M]=G;continue}if(M==="class"){var A=e.namespaceURI==="http://www.w3.org/1999/xhtml";$e(e,A,G,a,t==null?void 0:t[is],r[is]),f[M]=G,f[is]=r[is];continue}if(M==="style"){zo(e,G,t==null?void 0:t[ls],r[ls]),f[M]=G,f[ls]=r[ls];continue}var k=f[M];if(!(G===k&&!(G===void 0&&e.hasAttribute(M)))){f[M]=G;var P=M[0]+M[1];if(P!=="$$")if(P==="on"){const de={},$="$$"+M;let g=M.slice(2);var y=ou(g);if(au(g)&&(g=g.slice(0,-7),de.capture=!0),!y&&k){if(G!=null)continue;e.removeEventListener(g,f[$],de),f[$]=null}if(y)re(g,e,G),Vn([g]);else if(G!=null){let K=function(ee){f[M].call(this,ee)};var Y=K;f[$]=Ol(g,e,K,de)}}else if(M==="style")Dn(e,M,G);else if(M==="autofocus")xl(e,!!G);else if(!l&&(M==="__value"||M==="value"&&G!=null))e.value=e.__value=G;else if(M==="selected"&&p)zu(e,G);else{var C=M;c||(C=lu(C));var j=C==="defaultValue"||C==="defaultChecked";if(G==null&&!l&&!j)if(i[M]=null,C==="value"||C==="checked"){let de=e;const $=t===void 0;if(C==="value"){let g=de.defaultValue;de.removeAttribute(C),de.defaultValue=g,de.value=de.__value=$?g:null}else{let g=de.defaultChecked;de.removeAttribute(C),de.defaultChecked=g,de.checked=$?g:!1}}else e.removeAttribute(M);else j||w.includes(C)&&(l||typeof G!="string")?(e[C]=G,C in i&&(i[C]=sr)):typeof G!="function"&&Dn(e,C,G)}}}return f}function Rs(e,t,r=[],a=[],s=[],o,i=!1,l=!1){dl(s,r,a,c=>{var f=void 0,p={},b=e.nodeName===Eu,w=!1;if(wl(()=>{var k=t(...c.map(n)),P=Au(e,f,k,o,i,l);w&&b&&"value"in k&&Ao(e,k.value);for(let C of Object.getOwnPropertySymbols(p))k[C]||xr(p[C]);for(let C of Object.getOwnPropertySymbols(k)){var y=k[C];C.description===bc&&(!f||y!==f[C])&&(p[C]&&xr(p[C]),p[C]=Nr(()=>yu(e,()=>y))),P[C]=y}f=P}),b){var A=e;Fo(()=>{Ao(A,f.value,!0),Su(A)})}w=!0})}function Fl(e){return e.__attributes??(e.__attributes={[jl]:e.nodeName.includes("-"),[Vl]:e.namespaceURI===Ji})}var _i=new Map;function ql(e){var t=e.getAttribute("is")||e.nodeName,r=_i.get(t);if(r)return r;_i.set(t,r=[]);for(var a,s=e,o=Element.prototype;o!==s;){a=Bi(s);for(var i in a)a[i].set&&r.push(i);s=No(s)}return r}function $a(e,t,r=t){var a=new WeakSet;Yc(e,"input",async s=>{var o=s?e.defaultValue:e.value;if(o=ao(e)?so(o):o,r(o),Be!==null&&a.add(Be),await nu(),o!==(o=t())){var i=e.selectionStart,l=e.selectionEnd,c=e.value.length;if(e.value=o??"",l!==null){var f=e.value.length;i===l&&l===c&&f>c?(e.selectionStart=f,e.selectionEnd=f):(e.selectionStart=i,e.selectionEnd=Math.min(l,f))}}}),Sa(t)==null&&e.value&&(r(ao(e)?so(e.value):e.value),Be!==null&&a.add(Be)),qo(()=>{var s=t();if(e===document.activeElement){var o=vo??Be;if(a.has(o))return}ao(e)&&s===so(e.value)||e.type==="date"&&!s&&!e.value||s!==e.value&&(e.value=s??"")})}function ao(e){var t=e.type;return t==="number"||t==="range"}function so(e){return e===""?null:+e}function wi(e,t){return e===t||(e==null?void 0:e[kn])===t}function Ka(e={},t,r,a){return Fo(()=>{var s,o;return qo(()=>{s=o,o=[],Sa(()=>{e!==r(...o)&&(t(e,...o),s&&wi(r(...s),e)&&t(null,...s))})}),()=>{Cn(()=>{o&&wi(r(...o),e)&&t(null,...o)})}}),e}function Tu(e=!1){const t=or,r=t.l.u;if(!r)return;let a=()=>fa(t.s);if(e){let s=0,o={};const i=Ss(()=>{let l=!1;const c=t.s;for(const f in c)c[f]!==o[f]&&(o[f]=c[f],l=!0);return l&&s++,s});a=()=>n(i)}r.b.length&&Jc(()=>{yi(t,a),co(r.b)}),Zn(()=>{const s=Sa(()=>r.m.map(Kd));return()=>{for(const o of s)typeof o=="function"&&o()}}),r.a.length&&Zn(()=>{yi(t,a),co(r.a)})}function yi(e,t){if(e.l.s)for(const r of e.l.s)n(r);t()}let Is=!1;function Iu(e){var t=Is;try{return Is=!1,[e(),Is]}finally{Is=t}}const Pu={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function $u(e,t,r){return new Proxy({props:e,exclude:t},Pu)}const Nu={get(e,t){if(!e.exclude.includes(t))return n(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,r){if(!(t in e.special)){var a=We;try{Zr(e.parent_effect),e.special[t]=nt({get[t](){return e.props[t]}},t,Xi)}finally{Zr(a)}}return e.special[t](r),ps(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),ps(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Ne(e,t){return new Proxy({props:e,exclude:t,special:{},version:sa(0),parent_effect:We},Nu)}const Ou={get(e,t){let r=e.props.length;for(;r--;){let a=e.props[r];if(ss(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a)return a[t]}},set(e,t,r){let a=e.props.length;for(;a--;){let s=e.props[a];ss(s)&&(s=s());const o=ta(s,t);if(o&&o.set)return o.set(r),!0}return!1},getOwnPropertyDescriptor(e,t){let r=e.props.length;for(;r--;){let a=e.props[r];if(ss(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a){const s=ta(a,t);return s&&!s.configurable&&(s.configurable=!0),s}}},has(e,t){if(t===kn||t===Wi)return!1;for(let r of e.props)if(ss(r)&&(r=r()),r!=null&&t in r)return!0;return!1},ownKeys(e){const t=[];for(let r of e.props)if(ss(r)&&(r=r()),!!r){for(const a in r)t.includes(a)||t.push(a);for(const a of Object.getOwnPropertySymbols(r))t.includes(a)||t.push(a)}return t}};function Ge(...e){return new Proxy({props:e},Ou)}function nt(e,t,r,a){var Y;var s=!ks||(r&vc)!==0,o=(r&pc)!==0,i=(r&mc)!==0,l=a,c=!0,f=()=>(c&&(c=!1,l=i?Sa(a):a),l),p;if(o){var b=kn in e||Wi in e;p=((Y=ta(e,t))==null?void 0:Y.set)??(b&&t in e?M=>e[t]=M:void 0)}var w,A=!1;o?[w,A]=Iu(()=>e[t]):w=e[t],w===void 0&&a!==void 0&&(w=f(),p&&(s&&nc(),p(w)));var k;if(s?k=()=>{var M=e[t];return M===void 0?f():(c=!0,M)}:k=()=>{var M=e[t];return M!==void 0&&(l=void 0),M===void 0?l:M},s&&(r&Xi)===0)return k;if(p){var P=e.$$legacy;return(function(M,G){return arguments.length>0?((!s||!G||P||A)&&p(G?k():M),M):k()})}var y=!1,C=((r&fc)!==0?Ss:Ro)(()=>(y=!1,k()));o&&n(C);var j=We;return(function(M,G){if(arguments.length>0){const de=G?n(C):s&&o?Et(M):M;return u(C,de),y=!0,l!==void 0&&(l=de),M}return oa&&y||(j.f&yn)!==0?C.v:n(C)})}const Lu="5";var qi;typeof window<"u"&&((qi=window.__svelte??(window.__svelte={})).v??(qi.v=new Set)).add(Lu);const rn="";async function Ru(){const e=await fetch(`${rn}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function Pa(e,t=null,r=null){const a={provider:e};t&&(a.model=t),r&&(a.api_key=r);const s=await fetch(`${rn}/api/configure`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!s.ok)throw new Error("설정 실패");return s.json()}async function Du(e){const t=await fetch(`${rn}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function ju(e,{onProgress:t,onDone:r,onError:a}){const s=new AbortController;return fetch(`${rn}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:s.signal}).then(async o=>{if(!o.ok){a==null||a("다운로드 실패");return}const i=o.body.getReader(),l=new TextDecoder;let c="";for(;;){const{done:f,value:p}=await i.read();if(f)break;c+=l.decode(p,{stream:!0});const b=c.split(`
`);c=b.pop()||"";for(const w of b)if(w.startsWith("data:"))try{const A=JSON.parse(w.slice(5).trim());A.total&&A.completed!==void 0?t==null||t({total:A.total,completed:A.completed,status:A.status}):A.status&&(t==null||t({status:A.status}))}catch{}}r==null||r()}).catch(o=>{o.name!=="AbortError"&&(a==null||a(o.message))}),{abort:()=>s.abort()}}async function Vu(){const e=await fetch(`${rn}/api/oauth/authorize`);if(!e.ok)throw new Error("OAuth 인증 시작 실패");return e.json()}async function Fu(){const e=await fetch(`${rn}/api/oauth/status`);return e.ok?e.json():{done:!1}}async function qu(){const e=await fetch(`${rn}/api/oauth/logout`,{method:"POST"});if(!e.ok)throw new Error("로그아웃 실패");return e.json()}async function Bu(e,t=null,r=null){let a=`${rn}/api/export/excel/${encodeURIComponent(e)}`;const s=new URLSearchParams;r?s.set("template_id",r):t&&t.length>0&&s.set("modules",t.join(","));const o=s.toString();o&&(a+=`?${o}`);const i=await fetch(a);if(!i.ok){const w=await i.json().catch(()=>({}));throw new Error(w.detail||"Excel 다운로드 실패")}const l=await i.blob(),f=(i.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),p=f?decodeURIComponent(f[1]):`${e}.xlsx`,b=document.createElement("a");return b.href=URL.createObjectURL(l),b.download=p,b.click(),URL.revokeObjectURL(b.href),p}async function Bl(e){const t=await fetch(`${rn}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}async function Gu(e,t){const r=await fetch(`${rn}/api/company/${e}/show/${encodeURIComponent(t)}/all`);if(!r.ok)throw new Error("company topic 일괄 조회 실패");return r.json()}async function Hu(e){const t=await fetch(`${rn}/api/company/${e}/sections`);if(!t.ok)throw new Error("sections 조회 실패");return t.json()}function Uu(e,t,r={},{onMeta:a,onSnapshot:s,onContext:o,onSystemPrompt:i,onToolCall:l,onToolResult:c,onChunk:f,onDone:p,onError:b},w=null){const A={question:t,stream:!0,...r};e&&(A.company=e),w&&w.length>0&&(A.history=w);const k=new AbortController;return fetch(`${rn}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(A),signal:k.signal}).then(async P=>{if(!P.ok){const G=await P.json().catch(()=>({}));b==null||b(G.detail||"스트리밍 실패");return}const y=P.body.getReader(),C=new TextDecoder;let j="",Y=!1,M=null;for(;;){const{done:G,value:de}=await y.read();if(G)break;j+=C.decode(de,{stream:!0});const $=j.split(`
`);j=$.pop()||"";for(const g of $)if(g.startsWith("event:"))M=g.slice(6).trim();else if(g.startsWith("data:")&&M){const K=g.slice(5).trim();try{const ee=JSON.parse(K);M==="meta"?a==null||a(ee):M==="snapshot"?s==null||s(ee):M==="context"?o==null||o(ee):M==="system_prompt"?i==null||i(ee):M==="tool_call"?l==null||l(ee):M==="tool_result"?c==null||c(ee):M==="chunk"?f==null||f(ee.text):M==="error"?b==null||b(ee.error,ee.action,ee.detail):M==="done"&&(Y||(Y=!0,p==null||p()))}catch{}M=null}}Y||(Y=!0,p==null||p())}).catch(P=>{P.name!=="AbortError"&&(b==null||b(P.message))}),{abort:()=>k.abort()}}const Wu=(e,t)=>{const r=new Array(e.length+t.length);for(let a=0;a<e.length;a++)r[a]=e[a];for(let a=0;a<t.length;a++)r[e.length+a]=t[a];return r},Ku=(e,t)=>({classGroupId:e,validator:t}),Gl=(e=new Map,t=null,r)=>({nextPart:e,validators:t,classGroupId:r}),Ds="-",ki=[],Yu="arbitrary..",Xu=e=>{const t=Qu(e),{conflictingClassGroups:r,conflictingClassGroupModifiers:a}=e;return{getClassGroupId:i=>{if(i.startsWith("[")&&i.endsWith("]"))return Ju(i);const l=i.split(Ds),c=l[0]===""&&l.length>1?1:0;return Hl(l,c,t)},getConflictingClassGroupIds:(i,l)=>{if(l){const c=a[i],f=r[i];return c?f?Wu(f,c):c:f||ki}return r[i]||ki}}},Hl=(e,t,r)=>{if(e.length-t===0)return r.classGroupId;const s=e[t],o=r.nextPart.get(s);if(o){const f=Hl(e,t+1,o);if(f)return f}const i=r.validators;if(i===null)return;const l=t===0?e.join(Ds):e.slice(t).join(Ds),c=i.length;for(let f=0;f<c;f++){const p=i[f];if(p.validator(l))return p.classGroupId}},Ju=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),r=t.indexOf(":"),a=t.slice(0,r);return a?Yu+a:void 0})(),Qu=e=>{const{theme:t,classGroups:r}=e;return Zu(r,t)},Zu=(e,t)=>{const r=Gl();for(const a in e){const s=e[a];Uo(s,r,a,t)}return r},Uo=(e,t,r,a)=>{const s=e.length;for(let o=0;o<s;o++){const i=e[o];ef(i,t,r,a)}},ef=(e,t,r,a)=>{if(typeof e=="string"){tf(e,t,r);return}if(typeof e=="function"){rf(e,t,r,a);return}nf(e,t,r,a)},tf=(e,t,r)=>{const a=e===""?t:Ul(t,e);a.classGroupId=r},rf=(e,t,r,a)=>{if(af(e)){Uo(e(a),t,r,a);return}t.validators===null&&(t.validators=[]),t.validators.push(Ku(r,e))},nf=(e,t,r,a)=>{const s=Object.entries(e),o=s.length;for(let i=0;i<o;i++){const[l,c]=s[i];Uo(c,Ul(t,l),r,a)}},Ul=(e,t)=>{let r=e;const a=t.split(Ds),s=a.length;for(let o=0;o<s;o++){const i=a[o];let l=r.nextPart.get(i);l||(l=Gl(),r.nextPart.set(i,l)),r=l}return r},af=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,sf=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,r=Object.create(null),a=Object.create(null);const s=(o,i)=>{r[o]=i,t++,t>e&&(t=0,a=r,r=Object.create(null))};return{get(o){let i=r[o];if(i!==void 0)return i;if((i=a[o])!==void 0)return s(o,i),i},set(o,i){o in r?r[o]=i:s(o,i)}}},To="!",Ci=":",of=[],Si=(e,t,r,a,s)=>({modifiers:e,hasImportantModifier:t,baseClassName:r,maybePostfixModifierPosition:a,isExternal:s}),lf=e=>{const{prefix:t,experimentalParseClassName:r}=e;let a=s=>{const o=[];let i=0,l=0,c=0,f;const p=s.length;for(let P=0;P<p;P++){const y=s[P];if(i===0&&l===0){if(y===Ci){o.push(s.slice(c,P)),c=P+1;continue}if(y==="/"){f=P;continue}}y==="["?i++:y==="]"?i--:y==="("?l++:y===")"&&l--}const b=o.length===0?s:s.slice(c);let w=b,A=!1;b.endsWith(To)?(w=b.slice(0,-1),A=!0):b.startsWith(To)&&(w=b.slice(1),A=!0);const k=f&&f>c?f-c:void 0;return Si(o,A,w,k)};if(t){const s=t+Ci,o=a;a=i=>i.startsWith(s)?o(i.slice(s.length)):Si(of,!1,i,void 0,!0)}if(r){const s=a;a=o=>r({className:o,parseClassName:s})}return a},df=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((r,a)=>{t.set(r,1e6+a)}),r=>{const a=[];let s=[];for(let o=0;o<r.length;o++){const i=r[o],l=i[0]==="[",c=t.has(i);l||c?(s.length>0&&(s.sort(),a.push(...s),s=[]),a.push(i)):s.push(i)}return s.length>0&&(s.sort(),a.push(...s)),a}},cf=e=>({cache:sf(e.cacheSize),parseClassName:lf(e),sortModifiers:df(e),...Xu(e)}),uf=/\s+/,ff=(e,t)=>{const{parseClassName:r,getClassGroupId:a,getConflictingClassGroupIds:s,sortModifiers:o}=t,i=[],l=e.trim().split(uf);let c="";for(let f=l.length-1;f>=0;f-=1){const p=l[f],{isExternal:b,modifiers:w,hasImportantModifier:A,baseClassName:k,maybePostfixModifierPosition:P}=r(p);if(b){c=p+(c.length>0?" "+c:c);continue}let y=!!P,C=a(y?k.substring(0,P):k);if(!C){if(!y){c=p+(c.length>0?" "+c:c);continue}if(C=a(k),!C){c=p+(c.length>0?" "+c:c);continue}y=!1}const j=w.length===0?"":w.length===1?w[0]:o(w).join(":"),Y=A?j+To:j,M=Y+C;if(i.indexOf(M)>-1)continue;i.push(M);const G=s(C,y);for(let de=0;de<G.length;++de){const $=G[de];i.push(Y+$)}c=p+(c.length>0?" "+c:c)}return c},vf=(...e)=>{let t=0,r,a,s="";for(;t<e.length;)(r=e[t++])&&(a=Wl(r))&&(s&&(s+=" "),s+=a);return s},Wl=e=>{if(typeof e=="string")return e;let t,r="";for(let a=0;a<e.length;a++)e[a]&&(t=Wl(e[a]))&&(r&&(r+=" "),r+=t);return r},pf=(e,...t)=>{let r,a,s,o;const i=c=>{const f=t.reduce((p,b)=>b(p),e());return r=cf(f),a=r.cache.get,s=r.cache.set,o=l,l(c)},l=c=>{const f=a(c);if(f)return f;const p=ff(c,r);return s(c,p),p};return o=i,(...c)=>o(vf(...c))},mf=[],tr=e=>{const t=r=>r[e]||mf;return t.isThemeGetter=!0,t},Kl=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Yl=/^\((?:(\w[\w-]*):)?(.+)\)$/i,hf=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,gf=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,xf=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,bf=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,_f=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,wf=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,Wn=e=>hf.test(e),Le=e=>!!e&&!Number.isNaN(Number(e)),Kn=e=>!!e&&Number.isInteger(Number(e)),oo=e=>e.endsWith("%")&&Le(e.slice(0,-1)),$n=e=>gf.test(e),Xl=()=>!0,yf=e=>xf.test(e)&&!bf.test(e),Wo=()=>!1,kf=e=>_f.test(e),Cf=e=>wf.test(e),Sf=e=>!ae(e)&&!oe(e),Mf=e=>la(e,Zl,Wo),ae=e=>Kl.test(e),ua=e=>la(e,ed,yf),Mi=e=>la(e,Nf,Le),Ef=e=>la(e,rd,Xl),zf=e=>la(e,td,Wo),Ei=e=>la(e,Jl,Wo),Af=e=>la(e,Ql,Cf),Ps=e=>la(e,nd,kf),oe=e=>Yl.test(e),ds=e=>za(e,ed),Tf=e=>za(e,td),zi=e=>za(e,Jl),If=e=>za(e,Zl),Pf=e=>za(e,Ql),$s=e=>za(e,nd,!0),$f=e=>za(e,rd,!0),la=(e,t,r)=>{const a=Kl.exec(e);return a?a[1]?t(a[1]):r(a[2]):!1},za=(e,t,r=!1)=>{const a=Yl.exec(e);return a?a[1]?t(a[1]):r:!1},Jl=e=>e==="position"||e==="percentage",Ql=e=>e==="image"||e==="url",Zl=e=>e==="length"||e==="size"||e==="bg-size",ed=e=>e==="length",Nf=e=>e==="number",td=e=>e==="family-name",rd=e=>e==="number"||e==="weight",nd=e=>e==="shadow",Of=()=>{const e=tr("color"),t=tr("font"),r=tr("text"),a=tr("font-weight"),s=tr("tracking"),o=tr("leading"),i=tr("breakpoint"),l=tr("container"),c=tr("spacing"),f=tr("radius"),p=tr("shadow"),b=tr("inset-shadow"),w=tr("text-shadow"),A=tr("drop-shadow"),k=tr("blur"),P=tr("perspective"),y=tr("aspect"),C=tr("ease"),j=tr("animate"),Y=()=>["auto","avoid","all","avoid-page","page","left","right","column"],M=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],G=()=>[...M(),oe,ae],de=()=>["auto","hidden","clip","visible","scroll"],$=()=>["auto","contain","none"],g=()=>[oe,ae,c],K=()=>[Wn,"full","auto",...g()],ee=()=>[Kn,"none","subgrid",oe,ae],Z=()=>["auto",{span:["full",Kn,oe,ae]},Kn,oe,ae],L=()=>[Kn,"auto",oe,ae],ce=()=>["auto","min","max","fr",oe,ae],te=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],we=()=>["start","end","center","stretch","center-safe","end-safe"],Ce=()=>["auto",...g()],Pe=()=>[Wn,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...g()],ye=()=>[Wn,"screen","full","dvw","lvw","svw","min","max","fit",...g()],ue=()=>[Wn,"screen","full","lh","dvh","lvh","svh","min","max","fit",...g()],B=()=>[e,oe,ae],T=()=>[...M(),zi,Ei,{position:[oe,ae]}],V=()=>["no-repeat",{repeat:["","x","y","space","round"]}],ne=()=>["auto","cover","contain",If,Mf,{size:[oe,ae]}],se=()=>[oo,ds,ua],me=()=>["","none","full",f,oe,ae],fe=()=>["",Le,ds,ua],he=()=>["solid","dashed","dotted","double"],ze=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],X=()=>[Le,oo,zi,Ei],qt=()=>["","none",k,oe,ae],ut=()=>["none",Le,oe,ae],zt=()=>["none",Le,oe,ae],Ze=()=>[Le,oe,ae],De=()=>[Wn,"full",...g()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[$n],breakpoint:[$n],color:[Xl],container:[$n],"drop-shadow":[$n],ease:["in","out","in-out"],font:[Sf],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[$n],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[$n],shadow:[$n],spacing:["px",Le],text:[$n],"text-shadow":[$n],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",Wn,ae,oe,y]}],container:["container"],columns:[{columns:[Le,ae,oe,l]}],"break-after":[{"break-after":Y()}],"break-before":[{"break-before":Y()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:G()}],overflow:[{overflow:de()}],"overflow-x":[{"overflow-x":de()}],"overflow-y":[{"overflow-y":de()}],overscroll:[{overscroll:$()}],"overscroll-x":[{"overscroll-x":$()}],"overscroll-y":[{"overscroll-y":$()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:K()}],"inset-x":[{"inset-x":K()}],"inset-y":[{"inset-y":K()}],start:[{"inset-s":K(),start:K()}],end:[{"inset-e":K(),end:K()}],"inset-bs":[{"inset-bs":K()}],"inset-be":[{"inset-be":K()}],top:[{top:K()}],right:[{right:K()}],bottom:[{bottom:K()}],left:[{left:K()}],visibility:["visible","invisible","collapse"],z:[{z:[Kn,"auto",oe,ae]}],basis:[{basis:[Wn,"full","auto",l,...g()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[Le,Wn,"auto","initial","none",ae]}],grow:[{grow:["",Le,oe,ae]}],shrink:[{shrink:["",Le,oe,ae]}],order:[{order:[Kn,"first","last","none",oe,ae]}],"grid-cols":[{"grid-cols":ee()}],"col-start-end":[{col:Z()}],"col-start":[{"col-start":L()}],"col-end":[{"col-end":L()}],"grid-rows":[{"grid-rows":ee()}],"row-start-end":[{row:Z()}],"row-start":[{"row-start":L()}],"row-end":[{"row-end":L()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":ce()}],"auto-rows":[{"auto-rows":ce()}],gap:[{gap:g()}],"gap-x":[{"gap-x":g()}],"gap-y":[{"gap-y":g()}],"justify-content":[{justify:[...te(),"normal"]}],"justify-items":[{"justify-items":[...we(),"normal"]}],"justify-self":[{"justify-self":["auto",...we()]}],"align-content":[{content:["normal",...te()]}],"align-items":[{items:[...we(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...we(),{baseline:["","last"]}]}],"place-content":[{"place-content":te()}],"place-items":[{"place-items":[...we(),"baseline"]}],"place-self":[{"place-self":["auto",...we()]}],p:[{p:g()}],px:[{px:g()}],py:[{py:g()}],ps:[{ps:g()}],pe:[{pe:g()}],pbs:[{pbs:g()}],pbe:[{pbe:g()}],pt:[{pt:g()}],pr:[{pr:g()}],pb:[{pb:g()}],pl:[{pl:g()}],m:[{m:Ce()}],mx:[{mx:Ce()}],my:[{my:Ce()}],ms:[{ms:Ce()}],me:[{me:Ce()}],mbs:[{mbs:Ce()}],mbe:[{mbe:Ce()}],mt:[{mt:Ce()}],mr:[{mr:Ce()}],mb:[{mb:Ce()}],ml:[{ml:Ce()}],"space-x":[{"space-x":g()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":g()}],"space-y-reverse":["space-y-reverse"],size:[{size:Pe()}],"inline-size":[{inline:["auto",...ye()]}],"min-inline-size":[{"min-inline":["auto",...ye()]}],"max-inline-size":[{"max-inline":["none",...ye()]}],"block-size":[{block:["auto",...ue()]}],"min-block-size":[{"min-block":["auto",...ue()]}],"max-block-size":[{"max-block":["none",...ue()]}],w:[{w:[l,"screen",...Pe()]}],"min-w":[{"min-w":[l,"screen","none",...Pe()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[i]},...Pe()]}],h:[{h:["screen","lh",...Pe()]}],"min-h":[{"min-h":["screen","lh","none",...Pe()]}],"max-h":[{"max-h":["screen","lh",...Pe()]}],"font-size":[{text:["base",r,ds,ua]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[a,$f,Ef]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",oo,ae]}],"font-family":[{font:[Tf,zf,t]}],"font-features":[{"font-features":[ae]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[s,oe,ae]}],"line-clamp":[{"line-clamp":[Le,"none",oe,Mi]}],leading:[{leading:[o,...g()]}],"list-image":[{"list-image":["none",oe,ae]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",oe,ae]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:B()}],"text-color":[{text:B()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...he(),"wavy"]}],"text-decoration-thickness":[{decoration:[Le,"from-font","auto",oe,ua]}],"text-decoration-color":[{decoration:B()}],"underline-offset":[{"underline-offset":[Le,"auto",oe,ae]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:g()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",oe,ae]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",oe,ae]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:T()}],"bg-repeat":[{bg:V()}],"bg-size":[{bg:ne()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},Kn,oe,ae],radial:["",oe,ae],conic:[Kn,oe,ae]},Pf,Af]}],"bg-color":[{bg:B()}],"gradient-from-pos":[{from:se()}],"gradient-via-pos":[{via:se()}],"gradient-to-pos":[{to:se()}],"gradient-from":[{from:B()}],"gradient-via":[{via:B()}],"gradient-to":[{to:B()}],rounded:[{rounded:me()}],"rounded-s":[{"rounded-s":me()}],"rounded-e":[{"rounded-e":me()}],"rounded-t":[{"rounded-t":me()}],"rounded-r":[{"rounded-r":me()}],"rounded-b":[{"rounded-b":me()}],"rounded-l":[{"rounded-l":me()}],"rounded-ss":[{"rounded-ss":me()}],"rounded-se":[{"rounded-se":me()}],"rounded-ee":[{"rounded-ee":me()}],"rounded-es":[{"rounded-es":me()}],"rounded-tl":[{"rounded-tl":me()}],"rounded-tr":[{"rounded-tr":me()}],"rounded-br":[{"rounded-br":me()}],"rounded-bl":[{"rounded-bl":me()}],"border-w":[{border:fe()}],"border-w-x":[{"border-x":fe()}],"border-w-y":[{"border-y":fe()}],"border-w-s":[{"border-s":fe()}],"border-w-e":[{"border-e":fe()}],"border-w-bs":[{"border-bs":fe()}],"border-w-be":[{"border-be":fe()}],"border-w-t":[{"border-t":fe()}],"border-w-r":[{"border-r":fe()}],"border-w-b":[{"border-b":fe()}],"border-w-l":[{"border-l":fe()}],"divide-x":[{"divide-x":fe()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":fe()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...he(),"hidden","none"]}],"divide-style":[{divide:[...he(),"hidden","none"]}],"border-color":[{border:B()}],"border-color-x":[{"border-x":B()}],"border-color-y":[{"border-y":B()}],"border-color-s":[{"border-s":B()}],"border-color-e":[{"border-e":B()}],"border-color-bs":[{"border-bs":B()}],"border-color-be":[{"border-be":B()}],"border-color-t":[{"border-t":B()}],"border-color-r":[{"border-r":B()}],"border-color-b":[{"border-b":B()}],"border-color-l":[{"border-l":B()}],"divide-color":[{divide:B()}],"outline-style":[{outline:[...he(),"none","hidden"]}],"outline-offset":[{"outline-offset":[Le,oe,ae]}],"outline-w":[{outline:["",Le,ds,ua]}],"outline-color":[{outline:B()}],shadow:[{shadow:["","none",p,$s,Ps]}],"shadow-color":[{shadow:B()}],"inset-shadow":[{"inset-shadow":["none",b,$s,Ps]}],"inset-shadow-color":[{"inset-shadow":B()}],"ring-w":[{ring:fe()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:B()}],"ring-offset-w":[{"ring-offset":[Le,ua]}],"ring-offset-color":[{"ring-offset":B()}],"inset-ring-w":[{"inset-ring":fe()}],"inset-ring-color":[{"inset-ring":B()}],"text-shadow":[{"text-shadow":["none",w,$s,Ps]}],"text-shadow-color":[{"text-shadow":B()}],opacity:[{opacity:[Le,oe,ae]}],"mix-blend":[{"mix-blend":[...ze(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":ze()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[Le]}],"mask-image-linear-from-pos":[{"mask-linear-from":X()}],"mask-image-linear-to-pos":[{"mask-linear-to":X()}],"mask-image-linear-from-color":[{"mask-linear-from":B()}],"mask-image-linear-to-color":[{"mask-linear-to":B()}],"mask-image-t-from-pos":[{"mask-t-from":X()}],"mask-image-t-to-pos":[{"mask-t-to":X()}],"mask-image-t-from-color":[{"mask-t-from":B()}],"mask-image-t-to-color":[{"mask-t-to":B()}],"mask-image-r-from-pos":[{"mask-r-from":X()}],"mask-image-r-to-pos":[{"mask-r-to":X()}],"mask-image-r-from-color":[{"mask-r-from":B()}],"mask-image-r-to-color":[{"mask-r-to":B()}],"mask-image-b-from-pos":[{"mask-b-from":X()}],"mask-image-b-to-pos":[{"mask-b-to":X()}],"mask-image-b-from-color":[{"mask-b-from":B()}],"mask-image-b-to-color":[{"mask-b-to":B()}],"mask-image-l-from-pos":[{"mask-l-from":X()}],"mask-image-l-to-pos":[{"mask-l-to":X()}],"mask-image-l-from-color":[{"mask-l-from":B()}],"mask-image-l-to-color":[{"mask-l-to":B()}],"mask-image-x-from-pos":[{"mask-x-from":X()}],"mask-image-x-to-pos":[{"mask-x-to":X()}],"mask-image-x-from-color":[{"mask-x-from":B()}],"mask-image-x-to-color":[{"mask-x-to":B()}],"mask-image-y-from-pos":[{"mask-y-from":X()}],"mask-image-y-to-pos":[{"mask-y-to":X()}],"mask-image-y-from-color":[{"mask-y-from":B()}],"mask-image-y-to-color":[{"mask-y-to":B()}],"mask-image-radial":[{"mask-radial":[oe,ae]}],"mask-image-radial-from-pos":[{"mask-radial-from":X()}],"mask-image-radial-to-pos":[{"mask-radial-to":X()}],"mask-image-radial-from-color":[{"mask-radial-from":B()}],"mask-image-radial-to-color":[{"mask-radial-to":B()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":M()}],"mask-image-conic-pos":[{"mask-conic":[Le]}],"mask-image-conic-from-pos":[{"mask-conic-from":X()}],"mask-image-conic-to-pos":[{"mask-conic-to":X()}],"mask-image-conic-from-color":[{"mask-conic-from":B()}],"mask-image-conic-to-color":[{"mask-conic-to":B()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:T()}],"mask-repeat":[{mask:V()}],"mask-size":[{mask:ne()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",oe,ae]}],filter:[{filter:["","none",oe,ae]}],blur:[{blur:qt()}],brightness:[{brightness:[Le,oe,ae]}],contrast:[{contrast:[Le,oe,ae]}],"drop-shadow":[{"drop-shadow":["","none",A,$s,Ps]}],"drop-shadow-color":[{"drop-shadow":B()}],grayscale:[{grayscale:["",Le,oe,ae]}],"hue-rotate":[{"hue-rotate":[Le,oe,ae]}],invert:[{invert:["",Le,oe,ae]}],saturate:[{saturate:[Le,oe,ae]}],sepia:[{sepia:["",Le,oe,ae]}],"backdrop-filter":[{"backdrop-filter":["","none",oe,ae]}],"backdrop-blur":[{"backdrop-blur":qt()}],"backdrop-brightness":[{"backdrop-brightness":[Le,oe,ae]}],"backdrop-contrast":[{"backdrop-contrast":[Le,oe,ae]}],"backdrop-grayscale":[{"backdrop-grayscale":["",Le,oe,ae]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[Le,oe,ae]}],"backdrop-invert":[{"backdrop-invert":["",Le,oe,ae]}],"backdrop-opacity":[{"backdrop-opacity":[Le,oe,ae]}],"backdrop-saturate":[{"backdrop-saturate":[Le,oe,ae]}],"backdrop-sepia":[{"backdrop-sepia":["",Le,oe,ae]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":g()}],"border-spacing-x":[{"border-spacing-x":g()}],"border-spacing-y":[{"border-spacing-y":g()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",oe,ae]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[Le,"initial",oe,ae]}],ease:[{ease:["linear","initial",C,oe,ae]}],delay:[{delay:[Le,oe,ae]}],animate:[{animate:["none",j,oe,ae]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[P,oe,ae]}],"perspective-origin":[{"perspective-origin":G()}],rotate:[{rotate:ut()}],"rotate-x":[{"rotate-x":ut()}],"rotate-y":[{"rotate-y":ut()}],"rotate-z":[{"rotate-z":ut()}],scale:[{scale:zt()}],"scale-x":[{"scale-x":zt()}],"scale-y":[{"scale-y":zt()}],"scale-z":[{"scale-z":zt()}],"scale-3d":["scale-3d"],skew:[{skew:Ze()}],"skew-x":[{"skew-x":Ze()}],"skew-y":[{"skew-y":Ze()}],transform:[{transform:[oe,ae,"","none","gpu","cpu"]}],"transform-origin":[{origin:G()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:De()}],"translate-x":[{"translate-x":De()}],"translate-y":[{"translate-y":De()}],"translate-z":[{"translate-z":De()}],"translate-none":["translate-none"],accent:[{accent:B()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:B()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",oe,ae]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":g()}],"scroll-mx":[{"scroll-mx":g()}],"scroll-my":[{"scroll-my":g()}],"scroll-ms":[{"scroll-ms":g()}],"scroll-me":[{"scroll-me":g()}],"scroll-mbs":[{"scroll-mbs":g()}],"scroll-mbe":[{"scroll-mbe":g()}],"scroll-mt":[{"scroll-mt":g()}],"scroll-mr":[{"scroll-mr":g()}],"scroll-mb":[{"scroll-mb":g()}],"scroll-ml":[{"scroll-ml":g()}],"scroll-p":[{"scroll-p":g()}],"scroll-px":[{"scroll-px":g()}],"scroll-py":[{"scroll-py":g()}],"scroll-ps":[{"scroll-ps":g()}],"scroll-pe":[{"scroll-pe":g()}],"scroll-pbs":[{"scroll-pbs":g()}],"scroll-pbe":[{"scroll-pbe":g()}],"scroll-pt":[{"scroll-pt":g()}],"scroll-pr":[{"scroll-pr":g()}],"scroll-pb":[{"scroll-pb":g()}],"scroll-pl":[{"scroll-pl":g()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",oe,ae]}],fill:[{fill:["none",...B()]}],"stroke-w":[{stroke:[Le,ds,ua,Mi]}],stroke:[{stroke:["none",...B()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},Lf=pf(Of);function St(...e){return Lf(Dl(e))}const Io="dartlab-conversations",Ai=50;function Rf(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function Df(){try{const e=localStorage.getItem(Io);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const jf=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function Ti(e){return e.map(t=>({...t,messages:t.messages.map(r=>{if(r.role!=="assistant")return r;const a={};for(const[s,o]of Object.entries(r))jf.includes(s)||(a[s]=o);return a})}))}function Ii(e){try{const t={conversations:Ti(e.conversations),activeId:e.activeId};localStorage.setItem(Io,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:Ti(e.conversations),activeId:e.activeId};localStorage.setItem(Io,JSON.stringify(t))}catch{}}}}function Vf(){const e=Df(),t=e.conversations||[],r=t.find(C=>C.id===e.activeId)?e.activeId:null;let a=H(Et(t)),s=H(Et(r)),o=null;function i(){o&&clearTimeout(o),o=setTimeout(()=>{Ii({conversations:n(a),activeId:n(s)}),o=null},300)}function l(){o&&clearTimeout(o),o=null,Ii({conversations:n(a),activeId:n(s)})}function c(){return n(a).find(C=>C.id===n(s))||null}function f(){const C={id:Rf(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return u(a,[C,...n(a)],!0),n(a).length>Ai&&u(a,n(a).slice(0,Ai),!0),u(s,C.id,!0),l(),C.id}function p(C){n(a).find(j=>j.id===C)&&(u(s,C,!0),l())}function b(C,j,Y=null){const M=c();if(!M)return;const G={role:C,text:j};Y&&(G.meta=Y),M.messages=[...M.messages,G],M.updatedAt=Date.now(),M.title==="새 대화"&&C==="user"&&(M.title=j.length>30?j.slice(0,30)+"...":j),u(a,[...n(a)],!0),l()}function w(C){const j=c();if(!j||j.messages.length===0)return;const Y=j.messages[j.messages.length-1];Object.assign(Y,C),j.updatedAt=Date.now(),u(a,[...n(a)],!0),i()}function A(C){u(a,n(a).filter(j=>j.id!==C),!0),n(s)===C&&u(s,n(a).length>0?n(a)[0].id:null,!0),l()}function k(){const C=c();!C||C.messages.length===0||(C.messages=C.messages.slice(0,-1),C.updatedAt=Date.now(),u(a,[...n(a)],!0),l())}function P(C,j){const Y=n(a).find(M=>M.id===C);Y&&(Y.title=j,u(a,[...n(a)],!0),l())}function y(){u(a,[],!0),u(s,null),l()}return{get conversations(){return n(a)},get activeId(){return n(s)},get active(){return c()},createConversation:f,setActive:p,addMessage:b,updateLastMessage:w,removeLastMessage:k,deleteConversation:A,updateTitle:P,clearAll:y,flush:l}}const ad="dartlab-workspace",Ff=6;function sd(){return typeof window<"u"&&typeof localStorage<"u"}function qf(){if(!sd())return{};try{const e=localStorage.getItem(ad);return e?JSON.parse(e):{}}catch{return{}}}function Bf(e){sd()&&localStorage.setItem(ad,JSON.stringify(e))}function Gf(){const e=qf();let t=H(!1),r=H(null),a=H(null),s=H("explore"),o=H(null),i=H(null),l=H(null),c=H(null),f=H(Et(e.selectedCompany||null)),p=H(Et(e.recentCompanies||[]));function b(){Bf({selectedCompany:n(f),recentCompanies:n(p)})}function w($){if(!($!=null&&$.stockCode))return;const g={stockCode:$.stockCode,corpName:$.corpName||$.company||$.stockCode,company:$.company||$.corpName||$.stockCode,market:$.market||""};u(p,[g,...n(p).filter(K=>K.stockCode!==g.stockCode)].slice(0,Ff),!0)}function A($){$&&(u(f,$,!0),w($)),u(r,"viewer"),u(a,null),u(t,!0),b()}function k($){u(r,"data"),u(a,$,!0),u(t,!0),G("explore")}function P(){u(t,!1)}function y($){u(f,$,!0),$&&w($),b()}function C($,g){var K,ee,Z,L;!($!=null&&$.company)&&!($!=null&&$.stockCode)||(u(f,{...n(f)||{},...g||{},corpName:$.company||((K=n(f))==null?void 0:K.corpName)||(g==null?void 0:g.corpName)||(g==null?void 0:g.company),company:$.company||((ee=n(f))==null?void 0:ee.company)||(g==null?void 0:g.company)||(g==null?void 0:g.corpName),stockCode:$.stockCode||((Z=n(f))==null?void 0:Z.stockCode)||(g==null?void 0:g.stockCode),market:((L=n(f))==null?void 0:L.market)||(g==null?void 0:g.market)||""},!0),w(n(f)),b())}function j($,g){u(l,$,!0),u(c,g||$,!0)}function Y($,g=null){u(r,"data"),u(t,!0),u(s,"evidence"),u(o,$,!0),u(i,Number.isInteger(g)?g:null,!0)}function M(){u(o,null),u(i,null)}function G($){u(s,$||"explore",!0),n(s)!=="evidence"&&M()}function de(){return n(t)?n(r)==="viewer"&&n(f)?{type:"viewer",company:n(f),topic:n(l),topicLabel:n(c)}:n(r)==="data"&&n(a)?{type:"data",data:n(a)}:null:null}return{get panelOpen(){return n(t)},get panelMode(){return n(r)},get panelData(){return n(a)},get activeTab(){return n(s)},get activeEvidenceSection(){return n(o)},get selectedEvidenceIndex(){return n(i)},get selectedCompany(){return n(f)},get recentCompanies(){return n(p)},get viewerTopic(){return n(l)},get viewerTopicLabel(){return n(c)},openViewer:A,openData:k,openEvidence:Y,closePanel:P,selectCompany:y,setViewerTopic:j,clearEvidenceSelection:M,setTab:G,syncCompanyFromMessage:C,getViewContext:de}}var Hf=h("<a><!></a>"),Uf=h("<button><!></button>");function Wf(e,t){en(t,!0);let r=nt(t,"variant",3,"default"),a=nt(t,"size",3,"default"),s=$u(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const o={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},i={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=xe(),c=Q(l);{var f=b=>{var w=Hf();Rs(w,k=>({class:k,...s}),[()=>St("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",o[r()],i[a()],t.class)]);var A=d(w);Eo(A,()=>t.children),v(b,w)},p=b=>{var w=Uf();Rs(w,k=>({class:k,...s}),[()=>St("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",o[r()],i[a()],t.class)]);var A=d(w);Eo(A,()=>t.children),v(b,w)};z(c,b=>{t.href?b(f):b(p,-1)})}v(e,l),tn()}Cc();/**
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
 */const Pi=(...e)=>e.filter((t,r,a)=>!!t&&t.trim()!==""&&a.indexOf(t)===r).join(" ").trim();var Xf=vu("<svg><!><!></svg>");function He(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]),a=Ne(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);en(t,!1);let s=nt(t,"name",8,void 0),o=nt(t,"color",8,"currentColor"),i=nt(t,"size",8,24),l=nt(t,"strokeWidth",8,2),c=nt(t,"absoluteStrokeWidth",8,!1),f=nt(t,"iconNode",24,()=>[]);Tu();var p=Xf();Rs(p,(A,k,P)=>({...Kf,...A,...a,width:i(),height:i(),stroke:o(),"stroke-width":k,class:P}),[()=>Yf(a)?void 0:{"aria-hidden":"true"},()=>(fa(c()),fa(l()),fa(i()),Sa(()=>c()?Number(l())*24/Number(i()):l())),()=>(fa(Pi),fa(s()),fa(r),Sa(()=>Pi("lucide-icon","lucide",s()?`lucide-${s()}`:"",r.class)))]);var b=d(p);Ie(b,1,f,Te,(A,k)=>{var P=U(()=>Hi(n(k),2));let y=()=>n(P)[0],C=()=>n(P)[1];var j=xe(),Y=Q(j);wu(Y,y,!0,(M,G)=>{Rs(M,()=>({...C()}))}),v(A,j)});var w=m(b);Re(w,t,"default",{}),v(e,p),tn()}function Jf(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];He(e,Ge({name:"activity"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Qf(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];He(e,Ge({name:"arrow-up"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function $i(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 7v14"}],["path",{d:"M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"}]];He(e,Ge({name:"book-open"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function io(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];He(e,Ge({name:"brain"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Zf(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]];He(e,Ge({name:"chart-column"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ev(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M20 6 9 17l-5-5"}]];He(e,Ge({name:"check"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function tv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m6 9 6 6 6-6"}]];He(e,Ge({name:"chevron-down"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function rv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m9 18 6-6-6-6"}]];He(e,Ge({name:"chevron-right"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function cs(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];He(e,Ge({name:"circle-alert"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function gs(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];He(e,Ge({name:"circle-check"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function nv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];He(e,Ge({name:"clock"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function av(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];He(e,Ge({name:"code"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function sv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];He(e,Ge({name:"coffee"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function us(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];He(e,Ge({name:"database"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function xs(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];He(e,Ge({name:"download"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Ni(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];He(e,Ge({name:"external-link"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ov(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];He(e,Ge({name:"eye"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Ln(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];He(e,Ge({name:"file-text"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function iv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];He(e,Ge({name:"github"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Oi(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];He(e,Ge({name:"key"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Yr(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];He(e,Ge({name:"loader-circle"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function lv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m10 17 5-5-5-5"}],["path",{d:"M15 12H3"}],["path",{d:"M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"}]];He(e,Ge({name:"log-in"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function dv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];He(e,Ge({name:"log-out"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function od(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"m21 3-7 7"}],["path",{d:"m3 21 7-7"}],["path",{d:"M9 21H3v-6"}]];He(e,Ge({name:"maximize-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function cv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];He(e,Ge({name:"menu"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Li(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];He(e,Ge({name:"message-square"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function id(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m14 10 7-7"}],["path",{d:"M20 10h-6V4"}],["path",{d:"m3 21 7-7"}],["path",{d:"M4 14h6v6"}]];He(e,Ge({name:"minimize-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function uv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];He(e,Ge({name:"panel-left-close"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Ri(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];He(e,Ge({name:"plus"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function fv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];He(e,Ge({name:"refresh-cw"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function bs(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];He(e,Ge({name:"search"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function vv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];He(e,Ge({name:"settings"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function pv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];He(e,Ge({name:"square"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function mv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];He(e,Ge({name:"terminal"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function hv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];He(e,Ge({name:"trash-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function gv(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];He(e,Ge({name:"triangle-alert"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Di(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];He(e,Ge({name:"wrench"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function js(e,t){const r=Ne(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];He(e,Ge({name:"x"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=xe(),l=Q(i);Re(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}var xv=h("<!> 새 대화",1),bv=h('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),_v=h('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),wv=h('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),yv=h('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40"><span class="text-[10px] text-dl-text-dim font-mono"> </span></div>'),kv=h('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),Cv=h("<button><!></button>"),Sv=h('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),Mv=h("<aside><!></aside>");function Ev(e,t){en(t,!0);let r=nt(t,"conversations",19,()=>[]),a=nt(t,"activeId",3,null),s=nt(t,"open",3,!0),o=nt(t,"version",3,""),i=H("");function l(k){const P=new Date().setHours(0,0,0,0),y=P-864e5,C=P-7*864e5,j={오늘:[],어제:[],"이번 주":[],이전:[]};for(const M of k)M.updatedAt>=P?j.오늘.push(M):M.updatedAt>=y?j.어제.push(M):M.updatedAt>=C?j["이번 주"].push(M):j.이전.push(M);const Y=[];for(const[M,G]of Object.entries(j))G.length>0&&Y.push({label:M,items:G});return Y}let c=U(()=>n(i).trim()?r().filter(k=>k.title.toLowerCase().includes(n(i).toLowerCase())):r()),f=U(()=>l(n(c)));var p=Mv(),b=d(p);{var w=k=>{var P=kv(),y=m(d(P),2),C=d(y);Wf(C,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:($,g)=>{var K=xv(),ee=Q(K);Ri(ee,{size:16}),v($,K)},$$slots:{default:!0}});var j=m(y,2);{var Y=$=>{var g=bv(),K=d(g),ee=d(K);bs(ee,{size:12,class:"text-dl-text-dim flex-shrink-0"});var Z=m(ee,2);$a(Z,()=>n(i),L=>u(i,L)),v($,g)};z(j,$=>{r().length>3&&$(Y)})}var M=m(j,2);Ie(M,21,()=>n(f),Te,($,g)=>{var K=wv(),ee=d(K),Z=d(ee),L=m(ee,2);Ie(L,17,()=>n(g).items,Te,(ce,te)=>{var we=_v(),Ce=d(we),Pe=d(Ce);Li(Pe,{size:14,class:"flex-shrink-0 opacity-50"});var ye=m(Pe,2),ue=d(ye),B=m(Ce,2),T=d(B);hv(T,{size:12}),O(V=>{$e(we,1,V),Dn(Ce,"aria-current",n(te).id===a()?"true":void 0),N(ue,n(te).title),Dn(B,"aria-label",`${n(te).title} 삭제`)},[()=>Ct(St("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",n(te).id===a()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),re("click",Ce,()=>{var V;return(V=t.onSelect)==null?void 0:V.call(t,n(te).id)}),re("click",B,V=>{var ne;V.stopPropagation(),(ne=t.onDelete)==null||ne.call(t,n(te).id)}),v(ce,we)}),O(()=>N(Z,n(g).label)),v($,K)});var G=m(M,2);{var de=$=>{var g=yv(),K=d(g),ee=d(K);O(()=>N(ee,`v${o()??""}`)),v($,g)};z(G,$=>{o()&&$(de)})}v(k,P)},A=k=>{var P=Sv(),y=m(d(P),2),C=d(y);Ri(C,{size:18});var j=m(y,2);Ie(j,21,()=>r().slice(0,10),Te,(Y,M)=>{var G=Cv(),de=d(G);Li(de,{size:16}),O($=>{$e(G,1,$),Dn(G,"title",n(M).title)},[()=>Ct(St("p-2 rounded-lg transition-colors w-full flex justify-center",n(M).id===a()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),re("click",G,()=>{var $;return($=t.onSelect)==null?void 0:$.call(t,n(M).id)}),v(Y,G)}),re("click",y,function(...Y){var M;(M=t.onNewChat)==null||M.apply(this,Y)}),v(k,P)};z(b,k=>{s()?k(w):k(A,-1)})}O(k=>$e(p,1,k),[()=>Ct(St("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",s()?"w-[260px]":"w-[52px]"))]),v(e,p),tn()}Vn(["click"]);var zv=h('<button class="send-btn active"><!></button>'),Av=h("<button><!></button>"),Tv=h('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),Iv=h('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),Pv=h('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),$v=h('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function ld(e,t){en(t,!0);let r=nt(t,"inputText",15,""),a=nt(t,"isLoading",3,!1),s=nt(t,"large",3,!1),o=nt(t,"placeholder",3,"메시지를 입력하세요..."),i=H(Et([])),l=H(!1),c=H(-1),f=null,p=H(void 0);function b(g){var K;if(n(l)&&n(i).length>0){if(g.key==="ArrowDown"){g.preventDefault(),u(c,(n(c)+1)%n(i).length);return}if(g.key==="ArrowUp"){g.preventDefault(),u(c,n(c)<=0?n(i).length-1:n(c)-1,!0);return}if(g.key==="Enter"&&n(c)>=0){g.preventDefault(),k(n(i)[n(c)]);return}if(g.key==="Escape"){u(l,!1),u(c,-1);return}}g.key==="Enter"&&!g.shiftKey&&(g.preventDefault(),u(l,!1),(K=t.onSend)==null||K.call(t))}function w(g){g.target.style.height="auto",g.target.style.height=Math.min(g.target.scrollHeight,200)+"px"}function A(g){w(g);const K=r();f&&clearTimeout(f),K.length>=2&&!/\s/.test(K.slice(-1))?f=setTimeout(async()=>{var ee;try{const Z=await Bl(K.trim());((ee=Z.results)==null?void 0:ee.length)>0?(u(i,Z.results.slice(0,6),!0),u(l,!0),u(c,-1)):u(l,!1)}catch{u(l,!1)}},300):u(l,!1)}function k(g){var K;r(`${g.corpName} `),u(l,!1),u(c,-1),(K=t.onCompanySelect)==null||K.call(t,g),n(p)&&n(p).focus()}function P(){setTimeout(()=>{u(l,!1)},200)}var y=$v(),C=d(y),j=d(C);Ka(j,g=>u(p,g),()=>n(p));var Y=m(j,2);{var M=g=>{var K=zv(),ee=d(K);pv(ee,{size:14}),re("click",K,function(...Z){var L;(L=t.onStop)==null||L.apply(this,Z)}),v(g,K)},G=g=>{var K=Av(),ee=d(K);{let Z=U(()=>s()?18:16);Qf(ee,{get size(){return n(Z)},strokeWidth:2.5})}O((Z,L)=>{$e(K,1,Z),K.disabled=L},[()=>Ct(St("send-btn",r().trim()&&"active")),()=>!r().trim()]),re("click",K,()=>{var Z;u(l,!1),(Z=t.onSend)==null||Z.call(t)}),v(g,K)};z(Y,g=>{a()&&t.onStop?g(M):g(G,-1)})}var de=m(C,2);{var $=g=>{var K=Pv();Ie(K,21,()=>n(i),Te,(ee,Z,L)=>{var ce=Iv(),te=d(ce);bs(te,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var we=m(te,2),Ce=d(we),Pe=d(Ce),ye=m(Ce,2),ue=d(ye),B=m(we,2);{var T=V=>{var ne=Tv(),se=d(ne);O(()=>N(se,n(Z).sector)),v(V,ne)};z(B,V=>{n(Z).sector&&V(T)})}O(V=>{$e(ce,1,V),N(Pe,n(Z).corpName),N(ue,`${n(Z).stockCode??""} · ${(n(Z).market||"")??""}`)},[()=>Ct(St("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",L===n(c)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),re("mousedown",ce,()=>k(n(Z))),Na("mouseenter",ce,()=>{u(c,L,!0)}),v(ee,ce)}),v(g,K)};z(de,g=>{n(l)&&n(i).length>0&&g($)})}O(g=>{$e(C,1,g),Dn(j,"placeholder",o())},[()=>Ct(St("input-box",s()&&"large"))]),re("keydown",j,b),re("input",j,A),Na("blur",j,P),$a(j,r),v(e,y),tn()}Vn(["keydown","input","click","mousedown"]);var Nv=h('<button class="rounded-full border border-dl-border/60 bg-dl-bg-card/40 px-3 py-1.5 text-[12px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"> </button>'),Ov=h(`<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[580px] flex flex-col items-center"><div class="relative mb-8"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p> <div class="mb-6 max-w-[520px] rounded-2xl border border-dl-border/50 bg-dl-bg-card/50 px-4 py-3 text-left"><div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">Evidence First</div> <div class="mt-2 text-[13px] leading-relaxed text-dl-text-muted">DartLab은 재무 수치와 서술 텍스트를 함께 읽고, 표준화된 계정과 원문 근거를 같은 흐름에서 확인하도록 설계되어 있습니다.
				DART와 EDGAR를 포함한 40개 모듈 이상의 기능 범위를 먼저 물어본 뒤 바로 탐색을 시작할 수 있습니다.</div></div> <div class="w-full"><!></div> <div class="mt-5 flex w-full flex-wrap justify-center gap-2"></div></div></div>`);function Lv(e,t){en(t,!0);let r=nt(t,"inputText",15,"");const a=["지금 dartlab에서 할 수 있는 기능을 먼저 정리해줘","EDGAR에서 추가로 받을 수 있는 데이터와 방법을 알려줘","OpenDart와 OpenEdgar로 가능한 일을 비교해줘","GPT 연결 시 현재 UI에서 가능한 코딩 작업 범위를 알려줘"];var s=Ov(),o=d(s),i=m(d(o),8),l=d(i);ld(l,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get onCompanySelect(){return t.onCompanySelect},get inputText(){return r()},set inputText(f){r(f)}});var c=m(i,2);Ie(c,21,()=>a,Te,(f,p)=>{var b=Nv(),w=d(b);O(()=>N(w,n(p))),re("click",b,()=>{var A;return(A=t.onSend)==null?void 0:A.call(t,n(p))}),v(f,b)}),v(e,s),tn()}Vn(["click"]);var Rv=h("<span><!></span>");function ji(e,t){en(t,!0);let r=nt(t,"variant",3,"default");const a={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var s=Rv(),o=d(s);Eo(o,()=>t.children),O(i=>$e(s,1,i),[()=>Ct(St("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",a[r()],t.class))]),v(e,s),tn()}function Dv(e){const t=e.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(t)||t==="-"||t==="0"}function Ya(e){if(!e)return"";let t=[],r=[],a=e.replace(/```(\w*)\n([\s\S]*?)```/g,(o,i,l)=>{const c=t.length;return t.push(l.trimEnd()),`
%%CODE_${c}%%
`});a=a.replace(/((?:^\|.+\|$\n?)+)/gm,o=>{const i=o.trim().split(`
`).filter(w=>w.trim());let l=null,c=-1,f=[];for(let w=0;w<i.length;w++)if(i[w].slice(1,-1).split("|").map(k=>k.trim()).every(k=>/^[\-:]+$/.test(k))){c=w;break}c>0?(l=i[c-1],f=i.slice(c+1)):(c===0||(l=i[0]),f=i.slice(1));let p="<table>";if(l){const w=l.slice(1,-1).split("|").map(A=>A.trim());p+="<thead><tr>"+w.map(A=>`<th>${A.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(f.length>0){p+="<tbody>";for(const w of f){const A=w.slice(1,-1).split("|").map(k=>k.trim());p+="<tr>"+A.map(k=>{let P=k.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${Dv(k)?' class="num"':""}>${P}</td>`}).join("")+"</tr>"}p+="</tbody>"}p+="</table>";let b=r.length;return r.push(p),`
%%TABLE_${b}%%
`});let s=a.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");s=s.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,o=>"<ul>"+o.replace(/<br>/g,"")+"</ul>");for(let o=0;o<r.length;o++)s=s.replace(`%%TABLE_${o}%%`,r[o]);for(let o=0;o<t.length;o++){const i=t[o].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");s=s.replace(`%%CODE_${o}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${o}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${i}</code></pre></div>`)}return s=s.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(o,i)=>i.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+s+"</p>"}var jv=h('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),Vv=h('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),Fv=h('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),qv=h('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),Bv=h('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!></div></div>'),Gv=h('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),Hv=h('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),Uv=h('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),Wv=h('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),Kv=h("<button><!> </button>"),Yv=h('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),Xv=h('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),Jv=h('<!> <span class="text-dl-text-dim"> </span>',1),Qv=h('<div class="flex items-center gap-2 text-[11px]"><!></div>'),Zv=h('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),ep=h('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),tp=h('<div class="message-committed"><!></div>'),rp=h('<div><div class="message-live-label"> </div> <pre> </pre></div>'),np=h('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),ap=h('<span class="text-dl-accent/60"> </span>'),sp=h('<span class="text-dl-success/60"> </span>'),op=h('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),ip=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),lp=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),dp=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),cp=h('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),up=h("<!>  <div><!> <!></div> <!>",1),fp=h('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),vp=h('<span class="text-[10px] text-dl-text-dim"> </span>'),pp=h('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),mp=h("<button> </button>"),hp=h('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),gp=h("<button>시스템 프롬프트</button>"),xp=h("<button>LLM 입력</button>"),bp=h('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),_p=h('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),wp=h('<span class="text-dl-text"> </span>'),yp=h('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),kp=h('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),Cp=h('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Sp=h("<!> <!>",1);function Mp(e,t){en(t,!0);let r=H(null),a=H("context"),s=H("raw"),o=U(()=>{var T,V,ne,se,me,fe;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((T=t.message.toolEvents)==null?void 0:T.length)>0){const he=[...t.message.toolEvents].reverse().find(X=>X.type==="call"),ze=((V=he==null?void 0:he.arguments)==null?void 0:V.module)||((ne=he==null?void 0:he.arguments)==null?void 0:ne.keyword)||"";return`도구 실행 중 — ${(he==null?void 0:he.name)||""}${ze?` (${ze})`:""}`}if(((se=t.message.contexts)==null?void 0:se.length)>0){const he=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(he==null?void 0:he.label)||(he==null?void 0:he.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(me=t.message.meta)!=null&&me.company?`${t.message.meta.company} 데이터 검색 중`:(fe=t.message.meta)!=null&&fe.includedModules?"분석 모듈 선택 완료":"생각 중"}),i=U(()=>{var T;return t.message.company||((T=t.message.meta)==null?void 0:T.company)||null}),l=U(()=>{var T,V,ne;return t.message.systemPrompt||t.message.userContent||((T=t.message.contexts)==null?void 0:T.length)>0||((V=t.message.meta)==null?void 0:V.includedModules)||((ne=t.message.toolEvents)==null?void 0:ne.length)>0}),c=U(()=>{var V;const T=(V=t.message.meta)==null?void 0:V.dataYearRange;return T?typeof T=="string"?T:T.min_year&&T.max_year?`${T.min_year}~${T.max_year}년`:null:null});function f(T){if(!T)return 0;const V=(T.match(/[\uac00-\ud7af]/g)||[]).length,ne=T.length-V;return Math.round(V*1.5+ne/3.5)}function p(T){return T>=1e3?(T/1e3).toFixed(1)+"k":String(T)}let b=U(()=>{var V;let T=0;if(t.message.systemPrompt&&(T+=f(t.message.systemPrompt)),t.message.userContent)T+=f(t.message.userContent);else if(((V=t.message.contexts)==null?void 0:V.length)>0)for(const ne of t.message.contexts)T+=f(ne.text);return T}),w=U(()=>f(t.message.text)),A=H(void 0);const k=/^\s*\|.+\|\s*$/;function P(T,V){if(!T)return{committed:"",draft:"",draftType:"none"};if(!V)return{committed:T,draft:"",draftType:"none"};const ne=T.split(`
`);let se=ne.length;T.endsWith(`
`)||(se=Math.min(se,ne.length-1));let me=0,fe=-1;for(let ut=0;ut<ne.length;ut++)ne[ut].trim().startsWith("```")&&(me+=1,fe=ut);me%2===1&&fe>=0&&(se=Math.min(se,fe));let he=-1;for(let ut=ne.length-1;ut>=0;ut--){const zt=ne[ut];if(!zt.trim())break;if(k.test(zt))he=ut;else{he=-1;break}}if(he>=0&&(se=Math.min(se,he)),se<=0)return{committed:"",draft:T,draftType:he===0?"table":me%2===1?"code":"text"};const ze=ne.slice(0,se).join(`
`),X=ne.slice(se).join(`
`);let qt="text";return X&&he>=se?qt="table":X&&me%2===1&&(qt="code"),{committed:ze,draft:X,draftType:qt}}const y='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',C='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function j(T){var me;const V=T.target.closest(".code-copy-btn");if(!V)return;const ne=V.closest(".code-block-wrap"),se=((me=ne==null?void 0:ne.querySelector("code"))==null?void 0:me.textContent)||"";navigator.clipboard.writeText(se).then(()=>{V.innerHTML=C,setTimeout(()=>{V.innerHTML=y},2e3)})}function Y(T){if(t.onOpenEvidence){t.onOpenEvidence("contexts",T);return}u(r,T,!0),u(a,"context"),u(s,"rendered")}function M(){if(t.onOpenEvidence){t.onOpenEvidence("system");return}u(r,0),u(a,"system"),u(s,"raw")}function G(){if(t.onOpenEvidence){t.onOpenEvidence("snapshot");return}u(r,0),u(a,"snapshot")}function de(T){var V;if(t.onOpenEvidence){const ne=(V=t.message.toolEvents)==null?void 0:V[T];t.onOpenEvidence((ne==null?void 0:ne.type)==="result"?"tool-results":"tool-calls",T);return}u(r,T,!0),u(a,"tool"),u(s,"raw")}function $(){if(t.onOpenEvidence){t.onOpenEvidence("input");return}u(r,0),u(a,"userContent"),u(s,"raw")}function g(){u(r,null)}function K(T){var V,ne,se,me;return T?T.type==="call"?((V=T.arguments)==null?void 0:V.module)||((ne=T.arguments)==null?void 0:ne.keyword)||((se=T.arguments)==null?void 0:se.engine)||((me=T.arguments)==null?void 0:me.name)||"":typeof T.result=="string"?T.result.slice(0,120):T.result&&typeof T.result=="object"&&(T.result.module||T.result.status||T.result.name)||"":""}let ee=U(()=>(t.message.toolEvents||[]).filter(T=>T.type==="call")),Z=U(()=>(t.message.toolEvents||[]).filter(T=>T.type==="result")),L=U(()=>P(t.message.text||"",t.message.loading)),ce=U(()=>{var V,ne,se;const T=[];return((ne=(V=t.message.meta)==null?void 0:V.includedModules)==null?void 0:ne.length)>0&&T.push({label:`모듈 ${t.message.meta.includedModules.length}개`,icon:us}),((se=t.message.contexts)==null?void 0:se.length)>0&&T.push({label:`컨텍스트 ${t.message.contexts.length}건`,icon:ov}),n(ee).length>0&&T.push({label:`툴 호출 ${n(ee).length}건`,icon:Di}),n(Z).length>0&&T.push({label:`툴 결과 ${n(Z).length}건`,icon:gs}),t.message.systemPrompt&&T.push({label:"시스템 프롬프트",icon:io}),t.message.userContent&&T.push({label:"LLM 입력",icon:Ln}),T}),te=U(()=>{var V,ne,se;if(!t.message.loading)return[];const T=[];return(V=t.message.meta)!=null&&V.company&&T.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&T.push({label:"핵심 수치 확인",done:!0}),(ne=t.message.meta)!=null&&ne.includedModules&&T.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((se=t.message.contexts)==null?void 0:se.length)>0&&T.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&T.push({label:"프롬프트 조립",done:!0}),t.message.text?T.push({label:"응답 작성 중",done:!1}):T.push({label:n(o)||"준비 중",done:!1}),T});var we=Sp(),Ce=Q(we);{var Pe=T=>{var V=jv(),ne=m(d(V),2),se=d(ne),me=d(se);O(()=>N(me,t.message.text)),v(T,V)},ye=T=>{var V=fp(),ne=m(d(V),2),se=d(ne);{var me=Ze=>{var De=Bv(),mt=d(De),Ht=d(mt);Jf(Ht,{size:11});var Ot=m(mt,4),ht=d(Ot);{var gt=F=>{ji(F,{variant:"muted",children:(Se,it)=>{var ft=hs();O(()=>N(ft,n(i))),v(Se,ft)},$$slots:{default:!0}})};z(ht,F=>{n(i)&&F(gt)})}var Xt=m(ht,2);{var At=F=>{ji(F,{variant:"accent",children:(Se,it)=>{var ft=hs();O(()=>N(ft,n(c))),v(Se,ft)},$$slots:{default:!0}})};z(Xt,F=>{n(c)&&F(At)})}var x=m(Xt,2);{var q=F=>{var Se=xe(),it=Q(Se);Ie(it,17,()=>t.message.contexts,Te,(ft,et,Lt)=>{var Rt=Vv(),Lr=d(Rt);us(Lr,{size:10,class:"flex-shrink-0"});var qr=m(Lr);O(()=>N(qr,` ${(n(et).label||n(et).module)??""}`)),re("click",Rt,()=>Y(Lt)),v(ft,Rt)}),v(F,Se)},I=F=>{var Se=Fv(),it=d(Se);us(it,{size:10,class:"flex-shrink-0"});var ft=m(it);O(()=>N(ft,` 모듈 ${t.message.meta.includedModules.length??""}개`)),v(F,Se)};z(x,F=>{var Se,it,ft;((Se=t.message.contexts)==null?void 0:Se.length)>0?F(q):((ft=(it=t.message.meta)==null?void 0:it.includedModules)==null?void 0:ft.length)>0&&F(I,1)})}var W=m(x,2);Ie(W,17,()=>n(ce),Te,(F,Se)=>{var it=qv(),ft=d(it);_u(ft,()=>n(Se).icon,(Lt,Rt)=>{Rt(Lt,{size:10,class:"flex-shrink-0"})});var et=m(ft);O(()=>N(et,` ${n(Se).label??""}`)),re("click",it,()=>{n(Se).label.startsWith("컨텍스트")?Y(0):n(Se).label.startsWith("툴 호출")?t.onOpenEvidence?t.onOpenEvidence("tool-calls",0):de(0):n(Se).label.startsWith("툴 결과")?t.onOpenEvidence?t.onOpenEvidence("tool-results",0):de((t.message.toolEvents||[]).findIndex(Lt=>Lt.type==="result")):n(Se).label==="시스템 프롬프트"?M():n(Se).label==="LLM 입력"&&$()}),v(F,it)}),v(Ze,De)};z(se,Ze=>{var De,mt;(n(i)||n(c)||((De=t.message.contexts)==null?void 0:De.length)>0||(mt=t.message.meta)!=null&&mt.includedModules||n(ce).length>0)&&Ze(me)})}var fe=m(se,2);{var he=Ze=>{var De=Wv(),mt=d(De);Ie(mt,21,()=>t.message.snapshot.items,Te,(ht,gt)=>{const Xt=U(()=>n(gt).status==="good"?"text-dl-success":n(gt).status==="danger"?"text-dl-primary-light":n(gt).status==="caution"?"text-amber-400":"text-dl-text");var At=Gv(),x=d(At),q=d(x),I=m(x,2),W=d(I);O(F=>{N(q,n(gt).label),$e(I,1,F),N(W,n(gt).value)},[()=>Ct(St("text-[14px] font-semibold leading-snug mt-0.5",n(Xt)))]),v(ht,At)});var Ht=m(mt,2);{var Ot=ht=>{var gt=Uv();Ie(gt,21,()=>t.message.snapshot.warnings,Te,(Xt,At)=>{var x=Hv(),q=d(x);gv(q,{size:10});var I=m(q);O(()=>N(I,` ${n(At)??""}`)),v(Xt,x)}),v(ht,gt)};z(Ht,ht=>{var gt;((gt=t.message.snapshot.warnings)==null?void 0:gt.length)>0&&ht(Ot)})}re("click",De,G),v(Ze,De)};z(fe,Ze=>{var De,mt;((mt=(De=t.message.snapshot)==null?void 0:De.items)==null?void 0:mt.length)>0&&Ze(he)})}var ze=m(fe,2);{var X=Ze=>{var De=Yv(),mt=d(De),Ht=m(d(mt),4);Ie(Ht,21,()=>t.message.toolEvents,Te,(Ot,ht,gt)=>{const Xt=U(()=>K(n(ht)));var At=Kv(),x=d(At);{var q=F=>{Di(F,{size:11})},I=F=>{gs(F,{size:11})};z(x,F=>{n(ht).type==="call"?F(q):F(I,-1)})}var W=m(x);O(F=>{$e(At,1,F),N(W,` ${(n(ht).type==="call"?n(ht).name:`${n(ht).name} 결과`)??""}${n(Xt)?`: ${n(Xt)}`:""}`)},[()=>Ct(St("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",n(ht).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),re("click",At,()=>de(gt)),v(Ot,At)}),v(Ze,De)};z(ze,Ze=>{var De;((De=t.message.toolEvents)==null?void 0:De.length)>0&&Ze(X)})}var qt=m(ze,2);{var ut=Ze=>{var De=Zv(),mt=d(De);Ie(mt,21,()=>n(te),Te,(Ht,Ot)=>{var ht=Qv(),gt=d(ht);{var Xt=x=>{var q=Xv(),I=m(Q(q),2),W=d(I);O(()=>N(W,n(Ot).label)),v(x,q)},At=x=>{var q=Jv(),I=Q(q);Yr(I,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var W=m(I,2),F=d(W);O(()=>N(F,n(Ot).label)),v(x,q)};z(gt,x=>{n(Ot).done?x(Xt):x(At,-1)})}v(Ht,ht)}),v(Ze,De)},zt=Ze=>{var De=up(),mt=Q(De);{var Ht=I=>{var W=ep(),F=d(W);Yr(F,{size:12,class:"animate-spin flex-shrink-0"});var Se=m(F,2),it=d(Se);O(()=>N(it,n(o))),v(I,W)};z(mt,I=>{t.message.loading&&I(Ht)})}var Ot=m(mt,2),ht=d(Ot);{var gt=I=>{var W=tp(),F=d(W);ea(F,()=>Ya(n(L).committed)),v(I,W)};z(ht,I=>{n(L).committed&&I(gt)})}var Xt=m(ht,2);{var At=I=>{var W=rp(),F=d(W),Se=d(F),it=m(F,2),ft=d(it);O(et=>{$e(W,1,et),N(Se,n(L).draftType==="table"?"표 구성 중":n(L).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),N(ft,n(L).draft)},[()=>Ct(St("message-live-tail",n(L).draftType==="table"&&"message-draft-table",n(L).draftType==="code"&&"message-draft-code"))]),v(I,W)};z(Xt,I=>{n(L).draft&&I(At)})}Ka(Ot,I=>u(A,I),()=>n(A));var x=m(Ot,2);{var q=I=>{var W=cp(),F=d(W);{var Se=tt=>{var Xe=np(),Tt=d(Xe);nv(Tt,{size:10});var J=m(Tt);O(()=>N(J,` ${t.message.duration??""}초`)),v(tt,Xe)};z(F,tt=>{t.message.duration&&tt(Se)})}var it=m(F,2);{var ft=tt=>{var Xe=op(),Tt=d(Xe);{var J=Je=>{var vt=ap(),Dt=d(vt);O(Ut=>N(Dt,`↑${Ut??""}`),[()=>p(n(b))]),v(Je,vt)};z(Tt,Je=>{n(b)>0&&Je(J)})}var je=m(Tt,2);{var lt=Je=>{var vt=sp(),Dt=d(vt);O(Ut=>N(Dt,`↓${Ut??""}`),[()=>p(n(w))]),v(Je,vt)};z(je,Je=>{n(w)>0&&Je(lt)})}v(tt,Xe)};z(it,tt=>{(n(b)>0||n(w)>0)&&tt(ft)})}var et=m(it,2);{var Lt=tt=>{var Xe=ip(),Tt=d(Xe);fv(Tt,{size:10}),re("click",Xe,()=>{var J;return(J=t.onRegenerate)==null?void 0:J.call(t)}),v(tt,Xe)};z(et,tt=>{t.onRegenerate&&tt(Lt)})}var Rt=m(et,2);{var Lr=tt=>{var Xe=lp(),Tt=d(Xe);io(Tt,{size:10}),re("click",Xe,M),v(tt,Xe)};z(Rt,tt=>{t.message.systemPrompt&&tt(Lr)})}var qr=m(Rt,2);{var Mn=tt=>{var Xe=dp(),Tt=d(Xe);Ln(Tt,{size:10});var J=m(Tt);O((je,lt)=>N(J,` LLM 입력 (${je??""}자 · ~${lt??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>p(f(t.message.userContent))]),re("click",Xe,$),v(tt,Xe)};z(qr,tt=>{t.message.userContent&&tt(Mn)})}v(I,W)};z(x,I=>{!t.message.loading&&(t.message.duration||n(l)||t.onRegenerate)&&I(q)})}O(I=>$e(Ot,1,I),[()=>Ct(St("prose-dartlab message-body text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),re("click",Ot,j),v(Ze,De)};z(qt,Ze=>{t.message.loading&&!t.message.text?Ze(ut):Ze(zt,-1)})}v(T,V)};z(Ce,T=>{t.message.role==="user"?T(Pe):T(ye,-1)})}var ue=m(Ce,2);{var B=T=>{const V=U(()=>n(a)==="system"),ne=U(()=>n(a)==="userContent"),se=U(()=>n(a)==="context"),me=U(()=>n(a)==="snapshot"),fe=U(()=>n(a)==="tool"),he=U(()=>{var J;return n(se)?(J=t.message.contexts)==null?void 0:J[n(r)]:null}),ze=U(()=>{var J;return n(fe)?(J=t.message.toolEvents)==null?void 0:J[n(r)]:null}),X=U(()=>{var J,je,lt,Je,vt;return n(me)?"핵심 수치 (원본 데이터)":n(V)?"시스템 프롬프트":n(ne)?"LLM에 전달된 입력":n(fe)?((J=n(ze))==null?void 0:J.type)==="call"?`${(je=n(ze))==null?void 0:je.name} 호출`:`${(lt=n(ze))==null?void 0:lt.name} 결과`:((Je=n(he))==null?void 0:Je.label)||((vt=n(he))==null?void 0:vt.module)||""}),qt=U(()=>{var J;return n(me)?JSON.stringify(t.message.snapshot,null,2):n(V)?t.message.systemPrompt:n(ne)?t.message.userContent:n(fe)?JSON.stringify(n(ze),null,2):(J=n(he))==null?void 0:J.text});var ut=Cp(),zt=d(ut),Ze=d(zt),De=d(Ze),mt=d(De),Ht=d(mt);{var Ot=J=>{us(J,{size:15,class:"text-dl-success flex-shrink-0"})},ht=J=>{io(J,{size:15,class:"text-dl-primary-light flex-shrink-0"})},gt=J=>{Ln(J,{size:15,class:"text-dl-accent flex-shrink-0"})},Xt=J=>{us(J,{size:15,class:"flex-shrink-0"})};z(Ht,J=>{n(me)?J(Ot):n(V)?J(ht,1):n(ne)?J(gt,2):J(Xt,-1)})}var At=m(Ht,2),x=d(At),q=m(At,2);{var I=J=>{var je=vp(),lt=d(je);O(Je=>N(lt,`(${Je??""}자)`),[()=>{var Je,vt;return(vt=(Je=n(qt))==null?void 0:Je.length)==null?void 0:vt.toLocaleString()}]),v(J,je)};z(q,J=>{n(V)&&J(I)})}var W=m(mt,2),F=d(W);{var Se=J=>{var je=pp(),lt=d(je),Je=d(lt);Ln(Je,{size:11});var vt=m(lt,2),Dt=d(vt);av(Dt,{size:11}),O((Ut,Oe)=>{$e(lt,1,Ut),$e(vt,1,Oe)},[()=>Ct(St("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(s)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>Ct(St("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(s)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),re("click",lt,()=>u(s,"rendered")),re("click",vt,()=>u(s,"raw")),v(J,je)};z(F,J=>{n(se)&&J(Se)})}var it=m(F,2),ft=d(it);js(ft,{size:18});var et=m(De,2);{var Lt=J=>{var je=hp(),lt=d(je);Ie(lt,21,()=>t.message.contexts,Te,(Je,vt,Dt)=>{var Ut=mp(),Oe=d(Ut);O(Mt=>{$e(Ut,1,Mt),N(Oe,t.message.contexts[Dt].label||t.message.contexts[Dt].module)},[()=>Ct(St("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",Dt===n(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),re("click",Ut,()=>{u(r,Dt,!0)}),v(Je,Ut)}),v(J,je)};z(et,J=>{var je;n(se)&&((je=t.message.contexts)==null?void 0:je.length)>1&&J(Lt)})}var Rt=m(et,2);{var Lr=J=>{var je=bp(),lt=d(je),Je=d(lt);{var vt=Oe=>{var Mt=gp();O(_r=>$e(Mt,1,_r),[()=>Ct(St("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(V)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),re("click",Mt,()=>{u(a,"system")}),v(Oe,Mt)};z(Je,Oe=>{t.message.systemPrompt&&Oe(vt)})}var Dt=m(Je,2);{var Ut=Oe=>{var Mt=xp();O(_r=>$e(Mt,1,_r),[()=>Ct(St("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(ne)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),re("click",Mt,()=>{u(a,"userContent")}),v(Oe,Mt)};z(Dt,Oe=>{t.message.userContent&&Oe(Ut)})}v(J,je)};z(Rt,J=>{!n(se)&&!n(me)&&!n(fe)&&J(Lr)})}var qr=m(Ze,2),Mn=d(qr);{var tt=J=>{var je=_p(),lt=d(je);ea(lt,()=>{var Je;return Ya((Je=n(he))==null?void 0:Je.text)}),v(J,je)},Xe=J=>{var je=yp(),lt=d(je),Je=m(d(lt),2),vt=d(Je),Dt=m(vt);{var Ut=Sr=>{var vn=wp(),nr=d(vn);O(En=>N(nr,En),[()=>K(n(ze))]),v(Sr,vn)},Oe=U(()=>K(n(ze)));z(Dt,Sr=>{n(Oe)&&Sr(Ut)})}var Mt=m(lt,2),_r=d(Mt);O(()=>{var Sr;N(vt,`${((Sr=n(ze))==null?void 0:Sr.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),N(_r,n(qt))}),v(J,je)},Tt=J=>{var je=kp(),lt=d(je);O(()=>N(lt,n(qt))),v(J,je)};z(Mn,J=>{n(se)&&n(s)==="rendered"?J(tt):n(fe)?J(Xe,1):J(Tt,-1)})}O(()=>N(x,n(X))),re("click",ut,J=>{J.target===J.currentTarget&&g()}),re("keydown",ut,J=>{J.key==="Escape"&&g()}),re("click",it,g),v(T,ut)};z(ue,T=>{n(r)!==null&&T(B)})}v(e,we),tn()}Vn(["click","keydown"]);var Ep=h('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),zp=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),Ap=h('<div class="flex justify-end gap-2 mb-1.5"><!></div>'),Tp=h('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8"><!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function Ip(e,t){en(t,!0);function r(Z){if(s())return!1;for(let L=a().length-1;L>=0;L--)if(a()[L].role==="assistant"&&!a()[L].error&&a()[L].text)return L===Z;return!1}let a=nt(t,"messages",19,()=>[]),s=nt(t,"isLoading",3,!1),o=nt(t,"inputText",15,""),i=nt(t,"scrollTrigger",3,0);nt(t,"selectedCompany",3,null);function l(Z){return(L,ce)=>{var we,Ce,Pe,ye;(we=t.onOpenEvidence)==null||we.call(t,L,ce);let te;if(L==="contexts")te=(Ce=Z.contexts)==null?void 0:Ce[ce];else if(L==="snapshot")te={label:"핵심 수치",module:"snapshot",text:JSON.stringify(Z.snapshot,null,2)};else if(L==="system")te={label:"시스템 프롬프트",module:"system",text:Z.systemPrompt};else if(L==="input")te={label:"LLM 입력",module:"input",text:Z.userContent};else if(L==="tool-calls"||L==="tool-results"){const ue=(Pe=Z.toolEvents)==null?void 0:Pe[ce];te={label:`${(ue==null?void 0:ue.name)||"도구"} ${(ue==null?void 0:ue.type)==="call"?"호출":"결과"}`,module:"tool",text:JSON.stringify(ue,null,2)}}te&&((ye=t.onOpenData)==null||ye.call(t,te))}}let c,f,p=H(!0),b=H(!1),w=H(!0);function A(){if(!c)return;const{scrollTop:Z,scrollHeight:L,clientHeight:ce}=c;u(w,L-Z-ce<96),n(w)?(u(p,!0),u(b,!1)):(u(p,!1),u(b,!0))}function k(Z="smooth"){f&&(f.scrollIntoView({block:"end",behavior:Z}),u(p,!0),u(b,!1))}Zn(()=>{i(),!(!c||!f)&&requestAnimationFrame(()=>{!c||!f||(n(p)||n(w)?(f.scrollIntoView({block:"end",behavior:s()?"auto":"smooth"}),u(b,!1)):u(b,!0))})});var P=Tp(),y=d(P),C=d(y),j=d(C);Ie(j,17,a,Te,(Z,L,ce)=>{{let te=U(()=>r(ce)?t.onRegenerate:void 0),we=U(()=>t.onOpenData?l(n(L)):void 0);Mp(Z,{get message(){return n(L)},get onRegenerate(){return n(te)},get onOpenEvidence(){return n(we)}})}});var Y=m(j,2);Ka(Y,Z=>f=Z,()=>f),Ka(y,Z=>c=Z,()=>c);var M=m(y,2);{var G=Z=>{var L=Ep(),ce=d(L);re("click",ce,()=>k("smooth")),v(Z,L)};z(M,Z=>{n(b)&&Z(G)})}var de=m(M,2),$=d(de),g=d($);{var K=Z=>{var L=Ap(),ce=d(L);{var te=we=>{var Ce=zp(),Pe=d(Ce);xs(Pe,{size:10}),re("click",Ce,function(...ye){var ue;(ue=t.onExport)==null||ue.apply(this,ye)}),v(we,Ce)};z(ce,we=>{a().length>1&&t.onExport&&we(te)})}v(Z,L)};z(g,Z=>{s()||Z(K)})}var ee=m(g,2);ld(ee,{get isLoading(){return s()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get onCompanySelect(){return t.onCompanySelect},get inputText(){return o()},set inputText(Z){o(Z)}}),Na("scroll",y,A),v(e,P),tn()}Vn(["click"]);var Pp=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!> <span class="text-[13px]">공시 데이터 로딩 중...</span></div>'),$p=h('<div class="text-[11px] text-dl-text-dim"> </div>'),Np=h('<button><!> <span class="truncate flex-1"> </span></button>'),Op=h('<div class="py-0.5"></div>'),Lp=h('<div><button class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] opacity-30 font-normal"> </span></button> <!></div>'),Rp=h('<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50"><div class="px-3 py-2.5 border-b border-dl-border/20"><!></div> <!></nav>'),Dp=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim"><!> <p class="text-[13px]">좌측에서 섹션을 선택하세요</p></div>'),jp=h('<div class="text-[10px] text-dl-text-dim/50 mb-0.5"> </div>'),Vp=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!></div>'),Fp=h('<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>'),qp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Bp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Gp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Hp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Up=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Wp=h('<div class="vw-heading-node svelte-1l2nqwu"><!></div>'),Kp=h('<div class="vw-heading-block svelte-1l2nqwu"></div>'),Yp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Xp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Jp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Qp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Zp=h('<button><span class="vw-timeline-label svelte-1l2nqwu"> </span></button>'),em=h('<div class="vw-section-timeline svelte-1l2nqwu"></div>'),tm=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),rm=h('<span class="vw-meta-pill svelte-1l2nqwu">비교 없음</span>'),nm=h('<div class="vw-section-actions svelte-1l2nqwu"><span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span></div>'),am=h('<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span> </div>'),sm=h('<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),om=h('<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),im=h('<div class="text-[10px] text-dl-text-dim/35 mt-1"> </div>'),lm=h('<div class="vw-digest svelte-1l2nqwu"><div class="flex items-center gap-2 mb-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span></div> <div class="space-y-1"><!> <!> <!> <!></div></div>'),dm=h('<p class="vw-para"> </p>'),cm=h('<div class="vw-diff-added svelte-1l2nqwu"> </div>'),um=h('<div class="vw-diff-deleted svelte-1l2nqwu"> </div>'),fm=h('<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow svelte-1l2nqwu"></div>'),vm=h('<div class="disclosure-text vw-section-body vw-body-frame svelte-1l2nqwu"><!></div>'),pm=h('<div><!> <div class="vw-section-meta svelte-1l2nqwu"><span> </span> <!> <!> <!> <!></div> <!> <!> <!> <!></div>'),mm=h('<section class="vw-report-shell svelte-1l2nqwu"><div class="vw-report-header svelte-1l2nqwu"><div class="vw-report-badges svelte-1l2nqwu"><!> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <!> <!></div></div> <!></section>'),hm=h('<div class="vw-data-divider svelte-1l2nqwu"><div class="vw-data-kicker svelte-1l2nqwu">Structured Data</div> <div class="vw-data-title svelte-1l2nqwu">표 / 정형 데이터</div></div>'),gm=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),xm=h("<th> </th>"),bm=h("<td> </td>"),_m=h("<tr></tr>"),wm=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),ym=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),km=h("<th> </th>"),Cm=h("<td> </td>"),Sm=h("<tr></tr>"),Mm=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),Em=h("<button> </button>"),zm=h('<span class="text-[9px] text-dl-text-dim/30"> </span>'),Am=h('<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto"><!> <!></div>'),Tm=h('<div class="vw-table-wrap bg-dl-bg-card/10 svelte-1l2nqwu"><!> <div class="px-4 py-3"><div class="markdown-table overflow-x-auto svelte-1l2nqwu"><!></div></div></div>'),Im=h("<th> </th>"),Pm=h("<td> </td>"),$m=h("<tr></tr>"),Nm=h('<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02] svelte-1l2nqwu"><div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10"><!> <span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span></div> <div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Om=h('<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card"> </th>'),Lm=h('<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted"> </td>'),Rm=h("<tr></tr>"),Dm=h('<div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),jm=h('<article class="py-6 px-8"><!> <!> <!> <!></article>'),Vm=h('<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center"><div class="flex-1 min-w-0"><!> <h3 class="text-[16px] font-semibold text-dl-text"> </h3></div> <button class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"><!></button></div> <!>',1),Fm=h('<div class="flex flex-1 overflow-hidden min-h-0"><!> <main class="flex-1 overflow-y-auto min-w-0"><!></main></div>'),qm=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8"><!> <p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p></div>'),Bm=h('<div class="flex flex-col h-full font-sans bg-dl-bg-dark"><!></div>');function Gm(e,t){en(t,!0);let r=nt(t,"stockCode",3,null),a=nt(t,"onTopicChange",3,null),s=H(null),o=H(!1),i=H(Et(new Set)),l=H(null),c=H(null),f=H(Et([])),p=H(null),b=H(!1),w=H(Et([])),A=H(Et(new Map)),k=new Map,P=H(!1),y=H(Et(new Map));const C={companyOverview:"회사 개요",companyHistory:"회사 연혁",articlesOfIncorporation:"정관 사항",capitalChange:"자본금 변동",shareCapital:"주식 현황",dividend:"배당",productService:"사업 내용",rawMaterial:"원재료",businessOverview:"사업 개요",salesOrder:"매출/수주",riskDerivative:"위험관리/파생",majorContractsAndRnd:"주요 계약/R&D",otherReferences:"기타 참고사항",consolidatedStatements:"연결 재무제표",fsSummary:"재무제표 요약",consolidatedNotes:"연결 주석",financialStatements:"개별 재무제표",financialNotes:"개별 주석",fundraising:"자금조달",BS:"재무상태표",IS:"손익계산서",CIS:"포괄손익계산서",CF:"현금흐름표",SCE:"자본변동표",ratios:"재무비율",audit:"감사 의견",mdna:"경영진 분석(MD&A)",internalControl:"내부통제",auditContract:"감사 계약",nonAuditContract:"비감사 계약",boardOfDirectors:"이사회",shareholderMeeting:"주주총회",auditSystem:"감사 체계",outsideDirector:"사외이사",majorHolder:"주요 주주",majorHolderChange:"주주 변동",minorityHolder:"소수주주",stockTotal:"주식 총수",treasuryStock:"자기주식",employee:"직원 현황",executivePay:"임원 보수",executive:"임원 현황",executivePayAllTotal:"전체 보수 총액",executivePayIndividual:"개인별 보수",topPay:"5억이상 상위 보수",unregisteredExecutivePay:"미등기임원 보수",affiliateGroup:"계열회사",investedCompany:"투자회사",relatedPartyTx:"특수관계 거래",corporateBond:"사채 관리",privateOfferingUsage:"사모자금 사용",publicOfferingUsage:"공모자금 사용",shortTermBond:"단기사채",investorProtection:"투자자 보호",disclosureChanges:"공시변경 사항",contingentLiability:"우발채무",sanction:"제재/조치",subsequentEvents:"후발사건",expertConfirmation:"전문가 확인",subsidiaryDetail:"종속회사 상세",affiliateGroupDetail:"계열회사 상세",investmentInOtherDetail:"타법인 출자 상세",rndDetail:"R&D 상세"},j={I:"I. 회사의 개요",II:"II. 사업의 내용",III:"III. 재무에 관한 사항",IV:"IV. 감사인의 감사의견 등",V:"V. 이사의 경영진단 및 분석의견",VI:"VI. 이사회 등 회사의 기관에 관한 사항",VII:"VII. 주주에 관한 사항",VIII:"VIII. 임원 및 직원 등에 관한 사항",IX:"IX. 계열회사 등에 관한 사항",X:"X. 대주주 등과의 거래내용",XI:"XI. 그 밖에 투자자 보호를 위하여 필요한 사항",XII:"XII. 상세표"},Y={I:1,II:2,III:3,IV:4,V:5,VI:6,VII:7,VIII:8,IX:9,X:10,XI:11,XII:12};function M(x){return Y[x]??99}function G(x){return C[x]||x}function de(x){return j[x]||x||"기타"}Zn(()=>{r()&&$()});async function $(){var x,q;u(o,!0),u(s,null),u(l,null),u(c,null),u(f,[],!0),u(p,null),k=new Map;try{const I=await Hu(r());u(s,I.payload,!0),(x=n(s))!=null&&x.columns&&u(w,n(s).columns.filter(F=>/^\d{4}(Q[1-4])?$/.test(F)),!0);const W=te((q=n(s))==null?void 0:q.rows);W.length>0&&(u(i,new Set([W[0].chapter]),!0),W[0].topics.length>0&&g(W[0].topics[0].topic,W[0].chapter))}catch(I){console.error("viewer load error:",I)}u(o,!1)}async function g(x,q){var I;if(n(l)!==x){if(u(l,x,!0),u(c,q||null,!0),u(A,new Map,!0),u(y,new Map,!0),(I=a())==null||I(x,G(x)),k.has(x)){const W=k.get(x);u(f,W.blocks||[],!0),u(p,W.textDocument||null,!0);return}u(f,[],!0),u(p,null),u(b,!0);try{const W=await Gu(r(),x);u(f,W.blocks||[],!0),u(p,W.textDocument||null,!0),k.set(x,{blocks:n(f),textDocument:n(p)})}catch(W){console.error("topic load error:",W),u(f,[],!0),u(p,null)}u(b,!1)}}function K(x){const q=new Set(n(i));q.has(x)?q.delete(x):q.add(x),u(i,q,!0)}function ee(x,q){const I=new Map(n(A));I.get(x)===q?I.delete(x):I.set(x,q),u(A,I,!0)}function Z(x,q){const I=new Map(n(y));I.set(x,q),u(y,I,!0)}function L(x){return x==="updated"?"최근 수정":x==="new"?"신규":x==="stale"?"과거 유지":"유지"}function ce(x){return x==="updated"?"updated":x==="new"?"new":x==="stale"?"stale":"stable"}function te(x){if(!x)return[];const q=new Map,I=new Set;for(const W of x){const F=W.chapter||"";q.has(F)||q.set(F,{chapter:F,topics:[]}),I.has(W.topic)||(I.add(W.topic),q.get(F).topics.push({topic:W.topic,source:W.source||"docs"}))}return[...q.values()].sort((W,F)=>M(W.chapter)-M(F.chapter))}function we(x){return String(x).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function Ce(x){return String(x||"").replaceAll(" "," ").replace(/\s+/g," ").trim()}function Pe(x){return!x||x.length>88?!1:/^\[.+\]$/.test(x)||/^【.+】$/.test(x)||/^[IVX]+\.\s/.test(x)||/^\d+\.\s/.test(x)||/^[가-힣]\.\s/.test(x)||/^\(\d+\)\s/.test(x)||/^\([가-힣]\)\s/.test(x)}function ye(x){return/^\(\d+\)\s/.test(x)||/^\([가-힣]\)\s/.test(x)?"h5":"h4"}function ue(x){return/^\[.+\]$/.test(x)||/^【.+】$/.test(x)?"vw-h-bracket":/^\(\d+\)\s/.test(x)||/^\([가-힣]\)\s/.test(x)?"vw-h-sub":"vw-h-section"}function B(x){if(!x)return[];if(/^\|.+\|$/m.test(x)||/^#{1,3} /m.test(x)||/```/.test(x))return[{kind:"markdown",text:x}];const q=[];let I=[];const W=()=>{I.length!==0&&(q.push({kind:"paragraph",text:I.join(" ")}),I=[])};for(const F of String(x).split(`
`)){const Se=Ce(F);if(!Se){W();continue}if(Pe(Se)){W(),q.push({kind:"heading",text:Se,tag:ye(Se),className:ue(Se)});continue}I.push(Se)}return W(),q}function T(x){return x?x.kind==="annual"?`${x.year}Q4`:x.year&&x.quarter?`${x.year}Q${x.quarter}`:x.label||"":""}function V(x){var W;const q=B(x);if(q.length===0)return"";if(((W=q[0])==null?void 0:W.kind)==="markdown")return Ya(x);let I="";for(const F of q){if(F.kind==="heading"){I+=`<${F.tag} class="${F.className}">${we(F.text)}</${F.tag}>`;continue}I+=`<p class="vw-para">${we(F.text)}</p>`}return I}function ne(x){if(!x)return"";const q=x.trim().split(`
`).filter(W=>W.trim());let I="";for(const W of q){const F=W.trim();/^[가-힣]\.\s/.test(F)||/^\d+[-.]/.test(F)?I+=`<h4 class="vw-h-section">${F}</h4>`:/^\(\d+\)\s/.test(F)||/^\([가-힣]\)\s/.test(F)?I+=`<h5 class="vw-h-sub">${F}</h5>`:/^\[.+\]$/.test(F)||/^【.+】$/.test(F)?I+=`<h4 class="vw-h-bracket">${F}</h4>`:I+=`<h5 class="vw-h-sub">${F}</h5>`}return I}function se(x){var I;const q=n(A).get(x.id);return q&&((I=x==null?void 0:x.views)!=null&&I[q])?x.views[q]:(x==null?void 0:x.latest)||null}function me(x,q){var W,F;const I=n(A).get(x.id);return I?I===q:((F=(W=x==null?void 0:x.latest)==null?void 0:W.period)==null?void 0:F.label)===q}function fe(x){return n(A).has(x.id)}function he(x){return x==="updated"?"변경 있음":x==="new"?"직전 없음":"직전과 동일"}function ze(x){var Se,it,ft;if(!x)return[];const q=B(x.body);if(q.length===0||((Se=q[0])==null?void 0:Se.kind)==="markdown"||!((it=x.prevPeriod)!=null&&it.label)||!((ft=x.diff)!=null&&ft.length))return q;const I=[];for(const et of x.diff)for(const Lt of et.paragraphs||[])I.push({kind:et.kind,text:Ce(Lt)});const W=[];let F=0;for(const et of q){if(et.kind!=="paragraph"){W.push(et);continue}for(;F<I.length&&I[F].kind==="removed";)W.push({kind:"removed",text:I[F].text}),F+=1;F<I.length&&["same","added"].includes(I[F].kind)?(W.push({kind:I[F].kind,text:I[F].text||et.text}),F+=1):W.push({kind:"same",text:et.text})}for(;F<I.length;)W.push({kind:I[F].kind,text:I[F].text}),F+=1;return W}function X(x){return x==null?!1:/^-?[\d,.]+%?$/.test(String(x).trim().replace(/,/g,""))}function qt(x){return x==null?!1:/^-[\d.]+/.test(String(x).trim().replace(/,/g,""))}function ut(x,q){if(x==null||x==="")return"";const I=typeof x=="number"?x:Number(String(x).replace(/,/g,""));if(isNaN(I))return String(x);if(q<=1)return I.toLocaleString("ko-KR");const W=I/q;return Number.isInteger(W)?W.toLocaleString("ko-KR"):W.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g,",")}function zt(x){if(x==null||x==="")return"";const q=String(x).trim();if(q.includes(","))return q;const I=q.match(/^(-?\d+)(\.\d+)?(%?)$/);return I?I[1].replace(/\B(?=(\d{3})+(?!\d))/g,",")+(I[2]||"")+(I[3]||""):q}function Ze(x){var q,I;return(q=n(s))!=null&&q.rows&&((I=n(s).rows.find(W=>W.topic===x))==null?void 0:I.chapter)||null}function De(x){const q=x.match(/^(\d{4})(Q([1-4]))?$/);if(!q)return"0000_0";const I=q[1],W=q[3]||"5";return`${I}_${W}`}function mt(x){return[...x].sort((q,I)=>De(I).localeCompare(De(q)))}let Ht=U(()=>n(f).filter(x=>x.kind!=="text"));var Ot=Bm(),ht=d(Ot);{var gt=x=>{var q=Pp(),I=d(q);Yr(I,{size:18,class:"animate-spin"}),v(x,q)},Xt=x=>{var q=Fm(),I=d(q);{var W=et=>{var Lt=Rp(),Rt=d(Lt),Lr=d(Rt);{var qr=tt=>{var Xe=$p(),Tt=d(Xe);O(()=>N(Tt,`${n(w).length??""}개 기간 · ${n(w)[0]??""} ~ ${n(w)[n(w).length-1]??""}`)),v(tt,Xe)};z(Lr,tt=>{n(w).length>0&&tt(qr)})}var Mn=m(Rt,2);Ie(Mn,17,()=>te(n(s).rows),Te,(tt,Xe)=>{var Tt=Lp(),J=d(Tt),je=d(J);{var lt=nr=>{tv(nr,{size:11,class:"flex-shrink-0 opacity-40"})},Je=U(()=>n(i).has(n(Xe).chapter)),vt=nr=>{rv(nr,{size:11,class:"flex-shrink-0 opacity-40"})};z(je,nr=>{n(Je)?nr(lt):nr(vt,-1)})}var Dt=m(je,2),Ut=d(Dt),Oe=m(Dt,2),Mt=d(Oe),_r=m(J,2);{var Sr=nr=>{var En=Op();Ie(En,21,()=>n(Xe).topics,Te,(es,pn)=>{var jt=Np(),Ve=d(jt);{var wr=ir=>{Zf(ir,{size:11,class:"flex-shrink-0 text-blue-400/40"})},da=ir=>{$i(ir,{size:11,class:"flex-shrink-0 text-emerald-400/40"})},zn=ir=>{Ln(ir,{size:11,class:"flex-shrink-0 opacity-30"})};z(Ve,ir=>{n(pn).source==="finance"?ir(wr):n(pn).source==="report"?ir(da,1):ir(zn,-1)})}var ca=m(Ve,2),An=d(ca);O(ir=>{$e(jt,1,`group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											${n(l)===n(pn).topic?"bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]":"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent"}`),N(An,ir)},[()=>G(n(pn).topic)]),re("click",jt,()=>g(n(pn).topic,n(Xe).chapter)),v(es,jt)}),v(nr,En)},vn=U(()=>n(i).has(n(Xe).chapter));z(_r,nr=>{n(vn)&&nr(Sr)})}O(nr=>{N(Ut,nr),N(Mt,n(Xe).topics.length)},[()=>de(n(Xe).chapter)]),re("click",J,()=>K(n(Xe).chapter)),v(tt,Tt)}),v(et,Lt)};z(I,et=>{n(P)||et(W)})}var F=m(I,2),Se=d(F);{var it=et=>{var Lt=Dp(),Rt=d(Lt);Ln(Rt,{size:32,strokeWidth:1,class:"opacity-20"}),v(et,Lt)},ft=et=>{var Lt=Vm(),Rt=Q(Lt),Lr=d(Rt),qr=d(Lr);{var Mn=Oe=>{var Mt=jp(),_r=d(Mt);O(Sr=>N(_r,Sr),[()=>de(n(c)||Ze(n(l)))]),v(Oe,Mt)},tt=U(()=>n(c)||Ze(n(l)));z(qr,Oe=>{n(tt)&&Oe(Mn)})}var Xe=m(qr,2),Tt=d(Xe),J=m(Lr,2),je=d(J);{var lt=Oe=>{id(Oe,{size:15})},Je=Oe=>{od(Oe,{size:15})};z(je,Oe=>{n(P)?Oe(lt):Oe(Je,-1)})}var vt=m(Rt,2);{var Dt=Oe=>{var Mt=Vp(),_r=d(Mt);Yr(_r,{size:16,class:"animate-spin"}),v(Oe,Mt)},Ut=Oe=>{var Mt=jm(),_r=d(Mt);{var Sr=jt=>{var Ve=Fp();v(jt,Ve)};z(_r,jt=>{var Ve,wr;n(f).length===0&&!(((wr=(Ve=n(p))==null?void 0:Ve.sections)==null?void 0:wr.length)>0)&&jt(Sr)})}var vn=m(_r,2);{var nr=jt=>{var Ve=mm(),wr=d(Ve),da=d(wr),zn=d(da);{var ca=Qe=>{var ge=qp(),Fe=d(ge);O(rt=>N(Fe,`최신 기준 ${rt??""}`),[()=>T(n(p).latestPeriod)]),v(Qe,ge)};z(zn,Qe=>{n(p).latestPeriod&&Qe(ca)})}var An=m(zn,2);{var ir=Qe=>{var ge=Bp(),Fe=d(ge);O((rt,wt)=>N(Fe,`커버리지 ${rt??""}~${wt??""}`),[()=>T(n(p).firstPeriod),()=>T(n(p).latestPeriod)]),v(Qe,ge)};z(An,Qe=>{n(p).firstPeriod&&Qe(ir)})}var Fn=m(An,2),Wt=d(Fn),_t=m(Fn,2);{var lr=Qe=>{var ge=Gp(),Fe=d(ge);O(()=>N(Fe,`최근 수정 ${n(p).updatedCount??""}개`)),v(Qe,ge)};z(_t,Qe=>{n(p).updatedCount>0&&Qe(lr)})}var Kt=m(_t,2);{var yr=Qe=>{var ge=Hp(),Fe=d(ge);O(()=>N(Fe,`신규 ${n(p).newCount??""}개`)),v(Qe,ge)};z(Kt,Qe=>{n(p).newCount>0&&Qe(yr)})}var kr=m(Kt,2);{var dr=Qe=>{var ge=Up(),Fe=d(ge);O(()=>N(Fe,`과거 유지 ${n(p).staleCount??""}개`)),v(Qe,ge)};z(kr,Qe=>{n(p).staleCount>0&&Qe(dr)})}var Rr=m(wr,2);Ie(Rr,17,()=>n(p).sections,Te,(Qe,ge)=>{const Fe=U(()=>se(n(ge))),rt=U(()=>fe(n(ge)));var wt=pm(),cr=d(wt);{var Ae=ke=>{var S=Kp();Ie(S,21,()=>n(ge).headingPath,Te,(D,ie)=>{var be=Wp(),pe=d(be);ea(pe,()=>ne(n(ie).text)),v(D,be)}),v(ke,S)};z(cr,ke=>{var S;((S=n(ge).headingPath)==null?void 0:S.length)>0&&ke(Ae)})}var Ke=m(cr,2),at=d(Ke),It=d(at),yt=m(at,2);{var ur=ke=>{var S=Yp(),D=d(S);O(ie=>N(D,`최신 ${ie??""}`),[()=>T(n(ge).latestPeriod)]),v(ke,S)};z(yt,ke=>{var S;(S=n(ge).latestPeriod)!=null&&S.label&&ke(ur)})}var _=m(yt,2);{var R=ke=>{var S=Xp(),D=d(S);O(ie=>N(D,`최초 ${ie??""}`),[()=>T(n(ge).firstPeriod)]),v(ke,S)};z(_,ke=>{var S,D;(S=n(ge).firstPeriod)!=null&&S.label&&n(ge).firstPeriod.label!==((D=n(ge).latestPeriod)==null?void 0:D.label)&&ke(R)})}var le=m(_,2);{var _e=ke=>{var S=Jp(),D=d(S);O(()=>N(D,`${n(ge).periodCount??""}기간`)),v(ke,S)};z(le,ke=>{n(ge).periodCount>0&&ke(_e)})}var Me=m(le,2);{var Ee=ke=>{var S=Qp(),D=d(S);O(()=>N(D,`최근 변경 ${n(ge).latestChange??""}`)),v(ke,S)};z(Me,ke=>{n(ge).latestChange&&ke(Ee)})}var ve=m(Ke,2);{var st=ke=>{var S=em();Ie(S,21,()=>n(ge).timeline,Te,(D,ie)=>{var be=Zp(),pe=d(be),ct=d(pe);O((xt,pt)=>{$e(be,1,`vw-timeline-chip ${xt??""}`,"svelte-1l2nqwu"),N(ct,pt)},[()=>me(n(ge),n(ie).period.label)?"is-active":"",()=>T(n(ie).period)]),re("click",be,()=>ee(n(ge).id,n(ie).period.label)),v(D,be)}),v(ke,S)};z(ve,ke=>{var S;((S=n(ge).timeline)==null?void 0:S.length)>0&&ke(st)})}var Br=m(ve,2);{var fr=ke=>{var S=nm(),D=d(S),ie=d(D),be=m(D,2);{var pe=Vt=>{var Pt=tm(),zr=d(Pt);O(bt=>N(zr,`비교 ${bt??""}`),[()=>T(n(Fe).prevPeriod)]),v(Vt,Pt)},ct=Vt=>{var Pt=rm();v(Vt,Pt)};z(be,Vt=>{var Pt;(Pt=n(Fe).prevPeriod)!=null&&Pt.label?Vt(pe):Vt(ct,-1)})}var xt=m(be,2),pt=d(xt);O((Vt,Pt)=>{N(ie,`선택 ${Vt??""}`),N(pt,Pt)},[()=>T(n(Fe).period),()=>he(n(Fe).status)]),v(ke,S)};z(Br,ke=>{n(rt)&&n(Fe)&&ke(fr)})}var Tn=m(Br,2);{var qn=ke=>{const S=U(()=>n(Fe).digest);var D=lm(),ie=d(D),be=d(ie),pe=d(be),ct=m(ie,2),xt=d(ct);Ie(xt,17,()=>n(S).items.filter(bt=>bt.kind==="numeric"),Te,(bt,ar)=>{var Jt=am(),kt=m(d(Jt));O(()=>N(kt,` ${n(ar).text??""}`)),v(bt,Jt)});var pt=m(xt,2);Ie(pt,17,()=>n(S).items.filter(bt=>bt.kind==="added"),Te,(bt,ar)=>{var Jt=sm(),kt=m(d(Jt),2),Ft=d(kt);O(()=>N(Ft,n(ar).text)),v(bt,Jt)});var Vt=m(pt,2);Ie(Vt,17,()=>n(S).items.filter(bt=>bt.kind==="removed"),Te,(bt,ar)=>{var Jt=om(),kt=m(d(Jt),2),Ft=d(kt);O(()=>N(Ft,n(ar).text)),v(bt,Jt)});var Pt=m(Vt,2);{var zr=bt=>{var ar=im(),Jt=d(ar);O(()=>N(Jt,`외 ${n(S).wordingCount??""}건 문구 수정`)),v(bt,ar)};z(Pt,bt=>{n(S).wordingCount>0&&bt(zr)})}O(()=>N(pe,`${n(S).to??""} vs ${n(S).from??""}`)),v(ke,D)};z(Tn,ke=>{var S,D,ie;n(rt)&&((ie=(D=(S=n(Fe))==null?void 0:S.digest)==null?void 0:D.items)==null?void 0:ie.length)>0&&ke(qn)})}var Bn=m(Tn,2);{var Gn=ke=>{var S=xe(),D=Q(S);{var ie=pe=>{var ct=fm();Ie(ct,21,()=>ze(n(Fe)),Te,(xt,pt)=>{var Vt=xe(),Pt=Q(Vt);{var zr=kt=>{var Ft=xe(),Gr=Q(Ft);ea(Gr,()=>ne(n(pt).text)),v(kt,Ft)},bt=kt=>{var Ft=dm(),Gr=d(Ft);O(()=>N(Gr,n(pt).text)),v(kt,Ft)},ar=kt=>{var Ft=cm(),Gr=d(Ft);O(()=>N(Gr,n(pt).text)),v(kt,Ft)},Jt=kt=>{var Ft=um(),Gr=d(Ft);O(()=>N(Gr,n(pt).text)),v(kt,Ft)};z(Pt,kt=>{n(pt).kind==="heading"?kt(zr):n(pt).kind==="same"?kt(bt,1):n(pt).kind==="added"?kt(ar,2):n(pt).kind==="removed"&&kt(Jt,3)})}v(xt,Vt)}),v(pe,ct)},be=pe=>{var ct=vm(),xt=d(ct);ea(xt,()=>V(n(Fe).body)),v(pe,ct)};z(D,pe=>{var ct,xt;n(rt)&&((ct=n(Fe).prevPeriod)!=null&&ct.label)&&((xt=n(Fe).diff)==null?void 0:xt.length)>0?pe(ie):pe(be,-1)})}v(ke,S)};z(Bn,ke=>{n(Fe)&&ke(Gn)})}O((ke,S)=>{$e(wt,1,`vw-text-section ${n(ge).status==="stale"?"vw-text-section-stale":""}`,"svelte-1l2nqwu"),$e(at,1,`vw-status-pill ${ke??""}`,"svelte-1l2nqwu"),N(It,S)},[()=>ce(n(ge).status),()=>L(n(ge).status)]),v(Qe,wt)}),O(()=>N(Wt,`본문 ${n(p).sectionCount??""}개`)),v(jt,Ve)};z(vn,jt=>{var Ve,wr;((wr=(Ve=n(p))==null?void 0:Ve.sections)==null?void 0:wr.length)>0&&jt(nr)})}var En=m(vn,2);{var es=jt=>{var Ve=hm();v(jt,Ve)};z(En,jt=>{n(Ht).length>0&&jt(es)})}var pn=m(En,2);Ie(pn,17,()=>n(Ht),Te,(jt,Ve)=>{var wr=xe(),da=Q(wr);{var zn=Wt=>{const _t=U(()=>{var Ae;return((Ae=n(Ve).data)==null?void 0:Ae.columns)||[]}),lr=U(()=>{var Ae;return((Ae=n(Ve).data)==null?void 0:Ae.rows)||[]}),Kt=U(()=>n(Ve).meta||{}),yr=U(()=>n(Kt).scaleDivisor||1);var kr=wm(),dr=Q(kr);{var Rr=Ae=>{var Ke=gm(),at=d(Ke);O(()=>N(at,`(단위: ${n(Kt).scale??""})`)),v(Ae,Ke)};z(dr,Ae=>{n(Kt).scale&&Ae(Rr)})}var Qe=m(dr,2),ge=d(Qe),Fe=d(ge),rt=d(Fe),wt=d(rt);Ie(wt,21,()=>n(_t),Te,(Ae,Ke,at)=>{const It=U(()=>/^\d{4}/.test(n(Ke)));var yt=xm(),ur=d(yt);O(()=>{$e(yt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(It)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${at===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),N(ur,n(Ke))}),v(Ae,yt)});var cr=m(rt);Ie(cr,21,()=>n(lr),Te,(Ae,Ke,at)=>{var It=_m();$e(It,1,`hover:bg-white/[0.03] ${at%2===1?"bg-white/[0.012]":""}`),Ie(It,21,()=>n(_t),Te,(yt,ur,_)=>{const R=U(()=>n(Ke)[n(ur)]??""),le=U(()=>X(n(R))),_e=U(()=>qt(n(R))),Me=U(()=>n(le)?ut(n(R),n(yr)):n(R));var Ee=bm(),ve=d(Ee);O(()=>{$e(Ee,1,`px-3 py-1.5 border-b border-white/[0.025]
																	${n(le)?"text-right tabular-nums font-mono text-[11.5px]":"whitespace-nowrap"}
																	${n(_e)?"text-red-400/60":n(le)?"text-dl-text/90":""}
																	${_===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]":"text-dl-text-muted"}
																	${_===0&&at%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),N(ve,n(Me))}),v(yt,Ee)}),v(Ae,It)}),v(Wt,kr)},ca=Wt=>{const _t=U(()=>{var Ae;return((Ae=n(Ve).data)==null?void 0:Ae.columns)||[]}),lr=U(()=>{var Ae;return((Ae=n(Ve).data)==null?void 0:Ae.rows)||[]}),Kt=U(()=>n(Ve).meta||{}),yr=U(()=>n(Kt).scaleDivisor||1);var kr=Mm(),dr=Q(kr);{var Rr=Ae=>{var Ke=ym(),at=d(Ke);O(()=>N(at,`(단위: ${n(Kt).scale??""})`)),v(Ae,Ke)};z(dr,Ae=>{n(Kt).scale&&Ae(Rr)})}var Qe=m(dr,2),ge=d(Qe),Fe=d(ge),rt=d(Fe),wt=d(rt);Ie(wt,21,()=>n(_t),Te,(Ae,Ke,at)=>{const It=U(()=>/^\d{4}/.test(n(Ke)));var yt=km(),ur=d(yt);O(()=>{$e(yt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(It)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${at===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),N(ur,n(Ke))}),v(Ae,yt)});var cr=m(rt);Ie(cr,21,()=>n(lr),Te,(Ae,Ke,at)=>{var It=Sm();$e(It,1,`hover:bg-white/[0.03] ${at%2===1?"bg-white/[0.012]":""}`),Ie(It,21,()=>n(_t),Te,(yt,ur,_)=>{const R=U(()=>n(Ke)[n(ur)]??""),le=U(()=>X(n(R))),_e=U(()=>qt(n(R))),Me=U(()=>n(le)?n(yr)>1?ut(n(R),n(yr)):zt(n(R)):n(R));var Ee=Cm(),ve=d(Ee);O(()=>{$e(Ee,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(le)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(_e)?"text-red-400/60":n(le)?"text-dl-text/90":""}
																	${_===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${_===0&&at%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),N(ve,n(Me))}),v(yt,Ee)}),v(Ae,It)}),v(Wt,kr)},An=Wt=>{const _t=U(()=>mt(Object.keys(n(Ve).rawMarkdown))),lr=U(()=>n(y).get(n(Ve).block)??0),Kt=U(()=>n(_t)[n(lr)]||n(_t)[0]);var yr=Tm(),kr=d(yr);{var dr=Fe=>{var rt=Am(),wt=d(rt);Ie(wt,17,()=>n(_t).slice(0,8),Te,(Ke,at,It)=>{var yt=Em(),ur=d(yt);O(()=>{$e(yt,1,`px-2 py-0.5 rounded text-[10px] transition-colors
															${It===n(lr)?"bg-white/[0.08] text-dl-text font-medium":"text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]"}`),N(ur,n(at))}),re("click",yt,()=>Z(n(Ve).block,It)),v(Ke,yt)});var cr=m(wt,2);{var Ae=Ke=>{var at=zm(),It=d(at);O(()=>N(It,`외 ${n(_t).length-8}개`)),v(Ke,at)};z(cr,Ke=>{n(_t).length>8&&Ke(Ae)})}v(Fe,rt)};z(kr,Fe=>{n(_t).length>1&&Fe(dr)})}var Rr=m(kr,2),Qe=d(Rr),ge=d(Qe);ea(ge,()=>Ya(n(Ve).rawMarkdown[n(Kt)])),v(Wt,yr)},ir=Wt=>{const _t=U(()=>{var rt;return((rt=n(Ve).data)==null?void 0:rt.columns)||[]}),lr=U(()=>{var rt;return((rt=n(Ve).data)==null?void 0:rt.rows)||[]});var Kt=Nm(),yr=d(Kt),kr=d(yr);$i(kr,{size:12,class:"text-emerald-400/50"});var dr=m(yr,2),Rr=d(dr),Qe=d(Rr),ge=d(Qe);Ie(ge,21,()=>n(_t),Te,(rt,wt,cr)=>{const Ae=U(()=>/^\d{4}/.test(n(wt)));var Ke=Im(),at=d(Ke);O(()=>{$e(Ke,1,`px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															${n(Ae)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
															${cr===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),N(at,n(wt))}),v(rt,Ke)});var Fe=m(Qe);Ie(Fe,21,()=>n(lr),Te,(rt,wt,cr)=>{var Ae=$m();$e(Ae,1,`hover:bg-white/[0.03] ${cr%2===1?"bg-white/[0.012]":""}`),Ie(Ae,21,()=>n(_t),Te,(Ke,at,It)=>{const yt=U(()=>n(wt)[n(at)]??""),ur=U(()=>X(n(yt))),_=U(()=>qt(n(yt)));var R=Pm(),le=d(R);O(_e=>{$e(R,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(ur)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(_)?"text-red-400/60":n(ur)?"text-dl-text/90":""}
																	${It===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${It===0&&cr%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),N(le,_e)},[()=>n(ur)?zt(n(yt)):n(yt)]),v(Ke,R)}),v(rt,Ae)}),v(Wt,Kt)},Fn=Wt=>{const _t=U(()=>n(Ve).data.columns),lr=U(()=>n(Ve).data.rows||[]);var Kt=Dm(),yr=d(Kt),kr=d(yr),dr=d(kr),Rr=d(dr);Ie(Rr,21,()=>n(_t),Te,(ge,Fe)=>{var rt=Om(),wt=d(rt);O(()=>N(wt,n(Fe))),v(ge,rt)});var Qe=m(dr);Ie(Qe,21,()=>n(lr),Te,(ge,Fe,rt)=>{var wt=Rm();$e(wt,1,`hover:bg-white/[0.03] ${rt%2===1?"bg-white/[0.012]":""}`),Ie(wt,21,()=>n(_t),Te,(cr,Ae)=>{var Ke=Lm(),at=d(Ke);O(()=>N(at,n(Fe)[n(Ae)]??"")),v(cr,Ke)}),v(ge,wt)}),v(Wt,Kt)};z(da,Wt=>{var _t,lr;n(Ve).kind==="finance"?Wt(zn):n(Ve).kind==="structured"?Wt(ca,1):n(Ve).kind==="raw_markdown"&&n(Ve).rawMarkdown?Wt(An,2):n(Ve).kind==="report"?Wt(ir,3):((lr=(_t=n(Ve).data)==null?void 0:_t.columns)==null?void 0:lr.length)>0&&Wt(Fn,4)})}v(jt,wr)}),v(Oe,Mt)};z(vt,Oe=>{n(b)?Oe(Dt):Oe(Ut,-1)})}O(Oe=>{N(Tt,Oe),Dn(J,"title",n(P)?"목차 표시":"전체화면")},[()=>G(n(l))]),re("click",J,()=>u(P,!n(P))),v(et,Lt)};z(Se,et=>{n(l)?et(ft,-1):et(it)})}v(x,q)},At=x=>{var q=qm(),I=d(q);Ln(I,{size:36,strokeWidth:1,class:"opacity-20"}),v(x,q)};z(ht,x=>{var q;n(o)?x(gt):(q=n(s))!=null&&q.rows?x(Xt,1):x(At,-1)})}v(e,Ot),tn()}Vn(["click"]);var Hm=h('<span class="text-[12px] font-semibold text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim"> </span>',1),Um=h('<span class="text-[12px] font-semibold text-dl-text"> </span>'),Wm=h('<span class="text-[12px] font-semibold text-dl-text">데이터</span>'),Km=h('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" title="Excel 다운로드"><!></button> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button>',1),Ym=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Xm=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed"> </pre>'),Jm=h('<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2"> </div>'),Qm=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Zm=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),eh=h("<!> <!>",1),th=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),rh=h('<div class="p-4"><!></div>'),nh=h('<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">표시할 내용이 없습니다</div>'),ah=h('<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark"><div class="flex items-center justify-between h-10 mt-8 px-4 border-b border-dl-border/40 flex-shrink-0"><div class="flex items-center gap-2 min-w-0"><!></div> <div class="flex items-center gap-1"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 overflow-auto min-h-0"><!></div></div>');function sh(e,t){en(t,!0);let r=nt(t,"mode",3,null),a=nt(t,"company",3,null),s=nt(t,"data",3,null),o=nt(t,"onTopicChange",3,null),i=nt(t,"onFullscreen",3,null),l=nt(t,"isFullscreen",3,!1),c=H(!1);async function f(){var L;if(!(!((L=a())!=null&&L.stockCode)||n(c))){u(c,!0);try{await Bu(a().stockCode)}catch(ce){console.error("Excel download error:",ce)}u(c,!1)}}function p(L){return L?/^\|.+\|$/m.test(L)||/^#{1,3} /m.test(L)||/\*\*[^*]+\*\*/m.test(L)||/```/.test(L):!1}var b=ah(),w=d(b),A=d(w),k=d(A);{var P=L=>{var ce=Hm(),te=Q(ce),we=d(te),Ce=m(te,2),Pe=d(Ce);O(()=>{N(we,a().corpName||a().company),N(Pe,a().stockCode)}),v(L,ce)},y=L=>{var ce=Um(),te=d(ce);O(()=>N(te,s().label)),v(L,ce)},C=L=>{var ce=Wm();v(L,ce)};z(k,L=>{var ce;r()==="viewer"&&a()?L(P):r()==="data"&&((ce=s())!=null&&ce.label)?L(y,1):r()==="data"&&L(C,2)})}var j=m(A,2),Y=d(j);{var M=L=>{var ce=Km(),te=Q(ce),we=d(te);{var Ce=V=>{Yr(V,{size:14,class:"animate-spin"})},Pe=V=>{xs(V,{size:14})};z(we,V=>{n(c)?V(Ce):V(Pe,-1)})}var ye=m(te,2),ue=d(ye);{var B=V=>{id(V,{size:14})},T=V=>{od(V,{size:14})};z(ue,V=>{l()?V(B):V(T,-1)})}O(()=>{te.disabled=n(c),Dn(ye,"title",l()?"패널 모드로":"전체 화면")}),re("click",te,f),re("click",ye,()=>{var V;return(V=i())==null?void 0:V()}),v(L,ce)};z(Y,L=>{var ce;r()==="viewer"&&((ce=a())!=null&&ce.stockCode)&&L(M)})}var G=m(Y,2),de=d(G);js(de,{size:15});var $=m(w,2),g=d($);{var K=L=>{Gm(L,{get stockCode(){return a().stockCode},get onTopicChange(){return o()}})},ee=L=>{var ce=rh(),te=d(ce);{var we=ye=>{var ue=xe(),B=Q(ue);{var T=se=>{var me=Ym(),fe=d(me);ea(fe,()=>Ya(s())),v(se,me)},V=U(()=>p(s())),ne=se=>{var me=Xm(),fe=d(me);O(()=>N(fe,s())),v(se,me)};z(B,se=>{n(V)?se(T):se(ne,-1)})}v(ye,ue)},Ce=ye=>{var ue=eh(),B=Q(ue);{var T=fe=>{var he=Jm(),ze=d(he);O(()=>N(ze,s().module)),v(fe,he)};z(B,fe=>{s().module&&fe(T)})}var V=m(B,2);{var ne=fe=>{var he=Qm(),ze=d(he);ea(ze,()=>Ya(s().text)),v(fe,he)},se=U(()=>p(s().text)),me=fe=>{var he=Zm(),ze=d(he);O(()=>N(ze,s().text)),v(fe,he)};z(V,fe=>{n(se)?fe(ne):fe(me,-1)})}v(ye,ue)},Pe=ye=>{var ue=th(),B=d(ue);O(T=>N(B,T),[()=>JSON.stringify(s(),null,2)]),v(ye,ue)};z(te,ye=>{var ue;typeof s()=="string"?ye(we):(ue=s())!=null&&ue.text?ye(Ce,1):ye(Pe,-1)})}v(L,ce)},Z=L=>{var ce=nh();v(L,ce)};z(g,L=>{r()==="viewer"&&a()?L(K):r()==="data"&&s()?L(ee,1):L(Z,-1)})}re("click",G,()=>{var L;return(L=t.onClose)==null?void 0:L.call(t)}),v(e,b),tn()}Vn(["click"]);var oh=h('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),ih=h("<!> <span>확인 중...</span>",1),lh=h("<!> <span>설정 필요</span>",1),dh=h('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),ch=h('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!>',1),uh=h('<div class="flex-shrink-0 border-l border-dl-border/30 transition-all duration-300"><!></div>'),fh=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),vh=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),ph=h('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),mh=h('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),hh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),gh=h('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),xh=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),bh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),_h=h('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),wh=h('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),yh=h('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),kh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2">설치 완료 후 새로고침하세요</div></div>'),Ch=h("<!> 브라우저에서 로그인 중...",1),Sh=h("<!> OpenAI 계정으로 로그인",1),Mh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2.5">ChatGPT 계정으로 로그인하여 사용하세요</div> <button class="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div></div>'),Eh=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),zh=h('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),Ah=h("<button> <!></button>"),Th=h('<div class="flex flex-wrap gap-1.5"></div>'),Ih=h('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),Ph=h('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),$h=h('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),Nh=h('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),Oh=h('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),Lh=h('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),Rh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),Dh=h("<!> <!> <!> <!> <!> <!> <!>",1),jh=h('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),Vh=h('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),Fh=h('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),qh=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><span class="text-[10px] text-dl-text-dim">공시 보기</span> <!></div></button>'),Bh=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div></div> <!>',1),Gh=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div></button>'),Hh=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div></div> <!>',1),Uh=h('<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),Wh=h('<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim"><!> <div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div> <div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div></div>'),Kh=h('<div class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn" role="presentation"><div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"><div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"/> <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div> <div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim"><span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span></div></div></div>'),Yh=h('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),Xh=h('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-2 left-3 z-20 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="종목 검색 (Ctrl+K)"><!></button> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <button><!> <!></button></div> <div class="flex flex-1 min-h-0"><div class="min-w-0 flex-1 flex flex-col"><!></div> <!></div></div></div>  <!> <!> <!> <!>',1);function Jh(e,t){en(t,!0);let r=H(""),a=H(!1),s=H(null),o=H(Et({})),i=H(Et({})),l=H(null),c=H(null),f=H(Et([])),p=H(!1),b=H(0),w=H(!0),A=H(""),k=H(!1),P=H(null),y=H(Et({})),C=H(Et({})),j=H(""),Y=H(!1),M=H(null),G=H(""),de=H(!1),$=H(""),g=H(0),K=H(null),ee=H(!1),Z=H(Et({})),L=H(null),ce=H(null);const te=Gf();let we=H(!1),Ce=U(()=>n(we)?"100%":te.panelMode==="viewer"?"65%":"50%"),Pe=H(!1),ye=H(""),ue=H(Et([])),B=H(-1),T=null,V=H(!1);function ne(){u(V,window.innerWidth<=768),n(V)&&(u(p,!1),te.closePanel())}Zn(()=>(ne(),window.addEventListener("resize",ne),()=>window.removeEventListener("resize",ne))),Zn(()=>{!n(k)||!n(L)||requestAnimationFrame(()=>{var _;return(_=n(L))==null?void 0:_.focus()})}),Zn(()=>{!n(se)||!n(ce)||requestAnimationFrame(()=>{var _;return(_=n(ce))==null?void 0:_.focus()})});let se=H(null),me=H(""),fe=H("error"),he=H(!1);function ze(_,R="error",le=4e3){u(me,_,!0),u(fe,R,!0),u(he,!0),setTimeout(()=>{u(he,!1)},le)}const X=Vf();Zn(()=>{ut()});let qt=H(Et({}));async function ut(){var _,R,le;u(w,!0);try{const _e=await Ru();u(o,_e.providers||{},!0),u(i,_e.ollama||{},!0),u(qt,_e.codex||{},!0),u(Z,_e.chatgpt||{},!0),_e.version&&u(A,_e.version,!0);const Me=localStorage.getItem("dartlab-provider"),Ee=localStorage.getItem("dartlab-model");if(Me&&((_=n(o)[Me])!=null&&_.available)){u(l,Me,!0),u(P,Me,!0),await Pa(Me,Ee),await zt(Me);const ve=n(y)[Me]||[];Ee&&ve.includes(Ee)?u(c,Ee,!0):ve.length>0&&(u(c,ve[0],!0),localStorage.setItem("dartlab-model",n(c))),u(f,ve,!0),u(w,!1);return}if(Me&&n(o)[Me]){u(l,Me,!0),u(P,Me,!0),await zt(Me);const ve=n(y)[Me]||[];u(f,ve,!0),Ee&&ve.includes(Ee)?u(c,Ee,!0):ve.length>0&&u(c,ve[0],!0),u(w,!1);return}for(const ve of["chatgpt","codex","ollama"])if((R=n(o)[ve])!=null&&R.available){u(l,ve,!0),u(P,ve,!0),await Pa(ve),await zt(ve);const st=n(y)[ve]||[];u(f,st,!0),u(c,((le=n(o)[ve])==null?void 0:le.model)||(st.length>0?st[0]:null),!0),n(c)&&localStorage.setItem("dartlab-model",n(c));break}}catch{}u(w,!1)}async function zt(_){u(C,{...n(C),[_]:!0},!0);try{const R=await Du(_);u(y,{...n(y),[_]:R.models||[]},!0)}catch{u(y,{...n(y),[_]:[]},!0)}u(C,{...n(C),[_]:!1},!0)}async function Ze(_){var le;u(l,_,!0),u(c,null),u(P,_,!0),localStorage.setItem("dartlab-provider",_),localStorage.removeItem("dartlab-model"),u(j,""),u(M,null);try{await Pa(_)}catch{}await zt(_);const R=n(y)[_]||[];if(u(f,R,!0),R.length>0){u(c,((le=n(o)[_])==null?void 0:le.model)||R[0],!0),localStorage.setItem("dartlab-model",n(c));try{await Pa(_,n(c))}catch{}}}async function De(_){u(c,_,!0),localStorage.setItem("dartlab-model",_);try{await Pa(n(l),_)}catch{}}function mt(_){n(P)===_?u(P,null):(u(P,_,!0),zt(_))}async function Ht(){const _=n(j).trim();if(!(!_||!n(l))){u(Y,!0),u(M,null);try{const R=await Pa(n(l),n(c),_);R.available?(u(M,"success"),n(o)[n(l)]={...n(o)[n(l)],available:!0,model:R.model},!n(c)&&R.model&&u(c,R.model,!0),await zt(n(l)),u(f,n(y)[n(l)]||[],!0),ze("API 키 인증 성공","success")):u(M,"error")}catch{u(M,"error")}u(Y,!1)}}async function Ot(){if(!n(ee)){u(ee,!0);try{const{authUrl:_}=await Vu();window.open(_,"dartlab-oauth","width=600,height=700");const R=setInterval(async()=>{var le;try{const _e=await Fu();_e.done&&(clearInterval(R),u(ee,!1),_e.error?ze(`인증 실패: ${_e.error}`):(ze("ChatGPT 인증 성공","success"),await ut(),(le=n(o).chatgpt)!=null&&le.available&&await Ze("chatgpt")))}catch{clearInterval(R),u(ee,!1)}},2e3);setTimeout(()=>{clearInterval(R),n(ee)&&(u(ee,!1),ze("인증 시간이 초과되었습니다. 다시 시도해주세요."))},12e4)}catch(_){u(ee,!1),ze(`OAuth 시작 실패: ${_.message}`)}}}async function ht(){try{await qu(),u(Z,{authenticated:!1},!0),n(l)==="chatgpt"&&u(o,{...n(o),chatgpt:{...n(o).chatgpt,available:!1}},!0),ze("ChatGPT 로그아웃 완료","success"),await ut()}catch{ze("로그아웃 실패")}}function gt(){const _=n(G).trim();!_||n(de)||(u(de,!0),u($,"준비 중..."),u(g,0),u(K,ju(_,{onProgress(R){R.total&&R.completed!==void 0?(u(g,Math.round(R.completed/R.total*100),!0),u($,`다운로드 중... ${n(g)}%`)):R.status&&u($,R.status,!0)},async onDone(){u(de,!1),u(K,null),u(G,""),u($,""),u(g,0),ze(`${_} 다운로드 완료`,"success"),await zt("ollama"),u(f,n(y).ollama||[],!0),n(f).includes(_)&&await De(_)},onError(R){u(de,!1),u(K,null),u($,""),u(g,0),ze(`다운로드 실패: ${R}`)}}),!0))}function Xt(){n(K)&&(n(K).abort(),u(K,null)),u(de,!1),u(G,""),u($,""),u(g,0)}function At(){u(p,!n(p))}function x(_){te.openData(_)}function q(_,R=null){te.openEvidence(_,R)}function I(_){te.openViewer(_)}function W(){if(u(j,""),u(M,null),n(l))u(P,n(l),!0);else{const _=Object.keys(n(o));u(P,_.length>0?_[0]:null,!0)}u(k,!0),n(P)&&zt(n(P))}function F(_){var R,le,_e,Me;if(_)for(let Ee=_.messages.length-1;Ee>=0;Ee--){const ve=_.messages[Ee];if(ve.role==="assistant"&&((R=ve.meta)!=null&&R.stockCode||(le=ve.meta)!=null&&le.company||ve.company)){te.syncCompanyFromMessage({company:((_e=ve.meta)==null?void 0:_e.company)||ve.company,stockCode:(Me=ve.meta)==null?void 0:Me.stockCode},te.selectedCompany);return}}}function Se(){X.createConversation(),u(r,""),u(a,!1),n(s)&&(n(s).abort(),u(s,null))}function it(_){X.setActive(_),F(X.active),u(r,""),u(a,!1),n(s)&&(n(s).abort(),u(s,null))}function ft(_){u(se,_,!0)}function et(){n(se)&&(X.deleteConversation(n(se)),u(se,null))}function Lt(){var R;const _=X.active;if(!_)return null;for(let le=_.messages.length-1;le>=0;le--){const _e=_.messages[le];if(_e.role==="assistant"&&((R=_e.meta)!=null&&R.stockCode))return _e.meta.stockCode}return null}async function Rt(_=null){var qn,Bn,Gn,ke;const R=(_??n(r)).trim();if(!R||n(a))return;if(!n(l)||!((qn=n(o)[n(l)])!=null&&qn.available)){ze("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),W();return}X.activeId||X.createConversation();const le=X.activeId;X.addMessage("user",R),u(r,""),u(a,!0),X.addMessage("assistant",""),X.updateLastMessage({loading:!0,startedAt:Date.now()}),ps(b);const _e=X.active,Me=[];let Ee=null;if(_e){const S=_e.messages.slice(0,-2);for(const D of S)if((D.role==="user"||D.role==="assistant")&&D.text&&D.text.trim()&&!D.error&&!D.loading){const ie={role:D.role,text:D.text};D.role==="assistant"&&((Bn=D.meta)!=null&&Bn.stockCode)&&(ie.meta={company:D.meta.company||D.company,stockCode:D.meta.stockCode,modules:D.meta.includedModules||null},Ee=D.meta.stockCode),Me.push(ie)}}const ve=((Gn=te.selectedCompany)==null?void 0:Gn.stockCode)||Ee||Lt(),st=te.getViewContext();let Br=R;if((st==null?void 0:st.type)==="viewer"&&st.company){let S=`
[사용자가 현재 ${st.company.corpName}(${st.company.stockCode}) 공시를 보고 있습니다`;st.topic&&(S+=` — 현재 섹션: ${st.topicLabel||st.topic}(${st.topic})`),S+="]",Br+=S}else(st==null?void 0:st.type)==="data"&&((ke=st.data)!=null&&ke.label)&&(Br+=`
[사용자가 현재 "${st.data.label}" 데이터를 보고 있습니다]`);function fr(){return X.activeId!==le}const Tn=Uu(ve,Br,{provider:n(l),model:n(c)},{onMeta(S){var ct;if(fr())return;const D=X.active,ie=D==null?void 0:D.messages[D.messages.length-1],pe={meta:{...(ie==null?void 0:ie.meta)||{},...S}};S.company&&(pe.company=S.company,X.activeId&&((ct=X.active)==null?void 0:ct.title)==="새 대화"&&X.updateTitle(X.activeId,S.company)),S.stockCode&&(pe.stockCode=S.stockCode),(S.company||S.stockCode)&&te.syncCompanyFromMessage(S,te.selectedCompany),X.updateLastMessage(pe)},onSnapshot(S){fr()||X.updateLastMessage({snapshot:S})},onContext(S){if(fr())return;const D=X.active;if(!D)return;const ie=D.messages[D.messages.length-1],be=(ie==null?void 0:ie.contexts)||[];X.updateLastMessage({contexts:[...be,{module:S.module,label:S.label,text:S.text}]})},onSystemPrompt(S){fr()||X.updateLastMessage({systemPrompt:S.text,userContent:S.userContent||null})},onToolCall(S){if(fr())return;const D=X.active;if(!D)return;const ie=D.messages[D.messages.length-1],be=(ie==null?void 0:ie.toolEvents)||[];X.updateLastMessage({toolEvents:[...be,{type:"call",name:S.name,arguments:S.arguments}]})},onToolResult(S){if(fr())return;const D=X.active;if(!D)return;const ie=D.messages[D.messages.length-1],be=(ie==null?void 0:ie.toolEvents)||[];X.updateLastMessage({toolEvents:[...be,{type:"result",name:S.name,result:S.result}]})},onChunk(S){if(fr())return;const D=X.active;if(!D)return;const ie=D.messages[D.messages.length-1];X.updateLastMessage({text:((ie==null?void 0:ie.text)||"")+S}),ps(b)},onDone(){if(fr())return;const S=X.active,D=S==null?void 0:S.messages[S.messages.length-1],ie=D!=null&&D.startedAt?((Date.now()-D.startedAt)/1e3).toFixed(1):null;X.updateLastMessage({loading:!1,duration:ie}),X.flush(),u(a,!1),u(s,null),ps(b)},onError(S,D,ie){fr()||(X.updateLastMessage({text:`오류: ${S}`,loading:!1,error:!0}),X.flush(),D==="relogin"||D==="login"?(ze(`${S} — 설정에서 재로그인하세요`),W()):ze(D==="check_headers"||D==="check_endpoint"||D==="check_client_id"?`${S} — ChatGPT API 변경 감지. 업데이트를 확인하세요`:D==="rate_limit"?"요청이 너무 많습니다. 잠시 후 다시 시도해주세요":S),u(a,!1),u(s,null))}},Me);u(s,Tn,!0)}function Lr(){n(s)&&(n(s).abort(),u(s,null),u(a,!1),X.updateLastMessage({loading:!1}),X.flush())}function qr(){const _=X.active;if(!_||_.messages.length<2)return;let R="";for(let le=_.messages.length-1;le>=0;le--)if(_.messages[le].role==="user"){R=_.messages[le].text;break}R&&(X.removeLastMessage(),X.removeLastMessage(),u(r,R,!0),requestAnimationFrame(()=>{Rt()}))}function Mn(){const _=X.active;if(!_)return;let R=`# ${_.title}

`;for(const Ee of _.messages)Ee.role==="user"?R+=`## You

${Ee.text}

`:Ee.role==="assistant"&&Ee.text&&(R+=`## DartLab

${Ee.text}

`);const le=new Blob([R],{type:"text/markdown;charset=utf-8"}),_e=URL.createObjectURL(le),Me=document.createElement("a");Me.href=_e,Me.download=`${_.title||"dartlab-chat"}.md`,Me.click(),URL.revokeObjectURL(_e),ze("대화가 마크다운으로 내보내졌습니다","success")}function tt(){u(Pe,!0),u(ye,""),u(ue,[],!0),u(B,-1)}function Xe(_){(_.metaKey||_.ctrlKey)&&_.key==="n"&&(_.preventDefault(),Se()),(_.metaKey||_.ctrlKey)&&_.key==="k"&&(_.preventDefault(),tt()),(_.metaKey||_.ctrlKey)&&_.shiftKey&&_.key==="S"&&(_.preventDefault(),At()),_.key==="Escape"&&n(Pe)?u(Pe,!1):_.key==="Escape"&&n(k)?u(k,!1):_.key==="Escape"&&n(se)?u(se,null):_.key==="Escape"&&te.panelOpen&&te.closePanel()}let Tt=U(()=>{var _;return((_=X.active)==null?void 0:_.messages)||[]}),J=U(()=>X.active&&X.active.messages.length>0),je=U(()=>{var _;return!n(w)&&(!n(l)||!((_=n(o)[n(l)])!=null&&_.available))});const lt=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var Je=Xh();Na("keydown",yo,Xe);var vt=Q(Je),Dt=d(vt);{var Ut=_=>{var R=oh();re("click",R,()=>{u(p,!1)}),v(_,R)};z(Dt,_=>{n(V)&&n(p)&&_(Ut)})}var Oe=m(Dt,2),Mt=d(Oe);{let _=U(()=>n(V)?!0:n(p));Ev(Mt,{get conversations(){return X.conversations},get activeId(){return X.activeId},get open(){return n(_)},get version(){return n(A)},onNewChat:()=>{Se(),n(V)&&u(p,!1)},onSelect:R=>{it(R),n(V)&&u(p,!1)},onDelete:ft,onOpenSearch:tt})}var _r=m(Oe,2),Sr=d(_r),vn=d(Sr),nr=d(vn);{var En=_=>{uv(_,{size:18})},es=_=>{cv(_,{size:18})};z(nr,_=>{n(p)?_(En):_(es,-1)})}var pn=m(Sr,2),jt=d(pn),Ve=d(jt);bs(Ve,{size:14});var wr=m(jt,2),da=d(wr);Ln(da,{size:14});var zn=m(wr,2),ca=d(zn);iv(ca,{size:14});var An=m(zn,2),ir=d(An);sv(ir,{size:14});var Fn=m(An,2),Wt=d(Fn);{var _t=_=>{var R=ih(),le=Q(R);Yr(le,{size:12,class:"animate-spin"}),v(_,R)},lr=_=>{var R=lh(),le=Q(R);cs(le,{size:12}),v(_,R)},Kt=_=>{var R=ch(),le=m(Q(R),2),_e=d(le),Me=m(le,2);{var Ee=ve=>{var st=dh(),Br=m(Q(st),2),fr=d(Br);O(()=>N(fr,n(c))),v(ve,st)};z(Me,ve=>{n(c)&&ve(Ee)})}O(()=>N(_e,n(l))),v(_,R)};z(Wt,_=>{n(w)?_(_t):n(je)?_(lr,1):_(Kt,-1)})}var yr=m(Wt,2);vv(yr,{size:12});var kr=m(pn,2),dr=d(kr),Rr=d(dr);{var Qe=_=>{Ip(_,{get messages(){return n(Tt)},get isLoading(){return n(a)},get scrollTrigger(){return n(b)},get selectedCompany(){return te.selectedCompany},onSend:Rt,onStop:Lr,onRegenerate:qr,onExport:Mn,onOpenData:x,onOpenEvidence:q,onCompanySelect:I,get inputText(){return n(r)},set inputText(R){u(r,R,!0)}})},ge=_=>{Lv(_,{onSend:Rt,onCompanySelect:I,get inputText(){return n(r)},set inputText(R){u(r,R,!0)}})};z(Rr,_=>{n(J)?_(Qe):_(ge,-1)})}var Fe=m(dr,2);{var rt=_=>{var R=uh(),le=d(R);sh(le,{get mode(){return te.panelMode},get company(){return te.selectedCompany},get data(){return te.panelData},onClose:()=>{u(we,!1),te.closePanel()},onTopicChange:(_e,Me)=>te.setViewerTopic(_e,Me),onFullscreen:()=>{u(we,!n(we))},get isFullscreen(){return n(we)}}),O(()=>zo(R,`width: ${n(Ce)??""}; min-width: 360px; ${n(we)?"":"max-width: 75vw;"}`)),v(_,R)};z(Fe,_=>{!n(V)&&te.panelOpen&&_(rt)})}var wt=m(vt,2);{var cr=_=>{var R=Vh(),le=d(R),_e=d(le),Me=d(_e),Ee=m(d(Me),2),ve=d(Ee);js(ve,{size:18});var st=m(_e,2),Br=d(st);Ie(Br,21,()=>Object.entries(n(o)),Te,(S,D)=>{var ie=U(()=>Hi(n(D),2));let be=()=>n(ie)[0],pe=()=>n(ie)[1];const ct=U(()=>be()===n(l)),xt=U(()=>n(P)===be()),pt=U(()=>pe().auth==="api_key"),Vt=U(()=>pe().auth==="cli"),Pt=U(()=>n(y)[be()]||[]),zr=U(()=>n(C)[be()]);var bt=jh(),ar=d(bt),Jt=d(ar),kt=m(Jt,2),Ft=d(kt),Gr=d(Ft),Ks=d(Gr),dd=m(Gr,2);{var cd=Qt=>{var Hr=fh();v(Qt,Hr)};z(dd,Qt=>{n(ct)&&Qt(cd)})}var ud=m(Ft,2),fd=d(ud),vd=m(kt,2),pd=d(vd);{var md=Qt=>{gs(Qt,{size:16,class:"text-dl-success"})},hd=Qt=>{var Hr=vh(),Aa=Q(Hr);Oi(Aa,{size:14,class:"text-amber-400"}),v(Qt,Hr)},gd=Qt=>{var Hr=ph(),Aa=Q(Hr);mv(Aa,{size:14,class:"text-dl-text-dim"}),v(Qt,Hr)};z(pd,Qt=>{pe().available?Qt(md):n(pt)?Qt(hd,1):n(Vt)&&!pe().available&&Qt(gd,2)})}var xd=m(ar,2);{var bd=Qt=>{var Hr=Dh(),Aa=Q(Hr);{var _d=dt=>{var $t=hh(),Bt=d($t),vr=d(Bt),Cr=m(Bt,2),Zt=d(Cr),Ar=m(Zt,2),In=d(Ar);{var Mr=ot=>{Yr(ot,{size:12,class:"animate-spin"})},Yt=ot=>{Oi(ot,{size:12})};z(In,ot=>{n(Y)?ot(Mr):ot(Yt,-1)})}var Tr=m(Cr,2);{var Nt=ot=>{var Dr=mh(),pr=d(Dr);cs(pr,{size:12}),v(ot,Dr)};z(Tr,ot=>{n(M)==="error"&&ot(Nt)})}O(ot=>{N(vr,pe().envKey?`환경변수 ${pe().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),Dn(Zt,"placeholder",be()==="openai"?"sk-...":be()==="claude"?"sk-ant-...":"API Key"),Ar.disabled=ot},[()=>!n(j).trim()||n(Y)]),re("keydown",Zt,ot=>{ot.key==="Enter"&&Ht()}),$a(Zt,()=>n(j),ot=>u(j,ot)),re("click",Ar,Ht),v(dt,$t)};z(Aa,dt=>{n(pt)&&!pe().available&&dt(_d)})}var Yo=m(Aa,2);{var wd=dt=>{var $t=xh(),Bt=d($t),vr=d(Bt);gs(vr,{size:13,class:"text-dl-success"});var Cr=m(Bt,2),Zt=d(Cr),Ar=m(Zt,2);{var In=Yt=>{var Tr=gh(),Nt=d(Tr);{var ot=pr=>{Yr(pr,{size:10,class:"animate-spin"})},Dr=pr=>{var mn=hs("변경");v(pr,mn)};z(Nt,pr=>{n(Y)?pr(ot):pr(Dr,-1)})}O(()=>Tr.disabled=n(Y)),re("click",Tr,Ht),v(Yt,Tr)},Mr=U(()=>n(j).trim());z(Ar,Yt=>{n(Mr)&&Yt(In)})}re("keydown",Zt,Yt=>{Yt.key==="Enter"&&Ht()}),$a(Zt,()=>n(j),Yt=>u(j,Yt)),v(dt,$t)};z(Yo,dt=>{n(pt)&&pe().available&&dt(wd)})}var Xo=m(Yo,2);{var yd=dt=>{var $t=bh(),Bt=m(d($t),2),vr=d(Bt);xs(vr,{size:14});var Cr=m(vr,2);Ni(Cr,{size:10,class:"ml-auto"}),v(dt,$t)},kd=dt=>{var $t=_h(),Bt=d($t),vr=d(Bt);cs(vr,{size:14}),v(dt,$t)};z(Xo,dt=>{be()==="ollama"&&!n(i).installed?dt(yd):be()==="ollama"&&n(i).installed&&!n(i).running&&dt(kd,1)})}var Jo=m(Xo,2);{var Cd=dt=>{var $t=kh(),Bt=d($t);{var vr=Cr=>{var Zt=yh(),Ar=Q(Zt),In=d(Ar),Mr=m(Ar,2),Yt=d(Mr);{var Tr=Hn=>{var ts=wh();v(Hn,ts)};z(Yt,Hn=>{n(qt).installed||Hn(Tr)})}var Nt=m(Yt,2),ot=d(Nt),Dr=d(ot),pr=m(Mr,2),mn=d(pr);cs(mn,{size:12,class:"text-amber-400 flex-shrink-0"}),O(()=>{N(In,n(qt).installed?"Codex CLI가 설치되었지만 인증이 필요합니다":"Codex CLI 설치가 필요합니다"),N(Dr,n(qt).installed?"1.":"2.")}),v(Cr,Zt)};z(Bt,Cr=>{be()==="codex"&&Cr(vr)})}v(dt,$t)};z(Jo,dt=>{n(Vt)&&!pe().available&&dt(Cd)})}var Qo=m(Jo,2);{var Sd=dt=>{var $t=Mh(),Bt=m(d($t),2),vr=d(Bt);{var Cr=Mr=>{var Yt=Ch(),Tr=Q(Yt);Yr(Tr,{size:14,class:"animate-spin"}),v(Mr,Yt)},Zt=Mr=>{var Yt=Sh(),Tr=Q(Yt);lv(Tr,{size:14}),v(Mr,Yt)};z(vr,Mr=>{n(ee)?Mr(Cr):Mr(Zt,-1)})}var Ar=m(Bt,2),In=d(Ar);cs(In,{size:12,class:"text-amber-400 flex-shrink-0"}),O(()=>Bt.disabled=n(ee)),re("click",Bt,Ot),v(dt,$t)};z(Qo,dt=>{pe().auth==="oauth"&&!pe().available&&dt(Sd)})}var Zo=m(Qo,2);{var Md=dt=>{var $t=Eh(),Bt=d($t),vr=d(Bt),Cr=d(vr);gs(Cr,{size:13,class:"text-dl-success"});var Zt=m(vr,2),Ar=d(Zt);dv(Ar,{size:11}),re("click",Zt,ht),v(dt,$t)};z(Zo,dt=>{pe().auth==="oauth"&&pe().available&&dt(Md)})}var Ed=m(Zo,2);{var zd=dt=>{var $t=Rh(),Bt=d($t),vr=m(d(Bt),2);{var Cr=Nt=>{Yr(Nt,{size:12,class:"animate-spin text-dl-text-dim"})};z(vr,Nt=>{n(zr)&&Nt(Cr)})}var Zt=m(Bt,2);{var Ar=Nt=>{var ot=zh(),Dr=d(ot);Yr(Dr,{size:14,class:"animate-spin"}),v(Nt,ot)},In=Nt=>{var ot=Th();Ie(ot,21,()=>n(Pt),Te,(Dr,pr)=>{var mn=Ah(),Hn=d(mn),ts=m(Hn);{var Ys=Ur=>{ev(Ur,{size:10,class:"inline ml-1"})};z(ts,Ur=>{n(pr)===n(c)&&n(ct)&&Ur(Ys)})}O(Ur=>{$e(mn,1,Ur),N(Hn,`${n(pr)??""} `)},[()=>Ct(St("px-3 py-1.5 rounded-lg text-[11px] border transition-all",n(pr)===n(c)&&n(ct)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),re("click",mn,()=>{be()!==n(l)&&Ze(be()),De(n(pr))}),v(Dr,mn)}),v(Nt,ot)},Mr=Nt=>{var ot=Ih();v(Nt,ot)};z(Zt,Nt=>{n(zr)&&n(Pt).length===0?Nt(Ar):n(Pt).length>0?Nt(In,1):Nt(Mr,-1)})}var Yt=m(Zt,2);{var Tr=Nt=>{var ot=Lh(),Dr=d(ot),pr=m(d(Dr),2),mn=m(d(pr));Ni(mn,{size:9});var Hn=m(Dr,2);{var ts=Ur=>{var rs=Ph(),ns=d(rs),Ta=d(ns),as=d(Ta);Yr(as,{size:12,class:"animate-spin text-dl-primary-light"});var Xs=m(Ta,2),zs=m(ns,2),Pn=d(zs),nn=m(zs,2),Js=d(nn);O(()=>{zo(Pn,`width: ${n(g)??""}%`),N(Js,n($))}),re("click",Xs,Xt),v(Ur,rs)},Ys=Ur=>{var rs=Oh(),ns=Q(rs),Ta=d(ns),as=m(Ta,2),Xs=d(as);xs(Xs,{size:12});var zs=m(ns,2);Ie(zs,21,()=>lt,Te,(Pn,nn)=>{const Js=U(()=>n(Pt).some(Ia=>Ia===n(nn).name||Ia===n(nn).name.split(":")[0]));var ei=xe(),Ad=Q(ei);{var Td=Ia=>{var Qs=Nh(),ti=d(Qs),ri=d(ti),ni=d(ri),Id=d(ni),ai=m(ni,2),Pd=d(ai),$d=m(ai,2);{var Nd=Zs=>{var oi=$h(),Vd=d(oi);O(()=>N(Vd,n(nn).tag)),v(Zs,oi)};z($d,Zs=>{n(nn).tag&&Zs(Nd)})}var Od=m(ri,2),Ld=d(Od),Rd=m(ti,2),si=d(Rd),Dd=d(si),jd=m(si,2);xs(jd,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),O(()=>{N(Id,n(nn).name),N(Pd,n(nn).size),N(Ld,n(nn).desc),N(Dd,`${n(nn).gb??""} GB`)}),re("click",Qs,()=>{u(G,n(nn).name,!0),gt()}),v(Ia,Qs)};z(Ad,Ia=>{n(Js)||Ia(Td)})}v(Pn,ei)}),O(Pn=>as.disabled=Pn,[()=>!n(G).trim()]),re("keydown",Ta,Pn=>{Pn.key==="Enter"&&gt()}),$a(Ta,()=>n(G),Pn=>u(G,Pn)),re("click",as,gt),v(Ur,rs)};z(Hn,Ur=>{n(de)?Ur(ts):Ur(Ys,-1)})}v(Nt,ot)};z(Yt,Nt=>{be()==="ollama"&&Nt(Tr)})}v(dt,$t)};z(Ed,dt=>{(pe().available||n(pt)||n(Vt)||pe().auth==="oauth")&&dt(zd)})}v(Qt,Hr)};z(xd,Qt=>{(n(xt)||n(ct))&&Qt(bd)})}O((Qt,Hr)=>{$e(bt,1,Qt),$e(Jt,1,Hr),N(Ks,pe().label||be()),N(fd,pe().desc||"")},[()=>Ct(St("rounded-xl border transition-all",n(ct)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>Ct(St("w-2.5 h-2.5 rounded-full flex-shrink-0",pe().available?"bg-dl-success":n(pt)?"bg-amber-400":"bg-dl-text-dim"))]),re("click",ar,()=>{pe().available||n(pt)?be()===n(l)?mt(be()):Ze(be()):mt(be())}),v(S,bt)});var fr=m(st,2),Tn=d(fr),qn=d(Tn);{var Bn=S=>{var D=hs();O(()=>{var ie;return N(D,`현재: ${(((ie=n(o)[n(l)])==null?void 0:ie.label)||n(l))??""} / ${n(c)??""}`)}),v(S,D)},Gn=S=>{var D=hs();O(()=>{var ie;return N(D,`현재: ${(((ie=n(o)[n(l)])==null?void 0:ie.label)||n(l))??""}`)}),v(S,D)};z(qn,S=>{n(l)&&n(c)?S(Bn):n(l)&&S(Gn,1)})}var ke=m(Tn,2);Ka(le,S=>u(L,S),()=>n(L)),re("click",R,S=>{S.target===S.currentTarget&&u(k,!1)}),re("click",Ee,()=>u(k,!1)),re("click",ke,()=>u(k,!1)),v(_,R)};z(wt,_=>{n(k)&&_(cr)})}var Ae=m(wt,2);{var Ke=_=>{var R=Fh(),le=d(R),_e=m(d(le),4),Me=d(_e),Ee=m(Me,2);Ka(le,ve=>u(ce,ve),()=>n(ce)),re("click",R,ve=>{ve.target===ve.currentTarget&&u(se,null)}),re("click",Me,()=>u(se,null)),re("click",Ee,et),v(_,R)};z(Ae,_=>{n(se)&&_(Ke)})}var at=m(Ae,2);{var It=_=>{const R=U(()=>te.recentCompanies||[]);var le=Kh(),_e=d(le),Me=d(_e),Ee=d(Me);bs(Ee,{size:18,class:"text-dl-text-dim flex-shrink-0"});var ve=m(Ee,2);xl(ve,!0);var st=m(Me,2),Br=d(st);{var fr=S=>{var D=Bh(),ie=m(Q(D),2);Ie(ie,17,()=>n(ue),Te,(be,pe,ct)=>{var xt=qh(),pt=d(xt),Vt=d(pt),Pt=m(pt,2),zr=d(Pt),bt=d(zr),ar=m(zr,2),Jt=d(ar),kt=m(Pt,2),Ft=m(d(kt),2);Ln(Ft,{size:14,class:"text-dl-text-dim"}),O((Gr,Ks)=>{$e(xt,1,Gr),N(Vt,Ks),N(bt,n(pe).corpName),N(Jt,`${n(pe).stockCode??""} · ${(n(pe).market||"")??""}${n(pe).sector?` · ${n(pe).sector}`:""}`)},[()=>Ct(St("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",ct===n(B)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(pe).corpName||"?").charAt(0)]),re("click",xt,()=>{u(Pe,!1),u(ye,""),u(ue,[],!0),u(B,-1),I(n(pe))}),Na("mouseenter",xt,()=>{u(B,ct,!0)}),v(be,xt)}),v(S,D)},Tn=S=>{var D=Hh(),ie=m(Q(D),2);Ie(ie,17,()=>n(R),Te,(be,pe,ct)=>{var xt=Gh(),pt=d(xt),Vt=d(pt),Pt=m(pt,2),zr=d(Pt),bt=d(zr),ar=m(zr,2),Jt=d(ar);O((kt,Ft)=>{$e(xt,1,kt),N(Vt,Ft),N(bt,n(pe).corpName),N(Jt,`${n(pe).stockCode??""} · ${(n(pe).market||"")??""}`)},[()=>Ct(St("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",ct===n(B)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(pe).corpName||"?").charAt(0)]),re("click",xt,()=>{u(Pe,!1),u(ye,""),u(B,-1),I(n(pe))}),Na("mouseenter",xt,()=>{u(B,ct,!0)}),v(be,xt)}),v(S,D)},qn=U(()=>n(ye).trim().length===0&&n(R).length>0),Bn=S=>{var D=Uh();v(S,D)},Gn=U(()=>n(ye).trim().length>0),ke=S=>{var D=Wh(),ie=d(D);bs(ie,{size:24,class:"mb-2 opacity-40"}),v(S,D)};z(Br,S=>{n(ue).length>0?S(fr):n(qn)?S(Tn,1):n(Gn)?S(Bn,2):S(ke,-1)})}re("click",le,S=>{S.target===S.currentTarget&&u(Pe,!1)}),re("input",ve,()=>{T&&clearTimeout(T),n(ye).trim().length>=1?T=setTimeout(async()=>{var S;try{const D=await Bl(n(ye).trim());u(ue,((S=D.results)==null?void 0:S.slice(0,8))||[],!0)}catch{u(ue,[],!0)}},250):u(ue,[],!0)}),re("keydown",ve,S=>{const D=n(ue).length>0?n(ue):n(R);if(S.key==="ArrowDown")S.preventDefault(),u(B,Math.min(n(B)+1,D.length-1),!0);else if(S.key==="ArrowUp")S.preventDefault(),u(B,Math.max(n(B)-1,-1),!0);else if(S.key==="Enter"&&n(B)>=0&&D[n(B)]){S.preventDefault();const ie=D[n(B)];u(Pe,!1),u(ye,""),u(ue,[],!0),u(B,-1),I(ie)}else S.key==="Escape"&&u(Pe,!1)}),$a(ve,()=>n(ye),S=>u(ye,S)),v(_,le)};z(at,_=>{n(Pe)&&_(It)})}var yt=m(at,2);{var ur=_=>{var R=Yh(),le=d(R),_e=d(le),Me=d(_e),Ee=m(_e,2),ve=d(Ee);js(ve,{size:14}),O(st=>{$e(le,1,st),N(Me,n(me))},[()=>Ct(St("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",n(fe)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":n(fe)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),re("click",Ee,()=>{u(he,!1)}),v(_,R)};z(yt,_=>{n(he)&&_(ur)})}O(_=>{$e(Oe,1,Ct(n(V)?n(p)?"sidebar-mobile":"hidden":"")),$e(Fn,1,_)},[()=>Ct(St("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",n(w)?"text-dl-text-dim":n(je)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),re("click",vn,At),re("click",jt,tt),re("click",Fn,()=>W()),v(e,Je),tn()}Vn(["click","keydown","input"]);pu(Jh,{target:document.getElementById("app")});
