var rc=Object.defineProperty;var hi=e=>{throw TypeError(e)};var nc=(e,t,n)=>t in e?rc(e,t,{enumerable:!0,configurable:!0,writable:!0,value:n}):e[t]=n;var hn=(e,t,n)=>nc(e,typeof t!="symbol"?t+"":t,n),vs=(e,t,n)=>t.has(e)||hi("Cannot "+n);var j=(e,t,n)=>(vs(e,t,"read from private field"),n?n.call(e):t.get(e)),Mt=(e,t,n)=>t.has(e)?hi("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,n),gt=(e,t,n,a)=>(vs(e,t,"write to private field"),a?a.call(e,n):t.set(e,n),n),mr=(e,t,n)=>(vs(e,t,"access private method"),n);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const o of document.querySelectorAll('link[rel="modulepreload"]'))a(o);new MutationObserver(o=>{for(const i of o)if(i.type==="childList")for(const s of i.addedNodes)s.tagName==="LINK"&&s.rel==="modulepreload"&&a(s)}).observe(document,{childList:!0,subtree:!0});function n(o){const i={};return o.integrity&&(i.integrity=o.integrity),o.referrerPolicy&&(i.referrerPolicy=o.referrerPolicy),o.crossOrigin==="use-credentials"?i.credentials="include":o.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function a(o){if(o.ep)return;o.ep=!0;const i=n(o);fetch(o.href,i)}})();const _s=!1;var Us=Array.isArray,ac=Array.prototype.indexOf,ro=Array.prototype.includes,es=Array.from,oc=Object.defineProperty,da=Object.getOwnPropertyDescriptor,Qi=Object.getOwnPropertyDescriptors,sc=Object.prototype,ic=Array.prototype,Gs=Object.getPrototypeOf,gi=Object.isExtensible;function xo(e){return typeof e=="function"}const lc=()=>{};function dc(e){return e()}function ws(e){for(var t=0;t<e.length;t++)e[t]()}function Zi(){var e,t,n=new Promise((a,o)=>{e=a,t=o});return{promise:n,resolve:e,reject:t}}function el(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const n=[];for(const a of e)if(n.push(a),n.length===t)break;return n}const Ir=2,lo=4,Ra=8,ts=1<<24,ga=16,Cn=32,Fa=64,ys=128,cn=512,zr=1024,Er=2048,kn=4096,Vr=8192,Nn=16384,co=32768,Kn=65536,bi=1<<17,cc=1<<18,uo=1<<19,tl=1<<20,In=1<<25,Da=65536,ks=1<<21,Hs=1<<22,ca=1<<23,Ln=Symbol("$state"),rl=Symbol("legacy props"),uc=Symbol(""),Sa=new class extends Error{constructor(){super(...arguments);hn(this,"name","StaleReactionError");hn(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var Yi;const nl=!!((Yi=globalThis.document)!=null&&Yi.contentType)&&globalThis.document.contentType.includes("xml");function vc(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function fc(e,t,n){throw new Error("https://svelte.dev/e/each_key_duplicate")}function pc(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function mc(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function xc(e){throw new Error("https://svelte.dev/e/effect_orphan")}function hc(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function gc(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function bc(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function _c(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function wc(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function yc(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const kc=1,Cc=2,al=4,Sc=8,$c=16,Mc=1,Tc=2,ol=4,zc=8,Ec=16,Ac=1,Ic=2,br=Symbol(),sl="http://www.w3.org/1999/xhtml",il="http://www.w3.org/2000/svg",Pc="http://www.w3.org/1998/Math/MathML",Nc="@attach";function Lc(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function Oc(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function ll(e){return e===this.v}function Rc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function dl(e){return!Rc(e,this.v)}let Io=!1,Dc=!1;function jc(){Io=!0}let _r=null;function no(e){_r=e}function wr(e,t=!1,n){_r={p:_r,i:!1,c:null,e:null,s:e,x:null,l:Io&&!t?{s:null,u:null,$:[]}:null}}function yr(e){var t=_r,n=t.e;if(n!==null){t.e=null;for(var a of n)zl(a)}return t.i=!0,_r=t.p,{}}function Po(){return!Io||_r!==null&&_r.l===null}let $a=[];function cl(){var e=$a;$a=[],ws(e)}function On(e){if($a.length===0&&!Co){var t=$a;queueMicrotask(()=>{t===$a&&cl()})}$a.push(e)}function Vc(){for(;$a.length>0;)cl()}function ul(e){var t=kt;if(t===null)return yt.f|=ca,e;if((t.f&co)===0&&(t.f&lo)===0)throw e;la(e,t)}function la(e,t){for(;t!==null;){if((t.f&ys)!==0){if((t.f&co)===0)throw e;try{t.b.error(e);return}catch(n){e=n}}t=t.parent}throw e}const Fc=-7169;function cr(e,t){e.f=e.f&Fc|t}function Ks(e){(e.f&cn)!==0||e.deps===null?cr(e,zr):cr(e,kn)}function vl(e){if(e!==null)for(const t of e)(t.f&Ir)===0||(t.f&Da)===0||(t.f^=Da,vl(t.deps))}function fl(e,t,n){(e.f&Er)!==0?t.add(e):(e.f&kn)!==0&&n.add(e),vl(e.deps),cr(e,zr)}const jo=new Set;let bt=null,Cs=null,Tr=null,Br=[],rs=null,Co=!1,ao=null,qc=1;var oa,Wa,Ea,Ya,Xa,Ja,sa,Tn,Qa,Wr,Ss,$s,Ms,Ts;const oi=class oi{constructor(){Mt(this,Wr);hn(this,"id",qc++);hn(this,"current",new Map);hn(this,"previous",new Map);Mt(this,oa,new Set);Mt(this,Wa,new Set);Mt(this,Ea,0);Mt(this,Ya,0);Mt(this,Xa,null);Mt(this,Ja,new Set);Mt(this,sa,new Set);Mt(this,Tn,new Map);hn(this,"is_fork",!1);Mt(this,Qa,!1)}skip_effect(t){j(this,Tn).has(t)||j(this,Tn).set(t,{d:[],m:[]})}unskip_effect(t){var n=j(this,Tn).get(t);if(n){j(this,Tn).delete(t);for(var a of n.d)cr(a,Er),Pn(a);for(a of n.m)cr(a,kn),Pn(a)}}process(t){var o;Br=[],this.apply();var n=ao=[],a=[];for(const i of t)mr(this,Wr,$s).call(this,i,n,a);if(ao=null,mr(this,Wr,Ss).call(this)){mr(this,Wr,Ms).call(this,a),mr(this,Wr,Ms).call(this,n);for(const[i,s]of j(this,Tn))hl(i,s)}else{Cs=this,bt=null;for(const i of j(this,oa))i(this);j(this,oa).clear(),j(this,Ea)===0&&mr(this,Wr,Ts).call(this),_i(a),_i(n),j(this,Ja).clear(),j(this,sa).clear(),Cs=null,(o=j(this,Xa))==null||o.resolve()}Tr=null}capture(t,n){n!==br&&!this.previous.has(t)&&this.previous.set(t,n),(t.f&ca)===0&&(this.current.set(t,t.v),Tr==null||Tr.set(t,t.v))}activate(){bt=this,this.apply()}deactivate(){bt===this&&(bt=null,Tr=null)}flush(){var t;if(Br.length>0)bt=this,pl();else if(j(this,Ea)===0&&!this.is_fork){for(const n of j(this,oa))n(this);j(this,oa).clear(),mr(this,Wr,Ts).call(this),(t=j(this,Xa))==null||t.resolve()}this.deactivate()}discard(){for(const t of j(this,Wa))t(this);j(this,Wa).clear()}increment(t){gt(this,Ea,j(this,Ea)+1),t&&gt(this,Ya,j(this,Ya)+1)}decrement(t){gt(this,Ea,j(this,Ea)-1),t&&gt(this,Ya,j(this,Ya)-1),!j(this,Qa)&&(gt(this,Qa,!0),On(()=>{gt(this,Qa,!1),mr(this,Wr,Ss).call(this)?Br.length>0&&this.flush():this.revive()}))}revive(){for(const t of j(this,Ja))j(this,sa).delete(t),cr(t,Er),Pn(t);for(const t of j(this,sa))cr(t,kn),Pn(t);this.flush()}oncommit(t){j(this,oa).add(t)}ondiscard(t){j(this,Wa).add(t)}settled(){return(j(this,Xa)??gt(this,Xa,Zi())).promise}static ensure(){if(bt===null){const t=bt=new oi;jo.add(bt),Co||On(()=>{bt===t&&t.flush()})}return bt}apply(){}};oa=new WeakMap,Wa=new WeakMap,Ea=new WeakMap,Ya=new WeakMap,Xa=new WeakMap,Ja=new WeakMap,sa=new WeakMap,Tn=new WeakMap,Qa=new WeakMap,Wr=new WeakSet,Ss=function(){return this.is_fork||j(this,Ya)>0},$s=function(t,n,a){t.f^=zr;for(var o=t.first;o!==null;){var i=o.f,s=(i&(Cn|Fa))!==0,d=s&&(i&zr)!==0,u=(i&Vr)!==0,p=d||j(this,Tn).has(o);if(!p&&o.fn!==null){s?u||(o.f^=zr):(i&lo)!==0?n.push(o):(i&(Ra|ts))!==0&&u?a.push(o):Oo(o)&&(so(o),(i&ga)!==0&&(j(this,sa).add(o),u&&cr(o,Er)));var x=o.first;if(x!==null){o=x;continue}}for(;o!==null;){var g=o.next;if(g!==null){o=g;break}o=o.parent}}},Ms=function(t){for(var n=0;n<t.length;n+=1)fl(t[n],j(this,Ja),j(this,sa))},Ts=function(){var i;if(jo.size>1){this.previous.clear();var t=bt,n=Tr,a=!0;for(const s of jo){if(s===this){a=!1;continue}const d=[];for(const[p,x]of this.current){if(s.current.has(p))if(a&&x!==s.current.get(p))s.current.set(p,x);else continue;d.push(p)}if(d.length===0)continue;const u=[...s.current.keys()].filter(p=>!this.current.has(p));if(u.length>0){var o=Br;Br=[];const p=new Set,x=new Map;for(const g of d)ml(g,u,p,x);if(Br.length>0){bt=s,s.apply();for(const g of Br)mr(i=s,Wr,$s).call(i,g,[],[]);s.deactivate()}Br=o}}bt=t,Tr=n}j(this,Tn).clear(),jo.delete(this)};let ua=oi;function Bc(e){var t=Co;Co=!0;try{for(var n;;){if(Vc(),Br.length===0&&(bt==null||bt.flush(),Br.length===0))return rs=null,n;pl()}}finally{Co=t}}function pl(){var e=null;try{for(var t=0;Br.length>0;){var n=ua.ensure();if(t++>1e3){var a,o;Uc()}n.process(Br),va.clear()}}finally{Br=[],rs=null,ao=null}}function Uc(){try{hc()}catch(e){la(e,rs)}}let gn=null;function _i(e){var t=e.length;if(t!==0){for(var n=0;n<t;){var a=e[n++];if((a.f&(Nn|Vr))===0&&Oo(a)&&(gn=new Set,so(a),a.deps===null&&a.first===null&&a.nodes===null&&a.teardown===null&&a.ac===null&&Pl(a),(gn==null?void 0:gn.size)>0)){va.clear();for(const o of gn){if((o.f&(Nn|Vr))!==0)continue;const i=[o];let s=o.parent;for(;s!==null;)gn.has(s)&&(gn.delete(s),i.push(s)),s=s.parent;for(let d=i.length-1;d>=0;d--){const u=i[d];(u.f&(Nn|Vr))===0&&so(u)}}gn.clear()}}gn=null}}function ml(e,t,n,a){if(!n.has(e)&&(n.add(e),e.reactions!==null))for(const o of e.reactions){const i=o.f;(i&Ir)!==0?ml(o,t,n,a):(i&(Hs|ga))!==0&&(i&Er)===0&&xl(o,t,a)&&(cr(o,Er),Pn(o))}}function xl(e,t,n){const a=n.get(e);if(a!==void 0)return a;if(e.deps!==null)for(const o of e.deps){if(ro.call(t,o))return!0;if((o.f&Ir)!==0&&xl(o,t,n))return n.set(o,!0),!0}return n.set(e,!1),!1}function Pn(e){var t=rs=e,n=t.b;if(n!=null&&n.is_pending&&(e.f&(lo|Ra|ts))!==0&&(e.f&co)===0){n.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var a=t.f;if(ao!==null&&t===kt&&(e.f&Ra)===0)return;if((a&(Fa|Cn))!==0){if((a&zr)===0)return;t.f^=zr}}Br.push(t)}function hl(e,t){if(!((e.f&Cn)!==0&&(e.f&zr)!==0)){(e.f&Er)!==0?t.d.push(e):(e.f&kn)!==0&&t.m.push(e),cr(e,zr);for(var n=e.first;n!==null;)hl(n,t),n=n.next}}function Gc(e){let t=0,n=ma(0),a;return()=>{Js()&&(r(n),Zs(()=>(t===0&&(a=ja(()=>e(()=>$o(n)))),t+=1,()=>{On(()=>{t-=1,t===0&&(a==null||a(),a=void 0,$o(n))})})))}}var Hc=Kn|uo;function Kc(e,t,n,a){new Wc(e,t,n,a)}var dn,Bs,zn,Aa,qr,En,nn,bn,Un,Ia,ia,Za,eo,to,Gn,Qo,hr,Yc,Xc,Jc,zs,Uo,Go,Es;class Wc{constructor(t,n,a,o){Mt(this,hr);hn(this,"parent");hn(this,"is_pending",!1);hn(this,"transform_error");Mt(this,dn);Mt(this,Bs,null);Mt(this,zn);Mt(this,Aa);Mt(this,qr);Mt(this,En,null);Mt(this,nn,null);Mt(this,bn,null);Mt(this,Un,null);Mt(this,Ia,0);Mt(this,ia,0);Mt(this,Za,!1);Mt(this,eo,new Set);Mt(this,to,new Set);Mt(this,Gn,null);Mt(this,Qo,Gc(()=>(gt(this,Gn,ma(j(this,Ia))),()=>{gt(this,Gn,null)})));var i;gt(this,dn,t),gt(this,zn,n),gt(this,Aa,s=>{var d=kt;d.b=this,d.f|=ys,a(s)}),this.parent=kt.b,this.transform_error=o??((i=this.parent)==null?void 0:i.transform_error)??(s=>s),gt(this,qr,vo(()=>{mr(this,hr,zs).call(this)},Hc))}defer_effect(t){fl(t,j(this,eo),j(this,to))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!j(this,zn).pending}update_pending_count(t){mr(this,hr,Es).call(this,t),gt(this,Ia,j(this,Ia)+t),!(!j(this,Gn)||j(this,Za))&&(gt(this,Za,!0),On(()=>{gt(this,Za,!1),j(this,Gn)&&oo(j(this,Gn),j(this,Ia))}))}get_effect_pending(){return j(this,Qo).call(this),r(j(this,Gn))}error(t){var n=j(this,zn).onerror;let a=j(this,zn).failed;if(!n&&!a)throw t;j(this,En)&&(Ar(j(this,En)),gt(this,En,null)),j(this,nn)&&(Ar(j(this,nn)),gt(this,nn,null)),j(this,bn)&&(Ar(j(this,bn)),gt(this,bn,null));var o=!1,i=!1;const s=()=>{if(o){Oc();return}o=!0,i&&yc(),j(this,bn)!==null&&Na(j(this,bn),()=>{gt(this,bn,null)}),mr(this,hr,Go).call(this,()=>{ua.ensure(),mr(this,hr,zs).call(this)})},d=u=>{try{i=!0,n==null||n(u,s),i=!1}catch(p){la(p,j(this,qr)&&j(this,qr).parent)}a&&gt(this,bn,mr(this,hr,Go).call(this,()=>{ua.ensure();try{return Gr(()=>{var p=kt;p.b=this,p.f|=ys,a(j(this,dn),()=>u,()=>s)})}catch(p){return la(p,j(this,qr).parent),null}}))};On(()=>{var u;try{u=this.transform_error(t)}catch(p){la(p,j(this,qr)&&j(this,qr).parent);return}u!==null&&typeof u=="object"&&typeof u.then=="function"?u.then(d,p=>la(p,j(this,qr)&&j(this,qr).parent)):d(u)})}}dn=new WeakMap,Bs=new WeakMap,zn=new WeakMap,Aa=new WeakMap,qr=new WeakMap,En=new WeakMap,nn=new WeakMap,bn=new WeakMap,Un=new WeakMap,Ia=new WeakMap,ia=new WeakMap,Za=new WeakMap,eo=new WeakMap,to=new WeakMap,Gn=new WeakMap,Qo=new WeakMap,hr=new WeakSet,Yc=function(){try{gt(this,En,Gr(()=>j(this,Aa).call(this,j(this,dn))))}catch(t){this.error(t)}},Xc=function(t){const n=j(this,zn).failed;n&&gt(this,bn,Gr(()=>{n(j(this,dn),()=>t,()=>()=>{})}))},Jc=function(){const t=j(this,zn).pending;t&&(this.is_pending=!0,gt(this,nn,Gr(()=>t(j(this,dn)))),On(()=>{var n=gt(this,Un,document.createDocumentFragment()),a=Rn();n.append(a),gt(this,En,mr(this,hr,Go).call(this,()=>(ua.ensure(),Gr(()=>j(this,Aa).call(this,a))))),j(this,ia)===0&&(j(this,dn).before(n),gt(this,Un,null),Na(j(this,nn),()=>{gt(this,nn,null)}),mr(this,hr,Uo).call(this))}))},zs=function(){try{if(this.is_pending=this.has_pending_snippet(),gt(this,ia,0),gt(this,Ia,0),gt(this,En,Gr(()=>{j(this,Aa).call(this,j(this,dn))})),j(this,ia)>0){var t=gt(this,Un,document.createDocumentFragment());ri(j(this,En),t);const n=j(this,zn).pending;gt(this,nn,Gr(()=>n(j(this,dn))))}else mr(this,hr,Uo).call(this)}catch(n){this.error(n)}},Uo=function(){this.is_pending=!1;for(const t of j(this,eo))cr(t,Er),Pn(t);for(const t of j(this,to))cr(t,kn),Pn(t);j(this,eo).clear(),j(this,to).clear()},Go=function(t){var n=kt,a=yt,o=_r;fn(j(this,qr)),vn(j(this,qr)),no(j(this,qr).ctx);try{return t()}catch(i){return ul(i),null}finally{fn(n),vn(a),no(o)}},Es=function(t){var n;if(!this.has_pending_snippet()){this.parent&&mr(n=this.parent,hr,Es).call(n,t);return}gt(this,ia,j(this,ia)+t),j(this,ia)===0&&(mr(this,hr,Uo).call(this),j(this,nn)&&Na(j(this,nn),()=>{gt(this,nn,null)}),j(this,Un)&&(j(this,dn).before(j(this,Un)),gt(this,Un,null)))};function gl(e,t,n,a){const o=Po()?No:Ws;var i=e.filter(g=>!g.settled);if(n.length===0&&i.length===0){a(t.map(o));return}var s=kt,d=Qc(),u=i.length===1?i[0].promise:i.length>1?Promise.all(i.map(g=>g.promise)):null;function p(g){d();try{a(g)}catch(w){(s.f&Nn)===0&&la(w,s)}As()}if(n.length===0){u.then(()=>p(t.map(o)));return}function x(){d(),Promise.all(n.map(g=>eu(g))).then(g=>p([...t.map(o),...g])).catch(g=>la(g,s))}u?u.then(x):x()}function Qc(){var e=kt,t=yt,n=_r,a=bt;return function(i=!0){fn(e),vn(t),no(n),i&&(a==null||a.activate())}}function As(e=!0){fn(null),vn(null),no(null),e&&(bt==null||bt.deactivate())}function Zc(){var e=kt.b,t=bt,n=e.is_rendered();return e.update_pending_count(1),t.increment(n),()=>{e.update_pending_count(-1),t.decrement(n)}}function No(e){var t=Ir|Er,n=yt!==null&&(yt.f&Ir)!==0?yt:null;return kt!==null&&(kt.f|=uo),{ctx:_r,deps:null,effects:null,equals:ll,f:t,fn:e,reactions:null,rv:0,v:br,wv:0,parent:n??kt,ac:null}}function eu(e,t,n){kt===null&&vc();var o=void 0,i=ma(br),s=!yt,d=new Map;return mu(()=>{var w;var u=Zi();o=u.promise;try{Promise.resolve(e()).then(u.resolve,u.reject).finally(As)}catch(P){u.reject(P),As()}var p=bt;if(s){var x=Zc();(w=d.get(p))==null||w.reject(Sa),d.delete(p),d.set(p,u)}const g=(P,C=void 0)=>{if(p.activate(),C)C!==Sa&&(i.f|=ca,oo(i,C));else{(i.f&ca)!==0&&(i.f^=ca),oo(i,P);for(const[R,b]of d){if(d.delete(R),R===p)break;b.reject(Sa)}}x&&x()};u.promise.then(g,P=>g(null,P||"unknown"))}),as(()=>{for(const u of d.values())u.reject(Sa)}),new Promise(u=>{function p(x){function g(){x===o?u(i):p(o)}x.then(g,g)}p(o)})}function q(e){const t=No(e);return Ol(t),t}function Ws(e){const t=No(e);return t.equals=dl,t}function tu(e){var t=e.effects;if(t!==null){e.effects=null;for(var n=0;n<t.length;n+=1)Ar(t[n])}}function ru(e){for(var t=e.parent;t!==null;){if((t.f&Ir)===0)return(t.f&Nn)===0?t:null;t=t.parent}return null}function Ys(e){var t,n=kt;fn(ru(e));try{e.f&=~Da,tu(e),t=Vl(e)}finally{fn(n)}return t}function bl(e){var t=Ys(e);if(!e.equals(t)&&(e.wv=Dl(),(!(bt!=null&&bt.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){cr(e,zr);return}xa||(Tr!==null?(Js()||bt!=null&&bt.is_fork)&&Tr.set(e,t):Ks(e))}function nu(e){var t,n;if(e.effects!==null)for(const a of e.effects)(a.teardown||a.ac)&&((t=a.teardown)==null||t.call(a),(n=a.ac)==null||n.abort(Sa),a.teardown=lc,a.ac=null,zo(a,0),ei(a))}function _l(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&so(t)}let Is=new Set;const va=new Map;let wl=!1;function ma(e,t){var n={f:0,v:e,reactions:null,equals:ll,rv:0,wv:0};return n}function G(e,t){const n=ma(e);return Ol(n),n}function au(e,t=!1,n=!0){var o;const a=ma(e);return t||(a.equals=dl),Io&&n&&_r!==null&&_r.l!==null&&((o=_r.l).s??(o.s=[])).push(a),a}function v(e,t,n=!1){yt!==null&&(!wn||(yt.f&bi)!==0)&&Po()&&(yt.f&(Ir|ga|Hs|bi))!==0&&(un===null||!ro.call(un,e))&&wc();let a=n?Gt(t):t;return oo(e,a)}function oo(e,t){if(!e.equals(t)){var n=e.v;xa?va.set(e,t):va.set(e,n),e.v=t;var a=ua.ensure();if(a.capture(e,n),(e.f&Ir)!==0){const o=e;(e.f&Er)!==0&&Ys(o),Ks(o)}e.wv=Dl(),yl(e,Er),Po()&&kt!==null&&(kt.f&zr)!==0&&(kt.f&(Cn|Fa))===0&&(ln===null?hu([e]):ln.push(e)),!a.is_fork&&Is.size>0&&!wl&&ou()}return t}function ou(){wl=!1;for(const e of Is)(e.f&zr)!==0&&cr(e,kn),Oo(e)&&so(e);Is.clear()}function So(e,t=1){var n=r(e),a=t===1?n++:n--;return v(e,n),a}function $o(e){v(e,e.v+1)}function yl(e,t){var n=e.reactions;if(n!==null)for(var a=Po(),o=n.length,i=0;i<o;i++){var s=n[i],d=s.f;if(!(!a&&s===kt)){var u=(d&Er)===0;if(u&&cr(s,t),(d&Ir)!==0){var p=s;Tr==null||Tr.delete(p),(d&Da)===0&&(d&cn&&(s.f|=Da),yl(p,kn))}else u&&((d&ga)!==0&&gn!==null&&gn.add(s),Pn(s))}}}function Gt(e){if(typeof e!="object"||e===null||Ln in e)return e;const t=Gs(e);if(t!==sc&&t!==ic)return e;var n=new Map,a=Us(e),o=G(0),i=La,s=d=>{if(La===i)return d();var u=yt,p=La;vn(null),Ci(i);var x=d();return vn(u),Ci(p),x};return a&&n.set("length",G(e.length)),new Proxy(e,{defineProperty(d,u,p){(!("value"in p)||p.configurable===!1||p.enumerable===!1||p.writable===!1)&&bc();var x=n.get(u);return x===void 0?s(()=>{var g=G(p.value);return n.set(u,g),g}):v(x,p.value,!0),!0},deleteProperty(d,u){var p=n.get(u);if(p===void 0){if(u in d){const x=s(()=>G(br));n.set(u,x),$o(o)}}else v(p,br),$o(o);return!0},get(d,u,p){var P;if(u===Ln)return e;var x=n.get(u),g=u in d;if(x===void 0&&(!g||(P=da(d,u))!=null&&P.writable)&&(x=s(()=>{var C=Gt(g?d[u]:br),R=G(C);return R}),n.set(u,x)),x!==void 0){var w=r(x);return w===br?void 0:w}return Reflect.get(d,u,p)},getOwnPropertyDescriptor(d,u){var p=Reflect.getOwnPropertyDescriptor(d,u);if(p&&"value"in p){var x=n.get(u);x&&(p.value=r(x))}else if(p===void 0){var g=n.get(u),w=g==null?void 0:g.v;if(g!==void 0&&w!==br)return{enumerable:!0,configurable:!0,value:w,writable:!0}}return p},has(d,u){var w;if(u===Ln)return!0;var p=n.get(u),x=p!==void 0&&p.v!==br||Reflect.has(d,u);if(p!==void 0||kt!==null&&(!x||(w=da(d,u))!=null&&w.writable)){p===void 0&&(p=s(()=>{var P=x?Gt(d[u]):br,C=G(P);return C}),n.set(u,p));var g=r(p);if(g===br)return!1}return x},set(d,u,p,x){var V;var g=n.get(u),w=u in d;if(a&&u==="length")for(var P=p;P<g.v;P+=1){var C=n.get(P+"");C!==void 0?v(C,br):P in d&&(C=s(()=>G(br)),n.set(P+"",C))}if(g===void 0)(!w||(V=da(d,u))!=null&&V.writable)&&(g=s(()=>G(void 0)),v(g,Gt(p)),n.set(u,g));else{w=g.v!==br;var R=s(()=>Gt(p));v(g,R)}var b=Reflect.getOwnPropertyDescriptor(d,u);if(b!=null&&b.set&&b.set.call(x,p),!w){if(a&&typeof u=="string"){var S=n.get("length"),M=Number(u);Number.isInteger(M)&&M>=S.v&&v(S,M+1)}$o(o)}return!0},ownKeys(d){r(o);var u=Reflect.ownKeys(d).filter(g=>{var w=n.get(g);return w===void 0||w.v!==br});for(var[p,x]of n)x.v!==br&&!(p in d)&&u.push(p);return u},setPrototypeOf(){_c()}})}function wi(e){try{if(e!==null&&typeof e=="object"&&Ln in e)return e[Ln]}catch{}return e}function su(e,t){return Object.is(wi(e),wi(t))}var Ko,kl,Cl,Sl,$l;function iu(){if(Ko===void 0){Ko=window,kl=document,Cl=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,n=Text.prototype;Sl=da(t,"firstChild").get,$l=da(t,"nextSibling").get,gi(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),gi(n)&&(n.__t=void 0)}}function Rn(e=""){return document.createTextNode(e)}function Hn(e){return Sl.call(e)}function Lo(e){return $l.call(e)}function l(e,t){return Hn(e)}function Q(e,t=!1){{var n=Hn(e);return n instanceof Comment&&n.data===""?Lo(n):n}}function h(e,t=1,n=!1){let a=e;for(;t--;)a=Lo(a);return a}function lu(e){e.textContent=""}function Ml(){return!1}function Xs(e,t,n){return document.createElementNS(t??sl,e,void 0)}function du(e,t){if(t){const n=document.body;e.autofocus=!0,On(()=>{document.activeElement===n&&e.focus()})}}let yi=!1;function cu(){yi||(yi=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const n of e.target.elements)(t=n.__on_r)==null||t.call(n)})},{capture:!0}))}function ns(e){var t=yt,n=kt;vn(null),fn(null);try{return e()}finally{vn(t),fn(n)}}function uu(e,t,n,a=n){e.addEventListener(t,()=>ns(n));const o=e.__on_r;o?e.__on_r=()=>{o(),a(!0)}:e.__on_r=()=>a(!0),cu()}function Tl(e){kt===null&&(yt===null&&xc(),mc()),xa&&pc()}function vu(e,t){var n=t.last;n===null?t.last=t.first=e:(n.next=e,e.prev=n,t.last=e)}function Sn(e,t){var n=kt;n!==null&&(n.f&Vr)!==0&&(e|=Vr);var a={ctx:_r,deps:null,nodes:null,f:e|Er|cn,first:null,fn:t,last:null,next:null,parent:n,b:n&&n.b,prev:null,teardown:null,wv:0,ac:null},o=a;if((e&lo)!==0)ao!==null?ao.push(a):Pn(a);else if(t!==null){try{so(a)}catch(s){throw Ar(a),s}o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&uo)===0&&(o=o.first,(e&ga)!==0&&(e&Kn)!==0&&o!==null&&(o.f|=Kn))}if(o!==null&&(o.parent=n,n!==null&&vu(o,n),yt!==null&&(yt.f&Ir)!==0&&(e&Fa)===0)){var i=yt;(i.effects??(i.effects=[])).push(o)}return a}function Js(){return yt!==null&&!wn}function as(e){const t=Sn(Ra,null);return cr(t,zr),t.teardown=e,t}function Kr(e){Tl();var t=kt.f,n=!yt&&(t&Cn)!==0&&(t&co)===0;if(n){var a=_r;(a.e??(a.e=[])).push(e)}else return zl(e)}function zl(e){return Sn(lo|tl,e)}function fu(e){return Tl(),Sn(Ra|tl,e)}function pu(e){ua.ensure();const t=Sn(Fa|uo,e);return(n={})=>new Promise(a=>{n.outro?Na(t,()=>{Ar(t),a(void 0)}):(Ar(t),a(void 0))})}function Qs(e){return Sn(lo,e)}function mu(e){return Sn(Hs|uo,e)}function Zs(e,t=0){return Sn(Ra|t,e)}function I(e,t=[],n=[],a=[]){gl(a,t,n,o=>{Sn(Ra,()=>e(...o.map(r)))})}function vo(e,t=0){var n=Sn(ga|t,e);return n}function El(e,t=0){var n=Sn(ts|t,e);return n}function Gr(e){return Sn(Cn|uo,e)}function Al(e){var t=e.teardown;if(t!==null){const n=xa,a=yt;ki(!0),vn(null);try{t.call(null)}finally{ki(n),vn(a)}}}function ei(e,t=!1){var n=e.first;for(e.first=e.last=null;n!==null;){const o=n.ac;o!==null&&ns(()=>{o.abort(Sa)});var a=n.next;(n.f&Fa)!==0?n.parent=null:Ar(n,t),n=a}}function xu(e){for(var t=e.first;t!==null;){var n=t.next;(t.f&Cn)===0&&Ar(t),t=n}}function Ar(e,t=!0){var n=!1;(t||(e.f&cc)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(Il(e.nodes.start,e.nodes.end),n=!0),ei(e,t&&!n),zo(e,0),cr(e,Nn);var a=e.nodes&&e.nodes.t;if(a!==null)for(const i of a)i.stop();Al(e);var o=e.parent;o!==null&&o.first!==null&&Pl(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function Il(e,t){for(;e!==null;){var n=e===t?null:Lo(e);e.remove(),e=n}}function Pl(e){var t=e.parent,n=e.prev,a=e.next;n!==null&&(n.next=a),a!==null&&(a.prev=n),t!==null&&(t.first===e&&(t.first=a),t.last===e&&(t.last=n))}function Na(e,t,n=!0){var a=[];Nl(e,a,!0);var o=()=>{n&&Ar(e),t&&t()},i=a.length;if(i>0){var s=()=>--i||o();for(var d of a)d.out(s)}else o()}function Nl(e,t,n){if((e.f&Vr)===0){e.f^=Vr;var a=e.nodes&&e.nodes.t;if(a!==null)for(const d of a)(d.is_global||n)&&t.push(d);for(var o=e.first;o!==null;){var i=o.next,s=(o.f&Kn)!==0||(o.f&Cn)!==0&&(e.f&ga)!==0;Nl(o,t,s?n:!1),o=i}}}function ti(e){Ll(e,!0)}function Ll(e,t){if((e.f&Vr)!==0){e.f^=Vr;for(var n=e.first;n!==null;){var a=n.next,o=(n.f&Kn)!==0||(n.f&Cn)!==0;Ll(n,o?t:!1),n=a}var i=e.nodes&&e.nodes.t;if(i!==null)for(const s of i)(s.is_global||t)&&s.in()}}function ri(e,t){if(e.nodes)for(var n=e.nodes.start,a=e.nodes.end;n!==null;){var o=n===a?null:Lo(n);t.append(n),n=o}}let Ho=!1,xa=!1;function ki(e){xa=e}let yt=null,wn=!1;function vn(e){yt=e}let kt=null;function fn(e){kt=e}let un=null;function Ol(e){yt!==null&&(un===null?un=[e]:un.push(e))}let Ur=null,rn=0,ln=null;function hu(e){ln=e}let Rl=1,Ma=0,La=Ma;function Ci(e){La=e}function Dl(){return++Rl}function Oo(e){var t=e.f;if((t&Er)!==0)return!0;if(t&Ir&&(e.f&=~Da),(t&kn)!==0){for(var n=e.deps,a=n.length,o=0;o<a;o++){var i=n[o];if(Oo(i)&&bl(i),i.wv>e.wv)return!0}(t&cn)!==0&&Tr===null&&cr(e,zr)}return!1}function jl(e,t,n=!0){var a=e.reactions;if(a!==null&&!(un!==null&&ro.call(un,e)))for(var o=0;o<a.length;o++){var i=a[o];(i.f&Ir)!==0?jl(i,t,!1):t===i&&(n?cr(i,Er):(i.f&zr)!==0&&cr(i,kn),Pn(i))}}function Vl(e){var R;var t=Ur,n=rn,a=ln,o=yt,i=un,s=_r,d=wn,u=La,p=e.f;Ur=null,rn=0,ln=null,yt=(p&(Cn|Fa))===0?e:null,un=null,no(e.ctx),wn=!1,La=++Ma,e.ac!==null&&(ns(()=>{e.ac.abort(Sa)}),e.ac=null);try{e.f|=ks;var x=e.fn,g=x();e.f|=co;var w=e.deps,P=bt==null?void 0:bt.is_fork;if(Ur!==null){var C;if(P||zo(e,rn),w!==null&&rn>0)for(w.length=rn+Ur.length,C=0;C<Ur.length;C++)w[rn+C]=Ur[C];else e.deps=w=Ur;if(Js()&&(e.f&cn)!==0)for(C=rn;C<w.length;C++)((R=w[C]).reactions??(R.reactions=[])).push(e)}else!P&&w!==null&&rn<w.length&&(zo(e,rn),w.length=rn);if(Po()&&ln!==null&&!wn&&w!==null&&(e.f&(Ir|kn|Er))===0)for(C=0;C<ln.length;C++)jl(ln[C],e);if(o!==null&&o!==e){if(Ma++,o.deps!==null)for(let b=0;b<n;b+=1)o.deps[b].rv=Ma;if(t!==null)for(const b of t)b.rv=Ma;ln!==null&&(a===null?a=ln:a.push(...ln))}return(e.f&ca)!==0&&(e.f^=ca),g}catch(b){return ul(b)}finally{e.f^=ks,Ur=t,rn=n,ln=a,yt=o,un=i,no(s),wn=d,La=u}}function gu(e,t){let n=t.reactions;if(n!==null){var a=ac.call(n,e);if(a!==-1){var o=n.length-1;o===0?n=t.reactions=null:(n[a]=n[o],n.pop())}}if(n===null&&(t.f&Ir)!==0&&(Ur===null||!ro.call(Ur,t))){var i=t;(i.f&cn)!==0&&(i.f^=cn,i.f&=~Da),Ks(i),nu(i),zo(i,0)}}function zo(e,t){var n=e.deps;if(n!==null)for(var a=t;a<n.length;a++)gu(e,n[a])}function so(e){var t=e.f;if((t&Nn)===0){cr(e,zr);var n=kt,a=Ho;kt=e,Ho=!0;try{(t&(ga|ts))!==0?xu(e):ei(e),Al(e);var o=Vl(e);e.teardown=typeof o=="function"?o:null,e.wv=Rl;var i;_s&&Dc&&(e.f&Er)!==0&&e.deps}finally{Ho=a,kt=n}}}async function Fl(){await Promise.resolve(),Bc()}function r(e){var t=e.f,n=(t&Ir)!==0;if(yt!==null&&!wn){var a=kt!==null&&(kt.f&Nn)!==0;if(!a&&(un===null||!ro.call(un,e))){var o=yt.deps;if((yt.f&ks)!==0)e.rv<Ma&&(e.rv=Ma,Ur===null&&o!==null&&o[rn]===e?rn++:Ur===null?Ur=[e]:Ur.push(e));else{(yt.deps??(yt.deps=[])).push(e);var i=e.reactions;i===null?e.reactions=[yt]:ro.call(i,yt)||i.push(yt)}}}if(xa&&va.has(e))return va.get(e);if(n){var s=e;if(xa){var d=s.v;return((s.f&zr)===0&&s.reactions!==null||Bl(s))&&(d=Ys(s)),va.set(s,d),d}var u=(s.f&cn)===0&&!wn&&yt!==null&&(Ho||(yt.f&cn)!==0),p=(s.f&co)===0;Oo(s)&&(u&&(s.f|=cn),bl(s)),u&&!p&&(_l(s),ql(s))}if(Tr!=null&&Tr.has(e))return Tr.get(e);if((e.f&ca)!==0)throw e.v;return e.v}function ql(e){if(e.f|=cn,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&Ir)!==0&&(t.f&cn)===0&&(_l(t),ql(t))}function Bl(e){if(e.v===br)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(va.has(t)||(t.f&Ir)!==0&&Bl(t))return!0;return!1}function ja(e){var t=wn;try{return wn=!0,e()}finally{wn=t}}function Ca(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(Ln in e)Ps(e);else if(!Array.isArray(e))for(let t in e){const n=e[t];typeof n=="object"&&n&&Ln in n&&Ps(n)}}}function Ps(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let a in e)try{Ps(e[a],t)}catch{}const n=Gs(e);if(n!==Object.prototype&&n!==Array.prototype&&n!==Map.prototype&&n!==Set.prototype&&n!==Date.prototype){const a=Qi(n);for(let o in a){const i=a[o].get;if(i)try{i.call(e)}catch{}}}}}function bu(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const _u=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function wu(e){return _u.includes(e)}const yu={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function ku(e){return e=e.toLowerCase(),yu[e]??e}const Cu=["touchstart","touchmove"];function Su(e){return Cu.includes(e)}const Ta=Symbol("events"),Ul=new Set,Ns=new Set;function Gl(e,t,n,a={}){function o(i){if(a.capture||Ls.call(t,i),!i.cancelBubble)return ns(()=>n==null?void 0:n.call(this,i))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?On(()=>{t.addEventListener(e,o,a)}):t.addEventListener(e,o,a),o}function fa(e,t,n,a,o){var i={capture:a,passive:o},s=Gl(e,t,n,i);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&as(()=>{t.removeEventListener(e,s,i)})}function oe(e,t,n){(t[Ta]??(t[Ta]={}))[e]=n}function Yr(e){for(var t=0;t<e.length;t++)Ul.add(e[t]);for(var n of Ns)n(e)}let Si=null;function Ls(e){var b,S;var t=this,n=t.ownerDocument,a=e.type,o=((b=e.composedPath)==null?void 0:b.call(e))||[],i=o[0]||e.target;Si=e;var s=0,d=Si===e&&e[Ta];if(d){var u=o.indexOf(d);if(u!==-1&&(t===document||t===window)){e[Ta]=t;return}var p=o.indexOf(t);if(p===-1)return;u<=p&&(s=u)}if(i=o[s]||e.target,i!==t){oc(e,"currentTarget",{configurable:!0,get(){return i||n}});var x=yt,g=kt;vn(null),fn(null);try{for(var w,P=[];i!==null;){var C=i.assignedSlot||i.parentNode||i.host||null;try{var R=(S=i[Ta])==null?void 0:S[a];R!=null&&(!i.disabled||e.target===i)&&R.call(i,e)}catch(M){w?P.push(M):w=M}if(e.cancelBubble||C===t||C===null)break;i=C}if(w){for(let M of P)queueMicrotask(()=>{throw M});throw w}}finally{e[Ta]=t,delete e.currentTarget,vn(x),fn(g)}}}var Xi;const fs=((Xi=globalThis==null?void 0:globalThis.window)==null?void 0:Xi.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function $u(e){return(fs==null?void 0:fs.createHTML(e))??e}function Hl(e){var t=Xs("template");return t.innerHTML=$u(e.replaceAll("<!>","<!---->")),t.content}function Va(e,t){var n=kt;n.nodes===null&&(n.nodes={start:e,end:t,a:null,t:null})}function f(e,t){var n=(t&Ac)!==0,a=(t&Ic)!==0,o,i=!e.startsWith("<!>");return()=>{o===void 0&&(o=Hl(i?e:"<!>"+e),n||(o=Hn(o)));var s=a||Cl?document.importNode(o,!0):o.cloneNode(!0);if(n){var d=Hn(s),u=s.lastChild;Va(d,u)}else Va(s,s);return s}}function Mu(e,t,n="svg"){var a=!e.startsWith("<!>"),o=`<${n}>${a?e:"<!>"+e}</${n}>`,i;return()=>{if(!i){var s=Hl(o),d=Hn(s);i=Hn(d)}var u=i.cloneNode(!0);return Va(u,u),u}}function Tu(e,t){return Mu(e,t,"svg")}function aa(e=""){{var t=Rn(e+"");return Va(t,t),t}}function be(){var e=document.createDocumentFragment(),t=document.createComment(""),n=Rn();return e.append(t,n),Va(t,n),e}function c(e,t){e!==null&&e.before(t)}function A(e,t){var n=t==null?"":typeof t=="object"?`${t}`:t;n!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=n,e.nodeValue=`${n}`)}function zu(e,t){return Eu(e,t)}const Vo=new Map;function Eu(e,{target:t,anchor:n,props:a={},events:o,context:i,intro:s=!0,transformError:d}){iu();var u=void 0,p=pu(()=>{var x=n??t.appendChild(Rn());Kc(x,{pending:()=>{}},P=>{wr({});var C=_r;i&&(C.c=i),o&&(a.$$events=o),u=e(P,a)||{},yr()},d);var g=new Set,w=P=>{for(var C=0;C<P.length;C++){var R=P[C];if(!g.has(R)){g.add(R);var b=Su(R);for(const V of[t,document]){var S=Vo.get(V);S===void 0&&(S=new Map,Vo.set(V,S));var M=S.get(R);M===void 0?(V.addEventListener(R,Ls,{passive:b}),S.set(R,1)):S.set(R,M+1)}}}};return w(es(Ul)),Ns.add(w),()=>{var b;for(var P of g)for(const S of[t,document]){var C=Vo.get(S),R=C.get(P);--R==0?(S.removeEventListener(P,Ls),C.delete(P),C.size===0&&Vo.delete(S)):C.set(P,R)}Ns.delete(w),x!==n&&((b=x.parentNode)==null||b.removeChild(x))}});return Au.set(u,p),u}let Au=new WeakMap;var _n,An,an,Pa,Eo,Ao,Zo;class os{constructor(t,n=!0){hn(this,"anchor");Mt(this,_n,new Map);Mt(this,An,new Map);Mt(this,an,new Map);Mt(this,Pa,new Set);Mt(this,Eo,!0);Mt(this,Ao,t=>{if(j(this,_n).has(t)){var n=j(this,_n).get(t),a=j(this,An).get(n);if(a)ti(a),j(this,Pa).delete(n);else{var o=j(this,an).get(n);o&&(o.effect.f&Vr)===0&&(j(this,An).set(n,o.effect),j(this,an).delete(n),o.fragment.lastChild.remove(),this.anchor.before(o.fragment),a=o.effect)}for(const[i,s]of j(this,_n)){if(j(this,_n).delete(i),i===t)break;const d=j(this,an).get(s);d&&(Ar(d.effect),j(this,an).delete(s))}for(const[i,s]of j(this,An)){if(i===n||j(this,Pa).has(i)||(s.f&Vr)!==0)continue;const d=()=>{if(Array.from(j(this,_n).values()).includes(i)){var p=document.createDocumentFragment();ri(s,p),p.append(Rn()),j(this,an).set(i,{effect:s,fragment:p})}else Ar(s);j(this,Pa).delete(i),j(this,An).delete(i)};j(this,Eo)||!a?(j(this,Pa).add(i),Na(s,d,!1)):d()}}});Mt(this,Zo,t=>{j(this,_n).delete(t);const n=Array.from(j(this,_n).values());for(const[a,o]of j(this,an))n.includes(a)||(Ar(o.effect),j(this,an).delete(a))});this.anchor=t,gt(this,Eo,n)}ensure(t,n){var a=bt,o=Ml();if(n&&!j(this,An).has(t)&&!j(this,an).has(t))if(o){var i=document.createDocumentFragment(),s=Rn();i.append(s),j(this,an).set(t,{effect:Gr(()=>n(s)),fragment:i})}else j(this,An).set(t,Gr(()=>n(this.anchor)));if(j(this,_n).set(a,t),o){for(const[d,u]of j(this,An))d===t?a.unskip_effect(u):a.skip_effect(u);for(const[d,u]of j(this,an))d===t?a.unskip_effect(u.effect):a.skip_effect(u.effect);a.oncommit(j(this,Ao)),a.ondiscard(j(this,Zo))}else j(this,Ao).call(this,a)}}_n=new WeakMap,An=new WeakMap,an=new WeakMap,Pa=new WeakMap,Eo=new WeakMap,Ao=new WeakMap,Zo=new WeakMap;function k(e,t,n=!1){var a=new os(e),o=n?Kn:0;function i(s,d){a.ensure(s,d)}vo(()=>{var s=!1;t((d,u=0)=>{s=!0,i(u,d)}),s||i(-1,null)},o)}function Se(e,t){return t}function Iu(e,t,n){for(var a=[],o=t.length,i,s=t.length,d=0;d<o;d++){let g=t[d];Na(g,()=>{if(i){if(i.pending.delete(g),i.done.add(g),i.pending.size===0){var w=e.outrogroups;Os(e,es(i.done)),w.delete(i),w.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var u=a.length===0&&n!==null;if(u){var p=n,x=p.parentNode;lu(x),x.append(p),e.items.clear()}Os(e,t,!u)}else i={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(i)}function Os(e,t,n=!0){var a;if(e.pending.size>0){a=new Set;for(const s of e.pending.values())for(const d of s)a.add(e.items.get(d).e)}for(var o=0;o<t.length;o++){var i=t[o];if(a!=null&&a.has(i)){i.f|=In;const s=document.createDocumentFragment();ri(i,s)}else Ar(t[o],n)}}var $i;function ke(e,t,n,a,o,i=null){var s=e,d=new Map,u=(t&al)!==0;if(u){var p=e;s=p.appendChild(Rn())}var x=null,g=Ws(()=>{var V=n();return Us(V)?V:V==null?[]:es(V)}),w,P=new Map,C=!0;function R(V){(M.effect.f&Nn)===0&&(M.pending.delete(V),M.fallback=x,Pu(M,w,s,t,a),x!==null&&(w.length===0?(x.f&In)===0?ti(x):(x.f^=In,ko(x,null,s)):Na(x,()=>{x=null})))}function b(V){M.pending.delete(V)}var S=vo(()=>{w=r(g);for(var V=w.length,E=new Set,F=bt,se=Ml(),ne=0;ne<V;ne+=1){var z=w[ne],N=a(z,ne),X=C?null:d.get(N);X?(X.v&&oo(X.v,z),X.i&&oo(X.i,ne),se&&F.unskip_effect(X.e)):(X=Nu(d,C?s:$i??($i=Rn()),z,N,ne,o,t,n),C||(X.e.f|=In),d.set(N,X)),E.add(N)}if(V===0&&i&&!x&&(C?x=Gr(()=>i(s)):(x=Gr(()=>i($i??($i=Rn()))),x.f|=In)),V>E.size&&fc(),!C)if(P.set(F,E),se){for(const[H,O]of d)E.has(H)||F.skip_effect(O.e);F.oncommit(R),F.ondiscard(b)}else R(F);r(g)}),M={effect:S,items:d,pending:P,outrogroups:null,fallback:x};C=!1}function ho(e){for(;e!==null&&(e.f&Cn)===0;)e=e.next;return e}function Pu(e,t,n,a,o){var X,H,O,ce,ve,Pe,he,Ne,me;var i=(a&Sc)!==0,s=t.length,d=e.items,u=ho(e.effect.first),p,x=null,g,w=[],P=[],C,R,b,S;if(i)for(S=0;S<s;S+=1)C=t[S],R=o(C,S),b=d.get(R).e,(b.f&In)===0&&((H=(X=b.nodes)==null?void 0:X.a)==null||H.measure(),(g??(g=new Set)).add(b));for(S=0;S<s;S+=1){if(C=t[S],R=o(C,S),b=d.get(R).e,e.outrogroups!==null)for(const de of e.outrogroups)de.pending.delete(b),de.done.delete(b);if((b.f&In)!==0)if(b.f^=In,b===u)ko(b,null,n);else{var M=x?x.next:u;b===e.effect.last&&(e.effect.last=b.prev),b.prev&&(b.prev.next=b.next),b.next&&(b.next.prev=b.prev),ta(e,x,b),ta(e,b,M),ko(b,M,n),x=b,w=[],P=[],u=ho(x.next);continue}if((b.f&Vr)!==0&&(ti(b),i&&((ce=(O=b.nodes)==null?void 0:O.a)==null||ce.unfix(),(g??(g=new Set)).delete(b))),b!==u){if(p!==void 0&&p.has(b)){if(w.length<P.length){var V=P[0],E;x=V.prev;var F=w[0],se=w[w.length-1];for(E=0;E<w.length;E+=1)ko(w[E],V,n);for(E=0;E<P.length;E+=1)p.delete(P[E]);ta(e,F.prev,se.next),ta(e,x,F),ta(e,se,V),u=V,x=se,S-=1,w=[],P=[]}else p.delete(b),ko(b,u,n),ta(e,b.prev,b.next),ta(e,b,x===null?e.effect.first:x.next),ta(e,x,b),x=b;continue}for(w=[],P=[];u!==null&&u!==b;)(p??(p=new Set)).add(u),P.push(u),u=ho(u.next);if(u===null)continue}(b.f&In)===0&&w.push(b),x=b,u=ho(b.next)}if(e.outrogroups!==null){for(const de of e.outrogroups)de.pending.size===0&&(Os(e,es(de.done)),(ve=e.outrogroups)==null||ve.delete(de));e.outrogroups.size===0&&(e.outrogroups=null)}if(u!==null||p!==void 0){var ne=[];if(p!==void 0)for(b of p)(b.f&Vr)===0&&ne.push(b);for(;u!==null;)(u.f&Vr)===0&&u!==e.fallback&&ne.push(u),u=ho(u.next);var z=ne.length;if(z>0){var N=(a&al)!==0&&s===0?n:null;if(i){for(S=0;S<z;S+=1)(he=(Pe=ne[S].nodes)==null?void 0:Pe.a)==null||he.measure();for(S=0;S<z;S+=1)(me=(Ne=ne[S].nodes)==null?void 0:Ne.a)==null||me.fix()}Iu(e,ne,N)}}i&&On(()=>{var de,B;if(g!==void 0)for(b of g)(B=(de=b.nodes)==null?void 0:de.a)==null||B.apply()})}function Nu(e,t,n,a,o,i,s,d){var u=(s&kc)!==0?(s&$c)===0?au(n,!1,!1):ma(n):null,p=(s&Cc)!==0?ma(o):null;return{v:u,i:p,e:Gr(()=>(i(t,u??n,p??o,d),()=>{e.delete(a)}))}}function ko(e,t,n){if(e.nodes)for(var a=e.nodes.start,o=e.nodes.end,i=t&&(t.f&In)===0?t.nodes.start:n;a!==null;){var s=Lo(a);if(i.before(a),a===o)return;a=s}}function ta(e,t,n){t===null?e.effect.first=n:t.next=n,n===null?e.effect.last=t:n.prev=t}function yn(e,t,n=!1,a=!1,o=!1){var i=e,s="";I(()=>{var d=kt;if(s!==(s=t()??"")&&(d.nodes!==null&&(Il(d.nodes.start,d.nodes.end),d.nodes=null),s!=="")){var u=n?il:a?Pc:void 0,p=Xs(n?"svg":a?"math":"template",u);p.innerHTML=s;var x=n||a?p:p.content;if(Va(Hn(x),x.lastChild),n||a)for(;Hn(x);)i.before(Hn(x));else i.before(x)}})}function nt(e,t,n,a,o){var d;var i=(d=t.$$slots)==null?void 0:d[n],s=!1;i===!0&&(i=t.children,s=!0),i===void 0||i(e,s?()=>a:a)}function Rs(e,t,...n){var a=new os(e);vo(()=>{const o=t()??null;a.ensure(o,o&&(i=>o(i,...n)))},Kn)}function Kl(e,t,n){var a=new os(e);vo(()=>{var o=t()??null;a.ensure(o,o&&(i=>n(i,o)))},Kn)}function Lu(e,t,n,a,o,i){var s=null,d=e,u=new os(d,!1);vo(()=>{const p=t()||null;var x=il;if(p===null){u.ensure(null,null);return}return u.ensure(p,g=>{if(p){if(s=Xs(p,x),Va(s,s),a){var w=s.appendChild(Rn());a(s,w)}kt.nodes.end=s,g.before(s)}}),()=>{}},Kn),as(()=>{})}function Ou(e,t){var n=void 0,a;El(()=>{n!==(n=t())&&(a&&(Ar(a),a=null),n&&(a=Gr(()=>{Qs(()=>n(e))})))})}function Wl(e){var t,n,a="";if(typeof e=="string"||typeof e=="number")a+=e;else if(typeof e=="object")if(Array.isArray(e)){var o=e.length;for(t=0;t<o;t++)e[t]&&(n=Wl(e[t]))&&(a&&(a+=" "),a+=n)}else for(n in e)e[n]&&(a&&(a+=" "),a+=n);return a}function Yl(){for(var e,t,n=0,a="",o=arguments.length;n<o;n++)(e=arguments[n])&&(t=Wl(e))&&(a&&(a+=" "),a+=t);return a}function Ut(e){return typeof e=="object"?Yl(e):e??""}const Mi=[...` 	
\r\f \v\uFEFF`];function Ru(e,t,n){var a=e==null?"":""+e;if(t&&(a=a?a+" "+t:t),n){for(var o of Object.keys(n))if(n[o])a=a?a+" "+o:o;else if(a.length)for(var i=o.length,s=0;(s=a.indexOf(o,s))>=0;){var d=s+i;(s===0||Mi.includes(a[s-1]))&&(d===a.length||Mi.includes(a[d]))?a=(s===0?"":a.substring(0,s))+a.substring(d+1):s=d}}return a===""?null:a}function Ti(e,t=!1){var n=t?" !important;":";",a="";for(var o of Object.keys(e)){var i=e[o];i!=null&&i!==""&&(a+=" "+o+": "+i+n)}return a}function ps(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Du(e,t){if(t){var n="",a,o;if(Array.isArray(t)?(a=t[0],o=t[1]):a=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var i=!1,s=0,d=!1,u=[];a&&u.push(...Object.keys(a).map(ps)),o&&u.push(...Object.keys(o).map(ps));var p=0,x=-1;const R=e.length;for(var g=0;g<R;g++){var w=e[g];if(d?w==="/"&&e[g-1]==="*"&&(d=!1):i?i===w&&(i=!1):w==="/"&&e[g+1]==="*"?d=!0:w==='"'||w==="'"?i=w:w==="("?s++:w===")"&&s--,!d&&i===!1&&s===0){if(w===":"&&x===-1)x=g;else if(w===";"||g===R-1){if(x!==-1){var P=ps(e.substring(p,x).trim());if(!u.includes(P)){w!==";"&&g++;var C=e.substring(p,g).trim();n+=" "+C+";"}}p=g+1,x=-1}}}}return a&&(n+=Ti(a)),o&&(n+=Ti(o,!0)),n=n.trim(),n===""?null:n}return e==null?null:String(e)}function je(e,t,n,a,o,i){var s=e.__className;if(s!==n||s===void 0){var d=Ru(n,a,i);d==null?e.removeAttribute("class"):t?e.className=d:e.setAttribute("class",d),e.__className=n}else if(i&&o!==i)for(var u in i){var p=!!i[u];(o==null||p!==!!o[u])&&e.classList.toggle(u,p)}return i}function ms(e,t={},n,a){for(var o in n){var i=n[o];t[o]!==i&&(n[o]==null?e.style.removeProperty(o):e.style.setProperty(o,i,a))}}function Wo(e,t,n,a){var o=e.__style;if(o!==t){var i=Du(t,a);i==null?e.removeAttribute("style"):e.style.cssText=i,e.__style=t}else a&&(Array.isArray(a)?(ms(e,n==null?void 0:n[0],a[0]),ms(e,n==null?void 0:n[1],a[1],"important")):ms(e,n,a));return a}function Ds(e,t,n=!1){if(e.multiple){if(t==null)return;if(!Us(t))return Lc();for(var a of e.options)a.selected=t.includes(zi(a));return}for(a of e.options){var o=zi(a);if(su(o,t)){a.selected=!0;return}}(!n||t!==void 0)&&(e.selectedIndex=-1)}function ju(e){var t=new MutationObserver(()=>{Ds(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),as(()=>{t.disconnect()})}function zi(e){return"__value"in e?e.__value:e.value}const go=Symbol("class"),bo=Symbol("style"),Xl=Symbol("is custom element"),Jl=Symbol("is html"),Vu=nl?"option":"OPTION",Fu=nl?"select":"SELECT";function qu(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function Dn(e,t,n,a){var o=Ql(e);o[t]!==(o[t]=n)&&(t==="loading"&&(e[uc]=n),n==null?e.removeAttribute(t):typeof n!="string"&&Zl(e).includes(t)?e[t]=n:e.setAttribute(t,n))}function Bu(e,t,n,a,o=!1,i=!1){var s=Ql(e),d=s[Xl],u=!s[Jl],p=t||{},x=e.nodeName===Vu;for(var g in t)g in n||(n[g]=null);n.class?n.class=Ut(n.class):n[go]&&(n.class=null),n[bo]&&(n.style??(n.style=null));var w=Zl(e);for(const E in n){let F=n[E];if(x&&E==="value"&&F==null){e.value=e.__value="",p[E]=F;continue}if(E==="class"){var P=e.namespaceURI==="http://www.w3.org/1999/xhtml";je(e,P,F,a,t==null?void 0:t[go],n[go]),p[E]=F,p[go]=n[go];continue}if(E==="style"){Wo(e,F,t==null?void 0:t[bo],n[bo]),p[E]=F,p[bo]=n[bo];continue}var C=p[E];if(!(F===C&&!(F===void 0&&e.hasAttribute(E)))){p[E]=F;var R=E[0]+E[1];if(R!=="$$")if(R==="on"){const se={},ne="$$"+E;let z=E.slice(2);var b=wu(z);if(bu(z)&&(z=z.slice(0,-7),se.capture=!0),!b&&C){if(F!=null)continue;e.removeEventListener(z,p[ne],se),p[ne]=null}if(b)oe(z,e,F),Yr([z]);else if(F!=null){let N=function(X){p[E].call(this,X)};var V=N;p[ne]=Gl(z,e,N,se)}}else if(E==="style")Dn(e,E,F);else if(E==="autofocus")du(e,!!F);else if(!d&&(E==="__value"||E==="value"&&F!=null))e.value=e.__value=F;else if(E==="selected"&&x)qu(e,F);else{var S=E;u||(S=ku(S));var M=S==="defaultValue"||S==="defaultChecked";if(F==null&&!d&&!M)if(s[E]=null,S==="value"||S==="checked"){let se=e;const ne=t===void 0;if(S==="value"){let z=se.defaultValue;se.removeAttribute(S),se.defaultValue=z,se.value=se.__value=ne?z:null}else{let z=se.defaultChecked;se.removeAttribute(S),se.defaultChecked=z,se.checked=ne?z:!1}}else e.removeAttribute(E);else M||w.includes(S)&&(d||typeof F!="string")?(e[S]=F,S in s&&(s[S]=br)):typeof F!="function"&&Dn(e,S,F)}}}return p}function Yo(e,t,n=[],a=[],o=[],i,s=!1,d=!1){gl(o,n,a,u=>{var p=void 0,x={},g=e.nodeName===Fu,w=!1;if(El(()=>{var C=t(...u.map(r)),R=Bu(e,p,C,i,s,d);w&&g&&"value"in C&&Ds(e,C.value);for(let S of Object.getOwnPropertySymbols(x))C[S]||Ar(x[S]);for(let S of Object.getOwnPropertySymbols(C)){var b=C[S];S.description===Nc&&(!p||b!==p[S])&&(x[S]&&Ar(x[S]),x[S]=Gr(()=>Ou(e,()=>b))),R[S]=b}p=R}),g){var P=e;Qs(()=>{Ds(P,p.value,!0),ju(P)})}w=!0})}function Ql(e){return e.__attributes??(e.__attributes={[Xl]:e.nodeName.includes("-"),[Jl]:e.namespaceURI===sl})}var Ei=new Map;function Zl(e){var t=e.getAttribute("is")||e.nodeName,n=Ei.get(t);if(n)return n;Ei.set(t,n=[]);for(var a,o=e,i=Element.prototype;i!==o;){a=Qi(o);for(var s in a)a[s].set&&n.push(s);o=Gs(o)}return n}function za(e,t,n=t){var a=new WeakSet;uu(e,"input",async o=>{var i=o?e.defaultValue:e.value;if(i=xs(e)?hs(i):i,n(i),bt!==null&&a.add(bt),await Fl(),i!==(i=t())){var s=e.selectionStart,d=e.selectionEnd,u=e.value.length;if(e.value=i??"",d!==null){var p=e.value.length;s===d&&d===u&&p>u?(e.selectionStart=p,e.selectionEnd=p):(e.selectionStart=s,e.selectionEnd=Math.min(d,p))}}}),ja(t)==null&&e.value&&(n(xs(e)?hs(e.value):e.value),bt!==null&&a.add(bt)),Zs(()=>{var o=t();if(e===document.activeElement){var i=Cs??bt;if(a.has(i))return}xs(e)&&o===hs(e.value)||e.type==="date"&&!o&&!e.value||o!==e.value&&(e.value=o??"")})}function xs(e){var t=e.type;return t==="number"||t==="range"}function hs(e){return e===""?null:+e}function Ai(e,t){return e===t||(e==null?void 0:e[Ln])===t}function pa(e={},t,n,a){return Qs(()=>{var o,i;return Zs(()=>{o=i,i=[],ja(()=>{e!==n(...i)&&(t(e,...i),o&&Ai(n(...o),e)&&t(null,...o))})}),()=>{On(()=>{i&&Ai(n(...i),e)&&t(null,...i)})}}),e}function Uu(e=!1){const t=_r,n=t.l.u;if(!n)return;let a=()=>Ca(t.s);if(e){let o=0,i={};const s=No(()=>{let d=!1;const u=t.s;for(const p in u)u[p]!==i[p]&&(i[p]=u[p],d=!0);return d&&o++,o});a=()=>r(s)}n.b.length&&fu(()=>{Ii(t,a),ws(n.b)}),Kr(()=>{const o=ja(()=>n.m.map(dc));return()=>{for(const i of o)typeof i=="function"&&i()}}),n.a.length&&Kr(()=>{Ii(t,a),ws(n.a)})}function Ii(e,t){if(e.l.s)for(const n of e.l.s)r(n);t()}let Fo=!1;function Gu(e){var t=Fo;try{return Fo=!1,[e(),Fo]}finally{Fo=t}}const Hu={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Ku(e,t,n){return new Proxy({props:e,exclude:t},Hu)}const Wu={get(e,t){if(!e.exclude.includes(t))return r(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,n){if(!(t in e.special)){var a=kt;try{fn(e.parent_effect),e.special[t]=Be({get[t](){return e.props[t]}},t,ol)}finally{fn(a)}}return e.special[t](n),So(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),So(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function rt(e,t){return new Proxy({props:e,exclude:t,special:{},version:ma(0),parent_effect:kt},Wu)}const Yu={get(e,t){let n=e.props.length;for(;n--;){let a=e.props[n];if(xo(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a)return a[t]}},set(e,t,n){let a=e.props.length;for(;a--;){let o=e.props[a];xo(o)&&(o=o());const i=da(o,t);if(i&&i.set)return i.set(n),!0}return!1},getOwnPropertyDescriptor(e,t){let n=e.props.length;for(;n--;){let a=e.props[n];if(xo(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a){const o=da(a,t);return o&&!o.configurable&&(o.configurable=!0),o}}},has(e,t){if(t===Ln||t===rl)return!1;for(let n of e.props)if(xo(n)&&(n=n()),n!=null&&t in n)return!0;return!1},ownKeys(e){const t=[];for(let n of e.props)if(xo(n)&&(n=n()),!!n){for(const a in n)t.includes(a)||t.push(a);for(const a of Object.getOwnPropertySymbols(n))t.includes(a)||t.push(a)}return t}};function it(...e){return new Proxy({props:e},Yu)}function Be(e,t,n,a){var V;var o=!Io||(n&Tc)!==0,i=(n&zc)!==0,s=(n&Ec)!==0,d=a,u=!0,p=()=>(u&&(u=!1,d=s?ja(a):a),d),x;if(i){var g=Ln in e||rl in e;x=((V=da(e,t))==null?void 0:V.set)??(g&&t in e?E=>e[t]=E:void 0)}var w,P=!1;i?[w,P]=Gu(()=>e[t]):w=e[t],w===void 0&&a!==void 0&&(w=p(),x&&(o&&gc(),x(w)));var C;if(o?C=()=>{var E=e[t];return E===void 0?p():(u=!0,E)}:C=()=>{var E=e[t];return E!==void 0&&(d=void 0),E===void 0?d:E},o&&(n&ol)===0)return C;if(x){var R=e.$$legacy;return(function(E,F){return arguments.length>0?((!o||!F||R||P)&&x(F?C():E),E):C()})}var b=!1,S=((n&Mc)!==0?No:Ws)(()=>(b=!1,C()));i&&r(S);var M=kt;return(function(E,F){if(arguments.length>0){const se=F?r(S):o&&i?Gt(E):E;return v(S,se),b=!0,d!==void 0&&(d=se),E}return xa&&b||(M.f&Nn)!==0?S.v:r(S)})}const Xu="5";var Ji;typeof window<"u"&&((Ji=window.__svelte??(window.__svelte={})).v??(Ji.v=new Set)).add(Xu);const Xr="";async function Ju(){const e=await fetch(`${Xr}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function Qu(e,t=null,n=null){const a={provider:e};t&&(a.model=t),n&&(a.api_key=n);const o=await fetch(`${Xr}/api/provider/validate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!o.ok)throw new Error("설정 실패");return o.json()}async function Zu(e){const t=await fetch(`${Xr}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function ev(e,{onProgress:t,onDone:n,onError:a}){const o=new AbortController;return fetch(`${Xr}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:o.signal}).then(async i=>{if(!i.ok){a==null||a("다운로드 실패");return}const s=i.body.getReader(),d=new TextDecoder;let u="";for(;;){const{done:p,value:x}=await s.read();if(p)break;u+=d.decode(x,{stream:!0});const g=u.split(`
`);u=g.pop()||"";for(const w of g)if(w.startsWith("data:"))try{const P=JSON.parse(w.slice(5).trim());P.total&&P.completed!==void 0?t==null||t({total:P.total,completed:P.completed,status:P.status}):P.status&&(t==null||t({status:P.status}))}catch{}}n==null||n()}).catch(i=>{i.name!=="AbortError"&&(a==null||a(i.message))}),{abort:()=>o.abort()}}async function tv(){const e=await fetch(`${Xr}/api/codex/logout`,{method:"POST"});if(!e.ok)throw new Error("Codex 로그아웃 실패");return e.json()}async function rv(e,t=null,n=null){let a=`${Xr}/api/export/excel/${encodeURIComponent(e)}`;const o=new URLSearchParams;n?o.set("template_id",n):t&&t.length>0&&o.set("modules",t.join(","));const i=o.toString();i&&(a+=`?${i}`);const s=await fetch(a);if(!s.ok){const w=await s.json().catch(()=>({}));throw new Error(w.detail||"Excel 다운로드 실패")}const d=await s.blob(),p=(s.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),x=p?decodeURIComponent(p[1]):`${e}.xlsx`,g=document.createElement("a");return g.href=URL.createObjectURL(d),g.download=x,g.click(),URL.revokeObjectURL(g.href),x}async function ed(e){const t=await fetch(`${Xr}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}async function nv(e,t){const n=await fetch(`${Xr}/api/company/${e}/show/${encodeURIComponent(t)}/all`);if(!n.ok)throw new Error("company topic 일괄 조회 실패");return n.json()}async function av(e){const t=await fetch(`${Xr}/api/company/${e}/sections`);if(!t.ok)throw new Error("sections 조회 실패");return t.json()}async function ov(e){const t=await fetch(`${Xr}/api/company/${e}/toc`);if(!t.ok)throw new Error("목차 조회 실패");return t.json()}async function sv(e,t,n=null){const a=n?`?period=${encodeURIComponent(n)}`:"",o=await fetch(`${Xr}/api/company/${e}/viewer/${encodeURIComponent(t)}${a}`);if(!o.ok)throw new Error("viewer 조회 실패");return o.json()}async function iv(e,t){const n=await fetch(`${Xr}/api/company/${e}/diff/${encodeURIComponent(t)}/summary`);if(!n.ok)throw new Error("diff summary 조회 실패");return n.json()}async function lv(e,t){const n=new URLSearchParams({q:t}),a=await fetch(`${Xr}/api/company/${encodeURIComponent(e)}/search?${n}`);if(!a.ok)throw new Error("검색 실패");return a.json()}function dv(e,t,n={},{onMeta:a,onSnapshot:o,onContext:i,onSystemPrompt:s,onToolCall:d,onToolResult:u,onChunk:p,onDone:x,onError:g,onViewerNavigate:w},P=null){const C={question:t,stream:!0,...n};e&&(C.company=e),P&&P.length>0&&(C.history=P);const R=new AbortController;return fetch(`${Xr}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(C),signal:R.signal}).then(async b=>{if(!b.ok){const se=await b.json().catch(()=>({}));g==null||g(se.detail||"스트리밍 실패");return}const S=b.body.getReader(),M=new TextDecoder;let V="",E=!1,F=null;for(;;){const{done:se,value:ne}=await S.read();if(se)break;V+=M.decode(ne,{stream:!0});const z=V.split(`
`);V=z.pop()||"";for(const N of z)if(N.startsWith("event:"))F=N.slice(6).trim();else if(N.startsWith("data:")&&F){const X=N.slice(5).trim();try{const H=JSON.parse(X);F==="meta"?a==null||a(H):F==="snapshot"?o==null||o(H):F==="context"?i==null||i(H):F==="system_prompt"?s==null||s(H):F==="tool_call"?d==null||d(H):F==="tool_result"?u==null||u(H):F==="chunk"?p==null||p(H.text):F==="viewer_navigate"?w==null||w(H):F==="error"?g==null||g(H.error,H.action,H.detail):F==="done"&&(E||(E=!0,x==null||x()))}catch{}F=null}}E||(E=!0,x==null||x())}).catch(b=>{b.name!=="AbortError"&&(g==null||g(b.message))}),{abort:()=>R.abort()}}const cv=(e,t)=>{const n=new Array(e.length+t.length);for(let a=0;a<e.length;a++)n[a]=e[a];for(let a=0;a<t.length;a++)n[e.length+a]=t[a];return n},uv=(e,t)=>({classGroupId:e,validator:t}),td=(e=new Map,t=null,n)=>({nextPart:e,validators:t,classGroupId:n}),Xo="-",Pi=[],vv="arbitrary..",fv=e=>{const t=mv(e),{conflictingClassGroups:n,conflictingClassGroupModifiers:a}=e;return{getClassGroupId:s=>{if(s.startsWith("[")&&s.endsWith("]"))return pv(s);const d=s.split(Xo),u=d[0]===""&&d.length>1?1:0;return rd(d,u,t)},getConflictingClassGroupIds:(s,d)=>{if(d){const u=a[s],p=n[s];return u?p?cv(p,u):u:p||Pi}return n[s]||Pi}}},rd=(e,t,n)=>{if(e.length-t===0)return n.classGroupId;const o=e[t],i=n.nextPart.get(o);if(i){const p=rd(e,t+1,i);if(p)return p}const s=n.validators;if(s===null)return;const d=t===0?e.join(Xo):e.slice(t).join(Xo),u=s.length;for(let p=0;p<u;p++){const x=s[p];if(x.validator(d))return x.classGroupId}},pv=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),n=t.indexOf(":"),a=t.slice(0,n);return a?vv+a:void 0})(),mv=e=>{const{theme:t,classGroups:n}=e;return xv(n,t)},xv=(e,t)=>{const n=td();for(const a in e){const o=e[a];ni(o,n,a,t)}return n},ni=(e,t,n,a)=>{const o=e.length;for(let i=0;i<o;i++){const s=e[i];hv(s,t,n,a)}},hv=(e,t,n,a)=>{if(typeof e=="string"){gv(e,t,n);return}if(typeof e=="function"){bv(e,t,n,a);return}_v(e,t,n,a)},gv=(e,t,n)=>{const a=e===""?t:nd(t,e);a.classGroupId=n},bv=(e,t,n,a)=>{if(wv(e)){ni(e(a),t,n,a);return}t.validators===null&&(t.validators=[]),t.validators.push(uv(n,e))},_v=(e,t,n,a)=>{const o=Object.entries(e),i=o.length;for(let s=0;s<i;s++){const[d,u]=o[s];ni(u,nd(t,d),n,a)}},nd=(e,t)=>{let n=e;const a=t.split(Xo),o=a.length;for(let i=0;i<o;i++){const s=a[i];let d=n.nextPart.get(s);d||(d=td(),n.nextPart.set(s,d)),n=d}return n},wv=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,yv=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,n=Object.create(null),a=Object.create(null);const o=(i,s)=>{n[i]=s,t++,t>e&&(t=0,a=n,n=Object.create(null))};return{get(i){let s=n[i];if(s!==void 0)return s;if((s=a[i])!==void 0)return o(i,s),s},set(i,s){i in n?n[i]=s:o(i,s)}}},js="!",Ni=":",kv=[],Li=(e,t,n,a,o)=>({modifiers:e,hasImportantModifier:t,baseClassName:n,maybePostfixModifierPosition:a,isExternal:o}),Cv=e=>{const{prefix:t,experimentalParseClassName:n}=e;let a=o=>{const i=[];let s=0,d=0,u=0,p;const x=o.length;for(let R=0;R<x;R++){const b=o[R];if(s===0&&d===0){if(b===Ni){i.push(o.slice(u,R)),u=R+1;continue}if(b==="/"){p=R;continue}}b==="["?s++:b==="]"?s--:b==="("?d++:b===")"&&d--}const g=i.length===0?o:o.slice(u);let w=g,P=!1;g.endsWith(js)?(w=g.slice(0,-1),P=!0):g.startsWith(js)&&(w=g.slice(1),P=!0);const C=p&&p>u?p-u:void 0;return Li(i,P,w,C)};if(t){const o=t+Ni,i=a;a=s=>s.startsWith(o)?i(s.slice(o.length)):Li(kv,!1,s,void 0,!0)}if(n){const o=a;a=i=>n({className:i,parseClassName:o})}return a},Sv=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((n,a)=>{t.set(n,1e6+a)}),n=>{const a=[];let o=[];for(let i=0;i<n.length;i++){const s=n[i],d=s[0]==="[",u=t.has(s);d||u?(o.length>0&&(o.sort(),a.push(...o),o=[]),a.push(s)):o.push(s)}return o.length>0&&(o.sort(),a.push(...o)),a}},$v=e=>({cache:yv(e.cacheSize),parseClassName:Cv(e),sortModifiers:Sv(e),...fv(e)}),Mv=/\s+/,Tv=(e,t)=>{const{parseClassName:n,getClassGroupId:a,getConflictingClassGroupIds:o,sortModifiers:i}=t,s=[],d=e.trim().split(Mv);let u="";for(let p=d.length-1;p>=0;p-=1){const x=d[p],{isExternal:g,modifiers:w,hasImportantModifier:P,baseClassName:C,maybePostfixModifierPosition:R}=n(x);if(g){u=x+(u.length>0?" "+u:u);continue}let b=!!R,S=a(b?C.substring(0,R):C);if(!S){if(!b){u=x+(u.length>0?" "+u:u);continue}if(S=a(C),!S){u=x+(u.length>0?" "+u:u);continue}b=!1}const M=w.length===0?"":w.length===1?w[0]:i(w).join(":"),V=P?M+js:M,E=V+S;if(s.indexOf(E)>-1)continue;s.push(E);const F=o(S,b);for(let se=0;se<F.length;++se){const ne=F[se];s.push(V+ne)}u=x+(u.length>0?" "+u:u)}return u},zv=(...e)=>{let t=0,n,a,o="";for(;t<e.length;)(n=e[t++])&&(a=ad(n))&&(o&&(o+=" "),o+=a);return o},ad=e=>{if(typeof e=="string")return e;let t,n="";for(let a=0;a<e.length;a++)e[a]&&(t=ad(e[a]))&&(n&&(n+=" "),n+=t);return n},Ev=(e,...t)=>{let n,a,o,i;const s=u=>{const p=t.reduce((x,g)=>g(x),e());return n=$v(p),a=n.cache.get,o=n.cache.set,i=d,d(u)},d=u=>{const p=a(u);if(p)return p;const x=Tv(u,n);return o(u,x),x};return i=s,(...u)=>i(zv(...u))},Av=[],xr=e=>{const t=n=>n[e]||Av;return t.isThemeGetter=!0,t},od=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,sd=/^\((?:(\w[\w-]*):)?(.+)\)$/i,Iv=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,Pv=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,Nv=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,Lv=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,Ov=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,Rv=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,ra=e=>Iv.test(e),xt=e=>!!e&&!Number.isNaN(Number(e)),na=e=>!!e&&Number.isInteger(Number(e)),gs=e=>e.endsWith("%")&&xt(e.slice(0,-1)),Bn=e=>Pv.test(e),id=()=>!0,Dv=e=>Nv.test(e)&&!Lv.test(e),ai=()=>!1,jv=e=>Ov.test(e),Vv=e=>Rv.test(e),Fv=e=>!_e(e)&&!ye(e),qv=e=>ba(e,cd,ai),_e=e=>od.test(e),ka=e=>ba(e,ud,Dv),Oi=e=>ba(e,Xv,xt),Bv=e=>ba(e,fd,id),Uv=e=>ba(e,vd,ai),Ri=e=>ba(e,ld,ai),Gv=e=>ba(e,dd,Vv),qo=e=>ba(e,pd,jv),ye=e=>sd.test(e),_o=e=>qa(e,ud),Hv=e=>qa(e,vd),Di=e=>qa(e,ld),Kv=e=>qa(e,cd),Wv=e=>qa(e,dd),Bo=e=>qa(e,pd,!0),Yv=e=>qa(e,fd,!0),ba=(e,t,n)=>{const a=od.exec(e);return a?a[1]?t(a[1]):n(a[2]):!1},qa=(e,t,n=!1)=>{const a=sd.exec(e);return a?a[1]?t(a[1]):n:!1},ld=e=>e==="position"||e==="percentage",dd=e=>e==="image"||e==="url",cd=e=>e==="length"||e==="size"||e==="bg-size",ud=e=>e==="length",Xv=e=>e==="number",vd=e=>e==="family-name",fd=e=>e==="number"||e==="weight",pd=e=>e==="shadow",Jv=()=>{const e=xr("color"),t=xr("font"),n=xr("text"),a=xr("font-weight"),o=xr("tracking"),i=xr("leading"),s=xr("breakpoint"),d=xr("container"),u=xr("spacing"),p=xr("radius"),x=xr("shadow"),g=xr("inset-shadow"),w=xr("text-shadow"),P=xr("drop-shadow"),C=xr("blur"),R=xr("perspective"),b=xr("aspect"),S=xr("ease"),M=xr("animate"),V=()=>["auto","avoid","all","avoid-page","page","left","right","column"],E=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],F=()=>[...E(),ye,_e],se=()=>["auto","hidden","clip","visible","scroll"],ne=()=>["auto","contain","none"],z=()=>[ye,_e,u],N=()=>[ra,"full","auto",...z()],X=()=>[na,"none","subgrid",ye,_e],H=()=>["auto",{span:["full",na,ye,_e]},na,ye,_e],O=()=>[na,"auto",ye,_e],ce=()=>["auto","min","max","fr",ye,_e],ve=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],Pe=()=>["start","end","center","stretch","center-safe","end-safe"],he=()=>["auto",...z()],Ne=()=>[ra,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...z()],me=()=>[ra,"screen","full","dvw","lvw","svw","min","max","fit",...z()],de=()=>[ra,"screen","full","lh","dvh","lvh","svh","min","max","fit",...z()],B=()=>[e,ye,_e],ue=()=>[...E(),Di,Ri,{position:[ye,_e]}],le=()=>["no-repeat",{repeat:["","x","y","space","round"]}],D=()=>["auto","cover","contain",Kv,qv,{size:[ye,_e]}],m=()=>[gs,_o,ka],_=()=>["","none","full",p,ye,_e],T=()=>["",xt,_o,ka],K=()=>["solid","dashed","dotted","double"],W=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],L=()=>[xt,gs,Di,Ri],xe=()=>["","none",C,ye,_e],Ee=()=>["none",xt,ye,_e],at=()=>["none",xt,ye,_e],Ae=()=>[xt,ye,_e],Tt=()=>[ra,"full",...z()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Bn],breakpoint:[Bn],color:[id],container:[Bn],"drop-shadow":[Bn],ease:["in","out","in-out"],font:[Fv],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Bn],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Bn],shadow:[Bn],spacing:["px",xt],text:[Bn],"text-shadow":[Bn],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",ra,_e,ye,b]}],container:["container"],columns:[{columns:[xt,_e,ye,d]}],"break-after":[{"break-after":V()}],"break-before":[{"break-before":V()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:F()}],overflow:[{overflow:se()}],"overflow-x":[{"overflow-x":se()}],"overflow-y":[{"overflow-y":se()}],overscroll:[{overscroll:ne()}],"overscroll-x":[{"overscroll-x":ne()}],"overscroll-y":[{"overscroll-y":ne()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:N()}],"inset-x":[{"inset-x":N()}],"inset-y":[{"inset-y":N()}],start:[{"inset-s":N(),start:N()}],end:[{"inset-e":N(),end:N()}],"inset-bs":[{"inset-bs":N()}],"inset-be":[{"inset-be":N()}],top:[{top:N()}],right:[{right:N()}],bottom:[{bottom:N()}],left:[{left:N()}],visibility:["visible","invisible","collapse"],z:[{z:[na,"auto",ye,_e]}],basis:[{basis:[ra,"full","auto",d,...z()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[xt,ra,"auto","initial","none",_e]}],grow:[{grow:["",xt,ye,_e]}],shrink:[{shrink:["",xt,ye,_e]}],order:[{order:[na,"first","last","none",ye,_e]}],"grid-cols":[{"grid-cols":X()}],"col-start-end":[{col:H()}],"col-start":[{"col-start":O()}],"col-end":[{"col-end":O()}],"grid-rows":[{"grid-rows":X()}],"row-start-end":[{row:H()}],"row-start":[{"row-start":O()}],"row-end":[{"row-end":O()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":ce()}],"auto-rows":[{"auto-rows":ce()}],gap:[{gap:z()}],"gap-x":[{"gap-x":z()}],"gap-y":[{"gap-y":z()}],"justify-content":[{justify:[...ve(),"normal"]}],"justify-items":[{"justify-items":[...Pe(),"normal"]}],"justify-self":[{"justify-self":["auto",...Pe()]}],"align-content":[{content:["normal",...ve()]}],"align-items":[{items:[...Pe(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...Pe(),{baseline:["","last"]}]}],"place-content":[{"place-content":ve()}],"place-items":[{"place-items":[...Pe(),"baseline"]}],"place-self":[{"place-self":["auto",...Pe()]}],p:[{p:z()}],px:[{px:z()}],py:[{py:z()}],ps:[{ps:z()}],pe:[{pe:z()}],pbs:[{pbs:z()}],pbe:[{pbe:z()}],pt:[{pt:z()}],pr:[{pr:z()}],pb:[{pb:z()}],pl:[{pl:z()}],m:[{m:he()}],mx:[{mx:he()}],my:[{my:he()}],ms:[{ms:he()}],me:[{me:he()}],mbs:[{mbs:he()}],mbe:[{mbe:he()}],mt:[{mt:he()}],mr:[{mr:he()}],mb:[{mb:he()}],ml:[{ml:he()}],"space-x":[{"space-x":z()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":z()}],"space-y-reverse":["space-y-reverse"],size:[{size:Ne()}],"inline-size":[{inline:["auto",...me()]}],"min-inline-size":[{"min-inline":["auto",...me()]}],"max-inline-size":[{"max-inline":["none",...me()]}],"block-size":[{block:["auto",...de()]}],"min-block-size":[{"min-block":["auto",...de()]}],"max-block-size":[{"max-block":["none",...de()]}],w:[{w:[d,"screen",...Ne()]}],"min-w":[{"min-w":[d,"screen","none",...Ne()]}],"max-w":[{"max-w":[d,"screen","none","prose",{screen:[s]},...Ne()]}],h:[{h:["screen","lh",...Ne()]}],"min-h":[{"min-h":["screen","lh","none",...Ne()]}],"max-h":[{"max-h":["screen","lh",...Ne()]}],"font-size":[{text:["base",n,_o,ka]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[a,Yv,Bv]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",gs,_e]}],"font-family":[{font:[Hv,Uv,t]}],"font-features":[{"font-features":[_e]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[o,ye,_e]}],"line-clamp":[{"line-clamp":[xt,"none",ye,Oi]}],leading:[{leading:[i,...z()]}],"list-image":[{"list-image":["none",ye,_e]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",ye,_e]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:B()}],"text-color":[{text:B()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...K(),"wavy"]}],"text-decoration-thickness":[{decoration:[xt,"from-font","auto",ye,ka]}],"text-decoration-color":[{decoration:B()}],"underline-offset":[{"underline-offset":[xt,"auto",ye,_e]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:z()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",ye,_e]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",ye,_e]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:ue()}],"bg-repeat":[{bg:le()}],"bg-size":[{bg:D()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},na,ye,_e],radial:["",ye,_e],conic:[na,ye,_e]},Wv,Gv]}],"bg-color":[{bg:B()}],"gradient-from-pos":[{from:m()}],"gradient-via-pos":[{via:m()}],"gradient-to-pos":[{to:m()}],"gradient-from":[{from:B()}],"gradient-via":[{via:B()}],"gradient-to":[{to:B()}],rounded:[{rounded:_()}],"rounded-s":[{"rounded-s":_()}],"rounded-e":[{"rounded-e":_()}],"rounded-t":[{"rounded-t":_()}],"rounded-r":[{"rounded-r":_()}],"rounded-b":[{"rounded-b":_()}],"rounded-l":[{"rounded-l":_()}],"rounded-ss":[{"rounded-ss":_()}],"rounded-se":[{"rounded-se":_()}],"rounded-ee":[{"rounded-ee":_()}],"rounded-es":[{"rounded-es":_()}],"rounded-tl":[{"rounded-tl":_()}],"rounded-tr":[{"rounded-tr":_()}],"rounded-br":[{"rounded-br":_()}],"rounded-bl":[{"rounded-bl":_()}],"border-w":[{border:T()}],"border-w-x":[{"border-x":T()}],"border-w-y":[{"border-y":T()}],"border-w-s":[{"border-s":T()}],"border-w-e":[{"border-e":T()}],"border-w-bs":[{"border-bs":T()}],"border-w-be":[{"border-be":T()}],"border-w-t":[{"border-t":T()}],"border-w-r":[{"border-r":T()}],"border-w-b":[{"border-b":T()}],"border-w-l":[{"border-l":T()}],"divide-x":[{"divide-x":T()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":T()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...K(),"hidden","none"]}],"divide-style":[{divide:[...K(),"hidden","none"]}],"border-color":[{border:B()}],"border-color-x":[{"border-x":B()}],"border-color-y":[{"border-y":B()}],"border-color-s":[{"border-s":B()}],"border-color-e":[{"border-e":B()}],"border-color-bs":[{"border-bs":B()}],"border-color-be":[{"border-be":B()}],"border-color-t":[{"border-t":B()}],"border-color-r":[{"border-r":B()}],"border-color-b":[{"border-b":B()}],"border-color-l":[{"border-l":B()}],"divide-color":[{divide:B()}],"outline-style":[{outline:[...K(),"none","hidden"]}],"outline-offset":[{"outline-offset":[xt,ye,_e]}],"outline-w":[{outline:["",xt,_o,ka]}],"outline-color":[{outline:B()}],shadow:[{shadow:["","none",x,Bo,qo]}],"shadow-color":[{shadow:B()}],"inset-shadow":[{"inset-shadow":["none",g,Bo,qo]}],"inset-shadow-color":[{"inset-shadow":B()}],"ring-w":[{ring:T()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:B()}],"ring-offset-w":[{"ring-offset":[xt,ka]}],"ring-offset-color":[{"ring-offset":B()}],"inset-ring-w":[{"inset-ring":T()}],"inset-ring-color":[{"inset-ring":B()}],"text-shadow":[{"text-shadow":["none",w,Bo,qo]}],"text-shadow-color":[{"text-shadow":B()}],opacity:[{opacity:[xt,ye,_e]}],"mix-blend":[{"mix-blend":[...W(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":W()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[xt]}],"mask-image-linear-from-pos":[{"mask-linear-from":L()}],"mask-image-linear-to-pos":[{"mask-linear-to":L()}],"mask-image-linear-from-color":[{"mask-linear-from":B()}],"mask-image-linear-to-color":[{"mask-linear-to":B()}],"mask-image-t-from-pos":[{"mask-t-from":L()}],"mask-image-t-to-pos":[{"mask-t-to":L()}],"mask-image-t-from-color":[{"mask-t-from":B()}],"mask-image-t-to-color":[{"mask-t-to":B()}],"mask-image-r-from-pos":[{"mask-r-from":L()}],"mask-image-r-to-pos":[{"mask-r-to":L()}],"mask-image-r-from-color":[{"mask-r-from":B()}],"mask-image-r-to-color":[{"mask-r-to":B()}],"mask-image-b-from-pos":[{"mask-b-from":L()}],"mask-image-b-to-pos":[{"mask-b-to":L()}],"mask-image-b-from-color":[{"mask-b-from":B()}],"mask-image-b-to-color":[{"mask-b-to":B()}],"mask-image-l-from-pos":[{"mask-l-from":L()}],"mask-image-l-to-pos":[{"mask-l-to":L()}],"mask-image-l-from-color":[{"mask-l-from":B()}],"mask-image-l-to-color":[{"mask-l-to":B()}],"mask-image-x-from-pos":[{"mask-x-from":L()}],"mask-image-x-to-pos":[{"mask-x-to":L()}],"mask-image-x-from-color":[{"mask-x-from":B()}],"mask-image-x-to-color":[{"mask-x-to":B()}],"mask-image-y-from-pos":[{"mask-y-from":L()}],"mask-image-y-to-pos":[{"mask-y-to":L()}],"mask-image-y-from-color":[{"mask-y-from":B()}],"mask-image-y-to-color":[{"mask-y-to":B()}],"mask-image-radial":[{"mask-radial":[ye,_e]}],"mask-image-radial-from-pos":[{"mask-radial-from":L()}],"mask-image-radial-to-pos":[{"mask-radial-to":L()}],"mask-image-radial-from-color":[{"mask-radial-from":B()}],"mask-image-radial-to-color":[{"mask-radial-to":B()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":E()}],"mask-image-conic-pos":[{"mask-conic":[xt]}],"mask-image-conic-from-pos":[{"mask-conic-from":L()}],"mask-image-conic-to-pos":[{"mask-conic-to":L()}],"mask-image-conic-from-color":[{"mask-conic-from":B()}],"mask-image-conic-to-color":[{"mask-conic-to":B()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:ue()}],"mask-repeat":[{mask:le()}],"mask-size":[{mask:D()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",ye,_e]}],filter:[{filter:["","none",ye,_e]}],blur:[{blur:xe()}],brightness:[{brightness:[xt,ye,_e]}],contrast:[{contrast:[xt,ye,_e]}],"drop-shadow":[{"drop-shadow":["","none",P,Bo,qo]}],"drop-shadow-color":[{"drop-shadow":B()}],grayscale:[{grayscale:["",xt,ye,_e]}],"hue-rotate":[{"hue-rotate":[xt,ye,_e]}],invert:[{invert:["",xt,ye,_e]}],saturate:[{saturate:[xt,ye,_e]}],sepia:[{sepia:["",xt,ye,_e]}],"backdrop-filter":[{"backdrop-filter":["","none",ye,_e]}],"backdrop-blur":[{"backdrop-blur":xe()}],"backdrop-brightness":[{"backdrop-brightness":[xt,ye,_e]}],"backdrop-contrast":[{"backdrop-contrast":[xt,ye,_e]}],"backdrop-grayscale":[{"backdrop-grayscale":["",xt,ye,_e]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[xt,ye,_e]}],"backdrop-invert":[{"backdrop-invert":["",xt,ye,_e]}],"backdrop-opacity":[{"backdrop-opacity":[xt,ye,_e]}],"backdrop-saturate":[{"backdrop-saturate":[xt,ye,_e]}],"backdrop-sepia":[{"backdrop-sepia":["",xt,ye,_e]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":z()}],"border-spacing-x":[{"border-spacing-x":z()}],"border-spacing-y":[{"border-spacing-y":z()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",ye,_e]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[xt,"initial",ye,_e]}],ease:[{ease:["linear","initial",S,ye,_e]}],delay:[{delay:[xt,ye,_e]}],animate:[{animate:["none",M,ye,_e]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[R,ye,_e]}],"perspective-origin":[{"perspective-origin":F()}],rotate:[{rotate:Ee()}],"rotate-x":[{"rotate-x":Ee()}],"rotate-y":[{"rotate-y":Ee()}],"rotate-z":[{"rotate-z":Ee()}],scale:[{scale:at()}],"scale-x":[{"scale-x":at()}],"scale-y":[{"scale-y":at()}],"scale-z":[{"scale-z":at()}],"scale-3d":["scale-3d"],skew:[{skew:Ae()}],"skew-x":[{"skew-x":Ae()}],"skew-y":[{"skew-y":Ae()}],transform:[{transform:[ye,_e,"","none","gpu","cpu"]}],"transform-origin":[{origin:F()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:Tt()}],"translate-x":[{"translate-x":Tt()}],"translate-y":[{"translate-y":Tt()}],"translate-z":[{"translate-z":Tt()}],"translate-none":["translate-none"],accent:[{accent:B()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:B()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",ye,_e]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":z()}],"scroll-mx":[{"scroll-mx":z()}],"scroll-my":[{"scroll-my":z()}],"scroll-ms":[{"scroll-ms":z()}],"scroll-me":[{"scroll-me":z()}],"scroll-mbs":[{"scroll-mbs":z()}],"scroll-mbe":[{"scroll-mbe":z()}],"scroll-mt":[{"scroll-mt":z()}],"scroll-mr":[{"scroll-mr":z()}],"scroll-mb":[{"scroll-mb":z()}],"scroll-ml":[{"scroll-ml":z()}],"scroll-p":[{"scroll-p":z()}],"scroll-px":[{"scroll-px":z()}],"scroll-py":[{"scroll-py":z()}],"scroll-ps":[{"scroll-ps":z()}],"scroll-pe":[{"scroll-pe":z()}],"scroll-pbs":[{"scroll-pbs":z()}],"scroll-pbe":[{"scroll-pbe":z()}],"scroll-pt":[{"scroll-pt":z()}],"scroll-pr":[{"scroll-pr":z()}],"scroll-pb":[{"scroll-pb":z()}],"scroll-pl":[{"scroll-pl":z()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",ye,_e]}],fill:[{fill:["none",...B()]}],"stroke-w":[{stroke:[xt,_o,ka,Oi]}],stroke:[{stroke:["none",...B()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},Qv=Ev(Jv);function Jt(...e){return Qv(Yl(e))}const Vs="dartlab-conversations",ji=50;function Zv(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function ef(){try{const e=localStorage.getItem(Vs);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const tf=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function Vi(e){return e.map(t=>({...t,messages:t.messages.map(n=>{if(n.role!=="assistant")return n;const a={};for(const[o,i]of Object.entries(n))tf.includes(o)||(a[o]=i);return a})}))}function Fi(e){try{const t={conversations:Vi(e.conversations),activeId:e.activeId};localStorage.setItem(Vs,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:Vi(e.conversations),activeId:e.activeId};localStorage.setItem(Vs,JSON.stringify(t))}catch{}}}}function rf(){const e=ef(),t=e.conversations||[],n=t.find(S=>S.id===e.activeId)?e.activeId:null;let a=G(Gt(t)),o=G(Gt(n)),i=null;function s(){i&&clearTimeout(i),i=setTimeout(()=>{Fi({conversations:r(a),activeId:r(o)}),i=null},300)}function d(){i&&clearTimeout(i),i=null,Fi({conversations:r(a),activeId:r(o)})}function u(){return r(a).find(S=>S.id===r(o))||null}function p(){const S={id:Zv(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return v(a,[S,...r(a)],!0),r(a).length>ji&&v(a,r(a).slice(0,ji),!0),v(o,S.id,!0),d(),S.id}function x(S){r(a).find(M=>M.id===S)&&(v(o,S,!0),d())}function g(S,M,V=null){const E=u();if(!E)return;const F={role:S,text:M};V&&(F.meta=V),E.messages=[...E.messages,F],E.updatedAt=Date.now(),E.title==="새 대화"&&S==="user"&&(E.title=M.length>30?M.slice(0,30)+"...":M),v(a,[...r(a)],!0),d()}function w(S){const M=u();if(!M||M.messages.length===0)return;const V=M.messages[M.messages.length-1];Object.assign(V,S),M.updatedAt=Date.now(),v(a,[...r(a)],!0),s()}function P(S){v(a,r(a).filter(M=>M.id!==S),!0),r(o)===S&&v(o,r(a).length>0?r(a)[0].id:null,!0),d()}function C(){const S=u();!S||S.messages.length===0||(S.messages=S.messages.slice(0,-1),S.updatedAt=Date.now(),v(a,[...r(a)],!0),d())}function R(S,M){const V=r(a).find(E=>E.id===S);V&&(V.title=M,v(a,[...r(a)],!0),d())}function b(){v(a,[],!0),v(o,null),d()}return{get conversations(){return r(a)},get activeId(){return r(o)},get active(){return u()},createConversation:p,setActive:x,addMessage:g,updateLastMessage:w,removeLastMessage:C,deleteConversation:P,updateTitle:R,clearAll:b,flush:d}}const md="dartlab-workspace",nf=6;function xd(){return typeof window<"u"&&typeof localStorage<"u"}function af(){if(!xd())return{};try{const e=localStorage.getItem(md);return e?JSON.parse(e):{}}catch{return{}}}function of(e){xd()&&localStorage.setItem(md,JSON.stringify(e))}function sf(){const e=af();let t=G("chat"),n=G(!1),a=G(null),o=G(null),i=G("explore"),s=G(null),d=G(null),u=G(null),p=G(null),x=G(Gt(e.selectedCompany||null)),g=G(Gt(e.recentCompanies||[]));function w(){of({selectedCompany:r(x),recentCompanies:r(g)})}function P(N){if(!(N!=null&&N.stockCode))return;const X={stockCode:N.stockCode,corpName:N.corpName||N.company||N.stockCode,company:N.company||N.corpName||N.stockCode,market:N.market||""};v(g,[X,...r(g).filter(H=>H.stockCode!==X.stockCode)].slice(0,nf),!0)}function C(N){v(t,N,!0)}function R(N){N&&(v(x,N,!0),P(N)),v(t,"viewer"),v(n,!1),w()}function b(N){v(a,"data"),v(o,N,!0),v(n,!0),ne("explore")}function S(){v(n,!1)}function M(N){v(x,N,!0),N&&P(N),w()}function V(N,X){var H,O,ce,ve;!(N!=null&&N.company)&&!(N!=null&&N.stockCode)||(v(x,{...r(x)||{},...X||{},corpName:N.company||((H=r(x))==null?void 0:H.corpName)||(X==null?void 0:X.corpName)||(X==null?void 0:X.company),company:N.company||((O=r(x))==null?void 0:O.company)||(X==null?void 0:X.company)||(X==null?void 0:X.corpName),stockCode:N.stockCode||((ce=r(x))==null?void 0:ce.stockCode)||(X==null?void 0:X.stockCode),market:((ve=r(x))==null?void 0:ve.market)||(X==null?void 0:X.market)||""},!0),P(r(x)),w())}function E(N,X){v(u,N,!0),v(p,X||N,!0)}function F(N,X=null){v(a,"data"),v(n,!0),v(i,"evidence"),v(s,N,!0),v(d,Number.isInteger(X)?X:null,!0)}function se(){v(s,null),v(d,null)}function ne(N){v(i,N||"explore",!0),r(i)!=="evidence"&&se()}function z(){return r(t)==="viewer"&&r(x)&&r(u)?{type:"viewer",company:r(x),topic:r(u),topicLabel:r(p)}:r(n)?r(a)==="viewer"&&r(x)?{type:"viewer",company:r(x),topic:r(u),topicLabel:r(p)}:r(a)==="data"&&r(o)?{type:"data",data:r(o)}:null:null}return{get activeView(){return r(t)},get panelOpen(){return r(n)},get panelMode(){return r(a)},get panelData(){return r(o)},get activeTab(){return r(i)},get activeEvidenceSection(){return r(s)},get selectedEvidenceIndex(){return r(d)},get selectedCompany(){return r(x)},get recentCompanies(){return r(g)},get viewerTopic(){return r(u)},get viewerTopicLabel(){return r(p)},switchView:C,openViewer:R,openData:b,openEvidence:F,closePanel:S,selectCompany:M,setViewerTopic:E,clearEvidenceSelection:se,setTab:ne,syncCompanyFromMessage:V,getViewContext:z}}function lf(){let e=G(null),t=G(null),n=G(null),a=G(!1),o=G(null),i=G(null),s=G(Gt(new Set)),d=G(null),u=G(!1),p=G(null),x=new Map;async function g(C){var R,b;if(!(C===r(e)&&r(n))){v(e,C,!0),v(t,null),v(n,null),v(o,null),v(i,null),v(d,null),v(p,null),x=new Map,v(s,new Set,!0),v(a,!0);try{const S=await ov(C);if(v(n,S,!0),v(t,S.corpName,!0),((R=S.chapters)==null?void 0:R.length)>0&&(v(s,new Set([S.chapters[0].chapter]),!0),((b=S.chapters[0].topics)==null?void 0:b.length)>0)){const M=S.chapters[0].topics[0];await w(M.topic,S.chapters[0].chapter)}}catch(S){console.error("TOC 로드 실패:",S)}v(a,!1)}}async function w(C,R){if(C!==r(o)){if(v(o,C,!0),v(i,R,!0),R&&!r(s).has(R)&&v(s,new Set([...r(s),R]),!0),x.has(C)){v(d,x.get(C),!0);return}v(u,!0),v(d,null),v(p,null);try{const[b,S]=await Promise.allSettled([sv(r(e),C),iv(r(e),C)]);b.status==="fulfilled"&&(v(d,b.value,!0),x.set(C,b.value)),S.status==="fulfilled"&&v(p,S.value,!0)}catch(b){console.error("Topic 로드 실패:",b)}v(u,!1)}}function P(C){const R=new Set(r(s));R.has(C)?R.delete(C):R.add(C),v(s,R,!0)}return{get stockCode(){return r(e)},get corpName(){return r(t)},get toc(){return r(n)},get tocLoading(){return r(a)},get selectedTopic(){return r(o)},get selectedChapter(){return r(i)},get expandedChapters(){return r(s)},get topicData(){return r(d)},get topicLoading(){return r(u)},get diffSummary(){return r(p)},loadCompany:g,selectTopic:w,toggleChapter:P}}var df=f("<a><!></a>"),cf=f("<button><!></button>");function uf(e,t){wr(t,!0);let n=Be(t,"variant",3,"default"),a=Be(t,"size",3,"default"),o=Ku(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const i={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},s={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var d=be(),u=Q(d);{var p=g=>{var w=df();Yo(w,C=>({class:C,...o}),[()=>Jt("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",i[n()],s[a()],t.class)]);var P=l(w);Rs(P,()=>t.children),c(g,w)},x=g=>{var w=cf();Yo(w,C=>({class:C,...o}),[()=>Jt("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",i[n()],s[a()],t.class)]);var P=l(w);Rs(P,()=>t.children),c(g,w)};k(u,g=>{t.href?g(p):g(x,-1)})}c(e,d),yr()}jc();/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const vf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const ff=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const qi=(...e)=>e.filter((t,n,a)=>!!t&&t.trim()!==""&&a.indexOf(t)===n).join(" ").trim();var pf=Tu("<svg><!><!></svg>");function lt(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]),a=rt(n,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);wr(t,!1);let o=Be(t,"name",8,void 0),i=Be(t,"color",8,"currentColor"),s=Be(t,"size",8,24),d=Be(t,"strokeWidth",8,2),u=Be(t,"absoluteStrokeWidth",8,!1),p=Be(t,"iconNode",24,()=>[]);Uu();var x=pf();Yo(x,(P,C,R)=>({...vf,...P,...a,width:s(),height:s(),stroke:i(),"stroke-width":C,class:R}),[()=>ff(a)?void 0:{"aria-hidden":"true"},()=>(Ca(u()),Ca(d()),Ca(s()),ja(()=>u()?Number(d())*24/Number(s()):d())),()=>(Ca(qi),Ca(o()),Ca(n),ja(()=>qi("lucide-icon","lucide",o()?`lucide-${o()}`:"",n.class)))]);var g=l(x);ke(g,1,p,Se,(P,C)=>{var R=q(()=>el(r(C),2));let b=()=>r(R)[0],S=()=>r(R)[1];var M=be(),V=Q(M);Lu(V,b,!0,(E,F)=>{Yo(E,()=>({...S()}))}),c(P,M)});var w=h(g);nt(w,t,"default",{}),c(e,x),yr()}function mf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];lt(e,it({name:"activity"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function xf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"m12 5 7 7-7 7"}]];lt(e,it({name:"arrow-right"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function hf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];lt(e,it({name:"arrow-up"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Fs(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 7v14"}],["path",{d:"M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"}]];lt(e,it({name:"book-open"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function bs(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];lt(e,it({name:"brain"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function hd(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]];lt(e,it({name:"chart-column"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function qs(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M20 6 9 17l-5-5"}]];lt(e,it({name:"check"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function gd(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m6 9 6 6 6-6"}]];lt(e,it({name:"chevron-down"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function bd(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m9 18 6-6-6-6"}]];lt(e,it({name:"chevron-right"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ka(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];lt(e,it({name:"circle-alert"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Mo(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];lt(e,it({name:"circle-check"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function gf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];lt(e,it({name:"clock"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function bf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];lt(e,it({name:"code"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function _f(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];lt(e,it({name:"coffee"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Bi(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]];lt(e,it({name:"copy"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function wo(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];lt(e,it({name:"database"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function To(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];lt(e,it({name:"download"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ui(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];lt(e,it({name:"external-link"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function wf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];lt(e,it({name:"eye"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function on(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];lt(e,it({name:"file-text"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function yf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];lt(e,it({name:"github"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Gi(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];lt(e,it({name:"key"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Hr(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];lt(e,it({name:"loader-circle"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function kf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];lt(e,it({name:"log-out"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function _d(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"m21 3-7 7"}],["path",{d:"m3 21 7-7"}],["path",{d:"M9 21H3v-6"}]];lt(e,it({name:"maximize-2"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Cf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];lt(e,it({name:"menu"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Jo(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];lt(e,it({name:"message-square"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function wd(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m14 10 7-7"}],["path",{d:"M20 10h-6V4"}],["path",{d:"m3 21 7-7"}],["path",{d:"M4 14h6v6"}]];lt(e,it({name:"minimize-2"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Sf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}]];lt(e,it({name:"minus"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function $f(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];lt(e,it({name:"panel-left-close"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Hi(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];lt(e,it({name:"plus"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Mf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];lt(e,it({name:"refresh-cw"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Oa(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];lt(e,it({name:"search"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Tf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];lt(e,it({name:"settings"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function zf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];lt(e,it({name:"square"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ef(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];lt(e,it({name:"table-2"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Af(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];lt(e,it({name:"terminal"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function If(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];lt(e,it({name:"trash-2"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Pf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M16 7h6v6"}],["path",{d:"m22 7-8.5 8.5-5-5L2 17"}]];lt(e,it({name:"trending-up"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Nf(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];lt(e,it({name:"triangle-alert"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ki(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];lt(e,it({name:"wrench"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function io(e,t){const n=rt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];lt(e,it({name:"x"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),d=Q(s);nt(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}var Lf=f("<!> 새 대화",1),Of=f('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),Rf=f('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),Df=f('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),jf=f('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40"><span class="text-[10px] text-dl-text-dim font-mono"> </span></div>'),Vf=f('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),Ff=f("<button><!></button>"),qf=f('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),Bf=f("<aside><!></aside>");function Uf(e,t){wr(t,!0);let n=Be(t,"conversations",19,()=>[]),a=Be(t,"activeId",3,null),o=Be(t,"open",3,!0),i=Be(t,"version",3,""),s=G("");function d(C){const R=new Date().setHours(0,0,0,0),b=R-864e5,S=R-7*864e5,M={오늘:[],어제:[],"이번 주":[],이전:[]};for(const E of C)E.updatedAt>=R?M.오늘.push(E):E.updatedAt>=b?M.어제.push(E):E.updatedAt>=S?M["이번 주"].push(E):M.이전.push(E);const V=[];for(const[E,F]of Object.entries(M))F.length>0&&V.push({label:E,items:F});return V}let u=q(()=>r(s).trim()?n().filter(C=>C.title.toLowerCase().includes(r(s).toLowerCase())):n()),p=q(()=>d(r(u)));var x=Bf(),g=l(x);{var w=C=>{var R=Vf(),b=h(l(R),2),S=l(b);uf(S,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(ne,z)=>{var N=Lf(),X=Q(N);Hi(X,{size:16}),c(ne,N)},$$slots:{default:!0}});var M=h(b,2);{var V=ne=>{var z=Of(),N=l(z),X=l(N);Oa(X,{size:12,class:"text-dl-text-dim flex-shrink-0"});var H=h(X,2);za(H,()=>r(s),O=>v(s,O)),c(ne,z)};k(M,ne=>{n().length>3&&ne(V)})}var E=h(M,2);ke(E,21,()=>r(p),Se,(ne,z)=>{var N=Df(),X=l(N),H=l(X),O=h(X,2);ke(O,17,()=>r(z).items,Se,(ce,ve)=>{var Pe=Rf(),he=l(Pe),Ne=l(he);Jo(Ne,{size:14,class:"flex-shrink-0 opacity-50"});var me=h(Ne,2),de=l(me),B=h(he,2),ue=l(B);If(ue,{size:12}),I(le=>{je(Pe,1,le),Dn(he,"aria-current",r(ve).id===a()?"true":void 0),A(de,r(ve).title),Dn(B,"aria-label",`${r(ve).title} 삭제`)},[()=>Ut(Jt("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",r(ve).id===a()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),oe("click",he,()=>{var le;return(le=t.onSelect)==null?void 0:le.call(t,r(ve).id)}),oe("click",B,le=>{var D;le.stopPropagation(),(D=t.onDelete)==null||D.call(t,r(ve).id)}),c(ce,Pe)}),I(()=>A(H,r(z).label)),c(ne,N)});var F=h(E,2);{var se=ne=>{var z=jf(),N=l(z),X=l(N);I(()=>A(X,`v${i()??""}`)),c(ne,z)};k(F,ne=>{i()&&ne(se)})}c(C,R)},P=C=>{var R=qf(),b=h(l(R),2),S=l(b);Hi(S,{size:18});var M=h(b,2);ke(M,21,()=>n().slice(0,10),Se,(V,E)=>{var F=Ff(),se=l(F);Jo(se,{size:16}),I(ne=>{je(F,1,ne),Dn(F,"title",r(E).title)},[()=>Ut(Jt("p-2 rounded-lg transition-colors w-full flex justify-center",r(E).id===a()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),oe("click",F,()=>{var ne;return(ne=t.onSelect)==null?void 0:ne.call(t,r(E).id)}),c(V,F)}),oe("click",b,function(...V){var E;(E=t.onNewChat)==null||E.apply(this,V)}),c(C,R)};k(g,C=>{o()?C(w):C(P,-1)})}I(C=>je(x,1,C),[()=>Ut(Jt("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",o()?"w-[260px]":"w-[52px]"))]),c(e,x),yr()}Yr(["click"]);var Gf=f('<button class="send-btn active"><!></button>'),Hf=f("<button><!></button>"),Kf=f('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),Wf=f('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),Yf=f('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),Xf=f('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function yd(e,t){wr(t,!0);let n=Be(t,"inputText",15,""),a=Be(t,"isLoading",3,!1),o=Be(t,"large",3,!1),i=Be(t,"placeholder",3,"메시지를 입력하세요..."),s=G(Gt([])),d=G(!1),u=G(-1),p=null,x=G(void 0);function g(z){var N;if(r(d)&&r(s).length>0){if(z.key==="ArrowDown"){z.preventDefault(),v(u,(r(u)+1)%r(s).length);return}if(z.key==="ArrowUp"){z.preventDefault(),v(u,r(u)<=0?r(s).length-1:r(u)-1,!0);return}if(z.key==="Enter"&&r(u)>=0){z.preventDefault(),C(r(s)[r(u)]);return}if(z.key==="Escape"){v(d,!1),v(u,-1);return}}z.key==="Enter"&&!z.shiftKey&&(z.preventDefault(),v(d,!1),(N=t.onSend)==null||N.call(t))}function w(z){z.target.style.height="auto",z.target.style.height=Math.min(z.target.scrollHeight,200)+"px"}function P(z){w(z);const N=n();p&&clearTimeout(p),N.length>=2&&!/\s/.test(N.slice(-1))?p=setTimeout(async()=>{var X;try{const H=await ed(N.trim());((X=H.results)==null?void 0:X.length)>0?(v(s,H.results.slice(0,6),!0),v(d,!0),v(u,-1)):v(d,!1)}catch{v(d,!1)}},300):v(d,!1)}function C(z){var N;n(`${z.corpName} `),v(d,!1),v(u,-1),(N=t.onCompanySelect)==null||N.call(t,z),r(x)&&r(x).focus()}function R(){setTimeout(()=>{v(d,!1)},200)}var b=Xf(),S=l(b),M=l(S);pa(M,z=>v(x,z),()=>r(x));var V=h(M,2);{var E=z=>{var N=Gf(),X=l(N);zf(X,{size:14}),oe("click",N,function(...H){var O;(O=t.onStop)==null||O.apply(this,H)}),c(z,N)},F=z=>{var N=Hf(),X=l(N);{let H=q(()=>o()?18:16);hf(X,{get size(){return r(H)},strokeWidth:2.5})}I((H,O)=>{je(N,1,H),N.disabled=O},[()=>Ut(Jt("send-btn",n().trim()&&"active")),()=>!n().trim()]),oe("click",N,()=>{var H;v(d,!1),(H=t.onSend)==null||H.call(t)}),c(z,N)};k(V,z=>{a()&&t.onStop?z(E):z(F,-1)})}var se=h(S,2);{var ne=z=>{var N=Yf();ke(N,21,()=>r(s),Se,(X,H,O)=>{var ce=Wf(),ve=l(ce);Oa(ve,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var Pe=h(ve,2),he=l(Pe),Ne=l(he),me=h(he,2),de=l(me),B=h(Pe,2);{var ue=le=>{var D=Kf(),m=l(D);I(()=>A(m,r(H).sector)),c(le,D)};k(B,le=>{r(H).sector&&le(ue)})}I(le=>{je(ce,1,le),A(Ne,r(H).corpName),A(de,`${r(H).stockCode??""} · ${(r(H).market||"")??""}`)},[()=>Ut(Jt("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",O===r(u)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),oe("mousedown",ce,()=>C(r(H))),fa("mouseenter",ce,()=>{v(u,O,!0)}),c(X,ce)}),c(z,N)};k(se,z=>{r(d)&&r(s).length>0&&z(ne)})}I(z=>{je(S,1,z),Dn(M,"placeholder",i())},[()=>Ut(Jt("input-box",o()&&"large"))]),oe("keydown",M,g),oe("input",M,P),fa("blur",M,R),za(M,n),c(e,b),yr()}Yr(["keydown","input","click","mousedown"]);var Jf=f('<button class="rounded-full border border-dl-border/60 bg-dl-bg-card/40 px-3 py-1.5 text-[12px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"> </button>'),Qf=f(`<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[580px] flex flex-col items-center"><div class="relative mb-8"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p> <div class="mb-6 max-w-[520px] rounded-2xl border border-dl-border/50 bg-dl-bg-card/50 px-4 py-3 text-left"><div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">Evidence First</div> <div class="mt-2 text-[13px] leading-relaxed text-dl-text-muted">DartLab은 재무 수치와 서술 텍스트를 함께 읽고, 표준화된 계정과 원문 근거를 같은 흐름에서 확인하도록 설계되어 있습니다.
				DART와 EDGAR를 포함한 40개 모듈 이상의 기능 범위를 먼저 물어본 뒤 바로 탐색을 시작할 수 있습니다.</div></div> <div class="w-full"><!></div> <div class="mt-5 flex w-full flex-wrap justify-center gap-2"></div></div></div>`);function Zf(e,t){wr(t,!0);let n=Be(t,"inputText",15,"");const a=["지금 dartlab에서 할 수 있는 기능을 먼저 정리해줘","EDGAR에서 추가로 받을 수 있는 데이터와 방법을 알려줘","OpenDart와 OpenEdgar로 가능한 일을 비교해줘","GPT 연결 시 현재 UI에서 가능한 코딩 작업 범위를 알려줘"];var o=Qf(),i=l(o),s=h(l(i),8),d=l(s);yd(d,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get onCompanySelect(){return t.onCompanySelect},get inputText(){return n()},set inputText(p){n(p)}});var u=h(s,2);ke(u,21,()=>a,Se,(p,x)=>{var g=Jf(),w=l(g);I(()=>A(w,r(x))),oe("click",g,()=>{var P;return(P=t.onSend)==null?void 0:P.call(t,r(x))}),c(p,g)}),c(e,o),yr()}Yr(["click"]);var ep=f("<span><!></span>");function yo(e,t){wr(t,!0);let n=Be(t,"variant",3,"default");const a={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var o=ep(),i=l(o);Rs(i,()=>t.children),I(s=>je(o,1,s),[()=>Ut(Jt("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",a[n()],t.class))]),c(e,o),yr()}function tp(e){const t=e.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(t)||t==="-"||t==="0"}function ha(e){if(!e)return"";let t=[],n=[],a=e.replace(/```(\w*)\n([\s\S]*?)```/g,(i,s,d)=>{const u=t.length;return t.push(d.trimEnd()),`
%%CODE_${u}%%
`});a=a.replace(/((?:^\|.+\|$\n?)+)/gm,i=>{const s=i.trim().split(`
`).filter(w=>w.trim());let d=null,u=-1,p=[];for(let w=0;w<s.length;w++)if(s[w].slice(1,-1).split("|").map(C=>C.trim()).every(C=>/^[\-:]+$/.test(C))){u=w;break}u>0?(d=s[u-1],p=s.slice(u+1)):(u===0||(d=s[0]),p=s.slice(1));let x="<table>";if(d){const w=d.slice(1,-1).split("|").map(P=>P.trim());x+="<thead><tr>"+w.map(P=>`<th>${P.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(p.length>0){x+="<tbody>";for(const w of p){const P=w.slice(1,-1).split("|").map(C=>C.trim());x+="<tr>"+P.map(C=>{let R=C.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${tp(C)?' class="num"':""}>${R}</td>`}).join("")+"</tr>"}x+="</tbody>"}x+="</table>";let g=n.length;return n.push(x),`
%%TABLE_${g}%%
`});let o=a.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");o=o.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,i=>"<ul>"+i.replace(/<br>/g,"")+"</ul>");for(let i=0;i<n.length;i++)o=o.replace(`%%TABLE_${i}%%`,n[i]);for(let i=0;i<t.length;i++){const s=t[i].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");o=o.replace(`%%CODE_${i}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${i}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${s}</code></pre></div>`)}return o=o.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(i,s)=>s.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+o+"</p>"}var rp=f('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),np=f('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),ap=f('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),op=f('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),sp=f('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!> <!> <!> <!></div></div>'),ip=f('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),lp=f('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),dp=f('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),cp=f('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),up=f("<button><!> </button>"),vp=f('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),fp=f('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),pp=f('<!> <span class="text-dl-text-dim"> </span>',1),mp=f('<div class="flex items-center gap-2 text-[11px]"><!></div>'),xp=f('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),hp=f('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),gp=f('<div class="message-committed"><!></div>'),bp=f('<div><div class="message-live-label"> </div> <pre> </pre></div>'),_p=f('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),wp=f('<span class="text-dl-accent/60"> </span>'),yp=f('<span class="text-dl-success/60"> </span>'),kp=f('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),Cp=f('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),Sp=f('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),$p=f('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),Mp=f('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),Tp=f("<!>  <div><!> <!></div> <!>",1),zp=f('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),Ep=f('<span class="text-[10px] text-dl-text-dim"> </span>'),Ap=f('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),Ip=f("<button> </button>"),Pp=f('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),Np=f("<button>시스템 프롬프트</button>"),Lp=f("<button>LLM 입력</button>"),Op=f('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),Rp=f('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),Dp=f('<span class="text-dl-text"> </span>'),jp=f('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),Vp=f('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),Fp=f('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),qp=f("<!> <!>",1);function Bp(e,t){wr(t,!0);let n=G(null),a=G("context"),o=G("raw"),i=q(()=>{var D,m,_,T,K,W;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((D=t.message.toolEvents)==null?void 0:D.length)>0){const L=[...t.message.toolEvents].reverse().find(Ee=>Ee.type==="call"),xe=((m=L==null?void 0:L.arguments)==null?void 0:m.module)||((_=L==null?void 0:L.arguments)==null?void 0:_.keyword)||"";return`도구 실행 중 — ${(L==null?void 0:L.name)||""}${xe?` (${xe})`:""}`}if(((T=t.message.contexts)==null?void 0:T.length)>0){const L=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(L==null?void 0:L.label)||(L==null?void 0:L.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(K=t.message.meta)!=null&&K.company?`${t.message.meta.company} 데이터 검색 중`:(W=t.message.meta)!=null&&W.includedModules?"분석 모듈 선택 완료":"생각 중"}),s=q(()=>{var D;return t.message.company||((D=t.message.meta)==null?void 0:D.company)||null});const d={capability:"기능 탐색",coding:"코딩 작업",company_explore:"회사 탐색",company_analysis:"회사 분석",follow_up:"후속 질문",general_chat:"일반 대화"};let u=q(()=>{var D;return(D=t.message.meta)!=null&&D.dialogueMode?d[t.message.meta.dialogueMode]||t.message.meta.dialogueMode:null}),p=q(()=>{var D,m,_;return t.message.systemPrompt||t.message.userContent||((D=t.message.contexts)==null?void 0:D.length)>0||((m=t.message.meta)==null?void 0:m.includedModules)||((_=t.message.toolEvents)==null?void 0:_.length)>0}),x=q(()=>{var m;const D=(m=t.message.meta)==null?void 0:m.dataYearRange;return D?typeof D=="string"?D:D.min_year&&D.max_year?`${D.min_year}~${D.max_year}년`:null:null});function g(D){if(!D)return 0;const m=(D.match(/[\uac00-\ud7af]/g)||[]).length,_=D.length-m;return Math.round(m*1.5+_/3.5)}function w(D){return D>=1e3?(D/1e3).toFixed(1)+"k":String(D)}let P=q(()=>{var m;let D=0;if(t.message.systemPrompt&&(D+=g(t.message.systemPrompt)),t.message.userContent)D+=g(t.message.userContent);else if(((m=t.message.contexts)==null?void 0:m.length)>0)for(const _ of t.message.contexts)D+=g(_.text);return D}),C=q(()=>g(t.message.text)),R=G(void 0);const b=/^\s*\|.+\|\s*$/;function S(D,m){if(!D)return{committed:"",draft:"",draftType:"none"};if(!m)return{committed:D,draft:"",draftType:"none"};const _=D.split(`
`);let T=_.length;D.endsWith(`
`)||(T=Math.min(T,_.length-1));let K=0,W=-1;for(let Ae=0;Ae<_.length;Ae++)_[Ae].trim().startsWith("```")&&(K+=1,W=Ae);K%2===1&&W>=0&&(T=Math.min(T,W));let L=-1;for(let Ae=_.length-1;Ae>=0;Ae--){const Tt=_[Ae];if(!Tt.trim())break;if(b.test(Tt))L=Ae;else{L=-1;break}}if(L>=0&&(T=Math.min(T,L)),T<=0)return{committed:"",draft:D,draftType:L===0?"table":K%2===1?"code":"text"};const xe=_.slice(0,T).join(`
`),Ee=_.slice(T).join(`
`);let at="text";return Ee&&L>=T?at="table":Ee&&K%2===1&&(at="code"),{committed:xe,draft:Ee,draftType:at}}const M='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',V='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function E(D){var K;const m=D.target.closest(".code-copy-btn");if(!m)return;const _=m.closest(".code-block-wrap"),T=((K=_==null?void 0:_.querySelector("code"))==null?void 0:K.textContent)||"";navigator.clipboard.writeText(T).then(()=>{m.innerHTML=V,setTimeout(()=>{m.innerHTML=M},2e3)})}function F(D){if(t.onOpenEvidence){t.onOpenEvidence("contexts",D);return}v(n,D,!0),v(a,"context"),v(o,"rendered")}function se(){if(t.onOpenEvidence){t.onOpenEvidence("system");return}v(n,0),v(a,"system"),v(o,"raw")}function ne(){if(t.onOpenEvidence){t.onOpenEvidence("snapshot");return}v(n,0),v(a,"snapshot")}function z(D){var m;if(t.onOpenEvidence){const _=(m=t.message.toolEvents)==null?void 0:m[D];t.onOpenEvidence((_==null?void 0:_.type)==="result"?"tool-results":"tool-calls",D);return}v(n,D,!0),v(a,"tool"),v(o,"raw")}function N(){if(t.onOpenEvidence){t.onOpenEvidence("input");return}v(n,0),v(a,"userContent"),v(o,"raw")}function X(){v(n,null)}function H(D){var m,_,T,K;return D?D.type==="call"?((m=D.arguments)==null?void 0:m.module)||((_=D.arguments)==null?void 0:_.keyword)||((T=D.arguments)==null?void 0:T.engine)||((K=D.arguments)==null?void 0:K.name)||"":typeof D.result=="string"?D.result.slice(0,120):D.result&&typeof D.result=="object"&&(D.result.module||D.result.status||D.result.name)||"":""}let O=q(()=>(t.message.toolEvents||[]).filter(D=>D.type==="call")),ce=q(()=>(t.message.toolEvents||[]).filter(D=>D.type==="result")),ve=q(()=>S(t.message.text||"",t.message.loading)),Pe=q(()=>{var m,_,T;const D=[];return((_=(m=t.message.meta)==null?void 0:m.includedModules)==null?void 0:_.length)>0&&D.push({label:`모듈 ${t.message.meta.includedModules.length}개`,icon:wo}),((T=t.message.contexts)==null?void 0:T.length)>0&&D.push({label:`컨텍스트 ${t.message.contexts.length}건`,icon:wf}),r(O).length>0&&D.push({label:`툴 호출 ${r(O).length}건`,icon:Ki}),r(ce).length>0&&D.push({label:`툴 결과 ${r(ce).length}건`,icon:Mo}),t.message.systemPrompt&&D.push({label:"시스템 프롬프트",icon:bs}),t.message.userContent&&D.push({label:"LLM 입력",icon:on}),D}),he=q(()=>{var m,_,T;if(!t.message.loading)return[];const D=[];return(m=t.message.meta)!=null&&m.company&&D.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&D.push({label:"핵심 수치 확인",done:!0}),(_=t.message.meta)!=null&&_.includedModules&&D.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((T=t.message.contexts)==null?void 0:T.length)>0&&D.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&D.push({label:"프롬프트 조립",done:!0}),t.message.text?D.push({label:"응답 작성 중",done:!1}):D.push({label:r(i)||"준비 중",done:!1}),D});var Ne=qp(),me=Q(Ne);{var de=D=>{var m=rp(),_=h(l(m),2),T=l(_),K=l(T);I(()=>A(K,t.message.text)),c(D,m)},B=D=>{var m=zp(),_=h(l(m),2),T=l(_);{var K=Ue=>{var fe=sp(),Ve=l(fe),Pt=l(Ve);mf(Pt,{size:11});var Ye=h(Ve,4),ot=l(Ye);{var mt=we=>{yo(we,{variant:"muted",children:(Oe,De)=>{var Ce=aa();I(()=>A(Ce,r(s))),c(Oe,Ce)},$$slots:{default:!0}})};k(ot,we=>{r(s)&&we(mt)})}var $=h(ot,2);{var Y=we=>{yo(we,{variant:"muted",children:(Oe,De)=>{var Ce=aa();I(He=>A(Ce,He),[()=>t.message.meta.market.toUpperCase()]),c(Oe,Ce)},$$slots:{default:!0}})};k($,we=>{var Oe;(Oe=t.message.meta)!=null&&Oe.market&&we(Y)})}var U=h($,2);{var re=we=>{yo(we,{variant:"accent",children:(Oe,De)=>{var Ce=aa();I(()=>A(Ce,r(u))),c(Oe,Ce)},$$slots:{default:!0}})};k(U,we=>{r(u)&&we(re)})}var Z=h(U,2);{var Fe=we=>{yo(we,{variant:"muted",children:(Oe,De)=>{var Ce=aa();I(()=>A(Ce,t.message.meta.topicLabel)),c(Oe,Ce)},$$slots:{default:!0}})};k(Z,we=>{var Oe;(Oe=t.message.meta)!=null&&Oe.topicLabel&&we(Fe)})}var qe=h(Z,2);{var Dt=we=>{yo(we,{variant:"accent",children:(Oe,De)=>{var Ce=aa();I(()=>A(Ce,r(x))),c(Oe,Ce)},$$slots:{default:!0}})};k(qe,we=>{r(x)&&we(Dt)})}var st=h(qe,2);{var Me=we=>{var Oe=be(),De=Q(Oe);ke(De,17,()=>t.message.contexts,Se,(Ce,He,Je)=>{var Ct=np(),ae=l(Ct);wo(ae,{size:10,class:"flex-shrink-0"});var Ie=h(ae);I(()=>A(Ie,` ${(r(He).label||r(He).module)??""}`)),oe("click",Ct,()=>F(Je)),c(Ce,Ct)}),c(we,Oe)},ge=we=>{var Oe=ap(),De=l(Oe);wo(De,{size:10,class:"flex-shrink-0"});var Ce=h(De);I(()=>A(Ce,` 모듈 ${t.message.meta.includedModules.length??""}개`)),c(we,Oe)};k(st,we=>{var Oe,De,Ce;((Oe=t.message.contexts)==null?void 0:Oe.length)>0?we(Me):((Ce=(De=t.message.meta)==null?void 0:De.includedModules)==null?void 0:Ce.length)>0&&we(ge,1)})}var dt=h(st,2);ke(dt,17,()=>r(Pe),Se,(we,Oe)=>{var De=op(),Ce=l(De);Kl(Ce,()=>r(Oe).icon,(Je,Ct)=>{Ct(Je,{size:10,class:"flex-shrink-0"})});var He=h(Ce);I(()=>A(He,` ${r(Oe).label??""}`)),oe("click",De,()=>{r(Oe).label.startsWith("컨텍스트")?F(0):r(Oe).label.startsWith("툴 호출")?t.onOpenEvidence?t.onOpenEvidence("tool-calls",0):z(0):r(Oe).label.startsWith("툴 결과")?t.onOpenEvidence?t.onOpenEvidence("tool-results",0):z((t.message.toolEvents||[]).findIndex(Je=>Je.type==="result")):r(Oe).label==="시스템 프롬프트"?se():r(Oe).label==="LLM 입력"&&N()}),c(we,De)}),c(Ue,fe)};k(T,Ue=>{var fe,Ve;(r(s)||r(x)||((fe=t.message.contexts)==null?void 0:fe.length)>0||(Ve=t.message.meta)!=null&&Ve.includedModules||r(Pe).length>0)&&Ue(K)})}var W=h(T,2);{var L=Ue=>{var fe=cp(),Ve=l(fe);ke(Ve,21,()=>t.message.snapshot.items,Se,(ot,mt)=>{const $=q(()=>r(mt).status==="good"?"text-dl-success":r(mt).status==="danger"?"text-dl-primary-light":r(mt).status==="caution"?"text-amber-400":"text-dl-text");var Y=ip(),U=l(Y),re=l(U),Z=h(U,2),Fe=l(Z);I(qe=>{A(re,r(mt).label),je(Z,1,qe),A(Fe,r(mt).value)},[()=>Ut(Jt("text-[14px] font-semibold leading-snug mt-0.5",r($)))]),c(ot,Y)});var Pt=h(Ve,2);{var Ye=ot=>{var mt=dp();ke(mt,21,()=>t.message.snapshot.warnings,Se,($,Y)=>{var U=lp(),re=l(U);Nf(re,{size:10});var Z=h(re);I(()=>A(Z,` ${r(Y)??""}`)),c($,U)}),c(ot,mt)};k(Pt,ot=>{var mt;((mt=t.message.snapshot.warnings)==null?void 0:mt.length)>0&&ot(Ye)})}oe("click",fe,ne),c(Ue,fe)};k(W,Ue=>{var fe,Ve;((Ve=(fe=t.message.snapshot)==null?void 0:fe.items)==null?void 0:Ve.length)>0&&Ue(L)})}var xe=h(W,2);{var Ee=Ue=>{var fe=vp(),Ve=l(fe),Pt=h(l(Ve),4);ke(Pt,21,()=>t.message.toolEvents,Se,(Ye,ot,mt)=>{const $=q(()=>H(r(ot)));var Y=up(),U=l(Y);{var re=qe=>{Ki(qe,{size:11})},Z=qe=>{Mo(qe,{size:11})};k(U,qe=>{r(ot).type==="call"?qe(re):qe(Z,-1)})}var Fe=h(U);I(qe=>{je(Y,1,qe),A(Fe,` ${(r(ot).type==="call"?r(ot).name:`${r(ot).name} 결과`)??""}${r($)?`: ${r($)}`:""}`)},[()=>Ut(Jt("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",r(ot).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),oe("click",Y,()=>z(mt)),c(Ye,Y)}),c(Ue,fe)};k(xe,Ue=>{var fe;((fe=t.message.toolEvents)==null?void 0:fe.length)>0&&Ue(Ee)})}var at=h(xe,2);{var Ae=Ue=>{var fe=xp(),Ve=l(fe);ke(Ve,21,()=>r(he),Se,(Pt,Ye)=>{var ot=mp(),mt=l(ot);{var $=U=>{var re=fp(),Z=h(Q(re),2),Fe=l(Z);I(()=>A(Fe,r(Ye).label)),c(U,re)},Y=U=>{var re=pp(),Z=Q(re);Hr(Z,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var Fe=h(Z,2),qe=l(Fe);I(()=>A(qe,r(Ye).label)),c(U,re)};k(mt,U=>{r(Ye).done?U($):U(Y,-1)})}c(Pt,ot)}),c(Ue,fe)},Tt=Ue=>{var fe=Tp(),Ve=Q(fe);{var Pt=Z=>{var Fe=hp(),qe=l(Fe);Hr(qe,{size:12,class:"animate-spin flex-shrink-0"});var Dt=h(qe,2),st=l(Dt);I(()=>A(st,r(i))),c(Z,Fe)};k(Ve,Z=>{t.message.loading&&Z(Pt)})}var Ye=h(Ve,2),ot=l(Ye);{var mt=Z=>{var Fe=gp(),qe=l(Fe);yn(qe,()=>ha(r(ve).committed)),c(Z,Fe)};k(ot,Z=>{r(ve).committed&&Z(mt)})}var $=h(ot,2);{var Y=Z=>{var Fe=bp(),qe=l(Fe),Dt=l(qe),st=h(qe,2),Me=l(st);I(ge=>{je(Fe,1,ge),A(Dt,r(ve).draftType==="table"?"표 구성 중":r(ve).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),A(Me,r(ve).draft)},[()=>Ut(Jt("message-live-tail",r(ve).draftType==="table"&&"message-draft-table",r(ve).draftType==="code"&&"message-draft-code"))]),c(Z,Fe)};k($,Z=>{r(ve).draft&&Z(Y)})}pa(Ye,Z=>v(R,Z),()=>r(R));var U=h(Ye,2);{var re=Z=>{var Fe=Mp(),qe=l(Fe);{var Dt=He=>{var Je=_p(),Ct=l(Je);gf(Ct,{size:10});var ae=h(Ct);I(()=>A(ae,` ${t.message.duration??""}초`)),c(He,Je)};k(qe,He=>{t.message.duration&&He(Dt)})}var st=h(qe,2);{var Me=He=>{var Je=kp(),Ct=l(Je);{var ae=ht=>{var Et=wp(),Qe=l(Et);I(At=>A(Qe,`↑${At??""}`),[()=>w(r(P))]),c(ht,Et)};k(Ct,ht=>{r(P)>0&&ht(ae)})}var Ie=h(Ct,2);{var _t=ht=>{var Et=yp(),Qe=l(Et);I(At=>A(Qe,`↓${At??""}`),[()=>w(r(C))]),c(ht,Et)};k(Ie,ht=>{r(C)>0&&ht(_t)})}c(He,Je)};k(st,He=>{(r(P)>0||r(C)>0)&&He(Me)})}var ge=h(st,2);{var dt=He=>{var Je=Cp(),Ct=l(Je);Mf(Ct,{size:10}),oe("click",Je,()=>{var ae;return(ae=t.onRegenerate)==null?void 0:ae.call(t)}),c(He,Je)};k(ge,He=>{t.onRegenerate&&He(dt)})}var we=h(ge,2);{var Oe=He=>{var Je=Sp(),Ct=l(Je);bs(Ct,{size:10}),oe("click",Je,se),c(He,Je)};k(we,He=>{t.message.systemPrompt&&He(Oe)})}var De=h(we,2);{var Ce=He=>{var Je=$p(),Ct=l(Je);on(Ct,{size:10});var ae=h(Ct);I((Ie,_t)=>A(ae,` LLM 입력 (${Ie??""}자 · ~${_t??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>w(g(t.message.userContent))]),oe("click",Je,N),c(He,Je)};k(De,He=>{t.message.userContent&&He(Ce)})}c(Z,Fe)};k(U,Z=>{!t.message.loading&&(t.message.duration||r(p)||t.onRegenerate)&&Z(re)})}I(Z=>je(Ye,1,Z),[()=>Ut(Jt("prose-dartlab message-body text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),oe("click",Ye,E),c(Ue,fe)};k(at,Ue=>{t.message.loading&&!t.message.text?Ue(Ae):Ue(Tt,-1)})}c(D,m)};k(me,D=>{t.message.role==="user"?D(de):D(B,-1)})}var ue=h(me,2);{var le=D=>{const m=q(()=>r(a)==="system"),_=q(()=>r(a)==="userContent"),T=q(()=>r(a)==="context"),K=q(()=>r(a)==="snapshot"),W=q(()=>r(a)==="tool"),L=q(()=>{var ae;return r(T)?(ae=t.message.contexts)==null?void 0:ae[r(n)]:null}),xe=q(()=>{var ae;return r(W)?(ae=t.message.toolEvents)==null?void 0:ae[r(n)]:null}),Ee=q(()=>{var ae,Ie,_t,ht,Et;return r(K)?"핵심 수치 (원본 데이터)":r(m)?"시스템 프롬프트":r(_)?"LLM에 전달된 입력":r(W)?((ae=r(xe))==null?void 0:ae.type)==="call"?`${(Ie=r(xe))==null?void 0:Ie.name} 호출`:`${(_t=r(xe))==null?void 0:_t.name} 결과`:((ht=r(L))==null?void 0:ht.label)||((Et=r(L))==null?void 0:Et.module)||""}),at=q(()=>{var ae;return r(K)?JSON.stringify(t.message.snapshot,null,2):r(m)?t.message.systemPrompt:r(_)?t.message.userContent:r(W)?JSON.stringify(r(xe),null,2):(ae=r(L))==null?void 0:ae.text});var Ae=Fp(),Tt=l(Ae),Ue=l(Tt),fe=l(Ue),Ve=l(fe),Pt=l(Ve);{var Ye=ae=>{wo(ae,{size:15,class:"text-dl-success flex-shrink-0"})},ot=ae=>{bs(ae,{size:15,class:"text-dl-primary-light flex-shrink-0"})},mt=ae=>{on(ae,{size:15,class:"text-dl-accent flex-shrink-0"})},$=ae=>{wo(ae,{size:15,class:"flex-shrink-0"})};k(Pt,ae=>{r(K)?ae(Ye):r(m)?ae(ot,1):r(_)?ae(mt,2):ae($,-1)})}var Y=h(Pt,2),U=l(Y),re=h(Y,2);{var Z=ae=>{var Ie=Ep(),_t=l(Ie);I(ht=>A(_t,`(${ht??""}자)`),[()=>{var ht,Et;return(Et=(ht=r(at))==null?void 0:ht.length)==null?void 0:Et.toLocaleString()}]),c(ae,Ie)};k(re,ae=>{r(m)&&ae(Z)})}var Fe=h(Ve,2),qe=l(Fe);{var Dt=ae=>{var Ie=Ap(),_t=l(Ie),ht=l(_t);on(ht,{size:11});var Et=h(_t,2),Qe=l(Et);bf(Qe,{size:11}),I((At,Ot)=>{je(_t,1,At),je(Et,1,Ot)},[()=>Ut(Jt("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",r(o)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>Ut(Jt("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",r(o)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),oe("click",_t,()=>v(o,"rendered")),oe("click",Et,()=>v(o,"raw")),c(ae,Ie)};k(qe,ae=>{r(T)&&ae(Dt)})}var st=h(qe,2),Me=l(st);io(Me,{size:18});var ge=h(fe,2);{var dt=ae=>{var Ie=Pp(),_t=l(Ie);ke(_t,21,()=>t.message.contexts,Se,(ht,Et,Qe)=>{var At=Ip(),Ot=l(At);I(Ht=>{je(At,1,Ht),A(Ot,t.message.contexts[Qe].label||t.message.contexts[Qe].module)},[()=>Ut(Jt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",Qe===r(n)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),oe("click",At,()=>{v(n,Qe,!0)}),c(ht,At)}),c(ae,Ie)};k(ge,ae=>{var Ie;r(T)&&((Ie=t.message.contexts)==null?void 0:Ie.length)>1&&ae(dt)})}var we=h(ge,2);{var Oe=ae=>{var Ie=Op(),_t=l(Ie),ht=l(_t);{var Et=Ot=>{var Ht=Np();I(fr=>je(Ht,1,fr),[()=>Ut(Jt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",r(m)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),oe("click",Ht,()=>{v(a,"system")}),c(Ot,Ht)};k(ht,Ot=>{t.message.systemPrompt&&Ot(Et)})}var Qe=h(ht,2);{var At=Ot=>{var Ht=Lp();I(fr=>je(Ht,1,fr),[()=>Ut(Jt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",r(_)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),oe("click",Ht,()=>{v(a,"userContent")}),c(Ot,Ht)};k(Qe,Ot=>{t.message.userContent&&Ot(At)})}c(ae,Ie)};k(we,ae=>{!r(T)&&!r(K)&&!r(W)&&ae(Oe)})}var De=h(Ue,2),Ce=l(De);{var He=ae=>{var Ie=Rp(),_t=l(Ie);yn(_t,()=>{var ht;return ha((ht=r(L))==null?void 0:ht.text)}),c(ae,Ie)},Je=ae=>{var Ie=jp(),_t=l(Ie),ht=h(l(_t),2),Et=l(ht),Qe=h(Et);{var At=Ft=>{var Pr=Dp(),jn=l(Pr);I(vt=>A(jn,vt),[()=>H(r(xe))]),c(Ft,Pr)},Ot=q(()=>H(r(xe)));k(Qe,Ft=>{r(Ot)&&Ft(At)})}var Ht=h(_t,2),fr=l(Ht);I(()=>{var Ft;A(Et,`${((Ft=r(xe))==null?void 0:Ft.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),A(fr,r(at))}),c(ae,Ie)},Ct=ae=>{var Ie=Vp(),_t=l(Ie);I(()=>A(_t,r(at))),c(ae,Ie)};k(Ce,ae=>{r(T)&&r(o)==="rendered"?ae(He):r(W)?ae(Je,1):ae(Ct,-1)})}I(()=>A(U,r(Ee))),oe("click",Ae,ae=>{ae.target===ae.currentTarget&&X()}),oe("keydown",Ae,ae=>{ae.key==="Escape"&&X()}),oe("click",st,X),c(D,Ae)};k(ue,D=>{r(n)!==null&&D(le)})}c(e,Ne),yr()}Yr(["click","keydown"]);var Up=f('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),Gp=f('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),Hp=f('<div class="flex justify-end gap-2 mb-1.5"><!></div>'),Kp=f('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8"><!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function Wp(e,t){wr(t,!0);function n(H){if(o())return!1;for(let O=a().length-1;O>=0;O--)if(a()[O].role==="assistant"&&!a()[O].error&&a()[O].text)return O===H;return!1}let a=Be(t,"messages",19,()=>[]),o=Be(t,"isLoading",3,!1),i=Be(t,"inputText",15,""),s=Be(t,"scrollTrigger",3,0);Be(t,"selectedCompany",3,null);function d(H){return(O,ce)=>{var Pe,he,Ne,me;(Pe=t.onOpenEvidence)==null||Pe.call(t,O,ce);let ve;if(O==="contexts")ve=(he=H.contexts)==null?void 0:he[ce];else if(O==="snapshot")ve={label:"핵심 수치",module:"snapshot",text:JSON.stringify(H.snapshot,null,2)};else if(O==="system")ve={label:"시스템 프롬프트",module:"system",text:H.systemPrompt};else if(O==="input")ve={label:"LLM 입력",module:"input",text:H.userContent};else if(O==="tool-calls"||O==="tool-results"){const de=(Ne=H.toolEvents)==null?void 0:Ne[ce];ve={label:`${(de==null?void 0:de.name)||"도구"} ${(de==null?void 0:de.type)==="call"?"호출":"결과"}`,module:"tool",text:JSON.stringify(de,null,2)}}ve&&((me=t.onOpenData)==null||me.call(t,ve))}}let u,p,x=G(!0),g=G(!1),w=G(!0);function P(){if(!u)return;const{scrollTop:H,scrollHeight:O,clientHeight:ce}=u;v(w,O-H-ce<96),r(w)?(v(x,!0),v(g,!1)):(v(x,!1),v(g,!0))}function C(H="smooth"){p&&(p.scrollIntoView({block:"end",behavior:H}),v(x,!0),v(g,!1))}Kr(()=>{s(),!(!u||!p)&&requestAnimationFrame(()=>{!u||!p||(r(x)||r(w)?(p.scrollIntoView({block:"end",behavior:o()?"auto":"smooth"}),v(g,!1)):v(g,!0))})});var R=Kp(),b=l(R),S=l(b),M=l(S);ke(M,17,a,Se,(H,O,ce)=>{{let ve=q(()=>n(ce)?t.onRegenerate:void 0),Pe=q(()=>t.onOpenData?d(r(O)):void 0);Bp(H,{get message(){return r(O)},get onRegenerate(){return r(ve)},get onOpenEvidence(){return r(Pe)}})}});var V=h(M,2);pa(V,H=>p=H,()=>p),pa(b,H=>u=H,()=>u);var E=h(b,2);{var F=H=>{var O=Up(),ce=l(O);oe("click",ce,()=>C("smooth")),c(H,O)};k(E,H=>{r(g)&&H(F)})}var se=h(E,2),ne=l(se),z=l(ne);{var N=H=>{var O=Hp(),ce=l(O);{var ve=Pe=>{var he=Gp(),Ne=l(he);To(Ne,{size:10}),oe("click",he,function(...me){var de;(de=t.onExport)==null||de.apply(this,me)}),c(Pe,he)};k(ce,Pe=>{a().length>1&&t.onExport&&Pe(ve)})}c(H,O)};k(z,H=>{o()||H(N)})}var X=h(z,2);yd(X,{get isLoading(){return o()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get onCompanySelect(){return t.onCompanySelect},get inputText(){return i()},set inputText(H){i(H)}}),fa("scroll",b,P),c(e,R),yr()}Yr(["click"]);var Yp=f('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!> <span class="text-[13px]">공시 데이터 로딩 중...</span></div>'),Xp=f('<div class="text-[11px] text-dl-text-dim"> </div>'),Jp=f('<button><!> <span class="truncate flex-1"> </span></button>'),Qp=f('<div class="py-0.5"></div>'),Zp=f('<div><button class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] opacity-30 font-normal"> </span></button> <!></div>'),em=f('<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50"><div class="px-3 py-2.5 border-b border-dl-border/20"><!></div> <!></nav>'),tm=f('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim"><!> <p class="text-[13px]">좌측에서 섹션을 선택하세요</p></div>'),rm=f('<div class="text-[10px] text-dl-text-dim/50 mb-0.5"> </div>'),nm=f('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!></div>'),am=f('<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>'),om=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),sm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),im=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),lm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),dm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),cm=f('<div class="vw-heading-node svelte-1l2nqwu"><!></div>'),um=f('<div class="vw-heading-block svelte-1l2nqwu"></div>'),vm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),fm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),pm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),mm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),xm=f('<button><span class="vw-timeline-label svelte-1l2nqwu"> </span></button>'),hm=f('<div class="vw-section-timeline svelte-1l2nqwu"></div>'),gm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),bm=f('<span class="vw-meta-pill svelte-1l2nqwu">비교 없음</span>'),_m=f('<div class="vw-section-actions svelte-1l2nqwu"><span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span></div>'),wm=f('<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span> </div>'),ym=f('<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),km=f('<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),Cm=f('<div class="text-[10px] text-dl-text-dim/35 mt-1"> </div>'),Sm=f('<div class="vw-digest svelte-1l2nqwu"><div class="flex items-center gap-2 mb-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span></div> <div class="space-y-1"><!> <!> <!> <!></div></div>'),$m=f('<p class="vw-para"> </p>'),Mm=f('<div class="vw-diff-added svelte-1l2nqwu"> </div>'),Tm=f('<div class="vw-diff-deleted svelte-1l2nqwu"> </div>'),zm=f('<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow svelte-1l2nqwu"></div>'),Em=f('<div class="disclosure-text vw-section-body vw-body-frame svelte-1l2nqwu"><!></div>'),Am=f('<div><!> <div class="vw-section-meta svelte-1l2nqwu"><span> </span> <!> <!> <!> <!></div> <!> <!> <!> <!></div>'),Im=f('<section class="vw-report-shell svelte-1l2nqwu"><div class="vw-report-header svelte-1l2nqwu"><div class="vw-report-badges svelte-1l2nqwu"><!> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <!> <!></div></div> <!></section>'),Pm=f('<div class="vw-data-divider svelte-1l2nqwu"><div class="vw-data-kicker svelte-1l2nqwu">Structured Data</div> <div class="vw-data-title svelte-1l2nqwu">표 / 정형 데이터</div></div>'),Nm=f('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),Lm=f("<th> </th>"),Om=f("<td> </td>"),Rm=f("<tr></tr>"),Dm=f('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),jm=f('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),Vm=f("<th> </th>"),Fm=f("<td> </td>"),qm=f("<tr></tr>"),Bm=f('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),Um=f("<button> </button>"),Gm=f('<span class="text-[9px] text-dl-text-dim/30"> </span>'),Hm=f('<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto"><!> <!></div>'),Km=f('<div class="vw-table-wrap bg-dl-bg-card/10 svelte-1l2nqwu"><!> <div class="px-4 py-3"><div class="markdown-table overflow-x-auto svelte-1l2nqwu"><!></div></div></div>'),Wm=f("<th> </th>"),Ym=f("<td> </td>"),Xm=f("<tr></tr>"),Jm=f('<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02] svelte-1l2nqwu"><div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10"><!> <span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span></div> <div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Qm=f('<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card"> </th>'),Zm=f('<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted"> </td>'),ex=f("<tr></tr>"),tx=f('<div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),rx=f('<article class="py-6 px-8"><!> <!> <!> <!></article>'),nx=f('<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center"><div class="flex-1 min-w-0"><!> <h3 class="text-[16px] font-semibold text-dl-text"> </h3></div> <button class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"><!></button></div> <!>',1),ax=f('<div class="flex flex-1 overflow-hidden min-h-0"><!> <main class="flex-1 overflow-y-auto min-w-0"><!></main></div>'),ox=f('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8"><!> <p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p></div>'),sx=f('<div class="flex flex-col h-full font-sans bg-dl-bg-dark"><!></div>');function ix(e,t){wr(t,!0);let n=Be(t,"stockCode",3,null),a=Be(t,"onTopicChange",3,null),o=G(null),i=G(!1),s=G(Gt(new Set)),d=G(null),u=G(null),p=G(Gt([])),x=G(null),g=G(!1),w=G(Gt([])),P=G(Gt(new Map)),C=new Map,R=G(!1),b=G(Gt(new Map));const S={companyOverview:"회사 개요",companyHistory:"회사 연혁",articlesOfIncorporation:"정관 사항",capitalChange:"자본금 변동",shareCapital:"주식 현황",dividend:"배당",productService:"사업 내용",rawMaterial:"원재료",businessOverview:"사업 개요",salesOrder:"매출/수주",riskDerivative:"위험관리/파생",majorContractsAndRnd:"주요 계약/R&D",otherReferences:"기타 참고사항",consolidatedStatements:"연결 재무제표",fsSummary:"재무제표 요약",consolidatedNotes:"연결 주석",financialStatements:"개별 재무제표",financialNotes:"개별 주석",fundraising:"자금조달",BS:"재무상태표",IS:"손익계산서",CIS:"포괄손익계산서",CF:"현금흐름표",SCE:"자본변동표",ratios:"재무비율",audit:"감사 의견",mdna:"경영진 분석(MD&A)",internalControl:"내부통제",auditContract:"감사 계약",nonAuditContract:"비감사 계약",boardOfDirectors:"이사회",shareholderMeeting:"주주총회",auditSystem:"감사 체계",outsideDirector:"사외이사",majorHolder:"주요 주주",majorHolderChange:"주주 변동",minorityHolder:"소수주주",stockTotal:"주식 총수",treasuryStock:"자기주식",employee:"직원 현황",executivePay:"임원 보수",executive:"임원 현황",executivePayAllTotal:"전체 보수 총액",executivePayIndividual:"개인별 보수",topPay:"5억이상 상위 보수",unregisteredExecutivePay:"미등기임원 보수",affiliateGroup:"계열회사",investedCompany:"투자회사",relatedPartyTx:"특수관계 거래",corporateBond:"사채 관리",privateOfferingUsage:"사모자금 사용",publicOfferingUsage:"공모자금 사용",shortTermBond:"단기사채",investorProtection:"투자자 보호",disclosureChanges:"공시변경 사항",contingentLiability:"우발채무",sanction:"제재/조치",subsequentEvents:"후발사건",expertConfirmation:"전문가 확인",subsidiaryDetail:"종속회사 상세",affiliateGroupDetail:"계열회사 상세",investmentInOtherDetail:"타법인 출자 상세",rndDetail:"R&D 상세"},M={I:"I. 회사의 개요",II:"II. 사업의 내용",III:"III. 재무에 관한 사항",IV:"IV. 감사인의 감사의견 등",V:"V. 이사의 경영진단 및 분석의견",VI:"VI. 이사회 등 회사의 기관에 관한 사항",VII:"VII. 주주에 관한 사항",VIII:"VIII. 임원 및 직원 등에 관한 사항",IX:"IX. 계열회사 등에 관한 사항",X:"X. 대주주 등과의 거래내용",XI:"XI. 그 밖에 투자자 보호를 위하여 필요한 사항",XII:"XII. 상세표"},V={I:1,II:2,III:3,IV:4,V:5,VI:6,VII:7,VIII:8,IX:9,X:10,XI:11,XII:12};function E($){return V[$]??99}function F($){return S[$]||$}function se($){return M[$]||$||"기타"}Kr(()=>{n()&&ne()});async function ne(){var $,Y;v(i,!0),v(o,null),v(d,null),v(u,null),v(p,[],!0),v(x,null),C=new Map;try{const U=await av(n());v(o,U.payload,!0),($=r(o))!=null&&$.columns&&v(w,r(o).columns.filter(Z=>/^\d{4}(Q[1-4])?$/.test(Z)),!0);const re=ve((Y=r(o))==null?void 0:Y.rows);re.length>0&&(v(s,new Set([re[0].chapter]),!0),re[0].topics.length>0&&z(re[0].topics[0].topic,re[0].chapter))}catch(U){console.error("viewer load error:",U)}v(i,!1)}async function z($,Y){var U;if(r(d)!==$){if(v(d,$,!0),v(u,Y||null,!0),v(P,new Map,!0),v(b,new Map,!0),(U=a())==null||U($,F($)),C.has($)){const re=C.get($);v(p,re.blocks||[],!0),v(x,re.textDocument||null,!0);return}v(p,[],!0),v(x,null),v(g,!0);try{const re=await nv(n(),$);v(p,re.blocks||[],!0),v(x,re.textDocument||null,!0),C.set($,{blocks:r(p),textDocument:r(x)})}catch(re){console.error("topic load error:",re),v(p,[],!0),v(x,null)}v(g,!1)}}function N($){const Y=new Set(r(s));Y.has($)?Y.delete($):Y.add($),v(s,Y,!0)}function X($,Y){const U=new Map(r(P));U.get($)===Y?U.delete($):U.set($,Y),v(P,U,!0)}function H($,Y){const U=new Map(r(b));U.set($,Y),v(b,U,!0)}function O($){return $==="updated"?"최근 수정":$==="new"?"신규":$==="stale"?"과거 유지":"유지"}function ce($){return $==="updated"?"updated":$==="new"?"new":$==="stale"?"stale":"stable"}function ve($){if(!$)return[];const Y=new Map,U=new Set;for(const re of $){const Z=re.chapter||"";Y.has(Z)||Y.set(Z,{chapter:Z,topics:[]}),U.has(re.topic)||(U.add(re.topic),Y.get(Z).topics.push({topic:re.topic,source:re.source||"docs"}))}return[...Y.values()].sort((re,Z)=>E(re.chapter)-E(Z.chapter))}function Pe($){return String($).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function he($){return String($||"").replaceAll(" "," ").replace(/\s+/g," ").trim()}function Ne($){return!$||$.length>88?!1:/^\[.+\]$/.test($)||/^【.+】$/.test($)||/^[IVX]+\.\s/.test($)||/^\d+\.\s/.test($)||/^[가-힣]\.\s/.test($)||/^\(\d+\)\s/.test($)||/^\([가-힣]\)\s/.test($)}function me($){return/^\(\d+\)\s/.test($)||/^\([가-힣]\)\s/.test($)?"h5":"h4"}function de($){return/^\[.+\]$/.test($)||/^【.+】$/.test($)?"vw-h-bracket":/^\(\d+\)\s/.test($)||/^\([가-힣]\)\s/.test($)?"vw-h-sub":"vw-h-section"}function B($){if(!$)return[];if(/^\|.+\|$/m.test($)||/^#{1,3} /m.test($)||/```/.test($))return[{kind:"markdown",text:$}];const Y=[];let U=[];const re=()=>{U.length!==0&&(Y.push({kind:"paragraph",text:U.join(" ")}),U=[])};for(const Z of String($).split(`
`)){const Fe=he(Z);if(!Fe){re();continue}if(Ne(Fe)){re(),Y.push({kind:"heading",text:Fe,tag:me(Fe),className:de(Fe)});continue}U.push(Fe)}return re(),Y}function ue($){return $?$.kind==="annual"?`${$.year}Q4`:$.year&&$.quarter?`${$.year}Q${$.quarter}`:$.label||"":""}function le($){var re;const Y=B($);if(Y.length===0)return"";if(((re=Y[0])==null?void 0:re.kind)==="markdown")return ha($);let U="";for(const Z of Y){if(Z.kind==="heading"){U+=`<${Z.tag} class="${Z.className}">${Pe(Z.text)}</${Z.tag}>`;continue}U+=`<p class="vw-para">${Pe(Z.text)}</p>`}return U}function D($){if(!$)return"";const Y=$.trim().split(`
`).filter(re=>re.trim());let U="";for(const re of Y){const Z=re.trim();/^[가-힣]\.\s/.test(Z)||/^\d+[-.]/.test(Z)?U+=`<h4 class="vw-h-section">${Z}</h4>`:/^\(\d+\)\s/.test(Z)||/^\([가-힣]\)\s/.test(Z)?U+=`<h5 class="vw-h-sub">${Z}</h5>`:/^\[.+\]$/.test(Z)||/^【.+】$/.test(Z)?U+=`<h4 class="vw-h-bracket">${Z}</h4>`:U+=`<h5 class="vw-h-sub">${Z}</h5>`}return U}function m($){var U;const Y=r(P).get($.id);return Y&&((U=$==null?void 0:$.views)!=null&&U[Y])?$.views[Y]:($==null?void 0:$.latest)||null}function _($,Y){var re,Z;const U=r(P).get($.id);return U?U===Y:((Z=(re=$==null?void 0:$.latest)==null?void 0:re.period)==null?void 0:Z.label)===Y}function T($){return r(P).has($.id)}function K($){return $==="updated"?"변경 있음":$==="new"?"직전 없음":"직전과 동일"}function W($){var Fe,qe,Dt;if(!$)return[];const Y=B($.body);if(Y.length===0||((Fe=Y[0])==null?void 0:Fe.kind)==="markdown"||!((qe=$.prevPeriod)!=null&&qe.label)||!((Dt=$.diff)!=null&&Dt.length))return Y;const U=[];for(const st of $.diff)for(const Me of st.paragraphs||[])U.push({kind:st.kind,text:he(Me)});const re=[];let Z=0;for(const st of Y){if(st.kind!=="paragraph"){re.push(st);continue}for(;Z<U.length&&U[Z].kind==="removed";)re.push({kind:"removed",text:U[Z].text}),Z+=1;Z<U.length&&["same","added"].includes(U[Z].kind)?(re.push({kind:U[Z].kind,text:U[Z].text||st.text}),Z+=1):re.push({kind:"same",text:st.text})}for(;Z<U.length;)re.push({kind:U[Z].kind,text:U[Z].text}),Z+=1;return re}function L($){return $==null?!1:/^-?[\d,.]+%?$/.test(String($).trim().replace(/,/g,""))}function xe($){return $==null?!1:/^-[\d.]+/.test(String($).trim().replace(/,/g,""))}function Ee($,Y){if($==null||$==="")return"";const U=typeof $=="number"?$:Number(String($).replace(/,/g,""));if(isNaN(U))return String($);if(Y<=1)return U.toLocaleString("ko-KR");const re=U/Y;return Number.isInteger(re)?re.toLocaleString("ko-KR"):re.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g,",")}function at($){if($==null||$==="")return"";const Y=String($).trim();if(Y.includes(","))return Y;const U=Y.match(/^(-?\d+)(\.\d+)?(%?)$/);return U?U[1].replace(/\B(?=(\d{3})+(?!\d))/g,",")+(U[2]||"")+(U[3]||""):Y}function Ae($){var Y,U;return(Y=r(o))!=null&&Y.rows&&((U=r(o).rows.find(re=>re.topic===$))==null?void 0:U.chapter)||null}function Tt($){const Y=$.match(/^(\d{4})(Q([1-4]))?$/);if(!Y)return"0000_0";const U=Y[1],re=Y[3]||"5";return`${U}_${re}`}function Ue($){return[...$].sort((Y,U)=>Tt(U).localeCompare(Tt(Y)))}let fe=q(()=>r(p).filter($=>$.kind!=="text"));var Ve=sx(),Pt=l(Ve);{var Ye=$=>{var Y=Yp(),U=l(Y);Hr(U,{size:18,class:"animate-spin"}),c($,Y)},ot=$=>{var Y=ax(),U=l(Y);{var re=st=>{var Me=em(),ge=l(Me),dt=l(ge);{var we=De=>{var Ce=Xp(),He=l(Ce);I(()=>A(He,`${r(w).length??""}개 기간 · ${r(w)[0]??""} ~ ${r(w)[r(w).length-1]??""}`)),c(De,Ce)};k(dt,De=>{r(w).length>0&&De(we)})}var Oe=h(ge,2);ke(Oe,17,()=>ve(r(o).rows),Se,(De,Ce)=>{var He=Zp(),Je=l(He),Ct=l(Je);{var ae=Ft=>{gd(Ft,{size:11,class:"flex-shrink-0 opacity-40"})},Ie=q(()=>r(s).has(r(Ce).chapter)),_t=Ft=>{bd(Ft,{size:11,class:"flex-shrink-0 opacity-40"})};k(Ct,Ft=>{r(Ie)?Ft(ae):Ft(_t,-1)})}var ht=h(Ct,2),Et=l(ht),Qe=h(ht,2),At=l(Qe),Ot=h(Je,2);{var Ht=Ft=>{var Pr=Qp();ke(Pr,21,()=>r(Ce).topics,Se,(jn,vt)=>{var $e=Jp(),Te=l($e);{var Nt=ft=>{hd(ft,{size:11,class:"flex-shrink-0 text-blue-400/40"})},Yt=ft=>{Fs(ft,{size:11,class:"flex-shrink-0 text-emerald-400/40"})},ar=ft=>{on(ft,{size:11,class:"flex-shrink-0 opacity-30"})};k(Te,ft=>{r(vt).source==="finance"?ft(Nt):r(vt).source==="report"?ft(Yt,1):ft(ar,-1)})}var kr=h(Te,2),pr=l(kr);I(ft=>{je($e,1,`group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											${r(d)===r(vt).topic?"bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]":"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent"}`),A(pr,ft)},[()=>F(r(vt).topic)]),oe("click",$e,()=>z(r(vt).topic,r(Ce).chapter)),c(jn,$e)}),c(Ft,Pr)},fr=q(()=>r(s).has(r(Ce).chapter));k(Ot,Ft=>{r(fr)&&Ft(Ht)})}I(Ft=>{A(Et,Ft),A(At,r(Ce).topics.length)},[()=>se(r(Ce).chapter)]),oe("click",Je,()=>N(r(Ce).chapter)),c(De,He)}),c(st,Me)};k(U,st=>{r(R)||st(re)})}var Z=h(U,2),Fe=l(Z);{var qe=st=>{var Me=tm(),ge=l(Me);on(ge,{size:32,strokeWidth:1,class:"opacity-20"}),c(st,Me)},Dt=st=>{var Me=nx(),ge=Q(Me),dt=l(ge),we=l(dt);{var Oe=Qe=>{var At=rm(),Ot=l(At);I(Ht=>A(Ot,Ht),[()=>se(r(u)||Ae(r(d)))]),c(Qe,At)},De=q(()=>r(u)||Ae(r(d)));k(we,Qe=>{r(De)&&Qe(Oe)})}var Ce=h(we,2),He=l(Ce),Je=h(dt,2),Ct=l(Je);{var ae=Qe=>{wd(Qe,{size:15})},Ie=Qe=>{_d(Qe,{size:15})};k(Ct,Qe=>{r(R)?Qe(ae):Qe(Ie,-1)})}var _t=h(ge,2);{var ht=Qe=>{var At=nm(),Ot=l(At);Hr(Ot,{size:16,class:"animate-spin"}),c(Qe,At)},Et=Qe=>{var At=rx(),Ot=l(At);{var Ht=$e=>{var Te=am();c($e,Te)};k(Ot,$e=>{var Te,Nt;r(p).length===0&&!(((Nt=(Te=r(x))==null?void 0:Te.sections)==null?void 0:Nt.length)>0)&&$e(Ht)})}var fr=h(Ot,2);{var Ft=$e=>{var Te=Im(),Nt=l(Te),Yt=l(Nt),ar=l(Yt);{var kr=St=>{var Ge=om(),pt=l(Ge);I(zt=>A(pt,`최신 기준 ${zt??""}`),[()=>ue(r(x).latestPeriod)]),c(St,Ge)};k(ar,St=>{r(x).latestPeriod&&St(kr)})}var pr=h(ar,2);{var ft=St=>{var Ge=sm(),pt=l(Ge);I((zt,Xt)=>A(pt,`커버리지 ${zt??""}~${Xt??""}`),[()=>ue(r(x).firstPeriod),()=>ue(r(x).latestPeriod)]),c(St,Ge)};k(pr,St=>{r(x).firstPeriod&&St(ft)})}var jt=h(pr,2),Ze=l(jt),et=h(jt,2);{var qt=St=>{var Ge=im(),pt=l(Ge);I(()=>A(pt,`최근 수정 ${r(x).updatedCount??""}개`)),c(St,Ge)};k(et,St=>{r(x).updatedCount>0&&St(qt)})}var or=h(et,2);{var Qt=St=>{var Ge=lm(),pt=l(Ge);I(()=>A(pt,`신규 ${r(x).newCount??""}개`)),c(St,Ge)};k(or,St=>{r(x).newCount>0&&St(Qt)})}var tr=h(or,2);{var dr=St=>{var Ge=dm(),pt=l(Ge);I(()=>A(pt,`과거 유지 ${r(x).staleCount??""}개`)),c(St,Ge)};k(tr,St=>{r(x).staleCount>0&&St(dr)})}var Or=h(Nt,2);ke(Or,17,()=>r(x).sections,Se,(St,Ge)=>{const pt=q(()=>m(r(Ge))),zt=q(()=>T(r(Ge)));var Xt=Am(),Cr=l(Xt);{var ct=pe=>{var ie=um();ke(ie,21,()=>r(Ge).headingPath,Se,(ze,wt)=>{var Zt=cm(),sr=l(Zt);yn(sr,()=>D(r(wt).text)),c(ze,Zt)}),c(pe,ie)};k(Cr,pe=>{var ie;((ie=r(Ge).headingPath)==null?void 0:ie.length)>0&&pe(ct)})}var $t=h(Cr,2),Rt=l($t),rr=l(Rt),Kt=h(Rt,2);{var Sr=pe=>{var ie=vm(),ze=l(ie);I(wt=>A(ze,`최신 ${wt??""}`),[()=>ue(r(Ge).latestPeriod)]),c(pe,ie)};k(Kt,pe=>{var ie;(ie=r(Ge).latestPeriod)!=null&&ie.label&&pe(Sr)})}var Jr=h(Kt,2);{var gr=pe=>{var ie=fm(),ze=l(ie);I(wt=>A(ze,`최초 ${wt??""}`),[()=>ue(r(Ge).firstPeriod)]),c(pe,ie)};k(Jr,pe=>{var ie,ze;(ie=r(Ge).firstPeriod)!=null&&ie.label&&r(Ge).firstPeriod.label!==((ze=r(Ge).latestPeriod)==null?void 0:ze.label)&&pe(gr)})}var Rr=h(Jr,2);{var Vn=pe=>{var ie=pm(),ze=l(ie);I(()=>A(ze,`${r(Ge).periodCount??""}기간`)),c(pe,ie)};k(Rr,pe=>{r(Ge).periodCount>0&&pe(Vn)})}var Wn=h(Rr,2);{var pn=pe=>{var ie=mm(),ze=l(ie);I(()=>A(ze,`최근 변경 ${r(Ge).latestChange??""}`)),c(pe,ie)};k(Wn,pe=>{r(Ge).latestChange&&pe(pn)})}var Yn=h($t,2);{var ss=pe=>{var ie=hm();ke(ie,21,()=>r(Ge).timeline,Se,(ze,wt)=>{var Zt=xm(),sr=l(Zt),nr=l(sr);I((ur,ir)=>{je(Zt,1,`vw-timeline-chip ${ur??""}`,"svelte-1l2nqwu"),A(nr,ir)},[()=>_(r(Ge),r(wt).period.label)?"is-active":"",()=>ue(r(wt).period)]),oe("click",Zt,()=>X(r(Ge).id,r(wt).period.label)),c(ze,Zt)}),c(pe,ie)};k(Yn,pe=>{var ie;((ie=r(Ge).timeline)==null?void 0:ie.length)>0&&pe(ss)})}var y=h(Yn,2);{var ee=pe=>{var ie=_m(),ze=l(ie),wt=l(ze),Zt=h(ze,2);{var sr=J=>{var te=gm(),We=l(te);I(Re=>A(We,`비교 ${Re??""}`),[()=>ue(r(pt).prevPeriod)]),c(J,te)},nr=J=>{var te=bm();c(J,te)};k(Zt,J=>{var te;(te=r(pt).prevPeriod)!=null&&te.label?J(sr):J(nr,-1)})}var ur=h(Zt,2),ir=l(ur);I((J,te)=>{A(wt,`선택 ${J??""}`),A(ir,te)},[()=>ue(r(pt).period),()=>K(r(pt).status)]),c(pe,ie)};k(y,pe=>{r(zt)&&r(pt)&&pe(ee)})}var Le=h(y,2);{var Xe=pe=>{const ie=q(()=>r(pt).digest);var ze=Sm(),wt=l(ze),Zt=l(wt),sr=l(Zt),nr=h(wt,2),ur=l(nr);ke(ur,17,()=>r(ie).items.filter(Re=>Re.kind==="numeric"),Se,(Re,tt)=>{var Bt=wm(),It=h(l(Bt));I(()=>A(It,` ${r(tt).text??""}`)),c(Re,Bt)});var ir=h(ur,2);ke(ir,17,()=>r(ie).items.filter(Re=>Re.kind==="added"),Se,(Re,tt)=>{var Bt=ym(),It=h(l(Bt),2),Vt=l(It);I(()=>A(Vt,r(tt).text)),c(Re,Bt)});var J=h(ir,2);ke(J,17,()=>r(ie).items.filter(Re=>Re.kind==="removed"),Se,(Re,tt)=>{var Bt=km(),It=h(l(Bt),2),Vt=l(It);I(()=>A(Vt,r(tt).text)),c(Re,Bt)});var te=h(J,2);{var We=Re=>{var tt=Cm(),Bt=l(tt);I(()=>A(Bt,`외 ${r(ie).wordingCount??""}건 문구 수정`)),c(Re,tt)};k(te,Re=>{r(ie).wordingCount>0&&Re(We)})}I(()=>A(sr,`${r(ie).to??""} vs ${r(ie).from??""}`)),c(pe,ze)};k(Le,pe=>{var ie,ze,wt;r(zt)&&((wt=(ze=(ie=r(pt))==null?void 0:ie.digest)==null?void 0:ze.items)==null?void 0:wt.length)>0&&pe(Xe)})}var Ke=h(Le,2);{var ut=pe=>{var ie=be(),ze=Q(ie);{var wt=sr=>{var nr=zm();ke(nr,21,()=>W(r(pt)),Se,(ur,ir)=>{var J=be(),te=Q(J);{var We=It=>{var Vt=be(),Nr=Q(Vt);yn(Nr,()=>D(r(ir).text)),c(It,Vt)},Re=It=>{var Vt=$m(),Nr=l(Vt);I(()=>A(Nr,r(ir).text)),c(It,Vt)},tt=It=>{var Vt=Mm(),Nr=l(Vt);I(()=>A(Nr,r(ir).text)),c(It,Vt)},Bt=It=>{var Vt=Tm(),Nr=l(Vt);I(()=>A(Nr,r(ir).text)),c(It,Vt)};k(te,It=>{r(ir).kind==="heading"?It(We):r(ir).kind==="same"?It(Re,1):r(ir).kind==="added"?It(tt,2):r(ir).kind==="removed"&&It(Bt,3)})}c(ur,J)}),c(sr,nr)},Zt=sr=>{var nr=Em(),ur=l(nr);yn(ur,()=>le(r(pt).body)),c(sr,nr)};k(ze,sr=>{var nr,ur;r(zt)&&((nr=r(pt).prevPeriod)!=null&&nr.label)&&((ur=r(pt).diff)==null?void 0:ur.length)>0?sr(wt):sr(Zt,-1)})}c(pe,ie)};k(Ke,pe=>{r(pt)&&pe(ut)})}I((pe,ie)=>{je(Xt,1,`vw-text-section ${r(Ge).status==="stale"?"vw-text-section-stale":""}`,"svelte-1l2nqwu"),je(Rt,1,`vw-status-pill ${pe??""}`,"svelte-1l2nqwu"),A(rr,ie)},[()=>ce(r(Ge).status),()=>O(r(Ge).status)]),c(St,Xt)}),I(()=>A(Ze,`본문 ${r(x).sectionCount??""}개`)),c($e,Te)};k(fr,$e=>{var Te,Nt;((Nt=(Te=r(x))==null?void 0:Te.sections)==null?void 0:Nt.length)>0&&$e(Ft)})}var Pr=h(fr,2);{var jn=$e=>{var Te=Pm();c($e,Te)};k(Pr,$e=>{r(fe).length>0&&$e(jn)})}var vt=h(Pr,2);ke(vt,17,()=>r(fe),Se,($e,Te)=>{var Nt=be(),Yt=Q(Nt);{var ar=Ze=>{const et=q(()=>{var ct;return((ct=r(Te).data)==null?void 0:ct.columns)||[]}),qt=q(()=>{var ct;return((ct=r(Te).data)==null?void 0:ct.rows)||[]}),or=q(()=>r(Te).meta||{}),Qt=q(()=>r(or).scaleDivisor||1);var tr=Dm(),dr=Q(tr);{var Or=ct=>{var $t=Nm(),Rt=l($t);I(()=>A(Rt,`(단위: ${r(or).scale??""})`)),c(ct,$t)};k(dr,ct=>{r(or).scale&&ct(Or)})}var St=h(dr,2),Ge=l(St),pt=l(Ge),zt=l(pt),Xt=l(zt);ke(Xt,21,()=>r(et),Se,(ct,$t,Rt)=>{const rr=q(()=>/^\d{4}/.test(r($t)));var Kt=Lm(),Sr=l(Kt);I(()=>{je(Kt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${r(rr)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${Rt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),A(Sr,r($t))}),c(ct,Kt)});var Cr=h(zt);ke(Cr,21,()=>r(qt),Se,(ct,$t,Rt)=>{var rr=Rm();je(rr,1,`hover:bg-white/[0.03] ${Rt%2===1?"bg-white/[0.012]":""}`),ke(rr,21,()=>r(et),Se,(Kt,Sr,Jr)=>{const gr=q(()=>r($t)[r(Sr)]??""),Rr=q(()=>L(r(gr))),Vn=q(()=>xe(r(gr))),Wn=q(()=>r(Rr)?Ee(r(gr),r(Qt)):r(gr));var pn=Om(),Yn=l(pn);I(()=>{je(pn,1,`px-3 py-1.5 border-b border-white/[0.025]
																	${r(Rr)?"text-right tabular-nums font-mono text-[11.5px]":"whitespace-nowrap"}
																	${r(Vn)?"text-red-400/60":r(Rr)?"text-dl-text/90":""}
																	${Jr===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]":"text-dl-text-muted"}
																	${Jr===0&&Rt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),A(Yn,r(Wn))}),c(Kt,pn)}),c(ct,rr)}),c(Ze,tr)},kr=Ze=>{const et=q(()=>{var ct;return((ct=r(Te).data)==null?void 0:ct.columns)||[]}),qt=q(()=>{var ct;return((ct=r(Te).data)==null?void 0:ct.rows)||[]}),or=q(()=>r(Te).meta||{}),Qt=q(()=>r(or).scaleDivisor||1);var tr=Bm(),dr=Q(tr);{var Or=ct=>{var $t=jm(),Rt=l($t);I(()=>A(Rt,`(단위: ${r(or).scale??""})`)),c(ct,$t)};k(dr,ct=>{r(or).scale&&ct(Or)})}var St=h(dr,2),Ge=l(St),pt=l(Ge),zt=l(pt),Xt=l(zt);ke(Xt,21,()=>r(et),Se,(ct,$t,Rt)=>{const rr=q(()=>/^\d{4}/.test(r($t)));var Kt=Vm(),Sr=l(Kt);I(()=>{je(Kt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${r(rr)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${Rt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),A(Sr,r($t))}),c(ct,Kt)});var Cr=h(zt);ke(Cr,21,()=>r(qt),Se,(ct,$t,Rt)=>{var rr=qm();je(rr,1,`hover:bg-white/[0.03] ${Rt%2===1?"bg-white/[0.012]":""}`),ke(rr,21,()=>r(et),Se,(Kt,Sr,Jr)=>{const gr=q(()=>r($t)[r(Sr)]??""),Rr=q(()=>L(r(gr))),Vn=q(()=>xe(r(gr))),Wn=q(()=>r(Rr)?r(Qt)>1?Ee(r(gr),r(Qt)):at(r(gr)):r(gr));var pn=Fm(),Yn=l(pn);I(()=>{je(pn,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${r(Rr)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${r(Vn)?"text-red-400/60":r(Rr)?"text-dl-text/90":""}
																	${Jr===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Jr===0&&Rt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),A(Yn,r(Wn))}),c(Kt,pn)}),c(ct,rr)}),c(Ze,tr)},pr=Ze=>{const et=q(()=>Ue(Object.keys(r(Te).rawMarkdown))),qt=q(()=>r(b).get(r(Te).block)??0),or=q(()=>r(et)[r(qt)]||r(et)[0]);var Qt=Km(),tr=l(Qt);{var dr=pt=>{var zt=Hm(),Xt=l(zt);ke(Xt,17,()=>r(et).slice(0,8),Se,($t,Rt,rr)=>{var Kt=Um(),Sr=l(Kt);I(()=>{je(Kt,1,`px-2 py-0.5 rounded text-[10px] transition-colors
															${rr===r(qt)?"bg-white/[0.08] text-dl-text font-medium":"text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]"}`),A(Sr,r(Rt))}),oe("click",Kt,()=>H(r(Te).block,rr)),c($t,Kt)});var Cr=h(Xt,2);{var ct=$t=>{var Rt=Gm(),rr=l(Rt);I(()=>A(rr,`외 ${r(et).length-8}개`)),c($t,Rt)};k(Cr,$t=>{r(et).length>8&&$t(ct)})}c(pt,zt)};k(tr,pt=>{r(et).length>1&&pt(dr)})}var Or=h(tr,2),St=l(Or),Ge=l(St);yn(Ge,()=>ha(r(Te).rawMarkdown[r(or)])),c(Ze,Qt)},ft=Ze=>{const et=q(()=>{var zt;return((zt=r(Te).data)==null?void 0:zt.columns)||[]}),qt=q(()=>{var zt;return((zt=r(Te).data)==null?void 0:zt.rows)||[]});var or=Jm(),Qt=l(or),tr=l(Qt);Fs(tr,{size:12,class:"text-emerald-400/50"});var dr=h(Qt,2),Or=l(dr),St=l(Or),Ge=l(St);ke(Ge,21,()=>r(et),Se,(zt,Xt,Cr)=>{const ct=q(()=>/^\d{4}/.test(r(Xt)));var $t=Wm(),Rt=l($t);I(()=>{je($t,1,`px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															${r(ct)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
															${Cr===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),A(Rt,r(Xt))}),c(zt,$t)});var pt=h(St);ke(pt,21,()=>r(qt),Se,(zt,Xt,Cr)=>{var ct=Xm();je(ct,1,`hover:bg-white/[0.03] ${Cr%2===1?"bg-white/[0.012]":""}`),ke(ct,21,()=>r(et),Se,($t,Rt,rr)=>{const Kt=q(()=>r(Xt)[r(Rt)]??""),Sr=q(()=>L(r(Kt))),Jr=q(()=>xe(r(Kt)));var gr=Ym(),Rr=l(gr);I(Vn=>{je(gr,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${r(Sr)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${r(Jr)?"text-red-400/60":r(Sr)?"text-dl-text/90":""}
																	${rr===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${rr===0&&Cr%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),A(Rr,Vn)},[()=>r(Sr)?at(r(Kt)):r(Kt)]),c($t,gr)}),c(zt,ct)}),c(Ze,or)},jt=Ze=>{const et=q(()=>r(Te).data.columns),qt=q(()=>r(Te).data.rows||[]);var or=tx(),Qt=l(or),tr=l(Qt),dr=l(tr),Or=l(dr);ke(Or,21,()=>r(et),Se,(Ge,pt)=>{var zt=Qm(),Xt=l(zt);I(()=>A(Xt,r(pt))),c(Ge,zt)});var St=h(dr);ke(St,21,()=>r(qt),Se,(Ge,pt,zt)=>{var Xt=ex();je(Xt,1,`hover:bg-white/[0.03] ${zt%2===1?"bg-white/[0.012]":""}`),ke(Xt,21,()=>r(et),Se,(Cr,ct)=>{var $t=Zm(),Rt=l($t);I(()=>A(Rt,r(pt)[r(ct)]??"")),c(Cr,$t)}),c(Ge,Xt)}),c(Ze,or)};k(Yt,Ze=>{var et,qt;r(Te).kind==="finance"?Ze(ar):r(Te).kind==="structured"?Ze(kr,1):r(Te).kind==="raw_markdown"&&r(Te).rawMarkdown?Ze(pr,2):r(Te).kind==="report"?Ze(ft,3):((qt=(et=r(Te).data)==null?void 0:et.columns)==null?void 0:qt.length)>0&&Ze(jt,4)})}c($e,Nt)}),c(Qe,At)};k(_t,Qe=>{r(g)?Qe(ht):Qe(Et,-1)})}I(Qe=>{A(He,Qe),Dn(Je,"title",r(R)?"목차 표시":"전체화면")},[()=>F(r(d))]),oe("click",Je,()=>v(R,!r(R))),c(st,Me)};k(Fe,st=>{r(d)?st(Dt,-1):st(qe)})}c($,Y)},mt=$=>{var Y=ox(),U=l(Y);on(U,{size:36,strokeWidth:1,class:"opacity-20"}),c($,Y)};k(Pt,$=>{var Y;r(i)?$(Ye):(Y=r(o))!=null&&Y.rows?$(ot,1):$(mt,-1)})}c(e,Ve),yr()}Yr(["click"]);var lx=f('<span class="text-[12px] font-semibold text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim"> </span>',1),dx=f('<span class="text-[12px] font-semibold text-dl-text"> </span>'),cx=f('<span class="text-[12px] font-semibold text-dl-text">데이터</span>'),ux=f('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" title="Excel 다운로드"><!></button> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button>',1),vx=f('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),fx=f('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed"> </pre>'),px=f('<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2"> </div>'),mx=f('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),xx=f('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),hx=f("<!> <!>",1),gx=f('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),bx=f('<div class="p-4"><!></div>'),_x=f('<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">표시할 내용이 없습니다</div>'),wx=f('<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark"><div class="flex items-center justify-between h-10 mt-8 px-4 border-b border-dl-border/40 flex-shrink-0"><div class="flex items-center gap-2 min-w-0"><!></div> <div class="flex items-center gap-1"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 overflow-auto min-h-0"><!></div></div>');function yx(e,t){wr(t,!0);let n=Be(t,"mode",3,null),a=Be(t,"company",3,null),o=Be(t,"data",3,null),i=Be(t,"onTopicChange",3,null),s=Be(t,"onFullscreen",3,null),d=Be(t,"isFullscreen",3,!1),u=G(!1);async function p(){var O;if(!(!((O=a())!=null&&O.stockCode)||r(u))){v(u,!0);try{await rv(a().stockCode)}catch(ce){console.error("Excel download error:",ce)}v(u,!1)}}function x(O){return O?/^\|.+\|$/m.test(O)||/^#{1,3} /m.test(O)||/\*\*[^*]+\*\*/m.test(O)||/```/.test(O):!1}var g=wx(),w=l(g),P=l(w),C=l(P);{var R=O=>{var ce=lx(),ve=Q(ce),Pe=l(ve),he=h(ve,2),Ne=l(he);I(()=>{A(Pe,a().corpName||a().company),A(Ne,a().stockCode)}),c(O,ce)},b=O=>{var ce=dx(),ve=l(ce);I(()=>A(ve,o().label)),c(O,ce)},S=O=>{var ce=cx();c(O,ce)};k(C,O=>{var ce;n()==="viewer"&&a()?O(R):n()==="data"&&((ce=o())!=null&&ce.label)?O(b,1):n()==="data"&&O(S,2)})}var M=h(P,2),V=l(M);{var E=O=>{var ce=ux(),ve=Q(ce),Pe=l(ve);{var he=le=>{Hr(le,{size:14,class:"animate-spin"})},Ne=le=>{To(le,{size:14})};k(Pe,le=>{r(u)?le(he):le(Ne,-1)})}var me=h(ve,2),de=l(me);{var B=le=>{wd(le,{size:14})},ue=le=>{_d(le,{size:14})};k(de,le=>{d()?le(B):le(ue,-1)})}I(()=>{ve.disabled=r(u),Dn(me,"title",d()?"패널 모드로":"전체 화면")}),oe("click",ve,p),oe("click",me,()=>{var le;return(le=s())==null?void 0:le()}),c(O,ce)};k(V,O=>{var ce;n()==="viewer"&&((ce=a())!=null&&ce.stockCode)&&O(E)})}var F=h(V,2),se=l(F);io(se,{size:15});var ne=h(w,2),z=l(ne);{var N=O=>{ix(O,{get stockCode(){return a().stockCode},get onTopicChange(){return i()}})},X=O=>{var ce=bx(),ve=l(ce);{var Pe=me=>{var de=be(),B=Q(de);{var ue=m=>{var _=vx(),T=l(_);yn(T,()=>ha(o())),c(m,_)},le=q(()=>x(o())),D=m=>{var _=fx(),T=l(_);I(()=>A(T,o())),c(m,_)};k(B,m=>{r(le)?m(ue):m(D,-1)})}c(me,de)},he=me=>{var de=hx(),B=Q(de);{var ue=T=>{var K=px(),W=l(K);I(()=>A(W,o().module)),c(T,K)};k(B,T=>{o().module&&T(ue)})}var le=h(B,2);{var D=T=>{var K=mx(),W=l(K);yn(W,()=>ha(o().text)),c(T,K)},m=q(()=>x(o().text)),_=T=>{var K=xx(),W=l(K);I(()=>A(W,o().text)),c(T,K)};k(le,T=>{r(m)?T(D):T(_,-1)})}c(me,de)},Ne=me=>{var de=gx(),B=l(de);I(ue=>A(B,ue),[()=>JSON.stringify(o(),null,2)]),c(me,de)};k(ve,me=>{var de;typeof o()=="string"?me(Pe):(de=o())!=null&&de.text?me(he,1):me(Ne,-1)})}c(O,ce)},H=O=>{var ce=_x();c(O,ce)};k(z,O=>{n()==="viewer"&&a()?O(N):n()==="data"&&o()?O(X,1):O(H,-1)})}oe("click",F,()=>{var O;return(O=t.onClose)==null?void 0:O.call(t)}),c(e,g),yr()}Yr(["click"]);var kx=f('<div class="flex flex-col items-center justify-center py-8 gap-2"><!> <span class="text-[11px] text-dl-text-dim">목차 로딩 중...</span></div>'),Cx=f('<span class="w-1.5 h-1.5 rounded-full bg-emerald-400/70" title="최근 변경"></span>'),Sx=f('<span class="text-[9px] text-dl-text-dim/60 font-mono"> </span>'),$x=f('<button><!> <span class="truncate"> </span> <span class="ml-auto flex items-center gap-0.5"><!> <!> <!></span></button>'),Mx=f('<div class="ml-2 border-l border-dl-border/20 pl-1"></div>'),Tx=f('<div class="mb-0.5"><button class="flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-left text-[11px] font-semibold uppercase tracking-wider text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] text-dl-text-dim/60 font-mono"> </span></button> <!></div>'),zx=f('<div class="px-3 py-6 text-center text-[12px] text-dl-text-dim">종목을 선택하면 목차가 표시됩니다</div>'),Ex=f('<nav class="flex flex-col h-full min-h-0 overflow-y-auto py-2 px-1"><!></nav>');function Ax(e,t){wr(t,!0);let n=Be(t,"toc",3,null),a=Be(t,"loading",3,!1),o=Be(t,"selectedTopic",3,null),i=Be(t,"expandedChapters",19,()=>new Set),s=Be(t,"onSelectTopic",3,null),d=Be(t,"onToggleChapter",3,null);const u=new Set(["BS","IS","CIS","CF","SCE","ratios"]);function p(b){return u.has(b)?hd:on}function x(b){return b.tableCount>0&&b.textCount>0?"both":b.tableCount>0?"table":b.textCount>0?"text":"empty"}Kr(()=>{o()&&Fl().then(()=>{const b=document.querySelector(".viewer-nav-active-item");b&&b.scrollIntoView({block:"nearest",behavior:"smooth"})})});var g=Ex(),w=l(g);{var P=b=>{var S=kx(),M=l(S);Hr(M,{size:18,class:"animate-spin text-dl-text-dim"}),c(b,S)},C=b=>{var S=be(),M=Q(S);ke(M,17,()=>n().chapters,Se,(V,E)=>{var F=Tx(),se=l(F),ne=l(se);{var z=me=>{gd(me,{size:12})},N=q(()=>i().has(r(E).chapter)),X=me=>{bd(me,{size:12})};k(ne,me=>{r(N)?me(z):me(X,-1)})}var H=h(ne,2),O=l(H),ce=h(H,2),ve=l(ce),Pe=h(se,2);{var he=me=>{var de=Mx();ke(de,21,()=>r(E).topics,Se,(B,ue)=>{const le=q(()=>p(r(ue).topic)),D=q(()=>x(r(ue))),m=q(()=>o()===r(ue).topic);var _=$x(),T=l(_);Kl(T,()=>r(le),(fe,Ve)=>{Ve(fe,{size:12,class:"flex-shrink-0 opacity-50"})});var K=h(T,2),W=l(K),L=h(K,2),xe=l(L);{var Ee=fe=>{var Ve=Cx();c(fe,Ve)};k(xe,fe=>{r(ue).hasChanges&&fe(Ee)})}var at=h(xe,2);{var Ae=fe=>{Ef(fe,{size:9,class:"text-dl-text-dim/40"})};k(at,fe=>{(r(D)==="table"||r(D)==="both")&&fe(Ae)})}var Tt=h(at,2);{var Ue=fe=>{var Ve=Sx(),Pt=l(Ve);I(()=>A(Pt,r(ue).tableCount)),c(fe,Ve)};k(Tt,fe=>{r(ue).tableCount>0&&fe(Ue)})}I(()=>{je(_,1,`${r(m)?"viewer-nav-active-item":""} viewer-nav-active flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors ${r(m)?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-muted hover:text-dl-text hover:bg-white/5"}`),A(W,r(ue).label)}),oe("click",_,()=>{var fe;return(fe=s())==null?void 0:fe(r(ue).topic,r(E).chapter)}),c(B,_)}),c(me,de)},Ne=q(()=>i().has(r(E).chapter));k(Pe,me=>{r(Ne)&&me(he)})}I(()=>{A(O,r(E).chapter),A(ve,r(E).topics.length)}),oe("click",se,()=>{var me;return(me=d())==null?void 0:me(r(E).chapter)}),c(V,F)}),c(b,S)},R=b=>{var S=zx();c(b,S)};k(w,b=>{var S;a()?b(P):(S=n())!=null&&S.chapters?b(C,1):b(R,-1)})}c(e,g),yr()}Yr(["click"]);var Ix=f("<button> </button>"),Px=f('<div class="flex items-center gap-0.5 overflow-x-auto py-1 scrollbar-thin"></div>');function kd(e,t){wr(t,!0);let n=Be(t,"periods",19,()=>[]),a=Be(t,"selected",3,null),o=Be(t,"onSelect",3,null);function i(x){return/^\d{4}$/.test(x)||/^\d{4}Q4$/.test(x)}function s(x){const g=x.match(/^(\d{4})(Q([1-4]))?$/);if(!g)return x;const w="'"+g[1].slice(2);return g[3]?`${w}.${g[3]}Q`:w}var d=be(),u=Q(d);{var p=x=>{var g=Px();ke(g,21,n,Se,(w,P)=>{var C=Ix(),R=l(C);I((b,S)=>{je(C,1,`flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] font-mono transition-colors
					${b??""}`),Dn(C,"title",r(P)),A(R,S)},[()=>a()===r(P)?"bg-dl-primary/20 text-dl-primary-light font-medium":i(r(P))?"text-dl-text-muted hover:text-dl-text hover:bg-white/5":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5",()=>s(r(P))]),oe("click",C,()=>{var b;return(b=o())==null?void 0:b(r(P))}),c(w,C)}),c(x,g)};k(u,x=>{n().length>0&&x(p)})}c(e,d),yr()}Yr(["click"]);var Nx=f('<div class="mb-1"><!></div>'),Lx=f('<!> <div class="text-[10px] text-dl-text-dim mb-1 font-mono"> </div> <div class="prose-dartlab overflow-x-auto"><!></div>',1),Ox=f("<th> </th>"),Rx=f("<td> </td>"),Dx=f("<tr></tr>"),jx=f('<button class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"> </button>'),Vx=f('<div class="text-[10px] text-dl-text-dim mt-1"> </div>'),Fx=f('<div class="overflow-x-auto rounded-lg border border-dl-border/10"><table class="finance-table"><thead><tr></tr></thead><tbody></tbody></table> <!></div> <!>',1),qx=f("<th> </th>"),Bx=f("<td> </td>"),Ux=f("<tr></tr>"),Gx=f('<button class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"> </button>'),Hx=f('<div class="text-[10px] text-dl-text-dim mt-1"> </div>'),Kx=f('<div class="overflow-x-auto rounded-lg border border-dl-border/10"><table class="prose-dartlab w-full text-[12px]"><thead><tr></tr></thead><tbody></tbody></table> <!></div> <!>',1);function Wi(e,t){wr(t,!0);let n=Be(t,"block",3,null),a=Be(t,"maxRows",3,100),o=G(null),i=G(!1);const s=new Set(["매출액","revenue","영업이익","operating_income","당기순이익","net_income","자산총계","total_assets","부채총계","total_liabilities","자본총계","total_equity","영업활동현금흐름","operating_cash_flow","매출총이익","gross_profit","EBITDA"]);function d(M,V){if(!(V!=null&&V.length))return!1;const E=String(M[V[0]]??"").trim();return s.has(E)}function u(M){if(M==null||M===""||M==="-")return M??"";if(typeof M=="number")return Math.abs(M)>=1?M.toLocaleString("ko-KR"):M.toString();const V=String(M).trim();if(/^-?[\d,]+(\.\d+)?$/.test(V)){const E=parseFloat(V.replace(/,/g,""));if(!isNaN(E))return Math.abs(E)>=1?E.toLocaleString("ko-KR"):E.toString()}return M}function p(M){if(typeof M=="number")return M<0;const V=String(M??"").trim().replace(/,/g,"");return/^-\d/.test(V)}function x(M){return typeof M=="number"?!0:typeof M=="string"&&/^-?[\d,]+(\.\d+)?$/.test(M.trim())}function g(M){return(M==null?void 0:M.kind)==="finance"}function w(M){return M!=null&&M.rawMarkdown?Object.keys(M.rawMarkdown):[]}function P(M){const V=w(M);return r(o)&&V.includes(r(o))?r(o):V[0]??null}let C=q(()=>{var M,V,E,F;return r(i)?((V=(M=n())==null?void 0:M.data)==null?void 0:V.rows)??[]:(((F=(E=n())==null?void 0:E.data)==null?void 0:F.rows)??[]).slice(0,a())});var R=be(),b=Q(R);{var S=M=>{var V=be(),E=Q(V);{var F=N=>{const X=q(()=>w(n())),H=q(()=>P(n()));var O=be(),ce=Q(O);{var ve=Pe=>{var he=Lx(),Ne=Q(he);{var me=D=>{var m=Nx(),_=l(m);kd(_,{get periods(){return r(X)},get selected(){return r(H)},onSelect:T=>{v(o,T,!0)}}),c(D,m)};k(Ne,D=>{r(X).length>1&&D(me)})}var de=h(Ne,2),B=l(de),ue=h(de,2),le=l(ue);yn(le,()=>ha(n().rawMarkdown[r(H)])),I(()=>A(B,r(H))),c(Pe,he)};k(ce,Pe=>{r(X).length>0&&Pe(ve)})}c(N,O)},se=N=>{var X=Fx(),H=Q(X),O=l(H),ce=l(O),ve=l(ce);ke(ve,21,()=>n().data.columns??[],Se,(B,ue)=>{var le=Ox(),D=l(le);I(()=>A(D,r(ue))),c(B,le)});var Pe=h(ce);ke(Pe,21,()=>r(C),Se,(B,ue)=>{const le=q(()=>d(r(ue),n().data.columns));var D=Dx();ke(D,21,()=>n().data.columns??[],Se,(m,_,T)=>{const K=q(()=>r(ue)[r(_)]),W=q(()=>T>0&&x(r(K)));var L=Rx(),xe=l(L);I((Ee,at)=>{je(L,1,Ee),A(xe,at)},[()=>r(W)?p(r(K))?"val-neg":"val-pos":"",()=>r(W)?u(r(K)):r(K)??""]),c(m,L)}),I(()=>je(D,1,Ut(r(le)?"row-key":""))),c(B,D)});var he=h(O,2);{var Ne=B=>{var ue=jx(),le=l(ue);I(()=>A(le,`외 ${n().data.rows.length-a()}행 더 보기`)),oe("click",ue,()=>{v(i,!0)}),c(B,ue)};k(he,B=>{!r(i)&&n().data.rows.length>a()&&B(Ne)})}var me=h(H,2);{var de=B=>{var ue=Vx(),le=l(ue);I(()=>A(le,`단위: ${(n().meta.unit||"")??""} ${n().meta.scale?`(${n().meta.scale})`:""}`)),c(B,ue)};k(me,B=>{var ue,le;((ue=n().meta)!=null&&ue.scale||(le=n().meta)!=null&&le.unit)&&B(de)})}c(N,X)},ne=q(()=>{var N;return g(n())&&((N=n().data)==null?void 0:N.rows)}),z=N=>{var X=Kx(),H=Q(X),O=l(H),ce=l(O),ve=l(ce);ke(ve,21,()=>n().data.columns??[],Se,(B,ue)=>{var le=qx(),D=l(le);I(()=>A(D,r(ue))),c(B,le)});var Pe=h(ce);ke(Pe,21,()=>r(C),Se,(B,ue)=>{var le=Ux();ke(le,21,()=>n().data.columns??[],Se,(D,m)=>{var _=Bx(),T=l(_);I(K=>{je(_,1,K),A(T,r(ue)[r(m)]??"")},[()=>Ut(x(r(ue)[r(m)])?"num":"")]),c(D,_)}),c(B,le)});var he=h(O,2);{var Ne=B=>{var ue=Gx(),le=l(ue);I(()=>A(le,`외 ${n().data.rows.length-a()}행 더 보기`)),oe("click",ue,()=>{v(i,!0)}),c(B,ue)};k(he,B=>{!r(i)&&n().data.rows.length>a()&&B(Ne)})}var me=h(H,2);{var de=B=>{var ue=Hx(),le=l(ue);I(()=>A(le,`단위: ${(n().meta.unit||"")??""} ${n().meta.scale?`(${n().meta.scale})`:""}`)),c(B,ue)};k(me,B=>{var ue;(ue=n().meta)!=null&&ue.scale&&B(de)})}c(N,X)};k(E,N=>{var X;n().kind==="raw_markdown"&&n().rawMarkdown?N(F):r(ne)?N(se,1):(X=n().data)!=null&&X.rows&&N(z,2)})}c(M,V)};k(b,M=>{n()&&M(S)})}c(e,R),yr()}Yr(["click"]);var Wx=f('<span class="flex items-center gap-1"><!> <span class="text-dl-accent"> </span> <span class="text-dl-text-dim/60"> </span></span>'),Yx=f('<span class="flex items-center gap-1"><!> <span>변경 없음</span></span>'),Xx=f('<span class="flex items-center gap-1 ml-auto"><span class="font-mono"> </span> <!> <span class="font-mono"> </span></span>'),Jx=f('<div class="text-dl-success/80 truncate"> </div>'),Qx=f('<div class="text-dl-primary-light/70 truncate"> </div>'),Zx=f('<div class="text-[11px] leading-relaxed"><!> <!></div>'),eh=f('<div class="flex flex-col gap-1.5 p-2.5 rounded-lg bg-dl-surface-card border border-dl-border/20"><div class="flex items-center gap-3 text-[11px] text-dl-text-dim"><span class="font-mono"> </span> <!> <!></div> <!></div>');function th(e,t){wr(t,!0);let n=Be(t,"summary",3,null);var a=be(),o=Q(a);{var i=s=>{var d=eh(),u=l(d),p=l(u),x=l(p),g=h(p,2);{var w=M=>{var V=Wx(),E=l(V);Pf(E,{size:11,class:"text-dl-accent"});var F=h(E,2),se=l(F),ne=h(F,2),z=l(ne);I(N=>{A(se,`변경 ${n().changedCount??""}회`),A(z,`(${N??""}%)`)},[()=>(n().changeRate*100).toFixed(1)]),c(M,V)},P=M=>{var V=Yx(),E=l(V);Sf(E,{size:11}),c(M,V)};k(g,M=>{n().changedCount>0?M(w):M(P,-1)})}var C=h(g,2);{var R=M=>{var V=Xx(),E=l(V),F=l(E),se=h(E,2);xf(se,{size:10});var ne=h(se,2),z=l(ne);I(()=>{A(F,n().latestFrom),A(z,n().latestTo)}),c(M,V)};k(C,M=>{n().latestFrom&&n().latestTo&&M(R)})}var b=h(u,2);{var S=M=>{var V=Zx(),E=l(V);ke(E,17,()=>n().added.slice(0,2),Se,(se,ne)=>{var z=Jx(),N=l(z);I(()=>A(N,`+ ${r(ne)??""}`)),c(se,z)});var F=h(E,2);ke(F,17,()=>n().removed.slice(0,2),Se,(se,ne)=>{var z=Qx(),N=l(z);I(()=>A(N,`- ${r(ne)??""}`)),c(se,z)}),c(M,V)};k(b,M=>{var V,E;(((V=n().added)==null?void 0:V.length)>0||((E=n().removed)==null?void 0:E.length)>0)&&M(S)})}I(()=>A(x,`${n().totalPeriods??""} periods`)),c(s,d)};k(o,s=>{n()&&s(i)})}c(e,a),yr()}var rh=f('<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim"> </span>'),nh=f('<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim"> </span>'),ah=f('<span class="px-2 py-0.5 rounded-full border border-emerald-500/20 bg-emerald-500/8 text-emerald-400/80"> </span>'),oh=f('<span class="px-2 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/8 text-blue-400/80"> </span>'),sh=f("<div> </div>"),ih=f('<h4 class="text-[14px] font-semibold text-dl-text"> </h4>'),lh=f('<div class="mb-2 mt-2"></div>'),dh=f('<span class="text-[10px] text-dl-text-dim font-mono"> </span>'),ch=f('<span class="text-[10px] text-dl-text-dim"> </span>'),uh=f('<span class="ml-0.5 text-emerald-400/50">*</span>'),vh=f("<button> <!></button>"),fh=f('<div class="flex flex-wrap gap-1 mb-2"></div>'),ph=f('<div class="text-blue-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-blue-400/60 mt-1.5 shrink-0"></span> </div>'),mh=f('<div class="text-emerald-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-emerald-400/50 mt-1.5 shrink-0"></span> </div>'),xh=f('<div class="text-dl-text-dim/50 flex gap-1"><span class="w-1 h-1 rounded-full bg-red-400/40 mt-1.5 shrink-0"></span> </div>'),hh=f('<div class="mb-3 px-3 py-2 rounded-lg border border-dl-border/15 bg-dl-surface-card/50 text-[11px] space-y-0.5 max-w-2xl"><div class="text-dl-text-dim font-medium"> </div> <!> <!> <!></div>'),gh=f('<p class="vw-para"> </p>'),bh=f('<div class="pl-3 py-1 mb-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-dl-text/85 text-[14px] leading-[1.85] rounded-r"> </div>'),_h=f('<div class="pl-3 py-1 mb-1 border-l-2 border-red-400 bg-red-500/5 text-dl-text/50 text-[14px] leading-[1.85] rounded-r line-through decoration-red-400/30"> </div>'),wh=f('<div><!> <div class="flex flex-wrap items-center gap-1.5 mb-2"><span> </span> <!> <!></div> <!> <!>  <div class="disclosure-text max-w-3xl"><!></div></div>'),yh=f('<div class="mt-6 pt-4 border-t border-dl-border/10"><div class="text-[10px] text-dl-text-dim uppercase tracking-widest font-semibold mb-3">표 · 정형 데이터</div></div>'),kh=f('<button class="absolute top-1 right-1 z-10 p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors opacity-0 group-hover:opacity-100" title="테이블 복사"><!></button>'),Ch=f('<div class="group relative"><!> <!></div>'),Sh=f('<div class="flex flex-wrap gap-1.5 text-[10px]"><!> <!> <!> <!></div> <!> <!> <!>',1),$h=f('<h3 class="text-[14px] font-semibold text-dl-text mt-4 mb-1"> </h3>'),Mh=f('<div class="mb-1 opacity-0 group-hover:opacity-100 transition-opacity"><!></div>'),Th=f('<!> <div class="text-[10px] text-dl-text-dim mb-1 font-mono"> </div> <div class="disclosure-text"><!></div>',1),zh=f('<div class="group"><!></div>'),Eh=f('<button class="absolute top-1 right-1 z-10 p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors opacity-0 group-hover:opacity-100" title="테이블 복사"><!></button>'),Ah=f('<div class="group relative"><!> <!></div>'),Ih=f('<div class="text-center py-12 text-[13px] text-dl-text-dim">이 topic에 표시할 데이터가 없습니다</div>'),Ph=f('<div class="space-y-4"><div><h2 class="text-[16px] font-semibold text-dl-text"> </h2></div> <!> <!> <!></div>'),Nh=f('<button class="ask-ai-float"><span class="flex items-center gap-1"><!> AI에게 물어보기</span></button>'),Lh=f("<!> <!>",1);function Oh(e,t){wr(t,!0);let n=Be(t,"topicData",3,null),a=Be(t,"diffSummary",3,null),o=Be(t,"onAskAI",3,null),i=G(Gt(new Map)),s=G(Gt(new Map)),d=G(null),u=G(Gt({show:!1,x:0,y:0,text:""})),p=q(()=>{var m,_,T;return((T=(_=(m=n())==null?void 0:m.textDocument)==null?void 0:_.sections)==null?void 0:T.length)>0}),x=q(()=>{var m;return(((m=n())==null?void 0:m.blocks)??[]).filter(_=>_.kind!=="text")});function g(m){if(!m)return"";if(typeof m=="string"){const _=m.match(/^(\d{4})(Q([1-4]))?$/);return _?_[3]?`${_[1]}Q${_[3]}`:_[1]:m}return m.kind==="annual"?`${m.year}Q4`:m.year&&m.quarter?`${m.year}Q${m.quarter}`:m.label||""}function w(m){return m==="updated"?"수정됨":m==="new"?"신규":m==="stale"?"과거유지":"유지"}function P(m){return m==="updated"?"bg-emerald-500/10 text-emerald-400/80 border-emerald-500/20":m==="new"?"bg-blue-500/10 text-blue-400/80 border-blue-500/20":m==="stale"?"bg-amber-500/10 text-amber-400/80 border-amber-500/20":"bg-dl-border/10 text-dl-text-dim border-dl-border/20"}function C(m){var T;const _=r(s).get(m.id);return _&&((T=m.views)!=null&&T[_])?m.views[_]:m.latest||null}function R(m,_){var K,W;const T=r(s).get(m.id);return T?T===_:((W=(K=m.latest)==null?void 0:K.period)==null?void 0:W.label)===_}function b(m){return r(s).has(m.id)}function S(m,_){const T=new Map(r(s));T.get(m)===_?T.delete(m):T.set(m,_),v(s,T,!0)}function M(m){return m.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function V(m){return String(m||"").replace(/\u00a0/g," ").replace(/\s+/g," ").trim()}function E(m){return!m||m.length>88?!1:/^\[.+\]$/.test(m)||/^【.+】$/.test(m)||/^[IVX]+\.\s/.test(m)||/^\d+\.\s/.test(m)||/^[가-힣]\.\s/.test(m)||/^\(\d+\)\s/.test(m)||/^\([가-힣]\)\s/.test(m)||/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(m)}function F(m){return/^[가나다라마바사아자차카타파하]\.\s/.test(m)?1:/^\d+\.\s/.test(m)?2:/^\(\d+\)\s/.test(m)||/^\([가-힣]\)\s/.test(m)?3:/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(m)?4:/^\[.+\]$/.test(m)||/^【.+】$/.test(m)?1:2}function se(m){if(!m)return"";if(/^\|.+\|$/m.test(m))return ha(m);const _=m.split(`
`);let T="",K=[];function W(){K.length!==0&&(T+=`<p class="vw-para">${M(K.join(" "))}</p>`,K=[])}for(const L of _){const xe=V(L);if(!xe){W();continue}if(E(xe)){W();const Ee=F(xe);T+=`<div class="ko-h${Ee}">${M(xe)}</div>`}else K.push(xe)}return W(),T}function ne(m){var T;if(!((T=m==null?void 0:m.diff)!=null&&T.length))return null;const _=[];for(const K of m.diff)for(const W of K.paragraphs||[])_.push({kind:K.kind,text:V(W)});return _}function z(m){return r(i).get(m)??null}function N(m,_){const T=new Map(r(i));T.set(m,_),v(i,T,!0)}function X(m,_){var T,K;return(K=(T=m==null?void 0:m.data)==null?void 0:T.rows)!=null&&K[0]?m.data.rows[0][_]??null:null}function H(m){var T,K,W;if(!((K=(T=m==null?void 0:m.data)==null?void 0:T.rows)!=null&&K[0]))return null;const _=m.data.rows[0];for(const L of((W=m.meta)==null?void 0:W.periods)??[])if(_[L])return{period:L,text:_[L]};return null}function O(m){var T,K,W;if(!((K=(T=m==null?void 0:m.data)==null?void 0:T.rows)!=null&&K[0]))return[];const _=m.data.rows[0];return(((W=m.meta)==null?void 0:W.periods)??[]).filter(L=>_[L]!=null)}function ce(m){return m.kind==="text"}function ve(m){return m.kind==="finance"||m.kind==="structured"||m.kind==="report"||m.kind==="raw_markdown"}function Pe(m,_){var W,L;if(!((L=(W=m==null?void 0:m.data)==null?void 0:W.rows)!=null&&L.length))return;const T=m.data.columns||[],K=[T.join("	")];for(const xe of m.data.rows)K.push(T.map(Ee=>xe[Ee]??"").join("	"));navigator.clipboard.writeText(K.join(`
`)).then(()=>{v(d,_,!0),setTimeout(()=>{v(d,null)},2e3)})}function he(m){if(!o())return;const _=window.getSelection(),T=_==null?void 0:_.toString().trim();if(!T||T.length<5){v(u,{show:!1,x:0,y:0,text:""},!0);return}const W=_.getRangeAt(0).getBoundingClientRect();v(u,{show:!0,x:W.left+W.width/2,y:W.top-8,text:T.slice(0,500)},!0)}function Ne(){r(u).text&&o()&&o()(r(u).text),v(u,{show:!1,x:0,y:0,text:""},!0)}function me(){r(u).show&&v(u,{show:!1,x:0,y:0,text:""},!0)}var de=Lh();fa("click",kl,me);var B=Q(de);{var ue=m=>{var _=Ph(),T=l(_),K=l(T),W=l(K),L=h(T,2);th(L,{get summary(){return a()}});var xe=h(L,2);{var Ee=Ue=>{const fe=q(()=>n().textDocument);var Ve=Sh(),Pt=Q(Ve),Ye=l(Pt);{var ot=Me=>{var ge=rh(),dt=l(ge);I(we=>A(dt,`최신 ${we??""}`),[()=>g(r(fe).latestPeriod)]),c(Me,ge)};k(Ye,Me=>{r(fe).latestPeriod&&Me(ot)})}var mt=h(Ye,2);{var $=Me=>{var ge=nh(),dt=l(ge);I(()=>A(dt,`${r(fe).sectionCount??""}개 섹션`)),c(Me,ge)};k(mt,Me=>{r(fe).sectionCount&&Me($)})}var Y=h(mt,2);{var U=Me=>{var ge=ah(),dt=l(ge);I(()=>A(dt,`${r(fe).updatedCount??""}개 수정`)),c(Me,ge)};k(Y,Me=>{r(fe).updatedCount>0&&Me(U)})}var re=h(Y,2);{var Z=Me=>{var ge=oh(),dt=l(ge);I(()=>A(dt,`${r(fe).newCount??""}개 신규`)),c(Me,ge)};k(re,Me=>{r(fe).newCount>0&&Me(Z)})}var Fe=h(Pt,2);ke(Fe,17,()=>r(fe).sections,Me=>Me.id,(Me,ge)=>{const dt=q(()=>C(r(ge))),we=q(()=>b(r(ge))),Oe=q(()=>r(we)?ne(r(dt)):null);var De=wh(),Ce=l(De);{var He=vt=>{var $e=lh();ke($e,21,()=>r(ge).headingPath,Se,(Te,Nt)=>{const Yt=q(()=>{var ft;return(ft=r(Nt).text)==null?void 0:ft.trim()});var ar=be(),kr=Q(ar);{var pr=ft=>{var jt=be(),Ze=Q(jt);{var et=Qt=>{var tr=sh(),dr=l(tr);I(Or=>{je(tr,1,`ko-h${Or??""}`),A(dr,r(Yt))},[()=>F(r(Yt))]),c(Qt,tr)},qt=q(()=>E(r(Yt))),or=Qt=>{var tr=ih(),dr=l(tr);I(()=>A(dr,r(Yt))),c(Qt,tr)};k(Ze,Qt=>{r(qt)?Qt(et):Qt(or,-1)})}c(ft,jt)};k(kr,ft=>{r(Yt)&&ft(pr)})}c(Te,ar)}),c(vt,$e)};k(Ce,vt=>{var $e;(($e=r(ge).headingPath)==null?void 0:$e.length)>0&&vt(He)})}var Je=h(Ce,2),Ct=l(Je),ae=l(Ct),Ie=h(Ct,2);{var _t=vt=>{var $e=dh(),Te=l($e);I(()=>A(Te,r(ge).latestChange)),c(vt,$e)};k(Ie,vt=>{r(ge).latestChange&&vt(_t)})}var ht=h(Ie,2);{var Et=vt=>{var $e=ch(),Te=l($e);I(()=>A(Te,`${r(ge).periodCount??""}기간`)),c(vt,$e)};k(ht,vt=>{r(ge).periodCount>1&&vt(Et)})}var Qe=h(Je,2);{var At=vt=>{var $e=fh();ke($e,21,()=>r(ge).timeline,Se,(Te,Nt)=>{const Yt=q(()=>{var jt;return((jt=r(Nt).period)==null?void 0:jt.label)||g(r(Nt).period)});var ar=vh(),kr=l(ar),pr=h(kr);{var ft=jt=>{var Ze=uh();c(jt,Ze)};k(pr,jt=>{r(Nt).status==="updated"&&jt(ft)})}I((jt,Ze)=>{je(ar,1,`px-2 py-1 rounded-lg text-[10px] font-mono transition-colors border
										${jt??""}`),A(kr,`${Ze??""} `)},[()=>R(r(ge),r(Yt))?"border-dl-accent/30 bg-dl-accent/8 text-dl-accent-light font-medium":r(Nt).status==="updated"?"border-emerald-500/15 text-emerald-400/60 hover:bg-emerald-500/5":"border-dl-border/15 text-dl-text-dim hover:bg-white/3",()=>g(r(Nt).period)]),oe("click",ar,()=>S(r(ge).id,r(Yt))),c(Te,ar)}),c(vt,$e)};k(Qe,vt=>{var $e;(($e=r(ge).timeline)==null?void 0:$e.length)>1&&vt(At)})}var Ot=h(Qe,2);{var Ht=vt=>{const $e=q(()=>r(dt).digest);var Te=hh(),Nt=l(Te),Yt=l(Nt),ar=h(Nt,2);ke(ar,17,()=>r($e).items.filter(ft=>ft.kind==="numeric"),Se,(ft,jt)=>{var Ze=ph(),et=h(l(Ze),1,!0);I(()=>A(et,r(jt).text)),c(ft,Ze)});var kr=h(ar,2);ke(kr,17,()=>r($e).items.filter(ft=>ft.kind==="added"),Se,(ft,jt)=>{var Ze=mh(),et=h(l(Ze),1,!0);I(()=>A(et,r(jt).text)),c(ft,Ze)});var pr=h(kr,2);ke(pr,17,()=>r($e).items.filter(ft=>ft.kind==="removed"),Se,(ft,jt)=>{var Ze=xh(),et=h(l(Ze),1,!0);I(()=>A(et,r(jt).text)),c(ft,Ze)}),I(()=>A(Yt,`${r($e).to??""} vs ${r($e).from??""}`)),c(vt,Te)};k(Ot,vt=>{var $e,Te,Nt;r(we)&&((Nt=(Te=($e=r(dt))==null?void 0:$e.digest)==null?void 0:Te.items)==null?void 0:Nt.length)>0&&vt(Ht)})}var fr=h(Ot,2),Ft=l(fr);{var Pr=vt=>{var $e=be(),Te=Q($e);ke(Te,17,()=>r(Oe),Se,(Nt,Yt)=>{var ar=be(),kr=Q(ar);{var pr=Ze=>{var et=gh(),qt=l(et);I(()=>A(qt,r(Yt).text)),c(Ze,et)},ft=Ze=>{var et=bh(),qt=l(et);I(()=>A(qt,r(Yt).text)),c(Ze,et)},jt=Ze=>{var et=_h(),qt=l(et);I(()=>A(qt,r(Yt).text)),c(Ze,et)};k(kr,Ze=>{r(Yt).kind==="same"?Ze(pr):r(Yt).kind==="added"?Ze(ft,1):r(Yt).kind==="removed"&&Ze(jt,2)})}c(Nt,ar)}),c(vt,$e)},jn=vt=>{var $e=be(),Te=Q($e);yn(Te,()=>se(r(dt).body)),c(vt,$e)};k(Ft,vt=>{var $e;r(we)&&r(Oe)?vt(Pr):($e=r(dt))!=null&&$e.body&&vt(jn,1)})}I((vt,$e)=>{je(De,1,`pt-2 pb-6 border-b border-dl-border/8 last:border-b-0 ${r(ge).status==="stale"?"border-l-2 border-l-amber-400/40 pl-3":""}`),je(Ct,1,`px-1.5 py-0.5 rounded text-[9px] font-medium border ${vt??""}`),A(ae,$e)},[()=>P(r(ge).status),()=>w(r(ge).status)]),oe("mouseup",fr,he),c(Me,De)});var qe=h(Fe,2);{var Dt=Me=>{var ge=yh();c(Me,ge)};k(qe,Me=>{r(x).length>0&&Me(Dt)})}var st=h(qe,2);ke(st,19,()=>r(x),Me=>Me.block,(Me,ge)=>{var dt=Ch(),we=l(dt);{var Oe=Ce=>{var He=kh(),Je=l(He);{var Ct=Ie=>{qs(Ie,{size:12,class:"text-dl-success"})},ae=Ie=>{Bi(Ie,{size:12})};k(Je,Ie=>{r(d)===r(ge).block?Ie(Ct):Ie(ae,-1)})}oe("click",He,()=>Pe(r(ge),r(ge).block)),c(Ce,He)};k(we,Ce=>{var He,Je;((Je=(He=r(ge).data)==null?void 0:He.rows)==null?void 0:Je.length)>0&&Ce(Oe)})}var De=h(we,2);Wi(De,{get block(){return r(ge)}}),c(Me,dt)}),c(Ue,Ve)},at=Ue=>{var fe=be(),Ve=Q(fe);ke(Ve,19,()=>n().blocks,Pt=>Pt.block,(Pt,Ye,ot)=>{var mt=be(),$=Q(mt);{var Y=Fe=>{const qe=q(()=>z(r(ot))),Dt=q(()=>H(r(Ye))),st=q(()=>O(r(Ye))),Me=q(()=>{var De;return r(qe)||((De=r(Dt))==null?void 0:De.period)}),ge=q(()=>{var De;return r(Me)?X(r(Ye),r(Me)):(De=r(Dt))==null?void 0:De.text});var dt=be(),we=Q(dt);{var Oe=De=>{var Ce=zh(),He=l(Ce);{var Je=ae=>{var Ie=$h(),_t=l(Ie);I(()=>A(_t,r(ge))),c(ae,Ie)},Ct=ae=>{var Ie=Th(),_t=Q(Ie);{var ht=Ht=>{var fr=Mh(),Ft=l(fr);kd(Ft,{get periods(){return r(st)},get selected(){return r(Me)},onSelect:Pr=>N(r(ot),Pr)}),c(Ht,fr)};k(_t,Ht=>{r(st).length>1&&Ht(ht)})}var Et=h(_t,2),Qe=l(Et),At=h(Et,2),Ot=l(At);yn(Ot,()=>se(r(ge))),I(()=>A(Qe,r(Me))),oe("mouseup",At,he),c(ae,Ie)};k(He,ae=>{r(Ye).textType==="heading"?ae(Je):ae(Ct,-1)})}c(De,Ce)};k(we,De=>{r(ge)&&De(Oe)})}c(Fe,dt)},U=q(()=>ce(r(Ye))),re=Fe=>{var qe=Ah(),Dt=l(qe);{var st=ge=>{var dt=Eh(),we=l(dt);{var Oe=Ce=>{qs(Ce,{size:12,class:"text-dl-success"})},De=Ce=>{Bi(Ce,{size:12})};k(we,Ce=>{r(d)===r(Ye).block?Ce(Oe):Ce(De,-1)})}oe("click",dt,()=>Pe(r(Ye),r(Ye).block)),c(ge,dt)};k(Dt,ge=>{var dt,we;((we=(dt=r(Ye).data)==null?void 0:dt.rows)==null?void 0:we.length)>0&&ge(st)})}var Me=h(Dt,2);Wi(Me,{get block(){return r(Ye)}}),c(Fe,qe)},Z=q(()=>ve(r(Ye)));k($,Fe=>{r(U)?Fe(Y):r(Z)&&Fe(re,1)})}c(Pt,mt)}),c(Ue,fe)};k(xe,Ue=>{r(p)?Ue(Ee):Ue(at,-1)})}var Ae=h(xe,2);{var Tt=Ue=>{var fe=Ih();c(Ue,fe)};k(Ae,Ue=>{var fe;((fe=n().blocks)==null?void 0:fe.length)===0&&!r(p)&&Ue(Tt)})}I(()=>A(W,n().topicLabel||"")),c(m,_)};k(B,m=>{n()&&m(ue)})}var le=h(B,2);{var D=m=>{var _=Nh(),T=l(_),K=l(T);Jo(K,{size:10}),I(()=>Wo(_,`left: ${r(u).x??""}px; top: ${r(u).y??""}px; transform: translate(-50%, -100%)`)),oe("click",_,Ne),c(m,_)};k(le,m=>{r(u).show&&m(D)})}c(e,de),yr()}Yr(["click","mouseup"]);var Rh=f('<div class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"></div>'),Dh=f('<button class="p-1 rounded-md text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"><!></button>'),jh=f('<div class="flex items-center justify-between"><div class="min-w-0"><div class="text-[12px] font-semibold text-dl-text truncate"> </div> <div class="text-[10px] font-mono text-dl-text-dim"> </div></div> <div class="flex items-center gap-0.5 flex-shrink-0"><button class="p-1 rounded-md text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="검색 (Ctrl+F)"><!></button> <!></div></div>'),Vh=f('<div class="text-[12px] text-dl-text-dim">종목 미선택</div>'),Fh=f('<button class="text-dl-text-dim hover:text-dl-text"><!></button>'),qh=f('<div class="flex items-center justify-center py-2 gap-1"><!> <span class="text-[10px] text-dl-text-dim">검색 중...</span></div>'),Bh=f('<div class="text-[10px] text-dl-text-dim py-2 text-center">결과 없음</div>'),Uh=f('<div class="text-[10px] text-dl-text-dim truncate mt-0.5"> </div>'),Gh=f('<button class="w-full text-left px-2 py-1 text-[11px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 rounded transition-colors"><div class="truncate"><span class="text-dl-text-dim/60 text-[9px]"> </span> <span class="ml-1"> </span></div> <!></button>'),Hh=f('<div class="flex items-center justify-center py-1"><!></div>'),Kh=f("<!> <!>",1),Wh=f('<div class="mt-1 max-h-48 overflow-y-auto"><!></div>'),Yh=f('<div class="px-2 py-1.5 border-b border-dl-border/20 flex-shrink-0"><div class="flex items-center gap-1 bg-dl-bg-darker rounded-md border border-dl-border/30 px-2 py-1"><!> <input placeholder="topic 검색..." class="flex-1 bg-transparent text-[11px] text-dl-text outline-none placeholder:text-dl-text-dim min-w-0"/> <!></div> <!></div>'),Xh=f('<span class="text-[11px] text-dl-text-muted truncate"> </span>'),Jh=f('<div class="sticky top-0 z-30 flex items-center gap-2 px-3 py-1.5 bg-dl-bg-dark/95 border-b border-dl-border/20 backdrop-blur-sm"><button class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"><!> <span>목차</span></button> <!></div>'),Qh=f('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[14px] text-dl-text-muted mb-1">공시 뷰어</div> <div class="text-[12px] text-dl-text-dim">종목을 검색하여 공시 문서를 살펴보세요</div></div>'),Zh=f('<div class="max-w-4xl mx-auto px-6 py-4 space-y-4 animate-fadeIn"><div class="skeleton-line w-48 h-5"></div> <div class="skeleton-line w-full h-3"></div> <div class="skeleton-line w-5/6 h-3"></div> <div class="skeleton-line w-full h-3"></div> <div class="skeleton-line w-4/6 h-3"></div> <div class="skeleton-line w-full h-16 mt-4"></div></div>'),eg=f('<div class="max-w-4xl mx-auto px-6 py-4 space-y-3 animate-fadeIn"><div class="skeleton-line w-40 h-5"></div> <div class="skeleton-line w-full h-3"></div> <div class="skeleton-line w-3/4 h-3"></div> <div class="skeleton-line w-full h-3"></div></div>'),tg=f('<div class="max-w-4xl mx-auto px-6 py-4 animate-fadeIn"><!></div>'),rg=f('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[13px] text-dl-text-dim">좌측 목차에서 항목을 선택하세요</div></div>'),ng=f('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[13px] text-dl-text-dim">이 종목의 공시 데이터가 없습니다</div></div>'),ag=f('<div class="flex h-full min-h-0 bg-dl-bg-dark relative"><!> <div><div class="h-full flex flex-col"><div class="px-3 py-2 border-b border-dl-border/20 flex-shrink-0"><!></div> <!> <!></div></div> <div class="flex-1 min-w-0 overflow-y-auto"><!> <!></div></div>');function og(e,t){wr(t,!0);let n=Be(t,"viewer",3,null),a=Be(t,"company",3,null),o=Be(t,"onAskAI",3,null),i=Be(t,"onTopicChange",3,null),s=G(!1),d=G(!1);function u(){v(d,typeof window<"u"&&window.innerWidth<=768,!0)}Kr(()=>(u(),window.addEventListener("resize",u),()=>window.removeEventListener("resize",u)));let p=G(!1),x=G(""),g=G(null);function w(){v(p,!r(p)),r(p)?requestAnimationFrame(()=>{var m;return(m=r(g))==null?void 0:m.focus()}):v(x,"")}Kr(()=>{var m;(m=a())!=null&&m.stockCode&&n()&&n().loadCompany(a().stockCode)}),Kr(()=>{var m,_,T;(m=n())!=null&&m.selectedTopic&&((_=n())!=null&&_.topicData)&&((T=i())==null||T(n().selectedTopic,n().topicData.topicLabel||n().selectedTopic))});let P=G(null),C=G(!1),R=null;function b(){var _,T;if(!((T=(_=n())==null?void 0:_.toc)!=null&&T.chapters))return[];const m=[];for(const K of n().toc.chapters)for(const W of K.topics)m.push({topic:W.topic,chapter:K.chapter});return m}function S(m){var _;if(m.key==="f"&&(m.ctrlKey||m.metaKey)&&a()&&(m.preventDefault(),w()),m.key==="Escape"&&r(p)&&(v(p,!1),v(x,""),v(P,null)),!r(p)&&(m.key==="ArrowUp"||m.key==="ArrowDown")&&((_=n())!=null&&_.selectedTopic)){const T=b(),K=T.findIndex(L=>L.topic===n().selectedTopic);if(K<0)return;const W=m.key==="ArrowDown"?K+1:K-1;W>=0&&W<T.length&&(m.preventDefault(),n().selectTopic(T[W].topic,T[W].chapter))}}Kr(()=>{var T,K,W;const m=r(x).trim();if(!m||!((T=a())!=null&&T.stockCode)){v(P,null);return}const _=[];if((W=(K=n())==null?void 0:K.toc)!=null&&W.chapters){const L=m.toLowerCase();for(const xe of n().toc.chapters)for(const Ee of xe.topics)(Ee.label.toLowerCase().includes(L)||Ee.topic.toLowerCase().includes(L))&&_.push({topic:Ee.topic,label:Ee.label,chapter:xe.chapter,snippet:"",matchCount:0,source:"toc"})}v(P,_.length>0?_:null,!0),clearTimeout(R),m.length>=2&&(v(C,!0),R=setTimeout(async()=>{try{const L=await lv(a().stockCode,m);if(r(x).trim()!==m)return;const xe=(L.results||[]).map(Ae=>({...Ae,source:"text"})),Ee=new Set(_.map(Ae=>Ae.topic)),at=[..._,...xe.filter(Ae=>!Ee.has(Ae.topic))];v(P,at.length>0?at:null,!0)}catch{}v(C,!1)},300))});var M=ag();fa("keydown",Ko,S);var V=l(M);{var E=m=>{var _=Rh();oe("click",_,()=>{v(s,!1)}),c(m,_)};k(V,m=>{r(d)&&r(s)&&m(E)})}var F=h(V,2),se=l(F),ne=l(se),z=l(ne);{var N=m=>{var _=jh(),T=l(_),K=l(T),W=l(K),L=h(K,2),xe=l(L),Ee=h(T,2),at=l(Ee),Ae=l(at);Oa(Ae,{size:12});var Tt=h(at,2);{var Ue=fe=>{var Ve=Dh(),Pt=l(Ve);io(Pt,{size:12}),oe("click",Ve,()=>{v(s,!1)}),c(fe,Ve)};k(Tt,fe=>{r(d)&&fe(Ue)})}I(()=>{A(W,a().corpName||a().company),A(xe,a().stockCode)}),oe("click",at,w),c(m,_)},X=m=>{var _=Vh();c(m,_)};k(z,m=>{a()?m(N):m(X,-1)})}var H=h(ne,2);{var O=m=>{var _=Yh(),T=l(_),K=l(T);Oa(K,{size:11,class:"text-dl-text-dim flex-shrink-0"});var W=h(K,2);pa(W,Ae=>v(g,Ae),()=>r(g));var L=h(W,2);{var xe=Ae=>{var Tt=Fh(),Ue=l(Tt);io(Ue,{size:10}),oe("click",Tt,()=>{v(x,"")}),c(Ae,Tt)};k(L,Ae=>{r(x)&&Ae(xe)})}var Ee=h(T,2);{var at=Ae=>{var Tt=Wh(),Ue=l(Tt);{var fe=Ye=>{var ot=qh(),mt=l(ot);Hr(mt,{size:10,class:"animate-spin text-dl-text-dim"}),c(Ye,ot)},Ve=Ye=>{var ot=Bh();c(Ye,ot)},Pt=Ye=>{var ot=Kh(),mt=Q(ot);ke(mt,17,()=>r(P).slice(0,20),Se,(U,re)=>{var Z=Gh(),Fe=l(Z),qe=l(Fe),Dt=l(qe),st=h(qe,2),Me=l(st),ge=h(Fe,2);{var dt=we=>{var Oe=Uh(),De=l(Oe);I(()=>A(De,r(re).snippet)),c(we,Oe)};k(ge,we=>{r(re).snippet&&we(dt)})}I(()=>{A(Dt,r(re).chapter||""),A(Me,r(re).label)}),oe("click",Z,()=>{var we;(we=n())==null||we.selectTopic(r(re).topic,r(re).chapter),v(p,!1),v(x,""),v(P,null)}),c(U,Z)});var $=h(mt,2);{var Y=U=>{var re=Hh(),Z=l(re);Hr(Z,{size:9,class:"animate-spin text-dl-text-dim"}),c(U,re)};k($,U=>{r(C)&&U(Y)})}c(Ye,ot)};k(Ue,Ye=>{r(C)&&!r(P)?Ye(fe):r(P)&&r(P).length===0?Ye(Ve,1):r(P)&&Ye(Pt,2)})}c(Ae,Tt)};k(Ee,Ae=>{(r(P)||r(C))&&Ae(at)})}za(W,()=>r(x),Ae=>v(x,Ae)),c(m,_)};k(H,m=>{r(p)&&m(O)})}var ce=h(H,2);{let m=q(()=>{var W;return(W=n())==null?void 0:W.toc}),_=q(()=>{var W;return(W=n())==null?void 0:W.tocLoading}),T=q(()=>{var W;return(W=n())==null?void 0:W.selectedTopic}),K=q(()=>{var W;return(W=n())==null?void 0:W.expandedChapters});Ax(ce,{get toc(){return r(m)},get loading(){return r(_)},get selectedTopic(){return r(T)},get expandedChapters(){return r(K)},onSelectTopic:(W,L)=>{var xe;(xe=n())==null||xe.selectTopic(W,L),r(d)&&v(s,!1)},onToggleChapter:W=>{var L;return(L=n())==null?void 0:L.toggleChapter(W)}})}var ve=h(F,2),Pe=l(ve);{var he=m=>{var _=Jh(),T=l(_),K=l(T);on(K,{size:11});var W=h(T,2);{var L=xe=>{var Ee=Xh(),at=l(Ee);I(()=>{var Ae,Tt,Ue;return A(at,((Tt=(Ae=n())==null?void 0:Ae.topicData)==null?void 0:Tt.topicLabel)||((Ue=n())==null?void 0:Ue.selectedTopic))}),c(xe,Ee)};k(W,xe=>{var Ee;(Ee=n())!=null&&Ee.selectedTopic&&xe(L)})}oe("click",T,()=>{v(s,!0)}),c(m,_)};k(Pe,m=>{r(d)&&a()&&m(he)})}var Ne=h(Pe,2);{var me=m=>{var _=Qh(),T=l(_);on(T,{size:32,class:"text-dl-text-dim/30 mb-3"}),c(m,_)},de=m=>{var _=Zh();c(m,_)},B=m=>{var _=eg();c(m,_)},ue=m=>{var _=tg(),T=l(_);Oh(T,{get topicData(){return n().topicData},get diffSummary(){return n().diffSummary},get onAskAI(){return o()}}),c(m,_)},le=m=>{var _=rg(),T=l(_);on(T,{size:28,class:"text-dl-text-dim/30 mb-3"}),c(m,_)},D=m=>{var _=ng(),T=l(_);Ka(T,{size:28,class:"text-dl-text-dim/30 mb-3"}),c(m,_)};k(Ne,m=>{var _,T,K,W,L,xe,Ee,at;a()?(_=n())!=null&&_.tocLoading?m(de,1):(T=n())!=null&&T.topicLoading?m(B,2):(K=n())!=null&&K.topicData?m(ue,3):(W=n())!=null&&W.toc&&!((L=n())!=null&&L.selectedTopic)?m(le,4):((at=(Ee=(xe=n())==null?void 0:xe.toc)==null?void 0:Ee.chapters)==null?void 0:at.length)===0&&m(D,5):m(me)})}I(()=>je(F,1,`${r(d)?`fixed top-0 left-0 bottom-0 z-50 w-64 transition-transform duration-200 ${r(s)?"translate-x-0":"-translate-x-full"}`:"flex-shrink-0 w-56"} border-r border-dl-border/30 overflow-hidden bg-dl-bg-dark`)),c(e,M),yr()}Yr(["click"]);var sg=f('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),ig=f("<!> <span>확인 중...</span>",1),lg=f("<!> <span>설정 필요</span>",1),dg=f('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),cg=f('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!>',1),ug=f('<div class="min-w-0 flex-1 pt-10"><!></div>'),vg=f('<div class="flex-shrink-0 border-l border-dl-border/30 transition-all duration-300"><!></div>'),fg=f('<div class="min-w-0 flex-1 flex flex-col"><!></div> <!>',1),pg=f('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),mg=f('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),xg=f('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),hg=f('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),gg=f('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),bg=f('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),_g=f('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),wg=f('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),yg=f('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),kg=f('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),Cg=f('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),Sg=f('<div class="text-[10px] text-dl-text-dim mt-2"> </div>'),$g=f('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex login</div></div></div></div> <!> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),Mg=f('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2"> </div></div>'),Tg=f('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 계정 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),zg=f('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),Eg=f("<button> <!></button>"),Ag=f('<div class="flex flex-wrap gap-1.5"></div>'),Ig=f('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),Pg=f('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),Ng=f('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),Lg=f('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),Og=f('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),Rg=f('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),Dg=f('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),jg=f("<!> <!> <!> <!> <!> <!>",1),Vg=f('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),Fg=f('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),qg=f('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),Bg=f('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><span class="text-[10px] text-dl-text-dim">공시 보기</span> <!></div></button>'),Ug=f('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div></div> <!>',1),Gg=f('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div></button>'),Hg=f('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div></div> <!>',1),Kg=f('<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),Wg=f('<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim"><!> <div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div> <div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div></div>'),Yg=f('<div class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn" role="presentation"><div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"><div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"/> <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div> <div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim"><span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span></div></div></div>'),Xg=f('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),Jg=f('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-2 left-3 z-20 pointer-events-auto flex items-center gap-1"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center ml-2 rounded-lg bg-dl-bg-card/60 border border-dl-border/20 p-0.5"><button><!> <span>Chat</span></button> <button><!> <span>Viewer</span></button></div></div> <div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="종목 검색 (Ctrl+K)"><!></button> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <button><!> <!></button></div> <div class="flex flex-1 min-h-0"><!></div></div></div>  <!> <!> <!> <!>',1);function Qg(e,t){wr(t,!0);let n=G(""),a=G(!1),o=G(null),i=G(Gt({})),s=G(Gt({})),d=G(null),u=G(null),p=G(Gt([])),x=G(!1),g=G(0),w=G(!0),P=G(""),C=G(!1),R=G(null),b=G(Gt({})),S=G(Gt({})),M=G(""),V=G(!1),E=G(null),F=G(""),se=G(!1),ne=G(""),z=G(0),N=G(null),X=G(null),H=G(null);const O=sf(),ce=lf();let ve=G(!1),Pe=q(()=>r(ve)?"100%":O.panelMode==="viewer"?"65%":"50%"),he=G(!1),Ne=G(""),me=G(Gt([])),de=G(-1),B=null,ue=G(null),le=G(!1);function D(){v(le,window.innerWidth<=768),r(le)&&(v(x,!1),O.closePanel())}Kr(()=>(D(),window.addEventListener("resize",D),()=>window.removeEventListener("resize",D))),Kr(()=>{!r(C)||!r(X)||requestAnimationFrame(()=>{var y;return(y=r(X))==null?void 0:y.focus()})}),Kr(()=>{!r(m)||!r(H)||requestAnimationFrame(()=>{var y;return(y=r(H))==null?void 0:y.focus()})}),Kr(()=>{!r(he)||!r(ue)||requestAnimationFrame(()=>{var y;return(y=r(ue))==null?void 0:y.focus()})});let m=G(null),_=G(""),T=G("error"),K=G(!1);function W(y,ee="error",Le=4e3){v(_,y,!0),v(T,ee,!0),v(K,!0),setTimeout(()=>{v(K,!1)},Le)}const L=rf();Kr(()=>{fe()});let xe=G(Gt({}));function Ee(y){return y==="chatgpt"?"codex":y}function at(y){return`dartlab-api-key:${Ee(y)}`}function Ae(y){return typeof sessionStorage>"u"||!y?"":sessionStorage.getItem(at(y))||""}function Tt(y,ee){typeof sessionStorage>"u"||!y||(ee?sessionStorage.setItem(at(y),ee):sessionStorage.removeItem(at(y)))}async function Ue(y,ee=null,Le=null){var Ke;const Xe=await Qu(y,ee,Le);if(Xe!=null&&Xe.provider){const ut=Ee(Xe.provider);v(i,{...r(i),[ut]:{...r(i)[ut]||{},available:!!Xe.available,model:Xe.model||((Ke=r(i)[ut])==null?void 0:Ke.model)||ee||null}},!0)}return Xe}async function fe(){var y,ee,Le;v(w,!0);try{const Xe=await Ju();v(i,Xe.providers||{},!0),v(s,Xe.ollama||{},!0),v(xe,Xe.codex||{},!0),Xe.version&&v(P,Xe.version,!0);const Ke=Ee(localStorage.getItem("dartlab-provider")),ut=localStorage.getItem("dartlab-model"),pe=Ae(Ke);if(Ke&&((y=r(i)[Ke])!=null&&y.available)){v(d,Ke,!0),v(R,Ke,!0),v(M,pe,!0),await Ve(Ke);const ie=r(b)[Ke]||[];ut&&ie.includes(ut)?v(u,ut,!0):ie.length>0&&(v(u,ie[0],!0),localStorage.setItem("dartlab-model",r(u))),v(p,ie,!0),v(w,!1);return}if(Ke&&r(i)[Ke]){if(v(d,Ke,!0),v(R,Ke,!0),v(M,pe,!0),pe)try{await Ue(Ke,ut,pe)}catch{}await Ve(Ke);const ie=r(b)[Ke]||[];v(p,ie,!0),ut&&ie.includes(ut)?v(u,ut,!0):ie.length>0&&v(u,ie[0],!0),v(w,!1);return}for(const ie of["codex","ollama","openai"])if((ee=r(i)[ie])!=null&&ee.available){v(d,ie,!0),v(R,ie,!0),v(M,Ae(ie),!0),await Ve(ie);const ze=r(b)[ie]||[];v(p,ze,!0),v(u,((Le=r(i)[ie])==null?void 0:Le.model)||(ze.length>0?ze[0]:null),!0),r(u)&&localStorage.setItem("dartlab-model",r(u));break}}catch{}v(w,!1)}async function Ve(y){y=Ee(y),v(S,{...r(S),[y]:!0},!0);try{const ee=await Zu(y);v(b,{...r(b),[y]:ee.models||[]},!0)}catch{v(b,{...r(b),[y]:[]},!0)}v(S,{...r(S),[y]:!1},!0)}async function Pt(y){var Le;y=Ee(y),v(d,y,!0),v(u,null),v(R,y,!0),localStorage.setItem("dartlab-provider",y),localStorage.removeItem("dartlab-model"),v(M,Ae(y),!0),v(E,null),await Ve(y);const ee=r(b)[y]||[];if(v(p,ee,!0),ee.length>0&&(v(u,((Le=r(i)[y])==null?void 0:Le.model)||ee[0],!0),localStorage.setItem("dartlab-model",r(u)),r(M)))try{await Ue(y,r(u),r(M))}catch{}}async function Ye(y){v(u,y,!0),localStorage.setItem("dartlab-model",y);const ee=Ae(r(d));if(ee)try{await Ue(Ee(r(d)),y,ee)}catch{}}function ot(y){y=Ee(y),r(R)===y?v(R,null):(v(R,y,!0),Ve(y))}async function mt(){const y=r(M).trim();if(!(!y||!r(d))){v(V,!0),v(E,null);try{const ee=await Ue(Ee(r(d)),r(u),y);ee.available?(Tt(r(d),y),v(E,"success"),!r(u)&&ee.model&&v(u,ee.model,!0),await Ve(r(d)),v(p,r(b)[r(d)]||[],!0),W("API 키 인증 성공","success")):(Tt(r(d),""),v(E,"error"))}catch{Tt(r(d),""),v(E,"error")}v(V,!1)}}async function $(){try{await tv(),r(d)==="codex"&&v(i,{...r(i),codex:{...r(i).codex,available:!1}},!0),W("Codex 계정 로그아웃 완료","success"),await fe()}catch{W("로그아웃 실패")}}function Y(){const y=r(F).trim();!y||r(se)||(v(se,!0),v(ne,"준비 중..."),v(z,0),v(N,ev(y,{onProgress(ee){ee.total&&ee.completed!==void 0?(v(z,Math.round(ee.completed/ee.total*100),!0),v(ne,`다운로드 중... ${r(z)}%`)):ee.status&&v(ne,ee.status,!0)},async onDone(){v(se,!1),v(N,null),v(F,""),v(ne,""),v(z,0),W(`${y} 다운로드 완료`,"success"),await Ve("ollama"),v(p,r(b).ollama||[],!0),r(p).includes(y)&&await Ye(y)},onError(ee){v(se,!1),v(N,null),v(ne,""),v(z,0),W(`다운로드 실패: ${ee}`)}}),!0))}function U(){r(N)&&(r(N).abort(),v(N,null)),v(se,!1),v(F,""),v(ne,""),v(z,0)}function re(){v(x,!r(x))}function Z(y){O.openData(y)}function Fe(y,ee=null){O.openEvidence(y,ee)}function qe(y){O.openViewer(y)}function Dt(){if(v(M,""),v(E,null),r(d))v(R,r(d),!0);else{const y=Object.keys(r(i));v(R,y.length>0?y[0]:null,!0)}v(C,!0),r(R)&&Ve(r(R))}function st(y){var ee,Le,Xe,Ke;if(y)for(let ut=y.messages.length-1;ut>=0;ut--){const pe=y.messages[ut];if(pe.role==="assistant"&&((ee=pe.meta)!=null&&ee.stockCode||(Le=pe.meta)!=null&&Le.company||pe.company)){O.syncCompanyFromMessage({company:((Xe=pe.meta)==null?void 0:Xe.company)||pe.company,stockCode:(Ke=pe.meta)==null?void 0:Ke.stockCode},O.selectedCompany);return}}}function Me(){L.createConversation(),v(n,""),v(a,!1),r(o)&&(r(o).abort(),v(o,null))}function ge(y){L.setActive(y),st(L.active),v(n,""),v(a,!1),r(o)&&(r(o).abort(),v(o,null))}function dt(y){v(m,y,!0)}function we(){r(m)&&(L.deleteConversation(r(m)),v(m,null))}function Oe(){var ee;const y=L.active;if(!y)return null;for(let Le=y.messages.length-1;Le>=0;Le--){const Xe=y.messages[Le];if(Xe.role==="assistant"&&((ee=Xe.meta)!=null&&ee.stockCode))return Xe.meta.stockCode}return null}async function De(y=null){var nr,ur,ir;const ee=(y??r(n)).trim();if(!ee||r(a))return;if(!r(d)||!((nr=r(i)[r(d)])!=null&&nr.available)){W("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),Dt();return}L.activeId||L.createConversation();const Le=L.activeId;L.addMessage("user",ee),v(n,""),v(a,!0),L.addMessage("assistant",""),L.updateLastMessage({loading:!0,startedAt:Date.now()}),So(g);const Xe=L.active,Ke=[];let ut=null;if(Xe){const J=Xe.messages.slice(0,-2);for(const te of J)if((te.role==="user"||te.role==="assistant")&&te.text&&te.text.trim()&&!te.error&&!te.loading){const We={role:te.role,text:te.text};te.role==="assistant"&&((ur=te.meta)!=null&&ur.stockCode)&&(We.meta={company:te.meta.company||te.company,stockCode:te.meta.stockCode,modules:te.meta.includedModules||null,market:te.meta.market||null,topic:te.meta.topic||null,topicLabel:te.meta.topicLabel||null,dialogueMode:te.meta.dialogueMode||null,questionTypes:te.meta.questionTypes||null,userGoal:te.meta.userGoal||null},ut=te.meta.stockCode),Ke.push(We)}}const pe=((ir=O.selectedCompany)==null?void 0:ir.stockCode)||ut||Oe(),ie=O.getViewContext();function ze(){return L.activeId!==Le}const wt={provider:r(d),model:r(u),viewContext:ie},Zt=Ae(r(d));Zt&&(wt.api_key=Zt);const sr=dv(pe,ee,wt,{onMeta(J){var Bt;if(ze())return;const te=L.active,We=te==null?void 0:te.messages[te.messages.length-1],tt={meta:{...(We==null?void 0:We.meta)||{},...J}};J.company&&(tt.company=J.company,L.activeId&&((Bt=L.active)==null?void 0:Bt.title)==="새 대화"&&L.updateTitle(L.activeId,J.company)),J.stockCode&&(tt.stockCode=J.stockCode),(J.company||J.stockCode)&&O.syncCompanyFromMessage(J,O.selectedCompany),L.updateLastMessage(tt)},onSnapshot(J){ze()||L.updateLastMessage({snapshot:J})},onContext(J){if(ze())return;const te=L.active;if(!te)return;const We=te.messages[te.messages.length-1],Re=(We==null?void 0:We.contexts)||[];L.updateLastMessage({contexts:[...Re,{module:J.module,label:J.label,text:J.text}]})},onSystemPrompt(J){ze()||L.updateLastMessage({systemPrompt:J.text,userContent:J.userContent||null})},onToolCall(J){if(ze())return;const te=L.active;if(!te)return;const We=te.messages[te.messages.length-1],Re=(We==null?void 0:We.toolEvents)||[];L.updateLastMessage({toolEvents:[...Re,{type:"call",name:J.name,arguments:J.arguments}]})},onToolResult(J){if(ze())return;const te=L.active;if(!te)return;const We=te.messages[te.messages.length-1],Re=(We==null?void 0:We.toolEvents)||[];L.updateLastMessage({toolEvents:[...Re,{type:"result",name:J.name,result:J.result}]})},onChunk(J){if(ze())return;const te=L.active;if(!te)return;const We=te.messages[te.messages.length-1];L.updateLastMessage({text:((We==null?void 0:We.text)||"")+J}),So(g)},onDone(){if(ze())return;const J=L.active,te=J==null?void 0:J.messages[J.messages.length-1],We=te!=null&&te.startedAt?((Date.now()-te.startedAt)/1e3).toFixed(1):null;L.updateLastMessage({loading:!1,duration:We}),L.flush(),v(a,!1),v(o,null),So(g)},onViewerNavigate(J){ze()||ae(J)},onError(J,te,We){ze()||(L.updateLastMessage({text:`오류: ${J}`,loading:!1,error:!0}),L.flush(),te==="login"?(W(`${J} — 설정에서 Codex 로그인을 확인하세요`),Dt()):te==="install"?(W(`${J} — 설정에서 Codex 설치 안내를 확인하세요`),Dt()):W(J),v(a,!1),v(o,null))}},Ke);v(o,sr,!0)}function Ce(){r(o)&&(r(o).abort(),v(o,null),v(a,!1),L.updateLastMessage({loading:!1}),L.flush())}function He(){const y=L.active;if(!y||y.messages.length<2)return;let ee="";for(let Le=y.messages.length-1;Le>=0;Le--)if(y.messages[Le].role==="user"){ee=y.messages[Le].text;break}ee&&(L.removeLastMessage(),L.removeLastMessage(),v(n,ee,!0),requestAnimationFrame(()=>{De()}))}function Je(){const y=L.active;if(!y)return;let ee=`# ${y.title}

`;for(const ut of y.messages)ut.role==="user"?ee+=`## You

${ut.text}

`:ut.role==="assistant"&&ut.text&&(ee+=`## DartLab

${ut.text}

`);const Le=new Blob([ee],{type:"text/markdown;charset=utf-8"}),Xe=URL.createObjectURL(Le),Ke=document.createElement("a");Ke.href=Xe,Ke.download=`${y.title||"dartlab-chat"}.md`,Ke.click(),URL.revokeObjectURL(Xe),W("대화가 마크다운으로 내보내졌습니다","success")}function Ct(y){var Xe;O.switchView("chat");const ee=((Xe=ce.topicData)==null?void 0:Xe.topicLabel)||"",Le=ee?`[${ee}] `:"";v(n,`${Le}"${y}" — 이 내용에 대해 설명해줘`),requestAnimationFrame(()=>{const Ke=document.querySelector(".input-textarea");Ke&&Ke.focus()})}function ae(y){y!=null&&y.topic&&(O.switchView("viewer"),y.chapter&&ce.selectTopic(y.topic,y.chapter))}function Ie(){v(he,!0),v(Ne,""),v(me,[],!0),v(de,-1)}function _t(y){(y.metaKey||y.ctrlKey)&&y.key==="n"&&(y.preventDefault(),Me()),(y.metaKey||y.ctrlKey)&&y.key==="k"&&(y.preventDefault(),Ie()),(y.metaKey||y.ctrlKey)&&y.shiftKey&&y.key==="S"&&(y.preventDefault(),re()),y.key==="Escape"&&r(he)?v(he,!1):y.key==="Escape"&&r(C)?v(C,!1):y.key==="Escape"&&r(m)?v(m,null):y.key==="Escape"&&O.panelOpen&&O.closePanel()}let ht=q(()=>{var y;return((y=L.active)==null?void 0:y.messages)||[]}),Et=q(()=>L.active&&L.active.messages.length>0),Qe=q(()=>{var y;return!r(w)&&(!r(d)||!((y=r(i)[r(d)])!=null&&y.available))});const At=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var Ot=Jg();fa("keydown",Ko,_t);var Ht=Q(Ot),fr=l(Ht);{var Ft=y=>{var ee=sg();oe("click",ee,()=>{v(x,!1)}),c(y,ee)};k(fr,y=>{r(le)&&r(x)&&y(Ft)})}var Pr=h(fr,2),jn=l(Pr);{let y=q(()=>r(le)?!0:r(x));Uf(jn,{get conversations(){return L.conversations},get activeId(){return L.activeId},get open(){return r(y)},get version(){return r(P)},onNewChat:()=>{Me(),r(le)&&v(x,!1)},onSelect:ee=>{ge(ee),r(le)&&v(x,!1)},onDelete:dt,onOpenSearch:Ie})}var vt=h(Pr,2),$e=l(vt),Te=l($e),Nt=l(Te);{var Yt=y=>{$f(y,{size:18})},ar=y=>{Cf(y,{size:18})};k(Nt,y=>{r(x)?y(Yt):y(ar,-1)})}var kr=h(Te,2),pr=l(kr),ft=l(pr);Jo(ft,{size:12});var jt=h(pr,2),Ze=l(jt);Fs(Ze,{size:12});var et=h($e,2),qt=l(et),or=l(qt);Oa(or,{size:14});var Qt=h(qt,2),tr=l(Qt);on(tr,{size:14});var dr=h(Qt,2),Or=l(dr);yf(Or,{size:14});var St=h(dr,2),Ge=l(St);_f(Ge,{size:14});var pt=h(St,2),zt=l(pt);{var Xt=y=>{var ee=ig(),Le=Q(ee);Hr(Le,{size:12,class:"animate-spin"}),c(y,ee)},Cr=y=>{var ee=lg(),Le=Q(ee);Ka(Le,{size:12}),c(y,ee)},ct=y=>{var ee=cg(),Le=h(Q(ee),2),Xe=l(Le),Ke=h(Le,2);{var ut=pe=>{var ie=dg(),ze=h(Q(ie),2),wt=l(ze);I(()=>A(wt,r(u))),c(pe,ie)};k(Ke,pe=>{r(u)&&pe(ut)})}I(()=>A(Xe,r(d))),c(y,ee)};k(zt,y=>{r(w)?y(Xt):r(Qe)?y(Cr,1):y(ct,-1)})}var $t=h(zt,2);Tf($t,{size:12});var Rt=h(et,2),rr=l(Rt);{var Kt=y=>{var ee=ug(),Le=l(ee);og(Le,{get viewer(){return ce},get company(){return O.selectedCompany},onAskAI:Ct,onTopicChange:(Xe,Ke)=>O.setViewerTopic(Xe,Ke)}),c(y,ee)},Sr=y=>{var ee=fg(),Le=Q(ee),Xe=l(Le);{var Ke=ze=>{Wp(ze,{get messages(){return r(ht)},get isLoading(){return r(a)},get scrollTrigger(){return r(g)},get selectedCompany(){return O.selectedCompany},onSend:De,onStop:Ce,onRegenerate:He,onExport:Je,onOpenData:Z,onOpenEvidence:Fe,onCompanySelect:qe,get inputText(){return r(n)},set inputText(wt){v(n,wt,!0)}})},ut=ze=>{Zf(ze,{onSend:De,onCompanySelect:qe,get inputText(){return r(n)},set inputText(wt){v(n,wt,!0)}})};k(Xe,ze=>{r(Et)?ze(Ke):ze(ut,-1)})}var pe=h(Le,2);{var ie=ze=>{var wt=vg(),Zt=l(wt);yx(Zt,{get mode(){return O.panelMode},get company(){return O.selectedCompany},get data(){return O.panelData},onClose:()=>{v(ve,!1),O.closePanel()},onTopicChange:(sr,nr)=>O.setViewerTopic(sr,nr),onFullscreen:()=>{v(ve,!r(ve))},get isFullscreen(){return r(ve)}}),I(()=>Wo(wt,`width: ${r(Pe)??""}; min-width: 360px; ${r(ve)?"":"max-width: 75vw;"}`)),c(ze,wt)};k(pe,ze=>{!r(le)&&O.panelOpen&&ze(ie)})}c(y,ee)};k(rr,y=>{O.activeView==="viewer"?y(Kt):y(Sr,-1)})}var Jr=h(Ht,2);{var gr=y=>{var ee=Fg(),Le=l(ee),Xe=l(Le),Ke=l(Xe),ut=h(l(Ke),2),pe=l(ut);io(pe,{size:18});var ie=h(Xe,2),ze=l(ie);ke(ze,21,()=>Object.entries(r(i)),Se,(J,te)=>{var We=q(()=>el(r(te),2));let Re=()=>r(We)[0],tt=()=>r(We)[1];const Bt=q(()=>Re()===r(d)),It=q(()=>r(R)===Re()),Vt=q(()=>tt().auth==="api_key"),Nr=q(()=>tt().auth==="cli"),Fn=q(()=>r(b)[Re()]||[]),Xn=q(()=>r(S)[Re()]);var _a=Vg(),wa=l(_a),Ba=l(wa),Ua=h(Ba,2),Ga=l(Ua),Ro=l(Ga),is=l(Ro),Cd=h(Ro,2);{var Sd=lr=>{var Dr=pg();c(lr,Dr)};k(Cd,lr=>{r(Bt)&&lr(Sd)})}var $d=h(Ga,2),Md=l($d),Td=h(Ua,2),zd=l(Td);{var Ed=lr=>{Mo(lr,{size:16,class:"text-dl-success"})},Ad=lr=>{var Dr=mg(),Jn=Q(Dr);Gi(Jn,{size:14,class:"text-amber-400"}),c(lr,Dr)},Id=lr=>{var Dr=xg(),Jn=Q(Dr);Ka(Jn,{size:14,class:"text-amber-400"}),c(lr,Dr)},Pd=lr=>{var Dr=hg(),Jn=Q(Dr);Af(Jn,{size:14,class:"text-dl-text-dim"}),c(lr,Dr)};k(zd,lr=>{tt().available?lr(Ed):r(Vt)?lr(Ad,1):r(Nr)&&Re()==="codex"&&r(xe).installed?lr(Id,2):r(Nr)&&!tt().available&&lr(Pd,3)})}var Nd=h(wa,2);{var Ld=lr=>{var Dr=jg(),Jn=Q(Dr);{var Od=Wt=>{var vr=bg(),$r=l(vr),jr=l($r),sn=h($r,2),Lr=l(sn),Qr=h(Lr,2),Qn=l(Qr);{var Zn=Lt=>{Hr(Lt,{size:12,class:"animate-spin"})},Zr=Lt=>{Gi(Lt,{size:12})};k(Qn,Lt=>{r(V)?Lt(Zn):Lt(Zr,-1)})}var mn=h(sn,2);{var er=Lt=>{var en=gg(),Mr=l(en);Ka(Mr,{size:12}),c(Lt,en)};k(mn,Lt=>{r(E)==="error"&&Lt(er)})}I(Lt=>{A(jr,tt().envKey?`환경변수 ${tt().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),Dn(Lr,"placeholder",Re()==="openai"?"sk-...":Re()==="claude"?"sk-ant-...":"API Key"),Qr.disabled=Lt},[()=>!r(M).trim()||r(V)]),oe("keydown",Lr,Lt=>{Lt.key==="Enter"&&mt()}),za(Lr,()=>r(M),Lt=>v(M,Lt)),oe("click",Qr,mt),c(Wt,vr)};k(Jn,Wt=>{r(Vt)&&!tt().available&&Wt(Od)})}var si=h(Jn,2);{var Rd=Wt=>{var vr=wg(),$r=l(vr),jr=l($r);Mo(jr,{size:13,class:"text-dl-success"});var sn=h($r,2),Lr=l(sn),Qr=h(Lr,2);{var Qn=Zr=>{var mn=_g(),er=l(mn);{var Lt=Mr=>{Hr(Mr,{size:10,class:"animate-spin"})},en=Mr=>{var $n=aa("변경");c(Mr,$n)};k(er,Mr=>{r(V)?Mr(Lt):Mr(en,-1)})}I(()=>mn.disabled=r(V)),oe("click",mn,mt),c(Zr,mn)},Zn=q(()=>r(M).trim());k(Qr,Zr=>{r(Zn)&&Zr(Qn)})}oe("keydown",Lr,Zr=>{Zr.key==="Enter"&&mt()}),za(Lr,()=>r(M),Zr=>v(M,Zr)),c(Wt,vr)};k(si,Wt=>{r(Vt)&&tt().available&&Wt(Rd)})}var ii=h(si,2);{var Dd=Wt=>{var vr=yg(),$r=h(l(vr),2),jr=l($r);To(jr,{size:14});var sn=h(jr,2);Ui(sn,{size:10,class:"ml-auto"}),c(Wt,vr)},jd=Wt=>{var vr=kg(),$r=l(vr),jr=l($r);Ka(jr,{size:14}),c(Wt,vr)};k(ii,Wt=>{Re()==="ollama"&&!r(s).installed?Wt(Dd):Re()==="ollama"&&r(s).installed&&!r(s).running&&Wt(jd,1)})}var li=h(ii,2);{var Vd=Wt=>{var vr=Mg(),$r=l(vr);{var jr=Qr=>{var Qn=$g(),Zn=Q(Qn),Zr=l(Zn),mn=h(Zn,2),er=l(mn);{var Lt=tn=>{var Mn=Cg();c(tn,Mn)};k(er,tn=>{r(xe).installed||tn(Lt)})}var en=h(er,2),Mr=l(en),$n=l(Mr),ya=h(mn,2);{var fo=tn=>{var Mn=Sg(),ea=l(Mn);I(()=>A(ea,r(xe).loginStatus)),c(tn,Mn)};k(ya,tn=>{r(xe).loginStatus&&tn(fo)})}var po=h(ya,2),Fr=l(po);Ka(Fr,{size:12,class:"text-amber-400 flex-shrink-0"}),I(()=>{A(Zr,r(xe).installed?"Codex CLI가 설치되었지만 로그인이 필요합니다":"Codex CLI 설치가 필요합니다"),A($n,r(xe).installed?"1.":"2.")}),c(Qr,Qn)};k($r,Qr=>{Re()==="codex"&&Qr(jr)})}var sn=h($r,2),Lr=l(sn);I(()=>A(Lr,r(xe).installed?"로그인 완료 후 새로고침하세요":"설치 완료 후 새로고침하세요")),c(Wt,vr)};k(li,Wt=>{r(Nr)&&!tt().available&&Wt(Vd)})}var di=h(li,2);{var Fd=Wt=>{var vr=Tg(),$r=l(vr),jr=l($r),sn=l(jr);Mo(sn,{size:13,class:"text-dl-success"});var Lr=h(jr,2),Qr=l(Lr);kf(Qr,{size:11}),oe("click",Lr,$),c(Wt,vr)};k(di,Wt=>{Re()==="codex"&&tt().available&&Wt(Fd)})}var qd=h(di,2);{var Bd=Wt=>{var vr=Dg(),$r=l(vr),jr=h(l($r),2);{var sn=er=>{Hr(er,{size:12,class:"animate-spin text-dl-text-dim"})};k(jr,er=>{r(Xn)&&er(sn)})}var Lr=h($r,2);{var Qr=er=>{var Lt=zg(),en=l(Lt);Hr(en,{size:14,class:"animate-spin"}),c(er,Lt)},Qn=er=>{var Lt=Ag();ke(Lt,21,()=>r(Fn),Se,(en,Mr)=>{var $n=Eg(),ya=l($n),fo=h(ya);{var po=Fr=>{qs(Fr,{size:10,class:"inline ml-1"})};k(fo,Fr=>{r(Mr)===r(u)&&r(Bt)&&Fr(po)})}I(Fr=>{je($n,1,Fr),A(ya,`${r(Mr)??""} `)},[()=>Ut(Jt("px-3 py-1.5 rounded-lg text-[11px] border transition-all",r(Mr)===r(u)&&r(Bt)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),oe("click",$n,()=>{Re()!==r(d)&&Pt(Re()),Ye(r(Mr))}),c(en,$n)}),c(er,Lt)},Zn=er=>{var Lt=Ig();c(er,Lt)};k(Lr,er=>{r(Xn)&&r(Fn).length===0?er(Qr):r(Fn).length>0?er(Qn,1):er(Zn,-1)})}var Zr=h(Lr,2);{var mn=er=>{var Lt=Rg(),en=l(Lt),Mr=h(l(en),2),$n=h(l(Mr));Ui($n,{size:9});var ya=h(en,2);{var fo=Fr=>{var tn=Pg(),Mn=l(tn),ea=l(Mn),mo=l(ea);Hr(mo,{size:12,class:"animate-spin text-dl-primary-light"});var ls=h(ea,2),Do=h(Mn,2),qn=l(Do),xn=h(Do,2),ds=l(xn);I(()=>{Wo(qn,`width: ${r(z)??""}%`),A(ds,r(ne))}),oe("click",ls,U),c(Fr,tn)},po=Fr=>{var tn=Og(),Mn=Q(tn),ea=l(Mn),mo=h(ea,2),ls=l(mo);To(ls,{size:12});var Do=h(Mn,2);ke(Do,21,()=>At,Se,(qn,xn)=>{const ds=q(()=>r(Fn).some(Ha=>Ha===r(xn).name||Ha===r(xn).name.split(":")[0]));var ci=be(),Ud=Q(ci);{var Gd=Ha=>{var cs=Lg(),ui=l(cs),vi=l(ui),fi=l(vi),Hd=l(fi),pi=h(fi,2),Kd=l(pi),Wd=h(pi,2);{var Yd=us=>{var xi=Ng(),tc=l(xi);I(()=>A(tc,r(xn).tag)),c(us,xi)};k(Wd,us=>{r(xn).tag&&us(Yd)})}var Xd=h(vi,2),Jd=l(Xd),Qd=h(ui,2),mi=l(Qd),Zd=l(mi),ec=h(mi,2);To(ec,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),I(()=>{A(Hd,r(xn).name),A(Kd,r(xn).size),A(Jd,r(xn).desc),A(Zd,`${r(xn).gb??""} GB`)}),oe("click",cs,()=>{v(F,r(xn).name,!0),Y()}),c(Ha,cs)};k(Ud,Ha=>{r(ds)||Ha(Gd)})}c(qn,ci)}),I(qn=>mo.disabled=qn,[()=>!r(F).trim()]),oe("keydown",ea,qn=>{qn.key==="Enter"&&Y()}),za(ea,()=>r(F),qn=>v(F,qn)),oe("click",mo,Y),c(Fr,tn)};k(ya,Fr=>{r(se)?Fr(fo):Fr(po,-1)})}c(er,Lt)};k(Zr,er=>{Re()==="ollama"&&er(mn)})}c(Wt,vr)};k(qd,Wt=>{(tt().available||r(Vt)||r(Nr))&&Wt(Bd)})}c(lr,Dr)};k(Nd,lr=>{(r(It)||r(Bt))&&lr(Ld)})}I((lr,Dr)=>{je(_a,1,lr),je(Ba,1,Dr),A(is,tt().label||Re()),A(Md,tt().desc||"")},[()=>Ut(Jt("rounded-xl border transition-all",r(Bt)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>Ut(Jt("w-2.5 h-2.5 rounded-full flex-shrink-0",tt().available?"bg-dl-success":r(Vt)?"bg-amber-400":"bg-dl-text-dim"))]),oe("click",wa,()=>{tt().available||r(Vt)?Re()===r(d)?ot(Re()):Pt(Re()):ot(Re())}),c(J,_a)});var wt=h(ie,2),Zt=l(wt),sr=l(Zt);{var nr=J=>{var te=aa();I(()=>{var We;return A(te,`현재: ${(((We=r(i)[r(d)])==null?void 0:We.label)||r(d))??""} / ${r(u)??""}`)}),c(J,te)},ur=J=>{var te=aa();I(()=>{var We;return A(te,`현재: ${(((We=r(i)[r(d)])==null?void 0:We.label)||r(d))??""}`)}),c(J,te)};k(sr,J=>{r(d)&&r(u)?J(nr):r(d)&&J(ur,1)})}var ir=h(Zt,2);pa(Le,J=>v(X,J),()=>r(X)),oe("click",ee,J=>{J.target===J.currentTarget&&v(C,!1)}),oe("click",ut,()=>v(C,!1)),oe("click",ir,()=>v(C,!1)),c(y,ee)};k(Jr,y=>{r(C)&&y(gr)})}var Rr=h(Jr,2);{var Vn=y=>{var ee=qg(),Le=l(ee),Xe=h(l(Le),4),Ke=l(Xe),ut=h(Ke,2);pa(Le,pe=>v(H,pe),()=>r(H)),oe("click",ee,pe=>{pe.target===pe.currentTarget&&v(m,null)}),oe("click",Ke,()=>v(m,null)),oe("click",ut,we),c(y,ee)};k(Rr,y=>{r(m)&&y(Vn)})}var Wn=h(Rr,2);{var pn=y=>{const ee=q(()=>O.recentCompanies||[]);var Le=Yg(),Xe=l(Le),Ke=l(Xe),ut=l(Ke);Oa(ut,{size:18,class:"text-dl-text-dim flex-shrink-0"});var pe=h(ut,2);pa(pe,J=>v(ue,J),()=>r(ue));var ie=h(Ke,2),ze=l(ie);{var wt=J=>{var te=Ug(),We=h(Q(te),2);ke(We,17,()=>r(me),Se,(Re,tt,Bt)=>{var It=Bg(),Vt=l(It),Nr=l(Vt),Fn=h(Vt,2),Xn=l(Fn),_a=l(Xn),wa=h(Xn,2),Ba=l(wa),Ua=h(Fn,2),Ga=h(l(Ua),2);on(Ga,{size:14,class:"text-dl-text-dim"}),I((Ro,is)=>{je(It,1,Ro),A(Nr,is),A(_a,r(tt).corpName),A(Ba,`${r(tt).stockCode??""} · ${(r(tt).market||"")??""}${r(tt).sector?` · ${r(tt).sector}`:""}`)},[()=>Ut(Jt("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",Bt===r(de)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(r(tt).corpName||"?").charAt(0)]),oe("click",It,()=>{v(he,!1),v(Ne,""),v(me,[],!0),v(de,-1),qe(r(tt))}),fa("mouseenter",It,()=>{v(de,Bt,!0)}),c(Re,It)}),c(J,te)},Zt=J=>{var te=Hg(),We=h(Q(te),2);ke(We,17,()=>r(ee),Se,(Re,tt,Bt)=>{var It=Gg(),Vt=l(It),Nr=l(Vt),Fn=h(Vt,2),Xn=l(Fn),_a=l(Xn),wa=h(Xn,2),Ba=l(wa);I((Ua,Ga)=>{je(It,1,Ua),A(Nr,Ga),A(_a,r(tt).corpName),A(Ba,`${r(tt).stockCode??""} · ${(r(tt).market||"")??""}`)},[()=>Ut(Jt("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",Bt===r(de)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(r(tt).corpName||"?").charAt(0)]),oe("click",It,()=>{v(he,!1),v(Ne,""),v(de,-1),qe(r(tt))}),fa("mouseenter",It,()=>{v(de,Bt,!0)}),c(Re,It)}),c(J,te)},sr=q(()=>r(Ne).trim().length===0&&r(ee).length>0),nr=J=>{var te=Kg();c(J,te)},ur=q(()=>r(Ne).trim().length>0),ir=J=>{var te=Wg(),We=l(te);Oa(We,{size:24,class:"mb-2 opacity-40"}),c(J,te)};k(ze,J=>{r(me).length>0?J(wt):r(sr)?J(Zt,1):r(ur)?J(nr,2):J(ir,-1)})}oe("click",Le,J=>{J.target===J.currentTarget&&v(he,!1)}),oe("input",pe,()=>{B&&clearTimeout(B),r(Ne).trim().length>=1?B=setTimeout(async()=>{var J;try{const te=await ed(r(Ne).trim());v(me,((J=te.results)==null?void 0:J.slice(0,8))||[],!0)}catch{v(me,[],!0)}},250):v(me,[],!0)}),oe("keydown",pe,J=>{const te=r(me).length>0?r(me):r(ee);if(J.key==="ArrowDown")J.preventDefault(),v(de,Math.min(r(de)+1,te.length-1),!0);else if(J.key==="ArrowUp")J.preventDefault(),v(de,Math.max(r(de)-1,-1),!0);else if(J.key==="Enter"&&r(de)>=0&&te[r(de)]){J.preventDefault();const We=te[r(de)];v(he,!1),v(Ne,""),v(me,[],!0),v(de,-1),qe(We)}else J.key==="Escape"&&v(he,!1)}),za(pe,()=>r(Ne),J=>v(Ne,J)),c(y,Le)};k(Wn,y=>{r(he)&&y(pn)})}var Yn=h(Wn,2);{var ss=y=>{var ee=Xg(),Le=l(ee),Xe=l(Le),Ke=l(Xe),ut=h(Xe,2),pe=l(ut);io(pe,{size:14}),I(ie=>{je(Le,1,ie),A(Ke,r(_))},[()=>Ut(Jt("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",r(T)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":r(T)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),oe("click",ut,()=>{v(K,!1)}),c(y,ee)};k(Yn,y=>{r(K)&&y(ss)})}I(y=>{je(Pr,1,Ut(r(le)?r(x)?"sidebar-mobile":"hidden":"")),je(pr,1,`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors ${O.activeView==="chat"?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-dim hover:text-dl-text-muted"}`),je(jt,1,`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors ${O.activeView==="viewer"?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-dim hover:text-dl-text-muted"}`),je(pt,1,y)},[()=>Ut(Jt("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",r(w)?"text-dl-text-dim":r(Qe)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),oe("click",Te,re),oe("click",pr,()=>O.switchView("chat")),oe("click",jt,()=>O.switchView("viewer")),oe("click",qt,Ie),oe("click",pt,()=>Dt()),c(e,Ot),yr()}Yr(["click","keydown","input"]);zu(Qg,{target:document.getElementById("app")});
