const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/ChartRenderer-CMF5oGVz.js","assets/ChartRenderer-DW5VYfwI.css"])))=>i.map(i=>d[i]);
var Ou=Object.defineProperty;var Sl=t=>{throw TypeError(t)};var Du=(t,e,n)=>e in t?Ou(t,e,{enumerable:!0,configurable:!0,writable:!0,value:n}):t[e]=n;var Bn=(t,e,n)=>Du(t,typeof e!="symbol"?e+"":e,n),ti=(t,e,n)=>e.has(t)||Sl("Cannot "+n);var se=(t,e,n)=>(ti(t,e,"read from private field"),n?n.call(t):e.get(t)),Qt=(t,e,n)=>e.has(t)?Sl("Cannot add the same private member more than once"):e instanceof WeakSet?e.add(t):e.set(t,n),Vt=(t,e,n,a)=>(ti(t,e,"write to private field"),a?a.call(t,n):e.set(t,n),n),Dr=(t,e,n)=>(ti(t,e,"access private method"),n);(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const o of document.querySelectorAll('link[rel="modulepreload"]'))a(o);new MutationObserver(o=>{for(const i of o)if(i.type==="childList")for(const s of i.addedNodes)s.tagName==="LINK"&&s.rel==="modulepreload"&&a(s)}).observe(document,{childList:!0,subtree:!0});function n(o){const i={};return o.integrity&&(i.integrity=o.integrity),o.referrerPolicy&&(i.referrerPolicy=o.referrerPolicy),o.crossOrigin==="use-credentials"?i.credentials="include":o.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function a(o){if(o.ep)return;o.ep=!0;const i=n(o);fetch(o.href,i)}})();const pi=!1;var Ki=Array.isArray,Ru=Array.prototype.indexOf,Mo=Array.prototype.includes,Hs=Array.from,ju=Object.defineProperty,La=Object.getOwnPropertyDescriptor,bd=Object.getOwnPropertyDescriptors,Fu=Object.prototype,Vu=Array.prototype,Gi=Object.getPrototypeOf,Ml=Object.isExtensible;function Ho(t){return typeof t=="function"}const Bu=()=>{};function qu(t){return typeof(t==null?void 0:t.then)=="function"}function Hu(t){return t()}function hi(t){for(var e=0;e<t.length;e++)t[e]()}function wd(){var t,e,n=new Promise((a,o)=>{t=a,e=o});return{promise:n,resolve:t,reject:e}}function Ji(t,e){if(Array.isArray(t))return t;if(!(Symbol.iterator in t))return Array.from(t);const n=[];for(const a of t)if(n.push(a),n.length===e)break;return n}const tn=2,Po=4,io=8,Us=1<<24,Ba=16,Xn=32,fo=64,mi=128,Ln=512,Qr=1024,Zr=2048,Yn=4096,cn=8192,la=16384,Lo=32768,ba=65536,zl=1<<17,Uu=1<<18,Oo=1<<19,yd=1<<20,sa=1<<25,lo=65536,xi=1<<21,Yi=1<<22,Oa=1<<23,da=Symbol("$state"),kd=Symbol("legacy props"),Wu=Symbol(""),Ya=new class extends Error{constructor(){super(...arguments);Bn(this,"name","StaleReactionError");Bn(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var xd;const Cd=!!((xd=globalThis.document)!=null&&xd.contentType)&&globalThis.document.contentType.includes("xml");function Ku(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function Gu(t,e,n){throw new Error("https://svelte.dev/e/each_key_duplicate")}function Ju(t){throw new Error("https://svelte.dev/e/effect_in_teardown")}function Yu(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Xu(t){throw new Error("https://svelte.dev/e/effect_orphan")}function Qu(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function Zu(t){throw new Error("https://svelte.dev/e/props_invalid_value")}function ef(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function tf(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function rf(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function nf(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const af=1,of=2,$d=4,sf=8,lf=16,df=1,cf=2,Sd=4,uf=8,ff=16,Md=1,vf=2,jr=Symbol(),zd="http://www.w3.org/1999/xhtml",Td="http://www.w3.org/2000/svg",pf="http://www.w3.org/1998/Math/MathML",hf="@attach";function mf(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function xf(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Id(t){return t===this.v}function gf(t,e){return t!=t?e==e:t!==e||t!==null&&typeof t=="object"||typeof t=="function"}function Ad(t){return!gf(t,this.v)}let fs=!1,_f=!1;function bf(){fs=!0}let Wr=null;function zo(t){Wr=t}function Ir(t,e=!1,n){Wr={p:Wr,i:!1,c:null,e:null,s:t,x:null,l:fs&&!e?{s:null,u:null,$:[]}:null}}function Ar(t){var e=Wr,n=e.e;if(n!==null){e.e=null;for(var a of n)ec(a)}return e.i=!0,Wr=e.p,{}}function Do(){return!fs||Wr!==null&&Wr.l===null}let Xa=[];function Ed(){var t=Xa;Xa=[],hi(t)}function Gn(t){if(Xa.length===0&&!xo){var e=Xa;queueMicrotask(()=>{e===Xa&&Ed()})}Xa.push(t)}function wf(){for(;Xa.length>0;)Ed()}function Nd(t){var e=Yt;if(e===null)return Jt.f|=Oa,t;if((e.f&Lo)===0&&(e.f&Po)===0)throw t;Aa(t,e)}function Aa(t,e){for(;e!==null;){if((e.f&mi)!==0){if((e.f&Lo)===0)throw t;try{e.b.error(t);return}catch(n){t=n}}e=e.parent}throw t}const yf=-7169;function Tr(t,e){t.f=t.f&yf|e}function Xi(t){(t.f&Ln)!==0||t.deps===null?Tr(t,Qr):Tr(t,Yn)}function Pd(t){if(t!==null)for(const e of t)(e.f&tn)===0||(e.f&lo)===0||(e.f^=lo,Pd(e.deps))}function Ld(t,e,n){(t.f&Zr)!==0?e.add(t):(t.f&Yn)!==0&&n.add(t),Pd(t.deps),Tr(t,Qr)}const _s=new Set;let Et=null,As=null,Xr=null,pn=[],Ws=null,xo=!1,To=null,kf=1;var za,_o,eo,bo,wo,yo,Ta,ta,ko,gn,gi,_i,bi,wi;const pl=class pl{constructor(){Qt(this,gn);Bn(this,"id",kf++);Bn(this,"current",new Map);Bn(this,"previous",new Map);Qt(this,za,new Set);Qt(this,_o,new Set);Qt(this,eo,0);Qt(this,bo,0);Qt(this,wo,null);Qt(this,yo,new Set);Qt(this,Ta,new Set);Qt(this,ta,new Map);Bn(this,"is_fork",!1);Qt(this,ko,!1)}skip_effect(e){se(this,ta).has(e)||se(this,ta).set(e,{d:[],m:[]})}unskip_effect(e){var n=se(this,ta).get(e);if(n){se(this,ta).delete(e);for(var a of n.d)Tr(a,Zr),ia(a);for(a of n.m)Tr(a,Yn),ia(a)}}process(e){var o;pn=[],this.apply();var n=To=[],a=[];for(const i of e)Dr(this,gn,_i).call(this,i,n,a);if(To=null,Dr(this,gn,gi).call(this)){Dr(this,gn,bi).call(this,a),Dr(this,gn,bi).call(this,n);for(const[i,s]of se(this,ta))Fd(i,s)}else{As=this,Et=null;for(const i of se(this,za))i(this);se(this,za).clear(),se(this,eo)===0&&Dr(this,gn,wi).call(this),Tl(a),Tl(n),se(this,yo).clear(),se(this,Ta).clear(),As=null,(o=se(this,wo))==null||o.resolve()}Xr=null}capture(e,n){n!==jr&&!this.previous.has(e)&&this.previous.set(e,n),(e.f&Oa)===0&&(this.current.set(e,e.v),Xr==null||Xr.set(e,e.v))}activate(){Et=this,this.apply()}deactivate(){Et===this&&(Et=null,Xr=null)}flush(){var e;if(pn.length>0)Et=this,Dd();else if(se(this,eo)===0&&!this.is_fork){for(const n of se(this,za))n(this);se(this,za).clear(),Dr(this,gn,wi).call(this),(e=se(this,wo))==null||e.resolve()}this.deactivate()}discard(){for(const e of se(this,_o))e(this);se(this,_o).clear()}increment(e){Vt(this,eo,se(this,eo)+1),e&&Vt(this,bo,se(this,bo)+1)}decrement(e){Vt(this,eo,se(this,eo)-1),e&&Vt(this,bo,se(this,bo)-1),!se(this,ko)&&(Vt(this,ko,!0),Gn(()=>{Vt(this,ko,!1),Dr(this,gn,gi).call(this)?pn.length>0&&this.flush():this.revive()}))}revive(){for(const e of se(this,yo))se(this,Ta).delete(e),Tr(e,Zr),ia(e);for(const e of se(this,Ta))Tr(e,Yn),ia(e);this.flush()}oncommit(e){se(this,za).add(e)}ondiscard(e){se(this,_o).add(e)}settled(){return(se(this,wo)??Vt(this,wo,wd())).promise}static ensure(){if(Et===null){const e=Et=new pl;_s.add(Et),xo||Gn(()=>{Et===e&&e.flush()})}return Et}apply(){}};za=new WeakMap,_o=new WeakMap,eo=new WeakMap,bo=new WeakMap,wo=new WeakMap,yo=new WeakMap,Ta=new WeakMap,ta=new WeakMap,ko=new WeakMap,gn=new WeakSet,gi=function(){return this.is_fork||se(this,bo)>0},_i=function(e,n,a){e.f^=Qr;for(var o=e.first;o!==null;){var i=o.f,s=(i&(Xn|fo))!==0,l=s&&(i&Qr)!==0,u=(i&cn)!==0,f=l||se(this,ta).has(o);if(!f&&o.fn!==null){s?u||(o.f^=Qr):(i&Po)!==0?n.push(o):(i&(io|Us))!==0&&u?a.push(o):hs(o)&&(Io(o),(i&Ba)!==0&&(se(this,Ta).add(o),u&&Tr(o,Zr)));var p=o.first;if(p!==null){o=p;continue}}for(;o!==null;){var _=o.next;if(_!==null){o=_;break}o=o.parent}}},bi=function(e){for(var n=0;n<e.length;n+=1)Ld(e[n],se(this,yo),se(this,Ta))},wi=function(){var i;if(_s.size>1){this.previous.clear();var e=Et,n=Xr,a=!0;for(const s of _s){if(s===this){a=!1;continue}const l=[];for(const[f,p]of this.current){if(s.current.has(f))if(a&&p!==s.current.get(f))s.current.set(f,p);else continue;l.push(f)}if(l.length===0)continue;const u=[...s.current.keys()].filter(f=>!this.current.has(f));if(u.length>0){var o=pn;pn=[];const f=new Set,p=new Map;for(const _ of l)Rd(_,u,f,p);if(pn.length>0){Et=s,s.apply();for(const _ of pn)Dr(i=s,gn,_i).call(i,_,[],[]);s.deactivate()}pn=o}}Et=e,Xr=n}se(this,ta).clear(),_s.delete(this)};let ga=pl;function Od(t){var e=xo;xo=!0;try{for(var n;;){if(wf(),pn.length===0&&(Et==null||Et.flush(),pn.length===0))return Ws=null,n;Dd()}}finally{xo=e}}function Dd(){var t=null;try{for(var e=0;pn.length>0;){var n=ga.ensure();if(e++>1e3){var a,o;Cf()}n.process(pn),Da.clear()}}finally{pn=[],Ws=null,To=null}}function Cf(){try{Qu()}catch(t){Aa(t,Ws)}}let qn=null;function Tl(t){var e=t.length;if(e!==0){for(var n=0;n<e;){var a=t[n++];if((a.f&(la|cn))===0&&hs(a)&&(qn=new Set,Io(a),a.deps===null&&a.first===null&&a.nodes===null&&a.teardown===null&&a.ac===null&&ac(a),(qn==null?void 0:qn.size)>0)){Da.clear();for(const o of qn){if((o.f&(la|cn))!==0)continue;const i=[o];let s=o.parent;for(;s!==null;)qn.has(s)&&(qn.delete(s),i.push(s)),s=s.parent;for(let l=i.length-1;l>=0;l--){const u=i[l];(u.f&(la|cn))===0&&Io(u)}}qn.clear()}}qn=null}}function Rd(t,e,n,a){if(!n.has(t)&&(n.add(t),t.reactions!==null))for(const o of t.reactions){const i=o.f;(i&tn)!==0?Rd(o,e,n,a):(i&(Yi|Ba))!==0&&(i&Zr)===0&&jd(o,e,a)&&(Tr(o,Zr),ia(o))}}function jd(t,e,n){const a=n.get(t);if(a!==void 0)return a;if(t.deps!==null)for(const o of t.deps){if(Mo.call(e,o))return!0;if((o.f&tn)!==0&&jd(o,e,n))return n.set(o,!0),!0}return n.set(t,!1),!1}function ia(t){var e=Ws=t,n=e.b;if(n!=null&&n.is_pending&&(t.f&(Po|io|Us))!==0&&(t.f&Lo)===0){n.defer_effect(t);return}for(;e.parent!==null;){e=e.parent;var a=e.f;if(To!==null&&e===Yt&&(t.f&io)===0)return;if((a&(fo|Xn))!==0){if((a&Qr)===0)return;e.f^=Qr}}pn.push(e)}function Fd(t,e){if(!((t.f&Xn)!==0&&(t.f&Qr)!==0)){(t.f&Zr)!==0?e.d.push(t):(t.f&Yn)!==0&&e.m.push(t),Tr(t,Qr);for(var n=t.first;n!==null;)Fd(n,e),n=n.next}}function $f(t){let e=0,n=ua(0),a;return()=>{tl()&&(r(n),rl(()=>(e===0&&(a=co(()=>t(()=>rs(n)))),e+=1,()=>{Gn(()=>{e-=1,e===0&&(a==null||a(),a=void 0,rs(n))})})))}}var Sf=ba|Oo;function Mf(t,e,n,a){new zf(t,e,n,a)}var Nn,Wi,ra,to,vn,na,Sn,Hn,ha,ro,Ia,Co,$o,So,ma,Bs,Fr,Tf,If,Af,yi,Ss,Ms,ki;class zf{constructor(e,n,a,o){Qt(this,Fr);Bn(this,"parent");Bn(this,"is_pending",!1);Bn(this,"transform_error");Qt(this,Nn);Qt(this,Wi,null);Qt(this,ra);Qt(this,to);Qt(this,vn);Qt(this,na,null);Qt(this,Sn,null);Qt(this,Hn,null);Qt(this,ha,null);Qt(this,ro,0);Qt(this,Ia,0);Qt(this,Co,!1);Qt(this,$o,new Set);Qt(this,So,new Set);Qt(this,ma,null);Qt(this,Bs,$f(()=>(Vt(this,ma,ua(se(this,ro))),()=>{Vt(this,ma,null)})));var i;Vt(this,Nn,e),Vt(this,ra,n),Vt(this,to,s=>{var l=Yt;l.b=this,l.f|=mi,a(s)}),this.parent=Yt.b,this.transform_error=o??((i=this.parent)==null?void 0:i.transform_error)??(s=>s),Vt(this,vn,vo(()=>{Dr(this,Fr,yi).call(this)},Sf))}defer_effect(e){Ld(e,se(this,$o),se(this,So))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!se(this,ra).pending}update_pending_count(e){Dr(this,Fr,ki).call(this,e),Vt(this,ro,se(this,ro)+e),!(!se(this,ma)||se(this,Co))&&(Vt(this,Co,!0),Gn(()=>{Vt(this,Co,!1),se(this,ma)&&_a(se(this,ma),se(this,ro))}))}get_effect_pending(){return se(this,Bs).call(this),r(se(this,ma))}error(e){var n=se(this,ra).onerror;let a=se(this,ra).failed;if(!n&&!a)throw e;se(this,na)&&(en(se(this,na)),Vt(this,na,null)),se(this,Sn)&&(en(se(this,Sn)),Vt(this,Sn,null)),se(this,Hn)&&(en(se(this,Hn)),Vt(this,Hn,null));var o=!1,i=!1;const s=()=>{if(o){xf();return}o=!0,i&&nf(),se(this,Hn)!==null&&ao(se(this,Hn),()=>{Vt(this,Hn,null)}),Dr(this,Fr,Ms).call(this,()=>{ga.ensure(),Dr(this,Fr,yi).call(this)})},l=u=>{try{i=!0,n==null||n(u,s),i=!1}catch(f){Aa(f,se(this,vn)&&se(this,vn).parent)}a&&Vt(this,Hn,Dr(this,Fr,Ms).call(this,()=>{ga.ensure();try{return mn(()=>{var f=Yt;f.b=this,f.f|=mi,a(se(this,Nn),()=>u,()=>s)})}catch(f){return Aa(f,se(this,vn).parent),null}}))};Gn(()=>{var u;try{u=this.transform_error(e)}catch(f){Aa(f,se(this,vn)&&se(this,vn).parent);return}u!==null&&typeof u=="object"&&typeof u.then=="function"?u.then(l,f=>Aa(f,se(this,vn)&&se(this,vn).parent)):l(u)})}}Nn=new WeakMap,Wi=new WeakMap,ra=new WeakMap,to=new WeakMap,vn=new WeakMap,na=new WeakMap,Sn=new WeakMap,Hn=new WeakMap,ha=new WeakMap,ro=new WeakMap,Ia=new WeakMap,Co=new WeakMap,$o=new WeakMap,So=new WeakMap,ma=new WeakMap,Bs=new WeakMap,Fr=new WeakSet,Tf=function(){try{Vt(this,na,mn(()=>se(this,to).call(this,se(this,Nn))))}catch(e){this.error(e)}},If=function(e){const n=se(this,ra).failed;n&&Vt(this,Hn,mn(()=>{n(se(this,Nn),()=>e,()=>()=>{})}))},Af=function(){const e=se(this,ra).pending;e&&(this.is_pending=!0,Vt(this,Sn,mn(()=>e(se(this,Nn)))),Gn(()=>{var n=Vt(this,ha,document.createDocumentFragment()),a=ca();n.append(a),Vt(this,na,Dr(this,Fr,Ms).call(this,()=>(ga.ensure(),mn(()=>se(this,to).call(this,a))))),se(this,Ia)===0&&(se(this,Nn).before(n),Vt(this,ha,null),ao(se(this,Sn),()=>{Vt(this,Sn,null)}),Dr(this,Fr,Ss).call(this))}))},yi=function(){try{if(this.is_pending=this.has_pending_snippet(),Vt(this,Ia,0),Vt(this,ro,0),Vt(this,na,mn(()=>{se(this,to).call(this,se(this,Nn))})),se(this,Ia)>0){var e=Vt(this,ha,document.createDocumentFragment());ol(se(this,na),e);const n=se(this,ra).pending;Vt(this,Sn,mn(()=>n(se(this,Nn))))}else Dr(this,Fr,Ss).call(this)}catch(n){this.error(n)}},Ss=function(){this.is_pending=!1;for(const e of se(this,$o))Tr(e,Zr),ia(e);for(const e of se(this,So))Tr(e,Yn),ia(e);se(this,$o).clear(),se(this,So).clear()},Ms=function(e){var n=Yt,a=Jt,o=Wr;Rn(se(this,vn)),Dn(se(this,vn)),zo(se(this,vn).ctx);try{return e()}catch(i){return Nd(i),null}finally{Rn(n),Dn(a),zo(o)}},ki=function(e){var n;if(!this.has_pending_snippet()){this.parent&&Dr(n=this.parent,Fr,ki).call(n,e);return}Vt(this,Ia,se(this,Ia)+e),se(this,Ia)===0&&(Dr(this,Fr,Ss).call(this),se(this,Sn)&&ao(se(this,Sn),()=>{Vt(this,Sn,null)}),se(this,ha)&&(se(this,Nn).before(se(this,ha)),Vt(this,ha,null)))};function Vd(t,e,n,a){const o=Do()?vs:Qi;var i=t.filter(_=>!_.settled);if(n.length===0&&i.length===0){a(e.map(o));return}var s=Yt,l=Bd(),u=i.length===1?i[0].promise:i.length>1?Promise.all(i.map(_=>_.promise)):null;function f(_){l();try{a(_)}catch(x){(s.f&la)===0&&Aa(x,s)}Es()}if(n.length===0){u.then(()=>f(e.map(o)));return}function p(){l(),Promise.all(n.map(_=>Nf(_))).then(_=>f([...e.map(o),..._])).catch(_=>Aa(_,s))}u?u.then(p):p()}function Bd(){var t=Yt,e=Jt,n=Wr,a=Et;return function(i=!0){Rn(t),Dn(e),zo(n),i&&(a==null||a.activate())}}function Es(t=!0){Rn(null),Dn(null),zo(null),t&&(Et==null||Et.deactivate())}function Ef(){var t=Yt.b,e=Et,n=t.is_rendered();return t.update_pending_count(1),e.increment(n),()=>{t.update_pending_count(-1),e.decrement(n)}}function vs(t){var e=tn|Zr,n=Jt!==null&&(Jt.f&tn)!==0?Jt:null;return Yt!==null&&(Yt.f|=Oo),{ctx:Wr,deps:null,effects:null,equals:Id,f:e,fn:t,reactions:null,rv:0,v:jr,wv:0,parent:n??Yt,ac:null}}function Nf(t,e,n){Yt===null&&Ku();var o=void 0,i=ua(jr),s=!Jt,l=new Map;return Wf(()=>{var x;var u=wd();o=u.promise;try{Promise.resolve(t()).then(u.resolve,u.reject).finally(Es)}catch(b){u.reject(b),Es()}var f=Et;if(s){var p=Ef();(x=l.get(f))==null||x.reject(Ya),l.delete(f),l.set(f,u)}const _=(b,k=void 0)=>{if(f.activate(),k)k!==Ya&&(i.f|=Oa,_a(i,k));else{(i.f&Oa)!==0&&(i.f^=Oa),_a(i,b);for(const[C,g]of l){if(l.delete(C),C===f)break;g.reject(Ya)}}p&&p()};u.promise.then(_,b=>_(null,b||"unknown"))}),Gs(()=>{for(const u of l.values())u.reject(Ya)}),new Promise(u=>{function f(p){function _(){p===o?u(i):f(o)}p.then(_,_)}f(o)})}function D(t){const e=vs(t);return ic(e),e}function Qi(t){const e=vs(t);return e.equals=Ad,e}function Pf(t){var e=t.effects;if(e!==null){t.effects=null;for(var n=0;n<e.length;n+=1)en(e[n])}}function Lf(t){for(var e=t.parent;e!==null;){if((e.f&tn)===0)return(e.f&la)===0?e:null;e=e.parent}return null}function Zi(t){var e,n=Yt;Rn(Lf(t));try{t.f&=~lo,Pf(t),e=uc(t)}finally{Rn(n)}return e}function qd(t){var e=Zi(t);if(!t.equals(e)&&(t.wv=dc(),(!(Et!=null&&Et.is_fork)||t.deps===null)&&(t.v=e,t.deps===null))){Tr(t,Qr);return}Ra||(Xr!==null?(tl()||Et!=null&&Et.is_fork)&&Xr.set(t,e):Xi(t))}function Of(t){var e,n;if(t.effects!==null)for(const a of t.effects)(a.teardown||a.ac)&&((e=a.teardown)==null||e.call(a),(n=a.ac)==null||n.abort(Ya),a.teardown=Bu,a.ac=null,is(a,0),nl(a))}function Hd(t){if(t.effects!==null)for(const e of t.effects)e.teardown&&Io(e)}let Ci=new Set;const Da=new Map;let Ud=!1;function ua(t,e){var n={f:0,v:t,reactions:null,equals:Id,rv:0,wv:0};return n}function K(t,e){const n=ua(t);return ic(n),n}function $i(t,e=!1,n=!0){var o;const a=ua(t);return e||(a.equals=Ad),fs&&n&&Wr!==null&&Wr.l!==null&&((o=Wr.l).s??(o.s=[])).push(a),a}function v(t,e,n=!1){Jt!==null&&(!Wn||(Jt.f&zl)!==0)&&Do()&&(Jt.f&(tn|Ba|Yi|zl))!==0&&(On===null||!Mo.call(On,t))&&rf();let a=n?Bt(e):e;return _a(t,a)}function _a(t,e){if(!t.equals(e)){var n=t.v;Ra?Da.set(t,e):Da.set(t,n),t.v=e;var a=ga.ensure();if(a.capture(t,n),(t.f&tn)!==0){const o=t;(t.f&Zr)!==0&&Zi(o),Xi(o)}t.wv=dc(),Wd(t,Zr),Do()&&Yt!==null&&(Yt.f&Qr)!==0&&(Yt.f&(Xn|fo))===0&&(En===null?Gf([t]):En.push(t)),!a.is_fork&&Ci.size>0&&!Ud&&Df()}return e}function Df(){Ud=!1;for(const t of Ci)(t.f&Qr)!==0&&Tr(t,Yn),hs(t)&&Io(t);Ci.clear()}function ts(t,e=1){var n=r(t),a=e===1?n++:n--;return v(t,n),a}function rs(t){v(t,t.v+1)}function Wd(t,e){var n=t.reactions;if(n!==null)for(var a=Do(),o=n.length,i=0;i<o;i++){var s=n[i],l=s.f;if(!(!a&&s===Yt)){var u=(l&Zr)===0;if(u&&Tr(s,e),(l&tn)!==0){var f=s;Xr==null||Xr.delete(f),(l&lo)===0&&(l&Ln&&(s.f|=lo),Wd(f,Yn))}else u&&((l&Ba)!==0&&qn!==null&&qn.add(s),ia(s))}}}function Bt(t){if(typeof t!="object"||t===null||da in t)return t;const e=Gi(t);if(e!==Fu&&e!==Vu)return t;var n=new Map,a=Ki(t),o=K(0),i=oo,s=l=>{if(oo===i)return l();var u=Jt,f=oo;Dn(null),Nl(i);var p=l();return Dn(u),Nl(f),p};return a&&n.set("length",K(t.length)),new Proxy(t,{defineProperty(l,u,f){(!("value"in f)||f.configurable===!1||f.enumerable===!1||f.writable===!1)&&ef();var p=n.get(u);return p===void 0?s(()=>{var _=K(f.value);return n.set(u,_),_}):v(p,f.value,!0),!0},deleteProperty(l,u){var f=n.get(u);if(f===void 0){if(u in l){const p=s(()=>K(jr));n.set(u,p),rs(o)}}else v(f,jr),rs(o);return!0},get(l,u,f){var b;if(u===da)return t;var p=n.get(u),_=u in l;if(p===void 0&&(!_||(b=La(l,u))!=null&&b.writable)&&(p=s(()=>{var k=Bt(_?l[u]:jr),C=K(k);return C}),n.set(u,p)),p!==void 0){var x=r(p);return x===jr?void 0:x}return Reflect.get(l,u,f)},getOwnPropertyDescriptor(l,u){var f=Reflect.getOwnPropertyDescriptor(l,u);if(f&&"value"in f){var p=n.get(u);p&&(f.value=r(p))}else if(f===void 0){var _=n.get(u),x=_==null?void 0:_.v;if(_!==void 0&&x!==jr)return{enumerable:!0,configurable:!0,value:x,writable:!0}}return f},has(l,u){var x;if(u===da)return!0;var f=n.get(u),p=f!==void 0&&f.v!==jr||Reflect.has(l,u);if(f!==void 0||Yt!==null&&(!p||(x=La(l,u))!=null&&x.writable)){f===void 0&&(f=s(()=>{var b=p?Bt(l[u]):jr,k=K(b);return k}),n.set(u,f));var _=r(f);if(_===jr)return!1}return p},set(l,u,f,p){var O;var _=n.get(u),x=u in l;if(a&&u==="length")for(var b=f;b<_.v;b+=1){var k=n.get(b+"");k!==void 0?v(k,jr):b in l&&(k=s(()=>K(jr)),n.set(b+"",k))}if(_===void 0)(!x||(O=La(l,u))!=null&&O.writable)&&(_=s(()=>K(void 0)),v(_,Bt(f)),n.set(u,_));else{x=_.v!==jr;var C=s(()=>Bt(f));v(_,C)}var g=Reflect.getOwnPropertyDescriptor(l,u);if(g!=null&&g.set&&g.set.call(p,f),!x){if(a&&typeof u=="string"){var y=n.get("length"),I=Number(u);Number.isInteger(I)&&I>=y.v&&v(y,I+1)}rs(o)}return!0},ownKeys(l){r(o);var u=Reflect.ownKeys(l).filter(_=>{var x=n.get(_);return x===void 0||x.v!==jr});for(var[f,p]of n)p.v!==jr&&!(f in l)&&u.push(f);return u},setPrototypeOf(){tf()}})}function Il(t){try{if(t!==null&&typeof t=="object"&&da in t)return t[da]}catch{}return t}function Rf(t,e){return Object.is(Il(t),Il(e))}var Ns,Kd,Gd,Jd,Yd;function jf(){if(Ns===void 0){Ns=window,Kd=document,Gd=/Firefox/.test(navigator.userAgent);var t=Element.prototype,e=Node.prototype,n=Text.prototype;Jd=La(e,"firstChild").get,Yd=La(e,"nextSibling").get,Ml(t)&&(t.__click=void 0,t.__className=void 0,t.__attributes=null,t.__style=void 0,t.__e=void 0),Ml(n)&&(n.__t=void 0)}}function ca(t=""){return document.createTextNode(t)}function Pn(t){return Jd.call(t)}function ps(t){return Yd.call(t)}function d(t,e){return Pn(t)}function ae(t,e=!1){{var n=Pn(t);return n instanceof Comment&&n.data===""?ps(n):n}}function m(t,e=1,n=!1){let a=t;for(;e--;)a=ps(a);return a}function Ff(t){t.textContent=""}function Xd(){return!1}function el(t,e,n){return document.createElementNS(e??zd,t,void 0)}function Vf(t,e){if(e){const n=document.body;t.autofocus=!0,Gn(()=>{document.activeElement===n&&t.focus()})}}let Al=!1;function Bf(){Al||(Al=!0,document.addEventListener("reset",t=>{Promise.resolve().then(()=>{var e;if(!t.defaultPrevented)for(const n of t.target.elements)(e=n.__on_r)==null||e.call(n)})},{capture:!0}))}function Ks(t){var e=Jt,n=Yt;Dn(null),Rn(null);try{return t()}finally{Dn(e),Rn(n)}}function Qd(t,e,n,a=n){t.addEventListener(e,()=>Ks(n));const o=t.__on_r;o?t.__on_r=()=>{o(),a(!0)}:t.__on_r=()=>a(!0),Bf()}function Zd(t){Yt===null&&(Jt===null&&Xu(),Yu()),Ra&&Ju()}function qf(t,e){var n=e.last;n===null?e.last=e.first=t:(n.next=t,t.prev=n,e.last=t)}function Qn(t,e){var n=Yt;n!==null&&(n.f&cn)!==0&&(t|=cn);var a={ctx:Wr,deps:null,nodes:null,f:t|Zr|Ln,first:null,fn:e,last:null,next:null,parent:n,b:n&&n.b,prev:null,teardown:null,wv:0,ac:null},o=a;if((t&Po)!==0)To!==null?To.push(a):ia(a);else if(e!==null){try{Io(a)}catch(s){throw en(a),s}o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&Oo)===0&&(o=o.first,(t&Ba)!==0&&(t&ba)!==0&&o!==null&&(o.f|=ba))}if(o!==null&&(o.parent=n,n!==null&&qf(o,n),Jt!==null&&(Jt.f&tn)!==0&&(t&fo)===0)){var i=Jt;(i.effects??(i.effects=[])).push(o)}return a}function tl(){return Jt!==null&&!Wn}function Gs(t){const e=Qn(io,null);return Tr(e,Qr),e.teardown=t,e}function gr(t){Zd();var e=Yt.f,n=!Jt&&(e&Xn)!==0&&(e&Lo)===0;if(n){var a=Wr;(a.e??(a.e=[])).push(t)}else return ec(t)}function ec(t){return Qn(Po|yd,t)}function Hf(t){return Zd(),Qn(io|yd,t)}function Uf(t){ga.ensure();const e=Qn(fo|Oo,t);return(n={})=>new Promise(a=>{n.outro?ao(e,()=>{en(e),a(void 0)}):(en(e),a(void 0))})}function Js(t){return Qn(Po,t)}function Wf(t){return Qn(Yi|Oo,t)}function rl(t,e=0){return Qn(io|e,t)}function z(t,e=[],n=[],a=[]){Vd(a,e,n,o=>{Qn(io,()=>t(...o.map(r)))})}function vo(t,e=0){var n=Qn(Ba|e,t);return n}function tc(t,e=0){var n=Qn(Us|e,t);return n}function mn(t){return Qn(Xn|Oo,t)}function rc(t){var e=t.teardown;if(e!==null){const n=Ra,a=Jt;El(!0),Dn(null);try{e.call(null)}finally{El(n),Dn(a)}}}function nl(t,e=!1){var n=t.first;for(t.first=t.last=null;n!==null;){const o=n.ac;o!==null&&Ks(()=>{o.abort(Ya)});var a=n.next;(n.f&fo)!==0?n.parent=null:en(n,e),n=a}}function Kf(t){for(var e=t.first;e!==null;){var n=e.next;(e.f&Xn)===0&&en(e),e=n}}function en(t,e=!0){var n=!1;(e||(t.f&Uu)!==0)&&t.nodes!==null&&t.nodes.end!==null&&(nc(t.nodes.start,t.nodes.end),n=!0),nl(t,e&&!n),is(t,0),Tr(t,la);var a=t.nodes&&t.nodes.t;if(a!==null)for(const i of a)i.stop();rc(t);var o=t.parent;o!==null&&o.first!==null&&ac(t),t.next=t.prev=t.teardown=t.ctx=t.deps=t.fn=t.nodes=t.ac=null}function nc(t,e){for(;t!==null;){var n=t===e?null:ps(t);t.remove(),t=n}}function ac(t){var e=t.parent,n=t.prev,a=t.next;n!==null&&(n.next=a),a!==null&&(a.prev=n),e!==null&&(e.first===t&&(e.first=a),e.last===t&&(e.last=n))}function ao(t,e,n=!0){var a=[];oc(t,a,!0);var o=()=>{n&&en(t),e&&e()},i=a.length;if(i>0){var s=()=>--i||o();for(var l of a)l.out(s)}else o()}function oc(t,e,n){if((t.f&cn)===0){t.f^=cn;var a=t.nodes&&t.nodes.t;if(a!==null)for(const l of a)(l.is_global||n)&&e.push(l);for(var o=t.first;o!==null;){var i=o.next,s=(o.f&ba)!==0||(o.f&Xn)!==0&&(t.f&Ba)!==0;oc(o,e,s?n:!1),o=i}}}function al(t){sc(t,!0)}function sc(t,e){if((t.f&cn)!==0){t.f^=cn;for(var n=t.first;n!==null;){var a=n.next,o=(n.f&ba)!==0||(n.f&Xn)!==0;sc(n,o?e:!1),n=a}var i=t.nodes&&t.nodes.t;if(i!==null)for(const s of i)(s.is_global||e)&&s.in()}}function ol(t,e){if(t.nodes)for(var n=t.nodes.start,a=t.nodes.end;n!==null;){var o=n===a?null:ps(n);e.append(n),n=o}}let zs=!1,Ra=!1;function El(t){Ra=t}let Jt=null,Wn=!1;function Dn(t){Jt=t}let Yt=null;function Rn(t){Yt=t}let On=null;function ic(t){Jt!==null&&(On===null?On=[t]:On.push(t))}let hn=null,$n=0,En=null;function Gf(t){En=t}let lc=1,Qa=0,oo=Qa;function Nl(t){oo=t}function dc(){return++lc}function hs(t){var e=t.f;if((e&Zr)!==0)return!0;if(e&tn&&(t.f&=~lo),(e&Yn)!==0){for(var n=t.deps,a=n.length,o=0;o<a;o++){var i=n[o];if(hs(i)&&qd(i),i.wv>t.wv)return!0}(e&Ln)!==0&&Xr===null&&Tr(t,Qr)}return!1}function cc(t,e,n=!0){var a=t.reactions;if(a!==null&&!(On!==null&&Mo.call(On,t)))for(var o=0;o<a.length;o++){var i=a[o];(i.f&tn)!==0?cc(i,e,!1):e===i&&(n?Tr(i,Zr):(i.f&Qr)!==0&&Tr(i,Yn),ia(i))}}function uc(t){var C;var e=hn,n=$n,a=En,o=Jt,i=On,s=Wr,l=Wn,u=oo,f=t.f;hn=null,$n=0,En=null,Jt=(f&(Xn|fo))===0?t:null,On=null,zo(t.ctx),Wn=!1,oo=++Qa,t.ac!==null&&(Ks(()=>{t.ac.abort(Ya)}),t.ac=null);try{t.f|=xi;var p=t.fn,_=p();t.f|=Lo;var x=t.deps,b=Et==null?void 0:Et.is_fork;if(hn!==null){var k;if(b||is(t,$n),x!==null&&$n>0)for(x.length=$n+hn.length,k=0;k<hn.length;k++)x[$n+k]=hn[k];else t.deps=x=hn;if(tl()&&(t.f&Ln)!==0)for(k=$n;k<x.length;k++)((C=x[k]).reactions??(C.reactions=[])).push(t)}else!b&&x!==null&&$n<x.length&&(is(t,$n),x.length=$n);if(Do()&&En!==null&&!Wn&&x!==null&&(t.f&(tn|Yn|Zr))===0)for(k=0;k<En.length;k++)cc(En[k],t);if(o!==null&&o!==t){if(Qa++,o.deps!==null)for(let g=0;g<n;g+=1)o.deps[g].rv=Qa;if(e!==null)for(const g of e)g.rv=Qa;En!==null&&(a===null?a=En:a.push(...En))}return(t.f&Oa)!==0&&(t.f^=Oa),_}catch(g){return Nd(g)}finally{t.f^=xi,hn=e,$n=n,En=a,Jt=o,On=i,zo(s),Wn=l,oo=u}}function Jf(t,e){let n=e.reactions;if(n!==null){var a=Ru.call(n,t);if(a!==-1){var o=n.length-1;o===0?n=e.reactions=null:(n[a]=n[o],n.pop())}}if(n===null&&(e.f&tn)!==0&&(hn===null||!Mo.call(hn,e))){var i=e;(i.f&Ln)!==0&&(i.f^=Ln,i.f&=~lo),Xi(i),Of(i),is(i,0)}}function is(t,e){var n=t.deps;if(n!==null)for(var a=e;a<n.length;a++)Jf(t,n[a])}function Io(t){var e=t.f;if((e&la)===0){Tr(t,Qr);var n=Yt,a=zs;Yt=t,zs=!0;try{(e&(Ba|Us))!==0?Kf(t):nl(t),rc(t);var o=uc(t);t.teardown=typeof o=="function"?o:null,t.wv=lc;var i;pi&&_f&&(t.f&Zr)!==0&&t.deps}finally{zs=a,Yt=n}}}async function fc(){await Promise.resolve(),Od()}function r(t){var e=t.f,n=(e&tn)!==0;if(Jt!==null&&!Wn){var a=Yt!==null&&(Yt.f&la)!==0;if(!a&&(On===null||!Mo.call(On,t))){var o=Jt.deps;if((Jt.f&xi)!==0)t.rv<Qa&&(t.rv=Qa,hn===null&&o!==null&&o[$n]===t?$n++:hn===null?hn=[t]:hn.push(t));else{(Jt.deps??(Jt.deps=[])).push(t);var i=t.reactions;i===null?t.reactions=[Jt]:Mo.call(i,Jt)||i.push(Jt)}}}if(Ra&&Da.has(t))return Da.get(t);if(n){var s=t;if(Ra){var l=s.v;return((s.f&Qr)===0&&s.reactions!==null||pc(s))&&(l=Zi(s)),Da.set(s,l),l}var u=(s.f&Ln)===0&&!Wn&&Jt!==null&&(zs||(Jt.f&Ln)!==0),f=(s.f&Lo)===0;hs(s)&&(u&&(s.f|=Ln),qd(s)),u&&!f&&(Hd(s),vc(s))}if(Xr!=null&&Xr.has(t))return Xr.get(t);if((t.f&Oa)!==0)throw t.v;return t.v}function vc(t){if(t.f|=Ln,t.deps!==null)for(const e of t.deps)(e.reactions??(e.reactions=[])).push(t),(e.f&tn)!==0&&(e.f&Ln)===0&&(Hd(e),vc(e))}function pc(t){if(t.v===jr)return!0;if(t.deps===null)return!1;for(const e of t.deps)if(Da.has(e)||(e.f&tn)!==0&&pc(e))return!0;return!1}function co(t){var e=Wn;try{return Wn=!0,t()}finally{Wn=e}}function Ga(t){if(!(typeof t!="object"||!t||t instanceof EventTarget)){if(da in t)Si(t);else if(!Array.isArray(t))for(let e in t){const n=t[e];typeof n=="object"&&n&&da in n&&Si(n)}}}function Si(t,e=new Set){if(typeof t=="object"&&t!==null&&!(t instanceof EventTarget)&&!e.has(t)){e.add(t),t instanceof Date&&t.getTime();for(let a in t)try{Si(t[a],e)}catch{}const n=Gi(t);if(n!==Object.prototype&&n!==Array.prototype&&n!==Map.prototype&&n!==Set.prototype&&n!==Date.prototype){const a=bd(n);for(let o in a){const i=a[o].get;if(i)try{i.call(t)}catch{}}}}}function Yf(t){return t.endsWith("capture")&&t!=="gotpointercapture"&&t!=="lostpointercapture"}const Xf=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function Qf(t){return Xf.includes(t)}const Zf={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function ev(t){return t=t.toLowerCase(),Zf[t]??t}const tv=["touchstart","touchmove"];function rv(t){return tv.includes(t)}const Za=Symbol("events"),hc=new Set,Mi=new Set;function mc(t,e,n,a={}){function o(i){if(a.capture||zi.call(e,i),!i.cancelBubble)return Ks(()=>n==null?void 0:n.call(this,i))}return t.startsWith("pointer")||t.startsWith("touch")||t==="wheel"?Gn(()=>{e.addEventListener(t,o,a)}):e.addEventListener(t,o,a),o}function xn(t,e,n,a,o){var i={capture:a,passive:o},s=mc(t,e,n,i);(e===document.body||e===window||e===document||e instanceof HTMLMediaElement)&&Gs(()=>{e.removeEventListener(t,s,i)})}function he(t,e,n){(e[Za]??(e[Za]={}))[t]=n}function Kr(t){for(var e=0;e<t.length;e++)hc.add(t[e]);for(var n of Mi)n(t)}let Pl=null;function zi(t){var g,y;var e=this,n=e.ownerDocument,a=t.type,o=((g=t.composedPath)==null?void 0:g.call(t))||[],i=o[0]||t.target;Pl=t;var s=0,l=Pl===t&&t[Za];if(l){var u=o.indexOf(l);if(u!==-1&&(e===document||e===window)){t[Za]=e;return}var f=o.indexOf(e);if(f===-1)return;u<=f&&(s=u)}if(i=o[s]||t.target,i!==e){ju(t,"currentTarget",{configurable:!0,get(){return i||n}});var p=Jt,_=Yt;Dn(null),Rn(null);try{for(var x,b=[];i!==null;){var k=i.assignedSlot||i.parentNode||i.host||null;try{var C=(y=i[Za])==null?void 0:y[a];C!=null&&(!i.disabled||t.target===i)&&C.call(i,t)}catch(I){x?b.push(I):x=I}if(t.cancelBubble||k===e||k===null)break;i=k}if(x){for(let I of b)queueMicrotask(()=>{throw I});throw x}}finally{t[Za]=e,delete t.currentTarget,Dn(p),Rn(_)}}}var gd;const ri=((gd=globalThis==null?void 0:globalThis.window)==null?void 0:gd.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:t=>t});function nv(t){return(ri==null?void 0:ri.createHTML(t))??t}function xc(t){var e=el("template");return e.innerHTML=nv(t.replaceAll("<!>","<!---->")),e.content}function ja(t,e){var n=Yt;n.nodes===null&&(n.nodes={start:t,end:e,a:null,t:null})}function h(t,e){var n=(e&Md)!==0,a=(e&vf)!==0,o,i=!t.startsWith("<!>");return()=>{o===void 0&&(o=xc(i?t:"<!>"+t),n||(o=Pn(o)));var s=a||Gd?document.importNode(o,!0):o.cloneNode(!0);if(n){var l=Pn(s),u=s.lastChild;ja(l,u)}else ja(s,s);return s}}function av(t,e,n="svg"){var a=!t.startsWith("<!>"),o=(e&Md)!==0,i=`<${n}>${a?t:"<!>"+t}</${n}>`,s;return()=>{if(!s){var l=xc(i),u=Pn(l);if(o)for(s=document.createDocumentFragment();Pn(u);)s.appendChild(Pn(u));else s=Pn(u)}var f=s.cloneNode(!0);if(o){var p=Pn(f),_=f.lastChild;ja(p,_)}else ja(f,f);return f}}function ms(t,e){return av(t,e,"svg")}function oa(t=""){{var e=ca(t+"");return ja(e,e),e}}function Ce(){var t=document.createDocumentFragment(),e=document.createComment(""),n=ca();return t.append(e,n),ja(e,n),t}function c(t,e){t!==null&&t.before(e)}function T(t,e){var n=e==null?"":typeof e=="object"?`${e}`:e;n!==(t.__t??(t.__t=t.nodeValue))&&(t.__t=n,t.nodeValue=`${n}`)}function ov(t,e){return sv(t,e)}const bs=new Map;function sv(t,{target:e,anchor:n,props:a={},events:o,context:i,intro:s=!0,transformError:l}){jf();var u=void 0,f=Uf(()=>{var p=n??e.appendChild(ca());Mf(p,{pending:()=>{}},b=>{Ir({});var k=Wr;i&&(k.c=i),o&&(a.$$events=o),u=t(b,a)||{},Ar()},l);var _=new Set,x=b=>{for(var k=0;k<b.length;k++){var C=b[k];if(!_.has(C)){_.add(C);var g=rv(C);for(const O of[e,document]){var y=bs.get(O);y===void 0&&(y=new Map,bs.set(O,y));var I=y.get(C);I===void 0?(O.addEventListener(C,zi,{passive:g}),y.set(C,1)):y.set(C,I+1)}}}};return x(Hs(hc)),Mi.add(x),()=>{var g;for(var b of _)for(const y of[e,document]){var k=bs.get(y),C=k.get(b);--C==0?(y.removeEventListener(b,zi),k.delete(b),k.size===0&&bs.delete(y)):k.set(b,C)}Mi.delete(x),p!==n&&((g=p.parentNode)==null||g.removeChild(p))}});return iv.set(u,f),u}let iv=new WeakMap;var Un,aa,Mn,no,cs,us,qs;class xs{constructor(e,n=!0){Bn(this,"anchor");Qt(this,Un,new Map);Qt(this,aa,new Map);Qt(this,Mn,new Map);Qt(this,no,new Set);Qt(this,cs,!0);Qt(this,us,e=>{if(se(this,Un).has(e)){var n=se(this,Un).get(e),a=se(this,aa).get(n);if(a)al(a),se(this,no).delete(n);else{var o=se(this,Mn).get(n);o&&(o.effect.f&cn)===0&&(se(this,aa).set(n,o.effect),se(this,Mn).delete(n),o.fragment.lastChild.remove(),this.anchor.before(o.fragment),a=o.effect)}for(const[i,s]of se(this,Un)){if(se(this,Un).delete(i),i===e)break;const l=se(this,Mn).get(s);l&&(en(l.effect),se(this,Mn).delete(s))}for(const[i,s]of se(this,aa)){if(i===n||se(this,no).has(i)||(s.f&cn)!==0)continue;const l=()=>{if(Array.from(se(this,Un).values()).includes(i)){var f=document.createDocumentFragment();ol(s,f),f.append(ca()),se(this,Mn).set(i,{effect:s,fragment:f})}else en(s);se(this,no).delete(i),se(this,aa).delete(i)};se(this,cs)||!a?(se(this,no).add(i),ao(s,l,!1)):l()}}});Qt(this,qs,e=>{se(this,Un).delete(e);const n=Array.from(se(this,Un).values());for(const[a,o]of se(this,Mn))n.includes(a)||(en(o.effect),se(this,Mn).delete(a))});this.anchor=e,Vt(this,cs,n)}ensure(e,n){var a=Et,o=Xd();if(n&&!se(this,aa).has(e)&&!se(this,Mn).has(e))if(o){var i=document.createDocumentFragment(),s=ca();i.append(s),se(this,Mn).set(e,{effect:mn(()=>n(s)),fragment:i})}else se(this,aa).set(e,mn(()=>n(this.anchor)));if(se(this,Un).set(a,e),o){for(const[l,u]of se(this,aa))l===e?a.unskip_effect(u):a.skip_effect(u);for(const[l,u]of se(this,Mn))l===e?a.unskip_effect(u.effect):a.skip_effect(u.effect);a.oncommit(se(this,us)),a.ondiscard(se(this,qs))}else se(this,us).call(this,a)}}Un=new WeakMap,aa=new WeakMap,Mn=new WeakMap,no=new WeakMap,cs=new WeakMap,us=new WeakMap,qs=new WeakMap;const lv=0,Ll=1,dv=2;function Ti(t,e,n,a,o){var i=Do(),s=jr,l=i?ua(s):$i(s,!1,!1),u=i?ua(s):$i(s,!1,!1),f=new xs(t);vo(()=>{var p=e(),_=!1;if(qu(p)){var x=Bd(),b=!1;const k=C=>{if(!_){b=!0,x(!1),ga.ensure();try{C()}finally{Es(!1),xo||Od()}}};p.then(C=>{k(()=>{_a(l,C),f.ensure(Ll,a&&(g=>a(g,l)))})},C=>{k(()=>{if(_a(u,C),f.ensure(dv,o&&(g=>o(g,u))),!o)throw u.v})}),Gn(()=>{b||k(()=>{f.ensure(lv,n)})})}else _a(l,p),f.ensure(Ll,a&&(k=>a(k,l)));return()=>{_=!0}})}function $(t,e,n=!1){var a=new xs(t),o=n?ba:0;function i(s,l){a.ensure(s,l)}vo(()=>{var s=!1;e((l,u=0)=>{s=!0,i(u,l)}),s||i(-1,null)},o)}function Ne(t,e){return e}function cv(t,e,n){for(var a=[],o=e.length,i,s=e.length,l=0;l<o;l++){let _=e[l];ao(_,()=>{if(i){if(i.pending.delete(_),i.done.add(_),i.pending.size===0){var x=t.outrogroups;Ii(t,Hs(i.done)),x.delete(i),x.size===0&&(t.outrogroups=null)}}else s-=1},!1)}if(s===0){var u=a.length===0&&n!==null;if(u){var f=n,p=f.parentNode;Ff(p),p.append(f),t.items.clear()}Ii(t,e,!u)}else i={pending:new Set(e),done:new Set},(t.outrogroups??(t.outrogroups=new Set)).add(i)}function Ii(t,e,n=!0){var a;if(t.pending.size>0){a=new Set;for(const s of t.pending.values())for(const l of s)a.add(t.items.get(l).e)}for(var o=0;o<e.length;o++){var i=e[o];if(a!=null&&a.has(i)){i.f|=sa;const s=document.createDocumentFragment();ol(i,s)}else en(e[o],n)}}var Ol;function Ae(t,e,n,a,o,i=null){var s=t,l=new Map,u=(e&$d)!==0;if(u){var f=t;s=f.appendChild(ca())}var p=null,_=Qi(()=>{var O=n();return Ki(O)?O:O==null?[]:Hs(O)}),x,b=new Map,k=!0;function C(O){(I.effect.f&la)===0&&(I.pending.delete(O),I.fallback=p,uv(I,x,s,e,a),p!==null&&(x.length===0?(p.f&sa)===0?al(p):(p.f^=sa,Qo(p,null,s)):ao(p,()=>{p=null})))}function g(O){I.pending.delete(O)}var y=vo(()=>{x=r(_);for(var O=x.length,M=new Set,ee=Et,fe=Xd(),L=0;L<O;L+=1){var S=x[L],X=a(S,L),G=k?null:l.get(X);G?(G.v&&_a(G.v,S),G.i&&_a(G.i,L),fe&&ee.unskip_effect(G.e)):(G=fv(l,k?s:Ol??(Ol=ca()),S,X,L,o,e,n),k||(G.e.f|=sa),l.set(X,G)),M.add(X)}if(O===0&&i&&!p&&(k?p=mn(()=>i(s)):(p=mn(()=>i(Ol??(Ol=ca()))),p.f|=sa)),O>M.size&&Gu(),!k)if(b.set(ee,M),fe){for(const[me,V]of l)M.has(me)||ee.skip_effect(V.e);ee.oncommit(C),ee.ondiscard(g)}else C(ee);r(_)}),I={effect:y,items:l,pending:b,outrogroups:null,fallback:p};k=!1}function Uo(t){for(;t!==null&&(t.f&Xn)===0;)t=t.next;return t}function uv(t,e,n,a,o){var G,me,V,ze,j,B,le,we,U;var i=(a&sf)!==0,s=e.length,l=t.items,u=Uo(t.effect.first),f,p=null,_,x=[],b=[],k,C,g,y;if(i)for(y=0;y<s;y+=1)k=e[y],C=o(k,y),g=l.get(C).e,(g.f&sa)===0&&((me=(G=g.nodes)==null?void 0:G.a)==null||me.measure(),(_??(_=new Set)).add(g));for(y=0;y<s;y+=1){if(k=e[y],C=o(k,y),g=l.get(C).e,t.outrogroups!==null)for(const ne of t.outrogroups)ne.pending.delete(g),ne.done.delete(g);if((g.f&sa)!==0)if(g.f^=sa,g===u)Qo(g,null,n);else{var I=p?p.next:u;g===t.effect.last&&(t.effect.last=g.prev),g.prev&&(g.prev.next=g.next),g.next&&(g.next.prev=g.prev),$a(t,p,g),$a(t,g,I),Qo(g,I,n),p=g,x=[],b=[],u=Uo(p.next);continue}if((g.f&cn)!==0&&(al(g),i&&((ze=(V=g.nodes)==null?void 0:V.a)==null||ze.unfix(),(_??(_=new Set)).delete(g))),g!==u){if(f!==void 0&&f.has(g)){if(x.length<b.length){var O=b[0],M;p=O.prev;var ee=x[0],fe=x[x.length-1];for(M=0;M<x.length;M+=1)Qo(x[M],O,n);for(M=0;M<b.length;M+=1)f.delete(b[M]);$a(t,ee.prev,fe.next),$a(t,p,ee),$a(t,fe,O),u=O,p=fe,y-=1,x=[],b=[]}else f.delete(g),Qo(g,u,n),$a(t,g.prev,g.next),$a(t,g,p===null?t.effect.first:p.next),$a(t,p,g),p=g;continue}for(x=[],b=[];u!==null&&u!==g;)(f??(f=new Set)).add(u),b.push(u),u=Uo(u.next);if(u===null)continue}(g.f&sa)===0&&x.push(g),p=g,u=Uo(g.next)}if(t.outrogroups!==null){for(const ne of t.outrogroups)ne.pending.size===0&&(Ii(t,Hs(ne.done)),(j=t.outrogroups)==null||j.delete(ne));t.outrogroups.size===0&&(t.outrogroups=null)}if(u!==null||f!==void 0){var L=[];if(f!==void 0)for(g of f)(g.f&cn)===0&&L.push(g);for(;u!==null;)(u.f&cn)===0&&u!==t.fallback&&L.push(u),u=Uo(u.next);var S=L.length;if(S>0){var X=(a&$d)!==0&&s===0?n:null;if(i){for(y=0;y<S;y+=1)(le=(B=L[y].nodes)==null?void 0:B.a)==null||le.measure();for(y=0;y<S;y+=1)(U=(we=L[y].nodes)==null?void 0:we.a)==null||U.fix()}cv(t,L,X)}}i&&Gn(()=>{var ne,N;if(_!==void 0)for(g of _)(N=(ne=g.nodes)==null?void 0:ne.a)==null||N.apply()})}function fv(t,e,n,a,o,i,s,l){var u=(s&af)!==0?(s&lf)===0?$i(n,!1,!1):ua(n):null,f=(s&of)!==0?ua(o):null;return{v:u,i:f,e:mn(()=>(i(e,u??n,f??o,l),()=>{t.delete(a)}))}}function Qo(t,e,n){if(t.nodes)for(var a=t.nodes.start,o=t.nodes.end,i=e&&(e.f&sa)===0?e.nodes.start:n;a!==null;){var s=ps(a);if(i.before(a),a===o)return;a=s}}function $a(t,e,n){e===null?t.effect.first=n:e.next=n,n===null?t.effect.last=e:n.prev=e}function Kn(t,e,n=!1,a=!1,o=!1){var i=t,s="";z(()=>{var l=Yt;if(s!==(s=e()??"")&&(l.nodes!==null&&(nc(l.nodes.start,l.nodes.end),l.nodes=null),s!=="")){var u=n?Td:a?pf:void 0,f=el(n?"svg":a?"math":"template",u);f.innerHTML=s;var p=n||a?f:f.content;if(ja(Pn(p),p.lastChild),n||a)for(;Pn(p);)i.before(Pn(p));else i.before(p)}})}function pt(t,e,n,a,o){var l;var i=(l=e.$$slots)==null?void 0:l[n],s=!1;i===!0&&(i=e.children,s=!0),i===void 0||i(t,s?()=>a:a)}function Ai(t,e,...n){var a=new xs(t);vo(()=>{const o=e()??null;a.ensure(o,o&&(i=>o(i,...n)))},ba)}function Ao(t,e,n){var a=new xs(t);vo(()=>{var o=e()??null;a.ensure(o,o&&(i=>n(i,o)))},ba)}function vv(t,e,n,a,o,i){var s=null,l=t,u=new xs(l,!1);vo(()=>{const f=e()||null;var p=Td;if(f===null){u.ensure(null,null);return}return u.ensure(f,_=>{if(f){if(s=el(f,p),ja(s,s),a){var x=s.appendChild(ca());a(s,x)}Yt.nodes.end=s,_.before(s)}}),()=>{}},ba),Gs(()=>{})}function pv(t,e){var n=void 0,a;tc(()=>{n!==(n=e())&&(a&&(en(a),a=null),n&&(a=mn(()=>{Js(()=>n(t))})))})}function gc(t){var e,n,a="";if(typeof t=="string"||typeof t=="number")a+=t;else if(typeof t=="object")if(Array.isArray(t)){var o=t.length;for(e=0;e<o;e++)t[e]&&(n=gc(t[e]))&&(a&&(a+=" "),a+=n)}else for(n in t)t[n]&&(a&&(a+=" "),a+=n);return a}function _c(){for(var t,e,n=0,a="",o=arguments.length;n<o;n++)(t=arguments[n])&&(e=gc(t))&&(a&&(a+=" "),a+=e);return a}function xr(t){return typeof t=="object"?_c(t):t??""}const Dl=[...` 	
\r\f \v\uFEFF`];function hv(t,e,n){var a=t==null?"":""+t;if(e&&(a=a?a+" "+e:e),n){for(var o of Object.keys(n))if(n[o])a=a?a+" "+o:o;else if(a.length)for(var i=o.length,s=0;(s=a.indexOf(o,s))>=0;){var l=s+i;(s===0||Dl.includes(a[s-1]))&&(l===a.length||Dl.includes(a[l]))?a=(s===0?"":a.substring(0,s))+a.substring(l+1):s=l}}return a===""?null:a}function Rl(t,e=!1){var n=e?" !important;":";",a="";for(var o of Object.keys(t)){var i=t[o];i!=null&&i!==""&&(a+=" "+o+": "+i+n)}return a}function ni(t){return t[0]!=="-"||t[1]!=="-"?t.toLowerCase():t}function mv(t,e){if(e){var n="",a,o;if(Array.isArray(e)?(a=e[0],o=e[1]):a=e,t){t=String(t).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var i=!1,s=0,l=!1,u=[];a&&u.push(...Object.keys(a).map(ni)),o&&u.push(...Object.keys(o).map(ni));var f=0,p=-1;const C=t.length;for(var _=0;_<C;_++){var x=t[_];if(l?x==="/"&&t[_-1]==="*"&&(l=!1):i?i===x&&(i=!1):x==="/"&&t[_+1]==="*"?l=!0:x==='"'||x==="'"?i=x:x==="("?s++:x===")"&&s--,!l&&i===!1&&s===0){if(x===":"&&p===-1)p=_;else if(x===";"||_===C-1){if(p!==-1){var b=ni(t.substring(f,p).trim());if(!u.includes(b)){x!==";"&&_++;var k=t.substring(f,_).trim();n+=" "+k+";"}}f=_+1,p=-1}}}}return a&&(n+=Rl(a)),o&&(n+=Rl(o,!0)),n=n.trim(),n===""?null:n}return t==null?null:String(t)}function Ue(t,e,n,a,o,i){var s=t.__className;if(s!==n||s===void 0){var l=hv(n,a,i);l==null?t.removeAttribute("class"):e?t.className=l:t.setAttribute("class",l),t.__className=n}else if(i&&o!==i)for(var u in i){var f=!!i[u];(o==null||f!==!!o[u])&&t.classList.toggle(u,f)}return i}function ai(t,e={},n,a){for(var o in n){var i=n[o];e[o]!==i&&(n[o]==null?t.style.removeProperty(o):t.style.setProperty(o,i,a))}}function Eo(t,e,n,a){var o=t.__style;if(o!==e){var i=mv(e,a);i==null?t.removeAttribute("style"):t.style.cssText=i,t.__style=e}else a&&(Array.isArray(a)?(ai(t,n==null?void 0:n[0],a[0]),ai(t,n==null?void 0:n[1],a[1],"important")):ai(t,n,a));return a}function Ps(t,e,n=!1){if(t.multiple){if(e==null)return;if(!Ki(e))return mf();for(var a of t.options)a.selected=e.includes(ns(a));return}for(a of t.options){var o=ns(a);if(Rf(o,e)){a.selected=!0;return}}(!n||e!==void 0)&&(t.selectedIndex=-1)}function bc(t){var e=new MutationObserver(()=>{Ps(t,t.__value)});e.observe(t,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Gs(()=>{e.disconnect()})}function jl(t,e,n=e){var a=new WeakSet,o=!0;Qd(t,"change",i=>{var s=i?"[selected]":":checked",l;if(t.multiple)l=[].map.call(t.querySelectorAll(s),ns);else{var u=t.querySelector(s)??t.querySelector("option:not([disabled])");l=u&&ns(u)}n(l),Et!==null&&a.add(Et)}),Js(()=>{var i=e();if(t===document.activeElement){var s=As??Et;if(a.has(s))return}if(Ps(t,i,o),o&&i===void 0){var l=t.querySelector(":checked");l!==null&&(i=ns(l),n(i))}t.__value=i,o=!1}),bc(t)}function ns(t){return"__value"in t?t.__value:t.value}const Wo=Symbol("class"),Ko=Symbol("style"),wc=Symbol("is custom element"),yc=Symbol("is html"),xv=Cd?"option":"OPTION",gv=Cd?"select":"SELECT";function _v(t,e){e?t.hasAttribute("selected")||t.setAttribute("selected",""):t.removeAttribute("selected")}function ir(t,e,n,a){var o=kc(t);o[e]!==(o[e]=n)&&(e==="loading"&&(t[Wu]=n),n==null?t.removeAttribute(e):typeof n!="string"&&Cc(t).includes(e)?t[e]=n:t.setAttribute(e,n))}function bv(t,e,n,a,o=!1,i=!1){var s=kc(t),l=s[wc],u=!s[yc],f=e||{},p=t.nodeName===xv;for(var _ in e)_ in n||(n[_]=null);n.class?n.class=xr(n.class):n[Wo]&&(n.class=null),n[Ko]&&(n.style??(n.style=null));var x=Cc(t);for(const O in n){let M=n[O];if(p&&O==="value"&&M==null){t.value=t.__value="",f[O]=M;continue}if(O==="class"){var b=t.namespaceURI==="http://www.w3.org/1999/xhtml";Ue(t,b,M,a,e==null?void 0:e[Wo],n[Wo]),f[O]=M,f[Wo]=n[Wo];continue}if(O==="style"){Eo(t,M,e==null?void 0:e[Ko],n[Ko]),f[O]=M,f[Ko]=n[Ko];continue}var k=f[O];if(!(M===k&&!(M===void 0&&t.hasAttribute(O)))){f[O]=M;var C=O[0]+O[1];if(C!=="$$")if(C==="on"){const ee={},fe="$$"+O;let L=O.slice(2);var g=Qf(L);if(Yf(L)&&(L=L.slice(0,-7),ee.capture=!0),!g&&k){if(M!=null)continue;t.removeEventListener(L,f[fe],ee),f[fe]=null}if(g)he(L,t,M),Kr([L]);else if(M!=null){let S=function(X){f[O].call(this,X)};f[fe]=mc(L,t,S,ee)}}else if(O==="style")ir(t,O,M);else if(O==="autofocus")Vf(t,!!M);else if(!l&&(O==="__value"||O==="value"&&M!=null))t.value=t.__value=M;else if(O==="selected"&&p)_v(t,M);else{var y=O;u||(y=ev(y));var I=y==="defaultValue"||y==="defaultChecked";if(M==null&&!l&&!I)if(s[O]=null,y==="value"||y==="checked"){let ee=t;const fe=e===void 0;if(y==="value"){let L=ee.defaultValue;ee.removeAttribute(y),ee.defaultValue=L,ee.value=ee.__value=fe?L:null}else{let L=ee.defaultChecked;ee.removeAttribute(y),ee.defaultChecked=L,ee.checked=fe?L:!1}}else t.removeAttribute(O);else I||x.includes(y)&&(l||typeof M!="string")?(t[y]=M,y in s&&(s[y]=jr)):typeof M!="function"&&ir(t,y,M)}}}return f}function Ls(t,e,n=[],a=[],o=[],i,s=!1,l=!1){Vd(o,n,a,u=>{var f=void 0,p={},_=t.nodeName===gv,x=!1;if(tc(()=>{var k=e(...u.map(r)),C=bv(t,f,k,i,s,l);x&&_&&"value"in k&&Ps(t,k.value);for(let y of Object.getOwnPropertySymbols(p))k[y]||en(p[y]);for(let y of Object.getOwnPropertySymbols(k)){var g=k[y];y.description===hf&&(!f||g!==f[y])&&(p[y]&&en(p[y]),p[y]=mn(()=>pv(t,()=>g))),C[y]=g}f=C}),_){var b=t;Js(()=>{Ps(b,f.value,!0),bc(b)})}x=!0})}function kc(t){return t.__attributes??(t.__attributes={[wc]:t.nodeName.includes("-"),[yc]:t.namespaceURI===zd})}var Fl=new Map;function Cc(t){var e=t.getAttribute("is")||t.nodeName,n=Fl.get(e);if(n)return n;Fl.set(e,n=[]);for(var a,o=t,i=Element.prototype;i!==o;){a=bd(o);for(var s in a)a[s].set&&n.push(s);o=Gi(o)}return n}function Ea(t,e,n=e){var a=new WeakSet;Qd(t,"input",async o=>{var i=o?t.defaultValue:t.value;if(i=oi(t)?si(i):i,n(i),Et!==null&&a.add(Et),await fc(),i!==(i=e())){var s=t.selectionStart,l=t.selectionEnd,u=t.value.length;if(t.value=i??"",l!==null){var f=t.value.length;s===l&&l===u&&f>u?(t.selectionStart=f,t.selectionEnd=f):(t.selectionStart=s,t.selectionEnd=Math.min(l,f))}}}),co(e)==null&&t.value&&(n(oi(t)?si(t.value):t.value),Et!==null&&a.add(Et)),rl(()=>{var o=e();if(t===document.activeElement){var i=As??Et;if(a.has(i))return}oi(t)&&o===si(t.value)||t.type==="date"&&!o&&!t.value||o!==t.value&&(t.value=o??"")})}function oi(t){var e=t.type;return e==="number"||e==="range"}function si(t){return t===""?null:+t}function Vl(t,e){return t===e||(t==null?void 0:t[da])===e}function Jn(t={},e,n,a){return Js(()=>{var o,i;return rl(()=>{o=i,i=[],co(()=>{t!==n(...i)&&(e(t,...i),o&&Vl(n(...o),t)&&e(null,...o))})}),()=>{Gn(()=>{i&&Vl(n(...i),t)&&e(null,...i)})}}),t}function wv(t=!1){const e=Wr,n=e.l.u;if(!n)return;let a=()=>Ga(e.s);if(t){let o=0,i={};const s=vs(()=>{let l=!1;const u=e.s;for(const f in u)u[f]!==i[f]&&(i[f]=u[f],l=!0);return l&&o++,o});a=()=>r(s)}n.b.length&&Hf(()=>{Bl(e,a),hi(n.b)}),gr(()=>{const o=co(()=>n.m.map(Hu));return()=>{for(const i of o)typeof i=="function"&&i()}}),n.a.length&&gr(()=>{Bl(e,a),hi(n.a)})}function Bl(t,e){if(t.l.s)for(const n of t.l.s)r(n);e()}let ws=!1;function yv(t){var e=ws;try{return ws=!1,[t(),ws]}finally{ws=e}}const kv={get(t,e){if(!t.exclude.includes(e))return t.props[e]},set(t,e){return!1},getOwnPropertyDescriptor(t,e){if(!t.exclude.includes(e)&&e in t.props)return{enumerable:!0,configurable:!0,value:t.props[e]}},has(t,e){return t.exclude.includes(e)?!1:e in t.props},ownKeys(t){return Reflect.ownKeys(t.props).filter(e=>!t.exclude.includes(e))}};function Cv(t,e,n){return new Proxy({props:t,exclude:e},kv)}const $v={get(t,e){if(!t.exclude.includes(e))return r(t.version),e in t.special?t.special[e]():t.props[e]},set(t,e,n){if(!(e in t.special)){var a=Yt;try{Rn(t.parent_effect),t.special[e]=je({get[e](){return t.props[e]}},e,Sd)}finally{Rn(a)}}return t.special[e](n),ts(t.version),!0},getOwnPropertyDescriptor(t,e){if(!t.exclude.includes(e)&&e in t.props)return{enumerable:!0,configurable:!0,value:t.props[e]}},deleteProperty(t,e){return t.exclude.includes(e)||(t.exclude.push(e),ts(t.version)),!0},has(t,e){return t.exclude.includes(e)?!1:e in t.props},ownKeys(t){return Reflect.ownKeys(t.props).filter(e=>!t.exclude.includes(e))}};function lt(t,e){return new Proxy({props:t,exclude:e,special:{},version:ua(0),parent_effect:Yt},$v)}const Sv={get(t,e){let n=t.props.length;for(;n--;){let a=t.props[n];if(Ho(a)&&(a=a()),typeof a=="object"&&a!==null&&e in a)return a[e]}},set(t,e,n){let a=t.props.length;for(;a--;){let o=t.props[a];Ho(o)&&(o=o());const i=La(o,e);if(i&&i.set)return i.set(n),!0}return!1},getOwnPropertyDescriptor(t,e){let n=t.props.length;for(;n--;){let a=t.props[n];if(Ho(a)&&(a=a()),typeof a=="object"&&a!==null&&e in a){const o=La(a,e);return o&&!o.configurable&&(o.configurable=!0),o}}},has(t,e){if(e===da||e===kd)return!1;for(let n of t.props)if(Ho(n)&&(n=n()),n!=null&&e in n)return!0;return!1},ownKeys(t){const e=[];for(let n of t.props)if(Ho(n)&&(n=n()),!!n){for(const a in n)e.includes(a)||e.push(a);for(const a of Object.getOwnPropertySymbols(n))e.includes(a)||e.push(a)}return e}};function ht(...t){return new Proxy({props:t},Sv)}function je(t,e,n,a){var O;var o=!fs||(n&cf)!==0,i=(n&uf)!==0,s=(n&ff)!==0,l=a,u=!0,f=()=>(u&&(u=!1,l=s?co(a):a),l),p;if(i){var _=da in t||kd in t;p=((O=La(t,e))==null?void 0:O.set)??(_&&e in t?M=>t[e]=M:void 0)}var x,b=!1;i?[x,b]=yv(()=>t[e]):x=t[e],x===void 0&&a!==void 0&&(x=f(),p&&(o&&Zu(),p(x)));var k;if(o?k=()=>{var M=t[e];return M===void 0?f():(u=!0,M)}:k=()=>{var M=t[e];return M!==void 0&&(l=void 0),M===void 0?l:M},o&&(n&Sd)===0)return k;if(p){var C=t.$$legacy;return(function(M,ee){return arguments.length>0?((!o||!ee||C||b)&&p(ee?k():M),M):k()})}var g=!1,y=((n&df)!==0?vs:Qi)(()=>(g=!1,k()));i&&r(y);var I=Yt;return(function(M,ee){if(arguments.length>0){const fe=ee?r(y):o&&i?Bt(M):M;return v(y,fe),g=!0,l!==void 0&&(l=fe),M}return Ra&&g||(I.f&la)!==0?y.v:r(y)})}const Mv="5";var _d;typeof window<"u"&&((_d=window.__svelte??(window.__svelte={})).v??(_d.v=new Set)).add(Mv);const Vr="";async function zv(){const t=await fetch(`${Vr}/api/status`);if(!t.ok)throw new Error("상태 확인 실패");return t.json()}async function Tv(t,e=null,n=null){const a={provider:t};e&&(a.model=e),n&&(a.api_key=n);const o=await fetch(`${Vr}/api/provider/validate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!o.ok)throw new Error("설정 실패");return o.json()}async function Iv(t){const e=await fetch(`${Vr}/api/models/${encodeURIComponent(t)}`);return e.ok?e.json():{models:[]}}function Av(t,{onProgress:e,onDone:n,onError:a}){const o=new AbortController;return fetch(`${Vr}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:t}),signal:o.signal}).then(async i=>{if(!i.ok){a==null||a("다운로드 실패");return}const s=i.body.getReader(),l=new TextDecoder;let u="";for(;;){const{done:f,value:p}=await s.read();if(f)break;u+=l.decode(p,{stream:!0});const _=u.split(`
`);u=_.pop()||"";for(const x of _)if(x.startsWith("data:"))try{const b=JSON.parse(x.slice(5).trim());b.total&&b.completed!==void 0?e==null||e({total:b.total,completed:b.completed,status:b.status}):b.status&&(e==null||e({status:b.status}))}catch{}}n==null||n()}).catch(i=>{i.name!=="AbortError"&&(a==null||a(i.message))}),{abort:()=>o.abort()}}async function Ev(){const t=await fetch(`${Vr}/api/codex/logout`,{method:"POST"});if(!t.ok)throw new Error("Codex 로그아웃 실패");return t.json()}async function Nv(t,e=null,n=null){let a=`${Vr}/api/export/excel/${encodeURIComponent(t)}`;const o=new URLSearchParams;n?o.set("template_id",n):e&&e.length>0&&o.set("modules",e.join(","));const i=o.toString();i&&(a+=`?${i}`);const s=await fetch(a);if(!s.ok){const x=await s.json().catch(()=>({}));throw new Error(x.detail||"Excel 다운로드 실패")}const l=await s.blob(),f=(s.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),p=f?decodeURIComponent(f[1]):`${t}.xlsx`,_=document.createElement("a");return _.href=URL.createObjectURL(l),_.download=p,_.click(),URL.revokeObjectURL(_.href),p}async function sl(t){const e=await fetch(`${Vr}/api/search?q=${encodeURIComponent(t)}`);if(!e.ok)throw new Error("검색 실패");return e.json()}async function Pv(t,e){const n=await fetch(`${Vr}/api/company/${t}/show/${encodeURIComponent(e)}/all`);if(!n.ok)throw new Error("company topic 일괄 조회 실패");return n.json()}async function Lv(t){const e=await fetch(`${Vr}/api/company/${t}/sections`);if(!e.ok)throw new Error("sections 조회 실패");return e.json()}async function Ov(t){const e=await fetch(`${Vr}/api/company/${t}/toc`);if(!e.ok)throw new Error("목차 조회 실패");return e.json()}async function ql(t,e,n=null){const a=n?`?period=${encodeURIComponent(n)}`:"",o=await fetch(`${Vr}/api/company/${t}/viewer/${encodeURIComponent(e)}${a}`);if(!o.ok)throw new Error("viewer 조회 실패");return o.json()}async function Dv(t,e){const n=await fetch(`${Vr}/api/company/${t}/diff/${encodeURIComponent(e)}/summary`);if(!n.ok)throw new Error("diff summary 조회 실패");return n.json()}async function $c(t,e,n,a){const o=new URLSearchParams({from:n,to:a}),i=await fetch(`${Vr}/api/company/${t}/diff/${encodeURIComponent(e)}?${o}`);if(!i.ok)throw new Error("topic diff 조회 실패");return i.json()}async function Rv(t,e){const n=new URLSearchParams({q:e}),a=await fetch(`${Vr}/api/company/${encodeURIComponent(t)}/search?${n}`);if(!a.ok)throw new Error("검색 실패");return a.json()}async function jv(t){const e=await fetch(`${Vr}/api/company/${encodeURIComponent(t)}/searchIndex`);if(!e.ok)throw new Error("검색 인덱스 조회 실패");return e.json()}async function Fv(t){const e=await fetch(`${Vr}/api/company/${encodeURIComponent(t)}/insights`);if(!e.ok)throw new Error("인사이트 조회 실패");return e.json()}async function Vv(t){const e=await fetch(`${Vr}/api/company/${encodeURIComponent(t)}/network`);if(!e.ok)throw new Error("네트워크 조회 실패");return e.json()}function Bv(t,e,{onContext:n,onChunk:a,onDone:o,onError:i,provider:s,model:l}={}){const u=new AbortController,f=new URLSearchParams;s&&f.set("provider",s),l&&f.set("model",l);const p=f.toString(),_=`${Vr}/api/company/${encodeURIComponent(t)}/summary/${encodeURIComponent(e)}${p?`?${p}`:""}`;return fetch(_,{signal:u.signal}).then(async x=>{if(!x.ok){i==null||i("요약 생성 실패");return}const b=x.body.getReader(),k=new TextDecoder;let C="",g=null;for(;;){const{done:y,value:I}=await b.read();if(y)break;C+=k.decode(I,{stream:!0});const O=C.split(`
`);C=O.pop()||"";for(const M of O)if(M.startsWith("event:"))g=M.slice(6).trim();else if(M.startsWith("data:")&&g){try{const ee=JSON.parse(M.slice(5).trim());g==="context"?n==null||n(ee):g==="chunk"?a==null||a(ee.text):g==="error"?i==null||i(ee.error):g==="done"&&(o==null||o())}catch{}g=null}}o==null||o()}).catch(x=>{x.name!=="AbortError"&&(i==null||i(x.message))}),{abort:()=>u.abort()}}function qv(t,e,n={},{onMeta:a,onSnapshot:o,onContext:i,onSystemPrompt:s,onToolCall:l,onToolResult:u,onChart:f,onChunk:p,onDone:_,onError:x,onViewerNavigate:b},k=null){const C={question:e,stream:!0,...n};t&&(C.company=t),k&&k.length>0&&(C.history=k);const g=new AbortController;return fetch(`${Vr}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(C),signal:g.signal}).then(async y=>{if(!y.ok){const L=await y.json().catch(()=>({}));x==null||x(L.detail||"스트리밍 실패");return}const I=y.body.getReader(),O=new TextDecoder;let M="",ee=!1,fe=null;for(;;){const{done:L,value:S}=await I.read();if(L)break;M+=O.decode(S,{stream:!0});const X=M.split(`
`);M=X.pop()||"";for(const G of X)if(G.startsWith("event:"))fe=G.slice(6).trim();else if(G.startsWith("data:")&&fe){const me=G.slice(5).trim();try{const V=JSON.parse(me);fe==="meta"?a==null||a(V):fe==="snapshot"?o==null||o(V):fe==="context"?i==null||i(V):fe==="system_prompt"?s==null||s(V):fe==="tool_call"?l==null||l(V):fe==="tool_result"?u==null||u(V):fe==="chunk"?p==null||p(V.text):fe==="chart"?f==null||f(V):fe==="viewer_navigate"?b==null||b(V):fe==="error"?x==null||x(V.error,V.action,V.detail):fe==="done"&&(ee||(ee=!0,_==null||_()))}catch(V){console.warn("SSE JSON parse:",V)}fe=null}}ee||(ee=!0,_==null||_())}).catch(y=>{y.name!=="AbortError"&&(x==null||x(y.message))}),{abort:()=>g.abort()}}const Hv=(t,e)=>{const n=new Array(t.length+e.length);for(let a=0;a<t.length;a++)n[a]=t[a];for(let a=0;a<e.length;a++)n[t.length+a]=e[a];return n},Uv=(t,e)=>({classGroupId:t,validator:e}),Sc=(t=new Map,e=null,n)=>({nextPart:t,validators:e,classGroupId:n}),Os="-",Hl=[],Wv="arbitrary..",Kv=t=>{const e=Jv(t),{conflictingClassGroups:n,conflictingClassGroupModifiers:a}=t;return{getClassGroupId:s=>{if(s.startsWith("[")&&s.endsWith("]"))return Gv(s);const l=s.split(Os),u=l[0]===""&&l.length>1?1:0;return Mc(l,u,e)},getConflictingClassGroupIds:(s,l)=>{if(l){const u=a[s],f=n[s];return u?f?Hv(f,u):u:f||Hl}return n[s]||Hl}}},Mc=(t,e,n)=>{if(t.length-e===0)return n.classGroupId;const o=t[e],i=n.nextPart.get(o);if(i){const f=Mc(t,e+1,i);if(f)return f}const s=n.validators;if(s===null)return;const l=e===0?t.join(Os):t.slice(e).join(Os),u=s.length;for(let f=0;f<u;f++){const p=s[f];if(p.validator(l))return p.classGroupId}},Gv=t=>t.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const e=t.slice(1,-1),n=e.indexOf(":"),a=e.slice(0,n);return a?Wv+a:void 0})(),Jv=t=>{const{theme:e,classGroups:n}=t;return Yv(n,e)},Yv=(t,e)=>{const n=Sc();for(const a in t){const o=t[a];il(o,n,a,e)}return n},il=(t,e,n,a)=>{const o=t.length;for(let i=0;i<o;i++){const s=t[i];Xv(s,e,n,a)}},Xv=(t,e,n,a)=>{if(typeof t=="string"){Qv(t,e,n);return}if(typeof t=="function"){Zv(t,e,n,a);return}ep(t,e,n,a)},Qv=(t,e,n)=>{const a=t===""?e:zc(e,t);a.classGroupId=n},Zv=(t,e,n,a)=>{if(tp(t)){il(t(a),e,n,a);return}e.validators===null&&(e.validators=[]),e.validators.push(Uv(n,t))},ep=(t,e,n,a)=>{const o=Object.entries(t),i=o.length;for(let s=0;s<i;s++){const[l,u]=o[s];il(u,zc(e,l),n,a)}},zc=(t,e)=>{let n=t;const a=e.split(Os),o=a.length;for(let i=0;i<o;i++){const s=a[i];let l=n.nextPart.get(s);l||(l=Sc(),n.nextPart.set(s,l)),n=l}return n},tp=t=>"isThemeGetter"in t&&t.isThemeGetter===!0,rp=t=>{if(t<1)return{get:()=>{},set:()=>{}};let e=0,n=Object.create(null),a=Object.create(null);const o=(i,s)=>{n[i]=s,e++,e>t&&(e=0,a=n,n=Object.create(null))};return{get(i){let s=n[i];if(s!==void 0)return s;if((s=a[i])!==void 0)return o(i,s),s},set(i,s){i in n?n[i]=s:o(i,s)}}},Ei="!",Ul=":",np=[],Wl=(t,e,n,a,o)=>({modifiers:t,hasImportantModifier:e,baseClassName:n,maybePostfixModifierPosition:a,isExternal:o}),ap=t=>{const{prefix:e,experimentalParseClassName:n}=t;let a=o=>{const i=[];let s=0,l=0,u=0,f;const p=o.length;for(let C=0;C<p;C++){const g=o[C];if(s===0&&l===0){if(g===Ul){i.push(o.slice(u,C)),u=C+1;continue}if(g==="/"){f=C;continue}}g==="["?s++:g==="]"?s--:g==="("?l++:g===")"&&l--}const _=i.length===0?o:o.slice(u);let x=_,b=!1;_.endsWith(Ei)?(x=_.slice(0,-1),b=!0):_.startsWith(Ei)&&(x=_.slice(1),b=!0);const k=f&&f>u?f-u:void 0;return Wl(i,b,x,k)};if(e){const o=e+Ul,i=a;a=s=>s.startsWith(o)?i(s.slice(o.length)):Wl(np,!1,s,void 0,!0)}if(n){const o=a;a=i=>n({className:i,parseClassName:o})}return a},op=t=>{const e=new Map;return t.orderSensitiveModifiers.forEach((n,a)=>{e.set(n,1e6+a)}),n=>{const a=[];let o=[];for(let i=0;i<n.length;i++){const s=n[i],l=s[0]==="[",u=e.has(s);l||u?(o.length>0&&(o.sort(),a.push(...o),o=[]),a.push(s)):o.push(s)}return o.length>0&&(o.sort(),a.push(...o)),a}},sp=t=>({cache:rp(t.cacheSize),parseClassName:ap(t),sortModifiers:op(t),...Kv(t)}),ip=/\s+/,lp=(t,e)=>{const{parseClassName:n,getClassGroupId:a,getConflictingClassGroupIds:o,sortModifiers:i}=e,s=[],l=t.trim().split(ip);let u="";for(let f=l.length-1;f>=0;f-=1){const p=l[f],{isExternal:_,modifiers:x,hasImportantModifier:b,baseClassName:k,maybePostfixModifierPosition:C}=n(p);if(_){u=p+(u.length>0?" "+u:u);continue}let g=!!C,y=a(g?k.substring(0,C):k);if(!y){if(!g){u=p+(u.length>0?" "+u:u);continue}if(y=a(k),!y){u=p+(u.length>0?" "+u:u);continue}g=!1}const I=x.length===0?"":x.length===1?x[0]:i(x).join(":"),O=b?I+Ei:I,M=O+y;if(s.indexOf(M)>-1)continue;s.push(M);const ee=o(y,g);for(let fe=0;fe<ee.length;++fe){const L=ee[fe];s.push(O+L)}u=p+(u.length>0?" "+u:u)}return u},dp=(...t)=>{let e=0,n,a,o="";for(;e<t.length;)(n=t[e++])&&(a=Tc(n))&&(o&&(o+=" "),o+=a);return o},Tc=t=>{if(typeof t=="string")return t;let e,n="";for(let a=0;a<t.length;a++)t[a]&&(e=Tc(t[a]))&&(n&&(n+=" "),n+=e);return n},cp=(t,...e)=>{let n,a,o,i;const s=u=>{const f=e.reduce((p,_)=>_(p),t());return n=sp(f),a=n.cache.get,o=n.cache.set,i=l,l(u)},l=u=>{const f=a(u);if(f)return f;const p=lp(u,n);return o(u,p),p};return i=s,(...u)=>i(dp(...u))},up=[],Rr=t=>{const e=n=>n[t]||up;return e.isThemeGetter=!0,e},Ic=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Ac=/^\((?:(\w[\w-]*):)?(.+)\)$/i,fp=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,vp=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,pp=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,hp=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,mp=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,xp=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,Sa=t=>fp.test(t),jt=t=>!!t&&!Number.isNaN(Number(t)),Ma=t=>!!t&&Number.isInteger(Number(t)),ii=t=>t.endsWith("%")&&jt(t.slice(0,-1)),pa=t=>vp.test(t),Ec=()=>!0,gp=t=>pp.test(t)&&!hp.test(t),ll=()=>!1,_p=t=>mp.test(t),bp=t=>xp.test(t),wp=t=>!Ke(t)&&!Xe(t),yp=t=>qa(t,Lc,ll),Ke=t=>Ic.test(t),Ka=t=>qa(t,Oc,gp),Kl=t=>qa(t,Ip,jt),kp=t=>qa(t,Rc,Ec),Cp=t=>qa(t,Dc,ll),Gl=t=>qa(t,Nc,ll),$p=t=>qa(t,Pc,bp),ys=t=>qa(t,jc,_p),Xe=t=>Ac.test(t),Go=t=>po(t,Oc),Sp=t=>po(t,Dc),Jl=t=>po(t,Nc),Mp=t=>po(t,Lc),zp=t=>po(t,Pc),ks=t=>po(t,jc,!0),Tp=t=>po(t,Rc,!0),qa=(t,e,n)=>{const a=Ic.exec(t);return a?a[1]?e(a[1]):n(a[2]):!1},po=(t,e,n=!1)=>{const a=Ac.exec(t);return a?a[1]?e(a[1]):n:!1},Nc=t=>t==="position"||t==="percentage",Pc=t=>t==="image"||t==="url",Lc=t=>t==="length"||t==="size"||t==="bg-size",Oc=t=>t==="length",Ip=t=>t==="number",Dc=t=>t==="family-name",Rc=t=>t==="number"||t==="weight",jc=t=>t==="shadow",Ap=()=>{const t=Rr("color"),e=Rr("font"),n=Rr("text"),a=Rr("font-weight"),o=Rr("tracking"),i=Rr("leading"),s=Rr("breakpoint"),l=Rr("container"),u=Rr("spacing"),f=Rr("radius"),p=Rr("shadow"),_=Rr("inset-shadow"),x=Rr("text-shadow"),b=Rr("drop-shadow"),k=Rr("blur"),C=Rr("perspective"),g=Rr("aspect"),y=Rr("ease"),I=Rr("animate"),O=()=>["auto","avoid","all","avoid-page","page","left","right","column"],M=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],ee=()=>[...M(),Xe,Ke],fe=()=>["auto","hidden","clip","visible","scroll"],L=()=>["auto","contain","none"],S=()=>[Xe,Ke,u],X=()=>[Sa,"full","auto",...S()],G=()=>[Ma,"none","subgrid",Xe,Ke],me=()=>["auto",{span:["full",Ma,Xe,Ke]},Ma,Xe,Ke],V=()=>[Ma,"auto",Xe,Ke],ze=()=>["auto","min","max","fr",Xe,Ke],j=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],B=()=>["start","end","center","stretch","center-safe","end-safe"],le=()=>["auto",...S()],we=()=>[Sa,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...S()],U=()=>[Sa,"screen","full","dvw","lvw","svw","min","max","fit",...S()],ne=()=>[Sa,"screen","full","lh","dvh","lvh","svh","min","max","fit",...S()],N=()=>[t,Xe,Ke],W=()=>[...M(),Jl,Gl,{position:[Xe,Ke]}],H=()=>["no-repeat",{repeat:["","x","y","space","round"]}],E=()=>["auto","cover","contain",Mp,yp,{size:[Xe,Ke]}],q=()=>[ii,Go,Ka],J=()=>["","none","full",f,Xe,Ke],Y=()=>["",jt,Go,Ka],ye=()=>["solid","dashed","dotted","double"],Se=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],te=()=>[jt,ii,Jl,Gl],Oe=()=>["","none",k,Xe,Ke],tt=()=>["none",jt,Xe,Ke],ot=()=>["none",jt,Xe,Ke],Ge=()=>[jt,Xe,Ke],rt=()=>[Sa,"full",...S()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[pa],breakpoint:[pa],color:[Ec],container:[pa],"drop-shadow":[pa],ease:["in","out","in-out"],font:[wp],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[pa],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[pa],shadow:[pa],spacing:["px",jt],text:[pa],"text-shadow":[pa],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",Sa,Ke,Xe,g]}],container:["container"],columns:[{columns:[jt,Ke,Xe,l]}],"break-after":[{"break-after":O()}],"break-before":[{"break-before":O()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:ee()}],overflow:[{overflow:fe()}],"overflow-x":[{"overflow-x":fe()}],"overflow-y":[{"overflow-y":fe()}],overscroll:[{overscroll:L()}],"overscroll-x":[{"overscroll-x":L()}],"overscroll-y":[{"overscroll-y":L()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:X()}],"inset-x":[{"inset-x":X()}],"inset-y":[{"inset-y":X()}],start:[{"inset-s":X(),start:X()}],end:[{"inset-e":X(),end:X()}],"inset-bs":[{"inset-bs":X()}],"inset-be":[{"inset-be":X()}],top:[{top:X()}],right:[{right:X()}],bottom:[{bottom:X()}],left:[{left:X()}],visibility:["visible","invisible","collapse"],z:[{z:[Ma,"auto",Xe,Ke]}],basis:[{basis:[Sa,"full","auto",l,...S()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[jt,Sa,"auto","initial","none",Ke]}],grow:[{grow:["",jt,Xe,Ke]}],shrink:[{shrink:["",jt,Xe,Ke]}],order:[{order:[Ma,"first","last","none",Xe,Ke]}],"grid-cols":[{"grid-cols":G()}],"col-start-end":[{col:me()}],"col-start":[{"col-start":V()}],"col-end":[{"col-end":V()}],"grid-rows":[{"grid-rows":G()}],"row-start-end":[{row:me()}],"row-start":[{"row-start":V()}],"row-end":[{"row-end":V()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":ze()}],"auto-rows":[{"auto-rows":ze()}],gap:[{gap:S()}],"gap-x":[{"gap-x":S()}],"gap-y":[{"gap-y":S()}],"justify-content":[{justify:[...j(),"normal"]}],"justify-items":[{"justify-items":[...B(),"normal"]}],"justify-self":[{"justify-self":["auto",...B()]}],"align-content":[{content:["normal",...j()]}],"align-items":[{items:[...B(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...B(),{baseline:["","last"]}]}],"place-content":[{"place-content":j()}],"place-items":[{"place-items":[...B(),"baseline"]}],"place-self":[{"place-self":["auto",...B()]}],p:[{p:S()}],px:[{px:S()}],py:[{py:S()}],ps:[{ps:S()}],pe:[{pe:S()}],pbs:[{pbs:S()}],pbe:[{pbe:S()}],pt:[{pt:S()}],pr:[{pr:S()}],pb:[{pb:S()}],pl:[{pl:S()}],m:[{m:le()}],mx:[{mx:le()}],my:[{my:le()}],ms:[{ms:le()}],me:[{me:le()}],mbs:[{mbs:le()}],mbe:[{mbe:le()}],mt:[{mt:le()}],mr:[{mr:le()}],mb:[{mb:le()}],ml:[{ml:le()}],"space-x":[{"space-x":S()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":S()}],"space-y-reverse":["space-y-reverse"],size:[{size:we()}],"inline-size":[{inline:["auto",...U()]}],"min-inline-size":[{"min-inline":["auto",...U()]}],"max-inline-size":[{"max-inline":["none",...U()]}],"block-size":[{block:["auto",...ne()]}],"min-block-size":[{"min-block":["auto",...ne()]}],"max-block-size":[{"max-block":["none",...ne()]}],w:[{w:[l,"screen",...we()]}],"min-w":[{"min-w":[l,"screen","none",...we()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[s]},...we()]}],h:[{h:["screen","lh",...we()]}],"min-h":[{"min-h":["screen","lh","none",...we()]}],"max-h":[{"max-h":["screen","lh",...we()]}],"font-size":[{text:["base",n,Go,Ka]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[a,Tp,kp]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",ii,Ke]}],"font-family":[{font:[Sp,Cp,e]}],"font-features":[{"font-features":[Ke]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[o,Xe,Ke]}],"line-clamp":[{"line-clamp":[jt,"none",Xe,Kl]}],leading:[{leading:[i,...S()]}],"list-image":[{"list-image":["none",Xe,Ke]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",Xe,Ke]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:N()}],"text-color":[{text:N()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...ye(),"wavy"]}],"text-decoration-thickness":[{decoration:[jt,"from-font","auto",Xe,Ka]}],"text-decoration-color":[{decoration:N()}],"underline-offset":[{"underline-offset":[jt,"auto",Xe,Ke]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:S()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",Xe,Ke]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",Xe,Ke]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:W()}],"bg-repeat":[{bg:H()}],"bg-size":[{bg:E()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},Ma,Xe,Ke],radial:["",Xe,Ke],conic:[Ma,Xe,Ke]},zp,$p]}],"bg-color":[{bg:N()}],"gradient-from-pos":[{from:q()}],"gradient-via-pos":[{via:q()}],"gradient-to-pos":[{to:q()}],"gradient-from":[{from:N()}],"gradient-via":[{via:N()}],"gradient-to":[{to:N()}],rounded:[{rounded:J()}],"rounded-s":[{"rounded-s":J()}],"rounded-e":[{"rounded-e":J()}],"rounded-t":[{"rounded-t":J()}],"rounded-r":[{"rounded-r":J()}],"rounded-b":[{"rounded-b":J()}],"rounded-l":[{"rounded-l":J()}],"rounded-ss":[{"rounded-ss":J()}],"rounded-se":[{"rounded-se":J()}],"rounded-ee":[{"rounded-ee":J()}],"rounded-es":[{"rounded-es":J()}],"rounded-tl":[{"rounded-tl":J()}],"rounded-tr":[{"rounded-tr":J()}],"rounded-br":[{"rounded-br":J()}],"rounded-bl":[{"rounded-bl":J()}],"border-w":[{border:Y()}],"border-w-x":[{"border-x":Y()}],"border-w-y":[{"border-y":Y()}],"border-w-s":[{"border-s":Y()}],"border-w-e":[{"border-e":Y()}],"border-w-bs":[{"border-bs":Y()}],"border-w-be":[{"border-be":Y()}],"border-w-t":[{"border-t":Y()}],"border-w-r":[{"border-r":Y()}],"border-w-b":[{"border-b":Y()}],"border-w-l":[{"border-l":Y()}],"divide-x":[{"divide-x":Y()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":Y()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...ye(),"hidden","none"]}],"divide-style":[{divide:[...ye(),"hidden","none"]}],"border-color":[{border:N()}],"border-color-x":[{"border-x":N()}],"border-color-y":[{"border-y":N()}],"border-color-s":[{"border-s":N()}],"border-color-e":[{"border-e":N()}],"border-color-bs":[{"border-bs":N()}],"border-color-be":[{"border-be":N()}],"border-color-t":[{"border-t":N()}],"border-color-r":[{"border-r":N()}],"border-color-b":[{"border-b":N()}],"border-color-l":[{"border-l":N()}],"divide-color":[{divide:N()}],"outline-style":[{outline:[...ye(),"none","hidden"]}],"outline-offset":[{"outline-offset":[jt,Xe,Ke]}],"outline-w":[{outline:["",jt,Go,Ka]}],"outline-color":[{outline:N()}],shadow:[{shadow:["","none",p,ks,ys]}],"shadow-color":[{shadow:N()}],"inset-shadow":[{"inset-shadow":["none",_,ks,ys]}],"inset-shadow-color":[{"inset-shadow":N()}],"ring-w":[{ring:Y()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:N()}],"ring-offset-w":[{"ring-offset":[jt,Ka]}],"ring-offset-color":[{"ring-offset":N()}],"inset-ring-w":[{"inset-ring":Y()}],"inset-ring-color":[{"inset-ring":N()}],"text-shadow":[{"text-shadow":["none",x,ks,ys]}],"text-shadow-color":[{"text-shadow":N()}],opacity:[{opacity:[jt,Xe,Ke]}],"mix-blend":[{"mix-blend":[...Se(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":Se()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[jt]}],"mask-image-linear-from-pos":[{"mask-linear-from":te()}],"mask-image-linear-to-pos":[{"mask-linear-to":te()}],"mask-image-linear-from-color":[{"mask-linear-from":N()}],"mask-image-linear-to-color":[{"mask-linear-to":N()}],"mask-image-t-from-pos":[{"mask-t-from":te()}],"mask-image-t-to-pos":[{"mask-t-to":te()}],"mask-image-t-from-color":[{"mask-t-from":N()}],"mask-image-t-to-color":[{"mask-t-to":N()}],"mask-image-r-from-pos":[{"mask-r-from":te()}],"mask-image-r-to-pos":[{"mask-r-to":te()}],"mask-image-r-from-color":[{"mask-r-from":N()}],"mask-image-r-to-color":[{"mask-r-to":N()}],"mask-image-b-from-pos":[{"mask-b-from":te()}],"mask-image-b-to-pos":[{"mask-b-to":te()}],"mask-image-b-from-color":[{"mask-b-from":N()}],"mask-image-b-to-color":[{"mask-b-to":N()}],"mask-image-l-from-pos":[{"mask-l-from":te()}],"mask-image-l-to-pos":[{"mask-l-to":te()}],"mask-image-l-from-color":[{"mask-l-from":N()}],"mask-image-l-to-color":[{"mask-l-to":N()}],"mask-image-x-from-pos":[{"mask-x-from":te()}],"mask-image-x-to-pos":[{"mask-x-to":te()}],"mask-image-x-from-color":[{"mask-x-from":N()}],"mask-image-x-to-color":[{"mask-x-to":N()}],"mask-image-y-from-pos":[{"mask-y-from":te()}],"mask-image-y-to-pos":[{"mask-y-to":te()}],"mask-image-y-from-color":[{"mask-y-from":N()}],"mask-image-y-to-color":[{"mask-y-to":N()}],"mask-image-radial":[{"mask-radial":[Xe,Ke]}],"mask-image-radial-from-pos":[{"mask-radial-from":te()}],"mask-image-radial-to-pos":[{"mask-radial-to":te()}],"mask-image-radial-from-color":[{"mask-radial-from":N()}],"mask-image-radial-to-color":[{"mask-radial-to":N()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":M()}],"mask-image-conic-pos":[{"mask-conic":[jt]}],"mask-image-conic-from-pos":[{"mask-conic-from":te()}],"mask-image-conic-to-pos":[{"mask-conic-to":te()}],"mask-image-conic-from-color":[{"mask-conic-from":N()}],"mask-image-conic-to-color":[{"mask-conic-to":N()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:W()}],"mask-repeat":[{mask:H()}],"mask-size":[{mask:E()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",Xe,Ke]}],filter:[{filter:["","none",Xe,Ke]}],blur:[{blur:Oe()}],brightness:[{brightness:[jt,Xe,Ke]}],contrast:[{contrast:[jt,Xe,Ke]}],"drop-shadow":[{"drop-shadow":["","none",b,ks,ys]}],"drop-shadow-color":[{"drop-shadow":N()}],grayscale:[{grayscale:["",jt,Xe,Ke]}],"hue-rotate":[{"hue-rotate":[jt,Xe,Ke]}],invert:[{invert:["",jt,Xe,Ke]}],saturate:[{saturate:[jt,Xe,Ke]}],sepia:[{sepia:["",jt,Xe,Ke]}],"backdrop-filter":[{"backdrop-filter":["","none",Xe,Ke]}],"backdrop-blur":[{"backdrop-blur":Oe()}],"backdrop-brightness":[{"backdrop-brightness":[jt,Xe,Ke]}],"backdrop-contrast":[{"backdrop-contrast":[jt,Xe,Ke]}],"backdrop-grayscale":[{"backdrop-grayscale":["",jt,Xe,Ke]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[jt,Xe,Ke]}],"backdrop-invert":[{"backdrop-invert":["",jt,Xe,Ke]}],"backdrop-opacity":[{"backdrop-opacity":[jt,Xe,Ke]}],"backdrop-saturate":[{"backdrop-saturate":[jt,Xe,Ke]}],"backdrop-sepia":[{"backdrop-sepia":["",jt,Xe,Ke]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":S()}],"border-spacing-x":[{"border-spacing-x":S()}],"border-spacing-y":[{"border-spacing-y":S()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",Xe,Ke]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[jt,"initial",Xe,Ke]}],ease:[{ease:["linear","initial",y,Xe,Ke]}],delay:[{delay:[jt,Xe,Ke]}],animate:[{animate:["none",I,Xe,Ke]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[C,Xe,Ke]}],"perspective-origin":[{"perspective-origin":ee()}],rotate:[{rotate:tt()}],"rotate-x":[{"rotate-x":tt()}],"rotate-y":[{"rotate-y":tt()}],"rotate-z":[{"rotate-z":tt()}],scale:[{scale:ot()}],"scale-x":[{"scale-x":ot()}],"scale-y":[{"scale-y":ot()}],"scale-z":[{"scale-z":ot()}],"scale-3d":["scale-3d"],skew:[{skew:Ge()}],"skew-x":[{"skew-x":Ge()}],"skew-y":[{"skew-y":Ge()}],transform:[{transform:[Xe,Ke,"","none","gpu","cpu"]}],"transform-origin":[{origin:ee()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:rt()}],"translate-x":[{"translate-x":rt()}],"translate-y":[{"translate-y":rt()}],"translate-z":[{"translate-z":rt()}],"translate-none":["translate-none"],accent:[{accent:N()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:N()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",Xe,Ke]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":S()}],"scroll-mx":[{"scroll-mx":S()}],"scroll-my":[{"scroll-my":S()}],"scroll-ms":[{"scroll-ms":S()}],"scroll-me":[{"scroll-me":S()}],"scroll-mbs":[{"scroll-mbs":S()}],"scroll-mbe":[{"scroll-mbe":S()}],"scroll-mt":[{"scroll-mt":S()}],"scroll-mr":[{"scroll-mr":S()}],"scroll-mb":[{"scroll-mb":S()}],"scroll-ml":[{"scroll-ml":S()}],"scroll-p":[{"scroll-p":S()}],"scroll-px":[{"scroll-px":S()}],"scroll-py":[{"scroll-py":S()}],"scroll-ps":[{"scroll-ps":S()}],"scroll-pe":[{"scroll-pe":S()}],"scroll-pbs":[{"scroll-pbs":S()}],"scroll-pbe":[{"scroll-pbe":S()}],"scroll-pt":[{"scroll-pt":S()}],"scroll-pr":[{"scroll-pr":S()}],"scroll-pb":[{"scroll-pb":S()}],"scroll-pl":[{"scroll-pl":S()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",Xe,Ke]}],fill:[{fill:["none",...N()]}],"stroke-w":[{stroke:[jt,Go,Ka,Kl]}],stroke:[{stroke:["none",...N()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},Ep=cp(Ap);function wr(...t){return Ep(_c(t))}const Ni="dartlab-conversations",Yl=50;function Np(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function Pp(){try{const t=localStorage.getItem(Ni);return t?JSON.parse(t):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const Lp=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function Xl(t){return t.map(e=>({...e,messages:e.messages.map(n=>{if(n.role!=="assistant")return n;const a={};for(const[o,i]of Object.entries(n))Lp.includes(o)||(a[o]=i);return a})}))}function Ql(t){try{const e={conversations:Xl(t.conversations),activeId:t.activeId};localStorage.setItem(Ni,JSON.stringify(e))}catch{if(t.conversations.length>5){t.conversations=t.conversations.slice(0,t.conversations.length-5);try{const e={conversations:Xl(t.conversations),activeId:t.activeId};localStorage.setItem(Ni,JSON.stringify(e))}catch{}}}}function Op(){const t=Pp(),e=t.conversations||[],n=e.find(y=>y.id===t.activeId)?t.activeId:null;let a=K(Bt(e)),o=K(Bt(n)),i=null;function s(){i&&clearTimeout(i),i=setTimeout(()=>{Ql({conversations:r(a),activeId:r(o)}),i=null},300)}function l(){i&&clearTimeout(i),i=null,Ql({conversations:r(a),activeId:r(o)})}function u(){return r(a).find(y=>y.id===r(o))||null}function f(){const y={id:Np(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return v(a,[y,...r(a)],!0),r(a).length>Yl&&v(a,r(a).slice(0,Yl),!0),v(o,y.id,!0),l(),y.id}function p(y){r(a).find(I=>I.id===y)&&(v(o,y,!0),l())}function _(y,I,O=null){const M=u();if(!M)return;const ee={role:y,text:I};O&&(ee.meta=O),M.messages=[...M.messages,ee],M.updatedAt=Date.now(),M.title==="새 대화"&&y==="user"&&(M.title=I.length>30?I.slice(0,30)+"...":I),v(a,[...r(a)],!0),l()}function x(y){const I=u();if(!I||I.messages.length===0)return;const O=I.messages[I.messages.length-1];Object.assign(O,y),I.updatedAt=Date.now(),v(a,[...r(a)],!0),s()}function b(y){v(a,r(a).filter(I=>I.id!==y),!0),r(o)===y&&v(o,r(a).length>0?r(a)[0].id:null,!0),l()}function k(){const y=u();!y||y.messages.length===0||(y.messages=y.messages.slice(0,-1),y.updatedAt=Date.now(),v(a,[...r(a)],!0),l())}function C(y,I){const O=r(a).find(M=>M.id===y);O&&(O.title=I,v(a,[...r(a)],!0),l())}function g(){v(a,[],!0),v(o,null),l()}return{get conversations(){return r(a)},get activeId(){return r(o)},get active(){return u()},createConversation:f,setActive:p,addMessage:_,updateLastMessage:x,removeLastMessage:k,deleteConversation:b,updateTitle:C,clearAll:g,flush:l}}const Fc="dartlab-workspace",Dp=6;function Vc(){return typeof window<"u"&&typeof localStorage<"u"}function Rp(){if(!Vc())return{};try{const t=localStorage.getItem(Fc);return t?JSON.parse(t):{}}catch{return{}}}function jp(t){Vc()&&localStorage.setItem(Fc,JSON.stringify(t))}function Fp(){const t=Rp();let e=K("chat"),n=K(!1),a=K(null),o=K(null),i=K("explore"),s=K(null),l=K(null),u=K(null),f=K(null),p=K(null),_=K(Bt(t.selectedCompany||null)),x=K(Bt(t.recentCompanies||[]));function b(){jp({selectedCompany:r(_),recentCompanies:r(x)})}function k(G){if(!(G!=null&&G.stockCode))return;const me={stockCode:G.stockCode,corpName:G.corpName||G.company||G.stockCode,company:G.company||G.corpName||G.stockCode,market:G.market||""};v(x,[me,...r(x).filter(V=>V.stockCode!==me.stockCode)].slice(0,Dp),!0)}function C(G){v(e,G,!0)}function g(G){G&&(v(_,G,!0),k(G)),v(e,"viewer"),v(n,!1),b()}function y(G){v(a,"data"),v(o,G,!0),v(n,!0),S("explore")}function I(){v(n,!1)}function O(G){v(_,G,!0),G&&k(G),b()}function M(G,me){var V,ze,j,B;!(G!=null&&G.company)&&!(G!=null&&G.stockCode)||(v(_,{...r(_)||{},...me||{},corpName:G.company||((V=r(_))==null?void 0:V.corpName)||(me==null?void 0:me.corpName)||(me==null?void 0:me.company),company:G.company||((ze=r(_))==null?void 0:ze.company)||(me==null?void 0:me.company)||(me==null?void 0:me.corpName),stockCode:G.stockCode||((j=r(_))==null?void 0:j.stockCode)||(me==null?void 0:me.stockCode),market:((B=r(_))==null?void 0:B.market)||(me==null?void 0:me.market)||""},!0),k(r(_)),b())}function ee(G,me,V=null){v(u,G,!0),v(f,me||G,!0),v(p,V,!0)}function fe(G,me=null){v(a,"data"),v(n,!0),v(i,"evidence"),v(s,G,!0),v(l,Number.isInteger(me)?me:null,!0)}function L(){v(s,null),v(l,null)}function S(G){v(i,G||"explore",!0),r(i)!=="evidence"&&L()}function X(){return r(e)==="viewer"&&r(_)&&r(u)?{type:"viewer",company:r(_),topic:r(u),topicLabel:r(f),period:r(p)}:r(n)?r(a)==="viewer"&&r(_)?{type:"viewer",company:r(_),topic:r(u),topicLabel:r(f),period:r(p)}:r(a)==="data"&&r(o)?{type:"data",data:r(o)}:null:null}return{get activeView(){return r(e)},get panelOpen(){return r(n)},get panelMode(){return r(a)},get panelData(){return r(o)},get activeTab(){return r(i)},get activeEvidenceSection(){return r(s)},get selectedEvidenceIndex(){return r(l)},get selectedCompany(){return r(_)},get recentCompanies(){return r(x)},get viewerTopic(){return r(u)},get viewerTopicLabel(){return r(f)},get viewerPeriod(){return r(p)},switchView:C,openViewer:g,openData:y,openEvidence:fe,closePanel:I,selectCompany:O,setViewerTopic:ee,clearEvidenceSelection:L,setTab:S,syncCompanyFromMessage:M,getViewContext:X}}const Vp="ENTRIES",Bc="KEYS",qc="VALUES",Yr="";class li{constructor(e,n){const a=e._tree,o=Array.from(a.keys());this.set=e,this._type=n,this._path=o.length>0?[{node:a,keys:o}]:[]}next(){const e=this.dive();return this.backtrack(),e}dive(){if(this._path.length===0)return{done:!0,value:void 0};const{node:e,keys:n}=mo(this._path);if(mo(n)===Yr)return{done:!1,value:this.result()};const a=e.get(mo(n));return this._path.push({node:a,keys:Array.from(a.keys())}),this.dive()}backtrack(){if(this._path.length===0)return;const e=mo(this._path).keys;e.pop(),!(e.length>0)&&(this._path.pop(),this.backtrack())}key(){return this.set._prefix+this._path.map(({keys:e})=>mo(e)).filter(e=>e!==Yr).join("")}value(){return mo(this._path).node.get(Yr)}result(){switch(this._type){case qc:return this.value();case Bc:return this.key();default:return[this.key(),this.value()]}}[Symbol.iterator](){return this}}const mo=t=>t[t.length-1],Bp=(t,e,n)=>{const a=new Map;if(e===void 0)return a;const o=e.length+1,i=o+n,s=new Uint8Array(i*o).fill(n+1);for(let l=0;l<o;++l)s[l]=l;for(let l=1;l<i;++l)s[l*o]=l;return Hc(t,e,n,a,s,1,o,""),a},Hc=(t,e,n,a,o,i,s,l)=>{const u=i*s;e:for(const f of t.keys())if(f===Yr){const p=o[u-1];p<=n&&a.set(l,[t.get(f),p])}else{let p=i;for(let _=0;_<f.length;++_,++p){const x=f[_],b=s*p,k=b-s;let C=o[b];const g=Math.max(0,p-n-1),y=Math.min(s-1,p+n);for(let I=g;I<y;++I){const O=x!==e[I],M=o[k+I]+ +O,ee=o[k+I+1]+1,fe=o[b+I]+1,L=o[b+I+1]=Math.min(M,ee,fe);L<C&&(C=L)}if(C>n)continue e}Hc(t.get(f),e,n,a,o,p,s,l+f)}};class Na{constructor(e=new Map,n=""){this._size=void 0,this._tree=e,this._prefix=n}atPrefix(e){if(!e.startsWith(this._prefix))throw new Error("Mismatched prefix");const[n,a]=Ds(this._tree,e.slice(this._prefix.length));if(n===void 0){const[o,i]=dl(a);for(const s of o.keys())if(s!==Yr&&s.startsWith(i)){const l=new Map;return l.set(s.slice(i.length),o.get(s)),new Na(l,e)}}return new Na(n,e)}clear(){this._size=void 0,this._tree.clear()}delete(e){return this._size=void 0,qp(this._tree,e)}entries(){return new li(this,Vp)}forEach(e){for(const[n,a]of this)e(n,a,this)}fuzzyGet(e,n){return Bp(this._tree,e,n)}get(e){const n=Pi(this._tree,e);return n!==void 0?n.get(Yr):void 0}has(e){const n=Pi(this._tree,e);return n!==void 0&&n.has(Yr)}keys(){return new li(this,Bc)}set(e,n){if(typeof e!="string")throw new Error("key must be a string");return this._size=void 0,di(this._tree,e).set(Yr,n),this}get size(){if(this._size)return this._size;this._size=0;const e=this.entries();for(;!e.next().done;)this._size+=1;return this._size}update(e,n){if(typeof e!="string")throw new Error("key must be a string");this._size=void 0;const a=di(this._tree,e);return a.set(Yr,n(a.get(Yr))),this}fetch(e,n){if(typeof e!="string")throw new Error("key must be a string");this._size=void 0;const a=di(this._tree,e);let o=a.get(Yr);return o===void 0&&a.set(Yr,o=n()),o}values(){return new li(this,qc)}[Symbol.iterator](){return this.entries()}static from(e){const n=new Na;for(const[a,o]of e)n.set(a,o);return n}static fromObject(e){return Na.from(Object.entries(e))}}const Ds=(t,e,n=[])=>{if(e.length===0||t==null)return[t,n];for(const a of t.keys())if(a!==Yr&&e.startsWith(a))return n.push([t,a]),Ds(t.get(a),e.slice(a.length),n);return n.push([t,e]),Ds(void 0,"",n)},Pi=(t,e)=>{if(e.length===0||t==null)return t;for(const n of t.keys())if(n!==Yr&&e.startsWith(n))return Pi(t.get(n),e.slice(n.length))},di=(t,e)=>{const n=e.length;e:for(let a=0;t&&a<n;){for(const i of t.keys())if(i!==Yr&&e[a]===i[0]){const s=Math.min(n-a,i.length);let l=1;for(;l<s&&e[a+l]===i[l];)++l;const u=t.get(i);if(l===i.length)t=u;else{const f=new Map;f.set(i.slice(l),u),t.set(e.slice(a,a+l),f),t.delete(i),t=f}a+=l;continue e}const o=new Map;return t.set(e.slice(a),o),o}return t},qp=(t,e)=>{const[n,a]=Ds(t,e);if(n!==void 0){if(n.delete(Yr),n.size===0)Uc(a);else if(n.size===1){const[o,i]=n.entries().next().value;Wc(a,o,i)}}},Uc=t=>{if(t.length===0)return;const[e,n]=dl(t);if(e.delete(n),e.size===0)Uc(t.slice(0,-1));else if(e.size===1){const[a,o]=e.entries().next().value;a!==Yr&&Wc(t.slice(0,-1),a,o)}},Wc=(t,e,n)=>{if(t.length===0)return;const[a,o]=dl(t);a.set(o+e,n),a.delete(o)},dl=t=>t[t.length-1],cl="or",Kc="and",Hp="and_not";class go{constructor(e){if((e==null?void 0:e.fields)==null)throw new Error('MiniSearch: option "fields" must be provided');const n=e.autoVacuum==null||e.autoVacuum===!0?fi:e.autoVacuum;this._options={...ui,...e,autoVacuum:n,searchOptions:{...Zl,...e.searchOptions||{}},autoSuggestOptions:{...Jp,...e.autoSuggestOptions||{}}},this._index=new Na,this._documentCount=0,this._documentIds=new Map,this._idToShortId=new Map,this._fieldIds={},this._fieldLength=new Map,this._avgFieldLength=[],this._nextId=0,this._storedFields=new Map,this._dirtCount=0,this._currentVacuum=null,this._enqueuedVacuum=null,this._enqueuedVacuumConditions=Oi,this.addFields(this._options.fields)}add(e){const{extractField:n,stringifyField:a,tokenize:o,processTerm:i,fields:s,idField:l}=this._options,u=n(e,l);if(u==null)throw new Error(`MiniSearch: document does not have ID field "${l}"`);if(this._idToShortId.has(u))throw new Error(`MiniSearch: duplicate ID ${u}`);const f=this.addDocumentId(u);this.saveStoredFields(f,e);for(const p of s){const _=n(e,p);if(_==null)continue;const x=o(a(_,p),p),b=this._fieldIds[p],k=new Set(x).size;this.addFieldLength(f,b,this._documentCount-1,k);for(const C of x){const g=i(C,p);if(Array.isArray(g))for(const y of g)this.addTerm(b,f,y);else g&&this.addTerm(b,f,g)}}}addAll(e){for(const n of e)this.add(n)}addAllAsync(e,n={}){const{chunkSize:a=10}=n,o={chunk:[],promise:Promise.resolve()},{chunk:i,promise:s}=e.reduce(({chunk:l,promise:u},f,p)=>(l.push(f),(p+1)%a===0?{chunk:[],promise:u.then(()=>new Promise(_=>setTimeout(_,0))).then(()=>this.addAll(l))}:{chunk:l,promise:u}),o);return s.then(()=>this.addAll(i))}remove(e){const{tokenize:n,processTerm:a,extractField:o,stringifyField:i,fields:s,idField:l}=this._options,u=o(e,l);if(u==null)throw new Error(`MiniSearch: document does not have ID field "${l}"`);const f=this._idToShortId.get(u);if(f==null)throw new Error(`MiniSearch: cannot remove document with ID ${u}: it is not in the index`);for(const p of s){const _=o(e,p);if(_==null)continue;const x=n(i(_,p),p),b=this._fieldIds[p],k=new Set(x).size;this.removeFieldLength(f,b,this._documentCount,k);for(const C of x){const g=a(C,p);if(Array.isArray(g))for(const y of g)this.removeTerm(b,f,y);else g&&this.removeTerm(b,f,g)}}this._storedFields.delete(f),this._documentIds.delete(f),this._idToShortId.delete(u),this._fieldLength.delete(f),this._documentCount-=1}removeAll(e){if(e)for(const n of e)this.remove(n);else{if(arguments.length>0)throw new Error("Expected documents to be present. Omit the argument to remove all documents.");this._index=new Na,this._documentCount=0,this._documentIds=new Map,this._idToShortId=new Map,this._fieldLength=new Map,this._avgFieldLength=[],this._storedFields=new Map,this._nextId=0}}discard(e){const n=this._idToShortId.get(e);if(n==null)throw new Error(`MiniSearch: cannot discard document with ID ${e}: it is not in the index`);this._idToShortId.delete(e),this._documentIds.delete(n),this._storedFields.delete(n),(this._fieldLength.get(n)||[]).forEach((a,o)=>{this.removeFieldLength(n,o,this._documentCount,a)}),this._fieldLength.delete(n),this._documentCount-=1,this._dirtCount+=1,this.maybeAutoVacuum()}maybeAutoVacuum(){if(this._options.autoVacuum===!1)return;const{minDirtFactor:e,minDirtCount:n,batchSize:a,batchWait:o}=this._options.autoVacuum;this.conditionalVacuum({batchSize:a,batchWait:o},{minDirtCount:n,minDirtFactor:e})}discardAll(e){const n=this._options.autoVacuum;try{this._options.autoVacuum=!1;for(const a of e)this.discard(a)}finally{this._options.autoVacuum=n}this.maybeAutoVacuum()}replace(e){const{idField:n,extractField:a}=this._options,o=a(e,n);this.discard(o),this.add(e)}vacuum(e={}){return this.conditionalVacuum(e)}conditionalVacuum(e,n){return this._currentVacuum?(this._enqueuedVacuumConditions=this._enqueuedVacuumConditions&&n,this._enqueuedVacuum!=null?this._enqueuedVacuum:(this._enqueuedVacuum=this._currentVacuum.then(()=>{const a=this._enqueuedVacuumConditions;return this._enqueuedVacuumConditions=Oi,this.performVacuuming(e,a)}),this._enqueuedVacuum)):this.vacuumConditionsMet(n)===!1?Promise.resolve():(this._currentVacuum=this.performVacuuming(e),this._currentVacuum)}async performVacuuming(e,n){const a=this._dirtCount;if(this.vacuumConditionsMet(n)){const o=e.batchSize||Li.batchSize,i=e.batchWait||Li.batchWait;let s=1;for(const[l,u]of this._index){for(const[f,p]of u)for(const[_]of p)this._documentIds.has(_)||(p.size<=1?u.delete(f):p.delete(_));this._index.get(l).size===0&&this._index.delete(l),s%o===0&&await new Promise(f=>setTimeout(f,i)),s+=1}this._dirtCount-=a}await null,this._currentVacuum=this._enqueuedVacuum,this._enqueuedVacuum=null}vacuumConditionsMet(e){if(e==null)return!0;let{minDirtCount:n,minDirtFactor:a}=e;return n=n||fi.minDirtCount,a=a||fi.minDirtFactor,this.dirtCount>=n&&this.dirtFactor>=a}get isVacuuming(){return this._currentVacuum!=null}get dirtCount(){return this._dirtCount}get dirtFactor(){return this._dirtCount/(1+this._documentCount+this._dirtCount)}has(e){return this._idToShortId.has(e)}getStoredFields(e){const n=this._idToShortId.get(e);if(n!=null)return this._storedFields.get(n)}search(e,n={}){const{searchOptions:a}=this._options,o={...a,...n},i=this.executeQuery(e,n),s=[];for(const[l,{score:u,terms:f,match:p}]of i){const _=f.length||1,x={id:this._documentIds.get(l),score:u*_,terms:Object.keys(p),queryTerms:f,match:p};Object.assign(x,this._storedFields.get(l)),(o.filter==null||o.filter(x))&&s.push(x)}return e===go.wildcard&&o.boostDocument==null||s.sort(td),s}autoSuggest(e,n={}){n={...this._options.autoSuggestOptions,...n};const a=new Map;for(const{score:i,terms:s}of this.search(e,n)){const l=s.join(" "),u=a.get(l);u!=null?(u.score+=i,u.count+=1):a.set(l,{score:i,terms:s,count:1})}const o=[];for(const[i,{score:s,terms:l,count:u}]of a)o.push({suggestion:i,terms:l,score:s/u});return o.sort(td),o}get documentCount(){return this._documentCount}get termCount(){return this._index.size}static loadJSON(e,n){if(n==null)throw new Error("MiniSearch: loadJSON should be given the same options used when serializing the index");return this.loadJS(JSON.parse(e),n)}static async loadJSONAsync(e,n){if(n==null)throw new Error("MiniSearch: loadJSON should be given the same options used when serializing the index");return this.loadJSAsync(JSON.parse(e),n)}static getDefault(e){if(ui.hasOwnProperty(e))return ci(ui,e);throw new Error(`MiniSearch: unknown option "${e}"`)}static loadJS(e,n){const{index:a,documentIds:o,fieldLength:i,storedFields:s,serializationVersion:l}=e,u=this.instantiateMiniSearch(e,n);u._documentIds=Cs(o),u._fieldLength=Cs(i),u._storedFields=Cs(s);for(const[f,p]of u._documentIds)u._idToShortId.set(p,f);for(const[f,p]of a){const _=new Map;for(const x of Object.keys(p)){let b=p[x];l===1&&(b=b.ds),_.set(parseInt(x,10),Cs(b))}u._index.set(f,_)}return u}static async loadJSAsync(e,n){const{index:a,documentIds:o,fieldLength:i,storedFields:s,serializationVersion:l}=e,u=this.instantiateMiniSearch(e,n);u._documentIds=await $s(o),u._fieldLength=await $s(i),u._storedFields=await $s(s);for(const[p,_]of u._documentIds)u._idToShortId.set(_,p);let f=0;for(const[p,_]of a){const x=new Map;for(const b of Object.keys(_)){let k=_[b];l===1&&(k=k.ds),x.set(parseInt(b,10),await $s(k))}++f%1e3===0&&await Gc(0),u._index.set(p,x)}return u}static instantiateMiniSearch(e,n){const{documentCount:a,nextId:o,fieldIds:i,averageFieldLength:s,dirtCount:l,serializationVersion:u}=e;if(u!==1&&u!==2)throw new Error("MiniSearch: cannot deserialize an index created with an incompatible version");const f=new go(n);return f._documentCount=a,f._nextId=o,f._idToShortId=new Map,f._fieldIds=i,f._avgFieldLength=s,f._dirtCount=l||0,f._index=new Na,f}executeQuery(e,n={}){if(e===go.wildcard)return this.executeWildcardQuery(n);if(typeof e!="string"){const x={...n,...e,queries:void 0},b=e.queries.map(k=>this.executeQuery(k,x));return this.combineResults(b,x.combineWith)}const{tokenize:a,processTerm:o,searchOptions:i}=this._options,s={tokenize:a,processTerm:o,...i,...n},{tokenize:l,processTerm:u}=s,_=l(e).flatMap(x=>u(x)).filter(x=>!!x).map(Gp(s)).map(x=>this.executeQuerySpec(x,s));return this.combineResults(_,s.combineWith)}executeQuerySpec(e,n){const a={...this._options.searchOptions,...n},o=(a.fields||this._options.fields).reduce((C,g)=>({...C,[g]:ci(a.boost,g)||1}),{}),{boostDocument:i,weights:s,maxFuzzy:l,bm25:u}=a,{fuzzy:f,prefix:p}={...Zl.weights,...s},_=this._index.get(e.term),x=this.termResults(e.term,e.term,1,e.termBoost,_,o,i,u);let b,k;if(e.prefix&&(b=this._index.atPrefix(e.term)),e.fuzzy){const C=e.fuzzy===!0?.2:e.fuzzy,g=C<1?Math.min(l,Math.round(e.term.length*C)):C;g&&(k=this._index.fuzzyGet(e.term,g))}if(b)for(const[C,g]of b){const y=C.length-e.term.length;if(!y)continue;k==null||k.delete(C);const I=p*C.length/(C.length+.3*y);this.termResults(e.term,C,I,e.termBoost,g,o,i,u,x)}if(k)for(const C of k.keys()){const[g,y]=k.get(C);if(!y)continue;const I=f*C.length/(C.length+y);this.termResults(e.term,C,I,e.termBoost,g,o,i,u,x)}return x}executeWildcardQuery(e){const n=new Map,a={...this._options.searchOptions,...e};for(const[o,i]of this._documentIds){const s=a.boostDocument?a.boostDocument(i,"",this._storedFields.get(o)):1;n.set(o,{score:s,terms:[],match:{}})}return n}combineResults(e,n=cl){if(e.length===0)return new Map;const a=n.toLowerCase(),o=Up[a];if(!o)throw new Error(`Invalid combination operator: ${n}`);return e.reduce(o)||new Map}toJSON(){const e=[];for(const[n,a]of this._index){const o={};for(const[i,s]of a)o[i]=Object.fromEntries(s);e.push([n,o])}return{documentCount:this._documentCount,nextId:this._nextId,documentIds:Object.fromEntries(this._documentIds),fieldIds:this._fieldIds,fieldLength:Object.fromEntries(this._fieldLength),averageFieldLength:this._avgFieldLength,storedFields:Object.fromEntries(this._storedFields),dirtCount:this._dirtCount,index:e,serializationVersion:2}}termResults(e,n,a,o,i,s,l,u,f=new Map){if(i==null)return f;for(const p of Object.keys(s)){const _=s[p],x=this._fieldIds[p],b=i.get(x);if(b==null)continue;let k=b.size;const C=this._avgFieldLength[x];for(const g of b.keys()){if(!this._documentIds.has(g)){this.removeTerm(x,g,n),k-=1;continue}const y=l?l(this._documentIds.get(g),n,this._storedFields.get(g)):1;if(!y)continue;const I=b.get(g),O=this._fieldLength.get(g)[x],M=Kp(I,k,this._documentCount,O,C,u),ee=a*o*_*y*M,fe=f.get(g);if(fe){fe.score+=ee,Yp(fe.terms,e);const L=ci(fe.match,n);L?L.push(p):fe.match[n]=[p]}else f.set(g,{score:ee,terms:[e],match:{[n]:[p]}})}}return f}addTerm(e,n,a){const o=this._index.fetch(a,rd);let i=o.get(e);if(i==null)i=new Map,i.set(n,1),o.set(e,i);else{const s=i.get(n);i.set(n,(s||0)+1)}}removeTerm(e,n,a){if(!this._index.has(a)){this.warnDocumentChanged(n,e,a);return}const o=this._index.fetch(a,rd),i=o.get(e);i==null||i.get(n)==null?this.warnDocumentChanged(n,e,a):i.get(n)<=1?i.size<=1?o.delete(e):i.delete(n):i.set(n,i.get(n)-1),this._index.get(a).size===0&&this._index.delete(a)}warnDocumentChanged(e,n,a){for(const o of Object.keys(this._fieldIds))if(this._fieldIds[o]===n){this._options.logger("warn",`MiniSearch: document with ID ${this._documentIds.get(e)} has changed before removal: term "${a}" was not present in field "${o}". Removing a document after it has changed can corrupt the index!`,"version_conflict");return}}addDocumentId(e){const n=this._nextId;return this._idToShortId.set(e,n),this._documentIds.set(n,e),this._documentCount+=1,this._nextId+=1,n}addFields(e){for(let n=0;n<e.length;n++)this._fieldIds[e[n]]=n}addFieldLength(e,n,a,o){let i=this._fieldLength.get(e);i==null&&this._fieldLength.set(e,i=[]),i[n]=o;const l=(this._avgFieldLength[n]||0)*a+o;this._avgFieldLength[n]=l/(a+1)}removeFieldLength(e,n,a,o){if(a===1){this._avgFieldLength[n]=0;return}const i=this._avgFieldLength[n]*a-o;this._avgFieldLength[n]=i/(a-1)}saveStoredFields(e,n){const{storeFields:a,extractField:o}=this._options;if(a==null||a.length===0)return;let i=this._storedFields.get(e);i==null&&this._storedFields.set(e,i={});for(const s of a){const l=o(n,s);l!==void 0&&(i[s]=l)}}}go.wildcard=Symbol("*");const ci=(t,e)=>Object.prototype.hasOwnProperty.call(t,e)?t[e]:void 0,Up={[cl]:(t,e)=>{for(const n of e.keys()){const a=t.get(n);if(a==null)t.set(n,e.get(n));else{const{score:o,terms:i,match:s}=e.get(n);a.score=a.score+o,a.match=Object.assign(a.match,s),ed(a.terms,i)}}return t},[Kc]:(t,e)=>{const n=new Map;for(const a of e.keys()){const o=t.get(a);if(o==null)continue;const{score:i,terms:s,match:l}=e.get(a);ed(o.terms,s),n.set(a,{score:o.score+i,terms:o.terms,match:Object.assign(o.match,l)})}return n},[Hp]:(t,e)=>{for(const n of e.keys())t.delete(n);return t}},Wp={k:1.2,b:.7,d:.5},Kp=(t,e,n,a,o,i)=>{const{k:s,b:l,d:u}=i;return Math.log(1+(n-e+.5)/(e+.5))*(u+t*(s+1)/(t+s*(1-l+l*a/o)))},Gp=t=>(e,n,a)=>{const o=typeof t.fuzzy=="function"?t.fuzzy(e,n,a):t.fuzzy||!1,i=typeof t.prefix=="function"?t.prefix(e,n,a):t.prefix===!0,s=typeof t.boostTerm=="function"?t.boostTerm(e,n,a):1;return{term:e,fuzzy:o,prefix:i,termBoost:s}},ui={idField:"id",extractField:(t,e)=>t[e],stringifyField:(t,e)=>t.toString(),tokenize:t=>t.split(Xp),processTerm:t=>t.toLowerCase(),fields:void 0,searchOptions:void 0,storeFields:[],logger:(t,e)=>{typeof(console==null?void 0:console[t])=="function"&&console[t](e)},autoVacuum:!0},Zl={combineWith:cl,prefix:!1,fuzzy:!1,maxFuzzy:6,boost:{},weights:{fuzzy:.45,prefix:.375},bm25:Wp},Jp={combineWith:Kc,prefix:(t,e,n)=>e===n.length-1},Li={batchSize:1e3,batchWait:10},Oi={minDirtFactor:.1,minDirtCount:20},fi={...Li,...Oi},Yp=(t,e)=>{t.includes(e)||t.push(e)},ed=(t,e)=>{for(const n of e)t.includes(n)||t.push(n)},td=({score:t},{score:e})=>e-t,rd=()=>new Map,Cs=t=>{const e=new Map;for(const n of Object.keys(t))e.set(parseInt(n,10),t[n]);return e},$s=async t=>{const e=new Map;let n=0;for(const a of Object.keys(t))e.set(parseInt(a,10),t[a]),++n%1e3===0&&await Gc(0);return e},Gc=t=>new Promise(e=>setTimeout(e,t)),Xp=/[\n\r\p{Z}\p{P}]+/u;function Qp(){try{const t=localStorage.getItem("dartlab-bookmarks");return t?JSON.parse(t):{}}catch{return{}}}function Zp(t){try{localStorage.setItem("dartlab-bookmarks",JSON.stringify(t))}catch{}}function eh(){let t=K(null),e=K(null),n=K(null),a=K(!1),o=K(null),i=K(null),s=K(Bt(new Set)),l=K(null),u=K(!1),f=K(null),p=new Map,_=K(null),x=K(!1),b=K(null),k=K(!1),C=K(Bt(new Map)),g=K(null),y=null,I=K(!1),O=K(Bt(Qp()));async function M(N){var W,H;if(!(N===r(t)&&(r(n)||r(a)))){v(t,N,!0),v(e,null),v(n,null),v(o,null),v(i,null),v(l,null),v(f,null),p=new Map,v(s,new Set,!0),v(_,null),v(b,null),v(C,new Map,!0),y=null,v(I,!1),v(a,!0);try{const E=await Ov(N);if(v(n,E,!0),v(e,E.corpName,!0),((W=E.chapters)==null?void 0:W.length)>0&&(v(s,new Set([E.chapters[0].chapter]),!0),((H=E.chapters[0].topics)==null?void 0:H.length)>0)){const q=E.chapters[0].topics[0];await G(q.topic,E.chapters[0].chapter)}ee(N),fe(N),L(N)}catch(E){console.error("TOC 로드 실패:",E)}v(a,!1)}}async function ee(N){var W;if(((W=r(_))==null?void 0:W.stockCode)!==N){v(x,!0);try{const H=await Fv(N);H.available?v(_,H,!0):v(_,null)}catch{v(_,null)}v(x,!1)}}async function fe(N){v(k,!0);try{const W=await Vv(N);W.available?v(b,W,!0):v(b,null)}catch{v(b,null)}v(k,!1)}async function L(N){try{const W=await jv(N);if(!W.documents||W.documents.length===0)return;const H=new go({fields:["label","text"],storeFields:["topic","label","chapter","period","blockType"],searchOptions:{boost:{label:3},fuzzy:.2,prefix:!0}});H.addAll(W.documents),y=H,v(I,!0)}catch(W){console.error("SearchIndex 로드 실패:",W)}}function S(N){if(!y||!(N!=null&&N.trim()))return[];const W=y.search(N.trim(),{fuzzy:.2,prefix:!0,boost:{label:3}}),H=new Map;for(const E of W){const q=E.topic;(!H.has(q)||H.get(q).score<E.score)&&H.set(q,E)}return[...H.values()].sort((E,q)=>q.score-E.score).slice(0,20).map(E=>({topic:E.topic,label:E.label,chapter:E.chapter,period:E.period,blockType:E.blockType,score:E.score,source:"minisearch"}))}function X(N){v(g,N||null,!0)}async function G(N,W){if(N!==r(o)){if(v(o,N,!0),v(g,null),v(i,W,!0),W&&!r(s).has(W)&&v(s,new Set([...r(s),W]),!0),p.has(N)){v(l,p.get(N),!0),v(V,new Set([...r(V),N]),!0);return}v(u,!0),v(l,null),v(f,null);try{const[H,E]=await Promise.allSettled([ql(r(t),N),Dv(r(t),N)]);H.status==="fulfilled"&&(v(l,H.value,!0),p.set(N,H.value)),E.status==="fulfilled"&&v(f,E.value,!0)}catch(H){console.error("Topic 로드 실패:",H)}v(u,!1)}}let me=new Set,V=K(Bt(new Set));async function ze(N){if(!(!N||!r(t)||p.has(N)||me.has(N))){me.add(N);try{const W=await ql(r(t),N);p.set(N,W)}catch{}me.delete(N)}}function j(N){const W=new Set(r(s));W.has(N)?W.delete(N):W.add(N),v(s,W,!0)}function B(N){return r(C).get(N)??null}function le(N,W){const H=new Map(r(C));H.set(N,W),v(C,H,!0)}function we(){return r(O)[r(t)]||[]}function U(N){return(r(O)[r(t)]||[]).includes(N)}function ne(N){const W=r(O)[r(t)]||[],H=W.includes(N)?W.filter(E=>E!==N):[N,...W];v(O,{...r(O),[r(t)]:H},!0),Zp(r(O))}return{get stockCode(){return r(t)},get corpName(){return r(e)},get toc(){return r(n)},get tocLoading(){return r(a)},get selectedTopic(){return r(o)},get selectedChapter(){return r(i)},get expandedChapters(){return r(s)},get topicData(){return r(l)},get topicLoading(){return r(u)},get diffSummary(){return r(f)},get insightData(){return r(_)},get insightLoading(){return r(x)},get networkData(){return r(b)},get networkLoading(){return r(k)},get searchHighlight(){return r(g)},get searchIndexReady(){return r(I)},loadCompany:M,setSearchHighlight:X,searchSections:S,get visitedTopics(){return r(V)},selectTopic:G,prefetchTopic:ze,toggleChapter:j,getTopicSummary:B,setTopicSummary:le,getBookmarks:we,isBookmarked:U,toggleBookmark:ne}}var th=h("<a><!></a>"),rh=h("<button><!></button>");function nh(t,e){Ir(e,!0);let n=je(e,"variant",3,"default"),a=je(e,"size",3,"default"),o=Cv(e,["$$slots","$$events","$$legacy","variant","size","class","children"]);const i={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},s={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=Ce(),u=ae(l);{var f=_=>{var x=th();Ls(x,k=>({class:k,...o}),[()=>wr("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",i[n()],s[a()],e.class)]);var b=d(x);Ai(b,()=>e.children),c(_,x)},p=_=>{var x=rh();Ls(x,k=>({class:k,...o}),[()=>wr("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",i[n()],s[a()],e.class)]);var b=d(x);Ai(b,()=>e.children),c(_,x)};$(u,_=>{e.href?_(f):_(p,-1)})}c(t,l),Ar()}bf();/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const ah={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const oh=t=>{for(const e in t)if(e.startsWith("aria-")||e==="role"||e==="title")return!0;return!1};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const nd=(...t)=>t.filter((e,n,a)=>!!e&&e.trim()!==""&&a.indexOf(e)===n).join(" ").trim();var sh=ms("<svg><!><!></svg>");function mt(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]),a=lt(n,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);Ir(e,!1);let o=je(e,"name",8,void 0),i=je(e,"color",8,"currentColor"),s=je(e,"size",8,24),l=je(e,"strokeWidth",8,2),u=je(e,"absoluteStrokeWidth",8,!1),f=je(e,"iconNode",24,()=>[]);wv();var p=sh();Ls(p,(b,k,C)=>({...ah,...b,...a,width:s(),height:s(),stroke:i(),"stroke-width":k,class:C}),[()=>oh(a)?void 0:{"aria-hidden":"true"},()=>(Ga(u()),Ga(l()),Ga(s()),co(()=>u()?Number(l())*24/Number(s()):l())),()=>(Ga(nd),Ga(o()),Ga(n),co(()=>nd("lucide-icon","lucide",o()?`lucide-${o()}`:"",n.class)))]);var _=d(p);Ae(_,1,f,Ne,(b,k)=>{var C=D(()=>Ji(r(k),2));let g=()=>r(C)[0],y=()=>r(C)[1];var I=Ce(),O=ae(I);vv(O,g,!0,(M,ee)=>{Ls(M,()=>({...y()}))}),c(b,I)});var x=m(_);pt(x,e,"default",{}),c(t,p),Ar()}function ih(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];mt(t,ht({name:"activity"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Jc(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M8 3 4 7l4 4"}],["path",{d:"M4 7h16"}],["path",{d:"m16 21 4-4-4-4"}],["path",{d:"M20 17H4"}]];mt(t,ht({name:"arrow-left-right"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function lh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"m12 5 7 7-7 7"}]];mt(t,ht({name:"arrow-right"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function dh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];mt(t,ht({name:"arrow-up"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Di(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 7v14"}],["path",{d:"M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"}]];mt(t,ht({name:"book-open"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function vi(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];mt(t,ht({name:"brain"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ad(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 12h4"}],["path",{d:"M10 8h4"}],["path",{d:"M14 21v-3a2 2 0 0 0-4 0v3"}],["path",{d:"M6 10H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2"}],["path",{d:"M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"}]];mt(t,ht({name:"building-2"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Rs(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]];mt(t,ht({name:"chart-column"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ri(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M20 6 9 17l-5-5"}]];mt(t,ht({name:"check"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ul(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m6 9 6 6 6-6"}]];mt(t,ht({name:"chevron-down"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Yc(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m18 15-6-6-6 6"}]];mt(t,ht({name:"chevron-up"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Xc(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m9 18 6-6-6-6"}]];mt(t,ht({name:"chevron-right"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ja(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];mt(t,ht({name:"circle-alert"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function as(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];mt(t,ht({name:"circle-check"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ls(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];mt(t,ht({name:"clock"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ch(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];mt(t,ht({name:"code"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function uh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];mt(t,ht({name:"coffee"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function od(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]];mt(t,ht({name:"copy"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Jo(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];mt(t,ht({name:"database"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function os(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];mt(t,ht({name:"download"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function fh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["line",{x1:"5",x2:"19",y1:"9",y2:"9"}],["line",{x1:"5",x2:"19",y1:"15",y2:"15"}]];mt(t,ht({name:"equal"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function sd(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];mt(t,ht({name:"external-link"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function vh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];mt(t,ht({name:"eye"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function zn(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];mt(t,ht({name:"file-text"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ph(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];mt(t,ht({name:"github"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function id(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];mt(t,ht({name:"key"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function hh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 8h.01"}],["path",{d:"M12 12h.01"}],["path",{d:"M14 8h.01"}],["path",{d:"M16 12h.01"}],["path",{d:"M18 8h.01"}],["path",{d:"M6 8h.01"}],["path",{d:"M7 16h10"}],["path",{d:"M8 12h.01"}],["rect",{width:"20",height:"16",x:"2",y:"4",rx:"2"}]];mt(t,ht({name:"keyboard"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ur(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];mt(t,ht({name:"loader-circle"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function mh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];mt(t,ht({name:"log-out"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Qc(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"m21 3-7 7"}],["path",{d:"m3 21 7-7"}],["path",{d:"M9 21H3v-6"}]];mt(t,ht({name:"maximize-2"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function xh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];mt(t,ht({name:"menu"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function js(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];mt(t,ht({name:"message-square"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Zc(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m14 10 7-7"}],["path",{d:"M20 10h-6V4"}],["path",{d:"m3 21 7-7"}],["path",{d:"M4 14h6v6"}]];mt(t,ht({name:"minimize-2"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function eu(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}]];mt(t,ht({name:"minus"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function tu(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];mt(t,ht({name:"panel-left-close"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function gh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m14 9 3 3-3 3"}]];mt(t,ht({name:"panel-left-open"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ji(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];mt(t,ht({name:"plus"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function _h(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];mt(t,ht({name:"refresh-cw"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function xa(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];mt(t,ht({name:"search"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function bh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];mt(t,ht({name:"settings"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function wh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"}]];mt(t,ht({name:"shield"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ru(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];mt(t,ht({name:"sparkles"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function yh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];mt(t,ht({name:"square"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Fi(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"}]];mt(t,ht({name:"star"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Vi(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];mt(t,ht({name:"table-2"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function kh(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];mt(t,ht({name:"terminal"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ch(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];mt(t,ht({name:"trash-2"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ts(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M16 7h6v6"}],["path",{d:"m22 7-8.5 8.5-5-5L2 17"}]];mt(t,ht({name:"trending-up"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ss(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];mt(t,ht({name:"triangle-alert"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function nu(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["path",{d:"M16 3.128a4 4 0 0 1 0 7.744"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87"}],["circle",{cx:"9",cy:"7",r:"4"}]];mt(t,ht({name:"users"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function $h(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"}],["path",{d:"M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"}]];mt(t,ht({name:"wallet"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ld(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];mt(t,ht({name:"wrench"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Fa(t,e){const n=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];mt(t,ht({name:"x"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=Ce(),l=ae(s);pt(l,e,"default",{}),c(o,s)},$$slots:{default:!0}}))}var Sh=h("<!> 새 대화",1),Mh=h('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),zh=h('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),Th=h('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),Ih=h('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40"><span class="text-[10px] text-dl-text-dim font-mono"> </span></div>'),Ah=h('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),Eh=h("<button><!></button>"),Nh=h('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),Ph=h("<aside><!></aside>");function Lh(t,e){Ir(e,!0);let n=je(e,"conversations",19,()=>[]),a=je(e,"activeId",3,null),o=je(e,"open",3,!0),i=je(e,"version",3,""),s=K("");function l(k){const C=new Date().setHours(0,0,0,0),g=C-864e5,y=C-7*864e5,I={오늘:[],어제:[],"이번 주":[],이전:[]};for(const M of k)M.updatedAt>=C?I.오늘.push(M):M.updatedAt>=g?I.어제.push(M):M.updatedAt>=y?I["이번 주"].push(M):I.이전.push(M);const O=[];for(const[M,ee]of Object.entries(I))ee.length>0&&O.push({label:M,items:ee});return O}let u=D(()=>r(s).trim()?n().filter(k=>k.title.toLowerCase().includes(r(s).toLowerCase())):n()),f=D(()=>l(r(u)));var p=Ph(),_=d(p);{var x=k=>{var C=Ah(),g=m(d(C),2),y=d(g);nh(y,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return e.onNewChat},children:(L,S)=>{var X=Sh(),G=ae(X);ji(G,{size:16}),c(L,X)},$$slots:{default:!0}});var I=m(g,2);{var O=L=>{var S=Mh(),X=d(S),G=d(X);xa(G,{size:12,class:"text-dl-text-dim flex-shrink-0"});var me=m(G,2);Ea(me,()=>r(s),V=>v(s,V)),c(L,S)};$(I,L=>{n().length>3&&L(O)})}var M=m(I,2);Ae(M,21,()=>r(f),Ne,(L,S)=>{var X=Th(),G=d(X),me=d(G),V=m(G,2);Ae(V,17,()=>r(S).items,Ne,(ze,j)=>{var B=zh(),le=d(B),we=d(le);js(we,{size:14,class:"flex-shrink-0 opacity-50"});var U=m(we,2),ne=d(U),N=m(le,2),W=d(N);Ch(W,{size:12}),z(H=>{Ue(B,1,H),ir(le,"aria-current",r(j).id===a()?"true":void 0),T(ne,r(j).title),ir(N,"aria-label",`${r(j).title} 삭제`)},[()=>xr(wr("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",r(j).id===a()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),he("click",le,()=>{var H;return(H=e.onSelect)==null?void 0:H.call(e,r(j).id)}),he("click",N,H=>{var E;H.stopPropagation(),(E=e.onDelete)==null||E.call(e,r(j).id)}),c(ze,B)}),z(()=>T(me,r(S).label)),c(L,X)});var ee=m(M,2);{var fe=L=>{var S=Ih(),X=d(S),G=d(X);z(()=>T(G,`v${i()??""}`)),c(L,S)};$(ee,L=>{i()&&L(fe)})}c(k,C)},b=k=>{var C=Nh(),g=m(d(C),2),y=d(g);ji(y,{size:18});var I=m(g,2);Ae(I,21,()=>n().slice(0,10),Ne,(O,M)=>{var ee=Eh(),fe=d(ee);js(fe,{size:16}),z(L=>{Ue(ee,1,L),ir(ee,"title",r(M).title)},[()=>xr(wr("p-2 rounded-lg transition-colors w-full flex justify-center",r(M).id===a()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),he("click",ee,()=>{var L;return(L=e.onSelect)==null?void 0:L.call(e,r(M).id)}),c(O,ee)}),he("click",g,function(...O){var M;(M=e.onNewChat)==null||M.apply(this,O)}),c(k,C)};$(_,k=>{o()?k(x):k(b,-1)})}z(k=>Ue(p,1,k),[()=>xr(wr("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",o()?"w-[260px]":"w-[52px]"))]),c(t,p),Ar()}Kr(["click"]);var Oh=h('<button class="send-btn active"><!></button>'),Dh=h("<button><!></button>"),Rh=h('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),jh=h('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),Fh=h('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),Vh=h('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function au(t,e){Ir(e,!0);let n=je(e,"inputText",15,""),a=je(e,"isLoading",3,!1),o=je(e,"large",3,!1),i=je(e,"placeholder",3,"메시지를 입력하세요..."),s=K(Bt([])),l=K(!1),u=K(-1),f=null,p=K(void 0);function _(S){var X;if(r(l)&&r(s).length>0){if(S.key==="ArrowDown"){S.preventDefault(),v(u,(r(u)+1)%r(s).length);return}if(S.key==="ArrowUp"){S.preventDefault(),v(u,r(u)<=0?r(s).length-1:r(u)-1,!0);return}if(S.key==="Enter"&&r(u)>=0){S.preventDefault(),k(r(s)[r(u)]);return}if(S.key==="Escape"){v(l,!1),v(u,-1);return}}S.key==="Enter"&&!S.shiftKey&&(S.preventDefault(),v(l,!1),(X=e.onSend)==null||X.call(e))}function x(S){S.target.style.height="auto",S.target.style.height=Math.min(S.target.scrollHeight,200)+"px"}function b(S){x(S);const X=n();f&&clearTimeout(f),X.length>=2&&!/\s/.test(X.slice(-1))?f=setTimeout(async()=>{var G;try{const me=await sl(X.trim());((G=me.results)==null?void 0:G.length)>0?(v(s,me.results.slice(0,6),!0),v(l,!0),v(u,-1)):v(l,!1)}catch{v(l,!1)}},300):v(l,!1)}function k(S){var X;n(`${S.corpName} `),v(l,!1),v(u,-1),(X=e.onCompanySelect)==null||X.call(e,S),r(p)&&r(p).focus()}function C(){setTimeout(()=>{v(l,!1)},200)}var g=Vh(),y=d(g),I=d(y);Jn(I,S=>v(p,S),()=>r(p));var O=m(I,2);{var M=S=>{var X=Oh(),G=d(X);yh(G,{size:14}),he("click",X,function(...me){var V;(V=e.onStop)==null||V.apply(this,me)}),c(S,X)},ee=S=>{var X=Dh(),G=d(X);{let me=D(()=>o()?18:16);dh(G,{get size(){return r(me)},strokeWidth:2.5})}z((me,V)=>{Ue(X,1,me),X.disabled=V},[()=>xr(wr("send-btn",n().trim()&&"active")),()=>!n().trim()]),he("click",X,()=>{var me;v(l,!1),(me=e.onSend)==null||me.call(e)}),c(S,X)};$(O,S=>{a()&&e.onStop?S(M):S(ee,-1)})}var fe=m(y,2);{var L=S=>{var X=Fh();Ae(X,21,()=>r(s),Ne,(G,me,V)=>{var ze=jh(),j=d(ze);xa(j,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var B=m(j,2),le=d(B),we=d(le),U=m(le,2),ne=d(U),N=m(B,2);{var W=H=>{var E=Rh(),q=d(E);z(()=>T(q,r(me).sector)),c(H,E)};$(N,H=>{r(me).sector&&H(W)})}z(H=>{Ue(ze,1,H),T(we,r(me).corpName),T(ne,`${r(me).stockCode??""} · ${(r(me).market||"")??""}`)},[()=>xr(wr("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",V===r(u)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),he("mousedown",ze,()=>k(r(me))),xn("mouseenter",ze,()=>{v(u,V,!0)}),c(G,ze)}),c(S,X)};$(fe,S=>{r(l)&&r(s).length>0&&S(L)})}z(S=>{Ue(y,1,S),ir(I,"placeholder",i())},[()=>xr(wr("input-box",o()&&"large"))]),he("keydown",I,_),he("input",I,b),xn("blur",I,C),Ea(I,n),c(t,g),Ar()}Kr(["keydown","input","click","mousedown"]);var Bh=h('<button class="rounded-full border border-dl-border/60 bg-dl-bg-card/40 px-3 py-1.5 text-[12px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"> </button>'),qh=h(`<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[580px] flex flex-col items-center"><div class="relative mb-8"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p> <div class="mb-6 max-w-[520px] rounded-2xl border border-dl-border/50 bg-dl-bg-card/50 px-4 py-3 text-left"><div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">Evidence First</div> <div class="mt-2 text-[13px] leading-relaxed text-dl-text-muted">DartLab은 재무 수치와 서술 텍스트를 함께 읽고, 표준화된 계정과 원문 근거를 같은 흐름에서 확인하도록 설계되어 있습니다.
				DART와 EDGAR를 포함한 40개 모듈 이상의 기능 범위를 먼저 물어본 뒤 바로 탐색을 시작할 수 있습니다.</div></div> <div class="w-full"><!></div> <div class="mt-5 flex w-full flex-wrap justify-center gap-2"></div></div></div>`);function Hh(t,e){Ir(e,!0);let n=je(e,"inputText",15,"");const a=["지금 dartlab에서 할 수 있는 기능을 먼저 정리해줘","EDGAR에서 추가로 받을 수 있는 데이터와 방법을 알려줘","OpenDart와 OpenEdgar로 가능한 일을 비교해줘","GPT 연결 시 현재 UI에서 가능한 코딩 작업 범위를 알려줘"];var o=qh(),i=d(o),s=m(d(i),8),l=d(s);au(l,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return e.onSend},get onCompanySelect(){return e.onCompanySelect},get inputText(){return n()},set inputText(f){n(f)}});var u=m(s,2);Ae(u,21,()=>a,Ne,(f,p)=>{var _=Bh(),x=d(_);z(()=>T(x,r(p))),he("click",_,()=>{var b;return(b=e.onSend)==null?void 0:b.call(e,r(p))}),c(f,_)}),c(t,o),Ar()}Kr(["click"]);var Uh=h("<span><!></span>");function Yo(t,e){Ir(e,!0);let n=je(e,"variant",3,"default");const a={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var o=Uh(),i=d(o);Ai(i,()=>e.children),z(s=>Ue(o,1,s),[()=>xr(wr("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",a[n()],e.class))]),c(t,o),Ar()}function Wh(t){const e=t.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(e)||e==="-"||e==="0"}function Va(t){if(!t)return"";let e=[],n=[],a=t.replace(/```(\w*)\n([\s\S]*?)```/g,(i,s,l)=>{const u=e.length;return e.push(l.trimEnd()),`
%%CODE_${u}%%
`});a=a.replace(/((?:^\|.+\|$\n?)+)/gm,i=>{const s=i.trim().split(`
`).filter(x=>x.trim());let l=null,u=-1,f=[];for(let x=0;x<s.length;x++)if(s[x].slice(1,-1).split("|").map(k=>k.trim()).every(k=>/^[\-:]+$/.test(k))){u=x;break}u>0?(l=s[u-1],f=s.slice(u+1)):(u===0||(l=s[0]),f=s.slice(1));let p="<table>";if(l){const x=l.slice(1,-1).split("|").map(b=>b.trim());p+="<thead><tr>"+x.map(b=>`<th>${b.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(f.length>0){p+="<tbody>";for(const x of f){const b=x.slice(1,-1).split("|").map(k=>k.trim());p+="<tr>"+b.map(k=>{let C=k.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${Wh(k)?' class="num"':""}>${C}</td>`}).join("")+"</tr>"}p+="</tbody>"}p+="</table>";let _=n.length;return n.push(p),`
%%TABLE_${_}%%
`});let o=a.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");o=o.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,i=>"<ul>"+i.replace(/<br>/g,"")+"</ul>");for(let i=0;i<n.length;i++)o=o.replace(`%%TABLE_${i}%%`,n[i]);for(let i=0;i<e.length;i++){const s=e[i].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");o=o.replace(`%%CODE_${i}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${i}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${s}</code></pre></div>`)}return o=o.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(i,s)=>s.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+o+"</p>"}var Kh=h('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),Gh=h('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),Jh=h('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),Yh=h('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),Xh=h('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!> <!> <!> <!></div></div>'),Qh=h('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),Zh=h('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),em=h('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),tm=h("<span> </span>"),rm=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-bold border bg-red-500/10 text-red-400 border-red-500/20"> </span>'),nm=h('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-1.5"><!> <!></div>'),am=h('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!> <!></button>'),om=h("<button><!> </button>"),sm=h('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),im=h('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),lm=h('<!> <span class="text-dl-text-dim"> </span>',1),dm=h('<div class="flex items-center gap-2 text-[11px]"><!></div>'),cm=h('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),um=h('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),fm=h('<div class="message-committed"><!></div>'),vm=h('<div><div class="message-live-label"> </div> <pre> </pre></div>'),pm=h('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),hm=h('<span class="text-dl-accent/60"> </span>'),mm=h('<span class="text-dl-success/60"> </span>'),xm=h('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),gm=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),_m=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),bm=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),wm=h('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),ym=h("<!>  <div><!> <!></div> <!>",1),km=h('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),Cm=h('<span class="text-[10px] text-dl-text-dim"> </span>'),$m=h('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),Sm=h("<button> </button>"),Mm=h('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),zm=h("<button>시스템 프롬프트</button>"),Tm=h("<button>LLM 입력</button>"),Im=h('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),Am=h('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),Em=h('<span class="text-dl-text"> </span>'),Nm=h('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),Pm=h('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),Lm=h('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Om=h("<!> <!>",1);function Dm(t,e){Ir(e,!0);let n=K(null),a=K("context"),o=K("raw"),i=D(()=>{var E,q,J,Y,ye,Se;if(!e.message.loading)return"";if(e.message.text)return"응답 작성 중";if(((E=e.message.toolEvents)==null?void 0:E.length)>0){const te=[...e.message.toolEvents].reverse().find(tt=>tt.type==="call"),Oe=((q=te==null?void 0:te.arguments)==null?void 0:q.module)||((J=te==null?void 0:te.arguments)==null?void 0:J.keyword)||"";return`도구 실행 중 — ${(te==null?void 0:te.name)||""}${Oe?` (${Oe})`:""}`}if(((Y=e.message.contexts)==null?void 0:Y.length)>0){const te=e.message.contexts[e.message.contexts.length-1];return`데이터 분석 중 — ${(te==null?void 0:te.label)||(te==null?void 0:te.module)||""}`}return e.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(ye=e.message.meta)!=null&&ye.company?`${e.message.meta.company} 데이터 검색 중`:(Se=e.message.meta)!=null&&Se.includedModules?"분석 모듈 선택 완료":"생각 중"}),s=D(()=>{var E;return e.message.company||((E=e.message.meta)==null?void 0:E.company)||null});const l={capability:"기능 탐색",coding:"코딩 작업",company_explore:"회사 탐색",company_analysis:"회사 분석",follow_up:"후속 질문",general_chat:"일반 대화"};let u=D(()=>{var E;return(E=e.message.meta)!=null&&E.dialogueMode?l[e.message.meta.dialogueMode]||e.message.meta.dialogueMode:null}),f=D(()=>{var E,q,J;return e.message.systemPrompt||e.message.userContent||((E=e.message.contexts)==null?void 0:E.length)>0||((q=e.message.meta)==null?void 0:q.includedModules)||((J=e.message.toolEvents)==null?void 0:J.length)>0}),p=D(()=>{var q;const E=(q=e.message.meta)==null?void 0:q.dataYearRange;return E?typeof E=="string"?E:E.min_year&&E.max_year?`${E.min_year}~${E.max_year}년`:null:null});function _(E){if(!E)return 0;const q=(E.match(/[\uac00-\ud7af]/g)||[]).length,J=E.length-q;return Math.round(q*1.5+J/3.5)}function x(E){return E>=1e3?(E/1e3).toFixed(1)+"k":String(E)}let b=D(()=>{var q;let E=0;if(e.message.systemPrompt&&(E+=_(e.message.systemPrompt)),e.message.userContent)E+=_(e.message.userContent);else if(((q=e.message.contexts)==null?void 0:q.length)>0)for(const J of e.message.contexts)E+=_(J.text);return E}),k=D(()=>_(e.message.text)),C=K(void 0);const g=/^\s*\|.+\|\s*$/;function y(E,q){if(!E)return{committed:"",draft:"",draftType:"none"};if(!q)return{committed:E,draft:"",draftType:"none"};const J=E.split(`
`);let Y=J.length;E.endsWith(`
`)||(Y=Math.min(Y,J.length-1));let ye=0,Se=-1;for(let Ge=0;Ge<J.length;Ge++)J[Ge].trim().startsWith("```")&&(ye+=1,Se=Ge);ye%2===1&&Se>=0&&(Y=Math.min(Y,Se));let te=-1;for(let Ge=J.length-1;Ge>=0;Ge--){const rt=J[Ge];if(!rt.trim())break;if(g.test(rt))te=Ge;else{te=-1;break}}if(te>=0&&(Y=Math.min(Y,te)),Y<=0)return{committed:"",draft:E,draftType:te===0?"table":ye%2===1?"code":"text"};const Oe=J.slice(0,Y).join(`
`),tt=J.slice(Y).join(`
`);let ot="text";return tt&&te>=Y?ot="table":tt&&ye%2===1&&(ot="code"),{committed:Oe,draft:tt,draftType:ot}}const I='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',O='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function M(E){var ye;const q=E.target.closest(".code-copy-btn");if(!q)return;const J=q.closest(".code-block-wrap"),Y=((ye=J==null?void 0:J.querySelector("code"))==null?void 0:ye.textContent)||"";navigator.clipboard.writeText(Y).then(()=>{q.innerHTML=O,setTimeout(()=>{q.innerHTML=I},2e3)})}function ee(E){if(e.onOpenEvidence){e.onOpenEvidence("contexts",E);return}v(n,E,!0),v(a,"context"),v(o,"rendered")}function fe(){if(e.onOpenEvidence){e.onOpenEvidence("system");return}v(n,0),v(a,"system"),v(o,"raw")}function L(){if(e.onOpenEvidence){e.onOpenEvidence("snapshot");return}v(n,0),v(a,"snapshot")}function S(E){var q;if(e.onOpenEvidence){const J=(q=e.message.toolEvents)==null?void 0:q[E];e.onOpenEvidence((J==null?void 0:J.type)==="result"?"tool-results":"tool-calls",E);return}v(n,E,!0),v(a,"tool"),v(o,"raw")}function X(){if(e.onOpenEvidence){e.onOpenEvidence("input");return}v(n,0),v(a,"userContent"),v(o,"raw")}function G(){v(n,null)}function me(E){var q,J,Y,ye;return E?E.type==="call"?((q=E.arguments)==null?void 0:q.module)||((J=E.arguments)==null?void 0:J.keyword)||((Y=E.arguments)==null?void 0:Y.engine)||((ye=E.arguments)==null?void 0:ye.name)||"":typeof E.result=="string"?E.result.slice(0,120):E.result&&typeof E.result=="object"&&(E.result.module||E.result.status||E.result.name)||"":""}let V=D(()=>(e.message.toolEvents||[]).filter(E=>E.type==="call")),ze=D(()=>(e.message.toolEvents||[]).filter(E=>E.type==="result")),j=D(()=>y(e.message.text||"",e.message.loading)),B=D(()=>{var q,J,Y;const E=[];return((J=(q=e.message.meta)==null?void 0:q.includedModules)==null?void 0:J.length)>0&&E.push({label:`모듈 ${e.message.meta.includedModules.length}개`,icon:Jo}),((Y=e.message.contexts)==null?void 0:Y.length)>0&&E.push({label:`컨텍스트 ${e.message.contexts.length}건`,icon:vh}),r(V).length>0&&E.push({label:`툴 호출 ${r(V).length}건`,icon:ld}),r(ze).length>0&&E.push({label:`툴 결과 ${r(ze).length}건`,icon:as}),e.message.systemPrompt&&E.push({label:"시스템 프롬프트",icon:vi}),e.message.userContent&&E.push({label:"LLM 입력",icon:zn}),E}),le=D(()=>{var q,J,Y;if(!e.message.loading)return[];const E=[];return(q=e.message.meta)!=null&&q.company&&E.push({label:`${e.message.meta.company} 인식`,done:!0}),e.message.snapshot&&E.push({label:"핵심 수치 확인",done:!0}),(J=e.message.meta)!=null&&J.includedModules&&E.push({label:`모듈 ${e.message.meta.includedModules.length}개 선택`,done:!0}),((Y=e.message.contexts)==null?void 0:Y.length)>0&&E.push({label:`데이터 ${e.message.contexts.length}건 로드`,done:!0}),e.message.systemPrompt&&E.push({label:"프롬프트 조립",done:!0}),e.message.text?E.push({label:"응답 작성 중",done:!1}):E.push({label:r(i)||"준비 중",done:!1}),E});var we=Om(),U=ae(we);{var ne=E=>{var q=Kh(),J=m(d(q),2),Y=d(J),ye=d(Y);z(()=>T(ye,e.message.text)),c(E,q)},N=E=>{var q=km(),J=m(d(q),2),Y=d(J);{var ye=dt=>{var nt=Xh(),st=d(nt),xt=d(st);ih(xt,{size:11});var St=m(st,4),Nt=d(St);{var lr=ve=>{Yo(ve,{variant:"muted",children:(ke,Pe)=>{var de=oa();z(()=>T(de,r(s))),c(ke,de)},$$slots:{default:!0}})};$(Nt,ve=>{r(s)&&ve(lr)})}var R=m(Nt,2);{var pe=ve=>{Yo(ve,{variant:"muted",children:(ke,Pe)=>{var de=oa();z(Te=>T(de,Te),[()=>e.message.meta.market.toUpperCase()]),c(ke,de)},$$slots:{default:!0}})};$(R,ve=>{var ke;(ke=e.message.meta)!=null&&ke.market&&ve(pe)})}var oe=m(R,2);{var ce=ve=>{Yo(ve,{variant:"accent",children:(ke,Pe)=>{var de=oa();z(()=>T(de,r(u))),c(ke,de)},$$slots:{default:!0}})};$(oe,ve=>{r(u)&&ve(ce)})}var w=m(oe,2);{var F=ve=>{Yo(ve,{variant:"muted",children:(ke,Pe)=>{var de=oa();z(()=>T(de,e.message.meta.topicLabel)),c(ke,de)},$$slots:{default:!0}})};$(w,ve=>{var ke;(ke=e.message.meta)!=null&&ke.topicLabel&&ve(F)})}var re=m(w,2);{var ie=ve=>{Yo(ve,{variant:"accent",children:(ke,Pe)=>{var de=oa();z(()=>T(de,r(p))),c(ke,de)},$$slots:{default:!0}})};$(re,ve=>{r(p)&&ve(ie)})}var ue=m(re,2);{var P=ve=>{var ke=Ce(),Pe=ae(ke);Ae(Pe,17,()=>e.message.contexts,Ne,(de,Te,Re)=>{var He=Gh(),_e=d(He);Jo(_e,{size:10,class:"flex-shrink-0"});var et=m(_e);z(()=>T(et,` ${(r(Te).label||r(Te).module)??""}`)),he("click",He,()=>ee(Re)),c(de,He)}),c(ve,ke)},Z=ve=>{var ke=Jh(),Pe=d(ke);Jo(Pe,{size:10,class:"flex-shrink-0"});var de=m(Pe);z(()=>T(de,` 모듈 ${e.message.meta.includedModules.length??""}개`)),c(ve,ke)};$(ue,ve=>{var ke,Pe,de;((ke=e.message.contexts)==null?void 0:ke.length)>0?ve(P):((de=(Pe=e.message.meta)==null?void 0:Pe.includedModules)==null?void 0:de.length)>0&&ve(Z,1)})}var $e=m(ue,2);Ae($e,17,()=>r(B),Ne,(ve,ke)=>{var Pe=Yh(),de=d(Pe);Ao(de,()=>r(ke).icon,(Re,He)=>{He(Re,{size:10,class:"flex-shrink-0"})});var Te=m(de);z(()=>T(Te,` ${r(ke).label??""}`)),he("click",Pe,()=>{r(ke).label.startsWith("컨텍스트")?ee(0):r(ke).label.startsWith("툴 호출")?e.onOpenEvidence?e.onOpenEvidence("tool-calls",0):S(0):r(ke).label.startsWith("툴 결과")?e.onOpenEvidence?e.onOpenEvidence("tool-results",0):S((e.message.toolEvents||[]).findIndex(Re=>Re.type==="result")):r(ke).label==="시스템 프롬프트"?fe():r(ke).label==="LLM 입력"&&X()}),c(ve,Pe)}),c(dt,nt)};$(Y,dt=>{var nt,st;(r(s)||r(p)||((nt=e.message.contexts)==null?void 0:nt.length)>0||(st=e.message.meta)!=null&&st.includedModules||r(B).length>0)&&dt(ye)})}var Se=m(Y,2);{var te=dt=>{var nt=am(),st=d(nt);Ae(st,21,()=>e.message.snapshot.items,Ne,(R,pe)=>{const oe=D(()=>r(pe).status==="good"?"text-dl-success":r(pe).status==="danger"?"text-dl-primary-light":r(pe).status==="caution"?"text-amber-400":"text-dl-text");var ce=Qh(),w=d(ce),F=d(w),re=m(w,2),ie=d(re);z(ue=>{T(F,r(pe).label),Ue(re,1,ue),T(ie,r(pe).value)},[()=>xr(wr("text-[14px] font-semibold leading-snug mt-0.5",r(oe)))]),c(R,ce)});var xt=m(st,2);{var St=R=>{var pe=em();Ae(pe,21,()=>e.message.snapshot.warnings,Ne,(oe,ce)=>{var w=Zh(),F=d(w);ss(F,{size:10});var re=m(F);z(()=>T(re,` ${r(ce)??""}`)),c(oe,w)}),c(R,pe)};$(xt,R=>{var pe;((pe=e.message.snapshot.warnings)==null?void 0:pe.length)>0&&R(St)})}var Nt=m(xt,2);{var lr=R=>{const pe=D(()=>({performance:"실적",profitability:"수익성",health:"건전성",cashflow:"현금흐름",governance:"지배구조",risk:"리스크",opportunity:"기회"}));var oe=nm(),ce=d(oe);Ae(ce,17,()=>Object.entries(e.message.snapshot.grades),Ne,(re,ie)=>{var ue=D(()=>Ji(r(ie),2));let P=()=>r(ue)[0],Z=()=>r(ue)[1];const $e=D(()=>Z()==="A"?"bg-emerald-500/15 text-emerald-400 border-emerald-500/30":Z()==="B"?"bg-blue-500/15 text-blue-400 border-blue-500/30":Z()==="C"?"bg-amber-500/15 text-amber-400 border-amber-500/30":Z()==="D"?"bg-orange-500/15 text-orange-400 border-orange-500/30":Z()==="F"?"bg-red-500/15 text-red-400 border-red-500/30":"bg-dl-border/10 text-dl-text-dim border-dl-border/20");var ve=tm(),ke=d(ve);z(()=>{Ue(ve,1,`px-1.5 py-0.5 rounded text-[9px] font-bold border ${r($e)??""}`),T(ke,`${(r(pe)[P()]||P())??""} ${Z()??""}`)}),c(re,ve)});var w=m(ce,2);{var F=re=>{var ie=rm(),ue=d(ie);z(()=>T(ue,`이상치 ${e.message.snapshot.anomalyCount??""}건`)),c(re,ie)};$(w,re=>{e.message.snapshot.anomalyCount>0&&re(F)})}c(R,oe)};$(Nt,R=>{e.message.snapshot.grades&&R(lr)})}he("click",nt,L),c(dt,nt)};$(Se,dt=>{var nt,st;((st=(nt=e.message.snapshot)==null?void 0:nt.items)==null?void 0:st.length)>0&&dt(te)})}var Oe=m(Se,2);{var tt=dt=>{var nt=sm(),st=d(nt),xt=m(d(st),4);Ae(xt,21,()=>e.message.toolEvents,Ne,(St,Nt,lr)=>{const R=D(()=>me(r(Nt)));var pe=om(),oe=d(pe);{var ce=re=>{ld(re,{size:11})},w=re=>{as(re,{size:11})};$(oe,re=>{r(Nt).type==="call"?re(ce):re(w,-1)})}var F=m(oe);z(re=>{Ue(pe,1,re),T(F,` ${(r(Nt).type==="call"?r(Nt).name:`${r(Nt).name} 결과`)??""}${r(R)?`: ${r(R)}`:""}`)},[()=>xr(wr("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",r(Nt).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),he("click",pe,()=>S(lr)),c(St,pe)}),c(dt,nt)};$(Oe,dt=>{var nt;((nt=e.message.toolEvents)==null?void 0:nt.length)>0&&dt(tt)})}var ot=m(Oe,2);{var Ge=dt=>{var nt=cm(),st=d(nt);Ae(st,21,()=>r(le),Ne,(xt,St)=>{var Nt=dm(),lr=d(Nt);{var R=oe=>{var ce=im(),w=m(ae(ce),2),F=d(w);z(()=>T(F,r(St).label)),c(oe,ce)},pe=oe=>{var ce=lm(),w=ae(ce);Ur(w,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var F=m(w,2),re=d(F);z(()=>T(re,r(St).label)),c(oe,ce)};$(lr,oe=>{r(St).done?oe(R):oe(pe,-1)})}c(xt,Nt)}),c(dt,nt)},rt=dt=>{var nt=ym(),st=ae(nt);{var xt=w=>{var F=um(),re=d(F);Ur(re,{size:12,class:"animate-spin flex-shrink-0"});var ie=m(re,2),ue=d(ie);z(()=>T(ue,r(i))),c(w,F)};$(st,w=>{e.message.loading&&w(xt)})}var St=m(st,2),Nt=d(St);{var lr=w=>{var F=fm(),re=d(F);Kn(re,()=>Va(r(j).committed)),c(w,F)};$(Nt,w=>{r(j).committed&&w(lr)})}var R=m(Nt,2);{var pe=w=>{var F=vm(),re=d(F),ie=d(re),ue=m(re,2),P=d(ue);z(Z=>{Ue(F,1,Z),T(ie,r(j).draftType==="table"?"표 구성 중":r(j).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),T(P,r(j).draft)},[()=>xr(wr("message-live-tail",r(j).draftType==="table"&&"message-draft-table",r(j).draftType==="code"&&"message-draft-code"))]),c(w,F)};$(R,w=>{r(j).draft&&w(pe)})}Jn(St,w=>v(C,w),()=>r(C));var oe=m(St,2);{var ce=w=>{var F=wm(),re=d(F);{var ie=Te=>{var Re=pm(),He=d(Re);ls(He,{size:10});var _e=m(He);z(()=>T(_e,` ${e.message.duration??""}초`)),c(Te,Re)};$(re,Te=>{e.message.duration&&Te(ie)})}var ue=m(re,2);{var P=Te=>{var Re=xm(),He=d(Re);{var _e=at=>{var Dt=hm(),Ve=d(Dt);z(Ee=>T(Ve,`↑${Ee??""}`),[()=>x(r(b))]),c(at,Dt)};$(He,at=>{r(b)>0&&at(_e)})}var et=m(He,2);{var Ct=at=>{var Dt=mm(),Ve=d(Dt);z(Ee=>T(Ve,`↓${Ee??""}`),[()=>x(r(k))]),c(at,Dt)};$(et,at=>{r(k)>0&&at(Ct)})}c(Te,Re)};$(ue,Te=>{(r(b)>0||r(k)>0)&&Te(P)})}var Z=m(ue,2);{var $e=Te=>{var Re=gm(),He=d(Re);_h(He,{size:10}),he("click",Re,()=>{var _e;return(_e=e.onRegenerate)==null?void 0:_e.call(e)}),c(Te,Re)};$(Z,Te=>{e.onRegenerate&&Te($e)})}var ve=m(Z,2);{var ke=Te=>{var Re=_m(),He=d(Re);vi(He,{size:10}),he("click",Re,fe),c(Te,Re)};$(ve,Te=>{e.message.systemPrompt&&Te(ke)})}var Pe=m(ve,2);{var de=Te=>{var Re=bm(),He=d(Re);zn(He,{size:10});var _e=m(He);z((et,Ct)=>T(_e,` LLM 입력 (${et??""}자 · ~${Ct??""}tok)`),[()=>e.message.userContent.length.toLocaleString(),()=>x(_(e.message.userContent))]),he("click",Re,X),c(Te,Re)};$(Pe,Te=>{e.message.userContent&&Te(de)})}c(w,F)};$(oe,w=>{!e.message.loading&&(e.message.duration||r(f)||e.onRegenerate)&&w(ce)})}z(w=>Ue(St,1,w),[()=>xr(wr("prose-dartlab message-body text-[15px] leading-[1.75]",e.message.error&&"text-dl-primary"))]),he("click",St,M),c(dt,nt)};$(ot,dt=>{e.message.loading&&!e.message.text?dt(Ge):dt(rt,-1)})}c(E,q)};$(U,E=>{e.message.role==="user"?E(ne):E(N,-1)})}var W=m(U,2);{var H=E=>{const q=D(()=>r(a)==="system"),J=D(()=>r(a)==="userContent"),Y=D(()=>r(a)==="context"),ye=D(()=>r(a)==="snapshot"),Se=D(()=>r(a)==="tool"),te=D(()=>{var _e;return r(Y)?(_e=e.message.contexts)==null?void 0:_e[r(n)]:null}),Oe=D(()=>{var _e;return r(Se)?(_e=e.message.toolEvents)==null?void 0:_e[r(n)]:null}),tt=D(()=>{var _e,et,Ct,at,Dt;return r(ye)?"핵심 수치 (원본 데이터)":r(q)?"시스템 프롬프트":r(J)?"LLM에 전달된 입력":r(Se)?((_e=r(Oe))==null?void 0:_e.type)==="call"?`${(et=r(Oe))==null?void 0:et.name} 호출`:`${(Ct=r(Oe))==null?void 0:Ct.name} 결과`:((at=r(te))==null?void 0:at.label)||((Dt=r(te))==null?void 0:Dt.module)||""}),ot=D(()=>{var _e;return r(ye)?JSON.stringify(e.message.snapshot,null,2):r(q)?e.message.systemPrompt:r(J)?e.message.userContent:r(Se)?JSON.stringify(r(Oe),null,2):(_e=r(te))==null?void 0:_e.text});var Ge=Lm(),rt=d(Ge),dt=d(rt),nt=d(dt),st=d(nt),xt=d(st);{var St=_e=>{Jo(_e,{size:15,class:"text-dl-success flex-shrink-0"})},Nt=_e=>{vi(_e,{size:15,class:"text-dl-primary-light flex-shrink-0"})},lr=_e=>{zn(_e,{size:15,class:"text-dl-accent flex-shrink-0"})},R=_e=>{Jo(_e,{size:15,class:"flex-shrink-0"})};$(xt,_e=>{r(ye)?_e(St):r(q)?_e(Nt,1):r(J)?_e(lr,2):_e(R,-1)})}var pe=m(xt,2),oe=d(pe),ce=m(pe,2);{var w=_e=>{var et=Cm(),Ct=d(et);z(at=>T(Ct,`(${at??""}자)`),[()=>{var at,Dt;return(Dt=(at=r(ot))==null?void 0:at.length)==null?void 0:Dt.toLocaleString()}]),c(_e,et)};$(ce,_e=>{r(q)&&_e(w)})}var F=m(st,2),re=d(F);{var ie=_e=>{var et=$m(),Ct=d(et),at=d(Ct);zn(at,{size:11});var Dt=m(Ct,2),Ve=d(Dt);ch(Ve,{size:11}),z((Ee,Ie)=>{Ue(Ct,1,Ee),Ue(Dt,1,Ie)},[()=>xr(wr("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",r(o)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>xr(wr("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",r(o)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),he("click",Ct,()=>v(o,"rendered")),he("click",Dt,()=>v(o,"raw")),c(_e,et)};$(re,_e=>{r(Y)&&_e(ie)})}var ue=m(re,2),P=d(ue);Fa(P,{size:18});var Z=m(nt,2);{var $e=_e=>{var et=Mm(),Ct=d(et);Ae(Ct,21,()=>e.message.contexts,Ne,(at,Dt,Ve)=>{var Ee=Sm(),Ie=d(Ee);z(yt=>{Ue(Ee,1,yt),T(Ie,e.message.contexts[Ve].label||e.message.contexts[Ve].module)},[()=>xr(wr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",Ve===r(n)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),he("click",Ee,()=>{v(n,Ve,!0)}),c(at,Ee)}),c(_e,et)};$(Z,_e=>{var et;r(Y)&&((et=e.message.contexts)==null?void 0:et.length)>1&&_e($e)})}var ve=m(Z,2);{var ke=_e=>{var et=Im(),Ct=d(et),at=d(Ct);{var Dt=Ie=>{var yt=zm();z(Pt=>Ue(yt,1,Pt),[()=>xr(wr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",r(q)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),he("click",yt,()=>{v(a,"system")}),c(Ie,yt)};$(at,Ie=>{e.message.systemPrompt&&Ie(Dt)})}var Ve=m(at,2);{var Ee=Ie=>{var yt=Tm();z(Pt=>Ue(yt,1,Pt),[()=>xr(wr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",r(J)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),he("click",yt,()=>{v(a,"userContent")}),c(Ie,yt)};$(Ve,Ie=>{e.message.userContent&&Ie(Ee)})}c(_e,et)};$(ve,_e=>{!r(Y)&&!r(ye)&&!r(Se)&&_e(ke)})}var Pe=m(dt,2),de=d(Pe);{var Te=_e=>{var et=Am(),Ct=d(et);Kn(Ct,()=>{var at;return Va((at=r(te))==null?void 0:at.text)}),c(_e,et)},Re=_e=>{var et=Nm(),Ct=d(et),at=m(d(Ct),2),Dt=d(at),Ve=m(Dt);{var Ee=Je=>{var At=Em(),qt=d(At);z($t=>T(qt,$t),[()=>me(r(Oe))]),c(Je,At)},Ie=D(()=>me(r(Oe)));$(Ve,Je=>{r(Ie)&&Je(Ee)})}var yt=m(Ct,2),Pt=d(yt);z(()=>{var Je;T(Dt,`${((Je=r(Oe))==null?void 0:Je.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),T(Pt,r(ot))}),c(_e,et)},He=_e=>{var et=Pm(),Ct=d(et);z(()=>T(Ct,r(ot))),c(_e,et)};$(de,_e=>{r(Y)&&r(o)==="rendered"?_e(Te):r(Se)?_e(Re,1):_e(He,-1)})}z(()=>T(oe,r(tt))),he("click",Ge,_e=>{_e.target===_e.currentTarget&&G()}),he("keydown",Ge,_e=>{_e.key==="Escape"&&G()}),he("click",ue,G),c(E,Ge)};$(W,E=>{r(n)!==null&&E(H)})}c(t,we),Ar()}Kr(["click","keydown"]);var Rm=h('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),jm=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),Fm=h('<div class="flex justify-end gap-2 mb-1.5"><!></div>'),Vm=h('<div class="flex items-center gap-1.5 px-3 py-1 text-[10px] text-dl-text-dim"><span class="px-1.5 py-0.5 rounded bg-dl-accent/10 text-dl-accent-light border border-dl-accent/20 font-mono"> <!></span> <span>보는 중 — AI가 이 섹션을 참조합니다</span></div>'),Bm=h('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8"><!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!> <!></div></div></div>');function qm(t,e){Ir(e,!0);function n(j){if(o())return!1;for(let B=a().length-1;B>=0;B--)if(a()[B].role==="assistant"&&!a()[B].error&&a()[B].text)return B===j;return!1}let a=je(e,"messages",19,()=>[]),o=je(e,"isLoading",3,!1),i=je(e,"inputText",15,""),s=je(e,"scrollTrigger",3,0);je(e,"selectedCompany",3,null);let l=je(e,"viewerContext",3,null);function u(j){return(B,le)=>{var U,ne,N,W;(U=e.onOpenEvidence)==null||U.call(e,B,le);let we;if(B==="contexts")we=(ne=j.contexts)==null?void 0:ne[le];else if(B==="snapshot")we={label:"핵심 수치",module:"snapshot",text:JSON.stringify(j.snapshot,null,2)};else if(B==="system")we={label:"시스템 프롬프트",module:"system",text:j.systemPrompt};else if(B==="input")we={label:"LLM 입력",module:"input",text:j.userContent};else if(B==="tool-calls"||B==="tool-results"){const H=(N=j.toolEvents)==null?void 0:N[le];we={label:`${(H==null?void 0:H.name)||"도구"} ${(H==null?void 0:H.type)==="call"?"호출":"결과"}`,module:"tool",text:JSON.stringify(H,null,2)}}we&&((W=e.onOpenData)==null||W.call(e,we))}}let f,p,_=K(!0),x=K(!1),b=K(!0);function k(){if(!f)return;const{scrollTop:j,scrollHeight:B,clientHeight:le}=f;v(b,B-j-le<96),r(b)?(v(_,!0),v(x,!1)):(v(_,!1),v(x,!0))}function C(j="smooth"){p&&(p.scrollIntoView({block:"end",behavior:j}),v(_,!0),v(x,!1))}gr(()=>{s(),!(!f||!p)&&requestAnimationFrame(()=>{!f||!p||(r(_)||r(b)?(p.scrollIntoView({block:"end",behavior:o()?"auto":"smooth"}),v(x,!1)):v(x,!0))})});var g=Bm(),y=d(g),I=d(y),O=d(I);Ae(O,17,a,Ne,(j,B,le)=>{{let we=D(()=>n(le)?e.onRegenerate:void 0),U=D(()=>e.onOpenData?u(r(B)):void 0);Dm(j,{get message(){return r(B)},get onRegenerate(){return r(we)},get onOpenEvidence(){return r(U)}})}});var M=m(O,2);Jn(M,j=>p=j,()=>p),Jn(y,j=>f=j,()=>f);var ee=m(y,2);{var fe=j=>{var B=Rm(),le=d(B);he("click",le,()=>C("smooth")),c(j,B)};$(ee,j=>{r(x)&&j(fe)})}var L=m(ee,2),S=d(L),X=d(S);{var G=j=>{var B=Fm(),le=d(B);{var we=U=>{var ne=jm(),N=d(ne);os(N,{size:10}),he("click",ne,function(...W){var H;(H=e.onExport)==null||H.apply(this,W)}),c(U,ne)};$(le,U=>{a().length>1&&e.onExport&&U(we)})}c(j,B)};$(X,j=>{o()||j(G)})}var me=m(X,2);{var V=j=>{var B=Vm(),le=d(B),we=d(le),U=m(we);{var ne=N=>{var W=oa();z(()=>T(W,` (${l().period??""})`)),c(N,W)};$(U,N=>{l().period&&N(ne)})}z(()=>T(we,l().topicLabel||l().topic)),c(j,B)};$(me,j=>{var B;(B=l())!=null&&B.topic&&j(V)})}var ze=m(me,2);au(ze,{get isLoading(){return o()},placeholder:"메시지를 입력하세요...",get onSend(){return e.onSend},get onStop(){return e.onStop},get onCompanySelect(){return e.onCompanySelect},get inputText(){return i()},set inputText(j){i(j)}}),xn("scroll",y,k),c(t,g),Ar()}Kr(["click"]);var Hm=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!> <span class="text-[13px]">공시 데이터 로딩 중...</span></div>'),Um=h('<div class="text-[11px] text-dl-text-dim"> </div>'),Wm=h('<button><!> <span class="truncate flex-1"> </span></button>'),Km=h('<div class="py-0.5"></div>'),Gm=h('<div><button class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] opacity-30 font-normal"> </span></button> <!></div>'),Jm=h('<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50"><div class="px-3 py-2.5 border-b border-dl-border/20"><!></div> <!></nav>'),Ym=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim"><!> <p class="text-[13px]">좌측에서 섹션을 선택하세요</p></div>'),Xm=h('<div class="text-[10px] text-dl-text-dim/50 mb-0.5"> </div>'),Qm=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!></div>'),Zm=h('<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>'),ex=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),tx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),rx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),nx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),ax=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),ox=h('<div class="vw-heading-node svelte-1l2nqwu"><!></div>'),sx=h('<div class="vw-heading-block svelte-1l2nqwu"></div>'),ix=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),lx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),dx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),cx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),ux=h('<button><span class="vw-timeline-label svelte-1l2nqwu"> </span></button>'),fx=h('<div class="vw-section-timeline svelte-1l2nqwu"></div>'),vx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),px=h('<span class="vw-meta-pill svelte-1l2nqwu">비교 없음</span>'),hx=h('<div class="vw-section-actions svelte-1l2nqwu"><span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span></div>'),mx=h('<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span> </div>'),xx=h('<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),gx=h('<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),_x=h('<div class="text-[10px] text-dl-text-dim/35 mt-1"> </div>'),bx=h('<div class="vw-digest svelte-1l2nqwu"><div class="flex items-center gap-2 mb-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span></div> <div class="space-y-1"><!> <!> <!> <!></div></div>'),wx=h('<p class="vw-para"> </p>'),yx=h('<div class="vw-diff-added svelte-1l2nqwu"> </div>'),kx=h('<div class="vw-diff-deleted svelte-1l2nqwu"> </div>'),Cx=h('<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow svelte-1l2nqwu"></div>'),$x=h('<div class="disclosure-text vw-section-body vw-body-frame svelte-1l2nqwu"><!></div>'),Sx=h('<div><!> <div class="vw-section-meta svelte-1l2nqwu"><span> </span> <!> <!> <!> <!></div> <!> <!> <!> <!></div>'),Mx=h('<section class="vw-report-shell svelte-1l2nqwu"><div class="vw-report-header svelte-1l2nqwu"><div class="vw-report-badges svelte-1l2nqwu"><!> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <!> <!></div></div> <!></section>'),zx=h('<div class="vw-data-divider svelte-1l2nqwu"><div class="vw-data-kicker svelte-1l2nqwu">Structured Data</div> <div class="vw-data-title svelte-1l2nqwu">표 / 정형 데이터</div></div>'),Tx=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),Ix=h("<th> </th>"),Ax=h("<td> </td>"),Ex=h("<tr></tr>"),Nx=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),Px=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),Lx=h("<th> </th>"),Ox=h("<td> </td>"),Dx=h("<tr></tr>"),Rx=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),jx=h("<button> </button>"),Fx=h('<span class="text-[9px] text-dl-text-dim/30"> </span>'),Vx=h('<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto"><!> <!></div>'),Bx=h('<div class="vw-table-wrap bg-dl-bg-card/10 svelte-1l2nqwu"><!> <div class="px-4 py-3"><div class="markdown-table overflow-x-auto svelte-1l2nqwu"><!></div></div></div>'),qx=h("<th> </th>"),Hx=h("<td> </td>"),Ux=h("<tr></tr>"),Wx=h('<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02] svelte-1l2nqwu"><div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10"><!> <span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span></div> <div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Kx=h('<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card"> </th>'),Gx=h('<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted"> </td>'),Jx=h("<tr></tr>"),Yx=h('<div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Xx=h('<article class="py-6 px-8"><!> <!> <!> <!></article>'),Qx=h('<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center"><div class="flex-1 min-w-0"><!> <h3 class="text-[16px] font-semibold text-dl-text"> </h3></div> <button class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"><!></button></div> <!>',1),Zx=h('<div class="flex flex-1 overflow-hidden min-h-0"><!> <main class="flex-1 overflow-y-auto min-w-0"><!></main></div>'),e1=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8"><!> <p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p></div>'),t1=h('<div class="flex flex-col h-full font-sans bg-dl-bg-dark"><!></div>');function r1(t,e){Ir(e,!0);let n=je(e,"stockCode",3,null),a=je(e,"onTopicChange",3,null),o=K(null),i=K(!1),s=K(Bt(new Set)),l=K(null),u=K(null),f=K(Bt([])),p=K(null),_=K(!1),x=K(Bt([])),b=K(Bt(new Map)),k=new Map,C=K(!1),g=K(Bt(new Map));const y={companyOverview:"회사 개요",companyHistory:"회사 연혁",articlesOfIncorporation:"정관 사항",capitalChange:"자본금 변동",shareCapital:"주식 현황",dividend:"배당",productService:"사업 내용",rawMaterial:"원재료",businessOverview:"사업 개요",salesOrder:"매출/수주",riskDerivative:"위험관리/파생",majorContractsAndRnd:"주요 계약/R&D",otherReferences:"기타 참고사항",consolidatedStatements:"연결 재무제표",fsSummary:"재무제표 요약",consolidatedNotes:"연결 주석",financialStatements:"개별 재무제표",financialNotes:"개별 주석",fundraising:"자금조달",BS:"재무상태표",IS:"손익계산서",CIS:"포괄손익계산서",CF:"현금흐름표",SCE:"자본변동표",ratios:"재무비율",audit:"감사 의견",mdna:"경영진 분석(MD&A)",internalControl:"내부통제",auditContract:"감사 계약",nonAuditContract:"비감사 계약",boardOfDirectors:"이사회",shareholderMeeting:"주주총회",auditSystem:"감사 체계",outsideDirector:"사외이사",majorHolder:"주요 주주",majorHolderChange:"주주 변동",minorityHolder:"소수주주",stockTotal:"주식 총수",treasuryStock:"자기주식",employee:"직원 현황",executivePay:"임원 보수",executive:"임원 현황",executivePayAllTotal:"전체 보수 총액",executivePayIndividual:"개인별 보수",topPay:"5억이상 상위 보수",unregisteredExecutivePay:"미등기임원 보수",affiliateGroup:"계열회사",investedCompany:"투자회사",relatedPartyTx:"특수관계 거래",corporateBond:"사채 관리",privateOfferingUsage:"사모자금 사용",publicOfferingUsage:"공모자금 사용",shortTermBond:"단기사채",investorProtection:"투자자 보호",disclosureChanges:"공시변경 사항",contingentLiability:"우발채무",sanction:"제재/조치",subsequentEvents:"후발사건",expertConfirmation:"전문가 확인",subsidiaryDetail:"종속회사 상세",affiliateGroupDetail:"계열회사 상세",investmentInOtherDetail:"타법인 출자 상세",rndDetail:"R&D 상세"},I={I:"I. 회사의 개요",II:"II. 사업의 내용",III:"III. 재무에 관한 사항",IV:"IV. 감사인의 감사의견 등",V:"V. 이사의 경영진단 및 분석의견",VI:"VI. 이사회 등 회사의 기관에 관한 사항",VII:"VII. 주주에 관한 사항",VIII:"VIII. 임원 및 직원 등에 관한 사항",IX:"IX. 계열회사 등에 관한 사항",X:"X. 대주주 등과의 거래내용",XI:"XI. 그 밖에 투자자 보호를 위하여 필요한 사항",XII:"XII. 상세표"},O={I:1,II:2,III:3,IV:4,V:5,VI:6,VII:7,VIII:8,IX:9,X:10,XI:11,XII:12};function M(R){return O[R]??99}function ee(R){return y[R]||R}function fe(R){return I[R]||R||"기타"}gr(()=>{n()&&L()});async function L(){var R,pe;v(i,!0),v(o,null),v(l,null),v(u,null),v(f,[],!0),v(p,null),k=new Map;try{const oe=await Lv(n());v(o,oe.payload,!0),(R=r(o))!=null&&R.columns&&v(x,r(o).columns.filter(w=>/^\d{4}(Q[1-4])?$/.test(w)),!0);const ce=j((pe=r(o))==null?void 0:pe.rows);ce.length>0&&(v(s,new Set([ce[0].chapter]),!0),ce[0].topics.length>0&&S(ce[0].topics[0].topic,ce[0].chapter))}catch(oe){console.error("viewer load error:",oe)}v(i,!1)}async function S(R,pe){var oe;if(r(l)!==R){if(v(l,R,!0),v(u,pe||null,!0),v(b,new Map,!0),v(g,new Map,!0),(oe=a())==null||oe(R,ee(R)),k.has(R)){const ce=k.get(R);v(f,ce.blocks||[],!0),v(p,ce.textDocument||null,!0);return}v(f,[],!0),v(p,null),v(_,!0);try{const ce=await Pv(n(),R);v(f,ce.blocks||[],!0),v(p,ce.textDocument||null,!0),k.set(R,{blocks:r(f),textDocument:r(p)})}catch(ce){console.error("topic load error:",ce),v(f,[],!0),v(p,null)}v(_,!1)}}function X(R){const pe=new Set(r(s));pe.has(R)?pe.delete(R):pe.add(R),v(s,pe,!0)}function G(R,pe){const oe=new Map(r(b));oe.get(R)===pe?oe.delete(R):oe.set(R,pe),v(b,oe,!0)}function me(R,pe){const oe=new Map(r(g));oe.set(R,pe),v(g,oe,!0)}function V(R){return R==="updated"?"최근 수정":R==="new"?"신규":R==="stale"?"과거 유지":"유지"}function ze(R){return R==="updated"?"updated":R==="new"?"new":R==="stale"?"stale":"stable"}function j(R){if(!R)return[];const pe=new Map,oe=new Set;for(const ce of R){const w=ce.chapter||"";pe.has(w)||pe.set(w,{chapter:w,topics:[]}),oe.has(ce.topic)||(oe.add(ce.topic),pe.get(w).topics.push({topic:ce.topic,source:ce.source||"docs"}))}return[...pe.values()].sort((ce,w)=>M(ce.chapter)-M(w.chapter))}function B(R){return String(R).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function le(R){return String(R||"").replaceAll(" "," ").replace(/\s+/g," ").trim()}function we(R){return!R||R.length>88?!1:/^\[.+\]$/.test(R)||/^【.+】$/.test(R)||/^[IVX]+\.\s/.test(R)||/^\d+\.\s/.test(R)||/^[가-힣]\.\s/.test(R)||/^\(\d+\)\s/.test(R)||/^\([가-힣]\)\s/.test(R)}function U(R){return/^\(\d+\)\s/.test(R)||/^\([가-힣]\)\s/.test(R)?"h5":"h4"}function ne(R){return/^\[.+\]$/.test(R)||/^【.+】$/.test(R)?"vw-h-bracket":/^\(\d+\)\s/.test(R)||/^\([가-힣]\)\s/.test(R)?"vw-h-sub":"vw-h-section"}function N(R){if(!R)return[];if(/^\|.+\|$/m.test(R)||/^#{1,3} /m.test(R)||/```/.test(R))return[{kind:"markdown",text:R}];const pe=[];let oe=[];const ce=()=>{oe.length!==0&&(pe.push({kind:"paragraph",text:oe.join(" ")}),oe=[])};for(const w of String(R).split(`
`)){const F=le(w);if(!F){ce();continue}if(we(F)){ce(),pe.push({kind:"heading",text:F,tag:U(F),className:ne(F)});continue}oe.push(F)}return ce(),pe}function W(R){return R?R.kind==="annual"?`${R.year}Q4`:R.year&&R.quarter?`${R.year}Q${R.quarter}`:R.label||"":""}function H(R){var ce;const pe=N(R);if(pe.length===0)return"";if(((ce=pe[0])==null?void 0:ce.kind)==="markdown")return Va(R);let oe="";for(const w of pe){if(w.kind==="heading"){oe+=`<${w.tag} class="${w.className}">${B(w.text)}</${w.tag}>`;continue}oe+=`<p class="vw-para">${B(w.text)}</p>`}return oe}function E(R){if(!R)return"";const pe=R.trim().split(`
`).filter(ce=>ce.trim());let oe="";for(const ce of pe){const w=ce.trim();/^[가-힣]\.\s/.test(w)||/^\d+[-.]/.test(w)?oe+=`<h4 class="vw-h-section">${w}</h4>`:/^\(\d+\)\s/.test(w)||/^\([가-힣]\)\s/.test(w)?oe+=`<h5 class="vw-h-sub">${w}</h5>`:/^\[.+\]$/.test(w)||/^【.+】$/.test(w)?oe+=`<h4 class="vw-h-bracket">${w}</h4>`:oe+=`<h5 class="vw-h-sub">${w}</h5>`}return oe}function q(R){var oe;const pe=r(b).get(R.id);return pe&&((oe=R==null?void 0:R.views)!=null&&oe[pe])?R.views[pe]:(R==null?void 0:R.latest)||null}function J(R,pe){var ce,w;const oe=r(b).get(R.id);return oe?oe===pe:((w=(ce=R==null?void 0:R.latest)==null?void 0:ce.period)==null?void 0:w.label)===pe}function Y(R){return r(b).has(R.id)}function ye(R){return R==="updated"?"변경 있음":R==="new"?"직전 없음":"직전과 동일"}function Se(R){var F,re,ie;if(!R)return[];const pe=N(R.body);if(pe.length===0||((F=pe[0])==null?void 0:F.kind)==="markdown"||!((re=R.prevPeriod)!=null&&re.label)||!((ie=R.diff)!=null&&ie.length))return pe;const oe=[];for(const ue of R.diff)for(const P of ue.paragraphs||[])oe.push({kind:ue.kind,text:le(P)});const ce=[];let w=0;for(const ue of pe){if(ue.kind!=="paragraph"){ce.push(ue);continue}for(;w<oe.length&&oe[w].kind==="removed";)ce.push({kind:"removed",text:oe[w].text}),w+=1;w<oe.length&&["same","added"].includes(oe[w].kind)?(ce.push({kind:oe[w].kind,text:oe[w].text||ue.text}),w+=1):ce.push({kind:"same",text:ue.text})}for(;w<oe.length;)ce.push({kind:oe[w].kind,text:oe[w].text}),w+=1;return ce}function te(R){return R==null?!1:/^-?[\d,.]+%?$/.test(String(R).trim().replace(/,/g,""))}function Oe(R){return R==null?!1:/^-[\d.]+/.test(String(R).trim().replace(/,/g,""))}function tt(R,pe){if(R==null||R==="")return"";const oe=typeof R=="number"?R:Number(String(R).replace(/,/g,""));if(isNaN(oe))return String(R);if(pe<=1)return oe.toLocaleString("ko-KR");const ce=oe/pe;return Number.isInteger(ce)?ce.toLocaleString("ko-KR"):ce.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g,",")}function ot(R){if(R==null||R==="")return"";const pe=String(R).trim();if(pe.includes(","))return pe;const oe=pe.match(/^(-?\d+)(\.\d+)?(%?)$/);return oe?oe[1].replace(/\B(?=(\d{3})+(?!\d))/g,",")+(oe[2]||"")+(oe[3]||""):pe}function Ge(R){var pe,oe;return(pe=r(o))!=null&&pe.rows&&((oe=r(o).rows.find(ce=>ce.topic===R))==null?void 0:oe.chapter)||null}function rt(R){const pe=R.match(/^(\d{4})(Q([1-4]))?$/);if(!pe)return"0000_0";const oe=pe[1],ce=pe[3]||"5";return`${oe}_${ce}`}function dt(R){return[...R].sort((pe,oe)=>rt(oe).localeCompare(rt(pe)))}let nt=D(()=>r(f).filter(R=>R.kind!=="text"));var st=t1(),xt=d(st);{var St=R=>{var pe=Hm(),oe=d(pe);Ur(oe,{size:18,class:"animate-spin"}),c(R,pe)},Nt=R=>{var pe=Zx(),oe=d(pe);{var ce=ue=>{var P=Jm(),Z=d(P),$e=d(Z);{var ve=Pe=>{var de=Um(),Te=d(de);z(()=>T(Te,`${r(x).length??""}개 기간 · ${r(x)[0]??""} ~ ${r(x)[r(x).length-1]??""}`)),c(Pe,de)};$($e,Pe=>{r(x).length>0&&Pe(ve)})}var ke=m(Z,2);Ae(ke,17,()=>j(r(o).rows),Ne,(Pe,de)=>{var Te=Gm(),Re=d(Te),He=d(Re);{var _e=Je=>{ul(Je,{size:11,class:"flex-shrink-0 opacity-40"})},et=D(()=>r(s).has(r(de).chapter)),Ct=Je=>{Xc(Je,{size:11,class:"flex-shrink-0 opacity-40"})};$(He,Je=>{r(et)?Je(_e):Je(Ct,-1)})}var at=m(He,2),Dt=d(at),Ve=m(at,2),Ee=d(Ve),Ie=m(Re,2);{var yt=Je=>{var At=Km();Ae(At,21,()=>r(de).topics,Ne,(qt,$t)=>{var Mt=Wm(),ct=d(Mt);{var tr=_t=>{Rs(_t,{size:11,class:"flex-shrink-0 text-blue-400/40"})},Mr=_t=>{Di(_t,{size:11,class:"flex-shrink-0 text-emerald-400/40"})},yr=_t=>{zn(_t,{size:11,class:"flex-shrink-0 opacity-30"})};$(ct,_t=>{r($t).source==="finance"?_t(tr):r($t).source==="report"?_t(Mr,1):_t(yr,-1)})}var Br=m(ct,2),zr=d(Br);z(_t=>{Ue(Mt,1,`group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											${r(l)===r($t).topic?"bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]":"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent"}`),T(zr,_t)},[()=>ee(r($t).topic)]),he("click",Mt,()=>S(r($t).topic,r(de).chapter)),c(qt,Mt)}),c(Je,At)},Pt=D(()=>r(s).has(r(de).chapter));$(Ie,Je=>{r(Pt)&&Je(yt)})}z(Je=>{T(Dt,Je),T(Ee,r(de).topics.length)},[()=>fe(r(de).chapter)]),he("click",Re,()=>X(r(de).chapter)),c(Pe,Te)}),c(ue,P)};$(oe,ue=>{r(C)||ue(ce)})}var w=m(oe,2),F=d(w);{var re=ue=>{var P=Ym(),Z=d(P);zn(Z,{size:32,strokeWidth:1,class:"opacity-20"}),c(ue,P)},ie=ue=>{var P=Qx(),Z=ae(P),$e=d(Z),ve=d($e);{var ke=Ve=>{var Ee=Xm(),Ie=d(Ee);z(yt=>T(Ie,yt),[()=>fe(r(u)||Ge(r(l)))]),c(Ve,Ee)},Pe=D(()=>r(u)||Ge(r(l)));$(ve,Ve=>{r(Pe)&&Ve(ke)})}var de=m(ve,2),Te=d(de),Re=m($e,2),He=d(Re);{var _e=Ve=>{Zc(Ve,{size:15})},et=Ve=>{Qc(Ve,{size:15})};$(He,Ve=>{r(C)?Ve(_e):Ve(et,-1)})}var Ct=m(Z,2);{var at=Ve=>{var Ee=Qm(),Ie=d(Ee);Ur(Ie,{size:16,class:"animate-spin"}),c(Ve,Ee)},Dt=Ve=>{var Ee=Xx(),Ie=d(Ee);{var yt=Mt=>{var ct=Zm();c(Mt,ct)};$(Ie,Mt=>{var ct,tr;r(f).length===0&&!(((tr=(ct=r(p))==null?void 0:ct.sections)==null?void 0:tr.length)>0)&&Mt(yt)})}var Pt=m(Ie,2);{var Je=Mt=>{var ct=Mx(),tr=d(ct),Mr=d(tr),yr=d(Mr);{var Br=it=>{var Le=ex(),Qe=d(Le);z(ut=>T(Qe,`최신 기준 ${ut??""}`),[()=>W(r(p).latestPeriod)]),c(it,Le)};$(yr,it=>{r(p).latestPeriod&&it(Br)})}var zr=m(yr,2);{var _t=it=>{var Le=tx(),Qe=d(Le);z((ut,Ot)=>T(Qe,`커버리지 ${ut??""}~${Ot??""}`),[()=>W(r(p).firstPeriod),()=>W(r(p).latestPeriod)]),c(it,Le)};$(zr,it=>{r(p).firstPeriod&&it(_t)})}var Ht=m(zr,2),zt=d(Ht),Lt=m(Ht,2);{var dr=it=>{var Le=rx(),Qe=d(Le);z(()=>T(Qe,`최근 수정 ${r(p).updatedCount??""}개`)),c(it,Le)};$(Lt,it=>{r(p).updatedCount>0&&it(dr)})}var ur=m(Lt,2);{var bt=it=>{var Le=nx(),Qe=d(Le);z(()=>T(Qe,`신규 ${r(p).newCount??""}개`)),c(it,Le)};$(ur,it=>{r(p).newCount>0&&it(bt)})}var Be=m(ur,2);{var rr=it=>{var Le=ax(),Qe=d(Le);z(()=>T(Qe,`과거 유지 ${r(p).staleCount??""}개`)),c(it,Le)};$(Be,it=>{r(p).staleCount>0&&it(rr)})}var Cr=m(tr,2);Ae(Cr,17,()=>r(p).sections,Ne,(it,Le)=>{const Qe=D(()=>q(r(Le))),ut=D(()=>Y(r(Le)));var Ot=Sx(),Tt=d(Ot);{var gt=Me=>{var be=sx();Ae(be,21,()=>r(Le).headingPath,Ne,(De,Ye)=>{var ft=ox(),vt=d(ft);Kn(vt,()=>E(r(Ye).text)),c(De,ft)}),c(Me,be)};$(Tt,Me=>{var be;((be=r(Le).headingPath)==null?void 0:be.length)>0&&Me(gt)})}var wt=m(Tt,2),Ft=d(wt),Kt=d(Ft),Xt=m(Ft,2);{var _r=Me=>{var be=ix(),De=d(be);z(Ye=>T(De,`최신 ${Ye??""}`),[()=>W(r(Le).latestPeriod)]),c(Me,be)};$(Xt,Me=>{var be;(be=r(Le).latestPeriod)!=null&&be.label&&Me(_r)})}var Or=m(Xt,2);{var $r=Me=>{var be=lx(),De=d(be);z(Ye=>T(De,`최초 ${Ye??""}`),[()=>W(r(Le).firstPeriod)]),c(Me,be)};$(Or,Me=>{var be,De;(be=r(Le).firstPeriod)!=null&&be.label&&r(Le).firstPeriod.label!==((De=r(Le).latestPeriod)==null?void 0:De.label)&&Me($r)})}var ar=m(Or,2);{var fr=Me=>{var be=dx(),De=d(be);z(()=>T(De,`${r(Le).periodCount??""}기간`)),c(Me,be)};$(ar,Me=>{r(Le).periodCount>0&&Me(fr)})}var qr=m(ar,2);{var Zt=Me=>{var be=cx(),De=d(be);z(()=>T(De,`최근 변경 ${r(Le).latestChange??""}`)),c(Me,be)};$(qr,Me=>{r(Le).latestChange&&Me(Zt)})}var hr=m(wt,2);{var vr=Me=>{var be=fx();Ae(be,21,()=>r(Le).timeline,Ne,(De,Ye)=>{var ft=ux(),vt=d(ft),It=d(vt);z((Gt,Ut)=>{Ue(ft,1,`vw-timeline-chip ${Gt??""}`,"svelte-1l2nqwu"),T(It,Ut)},[()=>J(r(Le),r(Ye).period.label)?"is-active":"",()=>W(r(Ye).period)]),he("click",ft,()=>G(r(Le).id,r(Ye).period.label)),c(De,ft)}),c(Me,be)};$(hr,Me=>{var be;((be=r(Le).timeline)==null?void 0:be.length)>0&&Me(vr)})}var _n=m(hr,2);{var an=Me=>{var be=hx(),De=d(be),Ye=d(De),ft=m(De,2);{var vt=Wt=>{var cr=vx(),kt=d(cr);z(Q=>T(kt,`비교 ${Q??""}`),[()=>W(r(Qe).prevPeriod)]),c(Wt,cr)},It=Wt=>{var cr=px();c(Wt,cr)};$(ft,Wt=>{var cr;(cr=r(Qe).prevPeriod)!=null&&cr.label?Wt(vt):Wt(It,-1)})}var Gt=m(ft,2),Ut=d(Gt);z((Wt,cr)=>{T(Ye,`선택 ${Wt??""}`),T(Ut,cr)},[()=>W(r(Qe).period),()=>ye(r(Qe).status)]),c(Me,be)};$(_n,Me=>{r(ut)&&r(Qe)&&Me(an)})}var Tn=m(_n,2);{var A=Me=>{const be=D(()=>r(Qe).digest);var De=bx(),Ye=d(De),ft=d(Ye),vt=d(ft),It=m(Ye,2),Gt=d(It);Ae(Gt,17,()=>r(be).items.filter(Q=>Q.kind==="numeric"),Ne,(Q,xe)=>{var Fe=mx(),qe=m(d(Fe));z(()=>T(qe,` ${r(xe).text??""}`)),c(Q,Fe)});var Ut=m(Gt,2);Ae(Ut,17,()=>r(be).items.filter(Q=>Q.kind==="added"),Ne,(Q,xe)=>{var Fe=xx(),qe=m(d(Fe),2),Ze=d(qe);z(()=>T(Ze,r(xe).text)),c(Q,Fe)});var Wt=m(Ut,2);Ae(Wt,17,()=>r(be).items.filter(Q=>Q.kind==="removed"),Ne,(Q,xe)=>{var Fe=gx(),qe=m(d(Fe),2),Ze=d(qe);z(()=>T(Ze,r(xe).text)),c(Q,Fe)});var cr=m(Wt,2);{var kt=Q=>{var xe=_x(),Fe=d(xe);z(()=>T(Fe,`외 ${r(be).wordingCount??""}건 문구 수정`)),c(Q,xe)};$(cr,Q=>{r(be).wordingCount>0&&Q(kt)})}z(()=>T(vt,`${r(be).to??""} vs ${r(be).from??""}`)),c(Me,De)};$(Tn,Me=>{var be,De,Ye;r(ut)&&((Ye=(De=(be=r(Qe))==null?void 0:be.digest)==null?void 0:De.items)==null?void 0:Ye.length)>0&&Me(A)})}var ge=m(Tn,2);{var We=Me=>{var be=Ce(),De=ae(be);{var Ye=vt=>{var It=Cx();Ae(It,21,()=>Se(r(Qe)),Ne,(Gt,Ut)=>{var Wt=Ce(),cr=ae(Wt);{var kt=qe=>{var Ze=Ce(),Rt=ae(Ze);Kn(Rt,()=>E(r(Ut).text)),c(qe,Ze)},Q=qe=>{var Ze=wx(),Rt=d(Ze);z(()=>T(Rt,r(Ut).text)),c(qe,Ze)},xe=qe=>{var Ze=yx(),Rt=d(Ze);z(()=>T(Rt,r(Ut).text)),c(qe,Ze)},Fe=qe=>{var Ze=kx(),Rt=d(Ze);z(()=>T(Rt,r(Ut).text)),c(qe,Ze)};$(cr,qe=>{r(Ut).kind==="heading"?qe(kt):r(Ut).kind==="same"?qe(Q,1):r(Ut).kind==="added"?qe(xe,2):r(Ut).kind==="removed"&&qe(Fe,3)})}c(Gt,Wt)}),c(vt,It)},ft=vt=>{var It=$x(),Gt=d(It);Kn(Gt,()=>H(r(Qe).body)),c(vt,It)};$(De,vt=>{var It,Gt;r(ut)&&((It=r(Qe).prevPeriod)!=null&&It.label)&&((Gt=r(Qe).diff)==null?void 0:Gt.length)>0?vt(Ye):vt(ft,-1)})}c(Me,be)};$(ge,Me=>{r(Qe)&&Me(We)})}z((Me,be)=>{Ue(Ot,1,`vw-text-section ${r(Le).status==="stale"?"vw-text-section-stale":""}`,"svelte-1l2nqwu"),Ue(Ft,1,`vw-status-pill ${Me??""}`,"svelte-1l2nqwu"),T(Kt,be)},[()=>ze(r(Le).status),()=>V(r(Le).status)]),c(it,Ot)}),z(()=>T(zt,`본문 ${r(p).sectionCount??""}개`)),c(Mt,ct)};$(Pt,Mt=>{var ct,tr;((tr=(ct=r(p))==null?void 0:ct.sections)==null?void 0:tr.length)>0&&Mt(Je)})}var At=m(Pt,2);{var qt=Mt=>{var ct=zx();c(Mt,ct)};$(At,Mt=>{r(nt).length>0&&Mt(qt)})}var $t=m(At,2);Ae($t,17,()=>r(nt),Ne,(Mt,ct)=>{var tr=Ce(),Mr=ae(tr);{var yr=zt=>{const Lt=D(()=>{var gt;return((gt=r(ct).data)==null?void 0:gt.columns)||[]}),dr=D(()=>{var gt;return((gt=r(ct).data)==null?void 0:gt.rows)||[]}),ur=D(()=>r(ct).meta||{}),bt=D(()=>r(ur).scaleDivisor||1);var Be=Nx(),rr=ae(Be);{var Cr=gt=>{var wt=Tx(),Ft=d(wt);z(()=>T(Ft,`(단위: ${r(ur).scale??""})`)),c(gt,wt)};$(rr,gt=>{r(ur).scale&&gt(Cr)})}var it=m(rr,2),Le=d(it),Qe=d(Le),ut=d(Qe),Ot=d(ut);Ae(Ot,21,()=>r(Lt),Ne,(gt,wt,Ft)=>{const Kt=D(()=>/^\d{4}/.test(r(wt)));var Xt=Ix(),_r=d(Xt);z(()=>{Ue(Xt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${r(Kt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${Ft===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),T(_r,r(wt))}),c(gt,Xt)});var Tt=m(ut);Ae(Tt,21,()=>r(dr),Ne,(gt,wt,Ft)=>{var Kt=Ex();Ue(Kt,1,`hover:bg-white/[0.03] ${Ft%2===1?"bg-white/[0.012]":""}`),Ae(Kt,21,()=>r(Lt),Ne,(Xt,_r,Or)=>{const $r=D(()=>r(wt)[r(_r)]??""),ar=D(()=>te(r($r))),fr=D(()=>Oe(r($r))),qr=D(()=>r(ar)?tt(r($r),r(bt)):r($r));var Zt=Ax(),hr=d(Zt);z(()=>{Ue(Zt,1,`px-3 py-1.5 border-b border-white/[0.025]
																	${r(ar)?"text-right tabular-nums font-mono text-[11.5px]":"whitespace-nowrap"}
																	${r(fr)?"text-red-400/60":r(ar)?"text-dl-text/90":""}
																	${Or===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]":"text-dl-text-muted"}
																	${Or===0&&Ft%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),T(hr,r(qr))}),c(Xt,Zt)}),c(gt,Kt)}),c(zt,Be)},Br=zt=>{const Lt=D(()=>{var gt;return((gt=r(ct).data)==null?void 0:gt.columns)||[]}),dr=D(()=>{var gt;return((gt=r(ct).data)==null?void 0:gt.rows)||[]}),ur=D(()=>r(ct).meta||{}),bt=D(()=>r(ur).scaleDivisor||1);var Be=Rx(),rr=ae(Be);{var Cr=gt=>{var wt=Px(),Ft=d(wt);z(()=>T(Ft,`(단위: ${r(ur).scale??""})`)),c(gt,wt)};$(rr,gt=>{r(ur).scale&&gt(Cr)})}var it=m(rr,2),Le=d(it),Qe=d(Le),ut=d(Qe),Ot=d(ut);Ae(Ot,21,()=>r(Lt),Ne,(gt,wt,Ft)=>{const Kt=D(()=>/^\d{4}/.test(r(wt)));var Xt=Lx(),_r=d(Xt);z(()=>{Ue(Xt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${r(Kt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${Ft===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),T(_r,r(wt))}),c(gt,Xt)});var Tt=m(ut);Ae(Tt,21,()=>r(dr),Ne,(gt,wt,Ft)=>{var Kt=Dx();Ue(Kt,1,`hover:bg-white/[0.03] ${Ft%2===1?"bg-white/[0.012]":""}`),Ae(Kt,21,()=>r(Lt),Ne,(Xt,_r,Or)=>{const $r=D(()=>r(wt)[r(_r)]??""),ar=D(()=>te(r($r))),fr=D(()=>Oe(r($r))),qr=D(()=>r(ar)?r(bt)>1?tt(r($r),r(bt)):ot(r($r)):r($r));var Zt=Ox(),hr=d(Zt);z(()=>{Ue(Zt,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${r(ar)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${r(fr)?"text-red-400/60":r(ar)?"text-dl-text/90":""}
																	${Or===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Or===0&&Ft%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),T(hr,r(qr))}),c(Xt,Zt)}),c(gt,Kt)}),c(zt,Be)},zr=zt=>{const Lt=D(()=>dt(Object.keys(r(ct).rawMarkdown))),dr=D(()=>r(g).get(r(ct).block)??0),ur=D(()=>r(Lt)[r(dr)]||r(Lt)[0]);var bt=Bx(),Be=d(bt);{var rr=Qe=>{var ut=Vx(),Ot=d(ut);Ae(Ot,17,()=>r(Lt).slice(0,8),Ne,(wt,Ft,Kt)=>{var Xt=jx(),_r=d(Xt);z(()=>{Ue(Xt,1,`px-2 py-0.5 rounded text-[10px] transition-colors
															${Kt===r(dr)?"bg-white/[0.08] text-dl-text font-medium":"text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]"}`),T(_r,r(Ft))}),he("click",Xt,()=>me(r(ct).block,Kt)),c(wt,Xt)});var Tt=m(Ot,2);{var gt=wt=>{var Ft=Fx(),Kt=d(Ft);z(()=>T(Kt,`외 ${r(Lt).length-8}개`)),c(wt,Ft)};$(Tt,wt=>{r(Lt).length>8&&wt(gt)})}c(Qe,ut)};$(Be,Qe=>{r(Lt).length>1&&Qe(rr)})}var Cr=m(Be,2),it=d(Cr),Le=d(it);Kn(Le,()=>Va(r(ct).rawMarkdown[r(ur)])),c(zt,bt)},_t=zt=>{const Lt=D(()=>{var ut;return((ut=r(ct).data)==null?void 0:ut.columns)||[]}),dr=D(()=>{var ut;return((ut=r(ct).data)==null?void 0:ut.rows)||[]});var ur=Wx(),bt=d(ur),Be=d(bt);Di(Be,{size:12,class:"text-emerald-400/50"});var rr=m(bt,2),Cr=d(rr),it=d(Cr),Le=d(it);Ae(Le,21,()=>r(Lt),Ne,(ut,Ot,Tt)=>{const gt=D(()=>/^\d{4}/.test(r(Ot)));var wt=qx(),Ft=d(wt);z(()=>{Ue(wt,1,`px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															${r(gt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
															${Tt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),T(Ft,r(Ot))}),c(ut,wt)});var Qe=m(it);Ae(Qe,21,()=>r(dr),Ne,(ut,Ot,Tt)=>{var gt=Ux();Ue(gt,1,`hover:bg-white/[0.03] ${Tt%2===1?"bg-white/[0.012]":""}`),Ae(gt,21,()=>r(Lt),Ne,(wt,Ft,Kt)=>{const Xt=D(()=>r(Ot)[r(Ft)]??""),_r=D(()=>te(r(Xt))),Or=D(()=>Oe(r(Xt)));var $r=Hx(),ar=d($r);z(fr=>{Ue($r,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${r(_r)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${r(Or)?"text-red-400/60":r(_r)?"text-dl-text/90":""}
																	${Kt===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Kt===0&&Tt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),T(ar,fr)},[()=>r(_r)?ot(r(Xt)):r(Xt)]),c(wt,$r)}),c(ut,gt)}),c(zt,ur)},Ht=zt=>{const Lt=D(()=>r(ct).data.columns),dr=D(()=>r(ct).data.rows||[]);var ur=Yx(),bt=d(ur),Be=d(bt),rr=d(Be),Cr=d(rr);Ae(Cr,21,()=>r(Lt),Ne,(Le,Qe)=>{var ut=Kx(),Ot=d(ut);z(()=>T(Ot,r(Qe))),c(Le,ut)});var it=m(rr);Ae(it,21,()=>r(dr),Ne,(Le,Qe,ut)=>{var Ot=Jx();Ue(Ot,1,`hover:bg-white/[0.03] ${ut%2===1?"bg-white/[0.012]":""}`),Ae(Ot,21,()=>r(Lt),Ne,(Tt,gt)=>{var wt=Gx(),Ft=d(wt);z(()=>T(Ft,r(Qe)[r(gt)]??"")),c(Tt,wt)}),c(Le,Ot)}),c(zt,ur)};$(Mr,zt=>{var Lt,dr;r(ct).kind==="finance"?zt(yr):r(ct).kind==="structured"?zt(Br,1):r(ct).kind==="raw_markdown"&&r(ct).rawMarkdown?zt(zr,2):r(ct).kind==="report"?zt(_t,3):((dr=(Lt=r(ct).data)==null?void 0:Lt.columns)==null?void 0:dr.length)>0&&zt(Ht,4)})}c(Mt,tr)}),c(Ve,Ee)};$(Ct,Ve=>{r(_)?Ve(at):Ve(Dt,-1)})}z(Ve=>{T(Te,Ve),ir(Re,"title",r(C)?"목차 표시":"전체화면")},[()=>ee(r(l))]),he("click",Re,()=>v(C,!r(C))),c(ue,P)};$(F,ue=>{r(l)?ue(ie,-1):ue(re)})}c(R,pe)},lr=R=>{var pe=e1(),oe=d(pe);zn(oe,{size:36,strokeWidth:1,class:"opacity-20"}),c(R,pe)};$(xt,R=>{var pe;r(i)?R(St):(pe=r(o))!=null&&pe.rows?R(Nt,1):R(lr,-1)})}c(t,st),Ar()}Kr(["click"]);var n1=h('<span class="text-[12px] font-semibold text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim"> </span>',1),a1=h('<span class="text-[12px] font-semibold text-dl-text"> </span>'),o1=h('<span class="text-[12px] font-semibold text-dl-text">데이터</span>'),s1=h('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" title="Excel 다운로드"><!></button> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button>',1),i1=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),l1=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed"> </pre>'),d1=h('<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2"> </div>'),c1=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),u1=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),f1=h("<!> <!>",1),v1=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),p1=h('<div class="p-4"><!></div>'),h1=h('<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">표시할 내용이 없습니다</div>'),m1=h('<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark"><div class="flex items-center justify-between h-10 mt-8 px-4 border-b border-dl-border/40 flex-shrink-0"><div class="flex items-center gap-2 min-w-0"><!></div> <div class="flex items-center gap-1"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 overflow-auto min-h-0"><!></div></div>');function x1(t,e){Ir(e,!0);let n=je(e,"mode",3,null),a=je(e,"company",3,null),o=je(e,"data",3,null),i=je(e,"onTopicChange",3,null),s=je(e,"onFullscreen",3,null),l=je(e,"isFullscreen",3,!1),u=K(!1);async function f(){var V;if(!(!((V=a())!=null&&V.stockCode)||r(u))){v(u,!0);try{await Nv(a().stockCode)}catch(ze){console.error("Excel download error:",ze)}v(u,!1)}}function p(V){return V?/^\|.+\|$/m.test(V)||/^#{1,3} /m.test(V)||/\*\*[^*]+\*\*/m.test(V)||/```/.test(V):!1}var _=m1(),x=d(_),b=d(x),k=d(b);{var C=V=>{var ze=n1(),j=ae(ze),B=d(j),le=m(j,2),we=d(le);z(()=>{T(B,a().corpName||a().company),T(we,a().stockCode)}),c(V,ze)},g=V=>{var ze=a1(),j=d(ze);z(()=>T(j,o().label)),c(V,ze)},y=V=>{var ze=o1();c(V,ze)};$(k,V=>{var ze;n()==="viewer"&&a()?V(C):n()==="data"&&((ze=o())!=null&&ze.label)?V(g,1):n()==="data"&&V(y,2)})}var I=m(b,2),O=d(I);{var M=V=>{var ze=s1(),j=ae(ze),B=d(j);{var le=H=>{Ur(H,{size:14,class:"animate-spin"})},we=H=>{os(H,{size:14})};$(B,H=>{r(u)?H(le):H(we,-1)})}var U=m(j,2),ne=d(U);{var N=H=>{Zc(H,{size:14})},W=H=>{Qc(H,{size:14})};$(ne,H=>{l()?H(N):H(W,-1)})}z(()=>{j.disabled=r(u),ir(U,"title",l()?"패널 모드로":"전체 화면")}),he("click",j,f),he("click",U,()=>{var H;return(H=s())==null?void 0:H()}),c(V,ze)};$(O,V=>{var ze;n()==="viewer"&&((ze=a())!=null&&ze.stockCode)&&V(M)})}var ee=m(O,2),fe=d(ee);Fa(fe,{size:15});var L=m(x,2),S=d(L);{var X=V=>{r1(V,{get stockCode(){return a().stockCode},get onTopicChange(){return i()}})},G=V=>{var ze=p1(),j=d(ze);{var B=U=>{var ne=Ce(),N=ae(ne);{var W=q=>{var J=i1(),Y=d(J);Kn(Y,()=>Va(o())),c(q,J)},H=D(()=>p(o())),E=q=>{var J=l1(),Y=d(J);z(()=>T(Y,o())),c(q,J)};$(N,q=>{r(H)?q(W):q(E,-1)})}c(U,ne)},le=U=>{var ne=f1(),N=ae(ne);{var W=Y=>{var ye=d1(),Se=d(ye);z(()=>T(Se,o().module)),c(Y,ye)};$(N,Y=>{o().module&&Y(W)})}var H=m(N,2);{var E=Y=>{var ye=c1(),Se=d(ye);Kn(Se,()=>Va(o().text)),c(Y,ye)},q=D(()=>p(o().text)),J=Y=>{var ye=u1(),Se=d(ye);z(()=>T(Se,o().text)),c(Y,ye)};$(H,Y=>{r(q)?Y(E):Y(J,-1)})}c(U,ne)},we=U=>{var ne=v1(),N=d(ne);z(W=>T(N,W),[()=>JSON.stringify(o(),null,2)]),c(U,ne)};$(j,U=>{var ne;typeof o()=="string"?U(B):(ne=o())!=null&&ne.text?U(le,1):U(we,-1)})}c(V,ze)},me=V=>{var ze=h1();c(V,ze)};$(S,V=>{n()==="viewer"&&a()?V(X):n()==="data"&&o()?V(G,1):V(me,-1)})}he("click",ee,()=>{var V;return(V=e.onClose)==null?void 0:V.call(e)}),c(t,_),Ar()}Kr(["click"]);var g1=h('<div class="flex flex-col items-center justify-center py-8 gap-2"><!> <span class="text-[11px] text-dl-text-dim">목차 로딩 중...</span></div>'),_1=h('<button><!> <span class="truncate"> </span></button>'),b1=h('<div class="mb-1 pb-1 border-b border-dl-border/15"><div class="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-amber-400/70 uppercase tracking-wider"><!> <span>즐겨찾기</span></div> <!></div>'),w1=h('<button class="flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors text-dl-text-dim hover:text-dl-text hover:bg-white/5"><!> <span class="truncate"> </span></button>'),y1=h('<div class="mb-1 pb-1 border-b border-dl-border/15"><div class="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-dl-text-dim/60 uppercase tracking-wider"><!> <span>최근</span></div> <!></div>'),k1=h('<span class="w-1.5 h-1.5 rounded-full bg-emerald-400/70" title="최근 변경"></span>'),C1=h('<span class="text-[9px] text-dl-text-dim/60 font-mono"> </span>'),$1=h('<button><!> <span class="truncate"> </span> <span class="ml-auto flex items-center gap-0.5"><!> <!> <!></span></button>'),S1=h('<div class="ml-2 border-l border-dl-border/20 pl-1"></div>'),M1=h('<div class="mb-0.5"><button class="flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-left text-[11px] font-semibold uppercase tracking-wider text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"><!> <span class="truncate"> </span> <span> </span></button> <!></div>'),z1=h("<!> <!> <!>",1),T1=h('<div class="px-3 py-6 text-center text-[12px] text-dl-text-dim">종목을 선택하면 목차가 표시됩니다</div>'),I1=h('<nav class="flex flex-col h-full min-h-0 overflow-y-auto py-2 px-1"><!></nav>');function A1(t,e){Ir(e,!0);let n=je(e,"toc",3,null),a=je(e,"loading",3,!1),o=je(e,"selectedTopic",3,null),i=je(e,"expandedChapters",19,()=>new Set),s=je(e,"bookmarks",19,()=>[]),l=je(e,"recentHistory",19,()=>[]),u=je(e,"visitedTopics",19,()=>new Set),f=je(e,"onSelectTopic",3,null),p=je(e,"onToggleChapter",3,null),_=je(e,"onPrefetch",3,null),x=null;function b(L){clearTimeout(x),x=setTimeout(()=>{var S;return(S=_())==null?void 0:S(L)},300)}function k(){clearTimeout(x)}const C=new Set(["BS","IS","CIS","CF","SCE","ratios"]);function g(L){return C.has(L)?Rs:zn}function y(L){return L.tableCount>0&&L.textCount>0?"both":L.tableCount>0?"table":L.textCount>0?"text":"empty"}gr(()=>{o()&&fc().then(()=>{const L=document.querySelector(".viewer-nav-active-item");L&&L.scrollIntoView({block:"nearest",behavior:"smooth"})})});var I=I1(),O=d(I);{var M=L=>{var S=g1(),X=d(S);Ur(X,{size:18,class:"animate-spin text-dl-text-dim"}),c(L,S)},ee=L=>{var S=z1(),X=ae(S);{var G=j=>{const B=D(()=>s().map(ne=>{for(const N of n().chapters){const W=N.topics.find(H=>H.topic===ne);if(W)return{...W,chapter:N.chapter}}return null}).filter(Boolean));var le=Ce(),we=ae(le);{var U=ne=>{var N=b1(),W=d(N),H=d(W);Fi(H,{size:10,fill:"currentColor"});var E=m(W,2);Ae(E,17,()=>r(B),Ne,(q,J)=>{const Y=D(()=>o()===r(J).topic);var ye=_1(),Se=d(ye);Fi(Se,{size:10,class:"text-amber-400/60 flex-shrink-0",fill:"currentColor"});var te=m(Se,2),Oe=d(te);z(()=>{Ue(ye,1,`flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors ${r(Y)?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-muted hover:text-dl-text hover:bg-white/5"}`),T(Oe,r(J).label)}),he("click",ye,()=>{var tt;return(tt=f())==null?void 0:tt(r(J).topic,r(J).chapter)}),c(q,ye)}),c(ne,N)};$(we,ne=>{r(B).length>0&&ne(U)})}c(j,le)};$(X,j=>{s().length>0&&j(G)})}var me=m(X,2);{var V=j=>{const B=D(()=>new Set(s())),le=D(()=>l().slice(0,5).filter(N=>N.topic!==o()&&!r(B).has(N.topic)));var we=Ce(),U=ae(we);{var ne=N=>{var W=y1(),H=d(W),E=d(H);ls(E,{size:10});var q=m(H,2);Ae(q,17,()=>r(le),Ne,(J,Y)=>{var ye=w1(),Se=d(ye);ls(Se,{size:10,class:"text-dl-text-dim/30 flex-shrink-0"});var te=m(Se,2),Oe=d(te);z(()=>T(Oe,r(Y).label)),he("click",ye,()=>{var tt;return(tt=f())==null?void 0:tt(r(Y).topic,null)}),c(J,ye)}),c(N,W)};$(U,N=>{r(le).length>0&&N(ne)})}c(j,we)};$(me,j=>{l().length>0&&j(V)})}var ze=m(me,2);Ae(ze,17,()=>n().chapters,Ne,(j,B)=>{const le=D(()=>r(B).topics.filter(Oe=>u().has(Oe.topic)).length);var we=M1(),U=d(we),ne=d(U);{var N=Oe=>{ul(Oe,{size:12})},W=D(()=>i().has(r(B).chapter)),H=Oe=>{Xc(Oe,{size:12})};$(ne,Oe=>{r(W)?Oe(N):Oe(H,-1)})}var E=m(ne,2),q=d(E),J=m(E,2),Y=d(J),ye=m(U,2);{var Se=Oe=>{var tt=S1();Ae(tt,21,()=>r(B).topics,Ne,(ot,Ge)=>{const rt=D(()=>g(r(Ge).topic)),dt=D(()=>y(r(Ge))),nt=D(()=>o()===r(Ge).topic),st=D(()=>u().has(r(Ge).topic));var xt=$1(),St=d(xt);Ao(St,()=>r(rt),(ie,ue)=>{ue(ie,{size:12,class:"flex-shrink-0 opacity-50"})});var Nt=m(St,2),lr=d(Nt),R=m(Nt,2),pe=d(R);{var oe=ie=>{var ue=k1();c(ie,ue)};$(pe,ie=>{r(Ge).hasChanges&&ie(oe)})}var ce=m(pe,2);{var w=ie=>{Vi(ie,{size:9,class:"text-dl-text-dim/40"})};$(ce,ie=>{(r(dt)==="table"||r(dt)==="both")&&ie(w)})}var F=m(ce,2);{var re=ie=>{var ue=C1(),P=d(ue);z(()=>T(P,r(Ge).tableCount)),c(ie,ue)};$(F,ie=>{r(Ge).tableCount>0&&ie(re)})}z(()=>{Ue(xt,1,`${r(nt)?"viewer-nav-active-item":""} viewer-nav-active flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors ${r(nt)?"text-dl-text bg-dl-surface-active font-medium":r(st)?"text-dl-text/70 hover:text-dl-text hover:bg-white/5":"text-dl-text-muted hover:text-dl-text hover:bg-white/5"}`),T(lr,r(Ge).label)}),he("click",xt,()=>{var ie;return(ie=f())==null?void 0:ie(r(Ge).topic,r(B).chapter)}),xn("mouseenter",xt,()=>b(r(Ge).topic)),xn("mouseleave",xt,k),c(ot,xt)}),c(Oe,tt)},te=D(()=>i().has(r(B).chapter));$(ye,Oe=>{r(te)&&Oe(Se)})}z(()=>{T(q,r(B).chapter),Ue(J,1,`ml-auto text-[9px] font-mono ${r(le)===r(B).topics.length&&r(B).topics.length>0?"text-emerald-400/60":"text-dl-text-dim/60"}`),T(Y,`${r(le)??""}/${r(B).topics.length??""}`)}),he("click",U,()=>{var Oe;return(Oe=p())==null?void 0:Oe(r(B).chapter)}),c(j,we)}),c(L,S)},fe=L=>{var S=T1();c(L,S)};$(O,L=>{var S;a()?L(M):(S=n())!=null&&S.chapters?L(ee,1):L(fe,-1)})}c(t,I),Ar()}Kr(["click"]);const E1="modulepreload",N1=function(t){return"/"+t},dd={},Bi=function(e,n,a){let o=Promise.resolve();if(n&&n.length>0){let s=function(f){return Promise.all(f.map(p=>Promise.resolve(p).then(_=>({status:"fulfilled",value:_}),_=>({status:"rejected",reason:_}))))};document.getElementsByTagName("link");const l=document.querySelector("meta[property=csp-nonce]"),u=(l==null?void 0:l.nonce)||(l==null?void 0:l.getAttribute("nonce"));o=s(n.map(f=>{if(f=N1(f),f in dd)return;dd[f]=!0;const p=f.endsWith(".css"),_=p?'[rel="stylesheet"]':"";if(document.querySelector(`link[href="${f}"]${_}`))return;const x=document.createElement("link");if(x.rel=p?"stylesheet":E1,p||(x.as="script"),x.crossOrigin="",x.href=f,u&&x.setAttribute("nonce",u),document.head.appendChild(x),p)return new Promise((b,k)=>{x.addEventListener("load",b),x.addEventListener("error",()=>k(new Error(`Unable to preload CSS for ${f}`)))})}))}function i(s){const l=new Event("vite:preloadError",{cancelable:!0});if(l.payload=s,window.dispatchEvent(l),!l.defaultPrevented)throw s}return o.then(s=>{for(const l of s||[])l.status==="rejected"&&i(l.reason);return e().catch(i)})},qi=["#ea4647","#fb923c","#3b82f6","#22c55e","#8b5cf6","#06b6d4","#f59e0b","#ec4899"],cd={performance:"성과",profitability:"수익성",health:"건전성",cashflow:"현금흐름",governance:"지배구조",risk:"리스크",opportunity:"기회"},P1={A:5,B:4,C:3,D:2,F:0};function L1(t){var f,p;if(!((f=t==null?void 0:t.data)!=null&&f.rows)||!((p=t==null?void 0:t.data)!=null&&p.columns))return null;const{rows:e,columns:n}=t.data,a=t.meta||{},o=n.filter(_=>/^\d{4}/.test(_));if(o.length<2)return null;const i=n[0],s=[],l=["bar","line","line"];return e.slice(0,3).forEach((_,x)=>{const b=_[i]||`항목${x}`,k=o.map(C=>{const g=_[C];return g!=null?Number(g):0});k.some(C=>C!==0)&&s.push({name:b,data:k,color:qi[x%qi.length],type:l[x]||"line"})}),s.length===0?null:{chartType:"combo",title:a.title||"재무 추이",series:s,categories:o,options:{unit:a.unit||"백만원"}}}function O1(t,e=""){if(!t)return null;const n=Object.keys(cd),a=n.map(i=>cd[i]),o=n.map(i=>{var l;const s=((l=t[i])==null?void 0:l.grade)||t[i]||"F";return P1[s]??0});return{chartType:"radar",title:e?`${e} 투자 인사이트`:"투자 인사이트",series:[{name:e||"등급",data:o,color:qi[0]}],categories:a,options:{maxValue:5}}}var D1=h("<button> </button>"),R1=h('<div class="flex items-center gap-0.5 overflow-x-auto py-1 scrollbar-thin"></div>');function ou(t,e){Ir(e,!0);let n=je(e,"periods",19,()=>[]),a=je(e,"selected",3,null),o=je(e,"onSelect",3,null);function i(p){return/^\d{4}$/.test(p)||/^\d{4}Q4$/.test(p)}function s(p){const _=p.match(/^(\d{4})(Q([1-4]))?$/);if(!_)return p;const x="'"+_[1].slice(2);return _[3]?`${x}.${_[3]}Q`:x}var l=Ce(),u=ae(l);{var f=p=>{var _=R1();Ae(_,21,n,Ne,(x,b)=>{var k=D1(),C=d(k);z((g,y)=>{Ue(k,1,`flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] font-mono transition-colors
					${g??""}`),ir(k,"title",r(b)),T(C,y)},[()=>a()===r(b)?"bg-dl-primary/20 text-dl-primary-light font-medium":i(r(b))?"text-dl-text-muted hover:text-dl-text hover:bg-white/5":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5",()=>s(r(b))]),he("click",k,()=>{var g;return(g=o())==null?void 0:g(r(b))}),c(x,k)}),c(p,_)};$(u,p=>{n().length>0&&p(f)})}c(t,l),Ar()}Kr(["click"]);var j1=h('<div class="mb-1"><!></div>'),F1=h('<!> <div class="text-[10px] text-dl-text-dim mb-1 font-mono"> </div> <div class="prose-dartlab overflow-x-auto"><!></div>',1),V1=h('<th class="cursor-pointer select-none hover:text-dl-text"> </th>'),B1=h("<td> </td>"),q1=h("<tr></tr>"),H1=h('<button class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"> </button>'),U1=h('<div class="text-[10px] text-dl-text-dim mt-1"> </div>'),W1=h('<div class="overflow-x-auto rounded-lg border border-dl-border/10"><table class="finance-table"><thead><tr></tr></thead><tbody></tbody></table> <!></div> <!>',1),K1=h("<th> </th>"),G1=h("<td> </td>"),J1=h("<tr></tr>"),Y1=h('<button class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"> </button>'),X1=h('<div class="text-[10px] text-dl-text-dim mt-1"> </div>'),Q1=h('<div class="overflow-x-auto rounded-lg border border-dl-border/10"><table class="structured-table"><thead><tr></tr></thead><tbody></tbody></table> <!></div> <!>',1);function ud(t,e){Ir(e,!0);let n=je(e,"block",3,null),a=je(e,"maxRows",3,100),o=K(null),i=K(!1),s=K(null),l=K("asc");function u(L){r(s)===L?v(l,r(l)==="asc"?"desc":"asc",!0):(v(s,L,!0),v(l,"asc"))}function f(L){return r(s)!==L?"":r(l)==="asc"?" ▲":" ▼"}const p=new Set(["매출액","revenue","영업이익","operating_income","당기순이익","net_income","자산총계","total_assets","부채총계","total_liabilities","자본총계","total_equity","영업활동현금흐름","operating_cash_flow","매출총이익","gross_profit","EBITDA"]);function _(L,S){if(!(S!=null&&S.length))return!1;const X=String(L[S[0]]??"").trim();return p.has(X)}function x(L){if(L==null||L===""||L==="-")return L??"";if(typeof L=="number")return Math.abs(L)>=1?L.toLocaleString("ko-KR"):L.toString();const S=String(L).trim();if(/^-?[\d,]+(\.\d+)?$/.test(S)){const X=parseFloat(S.replace(/,/g,""));if(!isNaN(X))return Math.abs(X)>=1?X.toLocaleString("ko-KR"):X.toString()}return L}function b(L){if(typeof L=="number")return L<0;const S=String(L??"").trim().replace(/,/g,"");return/^-\d/.test(S)}function k(L){return typeof L=="number"?!0:typeof L=="string"&&/^-?[\d,]+(\.\d+)?$/.test(L.trim())}function C(L){return(L==null?void 0:L.kind)==="finance"}function g(L){return L!=null&&L.rawMarkdown?Object.keys(L.rawMarkdown):[]}function y(L){const S=g(L);return r(o)&&S.includes(r(o))?r(o):S[0]??null}let I=D(()=>{var X,G;const L=((G=(X=n())==null?void 0:X.data)==null?void 0:G.rows)??[];return r(s)?[...L].sort((me,V)=>{let ze=me[r(s)],j=V[r(s)];const B=typeof ze=="number"?ze:parseFloat(String(ze??"").replace(/,/g,"")),le=typeof j=="number"?j:parseFloat(String(j??"").replace(/,/g,""));return!isNaN(B)&&!isNaN(le)?r(l)==="asc"?B-le:le-B:(ze=String(ze??""),j=String(j??""),r(l)==="asc"?ze.localeCompare(j):j.localeCompare(ze))}):L}),O=D(()=>r(i)?r(I):r(I).slice(0,a()));var M=Ce(),ee=ae(M);{var fe=L=>{var S=Ce(),X=ae(S);{var G=j=>{const B=D(()=>g(n())),le=D(()=>y(n()));var we=Ce(),U=ae(we);{var ne=N=>{var W=F1(),H=ae(W);{var E=Se=>{var te=j1(),Oe=d(te);ou(Oe,{get periods(){return r(B)},get selected(){return r(le)},onSelect:tt=>{v(o,tt,!0)}}),c(Se,te)};$(H,Se=>{r(B).length>1&&Se(E)})}var q=m(H,2),J=d(q),Y=m(q,2),ye=d(Y);Kn(ye,()=>Va(n().rawMarkdown[r(le)])),z(()=>T(J,r(le))),c(N,W)};$(U,N=>{r(B).length>0&&N(ne)})}c(j,we)},me=j=>{var B=W1(),le=ae(B),we=d(le),U=d(we),ne=d(U);Ae(ne,21,()=>n().data.columns??[],Ne,(J,Y)=>{var ye=V1(),Se=d(ye);z(te=>T(Se,`${r(Y)??""}${te??""}`),[()=>f(r(Y))]),he("click",ye,()=>u(r(Y))),c(J,ye)});var N=m(U);Ae(N,21,()=>r(O),Ne,(J,Y)=>{const ye=D(()=>_(r(Y),n().data.columns));var Se=q1();Ae(Se,21,()=>n().data.columns??[],Ne,(te,Oe,tt)=>{const ot=D(()=>r(Y)[r(Oe)]),Ge=D(()=>tt>0&&k(r(ot)));var rt=B1(),dt=d(rt);z((nt,st)=>{Ue(rt,1,nt),T(dt,st)},[()=>r(Ge)?b(r(ot))?"val-neg":"val-pos":"",()=>r(Ge)?x(r(ot)):r(ot)??""]),c(te,rt)}),z(()=>Ue(Se,1,xr(r(ye)?"row-key":""))),c(J,Se)});var W=m(we,2);{var H=J=>{var Y=H1(),ye=d(Y);z(()=>T(ye,`외 ${n().data.rows.length-a()}행 더 보기`)),he("click",Y,()=>{v(i,!0)}),c(J,Y)};$(W,J=>{!r(i)&&n().data.rows.length>a()&&J(H)})}var E=m(le,2);{var q=J=>{var Y=U1(),ye=d(Y);z(()=>T(ye,`단위: ${(n().meta.unit||"")??""} ${n().meta.scale?`(${n().meta.scale})`:""}`)),c(J,Y)};$(E,J=>{var Y,ye;((Y=n().meta)!=null&&Y.scale||(ye=n().meta)!=null&&ye.unit)&&J(q)})}c(j,B)},V=D(()=>{var j;return C(n())&&((j=n().data)==null?void 0:j.rows)}),ze=j=>{var B=Q1(),le=ae(B),we=d(le),U=d(we),ne=d(U);Ae(ne,21,()=>n().data.columns??[],Ne,(J,Y,ye)=>{var Se=K1();Ue(Se,1,`${ye===0?"col-sticky":""} cursor-pointer select-none hover:text-dl-text`);var te=d(Se);z(Oe=>T(te,`${r(Y)??""}${Oe??""}`),[()=>f(r(Y))]),he("click",Se,()=>u(r(Y))),c(J,Se)});var N=m(U);Ae(N,21,()=>r(O),Ne,(J,Y)=>{var ye=J1();Ae(ye,21,()=>n().data.columns??[],Ne,(Se,te,Oe)=>{const tt=D(()=>r(Y)[r(te)]),ot=D(()=>Oe>0&&k(r(tt)));var Ge=G1(),rt=d(Ge);z((dt,nt)=>{Ue(Ge,1,`${Oe===0?"col-sticky":""} ${dt??""}`),T(rt,nt)},[()=>r(ot)?b(r(tt))?"val-neg":"val-pos":"",()=>r(ot)?x(r(tt)):r(tt)??""]),c(Se,Ge)}),c(J,ye)});var W=m(we,2);{var H=J=>{var Y=Y1(),ye=d(Y);z(()=>T(ye,`외 ${n().data.rows.length-a()}행 더 보기`)),he("click",Y,()=>{v(i,!0)}),c(J,Y)};$(W,J=>{!r(i)&&n().data.rows.length>a()&&J(H)})}var E=m(le,2);{var q=J=>{var Y=X1(),ye=d(Y);z(()=>T(ye,`단위: ${(n().meta.unit||"")??""} ${n().meta.scale?`(${n().meta.scale})`:""}`)),c(J,Y)};$(E,J=>{var Y;(Y=n().meta)!=null&&Y.scale&&J(q)})}c(j,B)};$(X,j=>{var B;n().kind==="raw_markdown"&&n().rawMarkdown?j(G):r(V)?j(me,1):(B=n().data)!=null&&B.rows&&j(ze,2)})}c(L,S)};$(ee,L=>{n()&&L(fe)})}c(t,M),Ar()}Kr(["click"]);var Z1=h('<span class="flex items-center gap-1"><!> <span class="text-dl-accent"> </span> <span class="text-dl-text-dim/60"> </span></span>'),eg=h('<span class="flex items-center gap-1"><!> <span>변경 없음</span></span>'),tg=h('<span class="flex items-center gap-1 ml-auto"><span class="font-mono"> </span> <!> <span class="font-mono"> </span></span>'),rg=h('<div class="text-dl-success/80 truncate"> </div>'),ng=h('<div class="text-dl-primary-light/70 truncate"> </div>'),ag=h('<div class="text-[11px] leading-relaxed"><!> <!></div>'),og=h('<div class="flex flex-col gap-1.5 p-2.5 rounded-lg bg-dl-surface-card border border-dl-border/20"><div class="flex items-center gap-3 text-[11px] text-dl-text-dim"><span class="font-mono"> </span> <!> <!></div> <!></div>');function sg(t,e){Ir(e,!0);let n=je(e,"summary",3,null);var a=Ce(),o=ae(a);{var i=s=>{var l=og(),u=d(l),f=d(u),p=d(f),_=m(f,2);{var x=I=>{var O=Z1(),M=d(O);Ts(M,{size:11,class:"text-dl-accent"});var ee=m(M,2),fe=d(ee),L=m(ee,2),S=d(L);z(X=>{T(fe,`변경 ${n().changedCount??""}회`),T(S,`(${X??""}%)`)},[()=>(n().changeRate*100).toFixed(1)]),c(I,O)},b=I=>{var O=eg(),M=d(O);eu(M,{size:11}),c(I,O)};$(_,I=>{n().changedCount>0?I(x):I(b,-1)})}var k=m(_,2);{var C=I=>{var O=tg(),M=d(O),ee=d(M),fe=m(M,2);lh(fe,{size:10});var L=m(fe,2),S=d(L);z(()=>{T(ee,n().latestFrom),T(S,n().latestTo)}),c(I,O)};$(k,I=>{n().latestFrom&&n().latestTo&&I(C)})}var g=m(u,2);{var y=I=>{var O=ag(),M=d(O);Ae(M,17,()=>n().added.slice(0,2),Ne,(fe,L)=>{var S=rg(),X=d(S);z(()=>T(X,`+ ${r(L)??""}`)),c(fe,S)});var ee=m(M,2);Ae(ee,17,()=>n().removed.slice(0,2),Ne,(fe,L)=>{var S=ng(),X=d(S);z(()=>T(X,`- ${r(L)??""}`)),c(fe,S)}),c(I,O)};$(g,I=>{var O,M;(((O=n().added)==null?void 0:O.length)>0||((M=n().removed)==null?void 0:M.length)>0)&&I(y)})}z(()=>T(p,`${n().totalPeriods??""} periods`)),c(s,l)};$(o,s=>{n()&&s(i)})}c(t,a),Ar()}var ig=h("<option> </option>"),lg=h("<option> </option>"),dg=h('<button class="p-1 ml-1 text-dl-text-dim hover:text-dl-text"><!></button>'),cg=h('<span class="flex items-center gap-1 text-emerald-400"><!> <span> </span></span>'),ug=h('<span class="flex items-center gap-1 text-red-400"><!> <span> </span></span>'),fg=h('<span class="flex items-center gap-1 text-dl-text-dim"><!> <span> </span></span>'),vg=h('<div class="flex items-center gap-3 px-4 py-1.5 border-b border-dl-border/10 text-[10px]"><!> <!> <!></div>'),pg=h('<div class="flex items-center justify-center py-8 gap-2"><!> <span class="text-[12px] text-dl-text-dim">비교 로딩 중...</span></div>'),hg=h('<div class="text-[12px] text-red-400 py-4"> </div>'),mg=h('<mark class="bg-emerald-400/25 text-emerald-300 rounded-sm px-[1px]"> </mark>'),xg=h('<span class="text-dl-text/85"> </span>'),gg=h('<span class="text-dl-text/85"> </span>'),_g=h('<div class="pl-3 py-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-[13px] leading-[1.8] rounded-r"><span class="text-emerald-500/60 text-[10px] mr-1">+</span> <!></div>'),bg=h('<mark class="bg-red-400/25 text-red-300 line-through decoration-red-400/40 rounded-sm px-[1px]"> </mark>'),wg=h('<span class="text-dl-text/40"> </span>'),yg=h('<span class="text-dl-text/40 line-through decoration-red-400/30"> </span>'),kg=h('<div class="pl-3 py-1 border-l-2 border-red-400 bg-red-500/5 text-[13px] leading-[1.8] rounded-r"><span class="text-red-400/60 text-[10px] mr-1">-</span> <!></div>'),Cg=h('<p class="text-[13px] leading-[1.8] text-dl-text/70 py-0.5"> </p>'),$g=h('<div class="space-y-0.5"></div>'),Sg=h('<div class="text-[12px] text-dl-text-dim text-center py-4">비교할 기간을 선택하세요</div>'),Mg=h('<div class="rounded-xl border border-dl-border/20 bg-dl-surface-card overflow-hidden"><div class="flex items-center gap-2 px-4 py-2 border-b border-dl-border/15 bg-dl-bg-darker/50"><!> <span class="text-[12px] font-semibold text-dl-text">기간 비교</span> <div class="flex items-center gap-1 ml-auto"><select class="px-2 py-0.5 rounded bg-dl-bg-darker border border-dl-border/20 text-[11px] text-dl-text outline-none"></select> <span class="text-[11px] text-dl-text-dim">→</span> <select class="px-2 py-0.5 rounded bg-dl-bg-darker border border-dl-border/20 text-[11px] text-dl-text outline-none"></select> <!></div></div> <!> <div class="max-h-[60vh] overflow-y-auto px-4 py-3"><!></div></div>');function zg(t,e){Ir(e,!0);let n=je(e,"stockCode",3,null),a=je(e,"topic",3,null),o=je(e,"periods",19,()=>[]),i=je(e,"onClose",3,null),s=K(null),l=K(null),u=K(null),f=K(!1),p=K(null);gr(()=>{o().length>=2&&!r(s)&&!r(l)&&(v(l,o()[0],!0),v(s,o()[1],!0))});async function _(){if(!(!n()||!a()||!r(s)||!r(l))){v(f,!0),v(p,null);try{const j=await $c(n(),a(),r(s),r(l));v(u,j,!0)}catch(j){v(p,j.message,!0)}v(f,!1)}}gr(()=>{r(s)&&r(l)&&r(s)!==r(l)&&_()});function x(j){if(!j)return"";const B=String(j).match(/^(\d{4})(Q([1-4]))?$/);return B?B[3]?`'${B[1].slice(2)}.${B[3]}Q`:`'${B[1].slice(2)}`:j}let b=D(()=>{var we;if(!((we=r(u))!=null&&we.diff))return{added:0,removed:0,same:0};let j=0,B=0,le=0;for(const U of r(u).diff)U.kind==="added"?j++:U.kind==="removed"?B++:le++;return{added:j,removed:B,same:le}});var k=Mg(),C=d(k),g=d(C);Jc(g,{size:14,class:"text-dl-accent"});var y=m(g,4),I=d(y);Ae(I,21,o,Ne,(j,B)=>{var le=ig(),we=d(le),U={};z(ne=>{le.disabled=r(B)===r(l),T(we,ne),U!==(U=r(B))&&(le.value=(le.__value=r(B))??"")},[()=>x(r(B))]),c(j,le)});var O=m(I,4);Ae(O,21,o,Ne,(j,B)=>{var le=lg(),we=d(le),U={};z(ne=>{le.disabled=r(B)===r(s),T(we,ne),U!==(U=r(B))&&(le.value=(le.__value=r(B))??"")},[()=>x(r(B))]),c(j,le)});var M=m(O,2);{var ee=j=>{var B=dg(),le=d(B);Fa(le,{size:12}),he("click",B,function(...we){var U;(U=i())==null||U.apply(this,we)}),c(j,B)};$(M,j=>{i()&&j(ee)})}var fe=m(C,2);{var L=j=>{var B=vg(),le=d(B);{var we=H=>{var E=cg(),q=d(E);ji(q,{size:10});var J=m(q,2),Y=d(J);z(()=>T(Y,`추가 ${r(b).added??""}`)),c(H,E)};$(le,H=>{r(b).added>0&&H(we)})}var U=m(le,2);{var ne=H=>{var E=ug(),q=d(E);eu(q,{size:10});var J=m(q,2),Y=d(J);z(()=>T(Y,`삭제 ${r(b).removed??""}`)),c(H,E)};$(U,H=>{r(b).removed>0&&H(ne)})}var N=m(U,2);{var W=H=>{var E=fg(),q=d(E);fh(q,{size:10});var J=m(q,2),Y=d(J);z(()=>T(Y,`유지 ${r(b).same??""}`)),c(H,E)};$(N,H=>{r(b).same>0&&H(W)})}c(j,B)};$(fe,j=>{r(u)&&!r(f)&&j(L)})}var S=m(fe,2),X=d(S);{var G=j=>{var B=pg(),le=d(B);Ur(le,{size:14,class:"animate-spin text-dl-text-dim"}),c(j,B)},me=j=>{var B=hg(),le=d(B);z(()=>T(le,r(p))),c(j,B)},V=j=>{var B=$g();Ae(B,21,()=>r(u).diff,Ne,(le,we)=>{var U=Ce(),ne=ae(U);{var N=E=>{var q=_g(),J=m(d(q),2);{var Y=Se=>{var te=Ce(),Oe=ae(te);Ae(Oe,17,()=>r(we).parts,Ne,(tt,ot)=>{var Ge=Ce(),rt=ae(Ge);{var dt=st=>{var xt=mg(),St=d(xt);z(()=>T(St,r(ot).text)),c(st,xt)},nt=st=>{var xt=xg(),St=d(xt);z(()=>T(St,r(ot).text)),c(st,xt)};$(rt,st=>{r(ot).kind==="insert"?st(dt):r(ot).kind==="equal"&&st(nt,1)})}c(tt,Ge)}),c(Se,te)},ye=Se=>{var te=gg(),Oe=d(te);z(()=>T(Oe,r(we).text)),c(Se,te)};$(J,Se=>{r(we).parts?Se(Y):Se(ye,-1)})}c(E,q)},W=E=>{var q=kg(),J=m(d(q),2);{var Y=Se=>{var te=Ce(),Oe=ae(te);Ae(Oe,17,()=>r(we).parts,Ne,(tt,ot)=>{var Ge=Ce(),rt=ae(Ge);{var dt=st=>{var xt=bg(),St=d(xt);z(()=>T(St,r(ot).text)),c(st,xt)},nt=st=>{var xt=wg(),St=d(xt);z(()=>T(St,r(ot).text)),c(st,xt)};$(rt,st=>{r(ot).kind==="delete"?st(dt):r(ot).kind==="equal"&&st(nt,1)})}c(tt,Ge)}),c(Se,te)},ye=Se=>{var te=yg(),Oe=d(te);z(()=>T(Oe,r(we).text)),c(Se,te)};$(J,Se=>{r(we).parts?Se(Y):Se(ye,-1)})}c(E,q)},H=E=>{var q=Cg(),J=d(q);z(()=>T(J,r(we).text)),c(E,q)};$(ne,E=>{r(we).kind==="added"?E(N):r(we).kind==="removed"?E(W,1):E(H,-1)})}c(le,U)}),c(j,B)},ze=j=>{var B=Sg();c(j,B)};$(X,j=>{var B;r(f)?j(G):r(p)?j(me,1):(B=r(u))!=null&&B.diff?j(V,2):j(ze,-1)})}jl(I,()=>r(s),j=>v(s,j)),jl(O,()=>r(l),j=>v(l,j)),c(t,k),Ar()}Kr(["click"]);var Tg=h("<button><!></button>"),Ig=h("<button><!> <span>기간 비교</span></button>"),Ag=h("<button><!> <span>AI 요약</span></button>"),Eg=h('<div class="text-red-400/80"> </div>'),Ng=h('<span class="inline-block w-1.5 h-3 bg-dl-accent/60 animate-pulse ml-0.5"></span>'),Pg=h('<div class="whitespace-pre-wrap"> <!></div>'),Lg=h('<div class="px-3 py-2 rounded-lg bg-dl-accent/5 border border-dl-accent/15 text-[12px] text-dl-text-muted leading-relaxed"><!></div>'),Og=h('<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim"> </span>'),Dg=h('<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim"> </span>'),Rg=h('<span class="px-2 py-0.5 rounded-full border border-emerald-500/20 bg-emerald-500/8 text-emerald-400/80"> </span>'),jg=h('<span class="px-2 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/8 text-blue-400/80"> </span>'),Fg=h("<div> </div>"),Vg=h('<h4 class="text-[14px] font-semibold text-dl-text"> </h4>'),Bg=h('<div class="mb-2 mt-2"></div>'),qg=h('<span class="text-[10px] text-dl-text-dim font-mono"> </span>'),Hg=h('<span class="text-[10px] text-dl-text-dim"> </span>'),Ug=h('<span class="ml-0.5 text-emerald-400/50">*</span>'),Wg=h("<button> <!></button>"),Kg=h('<div class="flex flex-wrap gap-1 mb-2"></div>'),Gg=h('<div class="text-blue-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-blue-400/60 mt-1.5 shrink-0"></span> </div>'),Jg=h('<div class="text-emerald-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-emerald-400/50 mt-1.5 shrink-0"></span> </div>'),Yg=h('<div class="text-dl-text-dim/50 flex gap-1"><span class="w-1 h-1 rounded-full bg-red-400/40 mt-1.5 shrink-0"></span> </div>'),Xg=h('<div class="mb-3 px-3 py-2 rounded-lg border border-dl-border/15 bg-dl-surface-card/50 text-[11px] space-y-0.5 max-w-2xl"><div class="text-dl-text-dim font-medium"> </div> <!> <!> <!></div>'),Qg=h('<div class="mb-2 px-3 py-1.5 rounded-lg border border-dl-border/15 bg-dl-surface-card/30 text-[11px] text-dl-text-dim">이전 기간과 동일 — 변경 없음</div>'),Zg=h('<mark class="bg-emerald-400/25 text-emerald-300 rounded-sm px-[1px]"> </mark>'),e0=h('<span class="text-dl-text/85"> </span>'),t0=h('<span class="text-dl-text/85"> </span>'),r0=h('<div class="pl-3 py-1 mb-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-[14px] leading-[1.85] rounded-r"><span class="text-emerald-500/50 text-[10px] mr-1">+</span> <!></div>'),n0=h('<mark class="bg-red-400/25 text-red-300 line-through decoration-red-400/40 rounded-sm px-[1px]"> </mark>'),a0=h('<span class="text-dl-text/40"> </span>'),o0=h('<span class="text-dl-text/40 line-through decoration-red-400/30"> </span>'),s0=h('<div class="pl-3 py-1 mb-1 border-l-2 border-red-400 bg-red-500/5 text-[14px] leading-[1.85] rounded-r"><span class="text-red-400/60 text-[10px] mr-1">-</span> <!></div>'),i0=h('<p class="vw-para"> </p>'),l0=h('<div class="text-[10px] text-dl-text-dim/40 mb-1">글자 단위 비교 로딩 중...</div>'),d0=h('<p class="vw-para"> </p>'),c0=h('<div class="pl-3 py-1 mb-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-dl-text/85 text-[14px] leading-[1.85] rounded-r"><span class="text-emerald-500/50 text-[10px] mr-1">+</span> </div>'),u0=h('<div class="pl-3 py-1 mb-1 border-l-2 border-red-400 bg-red-500/5 text-dl-text/50 text-[14px] leading-[1.85] rounded-r line-through decoration-red-400/30"><span class="text-red-400/50 text-[10px] mr-1">-</span> </div>'),f0=h("<!> <!>",1),v0=h('<div class="flex flex-wrap items-center gap-1.5 mb-2"><span> </span> <!> <!></div> <!> <!> <!>  <div class="disclosure-text max-w-3xl"><!></div>',1),p0=h("<div><!> <!></div>"),h0=h("<button><!></button>"),m0=h('<button class="p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="테이블 복사"><!></button>'),x0=h('<div class="group relative"><div class="absolute top-1 right-1 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"><!> <!></div> <!></div>'),g0=h('<div class="h-16 flex items-center justify-center"><div class="text-[10px] text-dl-text-dim/40"> </div></div>'),_0=h('<div class="flex flex-wrap gap-1.5 text-[10px] max-w-4xl"><!> <!> <!> <!></div> <!> <!>',1),b0=h('<h3 class="text-[14px] font-semibold text-dl-text mt-4 mb-1"> </h3>'),w0=h('<div class="mb-1 opacity-0 group-hover:opacity-100 transition-opacity"><!></div>'),y0=h('<!> <div class="text-[10px] text-dl-text-dim mb-1 font-mono"> </div> <div class="disclosure-text"><!></div>',1),k0=h('<div class="group"><!></div>'),C0=h("<button><!></button>"),$0=h('<button class="p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="테이블 복사"><!></button>'),S0=h('<div class="group relative"><div class="absolute top-1 right-1 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"><!> <!></div> <!></div>'),M0=h('<div class="text-center py-12 text-[13px] text-dl-text-dim">이 topic에 표시할 데이터가 없습니다</div>'),z0=h('<div class="space-y-4"><div class="flex items-center gap-2"><h2 class="text-[16px] font-semibold text-dl-text flex-1"> </h2> <!> <!> <!></div> <!> <!> <!> <!> <!></div>'),T0=h('<button class="ask-ai-float"><span class="flex items-center gap-1"><!> AI에게 물어보기</span></button>'),I0=h("<!> <!>",1);function A0(t,e){Ir(e,!0);let n=je(e,"topicData",3,null),a=je(e,"diffSummary",3,null),o=je(e,"viewer",3,null),i=je(e,"onAskAI",3,null),s=je(e,"searchHighlight",3,null),l=K(Bt(new Map)),u=K(Bt(new Map)),f=K(null),p=K(Bt(new Map)),_=K(8),x=K(null);gr(()=>{var w;(w=n())!=null&&w.topic&&v(_,8)}),gr(()=>{if(!r(x))return;const w=new IntersectionObserver(F=>{var re,ie,ue,P,Z,$e,ve;(re=F[0])!=null&&re.isIntersecting&&v(_,Math.min(r(_)+10,((P=(ue=(ie=n())==null?void 0:ie.textDocument)==null?void 0:ue.entries)==null?void 0:P.length)||((ve=($e=(Z=n())==null?void 0:Z.textDocument)==null?void 0:$e.sections)==null?void 0:ve.length)||999),!0)},{rootMargin:"200px"});return w.observe(r(x)),()=>w.disconnect()});let b=K(Bt({show:!1,x:0,y:0,text:""})),k=K(!1),C=K(""),g=K(null),y=K(null);gr(()=>{var w,F,re;if((w=n())!=null&&w.topic){v(k,!1),v(g,null);const ie=(re=(F=o())==null?void 0:F.getTopicSummary)==null?void 0:re.call(F,n().topic);v(C,ie||"",!0),r(y)&&(r(y).abort(),v(y,null))}});function I(){var re,ie;if(!((re=o())!=null&&re.stockCode)||!((ie=n())!=null&&ie.topic))return;v(k,!0),v(C,""),v(g,null);const w=typeof localStorage<"u"?localStorage.getItem("dartlab-provider"):null,F=typeof localStorage<"u"?localStorage.getItem("dartlab-model"):null;v(y,Bv(o().stockCode,n().topic,{provider:w||void 0,model:F||void 0,onContext(){},onChunk(ue){v(C,r(C)+ue)},onDone(){var ue,P;v(k,!1),v(y,null),r(C)&&((P=(ue=o())==null?void 0:ue.setTopicSummary)==null||P.call(ue,n().topic,r(C)))},onError(ue){v(k,!1),v(y,null),v(g,ue,!0)}}),!0)}let O=D(()=>{var w,F,re;return((re=(w=o())==null?void 0:w.isBookmarked)==null?void 0:re.call(w,(F=n())==null?void 0:F.topic))??!1}),M=K(Bt(new Map)),ee=K(Bt(new Set));async function fe(w,F,re){var P,Z;if(!((P=o())!=null&&P.stockCode)||!((Z=n())!=null&&Z.topic)||!re||!F)return;const ie=`${w}:${F}`;if(r(M).has(ie)||r(ee).has(ie))return;v(ee,new Set([...r(ee),ie]),!0);try{const $e=await $c(o().stockCode,n().topic,re,F),ve=new Map(r(M));ve.set(ie,$e),v(M,ve,!0)}catch{}const ue=new Set(r(ee));ue.delete(ie),v(ee,ue,!0)}let L=K(!1);gr(()=>{var w;(w=n())!=null&&w.topic&&(v(L,!1),v(M,new Map,!0),v(ee,new Set,!0))}),gr(()=>{var F,re,ie,ue,P,Z,$e,ve,ke,Pe;const w=(re=(F=n())==null?void 0:F.textDocument)==null?void 0:re.sections;if(!(!w||!((ie=o())!=null&&ie.stockCode)||!((ue=n())!=null&&ue.topic)))for(const de of w){if(de.status!=="updated"||!de.timeline||de.timeline.length<2)continue;const Te=((Z=(P=de.timeline[0])==null?void 0:P.period)==null?void 0:Z.label)||ze(($e=de.timeline[0])==null?void 0:$e.period),Re=((ke=(ve=de.timeline[1])==null?void 0:ve.period)==null?void 0:ke.label)||ze((Pe=de.timeline[1])==null?void 0:Pe.period);Te&&Re&&fe(de.id,Te,Re)}});let S=D(()=>{var F,re,ie,ue,P,Z;if(!((ie=(re=(F=n())==null?void 0:F.textDocument)==null?void 0:re.sections)!=null&&ie.length))return[];const w=new Set;for(const $e of n().textDocument.sections)if($e.timeline)for(const ve of $e.timeline){const ke=((ue=ve.period)==null?void 0:ue.label)||((P=ve.period)!=null&&P.year&&((Z=ve.period)!=null&&Z.quarter)?`${ve.period.year}Q${ve.period.quarter}`:null);ke&&w.add(ke)}return[...w].sort().reverse()}),X=D(()=>{var w,F,re;return((re=(F=(w=n())==null?void 0:w.textDocument)==null?void 0:F.sections)==null?void 0:re.length)>0}),G=D(()=>{var w,F;return new Map((((F=(w=n())==null?void 0:w.textDocument)==null?void 0:F.sections)??[]).map(re=>[re.id,re]))}),me=D(()=>{var w;return new Map((((w=n())==null?void 0:w.blocks)??[]).map(F=>[F.block,F]))}),V=D(()=>{var w,F;return((F=(w=n())==null?void 0:w.textDocument)==null?void 0:F.entries)??[]});function ze(w){if(!w)return"";if(typeof w=="string"){const F=w.match(/^(\d{4})(Q([1-4]))?$/);return F?F[3]?`${F[1]}Q${F[3]}`:F[1]:w}return w.kind==="annual"?`${w.year}`:w.year&&w.quarter?`${w.year}Q${w.quarter}`:w.label||""}function j(w){return w==="updated"?"수정됨":w==="new"?"신규":w==="stale"?"과거유지":"유지"}function B(w){return w==="updated"?"bg-emerald-500/10 text-emerald-400/80 border-emerald-500/20":w==="new"?"bg-blue-500/10 text-blue-400/80 border-blue-500/20":w==="stale"?"bg-amber-500/10 text-amber-400/80 border-amber-500/20":"bg-dl-border/10 text-dl-text-dim border-dl-border/20"}function le(w){var re;const F=r(u).get(w.id);return F&&((re=w.views)!=null&&re[F])?w.views[F]:w.latest||null}function we(w,F){var ie,ue;const re=r(u).get(w.id);return re?re===F:((ue=(ie=w.latest)==null?void 0:ie.period)==null?void 0:ue.label)===F}function U(w){return r(u).has(w.id)}function ne(w,F,re){var ue;const ie=new Map(r(u));if(ie.get(w)===F)ie.delete(w);else if(ie.set(w,F),((ue=re==null?void 0:re.timeline)==null?void 0:ue.length)>1){const P=re.timeline.map(ve=>{var ke;return((ke=ve.period)==null?void 0:ke.label)||ze(ve.period)}),Z=P.indexOf(F),$e=Z>=0&&Z<P.length-1?P[Z+1]:null;$e&&fe(w,F,$e)}v(u,ie,!0)}function N(w){return w.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function W(w){return String(w||"").replace(/\u00a0/g," ").replace(/\s+/g," ").trim()}function H(w){return!w||w.length>88?!1:/^\[.+\]$/.test(w)||/^【.+】$/.test(w)||/^[IVX]+\.\s/.test(w)||/^\d+\.\s/.test(w)||/^[가-힣]\.\s/.test(w)||/^\(\d+\)\s/.test(w)||/^\([가-힣]\)\s/.test(w)||/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(w)}function E(w){return/^[가나다라마바사아자차카타파하]\.\s/.test(w)?1:/^\d+\.\s/.test(w)?2:/^\(\d+\)\s/.test(w)||/^\([가-힣]\)\s/.test(w)?3:/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(w)?4:/^\[.+\]$/.test(w)||/^【.+】$/.test(w)?1:2}function q(w){if(!w)return"";if(/^\|.+\|$/m.test(w))return Va(w);const F=w.split(`
`);let re="",ie=[];function ue(){ie.length!==0&&(re+=`<p class="vw-para">${N(ie.join(" "))}</p>`,ie=[])}for(const P of F){const Z=W(P);if(!Z){ue();continue}if(H(Z)){ue();const $e=E(Z);re+=`<div class="ko-h${$e}">${N(Z)}</div>`}else ie.push(Z)}return ue(),re}function J(w){var re;if(!((re=w==null?void 0:w.diff)!=null&&re.length))return null;const F=[];for(const ie of w.diff)for(const ue of ie.paragraphs||[])F.push({kind:ie.kind,text:W(ue)});return F}function Y(w){return r(l).get(w)??null}function ye(w,F){const re=new Map(r(l));re.set(w,F),v(l,re,!0)}function Se(w,F){var re,ie;return(ie=(re=w==null?void 0:w.data)==null?void 0:re.rows)!=null&&ie[0]?w.data.rows[0][F]??null:null}function te(w){var re,ie,ue;if(!((ie=(re=w==null?void 0:w.data)==null?void 0:re.rows)!=null&&ie[0]))return null;const F=w.data.rows[0];for(const P of((ue=w.meta)==null?void 0:ue.periods)??[])if(F[P])return{period:P,text:F[P]};return null}function Oe(w){var re,ie,ue;if(!((ie=(re=w==null?void 0:w.data)==null?void 0:re.rows)!=null&&ie[0]))return[];const F=w.data.rows[0];return(((ue=w.meta)==null?void 0:ue.periods)??[]).filter(P=>F[P]!=null)}function tt(w){return w.kind==="text"}function ot(w){return w.kind==="finance"||w.kind==="structured"||w.kind==="report"||w.kind==="raw_markdown"}function Ge(w){var F,re,ie,ue;return w.kind==="finance"&&((re=(F=w.data)==null?void 0:F.rows)==null?void 0:re.length)>0&&((ue=(ie=w.data)==null?void 0:ie.columns)==null?void 0:ue.length)>2}function rt(w){return L1(w)}function dt(w){const F=new Map(r(p));F.set(w,!F.get(w)),v(p,F,!0)}function nt(w,F){var ue,P;if(!((P=(ue=w==null?void 0:w.data)==null?void 0:ue.rows)!=null&&P.length))return;const re=w.data.columns||[],ie=[re.join("	")];for(const Z of w.data.rows)ie.push(re.map($e=>Z[$e]??"").join("	"));navigator.clipboard.writeText(ie.join(`
`)).then(()=>{v(f,F,!0),setTimeout(()=>{v(f,null)},2e3)})}function st(w){if(!i())return;const F=window.getSelection(),re=F==null?void 0:F.toString().trim();if(!re||re.length<5){v(b,{show:!1,x:0,y:0,text:""},!0);return}const ue=F.getRangeAt(0).getBoundingClientRect();v(b,{show:!0,x:ue.left+ue.width/2,y:ue.top-8,text:re.slice(0,500)},!0)}function xt(){r(b).text&&i()&&i()(r(b).text),v(b,{show:!1,x:0,y:0,text:""},!0)}function St(){r(b).show&&v(b,{show:!1,x:0,y:0,text:""},!0)}function Nt(w){if(!s()||!w)return w;const F=s().replace(/[.*+?^${}()|[\]\\]/g,"\\$&"),re=new RegExp(`(${F})`,"gi");return w.replace(re,'<mark class="bg-amber-400/30 text-dl-text rounded-sm px-0.5">$1</mark>')}gr(()=>{var w;s()&&((w=n())!=null&&w.topic)&&requestAnimationFrame(()=>{const F=document.querySelector(".disclosure-text mark");F&&F.scrollIntoView({block:"center",behavior:"smooth"})})});var lr=I0();xn("click",Kd,St);var R=ae(lr);{var pe=w=>{var F=z0(),re=d(F),ie=d(re),ue=d(ie),P=m(ie,2);{var Z=Ee=>{var Ie=Tg(),yt=d(Ie);{let Pt=D(()=>r(O)?"currentColor":"none");Fi(yt,{size:14,get fill(){return r(Pt)}})}z(()=>{Ue(Ie,1,`p-1 rounded transition-colors ${r(O)?"text-amber-400":"text-dl-text-dim/30 hover:text-amber-400/60"}`),ir(Ie,"title",r(O)?"북마크 해제":"북마크 추가")}),he("click",Ie,()=>o().toggleBookmark(n().topic)),c(Ee,Ie)};$(P,Ee=>{o()&&Ee(Z)})}var $e=m(P,2);{var ve=Ee=>{var Ie=Ig(),yt=d(Ie);Jc(yt,{size:10}),z(()=>Ue(Ie,1,`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors border
						${r(L)?"border-dl-accent/30 bg-dl-accent/10 text-dl-accent-light":"border-dl-border/20 text-dl-text-dim hover:text-dl-text hover:bg-white/5"}`)),he("click",Ie,()=>{v(L,!r(L))}),c(Ee,Ie)};$($e,Ee=>{r(S).length>=2&&Ee(ve)})}var ke=m($e,2);{var Pe=Ee=>{var Ie=Ag(),yt=d(Ie);{var Pt=At=>{Ur(At,{size:10,class:"animate-spin"})},Je=At=>{ru(At,{size:10})};$(yt,At=>{r(k)?At(Pt):At(Je,-1)})}z(()=>{Ue(Ie,1,`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors border
						${r(k)?"border-dl-accent/30 bg-dl-accent/10 text-dl-accent-light":"border-dl-border/20 text-dl-text-dim hover:text-dl-text hover:bg-white/5"}`),Ie.disabled=r(k)}),he("click",Ie,I),c(Ee,Ie)};$(ke,Ee=>{var Ie;(Ie=o())!=null&&Ie.stockCode&&Ee(Pe)})}var de=m(re,2);{var Te=Ee=>{var Ie=Lg(),yt=d(Ie);{var Pt=At=>{var qt=Eg(),$t=d(qt);z(()=>T($t,r(g))),c(At,qt)},Je=At=>{var qt=Pg(),$t=d(qt),Mt=m($t);{var ct=tr=>{var Mr=Ng();c(tr,Mr)};$(Mt,tr=>{r(k)&&tr(ct)})}z(()=>T($t,r(C))),c(At,qt)};$(yt,At=>{r(g)?At(Pt):At(Je,-1)})}c(Ee,Ie)};$(de,Ee=>{(r(C)||r(k)||r(g))&&Ee(Te)})}var Re=m(de,2);sg(Re,{get summary(){return a()}});var He=m(Re,2);{var _e=Ee=>{zg(Ee,{get stockCode(){return o().stockCode},get topic(){return n().topic},get periods(){return r(S)},onClose:()=>{v(L,!1)}})};$(He,Ee=>{var Ie;r(L)&&((Ie=o())!=null&&Ie.stockCode)&&Ee(_e)})}var et=m(He,2);{var Ct=Ee=>{const Ie=D(()=>n().textDocument);var yt=_0(),Pt=ae(yt),Je=d(Pt);{var At=_t=>{var Ht=Og(),zt=d(Ht);z(Lt=>T(zt,`최신 ${Lt??""}`),[()=>ze(r(Ie).latestPeriod)]),c(_t,Ht)};$(Je,_t=>{r(Ie).latestPeriod&&_t(At)})}var qt=m(Je,2);{var $t=_t=>{var Ht=Dg(),zt=d(Ht);z(()=>T(zt,`${r(Ie).sectionCount??""}개 섹션`)),c(_t,Ht)};$(qt,_t=>{r(Ie).sectionCount&&_t($t)})}var Mt=m(qt,2);{var ct=_t=>{var Ht=Rg(),zt=d(Ht);z(()=>T(zt,`${r(Ie).updatedCount??""}개 수정`)),c(_t,Ht)};$(Mt,_t=>{r(Ie).updatedCount>0&&_t(ct)})}var tr=m(Mt,2);{var Mr=_t=>{var Ht=jg(),zt=d(Ht);z(()=>T(zt,`${r(Ie).newCount??""}개 신규`)),c(_t,Ht)};$(tr,_t=>{r(Ie).newCount>0&&_t(Mr)})}var yr=m(Pt,2);Ae(yr,17,()=>r(V).slice(0,r(_)),_t=>_t.order,(_t,Ht)=>{var zt=Ce(),Lt=ae(zt);{var dr=bt=>{const Be=D(()=>r(G).get(r(Ht).sectionId));var rr=Ce(),Cr=ae(rr);{var it=Le=>{const Qe=D(()=>le(r(Be))),ut=D(()=>U(r(Be))),Ot=D(()=>J(r(Qe))),Tt=D(()=>r(Ot)&&r(Ot).length>0),gt=D(()=>{var Zt,hr,vr;return`${r(Be).id}:${r(u).get(r(Be).id)||((vr=(hr=(Zt=r(Be).timeline)==null?void 0:Zt[0])==null?void 0:hr.period)==null?void 0:vr.label)||""}`}),wt=D(()=>r(M).get(r(gt))),Ft=D(()=>r(ee).has(r(gt))),Kt=D(()=>{var Zt;return(r(Tt)||((Zt=r(wt))==null?void 0:Zt.diff))&&(r(ut)||r(Be).status==="updated")}),Xt=D(()=>r(ut)&&!r(Tt)&&r(Be).periodCount>1);var _r=p0(),Or=d(_r);{var $r=Zt=>{var hr=Bg();Ae(hr,21,()=>r(Be).headingPath,Ne,(vr,_n)=>{const an=D(()=>{var We;return(We=r(_n).text)==null?void 0:We.trim()});var Tn=Ce(),A=ae(Tn);{var ge=We=>{const Me=D(()=>r(_n).level||E(r(an)));var be=Ce(),De=ae(be);{var Ye=It=>{var Gt=Fg(),Ut=d(Gt);z(Wt=>{Ue(Gt,1,`ko-h${Wt??""}`),T(Ut,r(an))},[()=>r(Me)||E(r(an))]),c(It,Gt)},ft=D(()=>r(Me)>0||H(r(an))),vt=It=>{var Gt=Vg(),Ut=d(Gt);z(()=>T(Ut,r(an))),c(It,Gt)};$(De,It=>{r(ft)?It(Ye):It(vt,-1)})}c(We,be)};$(A,We=>{r(an)&&We(ge)})}c(vr,Tn)}),c(Zt,hr)};$(Or,Zt=>{var hr;((hr=r(Be).headingPath)==null?void 0:hr.length)>0&&Zt($r)})}var ar=m(Or,2);{var fr=Zt=>{},qr=Zt=>{var hr=v0(),vr=ae(hr),_n=d(vr),an=d(_n),Tn=m(_n,2);{var A=kt=>{var Q=qg(),xe=d(Q);z(()=>T(xe,r(Be).latestChange)),c(kt,Q)};$(Tn,kt=>{r(Be).latestChange&&kt(A)})}var ge=m(Tn,2);{var We=kt=>{var Q=Hg(),xe=d(Q);z(()=>T(xe,`${r(Be).periodCount??""}기간`)),c(kt,Q)};$(ge,kt=>{r(Be).periodCount>1&&kt(We)})}var Me=m(vr,2);{var be=kt=>{var Q=Kg();Ae(Q,21,()=>r(Be).timeline,Ne,(xe,Fe,qe,Ze)=>{const Rt=D(()=>{var er;return((er=r(Fe).period)==null?void 0:er.label)||ze(r(Fe).period)});var br=Wg(),or=d(br),Er=m(or);{var nr=er=>{var pr=Ug();c(er,pr)};$(Er,er=>{r(Fe).status==="updated"&&er(nr)})}z((er,pr)=>{Ue(br,1,`px-2 py-1 rounded-lg text-[10px] font-mono transition-colors border
											${er??""}`),T(or,`${pr??""} `)},[()=>we(r(Be),r(Rt))?"border-dl-accent/30 bg-dl-accent/8 text-dl-accent-light font-medium":r(Fe).status==="updated"?"border-emerald-500/15 text-emerald-400/60 hover:bg-emerald-500/5":"border-dl-border/15 text-dl-text-dim hover:bg-white/3",()=>ze(r(Fe).period)]),he("click",br,()=>ne(r(Be).id,r(Rt),r(Be))),c(xe,br)}),c(kt,Q)};$(Me,kt=>{var Q;((Q=r(Be).timeline)==null?void 0:Q.length)>=1&&r(Be).preview&&r(Be).preview.length>=30&&kt(be)})}var De=m(Me,2);{var Ye=kt=>{const Q=D(()=>r(Qe).digest);var xe=Xg(),Fe=d(xe),qe=d(Fe),Ze=m(Fe,2);Ae(Ze,17,()=>r(Q).items.filter(or=>or.kind==="numeric"),Ne,(or,Er)=>{var nr=Gg(),er=m(d(nr),1,!0);z(()=>T(er,r(Er).text)),c(or,nr)});var Rt=m(Ze,2);Ae(Rt,17,()=>r(Q).items.filter(or=>or.kind==="added"),Ne,(or,Er)=>{var nr=Jg(),er=m(d(nr),1,!0);z(()=>T(er,r(Er).text)),c(or,nr)});var br=m(Rt,2);Ae(br,17,()=>r(Q).items.filter(or=>or.kind==="removed"),Ne,(or,Er)=>{var nr=Yg(),er=m(d(nr),1,!0);z(()=>T(er,r(Er).text)),c(or,nr)}),z(()=>T(qe,`${r(Q).to??""} vs ${r(Q).from??""}`)),c(kt,xe)};$(De,kt=>{var Q,xe,Fe;((Fe=(xe=(Q=r(Qe))==null?void 0:Q.digest)==null?void 0:xe.items)==null?void 0:Fe.length)>0&&kt(Ye)})}var ft=m(De,2);{var vt=kt=>{var Q=Qg();c(kt,Q)};$(ft,kt=>{r(Xt)&&kt(vt)})}var It=m(ft,2),Gt=d(It);{var Ut=kt=>{var Q=Ce(),xe=ae(Q);Ae(xe,17,()=>r(wt).diff,Ne,(Fe,qe)=>{var Ze=Ce(),Rt=ae(Ze);{var br=nr=>{var er=r0(),pr=m(d(er),2);{var Nr=Pr=>{var Hr=Ce(),In=ae(Hr);Ae(In,17,()=>r(qe).parts,Ne,(Ha,jn)=>{var Ua=Ce(),Ro=ae(Ua);{var jo=on=>{var bn=Zg(),fa=d(bn);z(()=>T(fa,r(jn).text)),c(on,bn)},Fo=on=>{var bn=e0(),fa=d(bn);z(()=>T(fa,r(jn).text)),c(on,bn)};$(Ro,on=>{r(jn).kind==="insert"?on(jo):r(jn).kind==="equal"&&on(Fo,1)})}c(Ha,Ua)}),c(Pr,Hr)},rn=Pr=>{var Hr=t0(),In=d(Hr);z(()=>T(In,r(qe).text)),c(Pr,Hr)};$(pr,Pr=>{r(qe).parts?Pr(Nr):Pr(rn,-1)})}c(nr,er)},or=nr=>{var er=s0(),pr=m(d(er),2);{var Nr=Pr=>{var Hr=Ce(),In=ae(Hr);Ae(In,17,()=>r(qe).parts,Ne,(Ha,jn)=>{var Ua=Ce(),Ro=ae(Ua);{var jo=on=>{var bn=n0(),fa=d(bn);z(()=>T(fa,r(jn).text)),c(on,bn)},Fo=on=>{var bn=a0(),fa=d(bn);z(()=>T(fa,r(jn).text)),c(on,bn)};$(Ro,on=>{r(jn).kind==="delete"?on(jo):r(jn).kind==="equal"&&on(Fo,1)})}c(Ha,Ua)}),c(Pr,Hr)},rn=Pr=>{var Hr=o0(),In=d(Hr);z(()=>T(In,r(qe).text)),c(Pr,Hr)};$(pr,Pr=>{r(qe).parts?Pr(Nr):Pr(rn,-1)})}c(nr,er)},Er=nr=>{var er=i0(),pr=d(er);z(()=>T(pr,r(qe).text)),c(nr,er)};$(Rt,nr=>{r(qe).kind==="added"?nr(br):r(qe).kind==="removed"?nr(or,1):nr(Er,-1)})}c(Fe,Ze)}),c(kt,Q)},Wt=kt=>{var Q=f0(),xe=ae(Q);{var Fe=Ze=>{var Rt=l0();c(Ze,Rt)};$(xe,Ze=>{r(Ft)&&Ze(Fe)})}var qe=m(xe,2);Ae(qe,17,()=>r(Ot),Ne,(Ze,Rt)=>{var br=Ce(),or=ae(br);{var Er=pr=>{var Nr=d0(),rn=d(Nr);z(()=>T(rn,r(Rt).text)),c(pr,Nr)},nr=pr=>{var Nr=c0(),rn=m(d(Nr),1,!0);z(()=>T(rn,r(Rt).text)),c(pr,Nr)},er=pr=>{var Nr=u0(),rn=m(d(Nr),1,!0);z(()=>T(rn,r(Rt).text)),c(pr,Nr)};$(or,pr=>{r(Rt).kind==="same"?pr(Er):r(Rt).kind==="added"?pr(nr,1):r(Rt).kind==="removed"&&pr(er,2)})}c(Ze,br)}),c(kt,Q)},cr=kt=>{var Q=Ce(),xe=ae(Q);Kn(xe,()=>Nt(q(r(Qe).body))),c(kt,Q)};$(Gt,kt=>{var Q,xe;r(Kt)&&((Q=r(wt))!=null&&Q.diff)?kt(Ut):r(Kt)?kt(Wt,1):(xe=r(Qe))!=null&&xe.body&&kt(cr,2)})}z((kt,Q)=>{Ue(_n,1,`px-1.5 py-0.5 rounded text-[9px] font-medium border ${kt??""}`),T(an,Q)},[()=>B(r(Be).status),()=>j(r(Be).status)]),he("mouseup",It,st),c(Zt,hr)};$(ar,Zt=>{!r(Be).preview||r(Be).preview.length<30?Zt(fr):Zt(qr,-1)})}z(()=>Ue(_r,1,`max-w-4xl pt-2 pb-6 border-b border-dl-border/8 last:border-b-0 ${r(Be).status==="stale"?"border-l-2 border-l-amber-400/40 pl-3":""}`)),c(Le,_r)};$(Cr,Le=>{r(Be)&&Le(it)})}c(bt,rr)},ur=bt=>{const Be=D(()=>r(me).get(r(Ht).blockRef));var rr=Ce(),Cr=ae(rr);{var it=Le=>{const Qe=D(()=>Ge(r(Be))),ut=D(()=>r(Qe)&&r(p).get(r(Be).block)),Ot=D(()=>r(ut)?rt(r(Be)):null);var Tt=x0(),gt=d(Tt),wt=d(gt);{var Ft=ar=>{var fr=h0(),qr=d(fr);{var Zt=vr=>{Vi(vr,{size:12})},hr=vr=>{Rs(vr,{size:12})};$(qr,vr=>{r(ut)?vr(Zt):vr(hr,-1)})}z(()=>{Ue(fr,1,`p-1 rounded transition-colors ${r(ut)?"text-dl-accent-light bg-dl-accent/10":"text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5"}`),ir(fr,"title",r(ut)?"표로 보기":"차트로 보기")}),he("click",fr,()=>dt(r(Be).block)),c(ar,fr)};$(wt,ar=>{r(Qe)&&ar(Ft)})}var Kt=m(wt,2);{var Xt=ar=>{var fr=m0(),qr=d(fr);{var Zt=vr=>{Ri(vr,{size:12,class:"text-dl-success"})},hr=vr=>{od(vr,{size:12})};$(qr,vr=>{r(f)===r(Be).block?vr(Zt):vr(hr,-1)})}he("click",fr,()=>nt(r(Be),r(Be).block)),c(ar,fr)};$(Kt,ar=>{var fr,qr;((qr=(fr=r(Be).data)==null?void 0:fr.rows)==null?void 0:qr.length)>0&&ar(Xt)})}var _r=m(gt,2);{var Or=ar=>{var fr=Ce(),qr=ae(fr);Ti(qr,()=>Bi(()=>import("./ChartRenderer-CMF5oGVz.js"),__vite__mapDeps([0,1])),null,(Zt,hr)=>{var vr=D(()=>{var{default:A}=r(hr);return{ChartRenderer:A}}),_n=D(()=>r(vr).ChartRenderer),an=Ce(),Tn=ae(an);Ao(Tn,()=>r(_n),(A,ge)=>{ge(A,{get spec(){return r(Ot)}})}),c(Zt,an)}),c(ar,fr)},$r=ar=>{ud(ar,{get block(){return r(Be)}})};$(_r,ar=>{r(ut)&&r(Ot)?ar(Or):ar($r,-1)})}c(Le,Tt)};$(Cr,Le=>{r(Be)&&Le(it)})}c(bt,rr)};$(Lt,bt=>{r(Ht).kind==="section"?bt(dr):r(Ht).kind==="block_ref"&&bt(ur,1)})}c(_t,zt)});var Br=m(yr,2);{var zr=_t=>{var Ht=g0(),zt=d(Ht),Lt=d(zt);Jn(Ht,dr=>v(x,dr),()=>r(x)),z(()=>T(Lt,`더 불러오는 중... (${r(_)??""}/${r(V).length??""})`)),c(_t,Ht)};$(Br,_t=>{r(_)<r(V).length&&_t(zr)})}c(Ee,yt)},at=Ee=>{var Ie=Ce(),yt=ae(Ie);Ae(yt,19,()=>n().blocks,Pt=>Pt.block,(Pt,Je,At)=>{var qt=Ce(),$t=ae(qt);{var Mt=yr=>{const Br=D(()=>Y(r(At))),zr=D(()=>te(r(Je))),_t=D(()=>Oe(r(Je))),Ht=D(()=>{var bt;return r(Br)||((bt=r(zr))==null?void 0:bt.period)}),zt=D(()=>{var bt;return r(Ht)?Se(r(Je),r(Ht)):(bt=r(zr))==null?void 0:bt.text});var Lt=Ce(),dr=ae(Lt);{var ur=bt=>{var Be=k0(),rr=d(Be);{var Cr=Le=>{var Qe=b0(),ut=d(Qe);z(()=>T(ut,r(zt))),c(Le,Qe)},it=Le=>{var Qe=y0(),ut=ae(Qe);{var Ot=Kt=>{var Xt=w0(),_r=d(Xt);ou(_r,{get periods(){return r(_t)},get selected(){return r(Ht)},onSelect:Or=>ye(r(At),Or)}),c(Kt,Xt)};$(ut,Kt=>{r(_t).length>1&&Kt(Ot)})}var Tt=m(ut,2),gt=d(Tt),wt=m(Tt,2),Ft=d(wt);Kn(Ft,()=>Nt(q(r(zt)))),z(()=>T(gt,r(Ht))),he("mouseup",wt,st),c(Le,Qe)};$(rr,Le=>{r(Je).textType==="heading"?Le(Cr):Le(it,-1)})}c(bt,Be)};$(dr,bt=>{r(zt)&&bt(ur)})}c(yr,Lt)},ct=D(()=>tt(r(Je))),tr=yr=>{const Br=D(()=>Ge(r(Je))),zr=D(()=>r(Br)&&r(p).get(r(Je).block)),_t=D(()=>r(zr)?rt(r(Je)):null);var Ht=S0(),zt=d(Ht),Lt=d(zt);{var dr=it=>{var Le=C0(),Qe=d(Le);{var ut=Tt=>{Vi(Tt,{size:12})},Ot=Tt=>{Rs(Tt,{size:12})};$(Qe,Tt=>{r(zr)?Tt(ut):Tt(Ot,-1)})}z(()=>{Ue(Le,1,`p-1 rounded transition-colors ${r(zr)?"text-dl-accent-light bg-dl-accent/10":"text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5"}`),ir(Le,"title",r(zr)?"표로 보기":"차트로 보기")}),he("click",Le,()=>dt(r(Je).block)),c(it,Le)};$(Lt,it=>{r(Br)&&it(dr)})}var ur=m(Lt,2);{var bt=it=>{var Le=$0(),Qe=d(Le);{var ut=Tt=>{Ri(Tt,{size:12,class:"text-dl-success"})},Ot=Tt=>{od(Tt,{size:12})};$(Qe,Tt=>{r(f)===r(Je).block?Tt(ut):Tt(Ot,-1)})}he("click",Le,()=>nt(r(Je),r(Je).block)),c(it,Le)};$(ur,it=>{var Le,Qe;((Qe=(Le=r(Je).data)==null?void 0:Le.rows)==null?void 0:Qe.length)>0&&it(bt)})}var Be=m(zt,2);{var rr=it=>{var Le=Ce(),Qe=ae(Le);Ti(Qe,()=>Bi(()=>import("./ChartRenderer-CMF5oGVz.js"),__vite__mapDeps([0,1])),null,(ut,Ot)=>{var Tt=D(()=>{var{default:Kt}=r(Ot);return{ChartRenderer:Kt}}),gt=D(()=>r(Tt).ChartRenderer),wt=Ce(),Ft=ae(wt);Ao(Ft,()=>r(gt),(Kt,Xt)=>{Xt(Kt,{get spec(){return r(_t)}})}),c(ut,wt)}),c(it,Le)},Cr=it=>{ud(it,{get block(){return r(Je)}})};$(Be,it=>{r(zr)&&r(_t)?it(rr):it(Cr,-1)})}c(yr,Ht)},Mr=D(()=>ot(r(Je)));$($t,yr=>{r(ct)?yr(Mt):r(Mr)&&yr(tr,1)})}c(Pt,qt)}),c(Ee,Ie)};$(et,Ee=>{r(X)?Ee(Ct):Ee(at,-1)})}var Dt=m(et,2);{var Ve=Ee=>{var Ie=M0();c(Ee,Ie)};$(Dt,Ee=>{var Ie;((Ie=n().blocks)==null?void 0:Ie.length)===0&&!r(X)&&Ee(Ve)})}z(()=>T(ue,n().topicLabel||"")),c(w,F)};$(R,w=>{n()&&w(pe)})}var oe=m(R,2);{var ce=w=>{var F=T0(),re=d(F),ie=d(re);js(ie,{size:10}),z(()=>Eo(F,`left: ${r(b).x??""}px; top: ${r(b).y??""}px; transform: translate(-50%, -100%)`)),he("click",F,xt),c(w,F)};$(oe,w=>{r(b).show&&w(ce)})}c(t,lr),Ar()}Kr(["click","mouseup"]);var E0=h("<div> </div>"),N0=h('<div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20"><!> <div class="text-[11px] text-red-400/90 space-y-0.5"></div></div>'),P0=h("<div> </div>"),L0=h('<div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-500/8 border border-amber-500/20"><!> <div class="text-[11px] text-amber-400/80 space-y-0.5"></div></div>'),O0=h('<button><!> <span class="text-[10px] opacity-80"> </span> <span class="text-[14px] font-bold"> </span></button>'),D0=h('<div class="flex items-start gap-1.5"><span class="w-1 h-1 rounded-full bg-dl-text-dim/40 mt-1.5 flex-shrink-0"></span> <span> </span></div>'),R0=h('<div class="text-[11px] text-dl-text-muted space-y-0.5"></div>'),j0=h("<div><!> <span> </span></div>"),F0=h('<div class="text-[11px] space-y-0.5"></div>'),V0=h("<div><!> <span> </span></div>"),B0=h('<div class="text-[11px] space-y-0.5"></div>'),q0=h('<button class="text-[10px] px-1.5 py-0.5 rounded bg-dl-accent/8 text-dl-accent-light border border-dl-accent/20 hover:bg-dl-accent/15 transition-colors"> </button>'),H0=h('<div class="flex flex-wrap gap-1 pt-1 border-t border-dl-border/10"><span class="text-[10px] text-dl-text-dim mr-1">원문 보기:</span> <!></div>'),U0=h('<div class="px-3 py-2 rounded-lg bg-dl-surface-card border border-dl-border/20 space-y-2 animate-fadeIn"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><span> </span> <span class="text-[12px] font-medium text-dl-text"> </span> <span class="text-[11px] text-dl-text-muted"> </span></div> <button class="p-0.5 text-dl-text-dim hover:text-dl-text"><!></button></div> <!> <!> <!> <!></div>'),W0=h('<div class="text-[10px] text-dl-text-dim px-1"> </div>'),K0=h('<div class="space-y-2"><!> <!> <div class="grid grid-cols-4 sm:grid-cols-7 gap-1.5"></div> <!> <!> <!></div>');function G0(t,e){Ir(e,!0);let n=je(e,"data",3,null),a=je(e,"loading",3,!1),o=je(e,"corpName",3,""),i=je(e,"onNavigateTopic",3,null),s=je(e,"toc",3,null),l=K(null);const u={performance:{label:"실적",icon:Ts},profitability:{label:"수익성",icon:ru},health:{label:"건전성",icon:wh},cashflow:{label:"현금흐름",icon:$h},governance:{label:"지배구조",icon:nu},risk:{label:"리스크",icon:ss},opportunity:{label:"기회",icon:Ts}},f={performance:["salesOrder","businessOverview"],profitability:["IS","CIS","ratios"],health:["BS","contingentLiability","corporateBond"],cashflow:["CF","ratios"],governance:["majorShareholder","audit","dividend"],risk:["contingentLiability","riskFactors","corporateBond"],opportunity:["businessOverview","investmentOverview"]};function p(S){return S==="A"?"bg-emerald-500/15 text-emerald-400 border-emerald-500/30":S==="B"?"bg-blue-500/15 text-blue-400 border-blue-500/30":S==="C"?"bg-amber-500/15 text-amber-400 border-amber-500/30":S==="D"?"bg-orange-500/15 text-orange-400 border-orange-500/30":S==="F"?"bg-red-500/15 text-red-400 border-red-500/30":"bg-dl-border/10 text-dl-text-dim border-dl-border/20"}function _(S){return S==="A"?"bg-emerald-500 text-white":S==="B"?"bg-blue-500 text-white":S==="C"?"bg-amber-500 text-white":S==="D"?"bg-orange-500 text-white":S==="F"?"bg-red-500 text-white":"bg-dl-border text-dl-text-dim"}function x(S){return S==="danger"?"text-red-400":S==="warning"?"text-amber-400":"text-dl-text-dim"}function b(S){return S==="strong"?"text-emerald-400":"text-blue-400"}function k(S){v(l,r(l)===S?null:S,!0)}let C=D(()=>{var X;if(!((X=s())!=null&&X.chapters))return null;const S=new Set;for(const G of s().chapters)for(const me of G.topics)S.add(me.topic);return S}),g=D(()=>{var S;return(((S=n())==null?void 0:S.anomalies)??[]).filter(X=>X.severity==="danger")}),y=D(()=>{var S;return(((S=n())==null?void 0:S.anomalies)??[]).filter(X=>X.severity==="warning")}),I=D(()=>{var S;return(S=n())!=null&&S.areas?Object.keys(u).filter(X=>n().areas[X]):[]}),O=D(()=>{var X;if(!((X=n())!=null&&X.areas)||r(I).length<3)return null;const S={};for(const G of r(I))S[G]={grade:n().areas[G].grade};return O1(S,o())});var M=Ce(),ee=ae(M);{var fe=S=>{},L=S=>{var X=K0(),G=d(X);{var me=W=>{var H=N0(),E=d(H);Ja(E,{size:14,class:"text-red-400 mt-0.5 flex-shrink-0"});var q=m(E,2);Ae(q,21,()=>r(g),Ne,(J,Y)=>{var ye=E0(),Se=d(ye);z(()=>T(Se,r(Y).text)),c(J,ye)}),c(W,H)};$(G,W=>{r(g).length>0&&W(me)})}var V=m(G,2);{var ze=W=>{var H=L0(),E=d(H);ss(E,{size:14,class:"text-amber-400 mt-0.5 flex-shrink-0"});var q=m(E,2);Ae(q,21,()=>r(y),Ne,(J,Y)=>{var ye=P0(),Se=d(ye);z(()=>T(Se,r(Y).text)),c(J,ye)}),c(W,H)};$(V,W=>{r(y).length>0&&W(ze)})}var j=m(V,2);Ae(j,21,()=>r(I),Ne,(W,H)=>{const E=D(()=>u[r(H)]),q=D(()=>n().areas[r(H)]),J=D(()=>r(E).icon);var Y=O0(),ye=d(Y);Ao(ye,()=>r(J),(ot,Ge)=>{Ge(ot,{size:13,class:"opacity-70"})});var Se=m(ye,2),te=d(Se),Oe=m(Se,2),tt=d(Oe);z(ot=>{Ue(Y,1,`flex flex-col items-center gap-1 px-2 py-2 rounded-lg border transition-colors cursor-pointer ${ot??""} ${r(l)===r(H)?"ring-1 ring-dl-accent/40":"hover:brightness-110"}`),T(te,r(E).label),T(tt,r(q).grade)},[()=>p(r(q).grade)]),he("click",Y,()=>k(r(H))),c(W,Y)});var B=m(j,2);{var le=W=>{var H=Ce(),E=ae(H);Ti(E,()=>Bi(()=>import("./ChartRenderer-CMF5oGVz.js"),__vite__mapDeps([0,1])),null,(q,J)=>{var Y=D(()=>{var{default:Oe}=r(J);return{ChartRenderer:Oe}}),ye=D(()=>r(Y).ChartRenderer),Se=Ce(),te=ae(Se);Ao(te,()=>r(ye),(Oe,tt)=>{tt(Oe,{get spec(){return r(O)},class:"max-w-xs mx-auto"})}),c(q,Se)}),c(W,H)};$(B,W=>{r(O)&&W(le)})}var we=m(B,2);{var U=W=>{const H=D(()=>n().areas[r(l)]),E=D(()=>u[r(l)]),q=D(()=>(f[r(l)]||[]).filter(oe=>!r(C)||r(C).has(oe)));var J=U0(),Y=d(J),ye=d(Y),Se=d(ye),te=d(Se),Oe=m(Se,2),tt=d(Oe),ot=m(Oe,2),Ge=d(ot),rt=m(ye,2),dt=d(rt);Yc(dt,{size:14});var nt=m(Y,2);{var st=oe=>{var ce=R0();Ae(ce,21,()=>r(H).details,Ne,(w,F)=>{var re=D0(),ie=m(d(re),2),ue=d(ie);z(()=>T(ue,r(F))),c(w,re)}),c(oe,ce)};$(nt,oe=>{var ce;((ce=r(H).details)==null?void 0:ce.length)>0&&oe(st)})}var xt=m(nt,2);{var St=oe=>{var ce=F0();Ae(ce,21,()=>r(H).risks,Ne,(w,F)=>{var re=j0(),ie=d(re);ss(ie,{size:10,class:"mt-0.5 flex-shrink-0"});var ue=m(ie,2),P=d(ue);z(Z=>{Ue(re,1,`flex items-start gap-1.5 ${Z??""}`),T(P,r(F).text)},[()=>x(r(F).level)]),c(w,re)}),c(oe,ce)};$(xt,oe=>{var ce;((ce=r(H).risks)==null?void 0:ce.length)>0&&oe(St)})}var Nt=m(xt,2);{var lr=oe=>{var ce=B0();Ae(ce,21,()=>r(H).opportunities,Ne,(w,F)=>{var re=V0(),ie=d(re);Ts(ie,{size:10,class:"mt-0.5 flex-shrink-0"});var ue=m(ie,2),P=d(ue);z(Z=>{Ue(re,1,`flex items-start gap-1.5 ${Z??""}`),T(P,r(F).text)},[()=>b(r(F).level)]),c(w,re)}),c(oe,ce)};$(Nt,oe=>{var ce;((ce=r(H).opportunities)==null?void 0:ce.length)>0&&oe(lr)})}var R=m(Nt,2);{var pe=oe=>{var ce=H0(),w=m(d(ce),2);Ae(w,17,()=>r(q),Ne,(F,re)=>{var ie=q0(),ue=d(ie);z(()=>T(ue,r(re))),he("click",ie,()=>i()(r(re))),c(F,ie)}),c(oe,ce)};$(R,oe=>{i()&&r(q).length>0&&oe(pe)})}z(oe=>{Ue(Se,1,`px-1.5 py-0.5 rounded text-[10px] font-bold ${oe??""}`),T(te,r(H).grade),T(tt,r(E).label),T(Ge,`— ${r(H).summary??""}`)},[()=>_(r(H).grade)]),he("click",rt,()=>{v(l,null)}),c(W,J)};$(we,W=>{r(l)&&n().areas[r(l)]&&W(U)})}var ne=m(we,2);{var N=W=>{var H=W0(),E=d(H);z(()=>T(E,n().profile)),c(W,H)};$(ne,W=>{n().profile&&W(N)})}c(S,X)};$(ee,S=>{a()?S(fe):n()&&S(L,1)})}c(t,M),Ar()}Kr(["click"]);function J0(t,e){var n,a=1;t==null&&(t=0),e==null&&(e=0);function o(){var i,s=n.length,l,u=0,f=0;for(i=0;i<s;++i)l=n[i],u+=l.x,f+=l.y;for(u=(u/s-t)*a,f=(f/s-e)*a,i=0;i<s;++i)l=n[i],l.x-=u,l.y-=f}return o.initialize=function(i){n=i},o.x=function(i){return arguments.length?(t=+i,o):t},o.y=function(i){return arguments.length?(e=+i,o):e},o.strength=function(i){return arguments.length?(a=+i,o):a},o}function Y0(t){const e=+this._x.call(null,t),n=+this._y.call(null,t);return su(this.cover(e,n),e,n,t)}function su(t,e,n,a){if(isNaN(e)||isNaN(n))return t;var o,i=t._root,s={data:a},l=t._x0,u=t._y0,f=t._x1,p=t._y1,_,x,b,k,C,g,y,I;if(!i)return t._root=s,t;for(;i.length;)if((C=e>=(_=(l+f)/2))?l=_:f=_,(g=n>=(x=(u+p)/2))?u=x:p=x,o=i,!(i=i[y=g<<1|C]))return o[y]=s,t;if(b=+t._x.call(null,i.data),k=+t._y.call(null,i.data),e===b&&n===k)return s.next=i,o?o[y]=s:t._root=s,t;do o=o?o[y]=new Array(4):t._root=new Array(4),(C=e>=(_=(l+f)/2))?l=_:f=_,(g=n>=(x=(u+p)/2))?u=x:p=x;while((y=g<<1|C)===(I=(k>=x)<<1|b>=_));return o[I]=i,o[y]=s,t}function X0(t){var e,n,a=t.length,o,i,s=new Array(a),l=new Array(a),u=1/0,f=1/0,p=-1/0,_=-1/0;for(n=0;n<a;++n)isNaN(o=+this._x.call(null,e=t[n]))||isNaN(i=+this._y.call(null,e))||(s[n]=o,l[n]=i,o<u&&(u=o),o>p&&(p=o),i<f&&(f=i),i>_&&(_=i));if(u>p||f>_)return this;for(this.cover(u,f).cover(p,_),n=0;n<a;++n)su(this,s[n],l[n],t[n]);return this}function Q0(t,e){if(isNaN(t=+t)||isNaN(e=+e))return this;var n=this._x0,a=this._y0,o=this._x1,i=this._y1;if(isNaN(n))o=(n=Math.floor(t))+1,i=(a=Math.floor(e))+1;else{for(var s=o-n||1,l=this._root,u,f;n>t||t>=o||a>e||e>=i;)switch(f=(e<a)<<1|t<n,u=new Array(4),u[f]=l,l=u,s*=2,f){case 0:o=n+s,i=a+s;break;case 1:n=o-s,i=a+s;break;case 2:o=n+s,a=i-s;break;case 3:n=o-s,a=i-s;break}this._root&&this._root.length&&(this._root=l)}return this._x0=n,this._y0=a,this._x1=o,this._y1=i,this}function Z0(){var t=[];return this.visit(function(e){if(!e.length)do t.push(e.data);while(e=e.next)}),t}function e_(t){return arguments.length?this.cover(+t[0][0],+t[0][1]).cover(+t[1][0],+t[1][1]):isNaN(this._x0)?void 0:[[this._x0,this._y0],[this._x1,this._y1]]}function dn(t,e,n,a,o){this.node=t,this.x0=e,this.y0=n,this.x1=a,this.y1=o}function t_(t,e,n){var a,o=this._x0,i=this._y0,s,l,u,f,p=this._x1,_=this._y1,x=[],b=this._root,k,C;for(b&&x.push(new dn(b,o,i,p,_)),n==null?n=1/0:(o=t-n,i=e-n,p=t+n,_=e+n,n*=n);k=x.pop();)if(!(!(b=k.node)||(s=k.x0)>p||(l=k.y0)>_||(u=k.x1)<o||(f=k.y1)<i))if(b.length){var g=(s+u)/2,y=(l+f)/2;x.push(new dn(b[3],g,y,u,f),new dn(b[2],s,y,g,f),new dn(b[1],g,l,u,y),new dn(b[0],s,l,g,y)),(C=(e>=y)<<1|t>=g)&&(k=x[x.length-1],x[x.length-1]=x[x.length-1-C],x[x.length-1-C]=k)}else{var I=t-+this._x.call(null,b.data),O=e-+this._y.call(null,b.data),M=I*I+O*O;if(M<n){var ee=Math.sqrt(n=M);o=t-ee,i=e-ee,p=t+ee,_=e+ee,a=b.data}}return a}function r_(t){if(isNaN(p=+this._x.call(null,t))||isNaN(_=+this._y.call(null,t)))return this;var e,n=this._root,a,o,i,s=this._x0,l=this._y0,u=this._x1,f=this._y1,p,_,x,b,k,C,g,y;if(!n)return this;if(n.length)for(;;){if((k=p>=(x=(s+u)/2))?s=x:u=x,(C=_>=(b=(l+f)/2))?l=b:f=b,e=n,!(n=n[g=C<<1|k]))return this;if(!n.length)break;(e[g+1&3]||e[g+2&3]||e[g+3&3])&&(a=e,y=g)}for(;n.data!==t;)if(o=n,!(n=n.next))return this;return(i=n.next)&&delete n.next,o?(i?o.next=i:delete o.next,this):e?(i?e[g]=i:delete e[g],(n=e[0]||e[1]||e[2]||e[3])&&n===(e[3]||e[2]||e[1]||e[0])&&!n.length&&(a?a[y]=n:this._root=n),this):(this._root=i,this)}function n_(t){for(var e=0,n=t.length;e<n;++e)this.remove(t[e]);return this}function a_(){return this._root}function o_(){var t=0;return this.visit(function(e){if(!e.length)do++t;while(e=e.next)}),t}function s_(t){var e=[],n,a=this._root,o,i,s,l,u;for(a&&e.push(new dn(a,this._x0,this._y0,this._x1,this._y1));n=e.pop();)if(!t(a=n.node,i=n.x0,s=n.y0,l=n.x1,u=n.y1)&&a.length){var f=(i+l)/2,p=(s+u)/2;(o=a[3])&&e.push(new dn(o,f,p,l,u)),(o=a[2])&&e.push(new dn(o,i,p,f,u)),(o=a[1])&&e.push(new dn(o,f,s,l,p)),(o=a[0])&&e.push(new dn(o,i,s,f,p))}return this}function i_(t){var e=[],n=[],a;for(this._root&&e.push(new dn(this._root,this._x0,this._y0,this._x1,this._y1));a=e.pop();){var o=a.node;if(o.length){var i,s=a.x0,l=a.y0,u=a.x1,f=a.y1,p=(s+u)/2,_=(l+f)/2;(i=o[0])&&e.push(new dn(i,s,l,p,_)),(i=o[1])&&e.push(new dn(i,p,l,u,_)),(i=o[2])&&e.push(new dn(i,s,_,p,f)),(i=o[3])&&e.push(new dn(i,p,_,u,f))}n.push(a)}for(;a=n.pop();)t(a.node,a.x0,a.y0,a.x1,a.y1);return this}function l_(t){return t[0]}function d_(t){return arguments.length?(this._x=t,this):this._x}function c_(t){return t[1]}function u_(t){return arguments.length?(this._y=t,this):this._y}function fl(t,e,n){var a=new vl(e??l_,n??c_,NaN,NaN,NaN,NaN);return t==null?a:a.addAll(t)}function vl(t,e,n,a,o,i){this._x=t,this._y=e,this._x0=n,this._y0=a,this._x1=o,this._y1=i,this._root=void 0}function fd(t){for(var e={data:t.data},n=e;t=t.next;)n=n.next={data:t.data};return e}var un=fl.prototype=vl.prototype;un.copy=function(){var t=new vl(this._x,this._y,this._x0,this._y0,this._x1,this._y1),e=this._root,n,a;if(!e)return t;if(!e.length)return t._root=fd(e),t;for(n=[{source:e,target:t._root=new Array(4)}];e=n.pop();)for(var o=0;o<4;++o)(a=e.source[o])&&(a.length?n.push({source:a,target:e.target[o]=new Array(4)}):e.target[o]=fd(a));return t};un.add=Y0;un.addAll=X0;un.cover=Q0;un.data=Z0;un.extent=e_;un.find=t_;un.remove=r_;un.removeAll=n_;un.root=a_;un.size=o_;un.visit=s_;un.visitAfter=i_;un.x=d_;un.y=u_;function so(t){return function(){return t}}function Pa(t){return(t()-.5)*1e-6}function f_(t){return t.x+t.vx}function v_(t){return t.y+t.vy}function p_(t){var e,n,a,o=1,i=1;typeof t!="function"&&(t=so(t==null?1:+t));function s(){for(var f,p=e.length,_,x,b,k,C,g,y=0;y<i;++y)for(_=fl(e,f_,v_).visitAfter(l),f=0;f<p;++f)x=e[f],C=n[x.index],g=C*C,b=x.x+x.vx,k=x.y+x.vy,_.visit(I);function I(O,M,ee,fe,L){var S=O.data,X=O.r,G=C+X;if(S){if(S.index>x.index){var me=b-S.x-S.vx,V=k-S.y-S.vy,ze=me*me+V*V;ze<G*G&&(me===0&&(me=Pa(a),ze+=me*me),V===0&&(V=Pa(a),ze+=V*V),ze=(G-(ze=Math.sqrt(ze)))/ze*o,x.vx+=(me*=ze)*(G=(X*=X)/(g+X)),x.vy+=(V*=ze)*G,S.vx-=me*(G=1-G),S.vy-=V*G)}return}return M>b+G||fe<b-G||ee>k+G||L<k-G}}function l(f){if(f.data)return f.r=n[f.data.index];for(var p=f.r=0;p<4;++p)f[p]&&f[p].r>f.r&&(f.r=f[p].r)}function u(){if(e){var f,p=e.length,_;for(n=new Array(p),f=0;f<p;++f)_=e[f],n[_.index]=+t(_,f,e)}}return s.initialize=function(f,p){e=f,a=p,u()},s.iterations=function(f){return arguments.length?(i=+f,s):i},s.strength=function(f){return arguments.length?(o=+f,s):o},s.radius=function(f){return arguments.length?(t=typeof f=="function"?f:so(+f),u(),s):t},s}function h_(t){return t.index}function vd(t,e){var n=t.get(e);if(!n)throw new Error("node not found: "+e);return n}function m_(t){var e=h_,n=_,a,o=so(30),i,s,l,u,f,p=1;t==null&&(t=[]);function _(g){return 1/Math.min(l[g.source.index],l[g.target.index])}function x(g){for(var y=0,I=t.length;y<p;++y)for(var O=0,M,ee,fe,L,S,X,G;O<I;++O)M=t[O],ee=M.source,fe=M.target,L=fe.x+fe.vx-ee.x-ee.vx||Pa(f),S=fe.y+fe.vy-ee.y-ee.vy||Pa(f),X=Math.sqrt(L*L+S*S),X=(X-i[O])/X*g*a[O],L*=X,S*=X,fe.vx-=L*(G=u[O]),fe.vy-=S*G,ee.vx+=L*(G=1-G),ee.vy+=S*G}function b(){if(s){var g,y=s.length,I=t.length,O=new Map(s.map((ee,fe)=>[e(ee,fe,s),ee])),M;for(g=0,l=new Array(y);g<I;++g)M=t[g],M.index=g,typeof M.source!="object"&&(M.source=vd(O,M.source)),typeof M.target!="object"&&(M.target=vd(O,M.target)),l[M.source.index]=(l[M.source.index]||0)+1,l[M.target.index]=(l[M.target.index]||0)+1;for(g=0,u=new Array(I);g<I;++g)M=t[g],u[g]=l[M.source.index]/(l[M.source.index]+l[M.target.index]);a=new Array(I),k(),i=new Array(I),C()}}function k(){if(s)for(var g=0,y=t.length;g<y;++g)a[g]=+n(t[g],g,t)}function C(){if(s)for(var g=0,y=t.length;g<y;++g)i[g]=+o(t[g],g,t)}return x.initialize=function(g,y){s=g,f=y,b()},x.links=function(g){return arguments.length?(t=g,b(),x):t},x.id=function(g){return arguments.length?(e=g,x):e},x.iterations=function(g){return arguments.length?(p=+g,x):p},x.strength=function(g){return arguments.length?(n=typeof g=="function"?g:so(+g),k(),x):n},x.distance=function(g){return arguments.length?(o=typeof g=="function"?g:so(+g),C(),x):o},x}var x_={value:()=>{}};function iu(){for(var t=0,e=arguments.length,n={},a;t<e;++t){if(!(a=arguments[t]+"")||a in n||/[\s.]/.test(a))throw new Error("illegal type: "+a);n[a]=[]}return new Is(n)}function Is(t){this._=t}function g_(t,e){return t.trim().split(/^|\s+/).map(function(n){var a="",o=n.indexOf(".");if(o>=0&&(a=n.slice(o+1),n=n.slice(0,o)),n&&!e.hasOwnProperty(n))throw new Error("unknown type: "+n);return{type:n,name:a}})}Is.prototype=iu.prototype={constructor:Is,on:function(t,e){var n=this._,a=g_(t+"",n),o,i=-1,s=a.length;if(arguments.length<2){for(;++i<s;)if((o=(t=a[i]).type)&&(o=__(n[o],t.name)))return o;return}if(e!=null&&typeof e!="function")throw new Error("invalid callback: "+e);for(;++i<s;)if(o=(t=a[i]).type)n[o]=pd(n[o],t.name,e);else if(e==null)for(o in n)n[o]=pd(n[o],t.name,null);return this},copy:function(){var t={},e=this._;for(var n in e)t[n]=e[n].slice();return new Is(t)},call:function(t,e){if((o=arguments.length-2)>0)for(var n=new Array(o),a=0,o,i;a<o;++a)n[a]=arguments[a+2];if(!this._.hasOwnProperty(t))throw new Error("unknown type: "+t);for(i=this._[t],a=0,o=i.length;a<o;++a)i[a].value.apply(e,n)},apply:function(t,e,n){if(!this._.hasOwnProperty(t))throw new Error("unknown type: "+t);for(var a=this._[t],o=0,i=a.length;o<i;++o)a[o].value.apply(e,n)}};function __(t,e){for(var n=0,a=t.length,o;n<a;++n)if((o=t[n]).name===e)return o.value}function pd(t,e,n){for(var a=0,o=t.length;a<o;++a)if(t[a].name===e){t[a]=x_,t=t.slice(0,a).concat(t.slice(a+1));break}return n!=null&&t.push({name:e,value:n}),t}var No=0,Zo=0,Xo=0,lu=1e3,Fs,es,Vs=0,uo=0,Ys=0,ds=typeof performance=="object"&&performance.now?performance:Date,du=typeof window=="object"&&window.requestAnimationFrame?window.requestAnimationFrame.bind(window):function(t){setTimeout(t,17)};function cu(){return uo||(du(b_),uo=ds.now()+Ys)}function b_(){uo=0}function Hi(){this._call=this._time=this._next=null}Hi.prototype=uu.prototype={constructor:Hi,restart:function(t,e,n){if(typeof t!="function")throw new TypeError("callback is not a function");n=(n==null?cu():+n)+(e==null?0:+e),!this._next&&es!==this&&(es?es._next=this:Fs=this,es=this),this._call=t,this._time=n,Ui()},stop:function(){this._call&&(this._call=null,this._time=1/0,Ui())}};function uu(t,e,n){var a=new Hi;return a.restart(t,e,n),a}function w_(){cu(),++No;for(var t=Fs,e;t;)(e=uo-t._time)>=0&&t._call.call(void 0,e),t=t._next;--No}function hd(){uo=(Vs=ds.now())+Ys,No=Zo=0;try{w_()}finally{No=0,k_(),uo=0}}function y_(){var t=ds.now(),e=t-Vs;e>lu&&(Ys-=e,Vs=t)}function k_(){for(var t,e=Fs,n,a=1/0;e;)e._call?(a>e._time&&(a=e._time),t=e,e=e._next):(n=e._next,e._next=null,e=t?t._next=n:Fs=n);es=t,Ui(a)}function Ui(t){if(!No){Zo&&(Zo=clearTimeout(Zo));var e=t-uo;e>24?(t<1/0&&(Zo=setTimeout(hd,t-ds.now()-Ys)),Xo&&(Xo=clearInterval(Xo))):(Xo||(Vs=ds.now(),Xo=setInterval(y_,lu)),No=1,du(hd))}}const C_=1664525,$_=1013904223,md=4294967296;function S_(){let t=1;return()=>(t=(C_*t+$_)%md)/md}function M_(t){return t.x}function z_(t){return t.y}var T_=10,I_=Math.PI*(3-Math.sqrt(5));function A_(t){var e,n=1,a=.001,o=1-Math.pow(a,1/300),i=0,s=.6,l=new Map,u=uu(_),f=iu("tick","end"),p=S_();t==null&&(t=[]);function _(){x(),f.call("tick",e),n<a&&(u.stop(),f.call("end",e))}function x(C){var g,y=t.length,I;C===void 0&&(C=1);for(var O=0;O<C;++O)for(n+=(i-n)*o,l.forEach(function(M){M(n)}),g=0;g<y;++g)I=t[g],I.fx==null?I.x+=I.vx*=s:(I.x=I.fx,I.vx=0),I.fy==null?I.y+=I.vy*=s:(I.y=I.fy,I.vy=0);return e}function b(){for(var C=0,g=t.length,y;C<g;++C){if(y=t[C],y.index=C,y.fx!=null&&(y.x=y.fx),y.fy!=null&&(y.y=y.fy),isNaN(y.x)||isNaN(y.y)){var I=T_*Math.sqrt(.5+C),O=C*I_;y.x=I*Math.cos(O),y.y=I*Math.sin(O)}(isNaN(y.vx)||isNaN(y.vy))&&(y.vx=y.vy=0)}}function k(C){return C.initialize&&C.initialize(t,p),C}return b(),e={tick:x,restart:function(){return u.restart(_),e},stop:function(){return u.stop(),e},nodes:function(C){return arguments.length?(t=C,b(),l.forEach(k),e):t},alpha:function(C){return arguments.length?(n=+C,e):n},alphaMin:function(C){return arguments.length?(a=+C,e):a},alphaDecay:function(C){return arguments.length?(o=+C,e):+o},alphaTarget:function(C){return arguments.length?(i=+C,e):i},velocityDecay:function(C){return arguments.length?(s=1-C,e):1-s},randomSource:function(C){return arguments.length?(p=C,l.forEach(k),e):p},force:function(C,g){return arguments.length>1?(g==null?l.delete(C):l.set(C,k(g)),e):l.get(C)},find:function(C,g,y){var I=0,O=t.length,M,ee,fe,L,S;for(y==null?y=1/0:y*=y,I=0;I<O;++I)L=t[I],M=C-L.x,ee=g-L.y,fe=M*M+ee*ee,fe<y&&(S=L,y=fe);return S},on:function(C,g){return arguments.length>1?(f.on(C,g),e):f.on(C)}}}function E_(){var t,e,n,a,o=so(-30),i,s=1,l=1/0,u=.81;function f(b){var k,C=t.length,g=fl(t,M_,z_).visitAfter(_);for(a=b,k=0;k<C;++k)e=t[k],g.visit(x)}function p(){if(t){var b,k=t.length,C;for(i=new Array(k),b=0;b<k;++b)C=t[b],i[C.index]=+o(C,b,t)}}function _(b){var k=0,C,g,y=0,I,O,M;if(b.length){for(I=O=M=0;M<4;++M)(C=b[M])&&(g=Math.abs(C.value))&&(k+=C.value,y+=g,I+=g*C.x,O+=g*C.y);b.x=I/y,b.y=O/y}else{C=b,C.x=C.data.x,C.y=C.data.y;do k+=i[C.data.index];while(C=C.next)}b.value=k}function x(b,k,C,g){if(!b.value)return!0;var y=b.x-e.x,I=b.y-e.y,O=g-k,M=y*y+I*I;if(O*O/u<M)return M<l&&(y===0&&(y=Pa(n),M+=y*y),I===0&&(I=Pa(n),M+=I*I),M<s&&(M=Math.sqrt(s*M)),e.vx+=y*b.value*a/M,e.vy+=I*b.value*a/M),!0;if(b.length||M>=l)return;(b.data!==e||b.next)&&(y===0&&(y=Pa(n),M+=y*y),I===0&&(I=Pa(n),M+=I*I),M<s&&(M=Math.sqrt(s*M)));do b.data!==e&&(O=i[b.data.index]*a/M,e.vx+=y*O,e.vy+=I*O);while(b=b.next)}return f.initialize=function(b,k){t=b,n=k,p()},f.strength=function(b){return arguments.length?(o=typeof b=="function"?b:so(+b),p(),f):o},f.distanceMin=function(b){return arguments.length?(s=b*b,f):Math.sqrt(s)},f.distanceMax=function(b){return arguments.length?(l=b*b,f):Math.sqrt(l)},f.theta=function(b){return arguments.length?(u=b*b,f):Math.sqrt(u)},f}var N_=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-medium border border-dl-border/20 text-dl-text-dim bg-dl-surface-card"> </span>'),P_=h('<span class="flex items-center gap-1 text-amber-400/70"><!>순환출자 감지</span>'),L_=ms('<line class="cursor-pointer hover:stroke-[#fff3]"></line>'),O_=ms('<circle fill="none" stroke="#818cf860" stroke-width="2"></circle>'),D_=ms('<text text-anchor="middle" class="fill-dl-text-dim/50 text-[8px] pointer-events-none select-none"> </text>'),R_=ms('<g class="cursor-pointer"><!><circle></circle><!></g>'),j_=h('<div class="absolute z-10 px-2 py-1 rounded-md bg-dl-bg-card/95 border border-dl-border/30 text-[10px] text-dl-text-muted whitespace-pre-line pointer-events-none shadow-lg"> </div>'),F_=h('<div class="flex flex-wrap gap-3 px-1 text-[9px] text-dl-text-dim/60"><span class="flex items-center gap-1"><span class="w-2 h-0.5 bg-blue-400/40 inline-block"></span>출자</span> <span class="flex items-center gap-1"><span class="w-2 h-0.5 bg-amber-400/30 inline-block" style="border-bottom: 1px dashed"></span>지분</span> <span class="flex items-center gap-1"><span class="w-2 h-0.5 bg-slate-400/30 inline-block" style="border-bottom: 1px dotted"></span>인물</span> <!></div> <div class="relative rounded-lg border border-dl-border/15 bg-dl-bg-darker/50 overflow-hidden"><svg class="w-full h-full"><defs><marker id="arrow-inv" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="8" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,3 L0,6" fill="#60a5fa40"></path></marker><marker id="arrow-sh" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="8" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,3 L0,6" fill="#f59e0b30"></path></marker></defs><!><!></svg> <!></div>',1),V_=h('<div class="space-y-2"><button class="flex items-center gap-2 w-full px-1 py-1 text-left rounded-md hover:bg-white/3 transition-colors"><!> <span class="text-[11px] font-semibold text-dl-text-dim uppercase tracking-wider flex-1">관계 네트워크</span> <!> <span class="text-[10px] text-dl-text-dim/50"> <!> </span> <!></button> <!></div>');function B_(t,e){Ir(e,!0);let n=je(e,"data",3,null),a=je(e,"loading",3,!1),o=je(e,"centerCode",3,""),i=je(e,"onNavigate",3,null),s=K(!1),l=K(null),u=K(640),f=400,p=K(Bt({show:!1,x:0,y:0,text:""})),_=K(Bt([])),x=K(Bt([])),b=null;const k=["#60a5fa","#f59e0b","#10b981","#f472b6","#a78bfa","#14b8a6","#fb923c","#e879f9","#38bdf8","#fbbf24","#4ade80","#f87171","#818cf8","#2dd4bf","#fb7185"];let C=D(()=>{var N;if(!((N=n())!=null&&N.nodes))return{};const U=[...new Set(n().nodes.map(W=>W.group).filter(Boolean))],ne={};return U.forEach((W,H)=>{ne[W]=k[H%k.length]}),ne});function g(U){return U.id===o()?"#818cf8":U.type==="person"?"#94a3b8":r(C)[U.group]||"#475569"}function y(U){return U.id===o()?18:U.type==="person"?7:Math.max(6,Math.min(14,6+(U.degree||0)*.8))}function I(U){return U.type==="investment"?"#60a5fa40":U.type==="shareholder"?"#f59e0b30":"#94a3b830"}function O(U){return U.type==="person_shareholder"?"3,3":U.type==="shareholder"?"5,3":"none"}function M(U,ne=6){return U?U.length>ne?U.slice(0,ne)+"…":U:""}gr(()=>{if(!r(l))return;const U=new ResizeObserver(ne=>{for(const N of ne)v(u,N.contentRect.width||640,!0)});return U.observe(r(l).parentElement),()=>U.disconnect()}),gr(()=>{var H,E;if(!((E=(H=n())==null?void 0:H.nodes)!=null&&E.length)||!r(s)){b&&(b.stop(),b=null),v(_,[],!0),v(x,[],!0);return}const U=n().nodes.map(q=>({...q,x:q.id===o()?r(u)/2:void 0,y:q.id===o()?f/2:void 0,fx:q.id===o()?r(u)/2:void 0,fy:q.id===o()?f/2:void 0})),ne=new Map(U.map(q=>[q.id,q])),N=n().edges.filter(q=>ne.has(q.source)&&ne.has(q.target)).map(q=>({...q,source:q.source,target:q.target}));b&&b.stop();const W=A_(U).force("link",m_(N).id(q=>q.id).distance(80).strength(.4)).force("charge",E_().strength(-200)).force("center",J0(r(u)/2,f/2)).force("collide",p_().radius(q=>y(q)+4)).alphaDecay(.03);return W.on("tick",()=>{for(const q of U){const J=y(q);q.x=Math.max(J,Math.min(r(u)-J,q.x)),q.y=Math.max(J,Math.min(f-J,q.y))}v(_,[...U],!0),v(x,[...N],!0)}),b=W,()=>{W.stop()}});function ee(U,ne){const N=r(l).getBoundingClientRect(),W=[ne.label];ne.group&&W.push(`그룹: ${ne.group}`),ne.industry&&W.push(ne.industry),ne.type==="company"&&W.push(`연결: ${ne.degree||0}개`),v(p,{show:!0,x:U.clientX-N.left,y:U.clientY-N.top-10,text:W.join(`
`)},!0)}function fe(U,ne){const N=r(l).getBoundingClientRect(),W=[],H=typeof ne.source=="object"?ne.source.label:ne.source,E=typeof ne.target=="object"?ne.target.label:ne.target;W.push(`${H} → ${E}`),ne.type==="investment"?W.push(`출자 (${ne.purpose||""})`):ne.type==="shareholder"?W.push("지분 보유"):W.push("인물 지분"),ne.ownershipPct!=null&&W.push(`지분율: ${ne.ownershipPct.toFixed(1)}%`),v(p,{show:!0,x:U.clientX-N.left,y:U.clientY-N.top-10,text:W.join(`
`)},!0)}function L(){v(p,{show:!1,x:0,y:0,text:""},!0)}function S(U){U.type==="company"&&U.id!==o()&&i()&&i()(U.id)}let X=D(()=>{var U,ne,N;return((N=(ne=(U=n())==null?void 0:U.nodes)==null?void 0:ne.find(W=>W.id===o()))==null?void 0:N.group)||""}),G=D(()=>{var U;return(((U=n())==null?void 0:U.nodes)||[]).filter(ne=>ne.type==="company").length}),me=D(()=>{var U;return(((U=n())==null?void 0:U.nodes)||[]).filter(ne=>ne.type==="person").length}),V=D(()=>{var U;return(((U=n())==null?void 0:U.edges)||[]).length}),ze=D(()=>{var U,ne;return(((ne=(U=n())==null?void 0:U.meta)==null?void 0:ne.cycleCount)||0)>0});var j=Ce(),B=ae(j);{var le=U=>{},we=U=>{var ne=V_(),N=d(ne),W=d(N);nu(W,{size:13,class:"text-dl-text-dim/60"});var H=m(W,4);{var E=rt=>{var dt=N_(),nt=d(dt);z(()=>T(nt,r(X))),c(rt,dt)};$(H,rt=>{r(X)&&rt(E)})}var q=m(H,2),J=d(q),Y=m(J);{var ye=rt=>{var dt=oa();z(()=>T(dt,`· ${r(me)??""}인`)),c(rt,dt)};$(Y,rt=>{r(me)>0&&rt(ye)})}var Se=m(Y),te=m(q,2);{var Oe=rt=>{Yc(rt,{size:12,class:"text-dl-text-dim/40"})},tt=rt=>{ul(rt,{size:12,class:"text-dl-text-dim/40"})};$(te,rt=>{r(s)?rt(Oe):rt(tt,-1)})}var ot=m(N,2);{var Ge=rt=>{var dt=F_(),nt=ae(dt),st=m(d(nt),6);{var xt=ce=>{var w=P_(),F=d(w);ss(F,{size:9}),c(ce,w)};$(st,ce=>{r(ze)&&ce(xt)})}var St=m(nt,2);Eo(St,"height: 400px;");var Nt=d(St),lr=m(d(Nt));Ae(lr,17,()=>r(x),Ne,(ce,w)=>{const F=D(()=>typeof r(w).source=="object"?r(w).source.x:0),re=D(()=>typeof r(w).source=="object"?r(w).source.y:0),ie=D(()=>typeof r(w).target=="object"?r(w).target.x:0),ue=D(()=>typeof r(w).target=="object"?r(w).target.y:0);var P=L_();z((Z,$e)=>{ir(P,"x1",r(F)),ir(P,"y1",r(re)),ir(P,"x2",r(ie)),ir(P,"y2",r(ue)),ir(P,"stroke",Z),ir(P,"stroke-width",r(w).ownershipPct>20?2:1),ir(P,"stroke-dasharray",$e),ir(P,"marker-end",r(w).type==="investment"?"url(#arrow-inv)":r(w).type==="shareholder"?"url(#arrow-sh)":"")},[()=>I(r(w)),()=>O(r(w))]),xn("mouseenter",P,Z=>fe(Z,r(w))),xn("mouseleave",P,L),c(ce,P)});var R=m(lr);Ae(R,17,()=>r(_),Ne,(ce,w)=>{const F=D(()=>y(r(w))),re=D(()=>g(r(w))),ie=D(()=>r(w).id===o());var ue=R_(),P=d(ue);{var Z=Pe=>{var de=O_();z(()=>ir(de,"r",r(F)+3)),c(Pe,de)};$(P,Pe=>{r(ie)&&Pe(Z)})}var $e=m(P),ve=m($e);{var ke=Pe=>{var de=D_(),Te=d(de);z(Re=>{ir(de,"y",r(F)+12),T(Te,Re)},[()=>M(r(w).label)]),c(Pe,de)};$(ve,Pe=>{r(F)>=8&&Pe(ke)})}z(()=>{ir(ue,"transform",`translate(${r(w).x??""},${r(w).y??""})`),ir($e,"r",r(F)),ir($e,"fill",r(re)),ir($e,"stroke",r(ie)?"#c4b5fd":"#ffffff10"),ir($e,"stroke-width",r(ie)?2:.5),ir($e,"opacity",r(w).type==="person"?.7:.85)}),xn("mouseenter",ue,Pe=>ee(Pe,r(w))),xn("mouseleave",ue,L),he("click",ue,()=>S(r(w))),c(ce,ue)}),Jn(Nt,ce=>v(l,ce),()=>r(l));var pe=m(Nt,2);{var oe=ce=>{var w=j_(),F=d(w);z(()=>{Eo(w,`left: ${r(p).x??""}px; top: ${r(p).y??""}px; transform: translate(-50%, -100%)`),T(F,r(p).text)}),c(ce,w)};$(pe,ce=>{r(p).show&&ce(oe)})}z(()=>ir(Nt,"viewBox",`0 0 ${r(u)??""} 400`)),c(rt,dt)};$(ot,rt=>{r(s)&&rt(Ge)})}z(()=>{T(J,`${r(G)??""}사`),T(Se,` · ${r(V)??""}연결`)}),he("click",N,()=>{v(s,!r(s))}),c(U,ne)};$(B,U=>{var ne,N,W;a()?U(le):((ne=n())==null?void 0:ne.available)!==!1&&((W=(N=n())==null?void 0:N.nodes)==null?void 0:W.length)>0&&U(we,1)})}c(t,j),Ar()}Kr(["click"]);var q_=h('<div class="flex items-center justify-between text-[12px]"><span class="text-dl-text-muted"> </span> <kbd class="px-1.5 py-0.5 rounded bg-dl-bg-darker border border-dl-border/30 text-[11px] font-mono text-dl-text-dim min-w-[32px] text-center"> </kbd></div>'),H_=h('<div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"><div class="bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl w-80 max-w-[90vw] overflow-hidden"><div class="flex items-center justify-between px-4 py-3 border-b border-dl-border/20"><div class="flex items-center gap-2 text-dl-text"><!> <span class="text-[13px] font-semibold">단축키</span></div> <button class="p-1 rounded text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="px-4 py-3 space-y-1.5"></div></div></div>');function U_(t,e){let n=je(e,"show",3,!1),a=je(e,"onClose",3,null);const o=[{key:"?",desc:"단축키 도움말"},{key:"1",desc:"Chat 탭"},{key:"2",desc:"Viewer 탭"},{key:"Ctrl+K",desc:"종목 검색"},{key:"Ctrl+F",desc:"뷰어 내 검색"},{key:"J / ↓",desc:"다음 topic"},{key:"K / ↑",desc:"이전 topic"},{key:"S",desc:"현재 topic AI 요약"},{key:"B",desc:"북마크 토글"},{key:"Esc",desc:"모달/검색 닫기"}];var i=Ce(),s=ae(i);{var l=u=>{var f=H_(),p=d(f),_=d(p),x=d(_),b=d(x);hh(b,{size:16});var k=m(x,2),C=d(k);Fa(C,{size:14});var g=m(_,2);Ae(g,21,()=>o,Ne,(y,I)=>{var O=q_(),M=d(O),ee=d(M),fe=m(M,2),L=d(fe);z(()=>{T(ee,r(I).desc),T(L,r(I).key)}),c(y,O)}),he("click",f,function(...y){var I;(I=a())==null||I.apply(this,y)}),he("click",p,y=>y.stopPropagation()),he("click",k,function(...y){var I;(I=a())==null||I.apply(this,y)}),c(u,f)};$(s,u=>{n()&&u(l)})}c(t,i)}Kr(["click"]);var W_=h('<div class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"></div>'),K_=h('<button class="p-1 rounded-md text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"><!></button>'),G_=h('<div class="flex items-center justify-between"><div class="min-w-0"><div class="text-[12px] font-semibold text-dl-text truncate"> </div> <div class="text-[10px] font-mono text-dl-text-dim"> </div></div> <div class="flex items-center gap-0.5 flex-shrink-0"><!></div></div>'),J_=h('<div class="text-[12px] text-dl-text-dim">종목 미선택</div>'),Y_=h('<button class="w-full text-left px-2 py-1.5 rounded-md text-[11px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-1.5"><!> <span class="truncate"> </span> <span class="text-[9px] font-mono text-dl-text-dim/40 ml-auto"> </span></button>'),X_=h('<div class="px-3 py-3 flex-1 overflow-y-auto"><div class="text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold mb-2">최근 종목</div> <!></div>'),Q_=h('<div class="sticky top-0 z-20 px-6 py-2 bg-dl-bg-dark/95 backdrop-blur-sm border-b border-dl-border/10"><div class="flex items-center gap-2 max-w-2xl mx-auto"><button class="flex-shrink-0 p-1.5 rounded-md text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <button class="flex items-center gap-2 flex-1 px-3 py-1.5 rounded-lg border border-dl-border/20 bg-dl-bg-darker/60 text-[12px] text-dl-text-dim hover:border-dl-border/40 hover:bg-dl-bg-darker transition-colors"><!> <span class="flex-1 text-left">공시 섹션 검색... <kbd class="ml-2 px-1 py-0.5 rounded bg-dl-border/15 text-[10px] font-mono">/</kbd></span></button></div></div>'),Z_=h('<button class="p-1 text-dl-text-dim hover:text-dl-text"><!></button>'),eb=h('<div class="text-[10px] text-dl-text-dim/60 mt-0.5"> </div>'),tb=h('<div class="text-[11px] text-dl-text-dim truncate mt-0.5"> </div>'),rb=h('<span class="text-[10px] text-dl-accent font-mono flex-shrink-0"> </span>'),nb=h('<button class="w-full text-left px-4 py-2 text-[13px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-start gap-2 border-b border-dl-border/5"><div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/50 font-mono"> </span></div> <!> <!></div> <!></button>'),ab=h('<button class="w-full py-2 text-[12px] text-dl-accent/70 hover:text-dl-accent hover:bg-white/3 transition-colors"> </button>'),ob=h('<div class="flex items-center justify-center py-3"><!></div>'),sb=h("<!> <!> <!>",1),ib=h('<div class="flex items-center justify-center py-6 gap-2"><!> <span class="text-[12px] text-dl-text-dim">검색 중...</span></div>'),lb=h('<div class="text-center py-6 text-[12px] text-dl-text-dim">결과 없음</div>'),db=h('<button class="w-full text-left px-4 py-2 text-[13px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-2"><!> <span> </span> <span class="text-[10px] text-dl-text-dim/40 font-mono ml-auto"> </span></button>'),cb=h('<div class="px-4 py-2 text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold">최근 본 섹션</div> <!>',1),ub=h('<div class="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/50 backdrop-blur-sm"><div class="w-full max-w-xl bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl overflow-hidden"><div class="flex items-center gap-2 px-4 py-3 border-b border-dl-border/20"><!> <input placeholder="섹션, topic, 키워드 검색..." class="flex-1 bg-transparent text-[14px] text-dl-text outline-none placeholder:text-dl-text-dim"/> <!> <kbd class="px-1.5 py-0.5 rounded bg-dl-border/15 text-[10px] font-mono text-dl-text-dim">Esc</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div></div></div>'),fb=h('<span class="text-[11px] text-dl-text-muted truncate"> </span>'),vb=h('<div class="sticky top-0 z-30 flex items-center gap-2 px-3 py-1.5 bg-dl-bg-dark/95 border-b border-dl-border/20 backdrop-blur-sm"><button class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"><!> <span>목차</span></button> <button class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"><!> <span>검색</span></button> <!></div>'),pb=h('<span class="text-[9px] px-1 py-0.5 rounded bg-dl-border/10 text-dl-text-dim/60"> </span>'),hb=h('<button class="w-full text-left px-3 py-2 text-[13px] hover:bg-white/5 transition-colors flex items-center gap-2 border-b border-dl-border/5 last:border-b-0"><!> <span class="text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim ml-auto flex-shrink-0"> </span> <!></button>'),mb=h('<div class="absolute top-full mt-1 w-full bg-dl-bg-card border border-dl-border/30 rounded-lg shadow-xl overflow-hidden z-30 max-h-[300px] overflow-y-auto"></div>'),xb=h('<button class="w-full text-left px-3 py-2 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-2"><!> <span class="truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim/50 ml-auto"> </span></button>'),gb=h('<div class="w-full max-w-sm mt-6"><div class="text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold mb-2 text-left">최근 검색</div> <div class="space-y-0.5"></div></div>'),_b=h('<div class="flex flex-col items-center justify-center h-full text-center px-8 max-w-lg mx-auto"><!> <div class="text-[14px] text-dl-text-muted mb-2">공시 뷰어</div> <div class="text-[12px] text-dl-text-dim mb-6">종목을 검색하여 공시 문서를 살펴보세요</div> <div class="w-full max-w-sm relative"><div class="flex items-center gap-2 px-3 py-2 rounded-lg border border-dl-border/30 bg-dl-bg-darker/60 focus-within:border-dl-accent/40 transition-colors"><!> <input placeholder="종목명 또는 종목코드..." class="flex-1 bg-transparent text-[13px] text-dl-text outline-none placeholder:text-dl-text-dim"/> <!></div> <!></div> <!></div>'),bb=h('<div class="flex flex-col items-center justify-center h-full"><!> <div class="text-[12px] text-dl-text-dim">공시 데이터 로딩 중...</div></div>'),wb=h('<div class="max-w-7xl mx-auto px-6 py-4"><div class="animate-pulse space-y-4"><div class="h-5 bg-dl-surface-card/40 rounded w-2/3"></div> <div class="h-3 bg-dl-surface-card/30 rounded w-full"></div> <div class="h-3 bg-dl-surface-card/30 rounded w-5/6"></div> <div class="h-20 bg-dl-surface-card/20 rounded"></div> <div class="h-3 bg-dl-surface-card/30 rounded w-4/5"></div> <div class="h-3 bg-dl-surface-card/30 rounded w-full"></div> <div class="h-16 bg-dl-surface-card/20 rounded"></div></div></div>'),yb=h('<div class="absolute top-0 left-0 right-0 h-0.5 bg-dl-accent/20 overflow-hidden z-10"><div class="h-full bg-dl-accent/60 animate-progress-bar"></div></div>'),kb=h('<div class="animate-fadeIn"><!> <!></div>'),Cb=h('<div class="mt-8 border-t border-dl-border/10 pt-4"><button class="flex items-center gap-2 text-[12px] text-dl-text-dim hover:text-dl-text transition-colors mb-3"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg> 투자 인사이트 · 관계도</button> <!></div>'),$b=h('<!> <div><div class="mt-0"><!></div> <!></div>',1),Sb=h('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[13px] text-dl-text-dim">좌측 목차에서 항목을 선택하세요</div></div>'),Mb=h('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[13px] text-dl-text-dim">이 종목의 공시 데이터가 없습니다</div></div>'),zb=h('<div class="flex h-full min-h-0 bg-dl-bg-dark relative"><!> <div><div class="h-full flex flex-col"><div class="px-3 py-2 border-b border-dl-border/20 flex-shrink-0"><!></div> <!> <!></div></div> <div class="flex-1 min-w-0 overflow-y-auto"><!> <!> <!> <!></div></div> <!>',1);function Tb(t,e){Ir(e,!0);let n=je(e,"viewer",3,null),a=je(e,"company",3,null),o=je(e,"onAskAI",3,null),i=je(e,"onTopicChange",3,null),s=je(e,"recentCompanies",19,()=>[]),l=je(e,"onCompanySelect",3,null),u=K(!1),f=K(!1),p=K(!1);function _(){v(f,typeof window<"u"&&window.innerWidth<=768,!0)}gr(()=>(_(),window.addEventListener("resize",_),()=>window.removeEventListener("resize",_)));let x=K(!1),b=K(""),k=K(null);function C(){v(x,!r(x)),r(x)?requestAnimationFrame(()=>{var P;return(P=r(k))==null?void 0:P.focus()}):(v(b,""),v(B,null))}let g=K(!1),y=K(!1),I=null;gr(()=>{var Z;const P=(Z=a())==null?void 0:Z.stockCode;P&&P!==I&&n()&&(I=P,n().loadCompany(P))});let O=null;gr(()=>{var $e,ve,ke,Pe;const P=($e=n())==null?void 0:$e.selectedTopic,Z=((ke=(ve=n())==null?void 0:ve.topicData)==null?void 0:ke.topicLabel)||P;P&&P!==O&&(O=P,(Pe=i())==null||Pe(P,Z),S(P,Z))});let M=K(Bt([]));const ee=8;function fe(){var P;try{const Z=localStorage.getItem("dartlab-viewer-history");return(Z?JSON.parse(Z):{})[(P=a())==null?void 0:P.stockCode]||[]}catch{return[]}}function L(P){var Z;try{const $e=localStorage.getItem("dartlab-viewer-history"),ve=$e?JSON.parse($e):{};ve[(Z=a())==null?void 0:Z.stockCode]=P,localStorage.setItem("dartlab-viewer-history",JSON.stringify(ve))}catch{}}function S(P,Z){var ve;if(!((ve=a())!=null&&ve.stockCode))return;const $e=r(M).filter(ke=>ke.topic!==P);v(M,[{topic:P,label:Z,time:Date.now()},...$e].slice(0,ee),!0),L(r(M))}gr(()=>{var P;(P=a())!=null&&P.stockCode&&v(M,fe(),!0)});let X=K(""),G=K(Bt([])),me=K(!1),V=null,ze=K(null);gr(()=>{const P=r(X).trim();if(!P||P.length<1){v(G,[],!0);return}clearTimeout(V),v(me,!0),V=setTimeout(async()=>{try{const Z=await sl(P);r(X).trim()===P&&v(G,Z||[],!0)}catch{v(G,[],!0)}v(me,!1)},200)});function j(P){var Z;v(X,""),v(G,[],!0),(Z=l())==null||Z(P)}let B=K(null),le=K(15),we=K(!1),U=null;function ne(){var Z,$e;if(!(($e=(Z=n())==null?void 0:Z.toc)!=null&&$e.chapters))return[];const P=[];for(const ve of n().toc.chapters)for(const ke of ve.topics)P.push({topic:ke.topic,chapter:ve.chapter});return P}function N(P){var Z,$e;if(($e=(Z=n())==null?void 0:Z.toc)!=null&&$e.chapters){for(const ve of n().toc.chapters)if(ve.topics.find(Pe=>Pe.topic===P)){n().selectTopic(P,ve.chapter);return}}}function W(P){var Z,$e,ve,ke;if(($e=(Z=n())==null?void 0:Z.toc)!=null&&$e.chapters){for(const Pe of n().toc.chapters)if(Pe.topics.find(Te=>Te.topic===P)){const Te=r(b).trim();n().selectTopic(P,Pe.chapter),Te&&((ke=(ve=n()).setSearchHighlight)==null||ke.call(ve,Te)),v(x,!1),v(b,""),v(B,null);return}}}function H(P){var ve,ke,Pe,de;const Z=(ve=P.target)==null?void 0:ve.tagName,$e=Z==="INPUT"||Z==="TEXTAREA"||((ke=P.target)==null?void 0:ke.isContentEditable);if(P.key==="f"&&(P.ctrlKey||P.metaKey)&&a()){P.preventDefault(),C();return}if(P.key==="Escape"){if(r(p)){v(p,!1);return}if(r(x)){v(x,!1),v(b,""),v(B,null);return}return}if(!$e){if(P.key==="?"){v(p,!r(p));return}if(P.key==="/"&&a()){P.preventDefault(),C();return}if(!r(x)&&(P.key==="ArrowUp"||P.key==="ArrowDown"||P.key==="j"||P.key==="k")&&((Pe=n())!=null&&Pe.selectedTopic)){const Te=ne(),Re=Te.findIndex(et=>et.topic===n().selectedTopic);if(Re<0)return;const _e=P.key==="ArrowDown"||P.key==="j"?Re+1:Re-1;_e>=0&&_e<Te.length&&(P.preventDefault(),n().selectTopic(Te[_e].topic,Te[_e].chapter));return}if(P.key==="b"&&((de=n())!=null&&de.selectedTopic)){n().toggleBookmark(n().selectedTopic);return}}}gr(()=>{var $e,ve,ke,Pe;const P=r(b).trim();if(v(le,15),!P||!(($e=a())!=null&&$e.stockCode)){v(B,null);return}if((ve=n())!=null&&ve.searchIndexReady){const de=n().searchSections(P);v(B,de.length>0?de:null,!0);return}const Z=[];if((Pe=(ke=n())==null?void 0:ke.toc)!=null&&Pe.chapters){const de=P.toLowerCase();for(const Te of n().toc.chapters)for(const Re of Te.topics)(Re.label.toLowerCase().includes(de)||Re.topic.toLowerCase().includes(de))&&Z.push({topic:Re.topic,label:Re.label,chapter:Te.chapter,snippet:"",matchCount:0,source:"toc"})}v(B,Z.length>0?Z:null,!0),clearTimeout(U),P.length>=2&&(v(we,!0),U=setTimeout(async()=>{try{const de=await Rv(a().stockCode,P);if(r(b).trim()!==P)return;const Te=(de.results||[]).map(_e=>({..._e,source:"text"})),Re=new Set(Z.map(_e=>_e.topic)),He=[...Z,...Te.filter(_e=>!Re.has(_e.topic))];v(B,He.length>0?He:null,!0)}catch{}v(we,!1)},300))});var E=zb();xn("keydown",Ns,H);var q=ae(E),J=d(q);{var Y=P=>{var Z=W_();he("click",Z,()=>{v(u,!1)}),c(P,Z)};$(J,P=>{r(f)&&r(u)&&P(Y)})}var ye=m(J,2),Se=d(ye),te=d(Se),Oe=d(te);{var tt=P=>{var Z=G_(),$e=d(Z),ve=d($e),ke=d(ve),Pe=m(ve,2),de=d(Pe),Te=m($e,2),Re=d(Te);{var He=_e=>{var et=K_(),Ct=d(et);Fa(Ct,{size:12}),he("click",et,()=>{v(u,!1)}),c(_e,et)};$(Re,_e=>{r(f)&&_e(He)})}z(()=>{T(ke,a().corpName||a().company),T(de,a().stockCode)}),c(P,Z)},ot=P=>{var Z=J_();c(P,Z)};$(Oe,P=>{a()?P(tt):P(ot,-1)})}var Ge=m(te,2);{var rt=P=>{var Z=X_(),$e=m(d(Z),2);Ae($e,17,s,Ne,(ve,ke)=>{var Pe=Y_(),de=d(Pe);ad(de,{size:11,class:"text-dl-text-dim/30 flex-shrink-0"});var Te=m(de,2),Re=d(Te),He=m(Te,2),_e=d(He);z(()=>{T(Re,r(ke).corpName||r(ke).company),T(_e,r(ke).stockCode)}),he("click",Pe,()=>{var et;return(et=l())==null?void 0:et(r(ke))}),c(ve,Pe)}),c(P,Z)};$(Ge,P=>{!a()&&s().length>0&&P(rt)})}var dt=m(Ge,2);{let P=D(()=>{var de;return(de=n())==null?void 0:de.toc}),Z=D(()=>{var de;return(de=n())==null?void 0:de.tocLoading}),$e=D(()=>{var de;return(de=n())==null?void 0:de.selectedTopic}),ve=D(()=>{var de;return(de=n())==null?void 0:de.expandedChapters}),ke=D(()=>{var de,Te;return((Te=(de=n())==null?void 0:de.getBookmarks)==null?void 0:Te.call(de))??[]}),Pe=D(()=>{var de;return((de=n())==null?void 0:de.visitedTopics)??new Set});A1(dt,{get toc(){return r(P)},get loading(){return r(Z)},get selectedTopic(){return r($e)},get expandedChapters(){return r(ve)},get bookmarks(){return r(ke)},get recentHistory(){return r(M)},onSelectTopic:(de,Te)=>{var Re;(Re=n())==null||Re.selectTopic(de,Te),r(f)&&v(u,!1)},get visitedTopics(){return r(Pe)},onToggleChapter:de=>{var Te;return(Te=n())==null?void 0:Te.toggleChapter(de)},onPrefetch:de=>{var Te;return(Te=n())==null?void 0:Te.prefetchTopic(de)}})}var nt=m(ye,2),st=d(nt);{var xt=P=>{var Z=Q_(),$e=d(Z),ve=d($e),ke=d(ve);{var Pe=He=>{gh(He,{size:15})},de=He=>{tu(He,{size:15})};$(ke,He=>{r(y)?He(Pe):He(de,-1)})}var Te=m(ve,2),Re=d(Te);xa(Re,{size:13,class:"flex-shrink-0"}),z(()=>ir(ve,"title",r(y)?"목차 펼치기":"목차 접기")),he("click",ve,()=>{v(y,!r(y))}),he("click",Te,C),c(P,Z)};$(st,P=>{a()&&!r(f)&&P(xt)})}var St=m(st,2);{var Nt=P=>{var Z=ub(),$e=d(Z),ve=d($e),ke=d(ve);xa(ke,{size:16,class:"text-dl-text-dim flex-shrink-0"});var Pe=m(ke,2);Jn(Pe,Ve=>v(k,Ve),()=>r(k));var de=m(Pe,2);{var Te=Ve=>{var Ee=Z_(),Ie=d(Ee);Fa(Ie,{size:14}),he("click",Ee,()=>{v(b,"")}),c(Ve,Ee)};$(de,Ve=>{r(b)&&Ve(Te)})}var Re=m(ve,2),He=d(Re);{var _e=Ve=>{var Ee=sb(),Ie=ae(Ee);Ae(Ie,17,()=>r(B).slice(0,r(le)),Ne,(qt,$t)=>{var Mt=nb(),ct=d(Mt),tr=d(ct),Mr=d(tr),yr=d(Mr),Br=m(Mr,2),zr=d(Br),_t=m(tr,2);{var Ht=bt=>{var Be=eb(),rr=d(Be);z(()=>T(rr,r($t).chapter)),c(bt,Be)};$(_t,bt=>{r($t).chapter&&bt(Ht)})}var zt=m(_t,2);{var Lt=bt=>{var Be=tb(),rr=d(Be);z(()=>T(rr,r($t).snippet)),c(bt,Be)};$(zt,bt=>{r($t).snippet&&bt(Lt)})}var dr=m(ct,2);{var ur=bt=>{var Be=rb(),rr=d(Be);z(()=>T(rr,`${r($t).matchCount??""}건`)),c(bt,Be)};$(dr,bt=>{r($t).matchCount>0&&bt(ur)})}z(()=>{T(yr,r($t).label),T(zr,r($t).topic)}),he("click",Mt,()=>W(r($t).topic)),c(qt,Mt)});var yt=m(Ie,2);{var Pt=qt=>{var $t=ab(),Mt=d($t);z(()=>T(Mt,`더보기 (${r(B).length-r(le)}개 남음)`)),he("click",$t,()=>{v(le,r(le)+15)}),c(qt,$t)};$(yt,qt=>{r(B).length>r(le)&&qt(Pt)})}var Je=m(yt,2);{var At=qt=>{var $t=ob(),Mt=d($t);Ur(Mt,{size:14,class:"animate-spin text-dl-text-dim"}),c(qt,$t)};$(Je,qt=>{r(we)&&qt(At)})}c(Ve,Ee)},et=Ve=>{var Ee=ib(),Ie=d(Ee);Ur(Ie,{size:14,class:"animate-spin text-dl-text-dim"}),c(Ve,Ee)},Ct=Ve=>{var Ee=lb();c(Ve,Ee)},at=D(()=>r(b).trim()),Dt=Ve=>{var Ee=Ce(),Ie=ae(Ee);{var yt=Pt=>{var Je=cb(),At=m(ae(Je),2);Ae(At,17,()=>r(M),Ne,(qt,$t)=>{var Mt=db(),ct=d(Mt);ls(ct,{size:12,class:"text-dl-text-dim/40 flex-shrink-0"});var tr=m(ct,2),Mr=d(tr),yr=m(tr,2),Br=d(yr);z(()=>{T(Mr,r($t).label),T(Br,r($t).topic)}),he("click",Mt,()=>W(r($t).topic)),c(qt,Mt)}),c(Pt,Je)};$(Ie,Pt=>{r(M).length>0&&Pt(yt)})}c(Ve,Ee)};$(He,Ve=>{r(B)?Ve(_e):r(we)?Ve(et,1):r(at)?Ve(Ct,2):Ve(Dt,-1)})}he("click",Z,()=>{v(x,!1),v(b,""),v(B,null)}),he("click",$e,Ve=>Ve.stopPropagation()),Ea(Pe,()=>r(b),Ve=>v(b,Ve)),c(P,Z)};$(St,P=>{r(x)&&P(Nt)})}var lr=m(St,2);{var R=P=>{var Z=vb(),$e=d(Z),ve=d($e);zn(ve,{size:11});var ke=m($e,2),Pe=d(ke);xa(Pe,{size:11});var de=m(ke,2);{var Te=Re=>{var He=fb(),_e=d(He);z(()=>{var et,Ct,at;return T(_e,((Ct=(et=n())==null?void 0:et.topicData)==null?void 0:Ct.topicLabel)||((at=n())==null?void 0:at.selectedTopic))}),c(Re,He)};$(de,Re=>{var He;(He=n())!=null&&He.selectedTopic&&Re(Te)})}he("click",$e,()=>{v(u,!0)}),he("click",ke,C),c(P,Z)};$(lr,P=>{r(f)&&a()&&P(R)})}var pe=m(lr,2);{var oe=P=>{var Z=_b(),$e=d(Z);zn($e,{size:32,class:"text-dl-text-dim/30 mb-3"});var ve=m($e,6),ke=d(ve),Pe=d(ke);xa(Pe,{size:14,class:"text-dl-text-dim flex-shrink-0"});var de=m(Pe,2);Jn(de,at=>v(ze,at),()=>r(ze));var Te=m(de,2);{var Re=at=>{Ur(at,{size:14,class:"animate-spin text-dl-text-dim flex-shrink-0"})};$(Te,at=>{r(me)&&at(Re)})}var He=m(ke,2);{var _e=at=>{var Dt=mb();Ae(Dt,21,()=>r(G).slice(0,10),Ne,(Ve,Ee)=>{var Ie=hb(),yt=d(Ie);ad(yt,{size:13,class:"text-dl-text-dim/40 flex-shrink-0"});var Pt=m(yt,2),Je=d(Pt),At=m(Pt,2),qt=d(At),$t=m(At,2);{var Mt=ct=>{var tr=pb(),Mr=d(tr);z(()=>T(Mr,r(Ee).market)),c(ct,tr)};$($t,ct=>{r(Ee).market&&ct(Mt)})}z(()=>{T(Je,r(Ee).corpName||r(Ee).company),T(qt,r(Ee).stockCode)}),he("click",Ie,()=>j(r(Ee))),c(Ve,Ie)}),c(at,Dt)};$(He,at=>{r(G).length>0&&at(_e)})}var et=m(ve,2);{var Ct=at=>{var Dt=gb(),Ve=m(d(Dt),2);Ae(Ve,21,s,Ne,(Ee,Ie)=>{var yt=xb(),Pt=d(yt);ls(Pt,{size:12,class:"text-dl-text-dim/30 flex-shrink-0"});var Je=m(Pt,2),At=d(Je),qt=m(Je,2),$t=d(qt);z(()=>{T(At,r(Ie).corpName||r(Ie).company),T($t,r(Ie).stockCode)}),he("click",yt,()=>{var Mt;return(Mt=l())==null?void 0:Mt(r(Ie))}),c(Ee,yt)}),c(at,Dt)};$(et,at=>{s().length>0&&at(Ct)})}Ea(de,()=>r(X),at=>v(X,at)),c(P,Z)},ce=P=>{var Z=bb(),$e=d(Z);Ur($e,{size:24,class:"animate-spin text-dl-text-dim/40 mb-3"}),c(P,Z)},w=P=>{var Z=wb();c(P,Z)},F=P=>{var Z=$b(),$e=ae(Z);{var ve=He=>{var _e=yb();c(He,_e)};$($e,He=>{var _e;(_e=n())!=null&&_e.topicLoading&&He(ve)})}var ke=m($e,2),Pe=d(ke),de=d(Pe);A0(de,{get topicData(){return n().topicData},get diffSummary(){return n().diffSummary},get viewer(){return n()},get onAskAI(){return o()},get searchHighlight(){return n().searchHighlight}});var Te=m(Pe,2);{var Re=He=>{var _e=Cb(),et=d(_e),Ct=d(et),at=m(et,2);{var Dt=Ve=>{var Ee=kb(),Ie=d(Ee);G0(Ie,{get data(){return n().insightData},get loading(){return n().insightLoading},get toc(){return n().toc},onNavigateTopic:N});var yt=m(Ie,2);{let Pt=D(()=>{var Je;return(Je=a())==null?void 0:Je.stockCode});B_(yt,{get data(){return n().networkData},get loading(){return n().networkLoading},get centerCode(){return r(Pt)},onNavigate:Je=>{var At;n()&&Je!==((At=a())==null?void 0:At.stockCode)&&n().loadCompany(Je)}})}c(Ve,Ee)};$(at,Ve=>{r(g)&&Ve(Dt)})}z(()=>Ue(Ct,0,`w-3 h-3 transition-transform ${r(g)?"rotate-90":""}`)),he("click",et,()=>{v(g,!r(g))}),c(He,_e)};$(Te,He=>{(n().insightData||n().networkData||n().insightLoading||n().networkLoading)&&He(Re)})}z(()=>{var He;return Ue(ke,1,`max-w-7xl mx-auto px-6 py-4 ${(He=n())!=null&&He.topicLoading?"opacity-40 pointer-events-none":"animate-fadeIn"} transition-opacity duration-200`)}),c(P,Z)},re=P=>{var Z=Sb(),$e=d(Z);zn($e,{size:28,class:"text-dl-text-dim/30 mb-3"}),c(P,Z)},ie=P=>{var Z=Mb(),$e=d(Z);Ja($e,{size:28,class:"text-dl-text-dim/30 mb-3"}),c(P,Z)};$(pe,P=>{var Z,$e,ve,ke,Pe,de,Te,Re,He;a()?(Z=n())!=null&&Z.tocLoading?P(ce,1):($e=n())!=null&&$e.topicLoading&&!((ve=n())!=null&&ve.topicData)?P(w,2):(ke=n())!=null&&ke.topicData?P(F,3):(Pe=n())!=null&&Pe.toc&&!((de=n())!=null&&de.selectedTopic)?P(re,4):((He=(Re=(Te=n())==null?void 0:Te.toc)==null?void 0:Re.chapters)==null?void 0:He.length)===0&&P(ie,5):P(oe)})}var ue=m(q,2);U_(ue,{get show(){return r(p)},onClose:()=>{v(p,!1)}}),z(()=>Ue(ye,1,`${r(f)?`fixed top-0 left-0 bottom-0 z-50 w-64 transition-transform duration-200 ${r(u)?"translate-x-0":"-translate-x-full"}`:`flex-shrink-0 transition-all duration-200 ${r(y)?"w-0 overflow-hidden":"w-56"}`} border-r border-dl-border/30 overflow-hidden bg-dl-bg-dark`)),c(t,E),Ar()}Kr(["click"]);var Ib=h('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),Ab=h('<button><div class="font-medium"> </div> <div class="text-[10px] text-dl-text-dim"> </div></button>'),Eb=h('<div class="px-3 py-4 text-[11px] text-dl-text-dim text-center">아직 조회한 종목이 없습니다</div>'),Nb=h('<div class="border-t border-dl-border/30 px-4 py-2 text-[10px] text-dl-text-dim/50"> </div>'),Pb=h('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-sm font-semibold text-dl-text">공시뷰어</div> <div class="text-[10px] text-dl-text-dim">Disclosure Viewer</div></div></div></div> <div class="flex-1 overflow-y-auto px-2 py-2"><div class="text-[10px] text-dl-text-dim uppercase tracking-widest font-semibold px-2 mb-2">최근 종목</div> <!></div> <!></div>'),Lb=h('<div class="flex flex-col items-center py-4 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full opacity-60"/></div>'),Ob=h("<aside><!></aside>"),Db=h("<!> <span>확인 중...</span>",1),Rb=h("<!> <span>설정 필요</span>",1),jb=h('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),Fb=h('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!>',1),Vb=h('<div class="min-w-0 flex-1 pt-10"><!></div>'),Bb=h('<div class="flex-shrink-0 border-l border-dl-border/30 transition-all duration-300"><!></div>'),qb=h('<div class="min-w-0 flex-1 flex flex-col"><!></div> <!>',1),Hb=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),Ub=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),Wb=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),Kb=h('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),Gb=h('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),Jb=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),Yb=h('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),Xb=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),Qb=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),Zb=h('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),e2=h('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),t2=h('<div class="text-[10px] text-dl-text-dim mt-2"> </div>'),r2=h('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex login</div></div></div></div> <!> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),n2=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2"> </div></div>'),a2=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 계정 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),o2=h('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),s2=h("<button> <!></button>"),i2=h('<div class="flex flex-wrap gap-1.5"></div>'),l2=h('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),d2=h('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),c2=h('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),u2=h('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),f2=h('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),v2=h('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),p2=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),h2=h("<!> <!> <!> <!> <!> <!>",1),m2=h('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),x2=h('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),g2=h('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),_2=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><span class="text-[10px] text-dl-text-dim">공시 보기</span> <!></div></button>'),b2=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div></div> <!>',1),w2=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div></button>'),y2=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div></div> <!>',1),k2=h('<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),C2=h('<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim"><!> <div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div> <div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div></div>'),$2=h('<div class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn" role="presentation"><div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"><div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"/> <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div> <div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim"><span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span></div></div></div>'),S2=h('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),M2=h('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-2 left-3 z-20 pointer-events-auto flex items-center gap-1"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center ml-2 rounded-lg bg-dl-bg-card/60 border border-dl-border/20 p-0.5"><button><!> <span>Chat</span></button> <button><!> <span>Viewer</span></button></div></div> <div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="종목 검색 (Ctrl+K)"><!></button> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <button><!> <!></button></div> <div class="flex flex-1 min-h-0"><!></div></div></div>  <!> <!> <!> <!>',1);function z2(t,e){Ir(e,!0);let n=K(""),a=K(!1),o=K(null),i=K(Bt({})),s=K(Bt({})),l=K(null),u=K(null),f=K(Bt([])),p=K(!1),_=K(0),x=K(!0),b=K(""),k=K(!1),C=K(null),g=K(Bt({})),y=K(Bt({})),I=K(""),O=K(!1),M=K(null),ee=K(""),fe=K(!1),L=K(""),S=K(0),X=K(null),G=K(null),me=K(null);const V=Fp(),ze=eh();let j=K(!1),B=D(()=>r(j)?"100%":V.panelMode==="viewer"?"65%":"50%"),le=K(!1),we=K(""),U=K(Bt([])),ne=K(-1),N=null,W=K(null),H=K(!1);function E(){v(H,window.innerWidth<=768),r(H)&&(v(p,!1),V.closePanel())}gr(()=>(E(),window.addEventListener("resize",E),()=>window.removeEventListener("resize",E))),gr(()=>{!r(k)||!r(G)||requestAnimationFrame(()=>{var A;return(A=r(G))==null?void 0:A.focus()})}),gr(()=>{!r(q)||!r(me)||requestAnimationFrame(()=>{var A;return(A=r(me))==null?void 0:A.focus()})}),gr(()=>{!r(le)||!r(W)||requestAnimationFrame(()=>{var A;return(A=r(W))==null?void 0:A.focus()})});let q=K(null),J=K(""),Y=K("error"),ye=K(!1);function Se(A,ge="error",We=4e3){v(J,A,!0),v(Y,ge,!0),v(ye,!0),setTimeout(()=>{v(ye,!1)},We)}const te=Op();let Oe=!1;gr(()=>{Oe||(Oe=!0,st())});let tt=K(Bt({}));function ot(A){return A==="chatgpt"?"codex":A}function Ge(A){return`dartlab-api-key:${ot(A)}`}function rt(A){return typeof sessionStorage>"u"||!A?"":sessionStorage.getItem(Ge(A))||""}function dt(A,ge){typeof sessionStorage>"u"||!A||(ge?sessionStorage.setItem(Ge(A),ge):sessionStorage.removeItem(Ge(A)))}async function nt(A,ge=null,We=null){var be;const Me=await Tv(A,ge,We);if(Me!=null&&Me.provider){const De=ot(Me.provider);v(i,{...r(i),[De]:{...r(i)[De]||{},available:!!Me.available,model:Me.model||((be=r(i)[De])==null?void 0:be.model)||ge||null}},!0)}return Me}async function st(){var A,ge,We;v(x,!0);try{const Me=await zv();v(i,Me.providers||{},!0),v(s,Me.ollama||{},!0),v(tt,Me.codex||{},!0),Me.version&&v(b,Me.version,!0);const be=ot(localStorage.getItem("dartlab-provider")),De=localStorage.getItem("dartlab-model"),Ye=rt(be);if(be&&((A=r(i)[be])!=null&&A.available)){v(l,be,!0),v(C,be,!0),v(I,Ye,!0),await xt(be);const ft=r(g)[be]||[];De&&ft.includes(De)?v(u,De,!0):ft.length>0&&(v(u,ft[0],!0),localStorage.setItem("dartlab-model",r(u))),v(f,ft,!0),v(x,!1);return}if(be&&r(i)[be]){if(v(l,be,!0),v(C,be,!0),v(I,Ye,!0),Ye)try{await nt(be,De,Ye)}catch(vt){console.warn("validateProvider:",vt)}await xt(be);const ft=r(g)[be]||[];v(f,ft,!0),De&&ft.includes(De)?v(u,De,!0):ft.length>0&&v(u,ft[0],!0),v(x,!1);return}for(const ft of["codex","ollama","openai"])if((ge=r(i)[ft])!=null&&ge.available){v(l,ft,!0),v(C,ft,!0),v(I,rt(ft),!0),await xt(ft);const vt=r(g)[ft]||[];v(f,vt,!0),v(u,((We=r(i)[ft])==null?void 0:We.model)||(vt.length>0?vt[0]:null),!0),r(u)&&localStorage.setItem("dartlab-model",r(u));break}}catch(Me){console.error("loadStatus:",Me)}v(x,!1)}async function xt(A){A=ot(A),v(y,{...r(y),[A]:!0},!0);try{const ge=await Iv(A);v(g,{...r(g),[A]:ge.models||[]},!0)}catch(ge){console.warn("loadModelsFor:",ge),v(g,{...r(g),[A]:[]},!0)}v(y,{...r(y),[A]:!1},!0)}async function St(A){var We;A=ot(A),v(l,A,!0),v(u,null),v(C,A,!0),localStorage.setItem("dartlab-provider",A),localStorage.removeItem("dartlab-model"),v(I,rt(A),!0),v(M,null),await xt(A);const ge=r(g)[A]||[];if(v(f,ge,!0),ge.length>0&&(v(u,((We=r(i)[A])==null?void 0:We.model)||ge[0],!0),localStorage.setItem("dartlab-model",r(u)),r(I)))try{await nt(A,r(u),r(I))}catch{}}async function Nt(A){v(u,A,!0),localStorage.setItem("dartlab-model",A);const ge=rt(r(l));if(ge)try{await nt(ot(r(l)),A,ge)}catch{}}function lr(A){A=ot(A),r(C)===A?v(C,null):(v(C,A,!0),xt(A))}async function R(){const A=r(I).trim();if(!(!A||!r(l))){v(O,!0),v(M,null);try{const ge=await nt(ot(r(l)),r(u),A);ge.available?(dt(r(l),A),v(M,"success"),!r(u)&&ge.model&&v(u,ge.model,!0),await xt(r(l)),v(f,r(g)[r(l)]||[],!0),Se("API 키 인증 성공","success")):(dt(r(l),""),v(M,"error"))}catch{dt(r(l),""),v(M,"error")}v(O,!1)}}async function pe(){try{await Ev(),r(l)==="codex"&&v(i,{...r(i),codex:{...r(i).codex,available:!1}},!0),Se("Codex 계정 로그아웃 완료","success"),await st()}catch{Se("로그아웃 실패")}}function oe(){const A=r(ee).trim();!A||r(fe)||(v(fe,!0),v(L,"준비 중..."),v(S,0),v(X,Av(A,{onProgress(ge){ge.total&&ge.completed!==void 0?(v(S,Math.round(ge.completed/ge.total*100),!0),v(L,`다운로드 중... ${r(S)}%`)):ge.status&&v(L,ge.status,!0)},async onDone(){v(fe,!1),v(X,null),v(ee,""),v(L,""),v(S,0),Se(`${A} 다운로드 완료`,"success"),await xt("ollama"),v(f,r(g).ollama||[],!0),r(f).includes(A)&&await Nt(A)},onError(ge){v(fe,!1),v(X,null),v(L,""),v(S,0),Se(`다운로드 실패: ${ge}`)}}),!0))}function ce(){r(X)&&(r(X).abort(),v(X,null)),v(fe,!1),v(ee,""),v(L,""),v(S,0)}function w(){v(p,!r(p))}function F(A){V.openData(A)}function re(A,ge=null){V.openEvidence(A,ge)}function ie(A){V.openViewer(A)}function ue(){if(v(I,""),v(M,null),r(l))v(C,r(l),!0);else{const A=Object.keys(r(i));v(C,A.length>0?A[0]:null,!0)}v(k,!0),r(C)&&xt(r(C))}function P(A){var ge,We,Me,be;if(A)for(let De=A.messages.length-1;De>=0;De--){const Ye=A.messages[De];if(Ye.role==="assistant"&&((ge=Ye.meta)!=null&&ge.stockCode||(We=Ye.meta)!=null&&We.company||Ye.company)){V.syncCompanyFromMessage({company:((Me=Ye.meta)==null?void 0:Me.company)||Ye.company,stockCode:(be=Ye.meta)==null?void 0:be.stockCode},V.selectedCompany);return}}}function Z(){te.createConversation(),v(n,""),v(a,!1),r(o)&&(r(o).abort(),v(o,null))}function $e(A){te.setActive(A),P(te.active),v(n,""),v(a,!1),r(o)&&(r(o).abort(),v(o,null))}function ve(A){v(q,A,!0)}function ke(){r(q)&&(te.deleteConversation(r(q)),v(q,null))}function Pe(){var ge;const A=te.active;if(!A)return null;for(let We=A.messages.length-1;We>=0;We--){const Me=A.messages[We];if(Me.role==="assistant"&&((ge=Me.meta)!=null&&ge.stockCode))return Me.meta.stockCode}return null}async function de(A=null){var Wt,cr,kt;const ge=(A??r(n)).trim();if(!ge||r(a))return;if(!r(l)||!((Wt=r(i)[r(l)])!=null&&Wt.available)){Se("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),ue();return}te.activeId||te.createConversation();const We=te.activeId;te.addMessage("user",ge),v(n,""),v(a,!0),te.addMessage("assistant",""),te.updateLastMessage({loading:!0,startedAt:Date.now()}),ts(_);const Me=te.active,be=[];let De=null;if(Me){const Q=Me.messages.slice(0,-2);for(const xe of Q)if((xe.role==="user"||xe.role==="assistant")&&xe.text&&xe.text.trim()&&!xe.error&&!xe.loading){const Fe={role:xe.role,text:xe.text};xe.role==="assistant"&&((cr=xe.meta)!=null&&cr.stockCode)&&(Fe.meta={company:xe.meta.company||xe.company,stockCode:xe.meta.stockCode,modules:xe.meta.includedModules||null,market:xe.meta.market||null,topic:xe.meta.topic||null,topicLabel:xe.meta.topicLabel||null,dialogueMode:xe.meta.dialogueMode||null,questionTypes:xe.meta.questionTypes||null,userGoal:xe.meta.userGoal||null},De=xe.meta.stockCode),be.push(Fe)}}const Ye=((kt=V.selectedCompany)==null?void 0:kt.stockCode)||De||Pe(),ft=V.getViewContext();function vt(){return te.activeId!==We}const It={provider:r(l),model:r(u),viewContext:ft},Gt=rt(r(l));Gt&&(It.api_key=Gt);const Ut=qv(Ye,ge,It,{onMeta(Q){var Rt;if(vt())return;const xe=te.active,Fe=xe==null?void 0:xe.messages[xe.messages.length-1],Ze={meta:{...(Fe==null?void 0:Fe.meta)||{},...Q}};Q.company&&(Ze.company=Q.company,te.activeId&&((Rt=te.active)==null?void 0:Rt.title)==="새 대화"&&te.updateTitle(te.activeId,Q.company)),Q.stockCode&&(Ze.stockCode=Q.stockCode),(Q.company||Q.stockCode)&&V.syncCompanyFromMessage(Q,V.selectedCompany),te.updateLastMessage(Ze)},onSnapshot(Q){vt()||te.updateLastMessage({snapshot:Q})},onContext(Q){if(vt())return;const xe=te.active;if(!xe)return;const Fe=xe.messages[xe.messages.length-1],qe=(Fe==null?void 0:Fe.contexts)||[];te.updateLastMessage({contexts:[...qe,{module:Q.module,label:Q.label,text:Q.text}]})},onSystemPrompt(Q){vt()||te.updateLastMessage({systemPrompt:Q.text,userContent:Q.userContent||null})},onToolCall(Q){if(vt())return;const xe=te.active;if(!xe)return;const Fe=xe.messages[xe.messages.length-1],qe=(Fe==null?void 0:Fe.toolEvents)||[];te.updateLastMessage({toolEvents:[...qe,{type:"call",name:Q.name,arguments:Q.arguments}]})},onToolResult(Q){if(vt())return;const xe=te.active;if(!xe)return;const Fe=xe.messages[xe.messages.length-1],qe=(Fe==null?void 0:Fe.toolEvents)||[];te.updateLastMessage({toolEvents:[...qe,{type:"result",name:Q.name,result:Q.result}]})},onChunk(Q){if(vt())return;const xe=te.active;if(!xe)return;const Fe=xe.messages[xe.messages.length-1];te.updateLastMessage({text:((Fe==null?void 0:Fe.text)||"")+Q}),ts(_)},onDone(){if(vt())return;const Q=te.active,xe=Q==null?void 0:Q.messages[Q.messages.length-1],Fe=xe!=null&&xe.startedAt?((Date.now()-xe.startedAt)/1e3).toFixed(1):null;te.updateLastMessage({loading:!1,duration:Fe}),te.flush(),v(a,!1),v(o,null),ts(_)},onViewerNavigate(Q){vt()||et(Q)},onError(Q,xe,Fe){vt()||(te.updateLastMessage({text:`오류: ${Q}`,loading:!1,error:!0}),te.flush(),Se(xe==="login"?`${Q} — 설정에서 Codex 로그인을 확인하세요`:xe==="install"?`${Q} — 설정에서 Codex 설치 안내를 확인하세요`:Q),v(a,!1),v(o,null))}},be);v(o,Ut,!0)}function Te(){r(o)&&(r(o).abort(),v(o,null),v(a,!1),te.updateLastMessage({loading:!1}),te.flush())}function Re(){const A=te.active;if(!A||A.messages.length<2)return;let ge="";for(let We=A.messages.length-1;We>=0;We--)if(A.messages[We].role==="user"){ge=A.messages[We].text;break}ge&&(te.removeLastMessage(),te.removeLastMessage(),v(n,ge,!0),requestAnimationFrame(()=>{de()}))}function He(){const A=te.active;if(!A)return;let ge=`# ${A.title}

`;for(const De of A.messages)De.role==="user"?ge+=`## You

${De.text}

`:De.role==="assistant"&&De.text&&(ge+=`## DartLab

${De.text}

`);const We=new Blob([ge],{type:"text/markdown;charset=utf-8"}),Me=URL.createObjectURL(We),be=document.createElement("a");be.href=Me,be.download=`${A.title||"dartlab-chat"}.md`,be.click(),URL.revokeObjectURL(Me),Se("대화가 마크다운으로 내보내졌습니다","success")}function _e(A){var Me;V.switchView("chat");const ge=((Me=ze.topicData)==null?void 0:Me.topicLabel)||"",We=ge?`[${ge}] `:"";v(n,`${We}"${A}" — 이 내용에 대해 설명해줘`),requestAnimationFrame(()=>{const be=document.querySelector(".input-textarea");be&&be.focus()})}function et(A){A!=null&&A.topic&&(V.switchView("viewer"),A.chapter&&ze.selectTopic(A.topic,A.chapter))}function Ct(){v(le,!0),v(we,""),v(U,[],!0),v(ne,-1)}function at(A){var Me,be;(A.metaKey||A.ctrlKey)&&A.key==="n"&&(A.preventDefault(),Z()),(A.metaKey||A.ctrlKey)&&A.key==="k"&&(A.preventDefault(),Ct()),(A.metaKey||A.ctrlKey)&&A.shiftKey&&A.key==="S"&&(A.preventDefault(),w()),A.key==="Escape"&&r(le)?v(le,!1):A.key==="Escape"&&r(k)?v(k,!1):A.key==="Escape"&&r(q)?v(q,null):A.key==="Escape"&&V.panelOpen&&V.closePanel();const ge=(Me=A.target)==null?void 0:Me.tagName;if(!(ge==="INPUT"||ge==="TEXTAREA"||((be=A.target)==null?void 0:be.isContentEditable))&&!A.ctrlKey&&!A.metaKey&&!A.altKey){if(A.key==="1"){V.switchView("chat");return}if(A.key==="2"){V.switchView("viewer");return}}}let Dt=D(()=>{var A;return((A=te.active)==null?void 0:A.messages)||[]}),Ve=D(()=>te.active&&te.active.messages.length>0),Ee=D(()=>{var A;return!r(x)&&(!r(l)||!((A=r(i)[r(l)])!=null&&A.available))});const Ie=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var yt=M2();xn("keydown",Ns,at);var Pt=ae(yt),Je=d(Pt);{var At=A=>{var ge=Ib();he("click",ge,()=>{v(p,!1)}),c(A,ge)};$(Je,A=>{r(H)&&r(p)&&A(At)})}var qt=m(Je,2),$t=d(qt);{var Mt=A=>{var ge=Ob(),We=d(ge);{var Me=De=>{var Ye=Pb(),ft=m(d(Ye),2),vt=m(d(ft),2);Ae(vt,17,()=>V.recentCompanies||[],Ne,(Ut,Wt)=>{var cr=Ab(),kt=d(cr),Q=d(kt),xe=m(kt,2),Fe=d(xe);z(()=>{var qe;Ue(cr,1,`w-full text-left px-3 py-2 rounded-lg text-[12px] transition-colors mb-0.5
										${((qe=V.selectedCompany)==null?void 0:qe.stockCode)===r(Wt).stockCode?"bg-dl-accent/10 text-dl-accent-light border border-dl-accent/20":"text-dl-text-muted hover:bg-white/5 hover:text-dl-text"}`),T(Q,r(Wt).name),T(Fe,r(Wt).stockCode)}),he("click",cr,()=>{ie(r(Wt)),r(H)&&v(p,!1)}),c(Ut,cr)},Ut=>{var Wt=Eb();c(Ut,Wt)});var It=m(ft,2);{var Gt=Ut=>{var Wt=Nb(),cr=d(Wt);z(()=>T(cr,`v${r(b)??""}`)),c(Ut,Wt)};$(It,Ut=>{r(b)&&Ut(Gt)})}c(De,Ye)},be=De=>{var Ye=Lb();c(De,Ye)};$(We,De=>{r(p)?De(Me):De(be,-1)})}z(()=>Ue(ge,1,`surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden ${r(p)?"w-[260px]":"w-[52px]"}`)),c(A,ge)},ct=A=>{{let ge=D(()=>r(H)?!0:r(p));Lh(A,{get conversations(){return te.conversations},get activeId(){return te.activeId},get open(){return r(ge)},get version(){return r(b)},onNewChat:()=>{Z(),r(H)&&v(p,!1)},onSelect:We=>{$e(We),r(H)&&v(p,!1)},onDelete:ve,onOpenSearch:Ct})}};$($t,A=>{V.activeView==="viewer"?A(Mt):A(ct,-1)})}var tr=m(qt,2),Mr=d(tr),yr=d(Mr),Br=d(yr);{var zr=A=>{tu(A,{size:18})},_t=A=>{xh(A,{size:18})};$(Br,A=>{r(p)?A(zr):A(_t,-1)})}var Ht=m(yr,2),zt=d(Ht),Lt=d(zt);js(Lt,{size:12});var dr=m(zt,2),ur=d(dr);Di(ur,{size:12});var bt=m(Mr,2),Be=d(bt),rr=d(Be);xa(rr,{size:14});var Cr=m(Be,2),it=d(Cr);zn(it,{size:14});var Le=m(Cr,2),Qe=d(Le);ph(Qe,{size:14});var ut=m(Le,2),Ot=d(ut);uh(Ot,{size:14});var Tt=m(ut,2),gt=d(Tt);{var wt=A=>{var ge=Db(),We=ae(ge);Ur(We,{size:12,class:"animate-spin"}),c(A,ge)},Ft=A=>{var ge=Rb(),We=ae(ge);Ja(We,{size:12}),c(A,ge)},Kt=A=>{var ge=Fb(),We=m(ae(ge),2),Me=d(We),be=m(We,2);{var De=Ye=>{var ft=jb(),vt=m(ae(ft),2),It=d(vt);z(()=>T(It,r(u))),c(Ye,ft)};$(be,Ye=>{r(u)&&Ye(De)})}z(()=>T(Me,r(l))),c(A,ge)};$(gt,A=>{r(x)?A(wt):r(Ee)?A(Ft,1):A(Kt,-1)})}var Xt=m(gt,2);bh(Xt,{size:12});var _r=m(bt,2),Or=d(_r);{var $r=A=>{var ge=Vb(),We=d(ge);Tb(We,{get viewer(){return ze},get company(){return V.selectedCompany},get recentCompanies(){return V.recentCompanies},onCompanySelect:ie,onAskAI:_e,onTopicChange:(Me,be)=>V.setViewerTopic(Me,be)}),c(A,ge)},ar=A=>{var ge=qb(),We=ae(ge),Me=d(We);{var be=vt=>{{let It=D(()=>V.viewerTopic?{topic:V.viewerTopic,topicLabel:V.viewerTopicLabel,period:V.viewerPeriod}:null);qm(vt,{get messages(){return r(Dt)},get isLoading(){return r(a)},get scrollTrigger(){return r(_)},get selectedCompany(){return V.selectedCompany},get viewerContext(){return r(It)},onSend:de,onStop:Te,onRegenerate:Re,onExport:He,onOpenData:F,onOpenEvidence:re,onCompanySelect:ie,get inputText(){return r(n)},set inputText(Gt){v(n,Gt,!0)}})}},De=vt=>{Hh(vt,{onSend:de,onCompanySelect:ie,get inputText(){return r(n)},set inputText(It){v(n,It,!0)}})};$(Me,vt=>{r(Ve)?vt(be):vt(De,-1)})}var Ye=m(We,2);{var ft=vt=>{var It=Bb(),Gt=d(It);x1(Gt,{get mode(){return V.panelMode},get company(){return V.selectedCompany},get data(){return V.panelData},onClose:()=>{v(j,!1),V.closePanel()},onTopicChange:(Ut,Wt)=>V.setViewerTopic(Ut,Wt),onFullscreen:()=>{v(j,!r(j))},get isFullscreen(){return r(j)}}),z(()=>Eo(It,`width: ${r(B)??""}; min-width: 360px; ${r(j)?"":"max-width: 75vw;"}`)),c(vt,It)};$(Ye,vt=>{!r(H)&&V.panelOpen&&vt(ft)})}c(A,ge)};$(Or,A=>{V.activeView==="viewer"?A($r):A(ar,-1)})}var fr=m(Pt,2);{var qr=A=>{var ge=x2(),We=d(ge),Me=d(We),be=d(Me),De=m(d(be),2),Ye=d(De);Fa(Ye,{size:18});var ft=m(Me,2),vt=d(ft);Ae(vt,21,()=>Object.entries(r(i)),Ne,(Q,xe)=>{var Fe=D(()=>Ji(r(xe),2));let qe=()=>r(Fe)[0],Ze=()=>r(Fe)[1];const Rt=D(()=>qe()===r(l)),br=D(()=>r(C)===qe()),or=D(()=>Ze().auth==="api_key"),Er=D(()=>Ze().auth==="cli"),nr=D(()=>r(g)[qe()]||[]),er=D(()=>r(y)[qe()]);var pr=m2(),Nr=d(pr),rn=d(Nr),Pr=m(rn,2),Hr=d(Pr),In=d(Hr),Ha=d(In),jn=m(In,2);{var Ua=Sr=>{var sn=Hb();c(Sr,sn)};$(jn,Sr=>{r(Rt)&&Sr(Ua)})}var Ro=m(Hr,2),jo=d(Ro),Fo=m(Pr,2),on=d(Fo);{var bn=Sr=>{as(Sr,{size:16,class:"text-dl-success"})},fa=Sr=>{var sn=Ub(),wa=ae(sn);id(wa,{size:14,class:"text-amber-400"}),c(Sr,sn)},fu=Sr=>{var sn=Wb(),wa=ae(sn);Ja(wa,{size:14,class:"text-amber-400"}),c(Sr,sn)},vu=Sr=>{var sn=Kb(),wa=ae(sn);kh(wa,{size:14,class:"text-dl-text-dim"}),c(Sr,sn)};$(on,Sr=>{Ze().available?Sr(bn):r(or)?Sr(fa,1):r(Er)&&qe()==="codex"&&r(tt).installed?Sr(fu,2):r(Er)&&!Ze().available&&Sr(vu,3)})}var pu=m(Nr,2);{var hu=Sr=>{var sn=h2(),wa=ae(sn);{var mu=mr=>{var Lr=Jb(),Gr=d(Lr),ln=d(Gr),An=m(Gr,2),nn=d(An),wn=m(nn,2),ya=d(wn);{var ka=sr=>{Ur(sr,{size:12,class:"animate-spin"})},yn=sr=>{id(sr,{size:12})};$(ya,sr=>{r(O)?sr(ka):sr(yn,-1)})}var Fn=m(An,2);{var kr=sr=>{var kn=Gb(),Jr=d(kn);Ja(Jr,{size:12}),c(sr,kn)};$(Fn,sr=>{r(M)==="error"&&sr(kr)})}z(sr=>{T(ln,Ze().envKey?`환경변수 ${Ze().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),ir(nn,"placeholder",qe()==="openai"?"sk-...":qe()==="claude"?"sk-ant-...":"API Key"),wn.disabled=sr},[()=>!r(I).trim()||r(O)]),he("keydown",nn,sr=>{sr.key==="Enter"&&R()}),Ea(nn,()=>r(I),sr=>v(I,sr)),he("click",wn,R),c(mr,Lr)};$(wa,mr=>{r(or)&&!Ze().available&&mr(mu)})}var hl=m(wa,2);{var xu=mr=>{var Lr=Xb(),Gr=d(Lr),ln=d(Gr);as(ln,{size:13,class:"text-dl-success"});var An=m(Gr,2),nn=d(An),wn=m(nn,2);{var ya=yn=>{var Fn=Yb(),kr=d(Fn);{var sr=Jr=>{Ur(Jr,{size:10,class:"animate-spin"})},kn=Jr=>{var Zn=oa("변경");c(Jr,Zn)};$(kr,Jr=>{r(O)?Jr(sr):Jr(kn,-1)})}z(()=>Fn.disabled=r(O)),he("click",Fn,R),c(yn,Fn)},ka=D(()=>r(I).trim());$(wn,yn=>{r(ka)&&yn(ya)})}he("keydown",nn,yn=>{yn.key==="Enter"&&R()}),Ea(nn,()=>r(I),yn=>v(I,yn)),c(mr,Lr)};$(hl,mr=>{r(or)&&Ze().available&&mr(xu)})}var ml=m(hl,2);{var gu=mr=>{var Lr=Qb(),Gr=m(d(Lr),2),ln=d(Gr);os(ln,{size:14});var An=m(ln,2);sd(An,{size:10,class:"ml-auto"}),c(mr,Lr)},_u=mr=>{var Lr=Zb(),Gr=d(Lr),ln=d(Gr);Ja(ln,{size:14}),c(mr,Lr)};$(ml,mr=>{qe()==="ollama"&&!r(s).installed?mr(gu):qe()==="ollama"&&r(s).installed&&!r(s).running&&mr(_u,1)})}var xl=m(ml,2);{var bu=mr=>{var Lr=n2(),Gr=d(Lr);{var ln=wn=>{var ya=r2(),ka=ae(ya),yn=d(ka),Fn=m(ka,2),kr=d(Fn);{var sr=Cn=>{var ea=e2();c(Cn,ea)};$(kr,Cn=>{r(tt).installed||Cn(sr)})}var kn=m(kr,2),Jr=d(kn),Zn=d(Jr),Wa=m(Fn,2);{var Vo=Cn=>{var ea=t2(),Ca=d(ea);z(()=>T(Ca,r(tt).loginStatus)),c(Cn,ea)};$(Wa,Cn=>{r(tt).loginStatus&&Cn(Vo)})}var Bo=m(Wa,2),fn=d(Bo);Ja(fn,{size:12,class:"text-amber-400 flex-shrink-0"}),z(()=>{T(yn,r(tt).installed?"Codex CLI가 설치되었지만 로그인이 필요합니다":"Codex CLI 설치가 필요합니다"),T(Zn,r(tt).installed?"1.":"2.")}),c(wn,ya)};$(Gr,wn=>{qe()==="codex"&&wn(ln)})}var An=m(Gr,2),nn=d(An);z(()=>T(nn,r(tt).installed?"로그인 완료 후 새로고침하세요":"설치 완료 후 새로고침하세요")),c(mr,Lr)};$(xl,mr=>{r(Er)&&!Ze().available&&mr(bu)})}var gl=m(xl,2);{var wu=mr=>{var Lr=a2(),Gr=d(Lr),ln=d(Gr),An=d(ln);as(An,{size:13,class:"text-dl-success"});var nn=m(ln,2),wn=d(nn);mh(wn,{size:11}),he("click",nn,pe),c(mr,Lr)};$(gl,mr=>{qe()==="codex"&&Ze().available&&mr(wu)})}var yu=m(gl,2);{var ku=mr=>{var Lr=p2(),Gr=d(Lr),ln=m(d(Gr),2);{var An=kr=>{Ur(kr,{size:12,class:"animate-spin text-dl-text-dim"})};$(ln,kr=>{r(er)&&kr(An)})}var nn=m(Gr,2);{var wn=kr=>{var sr=o2(),kn=d(sr);Ur(kn,{size:14,class:"animate-spin"}),c(kr,sr)},ya=kr=>{var sr=i2();Ae(sr,21,()=>r(nr),Ne,(kn,Jr)=>{var Zn=s2(),Wa=d(Zn),Vo=m(Wa);{var Bo=fn=>{Ri(fn,{size:10,class:"inline ml-1"})};$(Vo,fn=>{r(Jr)===r(u)&&r(Rt)&&fn(Bo)})}z(fn=>{Ue(Zn,1,fn),T(Wa,`${r(Jr)??""} `)},[()=>xr(wr("px-3 py-1.5 rounded-lg text-[11px] border transition-all",r(Jr)===r(u)&&r(Rt)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),he("click",Zn,()=>{qe()!==r(l)&&St(qe()),Nt(r(Jr))}),c(kn,Zn)}),c(kr,sr)},ka=kr=>{var sr=l2();c(kr,sr)};$(nn,kr=>{r(er)&&r(nr).length===0?kr(wn):r(nr).length>0?kr(ya,1):kr(ka,-1)})}var yn=m(nn,2);{var Fn=kr=>{var sr=v2(),kn=d(sr),Jr=m(d(kn),2),Zn=m(d(Jr));sd(Zn,{size:9});var Wa=m(kn,2);{var Vo=fn=>{var Cn=d2(),ea=d(Cn),Ca=d(ea),qo=d(Ca);Ur(qo,{size:12,class:"animate-spin text-dl-primary-light"});var Xs=m(Ca,2),gs=m(ea,2),va=d(gs),Vn=m(gs,2),Qs=d(Vn);z(()=>{Eo(va,`width: ${r(S)??""}%`),T(Qs,r(L))}),he("click",Xs,ce),c(fn,Cn)},Bo=fn=>{var Cn=f2(),ea=ae(Cn),Ca=d(ea),qo=m(Ca,2),Xs=d(qo);os(Xs,{size:12});var gs=m(ea,2);Ae(gs,21,()=>Ie,Ne,(va,Vn)=>{const Qs=D(()=>r(nr).some(ho=>ho===r(Vn).name||ho===r(Vn).name.split(":")[0]));var _l=Ce(),Cu=ae(_l);{var $u=ho=>{var Zs=u2(),bl=d(Zs),wl=d(bl),yl=d(wl),Su=d(yl),kl=m(yl,2),Mu=d(kl),zu=m(kl,2);{var Tu=ei=>{var $l=c2(),Lu=d($l);z(()=>T(Lu,r(Vn).tag)),c(ei,$l)};$(zu,ei=>{r(Vn).tag&&ei(Tu)})}var Iu=m(wl,2),Au=d(Iu),Eu=m(bl,2),Cl=d(Eu),Nu=d(Cl),Pu=m(Cl,2);os(Pu,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),z(()=>{T(Su,r(Vn).name),T(Mu,r(Vn).size),T(Au,r(Vn).desc),T(Nu,`${r(Vn).gb??""} GB`)}),he("click",Zs,()=>{v(ee,r(Vn).name,!0),oe()}),c(ho,Zs)};$(Cu,ho=>{r(Qs)||ho($u)})}c(va,_l)}),z(va=>qo.disabled=va,[()=>!r(ee).trim()]),he("keydown",Ca,va=>{va.key==="Enter"&&oe()}),Ea(Ca,()=>r(ee),va=>v(ee,va)),he("click",qo,oe),c(fn,Cn)};$(Wa,fn=>{r(fe)?fn(Vo):fn(Bo,-1)})}c(kr,sr)};$(yn,kr=>{qe()==="ollama"&&kr(Fn)})}c(mr,Lr)};$(yu,mr=>{(Ze().available||r(or)||r(Er))&&mr(ku)})}c(Sr,sn)};$(pu,Sr=>{(r(br)||r(Rt))&&Sr(hu)})}z((Sr,sn)=>{Ue(pr,1,Sr),Ue(rn,1,sn),T(Ha,Ze().label||qe()),T(jo,Ze().desc||"")},[()=>xr(wr("rounded-xl border transition-all",r(Rt)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>xr(wr("w-2.5 h-2.5 rounded-full flex-shrink-0",Ze().available?"bg-dl-success":r(or)?"bg-amber-400":"bg-dl-text-dim"))]),he("click",Nr,()=>{Ze().available||r(or)?qe()===r(l)?lr(qe()):St(qe()):lr(qe())}),c(Q,pr)});var It=m(ft,2),Gt=d(It),Ut=d(Gt);{var Wt=Q=>{var xe=oa();z(()=>{var Fe;return T(xe,`현재: ${(((Fe=r(i)[r(l)])==null?void 0:Fe.label)||r(l))??""} / ${r(u)??""}`)}),c(Q,xe)},cr=Q=>{var xe=oa();z(()=>{var Fe;return T(xe,`현재: ${(((Fe=r(i)[r(l)])==null?void 0:Fe.label)||r(l))??""}`)}),c(Q,xe)};$(Ut,Q=>{r(l)&&r(u)?Q(Wt):r(l)&&Q(cr,1)})}var kt=m(Gt,2);Jn(We,Q=>v(G,Q),()=>r(G)),he("click",ge,Q=>{Q.target===Q.currentTarget&&v(k,!1)}),he("click",De,()=>v(k,!1)),he("click",kt,()=>v(k,!1)),c(A,ge)};$(fr,A=>{r(k)&&A(qr)})}var Zt=m(fr,2);{var hr=A=>{var ge=g2(),We=d(ge),Me=m(d(We),4),be=d(Me),De=m(be,2);Jn(We,Ye=>v(me,Ye),()=>r(me)),he("click",ge,Ye=>{Ye.target===Ye.currentTarget&&v(q,null)}),he("click",be,()=>v(q,null)),he("click",De,ke),c(A,ge)};$(Zt,A=>{r(q)&&A(hr)})}var vr=m(Zt,2);{var _n=A=>{const ge=D(()=>V.recentCompanies||[]);var We=$2(),Me=d(We),be=d(Me),De=d(be);xa(De,{size:18,class:"text-dl-text-dim flex-shrink-0"});var Ye=m(De,2);Jn(Ye,Q=>v(W,Q),()=>r(W));var ft=m(be,2),vt=d(ft);{var It=Q=>{var xe=b2(),Fe=m(ae(xe),2);Ae(Fe,17,()=>r(U),Ne,(qe,Ze,Rt)=>{var br=_2(),or=d(br),Er=d(or),nr=m(or,2),er=d(nr),pr=d(er),Nr=m(er,2),rn=d(Nr),Pr=m(nr,2),Hr=m(d(Pr),2);zn(Hr,{size:14,class:"text-dl-text-dim"}),z((In,Ha)=>{Ue(br,1,In),T(Er,Ha),T(pr,r(Ze).corpName),T(rn,`${r(Ze).stockCode??""} · ${(r(Ze).market||"")??""}${r(Ze).sector?` · ${r(Ze).sector}`:""}`)},[()=>xr(wr("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",Rt===r(ne)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(r(Ze).corpName||"?").charAt(0)]),he("click",br,()=>{v(le,!1),v(we,""),v(U,[],!0),v(ne,-1),ie(r(Ze))}),xn("mouseenter",br,()=>{v(ne,Rt,!0)}),c(qe,br)}),c(Q,xe)},Gt=Q=>{var xe=y2(),Fe=m(ae(xe),2);Ae(Fe,17,()=>r(ge),Ne,(qe,Ze,Rt)=>{var br=w2(),or=d(br),Er=d(or),nr=m(or,2),er=d(nr),pr=d(er),Nr=m(er,2),rn=d(Nr);z((Pr,Hr)=>{Ue(br,1,Pr),T(Er,Hr),T(pr,r(Ze).corpName),T(rn,`${r(Ze).stockCode??""} · ${(r(Ze).market||"")??""}`)},[()=>xr(wr("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",Rt===r(ne)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(r(Ze).corpName||"?").charAt(0)]),he("click",br,()=>{v(le,!1),v(we,""),v(ne,-1),ie(r(Ze))}),xn("mouseenter",br,()=>{v(ne,Rt,!0)}),c(qe,br)}),c(Q,xe)},Ut=D(()=>r(we).trim().length===0&&r(ge).length>0),Wt=Q=>{var xe=k2();c(Q,xe)},cr=D(()=>r(we).trim().length>0),kt=Q=>{var xe=C2(),Fe=d(xe);xa(Fe,{size:24,class:"mb-2 opacity-40"}),c(Q,xe)};$(vt,Q=>{r(U).length>0?Q(It):r(Ut)?Q(Gt,1):r(cr)?Q(Wt,2):Q(kt,-1)})}he("click",We,Q=>{Q.target===Q.currentTarget&&v(le,!1)}),he("input",Ye,()=>{N&&clearTimeout(N),r(we).trim().length>=1?N=setTimeout(async()=>{var Q;try{const xe=await sl(r(we).trim());v(U,((Q=xe.results)==null?void 0:Q.slice(0,8))||[],!0)}catch{v(U,[],!0)}},250):v(U,[],!0)}),he("keydown",Ye,Q=>{const xe=r(U).length>0?r(U):r(ge);if(Q.key==="ArrowDown")Q.preventDefault(),v(ne,Math.min(r(ne)+1,xe.length-1),!0);else if(Q.key==="ArrowUp")Q.preventDefault(),v(ne,Math.max(r(ne)-1,-1),!0);else if(Q.key==="Enter"&&r(ne)>=0&&xe[r(ne)]){Q.preventDefault();const Fe=xe[r(ne)];v(le,!1),v(we,""),v(U,[],!0),v(ne,-1),ie(Fe)}else Q.key==="Escape"&&v(le,!1)}),Ea(Ye,()=>r(we),Q=>v(we,Q)),c(A,We)};$(vr,A=>{r(le)&&A(_n)})}var an=m(vr,2);{var Tn=A=>{var ge=S2(),We=d(ge),Me=d(We),be=d(Me),De=m(Me,2),Ye=d(De);Fa(Ye,{size:14}),z(ft=>{Ue(We,1,ft),T(be,r(J))},[()=>xr(wr("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",r(Y)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":r(Y)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),he("click",De,()=>{v(ye,!1)}),c(A,ge)};$(an,A=>{r(ye)&&A(Tn)})}z(A=>{Ue(qt,1,xr(r(H)?r(p)?"sidebar-mobile":"hidden":"")),Ue(zt,1,`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors ${V.activeView==="chat"?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-dim hover:text-dl-text-muted"}`),Ue(dr,1,`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors ${V.activeView==="viewer"?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-dim hover:text-dl-text-muted"}`),Ue(Tt,1,A)},[()=>xr(wr("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",r(x)?"text-dl-text-dim":r(Ee)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),he("click",yr,w),he("click",zt,()=>V.switchView("chat")),he("click",dr,()=>V.switchView("viewer")),he("click",Be,Ct),he("click",Tt,()=>ue()),c(t,yt),Ar()}Kr(["click","keydown","input"]);ov(z2,{target:document.getElementById("app")});export{qi as C,Bi as _,je as a,c as b,Ce as c,Ar as d,h as e,ae as f,d as g,Ti as h,$ as i,Ao as j,r as k,T as l,m,ir as n,Ae as o,Ir as p,Ne as q,ms as r,Ue as s,z as t,D as u,Eo as v};
