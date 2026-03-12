var Hd=Object.defineProperty;var Po=e=>{throw TypeError(e)};var Ud=(e,t,r)=>t in e?Hd(e,t,{enumerable:!0,configurable:!0,writable:!0,value:r}):e[t]=r;var fn=(e,t,r)=>Ud(e,typeof t!="symbol"?t+"":t,r),Il=(e,t,r)=>t.has(e)||Po("Cannot "+r);var T=(e,t,r)=>(Il(e,t,"read from private field"),r?r.call(e):t.get(e)),tt=(e,t,r)=>t.has(e)?Po("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,r),Ue=(e,t,r,a)=>(Il(e,t,"write to private field"),a?a.call(e,r):t.set(e,r),r),br=(e,t,r)=>(Il(e,t,"access private method"),r);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const i of document.querySelectorAll('link[rel="modulepreload"]'))a(i);new MutationObserver(i=>{for(const l of i)if(l.type==="childList")for(const s of l.addedNodes)s.tagName==="LINK"&&s.rel==="modulepreload"&&a(s)}).observe(document,{childList:!0,subtree:!0});function r(i){const l={};return i.integrity&&(l.integrity=i.integrity),i.referrerPolicy&&(l.referrerPolicy=i.referrerPolicy),i.crossOrigin==="use-credentials"?l.credentials="include":i.crossOrigin==="anonymous"?l.credentials="omit":l.credentials="same-origin",l}function a(i){if(i.ep)return;i.ep=!0;const l=r(i);fetch(i.href,l)}})();const $l=!1;var fo=Array.isArray,Wd=Array.prototype.indexOf,ii=Array.prototype.includes,ol=Array.from,qd=Object.defineProperty,oa=Object.getOwnPropertyDescriptor,hs=Object.getOwnPropertyDescriptors,Kd=Object.prototype,Yd=Array.prototype,po=Object.getPrototypeOf,Ro=Object.isExtensible;function bi(e){return typeof e=="function"}const Jd=()=>{};function Xd(e){return e()}function Vl(e){for(var t=0;t<e.length;t++)e[t]()}function _s(){var e,t,r=new Promise((a,i)=>{e=a,t=i});return{promise:r,resolve:e,reject:t}}function el(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const r=[];for(const a of e)if(r.push(a),r.length===t)break;return r}const Or=2,ci=4,Pa=8,sl=1<<24,pa=16,_n=32,Ba=64,Gl=128,on=512,Ar=1024,Tr=2048,hn=4096,Fr=8192,Rn=16384,ui=32768,Jn=65536,jo=1<<17,Qd=1<<18,vi=1<<19,ys=1<<20,Ln=1<<25,Ra=65536,Hl=1<<21,xo=1<<22,sa=1<<23,jn=Symbol("$state"),ws=Symbol("legacy props"),Zd=Symbol(""),wa=new class extends Error{constructor(){super(...arguments);fn(this,"name","StaleReactionError");fn(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var ms;const ks=!!((ms=globalThis.document)!=null&&ms.contentType)&&globalThis.document.contentType.includes("xml");function ec(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function tc(e,t,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function rc(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function nc(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function ac(e){throw new Error("https://svelte.dev/e/effect_orphan")}function ic(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function lc(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function oc(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function sc(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function dc(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function cc(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const uc=1,vc=2,Cs=4,fc=8,pc=16,xc=1,mc=2,Ss=4,bc=8,gc=16,hc=1,_c=2,Cr=Symbol(),Es="http://www.w3.org/1999/xhtml",Ms="http://www.w3.org/2000/svg",yc="http://www.w3.org/1998/Math/MathML",wc="@attach";function kc(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function Cc(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function zs(e){return e===this.v}function Sc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function As(e){return!Sc(e,this.v)}let Ai=!1,Ec=!1;function Mc(){Ai=!0}let Sr=null;function li(e){Sr=e}function yn(e,t=!1,r){Sr={p:Sr,i:!1,c:null,e:null,s:e,x:null,l:Ai&&!t?{s:null,u:null,$:[]}:null}}function wn(e){var t=Sr,r=t.e;if(r!==null){t.e=null;for(var a of r)Ks(a)}return t.i=!0,Sr=t.p,{}}function Ti(){return!Ai||Sr!==null&&Sr.l===null}let ka=[];function Ts(){var e=ka;ka=[],Vl(e)}function Dn(e){if(ka.length===0&&!ki){var t=ka;queueMicrotask(()=>{t===ka&&Ts()})}ka.push(e)}function zc(){for(;ka.length>0;)Ts()}function Ns(e){var t=Ze;if(t===null)return Qe.f|=sa,e;if((t.f&ui)===0&&(t.f&ci)===0)throw e;la(e,t)}function la(e,t){for(;t!==null;){if((t.f&Gl)!==0){if((t.f&ui)===0)throw e;try{t.b.error(e);return}catch(r){e=r}}t=t.parent}throw e}const Ac=-7169;function sr(e,t){e.f=e.f&Ac|t}function mo(e){(e.f&on)!==0||e.deps===null?sr(e,Ar):sr(e,hn)}function Os(e){if(e!==null)for(const t of e)(t.f&Or)===0||(t.f&Ra)===0||(t.f^=Ra,Os(t.deps))}function Is(e,t,r){(e.f&Tr)!==0?t.add(e):(e.f&hn)!==0&&r.add(e),Os(e.deps),sr(e,Ar)}const Ui=new Set;let We=null,Ul=null,zr=null,Gr=[],dl=null,ki=!1,oi=null,Tc=1;var na,Xa,Ea,Qa,Za,ei,aa,Tn,ti,Wr,Wl,ql,Kl,Yl;const zo=class zo{constructor(){tt(this,Wr);fn(this,"id",Tc++);fn(this,"current",new Map);fn(this,"previous",new Map);tt(this,na,new Set);tt(this,Xa,new Set);tt(this,Ea,0);tt(this,Qa,0);tt(this,Za,null);tt(this,ei,new Set);tt(this,aa,new Set);tt(this,Tn,new Map);fn(this,"is_fork",!1);tt(this,ti,!1)}skip_effect(t){T(this,Tn).has(t)||T(this,Tn).set(t,{d:[],m:[]})}unskip_effect(t){var r=T(this,Tn).get(t);if(r){T(this,Tn).delete(t);for(var a of r.d)sr(a,Tr),Pn(a);for(a of r.m)sr(a,hn),Pn(a)}}process(t){var i;Gr=[],this.apply();var r=oi=[],a=[];for(const l of t)br(this,Wr,ql).call(this,l,r,a);if(oi=null,br(this,Wr,Wl).call(this)){br(this,Wr,Kl).call(this,a),br(this,Wr,Kl).call(this,r);for(const[l,s]of T(this,Tn))js(l,s)}else{Ul=this,We=null;for(const l of T(this,na))l(this);T(this,na).clear(),T(this,Ea)===0&&br(this,Wr,Yl).call(this),Do(a),Do(r),T(this,ei).clear(),T(this,aa).clear(),Ul=null,(i=T(this,Za))==null||i.resolve()}zr=null}capture(t,r){r!==Cr&&!this.previous.has(t)&&this.previous.set(t,r),(t.f&sa)===0&&(this.current.set(t,t.v),zr==null||zr.set(t,t.v))}activate(){We=this,this.apply()}deactivate(){We===this&&(We=null,zr=null)}flush(){var t;if(Gr.length>0)We=this,Ls();else if(T(this,Ea)===0&&!this.is_fork){for(const r of T(this,na))r(this);T(this,na).clear(),br(this,Wr,Yl).call(this),(t=T(this,Za))==null||t.resolve()}this.deactivate()}discard(){for(const t of T(this,Xa))t(this);T(this,Xa).clear()}increment(t){Ue(this,Ea,T(this,Ea)+1),t&&Ue(this,Qa,T(this,Qa)+1)}decrement(t){Ue(this,Ea,T(this,Ea)-1),t&&Ue(this,Qa,T(this,Qa)-1),!T(this,ti)&&(Ue(this,ti,!0),Dn(()=>{Ue(this,ti,!1),br(this,Wr,Wl).call(this)?Gr.length>0&&this.flush():this.revive()}))}revive(){for(const t of T(this,ei))T(this,aa).delete(t),sr(t,Tr),Pn(t);for(const t of T(this,aa))sr(t,hn),Pn(t);this.flush()}oncommit(t){T(this,na).add(t)}ondiscard(t){T(this,Xa).add(t)}settled(){return(T(this,Za)??Ue(this,Za,_s())).promise}static ensure(){if(We===null){const t=We=new zo;Ui.add(We),ki||Dn(()=>{We===t&&t.flush()})}return We}apply(){}};na=new WeakMap,Xa=new WeakMap,Ea=new WeakMap,Qa=new WeakMap,Za=new WeakMap,ei=new WeakMap,aa=new WeakMap,Tn=new WeakMap,ti=new WeakMap,Wr=new WeakSet,Wl=function(){return this.is_fork||T(this,Qa)>0},ql=function(t,r,a){t.f^=Ar;for(var i=t.first;i!==null;){var l=i.f,s=(l&(_n|Ba))!==0,c=s&&(l&Ar)!==0,v=(l&Fr)!==0,m=c||T(this,Tn).has(i);if(!m&&i.fn!==null){s?v||(i.f^=Ar):(l&ci)!==0?r.push(i):(l&(Pa|sl))!==0&&v?a.push(i):Ii(i)&&(di(i),(l&pa)!==0&&(T(this,aa).add(i),v&&sr(i,Tr)));var g=i.first;if(g!==null){i=g;continue}}for(;i!==null;){var y=i.next;if(y!==null){i=y;break}i=i.parent}}},Kl=function(t){for(var r=0;r<t.length;r+=1)Is(t[r],T(this,ei),T(this,aa))},Yl=function(){var l;if(Ui.size>1){this.previous.clear();var t=We,r=zr,a=!0;for(const s of Ui){if(s===this){a=!1;continue}const c=[];for(const[m,g]of this.current){if(s.current.has(m))if(a&&g!==s.current.get(m))s.current.set(m,g);else continue;c.push(m)}if(c.length===0)continue;const v=[...s.current.keys()].filter(m=>!this.current.has(m));if(v.length>0){var i=Gr;Gr=[];const m=new Set,g=new Map;for(const y of c)Ps(y,v,m,g);if(Gr.length>0){We=s,s.apply();for(const y of Gr)br(l=s,Wr,ql).call(l,y,[],[]);s.deactivate()}Gr=i}}We=t,zr=r}T(this,Tn).clear(),Ui.delete(this)};let da=zo;function Nc(e){var t=ki;ki=!0;try{for(var r;;){if(zc(),Gr.length===0&&(We==null||We.flush(),Gr.length===0))return dl=null,r;Ls()}}finally{ki=t}}function Ls(){var e=null;try{for(var t=0;Gr.length>0;){var r=da.ensure();if(t++>1e3){var a,i;Oc()}r.process(Gr),ca.clear()}}finally{Gr=[],dl=null,oi=null}}function Oc(){try{ic()}catch(e){la(e,dl)}}let pn=null;function Do(e){var t=e.length;if(t!==0){for(var r=0;r<t;){var a=e[r++];if((a.f&(Rn|Fr))===0&&Ii(a)&&(pn=new Set,di(a),a.deps===null&&a.first===null&&a.nodes===null&&a.teardown===null&&a.ac===null&&Qs(a),(pn==null?void 0:pn.size)>0)){ca.clear();for(const i of pn){if((i.f&(Rn|Fr))!==0)continue;const l=[i];let s=i.parent;for(;s!==null;)pn.has(s)&&(pn.delete(s),l.push(s)),s=s.parent;for(let c=l.length-1;c>=0;c--){const v=l[c];(v.f&(Rn|Fr))===0&&di(v)}}pn.clear()}}pn=null}}function Ps(e,t,r,a){if(!r.has(e)&&(r.add(e),e.reactions!==null))for(const i of e.reactions){const l=i.f;(l&Or)!==0?Ps(i,t,r,a):(l&(xo|pa))!==0&&(l&Tr)===0&&Rs(i,t,a)&&(sr(i,Tr),Pn(i))}}function Rs(e,t,r){const a=r.get(e);if(a!==void 0)return a;if(e.deps!==null)for(const i of e.deps){if(ii.call(t,i))return!0;if((i.f&Or)!==0&&Rs(i,t,r))return r.set(i,!0),!0}return r.set(e,!1),!1}function Pn(e){var t=dl=e,r=t.b;if(r!=null&&r.is_pending&&(e.f&(ci|Pa|sl))!==0&&(e.f&ui)===0){r.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var a=t.f;if(oi!==null&&t===Ze&&(e.f&Pa)===0)return;if((a&(Ba|_n))!==0){if((a&Ar)===0)return;t.f^=Ar}}Gr.push(t)}function js(e,t){if(!((e.f&_n)!==0&&(e.f&Ar)!==0)){(e.f&Tr)!==0?t.d.push(e):(e.f&hn)!==0&&t.m.push(e),sr(e,Ar);for(var r=e.first;r!==null;)js(r,t),r=r.next}}function Ic(e){let t=0,r=va(0),a;return()=>{_o()&&(n(r),wo(()=>(t===0&&(a=ja(()=>e(()=>Si(r)))),t+=1,()=>{Dn(()=>{t-=1,t===0&&(a==null||a(),a=void 0,Si(r))})})))}}var Lc=Jn|vi;function Pc(e,t,r,a){new Rc(e,t,r,a)}var nn,vo,Nn,Ma,Vr,On,Xr,xn,qn,za,ia,ri,ni,ai,Kn,il,_r,jc,Dc,Fc,Jl,Ji,Xi,Xl;class Rc{constructor(t,r,a,i){tt(this,_r);fn(this,"parent");fn(this,"is_pending",!1);fn(this,"transform_error");tt(this,nn);tt(this,vo,null);tt(this,Nn);tt(this,Ma);tt(this,Vr);tt(this,On,null);tt(this,Xr,null);tt(this,xn,null);tt(this,qn,null);tt(this,za,0);tt(this,ia,0);tt(this,ri,!1);tt(this,ni,new Set);tt(this,ai,new Set);tt(this,Kn,null);tt(this,il,Ic(()=>(Ue(this,Kn,va(T(this,za))),()=>{Ue(this,Kn,null)})));var l;Ue(this,nn,t),Ue(this,Nn,r),Ue(this,Ma,s=>{var c=Ze;c.b=this,c.f|=Gl,a(s)}),this.parent=Ze.b,this.transform_error=i??((l=this.parent)==null?void 0:l.transform_error)??(s=>s),Ue(this,Vr,fi(()=>{br(this,_r,Jl).call(this)},Lc))}defer_effect(t){Is(t,T(this,ni),T(this,ai))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!T(this,Nn).pending}update_pending_count(t){br(this,_r,Xl).call(this,t),Ue(this,za,T(this,za)+t),!(!T(this,Kn)||T(this,ri))&&(Ue(this,ri,!0),Dn(()=>{Ue(this,ri,!1),T(this,Kn)&&si(T(this,Kn),T(this,za))}))}get_effect_pending(){return T(this,il).call(this),n(T(this,Kn))}error(t){var r=T(this,Nn).onerror;let a=T(this,Nn).failed;if(!r&&!a)throw t;T(this,On)&&(Nr(T(this,On)),Ue(this,On,null)),T(this,Xr)&&(Nr(T(this,Xr)),Ue(this,Xr,null)),T(this,xn)&&(Nr(T(this,xn)),Ue(this,xn,null));var i=!1,l=!1;const s=()=>{if(i){Cc();return}i=!0,l&&cc(),T(this,xn)!==null&&Ta(T(this,xn),()=>{Ue(this,xn,null)}),br(this,_r,Xi).call(this,()=>{da.ensure(),br(this,_r,Jl).call(this)})},c=v=>{try{l=!0,r==null||r(v,s),l=!1}catch(m){la(m,T(this,Vr)&&T(this,Vr).parent)}a&&Ue(this,xn,br(this,_r,Xi).call(this,()=>{da.ensure();try{return Ur(()=>{var m=Ze;m.b=this,m.f|=Gl,a(T(this,nn),()=>v,()=>s)})}catch(m){return la(m,T(this,Vr).parent),null}}))};Dn(()=>{var v;try{v=this.transform_error(t)}catch(m){la(m,T(this,Vr)&&T(this,Vr).parent);return}v!==null&&typeof v=="object"&&typeof v.then=="function"?v.then(c,m=>la(m,T(this,Vr)&&T(this,Vr).parent)):c(v)})}}nn=new WeakMap,vo=new WeakMap,Nn=new WeakMap,Ma=new WeakMap,Vr=new WeakMap,On=new WeakMap,Xr=new WeakMap,xn=new WeakMap,qn=new WeakMap,za=new WeakMap,ia=new WeakMap,ri=new WeakMap,ni=new WeakMap,ai=new WeakMap,Kn=new WeakMap,il=new WeakMap,_r=new WeakSet,jc=function(){try{Ue(this,On,Ur(()=>T(this,Ma).call(this,T(this,nn))))}catch(t){this.error(t)}},Dc=function(t){const r=T(this,Nn).failed;r&&Ue(this,xn,Ur(()=>{r(T(this,nn),()=>t,()=>()=>{})}))},Fc=function(){const t=T(this,Nn).pending;t&&(this.is_pending=!0,Ue(this,Xr,Ur(()=>t(T(this,nn)))),Dn(()=>{var r=Ue(this,qn,document.createDocumentFragment()),a=Fn();r.append(a),Ue(this,On,br(this,_r,Xi).call(this,()=>(da.ensure(),Ur(()=>T(this,Ma).call(this,a))))),T(this,ia)===0&&(T(this,nn).before(r),Ue(this,qn,null),Ta(T(this,Xr),()=>{Ue(this,Xr,null)}),br(this,_r,Ji).call(this))}))},Jl=function(){try{if(this.is_pending=this.has_pending_snippet(),Ue(this,ia,0),Ue(this,za,0),Ue(this,On,Ur(()=>{T(this,Ma).call(this,T(this,nn))})),T(this,ia)>0){var t=Ue(this,qn,document.createDocumentFragment());So(T(this,On),t);const r=T(this,Nn).pending;Ue(this,Xr,Ur(()=>r(T(this,nn))))}else br(this,_r,Ji).call(this)}catch(r){this.error(r)}},Ji=function(){this.is_pending=!1;for(const t of T(this,ni))sr(t,Tr),Pn(t);for(const t of T(this,ai))sr(t,hn),Pn(t);T(this,ni).clear(),T(this,ai).clear()},Xi=function(t){var r=Ze,a=Qe,i=Sr;cn(T(this,Vr)),dn(T(this,Vr)),li(T(this,Vr).ctx);try{return t()}catch(l){return Ns(l),null}finally{cn(r),dn(a),li(i)}},Xl=function(t){var r;if(!this.has_pending_snippet()){this.parent&&br(r=this.parent,_r,Xl).call(r,t);return}Ue(this,ia,T(this,ia)+t),T(this,ia)===0&&(br(this,_r,Ji).call(this),T(this,Xr)&&Ta(T(this,Xr),()=>{Ue(this,Xr,null)}),T(this,qn)&&(T(this,nn).before(T(this,qn)),Ue(this,qn,null)))};function Ds(e,t,r,a){const i=Ti()?Ni:bo;var l=e.filter(y=>!y.settled);if(r.length===0&&l.length===0){a(t.map(i));return}var s=Ze,c=Bc(),v=l.length===1?l[0].promise:l.length>1?Promise.all(l.map(y=>y.promise)):null;function m(y){c();try{a(y)}catch(C){(s.f&Rn)===0&&la(C,s)}Ql()}if(r.length===0){v.then(()=>m(t.map(i)));return}function g(){c(),Promise.all(r.map(y=>Vc(y))).then(y=>m([...t.map(i),...y])).catch(y=>la(y,s))}v?v.then(g):g()}function Bc(){var e=Ze,t=Qe,r=Sr,a=We;return function(l=!0){cn(e),dn(t),li(r),l&&(a==null||a.activate())}}function Ql(e=!0){cn(null),dn(null),li(null),e&&(We==null||We.deactivate())}function $c(){var e=Ze.b,t=We,r=e.is_rendered();return e.update_pending_count(1),t.increment(r),()=>{e.update_pending_count(-1),t.decrement(r)}}function Ni(e){var t=Or|Tr,r=Qe!==null&&(Qe.f&Or)!==0?Qe:null;return Ze!==null&&(Ze.f|=vi),{ctx:Sr,deps:null,effects:null,equals:zs,f:t,fn:e,reactions:null,rv:0,v:Cr,wv:0,parent:r??Ze,ac:null}}function Vc(e,t,r){Ze===null&&ec();var i=void 0,l=va(Cr),s=!Qe,c=new Map;return nu(()=>{var C;var v=_s();i=v.promise;try{Promise.resolve(e()).then(v.resolve,v.reject).finally(Ql)}catch(P){v.reject(P),Ql()}var m=We;if(s){var g=$c();(C=c.get(m))==null||C.reject(wa),c.delete(m),c.set(m,v)}const y=(P,E=void 0)=>{if(m.activate(),E)E!==wa&&(l.f|=sa,si(l,E));else{(l.f&sa)!==0&&(l.f^=sa),si(l,P);for(const[O,_]of c){if(c.delete(O),O===m)break;_.reject(wa)}}g&&g()};v.promise.then(y,P=>y(null,P||"unknown"))}),ul(()=>{for(const v of c.values())v.reject(wa)}),new Promise(v=>{function m(g){function y(){g===i?v(l):m(i)}g.then(y,y)}m(i)})}function ne(e){const t=Ni(e);return td(t),t}function bo(e){const t=Ni(e);return t.equals=As,t}function Gc(e){var t=e.effects;if(t!==null){e.effects=null;for(var r=0;r<t.length;r+=1)Nr(t[r])}}function Hc(e){for(var t=e.parent;t!==null;){if((t.f&Or)===0)return(t.f&Rn)===0?t:null;t=t.parent}return null}function go(e){var t,r=Ze;cn(Hc(e));try{e.f&=~Ra,Gc(e),t=id(e)}finally{cn(r)}return t}function Fs(e){var t=go(e);if(!e.equals(t)&&(e.wv=nd(),(!(We!=null&&We.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){sr(e,Ar);return}fa||(zr!==null?(_o()||We!=null&&We.is_fork)&&zr.set(e,t):mo(e))}function Uc(e){var t,r;if(e.effects!==null)for(const a of e.effects)(a.teardown||a.ac)&&((t=a.teardown)==null||t.call(a),(r=a.ac)==null||r.abort(wa),a.teardown=Jd,a.ac=null,Ei(a,0),ko(a))}function Bs(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&di(t)}let Zl=new Set;const ca=new Map;let $s=!1;function va(e,t){var r={f:0,v:e,reactions:null,equals:zs,rv:0,wv:0};return r}function F(e,t){const r=va(e);return td(r),r}function Wc(e,t=!1,r=!0){var i;const a=va(e);return t||(a.equals=As),Ai&&r&&Sr!==null&&Sr.l!==null&&((i=Sr.l).s??(i.s=[])).push(a),a}function u(e,t,r=!1){Qe!==null&&(!bn||(Qe.f&jo)!==0)&&Ti()&&(Qe.f&(Or|pa|xo|jo))!==0&&(sn===null||!ii.call(sn,e))&&dc();let a=r?ut(t):t;return si(e,a)}function si(e,t){if(!e.equals(t)){var r=e.v;fa?ca.set(e,t):ca.set(e,r),e.v=t;var a=da.ensure();if(a.capture(e,r),(e.f&Or)!==0){const i=e;(e.f&Tr)!==0&&go(i),mo(i)}e.wv=nd(),Vs(e,Tr),Ti()&&Ze!==null&&(Ze.f&Ar)!==0&&(Ze.f&(_n|Ba))===0&&(rn===null?iu([e]):rn.push(e)),!a.is_fork&&Zl.size>0&&!$s&&qc()}return t}function qc(){$s=!1;for(const e of Zl)(e.f&Ar)!==0&&sr(e,hn),Ii(e)&&di(e);Zl.clear()}function Ci(e,t=1){var r=n(e),a=t===1?r++:r--;return u(e,r),a}function Si(e){u(e,e.v+1)}function Vs(e,t){var r=e.reactions;if(r!==null)for(var a=Ti(),i=r.length,l=0;l<i;l++){var s=r[l],c=s.f;if(!(!a&&s===Ze)){var v=(c&Tr)===0;if(v&&sr(s,t),(c&Or)!==0){var m=s;zr==null||zr.delete(m),(c&Ra)===0&&(c&on&&(s.f|=Ra),Vs(m,hn))}else v&&((c&pa)!==0&&pn!==null&&pn.add(s),Pn(s))}}}function ut(e){if(typeof e!="object"||e===null||jn in e)return e;const t=po(e);if(t!==Kd&&t!==Yd)return e;var r=new Map,a=fo(e),i=F(0),l=Na,s=c=>{if(Na===l)return c();var v=Qe,m=Na;dn(null),Vo(l);var g=c();return dn(v),Vo(m),g};return a&&r.set("length",F(e.length)),new Proxy(e,{defineProperty(c,v,m){(!("value"in m)||m.configurable===!1||m.enumerable===!1||m.writable===!1)&&oc();var g=r.get(v);return g===void 0?s(()=>{var y=F(m.value);return r.set(v,y),y}):u(g,m.value,!0),!0},deleteProperty(c,v){var m=r.get(v);if(m===void 0){if(v in c){const g=s(()=>F(Cr));r.set(v,g),Si(i)}}else u(m,Cr),Si(i);return!0},get(c,v,m){var P;if(v===jn)return e;var g=r.get(v),y=v in c;if(g===void 0&&(!y||(P=oa(c,v))!=null&&P.writable)&&(g=s(()=>{var E=ut(y?c[v]:Cr),O=F(E);return O}),r.set(v,g)),g!==void 0){var C=n(g);return C===Cr?void 0:C}return Reflect.get(c,v,m)},getOwnPropertyDescriptor(c,v){var m=Reflect.getOwnPropertyDescriptor(c,v);if(m&&"value"in m){var g=r.get(v);g&&(m.value=n(g))}else if(m===void 0){var y=r.get(v),C=y==null?void 0:y.v;if(y!==void 0&&C!==Cr)return{enumerable:!0,configurable:!0,value:C,writable:!0}}return m},has(c,v){var C;if(v===jn)return!0;var m=r.get(v),g=m!==void 0&&m.v!==Cr||Reflect.has(c,v);if(m!==void 0||Ze!==null&&(!g||(C=oa(c,v))!=null&&C.writable)){m===void 0&&(m=s(()=>{var P=g?ut(c[v]):Cr,E=F(P);return E}),r.set(v,m));var y=n(m);if(y===Cr)return!1}return g},set(c,v,m,g){var V;var y=r.get(v),C=v in c;if(a&&v==="length")for(var P=m;P<y.v;P+=1){var E=r.get(P+"");E!==void 0?u(E,Cr):P in c&&(E=s(()=>F(Cr)),r.set(P+"",E))}if(y===void 0)(!C||(V=oa(c,v))!=null&&V.writable)&&(y=s(()=>F(void 0)),u(y,ut(m)),r.set(v,y));else{C=y.v!==Cr;var O=s(()=>ut(m));u(y,O)}var _=Reflect.getOwnPropertyDescriptor(c,v);if(_!=null&&_.set&&_.set.call(g,m),!C){if(a&&typeof v=="string"){var M=r.get("length"),R=Number(v);Number.isInteger(R)&&R>=M.v&&u(M,R+1)}Si(i)}return!0},ownKeys(c){n(i);var v=Reflect.ownKeys(c).filter(y=>{var C=r.get(y);return C===void 0||C.v!==Cr});for(var[m,g]of r)g.v!==Cr&&!(m in c)&&v.push(m);return v},setPrototypeOf(){sc()}})}function Fo(e){try{if(e!==null&&typeof e=="object"&&jn in e)return e[jn]}catch{}return e}function Kc(e,t){return Object.is(Fo(e),Fo(t))}var eo,Gs,Hs,Us;function Yc(){if(eo===void 0){eo=window,Gs=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,r=Text.prototype;Hs=oa(t,"firstChild").get,Us=oa(t,"nextSibling").get,Ro(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Ro(r)&&(r.__t=void 0)}}function Fn(e=""){return document.createTextNode(e)}function Yn(e){return Hs.call(e)}function Oi(e){return Us.call(e)}function d(e,t){return Yn(e)}function Z(e,t=!1){{var r=Yn(e);return r instanceof Comment&&r.data===""?Oi(r):r}}function f(e,t=1,r=!1){let a=e;for(;t--;)a=Oi(a);return a}function Jc(e){e.textContent=""}function Ws(){return!1}function ho(e,t,r){return document.createElementNS(t??Es,e,void 0)}function Xc(e,t){if(t){const r=document.body;e.autofocus=!0,Dn(()=>{document.activeElement===r&&e.focus()})}}let Bo=!1;function Qc(){Bo||(Bo=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const r of e.target.elements)(t=r.__on_r)==null||t.call(r)})},{capture:!0}))}function cl(e){var t=Qe,r=Ze;dn(null),cn(null);try{return e()}finally{dn(t),cn(r)}}function Zc(e,t,r,a=r){e.addEventListener(t,()=>cl(r));const i=e.__on_r;i?e.__on_r=()=>{i(),a(!0)}:e.__on_r=()=>a(!0),Qc()}function qs(e){Ze===null&&(Qe===null&&ac(),nc()),fa&&rc()}function eu(e,t){var r=t.last;r===null?t.last=t.first=e:(r.next=e,e.prev=r,t.last=e)}function kn(e,t){var r=Ze;r!==null&&(r.f&Fr)!==0&&(e|=Fr);var a={ctx:Sr,deps:null,nodes:null,f:e|Tr|on,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},i=a;if((e&ci)!==0)oi!==null?oi.push(a):Pn(a);else if(t!==null){try{di(a)}catch(s){throw Nr(a),s}i.deps===null&&i.teardown===null&&i.nodes===null&&i.first===i.last&&(i.f&vi)===0&&(i=i.first,(e&pa)!==0&&(e&Jn)!==0&&i!==null&&(i.f|=Jn))}if(i!==null&&(i.parent=r,r!==null&&eu(i,r),Qe!==null&&(Qe.f&Or)!==0&&(e&Ba)===0)){var l=Qe;(l.effects??(l.effects=[])).push(i)}return a}function _o(){return Qe!==null&&!bn}function ul(e){const t=kn(Pa,null);return sr(t,Ar),t.teardown=e,t}function ln(e){qs();var t=Ze.f,r=!Qe&&(t&_n)!==0&&(t&ui)===0;if(r){var a=Sr;(a.e??(a.e=[])).push(e)}else return Ks(e)}function Ks(e){return kn(ci|ys,e)}function tu(e){return qs(),kn(Pa|ys,e)}function ru(e){da.ensure();const t=kn(Ba|vi,e);return(r={})=>new Promise(a=>{r.outro?Ta(t,()=>{Nr(t),a(void 0)}):(Nr(t),a(void 0))})}function yo(e){return kn(ci,e)}function nu(e){return kn(xo|vi,e)}function wo(e,t=0){return kn(Pa|t,e)}function L(e,t=[],r=[],a=[]){Ds(a,t,r,i=>{kn(Pa,()=>e(...i.map(n)))})}function fi(e,t=0){var r=kn(pa|t,e);return r}function Ys(e,t=0){var r=kn(sl|t,e);return r}function Ur(e){return kn(_n|vi,e)}function Js(e){var t=e.teardown;if(t!==null){const r=fa,a=Qe;$o(!0),dn(null);try{t.call(null)}finally{$o(r),dn(a)}}}function ko(e,t=!1){var r=e.first;for(e.first=e.last=null;r!==null;){const i=r.ac;i!==null&&cl(()=>{i.abort(wa)});var a=r.next;(r.f&Ba)!==0?r.parent=null:Nr(r,t),r=a}}function au(e){for(var t=e.first;t!==null;){var r=t.next;(t.f&_n)===0&&Nr(t),t=r}}function Nr(e,t=!0){var r=!1;(t||(e.f&Qd)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(Xs(e.nodes.start,e.nodes.end),r=!0),ko(e,t&&!r),Ei(e,0),sr(e,Rn);var a=e.nodes&&e.nodes.t;if(a!==null)for(const l of a)l.stop();Js(e);var i=e.parent;i!==null&&i.first!==null&&Qs(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function Xs(e,t){for(;e!==null;){var r=e===t?null:Oi(e);e.remove(),e=r}}function Qs(e){var t=e.parent,r=e.prev,a=e.next;r!==null&&(r.next=a),a!==null&&(a.prev=r),t!==null&&(t.first===e&&(t.first=a),t.last===e&&(t.last=r))}function Ta(e,t,r=!0){var a=[];Zs(e,a,!0);var i=()=>{r&&Nr(e),t&&t()},l=a.length;if(l>0){var s=()=>--l||i();for(var c of a)c.out(s)}else i()}function Zs(e,t,r){if((e.f&Fr)===0){e.f^=Fr;var a=e.nodes&&e.nodes.t;if(a!==null)for(const c of a)(c.is_global||r)&&t.push(c);for(var i=e.first;i!==null;){var l=i.next,s=(i.f&Jn)!==0||(i.f&_n)!==0&&(e.f&pa)!==0;Zs(i,t,s?r:!1),i=l}}}function Co(e){ed(e,!0)}function ed(e,t){if((e.f&Fr)!==0){e.f^=Fr;for(var r=e.first;r!==null;){var a=r.next,i=(r.f&Jn)!==0||(r.f&_n)!==0;ed(r,i?t:!1),r=a}var l=e.nodes&&e.nodes.t;if(l!==null)for(const s of l)(s.is_global||t)&&s.in()}}function So(e,t){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end;r!==null;){var i=r===a?null:Oi(r);t.append(r),r=i}}let Qi=!1,fa=!1;function $o(e){fa=e}let Qe=null,bn=!1;function dn(e){Qe=e}let Ze=null;function cn(e){Ze=e}let sn=null;function td(e){Qe!==null&&(sn===null?sn=[e]:sn.push(e))}let Hr=null,Jr=0,rn=null;function iu(e){rn=e}let rd=1,Ca=0,Na=Ca;function Vo(e){Na=e}function nd(){return++rd}function Ii(e){var t=e.f;if((t&Tr)!==0)return!0;if(t&Or&&(e.f&=~Ra),(t&hn)!==0){for(var r=e.deps,a=r.length,i=0;i<a;i++){var l=r[i];if(Ii(l)&&Fs(l),l.wv>e.wv)return!0}(t&on)!==0&&zr===null&&sr(e,Ar)}return!1}function ad(e,t,r=!0){var a=e.reactions;if(a!==null&&!(sn!==null&&ii.call(sn,e)))for(var i=0;i<a.length;i++){var l=a[i];(l.f&Or)!==0?ad(l,t,!1):t===l&&(r?sr(l,Tr):(l.f&Ar)!==0&&sr(l,hn),Pn(l))}}function id(e){var O;var t=Hr,r=Jr,a=rn,i=Qe,l=sn,s=Sr,c=bn,v=Na,m=e.f;Hr=null,Jr=0,rn=null,Qe=(m&(_n|Ba))===0?e:null,sn=null,li(e.ctx),bn=!1,Na=++Ca,e.ac!==null&&(cl(()=>{e.ac.abort(wa)}),e.ac=null);try{e.f|=Hl;var g=e.fn,y=g();e.f|=ui;var C=e.deps,P=We==null?void 0:We.is_fork;if(Hr!==null){var E;if(P||Ei(e,Jr),C!==null&&Jr>0)for(C.length=Jr+Hr.length,E=0;E<Hr.length;E++)C[Jr+E]=Hr[E];else e.deps=C=Hr;if(_o()&&(e.f&on)!==0)for(E=Jr;E<C.length;E++)((O=C[E]).reactions??(O.reactions=[])).push(e)}else!P&&C!==null&&Jr<C.length&&(Ei(e,Jr),C.length=Jr);if(Ti()&&rn!==null&&!bn&&C!==null&&(e.f&(Or|hn|Tr))===0)for(E=0;E<rn.length;E++)ad(rn[E],e);if(i!==null&&i!==e){if(Ca++,i.deps!==null)for(let _=0;_<r;_+=1)i.deps[_].rv=Ca;if(t!==null)for(const _ of t)_.rv=Ca;rn!==null&&(a===null?a=rn:a.push(...rn))}return(e.f&sa)!==0&&(e.f^=sa),y}catch(_){return Ns(_)}finally{e.f^=Hl,Hr=t,Jr=r,rn=a,Qe=i,sn=l,li(s),bn=c,Na=v}}function lu(e,t){let r=t.reactions;if(r!==null){var a=Wd.call(r,e);if(a!==-1){var i=r.length-1;i===0?r=t.reactions=null:(r[a]=r[i],r.pop())}}if(r===null&&(t.f&Or)!==0&&(Hr===null||!ii.call(Hr,t))){var l=t;(l.f&on)!==0&&(l.f^=on,l.f&=~Ra),mo(l),Uc(l),Ei(l,0)}}function Ei(e,t){var r=e.deps;if(r!==null)for(var a=t;a<r.length;a++)lu(e,r[a])}function di(e){var t=e.f;if((t&Rn)===0){sr(e,Ar);var r=Ze,a=Qi;Ze=e,Qi=!0;try{(t&(pa|sl))!==0?au(e):ko(e),Js(e);var i=id(e);e.teardown=typeof i=="function"?i:null,e.wv=rd;var l;$l&&Ec&&(e.f&Tr)!==0&&e.deps}finally{Qi=a,Ze=r}}}async function ou(){await Promise.resolve(),Nc()}function n(e){var t=e.f,r=(t&Or)!==0;if(Qe!==null&&!bn){var a=Ze!==null&&(Ze.f&Rn)!==0;if(!a&&(sn===null||!ii.call(sn,e))){var i=Qe.deps;if((Qe.f&Hl)!==0)e.rv<Ca&&(e.rv=Ca,Hr===null&&i!==null&&i[Jr]===e?Jr++:Hr===null?Hr=[e]:Hr.push(e));else{(Qe.deps??(Qe.deps=[])).push(e);var l=e.reactions;l===null?e.reactions=[Qe]:ii.call(l,Qe)||l.push(Qe)}}}if(fa&&ca.has(e))return ca.get(e);if(r){var s=e;if(fa){var c=s.v;return((s.f&Ar)===0&&s.reactions!==null||od(s))&&(c=go(s)),ca.set(s,c),c}var v=(s.f&on)===0&&!bn&&Qe!==null&&(Qi||(Qe.f&on)!==0),m=(s.f&ui)===0;Ii(s)&&(v&&(s.f|=on),Fs(s)),v&&!m&&(Bs(s),ld(s))}if(zr!=null&&zr.has(e))return zr.get(e);if((e.f&sa)!==0)throw e.v;return e.v}function ld(e){if(e.f|=on,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&Or)!==0&&(t.f&on)===0&&(Bs(t),ld(t))}function od(e){if(e.v===Cr)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(ca.has(t)||(t.f&Or)!==0&&od(t))return!0;return!1}function ja(e){var t=bn;try{return bn=!0,e()}finally{bn=t}}function ya(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(jn in e)to(e);else if(!Array.isArray(e))for(let t in e){const r=e[t];typeof r=="object"&&r&&jn in r&&to(r)}}}function to(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let a in e)try{to(e[a],t)}catch{}const r=po(e);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const a=hs(r);for(let i in a){const l=a[i].get;if(l)try{l.call(e)}catch{}}}}}function su(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const du=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function cu(e){return du.includes(e)}const uu={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function vu(e){return e=e.toLowerCase(),uu[e]??e}const fu=["touchstart","touchmove"];function pu(e){return fu.includes(e)}const Sa=Symbol("events"),sd=new Set,ro=new Set;function dd(e,t,r,a={}){function i(l){if(a.capture||no.call(t,l),!l.cancelBubble)return cl(()=>r==null?void 0:r.call(this,l))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Dn(()=>{t.addEventListener(e,i,a)}):t.addEventListener(e,i,a),i}function tl(e,t,r,a,i){var l={capture:a,passive:i},s=dd(e,t,r,l);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&ul(()=>{t.removeEventListener(e,s,l)})}function j(e,t,r){(t[Sa]??(t[Sa]={}))[e]=r}function xa(e){for(var t=0;t<e.length;t++)sd.add(e[t]);for(var r of ro)r(e)}let Go=null;function no(e){var _,M;var t=this,r=t.ownerDocument,a=e.type,i=((_=e.composedPath)==null?void 0:_.call(e))||[],l=i[0]||e.target;Go=e;var s=0,c=Go===e&&e[Sa];if(c){var v=i.indexOf(c);if(v!==-1&&(t===document||t===window)){e[Sa]=t;return}var m=i.indexOf(t);if(m===-1)return;v<=m&&(s=v)}if(l=i[s]||e.target,l!==t){qd(e,"currentTarget",{configurable:!0,get(){return l||r}});var g=Qe,y=Ze;dn(null),cn(null);try{for(var C,P=[];l!==null;){var E=l.assignedSlot||l.parentNode||l.host||null;try{var O=(M=l[Sa])==null?void 0:M[a];O!=null&&(!l.disabled||e.target===l)&&O.call(l,e)}catch(R){C?P.push(R):C=R}if(e.cancelBubble||E===t||E===null)break;l=E}if(C){for(let R of P)queueMicrotask(()=>{throw R});throw C}}finally{e[Sa]=t,delete e.currentTarget,dn(g),cn(y)}}}var bs;const Ll=((bs=globalThis==null?void 0:globalThis.window)==null?void 0:bs.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function xu(e){return(Ll==null?void 0:Ll.createHTML(e))??e}function cd(e){var t=ho("template");return t.innerHTML=xu(e.replaceAll("<!>","<!---->")),t.content}function Da(e,t){var r=Ze;r.nodes===null&&(r.nodes={start:e,end:t,a:null,t:null})}function b(e,t){var r=(t&hc)!==0,a=(t&_c)!==0,i,l=!e.startsWith("<!>");return()=>{i===void 0&&(i=cd(l?e:"<!>"+e),r||(i=Yn(i)));var s=a||Gs?document.importNode(i,!0):i.cloneNode(!0);if(r){var c=Yn(s),v=s.lastChild;Da(c,v)}else Da(s,s);return s}}function mu(e,t,r="svg"){var a=!e.startsWith("<!>"),i=`<${r}>${a?e:"<!>"+e}</${r}>`,l;return()=>{if(!l){var s=cd(i),c=Yn(s);l=Yn(c)}var v=l.cloneNode(!0);return Da(v,v),v}}function bu(e,t){return mu(e,t,"svg")}function an(e=""){{var t=Fn(e+"");return Da(t,t),t}}function ye(){var e=document.createDocumentFragment(),t=document.createComment(""),r=Fn();return e.append(t,r),Da(t,r),e}function x(e,t){e!==null&&e.before(t)}function z(e,t){var r=t==null?"":typeof t=="object"?`${t}`:t;r!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=r,e.nodeValue=`${r}`)}function gu(e,t){return hu(e,t)}const Wi=new Map;function hu(e,{target:t,anchor:r,props:a={},events:i,context:l,intro:s=!0,transformError:c}){Yc();var v=void 0,m=ru(()=>{var g=r??t.appendChild(Fn());Pc(g,{pending:()=>{}},P=>{yn({});var E=Sr;l&&(E.c=l),i&&(a.$$events=i),v=e(P,a)||{},wn()},c);var y=new Set,C=P=>{for(var E=0;E<P.length;E++){var O=P[E];if(!y.has(O)){y.add(O);var _=pu(O);for(const V of[t,document]){var M=Wi.get(V);M===void 0&&(M=new Map,Wi.set(V,M));var R=M.get(O);R===void 0?(V.addEventListener(O,no,{passive:_}),M.set(O,1)):M.set(O,R+1)}}}};return C(ol(sd)),ro.add(C),()=>{var _;for(var P of y)for(const M of[t,document]){var E=Wi.get(M),O=E.get(P);--O==0?(M.removeEventListener(P,no),E.delete(P),E.size===0&&Wi.delete(M)):E.set(P,O)}ro.delete(C),g!==r&&((_=g.parentNode)==null||_.removeChild(g))}});return _u.set(v,m),v}let _u=new WeakMap;var mn,In,Qr,Aa,Mi,zi,ll;class vl{constructor(t,r=!0){fn(this,"anchor");tt(this,mn,new Map);tt(this,In,new Map);tt(this,Qr,new Map);tt(this,Aa,new Set);tt(this,Mi,!0);tt(this,zi,t=>{if(T(this,mn).has(t)){var r=T(this,mn).get(t),a=T(this,In).get(r);if(a)Co(a),T(this,Aa).delete(r);else{var i=T(this,Qr).get(r);i&&(i.effect.f&Fr)===0&&(T(this,In).set(r,i.effect),T(this,Qr).delete(r),i.fragment.lastChild.remove(),this.anchor.before(i.fragment),a=i.effect)}for(const[l,s]of T(this,mn)){if(T(this,mn).delete(l),l===t)break;const c=T(this,Qr).get(s);c&&(Nr(c.effect),T(this,Qr).delete(s))}for(const[l,s]of T(this,In)){if(l===r||T(this,Aa).has(l)||(s.f&Fr)!==0)continue;const c=()=>{if(Array.from(T(this,mn).values()).includes(l)){var m=document.createDocumentFragment();So(s,m),m.append(Fn()),T(this,Qr).set(l,{effect:s,fragment:m})}else Nr(s);T(this,Aa).delete(l),T(this,In).delete(l)};T(this,Mi)||!a?(T(this,Aa).add(l),Ta(s,c,!1)):c()}}});tt(this,ll,t=>{T(this,mn).delete(t);const r=Array.from(T(this,mn).values());for(const[a,i]of T(this,Qr))r.includes(a)||(Nr(i.effect),T(this,Qr).delete(a))});this.anchor=t,Ue(this,Mi,r)}ensure(t,r){var a=We,i=Ws();if(r&&!T(this,In).has(t)&&!T(this,Qr).has(t))if(i){var l=document.createDocumentFragment(),s=Fn();l.append(s),T(this,Qr).set(t,{effect:Ur(()=>r(s)),fragment:l})}else T(this,In).set(t,Ur(()=>r(this.anchor)));if(T(this,mn).set(a,t),i){for(const[c,v]of T(this,In))c===t?a.unskip_effect(v):a.skip_effect(v);for(const[c,v]of T(this,Qr))c===t?a.unskip_effect(v.effect):a.skip_effect(v.effect);a.oncommit(T(this,zi)),a.ondiscard(T(this,ll))}else T(this,zi).call(this,a)}}mn=new WeakMap,In=new WeakMap,Qr=new WeakMap,Aa=new WeakMap,Mi=new WeakMap,zi=new WeakMap,ll=new WeakMap;function A(e,t,r=!1){var a=new vl(e),i=r?Jn:0;function l(s,c){a.ensure(s,c)}fi(()=>{var s=!1;t((c,v=0)=>{s=!0,l(v,c)}),s||l(-1,null)},i)}function Me(e,t){return t}function yu(e,t,r){for(var a=[],i=t.length,l,s=t.length,c=0;c<i;c++){let y=t[c];Ta(y,()=>{if(l){if(l.pending.delete(y),l.done.add(y),l.pending.size===0){var C=e.outrogroups;ao(e,ol(l.done)),C.delete(l),C.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var v=a.length===0&&r!==null;if(v){var m=r,g=m.parentNode;Jc(g),g.append(m),e.items.clear()}ao(e,t,!v)}else l={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(l)}function ao(e,t,r=!0){var a;if(e.pending.size>0){a=new Set;for(const s of e.pending.values())for(const c of s)a.add(e.items.get(c).e)}for(var i=0;i<t.length;i++){var l=t[i];if(a!=null&&a.has(l)){l.f|=Ln;const s=document.createDocumentFragment();So(l,s)}else Nr(t[i],r)}}var Ho;function ze(e,t,r,a,i,l=null){var s=e,c=new Map,v=(t&Cs)!==0;if(v){var m=e;s=m.appendChild(Fn())}var g=null,y=bo(()=>{var V=r();return fo(V)?V:V==null?[]:ol(V)}),C,P=new Map,E=!0;function O(V){(R.effect.f&Rn)===0&&(R.pending.delete(V),R.fallback=g,wu(R,C,s,t,a),g!==null&&(C.length===0?(g.f&Ln)===0?Co(g):(g.f^=Ln,wi(g,null,s)):Ta(g,()=>{g=null})))}function _(V){R.pending.delete(V)}var M=fi(()=>{C=n(y);for(var V=C.length,h=new Set,N=We,G=Ws(),K=0;K<V;K+=1){var S=C[K],W=a(S,K),q=E?null:c.get(W);q?(q.v&&si(q.v,S),q.i&&si(q.i,K),G&&N.unskip_effect(q.e)):(q=ku(c,E?s:Ho??(Ho=Fn()),S,W,K,i,t,r),E||(q.e.f|=Ln),c.set(W,q)),h.add(W)}if(V===0&&l&&!g&&(E?g=Ur(()=>l(s)):(g=Ur(()=>l(Ho??(Ho=Fn()))),g.f|=Ln)),V>h.size&&tc(),!E)if(P.set(N,h),G){for(const[_e,et]of c)h.has(_e)||N.skip_effect(et.e);N.oncommit(O),N.ondiscard(_)}else O(N);n(y)}),R={effect:M,items:c,pending:P,outrogroups:null,fallback:g};E=!1}function gi(e){for(;e!==null&&(e.f&_n)===0;)e=e.next;return e}function wu(e,t,r,a,i){var q,_e,et,me,ve,H,we,Ye,xe;var l=(a&fc)!==0,s=t.length,c=e.items,v=gi(e.effect.first),m,g=null,y,C=[],P=[],E,O,_,M;if(l)for(M=0;M<s;M+=1)E=t[M],O=i(E,M),_=c.get(O).e,(_.f&Ln)===0&&((_e=(q=_.nodes)==null?void 0:q.a)==null||_e.measure(),(y??(y=new Set)).add(_));for(M=0;M<s;M+=1){if(E=t[M],O=i(E,M),_=c.get(O).e,e.outrogroups!==null)for(const vt of e.outrogroups)vt.pending.delete(_),vt.done.delete(_);if((_.f&Ln)!==0)if(_.f^=Ln,_===v)wi(_,null,r);else{var R=g?g.next:v;_===e.effect.last&&(e.effect.last=_.prev),_.prev&&(_.prev.next=_.next),_.next&&(_.next.prev=_.prev),ea(e,g,_),ea(e,_,R),wi(_,R,r),g=_,C=[],P=[],v=gi(g.next);continue}if((_.f&Fr)!==0&&(Co(_),l&&((me=(et=_.nodes)==null?void 0:et.a)==null||me.unfix(),(y??(y=new Set)).delete(_))),_!==v){if(m!==void 0&&m.has(_)){if(C.length<P.length){var V=P[0],h;g=V.prev;var N=C[0],G=C[C.length-1];for(h=0;h<C.length;h+=1)wi(C[h],V,r);for(h=0;h<P.length;h+=1)m.delete(P[h]);ea(e,N.prev,G.next),ea(e,g,N),ea(e,G,V),v=V,g=G,M-=1,C=[],P=[]}else m.delete(_),wi(_,v,r),ea(e,_.prev,_.next),ea(e,_,g===null?e.effect.first:g.next),ea(e,g,_),g=_;continue}for(C=[],P=[];v!==null&&v!==_;)(m??(m=new Set)).add(v),P.push(v),v=gi(v.next);if(v===null)continue}(_.f&Ln)===0&&C.push(_),g=_,v=gi(_.next)}if(e.outrogroups!==null){for(const vt of e.outrogroups)vt.pending.size===0&&(ao(e,ol(vt.done)),(ve=e.outrogroups)==null||ve.delete(vt));e.outrogroups.size===0&&(e.outrogroups=null)}if(v!==null||m!==void 0){var K=[];if(m!==void 0)for(_ of m)(_.f&Fr)===0&&K.push(_);for(;v!==null;)(v.f&Fr)===0&&v!==e.fallback&&K.push(v),v=gi(v.next);var S=K.length;if(S>0){var W=(a&Cs)!==0&&s===0?r:null;if(l){for(M=0;M<S;M+=1)(we=(H=K[M].nodes)==null?void 0:H.a)==null||we.measure();for(M=0;M<S;M+=1)(xe=(Ye=K[M].nodes)==null?void 0:Ye.a)==null||xe.fix()}yu(e,K,W)}}l&&Dn(()=>{var vt,Y;if(y!==void 0)for(_ of y)(Y=(vt=_.nodes)==null?void 0:vt.a)==null||Y.apply()})}function ku(e,t,r,a,i,l,s,c){var v=(s&uc)!==0?(s&pc)===0?Wc(r,!1,!1):va(r):null,m=(s&vc)!==0?va(i):null;return{v,i:m,e:Ur(()=>(l(t,v??r,m??i,c),()=>{e.delete(a)}))}}function wi(e,t,r){if(e.nodes)for(var a=e.nodes.start,i=e.nodes.end,l=t&&(t.f&Ln)===0?t.nodes.start:r;a!==null;){var s=Oi(a);if(l.before(a),a===i)return;a=s}}function ea(e,t,r){t===null?e.effect.first=r:t.next=r,r===null?e.effect.last=t:r.prev=t}function Uo(e,t,r=!1,a=!1,i=!1){var l=e,s="";L(()=>{var c=Ze;if(s!==(s=t()??"")&&(c.nodes!==null&&(Xs(c.nodes.start,c.nodes.end),c.nodes=null),s!=="")){var v=r?Ms:a?yc:void 0,m=ho(r?"svg":a?"math":"template",v);m.innerHTML=s;var g=r||a?m:m.content;if(Da(Yn(g),g.lastChild),r||a)for(;Yn(g);)l.before(Yn(g));else l.before(g)}})}function je(e,t,r,a,i){var c;var l=(c=t.$$slots)==null?void 0:c[r],s=!1;l===!0&&(l=t.children,s=!0),l===void 0||l(e,s?()=>a:a)}function io(e,t,...r){var a=new vl(e);fi(()=>{const i=t()??null;a.ensure(i,i&&(l=>i(l,...r)))},Jn)}function Cu(e,t,r){var a=new vl(e);fi(()=>{var i=t()??null;a.ensure(i,i&&(l=>r(l,i)))},Jn)}function Su(e,t,r,a,i,l){var s=null,c=e,v=new vl(c,!1);fi(()=>{const m=t()||null;var g=Ms;if(m===null){v.ensure(null,null);return}return v.ensure(m,y=>{if(m){if(s=ho(m,g),Da(s,s),a){var C=s.appendChild(Fn());a(s,C)}Ze.nodes.end=s,y.before(s)}}),()=>{}},Jn),ul(()=>{})}function Eu(e,t){var r=void 0,a;Ys(()=>{r!==(r=t())&&(a&&(Nr(a),a=null),r&&(a=Ur(()=>{yo(()=>r(e))})))})}function ud(e){var t,r,a="";if(typeof e=="string"||typeof e=="number")a+=e;else if(typeof e=="object")if(Array.isArray(e)){var i=e.length;for(t=0;t<i;t++)e[t]&&(r=ud(e[t]))&&(a&&(a+=" "),a+=r)}else for(r in e)e[r]&&(a&&(a+=" "),a+=r);return a}function vd(){for(var e,t,r=0,a="",i=arguments.length;r<i;r++)(e=arguments[r])&&(t=ud(e))&&(a&&(a+=" "),a+=t);return a}function rt(e){return typeof e=="object"?vd(e):e??""}const Wo=[...` 	
\r\f \v\uFEFF`];function Mu(e,t,r){var a=e==null?"":""+e;if(r){for(var i of Object.keys(r))if(r[i])a=a?a+" "+i:i;else if(a.length)for(var l=i.length,s=0;(s=a.indexOf(i,s))>=0;){var c=s+l;(s===0||Wo.includes(a[s-1]))&&(c===a.length||Wo.includes(a[c]))?a=(s===0?"":a.substring(0,s))+a.substring(c+1):s=c}}return a===""?null:a}function qo(e,t=!1){var r=t?" !important;":";",a="";for(var i of Object.keys(e)){var l=e[i];l!=null&&l!==""&&(a+=" "+i+": "+l+r)}return a}function Pl(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function zu(e,t){if(t){var r="",a,i;if(Array.isArray(t)?(a=t[0],i=t[1]):a=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var l=!1,s=0,c=!1,v=[];a&&v.push(...Object.keys(a).map(Pl)),i&&v.push(...Object.keys(i).map(Pl));var m=0,g=-1;const O=e.length;for(var y=0;y<O;y++){var C=e[y];if(c?C==="/"&&e[y-1]==="*"&&(c=!1):l?l===C&&(l=!1):C==="/"&&e[y+1]==="*"?c=!0:C==='"'||C==="'"?l=C:C==="("?s++:C===")"&&s--,!c&&l===!1&&s===0){if(C===":"&&g===-1)g=y;else if(C===";"||y===O-1){if(g!==-1){var P=Pl(e.substring(m,g).trim());if(!v.includes(P)){C!==";"&&y++;var E=e.substring(m,y).trim();r+=" "+E+";"}}m=y+1,g=-1}}}}return a&&(r+=qo(a)),i&&(r+=qo(i,!0)),r=r.trim(),r===""?null:r}return e==null?null:String(e)}function nt(e,t,r,a,i,l){var s=e.__className;if(s!==r||s===void 0){var c=Mu(r,a,l);c==null?e.removeAttribute("class"):t?e.className=c:e.setAttribute("class",c),e.__className=r}else if(l&&i!==l)for(var v in l){var m=!!l[v];(i==null||m!==!!i[v])&&e.classList.toggle(v,m)}return l}function Rl(e,t={},r,a){for(var i in r){var l=r[i];t[i]!==l&&(r[i]==null?e.style.removeProperty(i):e.style.setProperty(i,l,a))}}function rl(e,t,r,a){var i=e.__style;if(i!==t){var l=zu(t,a);l==null?e.removeAttribute("style"):e.style.cssText=l,e.__style=t}else a&&(Array.isArray(a)?(Rl(e,r==null?void 0:r[0],a[0]),Rl(e,r==null?void 0:r[1],a[1],"important")):Rl(e,r,a));return a}function lo(e,t,r=!1){if(e.multiple){if(t==null)return;if(!fo(t))return kc();for(var a of e.options)a.selected=t.includes(Ko(a));return}for(a of e.options){var i=Ko(a);if(Kc(i,t)){a.selected=!0;return}}(!r||t!==void 0)&&(e.selectedIndex=-1)}function Au(e){var t=new MutationObserver(()=>{lo(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),ul(()=>{t.disconnect()})}function Ko(e){return"__value"in e?e.__value:e.value}const hi=Symbol("class"),_i=Symbol("style"),fd=Symbol("is custom element"),pd=Symbol("is html"),Tu=ks?"option":"OPTION",Nu=ks?"select":"SELECT";function Ou(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function gn(e,t,r,a){var i=xd(e);i[t]!==(i[t]=r)&&(t==="loading"&&(e[Zd]=r),r==null?e.removeAttribute(t):typeof r!="string"&&md(e).includes(t)?e[t]=r:e.setAttribute(t,r))}function Iu(e,t,r,a,i=!1,l=!1){var s=xd(e),c=s[fd],v=!s[pd],m=t||{},g=e.nodeName===Tu;for(var y in t)y in r||(r[y]=null);r.class?r.class=rt(r.class):r[hi]&&(r.class=null),r[_i]&&(r.style??(r.style=null));var C=md(e);for(const h in r){let N=r[h];if(g&&h==="value"&&N==null){e.value=e.__value="",m[h]=N;continue}if(h==="class"){var P=e.namespaceURI==="http://www.w3.org/1999/xhtml";nt(e,P,N,a,t==null?void 0:t[hi],r[hi]),m[h]=N,m[hi]=r[hi];continue}if(h==="style"){rl(e,N,t==null?void 0:t[_i],r[_i]),m[h]=N,m[_i]=r[_i];continue}var E=m[h];if(!(N===E&&!(N===void 0&&e.hasAttribute(h)))){m[h]=N;var O=h[0]+h[1];if(O!=="$$")if(O==="on"){const G={},K="$$"+h;let S=h.slice(2);var _=cu(S);if(su(S)&&(S=S.slice(0,-7),G.capture=!0),!_&&E){if(N!=null)continue;e.removeEventListener(S,m[K],G),m[K]=null}if(_)j(S,e,N),xa([S]);else if(N!=null){let W=function(q){m[h].call(this,q)};var V=W;m[K]=dd(S,e,W,G)}}else if(h==="style")gn(e,h,N);else if(h==="autofocus")Xc(e,!!N);else if(!c&&(h==="__value"||h==="value"&&N!=null))e.value=e.__value=N;else if(h==="selected"&&g)Ou(e,N);else{var M=h;v||(M=vu(M));var R=M==="defaultValue"||M==="defaultChecked";if(N==null&&!c&&!R)if(s[h]=null,M==="value"||M==="checked"){let G=e;const K=t===void 0;if(M==="value"){let S=G.defaultValue;G.removeAttribute(M),G.defaultValue=S,G.value=G.__value=K?S:null}else{let S=G.defaultChecked;G.removeAttribute(M),G.defaultChecked=S,G.checked=K?S:!1}}else e.removeAttribute(h);else R||C.includes(M)&&(c||typeof N!="string")?(e[M]=N,M in s&&(s[M]=Cr)):typeof N!="function"&&gn(e,M,N)}}}return m}function nl(e,t,r=[],a=[],i=[],l,s=!1,c=!1){Ds(i,r,a,v=>{var m=void 0,g={},y=e.nodeName===Nu,C=!1;if(Ys(()=>{var E=t(...v.map(n)),O=Iu(e,m,E,l,s,c);C&&y&&"value"in E&&lo(e,E.value);for(let M of Object.getOwnPropertySymbols(g))E[M]||Nr(g[M]);for(let M of Object.getOwnPropertySymbols(E)){var _=E[M];M.description===wc&&(!m||_!==m[M])&&(g[M]&&Nr(g[M]),g[M]=Ur(()=>Eu(e,()=>_))),O[M]=_}m=O}),y){var P=e;yo(()=>{lo(P,m.value,!0),Au(P)})}C=!0})}function xd(e){return e.__attributes??(e.__attributes={[fd]:e.nodeName.includes("-"),[pd]:e.namespaceURI===Es})}var Yo=new Map;function md(e){var t=e.getAttribute("is")||e.nodeName,r=Yo.get(t);if(r)return r;Yo.set(t,r=[]);for(var a,i=e,l=Element.prototype;l!==i;){a=hs(i);for(var s in a)a[s].set&&r.push(s);i=po(i)}return r}function Oa(e,t,r=t){var a=new WeakSet;Zc(e,"input",async i=>{var l=i?e.defaultValue:e.value;if(l=jl(e)?Dl(l):l,r(l),We!==null&&a.add(We),await ou(),l!==(l=t())){var s=e.selectionStart,c=e.selectionEnd,v=e.value.length;if(e.value=l??"",c!==null){var m=e.value.length;s===c&&c===v&&m>v?(e.selectionStart=m,e.selectionEnd=m):(e.selectionStart=s,e.selectionEnd=Math.min(c,m))}}}),ja(t)==null&&e.value&&(r(jl(e)?Dl(e.value):e.value),We!==null&&a.add(We)),wo(()=>{var i=t();if(e===document.activeElement){var l=Ul??We;if(a.has(l))return}jl(e)&&i===Dl(e.value)||e.type==="date"&&!i&&!e.value||i!==e.value&&(e.value=i??"")})}function jl(e){var t=e.type;return t==="number"||t==="range"}function Dl(e){return e===""?null:+e}function Jo(e,t){return e===t||(e==null?void 0:e[jn])===t}function ua(e={},t,r,a){return yo(()=>{var i,l;return wo(()=>{i=l,l=[],ja(()=>{e!==r(...l)&&(t(e,...l),i&&Jo(r(...i),e)&&t(null,...i))})}),()=>{Dn(()=>{l&&Jo(r(...l),e)&&t(null,...l)})}}),e}function Lu(e=!1){const t=Sr,r=t.l.u;if(!r)return;let a=()=>ya(t.s);if(e){let i=0,l={};const s=Ni(()=>{let c=!1;const v=t.s;for(const m in v)v[m]!==l[m]&&(l[m]=v[m],c=!0);return c&&i++,i});a=()=>n(s)}r.b.length&&tu(()=>{Xo(t,a),Vl(r.b)}),ln(()=>{const i=ja(()=>r.m.map(Xd));return()=>{for(const l of i)typeof l=="function"&&l()}}),r.a.length&&ln(()=>{Xo(t,a),Vl(r.a)})}function Xo(e,t){if(e.l.s)for(const r of e.l.s)n(r);t()}let qi=!1;function Pu(e){var t=qi;try{return qi=!1,[e(),qi]}finally{qi=t}}const Ru={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function ju(e,t,r){return new Proxy({props:e,exclude:t},Ru)}const Du={get(e,t){if(!e.exclude.includes(t))return n(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,r){if(!(t in e.special)){var a=Ze;try{cn(e.parent_effect),e.special[t]=pt({get[t](){return e.props[t]}},t,Ss)}finally{cn(a)}}return e.special[t](r),Ci(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),Ci(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Ie(e,t){return new Proxy({props:e,exclude:t,special:{},version:va(0),parent_effect:Ze},Du)}const Fu={get(e,t){let r=e.props.length;for(;r--;){let a=e.props[r];if(bi(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a)return a[t]}},set(e,t,r){let a=e.props.length;for(;a--;){let i=e.props[a];bi(i)&&(i=i());const l=oa(i,t);if(l&&l.set)return l.set(r),!0}return!1},getOwnPropertyDescriptor(e,t){let r=e.props.length;for(;r--;){let a=e.props[r];if(bi(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a){const i=oa(a,t);return i&&!i.configurable&&(i.configurable=!0),i}}},has(e,t){if(t===jn||t===ws)return!1;for(let r of e.props)if(bi(r)&&(r=r()),r!=null&&t in r)return!0;return!1},ownKeys(e){const t=[];for(let r of e.props)if(bi(r)&&(r=r()),!!r){for(const a in r)t.includes(a)||t.push(a);for(const a of Object.getOwnPropertySymbols(r))t.includes(a)||t.push(a)}return t}};function Ve(...e){return new Proxy({props:e},Fu)}function pt(e,t,r,a){var V;var i=!Ai||(r&mc)!==0,l=(r&bc)!==0,s=(r&gc)!==0,c=a,v=!0,m=()=>(v&&(v=!1,c=s?ja(a):a),c),g;if(l){var y=jn in e||ws in e;g=((V=oa(e,t))==null?void 0:V.set)??(y&&t in e?h=>e[t]=h:void 0)}var C,P=!1;l?[C,P]=Pu(()=>e[t]):C=e[t],C===void 0&&a!==void 0&&(C=m(),g&&(i&&lc(),g(C)));var E;if(i?E=()=>{var h=e[t];return h===void 0?m():(v=!0,h)}:E=()=>{var h=e[t];return h!==void 0&&(c=void 0),h===void 0?c:h},i&&(r&Ss)===0)return E;if(g){var O=e.$$legacy;return(function(h,N){return arguments.length>0?((!i||!N||O||P)&&g(N?E():h),h):E()})}var _=!1,M=((r&xc)!==0?Ni:bo)(()=>(_=!1,E()));l&&n(M);var R=Ze;return(function(h,N){if(arguments.length>0){const G=N?n(M):i&&l?ut(h):h;return u(M,G),_=!0,c!==void 0&&(c=G),h}return fa&&_||(R.f&Rn)!==0?M.v:n(M)})}const Bu="5";var gs;typeof window<"u"&&((gs=window.__svelte??(window.__svelte={})).v??(gs.v=new Set)).add(Bu);const Zr="";async function $u(){const e=await fetch(`${Zr}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function qa(e,t=null,r=null){const a={provider:e};t&&(a.model=t),r&&(a.api_key=r);const i=await fetch(`${Zr}/api/configure`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!i.ok)throw new Error("설정 실패");return i.json()}async function Vu(e){const t=await fetch(`${Zr}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function Gu(e,{onProgress:t,onDone:r,onError:a}){const i=new AbortController;return fetch(`${Zr}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:i.signal}).then(async l=>{if(!l.ok){a==null||a("다운로드 실패");return}const s=l.body.getReader(),c=new TextDecoder;let v="";for(;;){const{done:m,value:g}=await s.read();if(m)break;v+=c.decode(g,{stream:!0});const y=v.split(`
`);v=y.pop()||"";for(const C of y)if(C.startsWith("data:"))try{const P=JSON.parse(C.slice(5).trim());P.total&&P.completed!==void 0?t==null||t({total:P.total,completed:P.completed,status:P.status}):P.status&&(t==null||t({status:P.status}))}catch{}}r==null||r()}).catch(l=>{l.name!=="AbortError"&&(a==null||a(l.message))}),{abort:()=>i.abort()}}async function Hu(){const e=await fetch(`${Zr}/api/oauth/authorize`);if(!e.ok)throw new Error("OAuth 인증 시작 실패");return e.json()}async function Uu(){const e=await fetch(`${Zr}/api/oauth/status`);return e.ok?e.json():{done:!1}}async function Wu(){const e=await fetch(`${Zr}/api/oauth/logout`,{method:"POST"});if(!e.ok)throw new Error("로그아웃 실패");return e.json()}async function qu(e,t=null,r=null){let a=`${Zr}/api/export/excel/${encodeURIComponent(e)}`;const i=new URLSearchParams;r?i.set("template_id",r):t&&t.length>0&&i.set("modules",t.join(","));const l=i.toString();l&&(a+=`?${l}`);const s=await fetch(a);if(!s.ok){const C=await s.json().catch(()=>({}));throw new Error(C.detail||"Excel 다운로드 실패")}const c=await s.blob(),m=(s.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),g=m?decodeURIComponent(m[1]):`${e}.xlsx`,y=document.createElement("a");return y.href=URL.createObjectURL(c),y.download=g,y.click(),URL.revokeObjectURL(y.href),g}async function Ku(e){const t=await fetch(`${Zr}/api/data/sources/${encodeURIComponent(e)}`);if(!t.ok)throw new Error("소스 목록 조회 실패");return t.json()}async function Fl(e,t,r=50){const a=new URLSearchParams;r!==50&&a.set("max_rows",String(r));const i=a.toString(),l=`${Zr}/api/data/preview/${encodeURIComponent(e)}/${encodeURIComponent(t)}${i?"?"+i:""}`,s=await fetch(l);if(!s.ok){const c=await s.json().catch(()=>({}));throw new Error(c.detail||"미리보기 실패")}return s.json()}async function bd(e){const t=await fetch(`${Zr}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}async function Yu(e){const t=await fetch(`${Zr}/api/company/${e}`);if(!t.ok)throw new Error("기업 정보 조회 실패");return t.json()}function Ju(e,t,r={},{onMeta:a,onSnapshot:i,onContext:l,onSystemPrompt:s,onToolCall:c,onToolResult:v,onChunk:m,onDone:g,onError:y},C=null){const P={question:t,stream:!0,...r};e&&(P.company=e),C&&C.length>0&&(P.history=C);const E=new AbortController;return fetch(`${Zr}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(P),signal:E.signal}).then(async O=>{if(!O.ok){const N=await O.json().catch(()=>({}));y==null||y(N.detail||"스트리밍 실패");return}const _=O.body.getReader(),M=new TextDecoder;let R="",V=!1,h=null;for(;;){const{done:N,value:G}=await _.read();if(N)break;R+=M.decode(G,{stream:!0});const K=R.split(`
`);R=K.pop()||"";for(const S of K)if(S.startsWith("event:"))h=S.slice(6).trim();else if(S.startsWith("data:")&&h){const W=S.slice(5).trim();try{const q=JSON.parse(W);h==="meta"?a==null||a(q):h==="snapshot"?i==null||i(q):h==="context"?l==null||l(q):h==="system_prompt"?s==null||s(q):h==="tool_call"?c==null||c(q):h==="tool_result"?v==null||v(q):h==="chunk"?m==null||m(q.text):h==="error"?y==null||y(q.error,q.action,q.detail):h==="done"&&(V||(V=!0,g==null||g()))}catch{}h=null}}V||(V=!0,g==null||g())}).catch(O=>{O.name!=="AbortError"&&(y==null||y(O.message))}),{abort:()=>E.abort()}}const Xu=(e,t)=>{const r=new Array(e.length+t.length);for(let a=0;a<e.length;a++)r[a]=e[a];for(let a=0;a<t.length;a++)r[e.length+a]=t[a];return r},Qu=(e,t)=>({classGroupId:e,validator:t}),gd=(e=new Map,t=null,r)=>({nextPart:e,validators:t,classGroupId:r}),al="-",Qo=[],Zu="arbitrary..",ev=e=>{const t=rv(e),{conflictingClassGroups:r,conflictingClassGroupModifiers:a}=e;return{getClassGroupId:s=>{if(s.startsWith("[")&&s.endsWith("]"))return tv(s);const c=s.split(al),v=c[0]===""&&c.length>1?1:0;return hd(c,v,t)},getConflictingClassGroupIds:(s,c)=>{if(c){const v=a[s],m=r[s];return v?m?Xu(m,v):v:m||Qo}return r[s]||Qo}}},hd=(e,t,r)=>{if(e.length-t===0)return r.classGroupId;const i=e[t],l=r.nextPart.get(i);if(l){const m=hd(e,t+1,l);if(m)return m}const s=r.validators;if(s===null)return;const c=t===0?e.join(al):e.slice(t).join(al),v=s.length;for(let m=0;m<v;m++){const g=s[m];if(g.validator(c))return g.classGroupId}},tv=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),r=t.indexOf(":"),a=t.slice(0,r);return a?Zu+a:void 0})(),rv=e=>{const{theme:t,classGroups:r}=e;return nv(r,t)},nv=(e,t)=>{const r=gd();for(const a in e){const i=e[a];Eo(i,r,a,t)}return r},Eo=(e,t,r,a)=>{const i=e.length;for(let l=0;l<i;l++){const s=e[l];av(s,t,r,a)}},av=(e,t,r,a)=>{if(typeof e=="string"){iv(e,t,r);return}if(typeof e=="function"){lv(e,t,r,a);return}ov(e,t,r,a)},iv=(e,t,r)=>{const a=e===""?t:_d(t,e);a.classGroupId=r},lv=(e,t,r,a)=>{if(sv(e)){Eo(e(a),t,r,a);return}t.validators===null&&(t.validators=[]),t.validators.push(Qu(r,e))},ov=(e,t,r,a)=>{const i=Object.entries(e),l=i.length;for(let s=0;s<l;s++){const[c,v]=i[s];Eo(v,_d(t,c),r,a)}},_d=(e,t)=>{let r=e;const a=t.split(al),i=a.length;for(let l=0;l<i;l++){const s=a[l];let c=r.nextPart.get(s);c||(c=gd(),r.nextPart.set(s,c)),r=c}return r},sv=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,dv=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,r=Object.create(null),a=Object.create(null);const i=(l,s)=>{r[l]=s,t++,t>e&&(t=0,a=r,r=Object.create(null))};return{get(l){let s=r[l];if(s!==void 0)return s;if((s=a[l])!==void 0)return i(l,s),s},set(l,s){l in r?r[l]=s:i(l,s)}}},oo="!",Zo=":",cv=[],es=(e,t,r,a,i)=>({modifiers:e,hasImportantModifier:t,baseClassName:r,maybePostfixModifierPosition:a,isExternal:i}),uv=e=>{const{prefix:t,experimentalParseClassName:r}=e;let a=i=>{const l=[];let s=0,c=0,v=0,m;const g=i.length;for(let O=0;O<g;O++){const _=i[O];if(s===0&&c===0){if(_===Zo){l.push(i.slice(v,O)),v=O+1;continue}if(_==="/"){m=O;continue}}_==="["?s++:_==="]"?s--:_==="("?c++:_===")"&&c--}const y=l.length===0?i:i.slice(v);let C=y,P=!1;y.endsWith(oo)?(C=y.slice(0,-1),P=!0):y.startsWith(oo)&&(C=y.slice(1),P=!0);const E=m&&m>v?m-v:void 0;return es(l,P,C,E)};if(t){const i=t+Zo,l=a;a=s=>s.startsWith(i)?l(s.slice(i.length)):es(cv,!1,s,void 0,!0)}if(r){const i=a;a=l=>r({className:l,parseClassName:i})}return a},vv=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((r,a)=>{t.set(r,1e6+a)}),r=>{const a=[];let i=[];for(let l=0;l<r.length;l++){const s=r[l],c=s[0]==="[",v=t.has(s);c||v?(i.length>0&&(i.sort(),a.push(...i),i=[]),a.push(s)):i.push(s)}return i.length>0&&(i.sort(),a.push(...i)),a}},fv=e=>({cache:dv(e.cacheSize),parseClassName:uv(e),sortModifiers:vv(e),...ev(e)}),pv=/\s+/,xv=(e,t)=>{const{parseClassName:r,getClassGroupId:a,getConflictingClassGroupIds:i,sortModifiers:l}=t,s=[],c=e.trim().split(pv);let v="";for(let m=c.length-1;m>=0;m-=1){const g=c[m],{isExternal:y,modifiers:C,hasImportantModifier:P,baseClassName:E,maybePostfixModifierPosition:O}=r(g);if(y){v=g+(v.length>0?" "+v:v);continue}let _=!!O,M=a(_?E.substring(0,O):E);if(!M){if(!_){v=g+(v.length>0?" "+v:v);continue}if(M=a(E),!M){v=g+(v.length>0?" "+v:v);continue}_=!1}const R=C.length===0?"":C.length===1?C[0]:l(C).join(":"),V=P?R+oo:R,h=V+M;if(s.indexOf(h)>-1)continue;s.push(h);const N=i(M,_);for(let G=0;G<N.length;++G){const K=N[G];s.push(V+K)}v=g+(v.length>0?" "+v:v)}return v},mv=(...e)=>{let t=0,r,a,i="";for(;t<e.length;)(r=e[t++])&&(a=yd(r))&&(i&&(i+=" "),i+=a);return i},yd=e=>{if(typeof e=="string")return e;let t,r="";for(let a=0;a<e.length;a++)e[a]&&(t=yd(e[a]))&&(r&&(r+=" "),r+=t);return r},bv=(e,...t)=>{let r,a,i,l;const s=v=>{const m=t.reduce((g,y)=>y(g),e());return r=fv(m),a=r.cache.get,i=r.cache.set,l=c,c(v)},c=v=>{const m=a(v);if(m)return m;const g=xv(v,r);return i(v,g),g};return l=s,(...v)=>l(mv(...v))},gv=[],gr=e=>{const t=r=>r[e]||gv;return t.isThemeGetter=!0,t},wd=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,kd=/^\((?:(\w[\w-]*):)?(.+)\)$/i,hv=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,_v=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,yv=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,wv=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,kv=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,Cv=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,ta=e=>hv.test(e),$e=e=>!!e&&!Number.isNaN(Number(e)),ra=e=>!!e&&Number.isInteger(Number(e)),Bl=e=>e.endsWith("%")&&$e(e.slice(0,-1)),Wn=e=>_v.test(e),Cd=()=>!0,Sv=e=>yv.test(e)&&!wv.test(e),Mo=()=>!1,Ev=e=>kv.test(e),Mv=e=>Cv.test(e),zv=e=>!ae(e)&&!oe(e),Av=e=>ma(e,Md,Mo),ae=e=>wd.test(e),ha=e=>ma(e,zd,Sv),ts=e=>ma(e,jv,$e),Tv=e=>ma(e,Td,Cd),Nv=e=>ma(e,Ad,Mo),rs=e=>ma(e,Sd,Mo),Ov=e=>ma(e,Ed,Mv),Ki=e=>ma(e,Nd,Ev),oe=e=>kd.test(e),yi=e=>$a(e,zd),Iv=e=>$a(e,Ad),ns=e=>$a(e,Sd),Lv=e=>$a(e,Md),Pv=e=>$a(e,Ed),Yi=e=>$a(e,Nd,!0),Rv=e=>$a(e,Td,!0),ma=(e,t,r)=>{const a=wd.exec(e);return a?a[1]?t(a[1]):r(a[2]):!1},$a=(e,t,r=!1)=>{const a=kd.exec(e);return a?a[1]?t(a[1]):r:!1},Sd=e=>e==="position"||e==="percentage",Ed=e=>e==="image"||e==="url",Md=e=>e==="length"||e==="size"||e==="bg-size",zd=e=>e==="length",jv=e=>e==="number",Ad=e=>e==="family-name",Td=e=>e==="number"||e==="weight",Nd=e=>e==="shadow",Dv=()=>{const e=gr("color"),t=gr("font"),r=gr("text"),a=gr("font-weight"),i=gr("tracking"),l=gr("leading"),s=gr("breakpoint"),c=gr("container"),v=gr("spacing"),m=gr("radius"),g=gr("shadow"),y=gr("inset-shadow"),C=gr("text-shadow"),P=gr("drop-shadow"),E=gr("blur"),O=gr("perspective"),_=gr("aspect"),M=gr("ease"),R=gr("animate"),V=()=>["auto","avoid","all","avoid-page","page","left","right","column"],h=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],N=()=>[...h(),oe,ae],G=()=>["auto","hidden","clip","visible","scroll"],K=()=>["auto","contain","none"],S=()=>[oe,ae,v],W=()=>[ta,"full","auto",...S()],q=()=>[ra,"none","subgrid",oe,ae],_e=()=>["auto",{span:["full",ra,oe,ae]},ra,oe,ae],et=()=>[ra,"auto",oe,ae],me=()=>["auto","min","max","fr",oe,ae],ve=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],H=()=>["start","end","center","stretch","center-safe","end-safe"],we=()=>["auto",...S()],Ye=()=>[ta,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...S()],xe=()=>[ta,"screen","full","dvw","lvw","svw","min","max","fit",...S()],vt=()=>[ta,"screen","full","lh","dvh","lvh","svh","min","max","fit",...S()],Y=()=>[e,oe,ae],zt=()=>[...h(),ns,rs,{position:[oe,ae]}],Ce=()=>["no-repeat",{repeat:["","x","y","space","round"]}],k=()=>["auto","cover","contain",Lv,Av,{size:[oe,ae]}],J=()=>[Bl,yi,ha],U=()=>["","none","full",m,oe,ae],re=()=>["",$e,yi,ha],he=()=>["solid","dashed","dotted","double"],ge=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],ee=()=>[$e,Bl,ns,rs],ct=()=>["","none",E,oe,ae],xt=()=>["none",$e,oe,ae],Dt=()=>["none",$e,oe,ae],ft=()=>[$e,oe,ae],cr=()=>[ta,"full",...S()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Wn],breakpoint:[Wn],color:[Cd],container:[Wn],"drop-shadow":[Wn],ease:["in","out","in-out"],font:[zv],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Wn],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Wn],shadow:[Wn],spacing:["px",$e],text:[Wn],"text-shadow":[Wn],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",ta,ae,oe,_]}],container:["container"],columns:[{columns:[$e,ae,oe,c]}],"break-after":[{"break-after":V()}],"break-before":[{"break-before":V()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:N()}],overflow:[{overflow:G()}],"overflow-x":[{"overflow-x":G()}],"overflow-y":[{"overflow-y":G()}],overscroll:[{overscroll:K()}],"overscroll-x":[{"overscroll-x":K()}],"overscroll-y":[{"overscroll-y":K()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:W()}],"inset-x":[{"inset-x":W()}],"inset-y":[{"inset-y":W()}],start:[{"inset-s":W(),start:W()}],end:[{"inset-e":W(),end:W()}],"inset-bs":[{"inset-bs":W()}],"inset-be":[{"inset-be":W()}],top:[{top:W()}],right:[{right:W()}],bottom:[{bottom:W()}],left:[{left:W()}],visibility:["visible","invisible","collapse"],z:[{z:[ra,"auto",oe,ae]}],basis:[{basis:[ta,"full","auto",c,...S()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[$e,ta,"auto","initial","none",ae]}],grow:[{grow:["",$e,oe,ae]}],shrink:[{shrink:["",$e,oe,ae]}],order:[{order:[ra,"first","last","none",oe,ae]}],"grid-cols":[{"grid-cols":q()}],"col-start-end":[{col:_e()}],"col-start":[{"col-start":et()}],"col-end":[{"col-end":et()}],"grid-rows":[{"grid-rows":q()}],"row-start-end":[{row:_e()}],"row-start":[{"row-start":et()}],"row-end":[{"row-end":et()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":me()}],"auto-rows":[{"auto-rows":me()}],gap:[{gap:S()}],"gap-x":[{"gap-x":S()}],"gap-y":[{"gap-y":S()}],"justify-content":[{justify:[...ve(),"normal"]}],"justify-items":[{"justify-items":[...H(),"normal"]}],"justify-self":[{"justify-self":["auto",...H()]}],"align-content":[{content:["normal",...ve()]}],"align-items":[{items:[...H(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...H(),{baseline:["","last"]}]}],"place-content":[{"place-content":ve()}],"place-items":[{"place-items":[...H(),"baseline"]}],"place-self":[{"place-self":["auto",...H()]}],p:[{p:S()}],px:[{px:S()}],py:[{py:S()}],ps:[{ps:S()}],pe:[{pe:S()}],pbs:[{pbs:S()}],pbe:[{pbe:S()}],pt:[{pt:S()}],pr:[{pr:S()}],pb:[{pb:S()}],pl:[{pl:S()}],m:[{m:we()}],mx:[{mx:we()}],my:[{my:we()}],ms:[{ms:we()}],me:[{me:we()}],mbs:[{mbs:we()}],mbe:[{mbe:we()}],mt:[{mt:we()}],mr:[{mr:we()}],mb:[{mb:we()}],ml:[{ml:we()}],"space-x":[{"space-x":S()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":S()}],"space-y-reverse":["space-y-reverse"],size:[{size:Ye()}],"inline-size":[{inline:["auto",...xe()]}],"min-inline-size":[{"min-inline":["auto",...xe()]}],"max-inline-size":[{"max-inline":["none",...xe()]}],"block-size":[{block:["auto",...vt()]}],"min-block-size":[{"min-block":["auto",...vt()]}],"max-block-size":[{"max-block":["none",...vt()]}],w:[{w:[c,"screen",...Ye()]}],"min-w":[{"min-w":[c,"screen","none",...Ye()]}],"max-w":[{"max-w":[c,"screen","none","prose",{screen:[s]},...Ye()]}],h:[{h:["screen","lh",...Ye()]}],"min-h":[{"min-h":["screen","lh","none",...Ye()]}],"max-h":[{"max-h":["screen","lh",...Ye()]}],"font-size":[{text:["base",r,yi,ha]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[a,Rv,Tv]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",Bl,ae]}],"font-family":[{font:[Iv,Nv,t]}],"font-features":[{"font-features":[ae]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[i,oe,ae]}],"line-clamp":[{"line-clamp":[$e,"none",oe,ts]}],leading:[{leading:[l,...S()]}],"list-image":[{"list-image":["none",oe,ae]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",oe,ae]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:Y()}],"text-color":[{text:Y()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...he(),"wavy"]}],"text-decoration-thickness":[{decoration:[$e,"from-font","auto",oe,ha]}],"text-decoration-color":[{decoration:Y()}],"underline-offset":[{"underline-offset":[$e,"auto",oe,ae]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:S()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",oe,ae]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",oe,ae]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:zt()}],"bg-repeat":[{bg:Ce()}],"bg-size":[{bg:k()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},ra,oe,ae],radial:["",oe,ae],conic:[ra,oe,ae]},Pv,Ov]}],"bg-color":[{bg:Y()}],"gradient-from-pos":[{from:J()}],"gradient-via-pos":[{via:J()}],"gradient-to-pos":[{to:J()}],"gradient-from":[{from:Y()}],"gradient-via":[{via:Y()}],"gradient-to":[{to:Y()}],rounded:[{rounded:U()}],"rounded-s":[{"rounded-s":U()}],"rounded-e":[{"rounded-e":U()}],"rounded-t":[{"rounded-t":U()}],"rounded-r":[{"rounded-r":U()}],"rounded-b":[{"rounded-b":U()}],"rounded-l":[{"rounded-l":U()}],"rounded-ss":[{"rounded-ss":U()}],"rounded-se":[{"rounded-se":U()}],"rounded-ee":[{"rounded-ee":U()}],"rounded-es":[{"rounded-es":U()}],"rounded-tl":[{"rounded-tl":U()}],"rounded-tr":[{"rounded-tr":U()}],"rounded-br":[{"rounded-br":U()}],"rounded-bl":[{"rounded-bl":U()}],"border-w":[{border:re()}],"border-w-x":[{"border-x":re()}],"border-w-y":[{"border-y":re()}],"border-w-s":[{"border-s":re()}],"border-w-e":[{"border-e":re()}],"border-w-bs":[{"border-bs":re()}],"border-w-be":[{"border-be":re()}],"border-w-t":[{"border-t":re()}],"border-w-r":[{"border-r":re()}],"border-w-b":[{"border-b":re()}],"border-w-l":[{"border-l":re()}],"divide-x":[{"divide-x":re()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":re()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...he(),"hidden","none"]}],"divide-style":[{divide:[...he(),"hidden","none"]}],"border-color":[{border:Y()}],"border-color-x":[{"border-x":Y()}],"border-color-y":[{"border-y":Y()}],"border-color-s":[{"border-s":Y()}],"border-color-e":[{"border-e":Y()}],"border-color-bs":[{"border-bs":Y()}],"border-color-be":[{"border-be":Y()}],"border-color-t":[{"border-t":Y()}],"border-color-r":[{"border-r":Y()}],"border-color-b":[{"border-b":Y()}],"border-color-l":[{"border-l":Y()}],"divide-color":[{divide:Y()}],"outline-style":[{outline:[...he(),"none","hidden"]}],"outline-offset":[{"outline-offset":[$e,oe,ae]}],"outline-w":[{outline:["",$e,yi,ha]}],"outline-color":[{outline:Y()}],shadow:[{shadow:["","none",g,Yi,Ki]}],"shadow-color":[{shadow:Y()}],"inset-shadow":[{"inset-shadow":["none",y,Yi,Ki]}],"inset-shadow-color":[{"inset-shadow":Y()}],"ring-w":[{ring:re()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:Y()}],"ring-offset-w":[{"ring-offset":[$e,ha]}],"ring-offset-color":[{"ring-offset":Y()}],"inset-ring-w":[{"inset-ring":re()}],"inset-ring-color":[{"inset-ring":Y()}],"text-shadow":[{"text-shadow":["none",C,Yi,Ki]}],"text-shadow-color":[{"text-shadow":Y()}],opacity:[{opacity:[$e,oe,ae]}],"mix-blend":[{"mix-blend":[...ge(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":ge()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[$e]}],"mask-image-linear-from-pos":[{"mask-linear-from":ee()}],"mask-image-linear-to-pos":[{"mask-linear-to":ee()}],"mask-image-linear-from-color":[{"mask-linear-from":Y()}],"mask-image-linear-to-color":[{"mask-linear-to":Y()}],"mask-image-t-from-pos":[{"mask-t-from":ee()}],"mask-image-t-to-pos":[{"mask-t-to":ee()}],"mask-image-t-from-color":[{"mask-t-from":Y()}],"mask-image-t-to-color":[{"mask-t-to":Y()}],"mask-image-r-from-pos":[{"mask-r-from":ee()}],"mask-image-r-to-pos":[{"mask-r-to":ee()}],"mask-image-r-from-color":[{"mask-r-from":Y()}],"mask-image-r-to-color":[{"mask-r-to":Y()}],"mask-image-b-from-pos":[{"mask-b-from":ee()}],"mask-image-b-to-pos":[{"mask-b-to":ee()}],"mask-image-b-from-color":[{"mask-b-from":Y()}],"mask-image-b-to-color":[{"mask-b-to":Y()}],"mask-image-l-from-pos":[{"mask-l-from":ee()}],"mask-image-l-to-pos":[{"mask-l-to":ee()}],"mask-image-l-from-color":[{"mask-l-from":Y()}],"mask-image-l-to-color":[{"mask-l-to":Y()}],"mask-image-x-from-pos":[{"mask-x-from":ee()}],"mask-image-x-to-pos":[{"mask-x-to":ee()}],"mask-image-x-from-color":[{"mask-x-from":Y()}],"mask-image-x-to-color":[{"mask-x-to":Y()}],"mask-image-y-from-pos":[{"mask-y-from":ee()}],"mask-image-y-to-pos":[{"mask-y-to":ee()}],"mask-image-y-from-color":[{"mask-y-from":Y()}],"mask-image-y-to-color":[{"mask-y-to":Y()}],"mask-image-radial":[{"mask-radial":[oe,ae]}],"mask-image-radial-from-pos":[{"mask-radial-from":ee()}],"mask-image-radial-to-pos":[{"mask-radial-to":ee()}],"mask-image-radial-from-color":[{"mask-radial-from":Y()}],"mask-image-radial-to-color":[{"mask-radial-to":Y()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":h()}],"mask-image-conic-pos":[{"mask-conic":[$e]}],"mask-image-conic-from-pos":[{"mask-conic-from":ee()}],"mask-image-conic-to-pos":[{"mask-conic-to":ee()}],"mask-image-conic-from-color":[{"mask-conic-from":Y()}],"mask-image-conic-to-color":[{"mask-conic-to":Y()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:zt()}],"mask-repeat":[{mask:Ce()}],"mask-size":[{mask:k()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",oe,ae]}],filter:[{filter:["","none",oe,ae]}],blur:[{blur:ct()}],brightness:[{brightness:[$e,oe,ae]}],contrast:[{contrast:[$e,oe,ae]}],"drop-shadow":[{"drop-shadow":["","none",P,Yi,Ki]}],"drop-shadow-color":[{"drop-shadow":Y()}],grayscale:[{grayscale:["",$e,oe,ae]}],"hue-rotate":[{"hue-rotate":[$e,oe,ae]}],invert:[{invert:["",$e,oe,ae]}],saturate:[{saturate:[$e,oe,ae]}],sepia:[{sepia:["",$e,oe,ae]}],"backdrop-filter":[{"backdrop-filter":["","none",oe,ae]}],"backdrop-blur":[{"backdrop-blur":ct()}],"backdrop-brightness":[{"backdrop-brightness":[$e,oe,ae]}],"backdrop-contrast":[{"backdrop-contrast":[$e,oe,ae]}],"backdrop-grayscale":[{"backdrop-grayscale":["",$e,oe,ae]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[$e,oe,ae]}],"backdrop-invert":[{"backdrop-invert":["",$e,oe,ae]}],"backdrop-opacity":[{"backdrop-opacity":[$e,oe,ae]}],"backdrop-saturate":[{"backdrop-saturate":[$e,oe,ae]}],"backdrop-sepia":[{"backdrop-sepia":["",$e,oe,ae]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":S()}],"border-spacing-x":[{"border-spacing-x":S()}],"border-spacing-y":[{"border-spacing-y":S()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",oe,ae]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[$e,"initial",oe,ae]}],ease:[{ease:["linear","initial",M,oe,ae]}],delay:[{delay:[$e,oe,ae]}],animate:[{animate:["none",R,oe,ae]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[O,oe,ae]}],"perspective-origin":[{"perspective-origin":N()}],rotate:[{rotate:xt()}],"rotate-x":[{"rotate-x":xt()}],"rotate-y":[{"rotate-y":xt()}],"rotate-z":[{"rotate-z":xt()}],scale:[{scale:Dt()}],"scale-x":[{"scale-x":Dt()}],"scale-y":[{"scale-y":Dt()}],"scale-z":[{"scale-z":Dt()}],"scale-3d":["scale-3d"],skew:[{skew:ft()}],"skew-x":[{"skew-x":ft()}],"skew-y":[{"skew-y":ft()}],transform:[{transform:[oe,ae,"","none","gpu","cpu"]}],"transform-origin":[{origin:N()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:cr()}],"translate-x":[{"translate-x":cr()}],"translate-y":[{"translate-y":cr()}],"translate-z":[{"translate-z":cr()}],"translate-none":["translate-none"],accent:[{accent:Y()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:Y()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",oe,ae]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":S()}],"scroll-mx":[{"scroll-mx":S()}],"scroll-my":[{"scroll-my":S()}],"scroll-ms":[{"scroll-ms":S()}],"scroll-me":[{"scroll-me":S()}],"scroll-mbs":[{"scroll-mbs":S()}],"scroll-mbe":[{"scroll-mbe":S()}],"scroll-mt":[{"scroll-mt":S()}],"scroll-mr":[{"scroll-mr":S()}],"scroll-mb":[{"scroll-mb":S()}],"scroll-ml":[{"scroll-ml":S()}],"scroll-p":[{"scroll-p":S()}],"scroll-px":[{"scroll-px":S()}],"scroll-py":[{"scroll-py":S()}],"scroll-ps":[{"scroll-ps":S()}],"scroll-pe":[{"scroll-pe":S()}],"scroll-pbs":[{"scroll-pbs":S()}],"scroll-pbe":[{"scroll-pbe":S()}],"scroll-pt":[{"scroll-pt":S()}],"scroll-pr":[{"scroll-pr":S()}],"scroll-pb":[{"scroll-pb":S()}],"scroll-pl":[{"scroll-pl":S()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",oe,ae]}],fill:[{fill:["none",...Y()]}],"stroke-w":[{stroke:[$e,yi,ha,ts]}],stroke:[{stroke:["none",...Y()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},Fv=bv(Dv);function at(...e){return Fv(vd(e))}const so="dartlab-conversations",as=50;function Bv(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function $v(){try{const e=localStorage.getItem(so);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const Vv=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function is(e){return e.map(t=>({...t,messages:t.messages.map(r=>{if(r.role!=="assistant")return r;const a={};for(const[i,l]of Object.entries(r))Vv.includes(i)||(a[i]=l);return a})}))}function ls(e){try{const t={conversations:is(e.conversations),activeId:e.activeId};localStorage.setItem(so,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:is(e.conversations),activeId:e.activeId};localStorage.setItem(so,JSON.stringify(t))}catch{}}}}function Gv(){const e=$v(),t=e.conversations||[],r=t.find(M=>M.id===e.activeId)?e.activeId:null;let a=F(ut(t)),i=F(ut(r)),l=null;function s(){l&&clearTimeout(l),l=setTimeout(()=>{ls({conversations:n(a),activeId:n(i)}),l=null},300)}function c(){l&&clearTimeout(l),l=null,ls({conversations:n(a),activeId:n(i)})}function v(){return n(a).find(M=>M.id===n(i))||null}function m(){const M={id:Bv(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return u(a,[M,...n(a)],!0),n(a).length>as&&u(a,n(a).slice(0,as),!0),u(i,M.id,!0),c(),M.id}function g(M){n(a).find(R=>R.id===M)&&(u(i,M,!0),c())}function y(M,R,V=null){const h=v();if(!h)return;const N={role:M,text:R};V&&(N.meta=V),h.messages=[...h.messages,N],h.updatedAt=Date.now(),h.title==="새 대화"&&M==="user"&&(h.title=R.length>30?R.slice(0,30)+"...":R),u(a,[...n(a)],!0),c()}function C(M){const R=v();if(!R||R.messages.length===0)return;const V=R.messages[R.messages.length-1];Object.assign(V,M),R.updatedAt=Date.now(),u(a,[...n(a)],!0),s()}function P(M){u(a,n(a).filter(R=>R.id!==M),!0),n(i)===M&&u(i,n(a).length>0?n(a)[0].id:null,!0),c()}function E(){const M=v();!M||M.messages.length===0||(M.messages=M.messages.slice(0,-1),M.updatedAt=Date.now(),u(a,[...n(a)],!0),c())}function O(M,R){const V=n(a).find(h=>h.id===M);V&&(V.title=R,u(a,[...n(a)],!0),c())}function _(){u(a,[],!0),u(i,null),c()}return{get conversations(){return n(a)},get activeId(){return n(i)},get active(){return v()},createConversation:m,setActive:g,addMessage:y,updateLastMessage:C,removeLastMessage:E,deleteConversation:P,updateTitle:O,clearAll:_,flush:c}}const Od="dartlab-workspace",Hv=new Set(["overview","explore","evidence"]),Uv=6;function Ya(e){return Hv.has(e)?e:"overview"}function fl(){return typeof window<"u"&&typeof localStorage<"u"}function Wv(){if(!fl())return{};const e=new URLSearchParams(window.location.search),t=e.get("company")||null,r=e.get("tab"),a=e.get("panel");return{stockCode:t,tab:r?Ya(r):null,isOpen:a==="open"?!0:a==="closed"?!1:null}}function qv(){if(!fl())return{};try{const e=localStorage.getItem(Od);if(!e)return{};const t=JSON.parse(e);return{isOpen:typeof t.isOpen=="boolean"?t.isOpen:!0,activeTab:Ya(t.activeTab),selectedCompany:t.selectedCompany||null,userPinnedCompany:!!t.userPinnedCompany,recentCompanies:Array.isArray(t.recentCompanies)?t.recentCompanies:[],activeEvidenceSection:t.activeEvidenceSection||null,selectedEvidenceIndex:Number.isInteger(t.selectedEvidenceIndex)?t.selectedEvidenceIndex:null}}catch{return{}}}function Kv(e){fl()&&localStorage.setItem(Od,JSON.stringify(e))}function Yv(e){var r;if(!fl())return;const t=new URL(window.location.href);(r=e.selectedCompany)!=null&&r.stockCode?t.searchParams.set("company",e.selectedCompany.stockCode):t.searchParams.delete("company"),t.searchParams.set("tab",Ya(e.activeTab)),t.searchParams.set("panel",e.isOpen?"open":"closed"),window.history.replaceState({},"",t)}function Jv(){const e=qv(),t=Wv(),r=t.stockCode?{...e.selectedCompany||{},stockCode:t.stockCode}:e.selectedCompany||null;let a=F(ut(t.isOpen??e.isOpen??!0)),i=F(ut(t.tab??e.activeTab??"overview")),l=F(ut(r)),s=F(ut(e.userPinnedCompany??!!r)),c=F(ut(e.recentCompanies||[])),v=F(ut(e.activeEvidenceSection??null)),m=F(ut(e.selectedEvidenceIndex??null));function g(h){if(!(h!=null&&h.stockCode))return;const N={stockCode:h.stockCode,corpName:h.corpName||h.company||h.stockCode,company:h.company||h.corpName||h.stockCode,market:h.market||"",sector:h.sector||""},G=n(c).filter(K=>K.stockCode!==N.stockCode);u(c,[N,...G].slice(0,Uv),!0)}function y(){const h={isOpen:n(a),activeTab:n(i),selectedCompany:n(l),userPinnedCompany:n(s),recentCompanies:n(c),activeEvidenceSection:n(v),selectedEvidenceIndex:n(m)};Kv(h),Yv(h)}function C(h="explore"){u(i,Ya(h),!0),u(a,!0),n(i)!=="evidence"&&(u(v,null),u(m,null)),y()}function P(){u(a,!1),y()}function E(h){u(i,Ya(h),!0),n(i)!=="evidence"&&(u(v,null),u(m,null)),y()}function O(h,N=null){u(i,"evidence"),u(a,!0),u(v,h||null,!0),u(m,Number.isInteger(N)?N:null,!0),y()}function _(){u(v,null),u(m,null),y()}function M(h,{pin:N=!0,openTab:G=null}={}){u(l,h,!0),u(s,h?N:!1,!0),u(v,null),u(m,null),h&&g(h),G&&(u(i,Ya(G),!0),u(a,!0)),y()}function R(h={},N=null){var G,K,S,W,q;!(h!=null&&h.company)&&!(h!=null&&h.stockCode)||(u(l,{...n(l)||{},...N||{},corpName:h.company||((G=n(l))==null?void 0:G.corpName)||(N==null?void 0:N.corpName)||(N==null?void 0:N.company),company:h.company||((K=n(l))==null?void 0:K.company)||(N==null?void 0:N.company)||(N==null?void 0:N.corpName),stockCode:h.stockCode||((S=n(l))==null?void 0:S.stockCode)||(N==null?void 0:N.stockCode),market:((W=n(l))==null?void 0:W.market)||(N==null?void 0:N.market)||"",sector:((q=n(l))==null?void 0:q.sector)||(N==null?void 0:N.sector)||""},!0),u(s,!0),g(n(l)),y())}function V(){u(l,null),u(s,!1),u(v,null),u(m,null),y()}return{get isOpen(){return n(a)},get activeTab(){return n(i)},get selectedCompany(){return n(l)},get userPinnedCompany(){return n(s)},get recentCompanies(){return n(c)},get activeEvidenceSection(){return n(v)},get selectedEvidenceIndex(){return n(m)},open:C,close:P,setTab:E,openEvidence:O,clearEvidenceSelection:_,selectCompany:M,syncCompanyFromMessage:R,resetCompany:V}}var Xv=b("<a><!></a>"),Qv=b("<button><!></button>");function Zv(e,t){yn(t,!0);let r=pt(t,"variant",3,"default"),a=pt(t,"size",3,"default"),i=ju(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const l={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},s={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var c=ye(),v=Z(c);{var m=y=>{var C=Xv();nl(C,E=>({class:E,...i}),[()=>at("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",l[r()],s[a()],t.class)]);var P=d(C);io(P,()=>t.children),x(y,C)},g=y=>{var C=Qv();nl(C,E=>({class:E,...i}),[()=>at("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",l[r()],s[a()],t.class)]);var P=d(C);io(P,()=>t.children),x(y,C)};A(v,y=>{t.href?y(m):y(g,-1)})}x(e,c),wn()}Mc();/**
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
 */const ef={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const tf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const os=(...e)=>e.filter((t,r,a)=>!!t&&t.trim()!==""&&a.indexOf(t)===r).join(" ").trim();var rf=bu("<svg><!><!></svg>");function Ge(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]),a=Ie(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);yn(t,!1);let i=pt(t,"name",8,void 0),l=pt(t,"color",8,"currentColor"),s=pt(t,"size",8,24),c=pt(t,"strokeWidth",8,2),v=pt(t,"absoluteStrokeWidth",8,!1),m=pt(t,"iconNode",24,()=>[]);Lu();var g=rf();nl(g,(P,E,O)=>({...ef,...P,...a,width:s(),height:s(),stroke:l(),"stroke-width":E,class:O}),[()=>tf(a)?void 0:{"aria-hidden":"true"},()=>(ya(v()),ya(c()),ya(s()),ja(()=>v()?Number(c())*24/Number(s()):c())),()=>(ya(os),ya(i()),ya(r),ja(()=>os("lucide-icon","lucide",i()?`lucide-${i()}`:"",r.class)))]);var y=d(g);ze(y,1,m,Me,(P,E)=>{var O=ne(()=>el(n(E),2));let _=()=>n(O)[0],M=()=>n(O)[1];var R=ye(),V=Z(R);Su(V,_,!0,(h,N)=>{nl(h,()=>({...M()}))}),x(P,R)});var C=f(y);je(C,t,"default",{}),x(e,g),wn()}function nf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];Ge(e,Ve({name:"activity"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function af(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];Ge(e,Ve({name:"arrow-up"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function Zi(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];Ge(e,Ve({name:"brain"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function lf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M20 6 9 17l-5-5"}]];Ge(e,Ve({name:"check"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function of(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m6 9 6 6 6-6"}]];Ge(e,Ve({name:"chevron-down"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function ss(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m9 18 6-6-6-6"}]];Ge(e,Ve({name:"chevron-right"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function _a(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];Ge(e,Ve({name:"circle-alert"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function Ia(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];Ge(e,Ve({name:"circle-check"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function sf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];Ge(e,Ve({name:"clock"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function df(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];Ge(e,Ve({name:"code"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function cf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];Ge(e,Ve({name:"coffee"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function hr(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];Ge(e,Ve({name:"database"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function La(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];Ge(e,Ve({name:"download"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function ds(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];Ge(e,Ve({name:"external-link"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function co(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];Ge(e,Ve({name:"eye"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function Ka(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];Ge(e,Ve({name:"file-text"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function uf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];Ge(e,Ve({name:"github"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function cs(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];Ge(e,Ve({name:"key"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function vf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m5 8 6 6"}],["path",{d:"m4 14 6-6 2-3"}],["path",{d:"M2 5h12"}],["path",{d:"M7 2h1"}],["path",{d:"m22 22-5-10-5 10"}],["path",{d:"M14 18h6"}]];Ge(e,Ve({name:"languages"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function ff(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M9 17H7A5 5 0 0 1 7 7h2"}],["path",{d:"M15 7h2a5 5 0 1 1 0 10h-2"}],["line",{x1:"8",x2:"16",y1:"12",y2:"12"}]];Ge(e,Ve({name:"link-2"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function Lr(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];Ge(e,Ve({name:"loader-circle"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function pf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m10 17 5-5-5-5"}],["path",{d:"M15 12H3"}],["path",{d:"M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"}]];Ge(e,Ve({name:"log-in"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function xf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];Ge(e,Ve({name:"log-out"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function mf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];Ge(e,Ve({name:"menu"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function us(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];Ge(e,Ve({name:"message-square"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function bf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];Ge(e,Ve({name:"panel-left-close"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function vs(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];Ge(e,Ve({name:"plus"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function gf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];Ge(e,Ve({name:"refresh-cw"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function hf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"}],["path",{d:"M3 3v5h5"}]];Ge(e,Ve({name:"rotate-ccw"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function Fa(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];Ge(e,Ve({name:"search"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function _f(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];Ge(e,Ve({name:"settings"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function yf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];Ge(e,Ve({name:"sparkles"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function wf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];Ge(e,Ve({name:"square"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function fs(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];Ge(e,Ve({name:"table-2"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function kf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];Ge(e,Ve({name:"terminal"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function Cf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];Ge(e,Ve({name:"trash-2"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function Sf(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];Ge(e,Ve({name:"triangle-alert"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function uo(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];Ge(e,Ve({name:"wrench"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}function Ja(e,t){const r=Ie(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];Ge(e,Ve({name:"x"},()=>r,{get iconNode(){return a},children:(i,l)=>{var s=ye(),c=Z(s);je(c,t,"default",{}),x(i,s)},$$slots:{default:!0}}))}var Ef=b("<!> 새 대화",1),Mf=b('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),zf=b('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),Af=b('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),Tf=b('<div class="flex-shrink-0 px-4 py-3 border-t border-dl-border/40"><div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Version</div> <div class="mt-1 text-[10px] text-dl-text-muted"> </div></div>'),Nf=b('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),Of=b("<button><!></button>"),If=b('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),Lf=b("<aside><!></aside>");function Pf(e,t){yn(t,!0);let r=pt(t,"conversations",19,()=>[]),a=pt(t,"activeId",3,null),i=pt(t,"open",3,!0),l=pt(t,"version",3,""),s=F("");function c(E){const O=new Date().setHours(0,0,0,0),_=O-864e5,M=O-7*864e5,R={오늘:[],어제:[],"이번 주":[],이전:[]};for(const h of E)h.updatedAt>=O?R.오늘.push(h):h.updatedAt>=_?R.어제.push(h):h.updatedAt>=M?R["이번 주"].push(h):R.이전.push(h);const V=[];for(const[h,N]of Object.entries(R))N.length>0&&V.push({label:h,items:N});return V}let v=ne(()=>n(s).trim()?r().filter(E=>E.title.toLowerCase().includes(n(s).toLowerCase())):r()),m=ne(()=>c(n(v)));var g=Lf(),y=d(g);{var C=E=>{var O=Nf(),_=f(d(O),2),M=d(_);Zv(M,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(K,S)=>{var W=Ef(),q=Z(W);vs(q,{size:16}),x(K,W)},$$slots:{default:!0}});var R=f(_,2);{var V=K=>{var S=Mf(),W=d(S),q=d(W);Fa(q,{size:12,class:"text-dl-text-dim flex-shrink-0"});var _e=f(q,2);Oa(_e,()=>n(s),et=>u(s,et)),x(K,S)};A(R,K=>{r().length>3&&K(V)})}var h=f(R,2);ze(h,21,()=>n(m),Me,(K,S)=>{var W=Af(),q=d(W),_e=d(q),et=f(q,2);ze(et,17,()=>n(S).items,Me,(me,ve)=>{var H=zf(),we=d(H),Ye=d(we);us(Ye,{size:14,class:"flex-shrink-0 opacity-50"});var xe=f(Ye,2),vt=d(xe),Y=f(we,2),zt=d(Y);Cf(zt,{size:12}),L(Ce=>{nt(H,1,Ce),gn(we,"aria-current",n(ve).id===a()?"true":void 0),z(vt,n(ve).title),gn(Y,"aria-label",`${n(ve).title} 삭제`)},[()=>rt(at("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",n(ve).id===a()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),j("click",we,()=>{var Ce;return(Ce=t.onSelect)==null?void 0:Ce.call(t,n(ve).id)}),j("click",Y,Ce=>{var k;Ce.stopPropagation(),(k=t.onDelete)==null||k.call(t,n(ve).id)}),x(me,H)}),L(()=>z(_e,n(S).label)),x(K,W)});var N=f(h,2);{var G=K=>{var S=Tf(),W=f(d(S),2),q=d(W);L(()=>z(q,`DartLab v${l()??""}`)),x(K,S)};A(N,K=>{l()&&K(G)})}x(E,O)},P=E=>{var O=If(),_=f(d(O),2),M=d(_);vs(M,{size:18});var R=f(_,2);ze(R,21,()=>r().slice(0,10),Me,(V,h)=>{var N=Of(),G=d(N);us(G,{size:16}),L(K=>{nt(N,1,K),gn(N,"title",n(h).title)},[()=>rt(at("p-2 rounded-lg transition-colors w-full flex justify-center",n(h).id===a()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),j("click",N,()=>{var K;return(K=t.onSelect)==null?void 0:K.call(t,n(h).id)}),x(V,N)}),j("click",_,function(...V){var h;(h=t.onNewChat)==null||h.apply(this,V)}),x(E,O)};A(y,E=>{i()?E(C):E(P,-1)})}L(E=>nt(g,1,E),[()=>rt(at("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",i()?"w-[260px]":"w-[52px]"))]),x(e,g),wn()}xa(["click"]);var Rf=b('<button class="send-btn active"><!></button>'),jf=b("<button><!></button>"),Df=b('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),Ff=b('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),Bf=b('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),$f=b('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function Id(e,t){yn(t,!0);let r=pt(t,"inputText",15,""),a=pt(t,"isLoading",3,!1),i=pt(t,"large",3,!1),l=pt(t,"placeholder",3,"메시지를 입력하세요..."),s=F(ut([])),c=F(!1),v=F(-1),m=null,g=F(void 0);function y(S){var W;if(n(c)&&n(s).length>0){if(S.key==="ArrowDown"){S.preventDefault(),u(v,(n(v)+1)%n(s).length);return}if(S.key==="ArrowUp"){S.preventDefault(),u(v,n(v)<=0?n(s).length-1:n(v)-1,!0);return}if(S.key==="Enter"&&n(v)>=0){S.preventDefault(),E(n(s)[n(v)]);return}if(S.key==="Escape"){u(c,!1),u(v,-1);return}}S.key==="Enter"&&!S.shiftKey&&(S.preventDefault(),u(c,!1),(W=t.onSend)==null||W.call(t))}function C(S){S.target.style.height="auto",S.target.style.height=Math.min(S.target.scrollHeight,200)+"px"}function P(S){C(S);const W=r();m&&clearTimeout(m),W.length>=2&&!/\s/.test(W.slice(-1))?m=setTimeout(async()=>{var q;try{const _e=await bd(W.trim());((q=_e.results)==null?void 0:q.length)>0?(u(s,_e.results.slice(0,6),!0),u(c,!0),u(v,-1)):u(c,!1)}catch{u(c,!1)}},300):u(c,!1)}function E(S){r(`${S.corpName} `),u(c,!1),u(v,-1),n(g)&&n(g).focus()}function O(){setTimeout(()=>{u(c,!1)},200)}var _=$f(),M=d(_),R=d(M);ua(R,S=>u(g,S),()=>n(g));var V=f(R,2);{var h=S=>{var W=Rf(),q=d(W);wf(q,{size:14}),j("click",W,function(..._e){var et;(et=t.onStop)==null||et.apply(this,_e)}),x(S,W)},N=S=>{var W=jf(),q=d(W);{let _e=ne(()=>i()?18:16);af(q,{get size(){return n(_e)},strokeWidth:2.5})}L((_e,et)=>{nt(W,1,_e),W.disabled=et},[()=>rt(at("send-btn",r().trim()&&"active")),()=>!r().trim()]),j("click",W,()=>{var _e;u(c,!1),(_e=t.onSend)==null||_e.call(t)}),x(S,W)};A(V,S=>{a()&&t.onStop?S(h):S(N,-1)})}var G=f(M,2);{var K=S=>{var W=Bf();ze(W,21,()=>n(s),Me,(q,_e,et)=>{var me=Ff(),ve=d(me);Fa(ve,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var H=f(ve,2),we=d(H),Ye=d(we),xe=f(we,2),vt=d(xe),Y=f(H,2);{var zt=Ce=>{var k=Df(),J=d(k);L(()=>z(J,n(_e).sector)),x(Ce,k)};A(Y,Ce=>{n(_e).sector&&Ce(zt)})}L(Ce=>{nt(me,1,Ce),z(Ye,n(_e).corpName),z(vt,`${n(_e).stockCode??""} · ${(n(_e).market||"")??""}`)},[()=>rt(at("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",et===n(v)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),j("mousedown",me,()=>E(n(_e))),tl("mouseenter",me,()=>{u(v,et,!0)}),x(q,me)}),x(S,W)};A(G,S=>{n(c)&&n(s).length>0&&S(K)})}L(S=>{nt(M,1,S),gn(R,"placeholder",l())},[()=>rt(at("input-box",i()&&"large"))]),j("keydown",R,y),j("input",R,P),tl("blur",R,O),Oa(R,r),x(e,_),wn()}xa(["keydown","input","click","mousedown"]);var Vf=b('<div class="mb-6 inline-flex items-center gap-2 rounded-full border border-dl-primary/20 bg-dl-primary/[0.05] px-3 py-1.5 text-[12px] text-dl-text"><!> <span> </span></div>'),Gf=b('<button class="rounded-2xl border border-dl-border/50 bg-dl-bg-card/40 px-3 py-3 text-left text-[12px] text-dl-text-muted transition-all duration-200 hover:-translate-y-0.5 hover:border-dl-primary/30 hover:bg-dl-bg-card/65 hover:text-dl-text"> </button>'),Hf=b('<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[720px] flex flex-col items-center"><div class="relative mb-6"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-4">재무 수치와 서술 텍스트를 함께 읽고, 필요하면 원문 근거까지 바로 확인할 수 있습니다</p> <!> <div class="w-full"><!></div> <div class="mt-5 grid w-full gap-3 md:grid-cols-3"><div class="surface-panel rounded-2xl border border-dl-border/60 px-4 py-3"><div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Coverage</div> <div class="mt-1 text-[18px] font-semibold text-dl-text">40개 모듈</div> <div class="mt-1 text-[11px] text-dl-text-dim">재무, 주석, 사업, 리스크, 지배구조까지 연결</div></div> <div class="surface-panel rounded-2xl border border-dl-border/60 px-4 py-3"><div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Schema</div> <div class="mt-1 text-[18px] font-semibold text-dl-text">표준화 계정</div> <div class="mt-1 text-[11px] text-dl-text-dim">회사마다 다른 XBRL 계정을 비교 가능한 구조로 정리</div></div> <div class="surface-panel rounded-2xl border border-dl-border/60 px-4 py-3"><div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Evidence</div> <div class="mt-1 text-[18px] font-semibold text-dl-text">원문 근거 보존</div> <div class="mt-1 text-[11px] text-dl-text-dim">숫자와 서술 텍스트를 함께 보고 근거까지 바로 열람</div></div></div> <div class="mt-5 grid w-full gap-3 md:grid-cols-3"><button class="surface-panel flex items-center justify-center gap-2 rounded-2xl border border-dl-border/60 px-4 py-3 text-[13px] text-dl-text-dim transition-all duration-200 hover:-translate-y-0.5 hover:border-dl-primary/30 hover:text-dl-text-muted"><!> 검색 탐색</button> <button class="surface-panel flex items-center justify-center gap-2 rounded-2xl border border-dl-border/60 px-4 py-3 text-[13px] text-dl-text-dim transition-all duration-200 hover:-translate-y-0.5 hover:border-dl-primary/30 hover:text-dl-text-muted"><!> Overview</button> <button class="surface-panel flex items-center justify-center gap-2 rounded-2xl border border-dl-border/60 px-4 py-3 text-[13px] text-dl-text-dim transition-all duration-200 hover:-translate-y-0.5 hover:border-dl-primary/30 hover:text-dl-text-muted"><!> 근거 패널</button></div> <div class="surface-panel mt-5 w-full rounded-[24px] border border-dl-border/60 p-4"><div class="mb-3 flex items-center justify-between gap-3"><div><div class="text-[12px] font-medium text-dl-text">바로 시작할 질문</div> <div class="mt-1 text-[11px] text-dl-text-dim">표준화된 계정, 40개 모듈, 원문 근거 보존이라는 DartLab의 강점을 바로 써먹는 질문입니다.</div></div> <span class="rounded-full bg-dl-primary/10 px-2.5 py-1 text-[9px] uppercase tracking-[0.16em] text-dl-primary-light">Evidence First</span></div> <div class="grid gap-2 md:grid-cols-3"></div></div></div></div>');function Uf(e,t){yn(t,!0);let r=pt(t,"inputText",15,""),a=pt(t,"selectedCompany",3,null);const i=["표준화된 계정 기준으로 최근 실적 변화를 비교해줘","사업보고서와 공시 텍스트에서 핵심 리스크를 정리해줘","재무 수치와 원문 근거를 같이 보여주면서 설명해줘"];var l=Hf(),s=d(l),c=f(d(s),6);{var v=h=>{var N=Vf(),G=d(N);hr(G,{size:13,class:"text-dl-primary-light"});var K=f(G,2),S=d(K);L(()=>z(S,`${(a().corpName||a().company||"선택된 회사")??""} · ${a().stockCode??""}`)),x(h,N)};A(c,h=>{a()&&h(v)})}var m=f(c,2),g=d(m);Id(g,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get inputText(){return r()},set inputText(h){r(h)}});var y=f(m,4),C=d(y),P=d(C);Fa(P,{size:14});var E=f(C,2),O=d(E);hr(O,{size:14});var _=f(E,2),M=d(_);hr(M,{size:14});var R=f(y,2),V=f(d(R),2);ze(V,21,()=>i,Me,(h,N)=>{var G=Gf(),K=d(G);L(()=>z(K,n(N))),j("click",G,()=>{r(a()?`${a().corpName||a().company||a().stockCode} ${n(N)}`:n(N))}),x(h,G)}),j("click",C,()=>{var h;return(h=t.onOpenExplorer)==null?void 0:h.call(t,"explore")}),j("click",E,()=>{var h;return(h=t.onOpenExplorer)==null?void 0:h.call(t,"overview")}),j("click",_,()=>{var h;return(h=t.onOpenExplorer)==null?void 0:h.call(t,"evidence")}),x(e,l),wn()}xa(["click"]);var Wf=b("<span><!></span>");function ps(e,t){yn(t,!0);let r=pt(t,"variant",3,"default");const a={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var i=Wf(),l=d(i);io(l,()=>t.children),L(s=>nt(i,1,s),[()=>rt(at("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",a[r()],t.class))]),x(e,i),wn()}var qf=b('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),Kf=b('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),Yf=b('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),Jf=b('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),Xf=b('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!></div></div>'),Qf=b('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),Zf=b('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),ep=b('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),tp=b('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),rp=b("<button><!> </button>"),np=b('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),ap=b('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),ip=b('<!> <span class="text-dl-text-dim"> </span>',1),lp=b('<div class="flex items-center gap-2 text-[11px]"><!></div>'),op=b('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),sp=b('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),dp=b('<div class="message-committed"><!></div>'),cp=b('<div><div class="message-live-label"> </div> <pre> </pre></div>'),up=b('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),vp=b('<span class="text-dl-accent/60"> </span>'),fp=b('<span class="text-dl-success/60"> </span>'),pp=b('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),xp=b('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),mp=b('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),bp=b('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),gp=b('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),hp=b("<!>  <div><!> <!></div> <!>",1),_p=b('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),yp=b('<span class="text-[10px] text-dl-text-dim"> </span>'),wp=b('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),kp=b("<button> </button>"),Cp=b('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),Sp=b("<button>시스템 프롬프트</button>"),Ep=b("<button>LLM 입력</button>"),Mp=b('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),zp=b('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),Ap=b('<span class="text-dl-text"> </span>'),Tp=b('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),Np=b('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),Op=b('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Ip=b("<!> <!>",1);function Lp(e,t){yn(t,!0);let r=F(null),a=F("context"),i=F("raw"),l=ne(()=>{var k,J,U,re,he,ge;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((k=t.message.toolEvents)==null?void 0:k.length)>0){const ee=[...t.message.toolEvents].reverse().find(xt=>xt.type==="call"),ct=((J=ee==null?void 0:ee.arguments)==null?void 0:J.module)||((U=ee==null?void 0:ee.arguments)==null?void 0:U.keyword)||"";return`도구 실행 중 — ${(ee==null?void 0:ee.name)||""}${ct?` (${ct})`:""}`}if(((re=t.message.contexts)==null?void 0:re.length)>0){const ee=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(ee==null?void 0:ee.label)||(ee==null?void 0:ee.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(he=t.message.meta)!=null&&he.company?`${t.message.meta.company} 데이터 검색 중`:(ge=t.message.meta)!=null&&ge.includedModules?"분석 모듈 선택 완료":"생각 중"}),s=ne(()=>{var k;return t.message.company||((k=t.message.meta)==null?void 0:k.company)||null}),c=ne(()=>{var k,J,U;return t.message.systemPrompt||t.message.userContent||((k=t.message.contexts)==null?void 0:k.length)>0||((J=t.message.meta)==null?void 0:J.includedModules)||((U=t.message.toolEvents)==null?void 0:U.length)>0}),v=ne(()=>{var J;const k=(J=t.message.meta)==null?void 0:J.dataYearRange;return k?typeof k=="string"?k:k.min_year&&k.max_year?`${k.min_year}~${k.max_year}년`:null:null});function m(k){if(!k)return 0;const J=(k.match(/[\uac00-\ud7af]/g)||[]).length,U=k.length-J;return Math.round(J*1.5+U/3.5)}function g(k){return k>=1e3?(k/1e3).toFixed(1)+"k":String(k)}let y=ne(()=>{var J;let k=0;if(t.message.systemPrompt&&(k+=m(t.message.systemPrompt)),t.message.userContent)k+=m(t.message.userContent);else if(((J=t.message.contexts)==null?void 0:J.length)>0)for(const U of t.message.contexts)k+=m(U.text);return k}),C=ne(()=>m(t.message.text));function P(k){const J=k.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(J)||J==="-"||J==="0"}function E(k){if(!k)return"";let J=[],U=[],re=k.replace(/```(\w*)\n([\s\S]*?)```/g,(ge,ee,ct)=>{const xt=J.length;return J.push(ct.trimEnd()),`
%%CODE_${xt}%%
`});re=re.replace(/((?:^\|.+\|$\n?)+)/gm,ge=>{const ee=ge.trim().split(`
`).filter(Ae=>Ae.trim());let ct=null,xt=-1,Dt=[];for(let Ae=0;Ae<ee.length;Ae++)if(ee[Ae].slice(1,-1).split("|").map(He=>He.trim()).every(He=>/^[\-:]+$/.test(He))){xt=Ae;break}xt>0?(ct=ee[xt-1],Dt=ee.slice(xt+1)):(xt===0||(ct=ee[0]),Dt=ee.slice(1));let ft="<table>";if(ct){const Ae=ct.slice(1,-1).split("|").map(De=>De.trim());ft+="<thead><tr>"+Ae.map(De=>`<th>${De.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(Dt.length>0){ft+="<tbody>";for(const Ae of Dt){const De=Ae.slice(1,-1).split("|").map(He=>He.trim());ft+="<tr>"+De.map(He=>{let Vt=He.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${P(He)?' class="num"':""}>${Vt}</td>`}).join("")+"</tr>"}ft+="</tbody>"}ft+="</table>";let cr=U.length;return U.push(ft),`
%%TABLE_${cr}%%
`});let he=re.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");he=he.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,ge=>"<ul>"+ge.replace(/<br>/g,"")+"</ul>");for(let ge=0;ge<U.length;ge++)he=he.replace(`%%TABLE_${ge}%%`,U[ge]);for(let ge=0;ge<J.length;ge++){const ee=J[ge].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");he=he.replace(`%%CODE_${ge}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${ge}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${ee}</code></pre></div>`)}return he=he.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(ge,ee)=>ee.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+he+"</p>"}let O=F(void 0);const _=/^\s*\|.+\|\s*$/;function M(k,J){if(!k)return{committed:"",draft:"",draftType:"none"};if(!J)return{committed:k,draft:"",draftType:"none"};const U=k.split(`
`);let re=U.length;k.endsWith(`
`)||(re=Math.min(re,U.length-1));let he=0,ge=-1;for(let ft=0;ft<U.length;ft++)U[ft].trim().startsWith("```")&&(he+=1,ge=ft);he%2===1&&ge>=0&&(re=Math.min(re,ge));let ee=-1;for(let ft=U.length-1;ft>=0;ft--){const cr=U[ft];if(!cr.trim())break;if(_.test(cr))ee=ft;else{ee=-1;break}}if(ee>=0&&(re=Math.min(re,ee)),re<=0)return{committed:"",draft:k,draftType:ee===0?"table":he%2===1?"code":"text"};const ct=U.slice(0,re).join(`
`),xt=U.slice(re).join(`
`);let Dt="text";return xt&&ee>=re?Dt="table":xt&&he%2===1&&(Dt="code"),{committed:ct,draft:xt,draftType:Dt}}const R='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',V='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function h(k){var he;const J=k.target.closest(".code-copy-btn");if(!J)return;const U=J.closest(".code-block-wrap"),re=((he=U==null?void 0:U.querySelector("code"))==null?void 0:he.textContent)||"";navigator.clipboard.writeText(re).then(()=>{J.innerHTML=V,setTimeout(()=>{J.innerHTML=R},2e3)})}function N(k){if(t.onOpenEvidence){t.onOpenEvidence("contexts",k);return}u(r,k,!0),u(a,"context"),u(i,"rendered")}function G(){if(t.onOpenEvidence){t.onOpenEvidence("system");return}u(r,0),u(a,"system"),u(i,"raw")}function K(){if(t.onOpenEvidence){t.onOpenEvidence("snapshot");return}u(r,0),u(a,"snapshot")}function S(k){var J;if(t.onOpenEvidence){const U=(J=t.message.toolEvents)==null?void 0:J[k];t.onOpenEvidence((U==null?void 0:U.type)==="result"?"tool-results":"tool-calls",k);return}u(r,k,!0),u(a,"tool"),u(i,"raw")}function W(){if(t.onOpenEvidence){t.onOpenEvidence("input");return}u(r,0),u(a,"userContent"),u(i,"raw")}function q(){u(r,null)}function _e(k){var J,U,re,he;return k?k.type==="call"?((J=k.arguments)==null?void 0:J.module)||((U=k.arguments)==null?void 0:U.keyword)||((re=k.arguments)==null?void 0:re.engine)||((he=k.arguments)==null?void 0:he.name)||"":typeof k.result=="string"?k.result.slice(0,120):k.result&&typeof k.result=="object"&&(k.result.module||k.result.status||k.result.name)||"":""}let et=ne(()=>(t.message.toolEvents||[]).filter(k=>k.type==="call")),me=ne(()=>(t.message.toolEvents||[]).filter(k=>k.type==="result")),ve=ne(()=>M(t.message.text||"",t.message.loading)),H=ne(()=>{var J,U,re;const k=[];return((U=(J=t.message.meta)==null?void 0:J.includedModules)==null?void 0:U.length)>0&&k.push({label:`모듈 ${t.message.meta.includedModules.length}개`,icon:hr}),((re=t.message.contexts)==null?void 0:re.length)>0&&k.push({label:`컨텍스트 ${t.message.contexts.length}건`,icon:co}),n(et).length>0&&k.push({label:`툴 호출 ${n(et).length}건`,icon:uo}),n(me).length>0&&k.push({label:`툴 결과 ${n(me).length}건`,icon:Ia}),t.message.systemPrompt&&k.push({label:"시스템 프롬프트",icon:Zi}),t.message.userContent&&k.push({label:"LLM 입력",icon:Ka}),k}),we=ne(()=>{var J,U,re;if(!t.message.loading)return[];const k=[];return(J=t.message.meta)!=null&&J.company&&k.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&k.push({label:"핵심 수치 확인",done:!0}),(U=t.message.meta)!=null&&U.includedModules&&k.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((re=t.message.contexts)==null?void 0:re.length)>0&&k.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&k.push({label:"프롬프트 조립",done:!0}),t.message.text?k.push({label:"응답 작성 중",done:!1}):k.push({label:n(l)||"준비 중",done:!1}),k});var Ye=Ip(),xe=Z(Ye);{var vt=k=>{var J=qf(),U=f(d(J),2),re=d(U),he=d(re);L(()=>z(he,t.message.text)),x(k,J)},Y=k=>{var J=_p(),U=f(d(J),2),re=d(U);{var he=Ae=>{var De=Xf(),He=d(De),Vt=d(He);nf(Vt,{size:11});var Wt=f(He,4),wt=d(Wt);{var kt=be=>{ps(be,{variant:"muted",children:(Je,At)=>{var Ft=an();L(()=>z(Ft,n(s))),x(Je,Ft)},$$slots:{default:!0}})};A(wt,be=>{n(s)&&be(kt)})}var ur=f(wt,2);{var Gt=be=>{ps(be,{variant:"accent",children:(Je,At)=>{var Ft=an();L(()=>z(Ft,n(v))),x(Je,Ft)},$$slots:{default:!0}})};A(ur,be=>{n(v)&&be(Gt)})}var Ct=f(ur,2);{var Xt=be=>{var Je=ye(),At=Z(Je);ze(At,17,()=>t.message.contexts,Me,(Ft,tr,rr)=>{var vr=Kf(),qr=d(vr);hr(qr,{size:10,class:"flex-shrink-0"});var Cn=f(qr);L(()=>z(Cn,` ${(n(tr).label||n(tr).module)??""}`)),j("click",vr,()=>N(rr)),x(Ft,vr)}),x(be,Je)},Fe=be=>{var Je=Yf(),At=d(Je);hr(At,{size:10,class:"flex-shrink-0"});var Ft=f(At);L(()=>z(Ft,` 모듈 ${t.message.meta.includedModules.length??""}개`)),x(be,Je)};A(Ct,be=>{var Je,At,Ft;((Je=t.message.contexts)==null?void 0:Je.length)>0?be(Xt):((Ft=(At=t.message.meta)==null?void 0:At.includedModules)==null?void 0:Ft.length)>0&&be(Fe,1)})}var mt=f(Ct,2);ze(mt,17,()=>n(H),Me,(be,Je)=>{var At=Jf(),Ft=d(At);Cu(Ft,()=>n(Je).icon,(rr,vr)=>{vr(rr,{size:10,class:"flex-shrink-0"})});var tr=f(Ft);L(()=>z(tr,` ${n(Je).label??""}`)),j("click",At,()=>{n(Je).label.startsWith("컨텍스트")?N(0):n(Je).label.startsWith("툴 호출")?t.onOpenEvidence?t.onOpenEvidence("tool-calls",0):S(0):n(Je).label.startsWith("툴 결과")?t.onOpenEvidence?t.onOpenEvidence("tool-results",0):S((t.message.toolEvents||[]).findIndex(rr=>rr.type==="result")):n(Je).label==="시스템 프롬프트"?G():n(Je).label==="LLM 입력"&&W()}),x(be,At)}),x(Ae,De)};A(re,Ae=>{var De,He;(n(s)||n(v)||((De=t.message.contexts)==null?void 0:De.length)>0||(He=t.message.meta)!=null&&He.includedModules||n(H).length>0)&&Ae(he)})}var ge=f(re,2);{var ee=Ae=>{var De=tp(),He=d(De);ze(He,21,()=>t.message.snapshot.items,Me,(wt,kt)=>{const ur=ne(()=>n(kt).status==="good"?"text-dl-success":n(kt).status==="danger"?"text-dl-primary-light":n(kt).status==="caution"?"text-amber-400":"text-dl-text");var Gt=Qf(),Ct=d(Gt),Xt=d(Ct),Fe=f(Ct,2),mt=d(Fe);L(be=>{z(Xt,n(kt).label),nt(Fe,1,be),z(mt,n(kt).value)},[()=>rt(at("text-[14px] font-semibold leading-snug mt-0.5",n(ur)))]),x(wt,Gt)});var Vt=f(He,2);{var Wt=wt=>{var kt=ep();ze(kt,21,()=>t.message.snapshot.warnings,Me,(ur,Gt)=>{var Ct=Zf(),Xt=d(Ct);Sf(Xt,{size:10});var Fe=f(Xt);L(()=>z(Fe,` ${n(Gt)??""}`)),x(ur,Ct)}),x(wt,kt)};A(Vt,wt=>{var kt;((kt=t.message.snapshot.warnings)==null?void 0:kt.length)>0&&wt(Wt)})}j("click",De,K),x(Ae,De)};A(ge,Ae=>{var De,He;((He=(De=t.message.snapshot)==null?void 0:De.items)==null?void 0:He.length)>0&&Ae(ee)})}var ct=f(ge,2);{var xt=Ae=>{var De=np(),He=d(De),Vt=f(d(He),4);ze(Vt,21,()=>t.message.toolEvents,Me,(Wt,wt,kt)=>{const ur=ne(()=>_e(n(wt)));var Gt=rp(),Ct=d(Gt);{var Xt=be=>{uo(be,{size:11})},Fe=be=>{Ia(be,{size:11})};A(Ct,be=>{n(wt).type==="call"?be(Xt):be(Fe,-1)})}var mt=f(Ct);L(be=>{nt(Gt,1,be),z(mt,` ${(n(wt).type==="call"?n(wt).name:`${n(wt).name} 결과`)??""}${n(ur)?`: ${n(ur)}`:""}`)},[()=>rt(at("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",n(wt).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),j("click",Gt,()=>S(kt)),x(Wt,Gt)}),x(Ae,De)};A(ct,Ae=>{var De;((De=t.message.toolEvents)==null?void 0:De.length)>0&&Ae(xt)})}var Dt=f(ct,2);{var ft=Ae=>{var De=op(),He=d(De);ze(He,21,()=>n(we),Me,(Vt,Wt)=>{var wt=lp(),kt=d(wt);{var ur=Ct=>{var Xt=ap(),Fe=f(Z(Xt),2),mt=d(Fe);L(()=>z(mt,n(Wt).label)),x(Ct,Xt)},Gt=Ct=>{var Xt=ip(),Fe=Z(Xt);Lr(Fe,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var mt=f(Fe,2),be=d(mt);L(()=>z(be,n(Wt).label)),x(Ct,Xt)};A(kt,Ct=>{n(Wt).done?Ct(ur):Ct(Gt,-1)})}x(Vt,wt)}),x(Ae,De)},cr=Ae=>{var De=hp(),He=Z(De);{var Vt=Fe=>{var mt=sp(),be=d(mt);Lr(be,{size:12,class:"animate-spin flex-shrink-0"});var Je=f(be,2),At=d(Je);L(()=>z(At,n(l))),x(Fe,mt)};A(He,Fe=>{t.message.loading&&Fe(Vt)})}var Wt=f(He,2),wt=d(Wt);{var kt=Fe=>{var mt=dp(),be=d(mt);Uo(be,()=>E(n(ve).committed)),x(Fe,mt)};A(wt,Fe=>{n(ve).committed&&Fe(kt)})}var ur=f(wt,2);{var Gt=Fe=>{var mt=cp(),be=d(mt),Je=d(be),At=f(be,2),Ft=d(At);L(tr=>{nt(mt,1,tr),z(Je,n(ve).draftType==="table"?"표 구성 중":n(ve).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),z(Ft,n(ve).draft)},[()=>rt(at("message-live-tail",n(ve).draftType==="table"&&"message-draft-table",n(ve).draftType==="code"&&"message-draft-code"))]),x(Fe,mt)};A(ur,Fe=>{n(ve).draft&&Fe(Gt)})}ua(Wt,Fe=>u(O,Fe),()=>n(O));var Ct=f(Wt,2);{var Xt=Fe=>{var mt=gp(),be=d(mt);{var Je=Pt=>{var it=up(),fr=d(it);sf(fr,{size:10});var X=f(fr);L(()=>z(X,` ${t.message.duration??""}초`)),x(Pt,it)};A(be,Pt=>{t.message.duration&&Pt(Je)})}var At=f(be,2);{var Ft=Pt=>{var it=pp(),fr=d(it);{var X=ot=>{var ht=vp(),pr=d(ht);L(nr=>z(pr,`↑${nr??""}`),[()=>g(n(y))]),x(ot,ht)};A(fr,ot=>{n(y)>0&&ot(X)})}var Ne=f(fr,2);{var bt=ot=>{var ht=fp(),pr=d(ht);L(nr=>z(pr,`↓${nr??""}`),[()=>g(n(C))]),x(ot,ht)};A(Ne,ot=>{n(C)>0&&ot(bt)})}x(Pt,it)};A(At,Pt=>{(n(y)>0||n(C)>0)&&Pt(Ft)})}var tr=f(At,2);{var rr=Pt=>{var it=xp(),fr=d(it);gf(fr,{size:10}),j("click",it,()=>{var X;return(X=t.onRegenerate)==null?void 0:X.call(t)}),x(Pt,it)};A(tr,Pt=>{t.onRegenerate&&Pt(rr)})}var vr=f(tr,2);{var qr=Pt=>{var it=mp(),fr=d(it);Zi(fr,{size:10}),j("click",it,G),x(Pt,it)};A(vr,Pt=>{t.message.systemPrompt&&Pt(qr)})}var Cn=f(vr,2);{var Xn=Pt=>{var it=bp(),fr=d(it);Ka(fr,{size:10});var X=f(fr);L((Ne,bt)=>z(X,` LLM 입력 (${Ne??""}자 · ~${bt??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>g(m(t.message.userContent))]),j("click",it,W),x(Pt,it)};A(Cn,Pt=>{t.message.userContent&&Pt(Xn)})}x(Fe,mt)};A(Ct,Fe=>{!t.message.loading&&(t.message.duration||n(c)||t.onRegenerate)&&Fe(Xt)})}L(Fe=>nt(Wt,1,Fe),[()=>rt(at("prose-dartlab message-body text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),j("click",Wt,h),x(Ae,De)};A(Dt,Ae=>{t.message.loading&&!t.message.text?Ae(ft):Ae(cr,-1)})}x(k,J)};A(xe,k=>{t.message.role==="user"?k(vt):k(Y,-1)})}var zt=f(xe,2);{var Ce=k=>{const J=ne(()=>n(a)==="system"),U=ne(()=>n(a)==="userContent"),re=ne(()=>n(a)==="context"),he=ne(()=>n(a)==="snapshot"),ge=ne(()=>n(a)==="tool"),ee=ne(()=>{var X;return n(re)?(X=t.message.contexts)==null?void 0:X[n(r)]:null}),ct=ne(()=>{var X;return n(ge)?(X=t.message.toolEvents)==null?void 0:X[n(r)]:null}),xt=ne(()=>{var X,Ne,bt,ot,ht;return n(he)?"핵심 수치 (원본 데이터)":n(J)?"시스템 프롬프트":n(U)?"LLM에 전달된 입력":n(ge)?((X=n(ct))==null?void 0:X.type)==="call"?`${(Ne=n(ct))==null?void 0:Ne.name} 호출`:`${(bt=n(ct))==null?void 0:bt.name} 결과`:((ot=n(ee))==null?void 0:ot.label)||((ht=n(ee))==null?void 0:ht.module)||""}),Dt=ne(()=>{var X;return n(he)?JSON.stringify(t.message.snapshot,null,2):n(J)?t.message.systemPrompt:n(U)?t.message.userContent:n(ge)?JSON.stringify(n(ct),null,2):(X=n(ee))==null?void 0:X.text});var ft=Op(),cr=d(ft),Ae=d(cr),De=d(Ae),He=d(De),Vt=d(He);{var Wt=X=>{hr(X,{size:15,class:"text-dl-success flex-shrink-0"})},wt=X=>{Zi(X,{size:15,class:"text-dl-primary-light flex-shrink-0"})},kt=X=>{Ka(X,{size:15,class:"text-dl-accent flex-shrink-0"})},ur=X=>{hr(X,{size:15,class:"flex-shrink-0"})};A(Vt,X=>{n(he)?X(Wt):n(J)?X(wt,1):n(U)?X(kt,2):X(ur,-1)})}var Gt=f(Vt,2),Ct=d(Gt),Xt=f(Gt,2);{var Fe=X=>{var Ne=yp(),bt=d(Ne);L(ot=>z(bt,`(${ot??""}자)`),[()=>{var ot,ht;return(ht=(ot=n(Dt))==null?void 0:ot.length)==null?void 0:ht.toLocaleString()}]),x(X,Ne)};A(Xt,X=>{n(J)&&X(Fe)})}var mt=f(He,2),be=d(mt);{var Je=X=>{var Ne=wp(),bt=d(Ne),ot=d(bt);Ka(ot,{size:11});var ht=f(bt,2),pr=d(ht);df(pr,{size:11}),L((nr,Er)=>{nt(bt,1,nr),nt(ht,1,Er)},[()=>rt(at("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(i)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>rt(at("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(i)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),j("click",bt,()=>u(i,"rendered")),j("click",ht,()=>u(i,"raw")),x(X,Ne)};A(be,X=>{n(re)&&X(Je)})}var At=f(be,2),Ft=d(At);Ja(Ft,{size:18});var tr=f(De,2);{var rr=X=>{var Ne=Cp(),bt=d(Ne);ze(bt,21,()=>t.message.contexts,Me,(ot,ht,pr)=>{var nr=kp(),Er=d(nr);L(Pr=>{nt(nr,1,Pr),z(Er,t.message.contexts[pr].label||t.message.contexts[pr].module)},[()=>rt(at("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",pr===n(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),j("click",nr,()=>{u(r,pr,!0)}),x(ot,nr)}),x(X,Ne)};A(tr,X=>{var Ne;n(re)&&((Ne=t.message.contexts)==null?void 0:Ne.length)>1&&X(rr)})}var vr=f(tr,2);{var qr=X=>{var Ne=Mp(),bt=d(Ne),ot=d(bt);{var ht=Er=>{var Pr=Sp();L(Bn=>nt(Pr,1,Bn),[()=>rt(at("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(J)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),j("click",Pr,()=>{u(a,"system")}),x(Er,Pr)};A(ot,Er=>{t.message.systemPrompt&&Er(ht)})}var pr=f(ot,2);{var nr=Er=>{var Pr=Ep();L(Bn=>nt(Pr,1,Bn),[()=>rt(at("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(U)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),j("click",Pr,()=>{u(a,"userContent")}),x(Er,Pr)};A(pr,Er=>{t.message.userContent&&Er(nr)})}x(X,Ne)};A(vr,X=>{!n(re)&&!n(he)&&!n(ge)&&X(qr)})}var Cn=f(Ae,2),Xn=d(Cn);{var Pt=X=>{var Ne=zp(),bt=d(Ne);Uo(bt,()=>{var ot;return E((ot=n(ee))==null?void 0:ot.text)}),x(X,Ne)},it=X=>{var Ne=Tp(),bt=d(Ne),ot=f(d(bt),2),ht=d(ot),pr=f(ht);{var nr=Sn=>{var un=Ap(),ba=d(un);L(Va=>z(ba,Va),[()=>_e(n(ct))]),x(Sn,un)},Er=ne(()=>_e(n(ct)));A(pr,Sn=>{n(Er)&&Sn(nr)})}var Pr=f(bt,2),Bn=d(Pr);L(()=>{var Sn;z(ht,`${((Sn=n(ct))==null?void 0:Sn.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),z(Bn,n(Dt))}),x(X,Ne)},fr=X=>{var Ne=Np(),bt=d(Ne);L(()=>z(bt,n(Dt))),x(X,Ne)};A(Xn,X=>{n(re)&&n(i)==="rendered"?X(Pt):n(ge)?X(it,1):X(fr,-1)})}L(()=>z(Ct,n(xt))),j("click",ft,X=>{X.target===X.currentTarget&&q()}),j("keydown",ft,X=>{X.key==="Escape"&&q()}),j("click",At,q),x(k,ft)};A(zt,k=>{n(r)!==null&&k(Ce)})}x(e,Ye),wn()}xa(["click","keydown"]);var Pp=b('<div class="surface-panel flex flex-wrap items-center gap-2 rounded-2xl border border-dl-primary/20 bg-dl-primary/[0.05] px-4 py-3"><div class="flex items-center gap-2 text-[12px] text-dl-text"><!> <span class="font-medium"> </span> <span class="text-dl-text-dim"> </span></div> <div class="flex flex-wrap gap-1.5 ml-auto"><button class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> Overview</button> <button class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> Explore</button> <button class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> Evidence</button></div></div>'),Rp=b('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),jp=b('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),Dp=b('<div class="flex justify-end gap-2 mb-1.5"><button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 탐색</button> <button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 근거</button> <!></div>'),Fp=b('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-14 pb-10 space-y-8"><!> <!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function Bp(e,t){yn(t,!0);function r(me){if(i())return!1;for(let ve=a().length-1;ve>=0;ve--)if(a()[ve].role==="assistant"&&!a()[ve].error&&a()[ve].text)return ve===me;return!1}let a=pt(t,"messages",19,()=>[]),i=pt(t,"isLoading",3,!1),l=pt(t,"inputText",15,""),s=pt(t,"scrollTrigger",3,0),c=pt(t,"selectedCompany",3,null),v,m,g=F(!0),y=F(!1),C=F(!0);function P(){if(!v)return;const{scrollTop:me,scrollHeight:ve,clientHeight:H}=v;u(C,ve-me-H<96),n(C)?(u(g,!0),u(y,!1)):(u(g,!1),u(y,!0))}function E(me="smooth"){m&&(m.scrollIntoView({block:"end",behavior:me}),u(g,!0),u(y,!1))}ln(()=>{s(),!(!v||!m)&&requestAnimationFrame(()=>{!v||!m||(n(g)||n(C)?(m.scrollIntoView({block:"end",behavior:i()?"auto":"smooth"}),u(y,!1)):u(y,!0))})});var O=Fp(),_=d(O),M=d(_),R=d(M);{var V=me=>{var ve=Pp(),H=d(ve),we=d(H);hr(we,{size:13,class:"text-dl-primary-light"});var Ye=f(we,2),xe=d(Ye),vt=f(Ye,2),Y=d(vt),zt=f(H,2),Ce=d(zt),k=d(Ce);hr(k,{size:10,class:"inline mr-1"});var J=f(Ce,2),U=d(J);Fa(U,{size:10,class:"inline mr-1"});var re=f(J,2),he=d(re);hr(he,{size:10,class:"inline mr-1"}),L(()=>{z(xe,c().corpName||c().company||"선택된 회사"),z(Y,c().stockCode)}),j("click",Ce,()=>{var ge;return(ge=t.onOpenExplorer)==null?void 0:ge.call(t,"overview")}),j("click",J,()=>{var ge;return(ge=t.onOpenExplorer)==null?void 0:ge.call(t,"explore")}),j("click",re,()=>{var ge;return(ge=t.onOpenExplorer)==null?void 0:ge.call(t,"evidence")}),x(me,ve)};A(R,me=>{c()&&me(V)})}var h=f(R,2);ze(h,17,a,Me,(me,ve,H)=>{{let we=ne(()=>r(H)?t.onRegenerate:void 0);Lp(me,{get message(){return n(ve)},get onRegenerate(){return n(we)},get onOpenEvidence(){return t.onOpenEvidence}})}});var N=f(h,2);ua(N,me=>m=me,()=>m),ua(_,me=>v=me,()=>v);var G=f(_,2);{var K=me=>{var ve=Rp(),H=d(ve);j("click",H,()=>E("smooth")),x(me,ve)};A(G,me=>{n(y)&&me(K)})}var S=f(G,2),W=d(S),q=d(W);{var _e=me=>{var ve=Dp(),H=d(ve),we=d(H);Fa(we,{size:10});var Ye=f(H,2),xe=d(Ye);hr(xe,{size:10});var vt=f(Ye,2);{var Y=zt=>{var Ce=jp(),k=d(Ce);La(k,{size:10}),j("click",Ce,function(...J){var U;(U=t.onExport)==null||U.apply(this,J)}),x(zt,Ce)};A(vt,zt=>{a().length>1&&t.onExport&&zt(Y)})}j("click",H,()=>{var zt;return(zt=t.onOpenExplorer)==null?void 0:zt.call(t,"explore")}),j("click",Ye,()=>{var zt;return(zt=t.onOpenExplorer)==null?void 0:zt.call(t,"evidence")}),x(me,ve)};A(q,me=>{i()||me(_e)})}var et=f(q,2);Id(et,{get isLoading(){return i()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get inputText(){return l()},set inputText(me){l(me)}}),tl("scroll",_,P),x(e,O),wn()}xa(["click"]);var $p=b('<button class="rounded-lg p-1.5 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text" aria-label="워크스페이스 닫기"><!></button>'),Vp=b('<button class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors hover:bg-white/[0.04]"><div class="flex h-8 w-8 items-center justify-center rounded-lg bg-dl-primary/10 text-[11px] font-semibold text-dl-primary-light"> </div> <div class="min-w-0 flex-1"><div class="truncate text-[12px] font-medium text-dl-text"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></button>'),Gp=b('<div class="mt-2 space-y-1 rounded-xl border border-dl-border/50 bg-dl-bg-darker/95 p-1"></div>'),Hp=b('<div class="mt-3 rounded-2xl border border-dl-primary/20 bg-dl-primary/[0.05] p-3"><div class="flex items-start justify-between gap-3"><div class="min-w-0"><div class="text-[13px] font-semibold text-dl-text"> </div> <div class="mt-0.5 text-[10px] text-dl-text-dim"> <!> <!></div></div> <button class="rounded-lg px-2 py-1 text-[10px] text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text">초기화</button></div> <div class="mt-2 flex gap-2"><button class="rounded-lg border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button> <button class="rounded-lg border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> 새로고침</button></div></div>'),Up=b('<button class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"> </button>'),Wp=b('<div class="mt-3 rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-3"><div class="mb-2 text-[11px] font-medium text-dl-text">최근 본 회사</div> <div class="flex flex-wrap gap-1.5"></div></div>'),qp=b('<div class="mt-3 grid grid-cols-3 gap-2"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2"><div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">View</div> <div class="mt-1 text-[12px] font-medium text-dl-text"> </div></div> <div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2"><div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">Modules</div> <div class="mt-1 text-[12px] font-medium text-dl-text"> </div></div> <div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2"><div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">Selected</div> <div class="mt-1 text-[12px] font-medium text-dl-text"> </div></div></div> <div class="mt-3 grid grid-cols-2 gap-2"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2"><div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">Schema</div> <div class="mt-1 text-[12px] font-medium text-dl-text">표준화 계정 비교</div></div> <div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2"><div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">Evidence</div> <div class="mt-1 text-[12px] font-medium text-dl-text">원문 근거 보존</div></div></div>',1),Kp=b("<div> </div>"),Yp=b('<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center"><!> <div class="text-[13px] font-medium text-dl-text">회사별 워크스페이스 준비</div> <div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">회사를 먼저 선택하면 추후 대시보드가 들어갈 Overview 슬롯과 추천 모듈 요약을 바로 볼 수 있습니다.</div></div>'),Jp=b('<div class="mt-3 space-y-2"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[82%]"></div> <div class="skeleton-line w-[68%]"></div></div>'),Xp=b('<div class="rounded-xl bg-dl-bg-card/60 p-3"><div class="text-[10px] text-dl-text-dim"> </div> <div class="mt-1 text-[13px] font-semibold text-dl-text"> </div> <div class="mt-1 text-[9px] text-dl-text-dim"> </div></div>'),Qp=b('<div class="mt-2 text-[10px] text-dl-text-dim"> </div>'),Zp=b('<div class="flex flex-1 flex-col items-center gap-1"><div class="w-full rounded-t-md bg-gradient-to-t from-dl-primary to-dl-accent transition-all"></div> <div class="text-[9px] text-dl-text-dim"> </div></div>'),ex=b('<div class="mt-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/50 p-3"><div class="mb-2 text-[10px] uppercase tracking-wide text-dl-text-dim">매출 추세</div> <div class="flex items-end gap-2"></div></div>'),tx=b('<div class="mt-3 grid grid-cols-2 gap-2"></div> <!> <!>',1),rx=b('<div class="mt-2 text-[11px] leading-relaxed text-dl-text-dim">핵심 재무 카드를 자동으로 만들 수 있는 시계열 데이터가 부족합니다. Explore에서 원본 모듈을 먼저 확인하는 흐름이 적합합니다.</div>'),nx=b('<div class="mt-3 rounded-xl border border-dl-primary/20 bg-dl-primary/[0.05] px-3 py-2 text-[10px] text-dl-primary-light"> </div>'),ax=b('<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/40 px-3 py-2 text-[11px] leading-relaxed text-dl-text-muted"> </div>'),ix=b('<div class="rounded-xl bg-dl-bg-card/50 px-3 py-2 text-[11px] text-dl-text-muted"> </div>'),lx=b('<button class="w-full rounded-xl border border-dl-border/50 bg-dl-bg-card/40 p-3 text-left transition-colors hover:border-dl-primary/30 hover:bg-white/[0.02]"><div class="text-[11px] font-medium text-dl-text"> </div> <div class="mt-1 text-[10px] leading-relaxed text-dl-text-dim"> </div></button>'),ox=b('<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 text-[12px] font-medium text-dl-text">추천 액션</div> <div class="space-y-2"></div></div>'),sx=b('<button class="w-full rounded-xl border border-dl-border/50 bg-dl-bg-card/40 p-3 text-left transition-colors hover:border-dl-primary/30 hover:bg-white/[0.02]"><div class="flex items-center justify-between gap-3"><div class="min-w-0"><div class="truncate text-[12px] font-medium text-dl-text"> </div> <div class="mt-0.5 text-[10px] text-dl-text-dim"> </div></div> <span class="rounded-full bg-dl-primary/10 px-2 py-0.5 text-[9px] text-dl-primary-light"> </span></div></button>'),dx=b('<div class="space-y-3"><div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="flex items-start justify-between gap-3"><div><div class="text-[14px] font-semibold text-dl-text"> </div> <div class="mt-1 text-[10px] text-dl-text-dim"> <!> <!></div></div> <span class="rounded-full bg-dl-primary/10 px-2 py-0.5 text-[9px] text-dl-primary-light">Overview</span></div> <div class="mt-3 grid grid-cols-2 gap-2"><div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/80 p-3"><div class="text-[10px] text-dl-text-dim">사용 가능 데이터</div> <div class="mt-1 text-[22px] font-semibold text-dl-text"> </div></div> <div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/80 p-3"><div class="text-[10px] text-dl-text-dim">활성 카테고리</div> <div class="mt-1 text-[22px] font-semibold text-dl-text"> </div></div></div></div> <div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="flex items-center gap-2 text-[12px] font-medium text-dl-text"><!> 핵심 재무 카드</div> <!> <!></div> <div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 text-[12px] font-medium text-dl-text">Overview 노트</div> <div class="space-y-2"></div></div> <div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 text-[12px] font-medium text-dl-text">읽기 포인트</div> <div class="space-y-2"></div></div> <!> <div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 text-[12px] font-medium text-dl-text">추천 모듈</div> <div class="space-y-2"></div></div> <div class="flex gap-2"><button class="flex-1 rounded-xl bg-dl-primary/20 px-3 py-2 text-[11px] font-medium text-dl-primary-light transition-colors hover:bg-dl-primary/30">모듈 탐색</button> <button class="flex-1 rounded-xl border border-dl-border/60 px-3 py-2 text-[11px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-text">현재 근거 보기</button></div></div>'),cx=b('<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center"><!> <div class="text-[13px] font-medium text-dl-text">아직 연결된 응답이 없습니다</div> <div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">채팅을 시작하면 이 패널에서 스냅샷, 사용한 모듈, 도구 호출, 시스템 프롬프트 요약을 함께 확인할 수 있습니다.</div></div>'),ux=b('<div><div class="text-[10px] text-dl-text-dim"> </div> <div class="mt-1 text-[18px] font-semibold text-dl-text"> </div></div>'),vx=b('<div class="grid grid-cols-2 gap-2"></div>'),fx=b('<span class="rounded-full bg-dl-primary/10 px-2 py-1 text-[10px] text-dl-primary-light"> </span>'),px=b('<span class="rounded-full bg-dl-bg-card px-2 py-1 text-[10px] text-dl-text-muted"> </span>'),xx=b('<span class="rounded-full bg-dl-bg-card px-2 py-1 text-[10px] text-dl-text-muted"> </span>'),mx=b('<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="text-[12px] font-medium text-dl-text">현재 답변 컨텍스트</div> <div class="mt-2 flex flex-wrap gap-1.5"><!> <!> <!></div></div>'),bx=b('<div class="rounded-xl bg-dl-bg-card/60 p-2.5"><div class="text-[10px] text-dl-text-dim"> </div> <div class="mt-1 text-[12px] font-semibold text-dl-text"> </div></div>'),gx=b('<button data-evidence-section="snapshot" class="block w-full rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4 text-left transition-colors hover:border-dl-primary/25 hover:bg-dl-bg-darker/85"><div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text"><!> 핵심 수치</div> <div class="grid grid-cols-2 gap-2"></div></button>'),hx=b('<button class="w-full rounded-xl bg-dl-bg-card/50 p-3 text-left transition-colors hover:bg-dl-bg-card/70"><div class="flex items-center justify-between gap-2"><div class="text-[11px] font-medium text-dl-text"> </div> <span class="inline-flex items-center gap-1 text-[10px] text-dl-primary-light"><!> 상세</span></div> <div class="mt-1 line-clamp-3 text-[10px] leading-relaxed text-dl-text-dim"> </div></button>'),_x=b('<div class="mb-2 rounded-xl border border-dl-border/40 bg-dl-bg-card/35 px-3 py-2 text-[10px] leading-relaxed text-dl-text-dim">이 답변에 직접 투입된 원문/구조화 데이터입니다. 각 카드를 누르면 전문을 확인할 수 있습니다.</div> <div class="space-y-2"></div>',1),yx=b('<div class="text-[11px] text-dl-text-dim">표시할 컨텍스트 데이터가 없습니다.</div>'),wx=b('<button class="flex w-full items-center justify-between gap-3 rounded-xl bg-dl-bg-card/50 px-3 py-2 text-left text-[10px] text-dl-text-muted transition-colors hover:bg-dl-bg-card/70"><span> <!> <!></span> <span class="inline-flex items-center gap-1 text-dl-primary-light"><!> JSON</span></button>'),kx=b('<div class="space-y-1.5"></div>'),Cx=b('<div class="text-[11px] text-dl-text-dim">도구 호출 기록이 없습니다.</div>'),Sx=b('<button class="flex w-full items-center justify-between gap-3 rounded-xl bg-dl-bg-card/50 px-3 py-2 text-left text-[10px] text-dl-text-muted transition-colors hover:bg-dl-bg-card/70"><span class="min-w-0 flex-1 truncate"> <!></span> <span class="inline-flex items-center gap-1 text-dl-success"><!> 상세</span></button>'),Ex=b('<div class="mb-2 rounded-xl border border-dl-border/40 bg-dl-bg-card/35 px-3 py-2 text-[10px] leading-relaxed text-dl-text-dim">LLM이 받은 실제 툴 결과입니다. 요약만 보지 말고 상세를 열어 반환 구조를 검증할 수 있습니다.</div> <div class="space-y-1.5"></div>',1),Mx=b('<div class="text-[11px] text-dl-text-dim">도구 결과 기록이 없습니다.</div>'),zx=b('<button data-evidence-section="system" class="mb-2 block w-full rounded-xl bg-dl-bg-card/50 p-3 text-left transition-colors hover:bg-dl-bg-card/70"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">System</div> <div class="line-clamp-4 text-[10px] leading-relaxed text-dl-text-muted"> </div></button>'),Ax=b('<button data-evidence-section="input" class="block w-full rounded-xl bg-dl-bg-card/50 p-3 text-left transition-colors hover:bg-dl-bg-card/70"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">LLM Input</div> <div class="line-clamp-4 text-[10px] leading-relaxed text-dl-text-muted"> </div></button>'),Tx=b('<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text"><!> 프롬프트 투명성</div> <!> <!></div>'),Nx=b('<div class="space-y-3"><!> <!> <!> <div data-evidence-section="contexts" class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text"><!> 근거 모듈</div> <!></div> <div data-evidence-section="tool-calls" class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text"><!> 도구 호출</div> <!></div> <div data-evidence-section="tool-results" class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text"><!> 도구 결과</div> <!></div> <!></div>'),Ox=b('<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center"><!> <div class="text-[13px] font-medium text-dl-text">회사를 선택하면 탐색이 시작됩니다</div> <div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">채팅 없이도 검색 후 모듈을 열어 표, 요약, 텍스트를 직접 확인할 수 있습니다.</div></div>'),Ix=b('<button class="rounded-full bg-dl-primary/10 px-2.5 py-1 text-[10px] text-dl-primary-light"> </button>'),Lx=b('<div class="mb-3 flex flex-wrap gap-1.5 rounded-xl border border-dl-border/40 bg-dl-bg-card/40 p-2"><!> <button class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text">선택 해제</button></div>'),Px=b('<div class="rounded-xl border border-dl-primary/20 bg-dl-primary/[0.05] px-3 py-2 text-[10px] text-dl-primary-light"> </div>'),Rx=b('<div class="flex items-center gap-2 py-4 text-[11px] text-dl-text-dim"><!> 모듈 목록을 불러오는 중...</div>'),jx=b('<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/30 px-3 py-4 text-[11px] text-dl-text-dim">필터와 일치하는 모듈이 없습니다.</div>'),Dx=b('<button type="button">✓</button>'),Fx=b('<span class="h-4 w-4 flex-shrink-0"></span>'),Bx=b('<div><!> <button type="button" class="flex min-w-0 flex-1 items-center gap-2 text-left"><!> <div class="min-w-0 flex-1"><div class="truncate text-[11px] font-medium text-dl-text"> </div> <div class="mt-0.5 text-[10px] text-dl-text-dim"> </div></div></button></div>'),$x=b('<div class="space-y-1 border-t border-dl-border/30 px-2 pb-2 pt-1"></div>'),Vx=b('<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/30"><button class="flex w-full items-start gap-2 px-3 py-2.5 text-left"><!> <div class="min-w-0 flex-1"><div class="flex items-center justify-between gap-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[9px] text-dl-text-dim"> </span></div> <div class="mt-0.5 text-[10px] leading-relaxed text-dl-text-dim"> </div></div></button> <!></div>'),Gx=b('<div class="p-4 text-center"><!> <div class="text-[13px] font-medium text-dl-text">모듈을 선택하세요</div> <div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">선택한 모듈은 표 미리보기와 함께 질문으로 이어갈 수 있습니다.</div></div>'),Hx=b('<div class="flex items-center gap-2 p-4 text-[11px] text-dl-text-dim"><!> </div>'),Ux=b("<button><!> </button>"),Wx=b('<span class="rounded-full bg-dl-bg-card px-2 py-1 text-[9px] text-dl-text-muted"> </span>'),qx=b('<th class="min-w-[96px] border-b border-dl-border/30 bg-dl-bg-darker px-3 py-2 text-right text-[10px] font-medium text-dl-text-muted"> </th>'),Kx=b("<td> </td>"),Yx=b('<tr class="hover:bg-white/[0.02]"><td> </td><!></tr>'),Jx=b('<div class="max-h-[360px] overflow-auto"><table class="w-full border-collapse text-[11px]"><thead class="sticky top-0 z-[5]"><tr><th class="sticky left-0 z-[6] min-w-[180px] border-b border-r border-dl-border/30 bg-dl-bg-darker px-3 py-2 text-left text-[10px] font-medium text-dl-text-muted">계정명</th><!></tr></thead><tbody></tbody></table></div>'),Xx=b('<th class="border-b border-dl-border/30 bg-dl-bg-darker px-3 py-2 text-left text-[10px] font-medium text-dl-text-muted"> </th>'),Qx=b("<td> </td>"),Zx=b('<tr class="hover:bg-white/[0.02]"></tr>'),em=b('<div class="max-h-[360px] overflow-auto"><table class="w-full border-collapse text-[11px]"><thead class="sticky top-0 z-[5]"><tr></tr></thead><tbody></tbody></table></div>'),tm=b('<div class="rounded-xl bg-dl-bg-card/50 px-3 py-2"><div class="text-[10px] text-dl-text-dim"> </div> <div class="mt-1 text-[11px] text-dl-text-muted"> </div></div>'),rm=b('<div class="space-y-1.5 p-4"></div>'),nm=b('<div class="text-[11px] leading-relaxed text-dl-text-muted"> </div>'),am=b('<div class="mb-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/45 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">핵심 문장</div> <div class="space-y-2"></div></div>'),im=b('<div class="p-4"><!> <pre class="whitespace-pre-wrap text-[11px] leading-relaxed text-dl-text-muted"> </pre></div>'),lm=b('<div class="p-4 text-[11px] text-dl-primary-light"> </div>'),om=b('<div class="p-4"><pre class="whitespace-pre-wrap text-[11px] text-dl-text-muted"> </pre></div>'),sm=b('<div class="border-b border-dl-border/40 px-4 py-3"><div class="flex items-start justify-between gap-3"><div class="min-w-0"><div class="text-[13px] font-medium text-dl-text"> </div> <div class="mt-1 text-[10px] leading-relaxed text-dl-text-dim"> </div></div> <div class="flex items-center gap-1.5"><!> <button class="rounded-lg bg-dl-success/10 px-2 py-1 text-[10px] text-dl-success transition-colors hover:bg-dl-success/20"><!> Excel</button></div></div> <div class="mt-3 flex flex-wrap gap-1.5"></div> <div class="mt-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/50 p-3"><div class="text-[10px] uppercase tracking-wide text-dl-text-dim">추천 질문</div> <div class="mt-1 text-[11px] leading-relaxed text-dl-text-muted"> </div> <button class="mt-3 rounded-lg bg-dl-primary/20 px-3 py-1.5 text-[11px] font-medium text-dl-primary-light transition-colors hover:bg-dl-primary/30">이 데이터로 질문하기</button></div></div> <!>',1),dm=b('<div class="space-y-3"><div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2"><div class="flex items-center justify-between gap-2"><div><div class="text-[12px] font-medium text-dl-text">데이터 탐색</div> <div class="mt-0.5 text-[10px] text-dl-text-dim">카테고리를 열고 모듈을 선택하면 우측에서 바로 미리볼 수 있습니다.</div></div> <div class="rounded-full bg-dl-primary/10 px-2.5 py-1 text-[9px] text-dl-primary-light"> </div></div></div> <div class="sticky top-0 z-[8] mb-3 rounded-xl border border-dl-border/50 bg-dl-bg-card/92 px-3 py-2 backdrop-blur-sm"><div><div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Download Actions</div> <div class="mt-1 text-[11px] text-dl-text-muted"> </div></div> <div class="mt-2 flex items-center gap-2"><button class="flex items-center gap-1 rounded-lg border border-dl-border/50 px-2.5 py-1.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text disabled:opacity-40"><!> 선택 다운로드</button> <button class="rounded-lg border border-dl-border/50 px-2.5 py-1.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text disabled:opacity-40">선택 해제</button> <button class="flex items-center gap-1 rounded-lg bg-dl-success/10 px-2.5 py-1.5 text-[10px] text-dl-success transition-colors hover:bg-dl-success/20 disabled:opacity-40"><!> 전체 Excel</button></div></div> <!> <div class="space-y-2"><div class="relative"><!> <input type="text" placeholder="모듈 이름 또는 설명 필터" class="w-full rounded-xl border border-dl-border bg-dl-bg-card/50 py-2 pl-8 pr-3 text-[11px] text-dl-text outline-none transition-colors placeholder:text-dl-text-dim focus:border-dl-primary/40"/></div> <!> <!></div></div> <div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70"><!></div></div>'),cm=b('<div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4"><pre class="whitespace-pre-wrap text-[11px] leading-relaxed text-dl-text-muted"> </pre></div>'),um=b('<pre class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4 text-[11px] leading-relaxed text-dl-text-muted"> </pre>'),vm=b('<pre class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4 text-[11px] leading-relaxed text-dl-text-muted"> </pre>'),fm=b('<div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4"><pre class="whitespace-pre-wrap text-[11px] leading-relaxed text-dl-text-muted"> </pre></div>'),pm=b('<div class="fixed inset-0 z-[320] flex items-center justify-center bg-black/60 px-4 backdrop-blur-sm" role="presentation"><div class="max-h-[80vh] w-full max-w-2xl overflow-hidden rounded-2xl border border-dl-border bg-dl-bg-card shadow-2xl shadow-black/30" role="dialog" aria-modal="true" aria-labelledby="workspace-detail-title" tabindex="-1"><div class="flex items-center justify-between border-b border-dl-border/50 px-5 py-4"><div><div id="workspace-detail-title" class="text-[14px] font-semibold text-dl-text"> </div> <div class="mt-1 text-[10px] uppercase tracking-[0.16em] text-dl-text-dim"> </div></div> <button class="rounded-lg p-1.5 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text" aria-label="상세 데이터 닫기"><!></button></div> <div class="max-h-[calc(80vh-76px)] overflow-y-auto p-5"><!></div></div></div>'),xm=b('<div class="surface-panel flex h-full min-h-0 flex-col bg-dl-bg-card/92 backdrop-blur-sm"><div class="border-b border-dl-border/60 px-4 py-3"><div class="flex items-center justify-between gap-3"><div class="min-w-0"><div class="flex items-center gap-2 text-[14px] font-semibold text-dl-text"><!> <span>Workspace</span></div> <div class="mt-0.5 text-[11px] text-dl-text-dim">표준화된 계정, 서술형 텍스트, 원문 근거를 한 화면에서 검증하는 분석 워크벤치</div></div> <!></div> <div class="relative mt-3"><!> <input type="text" placeholder="종목명 또는 종목코드 검색" class="w-full rounded-xl border border-dl-border bg-dl-bg-darker py-2.5 pl-9 pr-9 text-[12px] text-dl-text outline-none transition-colors placeholder:text-dl-text-dim focus:border-dl-primary/40"/> <!></div> <!> <!> <div class="mt-3 grid grid-cols-3 gap-1.5 rounded-xl bg-dl-bg-darker p-1"><button>Overview</button> <button>Explore</button> <button>Evidence</button></div> <!></div> <div class="flex-1 overflow-y-auto p-4"><!> <!></div></div> <!>',1);function xs(e,t){yn(t,!0);let r=pt(t,"selectedCompany",3,null),a=pt(t,"recentCompanies",19,()=>[]),i=pt(t,"activeTab",3,"explore"),l=pt(t,"evidenceMessage",3,null),s=pt(t,"activeEvidenceSection",3,null),c=pt(t,"selectedEvidenceIndex",3,null),v=F(""),m=F(ut([])),g=F(!1),y=null,C=F(null),P=F(!1),E=F(ut(new Set)),O=F(null),_=F(null),M=F(!1),R=F(!1),V=F(!0),h=F(ut(new Set)),N=F(null),G=F(null),K=F(!1),S=F(ut([])),W=F(ut([])),q=F(""),_e=F(ut([])),et=F(ut([])),me=F(""),ve=F(""),H=F(""),we=F(!1),Ye=F(null),xe=F(null),vt=F(null),Y=F(ut([]));const zt={finance:"재무제표",report:"정기보고서",disclosure:"공시 서술",notes:"K-IFRS 주석",analysis:"분석",raw:"원본 데이터"},Ce={finance:"실적, 재무상태, 현금흐름을 빠르게 확인합니다.",report:"정기보고서에서 구조화된 회사 정보를 확인합니다.",disclosure:"사업, MD&A, 원재료 등 서술형 공시를 읽습니다.",notes:"주석 계정과 세부 항목을 깊게 확인합니다.",analysis:"파생 분석이나 인사이트 결과를 확인합니다.",raw:"원본 데이터나 가공 전 결과를 검증합니다."};function k(o){return zt[o]||o}function J(o){return Ce[o]||"관련 데이터를 탐색합니다."}function U(o){return`${o.filter(w=>w.available).length}/${o.length}`}function re(o){return o.dataType==="timeseries"?"시계열 비교에 적합한 구조화 데이터":o.dataType==="table"||o.dataType==="dataframe"?"행·열 기준으로 직접 확인 가능한 표 데이터":o.dataType==="dict"?"핵심 필드를 빠르게 점검하는 요약 데이터":o.dataType==="text"?"원문 또는 긴 서술 데이터를 직접 읽는 모듈":"구조화된 모듈 데이터"}function he(o){var p,w,I,B;return o.category==="finance"?`${((p=r())==null?void 0:p.corpName)||"이 회사"}의 ${o.label}에서 가장 중요한 변화만 요약해줘`:o.category==="notes"?`${((w=r())==null?void 0:w.corpName)||"이 회사"}의 ${o.label}에서 주의할 점을 설명해줘`:o.category==="disclosure"?`${((I=r())==null?void 0:I.corpName)||"이 회사"}의 ${o.label} 핵심 내용을 요약해줘`:`${((B=r())==null?void 0:B.corpName)||"이 회사"}의 ${o.label} 데이터를 바탕으로 핵심 포인트를 정리해줘`}function ge(o){var p,w;return!((w=(p=n(_))==null?void 0:p.meta)!=null&&w.labels)||!n(V)?o:n(_).meta.labels[o]||o}function ee(o){var p,w;return(w=(p=n(_))==null?void 0:p.meta)!=null&&w.levels&&n(_).meta.levels[o]||1}function ct(){var o,p,w;return(p=(o=n(_))==null?void 0:o.meta)!=null&&p.unit?n(_).meta.unit:(w=n(_))!=null&&w.unit?n(_).unit:""}function xt(){var o,p;return!!((p=(o=n(_))==null?void 0:o.meta)!=null&&p.labels)}function Dt(){var o;return(o=n(_))!=null&&o.columns?n(_).columns.filter(p=>p!=="계정명"):[]}function ft(o){return Number.isInteger(o)&&o>=1900&&o<=2100}function cr(o){if(o==null)return"-";if(typeof o!="number")return String(o);if(o===0)return"0";const p=Math.abs(o),w=o<0?"-":"";return p>=1e12?`${w}${(p/1e12).toLocaleString("ko-KR",{maximumFractionDigits:1})}조`:p>=1e8?`${w}${Math.round(p/1e8).toLocaleString("ko-KR")}억`:p>=1e4?`${w}${Math.round(p/1e4).toLocaleString("ko-KR")}만`:o.toLocaleString("ko-KR")}function Ae(o,p){if(o==null)return"-";if(typeof o=="number"){if(ft(o))return String(o);if(p==="원"||p==="백만원")return p==="백만원"&&(o*=1e6),cr(o);if(Number.isInteger(o)&&Math.abs(o)>=1e3)return o.toLocaleString("ko-KR");if(!Number.isInteger(o))return o.toLocaleString("ko-KR",{maximumFractionDigits:2})}return String(o)}function De(o){var p,w,I;return o?o.type==="table"?[`${(o.totalRows||((p=o.rows)==null?void 0:p.length)||0).toLocaleString()}개 행`,`${(((w=o.columns)==null?void 0:w.length)||0).toLocaleString()}개 열`,o.truncated?"일부 행만 미리보기":"전체 미리보기 범위"]:o.type==="text"?[`${(((I=o.text)==null?void 0:I.length)||0).toLocaleString()}자 텍스트`,o.truncated?"긴 텍스트 일부만 노출":"본문 전체 미리보기"]:o.type==="dict"?[`${Object.keys(o.data||{}).length.toLocaleString()}개 필드`,"요약 필드 구조"]:["구조화 데이터","원본 확인 가능"]:[]}function He(o){return o?o.split(/\n+/).map(p=>p.trim()).filter(Boolean).filter(p=>p.length>18).slice(0,3):[]}async function Vt(o){if(!(o!=null&&o.stockCode)){u(C,null),u(G,null),u(S,[],!0),u(W,[],!0),u(_e,[],!0),u(H,"");return}u(P,!0),u(O,null),u(_,null),u(h,new Set,!0);try{u(C,await Ku(o.stockCode),!0);const p=Object.keys(n(C).categories||{});u(E,new Set(p.slice(0,2)),!0),u(N,o.stockCode,!0),u(H,"")}catch{u(C,null),u(H,"데이터 소스 목록을 불러오지 못했습니다. 다시 시도해 주세요.")}u(P,!1)}ln(()=>{var p;const o=((p=r())==null?void 0:p.stockCode)||null;!o||o===n(N)||Vt(r())}),ln(()=>{var p;!((p=r())!=null&&p.stockCode)||!n(C)||Bn(r(),n(C))});function Wt(){const o=n(v).trim();if(y&&clearTimeout(y),o.length<2){u(m,[],!0),u(g,!1);return}u(g,!0),y=setTimeout(async()=>{var p;try{const w=await bd(o);u(m,((p=w.results)==null?void 0:p.slice(0,8))||[],!0)}catch{u(m,[],!0)}u(g,!1)},250)}async function wt(o){var p,w;(p=t.onSelectCompany)==null||p.call(t,o),u(v,""),u(m,[],!0),(w=t.onChangeTab)==null||w.call(t,"overview"),await Vt(o)}function kt(){var o,p;(o=t.onSelectCompany)==null||o.call(t,null),u(v,""),u(m,[],!0),u(C,null),u(O,null),u(_,null),u(N,null),u(G,null),u(S,[],!0),u(W,[],!0),u(_e,[],!0),u(ve,""),u(h,new Set,!0),(p=t.onChangeTab)==null||p.call(t,"explore")}function ur(o){const p=new Set(n(E));p.has(o)?p.delete(o):p.add(o),u(E,p,!0)}async function Gt(o){var p,w;if(!(!o.available||!((p=r())!=null&&p.stockCode))){u(O,o,!0),(w=t.onChangeTab)==null||w.call(t,"explore"),u(M,!0),u(_,null);try{u(_,await Fl(r().stockCode,o.name,200),!0)}catch(I){u(_,{type:"error",error:I.message},!0)}u(M,!1)}}async function Ct(o=null){var p,w;if(r()){u(R,!0);try{await qu(r().stockCode,o);const I=o!=null&&o.length?`선택한 ${o.length}개 모듈을 다운로드했습니다.`:"전체 Excel 다운로드를 시작했습니다.";mt("success",I),(p=t.onNotify)==null||p.call(t,I,"success")}catch{const I="Excel 다운로드를 시작하지 못했습니다. 다시 시도해 주세요.";mt("error",I),(w=t.onNotify)==null||w.call(t,I)}u(R,!1)}}function Xt(o){if(!(o!=null&&o.available))return;const p=new Set(n(h));p.has(o.name)?p.delete(o.name):p.add(o.name),u(h,p,!0)}function Fe(){var o;!r()||!n(O)||(o=t.onAskAboutModule)==null||o.call(t,r(),n(O),n(_))}function mt(o,p){u(Ye,{type:o,text:p},!0),setTimeout(()=>{var w;((w=n(Ye))==null?void 0:w.text)===p&&u(Ye,null)},2600)}let be=ne(()=>{var w;const o=n(me).trim().toLowerCase(),p=Object.entries(((w=n(C))==null?void 0:w.categories)||{});return o?p.map(([I,B])=>[I,B.filter($=>`${$.label} ${$.name} ${$.description||""}`.toLowerCase().includes(o))]).filter(([,I])=>I.length>0):p}),Je=ne(()=>{var o;return((o=n(C))==null?void 0:o.availableSources)||0}),At=ne(()=>n(be).filter(([,o])=>o.some(p=>p.available)).length),Ft=ne(()=>n(be).flatMap(([p,w])=>w.filter(I=>I.available).map(I=>({...I,category:p}))).slice(0,5)),tr=ne(()=>{var o;return((o=l())==null?void 0:o.contexts)||[]}),rr=ne(()=>{var o;return(((o=l())==null?void 0:o.toolEvents)||[]).filter(p=>p.type==="call")}),vr=ne(()=>{var o;return(((o=l())==null?void 0:o.toolEvents)||[]).filter(p=>p.type==="result")}),qr=ne(()=>{var p,w,I,B;const o=[];return(I=(w=(p=l())==null?void 0:p.snapshot)==null?void 0:w.items)!=null&&I.length&&o.push({label:"핵심 수치",value:l().snapshot.items.length,tone:"success"}),n(tr).length&&o.push({label:"컨텍스트",value:n(tr).length,tone:"default"}),n(rr).length&&o.push({label:"툴 호출",value:n(rr).length,tone:"accent"}),n(vr).length&&o.push({label:"툴 결과",value:n(vr).length,tone:"success"}),(B=l())!=null&&B.systemPrompt&&o.push({label:"프롬프트",value:1,tone:"default"}),o}),Cn=ne(()=>De(n(_))),Xn=ne(()=>{var o;return((o=n(_))==null?void 0:o.type)==="text"?He(n(_).text):[]}),Pt=ne(()=>n(me).trim().length>0),it=ne(()=>[...n(h)]),fr=ne(()=>{var p;const o=new Map(Object.values(((p=n(C))==null?void 0:p.categories)||{}).flat().map(w=>[w.name,w]));return n(it).map(w=>o.get(w)).filter(Boolean)});function X(o){var p;(p=t.onChangeTab)==null||p.call(t,o)}function Ne(o,p,w){u(xe,{type:o,payload:p,title:w},!0)}function bt(){u(xe,null)}function ot(o,p){for(const w of p)if(o.has(w)&&o.get(w).available)return o.get(w);return null}function ht(o,p){var B,$;if(!((B=o==null?void 0:o.rows)!=null&&B.length)||!(($=o==null?void 0:o.columns)!=null&&$.length))return null;const w=o.columns.filter(D=>D!=="계정명");if(!w.length)return null;const I=w[w.length-1];for(const D of o.rows){const de=D.계정명;if(p.includes(de))return{value:D[I],period:I}}return null}function pr(o,p){var de,Be,Se,_t;const w=[],I=ht(o,["revenue","sales"]),B=ht(o,["operating_income"]),$=ht(o,["net_income","profit_loss"]),D=ht(p,["total_assets"]);return I&&w.push({label:"최근 매출",value:Ae(I.value,((de=o==null?void 0:o.meta)==null?void 0:de.unit)||(o==null?void 0:o.unit)||"원"),period:I.period}),B&&w.push({label:"최근 영업이익",value:Ae(B.value,((Be=o==null?void 0:o.meta)==null?void 0:Be.unit)||(o==null?void 0:o.unit)||"원"),period:B.period}),$&&w.push({label:"최근 순이익",value:Ae($.value,((Se=o==null?void 0:o.meta)==null?void 0:Se.unit)||(o==null?void 0:o.unit)||"원"),period:$.period}),D&&w.push({label:"최근 총자산",value:Ae(D.value,((_t=p==null?void 0:p.meta)==null?void 0:_t.unit)||(p==null?void 0:p.unit)||"원"),period:D.period}),w}function nr(o,p){var de,Be;if(!((de=o==null?void 0:o.rows)!=null&&de.length)||!((Be=o==null?void 0:o.columns)!=null&&Be.length))return[];const w=o.rows.find(Se=>p.includes(Se.계정명));if(!w)return[];const B=o.columns.filter(Se=>Se!=="계정명").slice(-5).map(Se=>({label:Se,value:typeof w[Se]=="number"?w[Se]:null})),$=B.filter(Se=>typeof Se.value=="number").map(Se=>Math.abs(Se.value)),D=Math.max(...$,0);return B.map(Se=>({...Se,ratio:D>0&&typeof Se.value=="number"?Math.max(8,Math.round(Math.abs(Se.value)/D*100)):0}))}function Er(o,p,w,I){var D,de,Be,Se;const B=[],$=Object.entries(p.categories||{}).filter(([,_t])=>_t.some(ce=>ce.available)).map(([_t])=>k(_t));return $.length>0&&B.push(`활성 카테고리 ${$.slice(0,3).join(", ")}`),(D=w.get("dividend"))!=null&&D.available&&B.push("배당 데이터 확인 가능"),(de=w.get("majorHolder"))!=null&&de.available&&B.push("최대주주 데이터 확인 가능"),((Be=w.get("business"))!=null&&Be.available||(Se=w.get("mdna"))!=null&&Se.available)&&B.push("서술형 사업/리스크 공시 탐색 가능"),I.length||B.push("핵심 재무 카드는 원본 표 탐색 후 질문으로 이어가는 흐름에 최적화됨"),o!=null&&o.market&&B.push(`${o.market} 상장사`),B.slice(0,4)}function Pr(o){var w,I;const p=[];return ot(o,["annual.IS","IS","fsSummary"])&&p.push({label:"실적 구조 보기",description:"표준화된 계정을 바로 열어 비교 가능한 숫자 구조를 확인합니다.",tab:"explore"}),((w=o.get("business"))!=null&&w.available||(I=o.get("mdna"))!=null&&I.available)&&p.push({label:"사업/리스크 읽기",description:"서술형 공시 텍스트와 원문 근거를 같이 훑습니다.",tab:"explore"}),p.push({label:"현재 근거 보기",description:"채팅에서 사용된 스냅샷, 컨텍스트, 툴 결과를 검증합니다.",tab:"evidence"}),p.slice(0,3)}async function Bn(o,p){if(!(o!=null&&o.stockCode)||!p)return;u(K,!0),u(ve,"");const w=new Map(Object.values(p.categories||{}).flat().map($=>[$.name,$])),I=ot(w,["annual.IS","IS","fsSummary"]),B=ot(w,["annual.BS","BS"]);try{const[$,D,de]=await Promise.all([Yu(o.stockCode).catch(()=>o),I?Fl(o.stockCode,I.name,80).catch(()=>null):Promise.resolve(null),B?Fl(o.stockCode,B.name,80).catch(()=>null):Promise.resolve(null)]);u(G,{...o,...$||{}},!0),u(S,pr(D,de),!0),u(W,Er(n(G),p,w,n(S)),!0),u(_e,nr(D,["revenue","sales"]),!0),u(q,[I==null?void 0:I.label,B==null?void 0:B.label].filter(Boolean).join(" / "),!0),u(Y,Pr(w),!0),u(et,[n(S)[0]?`${n(S)[0].label} 기준 최근 관측 시점은 ${n(S)[0].period}입니다.`:"핵심 재무 카드는 원본 시계열이 있을 때 자동 생성됩니다.",n(_e).length>1?"추세 막대는 최근 5개 시점의 절대 규모를 기준으로 시각화합니다.":"추세 데이터가 충분하지 않으면 Explore에서 원본 표를 먼저 확인하는 편이 낫습니다.",n(q)?`현재 Overview는 ${n(q)} 모듈을 기준으로 조립되었습니다.`:"현재 Overview는 기본 회사 정보와 사용 가능한 모듈 중심으로 조립되었습니다."],!0)}catch{u(G,o,!0),u(S,[],!0),u(W,["회사 기본 정보만 확인할 수 있습니다."],!0),u(_e,[],!0),u(q,""),u(ve,"Overview 데이터를 만들지 못했습니다. Explore에서 원본 모듈을 확인해 주세요."),u(Y,[],!0),u(et,["Overview 조립 실패로 인해 원본 모듈 탐색 흐름이 우선입니다."],!0)}u(K,!1)}async function Sn(){var o;typeof navigator>"u"||!navigator.clipboard||(await navigator.clipboard.writeText(window.location.href),u(we,!0),mt("success","워크스페이스 링크를 복사했습니다."),(o=t.onNotify)==null||o.call(t,"워크스페이스 링크를 복사했습니다.","success"),setTimeout(()=>{u(we,!1)},1500))}ln(()=>{i()!=="evidence"||!s()||!l()||requestAnimationFrame(()=>{var o;if((o=document.querySelector(`[data-evidence-section="${s()}"]`))==null||o.scrollIntoView({block:"start",behavior:"smooth"}),s()==="snapshot"&&l().snapshot){u(xe,{type:"snapshot",payload:l().snapshot,title:"핵심 수치"},!0);return}if(s()==="contexts"&&n(tr).length>0){const p=n(tr)[c()??0];p&&u(xe,{type:"context",payload:p,title:p.label||p.module||"컨텍스트"},!0);return}if(s()==="tool-calls"&&n(rr).length>0){const p=n(rr)[c()??0];p&&u(xe,{type:"tool-call",payload:p,title:`${p.name} 호출`},!0);return}if(s()==="tool-results"&&n(vr).length>0){const p=n(vr)[c()??0];p&&u(xe,{type:"tool-result",payload:p,title:`${p.name} 결과`},!0);return}if(s()==="system"&&l().systemPrompt){u(xe,{type:"system",payload:l().systemPrompt,title:"System Prompt"},!0);return}s()==="input"&&l().userContent&&u(xe,{type:"user",payload:l().userContent,title:"LLM Input"},!0)})}),ln(()=>{!n(xe)||!n(vt)||requestAnimationFrame(()=>{var o;return(o=n(vt))==null?void 0:o.focus()})});var un=xm(),ba=Z(un),Va=d(ba),Li=d(Va),pi=d(Li),pl=d(pi),Pi=d(pl);hr(Pi,{size:16,class:"text-dl-primary-light"});var xl=f(pi,2);{var Ri=o=>{var p=$p(),w=d(p);Ja(w,{size:16}),j("click",p,()=>{var I;return(I=t.onClose)==null?void 0:I.call(t)}),x(o,p)};A(xl,o=>{t.onClose&&o(Ri)})}var ji=f(Li,2),Ga=d(ji);Fa(Ga,{size:14,class:"pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-dl-text-dim"});var Ha=f(Ga,2),ml=f(Ha,2);{var bl=o=>{Lr(o,{size:14,class:"absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-dl-text-dim"})};A(ml,o=>{n(g)&&o(bl)})}var Di=f(ji,2);{var gl=o=>{var p=Gp();ze(p,21,()=>n(m),Me,(w,I)=>{var B=Vp(),$=d(B),D=d($),de=f($,2),Be=d(de),Se=d(Be),_t=f(Be,2),ce=d(_t),ie=f(de,2);ss(ie,{size:14,class:"flex-shrink-0 text-dl-text-dim"}),L(()=>{z(D,n(I).corpName[0]),z(Se,n(I).corpName),z(ce,`${n(I).stockCode??""} · ${(n(I).market||"미분류")??""}`)}),j("click",B,()=>wt(n(I))),x(w,B)}),x(o,p)};A(Di,o=>{n(m).length>0&&o(gl)})}var Fi=f(Di,2);{var hl=o=>{var p=Hp(),w=d(p),I=d(w),B=d(I),$=d(B),D=f(B,2),de=d(D),Be=f(de);{var Se=ke=>{var Rt=an();L(()=>z(Rt,`· ${r().market??""}`)),x(ke,Rt)};A(Be,ke=>{r().market&&ke(Se)})}var _t=f(Be,2);{var ce=ke=>{var Rt=an();L(()=>z(Rt,`· ${n(Je)??""}개 데이터`)),x(ke,Rt)};A(_t,ke=>{n(Je)&&ke(ce)})}var ie=f(I,2),Le=f(w,2),Qt=d(Le),St=d(Qt);ff(St,{size:10,class:"mr-1 inline"});var dr=f(St),Pe=f(Qt,2),Oe=d(Pe);hf(Oe,{size:10,class:"mr-1 inline"}),L(()=>{var ke;z($,r().corpName||r().company||((ke=n(G))==null?void 0:ke.corpName)||r().stockCode),z(de,`${r().stockCode??""} `),z(dr,` ${n(we)?"링크 복사됨":"링크 복사"}`)}),j("click",ie,kt),j("click",Qt,Sn),j("click",Pe,()=>Vt(r())),x(o,p)},_l=o=>{var p=Wp(),w=f(d(p),2);ze(w,21,a,Me,(I,B)=>{var $=Up(),D=d($);L(()=>z(D,`${(n(B).corpName||n(B).company)??""} · ${n(B).stockCode??""}`)),j("click",$,()=>wt(n(B))),x(I,$)}),x(o,p)};A(Fi,o=>{r()?o(hl):a().length>0&&o(_l,1)})}var Bi=f(Fi,2),Ua=d(Bi),xi=f(Ua,2),$i=f(xi,2),yl=f(Bi,2);{var wl=o=>{var p=qp(),w=Z(p),I=d(w),B=f(d(I),2),$=d(B),D=f(I,2),de=f(d(D),2),Be=d(de),Se=f(D,2),_t=f(d(Se),2),ce=d(_t);L(()=>{z($,i()==="overview"?"Overview":i()==="explore"?"Explore":"Evidence"),z(Be,n(Je)),z(ce,n(it).length)}),x(o,p)};A(yl,o=>{r()&&o(wl)})}var kl=f(Va,2),mi=d(kl);{var Cl=o=>{var p=Kp(),w=d(p);L(I=>{nt(p,1,I),z(w,n(Ye).text)},[()=>rt(at("mb-3 rounded-xl border px-3 py-2 text-[10px]",n(Ye).type==="success"?"border-dl-success/30 bg-dl-success/10 text-dl-success":"border-dl-primary/20 bg-dl-primary/[0.05] text-dl-primary-light"))]),x(o,p)};A(mi,o=>{n(Ye)&&o(Cl)})}var Vi=f(mi,2);{var Sl=o=>{var p=ye(),w=Z(p);{var I=$=>{var D=Yp(),de=d(D);hr(de,{size:28,class:"mx-auto mb-3 text-dl-text-dim/50"}),x($,D)},B=$=>{var D=dx(),de=d(D),Be=d(de),Se=d(Be),_t=d(Se),ce=d(_t),ie=f(_t,2),Le=d(ie),Qt=f(Le);{var St=Q=>{var le=an();L(()=>{var Ee;return z(le,`· ${(((Ee=n(G))==null?void 0:Ee.market)||r().market)??""}`)}),x(Q,le)};A(Qt,Q=>{var le;((le=n(G))!=null&&le.market||r().market)&&Q(St)})}var dr=f(Qt,2);{var Pe=Q=>{var le=an();L(()=>{var Ee;return z(le,`· ${(((Ee=n(G))==null?void 0:Ee.sector)||r().sector)??""}`)}),x(Q,le)};A(dr,Q=>{var le;((le=n(G))!=null&&le.sector||r().sector)&&Q(Pe)})}var Oe=f(Be,2),ke=d(Oe),Rt=f(d(ke),2),en=d(Rt),Br=f(ke,2),$n=f(d(Br),2),En=d($n),Mn=f(de,2),tn=d(Mn),Vn=d(tn);yf(Vn,{size:13,class:"text-dl-accent"});var Gn=f(tn,2);{var Hn=Q=>{var le=Jp();x(Q,le)},Un=Q=>{var le=tx(),Ee=Z(le);ze(Ee,21,()=>n(S),Me,(ar,er)=>{var Ir=Xp(),Kr=d(Ir),jr=d(Kr),$r=f(Kr,2),Yr=d($r),zn=f($r,2),An=d(zn);L(()=>{z(jr,n(er).label),z(Yr,n(er).value),z(An,n(er).period)}),x(ar,Ir)});var Zt=f(Ee,2);{var Kt=ar=>{var er=Qp(),Ir=d(er);L(()=>z(Ir,`출처: ${n(q)??""}`)),x(ar,er)};A(Zt,ar=>{n(q)&&ar(Kt)})}var yr=f(Zt,2);{var Rr=ar=>{var er=ex(),Ir=f(d(er),2);ze(Ir,21,()=>n(_e),Me,(Kr,jr)=>{var $r=Zp(),Yr=d($r),zn=f(Yr,2),An=d(zn);L(Xe=>{rl(Yr,`height: ${n(jr).ratio||8}px`),gn(Yr,"title",Xe),z(An,n(jr).label)},[()=>n(jr).value===null?"-":Ae(n(jr).value,"원")]),x(Kr,$r)}),x(ar,er)};A(yr,ar=>{n(_e).length>0&&ar(Rr)})}x(Q,le)},Qn=Q=>{var le=rx();x(Q,le)};A(Gn,Q=>{n(K)?Q(Hn):n(S).length>0?Q(Un,1):Q(Qn,-1)})}var Zn=f(Gn,2);{var Te=Q=>{var le=nx(),Ee=d(le);L(()=>z(Ee,n(ve))),x(Q,le)};A(Zn,Q=>{n(ve)&&Q(Te)})}var Re=f(Mn,2),Tt=f(d(Re),2);ze(Tt,21,()=>n(et),Me,(Q,le)=>{var Ee=ax(),Zt=d(Ee);L(()=>z(Zt,n(le))),x(Q,Ee)});var gt=f(Re,2),st=f(d(gt),2);ze(st,21,()=>n(W),Me,(Q,le)=>{var Ee=ix(),Zt=d(Ee);L(()=>z(Zt,n(le))),x(Q,Ee)});var Nt=f(gt,2);{var qt=Q=>{var le=ox(),Ee=f(d(le),2);ze(Ee,21,()=>n(Y),Me,(Zt,Kt)=>{var yr=lx(),Rr=d(yr),ar=d(Rr),er=f(Rr,2),Ir=d(er);L(()=>{z(ar,n(Kt).label),z(Ir,n(Kt).description)}),j("click",yr,()=>X(n(Kt).tab)),x(Zt,yr)}),x(Q,le)};A(Nt,Q=>{n(Y).length>0&&Q(qt)})}var Ht=f(Nt,2),qe=f(d(Ht),2);ze(qe,21,()=>n(Ft),Me,(Q,le)=>{var Ee=sx(),Zt=d(Ee),Kt=d(Zt),yr=d(Kt),Rr=d(yr),ar=f(yr,2),er=d(ar),Ir=f(Kt,2),Kr=d(Ir);L((jr,$r)=>{z(Rr,n(le).label),z(er,jr),z(Kr,$r)},[()=>re(n(le)),()=>k(n(le).category)]),j("click",Ee,()=>Gt(n(le))),x(Q,Ee)});var Ke=f(Ht,2),te=d(Ke),ue=f(te,2);L(()=>{var Q,le;z(ce,((Q=n(G))==null?void 0:Q.corpName)||r().corpName||r().company||r().stockCode),z(Le,`${(((le=n(G))==null?void 0:le.stockCode)||r().stockCode)??""} `),z(en,n(Je)),z(En,n(At))}),j("click",te,()=>X("explore")),j("click",ue,()=>X("evidence")),x($,D)};A(w,$=>{r()?$(B,-1):$(I)})}x(o,p)},Gi=o=>{var p=ye(),w=Z(p);{var I=$=>{var D=cx(),de=d(D);hr(de,{size:28,class:"mx-auto mb-3 text-dl-text-dim/50"}),x($,D)},B=$=>{var D=Nx(),de=d(D);{var Be=Te=>{var Re=vx();ze(Re,21,()=>n(qr),Me,(Tt,gt)=>{var st=ux(),Nt=d(st),qt=d(Nt),Ht=f(Nt,2),qe=d(Ht);L(Ke=>{nt(st,1,Ke),z(qt,n(gt).label),z(qe,n(gt).value)},[()=>rt(at("rounded-2xl border px-3 py-3",n(gt).tone==="success"?"border-dl-success/20 bg-dl-success/[0.06]":n(gt).tone==="accent"?"border-dl-accent/20 bg-dl-accent/[0.06]":"border-dl-border/40 bg-dl-bg-darker/70"))]),x(Tt,st)}),x(Te,Re)};A(de,Te=>{n(qr).length>0&&Te(Be)})}var Se=f(de,2);{var _t=Te=>{var Re=mx(),Tt=f(d(Re),2),gt=d(Tt);{var st=qe=>{var Ke=fx(),te=d(Ke);L(()=>z(te,l().meta.company)),x(qe,Ke)};A(gt,qe=>{var Ke;(Ke=l().meta)!=null&&Ke.company&&qe(st)})}var Nt=f(gt,2);{var qt=qe=>{var Ke=px(),te=d(Ke);L(()=>z(te,typeof l().meta.dataYearRange=="string"?l().meta.dataYearRange:`${l().meta.dataYearRange.min_year}~${l().meta.dataYearRange.max_year}년`)),x(qe,Ke)};A(Nt,qe=>{var Ke;(Ke=l().meta)!=null&&Ke.dataYearRange&&qe(qt)})}var Ht=f(Nt,2);ze(Ht,17,()=>{var qe;return((qe=l().meta)==null?void 0:qe.includedModules)||[]},Me,(qe,Ke)=>{var te=xx(),ue=d(te);L(()=>z(ue,n(Ke))),x(qe,te)}),x(Te,Re)};A(Se,Te=>{var Re,Tt;((Re=l().meta)!=null&&Re.company||(Tt=l().meta)!=null&&Tt.dataYearRange)&&Te(_t)})}var ce=f(Se,2);{var ie=Te=>{var Re=gx(),Tt=d(Re),gt=d(Tt);hr(gt,{size:13,class:"text-dl-success"});var st=f(Tt,2);ze(st,21,()=>l().snapshot.items,Me,(Nt,qt)=>{var Ht=bx(),qe=d(Ht),Ke=d(qe),te=f(qe,2),ue=d(te);L(()=>{z(Ke,n(qt).label),z(ue,n(qt).value)}),x(Nt,Ht)}),j("click",Re,()=>Ne("snapshot",l().snapshot,"핵심 수치")),x(Te,Re)};A(ce,Te=>{var Re,Tt;((Tt=(Re=l().snapshot)==null?void 0:Re.items)==null?void 0:Tt.length)>0&&Te(ie)})}var Le=f(ce,2),Qt=d(Le),St=d(Qt);hr(St,{size:13,class:"text-dl-accent"});var dr=f(Qt,2);{var Pe=Te=>{var Re=_x(),Tt=f(Z(Re),2);ze(Tt,21,()=>n(tr),Me,(gt,st)=>{var Nt=hx(),qt=d(Nt),Ht=d(qt),qe=d(Ht),Ke=f(Ht,2),te=d(Ke);co(te,{size:11});var ue=f(qt,2),Q=d(ue);L(()=>{z(qe,n(st).label||n(st).module),z(Q,n(st).text)}),j("click",Nt,()=>Ne("context",n(st),n(st).label||n(st).module||"컨텍스트")),x(gt,Nt)}),x(Te,Re)},Oe=Te=>{var Re=yx();x(Te,Re)};A(dr,Te=>{n(tr).length>0?Te(Pe):Te(Oe,-1)})}var ke=f(Le,2),Rt=d(ke),en=d(Rt);uo(en,{size:13,class:"text-dl-primary-light"});var Br=f(Rt,2);{var $n=Te=>{var Re=kx();ze(Re,21,()=>n(rr),Me,(Tt,gt)=>{var st=wx(),Nt=d(st),qt=d(Nt),Ht=f(qt);{var qe=le=>{var Ee=an();L(()=>z(Ee,`· ${n(gt).arguments.module??""}`)),x(le,Ee)};A(Ht,le=>{var Ee;(Ee=n(gt).arguments)!=null&&Ee.module&&le(qe)})}var Ke=f(Ht,2);{var te=le=>{var Ee=an();L(()=>z(Ee,`· ${n(gt).arguments.keyword??""}`)),x(le,Ee)};A(Ke,le=>{var Ee;(Ee=n(gt).arguments)!=null&&Ee.keyword&&le(te)})}var ue=f(Nt,2),Q=d(ue);Ia(Q,{size:11}),L(()=>z(qt,`${n(gt).name??""} `)),j("click",st,()=>Ne("tool-call",n(gt),`${n(gt).name} 호출`)),x(Tt,st)}),x(Te,Re)},En=Te=>{var Re=Cx();x(Te,Re)};A(Br,Te=>{n(rr).length>0?Te($n):Te(En,-1)})}var Mn=f(ke,2),tn=d(Mn),Vn=d(tn);Ia(Vn,{size:13,class:"text-dl-success"});var Gn=f(tn,2);{var Hn=Te=>{var Re=Ex(),Tt=f(Z(Re),2);ze(Tt,21,()=>n(vr),Me,(gt,st)=>{var Nt=Sx(),qt=d(Nt),Ht=d(qt),qe=f(Ht);{var Ke=Q=>{var le=an();L(Ee=>z(le,`· ${Ee??""}`),[()=>n(st).result.slice(0,80)]),x(Q,le)};A(qe,Q=>{typeof n(st).result=="string"&&Q(Ke)})}var te=f(qt,2),ue=d(te);co(ue,{size:11}),L(()=>z(Ht,`${n(st).name??""} `)),j("click",Nt,()=>Ne("tool-result",n(st),`${n(st).name} 결과`)),x(gt,Nt)}),x(Te,Re)},Un=Te=>{var Re=Mx();x(Te,Re)};A(Gn,Te=>{n(vr).length>0?Te(Hn):Te(Un,-1)})}var Qn=f(Mn,2);{var Zn=Te=>{var Re=Tx(),Tt=d(Re),gt=d(Tt);Zi(gt,{size:13,class:"text-dl-accent-light"});var st=f(Tt,2);{var Nt=qe=>{var Ke=zx(),te=f(d(Ke),2),ue=d(te);L(()=>z(ue,l().systemPrompt)),j("click",Ke,()=>Ne("system",l().systemPrompt,"System Prompt")),x(qe,Ke)};A(st,qe=>{l().systemPrompt&&qe(Nt)})}var qt=f(st,2);{var Ht=qe=>{var Ke=Ax(),te=f(d(Ke),2),ue=d(te);L(()=>z(ue,l().userContent)),j("click",Ke,()=>Ne("user",l().userContent,"LLM Input")),x(qe,Ke)};A(qt,qe=>{l().userContent&&qe(Ht)})}x(Te,Re)};A(Qn,Te=>{(l().systemPrompt||l().userContent)&&Te(Zn)})}x($,D)};A(w,$=>{l()?$(B,-1):$(I)})}x(o,p)},El=o=>{var p=ye(),w=Z(p);{var I=$=>{var D=Ox(),de=d(D);hr(de,{size:28,class:"mx-auto mb-3 text-dl-text-dim/50"}),x($,D)},B=$=>{var D=dm(),de=d(D),Be=d(de),Se=d(Be),_t=f(d(Se),2),ce=d(_t),ie=f(Be,2),Le=d(ie),Qt=f(d(Le),2),St=d(Qt),dr=f(Le,2),Pe=d(dr),Oe=d(Pe);{var ke=te=>{Lr(te,{size:11,class:"animate-spin"})},Rt=te=>{La(te,{size:11})};A(Oe,te=>{n(R)&&n(it).length>0?te(ke):te(Rt,-1)})}var en=f(Pe,2),Br=f(en,2),$n=d(Br);{var En=te=>{Lr(te,{size:11,class:"animate-spin"})},Mn=te=>{La(te,{size:11})};A($n,te=>{n(R)&&n(it).length===0?te(En):te(Mn,-1)})}var tn=f(ie,2);{var Vn=te=>{var ue=Lx(),Q=d(ue);ze(Q,17,()=>n(fr),Me,(Ee,Zt)=>{var Kt=Ix(),yr=d(Kt);L(()=>z(yr,`${n(Zt).label??""} ×`)),j("click",Kt,()=>u(h,new Set(n(it).filter(Rr=>Rr!==n(Zt).name)),!0)),x(Ee,Kt)});var le=f(Q,2);j("click",le,()=>u(h,new Set,!0)),x(te,ue)};A(tn,te=>{n(it).length>0&&te(Vn)})}var Gn=f(tn,2),Hn=d(Gn),Un=d(Hn);Fa(Un,{size:12,class:"pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-dl-text-dim"});var Qn=f(Un,2),Zn=f(Hn,2);{var Te=te=>{var ue=Px(),Q=d(ue);L(()=>z(Q,n(H))),x(te,ue)};A(Zn,te=>{n(H)&&te(Te)})}var Re=f(Zn,2);{var Tt=te=>{var ue=Rx(),Q=d(ue);Lr(Q,{size:14,class:"animate-spin"}),x(te,ue)},gt=te=>{var ue=jx();x(te,ue)},st=te=>{var ue=ye(),Q=Z(ue);ze(Q,17,()=>n(be),Me,(le,Ee)=>{var Zt=ne(()=>el(n(Ee),2));let Kt=()=>n(Zt)[0],yr=()=>n(Zt)[1];var Rr=Vx(),ar=d(Rr),er=d(ar);{var Ir=Et=>{of(Et,{size:13,class:"mt-0.5 flex-shrink-0 text-dl-text-dim"})},Kr=ne(()=>n(E).has(Kt())),jr=Et=>{ss(Et,{size:13,class:"mt-0.5 flex-shrink-0 text-dl-text-dim"})};A(er,Et=>{n(Kr)?Et(Ir):Et(jr,-1)})}var $r=f(er,2),Yr=d($r),zn=d(Yr),An=d(zn),Xe=f(zn,2),Ot=d(Xe),Bt=f(Yr,2),ir=d(Bt),wr=f(ar,2);{var It=Et=>{var Yt=$x();ze(Yt,21,yr,Me,(yt,se)=>{var fe=Bx(),pe=d(fe);{var dt=jt=>{var mr=Dx();L(Dr=>{nt(mr,1,Dr),gn(mr,"aria-label",`${n(se).label} 선택`)},[()=>rt(at("flex h-4 w-4 items-center justify-center rounded border flex-shrink-0",n(h).has(n(se).name)?"border-dl-primary bg-dl-primary/20 text-dl-primary-light":"border-dl-border text-transparent"))]),j("click",mr,()=>Xt(n(se))),x(jt,mr)},lt=jt=>{var mr=Fx();x(jt,mr)};A(pe,jt=>{n(se).available?jt(dt):jt(lt,-1)})}var Ut=f(pe,2),Jt=d(Ut);{var Lt=jt=>{fs(jt,{size:11,class:"flex-shrink-0 text-dl-text-dim"})},$t=jt=>{Ka(jt,{size:11,class:"flex-shrink-0 text-dl-text-dim"})};A(Jt,jt=>{n(se).dataType==="timeseries"||n(se).dataType==="table"||n(se).dataType==="dataframe"?jt(Lt):jt($t,-1)})}var Mt=f(Jt,2),or=d(Mt),kr=d(or),xr=f(or,2),vn=d(xr);L((jt,mr)=>{nt(fe,1,jt),Ut.disabled=!n(se).available,z(kr,n(se).label),z(vn,mr)},[()=>{var jt;return rt(at("flex items-center gap-2 rounded-lg border px-3 py-2 text-left transition-all",!n(se).available&&"cursor-default opacity-35",n(se).available&&((jt=n(O))==null?void 0:jt.name)===n(se).name?"border-dl-primary/40 bg-dl-primary/[0.08]":n(se).available?"border-transparent bg-white/[0.01] hover:border-dl-primary/20 hover:bg-white/[0.03]":"border-transparent bg-transparent"))},()=>re(n(se))]),j("click",Ut,()=>Gt({...n(se),category:Kt()})),x(yt,fe)}),x(Et,Yt)},lr=ne(()=>n(E).has(Kt()));A(wr,Et=>{n(lr)&&Et(It)})}L((Et,Yt,yt)=>{z(An,Et),z(Ot,Yt),z(ir,yt)},[()=>k(Kt()),()=>U(yr()),()=>J(Kt())]),j("click",ar,()=>ur(Kt())),x(le,Rr)}),x(te,ue)};A(Re,te=>{n(P)?te(Tt):n(be).length===0&&n(Pt)?te(gt,1):te(st,-1)})}var Nt=f(de,2),qt=d(Nt);{var Ht=te=>{var ue=Gx(),Q=d(ue);fs(Q,{size:28,class:"mx-auto mb-3 text-dl-text-dim/50"}),x(te,ue)},qe=te=>{var ue=Hx(),Q=d(ue);Lr(Q,{size:14,class:"animate-spin"});var le=f(Q);L(()=>z(le,` ${n(O).label??""} 미리보기 로딩 중...`)),x(te,ue)},Ke=te=>{var ue=sm(),Q=Z(ue),le=d(Q),Ee=d(le),Zt=d(Ee),Kt=d(Zt),yr=f(Zt,2),Rr=d(yr),ar=f(Ee,2),er=d(ar);{var Ir=se=>{var fe=Ux(),pe=d(fe);vf(pe,{size:11,class:"inline mr-1"});var dt=f(pe);L(lt=>{nt(fe,1,lt),z(dt,` ${n(V)?"한글":"EN"}`)},[()=>rt(at("rounded-lg px-2 py-1 text-[10px] transition-colors",n(V)?"bg-dl-primary/15 text-dl-primary-light":"text-dl-text-dim hover:bg-white/5 hover:text-dl-text"))]),j("click",fe,()=>u(V,!n(V))),x(se,fe)},Kr=ne(()=>xt());A(er,se=>{n(Kr)&&se(Ir)})}var jr=f(er,2),$r=d(jr);La($r,{size:11,class:"inline mr-1"});var Yr=f(le,2);ze(Yr,21,()=>n(Cn),Me,(se,fe)=>{var pe=Wx(),dt=d(pe);L(()=>z(dt,n(fe))),x(se,pe)});var zn=f(Yr,2),An=f(d(zn),2),Xe=d(An),Ot=f(An,2),Bt=f(Q,2);{var ir=se=>{var fe=Jx(),pe=d(fe),dt=d(pe),lt=d(dt),Ut=f(d(lt));ze(Ut,17,Dt,Me,(Lt,$t)=>{var Mt=qx(),or=d(Mt);L(()=>z(or,n($t))),x(Lt,Mt)});var Jt=f(dt);ze(Jt,21,()=>n(_).rows,Me,(Lt,$t)=>{const Mt=ne(()=>n($t).계정명),or=ne(()=>ee(n(Mt)));var kr=Yx(),xr=d(kr),vn=d(xr),jt=f(xr);ze(jt,17,Dt,Me,(mr,Dr)=>{const Mr=ne(()=>n($t)[n(Dr)]);var ga=Kx(),Hi=d(ga);L((Al,Tl)=>{nt(ga,1,Al),z(Hi,Tl)},[()=>rt(at("border-b border-dl-border/10 px-3 py-1.5 text-right font-mono text-[10px]",n(Mr)===null||n(Mr)===void 0?"text-dl-text-dim/30":typeof n(Mr)=="number"&&n(Mr)<0?"text-dl-primary-light":"text-dl-accent-light")),()=>Ae(n(Mr),ct())]),x(mr,ga)}),L((mr,Dr)=>{nt(xr,1,mr),rl(xr,`padding-left: ${8+(n(or)-1)*12}px`),z(vn,Dr)},[()=>rt(at("sticky left-0 border-b border-r border-dl-border/10 bg-dl-bg-card/95 px-3 py-1.5 whitespace-nowrap",n(or)===1&&"font-semibold text-dl-text",n(or)===2&&"text-dl-text-muted",n(or)>=3&&"text-dl-text-dim")),()=>ge(n(Mt))]),x(Lt,kr)}),x(se,fe)},wr=ne(()=>n(_).type==="table"&&xt()),It=se=>{var fe=em(),pe=d(fe),dt=d(pe),lt=d(dt);ze(lt,21,()=>n(_).columns,Me,(Jt,Lt)=>{var $t=Xx(),Mt=d($t);L(()=>z(Mt,n(Lt))),x(Jt,$t)});var Ut=f(dt);ze(Ut,21,()=>n(_).rows,Me,(Jt,Lt)=>{var $t=Zx();ze($t,21,()=>n(_).columns,Me,(Mt,or)=>{const kr=ne(()=>n(Lt)[n(or)]);var xr=Qx(),vn=d(xr);L((jt,mr)=>{nt(xr,1,jt),z(vn,mr)},[()=>rt(at("border-b border-dl-border/10 px-3 py-1.5 whitespace-nowrap",typeof n(kr)=="number"?"text-right font-mono text-[10px] text-dl-accent-light":"text-dl-text-muted")),()=>Ae(n(kr),ct())]),x(Mt,xr)}),x(Jt,$t)}),x(se,fe)},lr=se=>{var fe=rm();ze(fe,21,()=>Object.entries(n(_).data||{}),Me,(pe,dt)=>{var lt=ne(()=>el(n(dt),2));let Ut=()=>n(lt)[0],Jt=()=>n(lt)[1];var Lt=tm(),$t=d(Lt),Mt=d($t),or=f($t,2),kr=d(or);L(()=>{z(Mt,Ut()),z(kr,Jt()??"-")}),x(pe,Lt)}),x(se,fe)},Et=se=>{var fe=im(),pe=d(fe);{var dt=Jt=>{var Lt=am(),$t=f(d(Lt),2);ze($t,21,()=>n(Xn),Me,(Mt,or)=>{var kr=nm(),xr=d(kr);L(()=>z(xr,n(or))),x(Mt,kr)}),x(Jt,Lt)};A(pe,Jt=>{n(Xn).length>0&&Jt(dt)})}var lt=f(pe,2),Ut=d(lt);L(()=>z(Ut,n(_).text)),x(se,fe)},Yt=se=>{var fe=lm(),pe=d(fe);L(()=>z(pe,n(_).error||"데이터를 불러올 수 없습니다.")),x(se,fe)},yt=se=>{var fe=om(),pe=d(fe),dt=d(pe);L(lt=>z(dt,lt),[()=>n(_).data||JSON.stringify(n(_),null,2)]),x(se,fe)};A(Bt,se=>{n(wr)?se(ir):n(_).type==="table"?se(It,1):n(_).type==="dict"?se(lr,2):n(_).type==="text"?se(Et,3):n(_).type==="error"?se(Yt,4):se(yt,-1)})}L((se,fe)=>{z(Kt,n(O).label),z(Rr,se),z(Xe,fe)},[()=>re(n(O)),()=>he(n(O))]),j("click",jr,()=>Ct([n(O).name])),j("click",Ot,Fe),x(te,ue)};A(qt,te=>{n(O)?n(M)?te(qe,1):n(_)&&te(Ke,2):te(Ht)})}L(()=>{z(ce,`${n(Je)??""}개 모듈`),z(St,n(it).length>0?`${n(it).length}개 모듈 선택됨`:"다운로드할 모듈을 선택하거나 전체 Excel을 받으세요."),Pe.disabled=n(R)||n(it).length===0,en.disabled=n(it).length===0,Br.disabled=n(R)}),j("click",Pe,()=>Ct(n(it))),j("click",en,()=>u(h,new Set,!0)),j("click",Br,()=>Ct()),Oa(Qn,()=>n(me),te=>u(me,te)),x($,D)};A(w,$=>{r()?$(B,-1):$(I)})}x(o,p)};A(Vi,o=>{i()==="overview"?o(Sl):i()==="evidence"?o(Gi,1):o(El,-1)})}var Ml=f(ba,2);{var zl=o=>{var p=pm(),w=d(p),I=d(w),B=d(I),$=d(B),D=d($),de=f($,2),Be=d(de),Se=f(B,2),_t=d(Se);Ja(_t,{size:16});var ce=f(I,2),ie=d(ce);{var Le=Pe=>{var Oe=cm(),ke=d(Oe),Rt=d(ke);L(()=>{var en;return z(Rt,((en=n(xe).payload)==null?void 0:en.text)||"-")}),x(Pe,Oe)},Qt=Pe=>{var Oe=um(),ke=d(Oe);L(Rt=>z(ke,Rt),[()=>JSON.stringify(n(xe).payload,null,2)]),x(Pe,Oe)},St=Pe=>{var Oe=vm(),ke=d(Oe);L(Rt=>z(ke,Rt),[()=>JSON.stringify(n(xe).payload,null,2)]),x(Pe,Oe)},dr=Pe=>{var Oe=fm(),ke=d(Oe),Rt=d(ke);L(()=>z(Rt,n(xe).payload||"-")),x(Pe,Oe)};A(ie,Pe=>{n(xe).type==="context"?Pe(Le):n(xe).type==="tool"||n(xe).type==="tool-call"||n(xe).type==="tool-result"?Pe(Qt,1):n(xe).type==="snapshot"?Pe(St,2):Pe(dr,-1)})}ua(w,Pe=>u(vt,Pe),()=>n(vt)),L(()=>{z(D,n(xe).title),z(Be,n(xe).type==="context"?"Context Detail":n(xe).type==="tool"||n(xe).type==="tool-call"||n(xe).type==="tool-result"?"Tool Event":n(xe).type==="snapshot"?"Snapshot":"Prompt Detail")}),j("click",p,Pe=>{Pe.target===Pe.currentTarget&&bt()}),j("keydown",w,Pe=>{Pe.key==="Escape"&&bt()}),j("click",Se,bt),x(o,p)};A(Ml,o=>{n(xe)&&o(zl)})}L((o,p,w)=>{nt(Ua,1,o),nt(xi,1,p),nt($i,1,w)},[()=>rt(at("rounded-lg px-2 py-1.5 text-[11px] transition-colors",i()==="overview"?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted")),()=>rt(at("rounded-lg px-2 py-1.5 text-[11px] transition-colors",i()==="explore"?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted")),()=>rt(at("rounded-lg px-2 py-1.5 text-[11px] transition-colors",i()==="evidence"?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted"))]),j("input",Ha,Wt),Oa(Ha,()=>n(v),o=>u(v,o)),j("click",Ua,()=>X("overview")),j("click",xi,()=>X("explore")),j("click",$i,()=>X("evidence")),x(e,un),wn()}xa(["click","input","keydown"]);var mm=b('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),bm=b("<!> <span>확인 중...</span>",1),gm=b("<!> <span>설정 필요</span>",1),hm=b('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),_m=b('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!> <!>',1),ym=b('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/80 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text-muted">AI Provider 확인 중...</div></div></div>'),wm=b('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-primary/30 bg-dl-primary/5 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text">AI Provider가 설정되지 않았습니다</div> <div class="text-[11px] text-dl-text-muted mt-0.5">대화를 시작하려면 Provider를 설정해주세요</div></div> <button class="px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors flex-shrink-0">설정하기</button></div>'),km=b('<div class="surface-panel w-[400px] flex-shrink-0 border-l border-dl-border/60 bg-dl-bg-card/35 pt-11"><!></div>'),Cm=b('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),Sm=b('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),Em=b('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),Mm=b('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),zm=b('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),Am=b('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),Tm=b('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),Nm=b('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),Om=b('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),Im=b('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),Lm=b('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),Pm=b('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @anthropic-ai/claude-code</div></div></div>'),Rm=b('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">인증</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">claude auth login</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">Claude Pro 또는 Max 구독이 필요합니다</span></div>',1),jm=b('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2">설치 완료 후 새로고침하세요</div></div>'),Dm=b("<!> 브라우저에서 로그인 중...",1),Fm=b("<!> OpenAI 계정으로 로그인",1),Bm=b('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2.5">ChatGPT 계정으로 로그인하여 사용하세요</div> <button class="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div></div>'),$m=b('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),Vm=b('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),Gm=b("<button> <!></button>"),Hm=b('<div class="flex flex-wrap gap-1.5"></div>'),Um=b('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),Wm=b('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),qm=b('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),Km=b('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),Ym=b('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),Jm=b('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),Xm=b('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),Qm=b("<!> <!> <!> <!> <!> <!> <!>",1),Zm=b('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),eb=b('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),tb=b('<div class="fixed inset-0 z-[190] bg-black/50 backdrop-blur-sm" role="presentation"><div class="mobile-workspace-sheet absolute inset-x-0 bottom-0 top-[12vh] rounded-t-[24px] border border-dl-border bg-dl-bg-card shadow-2xl" role="dialog" aria-modal="true" aria-labelledby="mobile-workspace-title" tabindex="-1"><div class="flex items-center justify-between px-4 pt-2 pb-1"><div class="flex-1 flex justify-center"><div class="h-1.5 w-14 rounded-full bg-dl-border/80"></div></div> <button class="rounded-lg p-1.5 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text" aria-label="워크스페이스 닫기"><!></button></div> <div id="mobile-workspace-title" class="px-4 pb-2 text-[11px] uppercase tracking-[0.16em] text-dl-text-dim">Workspace</div> <!></div></div>'),rb=b('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),nb=b('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),ab=b('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-0 left-0 right-0 z-10 pointer-events-none"><div class="flex items-center justify-between px-3 h-11 pointer-events-auto" style="background: linear-gradient(to bottom, rgba(5,8,17,0.92) 40%, transparent);"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center gap-1"><button><!> <span> </span></button> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <div class="w-px h-4 bg-dl-border mx-1"></div> <button aria-label="AI Provider 설정 열기"><!> <!></button></div></div> <!></div> <div class="flex flex-1 min-h-0"><div class="min-w-0 flex-1"><!></div> <!></div></div></div>  <!> <!> <!> <!>',1);function ib(e,t){yn(t,!0);let r=F(""),a=F(!1),i=F(null),l=F(ut({})),s=F(ut({})),c=F(null),v=F(null),m=F(ut([])),g=F(!0),y=F(0),C=F(!0),P=F(""),E=F(!1),O=F(null),_=F(ut({})),M=F(ut({})),R=F(""),V=F(!1),h=F(null),N=F(""),G=F(!1),K=F(""),S=F(0),W=F(null),q=F(!1),_e=F(ut({})),et=F(null),me=F(null),ve=F(null);const H=Jv();let we=F(!1);function Ye(){u(we,window.innerWidth<=768),n(we)?(u(g,!1),H.close()):H.userPinnedCompany||H.open("overview")}ln(()=>(Ye(),window.addEventListener("resize",Ye),()=>window.removeEventListener("resize",Ye))),ln(()=>{!n(E)||!n(et)||requestAnimationFrame(()=>{var o;return(o=n(et))==null?void 0:o.focus()})}),ln(()=>{!n(xe)||!n(me)||requestAnimationFrame(()=>{var o;return(o=n(me))==null?void 0:o.focus()})}),ln(()=>{!n(we)||!H.isOpen||!n(ve)||requestAnimationFrame(()=>{var o;return(o=n(ve))==null?void 0:o.focus()})});let xe=F(null),vt=F(""),Y=F("error"),zt=F(!1);function Ce(o,p="error",w=4e3){u(vt,o,!0),u(Y,p,!0),u(zt,!0),setTimeout(()=>{u(zt,!1)},w)}const k=Gv();ln(()=>{re()});let J=F(ut({})),U=F(ut({}));async function re(){var o,p,w;u(C,!0);try{const I=await $u();u(l,I.providers||{},!0),u(s,I.ollama||{},!0),u(J,I.codex||{},!0),u(U,I.claudeCode||{},!0),u(_e,I.chatgpt||{},!0),I.version&&u(P,I.version,!0);const B=localStorage.getItem("dartlab-provider"),$=localStorage.getItem("dartlab-model");if(B&&((o=n(l)[B])!=null&&o.available)){u(c,B,!0),u(O,B,!0),await qa(B,$),await he(B);const D=n(_)[B]||[];$&&D.includes($)?u(v,$,!0):D.length>0&&(u(v,D[0],!0),localStorage.setItem("dartlab-model",n(v))),u(m,D,!0),u(C,!1);return}if(B&&n(l)[B]){u(c,B,!0),u(O,B,!0),await he(B);const D=n(_)[B]||[];u(m,D,!0),$&&D.includes($)?u(v,$,!0):D.length>0&&u(v,D[0],!0),u(C,!1);return}for(const D of["chatgpt","codex","ollama"])if((p=n(l)[D])!=null&&p.available){u(c,D,!0),u(O,D,!0),await qa(D),await he(D);const de=n(_)[D]||[];u(m,de,!0),u(v,((w=n(l)[D])==null?void 0:w.model)||(de.length>0?de[0]:null),!0),n(v)&&localStorage.setItem("dartlab-model",n(v));break}}catch{}u(C,!1)}async function he(o){u(M,{...n(M),[o]:!0},!0);try{const p=await Vu(o);u(_,{...n(_),[o]:p.models||[]},!0)}catch{u(_,{...n(_),[o]:[]},!0)}u(M,{...n(M),[o]:!1},!0)}async function ge(o){var w;u(c,o,!0),u(v,null),u(O,o,!0),localStorage.setItem("dartlab-provider",o),localStorage.removeItem("dartlab-model"),u(R,""),u(h,null);try{await qa(o)}catch{}await he(o);const p=n(_)[o]||[];if(u(m,p,!0),p.length>0){u(v,((w=n(l)[o])==null?void 0:w.model)||p[0],!0),localStorage.setItem("dartlab-model",n(v));try{await qa(o,n(v))}catch{}}}async function ee(o){u(v,o,!0),localStorage.setItem("dartlab-model",o);try{await qa(n(c),o)}catch{}}function ct(o){n(O)===o?u(O,null):(u(O,o,!0),he(o))}async function xt(){const o=n(R).trim();if(!(!o||!n(c))){u(V,!0),u(h,null);try{const p=await qa(n(c),n(v),o);p.available?(u(h,"success"),n(l)[n(c)]={...n(l)[n(c)],available:!0,model:p.model},!n(v)&&p.model&&u(v,p.model,!0),await he(n(c)),u(m,n(_)[n(c)]||[],!0),Ce("API 키 인증 성공","success")):u(h,"error")}catch{u(h,"error")}u(V,!1)}}async function Dt(){if(!n(q)){u(q,!0);try{const{authUrl:o}=await Hu();window.open(o,"dartlab-oauth","width=600,height=700");const p=setInterval(async()=>{var w;try{const I=await Uu();I.done&&(clearInterval(p),u(q,!1),I.error?Ce(`인증 실패: ${I.error}`):(Ce("ChatGPT 인증 성공","success"),await re(),(w=n(l).chatgpt)!=null&&w.available&&await ge("chatgpt")))}catch{clearInterval(p),u(q,!1)}},2e3);setTimeout(()=>{clearInterval(p),n(q)&&(u(q,!1),Ce("인증 시간이 초과되었습니다. 다시 시도해주세요."))},12e4)}catch(o){u(q,!1),Ce(`OAuth 시작 실패: ${o.message}`)}}}async function ft(){try{await Wu(),u(_e,{authenticated:!1},!0),n(c)==="chatgpt"&&u(l,{...n(l),chatgpt:{...n(l).chatgpt,available:!1}},!0),Ce("ChatGPT 로그아웃 완료","success"),await re()}catch{Ce("로그아웃 실패")}}function cr(){const o=n(N).trim();!o||n(G)||(u(G,!0),u(K,"준비 중..."),u(S,0),u(W,Gu(o,{onProgress(p){p.total&&p.completed!==void 0?(u(S,Math.round(p.completed/p.total*100),!0),u(K,`다운로드 중... ${n(S)}%`)):p.status&&u(K,p.status,!0)},async onDone(){u(G,!1),u(W,null),u(N,""),u(K,""),u(S,0),Ce(`${o} 다운로드 완료`,"success"),await he("ollama"),u(m,n(_).ollama||[],!0),n(m).includes(o)&&await ee(o)},onError(p){u(G,!1),u(W,null),u(K,""),u(S,0),Ce(`다운로드 실패: ${p}`)}}),!0))}function Ae(){n(W)&&(n(W).abort(),u(W,null)),u(G,!1),u(N,""),u(K,""),u(S,0)}function De(){u(g,!n(g))}function He(o="explore"){H.open(o)}function Vt(){H.close()}function Wt(o,p){if(!o||!p)return;const w=o.corpName||o.company||o.stockCode;u(r,`${w}의 ${p.label} 데이터를 바탕으로 핵심 포인트를 요약해줘`),H.selectCompany(o,{pin:!0}),He("evidence")}function wt(o,p=null){H.openEvidence(o,p)}function kt(){if(u(R,""),u(h,null),n(c))u(O,n(c),!0);else{const o=Object.keys(n(l));u(O,o.length>0?o[0]:null,!0)}u(E,!0),n(O)&&he(n(O))}function ur(o){var p,w,I,B;if(o)for(let $=o.messages.length-1;$>=0;$--){const D=o.messages[$];if(D.role==="assistant"&&((p=D.meta)!=null&&p.stockCode||(w=D.meta)!=null&&w.company||D.company)){H.syncCompanyFromMessage({company:((I=D.meta)==null?void 0:I.company)||D.company,stockCode:(B=D.meta)==null?void 0:B.stockCode},H.selectedCompany);return}}}function Gt(){k.createConversation(),H.clearEvidenceSelection(),u(r,""),u(a,!1),n(i)&&(n(i).abort(),u(i,null))}function Ct(o){k.setActive(o),H.clearEvidenceSelection(),ur(k.active),u(r,""),u(a,!1),n(i)&&(n(i).abort(),u(i,null))}function Xt(o){u(xe,o,!0)}function Fe(){n(xe)&&(k.deleteConversation(n(xe)),u(xe,null))}function mt(){var p;const o=k.active;if(!o)return null;for(let w=o.messages.length-1;w>=0;w--){const I=o.messages[w];if(I.role==="assistant"&&((p=I.meta)!=null&&p.stockCode))return I.meta.stockCode}return null}async function be(){var Be,Se,_t;const o=n(r).trim();if(!o||n(a))return;if(!n(c)||!((Be=n(l)[n(c)])!=null&&Be.available)){Ce("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),kt();return}k.activeId||k.createConversation();const p=k.activeId;k.addMessage("user",o),u(r,""),u(a,!0),k.addMessage("assistant",""),k.updateLastMessage({loading:!0,startedAt:Date.now()}),Ci(y);const w=k.active,I=[];let B=null;if(w){const ce=w.messages.slice(0,-2);for(const ie of ce)if((ie.role==="user"||ie.role==="assistant")&&ie.text&&ie.text.trim()&&!ie.error&&!ie.loading){const Le={role:ie.role,text:ie.text};ie.role==="assistant"&&((Se=ie.meta)!=null&&Se.stockCode)&&(Le.meta={company:ie.meta.company||ie.company,stockCode:ie.meta.stockCode,modules:ie.meta.includedModules||null},B=ie.meta.stockCode),I.push(Le)}}const $=((_t=H.selectedCompany)==null?void 0:_t.stockCode)||B||mt();function D(){return k.activeId!==p}const de=Ju($,o,{provider:n(c),model:n(v)},{onMeta(ce){var dr;if(D())return;const ie=k.active,Le=ie==null?void 0:ie.messages[ie.messages.length-1],St={meta:{...(Le==null?void 0:Le.meta)||{},...ce}};ce.company&&(St.company=ce.company,k.activeId&&((dr=k.active)==null?void 0:dr.title)==="새 대화"&&k.updateTitle(k.activeId,ce.company)),ce.stockCode&&(St.stockCode=ce.stockCode),(ce.company||ce.stockCode)&&H.syncCompanyFromMessage(ce,H.selectedCompany),k.updateLastMessage(St)},onSnapshot(ce){D()||k.updateLastMessage({snapshot:ce})},onContext(ce){if(D())return;const ie=k.active;if(!ie)return;const Le=ie.messages[ie.messages.length-1],Qt=(Le==null?void 0:Le.contexts)||[];k.updateLastMessage({contexts:[...Qt,{module:ce.module,label:ce.label,text:ce.text}]})},onSystemPrompt(ce){D()||k.updateLastMessage({systemPrompt:ce.text,userContent:ce.userContent||null})},onToolCall(ce){if(D())return;const ie=k.active;if(!ie)return;const Le=ie.messages[ie.messages.length-1],Qt=(Le==null?void 0:Le.toolEvents)||[];k.updateLastMessage({toolEvents:[...Qt,{type:"call",name:ce.name,arguments:ce.arguments}]})},onToolResult(ce){if(D())return;const ie=k.active;if(!ie)return;const Le=ie.messages[ie.messages.length-1],Qt=(Le==null?void 0:Le.toolEvents)||[];k.updateLastMessage({toolEvents:[...Qt,{type:"result",name:ce.name,result:ce.result}]})},onChunk(ce){if(D())return;const ie=k.active;if(!ie)return;const Le=ie.messages[ie.messages.length-1];k.updateLastMessage({text:((Le==null?void 0:Le.text)||"")+ce}),Ci(y)},onDone(){if(D())return;const ce=k.active,ie=ce==null?void 0:ce.messages[ce.messages.length-1],Le=ie!=null&&ie.startedAt?((Date.now()-ie.startedAt)/1e3).toFixed(1):null;k.updateLastMessage({loading:!1,duration:Le}),k.flush(),u(a,!1),u(i,null),Ci(y)},onError(ce,ie,Le){D()||(k.updateLastMessage({text:`오류: ${ce}`,loading:!1,error:!0}),k.flush(),ie==="relogin"||ie==="login"?(Ce(`${ce} — 설정에서 재로그인하세요`),kt()):Ce(ie==="check_headers"||ie==="check_endpoint"||ie==="check_client_id"?`${ce} — ChatGPT API 변경 감지. 업데이트를 확인하세요`:ie==="rate_limit"?"요청이 너무 많습니다. 잠시 후 다시 시도해주세요":ce),u(a,!1),u(i,null))}},I);u(i,de,!0)}function Je(){n(i)&&(n(i).abort(),u(i,null),u(a,!1),k.updateLastMessage({loading:!1}),k.flush())}function At(){const o=k.active;if(!o||o.messages.length<2)return;let p="";for(let w=o.messages.length-1;w>=0;w--)if(o.messages[w].role==="user"){p=o.messages[w].text;break}p&&(k.removeLastMessage(),k.removeLastMessage(),u(r,p,!0),requestAnimationFrame(()=>{be()}))}function Ft(){const o=k.active;if(!o)return;let p=`# ${o.title}

`;for(const $ of o.messages)$.role==="user"?p+=`## You

${$.text}

`:$.role==="assistant"&&$.text&&(p+=`## DartLab

${$.text}

`);const w=new Blob([p],{type:"text/markdown;charset=utf-8"}),I=URL.createObjectURL(w),B=document.createElement("a");B.href=I,B.download=`${o.title||"dartlab-chat"}.md`,B.click(),URL.revokeObjectURL(I),Ce("대화가 마크다운으로 내보내졌습니다","success")}function tr(o){(o.metaKey||o.ctrlKey)&&o.key==="n"&&(o.preventDefault(),Gt()),(o.metaKey||o.ctrlKey)&&o.shiftKey&&o.key==="S"&&(o.preventDefault(),De()),o.key==="Escape"&&n(E)?u(E,!1):o.key==="Escape"&&n(xe)?u(xe,null):o.key==="Escape"&&H.isOpen&&H.close()}let rr=ne(()=>{var o;return((o=k.active)==null?void 0:o.messages)||[]}),vr=ne(()=>k.active&&k.active.messages.length>0),qr=ne(()=>{var o;return!n(C)&&(!n(c)||!((o=n(l)[n(c)])!=null&&o.available))}),Cn=ne(()=>{for(let o=n(rr).length-1;o>=0;o--)if(n(rr)[o].role==="assistant")return n(rr)[o];return null});const Xn=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var Pt=ab();tl("keydown",eo,tr);var it=Z(Pt),fr=d(it);{var X=o=>{var p=mm();j("click",p,()=>{u(g,!1)}),x(o,p)};A(fr,o=>{n(we)&&n(g)&&o(X)})}var Ne=f(fr,2),bt=d(Ne);{let o=ne(()=>n(we)?!0:n(g));Pf(bt,{get conversations(){return k.conversations},get activeId(){return k.activeId},get open(){return n(o)},get version(){return n(P)},onNewChat:()=>{Gt(),n(we)&&u(g,!1)},onSelect:p=>{Ct(p),n(we)&&u(g,!1)},onDelete:Xt})}var ot=f(Ne,2),ht=d(ot),pr=d(ht),nr=d(pr),Er=d(nr);{var Pr=o=>{bf(o,{size:18})},Bn=o=>{mf(o,{size:18})};A(Er,o=>{n(g)?o(Pr):o(Bn,-1)})}var Sn=f(nr,2),un=d(Sn),ba=d(un);hr(ba,{size:12});var Va=f(ba,2),Li=d(Va),pi=f(un,2),pl=d(pi);cf(pl,{size:15});var Pi=f(pi,2),xl=d(Pi);Ka(xl,{size:15});var Ri=f(Pi,2),ji=d(Ri);uf(ji,{size:15});var Ga=f(Ri,4),Ha=d(Ga);{var ml=o=>{var p=bm(),w=Z(p);Lr(w,{size:12,class:"animate-spin"}),x(o,p)},bl=o=>{var p=gm(),w=Z(p);_a(w,{size:12}),x(o,p)},Di=o=>{var p=_m(),w=f(Z(p),2),I=d(w),B=f(w,2);{var $=Be=>{var Se=hm(),_t=f(Z(Se),2),ce=d(_t);L(()=>z(ce,n(v))),x(Be,Se)};A(B,Be=>{n(v)&&Be($)})}var D=f(B,2);{var de=Be=>{Lr(Be,{size:10,class:"animate-spin text-dl-primary-light"})};A(D,Be=>{n(G)&&Be(de)})}L(()=>z(I,n(c))),x(o,p)};A(Ha,o=>{n(C)?o(ml):n(qr)?o(bl,1):o(Di,-1)})}var gl=f(Ha,2);_f(gl,{size:12});var Fi=f(pr,2);{var hl=o=>{var p=ym(),w=d(p);Lr(w,{size:16,class:"text-dl-text-dim animate-spin flex-shrink-0"}),x(o,p)},_l=o=>{var p=wm(),w=d(p);_a(w,{size:16,class:"text-dl-primary-light flex-shrink-0"});var I=f(w,4);j("click",I,()=>kt()),x(o,p)};A(Fi,o=>{n(C)&&!n(E)?o(hl):n(qr)&&!n(E)&&o(_l,1)})}var Bi=f(ht,2),Ua=d(Bi),xi=d(Ua);{var $i=o=>{Bp(o,{get messages(){return n(rr)},get isLoading(){return n(a)},get scrollTrigger(){return n(y)},get selectedCompany(){return H.selectedCompany},onSend:be,onStop:Je,onRegenerate:At,onExport:Ft,onOpenExplorer:He,onOpenEvidence:wt,get inputText(){return n(r)},set inputText(p){u(r,p,!0)}})},yl=o=>{Uf(o,{get selectedCompany(){return H.selectedCompany},onSend:be,onOpenExplorer:He,get inputText(){return n(r)},set inputText(p){u(r,p,!0)}})};A(xi,o=>{n(vr)?o($i):o(yl,-1)})}var wl=f(Ua,2);{var kl=o=>{var p=km(),w=d(p);xs(w,{get selectedCompany(){return H.selectedCompany},get recentCompanies(){return H.recentCompanies},get activeTab(){return H.activeTab},get evidenceMessage(){return n(Cn)},get activeEvidenceSection(){return H.activeEvidenceSection},get selectedEvidenceIndex(){return H.selectedEvidenceIndex},onSelectCompany:I=>H.selectCompany(I,{pin:!0}),onChangeTab:I=>H.setTab(I),onAskAboutModule:Wt,onNotify:Ce,onClose:Vt}),x(o,p)};A(wl,o=>{!n(we)&&H.isOpen&&o(kl)})}var mi=f(it,2);{var Cl=o=>{var p=eb(),w=d(p),I=d(w),B=d(I),$=f(d(B),2),D=d($);Ja(D,{size:18});var de=f(I,2),Be=d(de);ze(Be,21,()=>Object.entries(n(l)),Me,(St,dr)=>{var Pe=ne(()=>el(n(dr),2));let Oe=()=>n(Pe)[0],ke=()=>n(Pe)[1];const Rt=ne(()=>Oe()===n(c)),en=ne(()=>n(O)===Oe()),Br=ne(()=>ke().auth==="api_key"),$n=ne(()=>ke().auth==="cli"),En=ne(()=>n(_)[Oe()]||[]),Mn=ne(()=>n(M)[Oe()]);var tn=Zm(),Vn=d(tn),Gn=d(Vn),Hn=f(Gn,2),Un=d(Hn),Qn=d(Un),Zn=d(Qn),Te=f(Qn,2);{var Re=ue=>{var Q=Cm();x(ue,Q)};A(Te,ue=>{n(Rt)&&ue(Re)})}var Tt=f(Un,2),gt=d(Tt),st=f(Hn,2),Nt=d(st);{var qt=ue=>{Ia(ue,{size:16,class:"text-dl-success"})},Ht=ue=>{var Q=Sm(),le=Z(Q);cs(le,{size:14,class:"text-amber-400"}),x(ue,Q)},qe=ue=>{var Q=Em(),le=Z(Q);kf(le,{size:14,class:"text-dl-text-dim"}),x(ue,Q)};A(Nt,ue=>{ke().available?ue(qt):n(Br)?ue(Ht,1):n($n)&&!ke().available&&ue(qe,2)})}var Ke=f(Vn,2);{var te=ue=>{var Q=Qm(),le=Z(Q);{var Ee=Xe=>{var Ot=zm(),Bt=d(Ot),ir=d(Bt),wr=f(Bt,2),It=d(wr),lr=f(It,2),Et=d(lr);{var Yt=pe=>{Lr(pe,{size:12,class:"animate-spin"})},yt=pe=>{cs(pe,{size:12})};A(Et,pe=>{n(V)?pe(Yt):pe(yt,-1)})}var se=f(wr,2);{var fe=pe=>{var dt=Mm(),lt=d(dt);_a(lt,{size:12}),x(pe,dt)};A(se,pe=>{n(h)==="error"&&pe(fe)})}L(pe=>{z(ir,ke().envKey?`환경변수 ${ke().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),gn(It,"placeholder",Oe()==="openai"?"sk-...":Oe()==="claude"?"sk-ant-...":"API Key"),lr.disabled=pe},[()=>!n(R).trim()||n(V)]),j("keydown",It,pe=>{pe.key==="Enter"&&xt()}),Oa(It,()=>n(R),pe=>u(R,pe)),j("click",lr,xt),x(Xe,Ot)};A(le,Xe=>{n(Br)&&!ke().available&&Xe(Ee)})}var Zt=f(le,2);{var Kt=Xe=>{var Ot=Tm(),Bt=d(Ot),ir=d(Bt);Ia(ir,{size:13,class:"text-dl-success"});var wr=f(Bt,2),It=d(wr),lr=f(It,2);{var Et=yt=>{var se=Am(),fe=d(se);{var pe=lt=>{Lr(lt,{size:10,class:"animate-spin"})},dt=lt=>{var Ut=an("변경");x(lt,Ut)};A(fe,lt=>{n(V)?lt(pe):lt(dt,-1)})}L(()=>se.disabled=n(V)),j("click",se,xt),x(yt,se)},Yt=ne(()=>n(R).trim());A(lr,yt=>{n(Yt)&&yt(Et)})}j("keydown",It,yt=>{yt.key==="Enter"&&xt()}),Oa(It,()=>n(R),yt=>u(R,yt)),x(Xe,Ot)};A(Zt,Xe=>{n(Br)&&ke().available&&Xe(Kt)})}var yr=f(Zt,2);{var Rr=Xe=>{var Ot=Nm(),Bt=f(d(Ot),2),ir=d(Bt);La(ir,{size:14});var wr=f(ir,2);ds(wr,{size:10,class:"ml-auto"}),x(Xe,Ot)},ar=Xe=>{var Ot=Om(),Bt=d(Ot),ir=d(Bt);_a(ir,{size:14}),x(Xe,Ot)};A(yr,Xe=>{Oe()==="ollama"&&!n(s).installed?Xe(Rr):Oe()==="ollama"&&n(s).installed&&!n(s).running&&Xe(ar,1)})}var er=f(yr,2);{var Ir=Xe=>{var Ot=jm(),Bt=d(Ot);{var ir=It=>{var lr=Lm(),Et=Z(lr),Yt=d(Et),yt=f(Et,2),se=d(yt);{var fe=Lt=>{var $t=Im();x(Lt,$t)};A(se,Lt=>{n(J).installed||Lt(fe)})}var pe=f(se,2),dt=d(pe),lt=d(dt),Ut=f(yt,2),Jt=d(Ut);_a(Jt,{size:12,class:"text-amber-400 flex-shrink-0"}),L(()=>{z(Yt,n(J).installed?"Codex CLI가 설치되었지만 인증이 필요합니다":"Codex CLI 설치가 필요합니다"),z(lt,n(J).installed?"1.":"2.")}),x(It,lr)},wr=It=>{var lr=Rm(),Et=Z(lr),Yt=d(Et),yt=f(Et,2),se=d(yt);{var fe=Lt=>{var $t=Pm();x(Lt,$t)};A(se,Lt=>{n(U).installed||Lt(fe)})}var pe=f(se,2),dt=d(pe),lt=d(dt),Ut=f(yt,2),Jt=d(Ut);_a(Jt,{size:12,class:"text-amber-400 flex-shrink-0"}),L(()=>{z(Yt,n(U).installed&&!n(U).authenticated?"Claude Code가 설치되었지만 인증이 필요합니다":"Claude Code CLI 설치가 필요합니다"),z(lt,n(U).installed?"1.":"2.")}),x(It,lr)};A(Bt,It=>{Oe()==="codex"?It(ir):Oe()==="claude-code"&&It(wr,1)})}x(Xe,Ot)};A(er,Xe=>{n($n)&&!ke().available&&Xe(Ir)})}var Kr=f(er,2);{var jr=Xe=>{var Ot=Bm(),Bt=f(d(Ot),2),ir=d(Bt);{var wr=Yt=>{var yt=Dm(),se=Z(yt);Lr(se,{size:14,class:"animate-spin"}),x(Yt,yt)},It=Yt=>{var yt=Fm(),se=Z(yt);pf(se,{size:14}),x(Yt,yt)};A(ir,Yt=>{n(q)?Yt(wr):Yt(It,-1)})}var lr=f(Bt,2),Et=d(lr);_a(Et,{size:12,class:"text-amber-400 flex-shrink-0"}),L(()=>Bt.disabled=n(q)),j("click",Bt,Dt),x(Xe,Ot)};A(Kr,Xe=>{ke().auth==="oauth"&&!ke().available&&Xe(jr)})}var $r=f(Kr,2);{var Yr=Xe=>{var Ot=$m(),Bt=d(Ot),ir=d(Bt),wr=d(ir);Ia(wr,{size:13,class:"text-dl-success"});var It=f(ir,2),lr=d(It);xf(lr,{size:11}),j("click",It,ft),x(Xe,Ot)};A($r,Xe=>{ke().auth==="oauth"&&ke().available&&Xe(Yr)})}var zn=f($r,2);{var An=Xe=>{var Ot=Xm(),Bt=d(Ot),ir=f(d(Bt),2);{var wr=fe=>{Lr(fe,{size:12,class:"animate-spin text-dl-text-dim"})};A(ir,fe=>{n(Mn)&&fe(wr)})}var It=f(Bt,2);{var lr=fe=>{var pe=Vm(),dt=d(pe);Lr(dt,{size:14,class:"animate-spin"}),x(fe,pe)},Et=fe=>{var pe=Hm();ze(pe,21,()=>n(En),Me,(dt,lt)=>{var Ut=Gm(),Jt=d(Ut),Lt=f(Jt);{var $t=Mt=>{lf(Mt,{size:10,class:"inline ml-1"})};A(Lt,Mt=>{n(lt)===n(v)&&n(Rt)&&Mt($t)})}L(Mt=>{nt(Ut,1,Mt),z(Jt,`${n(lt)??""} `)},[()=>rt(at("px-3 py-1.5 rounded-lg text-[11px] border transition-all",n(lt)===n(v)&&n(Rt)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),j("click",Ut,()=>{Oe()!==n(c)&&ge(Oe()),ee(n(lt))}),x(dt,Ut)}),x(fe,pe)},Yt=fe=>{var pe=Um();x(fe,pe)};A(It,fe=>{n(Mn)&&n(En).length===0?fe(lr):n(En).length>0?fe(Et,1):fe(Yt,-1)})}var yt=f(It,2);{var se=fe=>{var pe=Jm(),dt=d(pe),lt=f(d(dt),2),Ut=f(d(lt));ds(Ut,{size:9});var Jt=f(dt,2);{var Lt=Mt=>{var or=Wm(),kr=d(or),xr=d(kr),vn=d(xr);Lr(vn,{size:12,class:"animate-spin text-dl-primary-light"});var jt=f(xr,2),mr=f(kr,2),Dr=d(mr),Mr=f(mr,2),ga=d(Mr);L(()=>{rl(Dr,`width: ${n(S)??""}%`),z(ga,n(K))}),j("click",jt,Ae),x(Mt,or)},$t=Mt=>{var or=Ym(),kr=Z(or),xr=d(kr),vn=f(xr,2),jt=d(vn);La(jt,{size:12});var mr=f(kr,2);ze(mr,21,()=>Xn,Me,(Dr,Mr)=>{const ga=ne(()=>n(En).some(Wa=>Wa===n(Mr).name||Wa===n(Mr).name.split(":")[0]));var Hi=ye(),Al=Z(Hi);{var Tl=Wa=>{var Nl=Km(),Ao=d(Nl),To=d(Ao),No=d(To),Ld=d(No),Oo=f(No,2),Pd=d(Oo),Rd=f(Oo,2);{var jd=Ol=>{var Lo=qm(),Gd=d(Lo);L(()=>z(Gd,n(Mr).tag)),x(Ol,Lo)};A(Rd,Ol=>{n(Mr).tag&&Ol(jd)})}var Dd=f(To,2),Fd=d(Dd),Bd=f(Ao,2),Io=d(Bd),$d=d(Io),Vd=f(Io,2);La(Vd,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),L(()=>{z(Ld,n(Mr).name),z(Pd,n(Mr).size),z(Fd,n(Mr).desc),z($d,`${n(Mr).gb??""} GB`)}),j("click",Nl,()=>{u(N,n(Mr).name,!0),cr()}),x(Wa,Nl)};A(Al,Wa=>{n(ga)||Wa(Tl)})}x(Dr,Hi)}),L(Dr=>vn.disabled=Dr,[()=>!n(N).trim()]),j("keydown",xr,Dr=>{Dr.key==="Enter"&&cr()}),Oa(xr,()=>n(N),Dr=>u(N,Dr)),j("click",vn,cr),x(Mt,or)};A(Jt,Mt=>{n(G)?Mt(Lt):Mt($t,-1)})}x(fe,pe)};A(yt,fe=>{Oe()==="ollama"&&fe(se)})}x(Xe,Ot)};A(zn,Xe=>{(ke().available||n(Br)||n($n)||ke().auth==="oauth")&&Xe(An)})}x(ue,Q)};A(Ke,ue=>{(n(en)||n(Rt))&&ue(te)})}L((ue,Q)=>{nt(tn,1,ue),nt(Gn,1,Q),z(Zn,ke().label||Oe()),z(gt,ke().desc||"")},[()=>rt(at("rounded-xl border transition-all",n(Rt)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>rt(at("w-2.5 h-2.5 rounded-full flex-shrink-0",ke().available?"bg-dl-success":n(Br)?"bg-amber-400":"bg-dl-text-dim"))]),j("click",Vn,()=>{ke().available||n(Br)?Oe()===n(c)?ct(Oe()):ge(Oe()):ct(Oe())}),x(St,tn)});var Se=f(de,2),_t=d(Se),ce=d(_t);{var ie=St=>{var dr=an();L(()=>{var Pe;return z(dr,`현재: ${(((Pe=n(l)[n(c)])==null?void 0:Pe.label)||n(c))??""} / ${n(v)??""}`)}),x(St,dr)},Le=St=>{var dr=an();L(()=>{var Pe;return z(dr,`현재: ${(((Pe=n(l)[n(c)])==null?void 0:Pe.label)||n(c))??""}`)}),x(St,dr)};A(ce,St=>{n(c)&&n(v)?St(ie):n(c)&&St(Le,1)})}var Qt=f(_t,2);ua(w,St=>u(et,St),()=>n(et)),j("click",p,St=>{St.target===St.currentTarget&&u(E,!1)}),j("click",$,()=>u(E,!1)),j("click",Qt,()=>u(E,!1)),x(o,p)};A(mi,o=>{n(E)&&o(Cl)})}var Vi=f(mi,2);{var Sl=o=>{var p=tb(),w=d(p),I=d(w),B=f(d(I),2),$=d(B);Ja($,{size:16});var D=f(I,4);xs(D,{get selectedCompany(){return H.selectedCompany},get recentCompanies(){return H.recentCompanies},get activeTab(){return H.activeTab},get evidenceMessage(){return n(Cn)},get activeEvidenceSection(){return H.activeEvidenceSection},get selectedEvidenceIndex(){return H.selectedEvidenceIndex},onSelectCompany:de=>H.selectCompany(de,{pin:!0}),onChangeTab:de=>H.setTab(de),onAskAboutModule:Wt,onNotify:Ce,onClose:Vt}),ua(w,de=>u(ve,de),()=>n(ve)),j("click",p,de=>{de.target===de.currentTarget&&Vt()}),j("click",B,Vt),x(o,p)};A(Vi,o=>{n(we)&&H.isOpen&&o(Sl)})}var Gi=f(Vi,2);{var El=o=>{var p=rb(),w=d(p),I=f(d(w),4),B=d(I),$=f(B,2);ua(w,D=>u(me,D),()=>n(me)),j("click",p,D=>{D.target===D.currentTarget&&u(xe,null)}),j("click",B,()=>u(xe,null)),j("click",$,Fe),x(o,p)};A(Gi,o=>{n(xe)&&o(El)})}var Ml=f(Gi,2);{var zl=o=>{var p=nb(),w=d(p),I=d(w),B=d(I),$=f(I,2),D=d($);Ja(D,{size:14}),L(de=>{nt(w,1,de),z(B,n(vt))},[()=>rt(at("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",n(Y)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":n(Y)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),j("click",$,()=>{u(zt,!1)}),x(o,p)};A(Ml,o=>{n(zt)&&o(zl)})}L((o,p)=>{nt(Ne,1,rt(n(we)?n(g)?"sidebar-mobile":"hidden":"")),gn(nr,"aria-label",n(g)?"사이드바 접기":"사이드바 열기"),nt(un,1,o),gn(un,"aria-pressed",H.isOpen),z(Li,H.isOpen?"패널 닫기":"탐색 열기"),nt(Ga,1,p)},[()=>rt(at("flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] transition-colors",H.isOpen?"bg-dl-primary/10 text-dl-primary-light":"text-dl-text-dim hover:bg-white/5 hover:text-dl-text-muted")),()=>rt(at("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",n(C)?"text-dl-text-dim":n(qr)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),j("click",nr,De),j("click",un,()=>H.isOpen?Vt():He("explore")),j("click",Ga,()=>kt()),x(e,Pt),wn()}xa(["click","keydown"]);gu(ib,{target:document.getElementById("app")});
