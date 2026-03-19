const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/ChartRenderer-B5E7I3qo.js","assets/ChartRenderer-DW5VYfwI.css"])))=>i.map(i=>d[i]);
var Au=Object.defineProperty;var hl=t=>{throw TypeError(t)};var Eu=(t,e,r)=>e in t?Au(t,e,{enumerable:!0,configurable:!0,writable:!0,value:r}):t[e]=r;var Mn=(t,e,r)=>Eu(t,typeof e!="symbol"?e+"":e,r),Hs=(t,e,r)=>e.has(t)||hl("Cannot "+r);var oe=(t,e,r)=>(Hs(t,e,"read from private field"),r?r.call(t):e.get(t)),Yt=(t,e,r)=>e.has(t)?hl("Cannot add the same private member more than once"):e instanceof WeakSet?e.add(t):e.set(t,r),Vt=(t,e,r,a)=>(Hs(t,e,"write to private field"),a?a.call(t,r):e.set(t,r),r),Mr=(t,e,r)=>(Hs(t,e,"access private method"),r);(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const o of document.querySelectorAll('link[rel="modulepreload"]'))a(o);new MutationObserver(o=>{for(const i of o)if(i.type==="childList")for(const s of i.addedNodes)s.tagName==="LINK"&&s.rel==="modulepreload"&&a(s)}).observe(document,{childList:!0,subtree:!0});function r(o){const i={};return o.integrity&&(i.integrity=o.integrity),o.referrerPolicy&&(i.referrerPolicy=o.referrerPolicy),o.crossOrigin==="use-credentials"?i.credentials="include":o.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function a(o){if(o.ep)return;o.ep=!0;const i=r(o);fetch(o.href,i)}})();const ni=!1;var Oi=Array.isArray,Nu=Array.prototype.indexOf,xo=Array.prototype.includes,Es=Array.from,Pu=Object.defineProperty,ya=Object.getOwnPropertyDescriptor,ld=Object.getOwnPropertyDescriptors,Lu=Object.prototype,Ou=Array.prototype,Ri=Object.getPrototypeOf,ml=Object.isExtensible;function Ao(t){return typeof t=="function"}const Ru=()=>{};function Du(t){return typeof(t==null?void 0:t.then)=="function"}function ju(t){return t()}function ai(t){for(var e=0;e<t.length;e++)t[e]()}function dd(){var t,e,r=new Promise((a,o)=>{t=a,e=o});return{promise:r,resolve:t,reject:e}}function Di(t,e){if(Array.isArray(t))return t;if(!(Symbol.iterator in t))return Array.from(t);const r=[];for(const a of t)if(r.push(a),r.length===e)break;return r}const Ur=2,Co=4,Ga=8,Ns=1<<24,Ta=16,On=32,Qa=64,oi=128,wn=512,Br=1024,qr=2048,Ln=4096,Qr=8192,Jn=16384,So=32768,ia=65536,xl=1<<17,Fu=1<<18,$o=1<<19,cd=1<<20,Kn=1<<25,Ja=65536,si=1<<21,ji=1<<22,ka=1<<23,Yn=Symbol("$state"),ud=Symbol("legacy props"),Vu=Symbol(""),Ra=new class extends Error{constructor(){super(...arguments);Mn(this,"name","StaleReactionError");Mn(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var od;const fd=!!((od=globalThis.document)!=null&&od.contentType)&&globalThis.document.contentType.includes("xml");function Bu(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function qu(t,e,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function Hu(t){throw new Error("https://svelte.dev/e/effect_in_teardown")}function Uu(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Wu(t){throw new Error("https://svelte.dev/e/effect_orphan")}function Ku(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function Gu(t){throw new Error("https://svelte.dev/e/props_invalid_value")}function Ju(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function Yu(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function Xu(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function Qu(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const Zu=1,ef=2,vd=4,tf=8,rf=16,nf=1,af=2,pd=4,of=8,sf=16,hd=1,lf=2,Ir=Symbol(),md="http://www.w3.org/1999/xhtml",xd="http://www.w3.org/2000/svg",df="http://www.w3.org/1998/Math/MathML",cf="@attach";function uf(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function ff(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function gd(t){return t===this.v}function vf(t,e){return t!=t?e==e:t!==e||t!==null&&typeof t=="object"||typeof t=="function"}function _d(t){return!vf(t,this.v)}let Zo=!1,pf=!1;function hf(){Zo=!0}let Lr=null;function go(t){Lr=t}function Cr(t,e=!1,r){Lr={p:Lr,i:!1,c:null,e:null,s:t,x:null,l:Zo&&!e?{s:null,u:null,$:[]}:null}}function Sr(t){var e=Lr,r=e.e;if(r!==null){e.e=null;for(var a of r)Bd(a)}return e.i=!0,Lr=e.p,{}}function zo(){return!Zo||Lr!==null&&Lr.l===null}let Da=[];function bd(){var t=Da;Da=[],ai(t)}function Pn(t){if(Da.length===0&&!so){var e=Da;queueMicrotask(()=>{e===Da&&bd()})}Da.push(t)}function mf(){for(;Da.length>0;)bd()}function wd(t){var e=Jt;if(e===null)return Gt.f|=ka,t;if((e.f&So)===0&&(e.f&Co)===0)throw t;ga(t,e)}function ga(t,e){for(;e!==null;){if((e.f&oi)!==0){if((e.f&So)===0)throw t;try{e.b.error(t);return}catch(r){t=r}}e=e.parent}throw t}const xf=-7169;function kr(t,e){t.f=t.f&xf|e}function Fi(t){(t.f&wn)!==0||t.deps===null?kr(t,Br):kr(t,Ln)}function yd(t){if(t!==null)for(const e of t)(e.f&Ur)===0||(e.f&Ja)===0||(e.f^=Ja,yd(e.deps))}function kd(t,e,r){(t.f&qr)!==0?e.add(t):(t.f&Ln)!==0&&r.add(t),yd(t.deps),kr(t,Br)}const is=new Set;let Tt=null,_s=null,Vr=null,rn=[],Ps=null,so=!1,_o=null,gf=1;var ha,lo,Va,co,uo,fo,ma,Bn,vo,on,ii,li,di,ci;const nl=class nl{constructor(){Yt(this,on);Mn(this,"id",gf++);Mn(this,"current",new Map);Mn(this,"previous",new Map);Yt(this,ha,new Set);Yt(this,lo,new Set);Yt(this,Va,0);Yt(this,co,0);Yt(this,uo,null);Yt(this,fo,new Set);Yt(this,ma,new Set);Yt(this,Bn,new Map);Mn(this,"is_fork",!1);Yt(this,vo,!1)}skip_effect(e){oe(this,Bn).has(e)||oe(this,Bn).set(e,{d:[],m:[]})}unskip_effect(e){var r=oe(this,Bn).get(e);if(r){oe(this,Bn).delete(e);for(var a of r.d)kr(a,qr),Gn(a);for(a of r.m)kr(a,Ln),Gn(a)}}process(e){var o;rn=[],this.apply();var r=_o=[],a=[];for(const i of e)Mr(this,on,li).call(this,i,r,a);if(_o=null,Mr(this,on,ii).call(this)){Mr(this,on,di).call(this,a),Mr(this,on,di).call(this,r);for(const[i,s]of oe(this,Bn))Md(i,s)}else{_s=this,Tt=null;for(const i of oe(this,ha))i(this);oe(this,ha).clear(),oe(this,Va)===0&&Mr(this,on,ci).call(this),gl(a),gl(r),oe(this,fo).clear(),oe(this,ma).clear(),_s=null,(o=oe(this,uo))==null||o.resolve()}Vr=null}capture(e,r){r!==Ir&&!this.previous.has(e)&&this.previous.set(e,r),(e.f&ka)===0&&(this.current.set(e,e.v),Vr==null||Vr.set(e,e.v))}activate(){Tt=this,this.apply()}deactivate(){Tt===this&&(Tt=null,Vr=null)}flush(){var e;if(rn.length>0)Tt=this,Sd();else if(oe(this,Va)===0&&!this.is_fork){for(const r of oe(this,ha))r(this);oe(this,ha).clear(),Mr(this,on,ci).call(this),(e=oe(this,uo))==null||e.resolve()}this.deactivate()}discard(){for(const e of oe(this,lo))e(this);oe(this,lo).clear()}increment(e){Vt(this,Va,oe(this,Va)+1),e&&Vt(this,co,oe(this,co)+1)}decrement(e){Vt(this,Va,oe(this,Va)-1),e&&Vt(this,co,oe(this,co)-1),!oe(this,vo)&&(Vt(this,vo,!0),Pn(()=>{Vt(this,vo,!1),Mr(this,on,ii).call(this)?rn.length>0&&this.flush():this.revive()}))}revive(){for(const e of oe(this,fo))oe(this,ma).delete(e),kr(e,qr),Gn(e);for(const e of oe(this,ma))kr(e,Ln),Gn(e);this.flush()}oncommit(e){oe(this,ha).add(e)}ondiscard(e){oe(this,lo).add(e)}settled(){return(oe(this,uo)??Vt(this,uo,dd())).promise}static ensure(){if(Tt===null){const e=Tt=new nl;is.add(Tt),so||Pn(()=>{Tt===e&&e.flush()})}return Tt}apply(){}};ha=new WeakMap,lo=new WeakMap,Va=new WeakMap,co=new WeakMap,uo=new WeakMap,fo=new WeakMap,ma=new WeakMap,Bn=new WeakMap,vo=new WeakMap,on=new WeakSet,ii=function(){return this.is_fork||oe(this,co)>0},li=function(e,r,a){e.f^=Br;for(var o=e.first;o!==null;){var i=o.f,s=(i&(On|Qa))!==0,l=s&&(i&Br)!==0,u=(i&Qr)!==0,f=l||oe(this,Bn).has(o);if(!f&&o.fn!==null){s?u||(o.f^=Br):(i&Co)!==0?r.push(o):(i&(Ga|Ns))!==0&&u?a.push(o):rs(o)&&(bo(o),(i&Ta)!==0&&(oe(this,ma).add(o),u&&kr(o,qr)));var p=o.first;if(p!==null){o=p;continue}}for(;o!==null;){var _=o.next;if(_!==null){o=_;break}o=o.parent}}},di=function(e){for(var r=0;r<e.length;r+=1)kd(e[r],oe(this,fo),oe(this,ma))},ci=function(){var i;if(is.size>1){this.previous.clear();var e=Tt,r=Vr,a=!0;for(const s of is){if(s===this){a=!1;continue}const l=[];for(const[f,p]of this.current){if(s.current.has(f))if(a&&p!==s.current.get(f))s.current.set(f,p);else continue;l.push(f)}if(l.length===0)continue;const u=[...s.current.keys()].filter(f=>!this.current.has(f));if(u.length>0){var o=rn;rn=[];const f=new Set,p=new Map;for(const _ of l)$d(_,u,f,p);if(rn.length>0){Tt=s,s.apply();for(const _ of rn)Mr(i=s,on,li).call(i,_,[],[]);s.deactivate()}rn=o}}Tt=e,Vr=r}oe(this,Bn).clear(),is.delete(this)};let oa=nl;function Cd(t){var e=so;so=!0;try{for(var r;;){if(mf(),rn.length===0&&(Tt==null||Tt.flush(),rn.length===0))return Ps=null,r;Sd()}}finally{so=e}}function Sd(){var t=null;try{for(var e=0;rn.length>0;){var r=oa.ensure();if(e++>1e3){var a,o;_f()}r.process(rn),Ca.clear()}}finally{rn=[],Ps=null,_o=null}}function _f(){try{Ku()}catch(t){ga(t,Ps)}}let Tn=null;function gl(t){var e=t.length;if(e!==0){for(var r=0;r<e;){var a=t[r++];if((a.f&(Jn|Qr))===0&&rs(a)&&(Tn=new Set,bo(a),a.deps===null&&a.first===null&&a.nodes===null&&a.teardown===null&&a.ac===null&&Wd(a),(Tn==null?void 0:Tn.size)>0)){Ca.clear();for(const o of Tn){if((o.f&(Jn|Qr))!==0)continue;const i=[o];let s=o.parent;for(;s!==null;)Tn.has(s)&&(Tn.delete(s),i.push(s)),s=s.parent;for(let l=i.length-1;l>=0;l--){const u=i[l];(u.f&(Jn|Qr))===0&&bo(u)}}Tn.clear()}}Tn=null}}function $d(t,e,r,a){if(!r.has(t)&&(r.add(t),t.reactions!==null))for(const o of t.reactions){const i=o.f;(i&Ur)!==0?$d(o,e,r,a):(i&(ji|Ta))!==0&&(i&qr)===0&&zd(o,e,a)&&(kr(o,qr),Gn(o))}}function zd(t,e,r){const a=r.get(t);if(a!==void 0)return a;if(t.deps!==null)for(const o of t.deps){if(xo.call(e,o))return!0;if((o.f&Ur)!==0&&zd(o,e,r))return r.set(o,!0),!0}return r.set(t,!1),!1}function Gn(t){var e=Ps=t,r=e.b;if(r!=null&&r.is_pending&&(t.f&(Co|Ga|Ns))!==0&&(t.f&So)===0){r.defer_effect(t);return}for(;e.parent!==null;){e=e.parent;var a=e.f;if(_o!==null&&e===Jt&&(t.f&Ga)===0)return;if((a&(Qa|On))!==0){if((a&Br)===0)return;e.f^=Br}}rn.push(e)}function Md(t,e){if(!((t.f&On)!==0&&(t.f&Br)!==0)){(t.f&qr)!==0?e.d.push(t):(t.f&Ln)!==0&&e.m.push(t),kr(t,Br);for(var r=t.first;r!==null;)Md(r,e),r=r.next}}function bf(t){let e=0,r=Zn(0),a;return()=>{Hi()&&(n(r),Ui(()=>(e===0&&(a=Ya(()=>t(()=>qo(r)))),e+=1,()=>{Pn(()=>{e-=1,e===0&&(a==null||a(),a=void 0,qo(r))})})))}}var wf=ia|$o;function yf(t,e,r,a){new kf(t,e,r,a)}var gn,Li,qn,Ba,tn,Hn,vn,In,ra,qa,xa,po,ho,mo,na,Is,Er,Cf,Sf,$f,ui,ps,hs,fi;class kf{constructor(e,r,a,o){Yt(this,Er);Mn(this,"parent");Mn(this,"is_pending",!1);Mn(this,"transform_error");Yt(this,gn);Yt(this,Li,null);Yt(this,qn);Yt(this,Ba);Yt(this,tn);Yt(this,Hn,null);Yt(this,vn,null);Yt(this,In,null);Yt(this,ra,null);Yt(this,qa,0);Yt(this,xa,0);Yt(this,po,!1);Yt(this,ho,new Set);Yt(this,mo,new Set);Yt(this,na,null);Yt(this,Is,bf(()=>(Vt(this,na,Zn(oe(this,qa))),()=>{Vt(this,na,null)})));var i;Vt(this,gn,e),Vt(this,qn,r),Vt(this,Ba,s=>{var l=Jt;l.b=this,l.f|=oi,a(s)}),this.parent=Jt.b,this.transform_error=o??((i=this.parent)==null?void 0:i.transform_error)??(s=>s),Vt(this,tn,Za(()=>{Mr(this,Er,ui).call(this)},wf))}defer_effect(e){kd(e,oe(this,ho),oe(this,mo))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!oe(this,qn).pending}update_pending_count(e){Mr(this,Er,fi).call(this,e),Vt(this,qa,oe(this,qa)+e),!(!oe(this,na)||oe(this,po))&&(Vt(this,po,!0),Pn(()=>{Vt(this,po,!1),oe(this,na)&&sa(oe(this,na),oe(this,qa))}))}get_effect_pending(){return oe(this,Is).call(this),n(oe(this,na))}error(e){var r=oe(this,qn).onerror;let a=oe(this,qn).failed;if(!r&&!a)throw e;oe(this,Hn)&&(Hr(oe(this,Hn)),Vt(this,Hn,null)),oe(this,vn)&&(Hr(oe(this,vn)),Vt(this,vn,null)),oe(this,In)&&(Hr(oe(this,In)),Vt(this,In,null));var o=!1,i=!1;const s=()=>{if(o){ff();return}o=!0,i&&Qu(),oe(this,In)!==null&&Ua(oe(this,In),()=>{Vt(this,In,null)}),Mr(this,Er,hs).call(this,()=>{oa.ensure(),Mr(this,Er,ui).call(this)})},l=u=>{try{i=!0,r==null||r(u,s),i=!1}catch(f){ga(f,oe(this,tn)&&oe(this,tn).parent)}a&&Vt(this,In,Mr(this,Er,hs).call(this,()=>{oa.ensure();try{return an(()=>{var f=Jt;f.b=this,f.f|=oi,a(oe(this,gn),()=>u,()=>s)})}catch(f){return ga(f,oe(this,tn).parent),null}}))};Pn(()=>{var u;try{u=this.transform_error(e)}catch(f){ga(f,oe(this,tn)&&oe(this,tn).parent);return}u!==null&&typeof u=="object"&&typeof u.then=="function"?u.then(l,f=>ga(f,oe(this,tn)&&oe(this,tn).parent)):l(u)})}}gn=new WeakMap,Li=new WeakMap,qn=new WeakMap,Ba=new WeakMap,tn=new WeakMap,Hn=new WeakMap,vn=new WeakMap,In=new WeakMap,ra=new WeakMap,qa=new WeakMap,xa=new WeakMap,po=new WeakMap,ho=new WeakMap,mo=new WeakMap,na=new WeakMap,Is=new WeakMap,Er=new WeakSet,Cf=function(){try{Vt(this,Hn,an(()=>oe(this,Ba).call(this,oe(this,gn))))}catch(e){this.error(e)}},Sf=function(e){const r=oe(this,qn).failed;r&&Vt(this,In,an(()=>{r(oe(this,gn),()=>e,()=>()=>{})}))},$f=function(){const e=oe(this,qn).pending;e&&(this.is_pending=!0,Vt(this,vn,an(()=>e(oe(this,gn)))),Pn(()=>{var r=Vt(this,ra,document.createDocumentFragment()),a=Xn();r.append(a),Vt(this,Hn,Mr(this,Er,hs).call(this,()=>(oa.ensure(),an(()=>oe(this,Ba).call(this,a))))),oe(this,xa)===0&&(oe(this,gn).before(r),Vt(this,ra,null),Ua(oe(this,vn),()=>{Vt(this,vn,null)}),Mr(this,Er,ps).call(this))}))},ui=function(){try{if(this.is_pending=this.has_pending_snippet(),Vt(this,xa,0),Vt(this,qa,0),Vt(this,Hn,an(()=>{oe(this,Ba).call(this,oe(this,gn))})),oe(this,xa)>0){var e=Vt(this,ra,document.createDocumentFragment());Gi(oe(this,Hn),e);const r=oe(this,qn).pending;Vt(this,vn,an(()=>r(oe(this,gn))))}else Mr(this,Er,ps).call(this)}catch(r){this.error(r)}},ps=function(){this.is_pending=!1;for(const e of oe(this,ho))kr(e,qr),Gn(e);for(const e of oe(this,mo))kr(e,Ln),Gn(e);oe(this,ho).clear(),oe(this,mo).clear()},hs=function(e){var r=Jt,a=Gt,o=Lr;Cn(oe(this,tn)),kn(oe(this,tn)),go(oe(this,tn).ctx);try{return e()}catch(i){return wd(i),null}finally{Cn(r),kn(a),go(o)}},fi=function(e){var r;if(!this.has_pending_snippet()){this.parent&&Mr(r=this.parent,Er,fi).call(r,e);return}Vt(this,xa,oe(this,xa)+e),oe(this,xa)===0&&(Mr(this,Er,ps).call(this),oe(this,vn)&&Ua(oe(this,vn),()=>{Vt(this,vn,null)}),oe(this,ra)&&(oe(this,gn).before(oe(this,ra)),Vt(this,ra,null)))};function Td(t,e,r,a){const o=zo()?es:Vi;var i=t.filter(_=>!_.settled);if(r.length===0&&i.length===0){a(e.map(o));return}var s=Jt,l=Id(),u=i.length===1?i[0].promise:i.length>1?Promise.all(i.map(_=>_.promise)):null;function f(_){l();try{a(_)}catch(g){(s.f&Jn)===0&&ga(g,s)}bs()}if(r.length===0){u.then(()=>f(e.map(o)));return}function p(){l(),Promise.all(r.map(_=>Mf(_))).then(_=>f([...e.map(o),..._])).catch(_=>ga(_,s))}u?u.then(p):p()}function Id(){var t=Jt,e=Gt,r=Lr,a=Tt;return function(i=!0){Cn(t),kn(e),go(r),i&&(a==null||a.activate())}}function bs(t=!0){Cn(null),kn(null),go(null),t&&(Tt==null||Tt.deactivate())}function zf(){var t=Jt.b,e=Tt,r=t.is_rendered();return t.update_pending_count(1),e.increment(r),()=>{t.update_pending_count(-1),e.decrement(r)}}function es(t){var e=Ur|qr,r=Gt!==null&&(Gt.f&Ur)!==0?Gt:null;return Jt!==null&&(Jt.f|=$o),{ctx:Lr,deps:null,effects:null,equals:gd,f:e,fn:t,reactions:null,rv:0,v:Ir,wv:0,parent:r??Jt,ac:null}}function Mf(t,e,r){Jt===null&&Bu();var o=void 0,i=Zn(Ir),s=!Gt,l=new Map;return Vf(()=>{var g;var u=dd();o=u.promise;try{Promise.resolve(t()).then(u.resolve,u.reject).finally(bs)}catch(w){u.reject(w),bs()}var f=Tt;if(s){var p=zf();(g=l.get(f))==null||g.reject(Ra),l.delete(f),l.set(f,u)}const _=(w,k=void 0)=>{if(f.activate(),k)k!==Ra&&(i.f|=ka,sa(i,k));else{(i.f&ka)!==0&&(i.f^=ka),sa(i,w);for(const[S,b]of l){if(l.delete(S),S===f)break;b.reject(Ra)}}p&&p()};u.promise.then(_,w=>_(null,w||"unknown"))}),Os(()=>{for(const u of l.values())u.reject(Ra)}),new Promise(u=>{function f(p){function _(){p===o?u(i):f(o)}p.then(_,_)}f(o)})}function R(t){const e=es(t);return Jd(e),e}function Vi(t){const e=es(t);return e.equals=_d,e}function Tf(t){var e=t.effects;if(e!==null){t.effects=null;for(var r=0;r<e.length;r+=1)Hr(e[r])}}function If(t){for(var e=t.parent;e!==null;){if((e.f&Ur)===0)return(e.f&Jn)===0?e:null;e=e.parent}return null}function Bi(t){var e,r=Jt;Cn(If(t));try{t.f&=~Ja,Tf(t),e=Zd(t)}finally{Cn(r)}return e}function Ad(t){var e=Bi(t);if(!t.equals(e)&&(t.wv=Xd(),(!(Tt!=null&&Tt.is_fork)||t.deps===null)&&(t.v=e,t.deps===null))){kr(t,Br);return}Sa||(Vr!==null?(Hi()||Tt!=null&&Tt.is_fork)&&Vr.set(t,e):Fi(t))}function Af(t){var e,r;if(t.effects!==null)for(const a of t.effects)(a.teardown||a.ac)&&((e=a.teardown)==null||e.call(a),(r=a.ac)==null||r.abort(Ra),a.teardown=Ru,a.ac=null,Go(a,0),Wi(a))}function Ed(t){if(t.effects!==null)for(const e of t.effects)e.teardown&&bo(e)}let vi=new Set;const Ca=new Map;let Nd=!1;function Zn(t,e){var r={f:0,v:t,reactions:null,equals:gd,rv:0,wv:0};return r}function Z(t,e){const r=Zn(t);return Jd(r),r}function pi(t,e=!1,r=!0){var o;const a=Zn(t);return e||(a.equals=_d),Zo&&r&&Lr!==null&&Lr.l!==null&&((o=Lr.l).s??(o.s=[])).push(a),a}function v(t,e,r=!1){Gt!==null&&(!En||(Gt.f&xl)!==0)&&zo()&&(Gt.f&(Ur|Ta|ji|xl))!==0&&(yn===null||!xo.call(yn,t))&&Xu();let a=r?Ut(e):e;return sa(t,a)}function sa(t,e){if(!t.equals(e)){var r=t.v;Sa?Ca.set(t,e):Ca.set(t,r),t.v=e;var a=oa.ensure();if(a.capture(t,r),(t.f&Ur)!==0){const o=t;(t.f&qr)!==0&&Bi(o),Fi(o)}t.wv=Xd(),Pd(t,qr),zo()&&Jt!==null&&(Jt.f&Br)!==0&&(Jt.f&(On|Qa))===0&&(xn===null?qf([t]):xn.push(t)),!a.is_fork&&vi.size>0&&!Nd&&Ef()}return e}function Ef(){Nd=!1;for(const t of vi)(t.f&Br)!==0&&kr(t,Ln),rs(t)&&bo(t);vi.clear()}function Bo(t,e=1){var r=n(t),a=e===1?r++:r--;return v(t,r),a}function qo(t){v(t,t.v+1)}function Pd(t,e){var r=t.reactions;if(r!==null)for(var a=zo(),o=r.length,i=0;i<o;i++){var s=r[i],l=s.f;if(!(!a&&s===Jt)){var u=(l&qr)===0;if(u&&kr(s,e),(l&Ur)!==0){var f=s;Vr==null||Vr.delete(f),(l&Ja)===0&&(l&wn&&(s.f|=Ja),Pd(f,Ln))}else u&&((l&Ta)!==0&&Tn!==null&&Tn.add(s),Gn(s))}}}function Ut(t){if(typeof t!="object"||t===null||Yn in t)return t;const e=Ri(t);if(e!==Lu&&e!==Ou)return t;var r=new Map,a=Oi(t),o=Z(0),i=Wa,s=l=>{if(Wa===i)return l();var u=Gt,f=Wa;kn(null),yl(i);var p=l();return kn(u),yl(f),p};return a&&r.set("length",Z(t.length)),new Proxy(t,{defineProperty(l,u,f){(!("value"in f)||f.configurable===!1||f.enumerable===!1||f.writable===!1)&&Ju();var p=r.get(u);return p===void 0?s(()=>{var _=Z(f.value);return r.set(u,_),_}):v(p,f.value,!0),!0},deleteProperty(l,u){var f=r.get(u);if(f===void 0){if(u in l){const p=s(()=>Z(Ir));r.set(u,p),qo(o)}}else v(f,Ir),qo(o);return!0},get(l,u,f){var w;if(u===Yn)return t;var p=r.get(u),_=u in l;if(p===void 0&&(!_||(w=ya(l,u))!=null&&w.writable)&&(p=s(()=>{var k=Ut(_?l[u]:Ir),S=Z(k);return S}),r.set(u,p)),p!==void 0){var g=n(p);return g===Ir?void 0:g}return Reflect.get(l,u,f)},getOwnPropertyDescriptor(l,u){var f=Reflect.getOwnPropertyDescriptor(l,u);if(f&&"value"in f){var p=r.get(u);p&&(f.value=n(p))}else if(f===void 0){var _=r.get(u),g=_==null?void 0:_.v;if(_!==void 0&&g!==Ir)return{enumerable:!0,configurable:!0,value:g,writable:!0}}return f},has(l,u){var g;if(u===Yn)return!0;var f=r.get(u),p=f!==void 0&&f.v!==Ir||Reflect.has(l,u);if(f!==void 0||Jt!==null&&(!p||(g=ya(l,u))!=null&&g.writable)){f===void 0&&(f=s(()=>{var w=p?Ut(l[u]):Ir,k=Z(w);return k}),r.set(u,f));var _=n(f);if(_===Ir)return!1}return p},set(l,u,f,p){var P;var _=r.get(u),g=u in l;if(a&&u==="length")for(var w=f;w<_.v;w+=1){var k=r.get(w+"");k!==void 0?v(k,Ir):w in l&&(k=s(()=>Z(Ir)),r.set(w+"",k))}if(_===void 0)(!g||(P=ya(l,u))!=null&&P.writable)&&(_=s(()=>Z(void 0)),v(_,Ut(f)),r.set(u,_));else{g=_.v!==Ir;var S=s(()=>Ut(f));v(_,S)}var b=Reflect.getOwnPropertyDescriptor(l,u);if(b!=null&&b.set&&b.set.call(p,f),!g){if(a&&typeof u=="string"){var C=r.get("length"),z=Number(u);Number.isInteger(z)&&z>=C.v&&v(C,z+1)}qo(o)}return!0},ownKeys(l){n(o);var u=Reflect.ownKeys(l).filter(_=>{var g=r.get(_);return g===void 0||g.v!==Ir});for(var[f,p]of r)p.v!==Ir&&!(f in l)&&u.push(f);return u},setPrototypeOf(){Yu()}})}function _l(t){try{if(t!==null&&typeof t=="object"&&Yn in t)return t[Yn]}catch{}return t}function Nf(t,e){return Object.is(_l(t),_l(e))}var ws,Ld,Od,Rd,Dd;function Pf(){if(ws===void 0){ws=window,Ld=document,Od=/Firefox/.test(navigator.userAgent);var t=Element.prototype,e=Node.prototype,r=Text.prototype;Rd=ya(e,"firstChild").get,Dd=ya(e,"nextSibling").get,ml(t)&&(t.__click=void 0,t.__className=void 0,t.__attributes=null,t.__style=void 0,t.__e=void 0),ml(r)&&(r.__t=void 0)}}function Xn(t=""){return document.createTextNode(t)}function _n(t){return Rd.call(t)}function ts(t){return Dd.call(t)}function d(t,e){return _n(t)}function ae(t,e=!1){{var r=_n(t);return r instanceof Comment&&r.data===""?ts(r):r}}function m(t,e=1,r=!1){let a=t;for(;e--;)a=ts(a);return a}function Lf(t){t.textContent=""}function jd(){return!1}function qi(t,e,r){return document.createElementNS(e??md,t,void 0)}function Of(t,e){if(e){const r=document.body;t.autofocus=!0,Pn(()=>{document.activeElement===r&&t.focus()})}}let bl=!1;function Rf(){bl||(bl=!0,document.addEventListener("reset",t=>{Promise.resolve().then(()=>{var e;if(!t.defaultPrevented)for(const r of t.target.elements)(e=r.__on_r)==null||e.call(r)})},{capture:!0}))}function Ls(t){var e=Gt,r=Jt;kn(null),Cn(null);try{return t()}finally{kn(e),Cn(r)}}function Fd(t,e,r,a=r){t.addEventListener(e,()=>Ls(r));const o=t.__on_r;o?t.__on_r=()=>{o(),a(!0)}:t.__on_r=()=>a(!0),Rf()}function Vd(t){Jt===null&&(Gt===null&&Wu(),Uu()),Sa&&Hu()}function Df(t,e){var r=e.last;r===null?e.last=e.first=t:(r.next=t,t.prev=r,e.last=t)}function Rn(t,e){var r=Jt;r!==null&&(r.f&Qr)!==0&&(t|=Qr);var a={ctx:Lr,deps:null,nodes:null,f:t|qr|wn,first:null,fn:e,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},o=a;if((t&Co)!==0)_o!==null?_o.push(a):Gn(a);else if(e!==null){try{bo(a)}catch(s){throw Hr(a),s}o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&$o)===0&&(o=o.first,(t&Ta)!==0&&(t&ia)!==0&&o!==null&&(o.f|=ia))}if(o!==null&&(o.parent=r,r!==null&&Df(o,r),Gt!==null&&(Gt.f&Ur)!==0&&(t&Qa)===0)){var i=Gt;(i.effects??(i.effects=[])).push(o)}return a}function Hi(){return Gt!==null&&!En}function Os(t){const e=Rn(Ga,null);return kr(e,Br),e.teardown=t,e}function xr(t){Vd();var e=Jt.f,r=!Gt&&(e&On)!==0&&(e&So)===0;if(r){var a=Lr;(a.e??(a.e=[])).push(t)}else return Bd(t)}function Bd(t){return Rn(Co|cd,t)}function jf(t){return Vd(),Rn(Ga|cd,t)}function Ff(t){oa.ensure();const e=Rn(Qa|$o,t);return(r={})=>new Promise(a=>{r.outro?Ua(e,()=>{Hr(e),a(void 0)}):(Hr(e),a(void 0))})}function Rs(t){return Rn(Co,t)}function Vf(t){return Rn(ji|$o,t)}function Ui(t,e=0){return Rn(Ga|e,t)}function A(t,e=[],r=[],a=[]){Td(a,e,r,o=>{Rn(Ga,()=>t(...o.map(n)))})}function Za(t,e=0){var r=Rn(Ta|e,t);return r}function qd(t,e=0){var r=Rn(Ns|e,t);return r}function an(t){return Rn(On|$o,t)}function Hd(t){var e=t.teardown;if(e!==null){const r=Sa,a=Gt;wl(!0),kn(null);try{e.call(null)}finally{wl(r),kn(a)}}}function Wi(t,e=!1){var r=t.first;for(t.first=t.last=null;r!==null;){const o=r.ac;o!==null&&Ls(()=>{o.abort(Ra)});var a=r.next;(r.f&Qa)!==0?r.parent=null:Hr(r,e),r=a}}function Bf(t){for(var e=t.first;e!==null;){var r=e.next;(e.f&On)===0&&Hr(e),e=r}}function Hr(t,e=!0){var r=!1;(e||(t.f&Fu)!==0)&&t.nodes!==null&&t.nodes.end!==null&&(Ud(t.nodes.start,t.nodes.end),r=!0),Wi(t,e&&!r),Go(t,0),kr(t,Jn);var a=t.nodes&&t.nodes.t;if(a!==null)for(const i of a)i.stop();Hd(t);var o=t.parent;o!==null&&o.first!==null&&Wd(t),t.next=t.prev=t.teardown=t.ctx=t.deps=t.fn=t.nodes=t.ac=null}function Ud(t,e){for(;t!==null;){var r=t===e?null:ts(t);t.remove(),t=r}}function Wd(t){var e=t.parent,r=t.prev,a=t.next;r!==null&&(r.next=a),a!==null&&(a.prev=r),e!==null&&(e.first===t&&(e.first=a),e.last===t&&(e.last=r))}function Ua(t,e,r=!0){var a=[];Kd(t,a,!0);var o=()=>{r&&Hr(t),e&&e()},i=a.length;if(i>0){var s=()=>--i||o();for(var l of a)l.out(s)}else o()}function Kd(t,e,r){if((t.f&Qr)===0){t.f^=Qr;var a=t.nodes&&t.nodes.t;if(a!==null)for(const l of a)(l.is_global||r)&&e.push(l);for(var o=t.first;o!==null;){var i=o.next,s=(o.f&ia)!==0||(o.f&On)!==0&&(t.f&Ta)!==0;Kd(o,e,s?r:!1),o=i}}}function Ki(t){Gd(t,!0)}function Gd(t,e){if((t.f&Qr)!==0){t.f^=Qr;for(var r=t.first;r!==null;){var a=r.next,o=(r.f&ia)!==0||(r.f&On)!==0;Gd(r,o?e:!1),r=a}var i=t.nodes&&t.nodes.t;if(i!==null)for(const s of i)(s.is_global||e)&&s.in()}}function Gi(t,e){if(t.nodes)for(var r=t.nodes.start,a=t.nodes.end;r!==null;){var o=r===a?null:ts(r);e.append(r),r=o}}let ms=!1,Sa=!1;function wl(t){Sa=t}let Gt=null,En=!1;function kn(t){Gt=t}let Jt=null;function Cn(t){Jt=t}let yn=null;function Jd(t){Gt!==null&&(yn===null?yn=[t]:yn.push(t))}let nn=null,fn=0,xn=null;function qf(t){xn=t}let Yd=1,ja=0,Wa=ja;function yl(t){Wa=t}function Xd(){return++Yd}function rs(t){var e=t.f;if((e&qr)!==0)return!0;if(e&Ur&&(t.f&=~Ja),(e&Ln)!==0){for(var r=t.deps,a=r.length,o=0;o<a;o++){var i=r[o];if(rs(i)&&Ad(i),i.wv>t.wv)return!0}(e&wn)!==0&&Vr===null&&kr(t,Br)}return!1}function Qd(t,e,r=!0){var a=t.reactions;if(a!==null&&!(yn!==null&&xo.call(yn,t)))for(var o=0;o<a.length;o++){var i=a[o];(i.f&Ur)!==0?Qd(i,e,!1):e===i&&(r?kr(i,qr):(i.f&Br)!==0&&kr(i,Ln),Gn(i))}}function Zd(t){var S;var e=nn,r=fn,a=xn,o=Gt,i=yn,s=Lr,l=En,u=Wa,f=t.f;nn=null,fn=0,xn=null,Gt=(f&(On|Qa))===0?t:null,yn=null,go(t.ctx),En=!1,Wa=++ja,t.ac!==null&&(Ls(()=>{t.ac.abort(Ra)}),t.ac=null);try{t.f|=si;var p=t.fn,_=p();t.f|=So;var g=t.deps,w=Tt==null?void 0:Tt.is_fork;if(nn!==null){var k;if(w||Go(t,fn),g!==null&&fn>0)for(g.length=fn+nn.length,k=0;k<nn.length;k++)g[fn+k]=nn[k];else t.deps=g=nn;if(Hi()&&(t.f&wn)!==0)for(k=fn;k<g.length;k++)((S=g[k]).reactions??(S.reactions=[])).push(t)}else!w&&g!==null&&fn<g.length&&(Go(t,fn),g.length=fn);if(zo()&&xn!==null&&!En&&g!==null&&(t.f&(Ur|Ln|qr))===0)for(k=0;k<xn.length;k++)Qd(xn[k],t);if(o!==null&&o!==t){if(ja++,o.deps!==null)for(let b=0;b<r;b+=1)o.deps[b].rv=ja;if(e!==null)for(const b of e)b.rv=ja;xn!==null&&(a===null?a=xn:a.push(...xn))}return(t.f&ka)!==0&&(t.f^=ka),_}catch(b){return wd(b)}finally{t.f^=si,nn=e,fn=r,xn=a,Gt=o,yn=i,go(s),En=l,Wa=u}}function Hf(t,e){let r=e.reactions;if(r!==null){var a=Nu.call(r,t);if(a!==-1){var o=r.length-1;o===0?r=e.reactions=null:(r[a]=r[o],r.pop())}}if(r===null&&(e.f&Ur)!==0&&(nn===null||!xo.call(nn,e))){var i=e;(i.f&wn)!==0&&(i.f^=wn,i.f&=~Ja),Fi(i),Af(i),Go(i,0)}}function Go(t,e){var r=t.deps;if(r!==null)for(var a=e;a<r.length;a++)Hf(t,r[a])}function bo(t){var e=t.f;if((e&Jn)===0){kr(t,Br);var r=Jt,a=ms;Jt=t,ms=!0;try{(e&(Ta|Ns))!==0?Bf(t):Wi(t),Hd(t);var o=Zd(t);t.teardown=typeof o=="function"?o:null,t.wv=Yd;var i;ni&&pf&&(t.f&qr)!==0&&t.deps}finally{ms=a,Jt=r}}}async function ec(){await Promise.resolve(),Cd()}function n(t){var e=t.f,r=(e&Ur)!==0;if(Gt!==null&&!En){var a=Jt!==null&&(Jt.f&Jn)!==0;if(!a&&(yn===null||!xo.call(yn,t))){var o=Gt.deps;if((Gt.f&si)!==0)t.rv<ja&&(t.rv=ja,nn===null&&o!==null&&o[fn]===t?fn++:nn===null?nn=[t]:nn.push(t));else{(Gt.deps??(Gt.deps=[])).push(t);var i=t.reactions;i===null?t.reactions=[Gt]:xo.call(i,Gt)||i.push(Gt)}}}if(Sa&&Ca.has(t))return Ca.get(t);if(r){var s=t;if(Sa){var l=s.v;return((s.f&Br)===0&&s.reactions!==null||rc(s))&&(l=Bi(s)),Ca.set(s,l),l}var u=(s.f&wn)===0&&!En&&Gt!==null&&(ms||(Gt.f&wn)!==0),f=(s.f&So)===0;rs(s)&&(u&&(s.f|=wn),Ad(s)),u&&!f&&(Ed(s),tc(s))}if(Vr!=null&&Vr.has(t))return Vr.get(t);if((t.f&ka)!==0)throw t.v;return t.v}function tc(t){if(t.f|=wn,t.deps!==null)for(const e of t.deps)(e.reactions??(e.reactions=[])).push(t),(e.f&Ur)!==0&&(e.f&wn)===0&&(Ed(e),tc(e))}function rc(t){if(t.v===Ir)return!0;if(t.deps===null)return!1;for(const e of t.deps)if(Ca.has(e)||(e.f&Ur)!==0&&rc(e))return!0;return!1}function Ya(t){var e=En;try{return En=!0,t()}finally{En=e}}function La(t){if(!(typeof t!="object"||!t||t instanceof EventTarget)){if(Yn in t)hi(t);else if(!Array.isArray(t))for(let e in t){const r=t[e];typeof r=="object"&&r&&Yn in r&&hi(r)}}}function hi(t,e=new Set){if(typeof t=="object"&&t!==null&&!(t instanceof EventTarget)&&!e.has(t)){e.add(t),t instanceof Date&&t.getTime();for(let a in t)try{hi(t[a],e)}catch{}const r=Ri(t);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const a=ld(r);for(let o in a){const i=a[o].get;if(i)try{i.call(t)}catch{}}}}}function Uf(t){return t.endsWith("capture")&&t!=="gotpointercapture"&&t!=="lostpointercapture"}const Wf=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function Kf(t){return Wf.includes(t)}const Gf={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function Jf(t){return t=t.toLowerCase(),Gf[t]??t}const Yf=["touchstart","touchmove"];function Xf(t){return Yf.includes(t)}const Fa=Symbol("events"),nc=new Set,mi=new Set;function ac(t,e,r,a={}){function o(i){if(a.capture||xi.call(e,i),!i.cancelBubble)return Ls(()=>r==null?void 0:r.call(this,i))}return t.startsWith("pointer")||t.startsWith("touch")||t==="wheel"?Pn(()=>{e.addEventListener(t,o,a)}):e.addEventListener(t,o,a),o}function bn(t,e,r,a,o){var i={capture:a,passive:o},s=ac(t,e,r,i);(e===document.body||e===window||e===document||e instanceof HTMLMediaElement)&&Os(()=>{e.removeEventListener(t,s,i)})}function ve(t,e,r){(e[Fa]??(e[Fa]={}))[t]=r}function Or(t){for(var e=0;e<t.length;e++)nc.add(t[e]);for(var r of mi)r(t)}let kl=null;function xi(t){var b,C;var e=this,r=e.ownerDocument,a=t.type,o=((b=t.composedPath)==null?void 0:b.call(t))||[],i=o[0]||t.target;kl=t;var s=0,l=kl===t&&t[Fa];if(l){var u=o.indexOf(l);if(u!==-1&&(e===document||e===window)){t[Fa]=e;return}var f=o.indexOf(e);if(f===-1)return;u<=f&&(s=u)}if(i=o[s]||t.target,i!==e){Pu(t,"currentTarget",{configurable:!0,get(){return i||r}});var p=Gt,_=Jt;kn(null),Cn(null);try{for(var g,w=[];i!==null;){var k=i.assignedSlot||i.parentNode||i.host||null;try{var S=(C=i[Fa])==null?void 0:C[a];S!=null&&(!i.disabled||t.target===i)&&S.call(i,t)}catch(z){g?w.push(z):g=z}if(t.cancelBubble||k===e||k===null)break;i=k}if(g){for(let z of w)queueMicrotask(()=>{throw z});throw g}}finally{t[Fa]=e,delete t.currentTarget,kn(p),Cn(_)}}}var sd;const Us=((sd=globalThis==null?void 0:globalThis.window)==null?void 0:sd.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:t=>t});function Qf(t){return(Us==null?void 0:Us.createHTML(t))??t}function oc(t){var e=qi("template");return e.innerHTML=Qf(t.replaceAll("<!>","<!---->")),e.content}function $a(t,e){var r=Jt;r.nodes===null&&(r.nodes={start:t,end:e,a:null,t:null})}function h(t,e){var r=(e&hd)!==0,a=(e&lf)!==0,o,i=!t.startsWith("<!>");return()=>{o===void 0&&(o=oc(i?t:"<!>"+t),r||(o=_n(o)));var s=a||Od?document.importNode(o,!0):o.cloneNode(!0);if(r){var l=_n(s),u=s.lastChild;$a(l,u)}else $a(s,s);return s}}function Zf(t,e,r="svg"){var a=!t.startsWith("<!>"),o=(e&hd)!==0,i=`<${r}>${a?t:"<!>"+t}</${r}>`,s;return()=>{if(!s){var l=oc(i),u=_n(l);if(o)for(s=document.createDocumentFragment();_n(u);)s.appendChild(_n(u));else s=_n(u)}var f=s.cloneNode(!0);if(o){var p=_n(f),_=f.lastChild;$a(p,_)}else $a(f,f);return f}}function ns(t,e){return Zf(t,e,"svg")}function Wn(t=""){{var e=Xn(t+"");return $a(e,e),e}}function be(){var t=document.createDocumentFragment(),e=document.createComment(""),r=Xn();return t.append(e,r),$a(e,r),t}function c(t,e){t!==null&&t.before(e)}function I(t,e){var r=e==null?"":typeof e=="object"?`${e}`:e;r!==(t.__t??(t.__t=t.nodeValue))&&(t.__t=r,t.nodeValue=`${r}`)}function ev(t,e){return tv(t,e)}const ls=new Map;function tv(t,{target:e,anchor:r,props:a={},events:o,context:i,intro:s=!0,transformError:l}){Pf();var u=void 0,f=Ff(()=>{var p=r??e.appendChild(Xn());yf(p,{pending:()=>{}},w=>{Cr({});var k=Lr;i&&(k.c=i),o&&(a.$$events=o),u=t(w,a)||{},Sr()},l);var _=new Set,g=w=>{for(var k=0;k<w.length;k++){var S=w[k];if(!_.has(S)){_.add(S);var b=Xf(S);for(const P of[e,document]){var C=ls.get(P);C===void 0&&(C=new Map,ls.set(P,C));var z=C.get(S);z===void 0?(P.addEventListener(S,xi,{passive:b}),C.set(S,1)):C.set(S,z+1)}}}};return g(Es(nc)),mi.add(g),()=>{var b;for(var w of _)for(const C of[e,document]){var k=ls.get(C),S=k.get(w);--S==0?(C.removeEventListener(w,xi),k.delete(w),k.size===0&&ls.delete(C)):k.set(w,S)}mi.delete(g),p!==r&&((b=p.parentNode)==null||b.removeChild(p))}});return rv.set(u,f),u}let rv=new WeakMap;var An,Un,pn,Ha,Xo,Qo,As;class as{constructor(e,r=!0){Mn(this,"anchor");Yt(this,An,new Map);Yt(this,Un,new Map);Yt(this,pn,new Map);Yt(this,Ha,new Set);Yt(this,Xo,!0);Yt(this,Qo,e=>{if(oe(this,An).has(e)){var r=oe(this,An).get(e),a=oe(this,Un).get(r);if(a)Ki(a),oe(this,Ha).delete(r);else{var o=oe(this,pn).get(r);o&&(o.effect.f&Qr)===0&&(oe(this,Un).set(r,o.effect),oe(this,pn).delete(r),o.fragment.lastChild.remove(),this.anchor.before(o.fragment),a=o.effect)}for(const[i,s]of oe(this,An)){if(oe(this,An).delete(i),i===e)break;const l=oe(this,pn).get(s);l&&(Hr(l.effect),oe(this,pn).delete(s))}for(const[i,s]of oe(this,Un)){if(i===r||oe(this,Ha).has(i)||(s.f&Qr)!==0)continue;const l=()=>{if(Array.from(oe(this,An).values()).includes(i)){var f=document.createDocumentFragment();Gi(s,f),f.append(Xn()),oe(this,pn).set(i,{effect:s,fragment:f})}else Hr(s);oe(this,Ha).delete(i),oe(this,Un).delete(i)};oe(this,Xo)||!a?(oe(this,Ha).add(i),Ua(s,l,!1)):l()}}});Yt(this,As,e=>{oe(this,An).delete(e);const r=Array.from(oe(this,An).values());for(const[a,o]of oe(this,pn))r.includes(a)||(Hr(o.effect),oe(this,pn).delete(a))});this.anchor=e,Vt(this,Xo,r)}ensure(e,r){var a=Tt,o=jd();if(r&&!oe(this,Un).has(e)&&!oe(this,pn).has(e))if(o){var i=document.createDocumentFragment(),s=Xn();i.append(s),oe(this,pn).set(e,{effect:an(()=>r(s)),fragment:i})}else oe(this,Un).set(e,an(()=>r(this.anchor)));if(oe(this,An).set(a,e),o){for(const[l,u]of oe(this,Un))l===e?a.unskip_effect(u):a.skip_effect(u);for(const[l,u]of oe(this,pn))l===e?a.unskip_effect(u.effect):a.skip_effect(u.effect);a.oncommit(oe(this,Qo)),a.ondiscard(oe(this,As))}else oe(this,Qo).call(this,a)}}An=new WeakMap,Un=new WeakMap,pn=new WeakMap,Ha=new WeakMap,Xo=new WeakMap,Qo=new WeakMap,As=new WeakMap;const nv=0,Cl=1,av=2;function gi(t,e,r,a,o){var i=zo(),s=Ir,l=i?Zn(s):pi(s,!1,!1),u=i?Zn(s):pi(s,!1,!1),f=new as(t);Za(()=>{var p=e(),_=!1;if(Du(p)){var g=Id(),w=!1;const k=S=>{if(!_){w=!0,g(!1),oa.ensure();try{S()}finally{bs(!1),so||Cd()}}};p.then(S=>{k(()=>{sa(l,S),f.ensure(Cl,a&&(b=>a(b,l)))})},S=>{k(()=>{if(sa(u,S),f.ensure(av,o&&(b=>o(b,u))),!o)throw u.v})}),Pn(()=>{w||k(()=>{f.ensure(nv,r)})})}else sa(l,p),f.ensure(Cl,a&&(k=>a(k,l)));return()=>{_=!0}})}function $(t,e,r=!1){var a=new as(t),o=r?ia:0;function i(s,l){a.ensure(s,l)}Za(()=>{var s=!1;e((l,u=0)=>{s=!0,i(u,l)}),s||i(-1,null)},o)}function $e(t,e){return e}function ov(t,e,r){for(var a=[],o=e.length,i,s=e.length,l=0;l<o;l++){let _=e[l];Ua(_,()=>{if(i){if(i.pending.delete(_),i.done.add(_),i.pending.size===0){var g=t.outrogroups;_i(t,Es(i.done)),g.delete(i),g.size===0&&(t.outrogroups=null)}}else s-=1},!1)}if(s===0){var u=a.length===0&&r!==null;if(u){var f=r,p=f.parentNode;Lf(p),p.append(f),t.items.clear()}_i(t,e,!u)}else i={pending:new Set(e),done:new Set},(t.outrogroups??(t.outrogroups=new Set)).add(i)}function _i(t,e,r=!0){var a;if(t.pending.size>0){a=new Set;for(const s of t.pending.values())for(const l of s)a.add(t.items.get(l).e)}for(var o=0;o<e.length;o++){var i=e[o];if(a!=null&&a.has(i)){i.f|=Kn;const s=document.createDocumentFragment();Gi(i,s)}else Hr(e[o],r)}}var Sl;function Ce(t,e,r,a,o,i=null){var s=t,l=new Map,u=(e&vd)!==0;if(u){var f=t;s=f.appendChild(Xn())}var p=null,_=Vi(()=>{var P=r();return Oi(P)?P:P==null?[]:Es(P)}),g,w=new Map,k=!0;function S(P){(z.effect.f&Jn)===0&&(z.pending.delete(P),z.fallback=p,sv(z,g,s,e,a),p!==null&&(g.length===0?(p.f&Kn)===0?Ki(p):(p.f^=Kn,jo(p,null,s)):Ua(p,()=>{p=null})))}function b(P){z.pending.delete(P)}var C=Za(()=>{g=n(_);for(var P=g.length,E=new Set,ee=Tt,se=jd(),j=0;j<P;j+=1){var T=g[j],G=a(T,j),K=k?null:l.get(G);K?(K.v&&sa(K.v,T),K.i&&sa(K.i,j),se&&ee.unskip_effect(K.e)):(K=iv(l,k?s:Sl??(Sl=Xn()),T,G,j,o,e,r),k||(K.e.f|=Kn),l.set(G,K)),E.add(G)}if(P===0&&i&&!p&&(k?p=an(()=>i(s)):(p=an(()=>i(Sl??(Sl=Xn()))),p.f|=Kn)),P>E.size&&qu(),!k)if(w.set(ee,E),se){for(const[ie,U]of l)E.has(ie)||ee.skip_effect(U.e);ee.oncommit(S),ee.ondiscard(b)}else S(ee);n(_)}),z={effect:C,items:l,pending:w,outrogroups:null,fallback:p};k=!1}function Eo(t){for(;t!==null&&(t.f&On)===0;)t=t.next;return t}function sv(t,e,r,a,o){var K,ie,U,we,B,J,le,X,O;var i=(a&tf)!==0,s=e.length,l=t.items,u=Eo(t.effect.first),f,p=null,_,g=[],w=[],k,S,b,C;if(i)for(C=0;C<s;C+=1)k=e[C],S=o(k,C),b=l.get(S).e,(b.f&Kn)===0&&((ie=(K=b.nodes)==null?void 0:K.a)==null||ie.measure(),(_??(_=new Set)).add(b));for(C=0;C<s;C+=1){if(k=e[C],S=o(k,C),b=l.get(S).e,t.outrogroups!==null)for(const W of t.outrogroups)W.pending.delete(b),W.done.delete(b);if((b.f&Kn)!==0)if(b.f^=Kn,b===u)jo(b,null,r);else{var z=p?p.next:u;b===t.effect.last&&(t.effect.last=b.prev),b.prev&&(b.prev.next=b.next),b.next&&(b.next.prev=b.prev),fa(t,p,b),fa(t,b,z),jo(b,z,r),p=b,g=[],w=[],u=Eo(p.next);continue}if((b.f&Qr)!==0&&(Ki(b),i&&((we=(U=b.nodes)==null?void 0:U.a)==null||we.unfix(),(_??(_=new Set)).delete(b))),b!==u){if(f!==void 0&&f.has(b)){if(g.length<w.length){var P=w[0],E;p=P.prev;var ee=g[0],se=g[g.length-1];for(E=0;E<g.length;E+=1)jo(g[E],P,r);for(E=0;E<w.length;E+=1)f.delete(w[E]);fa(t,ee.prev,se.next),fa(t,p,ee),fa(t,se,P),u=P,p=se,C-=1,g=[],w=[]}else f.delete(b),jo(b,u,r),fa(t,b.prev,b.next),fa(t,b,p===null?t.effect.first:p.next),fa(t,p,b),p=b;continue}for(g=[],w=[];u!==null&&u!==b;)(f??(f=new Set)).add(u),w.push(u),u=Eo(u.next);if(u===null)continue}(b.f&Kn)===0&&g.push(b),p=b,u=Eo(b.next)}if(t.outrogroups!==null){for(const W of t.outrogroups)W.pending.size===0&&(_i(t,Es(W.done)),(B=t.outrogroups)==null||B.delete(W));t.outrogroups.size===0&&(t.outrogroups=null)}if(u!==null||f!==void 0){var j=[];if(f!==void 0)for(b of f)(b.f&Qr)===0&&j.push(b);for(;u!==null;)(u.f&Qr)===0&&u!==t.fallback&&j.push(u),u=Eo(u.next);var T=j.length;if(T>0){var G=(a&vd)!==0&&s===0?r:null;if(i){for(C=0;C<T;C+=1)(le=(J=j[C].nodes)==null?void 0:J.a)==null||le.measure();for(C=0;C<T;C+=1)(O=(X=j[C].nodes)==null?void 0:X.a)==null||O.fix()}ov(t,j,G)}}i&&Pn(()=>{var W,F;if(_!==void 0)for(b of _)(F=(W=b.nodes)==null?void 0:W.a)==null||F.apply()})}function iv(t,e,r,a,o,i,s,l){var u=(s&Zu)!==0?(s&rf)===0?pi(r,!1,!1):Zn(r):null,f=(s&ef)!==0?Zn(o):null;return{v:u,i:f,e:an(()=>(i(e,u??r,f??o,l),()=>{t.delete(a)}))}}function jo(t,e,r){if(t.nodes)for(var a=t.nodes.start,o=t.nodes.end,i=e&&(e.f&Kn)===0?e.nodes.start:r;a!==null;){var s=ts(a);if(i.before(a),a===o)return;a=s}}function fa(t,e,r){e===null?t.effect.first=r:e.next=r,r===null?t.effect.last=e:r.prev=e}function Nn(t,e,r=!1,a=!1,o=!1){var i=t,s="";A(()=>{var l=Jt;if(s!==(s=e()??"")&&(l.nodes!==null&&(Ud(l.nodes.start,l.nodes.end),l.nodes=null),s!=="")){var u=r?xd:a?df:void 0,f=qi(r?"svg":a?"math":"template",u);f.innerHTML=s;var p=r||a?f:f.content;if($a(_n(p),p.lastChild),r||a)for(;_n(p);)i.before(_n(p));else i.before(p)}})}function it(t,e,r,a,o){var l;var i=(l=e.$$slots)==null?void 0:l[r],s=!1;i===!0&&(i=e.children,s=!0),i===void 0||i(t,s?()=>a:a)}function bi(t,e,...r){var a=new as(t);Za(()=>{const o=e()??null;a.ensure(o,o&&(i=>o(i,...r)))},ia)}function wo(t,e,r){var a=new as(t);Za(()=>{var o=e()??null;a.ensure(o,o&&(i=>r(i,o)))},ia)}function lv(t,e,r,a,o,i){var s=null,l=t,u=new as(l,!1);Za(()=>{const f=e()||null;var p=xd;if(f===null){u.ensure(null,null);return}return u.ensure(f,_=>{if(f){if(s=qi(f,p),$a(s,s),a){var g=s.appendChild(Xn());a(s,g)}Jt.nodes.end=s,_.before(s)}}),()=>{}},ia),Os(()=>{})}function dv(t,e){var r=void 0,a;qd(()=>{r!==(r=e())&&(a&&(Hr(a),a=null),r&&(a=an(()=>{Rs(()=>r(t))})))})}function sc(t){var e,r,a="";if(typeof t=="string"||typeof t=="number")a+=t;else if(typeof t=="object")if(Array.isArray(t)){var o=t.length;for(e=0;e<o;e++)t[e]&&(r=sc(t[e]))&&(a&&(a+=" "),a+=r)}else for(r in t)t[r]&&(a&&(a+=" "),a+=r);return a}function ic(){for(var t,e,r=0,a="",o=arguments.length;r<o;r++)(t=arguments[r])&&(e=sc(t))&&(a&&(a+=" "),a+=e);return a}function ur(t){return typeof t=="object"?ic(t):t??""}const $l=[...` 	
\r\f \v\uFEFF`];function cv(t,e,r){var a=t==null?"":""+t;if(e&&(a=a?a+" "+e:e),r){for(var o of Object.keys(r))if(r[o])a=a?a+" "+o:o;else if(a.length)for(var i=o.length,s=0;(s=a.indexOf(o,s))>=0;){var l=s+i;(s===0||$l.includes(a[s-1]))&&(l===a.length||$l.includes(a[l]))?a=(s===0?"":a.substring(0,s))+a.substring(l+1):s=l}}return a===""?null:a}function zl(t,e=!1){var r=e?" !important;":";",a="";for(var o of Object.keys(t)){var i=t[o];i!=null&&i!==""&&(a+=" "+o+": "+i+r)}return a}function Ws(t){return t[0]!=="-"||t[1]!=="-"?t.toLowerCase():t}function uv(t,e){if(e){var r="",a,o;if(Array.isArray(e)?(a=e[0],o=e[1]):a=e,t){t=String(t).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var i=!1,s=0,l=!1,u=[];a&&u.push(...Object.keys(a).map(Ws)),o&&u.push(...Object.keys(o).map(Ws));var f=0,p=-1;const S=t.length;for(var _=0;_<S;_++){var g=t[_];if(l?g==="/"&&t[_-1]==="*"&&(l=!1):i?i===g&&(i=!1):g==="/"&&t[_+1]==="*"?l=!0:g==='"'||g==="'"?i=g:g==="("?s++:g===")"&&s--,!l&&i===!1&&s===0){if(g===":"&&p===-1)p=_;else if(g===";"||_===S-1){if(p!==-1){var w=Ws(t.substring(f,p).trim());if(!u.includes(w)){g!==";"&&_++;var k=t.substring(f,_).trim();r+=" "+k+";"}}f=_+1,p=-1}}}}return a&&(r+=zl(a)),o&&(r+=zl(o,!0)),r=r.trim(),r===""?null:r}return t==null?null:String(t)}function Xe(t,e,r,a,o,i){var s=t.__className;if(s!==r||s===void 0){var l=cv(r,a,i);l==null?t.removeAttribute("class"):e?t.className=l:t.setAttribute("class",l),t.__className=r}else if(i&&o!==i)for(var u in i){var f=!!i[u];(o==null||f!==!!o[u])&&t.classList.toggle(u,f)}return i}function Ks(t,e={},r,a){for(var o in r){var i=r[o];e[o]!==i&&(r[o]==null?t.style.removeProperty(o):t.style.setProperty(o,i,a))}}function yo(t,e,r,a){var o=t.__style;if(o!==e){var i=uv(e,a);i==null?t.removeAttribute("style"):t.style.cssText=i,t.__style=e}else a&&(Array.isArray(a)?(Ks(t,r==null?void 0:r[0],a[0]),Ks(t,r==null?void 0:r[1],a[1],"important")):Ks(t,r,a));return a}function ys(t,e,r=!1){if(t.multiple){if(e==null)return;if(!Oi(e))return uf();for(var a of t.options)a.selected=e.includes(Ho(a));return}for(a of t.options){var o=Ho(a);if(Nf(o,e)){a.selected=!0;return}}(!r||e!==void 0)&&(t.selectedIndex=-1)}function lc(t){var e=new MutationObserver(()=>{ys(t,t.__value)});e.observe(t,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Os(()=>{e.disconnect()})}function Ml(t,e,r=e){var a=new WeakSet,o=!0;Fd(t,"change",i=>{var s=i?"[selected]":":checked",l;if(t.multiple)l=[].map.call(t.querySelectorAll(s),Ho);else{var u=t.querySelector(s)??t.querySelector("option:not([disabled])");l=u&&Ho(u)}r(l),Tt!==null&&a.add(Tt)}),Rs(()=>{var i=e();if(t===document.activeElement){var s=_s??Tt;if(a.has(s))return}if(ys(t,i,o),o&&i===void 0){var l=t.querySelector(":checked");l!==null&&(i=Ho(l),r(i))}t.__value=i,o=!1}),lc(t)}function Ho(t){return"__value"in t?t.__value:t.value}const No=Symbol("class"),Po=Symbol("style"),dc=Symbol("is custom element"),cc=Symbol("is html"),fv=fd?"option":"OPTION",vv=fd?"select":"SELECT";function pv(t,e){e?t.hasAttribute("selected")||t.setAttribute("selected",""):t.removeAttribute("selected")}function ar(t,e,r,a){var o=uc(t);o[e]!==(o[e]=r)&&(e==="loading"&&(t[Vu]=r),r==null?t.removeAttribute(e):typeof r!="string"&&fc(t).includes(e)?t[e]=r:t.setAttribute(e,r))}function hv(t,e,r,a,o=!1,i=!1){var s=uc(t),l=s[dc],u=!s[cc],f=e||{},p=t.nodeName===fv;for(var _ in e)_ in r||(r[_]=null);r.class?r.class=ur(r.class):r[No]&&(r.class=null),r[Po]&&(r.style??(r.style=null));var g=fc(t);for(const P in r){let E=r[P];if(p&&P==="value"&&E==null){t.value=t.__value="",f[P]=E;continue}if(P==="class"){var w=t.namespaceURI==="http://www.w3.org/1999/xhtml";Xe(t,w,E,a,e==null?void 0:e[No],r[No]),f[P]=E,f[No]=r[No];continue}if(P==="style"){yo(t,E,e==null?void 0:e[Po],r[Po]),f[P]=E,f[Po]=r[Po];continue}var k=f[P];if(!(E===k&&!(E===void 0&&t.hasAttribute(P)))){f[P]=E;var S=P[0]+P[1];if(S!=="$$")if(S==="on"){const ee={},se="$$"+P;let j=P.slice(2);var b=Kf(j);if(Uf(j)&&(j=j.slice(0,-7),ee.capture=!0),!b&&k){if(E!=null)continue;t.removeEventListener(j,f[se],ee),f[se]=null}if(b)ve(j,t,E),Or([j]);else if(E!=null){let T=function(G){f[P].call(this,G)};f[se]=ac(j,t,T,ee)}}else if(P==="style")ar(t,P,E);else if(P==="autofocus")Of(t,!!E);else if(!l&&(P==="__value"||P==="value"&&E!=null))t.value=t.__value=E;else if(P==="selected"&&p)pv(t,E);else{var C=P;u||(C=Jf(C));var z=C==="defaultValue"||C==="defaultChecked";if(E==null&&!l&&!z)if(s[P]=null,C==="value"||C==="checked"){let ee=t;const se=e===void 0;if(C==="value"){let j=ee.defaultValue;ee.removeAttribute(C),ee.defaultValue=j,ee.value=ee.__value=se?j:null}else{let j=ee.defaultChecked;ee.removeAttribute(C),ee.defaultChecked=j,ee.checked=se?j:!1}}else t.removeAttribute(P);else z||g.includes(C)&&(l||typeof E!="string")?(t[C]=E,C in s&&(s[C]=Ir)):typeof E!="function"&&ar(t,C,E)}}}return f}function ks(t,e,r=[],a=[],o=[],i,s=!1,l=!1){Td(o,r,a,u=>{var f=void 0,p={},_=t.nodeName===vv,g=!1;if(qd(()=>{var k=e(...u.map(n)),S=hv(t,f,k,i,s,l);g&&_&&"value"in k&&ys(t,k.value);for(let C of Object.getOwnPropertySymbols(p))k[C]||Hr(p[C]);for(let C of Object.getOwnPropertySymbols(k)){var b=k[C];C.description===cf&&(!f||b!==f[C])&&(p[C]&&Hr(p[C]),p[C]=an(()=>dv(t,()=>b))),S[C]=b}f=S}),_){var w=t;Rs(()=>{ys(w,f.value,!0),lc(w)})}g=!0})}function uc(t){return t.__attributes??(t.__attributes={[dc]:t.nodeName.includes("-"),[cc]:t.namespaceURI===md})}var Tl=new Map;function fc(t){var e=t.getAttribute("is")||t.nodeName,r=Tl.get(e);if(r)return r;Tl.set(e,r=[]);for(var a,o=t,i=Element.prototype;i!==o;){a=ld(o);for(var s in a)a[s].set&&r.push(s);o=Ri(o)}return r}function _a(t,e,r=e){var a=new WeakSet;Fd(t,"input",async o=>{var i=o?t.defaultValue:t.value;if(i=Gs(t)?Js(i):i,r(i),Tt!==null&&a.add(Tt),await ec(),i!==(i=e())){var s=t.selectionStart,l=t.selectionEnd,u=t.value.length;if(t.value=i??"",l!==null){var f=t.value.length;s===l&&l===u&&f>u?(t.selectionStart=f,t.selectionEnd=f):(t.selectionStart=s,t.selectionEnd=Math.min(l,f))}}}),Ya(e)==null&&t.value&&(r(Gs(t)?Js(t.value):t.value),Tt!==null&&a.add(Tt)),Ui(()=>{var o=e();if(t===document.activeElement){var i=_s??Tt;if(a.has(i))return}Gs(t)&&o===Js(t.value)||t.type==="date"&&!o&&!t.value||o!==t.value&&(t.value=o??"")})}function Gs(t){var e=t.type;return e==="number"||e==="range"}function Js(t){return t===""?null:+t}function Il(t,e){return t===e||(t==null?void 0:t[Yn])===e}function Qn(t={},e,r,a){return Rs(()=>{var o,i;return Ui(()=>{o=i,i=[],Ya(()=>{t!==r(...i)&&(e(t,...i),o&&Il(r(...o),t)&&e(null,...o))})}),()=>{Pn(()=>{i&&Il(r(...i),t)&&e(null,...i)})}}),t}function mv(t=!1){const e=Lr,r=e.l.u;if(!r)return;let a=()=>La(e.s);if(t){let o=0,i={};const s=es(()=>{let l=!1;const u=e.s;for(const f in u)u[f]!==i[f]&&(i[f]=u[f],l=!0);return l&&o++,o});a=()=>n(s)}r.b.length&&jf(()=>{Al(e,a),ai(r.b)}),xr(()=>{const o=Ya(()=>r.m.map(ju));return()=>{for(const i of o)typeof i=="function"&&i()}}),r.a.length&&xr(()=>{Al(e,a),ai(r.a)})}function Al(t,e){if(t.l.s)for(const r of t.l.s)n(r);e()}let ds=!1;function xv(t){var e=ds;try{return ds=!1,[t(),ds]}finally{ds=e}}const gv={get(t,e){if(!t.exclude.includes(e))return t.props[e]},set(t,e){return!1},getOwnPropertyDescriptor(t,e){if(!t.exclude.includes(e)&&e in t.props)return{enumerable:!0,configurable:!0,value:t.props[e]}},has(t,e){return t.exclude.includes(e)?!1:e in t.props},ownKeys(t){return Reflect.ownKeys(t.props).filter(e=>!t.exclude.includes(e))}};function _v(t,e,r){return new Proxy({props:t,exclude:e},gv)}const bv={get(t,e){if(!t.exclude.includes(e))return n(t.version),e in t.special?t.special[e]():t.props[e]},set(t,e,r){if(!(e in t.special)){var a=Jt;try{Cn(t.parent_effect),t.special[e]=Pe({get[e](){return t.props[e]}},e,pd)}finally{Cn(a)}}return t.special[e](r),Bo(t.version),!0},getOwnPropertyDescriptor(t,e){if(!t.exclude.includes(e)&&e in t.props)return{enumerable:!0,configurable:!0,value:t.props[e]}},deleteProperty(t,e){return t.exclude.includes(e)||(t.exclude.push(e),Bo(t.version)),!0},has(t,e){return t.exclude.includes(e)?!1:e in t.props},ownKeys(t){return Reflect.ownKeys(t.props).filter(e=>!t.exclude.includes(e))}};function st(t,e){return new Proxy({props:t,exclude:e,special:{},version:Zn(0),parent_effect:Jt},bv)}const wv={get(t,e){let r=t.props.length;for(;r--;){let a=t.props[r];if(Ao(a)&&(a=a()),typeof a=="object"&&a!==null&&e in a)return a[e]}},set(t,e,r){let a=t.props.length;for(;a--;){let o=t.props[a];Ao(o)&&(o=o());const i=ya(o,e);if(i&&i.set)return i.set(r),!0}return!1},getOwnPropertyDescriptor(t,e){let r=t.props.length;for(;r--;){let a=t.props[r];if(Ao(a)&&(a=a()),typeof a=="object"&&a!==null&&e in a){const o=ya(a,e);return o&&!o.configurable&&(o.configurable=!0),o}}},has(t,e){if(e===Yn||e===ud)return!1;for(let r of t.props)if(Ao(r)&&(r=r()),r!=null&&e in r)return!0;return!1},ownKeys(t){const e=[];for(let r of t.props)if(Ao(r)&&(r=r()),!!r){for(const a in r)e.includes(a)||e.push(a);for(const a of Object.getOwnPropertySymbols(r))e.includes(a)||e.push(a)}return e}};function ut(...t){return new Proxy({props:t},wv)}function Pe(t,e,r,a){var P;var o=!Zo||(r&af)!==0,i=(r&of)!==0,s=(r&sf)!==0,l=a,u=!0,f=()=>(u&&(u=!1,l=s?Ya(a):a),l),p;if(i){var _=Yn in t||ud in t;p=((P=ya(t,e))==null?void 0:P.set)??(_&&e in t?E=>t[e]=E:void 0)}var g,w=!1;i?[g,w]=xv(()=>t[e]):g=t[e],g===void 0&&a!==void 0&&(g=f(),p&&(o&&Gu(),p(g)));var k;if(o?k=()=>{var E=t[e];return E===void 0?f():(u=!0,E)}:k=()=>{var E=t[e];return E!==void 0&&(l=void 0),E===void 0?l:E},o&&(r&pd)===0)return k;if(p){var S=t.$$legacy;return(function(E,ee){return arguments.length>0?((!o||!ee||S||w)&&p(ee?k():E),E):k()})}var b=!1,C=((r&nf)!==0?es:Vi)(()=>(b=!1,k()));i&&n(C);var z=Jt;return(function(E,ee){if(arguments.length>0){const se=ee?n(C):o&&i?Ut(E):E;return v(C,se),b=!0,l!==void 0&&(l=se),E}return Sa&&b||(z.f&Jn)!==0?C.v:n(C)})}const yv="5";var id;typeof window<"u"&&((id=window.__svelte??(window.__svelte={})).v??(id.v=new Set)).add(yv);const Nr="";async function kv(){const t=await fetch(`${Nr}/api/status`);if(!t.ok)throw new Error("상태 확인 실패");return t.json()}async function Cv(t,e=null,r=null){const a={provider:t};e&&(a.model=e),r&&(a.api_key=r);const o=await fetch(`${Nr}/api/provider/validate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!o.ok)throw new Error("설정 실패");return o.json()}async function Sv(t){const e=await fetch(`${Nr}/api/models/${encodeURIComponent(t)}`);return e.ok?e.json():{models:[]}}function $v(t,{onProgress:e,onDone:r,onError:a}){const o=new AbortController;return fetch(`${Nr}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:t}),signal:o.signal}).then(async i=>{if(!i.ok){a==null||a("다운로드 실패");return}const s=i.body.getReader(),l=new TextDecoder;let u="";for(;;){const{done:f,value:p}=await s.read();if(f)break;u+=l.decode(p,{stream:!0});const _=u.split(`
`);u=_.pop()||"";for(const g of _)if(g.startsWith("data:"))try{const w=JSON.parse(g.slice(5).trim());w.total&&w.completed!==void 0?e==null||e({total:w.total,completed:w.completed,status:w.status}):w.status&&(e==null||e({status:w.status}))}catch{}}r==null||r()}).catch(i=>{i.name!=="AbortError"&&(a==null||a(i.message))}),{abort:()=>o.abort()}}async function zv(){const t=await fetch(`${Nr}/api/codex/logout`,{method:"POST"});if(!t.ok)throw new Error("Codex 로그아웃 실패");return t.json()}async function Mv(t,e=null,r=null){let a=`${Nr}/api/export/excel/${encodeURIComponent(t)}`;const o=new URLSearchParams;r?o.set("template_id",r):e&&e.length>0&&o.set("modules",e.join(","));const i=o.toString();i&&(a+=`?${i}`);const s=await fetch(a);if(!s.ok){const g=await s.json().catch(()=>({}));throw new Error(g.detail||"Excel 다운로드 실패")}const l=await s.blob(),f=(s.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),p=f?decodeURIComponent(f[1]):`${t}.xlsx`,_=document.createElement("a");return _.href=URL.createObjectURL(l),_.download=p,_.click(),URL.revokeObjectURL(_.href),p}async function Ji(t){const e=await fetch(`${Nr}/api/search?q=${encodeURIComponent(t)}`);if(!e.ok)throw new Error("검색 실패");return e.json()}async function Tv(t,e){const r=await fetch(`${Nr}/api/company/${t}/show/${encodeURIComponent(e)}/all`);if(!r.ok)throw new Error("company topic 일괄 조회 실패");return r.json()}async function Iv(t){const e=await fetch(`${Nr}/api/company/${t}/sections`);if(!e.ok)throw new Error("sections 조회 실패");return e.json()}async function Av(t){const e=await fetch(`${Nr}/api/company/${t}/toc`);if(!e.ok)throw new Error("목차 조회 실패");return e.json()}async function Ev(t,e,r=null){const a=r?`?period=${encodeURIComponent(r)}`:"",o=await fetch(`${Nr}/api/company/${t}/viewer/${encodeURIComponent(e)}${a}`);if(!o.ok)throw new Error("viewer 조회 실패");return o.json()}async function Nv(t,e){const r=await fetch(`${Nr}/api/company/${t}/diff/${encodeURIComponent(e)}/summary`);if(!r.ok)throw new Error("diff summary 조회 실패");return r.json()}async function vc(t,e,r,a){const o=new URLSearchParams({from:r,to:a}),i=await fetch(`${Nr}/api/company/${t}/diff/${encodeURIComponent(e)}?${o}`);if(!i.ok)throw new Error("topic diff 조회 실패");return i.json()}async function Pv(t,e){const r=new URLSearchParams({q:e}),a=await fetch(`${Nr}/api/company/${encodeURIComponent(t)}/search?${r}`);if(!a.ok)throw new Error("검색 실패");return a.json()}async function Lv(t){const e=await fetch(`${Nr}/api/company/${encodeURIComponent(t)}/searchIndex`);if(!e.ok)throw new Error("검색 인덱스 조회 실패");return e.json()}async function Ov(t){const e=await fetch(`${Nr}/api/company/${encodeURIComponent(t)}/insights`);if(!e.ok)throw new Error("인사이트 조회 실패");return e.json()}async function Rv(t){const e=await fetch(`${Nr}/api/company/${encodeURIComponent(t)}/network`);if(!e.ok)throw new Error("네트워크 조회 실패");return e.json()}function Dv(t,e,{onContext:r,onChunk:a,onDone:o,onError:i}){const s=new AbortController;return fetch(`${Nr}/api/company/${encodeURIComponent(t)}/summary/${encodeURIComponent(e)}`,{signal:s.signal}).then(async l=>{if(!l.ok){i==null||i("요약 생성 실패");return}const u=l.body.getReader(),f=new TextDecoder;let p="",_=null;for(;;){const{done:g,value:w}=await u.read();if(g)break;p+=f.decode(w,{stream:!0});const k=p.split(`
`);p=k.pop()||"";for(const S of k)if(S.startsWith("event:"))_=S.slice(6).trim();else if(S.startsWith("data:")&&_){try{const b=JSON.parse(S.slice(5).trim());_==="context"?r==null||r(b):_==="chunk"?a==null||a(b.text):_==="error"?i==null||i(b.error):_==="done"&&(o==null||o())}catch{}_=null}}o==null||o()}).catch(l=>{l.name!=="AbortError"&&(i==null||i(l.message))}),{abort:()=>s.abort()}}function jv(t,e,r={},{onMeta:a,onSnapshot:o,onContext:i,onSystemPrompt:s,onToolCall:l,onToolResult:u,onChart:f,onChunk:p,onDone:_,onError:g,onViewerNavigate:w},k=null){const S={question:e,stream:!0,...r};t&&(S.company=t),k&&k.length>0&&(S.history=k);const b=new AbortController;return fetch(`${Nr}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(S),signal:b.signal}).then(async C=>{if(!C.ok){const j=await C.json().catch(()=>({}));g==null||g(j.detail||"스트리밍 실패");return}const z=C.body.getReader(),P=new TextDecoder;let E="",ee=!1,se=null;for(;;){const{done:j,value:T}=await z.read();if(j)break;E+=P.decode(T,{stream:!0});const G=E.split(`
`);E=G.pop()||"";for(const K of G)if(K.startsWith("event:"))se=K.slice(6).trim();else if(K.startsWith("data:")&&se){const ie=K.slice(5).trim();try{const U=JSON.parse(ie);se==="meta"?a==null||a(U):se==="snapshot"?o==null||o(U):se==="context"?i==null||i(U):se==="system_prompt"?s==null||s(U):se==="tool_call"?l==null||l(U):se==="tool_result"?u==null||u(U):se==="chunk"?p==null||p(U.text):se==="chart"?f==null||f(U):se==="viewer_navigate"?w==null||w(U):se==="error"?g==null||g(U.error,U.action,U.detail):se==="done"&&(ee||(ee=!0,_==null||_()))}catch{}se=null}}ee||(ee=!0,_==null||_())}).catch(C=>{C.name!=="AbortError"&&(g==null||g(C.message))}),{abort:()=>b.abort()}}const Fv=(t,e)=>{const r=new Array(t.length+e.length);for(let a=0;a<t.length;a++)r[a]=t[a];for(let a=0;a<e.length;a++)r[t.length+a]=e[a];return r},Vv=(t,e)=>({classGroupId:t,validator:e}),pc=(t=new Map,e=null,r)=>({nextPart:t,validators:e,classGroupId:r}),Cs="-",El=[],Bv="arbitrary..",qv=t=>{const e=Uv(t),{conflictingClassGroups:r,conflictingClassGroupModifiers:a}=t;return{getClassGroupId:s=>{if(s.startsWith("[")&&s.endsWith("]"))return Hv(s);const l=s.split(Cs),u=l[0]===""&&l.length>1?1:0;return hc(l,u,e)},getConflictingClassGroupIds:(s,l)=>{if(l){const u=a[s],f=r[s];return u?f?Fv(f,u):u:f||El}return r[s]||El}}},hc=(t,e,r)=>{if(t.length-e===0)return r.classGroupId;const o=t[e],i=r.nextPart.get(o);if(i){const f=hc(t,e+1,i);if(f)return f}const s=r.validators;if(s===null)return;const l=e===0?t.join(Cs):t.slice(e).join(Cs),u=s.length;for(let f=0;f<u;f++){const p=s[f];if(p.validator(l))return p.classGroupId}},Hv=t=>t.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const e=t.slice(1,-1),r=e.indexOf(":"),a=e.slice(0,r);return a?Bv+a:void 0})(),Uv=t=>{const{theme:e,classGroups:r}=t;return Wv(r,e)},Wv=(t,e)=>{const r=pc();for(const a in t){const o=t[a];Yi(o,r,a,e)}return r},Yi=(t,e,r,a)=>{const o=t.length;for(let i=0;i<o;i++){const s=t[i];Kv(s,e,r,a)}},Kv=(t,e,r,a)=>{if(typeof t=="string"){Gv(t,e,r);return}if(typeof t=="function"){Jv(t,e,r,a);return}Yv(t,e,r,a)},Gv=(t,e,r)=>{const a=t===""?e:mc(e,t);a.classGroupId=r},Jv=(t,e,r,a)=>{if(Xv(t)){Yi(t(a),e,r,a);return}e.validators===null&&(e.validators=[]),e.validators.push(Vv(r,t))},Yv=(t,e,r,a)=>{const o=Object.entries(t),i=o.length;for(let s=0;s<i;s++){const[l,u]=o[s];Yi(u,mc(e,l),r,a)}},mc=(t,e)=>{let r=t;const a=e.split(Cs),o=a.length;for(let i=0;i<o;i++){const s=a[i];let l=r.nextPart.get(s);l||(l=pc(),r.nextPart.set(s,l)),r=l}return r},Xv=t=>"isThemeGetter"in t&&t.isThemeGetter===!0,Qv=t=>{if(t<1)return{get:()=>{},set:()=>{}};let e=0,r=Object.create(null),a=Object.create(null);const o=(i,s)=>{r[i]=s,e++,e>t&&(e=0,a=r,r=Object.create(null))};return{get(i){let s=r[i];if(s!==void 0)return s;if((s=a[i])!==void 0)return o(i,s),s},set(i,s){i in r?r[i]=s:o(i,s)}}},wi="!",Nl=":",Zv=[],Pl=(t,e,r,a,o)=>({modifiers:t,hasImportantModifier:e,baseClassName:r,maybePostfixModifierPosition:a,isExternal:o}),ep=t=>{const{prefix:e,experimentalParseClassName:r}=t;let a=o=>{const i=[];let s=0,l=0,u=0,f;const p=o.length;for(let S=0;S<p;S++){const b=o[S];if(s===0&&l===0){if(b===Nl){i.push(o.slice(u,S)),u=S+1;continue}if(b==="/"){f=S;continue}}b==="["?s++:b==="]"?s--:b==="("?l++:b===")"&&l--}const _=i.length===0?o:o.slice(u);let g=_,w=!1;_.endsWith(wi)?(g=_.slice(0,-1),w=!0):_.startsWith(wi)&&(g=_.slice(1),w=!0);const k=f&&f>u?f-u:void 0;return Pl(i,w,g,k)};if(e){const o=e+Nl,i=a;a=s=>s.startsWith(o)?i(s.slice(o.length)):Pl(Zv,!1,s,void 0,!0)}if(r){const o=a;a=i=>r({className:i,parseClassName:o})}return a},tp=t=>{const e=new Map;return t.orderSensitiveModifiers.forEach((r,a)=>{e.set(r,1e6+a)}),r=>{const a=[];let o=[];for(let i=0;i<r.length;i++){const s=r[i],l=s[0]==="[",u=e.has(s);l||u?(o.length>0&&(o.sort(),a.push(...o),o=[]),a.push(s)):o.push(s)}return o.length>0&&(o.sort(),a.push(...o)),a}},rp=t=>({cache:Qv(t.cacheSize),parseClassName:ep(t),sortModifiers:tp(t),...qv(t)}),np=/\s+/,ap=(t,e)=>{const{parseClassName:r,getClassGroupId:a,getConflictingClassGroupIds:o,sortModifiers:i}=e,s=[],l=t.trim().split(np);let u="";for(let f=l.length-1;f>=0;f-=1){const p=l[f],{isExternal:_,modifiers:g,hasImportantModifier:w,baseClassName:k,maybePostfixModifierPosition:S}=r(p);if(_){u=p+(u.length>0?" "+u:u);continue}let b=!!S,C=a(b?k.substring(0,S):k);if(!C){if(!b){u=p+(u.length>0?" "+u:u);continue}if(C=a(k),!C){u=p+(u.length>0?" "+u:u);continue}b=!1}const z=g.length===0?"":g.length===1?g[0]:i(g).join(":"),P=w?z+wi:z,E=P+C;if(s.indexOf(E)>-1)continue;s.push(E);const ee=o(C,b);for(let se=0;se<ee.length;++se){const j=ee[se];s.push(P+j)}u=p+(u.length>0?" "+u:u)}return u},op=(...t)=>{let e=0,r,a,o="";for(;e<t.length;)(r=t[e++])&&(a=xc(r))&&(o&&(o+=" "),o+=a);return o},xc=t=>{if(typeof t=="string")return t;let e,r="";for(let a=0;a<t.length;a++)t[a]&&(e=xc(t[a]))&&(r&&(r+=" "),r+=e);return r},sp=(t,...e)=>{let r,a,o,i;const s=u=>{const f=e.reduce((p,_)=>_(p),t());return r=rp(f),a=r.cache.get,o=r.cache.set,i=l,l(u)},l=u=>{const f=a(u);if(f)return f;const p=ap(u,r);return o(u,p),p};return i=s,(...u)=>i(op(...u))},ip=[],Tr=t=>{const e=r=>r[t]||ip;return e.isThemeGetter=!0,e},gc=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,_c=/^\((?:(\w[\w-]*):)?(.+)\)$/i,lp=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,dp=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,cp=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,up=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,fp=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,vp=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,va=t=>lp.test(t),Lt=t=>!!t&&!Number.isNaN(Number(t)),pa=t=>!!t&&Number.isInteger(Number(t)),Ys=t=>t.endsWith("%")&&Lt(t.slice(0,-1)),ta=t=>dp.test(t),bc=()=>!0,pp=t=>cp.test(t)&&!up.test(t),Xi=()=>!1,hp=t=>fp.test(t),mp=t=>vp.test(t),xp=t=>!Ke(t)&&!Ye(t),gp=t=>Ia(t,kc,Xi),Ke=t=>gc.test(t),Pa=t=>Ia(t,Cc,pp),Ll=t=>Ia(t,$p,Lt),_p=t=>Ia(t,$c,bc),bp=t=>Ia(t,Sc,Xi),Ol=t=>Ia(t,wc,Xi),wp=t=>Ia(t,yc,mp),cs=t=>Ia(t,zc,hp),Ye=t=>_c.test(t),Lo=t=>eo(t,Cc),yp=t=>eo(t,Sc),Rl=t=>eo(t,wc),kp=t=>eo(t,kc),Cp=t=>eo(t,yc),us=t=>eo(t,zc,!0),Sp=t=>eo(t,$c,!0),Ia=(t,e,r)=>{const a=gc.exec(t);return a?a[1]?e(a[1]):r(a[2]):!1},eo=(t,e,r=!1)=>{const a=_c.exec(t);return a?a[1]?e(a[1]):r:!1},wc=t=>t==="position"||t==="percentage",yc=t=>t==="image"||t==="url",kc=t=>t==="length"||t==="size"||t==="bg-size",Cc=t=>t==="length",$p=t=>t==="number",Sc=t=>t==="family-name",$c=t=>t==="number"||t==="weight",zc=t=>t==="shadow",zp=()=>{const t=Tr("color"),e=Tr("font"),r=Tr("text"),a=Tr("font-weight"),o=Tr("tracking"),i=Tr("leading"),s=Tr("breakpoint"),l=Tr("container"),u=Tr("spacing"),f=Tr("radius"),p=Tr("shadow"),_=Tr("inset-shadow"),g=Tr("text-shadow"),w=Tr("drop-shadow"),k=Tr("blur"),S=Tr("perspective"),b=Tr("aspect"),C=Tr("ease"),z=Tr("animate"),P=()=>["auto","avoid","all","avoid-page","page","left","right","column"],E=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],ee=()=>[...E(),Ye,Ke],se=()=>["auto","hidden","clip","visible","scroll"],j=()=>["auto","contain","none"],T=()=>[Ye,Ke,u],G=()=>[va,"full","auto",...T()],K=()=>[pa,"none","subgrid",Ye,Ke],ie=()=>["auto",{span:["full",pa,Ye,Ke]},pa,Ye,Ke],U=()=>[pa,"auto",Ye,Ke],we=()=>["auto","min","max","fr",Ye,Ke],B=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],J=()=>["start","end","center","stretch","center-safe","end-safe"],le=()=>["auto",...T()],X=()=>[va,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...T()],O=()=>[va,"screen","full","dvw","lvw","svw","min","max","fit",...T()],W=()=>[va,"screen","full","lh","dvh","lvh","svh","min","max","fit",...T()],F=()=>[t,Ye,Ke],ce=()=>[...E(),Rl,Ol,{position:[Ye,Ke]}],ne=()=>["no-repeat",{repeat:["","x","y","space","round"]}],D=()=>["auto","cover","contain",kp,gp,{size:[Ye,Ke]}],H=()=>[Ys,Lo,Pa],te=()=>["","none","full",f,Ye,Ke],Y=()=>["",Lt,Lo,Pa],xe=()=>["solid","dashed","dotted","double"],ke=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],re=()=>[Lt,Ys,Rl,Ol],Fe=()=>["","none",k,Ye,Ke],ot=()=>["none",Lt,Ye,Ke],nt=()=>["none",Lt,Ye,Ke],lt=()=>[Lt,Ye,Ke],at=()=>[va,"full",...T()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[ta],breakpoint:[ta],color:[bc],container:[ta],"drop-shadow":[ta],ease:["in","out","in-out"],font:[xp],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[ta],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[ta],shadow:[ta],spacing:["px",Lt],text:[ta],"text-shadow":[ta],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",va,Ke,Ye,b]}],container:["container"],columns:[{columns:[Lt,Ke,Ye,l]}],"break-after":[{"break-after":P()}],"break-before":[{"break-before":P()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:ee()}],overflow:[{overflow:se()}],"overflow-x":[{"overflow-x":se()}],"overflow-y":[{"overflow-y":se()}],overscroll:[{overscroll:j()}],"overscroll-x":[{"overscroll-x":j()}],"overscroll-y":[{"overscroll-y":j()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:G()}],"inset-x":[{"inset-x":G()}],"inset-y":[{"inset-y":G()}],start:[{"inset-s":G(),start:G()}],end:[{"inset-e":G(),end:G()}],"inset-bs":[{"inset-bs":G()}],"inset-be":[{"inset-be":G()}],top:[{top:G()}],right:[{right:G()}],bottom:[{bottom:G()}],left:[{left:G()}],visibility:["visible","invisible","collapse"],z:[{z:[pa,"auto",Ye,Ke]}],basis:[{basis:[va,"full","auto",l,...T()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[Lt,va,"auto","initial","none",Ke]}],grow:[{grow:["",Lt,Ye,Ke]}],shrink:[{shrink:["",Lt,Ye,Ke]}],order:[{order:[pa,"first","last","none",Ye,Ke]}],"grid-cols":[{"grid-cols":K()}],"col-start-end":[{col:ie()}],"col-start":[{"col-start":U()}],"col-end":[{"col-end":U()}],"grid-rows":[{"grid-rows":K()}],"row-start-end":[{row:ie()}],"row-start":[{"row-start":U()}],"row-end":[{"row-end":U()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":we()}],"auto-rows":[{"auto-rows":we()}],gap:[{gap:T()}],"gap-x":[{"gap-x":T()}],"gap-y":[{"gap-y":T()}],"justify-content":[{justify:[...B(),"normal"]}],"justify-items":[{"justify-items":[...J(),"normal"]}],"justify-self":[{"justify-self":["auto",...J()]}],"align-content":[{content:["normal",...B()]}],"align-items":[{items:[...J(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...J(),{baseline:["","last"]}]}],"place-content":[{"place-content":B()}],"place-items":[{"place-items":[...J(),"baseline"]}],"place-self":[{"place-self":["auto",...J()]}],p:[{p:T()}],px:[{px:T()}],py:[{py:T()}],ps:[{ps:T()}],pe:[{pe:T()}],pbs:[{pbs:T()}],pbe:[{pbe:T()}],pt:[{pt:T()}],pr:[{pr:T()}],pb:[{pb:T()}],pl:[{pl:T()}],m:[{m:le()}],mx:[{mx:le()}],my:[{my:le()}],ms:[{ms:le()}],me:[{me:le()}],mbs:[{mbs:le()}],mbe:[{mbe:le()}],mt:[{mt:le()}],mr:[{mr:le()}],mb:[{mb:le()}],ml:[{ml:le()}],"space-x":[{"space-x":T()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":T()}],"space-y-reverse":["space-y-reverse"],size:[{size:X()}],"inline-size":[{inline:["auto",...O()]}],"min-inline-size":[{"min-inline":["auto",...O()]}],"max-inline-size":[{"max-inline":["none",...O()]}],"block-size":[{block:["auto",...W()]}],"min-block-size":[{"min-block":["auto",...W()]}],"max-block-size":[{"max-block":["none",...W()]}],w:[{w:[l,"screen",...X()]}],"min-w":[{"min-w":[l,"screen","none",...X()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[s]},...X()]}],h:[{h:["screen","lh",...X()]}],"min-h":[{"min-h":["screen","lh","none",...X()]}],"max-h":[{"max-h":["screen","lh",...X()]}],"font-size":[{text:["base",r,Lo,Pa]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[a,Sp,_p]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",Ys,Ke]}],"font-family":[{font:[yp,bp,e]}],"font-features":[{"font-features":[Ke]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[o,Ye,Ke]}],"line-clamp":[{"line-clamp":[Lt,"none",Ye,Ll]}],leading:[{leading:[i,...T()]}],"list-image":[{"list-image":["none",Ye,Ke]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",Ye,Ke]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:F()}],"text-color":[{text:F()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...xe(),"wavy"]}],"text-decoration-thickness":[{decoration:[Lt,"from-font","auto",Ye,Pa]}],"text-decoration-color":[{decoration:F()}],"underline-offset":[{"underline-offset":[Lt,"auto",Ye,Ke]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:T()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",Ye,Ke]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",Ye,Ke]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:ce()}],"bg-repeat":[{bg:ne()}],"bg-size":[{bg:D()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},pa,Ye,Ke],radial:["",Ye,Ke],conic:[pa,Ye,Ke]},Cp,wp]}],"bg-color":[{bg:F()}],"gradient-from-pos":[{from:H()}],"gradient-via-pos":[{via:H()}],"gradient-to-pos":[{to:H()}],"gradient-from":[{from:F()}],"gradient-via":[{via:F()}],"gradient-to":[{to:F()}],rounded:[{rounded:te()}],"rounded-s":[{"rounded-s":te()}],"rounded-e":[{"rounded-e":te()}],"rounded-t":[{"rounded-t":te()}],"rounded-r":[{"rounded-r":te()}],"rounded-b":[{"rounded-b":te()}],"rounded-l":[{"rounded-l":te()}],"rounded-ss":[{"rounded-ss":te()}],"rounded-se":[{"rounded-se":te()}],"rounded-ee":[{"rounded-ee":te()}],"rounded-es":[{"rounded-es":te()}],"rounded-tl":[{"rounded-tl":te()}],"rounded-tr":[{"rounded-tr":te()}],"rounded-br":[{"rounded-br":te()}],"rounded-bl":[{"rounded-bl":te()}],"border-w":[{border:Y()}],"border-w-x":[{"border-x":Y()}],"border-w-y":[{"border-y":Y()}],"border-w-s":[{"border-s":Y()}],"border-w-e":[{"border-e":Y()}],"border-w-bs":[{"border-bs":Y()}],"border-w-be":[{"border-be":Y()}],"border-w-t":[{"border-t":Y()}],"border-w-r":[{"border-r":Y()}],"border-w-b":[{"border-b":Y()}],"border-w-l":[{"border-l":Y()}],"divide-x":[{"divide-x":Y()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":Y()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...xe(),"hidden","none"]}],"divide-style":[{divide:[...xe(),"hidden","none"]}],"border-color":[{border:F()}],"border-color-x":[{"border-x":F()}],"border-color-y":[{"border-y":F()}],"border-color-s":[{"border-s":F()}],"border-color-e":[{"border-e":F()}],"border-color-bs":[{"border-bs":F()}],"border-color-be":[{"border-be":F()}],"border-color-t":[{"border-t":F()}],"border-color-r":[{"border-r":F()}],"border-color-b":[{"border-b":F()}],"border-color-l":[{"border-l":F()}],"divide-color":[{divide:F()}],"outline-style":[{outline:[...xe(),"none","hidden"]}],"outline-offset":[{"outline-offset":[Lt,Ye,Ke]}],"outline-w":[{outline:["",Lt,Lo,Pa]}],"outline-color":[{outline:F()}],shadow:[{shadow:["","none",p,us,cs]}],"shadow-color":[{shadow:F()}],"inset-shadow":[{"inset-shadow":["none",_,us,cs]}],"inset-shadow-color":[{"inset-shadow":F()}],"ring-w":[{ring:Y()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:F()}],"ring-offset-w":[{"ring-offset":[Lt,Pa]}],"ring-offset-color":[{"ring-offset":F()}],"inset-ring-w":[{"inset-ring":Y()}],"inset-ring-color":[{"inset-ring":F()}],"text-shadow":[{"text-shadow":["none",g,us,cs]}],"text-shadow-color":[{"text-shadow":F()}],opacity:[{opacity:[Lt,Ye,Ke]}],"mix-blend":[{"mix-blend":[...ke(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":ke()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[Lt]}],"mask-image-linear-from-pos":[{"mask-linear-from":re()}],"mask-image-linear-to-pos":[{"mask-linear-to":re()}],"mask-image-linear-from-color":[{"mask-linear-from":F()}],"mask-image-linear-to-color":[{"mask-linear-to":F()}],"mask-image-t-from-pos":[{"mask-t-from":re()}],"mask-image-t-to-pos":[{"mask-t-to":re()}],"mask-image-t-from-color":[{"mask-t-from":F()}],"mask-image-t-to-color":[{"mask-t-to":F()}],"mask-image-r-from-pos":[{"mask-r-from":re()}],"mask-image-r-to-pos":[{"mask-r-to":re()}],"mask-image-r-from-color":[{"mask-r-from":F()}],"mask-image-r-to-color":[{"mask-r-to":F()}],"mask-image-b-from-pos":[{"mask-b-from":re()}],"mask-image-b-to-pos":[{"mask-b-to":re()}],"mask-image-b-from-color":[{"mask-b-from":F()}],"mask-image-b-to-color":[{"mask-b-to":F()}],"mask-image-l-from-pos":[{"mask-l-from":re()}],"mask-image-l-to-pos":[{"mask-l-to":re()}],"mask-image-l-from-color":[{"mask-l-from":F()}],"mask-image-l-to-color":[{"mask-l-to":F()}],"mask-image-x-from-pos":[{"mask-x-from":re()}],"mask-image-x-to-pos":[{"mask-x-to":re()}],"mask-image-x-from-color":[{"mask-x-from":F()}],"mask-image-x-to-color":[{"mask-x-to":F()}],"mask-image-y-from-pos":[{"mask-y-from":re()}],"mask-image-y-to-pos":[{"mask-y-to":re()}],"mask-image-y-from-color":[{"mask-y-from":F()}],"mask-image-y-to-color":[{"mask-y-to":F()}],"mask-image-radial":[{"mask-radial":[Ye,Ke]}],"mask-image-radial-from-pos":[{"mask-radial-from":re()}],"mask-image-radial-to-pos":[{"mask-radial-to":re()}],"mask-image-radial-from-color":[{"mask-radial-from":F()}],"mask-image-radial-to-color":[{"mask-radial-to":F()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":E()}],"mask-image-conic-pos":[{"mask-conic":[Lt]}],"mask-image-conic-from-pos":[{"mask-conic-from":re()}],"mask-image-conic-to-pos":[{"mask-conic-to":re()}],"mask-image-conic-from-color":[{"mask-conic-from":F()}],"mask-image-conic-to-color":[{"mask-conic-to":F()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:ce()}],"mask-repeat":[{mask:ne()}],"mask-size":[{mask:D()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",Ye,Ke]}],filter:[{filter:["","none",Ye,Ke]}],blur:[{blur:Fe()}],brightness:[{brightness:[Lt,Ye,Ke]}],contrast:[{contrast:[Lt,Ye,Ke]}],"drop-shadow":[{"drop-shadow":["","none",w,us,cs]}],"drop-shadow-color":[{"drop-shadow":F()}],grayscale:[{grayscale:["",Lt,Ye,Ke]}],"hue-rotate":[{"hue-rotate":[Lt,Ye,Ke]}],invert:[{invert:["",Lt,Ye,Ke]}],saturate:[{saturate:[Lt,Ye,Ke]}],sepia:[{sepia:["",Lt,Ye,Ke]}],"backdrop-filter":[{"backdrop-filter":["","none",Ye,Ke]}],"backdrop-blur":[{"backdrop-blur":Fe()}],"backdrop-brightness":[{"backdrop-brightness":[Lt,Ye,Ke]}],"backdrop-contrast":[{"backdrop-contrast":[Lt,Ye,Ke]}],"backdrop-grayscale":[{"backdrop-grayscale":["",Lt,Ye,Ke]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[Lt,Ye,Ke]}],"backdrop-invert":[{"backdrop-invert":["",Lt,Ye,Ke]}],"backdrop-opacity":[{"backdrop-opacity":[Lt,Ye,Ke]}],"backdrop-saturate":[{"backdrop-saturate":[Lt,Ye,Ke]}],"backdrop-sepia":[{"backdrop-sepia":["",Lt,Ye,Ke]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":T()}],"border-spacing-x":[{"border-spacing-x":T()}],"border-spacing-y":[{"border-spacing-y":T()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",Ye,Ke]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[Lt,"initial",Ye,Ke]}],ease:[{ease:["linear","initial",C,Ye,Ke]}],delay:[{delay:[Lt,Ye,Ke]}],animate:[{animate:["none",z,Ye,Ke]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[S,Ye,Ke]}],"perspective-origin":[{"perspective-origin":ee()}],rotate:[{rotate:ot()}],"rotate-x":[{"rotate-x":ot()}],"rotate-y":[{"rotate-y":ot()}],"rotate-z":[{"rotate-z":ot()}],scale:[{scale:nt()}],"scale-x":[{"scale-x":nt()}],"scale-y":[{"scale-y":nt()}],"scale-z":[{"scale-z":nt()}],"scale-3d":["scale-3d"],skew:[{skew:lt()}],"skew-x":[{"skew-x":lt()}],"skew-y":[{"skew-y":lt()}],transform:[{transform:[Ye,Ke,"","none","gpu","cpu"]}],"transform-origin":[{origin:ee()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:at()}],"translate-x":[{"translate-x":at()}],"translate-y":[{"translate-y":at()}],"translate-z":[{"translate-z":at()}],"translate-none":["translate-none"],accent:[{accent:F()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:F()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",Ye,Ke]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":T()}],"scroll-mx":[{"scroll-mx":T()}],"scroll-my":[{"scroll-my":T()}],"scroll-ms":[{"scroll-ms":T()}],"scroll-me":[{"scroll-me":T()}],"scroll-mbs":[{"scroll-mbs":T()}],"scroll-mbe":[{"scroll-mbe":T()}],"scroll-mt":[{"scroll-mt":T()}],"scroll-mr":[{"scroll-mr":T()}],"scroll-mb":[{"scroll-mb":T()}],"scroll-ml":[{"scroll-ml":T()}],"scroll-p":[{"scroll-p":T()}],"scroll-px":[{"scroll-px":T()}],"scroll-py":[{"scroll-py":T()}],"scroll-ps":[{"scroll-ps":T()}],"scroll-pe":[{"scroll-pe":T()}],"scroll-pbs":[{"scroll-pbs":T()}],"scroll-pbe":[{"scroll-pbe":T()}],"scroll-pt":[{"scroll-pt":T()}],"scroll-pr":[{"scroll-pr":T()}],"scroll-pb":[{"scroll-pb":T()}],"scroll-pl":[{"scroll-pl":T()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",Ye,Ke]}],fill:[{fill:["none",...F()]}],"stroke-w":[{stroke:[Lt,Lo,Pa,Ll]}],stroke:[{stroke:["none",...F()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},Mp=sp(zp);function hr(...t){return Mp(ic(t))}const yi="dartlab-conversations",Dl=50;function Tp(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function Ip(){try{const t=localStorage.getItem(yi);return t?JSON.parse(t):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const Ap=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function jl(t){return t.map(e=>({...e,messages:e.messages.map(r=>{if(r.role!=="assistant")return r;const a={};for(const[o,i]of Object.entries(r))Ap.includes(o)||(a[o]=i);return a})}))}function Fl(t){try{const e={conversations:jl(t.conversations),activeId:t.activeId};localStorage.setItem(yi,JSON.stringify(e))}catch{if(t.conversations.length>5){t.conversations=t.conversations.slice(0,t.conversations.length-5);try{const e={conversations:jl(t.conversations),activeId:t.activeId};localStorage.setItem(yi,JSON.stringify(e))}catch{}}}}function Ep(){const t=Ip(),e=t.conversations||[],r=e.find(C=>C.id===t.activeId)?t.activeId:null;let a=Z(Ut(e)),o=Z(Ut(r)),i=null;function s(){i&&clearTimeout(i),i=setTimeout(()=>{Fl({conversations:n(a),activeId:n(o)}),i=null},300)}function l(){i&&clearTimeout(i),i=null,Fl({conversations:n(a),activeId:n(o)})}function u(){return n(a).find(C=>C.id===n(o))||null}function f(){const C={id:Tp(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return v(a,[C,...n(a)],!0),n(a).length>Dl&&v(a,n(a).slice(0,Dl),!0),v(o,C.id,!0),l(),C.id}function p(C){n(a).find(z=>z.id===C)&&(v(o,C,!0),l())}function _(C,z,P=null){const E=u();if(!E)return;const ee={role:C,text:z};P&&(ee.meta=P),E.messages=[...E.messages,ee],E.updatedAt=Date.now(),E.title==="새 대화"&&C==="user"&&(E.title=z.length>30?z.slice(0,30)+"...":z),v(a,[...n(a)],!0),l()}function g(C){const z=u();if(!z||z.messages.length===0)return;const P=z.messages[z.messages.length-1];Object.assign(P,C),z.updatedAt=Date.now(),v(a,[...n(a)],!0),s()}function w(C){v(a,n(a).filter(z=>z.id!==C),!0),n(o)===C&&v(o,n(a).length>0?n(a)[0].id:null,!0),l()}function k(){const C=u();!C||C.messages.length===0||(C.messages=C.messages.slice(0,-1),C.updatedAt=Date.now(),v(a,[...n(a)],!0),l())}function S(C,z){const P=n(a).find(E=>E.id===C);P&&(P.title=z,v(a,[...n(a)],!0),l())}function b(){v(a,[],!0),v(o,null),l()}return{get conversations(){return n(a)},get activeId(){return n(o)},get active(){return u()},createConversation:f,setActive:p,addMessage:_,updateLastMessage:g,removeLastMessage:k,deleteConversation:w,updateTitle:S,clearAll:b,flush:l}}const Mc="dartlab-workspace",Np=6;function Tc(){return typeof window<"u"&&typeof localStorage<"u"}function Pp(){if(!Tc())return{};try{const t=localStorage.getItem(Mc);return t?JSON.parse(t):{}}catch{return{}}}function Lp(t){Tc()&&localStorage.setItem(Mc,JSON.stringify(t))}function Op(){const t=Pp();let e=Z("chat"),r=Z(!1),a=Z(null),o=Z(null),i=Z("explore"),s=Z(null),l=Z(null),u=Z(null),f=Z(null),p=Z(null),_=Z(Ut(t.selectedCompany||null)),g=Z(Ut(t.recentCompanies||[]));function w(){Lp({selectedCompany:n(_),recentCompanies:n(g)})}function k(K){if(!(K!=null&&K.stockCode))return;const ie={stockCode:K.stockCode,corpName:K.corpName||K.company||K.stockCode,company:K.company||K.corpName||K.stockCode,market:K.market||""};v(g,[ie,...n(g).filter(U=>U.stockCode!==ie.stockCode)].slice(0,Np),!0)}function S(K){v(e,K,!0)}function b(K){K&&(v(_,K,!0),k(K)),v(e,"viewer"),v(r,!1),w()}function C(K){v(a,"data"),v(o,K,!0),v(r,!0),T("explore")}function z(){v(r,!1)}function P(K){v(_,K,!0),K&&k(K),w()}function E(K,ie){var U,we,B,J;!(K!=null&&K.company)&&!(K!=null&&K.stockCode)||(v(_,{...n(_)||{},...ie||{},corpName:K.company||((U=n(_))==null?void 0:U.corpName)||(ie==null?void 0:ie.corpName)||(ie==null?void 0:ie.company),company:K.company||((we=n(_))==null?void 0:we.company)||(ie==null?void 0:ie.company)||(ie==null?void 0:ie.corpName),stockCode:K.stockCode||((B=n(_))==null?void 0:B.stockCode)||(ie==null?void 0:ie.stockCode),market:((J=n(_))==null?void 0:J.market)||(ie==null?void 0:ie.market)||""},!0),k(n(_)),w())}function ee(K,ie,U=null){v(u,K,!0),v(f,ie||K,!0),v(p,U,!0)}function se(K,ie=null){v(a,"data"),v(r,!0),v(i,"evidence"),v(s,K,!0),v(l,Number.isInteger(ie)?ie:null,!0)}function j(){v(s,null),v(l,null)}function T(K){v(i,K||"explore",!0),n(i)!=="evidence"&&j()}function G(){return n(e)==="viewer"&&n(_)&&n(u)?{type:"viewer",company:n(_),topic:n(u),topicLabel:n(f),period:n(p)}:n(r)?n(a)==="viewer"&&n(_)?{type:"viewer",company:n(_),topic:n(u),topicLabel:n(f),period:n(p)}:n(a)==="data"&&n(o)?{type:"data",data:n(o)}:null:null}return{get activeView(){return n(e)},get panelOpen(){return n(r)},get panelMode(){return n(a)},get panelData(){return n(o)},get activeTab(){return n(i)},get activeEvidenceSection(){return n(s)},get selectedEvidenceIndex(){return n(l)},get selectedCompany(){return n(_)},get recentCompanies(){return n(g)},get viewerTopic(){return n(u)},get viewerTopicLabel(){return n(f)},get viewerPeriod(){return n(p)},switchView:S,openViewer:b,openData:C,openEvidence:se,closePanel:z,selectCompany:P,setViewerTopic:ee,clearEvidenceSelection:j,setTab:T,syncCompanyFromMessage:E,getViewContext:G}}const Rp="ENTRIES",Ic="KEYS",Ac="VALUES",Fr="";class Xs{constructor(e,r){const a=e._tree,o=Array.from(a.keys());this.set=e,this._type=r,this._path=o.length>0?[{node:a,keys:o}]:[]}next(){const e=this.dive();return this.backtrack(),e}dive(){if(this._path.length===0)return{done:!0,value:void 0};const{node:e,keys:r}=oo(this._path);if(oo(r)===Fr)return{done:!1,value:this.result()};const a=e.get(oo(r));return this._path.push({node:a,keys:Array.from(a.keys())}),this.dive()}backtrack(){if(this._path.length===0)return;const e=oo(this._path).keys;e.pop(),!(e.length>0)&&(this._path.pop(),this.backtrack())}key(){return this.set._prefix+this._path.map(({keys:e})=>oo(e)).filter(e=>e!==Fr).join("")}value(){return oo(this._path).node.get(Fr)}result(){switch(this._type){case Ac:return this.value();case Ic:return this.key();default:return[this.key(),this.value()]}}[Symbol.iterator](){return this}}const oo=t=>t[t.length-1],Dp=(t,e,r)=>{const a=new Map;if(e===void 0)return a;const o=e.length+1,i=o+r,s=new Uint8Array(i*o).fill(r+1);for(let l=0;l<o;++l)s[l]=l;for(let l=1;l<i;++l)s[l*o]=l;return Ec(t,e,r,a,s,1,o,""),a},Ec=(t,e,r,a,o,i,s,l)=>{const u=i*s;e:for(const f of t.keys())if(f===Fr){const p=o[u-1];p<=r&&a.set(l,[t.get(f),p])}else{let p=i;for(let _=0;_<f.length;++_,++p){const g=f[_],w=s*p,k=w-s;let S=o[w];const b=Math.max(0,p-r-1),C=Math.min(s-1,p+r);for(let z=b;z<C;++z){const P=g!==e[z],E=o[k+z]+ +P,ee=o[k+z+1]+1,se=o[w+z]+1,j=o[w+z+1]=Math.min(E,ee,se);j<S&&(S=j)}if(S>r)continue e}Ec(t.get(f),e,r,a,o,p,s,l+f)}};class ba{constructor(e=new Map,r=""){this._size=void 0,this._tree=e,this._prefix=r}atPrefix(e){if(!e.startsWith(this._prefix))throw new Error("Mismatched prefix");const[r,a]=Ss(this._tree,e.slice(this._prefix.length));if(r===void 0){const[o,i]=Qi(a);for(const s of o.keys())if(s!==Fr&&s.startsWith(i)){const l=new Map;return l.set(s.slice(i.length),o.get(s)),new ba(l,e)}}return new ba(r,e)}clear(){this._size=void 0,this._tree.clear()}delete(e){return this._size=void 0,jp(this._tree,e)}entries(){return new Xs(this,Rp)}forEach(e){for(const[r,a]of this)e(r,a,this)}fuzzyGet(e,r){return Dp(this._tree,e,r)}get(e){const r=ki(this._tree,e);return r!==void 0?r.get(Fr):void 0}has(e){const r=ki(this._tree,e);return r!==void 0&&r.has(Fr)}keys(){return new Xs(this,Ic)}set(e,r){if(typeof e!="string")throw new Error("key must be a string");return this._size=void 0,Qs(this._tree,e).set(Fr,r),this}get size(){if(this._size)return this._size;this._size=0;const e=this.entries();for(;!e.next().done;)this._size+=1;return this._size}update(e,r){if(typeof e!="string")throw new Error("key must be a string");this._size=void 0;const a=Qs(this._tree,e);return a.set(Fr,r(a.get(Fr))),this}fetch(e,r){if(typeof e!="string")throw new Error("key must be a string");this._size=void 0;const a=Qs(this._tree,e);let o=a.get(Fr);return o===void 0&&a.set(Fr,o=r()),o}values(){return new Xs(this,Ac)}[Symbol.iterator](){return this.entries()}static from(e){const r=new ba;for(const[a,o]of e)r.set(a,o);return r}static fromObject(e){return ba.from(Object.entries(e))}}const Ss=(t,e,r=[])=>{if(e.length===0||t==null)return[t,r];for(const a of t.keys())if(a!==Fr&&e.startsWith(a))return r.push([t,a]),Ss(t.get(a),e.slice(a.length),r);return r.push([t,e]),Ss(void 0,"",r)},ki=(t,e)=>{if(e.length===0||t==null)return t;for(const r of t.keys())if(r!==Fr&&e.startsWith(r))return ki(t.get(r),e.slice(r.length))},Qs=(t,e)=>{const r=e.length;e:for(let a=0;t&&a<r;){for(const i of t.keys())if(i!==Fr&&e[a]===i[0]){const s=Math.min(r-a,i.length);let l=1;for(;l<s&&e[a+l]===i[l];)++l;const u=t.get(i);if(l===i.length)t=u;else{const f=new Map;f.set(i.slice(l),u),t.set(e.slice(a,a+l),f),t.delete(i),t=f}a+=l;continue e}const o=new Map;return t.set(e.slice(a),o),o}return t},jp=(t,e)=>{const[r,a]=Ss(t,e);if(r!==void 0){if(r.delete(Fr),r.size===0)Nc(a);else if(r.size===1){const[o,i]=r.entries().next().value;Pc(a,o,i)}}},Nc=t=>{if(t.length===0)return;const[e,r]=Qi(t);if(e.delete(r),e.size===0)Nc(t.slice(0,-1));else if(e.size===1){const[a,o]=e.entries().next().value;a!==Fr&&Pc(t.slice(0,-1),a,o)}},Pc=(t,e,r)=>{if(t.length===0)return;const[a,o]=Qi(t);a.set(o+e,r),a.delete(o)},Qi=t=>t[t.length-1],Zi="or",Lc="and",Fp="and_not";class io{constructor(e){if((e==null?void 0:e.fields)==null)throw new Error('MiniSearch: option "fields" must be provided');const r=e.autoVacuum==null||e.autoVacuum===!0?ti:e.autoVacuum;this._options={...ei,...e,autoVacuum:r,searchOptions:{...Vl,...e.searchOptions||{}},autoSuggestOptions:{...Up,...e.autoSuggestOptions||{}}},this._index=new ba,this._documentCount=0,this._documentIds=new Map,this._idToShortId=new Map,this._fieldIds={},this._fieldLength=new Map,this._avgFieldLength=[],this._nextId=0,this._storedFields=new Map,this._dirtCount=0,this._currentVacuum=null,this._enqueuedVacuum=null,this._enqueuedVacuumConditions=Si,this.addFields(this._options.fields)}add(e){const{extractField:r,stringifyField:a,tokenize:o,processTerm:i,fields:s,idField:l}=this._options,u=r(e,l);if(u==null)throw new Error(`MiniSearch: document does not have ID field "${l}"`);if(this._idToShortId.has(u))throw new Error(`MiniSearch: duplicate ID ${u}`);const f=this.addDocumentId(u);this.saveStoredFields(f,e);for(const p of s){const _=r(e,p);if(_==null)continue;const g=o(a(_,p),p),w=this._fieldIds[p],k=new Set(g).size;this.addFieldLength(f,w,this._documentCount-1,k);for(const S of g){const b=i(S,p);if(Array.isArray(b))for(const C of b)this.addTerm(w,f,C);else b&&this.addTerm(w,f,b)}}}addAll(e){for(const r of e)this.add(r)}addAllAsync(e,r={}){const{chunkSize:a=10}=r,o={chunk:[],promise:Promise.resolve()},{chunk:i,promise:s}=e.reduce(({chunk:l,promise:u},f,p)=>(l.push(f),(p+1)%a===0?{chunk:[],promise:u.then(()=>new Promise(_=>setTimeout(_,0))).then(()=>this.addAll(l))}:{chunk:l,promise:u}),o);return s.then(()=>this.addAll(i))}remove(e){const{tokenize:r,processTerm:a,extractField:o,stringifyField:i,fields:s,idField:l}=this._options,u=o(e,l);if(u==null)throw new Error(`MiniSearch: document does not have ID field "${l}"`);const f=this._idToShortId.get(u);if(f==null)throw new Error(`MiniSearch: cannot remove document with ID ${u}: it is not in the index`);for(const p of s){const _=o(e,p);if(_==null)continue;const g=r(i(_,p),p),w=this._fieldIds[p],k=new Set(g).size;this.removeFieldLength(f,w,this._documentCount,k);for(const S of g){const b=a(S,p);if(Array.isArray(b))for(const C of b)this.removeTerm(w,f,C);else b&&this.removeTerm(w,f,b)}}this._storedFields.delete(f),this._documentIds.delete(f),this._idToShortId.delete(u),this._fieldLength.delete(f),this._documentCount-=1}removeAll(e){if(e)for(const r of e)this.remove(r);else{if(arguments.length>0)throw new Error("Expected documents to be present. Omit the argument to remove all documents.");this._index=new ba,this._documentCount=0,this._documentIds=new Map,this._idToShortId=new Map,this._fieldLength=new Map,this._avgFieldLength=[],this._storedFields=new Map,this._nextId=0}}discard(e){const r=this._idToShortId.get(e);if(r==null)throw new Error(`MiniSearch: cannot discard document with ID ${e}: it is not in the index`);this._idToShortId.delete(e),this._documentIds.delete(r),this._storedFields.delete(r),(this._fieldLength.get(r)||[]).forEach((a,o)=>{this.removeFieldLength(r,o,this._documentCount,a)}),this._fieldLength.delete(r),this._documentCount-=1,this._dirtCount+=1,this.maybeAutoVacuum()}maybeAutoVacuum(){if(this._options.autoVacuum===!1)return;const{minDirtFactor:e,minDirtCount:r,batchSize:a,batchWait:o}=this._options.autoVacuum;this.conditionalVacuum({batchSize:a,batchWait:o},{minDirtCount:r,minDirtFactor:e})}discardAll(e){const r=this._options.autoVacuum;try{this._options.autoVacuum=!1;for(const a of e)this.discard(a)}finally{this._options.autoVacuum=r}this.maybeAutoVacuum()}replace(e){const{idField:r,extractField:a}=this._options,o=a(e,r);this.discard(o),this.add(e)}vacuum(e={}){return this.conditionalVacuum(e)}conditionalVacuum(e,r){return this._currentVacuum?(this._enqueuedVacuumConditions=this._enqueuedVacuumConditions&&r,this._enqueuedVacuum!=null?this._enqueuedVacuum:(this._enqueuedVacuum=this._currentVacuum.then(()=>{const a=this._enqueuedVacuumConditions;return this._enqueuedVacuumConditions=Si,this.performVacuuming(e,a)}),this._enqueuedVacuum)):this.vacuumConditionsMet(r)===!1?Promise.resolve():(this._currentVacuum=this.performVacuuming(e),this._currentVacuum)}async performVacuuming(e,r){const a=this._dirtCount;if(this.vacuumConditionsMet(r)){const o=e.batchSize||Ci.batchSize,i=e.batchWait||Ci.batchWait;let s=1;for(const[l,u]of this._index){for(const[f,p]of u)for(const[_]of p)this._documentIds.has(_)||(p.size<=1?u.delete(f):p.delete(_));this._index.get(l).size===0&&this._index.delete(l),s%o===0&&await new Promise(f=>setTimeout(f,i)),s+=1}this._dirtCount-=a}await null,this._currentVacuum=this._enqueuedVacuum,this._enqueuedVacuum=null}vacuumConditionsMet(e){if(e==null)return!0;let{minDirtCount:r,minDirtFactor:a}=e;return r=r||ti.minDirtCount,a=a||ti.minDirtFactor,this.dirtCount>=r&&this.dirtFactor>=a}get isVacuuming(){return this._currentVacuum!=null}get dirtCount(){return this._dirtCount}get dirtFactor(){return this._dirtCount/(1+this._documentCount+this._dirtCount)}has(e){return this._idToShortId.has(e)}getStoredFields(e){const r=this._idToShortId.get(e);if(r!=null)return this._storedFields.get(r)}search(e,r={}){const{searchOptions:a}=this._options,o={...a,...r},i=this.executeQuery(e,r),s=[];for(const[l,{score:u,terms:f,match:p}]of i){const _=f.length||1,g={id:this._documentIds.get(l),score:u*_,terms:Object.keys(p),queryTerms:f,match:p};Object.assign(g,this._storedFields.get(l)),(o.filter==null||o.filter(g))&&s.push(g)}return e===io.wildcard&&o.boostDocument==null||s.sort(ql),s}autoSuggest(e,r={}){r={...this._options.autoSuggestOptions,...r};const a=new Map;for(const{score:i,terms:s}of this.search(e,r)){const l=s.join(" "),u=a.get(l);u!=null?(u.score+=i,u.count+=1):a.set(l,{score:i,terms:s,count:1})}const o=[];for(const[i,{score:s,terms:l,count:u}]of a)o.push({suggestion:i,terms:l,score:s/u});return o.sort(ql),o}get documentCount(){return this._documentCount}get termCount(){return this._index.size}static loadJSON(e,r){if(r==null)throw new Error("MiniSearch: loadJSON should be given the same options used when serializing the index");return this.loadJS(JSON.parse(e),r)}static async loadJSONAsync(e,r){if(r==null)throw new Error("MiniSearch: loadJSON should be given the same options used when serializing the index");return this.loadJSAsync(JSON.parse(e),r)}static getDefault(e){if(ei.hasOwnProperty(e))return Zs(ei,e);throw new Error(`MiniSearch: unknown option "${e}"`)}static loadJS(e,r){const{index:a,documentIds:o,fieldLength:i,storedFields:s,serializationVersion:l}=e,u=this.instantiateMiniSearch(e,r);u._documentIds=fs(o),u._fieldLength=fs(i),u._storedFields=fs(s);for(const[f,p]of u._documentIds)u._idToShortId.set(p,f);for(const[f,p]of a){const _=new Map;for(const g of Object.keys(p)){let w=p[g];l===1&&(w=w.ds),_.set(parseInt(g,10),fs(w))}u._index.set(f,_)}return u}static async loadJSAsync(e,r){const{index:a,documentIds:o,fieldLength:i,storedFields:s,serializationVersion:l}=e,u=this.instantiateMiniSearch(e,r);u._documentIds=await vs(o),u._fieldLength=await vs(i),u._storedFields=await vs(s);for(const[p,_]of u._documentIds)u._idToShortId.set(_,p);let f=0;for(const[p,_]of a){const g=new Map;for(const w of Object.keys(_)){let k=_[w];l===1&&(k=k.ds),g.set(parseInt(w,10),await vs(k))}++f%1e3===0&&await Oc(0),u._index.set(p,g)}return u}static instantiateMiniSearch(e,r){const{documentCount:a,nextId:o,fieldIds:i,averageFieldLength:s,dirtCount:l,serializationVersion:u}=e;if(u!==1&&u!==2)throw new Error("MiniSearch: cannot deserialize an index created with an incompatible version");const f=new io(r);return f._documentCount=a,f._nextId=o,f._idToShortId=new Map,f._fieldIds=i,f._avgFieldLength=s,f._dirtCount=l||0,f._index=new ba,f}executeQuery(e,r={}){if(e===io.wildcard)return this.executeWildcardQuery(r);if(typeof e!="string"){const g={...r,...e,queries:void 0},w=e.queries.map(k=>this.executeQuery(k,g));return this.combineResults(w,g.combineWith)}const{tokenize:a,processTerm:o,searchOptions:i}=this._options,s={tokenize:a,processTerm:o,...i,...r},{tokenize:l,processTerm:u}=s,_=l(e).flatMap(g=>u(g)).filter(g=>!!g).map(Hp(s)).map(g=>this.executeQuerySpec(g,s));return this.combineResults(_,s.combineWith)}executeQuerySpec(e,r){const a={...this._options.searchOptions,...r},o=(a.fields||this._options.fields).reduce((S,b)=>({...S,[b]:Zs(a.boost,b)||1}),{}),{boostDocument:i,weights:s,maxFuzzy:l,bm25:u}=a,{fuzzy:f,prefix:p}={...Vl.weights,...s},_=this._index.get(e.term),g=this.termResults(e.term,e.term,1,e.termBoost,_,o,i,u);let w,k;if(e.prefix&&(w=this._index.atPrefix(e.term)),e.fuzzy){const S=e.fuzzy===!0?.2:e.fuzzy,b=S<1?Math.min(l,Math.round(e.term.length*S)):S;b&&(k=this._index.fuzzyGet(e.term,b))}if(w)for(const[S,b]of w){const C=S.length-e.term.length;if(!C)continue;k==null||k.delete(S);const z=p*S.length/(S.length+.3*C);this.termResults(e.term,S,z,e.termBoost,b,o,i,u,g)}if(k)for(const S of k.keys()){const[b,C]=k.get(S);if(!C)continue;const z=f*S.length/(S.length+C);this.termResults(e.term,S,z,e.termBoost,b,o,i,u,g)}return g}executeWildcardQuery(e){const r=new Map,a={...this._options.searchOptions,...e};for(const[o,i]of this._documentIds){const s=a.boostDocument?a.boostDocument(i,"",this._storedFields.get(o)):1;r.set(o,{score:s,terms:[],match:{}})}return r}combineResults(e,r=Zi){if(e.length===0)return new Map;const a=r.toLowerCase(),o=Vp[a];if(!o)throw new Error(`Invalid combination operator: ${r}`);return e.reduce(o)||new Map}toJSON(){const e=[];for(const[r,a]of this._index){const o={};for(const[i,s]of a)o[i]=Object.fromEntries(s);e.push([r,o])}return{documentCount:this._documentCount,nextId:this._nextId,documentIds:Object.fromEntries(this._documentIds),fieldIds:this._fieldIds,fieldLength:Object.fromEntries(this._fieldLength),averageFieldLength:this._avgFieldLength,storedFields:Object.fromEntries(this._storedFields),dirtCount:this._dirtCount,index:e,serializationVersion:2}}termResults(e,r,a,o,i,s,l,u,f=new Map){if(i==null)return f;for(const p of Object.keys(s)){const _=s[p],g=this._fieldIds[p],w=i.get(g);if(w==null)continue;let k=w.size;const S=this._avgFieldLength[g];for(const b of w.keys()){if(!this._documentIds.has(b)){this.removeTerm(g,b,r),k-=1;continue}const C=l?l(this._documentIds.get(b),r,this._storedFields.get(b)):1;if(!C)continue;const z=w.get(b),P=this._fieldLength.get(b)[g],E=qp(z,k,this._documentCount,P,S,u),ee=a*o*_*C*E,se=f.get(b);if(se){se.score+=ee,Wp(se.terms,e);const j=Zs(se.match,r);j?j.push(p):se.match[r]=[p]}else f.set(b,{score:ee,terms:[e],match:{[r]:[p]}})}}return f}addTerm(e,r,a){const o=this._index.fetch(a,Hl);let i=o.get(e);if(i==null)i=new Map,i.set(r,1),o.set(e,i);else{const s=i.get(r);i.set(r,(s||0)+1)}}removeTerm(e,r,a){if(!this._index.has(a)){this.warnDocumentChanged(r,e,a);return}const o=this._index.fetch(a,Hl),i=o.get(e);i==null||i.get(r)==null?this.warnDocumentChanged(r,e,a):i.get(r)<=1?i.size<=1?o.delete(e):i.delete(r):i.set(r,i.get(r)-1),this._index.get(a).size===0&&this._index.delete(a)}warnDocumentChanged(e,r,a){for(const o of Object.keys(this._fieldIds))if(this._fieldIds[o]===r){this._options.logger("warn",`MiniSearch: document with ID ${this._documentIds.get(e)} has changed before removal: term "${a}" was not present in field "${o}". Removing a document after it has changed can corrupt the index!`,"version_conflict");return}}addDocumentId(e){const r=this._nextId;return this._idToShortId.set(e,r),this._documentIds.set(r,e),this._documentCount+=1,this._nextId+=1,r}addFields(e){for(let r=0;r<e.length;r++)this._fieldIds[e[r]]=r}addFieldLength(e,r,a,o){let i=this._fieldLength.get(e);i==null&&this._fieldLength.set(e,i=[]),i[r]=o;const l=(this._avgFieldLength[r]||0)*a+o;this._avgFieldLength[r]=l/(a+1)}removeFieldLength(e,r,a,o){if(a===1){this._avgFieldLength[r]=0;return}const i=this._avgFieldLength[r]*a-o;this._avgFieldLength[r]=i/(a-1)}saveStoredFields(e,r){const{storeFields:a,extractField:o}=this._options;if(a==null||a.length===0)return;let i=this._storedFields.get(e);i==null&&this._storedFields.set(e,i={});for(const s of a){const l=o(r,s);l!==void 0&&(i[s]=l)}}}io.wildcard=Symbol("*");const Zs=(t,e)=>Object.prototype.hasOwnProperty.call(t,e)?t[e]:void 0,Vp={[Zi]:(t,e)=>{for(const r of e.keys()){const a=t.get(r);if(a==null)t.set(r,e.get(r));else{const{score:o,terms:i,match:s}=e.get(r);a.score=a.score+o,a.match=Object.assign(a.match,s),Bl(a.terms,i)}}return t},[Lc]:(t,e)=>{const r=new Map;for(const a of e.keys()){const o=t.get(a);if(o==null)continue;const{score:i,terms:s,match:l}=e.get(a);Bl(o.terms,s),r.set(a,{score:o.score+i,terms:o.terms,match:Object.assign(o.match,l)})}return r},[Fp]:(t,e)=>{for(const r of e.keys())t.delete(r);return t}},Bp={k:1.2,b:.7,d:.5},qp=(t,e,r,a,o,i)=>{const{k:s,b:l,d:u}=i;return Math.log(1+(r-e+.5)/(e+.5))*(u+t*(s+1)/(t+s*(1-l+l*a/o)))},Hp=t=>(e,r,a)=>{const o=typeof t.fuzzy=="function"?t.fuzzy(e,r,a):t.fuzzy||!1,i=typeof t.prefix=="function"?t.prefix(e,r,a):t.prefix===!0,s=typeof t.boostTerm=="function"?t.boostTerm(e,r,a):1;return{term:e,fuzzy:o,prefix:i,termBoost:s}},ei={idField:"id",extractField:(t,e)=>t[e],stringifyField:(t,e)=>t.toString(),tokenize:t=>t.split(Kp),processTerm:t=>t.toLowerCase(),fields:void 0,searchOptions:void 0,storeFields:[],logger:(t,e)=>{typeof(console==null?void 0:console[t])=="function"&&console[t](e)},autoVacuum:!0},Vl={combineWith:Zi,prefix:!1,fuzzy:!1,maxFuzzy:6,boost:{},weights:{fuzzy:.45,prefix:.375},bm25:Bp},Up={combineWith:Lc,prefix:(t,e,r)=>e===r.length-1},Ci={batchSize:1e3,batchWait:10},Si={minDirtFactor:.1,minDirtCount:20},ti={...Ci,...Si},Wp=(t,e)=>{t.includes(e)||t.push(e)},Bl=(t,e)=>{for(const r of e)t.includes(r)||t.push(r)},ql=({score:t},{score:e})=>e-t,Hl=()=>new Map,fs=t=>{const e=new Map;for(const r of Object.keys(t))e.set(parseInt(r,10),t[r]);return e},vs=async t=>{const e=new Map;let r=0;for(const a of Object.keys(t))e.set(parseInt(a,10),t[a]),++r%1e3===0&&await Oc(0);return e},Oc=t=>new Promise(e=>setTimeout(e,t)),Kp=/[\n\r\p{Z}\p{P}]+/u;function Gp(){try{const t=localStorage.getItem("dartlab-bookmarks");return t?JSON.parse(t):{}}catch{return{}}}function Jp(t){try{localStorage.setItem("dartlab-bookmarks",JSON.stringify(t))}catch{}}function Yp(){let t=Z(null),e=Z(null),r=Z(null),a=Z(!1),o=Z(null),i=Z(null),s=Z(Ut(new Set)),l=Z(null),u=Z(!1),f=Z(null),p=new Map,_=Z(null),g=Z(!1),w=Z(null),k=Z(!1),S=Z(Ut(new Map)),b=Z(null),C=null,z=Z(!1),P=Z(Ut(Gp()));async function E(X){var O,W;if(!(X===n(t)&&n(r))){v(t,X,!0),v(e,null),v(r,null),v(o,null),v(i,null),v(l,null),v(f,null),p=new Map,v(s,new Set,!0),v(_,null),v(w,null),v(S,new Map,!0),C=null,v(z,!1),v(a,!0);try{const F=await Av(X);if(v(r,F,!0),v(e,F.corpName,!0),((O=F.chapters)==null?void 0:O.length)>0&&(v(s,new Set([F.chapters[0].chapter]),!0),((W=F.chapters[0].topics)==null?void 0:W.length)>0)){const ce=F.chapters[0].topics[0];await K(ce.topic,F.chapters[0].chapter)}ee(X),se(X),j(X)}catch(F){console.error("TOC 로드 실패:",F)}v(a,!1)}}async function ee(X){var O;if(((O=n(_))==null?void 0:O.stockCode)!==X){v(g,!0);try{const W=await Ov(X);W.available?v(_,W,!0):v(_,null)}catch{v(_,null)}v(g,!1)}}async function se(X){v(k,!0);try{const O=await Rv(X);O.available?v(w,O,!0):v(w,null)}catch{v(w,null)}v(k,!1)}async function j(X){try{const O=await Lv(X);if(!O.documents||O.documents.length===0)return;const W=new io({fields:["label","text"],storeFields:["topic","label","chapter","period","blockType"],searchOptions:{boost:{label:3},fuzzy:.2,prefix:!0}});W.addAll(O.documents),C=W,v(z,!0)}catch(O){console.error("SearchIndex 로드 실패:",O)}}function T(X){if(!C||!(X!=null&&X.trim()))return[];const O=C.search(X.trim(),{fuzzy:.2,prefix:!0,boost:{label:3}}),W=new Map;for(const F of O){const ce=F.topic;(!W.has(ce)||W.get(ce).score<F.score)&&W.set(ce,F)}return[...W.values()].sort((F,ce)=>ce.score-F.score).slice(0,20).map(F=>({topic:F.topic,label:F.label,chapter:F.chapter,period:F.period,blockType:F.blockType,score:F.score,source:"minisearch"}))}function G(X){v(b,X||null,!0)}async function K(X,O){if(X!==n(o)){if(v(o,X,!0),v(b,null),v(i,O,!0),O&&!n(s).has(O)&&v(s,new Set([...n(s),O]),!0),p.has(X)){v(l,p.get(X),!0);return}v(u,!0),v(l,null),v(f,null);try{const[W,F]=await Promise.allSettled([Ev(n(t),X),Nv(n(t),X)]);W.status==="fulfilled"&&(v(l,W.value,!0),p.set(X,W.value)),F.status==="fulfilled"&&v(f,F.value,!0)}catch(W){console.error("Topic 로드 실패:",W)}v(u,!1)}}function ie(X){const O=new Set(n(s));O.has(X)?O.delete(X):O.add(X),v(s,O,!0)}function U(X){return n(S).get(X)??null}function we(X,O){const W=new Map(n(S));W.set(X,O),v(S,W,!0)}function B(){return n(P)[n(t)]||[]}function J(X){return(n(P)[n(t)]||[]).includes(X)}function le(X){const O=n(P)[n(t)]||[],W=O.includes(X)?O.filter(F=>F!==X):[X,...O];v(P,{...n(P),[n(t)]:W},!0),Jp(n(P))}return{get stockCode(){return n(t)},get corpName(){return n(e)},get toc(){return n(r)},get tocLoading(){return n(a)},get selectedTopic(){return n(o)},get selectedChapter(){return n(i)},get expandedChapters(){return n(s)},get topicData(){return n(l)},get topicLoading(){return n(u)},get diffSummary(){return n(f)},get insightData(){return n(_)},get insightLoading(){return n(g)},get networkData(){return n(w)},get networkLoading(){return n(k)},get searchHighlight(){return n(b)},get searchIndexReady(){return n(z)},loadCompany:E,setSearchHighlight:G,searchSections:T,selectTopic:K,toggleChapter:ie,getTopicSummary:U,setTopicSummary:we,getBookmarks:B,isBookmarked:J,toggleBookmark:le}}var Xp=h("<a><!></a>"),Qp=h("<button><!></button>");function Zp(t,e){Cr(e,!0);let r=Pe(e,"variant",3,"default"),a=Pe(e,"size",3,"default"),o=_v(e,["$$slots","$$events","$$legacy","variant","size","class","children"]);const i={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},s={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=be(),u=ae(l);{var f=_=>{var g=Xp();ks(g,k=>({class:k,...o}),[()=>hr("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",i[r()],s[a()],e.class)]);var w=d(g);bi(w,()=>e.children),c(_,g)},p=_=>{var g=Qp();ks(g,k=>({class:k,...o}),[()=>hr("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",i[r()],s[a()],e.class)]);var w=d(g);bi(w,()=>e.children),c(_,g)};$(u,_=>{e.href?_(f):_(p,-1)})}c(t,l),Sr()}hf();/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const eh={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const th=t=>{for(const e in t)if(e.startsWith("aria-")||e==="role"||e==="title")return!0;return!1};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Ul=(...t)=>t.filter((e,r,a)=>!!e&&e.trim()!==""&&a.indexOf(e)===r).join(" ").trim();var rh=ns("<svg><!><!></svg>");function ft(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]),a=st(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);Cr(e,!1);let o=Pe(e,"name",8,void 0),i=Pe(e,"color",8,"currentColor"),s=Pe(e,"size",8,24),l=Pe(e,"strokeWidth",8,2),u=Pe(e,"absoluteStrokeWidth",8,!1),f=Pe(e,"iconNode",24,()=>[]);mv();var p=rh();ks(p,(w,k,S)=>({...eh,...w,...a,width:s(),height:s(),stroke:i(),"stroke-width":k,class:S}),[()=>th(a)?void 0:{"aria-hidden":"true"},()=>(La(u()),La(l()),La(s()),Ya(()=>u()?Number(l())*24/Number(s()):l())),()=>(La(Ul),La(o()),La(r),Ya(()=>Ul("lucide-icon","lucide",o()?`lucide-${o()}`:"",r.class)))]);var _=d(p);Ce(_,1,f,$e,(w,k)=>{var S=R(()=>Di(n(k),2));let b=()=>n(S)[0],C=()=>n(S)[1];var z=be(),P=ae(z);lv(P,b,!0,(E,ee)=>{ks(E,()=>({...C()}))}),c(w,z)});var g=m(_);it(g,e,"default",{}),c(t,p),Sr()}function nh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];ft(t,ut({name:"activity"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Rc(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M8 3 4 7l4 4"}],["path",{d:"M4 7h16"}],["path",{d:"m16 21 4-4-4-4"}],["path",{d:"M20 17H4"}]];ft(t,ut({name:"arrow-left-right"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ah(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"m12 5 7 7-7 7"}]];ft(t,ut({name:"arrow-right"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function oh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];ft(t,ut({name:"arrow-up"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function $i(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 7v14"}],["path",{d:"M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"}]];ft(t,ut({name:"book-open"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ri(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];ft(t,ut({name:"brain"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Wl(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 12h4"}],["path",{d:"M10 8h4"}],["path",{d:"M14 21v-3a2 2 0 0 0-4 0v3"}],["path",{d:"M6 10H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2"}],["path",{d:"M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"}]];ft(t,ut({name:"building-2"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function $s(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]];ft(t,ut({name:"chart-column"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function zi(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M20 6 9 17l-5-5"}]];ft(t,ut({name:"check"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function el(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m6 9 6 6 6-6"}]];ft(t,ut({name:"chevron-down"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Dc(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m18 15-6-6-6 6"}]];ft(t,ut({name:"chevron-up"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function jc(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m9 18 6-6-6-6"}]];ft(t,ut({name:"chevron-right"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Oa(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];ft(t,ut({name:"circle-alert"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Uo(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];ft(t,ut({name:"circle-check"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Jo(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];ft(t,ut({name:"clock"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function sh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];ft(t,ut({name:"code"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ih(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];ft(t,ut({name:"coffee"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Kl(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]];ft(t,ut({name:"copy"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Oo(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];ft(t,ut({name:"database"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Wo(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];ft(t,ut({name:"download"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function lh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["line",{x1:"5",x2:"19",y1:"9",y2:"9"}],["line",{x1:"5",x2:"19",y1:"15",y2:"15"}]];ft(t,ut({name:"equal"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Gl(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];ft(t,ut({name:"external-link"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function dh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];ft(t,ut({name:"eye"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function hn(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];ft(t,ut({name:"file-text"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ch(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];ft(t,ut({name:"github"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Jl(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];ft(t,ut({name:"key"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function uh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 8h.01"}],["path",{d:"M12 12h.01"}],["path",{d:"M14 8h.01"}],["path",{d:"M16 12h.01"}],["path",{d:"M18 8h.01"}],["path",{d:"M6 8h.01"}],["path",{d:"M7 16h10"}],["path",{d:"M8 12h.01"}],["rect",{width:"20",height:"16",x:"2",y:"4",rx:"2"}]];ft(t,ut({name:"keyboard"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ar(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];ft(t,ut({name:"loader-circle"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function fh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];ft(t,ut({name:"log-out"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Fc(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"m21 3-7 7"}],["path",{d:"m3 21 7-7"}],["path",{d:"M9 21H3v-6"}]];ft(t,ut({name:"maximize-2"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function vh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];ft(t,ut({name:"menu"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function zs(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];ft(t,ut({name:"message-square"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Vc(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m14 10 7-7"}],["path",{d:"M20 10h-6V4"}],["path",{d:"m3 21 7-7"}],["path",{d:"M4 14h6v6"}]];ft(t,ut({name:"minimize-2"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Bc(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}]];ft(t,ut({name:"minus"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ph(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];ft(t,ut({name:"panel-left-close"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Mi(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];ft(t,ut({name:"plus"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function hh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];ft(t,ut({name:"refresh-cw"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function aa(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];ft(t,ut({name:"search"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function mh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];ft(t,ut({name:"settings"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function xh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"}]];ft(t,ut({name:"shield"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function qc(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];ft(t,ut({name:"sparkles"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function gh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];ft(t,ut({name:"square"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ti(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"}]];ft(t,ut({name:"star"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ii(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];ft(t,ut({name:"table-2"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function _h(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];ft(t,ut({name:"terminal"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function bh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];ft(t,ut({name:"trash-2"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function xs(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M16 7h6v6"}],["path",{d:"m22 7-8.5 8.5-5-5L2 17"}]];ft(t,ut({name:"trending-up"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ko(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];ft(t,ut({name:"triangle-alert"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Hc(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["path",{d:"M16 3.128a4 4 0 0 1 0 7.744"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87"}],["circle",{cx:"9",cy:"7",r:"4"}]];ft(t,ut({name:"users"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function wh(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"}],["path",{d:"M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"}]];ft(t,ut({name:"wallet"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Yl(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];ft(t,ut({name:"wrench"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function za(t,e){const r=st(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];ft(t,ut({name:"x"},()=>r,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=ae(s);it(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}var yh=h("<!> 새 대화",1),kh=h('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),Ch=h('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),Sh=h('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),$h=h('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40"><span class="text-[10px] text-dl-text-dim font-mono"> </span></div>'),zh=h('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),Mh=h("<button><!></button>"),Th=h('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),Ih=h("<aside><!></aside>");function Ah(t,e){Cr(e,!0);let r=Pe(e,"conversations",19,()=>[]),a=Pe(e,"activeId",3,null),o=Pe(e,"open",3,!0),i=Pe(e,"version",3,""),s=Z("");function l(k){const S=new Date().setHours(0,0,0,0),b=S-864e5,C=S-7*864e5,z={오늘:[],어제:[],"이번 주":[],이전:[]};for(const E of k)E.updatedAt>=S?z.오늘.push(E):E.updatedAt>=b?z.어제.push(E):E.updatedAt>=C?z["이번 주"].push(E):z.이전.push(E);const P=[];for(const[E,ee]of Object.entries(z))ee.length>0&&P.push({label:E,items:ee});return P}let u=R(()=>n(s).trim()?r().filter(k=>k.title.toLowerCase().includes(n(s).toLowerCase())):r()),f=R(()=>l(n(u)));var p=Ih(),_=d(p);{var g=k=>{var S=zh(),b=m(d(S),2),C=d(b);Zp(C,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return e.onNewChat},children:(j,T)=>{var G=yh(),K=ae(G);Mi(K,{size:16}),c(j,G)},$$slots:{default:!0}});var z=m(b,2);{var P=j=>{var T=kh(),G=d(T),K=d(G);aa(K,{size:12,class:"text-dl-text-dim flex-shrink-0"});var ie=m(K,2);_a(ie,()=>n(s),U=>v(s,U)),c(j,T)};$(z,j=>{r().length>3&&j(P)})}var E=m(z,2);Ce(E,21,()=>n(f),$e,(j,T)=>{var G=Sh(),K=d(G),ie=d(K),U=m(K,2);Ce(U,17,()=>n(T).items,$e,(we,B)=>{var J=Ch(),le=d(J),X=d(le);zs(X,{size:14,class:"flex-shrink-0 opacity-50"});var O=m(X,2),W=d(O),F=m(le,2),ce=d(F);bh(ce,{size:12}),A(ne=>{Xe(J,1,ne),ar(le,"aria-current",n(B).id===a()?"true":void 0),I(W,n(B).title),ar(F,"aria-label",`${n(B).title} 삭제`)},[()=>ur(hr("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",n(B).id===a()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),ve("click",le,()=>{var ne;return(ne=e.onSelect)==null?void 0:ne.call(e,n(B).id)}),ve("click",F,ne=>{var D;ne.stopPropagation(),(D=e.onDelete)==null||D.call(e,n(B).id)}),c(we,J)}),A(()=>I(ie,n(T).label)),c(j,G)});var ee=m(E,2);{var se=j=>{var T=$h(),G=d(T),K=d(G);A(()=>I(K,`v${i()??""}`)),c(j,T)};$(ee,j=>{i()&&j(se)})}c(k,S)},w=k=>{var S=Th(),b=m(d(S),2),C=d(b);Mi(C,{size:18});var z=m(b,2);Ce(z,21,()=>r().slice(0,10),$e,(P,E)=>{var ee=Mh(),se=d(ee);zs(se,{size:16}),A(j=>{Xe(ee,1,j),ar(ee,"title",n(E).title)},[()=>ur(hr("p-2 rounded-lg transition-colors w-full flex justify-center",n(E).id===a()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),ve("click",ee,()=>{var j;return(j=e.onSelect)==null?void 0:j.call(e,n(E).id)}),c(P,ee)}),ve("click",b,function(...P){var E;(E=e.onNewChat)==null||E.apply(this,P)}),c(k,S)};$(_,k=>{o()?k(g):k(w,-1)})}A(k=>Xe(p,1,k),[()=>ur(hr("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",o()?"w-[260px]":"w-[52px]"))]),c(t,p),Sr()}Or(["click"]);var Eh=h('<button class="send-btn active"><!></button>'),Nh=h("<button><!></button>"),Ph=h('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),Lh=h('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),Oh=h('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),Rh=h('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function Uc(t,e){Cr(e,!0);let r=Pe(e,"inputText",15,""),a=Pe(e,"isLoading",3,!1),o=Pe(e,"large",3,!1),i=Pe(e,"placeholder",3,"메시지를 입력하세요..."),s=Z(Ut([])),l=Z(!1),u=Z(-1),f=null,p=Z(void 0);function _(T){var G;if(n(l)&&n(s).length>0){if(T.key==="ArrowDown"){T.preventDefault(),v(u,(n(u)+1)%n(s).length);return}if(T.key==="ArrowUp"){T.preventDefault(),v(u,n(u)<=0?n(s).length-1:n(u)-1,!0);return}if(T.key==="Enter"&&n(u)>=0){T.preventDefault(),k(n(s)[n(u)]);return}if(T.key==="Escape"){v(l,!1),v(u,-1);return}}T.key==="Enter"&&!T.shiftKey&&(T.preventDefault(),v(l,!1),(G=e.onSend)==null||G.call(e))}function g(T){T.target.style.height="auto",T.target.style.height=Math.min(T.target.scrollHeight,200)+"px"}function w(T){g(T);const G=r();f&&clearTimeout(f),G.length>=2&&!/\s/.test(G.slice(-1))?f=setTimeout(async()=>{var K;try{const ie=await Ji(G.trim());((K=ie.results)==null?void 0:K.length)>0?(v(s,ie.results.slice(0,6),!0),v(l,!0),v(u,-1)):v(l,!1)}catch{v(l,!1)}},300):v(l,!1)}function k(T){var G;r(`${T.corpName} `),v(l,!1),v(u,-1),(G=e.onCompanySelect)==null||G.call(e,T),n(p)&&n(p).focus()}function S(){setTimeout(()=>{v(l,!1)},200)}var b=Rh(),C=d(b),z=d(C);Qn(z,T=>v(p,T),()=>n(p));var P=m(z,2);{var E=T=>{var G=Eh(),K=d(G);gh(K,{size:14}),ve("click",G,function(...ie){var U;(U=e.onStop)==null||U.apply(this,ie)}),c(T,G)},ee=T=>{var G=Nh(),K=d(G);{let ie=R(()=>o()?18:16);oh(K,{get size(){return n(ie)},strokeWidth:2.5})}A((ie,U)=>{Xe(G,1,ie),G.disabled=U},[()=>ur(hr("send-btn",r().trim()&&"active")),()=>!r().trim()]),ve("click",G,()=>{var ie;v(l,!1),(ie=e.onSend)==null||ie.call(e)}),c(T,G)};$(P,T=>{a()&&e.onStop?T(E):T(ee,-1)})}var se=m(C,2);{var j=T=>{var G=Oh();Ce(G,21,()=>n(s),$e,(K,ie,U)=>{var we=Lh(),B=d(we);aa(B,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var J=m(B,2),le=d(J),X=d(le),O=m(le,2),W=d(O),F=m(J,2);{var ce=ne=>{var D=Ph(),H=d(D);A(()=>I(H,n(ie).sector)),c(ne,D)};$(F,ne=>{n(ie).sector&&ne(ce)})}A(ne=>{Xe(we,1,ne),I(X,n(ie).corpName),I(W,`${n(ie).stockCode??""} · ${(n(ie).market||"")??""}`)},[()=>ur(hr("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",U===n(u)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),ve("mousedown",we,()=>k(n(ie))),bn("mouseenter",we,()=>{v(u,U,!0)}),c(K,we)}),c(T,G)};$(se,T=>{n(l)&&n(s).length>0&&T(j)})}A(T=>{Xe(C,1,T),ar(z,"placeholder",i())},[()=>ur(hr("input-box",o()&&"large"))]),ve("keydown",z,_),ve("input",z,w),bn("blur",z,S),_a(z,r),c(t,b),Sr()}Or(["keydown","input","click","mousedown"]);var Dh=h('<button class="rounded-full border border-dl-border/60 bg-dl-bg-card/40 px-3 py-1.5 text-[12px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"> </button>'),jh=h(`<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[580px] flex flex-col items-center"><div class="relative mb-8"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p> <div class="mb-6 max-w-[520px] rounded-2xl border border-dl-border/50 bg-dl-bg-card/50 px-4 py-3 text-left"><div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">Evidence First</div> <div class="mt-2 text-[13px] leading-relaxed text-dl-text-muted">DartLab은 재무 수치와 서술 텍스트를 함께 읽고, 표준화된 계정과 원문 근거를 같은 흐름에서 확인하도록 설계되어 있습니다.
				DART와 EDGAR를 포함한 40개 모듈 이상의 기능 범위를 먼저 물어본 뒤 바로 탐색을 시작할 수 있습니다.</div></div> <div class="w-full"><!></div> <div class="mt-5 flex w-full flex-wrap justify-center gap-2"></div></div></div>`);function Fh(t,e){Cr(e,!0);let r=Pe(e,"inputText",15,"");const a=["지금 dartlab에서 할 수 있는 기능을 먼저 정리해줘","EDGAR에서 추가로 받을 수 있는 데이터와 방법을 알려줘","OpenDart와 OpenEdgar로 가능한 일을 비교해줘","GPT 연결 시 현재 UI에서 가능한 코딩 작업 범위를 알려줘"];var o=jh(),i=d(o),s=m(d(i),8),l=d(s);Uc(l,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return e.onSend},get onCompanySelect(){return e.onCompanySelect},get inputText(){return r()},set inputText(f){r(f)}});var u=m(s,2);Ce(u,21,()=>a,$e,(f,p)=>{var _=Dh(),g=d(_);A(()=>I(g,n(p))),ve("click",_,()=>{var w;return(w=e.onSend)==null?void 0:w.call(e,n(p))}),c(f,_)}),c(t,o),Sr()}Or(["click"]);var Vh=h("<span><!></span>");function Ro(t,e){Cr(e,!0);let r=Pe(e,"variant",3,"default");const a={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var o=Vh(),i=d(o);bi(i,()=>e.children),A(s=>Xe(o,1,s),[()=>ur(hr("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",a[r()],e.class))]),c(t,o),Sr()}function Bh(t){const e=t.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(e)||e==="-"||e==="0"}function Ma(t){if(!t)return"";let e=[],r=[],a=t.replace(/```(\w*)\n([\s\S]*?)```/g,(i,s,l)=>{const u=e.length;return e.push(l.trimEnd()),`
%%CODE_${u}%%
`});a=a.replace(/((?:^\|.+\|$\n?)+)/gm,i=>{const s=i.trim().split(`
`).filter(g=>g.trim());let l=null,u=-1,f=[];for(let g=0;g<s.length;g++)if(s[g].slice(1,-1).split("|").map(k=>k.trim()).every(k=>/^[\-:]+$/.test(k))){u=g;break}u>0?(l=s[u-1],f=s.slice(u+1)):(u===0||(l=s[0]),f=s.slice(1));let p="<table>";if(l){const g=l.slice(1,-1).split("|").map(w=>w.trim());p+="<thead><tr>"+g.map(w=>`<th>${w.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(f.length>0){p+="<tbody>";for(const g of f){const w=g.slice(1,-1).split("|").map(k=>k.trim());p+="<tr>"+w.map(k=>{let S=k.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${Bh(k)?' class="num"':""}>${S}</td>`}).join("")+"</tr>"}p+="</tbody>"}p+="</table>";let _=r.length;return r.push(p),`
%%TABLE_${_}%%
`});let o=a.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");o=o.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,i=>"<ul>"+i.replace(/<br>/g,"")+"</ul>");for(let i=0;i<r.length;i++)o=o.replace(`%%TABLE_${i}%%`,r[i]);for(let i=0;i<e.length;i++){const s=e[i].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");o=o.replace(`%%CODE_${i}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${i}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${s}</code></pre></div>`)}return o=o.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(i,s)=>s.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+o+"</p>"}var qh=h('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),Hh=h('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),Uh=h('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),Wh=h('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),Kh=h('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!> <!> <!> <!></div></div>'),Gh=h('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),Jh=h('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),Yh=h('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),Xh=h("<span> </span>"),Qh=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-bold border bg-red-500/10 text-red-400 border-red-500/20"> </span>'),Zh=h('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-1.5"><!> <!></div>'),em=h('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!> <!></button>'),tm=h("<button><!> </button>"),rm=h('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),nm=h('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),am=h('<!> <span class="text-dl-text-dim"> </span>',1),om=h('<div class="flex items-center gap-2 text-[11px]"><!></div>'),sm=h('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),im=h('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),lm=h('<div class="message-committed"><!></div>'),dm=h('<div><div class="message-live-label"> </div> <pre> </pre></div>'),cm=h('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),um=h('<span class="text-dl-accent/60"> </span>'),fm=h('<span class="text-dl-success/60"> </span>'),vm=h('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),pm=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),hm=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),mm=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),xm=h('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),gm=h("<!>  <div><!> <!></div> <!>",1),_m=h('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),bm=h('<span class="text-[10px] text-dl-text-dim"> </span>'),wm=h('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),ym=h("<button> </button>"),km=h('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),Cm=h("<button>시스템 프롬프트</button>"),Sm=h("<button>LLM 입력</button>"),$m=h('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),zm=h('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),Mm=h('<span class="text-dl-text"> </span>'),Tm=h('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),Im=h('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),Am=h('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Em=h("<!> <!>",1);function Nm(t,e){Cr(e,!0);let r=Z(null),a=Z("context"),o=Z("raw"),i=R(()=>{var D,H,te,Y,xe,ke;if(!e.message.loading)return"";if(e.message.text)return"응답 작성 중";if(((D=e.message.toolEvents)==null?void 0:D.length)>0){const re=[...e.message.toolEvents].reverse().find(ot=>ot.type==="call"),Fe=((H=re==null?void 0:re.arguments)==null?void 0:H.module)||((te=re==null?void 0:re.arguments)==null?void 0:te.keyword)||"";return`도구 실행 중 — ${(re==null?void 0:re.name)||""}${Fe?` (${Fe})`:""}`}if(((Y=e.message.contexts)==null?void 0:Y.length)>0){const re=e.message.contexts[e.message.contexts.length-1];return`데이터 분석 중 — ${(re==null?void 0:re.label)||(re==null?void 0:re.module)||""}`}return e.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(xe=e.message.meta)!=null&&xe.company?`${e.message.meta.company} 데이터 검색 중`:(ke=e.message.meta)!=null&&ke.includedModules?"분석 모듈 선택 완료":"생각 중"}),s=R(()=>{var D;return e.message.company||((D=e.message.meta)==null?void 0:D.company)||null});const l={capability:"기능 탐색",coding:"코딩 작업",company_explore:"회사 탐색",company_analysis:"회사 분석",follow_up:"후속 질문",general_chat:"일반 대화"};let u=R(()=>{var D;return(D=e.message.meta)!=null&&D.dialogueMode?l[e.message.meta.dialogueMode]||e.message.meta.dialogueMode:null}),f=R(()=>{var D,H,te;return e.message.systemPrompt||e.message.userContent||((D=e.message.contexts)==null?void 0:D.length)>0||((H=e.message.meta)==null?void 0:H.includedModules)||((te=e.message.toolEvents)==null?void 0:te.length)>0}),p=R(()=>{var H;const D=(H=e.message.meta)==null?void 0:H.dataYearRange;return D?typeof D=="string"?D:D.min_year&&D.max_year?`${D.min_year}~${D.max_year}년`:null:null});function _(D){if(!D)return 0;const H=(D.match(/[\uac00-\ud7af]/g)||[]).length,te=D.length-H;return Math.round(H*1.5+te/3.5)}function g(D){return D>=1e3?(D/1e3).toFixed(1)+"k":String(D)}let w=R(()=>{var H;let D=0;if(e.message.systemPrompt&&(D+=_(e.message.systemPrompt)),e.message.userContent)D+=_(e.message.userContent);else if(((H=e.message.contexts)==null?void 0:H.length)>0)for(const te of e.message.contexts)D+=_(te.text);return D}),k=R(()=>_(e.message.text)),S=Z(void 0);const b=/^\s*\|.+\|\s*$/;function C(D,H){if(!D)return{committed:"",draft:"",draftType:"none"};if(!H)return{committed:D,draft:"",draftType:"none"};const te=D.split(`
`);let Y=te.length;D.endsWith(`
`)||(Y=Math.min(Y,te.length-1));let xe=0,ke=-1;for(let lt=0;lt<te.length;lt++)te[lt].trim().startsWith("```")&&(xe+=1,ke=lt);xe%2===1&&ke>=0&&(Y=Math.min(Y,ke));let re=-1;for(let lt=te.length-1;lt>=0;lt--){const at=te[lt];if(!at.trim())break;if(b.test(at))re=lt;else{re=-1;break}}if(re>=0&&(Y=Math.min(Y,re)),Y<=0)return{committed:"",draft:D,draftType:re===0?"table":xe%2===1?"code":"text"};const Fe=te.slice(0,Y).join(`
`),ot=te.slice(Y).join(`
`);let nt="text";return ot&&re>=Y?nt="table":ot&&xe%2===1&&(nt="code"),{committed:Fe,draft:ot,draftType:nt}}const z='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',P='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function E(D){var xe;const H=D.target.closest(".code-copy-btn");if(!H)return;const te=H.closest(".code-block-wrap"),Y=((xe=te==null?void 0:te.querySelector("code"))==null?void 0:xe.textContent)||"";navigator.clipboard.writeText(Y).then(()=>{H.innerHTML=P,setTimeout(()=>{H.innerHTML=z},2e3)})}function ee(D){if(e.onOpenEvidence){e.onOpenEvidence("contexts",D);return}v(r,D,!0),v(a,"context"),v(o,"rendered")}function se(){if(e.onOpenEvidence){e.onOpenEvidence("system");return}v(r,0),v(a,"system"),v(o,"raw")}function j(){if(e.onOpenEvidence){e.onOpenEvidence("snapshot");return}v(r,0),v(a,"snapshot")}function T(D){var H;if(e.onOpenEvidence){const te=(H=e.message.toolEvents)==null?void 0:H[D];e.onOpenEvidence((te==null?void 0:te.type)==="result"?"tool-results":"tool-calls",D);return}v(r,D,!0),v(a,"tool"),v(o,"raw")}function G(){if(e.onOpenEvidence){e.onOpenEvidence("input");return}v(r,0),v(a,"userContent"),v(o,"raw")}function K(){v(r,null)}function ie(D){var H,te,Y,xe;return D?D.type==="call"?((H=D.arguments)==null?void 0:H.module)||((te=D.arguments)==null?void 0:te.keyword)||((Y=D.arguments)==null?void 0:Y.engine)||((xe=D.arguments)==null?void 0:xe.name)||"":typeof D.result=="string"?D.result.slice(0,120):D.result&&typeof D.result=="object"&&(D.result.module||D.result.status||D.result.name)||"":""}let U=R(()=>(e.message.toolEvents||[]).filter(D=>D.type==="call")),we=R(()=>(e.message.toolEvents||[]).filter(D=>D.type==="result")),B=R(()=>C(e.message.text||"",e.message.loading)),J=R(()=>{var H,te,Y;const D=[];return((te=(H=e.message.meta)==null?void 0:H.includedModules)==null?void 0:te.length)>0&&D.push({label:`모듈 ${e.message.meta.includedModules.length}개`,icon:Oo}),((Y=e.message.contexts)==null?void 0:Y.length)>0&&D.push({label:`컨텍스트 ${e.message.contexts.length}건`,icon:dh}),n(U).length>0&&D.push({label:`툴 호출 ${n(U).length}건`,icon:Yl}),n(we).length>0&&D.push({label:`툴 결과 ${n(we).length}건`,icon:Uo}),e.message.systemPrompt&&D.push({label:"시스템 프롬프트",icon:ri}),e.message.userContent&&D.push({label:"LLM 입력",icon:hn}),D}),le=R(()=>{var H,te,Y;if(!e.message.loading)return[];const D=[];return(H=e.message.meta)!=null&&H.company&&D.push({label:`${e.message.meta.company} 인식`,done:!0}),e.message.snapshot&&D.push({label:"핵심 수치 확인",done:!0}),(te=e.message.meta)!=null&&te.includedModules&&D.push({label:`모듈 ${e.message.meta.includedModules.length}개 선택`,done:!0}),((Y=e.message.contexts)==null?void 0:Y.length)>0&&D.push({label:`데이터 ${e.message.contexts.length}건 로드`,done:!0}),e.message.systemPrompt&&D.push({label:"프롬프트 조립",done:!0}),e.message.text?D.push({label:"응답 작성 중",done:!1}):D.push({label:n(i)||"준비 중",done:!1}),D});var X=Em(),O=ae(X);{var W=D=>{var H=qh(),te=m(d(H),2),Y=d(te),xe=d(Y);A(()=>I(xe,e.message.text)),c(D,H)},F=D=>{var H=_m(),te=m(d(H),2),Y=d(te);{var xe=vt=>{var tt=Kh(),Qe=d(tt),yt=d(Qe);nh(yt,{size:11});var $t=m(Qe,4),Et=d($t);{var or=Ie=>{Ro(Ie,{variant:"muted",children:(je,Re)=>{var De=Wn();A(()=>I(De,n(s))),c(je,De)},$$slots:{default:!0}})};$(Et,Ie=>{n(s)&&Ie(or)})}var x=m(Et,2);{var N=Ie=>{Ro(Ie,{variant:"muted",children:(je,Re)=>{var De=Wn();A(pt=>I(De,pt),[()=>e.message.meta.market.toUpperCase()]),c(je,De)},$$slots:{default:!0}})};$(x,Ie=>{var je;(je=e.message.meta)!=null&&je.market&&Ie(N)})}var L=m(x,2);{var q=Ie=>{Ro(Ie,{variant:"accent",children:(je,Re)=>{var De=Wn();A(()=>I(De,n(u))),c(je,De)},$$slots:{default:!0}})};$(L,Ie=>{n(u)&&Ie(q)})}var y=m(L,2);{var V=Ie=>{Ro(Ie,{variant:"muted",children:(je,Re)=>{var De=Wn();A(()=>I(De,e.message.meta.topicLabel)),c(je,De)},$$slots:{default:!0}})};$(y,Ie=>{var je;(je=e.message.meta)!=null&&je.topicLabel&&Ie(V)})}var Q=m(y,2);{var he=Ie=>{Ro(Ie,{variant:"accent",children:(je,Re)=>{var De=Wn();A(()=>I(De,n(p))),c(je,De)},$$slots:{default:!0}})};$(Q,Ie=>{n(p)&&Ie(he)})}var fe=m(Q,2);{var me=Ie=>{var je=be(),Re=ae(je);Ce(Re,17,()=>e.message.contexts,$e,(De,pt,Ze)=>{var Bt=Hh(),ge=d(Bt);Oo(ge,{size:10,class:"flex-shrink-0"});var Ve=m(ge);A(()=>I(Ve,` ${(n(pt).label||n(pt).module)??""}`)),ve("click",Bt,()=>ee(Ze)),c(De,Bt)}),c(Ie,je)},Ae=Ie=>{var je=Uh(),Re=d(je);Oo(Re,{size:10,class:"flex-shrink-0"});var De=m(Re);A(()=>I(De,` 모듈 ${e.message.meta.includedModules.length??""}개`)),c(Ie,je)};$(fe,Ie=>{var je,Re,De;((je=e.message.contexts)==null?void 0:je.length)>0?Ie(me):((De=(Re=e.message.meta)==null?void 0:Re.includedModules)==null?void 0:De.length)>0&&Ie(Ae,1)})}var qe=m(fe,2);Ce(qe,17,()=>n(J),$e,(Ie,je)=>{var Re=Wh(),De=d(Re);wo(De,()=>n(je).icon,(Ze,Bt)=>{Bt(Ze,{size:10,class:"flex-shrink-0"})});var pt=m(De);A(()=>I(pt,` ${n(je).label??""}`)),ve("click",Re,()=>{n(je).label.startsWith("컨텍스트")?ee(0):n(je).label.startsWith("툴 호출")?e.onOpenEvidence?e.onOpenEvidence("tool-calls",0):T(0):n(je).label.startsWith("툴 결과")?e.onOpenEvidence?e.onOpenEvidence("tool-results",0):T((e.message.toolEvents||[]).findIndex(Ze=>Ze.type==="result")):n(je).label==="시스템 프롬프트"?se():n(je).label==="LLM 입력"&&G()}),c(Ie,Re)}),c(vt,tt)};$(Y,vt=>{var tt,Qe;(n(s)||n(p)||((tt=e.message.contexts)==null?void 0:tt.length)>0||(Qe=e.message.meta)!=null&&Qe.includedModules||n(J).length>0)&&vt(xe)})}var ke=m(Y,2);{var re=vt=>{var tt=em(),Qe=d(tt);Ce(Qe,21,()=>e.message.snapshot.items,$e,(x,N)=>{const L=R(()=>n(N).status==="good"?"text-dl-success":n(N).status==="danger"?"text-dl-primary-light":n(N).status==="caution"?"text-amber-400":"text-dl-text");var q=Gh(),y=d(q),V=d(y),Q=m(y,2),he=d(Q);A(fe=>{I(V,n(N).label),Xe(Q,1,fe),I(he,n(N).value)},[()=>ur(hr("text-[14px] font-semibold leading-snug mt-0.5",n(L)))]),c(x,q)});var yt=m(Qe,2);{var $t=x=>{var N=Yh();Ce(N,21,()=>e.message.snapshot.warnings,$e,(L,q)=>{var y=Jh(),V=d(y);Ko(V,{size:10});var Q=m(V);A(()=>I(Q,` ${n(q)??""}`)),c(L,y)}),c(x,N)};$(yt,x=>{var N;((N=e.message.snapshot.warnings)==null?void 0:N.length)>0&&x($t)})}var Et=m(yt,2);{var or=x=>{const N=R(()=>({performance:"실적",profitability:"수익성",health:"건전성",cashflow:"현금흐름",governance:"지배구조",risk:"리스크",opportunity:"기회"}));var L=Zh(),q=d(L);Ce(q,17,()=>Object.entries(e.message.snapshot.grades),$e,(Q,he)=>{var fe=R(()=>Di(n(he),2));let me=()=>n(fe)[0],Ae=()=>n(fe)[1];const qe=R(()=>Ae()==="A"?"bg-emerald-500/15 text-emerald-400 border-emerald-500/30":Ae()==="B"?"bg-blue-500/15 text-blue-400 border-blue-500/30":Ae()==="C"?"bg-amber-500/15 text-amber-400 border-amber-500/30":Ae()==="D"?"bg-orange-500/15 text-orange-400 border-orange-500/30":Ae()==="F"?"bg-red-500/15 text-red-400 border-red-500/30":"bg-dl-border/10 text-dl-text-dim border-dl-border/20");var Ie=Xh(),je=d(Ie);A(()=>{Xe(Ie,1,`px-1.5 py-0.5 rounded text-[9px] font-bold border ${n(qe)??""}`),I(je,`${(n(N)[me()]||me())??""} ${Ae()??""}`)}),c(Q,Ie)});var y=m(q,2);{var V=Q=>{var he=Qh(),fe=d(he);A(()=>I(fe,`이상치 ${e.message.snapshot.anomalyCount??""}건`)),c(Q,he)};$(y,Q=>{e.message.snapshot.anomalyCount>0&&Q(V)})}c(x,L)};$(Et,x=>{e.message.snapshot.grades&&x(or)})}ve("click",tt,j),c(vt,tt)};$(ke,vt=>{var tt,Qe;((Qe=(tt=e.message.snapshot)==null?void 0:tt.items)==null?void 0:Qe.length)>0&&vt(re)})}var Fe=m(ke,2);{var ot=vt=>{var tt=rm(),Qe=d(tt),yt=m(d(Qe),4);Ce(yt,21,()=>e.message.toolEvents,$e,($t,Et,or)=>{const x=R(()=>ie(n(Et)));var N=tm(),L=d(N);{var q=Q=>{Yl(Q,{size:11})},y=Q=>{Uo(Q,{size:11})};$(L,Q=>{n(Et).type==="call"?Q(q):Q(y,-1)})}var V=m(L);A(Q=>{Xe(N,1,Q),I(V,` ${(n(Et).type==="call"?n(Et).name:`${n(Et).name} 결과`)??""}${n(x)?`: ${n(x)}`:""}`)},[()=>ur(hr("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",n(Et).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),ve("click",N,()=>T(or)),c($t,N)}),c(vt,tt)};$(Fe,vt=>{var tt;((tt=e.message.toolEvents)==null?void 0:tt.length)>0&&vt(ot)})}var nt=m(Fe,2);{var lt=vt=>{var tt=sm(),Qe=d(tt);Ce(Qe,21,()=>n(le),$e,(yt,$t)=>{var Et=om(),or=d(Et);{var x=L=>{var q=nm(),y=m(ae(q),2),V=d(y);A(()=>I(V,n($t).label)),c(L,q)},N=L=>{var q=am(),y=ae(q);Ar(y,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var V=m(y,2),Q=d(V);A(()=>I(Q,n($t).label)),c(L,q)};$(or,L=>{n($t).done?L(x):L(N,-1)})}c(yt,Et)}),c(vt,tt)},at=vt=>{var tt=gm(),Qe=ae(tt);{var yt=y=>{var V=im(),Q=d(V);Ar(Q,{size:12,class:"animate-spin flex-shrink-0"});var he=m(Q,2),fe=d(he);A(()=>I(fe,n(i))),c(y,V)};$(Qe,y=>{e.message.loading&&y(yt)})}var $t=m(Qe,2),Et=d($t);{var or=y=>{var V=lm(),Q=d(V);Nn(Q,()=>Ma(n(B).committed)),c(y,V)};$(Et,y=>{n(B).committed&&y(or)})}var x=m(Et,2);{var N=y=>{var V=dm(),Q=d(V),he=d(Q),fe=m(Q,2),me=d(fe);A(Ae=>{Xe(V,1,Ae),I(he,n(B).draftType==="table"?"표 구성 중":n(B).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),I(me,n(B).draft)},[()=>ur(hr("message-live-tail",n(B).draftType==="table"&&"message-draft-table",n(B).draftType==="code"&&"message-draft-code"))]),c(y,V)};$(x,y=>{n(B).draft&&y(N)})}Qn($t,y=>v(S,y),()=>n(S));var L=m($t,2);{var q=y=>{var V=xm(),Q=d(V);{var he=pt=>{var Ze=cm(),Bt=d(Ze);Jo(Bt,{size:10});var ge=m(Bt);A(()=>I(ge,` ${e.message.duration??""}초`)),c(pt,Ze)};$(Q,pt=>{e.message.duration&&pt(he)})}var fe=m(Q,2);{var me=pt=>{var Ze=vm(),Bt=d(Ze);{var ge=ye=>{var dt=um(),Be=d(dt);A(Oe=>I(Be,`↑${Oe??""}`),[()=>g(n(w))]),c(ye,dt)};$(Bt,ye=>{n(w)>0&&ye(ge)})}var Ve=m(Bt,2);{var Me=ye=>{var dt=fm(),Be=d(dt);A(Oe=>I(Be,`↓${Oe??""}`),[()=>g(n(k))]),c(ye,dt)};$(Ve,ye=>{n(k)>0&&ye(Me)})}c(pt,Ze)};$(fe,pt=>{(n(w)>0||n(k)>0)&&pt(me)})}var Ae=m(fe,2);{var qe=pt=>{var Ze=pm(),Bt=d(Ze);hh(Bt,{size:10}),ve("click",Ze,()=>{var ge;return(ge=e.onRegenerate)==null?void 0:ge.call(e)}),c(pt,Ze)};$(Ae,pt=>{e.onRegenerate&&pt(qe)})}var Ie=m(Ae,2);{var je=pt=>{var Ze=hm(),Bt=d(Ze);ri(Bt,{size:10}),ve("click",Ze,se),c(pt,Ze)};$(Ie,pt=>{e.message.systemPrompt&&pt(je)})}var Re=m(Ie,2);{var De=pt=>{var Ze=mm(),Bt=d(Ze);hn(Bt,{size:10});var ge=m(Bt);A((Ve,Me)=>I(ge,` LLM 입력 (${Ve??""}자 · ~${Me??""}tok)`),[()=>e.message.userContent.length.toLocaleString(),()=>g(_(e.message.userContent))]),ve("click",Ze,G),c(pt,Ze)};$(Re,pt=>{e.message.userContent&&pt(De)})}c(y,V)};$(L,y=>{!e.message.loading&&(e.message.duration||n(f)||e.onRegenerate)&&y(q)})}A(y=>Xe($t,1,y),[()=>ur(hr("prose-dartlab message-body text-[15px] leading-[1.75]",e.message.error&&"text-dl-primary"))]),ve("click",$t,E),c(vt,tt)};$(nt,vt=>{e.message.loading&&!e.message.text?vt(lt):vt(at,-1)})}c(D,H)};$(O,D=>{e.message.role==="user"?D(W):D(F,-1)})}var ce=m(O,2);{var ne=D=>{const H=R(()=>n(a)==="system"),te=R(()=>n(a)==="userContent"),Y=R(()=>n(a)==="context"),xe=R(()=>n(a)==="snapshot"),ke=R(()=>n(a)==="tool"),re=R(()=>{var ge;return n(Y)?(ge=e.message.contexts)==null?void 0:ge[n(r)]:null}),Fe=R(()=>{var ge;return n(ke)?(ge=e.message.toolEvents)==null?void 0:ge[n(r)]:null}),ot=R(()=>{var ge,Ve,Me,ye,dt;return n(xe)?"핵심 수치 (원본 데이터)":n(H)?"시스템 프롬프트":n(te)?"LLM에 전달된 입력":n(ke)?((ge=n(Fe))==null?void 0:ge.type)==="call"?`${(Ve=n(Fe))==null?void 0:Ve.name} 호출`:`${(Me=n(Fe))==null?void 0:Me.name} 결과`:((ye=n(re))==null?void 0:ye.label)||((dt=n(re))==null?void 0:dt.module)||""}),nt=R(()=>{var ge;return n(xe)?JSON.stringify(e.message.snapshot,null,2):n(H)?e.message.systemPrompt:n(te)?e.message.userContent:n(ke)?JSON.stringify(n(Fe),null,2):(ge=n(re))==null?void 0:ge.text});var lt=Am(),at=d(lt),vt=d(at),tt=d(vt),Qe=d(tt),yt=d(Qe);{var $t=ge=>{Oo(ge,{size:15,class:"text-dl-success flex-shrink-0"})},Et=ge=>{ri(ge,{size:15,class:"text-dl-primary-light flex-shrink-0"})},or=ge=>{hn(ge,{size:15,class:"text-dl-accent flex-shrink-0"})},x=ge=>{Oo(ge,{size:15,class:"flex-shrink-0"})};$(yt,ge=>{n(xe)?ge($t):n(H)?ge(Et,1):n(te)?ge(or,2):ge(x,-1)})}var N=m(yt,2),L=d(N),q=m(N,2);{var y=ge=>{var Ve=bm(),Me=d(Ve);A(ye=>I(Me,`(${ye??""}자)`),[()=>{var ye,dt;return(dt=(ye=n(nt))==null?void 0:ye.length)==null?void 0:dt.toLocaleString()}]),c(ge,Ve)};$(q,ge=>{n(H)&&ge(y)})}var V=m(Qe,2),Q=d(V);{var he=ge=>{var Ve=wm(),Me=d(Ve),ye=d(Me);hn(ye,{size:11});var dt=m(Me,2),Be=d(dt);sh(Be,{size:11}),A((Oe,rt)=>{Xe(Me,1,Oe),Xe(dt,1,rt)},[()=>ur(hr("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(o)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>ur(hr("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(o)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),ve("click",Me,()=>v(o,"rendered")),ve("click",dt,()=>v(o,"raw")),c(ge,Ve)};$(Q,ge=>{n(Y)&&ge(he)})}var fe=m(Q,2),me=d(fe);za(me,{size:18});var Ae=m(tt,2);{var qe=ge=>{var Ve=km(),Me=d(Ve);Ce(Me,21,()=>e.message.contexts,$e,(ye,dt,Be)=>{var Oe=ym(),rt=d(Oe);A(kt=>{Xe(Oe,1,kt),I(rt,e.message.contexts[Be].label||e.message.contexts[Be].module)},[()=>ur(hr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",Be===n(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),ve("click",Oe,()=>{v(r,Be,!0)}),c(ye,Oe)}),c(ge,Ve)};$(Ae,ge=>{var Ve;n(Y)&&((Ve=e.message.contexts)==null?void 0:Ve.length)>1&&ge(qe)})}var Ie=m(Ae,2);{var je=ge=>{var Ve=$m(),Me=d(Ve),ye=d(Me);{var dt=rt=>{var kt=Cm();A(Xt=>Xe(kt,1,Xt),[()=>ur(hr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(H)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),ve("click",kt,()=>{v(a,"system")}),c(rt,kt)};$(ye,rt=>{e.message.systemPrompt&&rt(dt)})}var Be=m(ye,2);{var Oe=rt=>{var kt=Sm();A(Xt=>Xe(kt,1,Xt),[()=>ur(hr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(te)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),ve("click",kt,()=>{v(a,"userContent")}),c(rt,kt)};$(Be,rt=>{e.message.userContent&&rt(Oe)})}c(ge,Ve)};$(Ie,ge=>{!n(Y)&&!n(xe)&&!n(ke)&&ge(je)})}var Re=m(vt,2),De=d(Re);{var pt=ge=>{var Ve=zm(),Me=d(Ve);Nn(Me,()=>{var ye;return Ma((ye=n(re))==null?void 0:ye.text)}),c(ge,Ve)},Ze=ge=>{var Ve=Tm(),Me=d(Ve),ye=m(d(Me),2),dt=d(ye),Be=m(dt);{var Oe=It=>{var fr=Mm(),_r=d(fr);A(br=>I(_r,br),[()=>ie(n(Fe))]),c(It,fr)},rt=R(()=>ie(n(Fe)));$(Be,It=>{n(rt)&&It(Oe)})}var kt=m(Me,2),Xt=d(kt);A(()=>{var It;I(dt,`${((It=n(Fe))==null?void 0:It.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),I(Xt,n(nt))}),c(ge,Ve)},Bt=ge=>{var Ve=Im(),Me=d(Ve);A(()=>I(Me,n(nt))),c(ge,Ve)};$(De,ge=>{n(Y)&&n(o)==="rendered"?ge(pt):n(ke)?ge(Ze,1):ge(Bt,-1)})}A(()=>I(L,n(ot))),ve("click",lt,ge=>{ge.target===ge.currentTarget&&K()}),ve("keydown",lt,ge=>{ge.key==="Escape"&&K()}),ve("click",fe,K),c(D,lt)};$(ce,D=>{n(r)!==null&&D(ne)})}c(t,X),Sr()}Or(["click","keydown"]);var Pm=h('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),Lm=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),Om=h('<div class="flex justify-end gap-2 mb-1.5"><!></div>'),Rm=h('<div class="flex items-center gap-1.5 px-3 py-1 text-[10px] text-dl-text-dim"><span class="px-1.5 py-0.5 rounded bg-dl-accent/10 text-dl-accent-light border border-dl-accent/20 font-mono"> <!></span> <span>보는 중 — AI가 이 섹션을 참조합니다</span></div>'),Dm=h('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8"><!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!> <!></div></div></div>');function jm(t,e){Cr(e,!0);function r(B){if(o())return!1;for(let J=a().length-1;J>=0;J--)if(a()[J].role==="assistant"&&!a()[J].error&&a()[J].text)return J===B;return!1}let a=Pe(e,"messages",19,()=>[]),o=Pe(e,"isLoading",3,!1),i=Pe(e,"inputText",15,""),s=Pe(e,"scrollTrigger",3,0);Pe(e,"selectedCompany",3,null);let l=Pe(e,"viewerContext",3,null);function u(B){return(J,le)=>{var O,W,F,ce;(O=e.onOpenEvidence)==null||O.call(e,J,le);let X;if(J==="contexts")X=(W=B.contexts)==null?void 0:W[le];else if(J==="snapshot")X={label:"핵심 수치",module:"snapshot",text:JSON.stringify(B.snapshot,null,2)};else if(J==="system")X={label:"시스템 프롬프트",module:"system",text:B.systemPrompt};else if(J==="input")X={label:"LLM 입력",module:"input",text:B.userContent};else if(J==="tool-calls"||J==="tool-results"){const ne=(F=B.toolEvents)==null?void 0:F[le];X={label:`${(ne==null?void 0:ne.name)||"도구"} ${(ne==null?void 0:ne.type)==="call"?"호출":"결과"}`,module:"tool",text:JSON.stringify(ne,null,2)}}X&&((ce=e.onOpenData)==null||ce.call(e,X))}}let f,p,_=Z(!0),g=Z(!1),w=Z(!0);function k(){if(!f)return;const{scrollTop:B,scrollHeight:J,clientHeight:le}=f;v(w,J-B-le<96),n(w)?(v(_,!0),v(g,!1)):(v(_,!1),v(g,!0))}function S(B="smooth"){p&&(p.scrollIntoView({block:"end",behavior:B}),v(_,!0),v(g,!1))}xr(()=>{s(),!(!f||!p)&&requestAnimationFrame(()=>{!f||!p||(n(_)||n(w)?(p.scrollIntoView({block:"end",behavior:o()?"auto":"smooth"}),v(g,!1)):v(g,!0))})});var b=Dm(),C=d(b),z=d(C),P=d(z);Ce(P,17,a,$e,(B,J,le)=>{{let X=R(()=>r(le)?e.onRegenerate:void 0),O=R(()=>e.onOpenData?u(n(J)):void 0);Nm(B,{get message(){return n(J)},get onRegenerate(){return n(X)},get onOpenEvidence(){return n(O)}})}});var E=m(P,2);Qn(E,B=>p=B,()=>p),Qn(C,B=>f=B,()=>f);var ee=m(C,2);{var se=B=>{var J=Pm(),le=d(J);ve("click",le,()=>S("smooth")),c(B,J)};$(ee,B=>{n(g)&&B(se)})}var j=m(ee,2),T=d(j),G=d(T);{var K=B=>{var J=Om(),le=d(J);{var X=O=>{var W=Lm(),F=d(W);Wo(F,{size:10}),ve("click",W,function(...ce){var ne;(ne=e.onExport)==null||ne.apply(this,ce)}),c(O,W)};$(le,O=>{a().length>1&&e.onExport&&O(X)})}c(B,J)};$(G,B=>{o()||B(K)})}var ie=m(G,2);{var U=B=>{var J=Rm(),le=d(J),X=d(le),O=m(X);{var W=F=>{var ce=Wn();A(()=>I(ce,` (${l().period??""})`)),c(F,ce)};$(O,F=>{l().period&&F(W)})}A(()=>I(X,l().topicLabel||l().topic)),c(B,J)};$(ie,B=>{var J;(J=l())!=null&&J.topic&&B(U)})}var we=m(ie,2);Uc(we,{get isLoading(){return o()},placeholder:"메시지를 입력하세요...",get onSend(){return e.onSend},get onStop(){return e.onStop},get onCompanySelect(){return e.onCompanySelect},get inputText(){return i()},set inputText(B){i(B)}}),bn("scroll",C,k),c(t,b),Sr()}Or(["click"]);var Fm=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!> <span class="text-[13px]">공시 데이터 로딩 중...</span></div>'),Vm=h('<div class="text-[11px] text-dl-text-dim"> </div>'),Bm=h('<button><!> <span class="truncate flex-1"> </span></button>'),qm=h('<div class="py-0.5"></div>'),Hm=h('<div><button class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] opacity-30 font-normal"> </span></button> <!></div>'),Um=h('<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50"><div class="px-3 py-2.5 border-b border-dl-border/20"><!></div> <!></nav>'),Wm=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim"><!> <p class="text-[13px]">좌측에서 섹션을 선택하세요</p></div>'),Km=h('<div class="text-[10px] text-dl-text-dim/50 mb-0.5"> </div>'),Gm=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!></div>'),Jm=h('<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>'),Ym=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Xm=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Qm=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Zm=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),ex=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),tx=h('<div class="vw-heading-node svelte-1l2nqwu"><!></div>'),rx=h('<div class="vw-heading-block svelte-1l2nqwu"></div>'),nx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),ax=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),ox=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),sx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),ix=h('<button><span class="vw-timeline-label svelte-1l2nqwu"> </span></button>'),lx=h('<div class="vw-section-timeline svelte-1l2nqwu"></div>'),dx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),cx=h('<span class="vw-meta-pill svelte-1l2nqwu">비교 없음</span>'),ux=h('<div class="vw-section-actions svelte-1l2nqwu"><span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span></div>'),fx=h('<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span> </div>'),vx=h('<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),px=h('<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),hx=h('<div class="text-[10px] text-dl-text-dim/35 mt-1"> </div>'),mx=h('<div class="vw-digest svelte-1l2nqwu"><div class="flex items-center gap-2 mb-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span></div> <div class="space-y-1"><!> <!> <!> <!></div></div>'),xx=h('<p class="vw-para"> </p>'),gx=h('<div class="vw-diff-added svelte-1l2nqwu"> </div>'),_x=h('<div class="vw-diff-deleted svelte-1l2nqwu"> </div>'),bx=h('<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow svelte-1l2nqwu"></div>'),wx=h('<div class="disclosure-text vw-section-body vw-body-frame svelte-1l2nqwu"><!></div>'),yx=h('<div><!> <div class="vw-section-meta svelte-1l2nqwu"><span> </span> <!> <!> <!> <!></div> <!> <!> <!> <!></div>'),kx=h('<section class="vw-report-shell svelte-1l2nqwu"><div class="vw-report-header svelte-1l2nqwu"><div class="vw-report-badges svelte-1l2nqwu"><!> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <!> <!></div></div> <!></section>'),Cx=h('<div class="vw-data-divider svelte-1l2nqwu"><div class="vw-data-kicker svelte-1l2nqwu">Structured Data</div> <div class="vw-data-title svelte-1l2nqwu">표 / 정형 데이터</div></div>'),Sx=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),$x=h("<th> </th>"),zx=h("<td> </td>"),Mx=h("<tr></tr>"),Tx=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),Ix=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),Ax=h("<th> </th>"),Ex=h("<td> </td>"),Nx=h("<tr></tr>"),Px=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),Lx=h("<button> </button>"),Ox=h('<span class="text-[9px] text-dl-text-dim/30"> </span>'),Rx=h('<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto"><!> <!></div>'),Dx=h('<div class="vw-table-wrap bg-dl-bg-card/10 svelte-1l2nqwu"><!> <div class="px-4 py-3"><div class="markdown-table overflow-x-auto svelte-1l2nqwu"><!></div></div></div>'),jx=h("<th> </th>"),Fx=h("<td> </td>"),Vx=h("<tr></tr>"),Bx=h('<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02] svelte-1l2nqwu"><div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10"><!> <span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span></div> <div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),qx=h('<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card"> </th>'),Hx=h('<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted"> </td>'),Ux=h("<tr></tr>"),Wx=h('<div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Kx=h('<article class="py-6 px-8"><!> <!> <!> <!></article>'),Gx=h('<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center"><div class="flex-1 min-w-0"><!> <h3 class="text-[16px] font-semibold text-dl-text"> </h3></div> <button class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"><!></button></div> <!>',1),Jx=h('<div class="flex flex-1 overflow-hidden min-h-0"><!> <main class="flex-1 overflow-y-auto min-w-0"><!></main></div>'),Yx=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8"><!> <p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p></div>'),Xx=h('<div class="flex flex-col h-full font-sans bg-dl-bg-dark"><!></div>');function Qx(t,e){Cr(e,!0);let r=Pe(e,"stockCode",3,null),a=Pe(e,"onTopicChange",3,null),o=Z(null),i=Z(!1),s=Z(Ut(new Set)),l=Z(null),u=Z(null),f=Z(Ut([])),p=Z(null),_=Z(!1),g=Z(Ut([])),w=Z(Ut(new Map)),k=new Map,S=Z(!1),b=Z(Ut(new Map));const C={companyOverview:"회사 개요",companyHistory:"회사 연혁",articlesOfIncorporation:"정관 사항",capitalChange:"자본금 변동",shareCapital:"주식 현황",dividend:"배당",productService:"사업 내용",rawMaterial:"원재료",businessOverview:"사업 개요",salesOrder:"매출/수주",riskDerivative:"위험관리/파생",majorContractsAndRnd:"주요 계약/R&D",otherReferences:"기타 참고사항",consolidatedStatements:"연결 재무제표",fsSummary:"재무제표 요약",consolidatedNotes:"연결 주석",financialStatements:"개별 재무제표",financialNotes:"개별 주석",fundraising:"자금조달",BS:"재무상태표",IS:"손익계산서",CIS:"포괄손익계산서",CF:"현금흐름표",SCE:"자본변동표",ratios:"재무비율",audit:"감사 의견",mdna:"경영진 분석(MD&A)",internalControl:"내부통제",auditContract:"감사 계약",nonAuditContract:"비감사 계약",boardOfDirectors:"이사회",shareholderMeeting:"주주총회",auditSystem:"감사 체계",outsideDirector:"사외이사",majorHolder:"주요 주주",majorHolderChange:"주주 변동",minorityHolder:"소수주주",stockTotal:"주식 총수",treasuryStock:"자기주식",employee:"직원 현황",executivePay:"임원 보수",executive:"임원 현황",executivePayAllTotal:"전체 보수 총액",executivePayIndividual:"개인별 보수",topPay:"5억이상 상위 보수",unregisteredExecutivePay:"미등기임원 보수",affiliateGroup:"계열회사",investedCompany:"투자회사",relatedPartyTx:"특수관계 거래",corporateBond:"사채 관리",privateOfferingUsage:"사모자금 사용",publicOfferingUsage:"공모자금 사용",shortTermBond:"단기사채",investorProtection:"투자자 보호",disclosureChanges:"공시변경 사항",contingentLiability:"우발채무",sanction:"제재/조치",subsequentEvents:"후발사건",expertConfirmation:"전문가 확인",subsidiaryDetail:"종속회사 상세",affiliateGroupDetail:"계열회사 상세",investmentInOtherDetail:"타법인 출자 상세",rndDetail:"R&D 상세"},z={I:"I. 회사의 개요",II:"II. 사업의 내용",III:"III. 재무에 관한 사항",IV:"IV. 감사인의 감사의견 등",V:"V. 이사의 경영진단 및 분석의견",VI:"VI. 이사회 등 회사의 기관에 관한 사항",VII:"VII. 주주에 관한 사항",VIII:"VIII. 임원 및 직원 등에 관한 사항",IX:"IX. 계열회사 등에 관한 사항",X:"X. 대주주 등과의 거래내용",XI:"XI. 그 밖에 투자자 보호를 위하여 필요한 사항",XII:"XII. 상세표"},P={I:1,II:2,III:3,IV:4,V:5,VI:6,VII:7,VIII:8,IX:9,X:10,XI:11,XII:12};function E(x){return P[x]??99}function ee(x){return C[x]||x}function se(x){return z[x]||x||"기타"}xr(()=>{r()&&j()});async function j(){var x,N;v(i,!0),v(o,null),v(l,null),v(u,null),v(f,[],!0),v(p,null),k=new Map;try{const L=await Iv(r());v(o,L.payload,!0),(x=n(o))!=null&&x.columns&&v(g,n(o).columns.filter(y=>/^\d{4}(Q[1-4])?$/.test(y)),!0);const q=B((N=n(o))==null?void 0:N.rows);q.length>0&&(v(s,new Set([q[0].chapter]),!0),q[0].topics.length>0&&T(q[0].topics[0].topic,q[0].chapter))}catch(L){console.error("viewer load error:",L)}v(i,!1)}async function T(x,N){var L;if(n(l)!==x){if(v(l,x,!0),v(u,N||null,!0),v(w,new Map,!0),v(b,new Map,!0),(L=a())==null||L(x,ee(x)),k.has(x)){const q=k.get(x);v(f,q.blocks||[],!0),v(p,q.textDocument||null,!0);return}v(f,[],!0),v(p,null),v(_,!0);try{const q=await Tv(r(),x);v(f,q.blocks||[],!0),v(p,q.textDocument||null,!0),k.set(x,{blocks:n(f),textDocument:n(p)})}catch(q){console.error("topic load error:",q),v(f,[],!0),v(p,null)}v(_,!1)}}function G(x){const N=new Set(n(s));N.has(x)?N.delete(x):N.add(x),v(s,N,!0)}function K(x,N){const L=new Map(n(w));L.get(x)===N?L.delete(x):L.set(x,N),v(w,L,!0)}function ie(x,N){const L=new Map(n(b));L.set(x,N),v(b,L,!0)}function U(x){return x==="updated"?"최근 수정":x==="new"?"신규":x==="stale"?"과거 유지":"유지"}function we(x){return x==="updated"?"updated":x==="new"?"new":x==="stale"?"stale":"stable"}function B(x){if(!x)return[];const N=new Map,L=new Set;for(const q of x){const y=q.chapter||"";N.has(y)||N.set(y,{chapter:y,topics:[]}),L.has(q.topic)||(L.add(q.topic),N.get(y).topics.push({topic:q.topic,source:q.source||"docs"}))}return[...N.values()].sort((q,y)=>E(q.chapter)-E(y.chapter))}function J(x){return String(x).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function le(x){return String(x||"").replaceAll(" "," ").replace(/\s+/g," ").trim()}function X(x){return!x||x.length>88?!1:/^\[.+\]$/.test(x)||/^【.+】$/.test(x)||/^[IVX]+\.\s/.test(x)||/^\d+\.\s/.test(x)||/^[가-힣]\.\s/.test(x)||/^\(\d+\)\s/.test(x)||/^\([가-힣]\)\s/.test(x)}function O(x){return/^\(\d+\)\s/.test(x)||/^\([가-힣]\)\s/.test(x)?"h5":"h4"}function W(x){return/^\[.+\]$/.test(x)||/^【.+】$/.test(x)?"vw-h-bracket":/^\(\d+\)\s/.test(x)||/^\([가-힣]\)\s/.test(x)?"vw-h-sub":"vw-h-section"}function F(x){if(!x)return[];if(/^\|.+\|$/m.test(x)||/^#{1,3} /m.test(x)||/```/.test(x))return[{kind:"markdown",text:x}];const N=[];let L=[];const q=()=>{L.length!==0&&(N.push({kind:"paragraph",text:L.join(" ")}),L=[])};for(const y of String(x).split(`
`)){const V=le(y);if(!V){q();continue}if(X(V)){q(),N.push({kind:"heading",text:V,tag:O(V),className:W(V)});continue}L.push(V)}return q(),N}function ce(x){return x?x.kind==="annual"?`${x.year}Q4`:x.year&&x.quarter?`${x.year}Q${x.quarter}`:x.label||"":""}function ne(x){var q;const N=F(x);if(N.length===0)return"";if(((q=N[0])==null?void 0:q.kind)==="markdown")return Ma(x);let L="";for(const y of N){if(y.kind==="heading"){L+=`<${y.tag} class="${y.className}">${J(y.text)}</${y.tag}>`;continue}L+=`<p class="vw-para">${J(y.text)}</p>`}return L}function D(x){if(!x)return"";const N=x.trim().split(`
`).filter(q=>q.trim());let L="";for(const q of N){const y=q.trim();/^[가-힣]\.\s/.test(y)||/^\d+[-.]/.test(y)?L+=`<h4 class="vw-h-section">${y}</h4>`:/^\(\d+\)\s/.test(y)||/^\([가-힣]\)\s/.test(y)?L+=`<h5 class="vw-h-sub">${y}</h5>`:/^\[.+\]$/.test(y)||/^【.+】$/.test(y)?L+=`<h4 class="vw-h-bracket">${y}</h4>`:L+=`<h5 class="vw-h-sub">${y}</h5>`}return L}function H(x){var L;const N=n(w).get(x.id);return N&&((L=x==null?void 0:x.views)!=null&&L[N])?x.views[N]:(x==null?void 0:x.latest)||null}function te(x,N){var q,y;const L=n(w).get(x.id);return L?L===N:((y=(q=x==null?void 0:x.latest)==null?void 0:q.period)==null?void 0:y.label)===N}function Y(x){return n(w).has(x.id)}function xe(x){return x==="updated"?"변경 있음":x==="new"?"직전 없음":"직전과 동일"}function ke(x){var V,Q,he;if(!x)return[];const N=F(x.body);if(N.length===0||((V=N[0])==null?void 0:V.kind)==="markdown"||!((Q=x.prevPeriod)!=null&&Q.label)||!((he=x.diff)!=null&&he.length))return N;const L=[];for(const fe of x.diff)for(const me of fe.paragraphs||[])L.push({kind:fe.kind,text:le(me)});const q=[];let y=0;for(const fe of N){if(fe.kind!=="paragraph"){q.push(fe);continue}for(;y<L.length&&L[y].kind==="removed";)q.push({kind:"removed",text:L[y].text}),y+=1;y<L.length&&["same","added"].includes(L[y].kind)?(q.push({kind:L[y].kind,text:L[y].text||fe.text}),y+=1):q.push({kind:"same",text:fe.text})}for(;y<L.length;)q.push({kind:L[y].kind,text:L[y].text}),y+=1;return q}function re(x){return x==null?!1:/^-?[\d,.]+%?$/.test(String(x).trim().replace(/,/g,""))}function Fe(x){return x==null?!1:/^-[\d.]+/.test(String(x).trim().replace(/,/g,""))}function ot(x,N){if(x==null||x==="")return"";const L=typeof x=="number"?x:Number(String(x).replace(/,/g,""));if(isNaN(L))return String(x);if(N<=1)return L.toLocaleString("ko-KR");const q=L/N;return Number.isInteger(q)?q.toLocaleString("ko-KR"):q.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g,",")}function nt(x){if(x==null||x==="")return"";const N=String(x).trim();if(N.includes(","))return N;const L=N.match(/^(-?\d+)(\.\d+)?(%?)$/);return L?L[1].replace(/\B(?=(\d{3})+(?!\d))/g,",")+(L[2]||"")+(L[3]||""):N}function lt(x){var N,L;return(N=n(o))!=null&&N.rows&&((L=n(o).rows.find(q=>q.topic===x))==null?void 0:L.chapter)||null}function at(x){const N=x.match(/^(\d{4})(Q([1-4]))?$/);if(!N)return"0000_0";const L=N[1],q=N[3]||"5";return`${L}_${q}`}function vt(x){return[...x].sort((N,L)=>at(L).localeCompare(at(N)))}let tt=R(()=>n(f).filter(x=>x.kind!=="text"));var Qe=Xx(),yt=d(Qe);{var $t=x=>{var N=Fm(),L=d(N);Ar(L,{size:18,class:"animate-spin"}),c(x,N)},Et=x=>{var N=Jx(),L=d(N);{var q=fe=>{var me=Um(),Ae=d(me),qe=d(Ae);{var Ie=Re=>{var De=Vm(),pt=d(De);A(()=>I(pt,`${n(g).length??""}개 기간 · ${n(g)[0]??""} ~ ${n(g)[n(g).length-1]??""}`)),c(Re,De)};$(qe,Re=>{n(g).length>0&&Re(Ie)})}var je=m(Ae,2);Ce(je,17,()=>B(n(o).rows),$e,(Re,De)=>{var pt=Hm(),Ze=d(pt),Bt=d(Ze);{var ge=It=>{el(It,{size:11,class:"flex-shrink-0 opacity-40"})},Ve=R(()=>n(s).has(n(De).chapter)),Me=It=>{jc(It,{size:11,class:"flex-shrink-0 opacity-40"})};$(Bt,It=>{n(Ve)?It(ge):It(Me,-1)})}var ye=m(Bt,2),dt=d(ye),Be=m(ye,2),Oe=d(Be),rt=m(Ze,2);{var kt=It=>{var fr=qm();Ce(fr,21,()=>n(De).topics,$e,(_r,br)=>{var Wt=Bm(),mt=d(Wt);{var lr=zt=>{$s(zt,{size:11,class:"flex-shrink-0 text-blue-400/40"})},Rr=zt=>{$i(zt,{size:11,class:"flex-shrink-0 text-emerald-400/40"})},_t=zt=>{hn(zt,{size:11,class:"flex-shrink-0 opacity-30"})};$(mt,zt=>{n(br).source==="finance"?zt(lr):n(br).source==="report"?zt(Rr,1):zt(_t,-1)})}var He=m(mt,2),bt=d(He);A(zt=>{Xe(Wt,1,`group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											${n(l)===n(br).topic?"bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]":"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent"}`),I(bt,zt)},[()=>ee(n(br).topic)]),ve("click",Wt,()=>T(n(br).topic,n(De).chapter)),c(_r,Wt)}),c(It,fr)},Xt=R(()=>n(s).has(n(De).chapter));$(rt,It=>{n(Xt)&&It(kt)})}A(It=>{I(dt,It),I(Oe,n(De).topics.length)},[()=>se(n(De).chapter)]),ve("click",Ze,()=>G(n(De).chapter)),c(Re,pt)}),c(fe,me)};$(L,fe=>{n(S)||fe(q)})}var y=m(L,2),V=d(y);{var Q=fe=>{var me=Wm(),Ae=d(me);hn(Ae,{size:32,strokeWidth:1,class:"opacity-20"}),c(fe,me)},he=fe=>{var me=Gx(),Ae=ae(me),qe=d(Ae),Ie=d(qe);{var je=Be=>{var Oe=Km(),rt=d(Oe);A(kt=>I(rt,kt),[()=>se(n(u)||lt(n(l)))]),c(Be,Oe)},Re=R(()=>n(u)||lt(n(l)));$(Ie,Be=>{n(Re)&&Be(je)})}var De=m(Ie,2),pt=d(De),Ze=m(qe,2),Bt=d(Ze);{var ge=Be=>{Vc(Be,{size:15})},Ve=Be=>{Fc(Be,{size:15})};$(Bt,Be=>{n(S)?Be(ge):Be(Ve,-1)})}var Me=m(Ae,2);{var ye=Be=>{var Oe=Gm(),rt=d(Oe);Ar(rt,{size:16,class:"animate-spin"}),c(Be,Oe)},dt=Be=>{var Oe=Kx(),rt=d(Oe);{var kt=Wt=>{var mt=Jm();c(Wt,mt)};$(rt,Wt=>{var mt,lr;n(f).length===0&&!(((lr=(mt=n(p))==null?void 0:mt.sections)==null?void 0:lr.length)>0)&&Wt(kt)})}var Xt=m(rt,2);{var It=Wt=>{var mt=kx(),lr=d(mt),Rr=d(lr),_t=d(Rr);{var He=gt=>{var Se=Ym(),Ue=d(Se);A(ht=>I(Ue,`최신 기준 ${ht??""}`),[()=>ce(n(p).latestPeriod)]),c(gt,Se)};$(_t,gt=>{n(p).latestPeriod&&gt(He)})}var bt=m(_t,2);{var zt=gt=>{var Se=Xm(),Ue=d(Se);A((ht,Dt)=>I(Ue,`커버리지 ${ht??""}~${Dt??""}`),[()=>ce(n(p).firstPeriod),()=>ce(n(p).latestPeriod)]),c(gt,Se)};$(bt,gt=>{n(p).firstPeriod&&gt(zt)})}var pr=m(bt,2),qt=d(pr),Ot=m(pr,2);{var dr=gt=>{var Se=Qm(),Ue=d(Se);A(()=>I(Ue,`최근 수정 ${n(p).updatedCount??""}개`)),c(gt,Se)};$(Ot,gt=>{n(p).updatedCount>0&&gt(dr)})}var sr=m(Ot,2);{var Nt=gt=>{var Se=Zm(),Ue=d(Se);A(()=>I(Ue,`신규 ${n(p).newCount??""}개`)),c(gt,Se)};$(sr,gt=>{n(p).newCount>0&&gt(Nt)})}var Ct=m(sr,2);{var Rt=gt=>{var Se=ex(),Ue=d(Se);A(()=>I(Ue,`과거 유지 ${n(p).staleCount??""}개`)),c(gt,Se)};$(Ct,gt=>{n(p).staleCount>0&&gt(Rt)})}var ir=m(lr,2);Ce(ir,17,()=>n(p).sections,$e,(gt,Se)=>{const Ue=R(()=>H(n(Se))),ht=R(()=>Y(n(Se)));var Dt=yx(),Qt=d(Dt);{var We=ze=>{var pe=rx();Ce(pe,21,()=>n(Se).headingPath,$e,(Te,Ge)=>{var wt=tx(),At=d(wt);Nn(At,()=>D(n(Ge).text)),c(Te,wt)}),c(ze,pe)};$(Qt,ze=>{var pe;((pe=n(Se).headingPath)==null?void 0:pe.length)>0&&ze(We)})}var Mt=m(Qt,2),jt=d(Mt),cr=d(jt),Zt=m(jt,2);{var wr=ze=>{var pe=nx(),Te=d(pe);A(Ge=>I(Te,`최신 ${Ge??""}`),[()=>ce(n(Se).latestPeriod)]),c(ze,pe)};$(Zt,ze=>{var pe;(pe=n(Se).latestPeriod)!=null&&pe.label&&ze(wr)})}var Wr=m(Zt,2);{var $r=ze=>{var pe=ax(),Te=d(pe);A(Ge=>I(Te,`최초 ${Ge??""}`),[()=>ce(n(Se).firstPeriod)]),c(ze,pe)};$(Wr,ze=>{var pe,Te;(pe=n(Se).firstPeriod)!=null&&pe.label&&n(Se).firstPeriod.label!==((Te=n(Se).latestPeriod)==null?void 0:Te.label)&&ze($r)})}var Pr=m(Wr,2);{var Sn=ze=>{var pe=ox(),Te=d(pe);A(()=>I(Te,`${n(Se).periodCount??""}기간`)),c(ze,pe)};$(Pr,ze=>{n(Se).periodCount>0&&ze(Sn)})}var Dn=m(Pr,2);{var sn=ze=>{var pe=sx(),Te=d(pe);A(()=>I(Te,`최근 변경 ${n(Se).latestChange??""}`)),c(ze,pe)};$(Dn,ze=>{n(Se).latestChange&&ze(sn)})}var jn=m(Mt,2);{var Pt=ze=>{var pe=lx();Ce(pe,21,()=>n(Se).timeline,$e,(Te,Ge)=>{var wt=ix(),At=d(wt),Ft=d(At);A((Ht,St)=>{Xe(wt,1,`vw-timeline-chip ${Ht??""}`,"svelte-1l2nqwu"),I(Ft,St)},[()=>te(n(Se),n(Ge).period.label)?"is-active":"",()=>ce(n(Ge).period)]),ve("click",wt,()=>K(n(Se).id,n(Ge).period.label)),c(Te,wt)}),c(ze,pe)};$(jn,ze=>{var pe;((pe=n(Se).timeline)==null?void 0:pe.length)>0&&ze(Pt)})}var M=m(jn,2);{var de=ze=>{var pe=ux(),Te=d(pe),Ge=d(Te),wt=m(Te,2);{var At=ue=>{var _e=dx(),ct=d(_e);A(Je=>I(ct,`비교 ${Je??""}`),[()=>ce(n(Ue).prevPeriod)]),c(ue,_e)},Ft=ue=>{var _e=cx();c(ue,_e)};$(wt,ue=>{var _e;(_e=n(Ue).prevPeriod)!=null&&_e.label?ue(At):ue(Ft,-1)})}var Ht=m(wt,2),St=d(Ht);A((ue,_e)=>{I(Ge,`선택 ${ue??""}`),I(St,_e)},[()=>ce(n(Ue).period),()=>xe(n(Ue).status)]),c(ze,pe)};$(M,ze=>{n(ht)&&n(Ue)&&ze(de)})}var Ee=m(M,2);{var Ne=ze=>{const pe=R(()=>n(Ue).digest);var Te=mx(),Ge=d(Te),wt=d(Ge),At=d(wt),Ft=m(Ge,2),Ht=d(Ft);Ce(Ht,17,()=>n(pe).items.filter(Je=>Je.kind==="numeric"),$e,(Je,xt)=>{var tr=fx(),Kt=m(d(tr));A(()=>I(Kt,` ${n(xt).text??""}`)),c(Je,tr)});var St=m(Ht,2);Ce(St,17,()=>n(pe).items.filter(Je=>Je.kind==="added"),$e,(Je,xt)=>{var tr=vx(),Kt=m(d(tr),2),er=d(Kt);A(()=>I(er,n(xt).text)),c(Je,tr)});var ue=m(St,2);Ce(ue,17,()=>n(pe).items.filter(Je=>Je.kind==="removed"),$e,(Je,xt)=>{var tr=px(),Kt=m(d(tr),2),er=d(Kt);A(()=>I(er,n(xt).text)),c(Je,tr)});var _e=m(ue,2);{var ct=Je=>{var xt=hx(),tr=d(xt);A(()=>I(tr,`외 ${n(pe).wordingCount??""}건 문구 수정`)),c(Je,xt)};$(_e,Je=>{n(pe).wordingCount>0&&Je(ct)})}A(()=>I(At,`${n(pe).to??""} vs ${n(pe).from??""}`)),c(ze,Te)};$(Ee,ze=>{var pe,Te,Ge;n(ht)&&((Ge=(Te=(pe=n(Ue))==null?void 0:pe.digest)==null?void 0:Te.items)==null?void 0:Ge.length)>0&&ze(Ne)})}var Le=m(Ee,2);{var et=ze=>{var pe=be(),Te=ae(pe);{var Ge=At=>{var Ft=bx();Ce(Ft,21,()=>ke(n(Ue)),$e,(Ht,St)=>{var ue=be(),_e=ae(ue);{var ct=Kt=>{var er=be(),nr=ae(er);Nn(nr,()=>D(n(St).text)),c(Kt,er)},Je=Kt=>{var er=xx(),nr=d(er);A(()=>I(nr,n(St).text)),c(Kt,er)},xt=Kt=>{var er=gx(),nr=d(er);A(()=>I(nr,n(St).text)),c(Kt,er)},tr=Kt=>{var er=_x(),nr=d(er);A(()=>I(nr,n(St).text)),c(Kt,er)};$(_e,Kt=>{n(St).kind==="heading"?Kt(ct):n(St).kind==="same"?Kt(Je,1):n(St).kind==="added"?Kt(xt,2):n(St).kind==="removed"&&Kt(tr,3)})}c(Ht,ue)}),c(At,Ft)},wt=At=>{var Ft=wx(),Ht=d(Ft);Nn(Ht,()=>ne(n(Ue).body)),c(At,Ft)};$(Te,At=>{var Ft,Ht;n(ht)&&((Ft=n(Ue).prevPeriod)!=null&&Ft.label)&&((Ht=n(Ue).diff)==null?void 0:Ht.length)>0?At(Ge):At(wt,-1)})}c(ze,pe)};$(Le,ze=>{n(Ue)&&ze(et)})}A((ze,pe)=>{Xe(Dt,1,`vw-text-section ${n(Se).status==="stale"?"vw-text-section-stale":""}`,"svelte-1l2nqwu"),Xe(jt,1,`vw-status-pill ${ze??""}`,"svelte-1l2nqwu"),I(cr,pe)},[()=>we(n(Se).status),()=>U(n(Se).status)]),c(gt,Dt)}),A(()=>I(qt,`본문 ${n(p).sectionCount??""}개`)),c(Wt,mt)};$(Xt,Wt=>{var mt,lr;((lr=(mt=n(p))==null?void 0:mt.sections)==null?void 0:lr.length)>0&&Wt(It)})}var fr=m(Xt,2);{var _r=Wt=>{var mt=Cx();c(Wt,mt)};$(fr,Wt=>{n(tt).length>0&&Wt(_r)})}var br=m(fr,2);Ce(br,17,()=>n(tt),$e,(Wt,mt)=>{var lr=be(),Rr=ae(lr);{var _t=qt=>{const Ot=R(()=>{var We;return((We=n(mt).data)==null?void 0:We.columns)||[]}),dr=R(()=>{var We;return((We=n(mt).data)==null?void 0:We.rows)||[]}),sr=R(()=>n(mt).meta||{}),Nt=R(()=>n(sr).scaleDivisor||1);var Ct=Tx(),Rt=ae(Ct);{var ir=We=>{var Mt=Sx(),jt=d(Mt);A(()=>I(jt,`(단위: ${n(sr).scale??""})`)),c(We,Mt)};$(Rt,We=>{n(sr).scale&&We(ir)})}var gt=m(Rt,2),Se=d(gt),Ue=d(Se),ht=d(Ue),Dt=d(ht);Ce(Dt,21,()=>n(Ot),$e,(We,Mt,jt)=>{const cr=R(()=>/^\d{4}/.test(n(Mt)));var Zt=$x(),wr=d(Zt);A(()=>{Xe(Zt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(cr)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${jt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),I(wr,n(Mt))}),c(We,Zt)});var Qt=m(ht);Ce(Qt,21,()=>n(dr),$e,(We,Mt,jt)=>{var cr=Mx();Xe(cr,1,`hover:bg-white/[0.03] ${jt%2===1?"bg-white/[0.012]":""}`),Ce(cr,21,()=>n(Ot),$e,(Zt,wr,Wr)=>{const $r=R(()=>n(Mt)[n(wr)]??""),Pr=R(()=>re(n($r))),Sn=R(()=>Fe(n($r))),Dn=R(()=>n(Pr)?ot(n($r),n(Nt)):n($r));var sn=zx(),jn=d(sn);A(()=>{Xe(sn,1,`px-3 py-1.5 border-b border-white/[0.025]
																	${n(Pr)?"text-right tabular-nums font-mono text-[11.5px]":"whitespace-nowrap"}
																	${n(Sn)?"text-red-400/60":n(Pr)?"text-dl-text/90":""}
																	${Wr===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]":"text-dl-text-muted"}
																	${Wr===0&&jt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),I(jn,n(Dn))}),c(Zt,sn)}),c(We,cr)}),c(qt,Ct)},He=qt=>{const Ot=R(()=>{var We;return((We=n(mt).data)==null?void 0:We.columns)||[]}),dr=R(()=>{var We;return((We=n(mt).data)==null?void 0:We.rows)||[]}),sr=R(()=>n(mt).meta||{}),Nt=R(()=>n(sr).scaleDivisor||1);var Ct=Px(),Rt=ae(Ct);{var ir=We=>{var Mt=Ix(),jt=d(Mt);A(()=>I(jt,`(단위: ${n(sr).scale??""})`)),c(We,Mt)};$(Rt,We=>{n(sr).scale&&We(ir)})}var gt=m(Rt,2),Se=d(gt),Ue=d(Se),ht=d(Ue),Dt=d(ht);Ce(Dt,21,()=>n(Ot),$e,(We,Mt,jt)=>{const cr=R(()=>/^\d{4}/.test(n(Mt)));var Zt=Ax(),wr=d(Zt);A(()=>{Xe(Zt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(cr)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${jt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),I(wr,n(Mt))}),c(We,Zt)});var Qt=m(ht);Ce(Qt,21,()=>n(dr),$e,(We,Mt,jt)=>{var cr=Nx();Xe(cr,1,`hover:bg-white/[0.03] ${jt%2===1?"bg-white/[0.012]":""}`),Ce(cr,21,()=>n(Ot),$e,(Zt,wr,Wr)=>{const $r=R(()=>n(Mt)[n(wr)]??""),Pr=R(()=>re(n($r))),Sn=R(()=>Fe(n($r))),Dn=R(()=>n(Pr)?n(Nt)>1?ot(n($r),n(Nt)):nt(n($r)):n($r));var sn=Ex(),jn=d(sn);A(()=>{Xe(sn,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(Pr)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(Sn)?"text-red-400/60":n(Pr)?"text-dl-text/90":""}
																	${Wr===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Wr===0&&jt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),I(jn,n(Dn))}),c(Zt,sn)}),c(We,cr)}),c(qt,Ct)},bt=qt=>{const Ot=R(()=>vt(Object.keys(n(mt).rawMarkdown))),dr=R(()=>n(b).get(n(mt).block)??0),sr=R(()=>n(Ot)[n(dr)]||n(Ot)[0]);var Nt=Dx(),Ct=d(Nt);{var Rt=Ue=>{var ht=Rx(),Dt=d(ht);Ce(Dt,17,()=>n(Ot).slice(0,8),$e,(Mt,jt,cr)=>{var Zt=Lx(),wr=d(Zt);A(()=>{Xe(Zt,1,`px-2 py-0.5 rounded text-[10px] transition-colors
															${cr===n(dr)?"bg-white/[0.08] text-dl-text font-medium":"text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]"}`),I(wr,n(jt))}),ve("click",Zt,()=>ie(n(mt).block,cr)),c(Mt,Zt)});var Qt=m(Dt,2);{var We=Mt=>{var jt=Ox(),cr=d(jt);A(()=>I(cr,`외 ${n(Ot).length-8}개`)),c(Mt,jt)};$(Qt,Mt=>{n(Ot).length>8&&Mt(We)})}c(Ue,ht)};$(Ct,Ue=>{n(Ot).length>1&&Ue(Rt)})}var ir=m(Ct,2),gt=d(ir),Se=d(gt);Nn(Se,()=>Ma(n(mt).rawMarkdown[n(sr)])),c(qt,Nt)},zt=qt=>{const Ot=R(()=>{var ht;return((ht=n(mt).data)==null?void 0:ht.columns)||[]}),dr=R(()=>{var ht;return((ht=n(mt).data)==null?void 0:ht.rows)||[]});var sr=Bx(),Nt=d(sr),Ct=d(Nt);$i(Ct,{size:12,class:"text-emerald-400/50"});var Rt=m(Nt,2),ir=d(Rt),gt=d(ir),Se=d(gt);Ce(Se,21,()=>n(Ot),$e,(ht,Dt,Qt)=>{const We=R(()=>/^\d{4}/.test(n(Dt)));var Mt=jx(),jt=d(Mt);A(()=>{Xe(Mt,1,`px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															${n(We)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
															${Qt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),I(jt,n(Dt))}),c(ht,Mt)});var Ue=m(gt);Ce(Ue,21,()=>n(dr),$e,(ht,Dt,Qt)=>{var We=Vx();Xe(We,1,`hover:bg-white/[0.03] ${Qt%2===1?"bg-white/[0.012]":""}`),Ce(We,21,()=>n(Ot),$e,(Mt,jt,cr)=>{const Zt=R(()=>n(Dt)[n(jt)]??""),wr=R(()=>re(n(Zt))),Wr=R(()=>Fe(n(Zt)));var $r=Fx(),Pr=d($r);A(Sn=>{Xe($r,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(wr)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(Wr)?"text-red-400/60":n(wr)?"text-dl-text/90":""}
																	${cr===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${cr===0&&Qt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),I(Pr,Sn)},[()=>n(wr)?nt(n(Zt)):n(Zt)]),c(Mt,$r)}),c(ht,We)}),c(qt,sr)},pr=qt=>{const Ot=R(()=>n(mt).data.columns),dr=R(()=>n(mt).data.rows||[]);var sr=Wx(),Nt=d(sr),Ct=d(Nt),Rt=d(Ct),ir=d(Rt);Ce(ir,21,()=>n(Ot),$e,(Se,Ue)=>{var ht=qx(),Dt=d(ht);A(()=>I(Dt,n(Ue))),c(Se,ht)});var gt=m(Rt);Ce(gt,21,()=>n(dr),$e,(Se,Ue,ht)=>{var Dt=Ux();Xe(Dt,1,`hover:bg-white/[0.03] ${ht%2===1?"bg-white/[0.012]":""}`),Ce(Dt,21,()=>n(Ot),$e,(Qt,We)=>{var Mt=Hx(),jt=d(Mt);A(()=>I(jt,n(Ue)[n(We)]??"")),c(Qt,Mt)}),c(Se,Dt)}),c(qt,sr)};$(Rr,qt=>{var Ot,dr;n(mt).kind==="finance"?qt(_t):n(mt).kind==="structured"?qt(He,1):n(mt).kind==="raw_markdown"&&n(mt).rawMarkdown?qt(bt,2):n(mt).kind==="report"?qt(zt,3):((dr=(Ot=n(mt).data)==null?void 0:Ot.columns)==null?void 0:dr.length)>0&&qt(pr,4)})}c(Wt,lr)}),c(Be,Oe)};$(Me,Be=>{n(_)?Be(ye):Be(dt,-1)})}A(Be=>{I(pt,Be),ar(Ze,"title",n(S)?"목차 표시":"전체화면")},[()=>ee(n(l))]),ve("click",Ze,()=>v(S,!n(S))),c(fe,me)};$(V,fe=>{n(l)?fe(he,-1):fe(Q)})}c(x,N)},or=x=>{var N=Yx(),L=d(N);hn(L,{size:36,strokeWidth:1,class:"opacity-20"}),c(x,N)};$(yt,x=>{var N;n(i)?x($t):(N=n(o))!=null&&N.rows?x(Et,1):x(or,-1)})}c(t,Qe),Sr()}Or(["click"]);var Zx=h('<span class="text-[12px] font-semibold text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim"> </span>',1),e1=h('<span class="text-[12px] font-semibold text-dl-text"> </span>'),t1=h('<span class="text-[12px] font-semibold text-dl-text">데이터</span>'),r1=h('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" title="Excel 다운로드"><!></button> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button>',1),n1=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),a1=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed"> </pre>'),o1=h('<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2"> </div>'),s1=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),i1=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),l1=h("<!> <!>",1),d1=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),c1=h('<div class="p-4"><!></div>'),u1=h('<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">표시할 내용이 없습니다</div>'),f1=h('<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark"><div class="flex items-center justify-between h-10 mt-8 px-4 border-b border-dl-border/40 flex-shrink-0"><div class="flex items-center gap-2 min-w-0"><!></div> <div class="flex items-center gap-1"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 overflow-auto min-h-0"><!></div></div>');function v1(t,e){Cr(e,!0);let r=Pe(e,"mode",3,null),a=Pe(e,"company",3,null),o=Pe(e,"data",3,null),i=Pe(e,"onTopicChange",3,null),s=Pe(e,"onFullscreen",3,null),l=Pe(e,"isFullscreen",3,!1),u=Z(!1);async function f(){var U;if(!(!((U=a())!=null&&U.stockCode)||n(u))){v(u,!0);try{await Mv(a().stockCode)}catch(we){console.error("Excel download error:",we)}v(u,!1)}}function p(U){return U?/^\|.+\|$/m.test(U)||/^#{1,3} /m.test(U)||/\*\*[^*]+\*\*/m.test(U)||/```/.test(U):!1}var _=f1(),g=d(_),w=d(g),k=d(w);{var S=U=>{var we=Zx(),B=ae(we),J=d(B),le=m(B,2),X=d(le);A(()=>{I(J,a().corpName||a().company),I(X,a().stockCode)}),c(U,we)},b=U=>{var we=e1(),B=d(we);A(()=>I(B,o().label)),c(U,we)},C=U=>{var we=t1();c(U,we)};$(k,U=>{var we;r()==="viewer"&&a()?U(S):r()==="data"&&((we=o())!=null&&we.label)?U(b,1):r()==="data"&&U(C,2)})}var z=m(w,2),P=d(z);{var E=U=>{var we=r1(),B=ae(we),J=d(B);{var le=ne=>{Ar(ne,{size:14,class:"animate-spin"})},X=ne=>{Wo(ne,{size:14})};$(J,ne=>{n(u)?ne(le):ne(X,-1)})}var O=m(B,2),W=d(O);{var F=ne=>{Vc(ne,{size:14})},ce=ne=>{Fc(ne,{size:14})};$(W,ne=>{l()?ne(F):ne(ce,-1)})}A(()=>{B.disabled=n(u),ar(O,"title",l()?"패널 모드로":"전체 화면")}),ve("click",B,f),ve("click",O,()=>{var ne;return(ne=s())==null?void 0:ne()}),c(U,we)};$(P,U=>{var we;r()==="viewer"&&((we=a())!=null&&we.stockCode)&&U(E)})}var ee=m(P,2),se=d(ee);za(se,{size:15});var j=m(g,2),T=d(j);{var G=U=>{Qx(U,{get stockCode(){return a().stockCode},get onTopicChange(){return i()}})},K=U=>{var we=c1(),B=d(we);{var J=O=>{var W=be(),F=ae(W);{var ce=H=>{var te=n1(),Y=d(te);Nn(Y,()=>Ma(o())),c(H,te)},ne=R(()=>p(o())),D=H=>{var te=a1(),Y=d(te);A(()=>I(Y,o())),c(H,te)};$(F,H=>{n(ne)?H(ce):H(D,-1)})}c(O,W)},le=O=>{var W=l1(),F=ae(W);{var ce=Y=>{var xe=o1(),ke=d(xe);A(()=>I(ke,o().module)),c(Y,xe)};$(F,Y=>{o().module&&Y(ce)})}var ne=m(F,2);{var D=Y=>{var xe=s1(),ke=d(xe);Nn(ke,()=>Ma(o().text)),c(Y,xe)},H=R(()=>p(o().text)),te=Y=>{var xe=i1(),ke=d(xe);A(()=>I(ke,o().text)),c(Y,xe)};$(ne,Y=>{n(H)?Y(D):Y(te,-1)})}c(O,W)},X=O=>{var W=d1(),F=d(W);A(ce=>I(F,ce),[()=>JSON.stringify(o(),null,2)]),c(O,W)};$(B,O=>{var W;typeof o()=="string"?O(J):(W=o())!=null&&W.text?O(le,1):O(X,-1)})}c(U,we)},ie=U=>{var we=u1();c(U,we)};$(T,U=>{r()==="viewer"&&a()?U(G):r()==="data"&&o()?U(K,1):U(ie,-1)})}ve("click",ee,()=>{var U;return(U=e.onClose)==null?void 0:U.call(e)}),c(t,_),Sr()}Or(["click"]);var p1=h('<div class="flex flex-col items-center justify-center py-8 gap-2"><!> <span class="text-[11px] text-dl-text-dim">목차 로딩 중...</span></div>'),h1=h('<button><!> <span class="truncate"> </span></button>'),m1=h('<div class="mb-1 pb-1 border-b border-dl-border/15"><div class="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-amber-400/70 uppercase tracking-wider"><!> <span>즐겨찾기</span></div> <!></div>'),x1=h('<button class="flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors text-dl-text-dim hover:text-dl-text hover:bg-white/5"><!> <span class="truncate"> </span></button>'),g1=h('<div class="mb-1 pb-1 border-b border-dl-border/15"><div class="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-dl-text-dim/60 uppercase tracking-wider"><!> <span>최근</span></div> <!></div>'),_1=h('<span class="w-1.5 h-1.5 rounded-full bg-emerald-400/70" title="최근 변경"></span>'),b1=h('<span class="text-[9px] text-dl-text-dim/60 font-mono"> </span>'),w1=h('<button><!> <span class="truncate"> </span> <span class="ml-auto flex items-center gap-0.5"><!> <!> <!></span></button>'),y1=h('<div class="ml-2 border-l border-dl-border/20 pl-1"></div>'),k1=h('<div class="mb-0.5"><button class="flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-left text-[11px] font-semibold uppercase tracking-wider text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] text-dl-text-dim/60 font-mono"> </span></button> <!></div>'),C1=h("<!> <!> <!>",1),S1=h('<div class="px-3 py-6 text-center text-[12px] text-dl-text-dim">종목을 선택하면 목차가 표시됩니다</div>'),$1=h('<nav class="flex flex-col h-full min-h-0 overflow-y-auto py-2 px-1"><!></nav>');function z1(t,e){Cr(e,!0);let r=Pe(e,"toc",3,null),a=Pe(e,"loading",3,!1),o=Pe(e,"selectedTopic",3,null),i=Pe(e,"expandedChapters",19,()=>new Set),s=Pe(e,"bookmarks",19,()=>[]),l=Pe(e,"recentHistory",19,()=>[]),u=Pe(e,"onSelectTopic",3,null),f=Pe(e,"onToggleChapter",3,null);const p=new Set(["BS","IS","CIS","CF","SCE","ratios"]);function _(z){return p.has(z)?$s:hn}function g(z){return z.tableCount>0&&z.textCount>0?"both":z.tableCount>0?"table":z.textCount>0?"text":"empty"}xr(()=>{o()&&ec().then(()=>{const z=document.querySelector(".viewer-nav-active-item");z&&z.scrollIntoView({block:"nearest",behavior:"smooth"})})});var w=$1(),k=d(w);{var S=z=>{var P=p1(),E=d(P);Ar(E,{size:18,class:"animate-spin text-dl-text-dim"}),c(z,P)},b=z=>{var P=C1(),E=ae(P);{var ee=G=>{const K=R(()=>s().map(B=>{for(const J of r().chapters){const le=J.topics.find(X=>X.topic===B);if(le)return{...le,chapter:J.chapter}}return null}).filter(Boolean));var ie=be(),U=ae(ie);{var we=B=>{var J=m1(),le=d(J),X=d(le);Ti(X,{size:10,fill:"currentColor"});var O=m(le,2);Ce(O,17,()=>n(K),$e,(W,F)=>{const ce=R(()=>o()===n(F).topic);var ne=h1(),D=d(ne);Ti(D,{size:10,class:"text-amber-400/60 flex-shrink-0",fill:"currentColor"});var H=m(D,2),te=d(H);A(()=>{Xe(ne,1,`flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors ${n(ce)?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-muted hover:text-dl-text hover:bg-white/5"}`),I(te,n(F).label)}),ve("click",ne,()=>{var Y;return(Y=u())==null?void 0:Y(n(F).topic,n(F).chapter)}),c(W,ne)}),c(B,J)};$(U,B=>{n(K).length>0&&B(we)})}c(G,ie)};$(E,G=>{s().length>0&&G(ee)})}var se=m(E,2);{var j=G=>{const K=R(()=>new Set(s())),ie=R(()=>l().slice(0,5).filter(J=>J.topic!==o()&&!n(K).has(J.topic)));var U=be(),we=ae(U);{var B=J=>{var le=g1(),X=d(le),O=d(X);Jo(O,{size:10});var W=m(X,2);Ce(W,17,()=>n(ie),$e,(F,ce)=>{var ne=x1(),D=d(ne);Jo(D,{size:10,class:"text-dl-text-dim/30 flex-shrink-0"});var H=m(D,2),te=d(H);A(()=>I(te,n(ce).label)),ve("click",ne,()=>{var Y;return(Y=u())==null?void 0:Y(n(ce).topic,null)}),c(F,ne)}),c(J,le)};$(we,J=>{n(ie).length>0&&J(B)})}c(G,U)};$(se,G=>{l().length>0&&G(j)})}var T=m(se,2);Ce(T,17,()=>r().chapters,$e,(G,K)=>{var ie=k1(),U=d(ie),we=d(U);{var B=H=>{el(H,{size:12})},J=R(()=>i().has(n(K).chapter)),le=H=>{jc(H,{size:12})};$(we,H=>{n(J)?H(B):H(le,-1)})}var X=m(we,2),O=d(X),W=m(X,2),F=d(W),ce=m(U,2);{var ne=H=>{var te=y1();Ce(te,21,()=>n(K).topics,$e,(Y,xe)=>{const ke=R(()=>_(n(xe).topic)),re=R(()=>g(n(xe))),Fe=R(()=>o()===n(xe).topic);var ot=w1(),nt=d(ot);wo(nt,()=>n(ke),(x,N)=>{N(x,{size:12,class:"flex-shrink-0 opacity-50"})});var lt=m(nt,2),at=d(lt),vt=m(lt,2),tt=d(vt);{var Qe=x=>{var N=_1();c(x,N)};$(tt,x=>{n(xe).hasChanges&&x(Qe)})}var yt=m(tt,2);{var $t=x=>{Ii(x,{size:9,class:"text-dl-text-dim/40"})};$(yt,x=>{(n(re)==="table"||n(re)==="both")&&x($t)})}var Et=m(yt,2);{var or=x=>{var N=b1(),L=d(N);A(()=>I(L,n(xe).tableCount)),c(x,N)};$(Et,x=>{n(xe).tableCount>0&&x(or)})}A(()=>{Xe(ot,1,`${n(Fe)?"viewer-nav-active-item":""} viewer-nav-active flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors ${n(Fe)?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-muted hover:text-dl-text hover:bg-white/5"}`),I(at,n(xe).label)}),ve("click",ot,()=>{var x;return(x=u())==null?void 0:x(n(xe).topic,n(K).chapter)}),c(Y,ot)}),c(H,te)},D=R(()=>i().has(n(K).chapter));$(ce,H=>{n(D)&&H(ne)})}A(()=>{I(O,n(K).chapter),I(F,n(K).topics.length)}),ve("click",U,()=>{var H;return(H=f())==null?void 0:H(n(K).chapter)}),c(G,ie)}),c(z,P)},C=z=>{var P=S1();c(z,P)};$(k,z=>{var P;a()?z(S):(P=r())!=null&&P.chapters?z(b,1):z(C,-1)})}c(t,w),Sr()}Or(["click"]);const M1="modulepreload",T1=function(t){return"/"+t},Xl={},Ai=function(e,r,a){let o=Promise.resolve();if(r&&r.length>0){let s=function(f){return Promise.all(f.map(p=>Promise.resolve(p).then(_=>({status:"fulfilled",value:_}),_=>({status:"rejected",reason:_}))))};document.getElementsByTagName("link");const l=document.querySelector("meta[property=csp-nonce]"),u=(l==null?void 0:l.nonce)||(l==null?void 0:l.getAttribute("nonce"));o=s(r.map(f=>{if(f=T1(f),f in Xl)return;Xl[f]=!0;const p=f.endsWith(".css"),_=p?'[rel="stylesheet"]':"";if(document.querySelector(`link[href="${f}"]${_}`))return;const g=document.createElement("link");if(g.rel=p?"stylesheet":M1,p||(g.as="script"),g.crossOrigin="",g.href=f,u&&g.setAttribute("nonce",u),document.head.appendChild(g),p)return new Promise((w,k)=>{g.addEventListener("load",w),g.addEventListener("error",()=>k(new Error(`Unable to preload CSS for ${f}`)))})}))}function i(s){const l=new Event("vite:preloadError",{cancelable:!0});if(l.payload=s,window.dispatchEvent(l),!l.defaultPrevented)throw s}return o.then(s=>{for(const l of s||[])l.status==="rejected"&&i(l.reason);return e().catch(i)})},Ei=["#ea4647","#fb923c","#3b82f6","#22c55e","#8b5cf6","#06b6d4","#f59e0b","#ec4899"],Ql={performance:"성과",profitability:"수익성",health:"건전성",cashflow:"현금흐름",governance:"지배구조",risk:"리스크",opportunity:"기회"},I1={A:5,B:4,C:3,D:2,F:0};function A1(t){var f,p;if(!((f=t==null?void 0:t.data)!=null&&f.rows)||!((p=t==null?void 0:t.data)!=null&&p.columns))return null;const{rows:e,columns:r}=t.data,a=t.meta||{},o=r.filter(_=>/^\d{4}/.test(_));if(o.length<2)return null;const i=r[0],s=[],l=["bar","line","line"];return e.slice(0,3).forEach((_,g)=>{const w=_[i]||`항목${g}`,k=o.map(S=>{const b=_[S];return b!=null?Number(b):0});k.some(S=>S!==0)&&s.push({name:w,data:k,color:Ei[g%Ei.length],type:l[g]||"line"})}),s.length===0?null:{chartType:"combo",title:a.title||"재무 추이",series:s,categories:o,options:{unit:a.unit||"백만원"}}}function E1(t,e=""){if(!t)return null;const r=Object.keys(Ql),a=r.map(i=>Ql[i]),o=r.map(i=>{var l;const s=((l=t[i])==null?void 0:l.grade)||t[i]||"F";return I1[s]??0});return{chartType:"radar",title:e?`${e} 투자 인사이트`:"투자 인사이트",series:[{name:e||"등급",data:o,color:Ei[0]}],categories:a,options:{maxValue:5}}}var N1=h("<button> </button>"),P1=h('<div class="flex items-center gap-0.5 overflow-x-auto py-1 scrollbar-thin"></div>');function Wc(t,e){Cr(e,!0);let r=Pe(e,"periods",19,()=>[]),a=Pe(e,"selected",3,null),o=Pe(e,"onSelect",3,null);function i(p){return/^\d{4}$/.test(p)||/^\d{4}Q4$/.test(p)}function s(p){const _=p.match(/^(\d{4})(Q([1-4]))?$/);if(!_)return p;const g="'"+_[1].slice(2);return _[3]?`${g}.${_[3]}Q`:g}var l=be(),u=ae(l);{var f=p=>{var _=P1();Ce(_,21,r,$e,(g,w)=>{var k=N1(),S=d(k);A((b,C)=>{Xe(k,1,`flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] font-mono transition-colors
					${b??""}`),ar(k,"title",n(w)),I(S,C)},[()=>a()===n(w)?"bg-dl-primary/20 text-dl-primary-light font-medium":i(n(w))?"text-dl-text-muted hover:text-dl-text hover:bg-white/5":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5",()=>s(n(w))]),ve("click",k,()=>{var b;return(b=o())==null?void 0:b(n(w))}),c(g,k)}),c(p,_)};$(u,p=>{r().length>0&&p(f)})}c(t,l),Sr()}Or(["click"]);var L1=h('<div class="mb-1"><!></div>'),O1=h('<!> <div class="text-[10px] text-dl-text-dim mb-1 font-mono"> </div> <div class="prose-dartlab overflow-x-auto"><!></div>',1),R1=h('<th class="cursor-pointer select-none hover:text-dl-text"> </th>'),D1=h("<td> </td>"),j1=h("<tr></tr>"),F1=h('<button class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"> </button>'),V1=h('<div class="text-[10px] text-dl-text-dim mt-1"> </div>'),B1=h('<div class="overflow-x-auto rounded-lg border border-dl-border/10"><table class="finance-table"><thead><tr></tr></thead><tbody></tbody></table> <!></div> <!>',1),q1=h('<th class="cursor-pointer select-none hover:text-dl-text"> </th>'),H1=h("<td> </td>"),U1=h("<tr></tr>"),W1=h('<button class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"> </button>'),K1=h('<div class="text-[10px] text-dl-text-dim mt-1"> </div>'),G1=h('<div class="overflow-x-auto rounded-lg border border-dl-border/10"><table class="prose-dartlab w-full text-[12px]"><thead><tr></tr></thead><tbody></tbody></table> <!></div> <!>',1);function Zl(t,e){Cr(e,!0);let r=Pe(e,"block",3,null),a=Pe(e,"maxRows",3,100),o=Z(null),i=Z(!1),s=Z(null),l=Z("asc");function u(j){n(s)===j?v(l,n(l)==="asc"?"desc":"asc",!0):(v(s,j,!0),v(l,"asc"))}function f(j){return n(s)!==j?"":n(l)==="asc"?" ▲":" ▼"}const p=new Set(["매출액","revenue","영업이익","operating_income","당기순이익","net_income","자산총계","total_assets","부채총계","total_liabilities","자본총계","total_equity","영업활동현금흐름","operating_cash_flow","매출총이익","gross_profit","EBITDA"]);function _(j,T){if(!(T!=null&&T.length))return!1;const G=String(j[T[0]]??"").trim();return p.has(G)}function g(j){if(j==null||j===""||j==="-")return j??"";if(typeof j=="number")return Math.abs(j)>=1?j.toLocaleString("ko-KR"):j.toString();const T=String(j).trim();if(/^-?[\d,]+(\.\d+)?$/.test(T)){const G=parseFloat(T.replace(/,/g,""));if(!isNaN(G))return Math.abs(G)>=1?G.toLocaleString("ko-KR"):G.toString()}return j}function w(j){if(typeof j=="number")return j<0;const T=String(j??"").trim().replace(/,/g,"");return/^-\d/.test(T)}function k(j){return typeof j=="number"?!0:typeof j=="string"&&/^-?[\d,]+(\.\d+)?$/.test(j.trim())}function S(j){return(j==null?void 0:j.kind)==="finance"}function b(j){return j!=null&&j.rawMarkdown?Object.keys(j.rawMarkdown):[]}function C(j){const T=b(j);return n(o)&&T.includes(n(o))?n(o):T[0]??null}let z=R(()=>{var G,K;const j=((K=(G=r())==null?void 0:G.data)==null?void 0:K.rows)??[];return n(s)?[...j].sort((ie,U)=>{let we=ie[n(s)],B=U[n(s)];const J=typeof we=="number"?we:parseFloat(String(we??"").replace(/,/g,"")),le=typeof B=="number"?B:parseFloat(String(B??"").replace(/,/g,""));return!isNaN(J)&&!isNaN(le)?n(l)==="asc"?J-le:le-J:(we=String(we??""),B=String(B??""),n(l)==="asc"?we.localeCompare(B):B.localeCompare(we))}):j}),P=R(()=>n(i)?n(z):n(z).slice(0,a()));var E=be(),ee=ae(E);{var se=j=>{var T=be(),G=ae(T);{var K=B=>{const J=R(()=>b(r())),le=R(()=>C(r()));var X=be(),O=ae(X);{var W=F=>{var ce=O1(),ne=ae(ce);{var D=ke=>{var re=L1(),Fe=d(re);Wc(Fe,{get periods(){return n(J)},get selected(){return n(le)},onSelect:ot=>{v(o,ot,!0)}}),c(ke,re)};$(ne,ke=>{n(J).length>1&&ke(D)})}var H=m(ne,2),te=d(H),Y=m(H,2),xe=d(Y);Nn(xe,()=>Ma(r().rawMarkdown[n(le)])),A(()=>I(te,n(le))),c(F,ce)};$(O,F=>{n(J).length>0&&F(W)})}c(B,X)},ie=B=>{var J=B1(),le=ae(J),X=d(le),O=d(X),W=d(O);Ce(W,21,()=>r().data.columns??[],$e,(te,Y)=>{var xe=R1(),ke=d(xe);A(re=>I(ke,`${n(Y)??""}${re??""}`),[()=>f(n(Y))]),ve("click",xe,()=>u(n(Y))),c(te,xe)});var F=m(O);Ce(F,21,()=>n(P),$e,(te,Y)=>{const xe=R(()=>_(n(Y),r().data.columns));var ke=j1();Ce(ke,21,()=>r().data.columns??[],$e,(re,Fe,ot)=>{const nt=R(()=>n(Y)[n(Fe)]),lt=R(()=>ot>0&&k(n(nt)));var at=D1(),vt=d(at);A((tt,Qe)=>{Xe(at,1,tt),I(vt,Qe)},[()=>n(lt)?w(n(nt))?"val-neg":"val-pos":"",()=>n(lt)?g(n(nt)):n(nt)??""]),c(re,at)}),A(()=>Xe(ke,1,ur(n(xe)?"row-key":""))),c(te,ke)});var ce=m(X,2);{var ne=te=>{var Y=F1(),xe=d(Y);A(()=>I(xe,`외 ${r().data.rows.length-a()}행 더 보기`)),ve("click",Y,()=>{v(i,!0)}),c(te,Y)};$(ce,te=>{!n(i)&&r().data.rows.length>a()&&te(ne)})}var D=m(le,2);{var H=te=>{var Y=V1(),xe=d(Y);A(()=>I(xe,`단위: ${(r().meta.unit||"")??""} ${r().meta.scale?`(${r().meta.scale})`:""}`)),c(te,Y)};$(D,te=>{var Y,xe;((Y=r().meta)!=null&&Y.scale||(xe=r().meta)!=null&&xe.unit)&&te(H)})}c(B,J)},U=R(()=>{var B;return S(r())&&((B=r().data)==null?void 0:B.rows)}),we=B=>{var J=G1(),le=ae(J),X=d(le),O=d(X),W=d(O);Ce(W,21,()=>r().data.columns??[],$e,(te,Y)=>{var xe=q1(),ke=d(xe);A(re=>I(ke,`${n(Y)??""}${re??""}`),[()=>f(n(Y))]),ve("click",xe,()=>u(n(Y))),c(te,xe)});var F=m(O);Ce(F,21,()=>n(P),$e,(te,Y)=>{var xe=U1();Ce(xe,21,()=>r().data.columns??[],$e,(ke,re)=>{var Fe=H1(),ot=d(Fe);A(nt=>{Xe(Fe,1,nt),I(ot,n(Y)[n(re)]??"")},[()=>ur(k(n(Y)[n(re)])?"num":"")]),c(ke,Fe)}),c(te,xe)});var ce=m(X,2);{var ne=te=>{var Y=W1(),xe=d(Y);A(()=>I(xe,`외 ${r().data.rows.length-a()}행 더 보기`)),ve("click",Y,()=>{v(i,!0)}),c(te,Y)};$(ce,te=>{!n(i)&&r().data.rows.length>a()&&te(ne)})}var D=m(le,2);{var H=te=>{var Y=K1(),xe=d(Y);A(()=>I(xe,`단위: ${(r().meta.unit||"")??""} ${r().meta.scale?`(${r().meta.scale})`:""}`)),c(te,Y)};$(D,te=>{var Y;(Y=r().meta)!=null&&Y.scale&&te(H)})}c(B,J)};$(G,B=>{var J;r().kind==="raw_markdown"&&r().rawMarkdown?B(K):n(U)?B(ie,1):(J=r().data)!=null&&J.rows&&B(we,2)})}c(j,T)};$(ee,j=>{r()&&j(se)})}c(t,E),Sr()}Or(["click"]);var J1=h('<span class="flex items-center gap-1"><!> <span class="text-dl-accent"> </span> <span class="text-dl-text-dim/60"> </span></span>'),Y1=h('<span class="flex items-center gap-1"><!> <span>변경 없음</span></span>'),X1=h('<span class="flex items-center gap-1 ml-auto"><span class="font-mono"> </span> <!> <span class="font-mono"> </span></span>'),Q1=h('<div class="text-dl-success/80 truncate"> </div>'),Z1=h('<div class="text-dl-primary-light/70 truncate"> </div>'),eg=h('<div class="text-[11px] leading-relaxed"><!> <!></div>'),tg=h('<div class="flex flex-col gap-1.5 p-2.5 rounded-lg bg-dl-surface-card border border-dl-border/20"><div class="flex items-center gap-3 text-[11px] text-dl-text-dim"><span class="font-mono"> </span> <!> <!></div> <!></div>');function rg(t,e){Cr(e,!0);let r=Pe(e,"summary",3,null);var a=be(),o=ae(a);{var i=s=>{var l=tg(),u=d(l),f=d(u),p=d(f),_=m(f,2);{var g=z=>{var P=J1(),E=d(P);xs(E,{size:11,class:"text-dl-accent"});var ee=m(E,2),se=d(ee),j=m(ee,2),T=d(j);A(G=>{I(se,`변경 ${r().changedCount??""}회`),I(T,`(${G??""}%)`)},[()=>(r().changeRate*100).toFixed(1)]),c(z,P)},w=z=>{var P=Y1(),E=d(P);Bc(E,{size:11}),c(z,P)};$(_,z=>{r().changedCount>0?z(g):z(w,-1)})}var k=m(_,2);{var S=z=>{var P=X1(),E=d(P),ee=d(E),se=m(E,2);ah(se,{size:10});var j=m(se,2),T=d(j);A(()=>{I(ee,r().latestFrom),I(T,r().latestTo)}),c(z,P)};$(k,z=>{r().latestFrom&&r().latestTo&&z(S)})}var b=m(u,2);{var C=z=>{var P=eg(),E=d(P);Ce(E,17,()=>r().added.slice(0,2),$e,(se,j)=>{var T=Q1(),G=d(T);A(()=>I(G,`+ ${n(j)??""}`)),c(se,T)});var ee=m(E,2);Ce(ee,17,()=>r().removed.slice(0,2),$e,(se,j)=>{var T=Z1(),G=d(T);A(()=>I(G,`- ${n(j)??""}`)),c(se,T)}),c(z,P)};$(b,z=>{var P,E;(((P=r().added)==null?void 0:P.length)>0||((E=r().removed)==null?void 0:E.length)>0)&&z(C)})}A(()=>I(p,`${r().totalPeriods??""} periods`)),c(s,l)};$(o,s=>{r()&&s(i)})}c(t,a),Sr()}var ng=h("<option> </option>"),ag=h("<option> </option>"),og=h('<button class="p-1 ml-1 text-dl-text-dim hover:text-dl-text"><!></button>'),sg=h('<span class="flex items-center gap-1 text-emerald-400"><!> <span> </span></span>'),ig=h('<span class="flex items-center gap-1 text-red-400"><!> <span> </span></span>'),lg=h('<span class="flex items-center gap-1 text-dl-text-dim"><!> <span> </span></span>'),dg=h('<div class="flex items-center gap-3 px-4 py-1.5 border-b border-dl-border/10 text-[10px]"><!> <!> <!></div>'),cg=h('<div class="flex items-center justify-center py-8 gap-2"><!> <span class="text-[12px] text-dl-text-dim">비교 로딩 중...</span></div>'),ug=h('<div class="text-[12px] text-red-400 py-4"> </div>'),fg=h('<mark class="bg-emerald-400/25 text-emerald-300 rounded-sm px-[1px]"> </mark>'),vg=h('<span class="text-dl-text/85"> </span>'),pg=h('<span class="text-dl-text/85"> </span>'),hg=h('<div class="pl-3 py-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-[13px] leading-[1.8] rounded-r"><span class="text-emerald-500/60 text-[10px] mr-1">+</span> <!></div>'),mg=h('<mark class="bg-red-400/25 text-red-300 line-through decoration-red-400/40 rounded-sm px-[1px]"> </mark>'),xg=h('<span class="text-dl-text/40"> </span>'),gg=h('<span class="text-dl-text/40 line-through decoration-red-400/30"> </span>'),_g=h('<div class="pl-3 py-1 border-l-2 border-red-400 bg-red-500/5 text-[13px] leading-[1.8] rounded-r"><span class="text-red-400/60 text-[10px] mr-1">-</span> <!></div>'),bg=h('<p class="text-[13px] leading-[1.8] text-dl-text/70 py-0.5"> </p>'),wg=h('<div class="space-y-0.5"></div>'),yg=h('<div class="text-[12px] text-dl-text-dim text-center py-4">비교할 기간을 선택하세요</div>'),kg=h('<div class="rounded-xl border border-dl-border/20 bg-dl-surface-card overflow-hidden"><div class="flex items-center gap-2 px-4 py-2 border-b border-dl-border/15 bg-dl-bg-darker/50"><!> <span class="text-[12px] font-semibold text-dl-text">기간 비교</span> <div class="flex items-center gap-1 ml-auto"><select class="px-2 py-0.5 rounded bg-dl-bg-darker border border-dl-border/20 text-[11px] text-dl-text outline-none"></select> <span class="text-[11px] text-dl-text-dim">→</span> <select class="px-2 py-0.5 rounded bg-dl-bg-darker border border-dl-border/20 text-[11px] text-dl-text outline-none"></select> <!></div></div> <!> <div class="max-h-[60vh] overflow-y-auto px-4 py-3"><!></div></div>');function Cg(t,e){Cr(e,!0);let r=Pe(e,"stockCode",3,null),a=Pe(e,"topic",3,null),o=Pe(e,"periods",19,()=>[]),i=Pe(e,"onClose",3,null),s=Z(null),l=Z(null),u=Z(null),f=Z(!1),p=Z(null);xr(()=>{o().length>=2&&!n(s)&&!n(l)&&(v(l,o()[0],!0),v(s,o()[1],!0))});async function _(){if(!(!r()||!a()||!n(s)||!n(l))){v(f,!0),v(p,null);try{const B=await vc(r(),a(),n(s),n(l));v(u,B,!0)}catch(B){v(p,B.message,!0)}v(f,!1)}}xr(()=>{n(s)&&n(l)&&n(s)!==n(l)&&_()});function g(B){if(!B)return"";const J=String(B).match(/^(\d{4})(Q([1-4]))?$/);return J?J[3]?`'${J[1].slice(2)}.${J[3]}Q`:`'${J[1].slice(2)}`:B}let w=R(()=>{var X;if(!((X=n(u))!=null&&X.diff))return{added:0,removed:0,same:0};let B=0,J=0,le=0;for(const O of n(u).diff)O.kind==="added"?B++:O.kind==="removed"?J++:le++;return{added:B,removed:J,same:le}});var k=kg(),S=d(k),b=d(S);Rc(b,{size:14,class:"text-dl-accent"});var C=m(b,4),z=d(C);Ce(z,21,o,$e,(B,J)=>{var le=ng(),X=d(le),O={};A(W=>{le.disabled=n(J)===n(l),I(X,W),O!==(O=n(J))&&(le.value=(le.__value=n(J))??"")},[()=>g(n(J))]),c(B,le)});var P=m(z,4);Ce(P,21,o,$e,(B,J)=>{var le=ag(),X=d(le),O={};A(W=>{le.disabled=n(J)===n(s),I(X,W),O!==(O=n(J))&&(le.value=(le.__value=n(J))??"")},[()=>g(n(J))]),c(B,le)});var E=m(P,2);{var ee=B=>{var J=og(),le=d(J);za(le,{size:12}),ve("click",J,function(...X){var O;(O=i())==null||O.apply(this,X)}),c(B,J)};$(E,B=>{i()&&B(ee)})}var se=m(S,2);{var j=B=>{var J=dg(),le=d(J);{var X=ne=>{var D=sg(),H=d(D);Mi(H,{size:10});var te=m(H,2),Y=d(te);A(()=>I(Y,`추가 ${n(w).added??""}`)),c(ne,D)};$(le,ne=>{n(w).added>0&&ne(X)})}var O=m(le,2);{var W=ne=>{var D=ig(),H=d(D);Bc(H,{size:10});var te=m(H,2),Y=d(te);A(()=>I(Y,`삭제 ${n(w).removed??""}`)),c(ne,D)};$(O,ne=>{n(w).removed>0&&ne(W)})}var F=m(O,2);{var ce=ne=>{var D=lg(),H=d(D);lh(H,{size:10});var te=m(H,2),Y=d(te);A(()=>I(Y,`유지 ${n(w).same??""}`)),c(ne,D)};$(F,ne=>{n(w).same>0&&ne(ce)})}c(B,J)};$(se,B=>{n(u)&&!n(f)&&B(j)})}var T=m(se,2),G=d(T);{var K=B=>{var J=cg(),le=d(J);Ar(le,{size:14,class:"animate-spin text-dl-text-dim"}),c(B,J)},ie=B=>{var J=ug(),le=d(J);A(()=>I(le,n(p))),c(B,J)},U=B=>{var J=wg();Ce(J,21,()=>n(u).diff,$e,(le,X)=>{var O=be(),W=ae(O);{var F=D=>{var H=hg(),te=m(d(H),2);{var Y=ke=>{var re=be(),Fe=ae(re);Ce(Fe,17,()=>n(X).parts,$e,(ot,nt)=>{var lt=be(),at=ae(lt);{var vt=Qe=>{var yt=fg(),$t=d(yt);A(()=>I($t,n(nt).text)),c(Qe,yt)},tt=Qe=>{var yt=vg(),$t=d(yt);A(()=>I($t,n(nt).text)),c(Qe,yt)};$(at,Qe=>{n(nt).kind==="insert"?Qe(vt):n(nt).kind==="equal"&&Qe(tt,1)})}c(ot,lt)}),c(ke,re)},xe=ke=>{var re=pg(),Fe=d(re);A(()=>I(Fe,n(X).text)),c(ke,re)};$(te,ke=>{n(X).parts?ke(Y):ke(xe,-1)})}c(D,H)},ce=D=>{var H=_g(),te=m(d(H),2);{var Y=ke=>{var re=be(),Fe=ae(re);Ce(Fe,17,()=>n(X).parts,$e,(ot,nt)=>{var lt=be(),at=ae(lt);{var vt=Qe=>{var yt=mg(),$t=d(yt);A(()=>I($t,n(nt).text)),c(Qe,yt)},tt=Qe=>{var yt=xg(),$t=d(yt);A(()=>I($t,n(nt).text)),c(Qe,yt)};$(at,Qe=>{n(nt).kind==="delete"?Qe(vt):n(nt).kind==="equal"&&Qe(tt,1)})}c(ot,lt)}),c(ke,re)},xe=ke=>{var re=gg(),Fe=d(re);A(()=>I(Fe,n(X).text)),c(ke,re)};$(te,ke=>{n(X).parts?ke(Y):ke(xe,-1)})}c(D,H)},ne=D=>{var H=bg(),te=d(H);A(()=>I(te,n(X).text)),c(D,H)};$(W,D=>{n(X).kind==="added"?D(F):n(X).kind==="removed"?D(ce,1):D(ne,-1)})}c(le,O)}),c(B,J)},we=B=>{var J=yg();c(B,J)};$(G,B=>{var J;n(f)?B(K):n(p)?B(ie,1):(J=n(u))!=null&&J.diff?B(U,2):B(we,-1)})}Ml(z,()=>n(s),B=>v(s,B)),Ml(P,()=>n(l),B=>v(l,B)),c(t,k),Sr()}Or(["click"]);var Sg=h("<button><!></button>"),$g=h("<button><!> <span>기간 비교</span></button>"),zg=h("<button><!> <span>AI 요약</span></button>"),Mg=h('<div class="text-red-400/80"> </div>'),Tg=h('<span class="inline-block w-1.5 h-3 bg-dl-accent/60 animate-pulse ml-0.5"></span>'),Ig=h('<div class="whitespace-pre-wrap"> <!></div>'),Ag=h('<div class="px-3 py-2 rounded-lg bg-dl-accent/5 border border-dl-accent/15 text-[12px] text-dl-text-muted leading-relaxed"><!></div>'),Eg=h('<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim"> </span>'),Ng=h('<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim"> </span>'),Pg=h('<span class="px-2 py-0.5 rounded-full border border-emerald-500/20 bg-emerald-500/8 text-emerald-400/80"> </span>'),Lg=h('<span class="px-2 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/8 text-blue-400/80"> </span>'),Og=h("<div> </div>"),Rg=h('<h4 class="text-[14px] font-semibold text-dl-text"> </h4>'),Dg=h('<div class="mb-2 mt-2"></div>'),jg=h('<span class="text-[10px] text-dl-text-dim font-mono"> </span>'),Fg=h('<span class="text-[10px] text-dl-text-dim"> </span>'),Vg=h('<span class="ml-0.5 text-emerald-400/50">*</span>'),Bg=h("<button> <!></button>"),qg=h('<div class="flex flex-wrap gap-1 mb-2"></div>'),Hg=h('<div class="text-blue-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-blue-400/60 mt-1.5 shrink-0"></span> </div>'),Ug=h('<div class="text-emerald-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-emerald-400/50 mt-1.5 shrink-0"></span> </div>'),Wg=h('<div class="text-dl-text-dim/50 flex gap-1"><span class="w-1 h-1 rounded-full bg-red-400/40 mt-1.5 shrink-0"></span> </div>'),Kg=h('<div class="mb-3 px-3 py-2 rounded-lg border border-dl-border/15 bg-dl-surface-card/50 text-[11px] space-y-0.5 max-w-2xl"><div class="text-dl-text-dim font-medium"> </div> <!> <!> <!></div>'),Gg=h('<div class="mb-2 px-3 py-1.5 rounded-lg border border-dl-border/15 bg-dl-surface-card/30 text-[11px] text-dl-text-dim">이전 기간과 동일 — 변경 없음</div>'),Jg=h('<mark class="bg-emerald-400/25 text-emerald-300 rounded-sm px-[1px]"> </mark>'),Yg=h('<span class="text-dl-text/85"> </span>'),Xg=h('<span class="text-dl-text/85"> </span>'),Qg=h('<div class="pl-3 py-1 mb-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-[14px] leading-[1.85] rounded-r"><span class="text-emerald-500/50 text-[10px] mr-1">+</span> <!></div>'),Zg=h('<mark class="bg-red-400/25 text-red-300 line-through decoration-red-400/40 rounded-sm px-[1px]"> </mark>'),e_=h('<span class="text-dl-text/40"> </span>'),t_=h('<span class="text-dl-text/40 line-through decoration-red-400/30"> </span>'),r_=h('<div class="pl-3 py-1 mb-1 border-l-2 border-red-400 bg-red-500/5 text-[14px] leading-[1.85] rounded-r"><span class="text-red-400/60 text-[10px] mr-1">-</span> <!></div>'),n_=h('<p class="vw-para"> </p>'),a_=h('<div class="text-[10px] text-dl-text-dim/40 mb-1">글자 단위 비교 로딩 중...</div>'),o_=h('<p class="vw-para"> </p>'),s_=h('<div class="pl-3 py-1 mb-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-dl-text/85 text-[14px] leading-[1.85] rounded-r"><span class="text-emerald-500/50 text-[10px] mr-1">+</span> </div>'),i_=h('<div class="pl-3 py-1 mb-1 border-l-2 border-red-400 bg-red-500/5 text-dl-text/50 text-[14px] leading-[1.85] rounded-r line-through decoration-red-400/30"><span class="text-red-400/50 text-[10px] mr-1">-</span> </div>'),l_=h("<!> <!>",1),d_=h('<div><!> <div class="flex flex-wrap items-center gap-1.5 mb-2"><span> </span> <!> <!></div> <!> <!> <!>  <div class="disclosure-text max-w-3xl"><!></div></div>'),c_=h('<div class="mt-6 pt-4 border-t border-dl-border/10"><div class="text-[10px] text-dl-text-dim uppercase tracking-widest font-semibold mb-3">표 · 정형 데이터</div></div>'),u_=h("<button><!></button>"),f_=h('<button class="p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="테이블 복사"><!></button>'),v_=h('<div class="group relative"><div class="absolute top-1 right-1 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"><!> <!></div> <!></div>'),p_=h('<div class="flex flex-wrap gap-1.5 text-[10px]"><!> <!> <!> <!></div> <!> <!> <!>',1),h_=h('<h3 class="text-[14px] font-semibold text-dl-text mt-4 mb-1"> </h3>'),m_=h('<div class="mb-1 opacity-0 group-hover:opacity-100 transition-opacity"><!></div>'),x_=h('<!> <div class="text-[10px] text-dl-text-dim mb-1 font-mono"> </div> <div class="disclosure-text"><!></div>',1),g_=h('<div class="group"><!></div>'),__=h("<button><!></button>"),b_=h('<button class="p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="테이블 복사"><!></button>'),w_=h('<div class="group relative"><div class="absolute top-1 right-1 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"><!> <!></div> <!></div>'),y_=h('<div class="text-center py-12 text-[13px] text-dl-text-dim">이 topic에 표시할 데이터가 없습니다</div>'),k_=h('<div class="space-y-4"><div class="flex items-center gap-2"><h2 class="text-[16px] font-semibold text-dl-text flex-1"> </h2> <!> <!> <!></div> <!> <!> <!> <!> <!></div>'),C_=h('<button class="ask-ai-float"><span class="flex items-center gap-1"><!> AI에게 물어보기</span></button>'),S_=h("<!> <!>",1);function $_(t,e){Cr(e,!0);let r=Pe(e,"topicData",3,null),a=Pe(e,"diffSummary",3,null),o=Pe(e,"viewer",3,null),i=Pe(e,"onAskAI",3,null),s=Pe(e,"searchHighlight",3,null),l=Z(Ut(new Map)),u=Z(Ut(new Map)),f=Z(null),p=Z(Ut(new Map)),_=Z(Ut({show:!1,x:0,y:0,text:""})),g=Z(!1),w=Z(""),k=Z(null),S=Z(null);xr(()=>{var x,N,L;if((x=r())!=null&&x.topic){v(g,!1),v(k,null);const q=(L=(N=o())==null?void 0:N.getTopicSummary)==null?void 0:L.call(N,r().topic);v(w,q||"",!0),n(S)&&(n(S).abort(),v(S,null))}});function b(){var x,N;!((x=o())!=null&&x.stockCode)||!((N=r())!=null&&N.topic)||(v(g,!0),v(w,""),v(k,null),v(S,Dv(o().stockCode,r().topic,{onContext(){},onChunk(L){v(w,n(w)+L)},onDone(){var L,q;v(g,!1),v(S,null),n(w)&&((q=(L=o())==null?void 0:L.setTopicSummary)==null||q.call(L,r().topic,n(w)))},onError(L){v(g,!1),v(S,null),v(k,L,!0)}}),!0))}let C=R(()=>{var x,N,L;return((L=(x=o())==null?void 0:x.isBookmarked)==null?void 0:L.call(x,(N=r())==null?void 0:N.topic))??!1}),z=Z(Ut(new Map)),P=Z(Ut(new Set));async function E(x,N,L){var V,Q;if(!((V=o())!=null&&V.stockCode)||!((Q=r())!=null&&Q.topic)||!L||!N)return;const q=`${x}:${N}`;if(n(z).has(q)||n(P).has(q))return;v(P,new Set([...n(P),q]),!0);try{const he=await vc(o().stockCode,r().topic,L,N),fe=new Map(n(z));fe.set(q,he),v(z,fe,!0)}catch{}const y=new Set(n(P));y.delete(q),v(P,y,!0)}let ee=Z(!1);xr(()=>{var x;(x=r())!=null&&x.topic&&(v(ee,!1),v(z,new Map,!0),v(P,new Set,!0))});let se=R(()=>{var N,L,q,y,V,Q;if(!((q=(L=(N=r())==null?void 0:N.textDocument)==null?void 0:L.sections)!=null&&q.length))return[];const x=new Set;for(const he of r().textDocument.sections)if(he.timeline)for(const fe of he.timeline){const me=((y=fe.period)==null?void 0:y.label)||((V=fe.period)!=null&&V.year&&((Q=fe.period)!=null&&Q.quarter)?`${fe.period.year}Q${fe.period.quarter}`:null);me&&x.add(me)}return[...x].sort().reverse()}),j=R(()=>{var x,N,L;return((L=(N=(x=r())==null?void 0:x.textDocument)==null?void 0:N.sections)==null?void 0:L.length)>0}),T=R(()=>{var x;return(((x=r())==null?void 0:x.blocks)??[]).filter(N=>N.kind!=="text")});function G(x){if(!x)return"";if(typeof x=="string"){const N=x.match(/^(\d{4})(Q([1-4]))?$/);return N?N[3]?`${N[1]}Q${N[3]}`:N[1]:x}return x.kind==="annual"?`${x.year}Q4`:x.year&&x.quarter?`${x.year}Q${x.quarter}`:x.label||""}function K(x){return x==="updated"?"수정됨":x==="new"?"신규":x==="stale"?"과거유지":"유지"}function ie(x){return x==="updated"?"bg-emerald-500/10 text-emerald-400/80 border-emerald-500/20":x==="new"?"bg-blue-500/10 text-blue-400/80 border-blue-500/20":x==="stale"?"bg-amber-500/10 text-amber-400/80 border-amber-500/20":"bg-dl-border/10 text-dl-text-dim border-dl-border/20"}function U(x){var L;const N=n(u).get(x.id);return N&&((L=x.views)!=null&&L[N])?x.views[N]:x.latest||null}function we(x,N){var q,y;const L=n(u).get(x.id);return L?L===N:((y=(q=x.latest)==null?void 0:q.period)==null?void 0:y.label)===N}function B(x){return n(u).has(x.id)}function J(x,N,L){var y;const q=new Map(n(u));if(q.get(x)===N)q.delete(x);else if(q.set(x,N),((y=L==null?void 0:L.timeline)==null?void 0:y.length)>1){const V=L.timeline.map(fe=>{var me;return((me=fe.period)==null?void 0:me.label)||G(fe.period)}),Q=V.indexOf(N),he=Q>=0&&Q<V.length-1?V[Q+1]:null;he&&E(x,N,he)}v(u,q,!0)}function le(x){return x.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function X(x){return String(x||"").replace(/\u00a0/g," ").replace(/\s+/g," ").trim()}function O(x){return!x||x.length>88?!1:/^\[.+\]$/.test(x)||/^【.+】$/.test(x)||/^[IVX]+\.\s/.test(x)||/^\d+\.\s/.test(x)||/^[가-힣]\.\s/.test(x)||/^\(\d+\)\s/.test(x)||/^\([가-힣]\)\s/.test(x)||/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(x)}function W(x){return/^[가나다라마바사아자차카타파하]\.\s/.test(x)?1:/^\d+\.\s/.test(x)?2:/^\(\d+\)\s/.test(x)||/^\([가-힣]\)\s/.test(x)?3:/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(x)?4:/^\[.+\]$/.test(x)||/^【.+】$/.test(x)?1:2}function F(x){if(!x)return"";if(/^\|.+\|$/m.test(x))return Ma(x);const N=x.split(`
`);let L="",q=[];function y(){q.length!==0&&(L+=`<p class="vw-para">${le(q.join(" "))}</p>`,q=[])}for(const V of N){const Q=X(V);if(!Q){y();continue}if(O(Q)){y();const he=W(Q);L+=`<div class="ko-h${he}">${le(Q)}</div>`}else q.push(Q)}return y(),L}function ce(x){var L;if(!((L=x==null?void 0:x.diff)!=null&&L.length))return null;const N=[];for(const q of x.diff)for(const y of q.paragraphs||[])N.push({kind:q.kind,text:X(y)});return N}function ne(x){return n(l).get(x)??null}function D(x,N){const L=new Map(n(l));L.set(x,N),v(l,L,!0)}function H(x,N){var L,q;return(q=(L=x==null?void 0:x.data)==null?void 0:L.rows)!=null&&q[0]?x.data.rows[0][N]??null:null}function te(x){var L,q,y;if(!((q=(L=x==null?void 0:x.data)==null?void 0:L.rows)!=null&&q[0]))return null;const N=x.data.rows[0];for(const V of((y=x.meta)==null?void 0:y.periods)??[])if(N[V])return{period:V,text:N[V]};return null}function Y(x){var L,q,y;if(!((q=(L=x==null?void 0:x.data)==null?void 0:L.rows)!=null&&q[0]))return[];const N=x.data.rows[0];return(((y=x.meta)==null?void 0:y.periods)??[]).filter(V=>N[V]!=null)}function xe(x){return x.kind==="text"}function ke(x){return x.kind==="finance"||x.kind==="structured"||x.kind==="report"||x.kind==="raw_markdown"}function re(x){var N,L,q,y;return x.kind==="finance"&&((L=(N=x.data)==null?void 0:N.rows)==null?void 0:L.length)>0&&((y=(q=x.data)==null?void 0:q.columns)==null?void 0:y.length)>2}function Fe(x){return A1(x)}function ot(x){const N=new Map(n(p));N.set(x,!N.get(x)),v(p,N,!0)}function nt(x,N){var y,V;if(!((V=(y=x==null?void 0:x.data)==null?void 0:y.rows)!=null&&V.length))return;const L=x.data.columns||[],q=[L.join("	")];for(const Q of x.data.rows)q.push(L.map(he=>Q[he]??"").join("	"));navigator.clipboard.writeText(q.join(`
`)).then(()=>{v(f,N,!0),setTimeout(()=>{v(f,null)},2e3)})}function lt(x){if(!i())return;const N=window.getSelection(),L=N==null?void 0:N.toString().trim();if(!L||L.length<5){v(_,{show:!1,x:0,y:0,text:""},!0);return}const y=N.getRangeAt(0).getBoundingClientRect();v(_,{show:!0,x:y.left+y.width/2,y:y.top-8,text:L.slice(0,500)},!0)}function at(){n(_).text&&i()&&i()(n(_).text),v(_,{show:!1,x:0,y:0,text:""},!0)}function vt(){n(_).show&&v(_,{show:!1,x:0,y:0,text:""},!0)}function tt(x){if(!s()||!x)return x;const N=s().replace(/[.*+?^${}()|[\]\\]/g,"\\$&"),L=new RegExp(`(${N})`,"gi");return x.replace(L,'<mark class="bg-amber-400/30 text-dl-text rounded-sm px-0.5">$1</mark>')}xr(()=>{var x;s()&&((x=r())!=null&&x.topic)&&requestAnimationFrame(()=>{const N=document.querySelector(".disclosure-text mark");N&&N.scrollIntoView({block:"center",behavior:"smooth"})})});var Qe=S_();bn("click",Ld,vt);var yt=ae(Qe);{var $t=x=>{var N=k_(),L=d(N),q=d(L),y=d(q),V=m(q,2);{var Q=Me=>{var ye=Sg(),dt=d(ye);{let Be=R(()=>n(C)?"currentColor":"none");Ti(dt,{size:14,get fill(){return n(Be)}})}A(()=>{Xe(ye,1,`p-1 rounded transition-colors ${n(C)?"text-amber-400":"text-dl-text-dim/30 hover:text-amber-400/60"}`),ar(ye,"title",n(C)?"북마크 해제":"북마크 추가")}),ve("click",ye,()=>o().toggleBookmark(r().topic)),c(Me,ye)};$(V,Me=>{o()&&Me(Q)})}var he=m(V,2);{var fe=Me=>{var ye=$g(),dt=d(ye);Rc(dt,{size:10}),A(()=>Xe(ye,1,`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors border
						${n(ee)?"border-dl-accent/30 bg-dl-accent/10 text-dl-accent-light":"border-dl-border/20 text-dl-text-dim hover:text-dl-text hover:bg-white/5"}`)),ve("click",ye,()=>{v(ee,!n(ee))}),c(Me,ye)};$(he,Me=>{n(se).length>=2&&Me(fe)})}var me=m(he,2);{var Ae=Me=>{var ye=zg(),dt=d(ye);{var Be=rt=>{Ar(rt,{size:10,class:"animate-spin"})},Oe=rt=>{qc(rt,{size:10})};$(dt,rt=>{n(g)?rt(Be):rt(Oe,-1)})}A(()=>{Xe(ye,1,`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors border
						${n(g)?"border-dl-accent/30 bg-dl-accent/10 text-dl-accent-light":"border-dl-border/20 text-dl-text-dim hover:text-dl-text hover:bg-white/5"}`),ye.disabled=n(g)}),ve("click",ye,b),c(Me,ye)};$(me,Me=>{var ye;(ye=o())!=null&&ye.stockCode&&Me(Ae)})}var qe=m(L,2);{var Ie=Me=>{var ye=Ag(),dt=d(ye);{var Be=rt=>{var kt=Mg(),Xt=d(kt);A(()=>I(Xt,n(k))),c(rt,kt)},Oe=rt=>{var kt=Ig(),Xt=d(kt),It=m(Xt);{var fr=_r=>{var br=Tg();c(_r,br)};$(It,_r=>{n(g)&&_r(fr)})}A(()=>I(Xt,n(w))),c(rt,kt)};$(dt,rt=>{n(k)?rt(Be):rt(Oe,-1)})}c(Me,ye)};$(qe,Me=>{(n(w)||n(g)||n(k))&&Me(Ie)})}var je=m(qe,2);rg(je,{get summary(){return a()}});var Re=m(je,2);{var De=Me=>{Cg(Me,{get stockCode(){return o().stockCode},get topic(){return r().topic},get periods(){return n(se)},onClose:()=>{v(ee,!1)}})};$(Re,Me=>{var ye;n(ee)&&((ye=o())!=null&&ye.stockCode)&&Me(De)})}var pt=m(Re,2);{var Ze=Me=>{const ye=R(()=>r().textDocument);var dt=p_(),Be=ae(dt),Oe=d(Be);{var rt=_t=>{var He=Eg(),bt=d(He);A(zt=>I(bt,`최신 ${zt??""}`),[()=>G(n(ye).latestPeriod)]),c(_t,He)};$(Oe,_t=>{n(ye).latestPeriod&&_t(rt)})}var kt=m(Oe,2);{var Xt=_t=>{var He=Ng(),bt=d(He);A(()=>I(bt,`${n(ye).sectionCount??""}개 섹션`)),c(_t,He)};$(kt,_t=>{n(ye).sectionCount&&_t(Xt)})}var It=m(kt,2);{var fr=_t=>{var He=Pg(),bt=d(He);A(()=>I(bt,`${n(ye).updatedCount??""}개 수정`)),c(_t,He)};$(It,_t=>{n(ye).updatedCount>0&&_t(fr)})}var _r=m(It,2);{var br=_t=>{var He=Lg(),bt=d(He);A(()=>I(bt,`${n(ye).newCount??""}개 신규`)),c(_t,He)};$(_r,_t=>{n(ye).newCount>0&&_t(br)})}var Wt=m(Be,2);Ce(Wt,17,()=>n(ye).sections,_t=>_t.id,(_t,He)=>{const bt=R(()=>U(n(He))),zt=R(()=>B(n(He))),pr=R(()=>ce(n(bt))),qt=R(()=>n(pr)&&n(pr).length>0),Ot=R(()=>n(qt)&&(n(zt)||n(He).status==="updated")),dr=R(()=>n(zt)&&!n(qt)&&n(He).periodCount>1),sr=R(()=>`${n(He).id}:${n(u).get(n(He).id)||""}`),Nt=R(()=>n(z).get(n(sr))),Ct=R(()=>n(P).has(n(sr)));var Rt=d_(),ir=d(Rt);{var gt=Pt=>{var M=Dg();Ce(M,21,()=>n(He).headingPath,$e,(de,Ee)=>{const Ne=R(()=>{var pe;return(pe=n(Ee).text)==null?void 0:pe.trim()});var Le=be(),et=ae(Le);{var ze=pe=>{var Te=be(),Ge=ae(Te);{var wt=Ht=>{var St=Og(),ue=d(St);A(_e=>{Xe(St,1,`ko-h${_e??""}`),I(ue,n(Ne))},[()=>W(n(Ne))]),c(Ht,St)},At=R(()=>O(n(Ne))),Ft=Ht=>{var St=Rg(),ue=d(St);A(()=>I(ue,n(Ne))),c(Ht,St)};$(Ge,Ht=>{n(At)?Ht(wt):Ht(Ft,-1)})}c(pe,Te)};$(et,pe=>{n(Ne)&&pe(ze)})}c(de,Le)}),c(Pt,M)};$(ir,Pt=>{var M;((M=n(He).headingPath)==null?void 0:M.length)>0&&Pt(gt)})}var Se=m(ir,2),Ue=d(Se),ht=d(Ue),Dt=m(Ue,2);{var Qt=Pt=>{var M=jg(),de=d(M);A(()=>I(de,n(He).latestChange)),c(Pt,M)};$(Dt,Pt=>{n(He).latestChange&&Pt(Qt)})}var We=m(Dt,2);{var Mt=Pt=>{var M=Fg(),de=d(M);A(()=>I(de,`${n(He).periodCount??""}기간`)),c(Pt,M)};$(We,Pt=>{n(He).periodCount>1&&Pt(Mt)})}var jt=m(Se,2);{var cr=Pt=>{var M=qg();Ce(M,21,()=>n(He).timeline,$e,(de,Ee)=>{const Ne=R(()=>{var Te;return((Te=n(Ee).period)==null?void 0:Te.label)||G(n(Ee).period)});var Le=Bg(),et=d(Le),ze=m(et);{var pe=Te=>{var Ge=Vg();c(Te,Ge)};$(ze,Te=>{n(Ee).status==="updated"&&Te(pe)})}A((Te,Ge)=>{Xe(Le,1,`px-2 py-1 rounded-lg text-[10px] font-mono transition-colors border
										${Te??""}`),I(et,`${Ge??""} `)},[()=>we(n(He),n(Ne))?"border-dl-accent/30 bg-dl-accent/8 text-dl-accent-light font-medium":n(Ee).status==="updated"?"border-emerald-500/15 text-emerald-400/60 hover:bg-emerald-500/5":"border-dl-border/15 text-dl-text-dim hover:bg-white/3",()=>G(n(Ee).period)]),ve("click",Le,()=>J(n(He).id,n(Ne),n(He))),c(de,Le)}),c(Pt,M)};$(jt,Pt=>{var M;((M=n(He).timeline)==null?void 0:M.length)>1&&!(n(He).status==="stable"&&(!n(He).preview||n(He).preview.length<60))&&Pt(cr)})}var Zt=m(jt,2);{var wr=Pt=>{const M=R(()=>n(bt).digest);var de=Kg(),Ee=d(de),Ne=d(Ee),Le=m(Ee,2);Ce(Le,17,()=>n(M).items.filter(pe=>pe.kind==="numeric"),$e,(pe,Te)=>{var Ge=Hg(),wt=m(d(Ge),1,!0);A(()=>I(wt,n(Te).text)),c(pe,Ge)});var et=m(Le,2);Ce(et,17,()=>n(M).items.filter(pe=>pe.kind==="added"),$e,(pe,Te)=>{var Ge=Ug(),wt=m(d(Ge),1,!0);A(()=>I(wt,n(Te).text)),c(pe,Ge)});var ze=m(et,2);Ce(ze,17,()=>n(M).items.filter(pe=>pe.kind==="removed"),$e,(pe,Te)=>{var Ge=Wg(),wt=m(d(Ge),1,!0);A(()=>I(wt,n(Te).text)),c(pe,Ge)}),A(()=>I(Ne,`${n(M).to??""} vs ${n(M).from??""}`)),c(Pt,de)};$(Zt,Pt=>{var M,de,Ee;((Ee=(de=(M=n(bt))==null?void 0:M.digest)==null?void 0:de.items)==null?void 0:Ee.length)>0&&Pt(wr)})}var Wr=m(Zt,2);{var $r=Pt=>{var M=Gg();c(Pt,M)};$(Wr,Pt=>{n(dr)&&Pt($r)})}var Pr=m(Wr,2),Sn=d(Pr);{var Dn=Pt=>{var M=be(),de=ae(M);Ce(de,17,()=>n(Nt).diff,$e,(Ee,Ne)=>{var Le=be(),et=ae(Le);{var ze=Ge=>{var wt=Qg(),At=m(d(wt),2);{var Ft=St=>{var ue=be(),_e=ae(ue);Ce(_e,17,()=>n(Ne).parts,$e,(ct,Je)=>{var xt=be(),tr=ae(xt);{var Kt=nr=>{var yr=Jg(),Kr=d(yr);A(()=>I(Kr,n(Je).text)),c(nr,yr)},er=nr=>{var yr=Yg(),Kr=d(yr);A(()=>I(Kr,n(Je).text)),c(nr,yr)};$(tr,nr=>{n(Je).kind==="insert"?nr(Kt):n(Je).kind==="equal"&&nr(er,1)})}c(ct,xt)}),c(St,ue)},Ht=St=>{var ue=Xg(),_e=d(ue);A(()=>I(_e,n(Ne).text)),c(St,ue)};$(At,St=>{n(Ne).parts?St(Ft):St(Ht,-1)})}c(Ge,wt)},pe=Ge=>{var wt=r_(),At=m(d(wt),2);{var Ft=St=>{var ue=be(),_e=ae(ue);Ce(_e,17,()=>n(Ne).parts,$e,(ct,Je)=>{var xt=be(),tr=ae(xt);{var Kt=nr=>{var yr=Zg(),Kr=d(yr);A(()=>I(Kr,n(Je).text)),c(nr,yr)},er=nr=>{var yr=e_(),Kr=d(yr);A(()=>I(Kr,n(Je).text)),c(nr,yr)};$(tr,nr=>{n(Je).kind==="delete"?nr(Kt):n(Je).kind==="equal"&&nr(er,1)})}c(ct,xt)}),c(St,ue)},Ht=St=>{var ue=t_(),_e=d(ue);A(()=>I(_e,n(Ne).text)),c(St,ue)};$(At,St=>{n(Ne).parts?St(Ft):St(Ht,-1)})}c(Ge,wt)},Te=Ge=>{var wt=n_(),At=d(wt);A(()=>I(At,n(Ne).text)),c(Ge,wt)};$(et,Ge=>{n(Ne).kind==="added"?Ge(ze):n(Ne).kind==="removed"?Ge(pe,1):Ge(Te,-1)})}c(Ee,Le)}),c(Pt,M)},sn=Pt=>{var M=l_(),de=ae(M);{var Ee=Le=>{var et=a_();c(Le,et)};$(de,Le=>{n(Ct)&&Le(Ee)})}var Ne=m(de,2);Ce(Ne,17,()=>n(pr),$e,(Le,et)=>{var ze=be(),pe=ae(ze);{var Te=At=>{var Ft=o_(),Ht=d(Ft);A(()=>I(Ht,n(et).text)),c(At,Ft)},Ge=At=>{var Ft=s_(),Ht=m(d(Ft),1,!0);A(()=>I(Ht,n(et).text)),c(At,Ft)},wt=At=>{var Ft=i_(),Ht=m(d(Ft),1,!0);A(()=>I(Ht,n(et).text)),c(At,Ft)};$(pe,At=>{n(et).kind==="same"?At(Te):n(et).kind==="added"?At(Ge,1):n(et).kind==="removed"&&At(wt,2)})}c(Le,ze)}),c(Pt,M)},jn=Pt=>{var M=be(),de=ae(M);Nn(de,()=>tt(F(n(bt).body))),c(Pt,M)};$(Sn,Pt=>{var M,de;n(Ot)&&((M=n(Nt))!=null&&M.diff)?Pt(Dn):n(Ot)?Pt(sn,1):(de=n(bt))!=null&&de.body&&Pt(jn,2)})}A((Pt,M)=>{Xe(Rt,1,`pt-2 pb-6 border-b border-dl-border/8 last:border-b-0 ${n(He).status==="stale"?"border-l-2 border-l-amber-400/40 pl-3":""}`),Xe(Ue,1,`px-1.5 py-0.5 rounded text-[9px] font-medium border ${Pt??""}`),I(ht,M)},[()=>ie(n(He).status),()=>K(n(He).status)]),ve("mouseup",Pr,lt),c(_t,Rt)});var mt=m(Wt,2);{var lr=_t=>{var He=c_();c(_t,He)};$(mt,_t=>{n(T).length>0&&_t(lr)})}var Rr=m(mt,2);Ce(Rr,19,()=>n(T),_t=>_t.block,(_t,He)=>{const bt=R(()=>re(n(He))),zt=R(()=>n(bt)&&n(p).get(n(He).block)),pr=R(()=>n(zt)?Fe(n(He)):null);var qt=v_(),Ot=d(qt),dr=d(Ot);{var sr=Se=>{var Ue=u_(),ht=d(Ue);{var Dt=We=>{Ii(We,{size:12})},Qt=We=>{$s(We,{size:12})};$(ht,We=>{n(zt)?We(Dt):We(Qt,-1)})}A(()=>{Xe(Ue,1,`p-1 rounded transition-colors ${n(zt)?"text-dl-accent-light bg-dl-accent/10":"text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5"}`),ar(Ue,"title",n(zt)?"표로 보기":"차트로 보기")}),ve("click",Ue,()=>ot(n(He).block)),c(Se,Ue)};$(dr,Se=>{n(bt)&&Se(sr)})}var Nt=m(dr,2);{var Ct=Se=>{var Ue=f_(),ht=d(Ue);{var Dt=We=>{zi(We,{size:12,class:"text-dl-success"})},Qt=We=>{Kl(We,{size:12})};$(ht,We=>{n(f)===n(He).block?We(Dt):We(Qt,-1)})}ve("click",Ue,()=>nt(n(He),n(He).block)),c(Se,Ue)};$(Nt,Se=>{var Ue,ht;((ht=(Ue=n(He).data)==null?void 0:Ue.rows)==null?void 0:ht.length)>0&&Se(Ct)})}var Rt=m(Ot,2);{var ir=Se=>{var Ue=be(),ht=ae(Ue);gi(ht,()=>Ai(()=>import("./ChartRenderer-B5E7I3qo.js"),__vite__mapDeps([0,1])),null,(Dt,Qt)=>{var We=R(()=>{var{default:Zt}=n(Qt);return{ChartRenderer:Zt}}),Mt=R(()=>n(We).ChartRenderer),jt=be(),cr=ae(jt);wo(cr,()=>n(Mt),(Zt,wr)=>{wr(Zt,{get spec(){return n(pr)}})}),c(Dt,jt)}),c(Se,Ue)},gt=Se=>{Zl(Se,{get block(){return n(He)}})};$(Rt,Se=>{n(zt)&&n(pr)?Se(ir):Se(gt,-1)})}c(_t,qt)}),c(Me,dt)},Bt=Me=>{var ye=be(),dt=ae(ye);Ce(dt,19,()=>r().blocks,Be=>Be.block,(Be,Oe,rt)=>{var kt=be(),Xt=ae(kt);{var It=Wt=>{const mt=R(()=>ne(n(rt))),lr=R(()=>te(n(Oe))),Rr=R(()=>Y(n(Oe))),_t=R(()=>{var qt;return n(mt)||((qt=n(lr))==null?void 0:qt.period)}),He=R(()=>{var qt;return n(_t)?H(n(Oe),n(_t)):(qt=n(lr))==null?void 0:qt.text});var bt=be(),zt=ae(bt);{var pr=qt=>{var Ot=g_(),dr=d(Ot);{var sr=Ct=>{var Rt=h_(),ir=d(Rt);A(()=>I(ir,n(He))),c(Ct,Rt)},Nt=Ct=>{var Rt=x_(),ir=ae(Rt);{var gt=Qt=>{var We=m_(),Mt=d(We);Wc(Mt,{get periods(){return n(Rr)},get selected(){return n(_t)},onSelect:jt=>D(n(rt),jt)}),c(Qt,We)};$(ir,Qt=>{n(Rr).length>1&&Qt(gt)})}var Se=m(ir,2),Ue=d(Se),ht=m(Se,2),Dt=d(ht);Nn(Dt,()=>tt(F(n(He)))),A(()=>I(Ue,n(_t))),ve("mouseup",ht,lt),c(Ct,Rt)};$(dr,Ct=>{n(Oe).textType==="heading"?Ct(sr):Ct(Nt,-1)})}c(qt,Ot)};$(zt,qt=>{n(He)&&qt(pr)})}c(Wt,bt)},fr=R(()=>xe(n(Oe))),_r=Wt=>{const mt=R(()=>re(n(Oe))),lr=R(()=>n(mt)&&n(p).get(n(Oe).block)),Rr=R(()=>n(lr)?Fe(n(Oe)):null);var _t=w_(),He=d(_t),bt=d(He);{var zt=Nt=>{var Ct=__(),Rt=d(Ct);{var ir=Se=>{Ii(Se,{size:12})},gt=Se=>{$s(Se,{size:12})};$(Rt,Se=>{n(lr)?Se(ir):Se(gt,-1)})}A(()=>{Xe(Ct,1,`p-1 rounded transition-colors ${n(lr)?"text-dl-accent-light bg-dl-accent/10":"text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5"}`),ar(Ct,"title",n(lr)?"표로 보기":"차트로 보기")}),ve("click",Ct,()=>ot(n(Oe).block)),c(Nt,Ct)};$(bt,Nt=>{n(mt)&&Nt(zt)})}var pr=m(bt,2);{var qt=Nt=>{var Ct=b_(),Rt=d(Ct);{var ir=Se=>{zi(Se,{size:12,class:"text-dl-success"})},gt=Se=>{Kl(Se,{size:12})};$(Rt,Se=>{n(f)===n(Oe).block?Se(ir):Se(gt,-1)})}ve("click",Ct,()=>nt(n(Oe),n(Oe).block)),c(Nt,Ct)};$(pr,Nt=>{var Ct,Rt;((Rt=(Ct=n(Oe).data)==null?void 0:Ct.rows)==null?void 0:Rt.length)>0&&Nt(qt)})}var Ot=m(He,2);{var dr=Nt=>{var Ct=be(),Rt=ae(Ct);gi(Rt,()=>Ai(()=>import("./ChartRenderer-B5E7I3qo.js"),__vite__mapDeps([0,1])),null,(ir,gt)=>{var Se=R(()=>{var{default:Qt}=n(gt);return{ChartRenderer:Qt}}),Ue=R(()=>n(Se).ChartRenderer),ht=be(),Dt=ae(ht);wo(Dt,()=>n(Ue),(Qt,We)=>{We(Qt,{get spec(){return n(Rr)}})}),c(ir,ht)}),c(Nt,Ct)},sr=Nt=>{Zl(Nt,{get block(){return n(Oe)}})};$(Ot,Nt=>{n(lr)&&n(Rr)?Nt(dr):Nt(sr,-1)})}c(Wt,_t)},br=R(()=>ke(n(Oe)));$(Xt,Wt=>{n(fr)?Wt(It):n(br)&&Wt(_r,1)})}c(Be,kt)}),c(Me,ye)};$(pt,Me=>{n(j)?Me(Ze):Me(Bt,-1)})}var ge=m(pt,2);{var Ve=Me=>{var ye=y_();c(Me,ye)};$(ge,Me=>{var ye;((ye=r().blocks)==null?void 0:ye.length)===0&&!n(j)&&Me(Ve)})}A(()=>I(y,r().topicLabel||"")),c(x,N)};$(yt,x=>{r()&&x($t)})}var Et=m(yt,2);{var or=x=>{var N=C_(),L=d(N),q=d(L);zs(q,{size:10}),A(()=>yo(N,`left: ${n(_).x??""}px; top: ${n(_).y??""}px; transform: translate(-50%, -100%)`)),ve("click",N,at),c(x,N)};$(Et,x=>{n(_).show&&x(or)})}c(t,Qe),Sr()}Or(["click","mouseup"]);var z_=h("<div> </div>"),M_=h('<div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20"><!> <div class="text-[11px] text-red-400/90 space-y-0.5"></div></div>'),T_=h("<div> </div>"),I_=h('<div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-500/8 border border-amber-500/20"><!> <div class="text-[11px] text-amber-400/80 space-y-0.5"></div></div>'),A_=h('<button><!> <span class="text-[10px] opacity-80"> </span> <span class="text-[14px] font-bold"> </span></button>'),E_=h('<div class="flex items-start gap-1.5"><span class="w-1 h-1 rounded-full bg-dl-text-dim/40 mt-1.5 flex-shrink-0"></span> <span> </span></div>'),N_=h('<div class="text-[11px] text-dl-text-muted space-y-0.5"></div>'),P_=h("<div><!> <span> </span></div>"),L_=h('<div class="text-[11px] space-y-0.5"></div>'),O_=h("<div><!> <span> </span></div>"),R_=h('<div class="text-[11px] space-y-0.5"></div>'),D_=h('<button class="text-[10px] px-1.5 py-0.5 rounded bg-dl-accent/8 text-dl-accent-light border border-dl-accent/20 hover:bg-dl-accent/15 transition-colors"> </button>'),j_=h('<div class="flex flex-wrap gap-1 pt-1 border-t border-dl-border/10"><span class="text-[10px] text-dl-text-dim mr-1">원문 보기:</span> <!></div>'),F_=h('<div class="px-3 py-2 rounded-lg bg-dl-surface-card border border-dl-border/20 space-y-2 animate-fadeIn"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><span> </span> <span class="text-[12px] font-medium text-dl-text"> </span> <span class="text-[11px] text-dl-text-muted"> </span></div> <button class="p-0.5 text-dl-text-dim hover:text-dl-text"><!></button></div> <!> <!> <!> <!></div>'),V_=h('<div class="text-[10px] text-dl-text-dim px-1"> </div>'),B_=h('<div class="space-y-2"><!> <!> <div class="grid grid-cols-4 sm:grid-cols-7 gap-1.5"></div> <!> <!> <!></div>');function q_(t,e){Cr(e,!0);let r=Pe(e,"data",3,null),a=Pe(e,"loading",3,!1),o=Pe(e,"corpName",3,""),i=Pe(e,"onNavigateTopic",3,null),s=Pe(e,"toc",3,null),l=Z(null);const u={performance:{label:"실적",icon:xs},profitability:{label:"수익성",icon:qc},health:{label:"건전성",icon:xh},cashflow:{label:"현금흐름",icon:wh},governance:{label:"지배구조",icon:Hc},risk:{label:"리스크",icon:Ko},opportunity:{label:"기회",icon:xs}},f={performance:["salesOrder","businessOverview"],profitability:["IS","CIS","ratios"],health:["BS","contingentLiability","corporateBond"],cashflow:["CF","ratios"],governance:["majorShareholder","audit","dividend"],risk:["contingentLiability","riskFactors","corporateBond"],opportunity:["businessOverview","investmentOverview"]};function p(T){return T==="A"?"bg-emerald-500/15 text-emerald-400 border-emerald-500/30":T==="B"?"bg-blue-500/15 text-blue-400 border-blue-500/30":T==="C"?"bg-amber-500/15 text-amber-400 border-amber-500/30":T==="D"?"bg-orange-500/15 text-orange-400 border-orange-500/30":T==="F"?"bg-red-500/15 text-red-400 border-red-500/30":"bg-dl-border/10 text-dl-text-dim border-dl-border/20"}function _(T){return T==="A"?"bg-emerald-500 text-white":T==="B"?"bg-blue-500 text-white":T==="C"?"bg-amber-500 text-white":T==="D"?"bg-orange-500 text-white":T==="F"?"bg-red-500 text-white":"bg-dl-border text-dl-text-dim"}function g(T){return T==="danger"?"text-red-400":T==="warning"?"text-amber-400":"text-dl-text-dim"}function w(T){return T==="strong"?"text-emerald-400":"text-blue-400"}function k(T){v(l,n(l)===T?null:T,!0)}let S=R(()=>{var G;if(!((G=s())!=null&&G.chapters))return null;const T=new Set;for(const K of s().chapters)for(const ie of K.topics)T.add(ie.topic);return T}),b=R(()=>{var T;return(((T=r())==null?void 0:T.anomalies)??[]).filter(G=>G.severity==="danger")}),C=R(()=>{var T;return(((T=r())==null?void 0:T.anomalies)??[]).filter(G=>G.severity==="warning")}),z=R(()=>{var T;return(T=r())!=null&&T.areas?Object.keys(u).filter(G=>r().areas[G]):[]}),P=R(()=>{var G;if(!((G=r())!=null&&G.areas)||n(z).length<3)return null;const T={};for(const K of n(z))T[K]={grade:r().areas[K].grade};return E1(T,o())});var E=be(),ee=ae(E);{var se=T=>{},j=T=>{var G=B_(),K=d(G);{var ie=ce=>{var ne=M_(),D=d(ne);Oa(D,{size:14,class:"text-red-400 mt-0.5 flex-shrink-0"});var H=m(D,2);Ce(H,21,()=>n(b),$e,(te,Y)=>{var xe=z_(),ke=d(xe);A(()=>I(ke,n(Y).text)),c(te,xe)}),c(ce,ne)};$(K,ce=>{n(b).length>0&&ce(ie)})}var U=m(K,2);{var we=ce=>{var ne=I_(),D=d(ne);Ko(D,{size:14,class:"text-amber-400 mt-0.5 flex-shrink-0"});var H=m(D,2);Ce(H,21,()=>n(C),$e,(te,Y)=>{var xe=T_(),ke=d(xe);A(()=>I(ke,n(Y).text)),c(te,xe)}),c(ce,ne)};$(U,ce=>{n(C).length>0&&ce(we)})}var B=m(U,2);Ce(B,21,()=>n(z),$e,(ce,ne)=>{const D=R(()=>u[n(ne)]),H=R(()=>r().areas[n(ne)]),te=R(()=>n(D).icon);var Y=A_(),xe=d(Y);wo(xe,()=>n(te),(nt,lt)=>{lt(nt,{size:13,class:"opacity-70"})});var ke=m(xe,2),re=d(ke),Fe=m(ke,2),ot=d(Fe);A(nt=>{Xe(Y,1,`flex flex-col items-center gap-1 px-2 py-2 rounded-lg border transition-colors cursor-pointer ${nt??""} ${n(l)===n(ne)?"ring-1 ring-dl-accent/40":"hover:brightness-110"}`),I(re,n(D).label),I(ot,n(H).grade)},[()=>p(n(H).grade)]),ve("click",Y,()=>k(n(ne))),c(ce,Y)});var J=m(B,2);{var le=ce=>{var ne=be(),D=ae(ne);gi(D,()=>Ai(()=>import("./ChartRenderer-B5E7I3qo.js"),__vite__mapDeps([0,1])),null,(H,te)=>{var Y=R(()=>{var{default:Fe}=n(te);return{ChartRenderer:Fe}}),xe=R(()=>n(Y).ChartRenderer),ke=be(),re=ae(ke);wo(re,()=>n(xe),(Fe,ot)=>{ot(Fe,{get spec(){return n(P)},class:"max-w-xs mx-auto"})}),c(H,ke)}),c(ce,ne)};$(J,ce=>{n(P)&&ce(le)})}var X=m(J,2);{var O=ce=>{const ne=R(()=>r().areas[n(l)]),D=R(()=>u[n(l)]),H=R(()=>(f[n(l)]||[]).filter(L=>!n(S)||n(S).has(L)));var te=F_(),Y=d(te),xe=d(Y),ke=d(xe),re=d(ke),Fe=m(ke,2),ot=d(Fe),nt=m(Fe,2),lt=d(nt),at=m(xe,2),vt=d(at);Dc(vt,{size:14});var tt=m(Y,2);{var Qe=L=>{var q=N_();Ce(q,21,()=>n(ne).details,$e,(y,V)=>{var Q=E_(),he=m(d(Q),2),fe=d(he);A(()=>I(fe,n(V))),c(y,Q)}),c(L,q)};$(tt,L=>{var q;((q=n(ne).details)==null?void 0:q.length)>0&&L(Qe)})}var yt=m(tt,2);{var $t=L=>{var q=L_();Ce(q,21,()=>n(ne).risks,$e,(y,V)=>{var Q=P_(),he=d(Q);Ko(he,{size:10,class:"mt-0.5 flex-shrink-0"});var fe=m(he,2),me=d(fe);A(Ae=>{Xe(Q,1,`flex items-start gap-1.5 ${Ae??""}`),I(me,n(V).text)},[()=>g(n(V).level)]),c(y,Q)}),c(L,q)};$(yt,L=>{var q;((q=n(ne).risks)==null?void 0:q.length)>0&&L($t)})}var Et=m(yt,2);{var or=L=>{var q=R_();Ce(q,21,()=>n(ne).opportunities,$e,(y,V)=>{var Q=O_(),he=d(Q);xs(he,{size:10,class:"mt-0.5 flex-shrink-0"});var fe=m(he,2),me=d(fe);A(Ae=>{Xe(Q,1,`flex items-start gap-1.5 ${Ae??""}`),I(me,n(V).text)},[()=>w(n(V).level)]),c(y,Q)}),c(L,q)};$(Et,L=>{var q;((q=n(ne).opportunities)==null?void 0:q.length)>0&&L(or)})}var x=m(Et,2);{var N=L=>{var q=j_(),y=m(d(q),2);Ce(y,17,()=>n(H),$e,(V,Q)=>{var he=D_(),fe=d(he);A(()=>I(fe,n(Q))),ve("click",he,()=>i()(n(Q))),c(V,he)}),c(L,q)};$(x,L=>{i()&&n(H).length>0&&L(N)})}A(L=>{Xe(ke,1,`px-1.5 py-0.5 rounded text-[10px] font-bold ${L??""}`),I(re,n(ne).grade),I(ot,n(D).label),I(lt,`— ${n(ne).summary??""}`)},[()=>_(n(ne).grade)]),ve("click",at,()=>{v(l,null)}),c(ce,te)};$(X,ce=>{n(l)&&r().areas[n(l)]&&ce(O)})}var W=m(X,2);{var F=ce=>{var ne=V_(),D=d(ne);A(()=>I(D,r().profile)),c(ce,ne)};$(W,ce=>{r().profile&&ce(F)})}c(T,G)};$(ee,T=>{a()?T(se):r()&&T(j,1)})}c(t,E),Sr()}Or(["click"]);function H_(t,e){var r,a=1;t==null&&(t=0),e==null&&(e=0);function o(){var i,s=r.length,l,u=0,f=0;for(i=0;i<s;++i)l=r[i],u+=l.x,f+=l.y;for(u=(u/s-t)*a,f=(f/s-e)*a,i=0;i<s;++i)l=r[i],l.x-=u,l.y-=f}return o.initialize=function(i){r=i},o.x=function(i){return arguments.length?(t=+i,o):t},o.y=function(i){return arguments.length?(e=+i,o):e},o.strength=function(i){return arguments.length?(a=+i,o):a},o}function U_(t){const e=+this._x.call(null,t),r=+this._y.call(null,t);return Kc(this.cover(e,r),e,r,t)}function Kc(t,e,r,a){if(isNaN(e)||isNaN(r))return t;var o,i=t._root,s={data:a},l=t._x0,u=t._y0,f=t._x1,p=t._y1,_,g,w,k,S,b,C,z;if(!i)return t._root=s,t;for(;i.length;)if((S=e>=(_=(l+f)/2))?l=_:f=_,(b=r>=(g=(u+p)/2))?u=g:p=g,o=i,!(i=i[C=b<<1|S]))return o[C]=s,t;if(w=+t._x.call(null,i.data),k=+t._y.call(null,i.data),e===w&&r===k)return s.next=i,o?o[C]=s:t._root=s,t;do o=o?o[C]=new Array(4):t._root=new Array(4),(S=e>=(_=(l+f)/2))?l=_:f=_,(b=r>=(g=(u+p)/2))?u=g:p=g;while((C=b<<1|S)===(z=(k>=g)<<1|w>=_));return o[z]=i,o[C]=s,t}function W_(t){var e,r,a=t.length,o,i,s=new Array(a),l=new Array(a),u=1/0,f=1/0,p=-1/0,_=-1/0;for(r=0;r<a;++r)isNaN(o=+this._x.call(null,e=t[r]))||isNaN(i=+this._y.call(null,e))||(s[r]=o,l[r]=i,o<u&&(u=o),o>p&&(p=o),i<f&&(f=i),i>_&&(_=i));if(u>p||f>_)return this;for(this.cover(u,f).cover(p,_),r=0;r<a;++r)Kc(this,s[r],l[r],t[r]);return this}function K_(t,e){if(isNaN(t=+t)||isNaN(e=+e))return this;var r=this._x0,a=this._y0,o=this._x1,i=this._y1;if(isNaN(r))o=(r=Math.floor(t))+1,i=(a=Math.floor(e))+1;else{for(var s=o-r||1,l=this._root,u,f;r>t||t>=o||a>e||e>=i;)switch(f=(e<a)<<1|t<r,u=new Array(4),u[f]=l,l=u,s*=2,f){case 0:o=r+s,i=a+s;break;case 1:r=o-s,i=a+s;break;case 2:o=r+s,a=i-s;break;case 3:r=o-s,a=i-s;break}this._root&&this._root.length&&(this._root=l)}return this._x0=r,this._y0=a,this._x1=o,this._y1=i,this}function G_(){var t=[];return this.visit(function(e){if(!e.length)do t.push(e.data);while(e=e.next)}),t}function J_(t){return arguments.length?this.cover(+t[0][0],+t[0][1]).cover(+t[1][0],+t[1][1]):isNaN(this._x0)?void 0:[[this._x0,this._y0],[this._x1,this._y1]]}function Xr(t,e,r,a,o){this.node=t,this.x0=e,this.y0=r,this.x1=a,this.y1=o}function Y_(t,e,r){var a,o=this._x0,i=this._y0,s,l,u,f,p=this._x1,_=this._y1,g=[],w=this._root,k,S;for(w&&g.push(new Xr(w,o,i,p,_)),r==null?r=1/0:(o=t-r,i=e-r,p=t+r,_=e+r,r*=r);k=g.pop();)if(!(!(w=k.node)||(s=k.x0)>p||(l=k.y0)>_||(u=k.x1)<o||(f=k.y1)<i))if(w.length){var b=(s+u)/2,C=(l+f)/2;g.push(new Xr(w[3],b,C,u,f),new Xr(w[2],s,C,b,f),new Xr(w[1],b,l,u,C),new Xr(w[0],s,l,b,C)),(S=(e>=C)<<1|t>=b)&&(k=g[g.length-1],g[g.length-1]=g[g.length-1-S],g[g.length-1-S]=k)}else{var z=t-+this._x.call(null,w.data),P=e-+this._y.call(null,w.data),E=z*z+P*P;if(E<r){var ee=Math.sqrt(r=E);o=t-ee,i=e-ee,p=t+ee,_=e+ee,a=w.data}}return a}function X_(t){if(isNaN(p=+this._x.call(null,t))||isNaN(_=+this._y.call(null,t)))return this;var e,r=this._root,a,o,i,s=this._x0,l=this._y0,u=this._x1,f=this._y1,p,_,g,w,k,S,b,C;if(!r)return this;if(r.length)for(;;){if((k=p>=(g=(s+u)/2))?s=g:u=g,(S=_>=(w=(l+f)/2))?l=w:f=w,e=r,!(r=r[b=S<<1|k]))return this;if(!r.length)break;(e[b+1&3]||e[b+2&3]||e[b+3&3])&&(a=e,C=b)}for(;r.data!==t;)if(o=r,!(r=r.next))return this;return(i=r.next)&&delete r.next,o?(i?o.next=i:delete o.next,this):e?(i?e[b]=i:delete e[b],(r=e[0]||e[1]||e[2]||e[3])&&r===(e[3]||e[2]||e[1]||e[0])&&!r.length&&(a?a[C]=r:this._root=r),this):(this._root=i,this)}function Q_(t){for(var e=0,r=t.length;e<r;++e)this.remove(t[e]);return this}function Z_(){return this._root}function e0(){var t=0;return this.visit(function(e){if(!e.length)do++t;while(e=e.next)}),t}function t0(t){var e=[],r,a=this._root,o,i,s,l,u;for(a&&e.push(new Xr(a,this._x0,this._y0,this._x1,this._y1));r=e.pop();)if(!t(a=r.node,i=r.x0,s=r.y0,l=r.x1,u=r.y1)&&a.length){var f=(i+l)/2,p=(s+u)/2;(o=a[3])&&e.push(new Xr(o,f,p,l,u)),(o=a[2])&&e.push(new Xr(o,i,p,f,u)),(o=a[1])&&e.push(new Xr(o,f,s,l,p)),(o=a[0])&&e.push(new Xr(o,i,s,f,p))}return this}function r0(t){var e=[],r=[],a;for(this._root&&e.push(new Xr(this._root,this._x0,this._y0,this._x1,this._y1));a=e.pop();){var o=a.node;if(o.length){var i,s=a.x0,l=a.y0,u=a.x1,f=a.y1,p=(s+u)/2,_=(l+f)/2;(i=o[0])&&e.push(new Xr(i,s,l,p,_)),(i=o[1])&&e.push(new Xr(i,p,l,u,_)),(i=o[2])&&e.push(new Xr(i,s,_,p,f)),(i=o[3])&&e.push(new Xr(i,p,_,u,f))}r.push(a)}for(;a=r.pop();)t(a.node,a.x0,a.y0,a.x1,a.y1);return this}function n0(t){return t[0]}function a0(t){return arguments.length?(this._x=t,this):this._x}function o0(t){return t[1]}function s0(t){return arguments.length?(this._y=t,this):this._y}function tl(t,e,r){var a=new rl(e??n0,r??o0,NaN,NaN,NaN,NaN);return t==null?a:a.addAll(t)}function rl(t,e,r,a,o,i){this._x=t,this._y=e,this._x0=r,this._y0=a,this._x1=o,this._y1=i,this._root=void 0}function ed(t){for(var e={data:t.data},r=e;t=t.next;)r=r.next={data:t.data};return e}var Zr=tl.prototype=rl.prototype;Zr.copy=function(){var t=new rl(this._x,this._y,this._x0,this._y0,this._x1,this._y1),e=this._root,r,a;if(!e)return t;if(!e.length)return t._root=ed(e),t;for(r=[{source:e,target:t._root=new Array(4)}];e=r.pop();)for(var o=0;o<4;++o)(a=e.source[o])&&(a.length?r.push({source:a,target:e.target[o]=new Array(4)}):e.target[o]=ed(a));return t};Zr.add=U_;Zr.addAll=W_;Zr.cover=K_;Zr.data=G_;Zr.extent=J_;Zr.find=Y_;Zr.remove=X_;Zr.removeAll=Q_;Zr.root=Z_;Zr.size=e0;Zr.visit=t0;Zr.visitAfter=r0;Zr.x=a0;Zr.y=s0;function Ka(t){return function(){return t}}function wa(t){return(t()-.5)*1e-6}function i0(t){return t.x+t.vx}function l0(t){return t.y+t.vy}function d0(t){var e,r,a,o=1,i=1;typeof t!="function"&&(t=Ka(t==null?1:+t));function s(){for(var f,p=e.length,_,g,w,k,S,b,C=0;C<i;++C)for(_=tl(e,i0,l0).visitAfter(l),f=0;f<p;++f)g=e[f],S=r[g.index],b=S*S,w=g.x+g.vx,k=g.y+g.vy,_.visit(z);function z(P,E,ee,se,j){var T=P.data,G=P.r,K=S+G;if(T){if(T.index>g.index){var ie=w-T.x-T.vx,U=k-T.y-T.vy,we=ie*ie+U*U;we<K*K&&(ie===0&&(ie=wa(a),we+=ie*ie),U===0&&(U=wa(a),we+=U*U),we=(K-(we=Math.sqrt(we)))/we*o,g.vx+=(ie*=we)*(K=(G*=G)/(b+G)),g.vy+=(U*=we)*K,T.vx-=ie*(K=1-K),T.vy-=U*K)}return}return E>w+K||se<w-K||ee>k+K||j<k-K}}function l(f){if(f.data)return f.r=r[f.data.index];for(var p=f.r=0;p<4;++p)f[p]&&f[p].r>f.r&&(f.r=f[p].r)}function u(){if(e){var f,p=e.length,_;for(r=new Array(p),f=0;f<p;++f)_=e[f],r[_.index]=+t(_,f,e)}}return s.initialize=function(f,p){e=f,a=p,u()},s.iterations=function(f){return arguments.length?(i=+f,s):i},s.strength=function(f){return arguments.length?(o=+f,s):o},s.radius=function(f){return arguments.length?(t=typeof f=="function"?f:Ka(+f),u(),s):t},s}function c0(t){return t.index}function td(t,e){var r=t.get(e);if(!r)throw new Error("node not found: "+e);return r}function u0(t){var e=c0,r=_,a,o=Ka(30),i,s,l,u,f,p=1;t==null&&(t=[]);function _(b){return 1/Math.min(l[b.source.index],l[b.target.index])}function g(b){for(var C=0,z=t.length;C<p;++C)for(var P=0,E,ee,se,j,T,G,K;P<z;++P)E=t[P],ee=E.source,se=E.target,j=se.x+se.vx-ee.x-ee.vx||wa(f),T=se.y+se.vy-ee.y-ee.vy||wa(f),G=Math.sqrt(j*j+T*T),G=(G-i[P])/G*b*a[P],j*=G,T*=G,se.vx-=j*(K=u[P]),se.vy-=T*K,ee.vx+=j*(K=1-K),ee.vy+=T*K}function w(){if(s){var b,C=s.length,z=t.length,P=new Map(s.map((ee,se)=>[e(ee,se,s),ee])),E;for(b=0,l=new Array(C);b<z;++b)E=t[b],E.index=b,typeof E.source!="object"&&(E.source=td(P,E.source)),typeof E.target!="object"&&(E.target=td(P,E.target)),l[E.source.index]=(l[E.source.index]||0)+1,l[E.target.index]=(l[E.target.index]||0)+1;for(b=0,u=new Array(z);b<z;++b)E=t[b],u[b]=l[E.source.index]/(l[E.source.index]+l[E.target.index]);a=new Array(z),k(),i=new Array(z),S()}}function k(){if(s)for(var b=0,C=t.length;b<C;++b)a[b]=+r(t[b],b,t)}function S(){if(s)for(var b=0,C=t.length;b<C;++b)i[b]=+o(t[b],b,t)}return g.initialize=function(b,C){s=b,f=C,w()},g.links=function(b){return arguments.length?(t=b,w(),g):t},g.id=function(b){return arguments.length?(e=b,g):e},g.iterations=function(b){return arguments.length?(p=+b,g):p},g.strength=function(b){return arguments.length?(r=typeof b=="function"?b:Ka(+b),k(),g):r},g.distance=function(b){return arguments.length?(o=typeof b=="function"?b:Ka(+b),S(),g):o},g}var f0={value:()=>{}};function Gc(){for(var t=0,e=arguments.length,r={},a;t<e;++t){if(!(a=arguments[t]+"")||a in r||/[\s.]/.test(a))throw new Error("illegal type: "+a);r[a]=[]}return new gs(r)}function gs(t){this._=t}function v0(t,e){return t.trim().split(/^|\s+/).map(function(r){var a="",o=r.indexOf(".");if(o>=0&&(a=r.slice(o+1),r=r.slice(0,o)),r&&!e.hasOwnProperty(r))throw new Error("unknown type: "+r);return{type:r,name:a}})}gs.prototype=Gc.prototype={constructor:gs,on:function(t,e){var r=this._,a=v0(t+"",r),o,i=-1,s=a.length;if(arguments.length<2){for(;++i<s;)if((o=(t=a[i]).type)&&(o=p0(r[o],t.name)))return o;return}if(e!=null&&typeof e!="function")throw new Error("invalid callback: "+e);for(;++i<s;)if(o=(t=a[i]).type)r[o]=rd(r[o],t.name,e);else if(e==null)for(o in r)r[o]=rd(r[o],t.name,null);return this},copy:function(){var t={},e=this._;for(var r in e)t[r]=e[r].slice();return new gs(t)},call:function(t,e){if((o=arguments.length-2)>0)for(var r=new Array(o),a=0,o,i;a<o;++a)r[a]=arguments[a+2];if(!this._.hasOwnProperty(t))throw new Error("unknown type: "+t);for(i=this._[t],a=0,o=i.length;a<o;++a)i[a].value.apply(e,r)},apply:function(t,e,r){if(!this._.hasOwnProperty(t))throw new Error("unknown type: "+t);for(var a=this._[t],o=0,i=a.length;o<i;++o)a[o].value.apply(e,r)}};function p0(t,e){for(var r=0,a=t.length,o;r<a;++r)if((o=t[r]).name===e)return o.value}function rd(t,e,r){for(var a=0,o=t.length;a<o;++a)if(t[a].name===e){t[a]=f0,t=t.slice(0,a).concat(t.slice(a+1));break}return r!=null&&t.push({name:e,value:r}),t}var ko=0,Fo=0,Do=0,Jc=1e3,Ms,Vo,Ts=0,Xa=0,Ds=0,Yo=typeof performance=="object"&&performance.now?performance:Date,Yc=typeof window=="object"&&window.requestAnimationFrame?window.requestAnimationFrame.bind(window):function(t){setTimeout(t,17)};function Xc(){return Xa||(Yc(h0),Xa=Yo.now()+Ds)}function h0(){Xa=0}function Ni(){this._call=this._time=this._next=null}Ni.prototype=Qc.prototype={constructor:Ni,restart:function(t,e,r){if(typeof t!="function")throw new TypeError("callback is not a function");r=(r==null?Xc():+r)+(e==null?0:+e),!this._next&&Vo!==this&&(Vo?Vo._next=this:Ms=this,Vo=this),this._call=t,this._time=r,Pi()},stop:function(){this._call&&(this._call=null,this._time=1/0,Pi())}};function Qc(t,e,r){var a=new Ni;return a.restart(t,e,r),a}function m0(){Xc(),++ko;for(var t=Ms,e;t;)(e=Xa-t._time)>=0&&t._call.call(void 0,e),t=t._next;--ko}function nd(){Xa=(Ts=Yo.now())+Ds,ko=Fo=0;try{m0()}finally{ko=0,g0(),Xa=0}}function x0(){var t=Yo.now(),e=t-Ts;e>Jc&&(Ds-=e,Ts=t)}function g0(){for(var t,e=Ms,r,a=1/0;e;)e._call?(a>e._time&&(a=e._time),t=e,e=e._next):(r=e._next,e._next=null,e=t?t._next=r:Ms=r);Vo=t,Pi(a)}function Pi(t){if(!ko){Fo&&(Fo=clearTimeout(Fo));var e=t-Xa;e>24?(t<1/0&&(Fo=setTimeout(nd,t-Yo.now()-Ds)),Do&&(Do=clearInterval(Do))):(Do||(Ts=Yo.now(),Do=setInterval(x0,Jc)),ko=1,Yc(nd))}}const _0=1664525,b0=1013904223,ad=4294967296;function w0(){let t=1;return()=>(t=(_0*t+b0)%ad)/ad}function y0(t){return t.x}function k0(t){return t.y}var C0=10,S0=Math.PI*(3-Math.sqrt(5));function $0(t){var e,r=1,a=.001,o=1-Math.pow(a,1/300),i=0,s=.6,l=new Map,u=Qc(_),f=Gc("tick","end"),p=w0();t==null&&(t=[]);function _(){g(),f.call("tick",e),r<a&&(u.stop(),f.call("end",e))}function g(S){var b,C=t.length,z;S===void 0&&(S=1);for(var P=0;P<S;++P)for(r+=(i-r)*o,l.forEach(function(E){E(r)}),b=0;b<C;++b)z=t[b],z.fx==null?z.x+=z.vx*=s:(z.x=z.fx,z.vx=0),z.fy==null?z.y+=z.vy*=s:(z.y=z.fy,z.vy=0);return e}function w(){for(var S=0,b=t.length,C;S<b;++S){if(C=t[S],C.index=S,C.fx!=null&&(C.x=C.fx),C.fy!=null&&(C.y=C.fy),isNaN(C.x)||isNaN(C.y)){var z=C0*Math.sqrt(.5+S),P=S*S0;C.x=z*Math.cos(P),C.y=z*Math.sin(P)}(isNaN(C.vx)||isNaN(C.vy))&&(C.vx=C.vy=0)}}function k(S){return S.initialize&&S.initialize(t,p),S}return w(),e={tick:g,restart:function(){return u.restart(_),e},stop:function(){return u.stop(),e},nodes:function(S){return arguments.length?(t=S,w(),l.forEach(k),e):t},alpha:function(S){return arguments.length?(r=+S,e):r},alphaMin:function(S){return arguments.length?(a=+S,e):a},alphaDecay:function(S){return arguments.length?(o=+S,e):+o},alphaTarget:function(S){return arguments.length?(i=+S,e):i},velocityDecay:function(S){return arguments.length?(s=1-S,e):1-s},randomSource:function(S){return arguments.length?(p=S,l.forEach(k),e):p},force:function(S,b){return arguments.length>1?(b==null?l.delete(S):l.set(S,k(b)),e):l.get(S)},find:function(S,b,C){var z=0,P=t.length,E,ee,se,j,T;for(C==null?C=1/0:C*=C,z=0;z<P;++z)j=t[z],E=S-j.x,ee=b-j.y,se=E*E+ee*ee,se<C&&(T=j,C=se);return T},on:function(S,b){return arguments.length>1?(f.on(S,b),e):f.on(S)}}}function z0(){var t,e,r,a,o=Ka(-30),i,s=1,l=1/0,u=.81;function f(w){var k,S=t.length,b=tl(t,y0,k0).visitAfter(_);for(a=w,k=0;k<S;++k)e=t[k],b.visit(g)}function p(){if(t){var w,k=t.length,S;for(i=new Array(k),w=0;w<k;++w)S=t[w],i[S.index]=+o(S,w,t)}}function _(w){var k=0,S,b,C=0,z,P,E;if(w.length){for(z=P=E=0;E<4;++E)(S=w[E])&&(b=Math.abs(S.value))&&(k+=S.value,C+=b,z+=b*S.x,P+=b*S.y);w.x=z/C,w.y=P/C}else{S=w,S.x=S.data.x,S.y=S.data.y;do k+=i[S.data.index];while(S=S.next)}w.value=k}function g(w,k,S,b){if(!w.value)return!0;var C=w.x-e.x,z=w.y-e.y,P=b-k,E=C*C+z*z;if(P*P/u<E)return E<l&&(C===0&&(C=wa(r),E+=C*C),z===0&&(z=wa(r),E+=z*z),E<s&&(E=Math.sqrt(s*E)),e.vx+=C*w.value*a/E,e.vy+=z*w.value*a/E),!0;if(w.length||E>=l)return;(w.data!==e||w.next)&&(C===0&&(C=wa(r),E+=C*C),z===0&&(z=wa(r),E+=z*z),E<s&&(E=Math.sqrt(s*E)));do w.data!==e&&(P=i[w.data.index]*a/E,e.vx+=C*P,e.vy+=z*P);while(w=w.next)}return f.initialize=function(w,k){t=w,r=k,p()},f.strength=function(w){return arguments.length?(o=typeof w=="function"?w:Ka(+w),p(),f):o},f.distanceMin=function(w){return arguments.length?(s=w*w,f):Math.sqrt(s)},f.distanceMax=function(w){return arguments.length?(l=w*w,f):Math.sqrt(l)},f.theta=function(w){return arguments.length?(u=w*w,f):Math.sqrt(u)},f}var M0=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-medium border border-dl-border/20 text-dl-text-dim bg-dl-surface-card"> </span>'),T0=h('<span class="flex items-center gap-1 text-amber-400/70"><!>순환출자 감지</span>'),I0=ns('<line class="cursor-pointer hover:stroke-[#fff3]"></line>'),A0=ns('<circle fill="none" stroke="#818cf860" stroke-width="2"></circle>'),E0=ns('<text text-anchor="middle" class="fill-dl-text-dim/50 text-[8px] pointer-events-none select-none"> </text>'),N0=ns('<g class="cursor-pointer"><!><circle></circle><!></g>'),P0=h('<div class="absolute z-10 px-2 py-1 rounded-md bg-dl-bg-card/95 border border-dl-border/30 text-[10px] text-dl-text-muted whitespace-pre-line pointer-events-none shadow-lg"> </div>'),L0=h('<div class="flex flex-wrap gap-3 px-1 text-[9px] text-dl-text-dim/60"><span class="flex items-center gap-1"><span class="w-2 h-0.5 bg-blue-400/40 inline-block"></span>출자</span> <span class="flex items-center gap-1"><span class="w-2 h-0.5 bg-amber-400/30 inline-block" style="border-bottom: 1px dashed"></span>지분</span> <span class="flex items-center gap-1"><span class="w-2 h-0.5 bg-slate-400/30 inline-block" style="border-bottom: 1px dotted"></span>인물</span> <!></div> <div class="relative rounded-lg border border-dl-border/15 bg-dl-bg-darker/50 overflow-hidden"><svg class="w-full h-full"><defs><marker id="arrow-inv" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="8" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,3 L0,6" fill="#60a5fa40"></path></marker><marker id="arrow-sh" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="8" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,3 L0,6" fill="#f59e0b30"></path></marker></defs><!><!></svg> <!></div>',1),O0=h('<div class="space-y-2"><button class="flex items-center gap-2 w-full px-1 py-1 text-left rounded-md hover:bg-white/3 transition-colors"><!> <span class="text-[11px] font-semibold text-dl-text-dim uppercase tracking-wider flex-1">관계 네트워크</span> <!> <span class="text-[10px] text-dl-text-dim/50"> <!> </span> <!></button> <!></div>');function R0(t,e){Cr(e,!0);let r=Pe(e,"data",3,null),a=Pe(e,"loading",3,!1),o=Pe(e,"centerCode",3,""),i=Pe(e,"onNavigate",3,null),s=Z(!1),l=Z(null),u=Z(640),f=400,p=Z(Ut({show:!1,x:0,y:0,text:""})),_=Z(Ut([])),g=Z(Ut([])),w=null;const k=["#60a5fa","#f59e0b","#10b981","#f472b6","#a78bfa","#14b8a6","#fb923c","#e879f9","#38bdf8","#fbbf24","#4ade80","#f87171","#818cf8","#2dd4bf","#fb7185"];let S=R(()=>{var F;if(!((F=r())!=null&&F.nodes))return{};const O=[...new Set(r().nodes.map(ce=>ce.group).filter(Boolean))],W={};return O.forEach((ce,ne)=>{W[ce]=k[ne%k.length]}),W});function b(O){return O.id===o()?"#818cf8":O.type==="person"?"#94a3b8":n(S)[O.group]||"#475569"}function C(O){return O.id===o()?18:O.type==="person"?7:Math.max(6,Math.min(14,6+(O.degree||0)*.8))}function z(O){return O.type==="investment"?"#60a5fa40":O.type==="shareholder"?"#f59e0b30":"#94a3b830"}function P(O){return O.type==="person_shareholder"?"3,3":O.type==="shareholder"?"5,3":"none"}function E(O,W=6){return O?O.length>W?O.slice(0,W)+"…":O:""}xr(()=>{if(!n(l))return;const O=new ResizeObserver(W=>{for(const F of W)v(u,F.contentRect.width||640,!0)});return O.observe(n(l).parentElement),()=>O.disconnect()}),xr(()=>{var ne,D;if(!((D=(ne=r())==null?void 0:ne.nodes)!=null&&D.length)||!n(s)){w&&(w.stop(),w=null),v(_,[],!0),v(g,[],!0);return}const O=r().nodes.map(H=>({...H,x:H.id===o()?n(u)/2:void 0,y:H.id===o()?f/2:void 0,fx:H.id===o()?n(u)/2:void 0,fy:H.id===o()?f/2:void 0})),W=new Map(O.map(H=>[H.id,H])),F=r().edges.filter(H=>W.has(H.source)&&W.has(H.target)).map(H=>({...H,source:H.source,target:H.target}));w&&w.stop();const ce=$0(O).force("link",u0(F).id(H=>H.id).distance(80).strength(.4)).force("charge",z0().strength(-200)).force("center",H_(n(u)/2,f/2)).force("collide",d0().radius(H=>C(H)+4)).alphaDecay(.03);return ce.on("tick",()=>{for(const H of O){const te=C(H);H.x=Math.max(te,Math.min(n(u)-te,H.x)),H.y=Math.max(te,Math.min(f-te,H.y))}v(_,[...O],!0),v(g,[...F],!0)}),w=ce,()=>{ce.stop()}});function ee(O,W){const F=n(l).getBoundingClientRect(),ce=[W.label];W.group&&ce.push(`그룹: ${W.group}`),W.industry&&ce.push(W.industry),W.type==="company"&&ce.push(`연결: ${W.degree||0}개`),v(p,{show:!0,x:O.clientX-F.left,y:O.clientY-F.top-10,text:ce.join(`
`)},!0)}function se(O,W){const F=n(l).getBoundingClientRect(),ce=[],ne=typeof W.source=="object"?W.source.label:W.source,D=typeof W.target=="object"?W.target.label:W.target;ce.push(`${ne} → ${D}`),W.type==="investment"?ce.push(`출자 (${W.purpose||""})`):W.type==="shareholder"?ce.push("지분 보유"):ce.push("인물 지분"),W.ownershipPct!=null&&ce.push(`지분율: ${W.ownershipPct.toFixed(1)}%`),v(p,{show:!0,x:O.clientX-F.left,y:O.clientY-F.top-10,text:ce.join(`
`)},!0)}function j(){v(p,{show:!1,x:0,y:0,text:""},!0)}function T(O){O.type==="company"&&O.id!==o()&&i()&&i()(O.id)}let G=R(()=>{var O,W,F;return((F=(W=(O=r())==null?void 0:O.nodes)==null?void 0:W.find(ce=>ce.id===o()))==null?void 0:F.group)||""}),K=R(()=>{var O;return(((O=r())==null?void 0:O.nodes)||[]).filter(W=>W.type==="company").length}),ie=R(()=>{var O;return(((O=r())==null?void 0:O.nodes)||[]).filter(W=>W.type==="person").length}),U=R(()=>{var O;return(((O=r())==null?void 0:O.edges)||[]).length}),we=R(()=>{var O,W;return(((W=(O=r())==null?void 0:O.meta)==null?void 0:W.cycleCount)||0)>0});var B=be(),J=ae(B);{var le=O=>{},X=O=>{var W=O0(),F=d(W),ce=d(F);Hc(ce,{size:13,class:"text-dl-text-dim/60"});var ne=m(ce,4);{var D=at=>{var vt=M0(),tt=d(vt);A(()=>I(tt,n(G))),c(at,vt)};$(ne,at=>{n(G)&&at(D)})}var H=m(ne,2),te=d(H),Y=m(te);{var xe=at=>{var vt=Wn();A(()=>I(vt,`· ${n(ie)??""}인`)),c(at,vt)};$(Y,at=>{n(ie)>0&&at(xe)})}var ke=m(Y),re=m(H,2);{var Fe=at=>{Dc(at,{size:12,class:"text-dl-text-dim/40"})},ot=at=>{el(at,{size:12,class:"text-dl-text-dim/40"})};$(re,at=>{n(s)?at(Fe):at(ot,-1)})}var nt=m(F,2);{var lt=at=>{var vt=L0(),tt=ae(vt),Qe=m(d(tt),6);{var yt=q=>{var y=T0(),V=d(y);Ko(V,{size:9}),c(q,y)};$(Qe,q=>{n(we)&&q(yt)})}var $t=m(tt,2);yo($t,"height: 400px;");var Et=d($t),or=m(d(Et));Ce(or,17,()=>n(g),$e,(q,y)=>{const V=R(()=>typeof n(y).source=="object"?n(y).source.x:0),Q=R(()=>typeof n(y).source=="object"?n(y).source.y:0),he=R(()=>typeof n(y).target=="object"?n(y).target.x:0),fe=R(()=>typeof n(y).target=="object"?n(y).target.y:0);var me=I0();A((Ae,qe)=>{ar(me,"x1",n(V)),ar(me,"y1",n(Q)),ar(me,"x2",n(he)),ar(me,"y2",n(fe)),ar(me,"stroke",Ae),ar(me,"stroke-width",n(y).ownershipPct>20?2:1),ar(me,"stroke-dasharray",qe),ar(me,"marker-end",n(y).type==="investment"?"url(#arrow-inv)":n(y).type==="shareholder"?"url(#arrow-sh)":"")},[()=>z(n(y)),()=>P(n(y))]),bn("mouseenter",me,Ae=>se(Ae,n(y))),bn("mouseleave",me,j),c(q,me)});var x=m(or);Ce(x,17,()=>n(_),$e,(q,y)=>{const V=R(()=>C(n(y))),Q=R(()=>b(n(y))),he=R(()=>n(y).id===o());var fe=N0(),me=d(fe);{var Ae=Re=>{var De=A0();A(()=>ar(De,"r",n(V)+3)),c(Re,De)};$(me,Re=>{n(he)&&Re(Ae)})}var qe=m(me),Ie=m(qe);{var je=Re=>{var De=E0(),pt=d(De);A(Ze=>{ar(De,"y",n(V)+12),I(pt,Ze)},[()=>E(n(y).label)]),c(Re,De)};$(Ie,Re=>{n(V)>=8&&Re(je)})}A(()=>{ar(fe,"transform",`translate(${n(y).x??""},${n(y).y??""})`),ar(qe,"r",n(V)),ar(qe,"fill",n(Q)),ar(qe,"stroke",n(he)?"#c4b5fd":"#ffffff10"),ar(qe,"stroke-width",n(he)?2:.5),ar(qe,"opacity",n(y).type==="person"?.7:.85)}),bn("mouseenter",fe,Re=>ee(Re,n(y))),bn("mouseleave",fe,j),ve("click",fe,()=>T(n(y))),c(q,fe)}),Qn(Et,q=>v(l,q),()=>n(l));var N=m(Et,2);{var L=q=>{var y=P0(),V=d(y);A(()=>{yo(y,`left: ${n(p).x??""}px; top: ${n(p).y??""}px; transform: translate(-50%, -100%)`),I(V,n(p).text)}),c(q,y)};$(N,q=>{n(p).show&&q(L)})}A(()=>ar(Et,"viewBox",`0 0 ${n(u)??""} 400`)),c(at,vt)};$(nt,at=>{n(s)&&at(lt)})}A(()=>{I(te,`${n(K)??""}사`),I(ke,` · ${n(U)??""}연결`)}),ve("click",F,()=>{v(s,!n(s))}),c(O,W)};$(J,O=>{var W,F,ce;a()?O(le):((W=r())==null?void 0:W.available)!==!1&&((ce=(F=r())==null?void 0:F.nodes)==null?void 0:ce.length)>0&&O(X,1)})}c(t,B),Sr()}Or(["click"]);var D0=h('<div class="flex items-center justify-between text-[12px]"><span class="text-dl-text-muted"> </span> <kbd class="px-1.5 py-0.5 rounded bg-dl-bg-darker border border-dl-border/30 text-[11px] font-mono text-dl-text-dim min-w-[32px] text-center"> </kbd></div>'),j0=h('<div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"><div class="bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl w-80 max-w-[90vw] overflow-hidden"><div class="flex items-center justify-between px-4 py-3 border-b border-dl-border/20"><div class="flex items-center gap-2 text-dl-text"><!> <span class="text-[13px] font-semibold">단축키</span></div> <button class="p-1 rounded text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="px-4 py-3 space-y-1.5"></div></div></div>');function F0(t,e){let r=Pe(e,"show",3,!1),a=Pe(e,"onClose",3,null);const o=[{key:"?",desc:"단축키 도움말"},{key:"1",desc:"Chat 탭"},{key:"2",desc:"Viewer 탭"},{key:"Ctrl+K",desc:"종목 검색"},{key:"Ctrl+F",desc:"뷰어 내 검색"},{key:"J / ↓",desc:"다음 topic"},{key:"K / ↑",desc:"이전 topic"},{key:"S",desc:"현재 topic AI 요약"},{key:"B",desc:"북마크 토글"},{key:"Esc",desc:"모달/검색 닫기"}];var i=be(),s=ae(i);{var l=u=>{var f=j0(),p=d(f),_=d(p),g=d(_),w=d(g);uh(w,{size:16});var k=m(g,2),S=d(k);za(S,{size:14});var b=m(_,2);Ce(b,21,()=>o,$e,(C,z)=>{var P=D0(),E=d(P),ee=d(E),se=m(E,2),j=d(se);A(()=>{I(ee,n(z).desc),I(j,n(z).key)}),c(C,P)}),ve("click",f,function(...C){var z;(z=a())==null||z.apply(this,C)}),ve("click",p,C=>C.stopPropagation()),ve("click",k,function(...C){var z;(z=a())==null||z.apply(this,C)}),c(u,f)};$(s,u=>{r()&&u(l)})}c(t,i)}Or(["click"]);var V0=h('<div class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"></div>'),B0=h('<button class="p-1 rounded-md text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"><!></button>'),q0=h('<div class="flex items-center justify-between"><div class="min-w-0"><div class="text-[12px] font-semibold text-dl-text truncate"> </div> <div class="text-[10px] font-mono text-dl-text-dim"> </div></div> <div class="flex items-center gap-0.5 flex-shrink-0"><!></div></div>'),H0=h('<div class="text-[12px] text-dl-text-dim">종목 미선택</div>'),U0=h('<button class="w-full text-left px-2 py-1.5 rounded-md text-[11px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-1.5"><!> <span class="truncate"> </span> <span class="text-[9px] font-mono text-dl-text-dim/40 ml-auto"> </span></button>'),W0=h('<div class="px-3 py-3 flex-1 overflow-y-auto"><div class="text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold mb-2">최근 종목</div> <!></div>'),K0=h('<div class="sticky top-0 z-20 px-6 py-2 bg-dl-bg-dark/95 backdrop-blur-sm border-b border-dl-border/10"><div class="max-w-2xl mx-auto"><button class="flex items-center gap-2 w-full px-3 py-1.5 rounded-lg border border-dl-border/20 bg-dl-bg-darker/60 text-[12px] text-dl-text-dim hover:border-dl-border/40 hover:bg-dl-bg-darker transition-colors"><!> <span class="flex-1 text-left">공시 섹션 검색... <kbd class="ml-2 px-1 py-0.5 rounded bg-dl-border/15 text-[10px] font-mono">/</kbd></span></button></div></div>'),G0=h('<button class="p-1 text-dl-text-dim hover:text-dl-text"><!></button>'),J0=h('<div class="text-[10px] text-dl-text-dim/60 mt-0.5"> </div>'),Y0=h('<div class="text-[11px] text-dl-text-dim truncate mt-0.5"> </div>'),X0=h('<span class="text-[10px] text-dl-accent font-mono flex-shrink-0"> </span>'),Q0=h('<button class="w-full text-left px-4 py-2 text-[13px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-start gap-2 border-b border-dl-border/5"><div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/50 font-mono"> </span></div> <!> <!></div> <!></button>'),Z0=h('<div class="flex items-center justify-center py-3"><!></div>'),eb=h("<!> <!>",1),tb=h('<div class="flex items-center justify-center py-6 gap-2"><!> <span class="text-[12px] text-dl-text-dim">검색 중...</span></div>'),rb=h('<div class="text-center py-6 text-[12px] text-dl-text-dim">결과 없음</div>'),nb=h('<button class="w-full text-left px-4 py-2 text-[13px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-2"><!> <span> </span> <span class="text-[10px] text-dl-text-dim/40 font-mono ml-auto"> </span></button>'),ab=h('<div class="px-4 py-2 text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold">최근 본 섹션</div> <!>',1),ob=h('<div class="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/50 backdrop-blur-sm"><div class="w-full max-w-xl bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl overflow-hidden"><div class="flex items-center gap-2 px-4 py-3 border-b border-dl-border/20"><!> <input placeholder="섹션, topic, 키워드 검색..." class="flex-1 bg-transparent text-[14px] text-dl-text outline-none placeholder:text-dl-text-dim"/> <!> <kbd class="px-1.5 py-0.5 rounded bg-dl-border/15 text-[10px] font-mono text-dl-text-dim">Esc</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div></div></div>'),sb=h('<span class="text-[11px] text-dl-text-muted truncate"> </span>'),ib=h('<div class="sticky top-0 z-30 flex items-center gap-2 px-3 py-1.5 bg-dl-bg-dark/95 border-b border-dl-border/20 backdrop-blur-sm"><button class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"><!> <span>목차</span></button> <button class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"><!> <span>검색</span></button> <!></div>'),lb=h('<span class="text-[9px] px-1 py-0.5 rounded bg-dl-border/10 text-dl-text-dim/60"> </span>'),db=h('<button class="w-full text-left px-3 py-2 text-[13px] hover:bg-white/5 transition-colors flex items-center gap-2 border-b border-dl-border/5 last:border-b-0"><!> <span class="text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim ml-auto flex-shrink-0"> </span> <!></button>'),cb=h('<div class="absolute top-full mt-1 w-full bg-dl-bg-card border border-dl-border/30 rounded-lg shadow-xl overflow-hidden z-30 max-h-[300px] overflow-y-auto"></div>'),ub=h('<button class="w-full text-left px-3 py-2 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-2"><!> <span class="truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim/50 ml-auto"> </span></button>'),fb=h('<div class="w-full max-w-sm mt-6"><div class="text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold mb-2 text-left">최근 검색</div> <div class="space-y-0.5"></div></div>'),vb=h('<div class="flex flex-col items-center justify-center h-full text-center px-8 max-w-lg mx-auto"><!> <div class="text-[14px] text-dl-text-muted mb-2">공시 뷰어</div> <div class="text-[12px] text-dl-text-dim mb-6">종목을 검색하여 공시 문서를 살펴보세요</div> <div class="w-full max-w-sm relative"><div class="flex items-center gap-2 px-3 py-2 rounded-lg border border-dl-border/30 bg-dl-bg-darker/60 focus-within:border-dl-accent/40 transition-colors"><!> <input placeholder="종목명 또는 종목코드..." class="flex-1 bg-transparent text-[13px] text-dl-text outline-none placeholder:text-dl-text-dim"/> <!></div> <!></div> <!></div>'),pb=h('<div class="flex flex-col items-center justify-center h-full"><!> <div class="text-[12px] text-dl-text-dim">공시 데이터 로딩 중...</div></div>'),hb=h('<div class="flex flex-col items-center justify-center h-full"><!> <div class="text-[11px] text-dl-text-dim">섹션 로딩 중...</div></div>'),mb=h('<div class="max-w-4xl mx-auto px-6 py-4 animate-fadeIn"><!> <!> <div class="mt-4"><!></div></div>'),xb=h('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[13px] text-dl-text-dim">좌측 목차에서 항목을 선택하세요</div></div>'),gb=h('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[13px] text-dl-text-dim">이 종목의 공시 데이터가 없습니다</div></div>'),_b=h('<div class="flex h-full min-h-0 bg-dl-bg-dark relative"><!> <div><div class="h-full flex flex-col"><div class="px-3 py-2 border-b border-dl-border/20 flex-shrink-0"><!></div> <!> <!></div></div> <div class="flex-1 min-w-0 overflow-y-auto"><!> <!> <!> <!></div></div> <!>',1);function bb(t,e){Cr(e,!0);let r=Pe(e,"viewer",3,null),a=Pe(e,"company",3,null),o=Pe(e,"onAskAI",3,null),i=Pe(e,"onTopicChange",3,null),s=Pe(e,"recentCompanies",19,()=>[]),l=Pe(e,"onCompanySelect",3,null),u=Z(!1),f=Z(!1),p=Z(!1);function _(){v(f,typeof window<"u"&&window.innerWidth<=768,!0)}xr(()=>(_(),window.addEventListener("resize",_),()=>window.removeEventListener("resize",_)));let g=Z(!1),w=Z(""),k=Z(null);function S(){v(g,!n(g)),n(g)?requestAnimationFrame(()=>{var y;return(y=n(k))==null?void 0:y.focus()}):(v(w,""),v(ie,null))}xr(()=>{var y;(y=a())!=null&&y.stockCode&&r()&&r().loadCompany(a().stockCode)}),xr(()=>{var y,V,Q;(y=r())!=null&&y.selectedTopic&&((V=r())!=null&&V.topicData)&&((Q=i())==null||Q(r().selectedTopic,r().topicData.topicLabel||r().selectedTopic),E(r().selectedTopic,r().topicData.topicLabel||r().selectedTopic))});let b=Z(Ut([]));const C=8;function z(){var y;try{const V=localStorage.getItem("dartlab-viewer-history");return(V?JSON.parse(V):{})[(y=a())==null?void 0:y.stockCode]||[]}catch{return[]}}function P(y){var V;try{const Q=localStorage.getItem("dartlab-viewer-history"),he=Q?JSON.parse(Q):{};he[(V=a())==null?void 0:V.stockCode]=y,localStorage.setItem("dartlab-viewer-history",JSON.stringify(he))}catch{}}function E(y,V){var he;if(!((he=a())!=null&&he.stockCode))return;const Q=n(b).filter(fe=>fe.topic!==y);v(b,[{topic:y,label:V,time:Date.now()},...Q].slice(0,C),!0),P(n(b))}xr(()=>{var y;(y=a())!=null&&y.stockCode&&v(b,z(),!0)});let ee=Z(""),se=Z(Ut([])),j=Z(!1),T=null,G=Z(null);xr(()=>{const y=n(ee).trim();if(!y||y.length<1){v(se,[],!0);return}clearTimeout(T),v(j,!0),T=setTimeout(async()=>{try{const V=await Ji(y);n(ee).trim()===y&&v(se,V||[],!0)}catch{v(se,[],!0)}v(j,!1)},200)});function K(y){var V;v(ee,""),v(se,[],!0),(V=l())==null||V(y)}let ie=Z(null),U=Z(!1),we=null;function B(){var V,Q;if(!((Q=(V=r())==null?void 0:V.toc)!=null&&Q.chapters))return[];const y=[];for(const he of r().toc.chapters)for(const fe of he.topics)y.push({topic:fe.topic,chapter:he.chapter});return y}function J(y){var V,Q;if((Q=(V=r())==null?void 0:V.toc)!=null&&Q.chapters){for(const he of r().toc.chapters)if(he.topics.find(me=>me.topic===y)){r().selectTopic(y,he.chapter);return}}}function le(y){var V,Q,he,fe;if((Q=(V=r())==null?void 0:V.toc)!=null&&Q.chapters){for(const me of r().toc.chapters)if(me.topics.find(qe=>qe.topic===y)){const qe=n(w).trim();r().selectTopic(y,me.chapter),qe&&((fe=(he=r()).setSearchHighlight)==null||fe.call(he,qe)),v(g,!1),v(w,""),v(ie,null);return}}}function X(y){var he,fe,me,Ae;const V=(he=y.target)==null?void 0:he.tagName,Q=V==="INPUT"||V==="TEXTAREA"||((fe=y.target)==null?void 0:fe.isContentEditable);if(y.key==="f"&&(y.ctrlKey||y.metaKey)&&a()){y.preventDefault(),S();return}if(y.key==="Escape"){if(n(p)){v(p,!1);return}if(n(g)){v(g,!1),v(w,""),v(ie,null);return}return}if(!Q){if(y.key==="?"){v(p,!n(p));return}if(y.key==="/"&&a()){y.preventDefault(),S();return}if(!n(g)&&(y.key==="ArrowUp"||y.key==="ArrowDown"||y.key==="j"||y.key==="k")&&((me=r())!=null&&me.selectedTopic)){const qe=B(),Ie=qe.findIndex(De=>De.topic===r().selectedTopic);if(Ie<0)return;const Re=y.key==="ArrowDown"||y.key==="j"?Ie+1:Ie-1;Re>=0&&Re<qe.length&&(y.preventDefault(),r().selectTopic(qe[Re].topic,qe[Re].chapter));return}if(y.key==="b"&&((Ae=r())!=null&&Ae.selectedTopic)){r().toggleBookmark(r().selectedTopic);return}}}xr(()=>{var Q,he,fe,me;const y=n(w).trim();if(!y||!((Q=a())!=null&&Q.stockCode)){v(ie,null);return}if((he=r())!=null&&he.searchIndexReady){const Ae=r().searchSections(y);v(ie,Ae.length>0?Ae:null,!0);return}const V=[];if((me=(fe=r())==null?void 0:fe.toc)!=null&&me.chapters){const Ae=y.toLowerCase();for(const qe of r().toc.chapters)for(const Ie of qe.topics)(Ie.label.toLowerCase().includes(Ae)||Ie.topic.toLowerCase().includes(Ae))&&V.push({topic:Ie.topic,label:Ie.label,chapter:qe.chapter,snippet:"",matchCount:0,source:"toc"})}v(ie,V.length>0?V:null,!0),clearTimeout(we),y.length>=2&&(v(U,!0),we=setTimeout(async()=>{try{const Ae=await Pv(a().stockCode,y);if(n(w).trim()!==y)return;const qe=(Ae.results||[]).map(Re=>({...Re,source:"text"})),Ie=new Set(V.map(Re=>Re.topic)),je=[...V,...qe.filter(Re=>!Ie.has(Re.topic))];v(ie,je.length>0?je:null,!0)}catch{}v(U,!1)},300))});var O=_b();bn("keydown",ws,X);var W=ae(O),F=d(W);{var ce=y=>{var V=V0();ve("click",V,()=>{v(u,!1)}),c(y,V)};$(F,y=>{n(f)&&n(u)&&y(ce)})}var ne=m(F,2),D=d(ne),H=d(D),te=d(H);{var Y=y=>{var V=q0(),Q=d(V),he=d(Q),fe=d(he),me=m(he,2),Ae=d(me),qe=m(Q,2),Ie=d(qe);{var je=Re=>{var De=B0(),pt=d(De);za(pt,{size:12}),ve("click",De,()=>{v(u,!1)}),c(Re,De)};$(Ie,Re=>{n(f)&&Re(je)})}A(()=>{I(fe,a().corpName||a().company),I(Ae,a().stockCode)}),c(y,V)},xe=y=>{var V=H0();c(y,V)};$(te,y=>{a()?y(Y):y(xe,-1)})}var ke=m(H,2);{var re=y=>{var V=W0(),Q=m(d(V),2);Ce(Q,17,s,$e,(he,fe)=>{var me=U0(),Ae=d(me);Wl(Ae,{size:11,class:"text-dl-text-dim/30 flex-shrink-0"});var qe=m(Ae,2),Ie=d(qe),je=m(qe,2),Re=d(je);A(()=>{I(Ie,n(fe).corpName||n(fe).company),I(Re,n(fe).stockCode)}),ve("click",me,()=>{var De;return(De=l())==null?void 0:De(n(fe))}),c(he,me)}),c(y,V)};$(ke,y=>{!a()&&s().length>0&&y(re)})}var Fe=m(ke,2);{let y=R(()=>{var me;return(me=r())==null?void 0:me.toc}),V=R(()=>{var me;return(me=r())==null?void 0:me.tocLoading}),Q=R(()=>{var me;return(me=r())==null?void 0:me.selectedTopic}),he=R(()=>{var me;return(me=r())==null?void 0:me.expandedChapters}),fe=R(()=>{var me,Ae;return((Ae=(me=r())==null?void 0:me.getBookmarks)==null?void 0:Ae.call(me))??[]});z1(Fe,{get toc(){return n(y)},get loading(){return n(V)},get selectedTopic(){return n(Q)},get expandedChapters(){return n(he)},get bookmarks(){return n(fe)},get recentHistory(){return n(b)},onSelectTopic:(me,Ae)=>{var qe;(qe=r())==null||qe.selectTopic(me,Ae),n(f)&&v(u,!1)},onToggleChapter:me=>{var Ae;return(Ae=r())==null?void 0:Ae.toggleChapter(me)}})}var ot=m(ne,2),nt=d(ot);{var lt=y=>{var V=K0(),Q=d(V),he=d(Q),fe=d(he);aa(fe,{size:13,class:"flex-shrink-0"}),ve("click",he,S),c(y,V)};$(nt,y=>{a()&&!n(f)&&y(lt)})}var at=m(nt,2);{var vt=y=>{var V=ob(),Q=d(V),he=d(Q),fe=d(he);aa(fe,{size:16,class:"text-dl-text-dim flex-shrink-0"});var me=m(fe,2);Qn(me,ge=>v(k,ge),()=>n(k));var Ae=m(me,2);{var qe=ge=>{var Ve=G0(),Me=d(Ve);za(Me,{size:14}),ve("click",Ve,()=>{v(w,"")}),c(ge,Ve)};$(Ae,ge=>{n(w)&&ge(qe)})}var Ie=m(he,2),je=d(Ie);{var Re=ge=>{var Ve=eb(),Me=ae(Ve);Ce(Me,17,()=>n(ie).slice(0,15),$e,(Be,Oe)=>{var rt=Q0(),kt=d(rt),Xt=d(kt),It=d(Xt),fr=d(It),_r=m(It,2),br=d(_r),Wt=m(Xt,2);{var mt=bt=>{var zt=J0(),pr=d(zt);A(()=>I(pr,n(Oe).chapter)),c(bt,zt)};$(Wt,bt=>{n(Oe).chapter&&bt(mt)})}var lr=m(Wt,2);{var Rr=bt=>{var zt=Y0(),pr=d(zt);A(()=>I(pr,n(Oe).snippet)),c(bt,zt)};$(lr,bt=>{n(Oe).snippet&&bt(Rr)})}var _t=m(kt,2);{var He=bt=>{var zt=X0(),pr=d(zt);A(()=>I(pr,`${n(Oe).matchCount??""}건`)),c(bt,zt)};$(_t,bt=>{n(Oe).matchCount>0&&bt(He)})}A(()=>{I(fr,n(Oe).label),I(br,n(Oe).topic)}),ve("click",rt,()=>le(n(Oe).topic)),c(Be,rt)});var ye=m(Me,2);{var dt=Be=>{var Oe=Z0(),rt=d(Oe);Ar(rt,{size:14,class:"animate-spin text-dl-text-dim"}),c(Be,Oe)};$(ye,Be=>{n(U)&&Be(dt)})}c(ge,Ve)},De=ge=>{var Ve=tb(),Me=d(Ve);Ar(Me,{size:14,class:"animate-spin text-dl-text-dim"}),c(ge,Ve)},pt=ge=>{var Ve=rb();c(ge,Ve)},Ze=R(()=>n(w).trim()),Bt=ge=>{var Ve=be(),Me=ae(Ve);{var ye=dt=>{var Be=ab(),Oe=m(ae(Be),2);Ce(Oe,17,()=>n(b),$e,(rt,kt)=>{var Xt=nb(),It=d(Xt);Jo(It,{size:12,class:"text-dl-text-dim/40 flex-shrink-0"});var fr=m(It,2),_r=d(fr),br=m(fr,2),Wt=d(br);A(()=>{I(_r,n(kt).label),I(Wt,n(kt).topic)}),ve("click",Xt,()=>le(n(kt).topic)),c(rt,Xt)}),c(dt,Be)};$(Me,dt=>{n(b).length>0&&dt(ye)})}c(ge,Ve)};$(je,ge=>{n(ie)?ge(Re):n(U)?ge(De,1):n(Ze)?ge(pt,2):ge(Bt,-1)})}ve("click",V,()=>{v(g,!1),v(w,""),v(ie,null)}),ve("click",Q,ge=>ge.stopPropagation()),_a(me,()=>n(w),ge=>v(w,ge)),c(y,V)};$(at,y=>{n(g)&&y(vt)})}var tt=m(at,2);{var Qe=y=>{var V=ib(),Q=d(V),he=d(Q);hn(he,{size:11});var fe=m(Q,2),me=d(fe);aa(me,{size:11});var Ae=m(fe,2);{var qe=Ie=>{var je=sb(),Re=d(je);A(()=>{var De,pt,Ze;return I(Re,((pt=(De=r())==null?void 0:De.topicData)==null?void 0:pt.topicLabel)||((Ze=r())==null?void 0:Ze.selectedTopic))}),c(Ie,je)};$(Ae,Ie=>{var je;(je=r())!=null&&je.selectedTopic&&Ie(qe)})}ve("click",Q,()=>{v(u,!0)}),ve("click",fe,S),c(y,V)};$(tt,y=>{n(f)&&a()&&y(Qe)})}var yt=m(tt,2);{var $t=y=>{var V=vb(),Q=d(V);hn(Q,{size:32,class:"text-dl-text-dim/30 mb-3"});var he=m(Q,6),fe=d(he),me=d(fe);aa(me,{size:14,class:"text-dl-text-dim flex-shrink-0"});var Ae=m(me,2);Qn(Ae,Ze=>v(G,Ze),()=>n(G));var qe=m(Ae,2);{var Ie=Ze=>{Ar(Ze,{size:14,class:"animate-spin text-dl-text-dim flex-shrink-0"})};$(qe,Ze=>{n(j)&&Ze(Ie)})}var je=m(fe,2);{var Re=Ze=>{var Bt=cb();Ce(Bt,21,()=>n(se).slice(0,10),$e,(ge,Ve)=>{var Me=db(),ye=d(Me);Wl(ye,{size:13,class:"text-dl-text-dim/40 flex-shrink-0"});var dt=m(ye,2),Be=d(dt),Oe=m(dt,2),rt=d(Oe),kt=m(Oe,2);{var Xt=It=>{var fr=lb(),_r=d(fr);A(()=>I(_r,n(Ve).market)),c(It,fr)};$(kt,It=>{n(Ve).market&&It(Xt)})}A(()=>{I(Be,n(Ve).corpName||n(Ve).company),I(rt,n(Ve).stockCode)}),ve("click",Me,()=>K(n(Ve))),c(ge,Me)}),c(Ze,Bt)};$(je,Ze=>{n(se).length>0&&Ze(Re)})}var De=m(he,2);{var pt=Ze=>{var Bt=fb(),ge=m(d(Bt),2);Ce(ge,21,s,$e,(Ve,Me)=>{var ye=ub(),dt=d(ye);Jo(dt,{size:12,class:"text-dl-text-dim/30 flex-shrink-0"});var Be=m(dt,2),Oe=d(Be),rt=m(Be,2),kt=d(rt);A(()=>{I(Oe,n(Me).corpName||n(Me).company),I(kt,n(Me).stockCode)}),ve("click",ye,()=>{var Xt;return(Xt=l())==null?void 0:Xt(n(Me))}),c(Ve,ye)}),c(Ze,Bt)};$(De,Ze=>{s().length>0&&Ze(pt)})}_a(Ae,()=>n(ee),Ze=>v(ee,Ze)),c(y,V)},Et=y=>{var V=pb(),Q=d(V);Ar(Q,{size:24,class:"animate-spin text-dl-text-dim/40 mb-3"}),c(y,V)},or=y=>{var V=hb(),Q=d(V);Ar(Q,{size:20,class:"animate-spin text-dl-text-dim/40 mb-2"}),c(y,V)},x=y=>{var V=mb(),Q=d(V);q_(Q,{get data(){return r().insightData},get loading(){return r().insightLoading},get toc(){return r().toc},onNavigateTopic:J});var he=m(Q,2);{let Ae=R(()=>{var qe;return(qe=a())==null?void 0:qe.stockCode});R0(he,{get data(){return r().networkData},get loading(){return r().networkLoading},get centerCode(){return n(Ae)},onNavigate:qe=>{var Ie;r()&&qe!==((Ie=a())==null?void 0:Ie.stockCode)&&r().loadCompany(qe)}})}var fe=m(he,2),me=d(fe);$_(me,{get topicData(){return r().topicData},get diffSummary(){return r().diffSummary},get viewer(){return r()},get onAskAI(){return o()},get searchHighlight(){return r().searchHighlight}}),c(y,V)},N=y=>{var V=xb(),Q=d(V);hn(Q,{size:28,class:"text-dl-text-dim/30 mb-3"}),c(y,V)},L=y=>{var V=gb(),Q=d(V);Oa(Q,{size:28,class:"text-dl-text-dim/30 mb-3"}),c(y,V)};$(yt,y=>{var V,Q,he,fe,me,Ae,qe,Ie;a()?(V=r())!=null&&V.tocLoading?y(Et,1):(Q=r())!=null&&Q.topicLoading?y(or,2):(he=r())!=null&&he.topicData?y(x,3):(fe=r())!=null&&fe.toc&&!((me=r())!=null&&me.selectedTopic)?y(N,4):((Ie=(qe=(Ae=r())==null?void 0:Ae.toc)==null?void 0:qe.chapters)==null?void 0:Ie.length)===0&&y(L,5):y($t)})}var q=m(W,2);F0(q,{get show(){return n(p)},onClose:()=>{v(p,!1)}}),A(()=>Xe(ne,1,`${n(f)?`fixed top-0 left-0 bottom-0 z-50 w-64 transition-transform duration-200 ${n(u)?"translate-x-0":"-translate-x-full"}`:"flex-shrink-0 w-56"} border-r border-dl-border/30 overflow-hidden bg-dl-bg-dark`)),c(t,O),Sr()}Or(["click"]);var wb=h('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),yb=h("<!> <span>확인 중...</span>",1),kb=h("<!> <span>설정 필요</span>",1),Cb=h('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),Sb=h('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!>',1),$b=h('<div class="min-w-0 flex-1 pt-10"><!></div>'),zb=h('<div class="flex-shrink-0 border-l border-dl-border/30 transition-all duration-300"><!></div>'),Mb=h('<div class="min-w-0 flex-1 flex flex-col"><!></div> <!>',1),Tb=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),Ib=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),Ab=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),Eb=h('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),Nb=h('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),Pb=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),Lb=h('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),Ob=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),Rb=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),Db=h('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),jb=h('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),Fb=h('<div class="text-[10px] text-dl-text-dim mt-2"> </div>'),Vb=h('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex login</div></div></div></div> <!> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),Bb=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2"> </div></div>'),qb=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 계정 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),Hb=h('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),Ub=h("<button> <!></button>"),Wb=h('<div class="flex flex-wrap gap-1.5"></div>'),Kb=h('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),Gb=h('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),Jb=h('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),Yb=h('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),Xb=h('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),Qb=h('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),Zb=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),e2=h("<!> <!> <!> <!> <!> <!>",1),t2=h('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),r2=h('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),n2=h('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),a2=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><span class="text-[10px] text-dl-text-dim">공시 보기</span> <!></div></button>'),o2=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div></div> <!>',1),s2=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div></button>'),i2=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div></div> <!>',1),l2=h('<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),d2=h('<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim"><!> <div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div> <div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div></div>'),c2=h('<div class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn" role="presentation"><div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"><div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"/> <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div> <div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim"><span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span></div></div></div>'),u2=h('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),f2=h('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-2 left-3 z-20 pointer-events-auto flex items-center gap-1"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center ml-2 rounded-lg bg-dl-bg-card/60 border border-dl-border/20 p-0.5"><button><!> <span>Chat</span></button> <button><!> <span>Viewer</span></button></div></div> <div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="종목 검색 (Ctrl+K)"><!></button> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <button><!> <!></button></div> <div class="flex flex-1 min-h-0"><!></div></div></div>  <!> <!> <!> <!>',1);function v2(t,e){Cr(e,!0);let r=Z(""),a=Z(!1),o=Z(null),i=Z(Ut({})),s=Z(Ut({})),l=Z(null),u=Z(null),f=Z(Ut([])),p=Z(!1),_=Z(0),g=Z(!0),w=Z(""),k=Z(!1),S=Z(null),b=Z(Ut({})),C=Z(Ut({})),z=Z(""),P=Z(!1),E=Z(null),ee=Z(""),se=Z(!1),j=Z(""),T=Z(0),G=Z(null),K=Z(null),ie=Z(null);const U=Op(),we=Yp();let B=Z(!1),J=R(()=>n(B)?"100%":U.panelMode==="viewer"?"65%":"50%"),le=Z(!1),X=Z(""),O=Z(Ut([])),W=Z(-1),F=null,ce=Z(null),ne=Z(!1);function D(){v(ne,window.innerWidth<=768),n(ne)&&(v(p,!1),U.closePanel())}xr(()=>(D(),window.addEventListener("resize",D),()=>window.removeEventListener("resize",D))),xr(()=>{!n(k)||!n(K)||requestAnimationFrame(()=>{var M;return(M=n(K))==null?void 0:M.focus()})}),xr(()=>{!n(H)||!n(ie)||requestAnimationFrame(()=>{var M;return(M=n(ie))==null?void 0:M.focus()})}),xr(()=>{!n(le)||!n(ce)||requestAnimationFrame(()=>{var M;return(M=n(ce))==null?void 0:M.focus()})});let H=Z(null),te=Z(""),Y=Z("error"),xe=Z(!1);function ke(M,de="error",Ee=4e3){v(te,M,!0),v(Y,de,!0),v(xe,!0),setTimeout(()=>{v(xe,!1)},Ee)}const re=Ep();xr(()=>{tt()});let Fe=Z(Ut({}));function ot(M){return M==="chatgpt"?"codex":M}function nt(M){return`dartlab-api-key:${ot(M)}`}function lt(M){return typeof sessionStorage>"u"||!M?"":sessionStorage.getItem(nt(M))||""}function at(M,de){typeof sessionStorage>"u"||!M||(de?sessionStorage.setItem(nt(M),de):sessionStorage.removeItem(nt(M)))}async function vt(M,de=null,Ee=null){var Le;const Ne=await Cv(M,de,Ee);if(Ne!=null&&Ne.provider){const et=ot(Ne.provider);v(i,{...n(i),[et]:{...n(i)[et]||{},available:!!Ne.available,model:Ne.model||((Le=n(i)[et])==null?void 0:Le.model)||de||null}},!0)}return Ne}async function tt(){var M,de,Ee;v(g,!0);try{const Ne=await kv();v(i,Ne.providers||{},!0),v(s,Ne.ollama||{},!0),v(Fe,Ne.codex||{},!0),Ne.version&&v(w,Ne.version,!0);const Le=ot(localStorage.getItem("dartlab-provider")),et=localStorage.getItem("dartlab-model"),ze=lt(Le);if(Le&&((M=n(i)[Le])!=null&&M.available)){v(l,Le,!0),v(S,Le,!0),v(z,ze,!0),await Qe(Le);const pe=n(b)[Le]||[];et&&pe.includes(et)?v(u,et,!0):pe.length>0&&(v(u,pe[0],!0),localStorage.setItem("dartlab-model",n(u))),v(f,pe,!0),v(g,!1);return}if(Le&&n(i)[Le]){if(v(l,Le,!0),v(S,Le,!0),v(z,ze,!0),ze)try{await vt(Le,et,ze)}catch{}await Qe(Le);const pe=n(b)[Le]||[];v(f,pe,!0),et&&pe.includes(et)?v(u,et,!0):pe.length>0&&v(u,pe[0],!0),v(g,!1);return}for(const pe of["codex","ollama","openai"])if((de=n(i)[pe])!=null&&de.available){v(l,pe,!0),v(S,pe,!0),v(z,lt(pe),!0),await Qe(pe);const Te=n(b)[pe]||[];v(f,Te,!0),v(u,((Ee=n(i)[pe])==null?void 0:Ee.model)||(Te.length>0?Te[0]:null),!0),n(u)&&localStorage.setItem("dartlab-model",n(u));break}}catch{}v(g,!1)}async function Qe(M){M=ot(M),v(C,{...n(C),[M]:!0},!0);try{const de=await Sv(M);v(b,{...n(b),[M]:de.models||[]},!0)}catch{v(b,{...n(b),[M]:[]},!0)}v(C,{...n(C),[M]:!1},!0)}async function yt(M){var Ee;M=ot(M),v(l,M,!0),v(u,null),v(S,M,!0),localStorage.setItem("dartlab-provider",M),localStorage.removeItem("dartlab-model"),v(z,lt(M),!0),v(E,null),await Qe(M);const de=n(b)[M]||[];if(v(f,de,!0),de.length>0&&(v(u,((Ee=n(i)[M])==null?void 0:Ee.model)||de[0],!0),localStorage.setItem("dartlab-model",n(u)),n(z)))try{await vt(M,n(u),n(z))}catch{}}async function $t(M){v(u,M,!0),localStorage.setItem("dartlab-model",M);const de=lt(n(l));if(de)try{await vt(ot(n(l)),M,de)}catch{}}function Et(M){M=ot(M),n(S)===M?v(S,null):(v(S,M,!0),Qe(M))}async function or(){const M=n(z).trim();if(!(!M||!n(l))){v(P,!0),v(E,null);try{const de=await vt(ot(n(l)),n(u),M);de.available?(at(n(l),M),v(E,"success"),!n(u)&&de.model&&v(u,de.model,!0),await Qe(n(l)),v(f,n(b)[n(l)]||[],!0),ke("API 키 인증 성공","success")):(at(n(l),""),v(E,"error"))}catch{at(n(l),""),v(E,"error")}v(P,!1)}}async function x(){try{await zv(),n(l)==="codex"&&v(i,{...n(i),codex:{...n(i).codex,available:!1}},!0),ke("Codex 계정 로그아웃 완료","success"),await tt()}catch{ke("로그아웃 실패")}}function N(){const M=n(ee).trim();!M||n(se)||(v(se,!0),v(j,"준비 중..."),v(T,0),v(G,$v(M,{onProgress(de){de.total&&de.completed!==void 0?(v(T,Math.round(de.completed/de.total*100),!0),v(j,`다운로드 중... ${n(T)}%`)):de.status&&v(j,de.status,!0)},async onDone(){v(se,!1),v(G,null),v(ee,""),v(j,""),v(T,0),ke(`${M} 다운로드 완료`,"success"),await Qe("ollama"),v(f,n(b).ollama||[],!0),n(f).includes(M)&&await $t(M)},onError(de){v(se,!1),v(G,null),v(j,""),v(T,0),ke(`다운로드 실패: ${de}`)}}),!0))}function L(){n(G)&&(n(G).abort(),v(G,null)),v(se,!1),v(ee,""),v(j,""),v(T,0)}function q(){v(p,!n(p))}function y(M){U.openData(M)}function V(M,de=null){U.openEvidence(M,de)}function Q(M){U.openViewer(M)}function he(){if(v(z,""),v(E,null),n(l))v(S,n(l),!0);else{const M=Object.keys(n(i));v(S,M.length>0?M[0]:null,!0)}v(k,!0),n(S)&&Qe(n(S))}function fe(M){var de,Ee,Ne,Le;if(M)for(let et=M.messages.length-1;et>=0;et--){const ze=M.messages[et];if(ze.role==="assistant"&&((de=ze.meta)!=null&&de.stockCode||(Ee=ze.meta)!=null&&Ee.company||ze.company)){U.syncCompanyFromMessage({company:((Ne=ze.meta)==null?void 0:Ne.company)||ze.company,stockCode:(Le=ze.meta)==null?void 0:Le.stockCode},U.selectedCompany);return}}}function me(){re.createConversation(),v(r,""),v(a,!1),n(o)&&(n(o).abort(),v(o,null))}function Ae(M){re.setActive(M),fe(re.active),v(r,""),v(a,!1),n(o)&&(n(o).abort(),v(o,null))}function qe(M){v(H,M,!0)}function Ie(){n(H)&&(re.deleteConversation(n(H)),v(H,null))}function je(){var de;const M=re.active;if(!M)return null;for(let Ee=M.messages.length-1;Ee>=0;Ee--){const Ne=M.messages[Ee];if(Ne.role==="assistant"&&((de=Ne.meta)!=null&&de.stockCode))return Ne.meta.stockCode}return null}async function Re(M=null){var Ft,Ht,St;const de=(M??n(r)).trim();if(!de||n(a))return;if(!n(l)||!((Ft=n(i)[n(l)])!=null&&Ft.available)){ke("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),he();return}re.activeId||re.createConversation();const Ee=re.activeId;re.addMessage("user",de),v(r,""),v(a,!0),re.addMessage("assistant",""),re.updateLastMessage({loading:!0,startedAt:Date.now()}),Bo(_);const Ne=re.active,Le=[];let et=null;if(Ne){const ue=Ne.messages.slice(0,-2);for(const _e of ue)if((_e.role==="user"||_e.role==="assistant")&&_e.text&&_e.text.trim()&&!_e.error&&!_e.loading){const ct={role:_e.role,text:_e.text};_e.role==="assistant"&&((Ht=_e.meta)!=null&&Ht.stockCode)&&(ct.meta={company:_e.meta.company||_e.company,stockCode:_e.meta.stockCode,modules:_e.meta.includedModules||null,market:_e.meta.market||null,topic:_e.meta.topic||null,topicLabel:_e.meta.topicLabel||null,dialogueMode:_e.meta.dialogueMode||null,questionTypes:_e.meta.questionTypes||null,userGoal:_e.meta.userGoal||null},et=_e.meta.stockCode),Le.push(ct)}}const ze=((St=U.selectedCompany)==null?void 0:St.stockCode)||et||je(),pe=U.getViewContext();function Te(){return re.activeId!==Ee}const Ge={provider:n(l),model:n(u),viewContext:pe},wt=lt(n(l));wt&&(Ge.api_key=wt);const At=jv(ze,de,Ge,{onMeta(ue){var tr;if(Te())return;const _e=re.active,ct=_e==null?void 0:_e.messages[_e.messages.length-1],xt={meta:{...(ct==null?void 0:ct.meta)||{},...ue}};ue.company&&(xt.company=ue.company,re.activeId&&((tr=re.active)==null?void 0:tr.title)==="새 대화"&&re.updateTitle(re.activeId,ue.company)),ue.stockCode&&(xt.stockCode=ue.stockCode),(ue.company||ue.stockCode)&&U.syncCompanyFromMessage(ue,U.selectedCompany),re.updateLastMessage(xt)},onSnapshot(ue){Te()||re.updateLastMessage({snapshot:ue})},onContext(ue){if(Te())return;const _e=re.active;if(!_e)return;const ct=_e.messages[_e.messages.length-1],Je=(ct==null?void 0:ct.contexts)||[];re.updateLastMessage({contexts:[...Je,{module:ue.module,label:ue.label,text:ue.text}]})},onSystemPrompt(ue){Te()||re.updateLastMessage({systemPrompt:ue.text,userContent:ue.userContent||null})},onToolCall(ue){if(Te())return;const _e=re.active;if(!_e)return;const ct=_e.messages[_e.messages.length-1],Je=(ct==null?void 0:ct.toolEvents)||[];re.updateLastMessage({toolEvents:[...Je,{type:"call",name:ue.name,arguments:ue.arguments}]})},onToolResult(ue){if(Te())return;const _e=re.active;if(!_e)return;const ct=_e.messages[_e.messages.length-1],Je=(ct==null?void 0:ct.toolEvents)||[];re.updateLastMessage({toolEvents:[...Je,{type:"result",name:ue.name,result:ue.result}]})},onChunk(ue){if(Te())return;const _e=re.active;if(!_e)return;const ct=_e.messages[_e.messages.length-1];re.updateLastMessage({text:((ct==null?void 0:ct.text)||"")+ue}),Bo(_)},onDone(){if(Te())return;const ue=re.active,_e=ue==null?void 0:ue.messages[ue.messages.length-1],ct=_e!=null&&_e.startedAt?((Date.now()-_e.startedAt)/1e3).toFixed(1):null;re.updateLastMessage({loading:!1,duration:ct}),re.flush(),v(a,!1),v(o,null),Bo(_)},onViewerNavigate(ue){Te()||ge(ue)},onError(ue,_e,ct){Te()||(re.updateLastMessage({text:`오류: ${ue}`,loading:!1,error:!0}),re.flush(),_e==="login"?(ke(`${ue} — 설정에서 Codex 로그인을 확인하세요`),he()):_e==="install"?(ke(`${ue} — 설정에서 Codex 설치 안내를 확인하세요`),he()):ke(ue),v(a,!1),v(o,null))}},Le);v(o,At,!0)}function De(){n(o)&&(n(o).abort(),v(o,null),v(a,!1),re.updateLastMessage({loading:!1}),re.flush())}function pt(){const M=re.active;if(!M||M.messages.length<2)return;let de="";for(let Ee=M.messages.length-1;Ee>=0;Ee--)if(M.messages[Ee].role==="user"){de=M.messages[Ee].text;break}de&&(re.removeLastMessage(),re.removeLastMessage(),v(r,de,!0),requestAnimationFrame(()=>{Re()}))}function Ze(){const M=re.active;if(!M)return;let de=`# ${M.title}

`;for(const et of M.messages)et.role==="user"?de+=`## You

${et.text}

`:et.role==="assistant"&&et.text&&(de+=`## DartLab

${et.text}

`);const Ee=new Blob([de],{type:"text/markdown;charset=utf-8"}),Ne=URL.createObjectURL(Ee),Le=document.createElement("a");Le.href=Ne,Le.download=`${M.title||"dartlab-chat"}.md`,Le.click(),URL.revokeObjectURL(Ne),ke("대화가 마크다운으로 내보내졌습니다","success")}function Bt(M){var Ne;U.switchView("chat");const de=((Ne=we.topicData)==null?void 0:Ne.topicLabel)||"",Ee=de?`[${de}] `:"";v(r,`${Ee}"${M}" — 이 내용에 대해 설명해줘`),requestAnimationFrame(()=>{const Le=document.querySelector(".input-textarea");Le&&Le.focus()})}function ge(M){M!=null&&M.topic&&(U.switchView("viewer"),M.chapter&&we.selectTopic(M.topic,M.chapter))}function Ve(){v(le,!0),v(X,""),v(O,[],!0),v(W,-1)}function Me(M){var Ne,Le;(M.metaKey||M.ctrlKey)&&M.key==="n"&&(M.preventDefault(),me()),(M.metaKey||M.ctrlKey)&&M.key==="k"&&(M.preventDefault(),Ve()),(M.metaKey||M.ctrlKey)&&M.shiftKey&&M.key==="S"&&(M.preventDefault(),q()),M.key==="Escape"&&n(le)?v(le,!1):M.key==="Escape"&&n(k)?v(k,!1):M.key==="Escape"&&n(H)?v(H,null):M.key==="Escape"&&U.panelOpen&&U.closePanel();const de=(Ne=M.target)==null?void 0:Ne.tagName;if(!(de==="INPUT"||de==="TEXTAREA"||((Le=M.target)==null?void 0:Le.isContentEditable))&&!M.ctrlKey&&!M.metaKey&&!M.altKey){if(M.key==="1"){U.switchView("chat");return}if(M.key==="2"){U.switchView("viewer");return}}}let ye=R(()=>{var M;return((M=re.active)==null?void 0:M.messages)||[]}),dt=R(()=>re.active&&re.active.messages.length>0),Be=R(()=>{var M;return!n(g)&&(!n(l)||!((M=n(i)[n(l)])!=null&&M.available))});const Oe=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var rt=f2();bn("keydown",ws,Me);var kt=ae(rt),Xt=d(kt);{var It=M=>{var de=wb();ve("click",de,()=>{v(p,!1)}),c(M,de)};$(Xt,M=>{n(ne)&&n(p)&&M(It)})}var fr=m(Xt,2),_r=d(fr);{let M=R(()=>n(ne)?!0:n(p));Ah(_r,{get conversations(){return re.conversations},get activeId(){return re.activeId},get open(){return n(M)},get version(){return n(w)},onNewChat:()=>{me(),n(ne)&&v(p,!1)},onSelect:de=>{Ae(de),n(ne)&&v(p,!1)},onDelete:qe,onOpenSearch:Ve})}var br=m(fr,2),Wt=d(br),mt=d(Wt),lr=d(mt);{var Rr=M=>{ph(M,{size:18})},_t=M=>{vh(M,{size:18})};$(lr,M=>{n(p)?M(Rr):M(_t,-1)})}var He=m(mt,2),bt=d(He),zt=d(bt);zs(zt,{size:12});var pr=m(bt,2),qt=d(pr);$i(qt,{size:12});var Ot=m(Wt,2),dr=d(Ot),sr=d(dr);aa(sr,{size:14});var Nt=m(dr,2),Ct=d(Nt);hn(Ct,{size:14});var Rt=m(Nt,2),ir=d(Rt);ch(ir,{size:14});var gt=m(Rt,2),Se=d(gt);ih(Se,{size:14});var Ue=m(gt,2),ht=d(Ue);{var Dt=M=>{var de=yb(),Ee=ae(de);Ar(Ee,{size:12,class:"animate-spin"}),c(M,de)},Qt=M=>{var de=kb(),Ee=ae(de);Oa(Ee,{size:12}),c(M,de)},We=M=>{var de=Sb(),Ee=m(ae(de),2),Ne=d(Ee),Le=m(Ee,2);{var et=ze=>{var pe=Cb(),Te=m(ae(pe),2),Ge=d(Te);A(()=>I(Ge,n(u))),c(ze,pe)};$(Le,ze=>{n(u)&&ze(et)})}A(()=>I(Ne,n(l))),c(M,de)};$(ht,M=>{n(g)?M(Dt):n(Be)?M(Qt,1):M(We,-1)})}var Mt=m(ht,2);mh(Mt,{size:12});var jt=m(Ot,2),cr=d(jt);{var Zt=M=>{var de=$b(),Ee=d(de);bb(Ee,{get viewer(){return we},get company(){return U.selectedCompany},get recentCompanies(){return U.recentCompanies},onCompanySelect:Q,onAskAI:Bt,onTopicChange:(Ne,Le)=>U.setViewerTopic(Ne,Le)}),c(M,de)},wr=M=>{var de=Mb(),Ee=ae(de),Ne=d(Ee);{var Le=Te=>{{let Ge=R(()=>U.viewerTopic?{topic:U.viewerTopic,topicLabel:U.viewerTopicLabel,period:U.viewerPeriod}:null);jm(Te,{get messages(){return n(ye)},get isLoading(){return n(a)},get scrollTrigger(){return n(_)},get selectedCompany(){return U.selectedCompany},get viewerContext(){return n(Ge)},onSend:Re,onStop:De,onRegenerate:pt,onExport:Ze,onOpenData:y,onOpenEvidence:V,onCompanySelect:Q,get inputText(){return n(r)},set inputText(wt){v(r,wt,!0)}})}},et=Te=>{Fh(Te,{onSend:Re,onCompanySelect:Q,get inputText(){return n(r)},set inputText(Ge){v(r,Ge,!0)}})};$(Ne,Te=>{n(dt)?Te(Le):Te(et,-1)})}var ze=m(Ee,2);{var pe=Te=>{var Ge=zb(),wt=d(Ge);v1(wt,{get mode(){return U.panelMode},get company(){return U.selectedCompany},get data(){return U.panelData},onClose:()=>{v(B,!1),U.closePanel()},onTopicChange:(At,Ft)=>U.setViewerTopic(At,Ft),onFullscreen:()=>{v(B,!n(B))},get isFullscreen(){return n(B)}}),A(()=>yo(Ge,`width: ${n(J)??""}; min-width: 360px; ${n(B)?"":"max-width: 75vw;"}`)),c(Te,Ge)};$(ze,Te=>{!n(ne)&&U.panelOpen&&Te(pe)})}c(M,de)};$(cr,M=>{U.activeView==="viewer"?M(Zt):M(wr,-1)})}var Wr=m(kt,2);{var $r=M=>{var de=r2(),Ee=d(de),Ne=d(Ee),Le=d(Ne),et=m(d(Le),2),ze=d(et);za(ze,{size:18});var pe=m(Ne,2),Te=d(pe);Ce(Te,21,()=>Object.entries(n(i)),$e,(ue,_e)=>{var ct=R(()=>Di(n(_e),2));let Je=()=>n(ct)[0],xt=()=>n(ct)[1];const tr=R(()=>Je()===n(l)),Kt=R(()=>n(S)===Je()),er=R(()=>xt().auth==="api_key"),nr=R(()=>xt().auth==="cli"),yr=R(()=>n(b)[Je()]||[]),Kr=R(()=>n(C)[Je()]);var Aa=t2(),Ea=d(Aa),to=d(Ea),ro=m(to,2),no=d(ro),os=d(no),js=d(os),Zc=m(os,2);{var eu=gr=>{var Jr=Tb();c(gr,Jr)};$(Zc,gr=>{n(tr)&&gr(eu)})}var tu=m(no,2),ru=d(tu),nu=m(ro,2),au=d(nu);{var ou=gr=>{Uo(gr,{size:16,class:"text-dl-success"})},su=gr=>{var Jr=Ib(),la=ae(Jr);Jl(la,{size:14,class:"text-amber-400"}),c(gr,Jr)},iu=gr=>{var Jr=Ab(),la=ae(Jr);Oa(la,{size:14,class:"text-amber-400"}),c(gr,Jr)},lu=gr=>{var Jr=Eb(),la=ae(Jr);_h(la,{size:14,class:"text-dl-text-dim"}),c(gr,Jr)};$(au,gr=>{xt().available?gr(ou):n(er)?gr(su,1):n(nr)&&Je()==="codex"&&n(Fe).installed?gr(iu,2):n(nr)&&!xt().available&&gr(lu,3)})}var du=m(Ea,2);{var cu=gr=>{var Jr=e2(),la=ae(Jr);{var uu=vr=>{var zr=Pb(),Dr=d(zr),Yr=d(Dr),mn=m(Dr,2),Gr=d(mn),ln=m(Gr,2),da=d(ln);{var ca=rr=>{Ar(rr,{size:12,class:"animate-spin"})},dn=rr=>{Jl(rr,{size:12})};$(da,rr=>{n(P)?rr(ca):rr(dn,-1)})}var $n=m(mn,2);{var mr=rr=>{var cn=Nb(),jr=d(cn);Oa(jr,{size:12}),c(rr,cn)};$($n,rr=>{n(E)==="error"&&rr(mr)})}A(rr=>{I(Yr,xt().envKey?`환경변수 ${xt().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),ar(Gr,"placeholder",Je()==="openai"?"sk-...":Je()==="claude"?"sk-ant-...":"API Key"),ln.disabled=rr},[()=>!n(z).trim()||n(P)]),ve("keydown",Gr,rr=>{rr.key==="Enter"&&or()}),_a(Gr,()=>n(z),rr=>v(z,rr)),ve("click",ln,or),c(vr,zr)};$(la,vr=>{n(er)&&!xt().available&&vr(uu)})}var al=m(la,2);{var fu=vr=>{var zr=Ob(),Dr=d(zr),Yr=d(Dr);Uo(Yr,{size:13,class:"text-dl-success"});var mn=m(Dr,2),Gr=d(mn),ln=m(Gr,2);{var da=dn=>{var $n=Lb(),mr=d($n);{var rr=jr=>{Ar(jr,{size:10,class:"animate-spin"})},cn=jr=>{var Fn=Wn("변경");c(jr,Fn)};$(mr,jr=>{n(P)?jr(rr):jr(cn,-1)})}A(()=>$n.disabled=n(P)),ve("click",$n,or),c(dn,$n)},ca=R(()=>n(z).trim());$(ln,dn=>{n(ca)&&dn(da)})}ve("keydown",Gr,dn=>{dn.key==="Enter"&&or()}),_a(Gr,()=>n(z),dn=>v(z,dn)),c(vr,zr)};$(al,vr=>{n(er)&&xt().available&&vr(fu)})}var ol=m(al,2);{var vu=vr=>{var zr=Rb(),Dr=m(d(zr),2),Yr=d(Dr);Wo(Yr,{size:14});var mn=m(Yr,2);Gl(mn,{size:10,class:"ml-auto"}),c(vr,zr)},pu=vr=>{var zr=Db(),Dr=d(zr),Yr=d(Dr);Oa(Yr,{size:14}),c(vr,zr)};$(ol,vr=>{Je()==="ollama"&&!n(s).installed?vr(vu):Je()==="ollama"&&n(s).installed&&!n(s).running&&vr(pu,1)})}var sl=m(ol,2);{var hu=vr=>{var zr=Bb(),Dr=d(zr);{var Yr=ln=>{var da=Vb(),ca=ae(da),dn=d(ca),$n=m(ca,2),mr=d($n);{var rr=un=>{var Vn=jb();c(un,Vn)};$(mr,un=>{n(Fe).installed||un(rr)})}var cn=m(mr,2),jr=d(cn),Fn=d(jr),Na=m($n,2);{var Mo=un=>{var Vn=Fb(),ua=d(Vn);A(()=>I(ua,n(Fe).loginStatus)),c(un,Vn)};$(Na,un=>{n(Fe).loginStatus&&un(Mo)})}var To=m(Na,2),en=d(To);Oa(en,{size:12,class:"text-amber-400 flex-shrink-0"}),A(()=>{I(dn,n(Fe).installed?"Codex CLI가 설치되었지만 로그인이 필요합니다":"Codex CLI 설치가 필요합니다"),I(Fn,n(Fe).installed?"1.":"2.")}),c(ln,da)};$(Dr,ln=>{Je()==="codex"&&ln(Yr)})}var mn=m(Dr,2),Gr=d(mn);A(()=>I(Gr,n(Fe).installed?"로그인 완료 후 새로고침하세요":"설치 완료 후 새로고침하세요")),c(vr,zr)};$(sl,vr=>{n(nr)&&!xt().available&&vr(hu)})}var il=m(sl,2);{var mu=vr=>{var zr=qb(),Dr=d(zr),Yr=d(Dr),mn=d(Yr);Uo(mn,{size:13,class:"text-dl-success"});var Gr=m(Yr,2),ln=d(Gr);fh(ln,{size:11}),ve("click",Gr,x),c(vr,zr)};$(il,vr=>{Je()==="codex"&&xt().available&&vr(mu)})}var xu=m(il,2);{var gu=vr=>{var zr=Zb(),Dr=d(zr),Yr=m(d(Dr),2);{var mn=mr=>{Ar(mr,{size:12,class:"animate-spin text-dl-text-dim"})};$(Yr,mr=>{n(Kr)&&mr(mn)})}var Gr=m(Dr,2);{var ln=mr=>{var rr=Hb(),cn=d(rr);Ar(cn,{size:14,class:"animate-spin"}),c(mr,rr)},da=mr=>{var rr=Wb();Ce(rr,21,()=>n(yr),$e,(cn,jr)=>{var Fn=Ub(),Na=d(Fn),Mo=m(Na);{var To=en=>{zi(en,{size:10,class:"inline ml-1"})};$(Mo,en=>{n(jr)===n(u)&&n(tr)&&en(To)})}A(en=>{Xe(Fn,1,en),I(Na,`${n(jr)??""} `)},[()=>ur(hr("px-3 py-1.5 rounded-lg text-[11px] border transition-all",n(jr)===n(u)&&n(tr)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),ve("click",Fn,()=>{Je()!==n(l)&&yt(Je()),$t(n(jr))}),c(cn,Fn)}),c(mr,rr)},ca=mr=>{var rr=Kb();c(mr,rr)};$(Gr,mr=>{n(Kr)&&n(yr).length===0?mr(ln):n(yr).length>0?mr(da,1):mr(ca,-1)})}var dn=m(Gr,2);{var $n=mr=>{var rr=Qb(),cn=d(rr),jr=m(d(cn),2),Fn=m(d(jr));Gl(Fn,{size:9});var Na=m(cn,2);{var Mo=en=>{var un=Gb(),Vn=d(un),ua=d(Vn),Io=d(ua);Ar(Io,{size:12,class:"animate-spin text-dl-primary-light"});var Fs=m(ua,2),ss=m(Vn,2),ea=d(ss),zn=m(ss,2),Vs=d(zn);A(()=>{yo(ea,`width: ${n(T)??""}%`),I(Vs,n(j))}),ve("click",Fs,L),c(en,un)},To=en=>{var un=Xb(),Vn=ae(un),ua=d(Vn),Io=m(ua,2),Fs=d(Io);Wo(Fs,{size:12});var ss=m(Vn,2);Ce(ss,21,()=>Oe,$e,(ea,zn)=>{const Vs=R(()=>n(yr).some(ao=>ao===n(zn).name||ao===n(zn).name.split(":")[0]));var ll=be(),_u=ae(ll);{var bu=ao=>{var Bs=Yb(),dl=d(Bs),cl=d(dl),ul=d(cl),wu=d(ul),fl=m(ul,2),yu=d(fl),ku=m(fl,2);{var Cu=qs=>{var pl=Jb(),Iu=d(pl);A(()=>I(Iu,n(zn).tag)),c(qs,pl)};$(ku,qs=>{n(zn).tag&&qs(Cu)})}var Su=m(cl,2),$u=d(Su),zu=m(dl,2),vl=d(zu),Mu=d(vl),Tu=m(vl,2);Wo(Tu,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),A(()=>{I(wu,n(zn).name),I(yu,n(zn).size),I($u,n(zn).desc),I(Mu,`${n(zn).gb??""} GB`)}),ve("click",Bs,()=>{v(ee,n(zn).name,!0),N()}),c(ao,Bs)};$(_u,ao=>{n(Vs)||ao(bu)})}c(ea,ll)}),A(ea=>Io.disabled=ea,[()=>!n(ee).trim()]),ve("keydown",ua,ea=>{ea.key==="Enter"&&N()}),_a(ua,()=>n(ee),ea=>v(ee,ea)),ve("click",Io,N),c(en,un)};$(Na,en=>{n(se)?en(Mo):en(To,-1)})}c(mr,rr)};$(dn,mr=>{Je()==="ollama"&&mr($n)})}c(vr,zr)};$(xu,vr=>{(xt().available||n(er)||n(nr))&&vr(gu)})}c(gr,Jr)};$(du,gr=>{(n(Kt)||n(tr))&&gr(cu)})}A((gr,Jr)=>{Xe(Aa,1,gr),Xe(to,1,Jr),I(js,xt().label||Je()),I(ru,xt().desc||"")},[()=>ur(hr("rounded-xl border transition-all",n(tr)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>ur(hr("w-2.5 h-2.5 rounded-full flex-shrink-0",xt().available?"bg-dl-success":n(er)?"bg-amber-400":"bg-dl-text-dim"))]),ve("click",Ea,()=>{xt().available||n(er)?Je()===n(l)?Et(Je()):yt(Je()):Et(Je())}),c(ue,Aa)});var Ge=m(pe,2),wt=d(Ge),At=d(wt);{var Ft=ue=>{var _e=Wn();A(()=>{var ct;return I(_e,`현재: ${(((ct=n(i)[n(l)])==null?void 0:ct.label)||n(l))??""} / ${n(u)??""}`)}),c(ue,_e)},Ht=ue=>{var _e=Wn();A(()=>{var ct;return I(_e,`현재: ${(((ct=n(i)[n(l)])==null?void 0:ct.label)||n(l))??""}`)}),c(ue,_e)};$(At,ue=>{n(l)&&n(u)?ue(Ft):n(l)&&ue(Ht,1)})}var St=m(wt,2);Qn(Ee,ue=>v(K,ue),()=>n(K)),ve("click",de,ue=>{ue.target===ue.currentTarget&&v(k,!1)}),ve("click",et,()=>v(k,!1)),ve("click",St,()=>v(k,!1)),c(M,de)};$(Wr,M=>{n(k)&&M($r)})}var Pr=m(Wr,2);{var Sn=M=>{var de=n2(),Ee=d(de),Ne=m(d(Ee),4),Le=d(Ne),et=m(Le,2);Qn(Ee,ze=>v(ie,ze),()=>n(ie)),ve("click",de,ze=>{ze.target===ze.currentTarget&&v(H,null)}),ve("click",Le,()=>v(H,null)),ve("click",et,Ie),c(M,de)};$(Pr,M=>{n(H)&&M(Sn)})}var Dn=m(Pr,2);{var sn=M=>{const de=R(()=>U.recentCompanies||[]);var Ee=c2(),Ne=d(Ee),Le=d(Ne),et=d(Le);aa(et,{size:18,class:"text-dl-text-dim flex-shrink-0"});var ze=m(et,2);Qn(ze,ue=>v(ce,ue),()=>n(ce));var pe=m(Le,2),Te=d(pe);{var Ge=ue=>{var _e=o2(),ct=m(ae(_e),2);Ce(ct,17,()=>n(O),$e,(Je,xt,tr)=>{var Kt=a2(),er=d(Kt),nr=d(er),yr=m(er,2),Kr=d(yr),Aa=d(Kr),Ea=m(Kr,2),to=d(Ea),ro=m(yr,2),no=m(d(ro),2);hn(no,{size:14,class:"text-dl-text-dim"}),A((os,js)=>{Xe(Kt,1,os),I(nr,js),I(Aa,n(xt).corpName),I(to,`${n(xt).stockCode??""} · ${(n(xt).market||"")??""}${n(xt).sector?` · ${n(xt).sector}`:""}`)},[()=>ur(hr("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",tr===n(W)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(xt).corpName||"?").charAt(0)]),ve("click",Kt,()=>{v(le,!1),v(X,""),v(O,[],!0),v(W,-1),Q(n(xt))}),bn("mouseenter",Kt,()=>{v(W,tr,!0)}),c(Je,Kt)}),c(ue,_e)},wt=ue=>{var _e=i2(),ct=m(ae(_e),2);Ce(ct,17,()=>n(de),$e,(Je,xt,tr)=>{var Kt=s2(),er=d(Kt),nr=d(er),yr=m(er,2),Kr=d(yr),Aa=d(Kr),Ea=m(Kr,2),to=d(Ea);A((ro,no)=>{Xe(Kt,1,ro),I(nr,no),I(Aa,n(xt).corpName),I(to,`${n(xt).stockCode??""} · ${(n(xt).market||"")??""}`)},[()=>ur(hr("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",tr===n(W)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(xt).corpName||"?").charAt(0)]),ve("click",Kt,()=>{v(le,!1),v(X,""),v(W,-1),Q(n(xt))}),bn("mouseenter",Kt,()=>{v(W,tr,!0)}),c(Je,Kt)}),c(ue,_e)},At=R(()=>n(X).trim().length===0&&n(de).length>0),Ft=ue=>{var _e=l2();c(ue,_e)},Ht=R(()=>n(X).trim().length>0),St=ue=>{var _e=d2(),ct=d(_e);aa(ct,{size:24,class:"mb-2 opacity-40"}),c(ue,_e)};$(Te,ue=>{n(O).length>0?ue(Ge):n(At)?ue(wt,1):n(Ht)?ue(Ft,2):ue(St,-1)})}ve("click",Ee,ue=>{ue.target===ue.currentTarget&&v(le,!1)}),ve("input",ze,()=>{F&&clearTimeout(F),n(X).trim().length>=1?F=setTimeout(async()=>{var ue;try{const _e=await Ji(n(X).trim());v(O,((ue=_e.results)==null?void 0:ue.slice(0,8))||[],!0)}catch{v(O,[],!0)}},250):v(O,[],!0)}),ve("keydown",ze,ue=>{const _e=n(O).length>0?n(O):n(de);if(ue.key==="ArrowDown")ue.preventDefault(),v(W,Math.min(n(W)+1,_e.length-1),!0);else if(ue.key==="ArrowUp")ue.preventDefault(),v(W,Math.max(n(W)-1,-1),!0);else if(ue.key==="Enter"&&n(W)>=0&&_e[n(W)]){ue.preventDefault();const ct=_e[n(W)];v(le,!1),v(X,""),v(O,[],!0),v(W,-1),Q(ct)}else ue.key==="Escape"&&v(le,!1)}),_a(ze,()=>n(X),ue=>v(X,ue)),c(M,Ee)};$(Dn,M=>{n(le)&&M(sn)})}var jn=m(Dn,2);{var Pt=M=>{var de=u2(),Ee=d(de),Ne=d(Ee),Le=d(Ne),et=m(Ne,2),ze=d(et);za(ze,{size:14}),A(pe=>{Xe(Ee,1,pe),I(Le,n(te))},[()=>ur(hr("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",n(Y)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":n(Y)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),ve("click",et,()=>{v(xe,!1)}),c(M,de)};$(jn,M=>{n(xe)&&M(Pt)})}A(M=>{Xe(fr,1,ur(n(ne)?n(p)?"sidebar-mobile":"hidden":"")),Xe(bt,1,`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors ${U.activeView==="chat"?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-dim hover:text-dl-text-muted"}`),Xe(pr,1,`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors ${U.activeView==="viewer"?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-dim hover:text-dl-text-muted"}`),Xe(Ue,1,M)},[()=>ur(hr("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",n(g)?"text-dl-text-dim":n(Be)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),ve("click",mt,q),ve("click",bt,()=>U.switchView("chat")),ve("click",pr,()=>U.switchView("viewer")),ve("click",dr,Ve),ve("click",Ue,()=>he()),c(t,rt),Sr()}Or(["click","keydown","input"]);ev(v2,{target:document.getElementById("app")});export{Ei as C,Ai as _,Pe as a,c as b,be as c,Sr as d,h as e,ae as f,d as g,gi as h,$ as i,wo as j,n as k,I as l,m,ar as n,Ce as o,Cr as p,$e as q,ns as r,Xe as s,A as t,R as u,yo as v};
