const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/ChartRenderer-DBJQ3K0G.js","assets/ChartRenderer-DW5VYfwI.css"])))=>i.map(i=>d[i]);
var Zu=Object.defineProperty;var Rl=t=>{throw TypeError(t)};var ef=(t,e,r)=>e in t?Zu(t,e,{enumerable:!0,configurable:!0,writable:!0,value:r}):t[e]=r;var Et=(t,e,r)=>ef(t,typeof e!="symbol"?e+"":e,r),li=(t,e,r)=>e.has(t)||Rl("Cannot "+r);var oe=(t,e,r)=>(li(t,e,"read from private field"),r?r.call(t):e.get(t)),Zt=(t,e,r)=>e.has(t)?Rl("Cannot add the same private member more than once"):e instanceof WeakSet?e.add(t):e.set(t,r),Vt=(t,e,r,a)=>(li(t,e,"write to private field"),a?a.call(t,r):e.set(t,r),r),Fr=(t,e,r)=>(li(t,e,"access private method"),r);(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))a(s);new MutationObserver(s=>{for(const o of s)if(o.type==="childList")for(const i of o.addedNodes)i.tagName==="LINK"&&i.rel==="modulepreload"&&a(i)}).observe(document,{childList:!0,subtree:!0});function r(s){const o={};return s.integrity&&(o.integrity=s.integrity),s.referrerPolicy&&(o.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?o.credentials="include":s.crossOrigin==="anonymous"?o.credentials="omit":o.credentials="same-origin",o}function a(s){if(s.ep)return;s.ep=!0;const o=r(s);fetch(s.href,o)}})();const wi=!1;var nl=Array.isArray,tf=Array.prototype.indexOf,Ms=Array.prototype.includes,Jo=Array.from,rf=Object.defineProperty,Da=Object.getOwnPropertyDescriptor,Nd=Object.getOwnPropertyDescriptors,nf=Object.prototype,af=Array.prototype,al=Object.getPrototypeOf,Fl=Object.isExtensible;function Hs(t){return typeof t=="function"}const sf=()=>{};function of(t){return typeof(t==null?void 0:t.then)=="function"}function lf(t){return t()}function ki(t){for(var e=0;e<t.length;e++)t[e]()}function Pd(){var t,e,r=new Promise((a,s)=>{t=a,e=s});return{promise:r,resolve:t,reject:e}}function sl(t,e){if(Array.isArray(t))return t;if(!(Symbol.iterator in t))return Array.from(t);const r=[];for(const a of t)if(r.push(a),r.length===e)break;return r}const rn=2,Ns=4,ls=8,Xo=1<<24,Ua=16,Qn=32,fs=64,Si=128,On=512,Zr=1024,en=2048,Xn=4096,un=8192,da=16384,Ps=32768,ya=65536,jl=1<<17,df=1<<18,Ds=1<<19,Dd=1<<20,ia=1<<25,ds=65536,Ci=1<<21,ol=1<<22,Oa=1<<23,ca=Symbol("$state"),Od=Symbol("legacy props"),cf=Symbol(""),Xa=new class extends Error{constructor(){super(...arguments);Et(this,"name","StaleReactionError");Et(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var Id;const Rd=!!((Id=globalThis.document)!=null&&Id.contentType)&&globalThis.document.contentType.includes("xml");function uf(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function ff(t,e,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function vf(t){throw new Error("https://svelte.dev/e/effect_in_teardown")}function pf(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function hf(t){throw new Error("https://svelte.dev/e/effect_orphan")}function mf(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function xf(t){throw new Error("https://svelte.dev/e/props_invalid_value")}function gf(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function _f(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function bf(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function yf(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const wf=1,kf=2,Fd=4,Sf=8,Cf=16,$f=1,Mf=2,jd=4,Tf=8,zf=16,Bd=1,Ef=2,Br=Symbol(),Vd="http://www.w3.org/1999/xhtml",Ud="http://www.w3.org/2000/svg",If="http://www.w3.org/1998/Math/MathML",Af="@attach";function Lf(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function Nf(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Hd(t){return t===this.v}function Pf(t,e){return t!=t?e==e:t!==e||t!==null&&typeof t=="object"||typeof t=="function"}function qd(t){return!Pf(t,this.v)}let mo=!1,Df=!1;function Of(){mo=!0}let Wr=null;function Ts(t){Wr=t}function Ir(t,e=!1,r){Wr={p:Wr,i:!1,c:null,e:null,s:t,x:null,l:mo&&!e?{s:null,u:null,$:[]}:null}}function Ar(t){var e=Wr,r=e.e;if(r!==null){e.e=null;for(var a of r)pc(a)}return e.i=!0,Wr=e.p,{}}function Os(){return!mo||Wr!==null&&Wr.l===null}let Qa=[];function Kd(){var t=Qa;Qa=[],ki(t)}function Yn(t){if(Qa.length===0&&!xs){var e=Qa;queueMicrotask(()=>{e===Qa&&Kd()})}Qa.push(t)}function Rf(){for(;Qa.length>0;)Kd()}function Wd(t){var e=Xt;if(e===null)return Jt.f|=Oa,t;if((e.f&Ps)===0&&(e.f&Ns)===0)throw t;Aa(t,e)}function Aa(t,e){for(;e!==null;){if((e.f&Si)!==0){if((e.f&Ps)===0)throw t;try{e.b.error(t);return}catch(r){t=r}}e=e.parent}throw t}const Ff=-7169;function Er(t,e){t.f=t.f&Ff|e}function il(t){(t.f&On)!==0||t.deps===null?Er(t,Zr):Er(t,Xn)}function Gd(t){if(t!==null)for(const e of t)(e.f&rn)===0||(e.f&ds)===0||(e.f^=ds,Gd(e.deps))}function Yd(t,e,r){(t.f&en)!==0?e.add(t):(t.f&Xn)!==0&&r.add(t),Gd(t.deps),Er(t,Zr)}const ko=new Set;let Lt=null,Do=null,Qr=null,hn=[],Qo=null,xs=!1,zs=null,jf=1;var za,_s,ts,bs,ys,ws,Ea,ra,ks,_n,$i,Mi,Ti,zi;const $l=class $l{constructor(){Zt(this,_n);Et(this,"id",jf++);Et(this,"current",new Map);Et(this,"previous",new Map);Zt(this,za,new Set);Zt(this,_s,new Set);Zt(this,ts,0);Zt(this,bs,0);Zt(this,ys,null);Zt(this,ws,new Set);Zt(this,Ea,new Set);Zt(this,ra,new Map);Et(this,"is_fork",!1);Zt(this,ks,!1)}skip_effect(e){oe(this,ra).has(e)||oe(this,ra).set(e,{d:[],m:[]})}unskip_effect(e){var r=oe(this,ra).get(e);if(r){oe(this,ra).delete(e);for(var a of r.d)Er(a,en),la(a);for(a of r.m)Er(a,Xn),la(a)}}process(e){var s;hn=[],this.apply();var r=zs=[],a=[];for(const o of e)Fr(this,_n,Mi).call(this,o,r,a);if(zs=null,Fr(this,_n,$i).call(this)){Fr(this,_n,Ti).call(this,a),Fr(this,_n,Ti).call(this,r);for(const[o,i]of oe(this,ra))ec(o,i)}else{Do=this,Lt=null;for(const o of oe(this,za))o(this);oe(this,za).clear(),oe(this,ts)===0&&Fr(this,_n,zi).call(this),Bl(a),Bl(r),oe(this,ws).clear(),oe(this,Ea).clear(),Do=null,(s=oe(this,ys))==null||s.resolve()}Qr=null}capture(e,r){r!==Br&&!this.previous.has(e)&&this.previous.set(e,r),(e.f&Oa)===0&&(this.current.set(e,e.v),Qr==null||Qr.set(e,e.v))}activate(){Lt=this,this.apply()}deactivate(){Lt===this&&(Lt=null,Qr=null)}flush(){var e;if(hn.length>0)Lt=this,Xd();else if(oe(this,ts)===0&&!this.is_fork){for(const r of oe(this,za))r(this);oe(this,za).clear(),Fr(this,_n,zi).call(this),(e=oe(this,ys))==null||e.resolve()}this.deactivate()}discard(){for(const e of oe(this,_s))e(this);oe(this,_s).clear()}increment(e){Vt(this,ts,oe(this,ts)+1),e&&Vt(this,bs,oe(this,bs)+1)}decrement(e){Vt(this,ts,oe(this,ts)-1),e&&Vt(this,bs,oe(this,bs)-1),!oe(this,ks)&&(Vt(this,ks,!0),Yn(()=>{Vt(this,ks,!1),Fr(this,_n,$i).call(this)?hn.length>0&&this.flush():this.revive()}))}revive(){for(const e of oe(this,ws))oe(this,Ea).delete(e),Er(e,en),la(e);for(const e of oe(this,Ea))Er(e,Xn),la(e);this.flush()}oncommit(e){oe(this,za).add(e)}ondiscard(e){oe(this,_s).add(e)}settled(){return(oe(this,ys)??Vt(this,ys,Pd())).promise}static ensure(){if(Lt===null){const e=Lt=new $l;ko.add(Lt),xs||Yn(()=>{Lt===e&&e.flush()})}return Lt}apply(){}};za=new WeakMap,_s=new WeakMap,ts=new WeakMap,bs=new WeakMap,ys=new WeakMap,ws=new WeakMap,Ea=new WeakMap,ra=new WeakMap,ks=new WeakMap,_n=new WeakSet,$i=function(){return this.is_fork||oe(this,bs)>0},Mi=function(e,r,a){e.f^=Zr;for(var s=e.first;s!==null;){var o=s.f,i=(o&(Qn|fs))!==0,l=i&&(o&Zr)!==0,u=(o&un)!==0,f=l||oe(this,ra).has(s);if(!f&&s.fn!==null){i?u||(s.f^=Zr):(o&Ns)!==0?r.push(s):(o&(ls|Xo))!==0&&u?a.push(s):_o(s)&&(Es(s),(o&Ua)!==0&&(oe(this,Ea).add(s),u&&Er(s,en)));var p=s.first;if(p!==null){s=p;continue}}for(;s!==null;){var g=s.next;if(g!==null){s=g;break}s=s.parent}}},Ti=function(e){for(var r=0;r<e.length;r+=1)Yd(e[r],oe(this,ws),oe(this,Ea))},zi=function(){var o;if(ko.size>1){this.previous.clear();var e=Lt,r=Qr,a=!0;for(const i of ko){if(i===this){a=!1;continue}const l=[];for(const[f,p]of this.current){if(i.current.has(f))if(a&&p!==i.current.get(f))i.current.set(f,p);else continue;l.push(f)}if(l.length===0)continue;const u=[...i.current.keys()].filter(f=>!this.current.has(f));if(u.length>0){var s=hn;hn=[];const f=new Set,p=new Map;for(const g of l)Qd(g,u,f,p);if(hn.length>0){Lt=i,i.apply();for(const g of hn)Fr(o=i,_n,Mi).call(o,g,[],[]);i.deactivate()}hn=s}}Lt=e,Qr=r}oe(this,ra).clear(),ko.delete(this)};let _a=$l;function Jd(t){var e=xs;xs=!0;try{for(var r;;){if(Rf(),hn.length===0&&(Lt==null||Lt.flush(),hn.length===0))return Qo=null,r;Xd()}}finally{xs=e}}function Xd(){var t=null;try{for(var e=0;hn.length>0;){var r=_a.ensure();if(e++>1e3){var a,s;Bf()}r.process(hn),Ra.clear()}}finally{hn=[],Qo=null,zs=null}}function Bf(){try{mf()}catch(t){Aa(t,Qo)}}let Hn=null;function Bl(t){var e=t.length;if(e!==0){for(var r=0;r<e;){var a=t[r++];if((a.f&(da|un))===0&&_o(a)&&(Hn=new Set,Es(a),a.deps===null&&a.first===null&&a.nodes===null&&a.teardown===null&&a.ac===null&&gc(a),(Hn==null?void 0:Hn.size)>0)){Ra.clear();for(const s of Hn){if((s.f&(da|un))!==0)continue;const o=[s];let i=s.parent;for(;i!==null;)Hn.has(i)&&(Hn.delete(i),o.push(i)),i=i.parent;for(let l=o.length-1;l>=0;l--){const u=o[l];(u.f&(da|un))===0&&Es(u)}}Hn.clear()}}Hn=null}}function Qd(t,e,r,a){if(!r.has(t)&&(r.add(t),t.reactions!==null))for(const s of t.reactions){const o=s.f;(o&rn)!==0?Qd(s,e,r,a):(o&(ol|Ua))!==0&&(o&en)===0&&Zd(s,e,a)&&(Er(s,en),la(s))}}function Zd(t,e,r){const a=r.get(t);if(a!==void 0)return a;if(t.deps!==null)for(const s of t.deps){if(Ms.call(e,s))return!0;if((s.f&rn)!==0&&Zd(s,e,r))return r.set(s,!0),!0}return r.set(t,!1),!1}function la(t){var e=Qo=t,r=e.b;if(r!=null&&r.is_pending&&(t.f&(Ns|ls|Xo))!==0&&(t.f&Ps)===0){r.defer_effect(t);return}for(;e.parent!==null;){e=e.parent;var a=e.f;if(zs!==null&&e===Xt&&(t.f&ls)===0)return;if((a&(fs|Qn))!==0){if((a&Zr)===0)return;e.f^=Zr}}hn.push(e)}function ec(t,e){if(!((t.f&Qn)!==0&&(t.f&Zr)!==0)){(t.f&en)!==0?e.d.push(t):(t.f&Xn)!==0&&e.m.push(t),Er(t,Zr);for(var r=t.first;r!==null;)ec(r,e),r=r.next}}function Vf(t){let e=0,r=fa(0),a;return()=>{ul()&&(n(r),fl(()=>(e===0&&(a=cs(()=>t(()=>ao(r)))),e+=1,()=>{Yn(()=>{e-=1,e===0&&(a==null||a(),a=void 0,ao(r))})})))}}var Uf=ya|Ds;function Hf(t,e,r,a){new qf(t,e,r,a)}var Pn,rl,na,rs,pn,aa,Mn,qn,ma,ns,Ia,Ss,Cs,$s,xa,Wo,Vr,Kf,Wf,Gf,Ei,Io,Ao,Ii;class qf{constructor(e,r,a,s){Zt(this,Vr);Et(this,"parent");Et(this,"is_pending",!1);Et(this,"transform_error");Zt(this,Pn);Zt(this,rl,null);Zt(this,na);Zt(this,rs);Zt(this,pn);Zt(this,aa,null);Zt(this,Mn,null);Zt(this,qn,null);Zt(this,ma,null);Zt(this,ns,0);Zt(this,Ia,0);Zt(this,Ss,!1);Zt(this,Cs,new Set);Zt(this,$s,new Set);Zt(this,xa,null);Zt(this,Wo,Vf(()=>(Vt(this,xa,fa(oe(this,ns))),()=>{Vt(this,xa,null)})));var o;Vt(this,Pn,e),Vt(this,na,r),Vt(this,rs,i=>{var l=Xt;l.b=this,l.f|=Si,a(i)}),this.parent=Xt.b,this.transform_error=s??((o=this.parent)==null?void 0:o.transform_error)??(i=>i),Vt(this,pn,vs(()=>{Fr(this,Vr,Ei).call(this)},Uf))}defer_effect(e){Yd(e,oe(this,Cs),oe(this,$s))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!oe(this,na).pending}update_pending_count(e){Fr(this,Vr,Ii).call(this,e),Vt(this,ns,oe(this,ns)+e),!(!oe(this,xa)||oe(this,Ss))&&(Vt(this,Ss,!0),Yn(()=>{Vt(this,Ss,!1),oe(this,xa)&&ba(oe(this,xa),oe(this,ns))}))}get_effect_pending(){return oe(this,Wo).call(this),n(oe(this,xa))}error(e){var r=oe(this,na).onerror;let a=oe(this,na).failed;if(!r&&!a)throw e;oe(this,aa)&&(tn(oe(this,aa)),Vt(this,aa,null)),oe(this,Mn)&&(tn(oe(this,Mn)),Vt(this,Mn,null)),oe(this,qn)&&(tn(oe(this,qn)),Vt(this,qn,null));var s=!1,o=!1;const i=()=>{if(s){Nf();return}s=!0,o&&yf(),oe(this,qn)!==null&&ss(oe(this,qn),()=>{Vt(this,qn,null)}),Fr(this,Vr,Ao).call(this,()=>{_a.ensure(),Fr(this,Vr,Ei).call(this)})},l=u=>{try{o=!0,r==null||r(u,i),o=!1}catch(f){Aa(f,oe(this,pn)&&oe(this,pn).parent)}a&&Vt(this,qn,Fr(this,Vr,Ao).call(this,()=>{_a.ensure();try{return xn(()=>{var f=Xt;f.b=this,f.f|=Si,a(oe(this,Pn),()=>u,()=>i)})}catch(f){return Aa(f,oe(this,pn).parent),null}}))};Yn(()=>{var u;try{u=this.transform_error(e)}catch(f){Aa(f,oe(this,pn)&&oe(this,pn).parent);return}u!==null&&typeof u=="object"&&typeof u.then=="function"?u.then(l,f=>Aa(f,oe(this,pn)&&oe(this,pn).parent)):l(u)})}}Pn=new WeakMap,rl=new WeakMap,na=new WeakMap,rs=new WeakMap,pn=new WeakMap,aa=new WeakMap,Mn=new WeakMap,qn=new WeakMap,ma=new WeakMap,ns=new WeakMap,Ia=new WeakMap,Ss=new WeakMap,Cs=new WeakMap,$s=new WeakMap,xa=new WeakMap,Wo=new WeakMap,Vr=new WeakSet,Kf=function(){try{Vt(this,aa,xn(()=>oe(this,rs).call(this,oe(this,Pn))))}catch(e){this.error(e)}},Wf=function(e){const r=oe(this,na).failed;r&&Vt(this,qn,xn(()=>{r(oe(this,Pn),()=>e,()=>()=>{})}))},Gf=function(){const e=oe(this,na).pending;e&&(this.is_pending=!0,Vt(this,Mn,xn(()=>e(oe(this,Pn)))),Yn(()=>{var r=Vt(this,ma,document.createDocumentFragment()),a=ua();r.append(a),Vt(this,aa,Fr(this,Vr,Ao).call(this,()=>(_a.ensure(),xn(()=>oe(this,rs).call(this,a))))),oe(this,Ia)===0&&(oe(this,Pn).before(r),Vt(this,ma,null),ss(oe(this,Mn),()=>{Vt(this,Mn,null)}),Fr(this,Vr,Io).call(this))}))},Ei=function(){try{if(this.is_pending=this.has_pending_snippet(),Vt(this,Ia,0),Vt(this,ns,0),Vt(this,aa,xn(()=>{oe(this,rs).call(this,oe(this,Pn))})),oe(this,Ia)>0){var e=Vt(this,ma,document.createDocumentFragment());hl(oe(this,aa),e);const r=oe(this,na).pending;Vt(this,Mn,xn(()=>r(oe(this,Pn))))}else Fr(this,Vr,Io).call(this)}catch(r){this.error(r)}},Io=function(){this.is_pending=!1;for(const e of oe(this,Cs))Er(e,en),la(e);for(const e of oe(this,$s))Er(e,Xn),la(e);oe(this,Cs).clear(),oe(this,$s).clear()},Ao=function(e){var r=Xt,a=Jt,s=Wr;jn(oe(this,pn)),Fn(oe(this,pn)),Ts(oe(this,pn).ctx);try{return e()}catch(o){return Wd(o),null}finally{jn(r),Fn(a),Ts(s)}},Ii=function(e){var r;if(!this.has_pending_snippet()){this.parent&&Fr(r=this.parent,Vr,Ii).call(r,e);return}Vt(this,Ia,oe(this,Ia)+e),oe(this,Ia)===0&&(Fr(this,Vr,Io).call(this),oe(this,Mn)&&ss(oe(this,Mn),()=>{Vt(this,Mn,null)}),oe(this,ma)&&(oe(this,Pn).before(oe(this,ma)),Vt(this,ma,null)))};function tc(t,e,r,a){const s=Os()?xo:ll;var o=t.filter(g=>!g.settled);if(r.length===0&&o.length===0){a(e.map(s));return}var i=Xt,l=rc(),u=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(g=>g.promise)):null;function f(g){l();try{a(g)}catch(x){(i.f&da)===0&&Aa(x,i)}Oo()}if(r.length===0){u.then(()=>f(e.map(s)));return}function p(){l(),Promise.all(r.map(g=>Jf(g))).then(g=>f([...e.map(s),...g])).catch(g=>Aa(g,i))}u?u.then(p):p()}function rc(){var t=Xt,e=Jt,r=Wr,a=Lt;return function(o=!0){jn(t),Fn(e),Ts(r),o&&(a==null||a.activate())}}function Oo(t=!0){jn(null),Fn(null),Ts(null),t&&(Lt==null||Lt.deactivate())}function Yf(){var t=Xt.b,e=Lt,r=t.is_rendered();return t.update_pending_count(1),e.increment(r),()=>{t.update_pending_count(-1),e.decrement(r)}}function xo(t){var e=rn|en,r=Jt!==null&&(Jt.f&rn)!==0?Jt:null;return Xt!==null&&(Xt.f|=Ds),{ctx:Wr,deps:null,effects:null,equals:Hd,f:e,fn:t,reactions:null,rv:0,v:Br,wv:0,parent:r??Xt,ac:null}}function Jf(t,e,r){Xt===null&&uf();var s=void 0,o=fa(Br),i=!Jt,l=new Map;return dv(()=>{var x;var u=Pd();s=u.promise;try{Promise.resolve(t()).then(u.resolve,u.reject).finally(Oo)}catch(b){u.reject(b),Oo()}var f=Lt;if(i){var p=Yf();(x=l.get(f))==null||x.reject(Xa),l.delete(f),l.set(f,u)}const g=(b,k=void 0)=>{if(f.activate(),k)k!==Xa&&(o.f|=Oa,ba(o,k));else{(o.f&Oa)!==0&&(o.f^=Oa),ba(o,b);for(const[S,_]of l){if(l.delete(S),S===f)break;_.reject(Xa)}}p&&p()};u.promise.then(g,b=>g(null,b||"unknown"))}),ei(()=>{for(const u of l.values())u.reject(Xa)}),new Promise(u=>{function f(p){function g(){p===s?u(o):f(s)}p.then(g,g)}f(s)})}function O(t){const e=xo(t);return yc(e),e}function ll(t){const e=xo(t);return e.equals=qd,e}function Xf(t){var e=t.effects;if(e!==null){t.effects=null;for(var r=0;r<e.length;r+=1)tn(e[r])}}function Qf(t){for(var e=t.parent;e!==null;){if((e.f&rn)===0)return(e.f&da)===0?e:null;e=e.parent}return null}function dl(t){var e,r=Xt;jn(Qf(t));try{t.f&=~ds,Xf(t),e=Cc(t)}finally{jn(r)}return e}function nc(t){var e=dl(t);if(!t.equals(e)&&(t.wv=kc(),(!(Lt!=null&&Lt.is_fork)||t.deps===null)&&(t.v=e,t.deps===null))){Er(t,Zr);return}Fa||(Qr!==null?(ul()||Lt!=null&&Lt.is_fork)&&Qr.set(t,e):il(t))}function Zf(t){var e,r;if(t.effects!==null)for(const a of t.effects)(a.teardown||a.ac)&&((e=a.teardown)==null||e.call(a),(r=a.ac)==null||r.abort(Xa),a.teardown=sf,a.ac=null,uo(a,0),vl(a))}function ac(t){if(t.effects!==null)for(const e of t.effects)e.teardown&&Es(e)}let Ai=new Set;const Ra=new Map;let sc=!1;function fa(t,e){var r={f:0,v:t,reactions:null,equals:Hd,rv:0,wv:0};return r}function Y(t,e){const r=fa(t);return yc(r),r}function Li(t,e=!1,r=!0){var s;const a=fa(t);return e||(a.equals=qd),mo&&r&&Wr!==null&&Wr.l!==null&&((s=Wr.l).s??(s.s=[])).push(a),a}function v(t,e,r=!1){Jt!==null&&(!Wn||(Jt.f&jl)!==0)&&Os()&&(Jt.f&(rn|Ua|ol|jl))!==0&&(Rn===null||!Ms.call(Rn,t))&&bf();let a=r?Ut(e):e;return ba(t,a)}function ba(t,e){if(!t.equals(e)){var r=t.v;Fa?Ra.set(t,e):Ra.set(t,r),t.v=e;var a=_a.ensure();if(a.capture(t,r),(t.f&rn)!==0){const s=t;(t.f&en)!==0&&dl(s),il(s)}t.wv=kc(),oc(t,en),Os()&&Xt!==null&&(Xt.f&Zr)!==0&&(Xt.f&(Qn|fs))===0&&(Nn===null?uv([t]):Nn.push(t)),!a.is_fork&&Ai.size>0&&!sc&&ev()}return e}function ev(){sc=!1;for(const t of Ai)(t.f&Zr)!==0&&Er(t,Xn),_o(t)&&Es(t);Ai.clear()}function no(t,e=1){var r=n(t),a=e===1?r++:r--;return v(t,r),a}function ao(t){v(t,t.v+1)}function oc(t,e){var r=t.reactions;if(r!==null)for(var a=Os(),s=r.length,o=0;o<s;o++){var i=r[o],l=i.f;if(!(!a&&i===Xt)){var u=(l&en)===0;if(u&&Er(i,e),(l&rn)!==0){var f=i;Qr==null||Qr.delete(f),(l&ds)===0&&(l&On&&(i.f|=ds),oc(f,Xn))}else u&&((l&Ua)!==0&&Hn!==null&&Hn.add(i),la(i))}}}function Ut(t){if(typeof t!="object"||t===null||ca in t)return t;const e=al(t);if(e!==nf&&e!==af)return t;var r=new Map,a=nl(t),s=Y(0),o=os,i=l=>{if(os===o)return l();var u=Jt,f=os;Fn(null),ql(o);var p=l();return Fn(u),ql(f),p};return a&&r.set("length",Y(t.length)),new Proxy(t,{defineProperty(l,u,f){(!("value"in f)||f.configurable===!1||f.enumerable===!1||f.writable===!1)&&gf();var p=r.get(u);return p===void 0?i(()=>{var g=Y(f.value);return r.set(u,g),g}):v(p,f.value,!0),!0},deleteProperty(l,u){var f=r.get(u);if(f===void 0){if(u in l){const p=i(()=>Y(Br));r.set(u,p),ao(s)}}else v(f,Br),ao(s);return!0},get(l,u,f){var b;if(u===ca)return t;var p=r.get(u),g=u in l;if(p===void 0&&(!g||(b=Da(l,u))!=null&&b.writable)&&(p=i(()=>{var k=Ut(g?l[u]:Br),S=Y(k);return S}),r.set(u,p)),p!==void 0){var x=n(p);return x===Br?void 0:x}return Reflect.get(l,u,f)},getOwnPropertyDescriptor(l,u){var f=Reflect.getOwnPropertyDescriptor(l,u);if(f&&"value"in f){var p=r.get(u);p&&(f.value=n(p))}else if(f===void 0){var g=r.get(u),x=g==null?void 0:g.v;if(g!==void 0&&x!==Br)return{enumerable:!0,configurable:!0,value:x,writable:!0}}return f},has(l,u){var x;if(u===ca)return!0;var f=r.get(u),p=f!==void 0&&f.v!==Br||Reflect.has(l,u);if(f!==void 0||Xt!==null&&(!p||(x=Da(l,u))!=null&&x.writable)){f===void 0&&(f=i(()=>{var b=p?Ut(l[u]):Br,k=Y(b);return k}),r.set(u,f));var g=n(f);if(g===Br)return!1}return p},set(l,u,f,p){var D;var g=r.get(u),x=u in l;if(a&&u==="length")for(var b=f;b<g.v;b+=1){var k=r.get(b+"");k!==void 0?v(k,Br):b in l&&(k=i(()=>Y(Br)),r.set(b+"",k))}if(g===void 0)(!x||(D=Da(l,u))!=null&&D.writable)&&(g=i(()=>Y(void 0)),v(g,Ut(f)),r.set(u,g));else{x=g.v!==Br;var S=i(()=>Ut(f));v(g,S)}var _=Reflect.getOwnPropertyDescriptor(l,u);if(_!=null&&_.set&&_.set.call(p,f),!x){if(a&&typeof u=="string"){var w=r.get("length"),E=Number(u);Number.isInteger(E)&&E>=w.v&&v(w,E+1)}ao(s)}return!0},ownKeys(l){n(s);var u=Reflect.ownKeys(l).filter(g=>{var x=r.get(g);return x===void 0||x.v!==Br});for(var[f,p]of r)p.v!==Br&&!(f in l)&&u.push(f);return u},setPrototypeOf(){_f()}})}function Vl(t){try{if(t!==null&&typeof t=="object"&&ca in t)return t[ca]}catch{}return t}function tv(t,e){return Object.is(Vl(t),Vl(e))}var Ro,ic,lc,dc,cc;function rv(){if(Ro===void 0){Ro=window,ic=document,lc=/Firefox/.test(navigator.userAgent);var t=Element.prototype,e=Node.prototype,r=Text.prototype;dc=Da(e,"firstChild").get,cc=Da(e,"nextSibling").get,Fl(t)&&(t.__click=void 0,t.__className=void 0,t.__attributes=null,t.__style=void 0,t.__e=void 0),Fl(r)&&(r.__t=void 0)}}function ua(t=""){return document.createTextNode(t)}function Dn(t){return dc.call(t)}function go(t){return cc.call(t)}function d(t,e){return Dn(t)}function ae(t,e=!1){{var r=Dn(t);return r instanceof Comment&&r.data===""?go(r):r}}function m(t,e=1,r=!1){let a=t;for(;e--;)a=go(a);return a}function nv(t){t.textContent=""}function uc(){return!1}function cl(t,e,r){return document.createElementNS(e??Vd,t,void 0)}function av(t,e){if(e){const r=document.body;t.autofocus=!0,Yn(()=>{document.activeElement===r&&t.focus()})}}let Ul=!1;function sv(){Ul||(Ul=!0,document.addEventListener("reset",t=>{Promise.resolve().then(()=>{var e;if(!t.defaultPrevented)for(const r of t.target.elements)(e=r.__on_r)==null||e.call(r)})},{capture:!0}))}function Zo(t){var e=Jt,r=Xt;Fn(null),jn(null);try{return t()}finally{Fn(e),jn(r)}}function fc(t,e,r,a=r){t.addEventListener(e,()=>Zo(r));const s=t.__on_r;s?t.__on_r=()=>{s(),a(!0)}:t.__on_r=()=>a(!0),sv()}function vc(t){Xt===null&&(Jt===null&&hf(),pf()),Fa&&vf()}function ov(t,e){var r=e.last;r===null?e.last=e.first=t:(r.next=t,t.prev=r,e.last=t)}function Zn(t,e){var r=Xt;r!==null&&(r.f&un)!==0&&(t|=un);var a={ctx:Wr,deps:null,nodes:null,f:t|en|On,first:null,fn:e,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},s=a;if((t&Ns)!==0)zs!==null?zs.push(a):la(a);else if(e!==null){try{Es(a)}catch(i){throw tn(a),i}s.deps===null&&s.teardown===null&&s.nodes===null&&s.first===s.last&&(s.f&Ds)===0&&(s=s.first,(t&Ua)!==0&&(t&ya)!==0&&s!==null&&(s.f|=ya))}if(s!==null&&(s.parent=r,r!==null&&ov(s,r),Jt!==null&&(Jt.f&rn)!==0&&(t&fs)===0)){var o=Jt;(o.effects??(o.effects=[])).push(s)}return a}function ul(){return Jt!==null&&!Wn}function ei(t){const e=Zn(ls,null);return Er(e,Zr),e.teardown=t,e}function _r(t){vc();var e=Xt.f,r=!Jt&&(e&Qn)!==0&&(e&Ps)===0;if(r){var a=Wr;(a.e??(a.e=[])).push(t)}else return pc(t)}function pc(t){return Zn(Ns|Dd,t)}function iv(t){return vc(),Zn(ls|Dd,t)}function lv(t){_a.ensure();const e=Zn(fs|Ds,t);return(r={})=>new Promise(a=>{r.outro?ss(e,()=>{tn(e),a(void 0)}):(tn(e),a(void 0))})}function ti(t){return Zn(Ns,t)}function dv(t){return Zn(ol|Ds,t)}function fl(t,e=0){return Zn(ls|e,t)}function T(t,e=[],r=[],a=[]){tc(a,e,r,s=>{Zn(ls,()=>t(...s.map(n)))})}function vs(t,e=0){var r=Zn(Ua|e,t);return r}function hc(t,e=0){var r=Zn(Xo|e,t);return r}function xn(t){return Zn(Qn|Ds,t)}function mc(t){var e=t.teardown;if(e!==null){const r=Fa,a=Jt;Hl(!0),Fn(null);try{e.call(null)}finally{Hl(r),Fn(a)}}}function vl(t,e=!1){var r=t.first;for(t.first=t.last=null;r!==null;){const s=r.ac;s!==null&&Zo(()=>{s.abort(Xa)});var a=r.next;(r.f&fs)!==0?r.parent=null:tn(r,e),r=a}}function cv(t){for(var e=t.first;e!==null;){var r=e.next;(e.f&Qn)===0&&tn(e),e=r}}function tn(t,e=!0){var r=!1;(e||(t.f&df)!==0)&&t.nodes!==null&&t.nodes.end!==null&&(xc(t.nodes.start,t.nodes.end),r=!0),vl(t,e&&!r),uo(t,0),Er(t,da);var a=t.nodes&&t.nodes.t;if(a!==null)for(const o of a)o.stop();mc(t);var s=t.parent;s!==null&&s.first!==null&&gc(t),t.next=t.prev=t.teardown=t.ctx=t.deps=t.fn=t.nodes=t.ac=null}function xc(t,e){for(;t!==null;){var r=t===e?null:go(t);t.remove(),t=r}}function gc(t){var e=t.parent,r=t.prev,a=t.next;r!==null&&(r.next=a),a!==null&&(a.prev=r),e!==null&&(e.first===t&&(e.first=a),e.last===t&&(e.last=r))}function ss(t,e,r=!0){var a=[];_c(t,a,!0);var s=()=>{r&&tn(t),e&&e()},o=a.length;if(o>0){var i=()=>--o||s();for(var l of a)l.out(i)}else s()}function _c(t,e,r){if((t.f&un)===0){t.f^=un;var a=t.nodes&&t.nodes.t;if(a!==null)for(const l of a)(l.is_global||r)&&e.push(l);for(var s=t.first;s!==null;){var o=s.next,i=(s.f&ya)!==0||(s.f&Qn)!==0&&(t.f&Ua)!==0;_c(s,e,i?r:!1),s=o}}}function pl(t){bc(t,!0)}function bc(t,e){if((t.f&un)!==0){t.f^=un;for(var r=t.first;r!==null;){var a=r.next,s=(r.f&ya)!==0||(r.f&Qn)!==0;bc(r,s?e:!1),r=a}var o=t.nodes&&t.nodes.t;if(o!==null)for(const i of o)(i.is_global||e)&&i.in()}}function hl(t,e){if(t.nodes)for(var r=t.nodes.start,a=t.nodes.end;r!==null;){var s=r===a?null:go(r);e.append(r),r=s}}let Lo=!1,Fa=!1;function Hl(t){Fa=t}let Jt=null,Wn=!1;function Fn(t){Jt=t}let Xt=null;function jn(t){Xt=t}let Rn=null;function yc(t){Jt!==null&&(Rn===null?Rn=[t]:Rn.push(t))}let mn=null,$n=0,Nn=null;function uv(t){Nn=t}let wc=1,Za=0,os=Za;function ql(t){os=t}function kc(){return++wc}function _o(t){var e=t.f;if((e&en)!==0)return!0;if(e&rn&&(t.f&=~ds),(e&Xn)!==0){for(var r=t.deps,a=r.length,s=0;s<a;s++){var o=r[s];if(_o(o)&&nc(o),o.wv>t.wv)return!0}(e&On)!==0&&Qr===null&&Er(t,Zr)}return!1}function Sc(t,e,r=!0){var a=t.reactions;if(a!==null&&!(Rn!==null&&Ms.call(Rn,t)))for(var s=0;s<a.length;s++){var o=a[s];(o.f&rn)!==0?Sc(o,e,!1):e===o&&(r?Er(o,en):(o.f&Zr)!==0&&Er(o,Xn),la(o))}}function Cc(t){var S;var e=mn,r=$n,a=Nn,s=Jt,o=Rn,i=Wr,l=Wn,u=os,f=t.f;mn=null,$n=0,Nn=null,Jt=(f&(Qn|fs))===0?t:null,Rn=null,Ts(t.ctx),Wn=!1,os=++Za,t.ac!==null&&(Zo(()=>{t.ac.abort(Xa)}),t.ac=null);try{t.f|=Ci;var p=t.fn,g=p();t.f|=Ps;var x=t.deps,b=Lt==null?void 0:Lt.is_fork;if(mn!==null){var k;if(b||uo(t,$n),x!==null&&$n>0)for(x.length=$n+mn.length,k=0;k<mn.length;k++)x[$n+k]=mn[k];else t.deps=x=mn;if(ul()&&(t.f&On)!==0)for(k=$n;k<x.length;k++)((S=x[k]).reactions??(S.reactions=[])).push(t)}else!b&&x!==null&&$n<x.length&&(uo(t,$n),x.length=$n);if(Os()&&Nn!==null&&!Wn&&x!==null&&(t.f&(rn|Xn|en))===0)for(k=0;k<Nn.length;k++)Sc(Nn[k],t);if(s!==null&&s!==t){if(Za++,s.deps!==null)for(let _=0;_<r;_+=1)s.deps[_].rv=Za;if(e!==null)for(const _ of e)_.rv=Za;Nn!==null&&(a===null?a=Nn:a.push(...Nn))}return(t.f&Oa)!==0&&(t.f^=Oa),g}catch(_){return Wd(_)}finally{t.f^=Ci,mn=e,$n=r,Nn=a,Jt=s,Rn=o,Ts(i),Wn=l,os=u}}function fv(t,e){let r=e.reactions;if(r!==null){var a=tf.call(r,t);if(a!==-1){var s=r.length-1;s===0?r=e.reactions=null:(r[a]=r[s],r.pop())}}if(r===null&&(e.f&rn)!==0&&(mn===null||!Ms.call(mn,e))){var o=e;(o.f&On)!==0&&(o.f^=On,o.f&=~ds),il(o),Zf(o),uo(o,0)}}function uo(t,e){var r=t.deps;if(r!==null)for(var a=e;a<r.length;a++)fv(t,r[a])}function Es(t){var e=t.f;if((e&da)===0){Er(t,Zr);var r=Xt,a=Lo;Xt=t,Lo=!0;try{(e&(Ua|Xo))!==0?cv(t):vl(t),mc(t);var s=Cc(t);t.teardown=typeof s=="function"?s:null,t.wv=wc;var o;wi&&Df&&(t.f&en)!==0&&t.deps}finally{Lo=a,Xt=r}}}async function $c(){await Promise.resolve(),Jd()}function n(t){var e=t.f,r=(e&rn)!==0;if(Jt!==null&&!Wn){var a=Xt!==null&&(Xt.f&da)!==0;if(!a&&(Rn===null||!Ms.call(Rn,t))){var s=Jt.deps;if((Jt.f&Ci)!==0)t.rv<Za&&(t.rv=Za,mn===null&&s!==null&&s[$n]===t?$n++:mn===null?mn=[t]:mn.push(t));else{(Jt.deps??(Jt.deps=[])).push(t);var o=t.reactions;o===null?t.reactions=[Jt]:Ms.call(o,Jt)||o.push(Jt)}}}if(Fa&&Ra.has(t))return Ra.get(t);if(r){var i=t;if(Fa){var l=i.v;return((i.f&Zr)===0&&i.reactions!==null||Tc(i))&&(l=dl(i)),Ra.set(i,l),l}var u=(i.f&On)===0&&!Wn&&Jt!==null&&(Lo||(Jt.f&On)!==0),f=(i.f&Ps)===0;_o(i)&&(u&&(i.f|=On),nc(i)),u&&!f&&(ac(i),Mc(i))}if(Qr!=null&&Qr.has(t))return Qr.get(t);if((t.f&Oa)!==0)throw t.v;return t.v}function Mc(t){if(t.f|=On,t.deps!==null)for(const e of t.deps)(e.reactions??(e.reactions=[])).push(t),(e.f&rn)!==0&&(e.f&On)===0&&(ac(e),Mc(e))}function Tc(t){if(t.v===Br)return!0;if(t.deps===null)return!1;for(const e of t.deps)if(Ra.has(e)||(e.f&rn)!==0&&Tc(e))return!0;return!1}function cs(t){var e=Wn;try{return Wn=!0,t()}finally{Wn=e}}function Ya(t){if(!(typeof t!="object"||!t||t instanceof EventTarget)){if(ca in t)Ni(t);else if(!Array.isArray(t))for(let e in t){const r=t[e];typeof r=="object"&&r&&ca in r&&Ni(r)}}}function Ni(t,e=new Set){if(typeof t=="object"&&t!==null&&!(t instanceof EventTarget)&&!e.has(t)){e.add(t),t instanceof Date&&t.getTime();for(let a in t)try{Ni(t[a],e)}catch{}const r=al(t);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const a=Nd(r);for(let s in a){const o=a[s].get;if(o)try{o.call(t)}catch{}}}}}function vv(t){return t.endsWith("capture")&&t!=="gotpointercapture"&&t!=="lostpointercapture"}const pv=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function hv(t){return pv.includes(t)}const mv={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function xv(t){return t=t.toLowerCase(),mv[t]??t}const gv=["touchstart","touchmove"];function _v(t){return gv.includes(t)}const es=Symbol("events"),zc=new Set,Pi=new Set;function Ec(t,e,r,a={}){function s(o){if(a.capture||Di.call(e,o),!o.cancelBubble)return Zo(()=>r==null?void 0:r.call(this,o))}return t.startsWith("pointer")||t.startsWith("touch")||t==="wheel"?Yn(()=>{e.addEventListener(t,s,a)}):e.addEventListener(t,s,a),s}function gn(t,e,r,a,s){var o={capture:a,passive:s},i=Ec(t,e,r,o);(e===document.body||e===window||e===document||e instanceof HTMLMediaElement)&&ei(()=>{e.removeEventListener(t,i,o)})}function he(t,e,r){(e[es]??(e[es]={}))[t]=r}function Gr(t){for(var e=0;e<t.length;e++)zc.add(t[e]);for(var r of Pi)r(t)}let Kl=null;function Di(t){var _,w;var e=this,r=e.ownerDocument,a=t.type,s=((_=t.composedPath)==null?void 0:_.call(t))||[],o=s[0]||t.target;Kl=t;var i=0,l=Kl===t&&t[es];if(l){var u=s.indexOf(l);if(u!==-1&&(e===document||e===window)){t[es]=e;return}var f=s.indexOf(e);if(f===-1)return;u<=f&&(i=u)}if(o=s[i]||t.target,o!==e){rf(t,"currentTarget",{configurable:!0,get(){return o||r}});var p=Jt,g=Xt;Fn(null),jn(null);try{for(var x,b=[];o!==null;){var k=o.assignedSlot||o.parentNode||o.host||null;try{var S=(w=o[es])==null?void 0:w[a];S!=null&&(!o.disabled||t.target===o)&&S.call(o,t)}catch(E){x?b.push(E):x=E}if(t.cancelBubble||k===e||k===null)break;o=k}if(x){for(let E of b)queueMicrotask(()=>{throw E});throw x}}finally{t[es]=e,delete t.currentTarget,Fn(p),jn(g)}}}var Ad;const di=((Ad=globalThis==null?void 0:globalThis.window)==null?void 0:Ad.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:t=>t});function bv(t){return(di==null?void 0:di.createHTML(t))??t}function Ic(t){var e=cl("template");return e.innerHTML=bv(t.replaceAll("<!>","<!---->")),e.content}function ja(t,e){var r=Xt;r.nodes===null&&(r.nodes={start:t,end:e,a:null,t:null})}function h(t,e){var r=(e&Bd)!==0,a=(e&Ef)!==0,s,o=!t.startsWith("<!>");return()=>{s===void 0&&(s=Ic(o?t:"<!>"+t),r||(s=Dn(s)));var i=a||lc?document.importNode(s,!0):s.cloneNode(!0);if(r){var l=Dn(i),u=i.lastChild;ja(l,u)}else ja(i,i);return i}}function yv(t,e,r="svg"){var a=!t.startsWith("<!>"),s=(e&Bd)!==0,o=`<${r}>${a?t:"<!>"+t}</${r}>`,i;return()=>{if(!i){var l=Ic(o),u=Dn(l);if(s)for(i=document.createDocumentFragment();Dn(u);)i.appendChild(Dn(u));else i=Dn(u)}var f=i.cloneNode(!0);if(s){var p=Dn(f),g=f.lastChild;ja(p,g)}else ja(f,f);return f}}function bo(t,e){return yv(t,e,"svg")}function oa(t=""){{var e=ua(t+"");return ja(e,e),e}}function Se(){var t=document.createDocumentFragment(),e=document.createComment(""),r=ua();return t.append(e,r),ja(e,r),t}function c(t,e){t!==null&&t.before(e)}function z(t,e){var r=e==null?"":typeof e=="object"?`${e}`:e;r!==(t.__t??(t.__t=t.nodeValue))&&(t.__t=r,t.nodeValue=`${r}`)}function wv(t,e){return kv(t,e)}const So=new Map;function kv(t,{target:e,anchor:r,props:a={},events:s,context:o,intro:i=!0,transformError:l}){rv();var u=void 0,f=lv(()=>{var p=r??e.appendChild(ua());Hf(p,{pending:()=>{}},b=>{Ir({});var k=Wr;o&&(k.c=o),s&&(a.$$events=s),u=t(b,a)||{},Ar()},l);var g=new Set,x=b=>{for(var k=0;k<b.length;k++){var S=b[k];if(!g.has(S)){g.add(S);var _=_v(S);for(const D of[e,document]){var w=So.get(D);w===void 0&&(w=new Map,So.set(D,w));var E=w.get(S);E===void 0?(D.addEventListener(S,Di,{passive:_}),w.set(S,1)):w.set(S,E+1)}}}};return x(Jo(zc)),Pi.add(x),()=>{var _;for(var b of g)for(const w of[e,document]){var k=So.get(w),S=k.get(b);--S==0?(w.removeEventListener(b,Di),k.delete(b),k.size===0&&So.delete(w)):k.set(b,S)}Pi.delete(x),p!==r&&((_=p.parentNode)==null||_.removeChild(p))}});return Sv.set(u,f),u}let Sv=new WeakMap;var Kn,sa,Tn,as,po,ho,Go;class yo{constructor(e,r=!0){Et(this,"anchor");Zt(this,Kn,new Map);Zt(this,sa,new Map);Zt(this,Tn,new Map);Zt(this,as,new Set);Zt(this,po,!0);Zt(this,ho,e=>{if(oe(this,Kn).has(e)){var r=oe(this,Kn).get(e),a=oe(this,sa).get(r);if(a)pl(a),oe(this,as).delete(r);else{var s=oe(this,Tn).get(r);s&&(s.effect.f&un)===0&&(oe(this,sa).set(r,s.effect),oe(this,Tn).delete(r),s.fragment.lastChild.remove(),this.anchor.before(s.fragment),a=s.effect)}for(const[o,i]of oe(this,Kn)){if(oe(this,Kn).delete(o),o===e)break;const l=oe(this,Tn).get(i);l&&(tn(l.effect),oe(this,Tn).delete(i))}for(const[o,i]of oe(this,sa)){if(o===r||oe(this,as).has(o)||(i.f&un)!==0)continue;const l=()=>{if(Array.from(oe(this,Kn).values()).includes(o)){var f=document.createDocumentFragment();hl(i,f),f.append(ua()),oe(this,Tn).set(o,{effect:i,fragment:f})}else tn(i);oe(this,as).delete(o),oe(this,sa).delete(o)};oe(this,po)||!a?(oe(this,as).add(o),ss(i,l,!1)):l()}}});Zt(this,Go,e=>{oe(this,Kn).delete(e);const r=Array.from(oe(this,Kn).values());for(const[a,s]of oe(this,Tn))r.includes(a)||(tn(s.effect),oe(this,Tn).delete(a))});this.anchor=e,Vt(this,po,r)}ensure(e,r){var a=Lt,s=uc();if(r&&!oe(this,sa).has(e)&&!oe(this,Tn).has(e))if(s){var o=document.createDocumentFragment(),i=ua();o.append(i),oe(this,Tn).set(e,{effect:xn(()=>r(i)),fragment:o})}else oe(this,sa).set(e,xn(()=>r(this.anchor)));if(oe(this,Kn).set(a,e),s){for(const[l,u]of oe(this,sa))l===e?a.unskip_effect(u):a.skip_effect(u);for(const[l,u]of oe(this,Tn))l===e?a.unskip_effect(u.effect):a.skip_effect(u.effect);a.oncommit(oe(this,ho)),a.ondiscard(oe(this,Go))}else oe(this,ho).call(this,a)}}Kn=new WeakMap,sa=new WeakMap,Tn=new WeakMap,as=new WeakMap,po=new WeakMap,ho=new WeakMap,Go=new WeakMap;const Cv=0,Wl=1,$v=2;function Oi(t,e,r,a,s){var o=Os(),i=Br,l=o?fa(i):Li(i,!1,!1),u=o?fa(i):Li(i,!1,!1),f=new yo(t);vs(()=>{var p=e(),g=!1;if(of(p)){var x=rc(),b=!1;const k=S=>{if(!g){b=!0,x(!1),_a.ensure();try{S()}finally{Oo(!1),xs||Jd()}}};p.then(S=>{k(()=>{ba(l,S),f.ensure(Wl,a&&(_=>a(_,l)))})},S=>{k(()=>{if(ba(u,S),f.ensure($v,s&&(_=>s(_,u))),!s)throw u.v})}),Yn(()=>{b||k(()=>{f.ensure(Cv,r)})})}else ba(l,p),f.ensure(Wl,a&&(k=>a(k,l)));return()=>{g=!0}})}function C(t,e,r=!1){var a=new yo(t),s=r?ya:0;function o(i,l){a.ensure(i,l)}vs(()=>{var i=!1;e((l,u=0)=>{i=!0,o(u,l)}),i||o(-1,null)},s)}function Le(t,e){return e}function Mv(t,e,r){for(var a=[],s=e.length,o,i=e.length,l=0;l<s;l++){let g=e[l];ss(g,()=>{if(o){if(o.pending.delete(g),o.done.add(g),o.pending.size===0){var x=t.outrogroups;Ri(t,Jo(o.done)),x.delete(o),x.size===0&&(t.outrogroups=null)}}else i-=1},!1)}if(i===0){var u=a.length===0&&r!==null;if(u){var f=r,p=f.parentNode;nv(p),p.append(f),t.items.clear()}Ri(t,e,!u)}else o={pending:new Set(e),done:new Set},(t.outrogroups??(t.outrogroups=new Set)).add(o)}function Ri(t,e,r=!0){var a;if(t.pending.size>0){a=new Set;for(const i of t.pending.values())for(const l of i)a.add(t.items.get(l).e)}for(var s=0;s<e.length;s++){var o=e[s];if(a!=null&&a.has(o)){o.f|=ia;const i=document.createDocumentFragment();hl(o,i)}else tn(e[s],r)}}var Gl;function Ie(t,e,r,a,s,o=null){var i=t,l=new Map,u=(e&Fd)!==0;if(u){var f=t;i=f.appendChild(ua())}var p=null,g=ll(()=>{var D=r();return nl(D)?D:D==null?[]:Jo(D)}),x,b=new Map,k=!0;function S(D){(E.effect.f&da)===0&&(E.pending.delete(D),E.fallback=p,Tv(E,x,i,e,a),p!==null&&(x.length===0?(p.f&ia)===0?pl(p):(p.f^=ia,eo(p,null,i)):ss(p,()=>{p=null})))}function _(D){E.pending.delete(D)}var w=vs(()=>{x=n(g);for(var D=x.length,M=new Set,Z=Lt,ce=uc(),P=0;P<D;P+=1){var $=x[P],X=a($,P),J=k?null:l.get(X);J?(J.v&&ba(J.v,$),J.i&&ba(J.i,P),ce&&Z.unskip_effect(J.e)):(J=zv(l,k?i:Gl??(Gl=ua()),$,X,P,s,e,r),k||(J.e.f|=ia),l.set(X,J)),M.add(X)}if(D===0&&o&&!p&&(k?p=xn(()=>o(i)):(p=xn(()=>o(Gl??(Gl=ua()))),p.f|=ia)),D>M.size&&ff(),!k)if(b.set(Z,M),ce){for(const[me,B]of l)M.has(me)||Z.skip_effect(B.e);Z.oncommit(S),Z.ondiscard(_)}else S(Z);n(g)}),E={effect:w,items:l,pending:b,outrogroups:null,fallback:p};k=!1}function qs(t){for(;t!==null&&(t.f&Qn)===0;)t=t.next;return t}function Tv(t,e,r,a,s){var J,me,B,Te,F,U,le,we,W;var o=(a&Sf)!==0,i=e.length,l=t.items,u=qs(t.effect.first),f,p=null,g,x=[],b=[],k,S,_,w;if(o)for(w=0;w<i;w+=1)k=e[w],S=s(k,w),_=l.get(S).e,(_.f&ia)===0&&((me=(J=_.nodes)==null?void 0:J.a)==null||me.measure(),(g??(g=new Set)).add(_));for(w=0;w<i;w+=1){if(k=e[w],S=s(k,w),_=l.get(S).e,t.outrogroups!==null)for(const ne of t.outrogroups)ne.pending.delete(_),ne.done.delete(_);if((_.f&ia)!==0)if(_.f^=ia,_===u)eo(_,null,r);else{var E=p?p.next:u;_===t.effect.last&&(t.effect.last=_.prev),_.prev&&(_.prev.next=_.next),_.next&&(_.next.prev=_.prev),$a(t,p,_),$a(t,_,E),eo(_,E,r),p=_,x=[],b=[],u=qs(p.next);continue}if((_.f&un)!==0&&(pl(_),o&&((Te=(B=_.nodes)==null?void 0:B.a)==null||Te.unfix(),(g??(g=new Set)).delete(_))),_!==u){if(f!==void 0&&f.has(_)){if(x.length<b.length){var D=b[0],M;p=D.prev;var Z=x[0],ce=x[x.length-1];for(M=0;M<x.length;M+=1)eo(x[M],D,r);for(M=0;M<b.length;M+=1)f.delete(b[M]);$a(t,Z.prev,ce.next),$a(t,p,Z),$a(t,ce,D),u=D,p=ce,w-=1,x=[],b=[]}else f.delete(_),eo(_,u,r),$a(t,_.prev,_.next),$a(t,_,p===null?t.effect.first:p.next),$a(t,p,_),p=_;continue}for(x=[],b=[];u!==null&&u!==_;)(f??(f=new Set)).add(u),b.push(u),u=qs(u.next);if(u===null)continue}(_.f&ia)===0&&x.push(_),p=_,u=qs(_.next)}if(t.outrogroups!==null){for(const ne of t.outrogroups)ne.pending.size===0&&(Ri(t,Jo(ne.done)),(F=t.outrogroups)==null||F.delete(ne));t.outrogroups.size===0&&(t.outrogroups=null)}if(u!==null||f!==void 0){var P=[];if(f!==void 0)for(_ of f)(_.f&un)===0&&P.push(_);for(;u!==null;)(u.f&un)===0&&u!==t.fallback&&P.push(u),u=qs(u.next);var $=P.length;if($>0){var X=(a&Fd)!==0&&i===0?r:null;if(o){for(w=0;w<$;w+=1)(le=(U=P[w].nodes)==null?void 0:U.a)==null||le.measure();for(w=0;w<$;w+=1)(W=(we=P[w].nodes)==null?void 0:we.a)==null||W.fix()}Mv(t,P,X)}}o&&Yn(()=>{var ne,A;if(g!==void 0)for(_ of g)(A=(ne=_.nodes)==null?void 0:ne.a)==null||A.apply()})}function zv(t,e,r,a,s,o,i,l){var u=(i&wf)!==0?(i&Cf)===0?Li(r,!1,!1):fa(r):null,f=(i&kf)!==0?fa(s):null;return{v:u,i:f,e:xn(()=>(o(e,u??r,f??s,l),()=>{t.delete(a)}))}}function eo(t,e,r){if(t.nodes)for(var a=t.nodes.start,s=t.nodes.end,o=e&&(e.f&ia)===0?e.nodes.start:r;a!==null;){var i=go(a);if(o.before(a),a===s)return;a=i}}function $a(t,e,r){e===null?t.effect.first=r:e.next=r,r===null?t.effect.last=e:r.prev=e}function Gn(t,e,r=!1,a=!1,s=!1){var o=t,i="";T(()=>{var l=Xt;if(i!==(i=e()??"")&&(l.nodes!==null&&(xc(l.nodes.start,l.nodes.end),l.nodes=null),i!=="")){var u=r?Ud:a?If:void 0,f=cl(r?"svg":a?"math":"template",u);f.innerHTML=i;var p=r||a?f:f.content;if(ja(Dn(p),p.lastChild),r||a)for(;Dn(p);)o.before(Dn(p));else o.before(p)}})}function pt(t,e,r,a,s){var l;var o=(l=e.$$slots)==null?void 0:l[r],i=!1;o===!0&&(o=e.children,i=!0),o===void 0||o(t,i?()=>a:a)}function Fi(t,e,...r){var a=new yo(t);vs(()=>{const s=e()??null;a.ensure(s,s&&(o=>s(o,...r)))},ya)}function Is(t,e,r){var a=new yo(t);vs(()=>{var s=e()??null;a.ensure(s,s&&(o=>r(o,s)))},ya)}function Ev(t,e,r,a,s,o){var i=null,l=t,u=new yo(l,!1);vs(()=>{const f=e()||null;var p=Ud;if(f===null){u.ensure(null,null);return}return u.ensure(f,g=>{if(f){if(i=cl(f,p),ja(i,i),a){var x=i.appendChild(ua());a(i,x)}Xt.nodes.end=i,g.before(i)}}),()=>{}},ya),ei(()=>{})}function Iv(t,e){var r=void 0,a;hc(()=>{r!==(r=e())&&(a&&(tn(a),a=null),r&&(a=xn(()=>{ti(()=>r(t))})))})}function Ac(t){var e,r,a="";if(typeof t=="string"||typeof t=="number")a+=t;else if(typeof t=="object")if(Array.isArray(t)){var s=t.length;for(e=0;e<s;e++)t[e]&&(r=Ac(t[e]))&&(a&&(a+=" "),a+=r)}else for(r in t)t[r]&&(a&&(a+=" "),a+=r);return a}function Lc(){for(var t,e,r=0,a="",s=arguments.length;r<s;r++)(t=arguments[r])&&(e=Ac(t))&&(a&&(a+=" "),a+=e);return a}function gr(t){return typeof t=="object"?Lc(t):t??""}const Yl=[...` 	
\r\f \v\uFEFF`];function Av(t,e,r){var a=t==null?"":""+t;if(e&&(a=a?a+" "+e:e),r){for(var s of Object.keys(r))if(r[s])a=a?a+" "+s:s;else if(a.length)for(var o=s.length,i=0;(i=a.indexOf(s,i))>=0;){var l=i+o;(i===0||Yl.includes(a[i-1]))&&(l===a.length||Yl.includes(a[l]))?a=(i===0?"":a.substring(0,i))+a.substring(l+1):i=l}}return a===""?null:a}function Jl(t,e=!1){var r=e?" !important;":";",a="";for(var s of Object.keys(t)){var o=t[s];o!=null&&o!==""&&(a+=" "+s+": "+o+r)}return a}function ci(t){return t[0]!=="-"||t[1]!=="-"?t.toLowerCase():t}function Lv(t,e){if(e){var r="",a,s;if(Array.isArray(e)?(a=e[0],s=e[1]):a=e,t){t=String(t).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,i=0,l=!1,u=[];a&&u.push(...Object.keys(a).map(ci)),s&&u.push(...Object.keys(s).map(ci));var f=0,p=-1;const S=t.length;for(var g=0;g<S;g++){var x=t[g];if(l?x==="/"&&t[g-1]==="*"&&(l=!1):o?o===x&&(o=!1):x==="/"&&t[g+1]==="*"?l=!0:x==='"'||x==="'"?o=x:x==="("?i++:x===")"&&i--,!l&&o===!1&&i===0){if(x===":"&&p===-1)p=g;else if(x===";"||g===S-1){if(p!==-1){var b=ci(t.substring(f,p).trim());if(!u.includes(b)){x!==";"&&g++;var k=t.substring(f,g).trim();r+=" "+k+";"}}f=g+1,p=-1}}}}return a&&(r+=Jl(a)),s&&(r+=Jl(s,!0)),r=r.trim(),r===""?null:r}return t==null?null:String(t)}function qe(t,e,r,a,s,o){var i=t.__className;if(i!==r||i===void 0){var l=Av(r,a,o);l==null?t.removeAttribute("class"):e?t.className=l:t.setAttribute("class",l),t.__className=r}else if(o&&s!==o)for(var u in o){var f=!!o[u];(s==null||f!==!!s[u])&&t.classList.toggle(u,f)}return o}function ui(t,e={},r,a){for(var s in r){var o=r[s];e[s]!==o&&(r[s]==null?t.style.removeProperty(s):t.style.setProperty(s,o,a))}}function As(t,e,r,a){var s=t.__style;if(s!==e){var o=Lv(e,a);o==null?t.removeAttribute("style"):t.style.cssText=o,t.__style=e}else a&&(Array.isArray(a)?(ui(t,r==null?void 0:r[0],a[0]),ui(t,r==null?void 0:r[1],a[1],"important")):ui(t,r,a));return a}function Fo(t,e,r=!1){if(t.multiple){if(e==null)return;if(!nl(e))return Lf();for(var a of t.options)a.selected=e.includes(so(a));return}for(a of t.options){var s=so(a);if(tv(s,e)){a.selected=!0;return}}(!r||e!==void 0)&&(t.selectedIndex=-1)}function Nc(t){var e=new MutationObserver(()=>{Fo(t,t.__value)});e.observe(t,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),ei(()=>{e.disconnect()})}function Xl(t,e,r=e){var a=new WeakSet,s=!0;fc(t,"change",o=>{var i=o?"[selected]":":checked",l;if(t.multiple)l=[].map.call(t.querySelectorAll(i),so);else{var u=t.querySelector(i)??t.querySelector("option:not([disabled])");l=u&&so(u)}r(l),Lt!==null&&a.add(Lt)}),ti(()=>{var o=e();if(t===document.activeElement){var i=Do??Lt;if(a.has(i))return}if(Fo(t,o,s),s&&o===void 0){var l=t.querySelector(":checked");l!==null&&(o=so(l),r(o))}t.__value=o,s=!1}),Nc(t)}function so(t){return"__value"in t?t.__value:t.value}const Ks=Symbol("class"),Ws=Symbol("style"),Pc=Symbol("is custom element"),Dc=Symbol("is html"),Nv=Rd?"option":"OPTION",Pv=Rd?"select":"SELECT";function Dv(t,e){e?t.hasAttribute("selected")||t.setAttribute("selected",""):t.removeAttribute("selected")}function lr(t,e,r,a){var s=Oc(t);s[e]!==(s[e]=r)&&(e==="loading"&&(t[cf]=r),r==null?t.removeAttribute(e):typeof r!="string"&&Rc(t).includes(e)?t[e]=r:t.setAttribute(e,r))}function Ov(t,e,r,a,s=!1,o=!1){var i=Oc(t),l=i[Pc],u=!i[Dc],f=e||{},p=t.nodeName===Nv;for(var g in e)g in r||(r[g]=null);r.class?r.class=gr(r.class):r[Ks]&&(r.class=null),r[Ws]&&(r.style??(r.style=null));var x=Rc(t);for(const D in r){let M=r[D];if(p&&D==="value"&&M==null){t.value=t.__value="",f[D]=M;continue}if(D==="class"){var b=t.namespaceURI==="http://www.w3.org/1999/xhtml";qe(t,b,M,a,e==null?void 0:e[Ks],r[Ks]),f[D]=M,f[Ks]=r[Ks];continue}if(D==="style"){As(t,M,e==null?void 0:e[Ws],r[Ws]),f[D]=M,f[Ws]=r[Ws];continue}var k=f[D];if(!(M===k&&!(M===void 0&&t.hasAttribute(D)))){f[D]=M;var S=D[0]+D[1];if(S!=="$$")if(S==="on"){const Z={},ce="$$"+D;let P=D.slice(2);var _=hv(P);if(vv(P)&&(P=P.slice(0,-7),Z.capture=!0),!_&&k){if(M!=null)continue;t.removeEventListener(P,f[ce],Z),f[ce]=null}if(_)he(P,t,M),Gr([P]);else if(M!=null){let $=function(X){f[D].call(this,X)};f[ce]=Ec(P,t,$,Z)}}else if(D==="style")lr(t,D,M);else if(D==="autofocus")av(t,!!M);else if(!l&&(D==="__value"||D==="value"&&M!=null))t.value=t.__value=M;else if(D==="selected"&&p)Dv(t,M);else{var w=D;u||(w=xv(w));var E=w==="defaultValue"||w==="defaultChecked";if(M==null&&!l&&!E)if(i[D]=null,w==="value"||w==="checked"){let Z=t;const ce=e===void 0;if(w==="value"){let P=Z.defaultValue;Z.removeAttribute(w),Z.defaultValue=P,Z.value=Z.__value=ce?P:null}else{let P=Z.defaultChecked;Z.removeAttribute(w),Z.defaultChecked=P,Z.checked=ce?P:!1}}else t.removeAttribute(D);else E||x.includes(w)&&(l||typeof M!="string")?(t[w]=M,w in i&&(i[w]=Br)):typeof M!="function"&&lr(t,w,M)}}}return f}function jo(t,e,r=[],a=[],s=[],o,i=!1,l=!1){tc(s,r,a,u=>{var f=void 0,p={},g=t.nodeName===Pv,x=!1;if(hc(()=>{var k=e(...u.map(n)),S=Ov(t,f,k,o,i,l);x&&g&&"value"in k&&Fo(t,k.value);for(let w of Object.getOwnPropertySymbols(p))k[w]||tn(p[w]);for(let w of Object.getOwnPropertySymbols(k)){var _=k[w];w.description===Af&&(!f||_!==f[w])&&(p[w]&&tn(p[w]),p[w]=xn(()=>Iv(t,()=>_))),S[w]=_}f=S}),g){var b=t;ti(()=>{Fo(b,f.value,!0),Nc(b)})}x=!0})}function Oc(t){return t.__attributes??(t.__attributes={[Pc]:t.nodeName.includes("-"),[Dc]:t.namespaceURI===Vd})}var Ql=new Map;function Rc(t){var e=t.getAttribute("is")||t.nodeName,r=Ql.get(e);if(r)return r;Ql.set(e,r=[]);for(var a,s=t,o=Element.prototype;o!==s;){a=Nd(s);for(var i in a)a[i].set&&r.push(i);s=al(s)}return r}function La(t,e,r=e){var a=new WeakSet;fc(t,"input",async s=>{var o=s?t.defaultValue:t.value;if(o=fi(t)?vi(o):o,r(o),Lt!==null&&a.add(Lt),await $c(),o!==(o=e())){var i=t.selectionStart,l=t.selectionEnd,u=t.value.length;if(t.value=o??"",l!==null){var f=t.value.length;i===l&&l===u&&f>u?(t.selectionStart=f,t.selectionEnd=f):(t.selectionStart=i,t.selectionEnd=Math.min(l,f))}}}),cs(e)==null&&t.value&&(r(fi(t)?vi(t.value):t.value),Lt!==null&&a.add(Lt)),fl(()=>{var s=e();if(t===document.activeElement){var o=Do??Lt;if(a.has(o))return}fi(t)&&s===vi(t.value)||t.type==="date"&&!s&&!t.value||s!==t.value&&(t.value=s??"")})}function fi(t){var e=t.type;return e==="number"||e==="range"}function vi(t){return t===""?null:+t}function Zl(t,e){return t===e||(t==null?void 0:t[ca])===e}function Jn(t={},e,r,a){return ti(()=>{var s,o;return fl(()=>{s=o,o=[],cs(()=>{t!==r(...o)&&(e(t,...o),s&&Zl(r(...s),t)&&e(null,...s))})}),()=>{Yn(()=>{o&&Zl(r(...o),t)&&e(null,...o)})}}),t}function Rv(t=!1){const e=Wr,r=e.l.u;if(!r)return;let a=()=>Ya(e.s);if(t){let s=0,o={};const i=xo(()=>{let l=!1;const u=e.s;for(const f in u)u[f]!==o[f]&&(o[f]=u[f],l=!0);return l&&s++,s});a=()=>n(i)}r.b.length&&iv(()=>{ed(e,a),ki(r.b)}),_r(()=>{const s=cs(()=>r.m.map(lf));return()=>{for(const o of s)typeof o=="function"&&o()}}),r.a.length&&_r(()=>{ed(e,a),ki(r.a)})}function ed(t,e){if(t.l.s)for(const r of t.l.s)n(r);e()}let Co=!1;function Fv(t){var e=Co;try{return Co=!1,[t(),Co]}finally{Co=e}}const jv={get(t,e){if(!t.exclude.includes(e))return t.props[e]},set(t,e){return!1},getOwnPropertyDescriptor(t,e){if(!t.exclude.includes(e)&&e in t.props)return{enumerable:!0,configurable:!0,value:t.props[e]}},has(t,e){return t.exclude.includes(e)?!1:e in t.props},ownKeys(t){return Reflect.ownKeys(t.props).filter(e=>!t.exclude.includes(e))}};function Bv(t,e,r){return new Proxy({props:t,exclude:e},jv)}const Vv={get(t,e){if(!t.exclude.includes(e))return n(t.version),e in t.special?t.special[e]():t.props[e]},set(t,e,r){if(!(e in t.special)){var a=Xt;try{jn(t.parent_effect),t.special[e]=Fe({get[e](){return t.props[e]}},e,jd)}finally{jn(a)}}return t.special[e](r),no(t.version),!0},getOwnPropertyDescriptor(t,e){if(!t.exclude.includes(e)&&e in t.props)return{enumerable:!0,configurable:!0,value:t.props[e]}},deleteProperty(t,e){return t.exclude.includes(e)||(t.exclude.push(e),no(t.version)),!0},has(t,e){return t.exclude.includes(e)?!1:e in t.props},ownKeys(t){return Reflect.ownKeys(t.props).filter(e=>!t.exclude.includes(e))}};function lt(t,e){return new Proxy({props:t,exclude:e,special:{},version:fa(0),parent_effect:Xt},Vv)}const Uv={get(t,e){let r=t.props.length;for(;r--;){let a=t.props[r];if(Hs(a)&&(a=a()),typeof a=="object"&&a!==null&&e in a)return a[e]}},set(t,e,r){let a=t.props.length;for(;a--;){let s=t.props[a];Hs(s)&&(s=s());const o=Da(s,e);if(o&&o.set)return o.set(r),!0}return!1},getOwnPropertyDescriptor(t,e){let r=t.props.length;for(;r--;){let a=t.props[r];if(Hs(a)&&(a=a()),typeof a=="object"&&a!==null&&e in a){const s=Da(a,e);return s&&!s.configurable&&(s.configurable=!0),s}}},has(t,e){if(e===ca||e===Od)return!1;for(let r of t.props)if(Hs(r)&&(r=r()),r!=null&&e in r)return!0;return!1},ownKeys(t){const e=[];for(let r of t.props)if(Hs(r)&&(r=r()),!!r){for(const a in r)e.includes(a)||e.push(a);for(const a of Object.getOwnPropertySymbols(r))e.includes(a)||e.push(a)}return e}};function ht(...t){return new Proxy({props:t},Uv)}function Fe(t,e,r,a){var D;var s=!mo||(r&Mf)!==0,o=(r&Tf)!==0,i=(r&zf)!==0,l=a,u=!0,f=()=>(u&&(u=!1,l=i?cs(a):a),l),p;if(o){var g=ca in t||Od in t;p=((D=Da(t,e))==null?void 0:D.set)??(g&&e in t?M=>t[e]=M:void 0)}var x,b=!1;o?[x,b]=Fv(()=>t[e]):x=t[e],x===void 0&&a!==void 0&&(x=f(),p&&(s&&xf(),p(x)));var k;if(s?k=()=>{var M=t[e];return M===void 0?f():(u=!0,M)}:k=()=>{var M=t[e];return M!==void 0&&(l=void 0),M===void 0?l:M},s&&(r&jd)===0)return k;if(p){var S=t.$$legacy;return(function(M,Z){return arguments.length>0?((!s||!Z||S||b)&&p(Z?k():M),M):k()})}var _=!1,w=((r&$f)!==0?xo:ll)(()=>(_=!1,k()));o&&n(w);var E=Xt;return(function(M,Z){if(arguments.length>0){const ce=Z?n(w):s&&o?Ut(M):M;return v(w,ce),_=!0,l!==void 0&&(l=ce),M}return Fa&&_||(E.f&da)!==0?w.v:n(w)})}const Hv="5";var Ld;typeof window<"u"&&((Ld=window.__svelte??(window.__svelte={})).v??(Ld.v=new Set)).add(Hv);new TextEncoder;const qv=4096;function Fc(t,e,r){let a=e;const s=a+r,o=[];let i="";for(;a<s;){const l=t[a++];if((l&128)===0)o.push(l);else if((l&224)===192){const u=t[a++]&63;o.push((l&31)<<6|u)}else if((l&240)===224){const u=t[a++]&63,f=t[a++]&63;o.push((l&31)<<12|u<<6|f)}else if((l&248)===240){const u=t[a++]&63,f=t[a++]&63,p=t[a++]&63;let g=(l&7)<<18|u<<12|f<<6|p;g>65535&&(g-=65536,o.push(g>>>10&1023|55296),g=56320|g&1023),o.push(g)}else o.push(l);o.length>=qv&&(i+=String.fromCharCode(...o),o.length=0)}return o.length>0&&(i+=String.fromCharCode(...o)),i}const Kv=new TextDecoder,Wv=200;function Gv(t,e,r){const a=t.subarray(e,e+r);return Kv.decode(a)}function Yv(t,e,r){return r>Wv?Gv(t,e,r):Fc(t,e,r)}class $o{constructor(e,r){Et(this,"type");Et(this,"data");this.type=e,this.data=r}}class zn extends Error{constructor(e){super(e);const r=Object.create(zn.prototype);Object.setPrototypeOf(this,r),Object.defineProperty(this,"name",{configurable:!0,enumerable:!1,value:zn.name})}}const Gs=4294967295;function Jv(t,e,r){const a=Math.floor(r/4294967296),s=r;t.setUint32(e,a),t.setUint32(e+4,s)}function jc(t,e){const r=t.getInt32(e),a=t.getUint32(e+4);return r*4294967296+a}function Xv(t,e){const r=t.getUint32(e),a=t.getUint32(e+4);return r*4294967296+a}const Qv=-1,Zv=4294967296-1,ep=17179869184-1;function tp({sec:t,nsec:e}){if(t>=0&&e>=0&&t<=ep)if(e===0&&t<=Zv){const r=new Uint8Array(4);return new DataView(r.buffer).setUint32(0,t),r}else{const r=t/4294967296,a=t&4294967295,s=new Uint8Array(8),o=new DataView(s.buffer);return o.setUint32(0,e<<2|r&3),o.setUint32(4,a),s}else{const r=new Uint8Array(12),a=new DataView(r.buffer);return a.setUint32(0,e),Jv(a,4,t),r}}function rp(t){const e=t.getTime(),r=Math.floor(e/1e3),a=(e-r*1e3)*1e6,s=Math.floor(a/1e9);return{sec:r+s,nsec:a-s*1e9}}function np(t){if(t instanceof Date){const e=rp(t);return tp(e)}else return null}function ap(t){const e=new DataView(t.buffer,t.byteOffset,t.byteLength);switch(t.byteLength){case 4:return{sec:e.getUint32(0),nsec:0};case 8:{const r=e.getUint32(0),a=e.getUint32(4),s=(r&3)*4294967296+a,o=r>>>2;return{sec:s,nsec:o}}case 12:{const r=jc(e,4),a=e.getUint32(0);return{sec:r,nsec:a}}default:throw new zn(`Unrecognized data size for timestamp (expected 4, 8, or 12): ${t.length}`)}}function sp(t){const e=ap(t);return new Date(e.sec*1e3+e.nsec/1e6)}const op={type:Qv,encode:np,decode:sp},Yo=class Yo{constructor(){Et(this,"__brand");Et(this,"builtInEncoders",[]);Et(this,"builtInDecoders",[]);Et(this,"encoders",[]);Et(this,"decoders",[]);this.register(op)}register({type:e,encode:r,decode:a}){if(e>=0)this.encoders[e]=r,this.decoders[e]=a;else{const s=-1-e;this.builtInEncoders[s]=r,this.builtInDecoders[s]=a}}tryToEncode(e,r){for(let a=0;a<this.builtInEncoders.length;a++){const s=this.builtInEncoders[a];if(s!=null){const o=s(e,r);if(o!=null){const i=-1-a;return new $o(i,o)}}}for(let a=0;a<this.encoders.length;a++){const s=this.encoders[a];if(s!=null){const o=s(e,r);if(o!=null){const i=a;return new $o(i,o)}}}return e instanceof $o?e:null}decode(e,r,a){const s=r<0?this.builtInDecoders[-1-r]:this.decoders[r];return s?s(e,r,a):new $o(r,e)}};Et(Yo,"defaultCodec",new Yo);let ji=Yo;function ip(t){return t instanceof ArrayBuffer||typeof SharedArrayBuffer<"u"&&t instanceof SharedArrayBuffer}function td(t){return t instanceof Uint8Array?t:ArrayBuffer.isView(t)?new Uint8Array(t.buffer,t.byteOffset,t.byteLength):ip(t)?new Uint8Array(t):Uint8Array.from(t)}function pi(t){return`${t<0?"-":""}0x${Math.abs(t).toString(16).padStart(2,"0")}`}const lp=16,dp=16;class cp{constructor(e=lp,r=dp){Et(this,"hit",0);Et(this,"miss",0);Et(this,"caches");Et(this,"maxKeyLength");Et(this,"maxLengthPerKey");this.maxKeyLength=e,this.maxLengthPerKey=r,this.caches=[];for(let a=0;a<this.maxKeyLength;a++)this.caches.push([])}canBeCached(e){return e>0&&e<=this.maxKeyLength}find(e,r,a){const s=this.caches[a-1];e:for(const o of s){const i=o.bytes;for(let l=0;l<a;l++)if(i[l]!==e[r+l])continue e;return o.str}return null}store(e,r){const a=this.caches[e.length-1],s={bytes:e,str:r};a.length>=this.maxLengthPerKey?a[Math.random()*a.length|0]=s:a.push(s)}decode(e,r,a){const s=this.find(e,r,a);if(s!=null)return this.hit++,s;this.miss++;const o=Fc(e,r,a),i=Uint8Array.prototype.slice.call(e,r,r+a);return this.store(i,o),o}}const Bi="array",oo="map_key",Bc="map_value",up=t=>{if(typeof t=="string"||typeof t=="number")return t;throw new zn("The type of key must be string or number but "+typeof t)};class fp{constructor(){Et(this,"stack",[]);Et(this,"stackHeadPosition",-1)}get length(){return this.stackHeadPosition+1}top(){return this.stack[this.stackHeadPosition]}pushArrayState(e){const r=this.getUninitializedStateFromPool();r.type=Bi,r.position=0,r.size=e,r.array=new Array(e)}pushMapState(e){const r=this.getUninitializedStateFromPool();r.type=oo,r.readCount=0,r.size=e,r.map={}}getUninitializedStateFromPool(){if(this.stackHeadPosition++,this.stackHeadPosition===this.stack.length){const e={type:void 0,size:0,array:void 0,position:0,readCount:0,map:void 0,key:null};this.stack.push(e)}return this.stack[this.stackHeadPosition]}release(e){if(this.stack[this.stackHeadPosition]!==e)throw new Error("Invalid stack state. Released state is not on top of the stack.");if(e.type===Bi){const a=e;a.size=0,a.array=void 0,a.position=0,a.type=void 0}if(e.type===oo||e.type===Bc){const a=e;a.size=0,a.map=void 0,a.readCount=0,a.type=void 0}this.stackHeadPosition--}reset(){this.stack.length=0,this.stackHeadPosition=-1}}const Ys=-1,ml=new DataView(new ArrayBuffer(0)),vp=new Uint8Array(ml.buffer);try{ml.getInt8(0)}catch(t){if(!(t instanceof RangeError))throw new Error("This module is not supported in the current JavaScript engine because DataView does not throw RangeError on out-of-bounds access")}const rd=new RangeError("Insufficient data"),pp=new cp;class xl{constructor(e){Et(this,"extensionCodec");Et(this,"context");Et(this,"useBigInt64");Et(this,"rawStrings");Et(this,"maxStrLength");Et(this,"maxBinLength");Et(this,"maxArrayLength");Et(this,"maxMapLength");Et(this,"maxExtLength");Et(this,"keyDecoder");Et(this,"mapKeyConverter");Et(this,"totalPos",0);Et(this,"pos",0);Et(this,"view",ml);Et(this,"bytes",vp);Et(this,"headByte",Ys);Et(this,"stack",new fp);Et(this,"entered",!1);this.extensionCodec=(e==null?void 0:e.extensionCodec)??ji.defaultCodec,this.context=e==null?void 0:e.context,this.useBigInt64=(e==null?void 0:e.useBigInt64)??!1,this.rawStrings=(e==null?void 0:e.rawStrings)??!1,this.maxStrLength=(e==null?void 0:e.maxStrLength)??Gs,this.maxBinLength=(e==null?void 0:e.maxBinLength)??Gs,this.maxArrayLength=(e==null?void 0:e.maxArrayLength)??Gs,this.maxMapLength=(e==null?void 0:e.maxMapLength)??Gs,this.maxExtLength=(e==null?void 0:e.maxExtLength)??Gs,this.keyDecoder=(e==null?void 0:e.keyDecoder)!==void 0?e.keyDecoder:pp,this.mapKeyConverter=(e==null?void 0:e.mapKeyConverter)??up}clone(){return new xl({extensionCodec:this.extensionCodec,context:this.context,useBigInt64:this.useBigInt64,rawStrings:this.rawStrings,maxStrLength:this.maxStrLength,maxBinLength:this.maxBinLength,maxArrayLength:this.maxArrayLength,maxMapLength:this.maxMapLength,maxExtLength:this.maxExtLength,keyDecoder:this.keyDecoder})}reinitializeState(){this.totalPos=0,this.headByte=Ys,this.stack.reset()}setBuffer(e){const r=td(e);this.bytes=r,this.view=new DataView(r.buffer,r.byteOffset,r.byteLength),this.pos=0}appendBuffer(e){if(this.headByte===Ys&&!this.hasRemaining(1))this.setBuffer(e);else{const r=this.bytes.subarray(this.pos),a=td(e),s=new Uint8Array(r.length+a.length);s.set(r),s.set(a,r.length),this.setBuffer(s)}}hasRemaining(e){return this.view.byteLength-this.pos>=e}createExtraByteError(e){const{view:r,pos:a}=this;return new RangeError(`Extra ${r.byteLength-a} of ${r.byteLength} byte(s) found at buffer[${e}]`)}decode(e){if(this.entered)return this.clone().decode(e);try{this.entered=!0,this.reinitializeState(),this.setBuffer(e);const r=this.doDecodeSync();if(this.hasRemaining(1))throw this.createExtraByteError(this.pos);return r}finally{this.entered=!1}}*decodeMulti(e){if(this.entered){yield*this.clone().decodeMulti(e);return}try{for(this.entered=!0,this.reinitializeState(),this.setBuffer(e);this.hasRemaining(1);)yield this.doDecodeSync()}finally{this.entered=!1}}async decodeAsync(e){if(this.entered)return this.clone().decodeAsync(e);try{this.entered=!0;let r=!1,a;for await(const l of e){if(r)throw this.entered=!1,this.createExtraByteError(this.totalPos);this.appendBuffer(l);try{a=this.doDecodeSync(),r=!0}catch(u){if(!(u instanceof RangeError))throw u}this.totalPos+=this.pos}if(r){if(this.hasRemaining(1))throw this.createExtraByteError(this.totalPos);return a}const{headByte:s,pos:o,totalPos:i}=this;throw new RangeError(`Insufficient data in parsing ${pi(s)} at ${i} (${o} in the current buffer)`)}finally{this.entered=!1}}decodeArrayStream(e){return this.decodeMultiAsync(e,!0)}decodeStream(e){return this.decodeMultiAsync(e,!1)}async*decodeMultiAsync(e,r){if(this.entered){yield*this.clone().decodeMultiAsync(e,r);return}try{this.entered=!0;let a=r,s=-1;for await(const o of e){if(r&&s===0)throw this.createExtraByteError(this.totalPos);this.appendBuffer(o),a&&(s=this.readArraySize(),a=!1,this.complete());try{for(;yield this.doDecodeSync(),--s!==0;);}catch(i){if(!(i instanceof RangeError))throw i}this.totalPos+=this.pos}}finally{this.entered=!1}}doDecodeSync(){e:for(;;){const e=this.readHeadByte();let r;if(e>=224)r=e-256;else if(e<192)if(e<128)r=e;else if(e<144){const s=e-128;if(s!==0){this.pushMapState(s),this.complete();continue e}else r={}}else if(e<160){const s=e-144;if(s!==0){this.pushArrayState(s),this.complete();continue e}else r=[]}else{const s=e-160;r=this.decodeString(s,0)}else if(e===192)r=null;else if(e===194)r=!1;else if(e===195)r=!0;else if(e===202)r=this.readF32();else if(e===203)r=this.readF64();else if(e===204)r=this.readU8();else if(e===205)r=this.readU16();else if(e===206)r=this.readU32();else if(e===207)this.useBigInt64?r=this.readU64AsBigInt():r=this.readU64();else if(e===208)r=this.readI8();else if(e===209)r=this.readI16();else if(e===210)r=this.readI32();else if(e===211)this.useBigInt64?r=this.readI64AsBigInt():r=this.readI64();else if(e===217){const s=this.lookU8();r=this.decodeString(s,1)}else if(e===218){const s=this.lookU16();r=this.decodeString(s,2)}else if(e===219){const s=this.lookU32();r=this.decodeString(s,4)}else if(e===220){const s=this.readU16();if(s!==0){this.pushArrayState(s),this.complete();continue e}else r=[]}else if(e===221){const s=this.readU32();if(s!==0){this.pushArrayState(s),this.complete();continue e}else r=[]}else if(e===222){const s=this.readU16();if(s!==0){this.pushMapState(s),this.complete();continue e}else r={}}else if(e===223){const s=this.readU32();if(s!==0){this.pushMapState(s),this.complete();continue e}else r={}}else if(e===196){const s=this.lookU8();r=this.decodeBinary(s,1)}else if(e===197){const s=this.lookU16();r=this.decodeBinary(s,2)}else if(e===198){const s=this.lookU32();r=this.decodeBinary(s,4)}else if(e===212)r=this.decodeExtension(1,0);else if(e===213)r=this.decodeExtension(2,0);else if(e===214)r=this.decodeExtension(4,0);else if(e===215)r=this.decodeExtension(8,0);else if(e===216)r=this.decodeExtension(16,0);else if(e===199){const s=this.lookU8();r=this.decodeExtension(s,1)}else if(e===200){const s=this.lookU16();r=this.decodeExtension(s,2)}else if(e===201){const s=this.lookU32();r=this.decodeExtension(s,4)}else throw new zn(`Unrecognized type byte: ${pi(e)}`);this.complete();const a=this.stack;for(;a.length>0;){const s=a.top();if(s.type===Bi)if(s.array[s.position]=r,s.position++,s.position===s.size)r=s.array,a.release(s);else continue e;else if(s.type===oo){if(r==="__proto__")throw new zn("The key __proto__ is not allowed");s.key=this.mapKeyConverter(r),s.type=Bc;continue e}else if(s.map[s.key]=r,s.readCount++,s.readCount===s.size)r=s.map,a.release(s);else{s.key=null,s.type=oo;continue e}}return r}}readHeadByte(){return this.headByte===Ys&&(this.headByte=this.readU8()),this.headByte}complete(){this.headByte=Ys}readArraySize(){const e=this.readHeadByte();switch(e){case 220:return this.readU16();case 221:return this.readU32();default:{if(e<160)return e-144;throw new zn(`Unrecognized array type byte: ${pi(e)}`)}}}pushMapState(e){if(e>this.maxMapLength)throw new zn(`Max length exceeded: map length (${e}) > maxMapLengthLength (${this.maxMapLength})`);this.stack.pushMapState(e)}pushArrayState(e){if(e>this.maxArrayLength)throw new zn(`Max length exceeded: array length (${e}) > maxArrayLength (${this.maxArrayLength})`);this.stack.pushArrayState(e)}decodeString(e,r){return!this.rawStrings||this.stateIsMapKey()?this.decodeUtf8String(e,r):this.decodeBinary(e,r)}decodeUtf8String(e,r){var o;if(e>this.maxStrLength)throw new zn(`Max length exceeded: UTF-8 byte length (${e}) > maxStrLength (${this.maxStrLength})`);if(this.bytes.byteLength<this.pos+r+e)throw rd;const a=this.pos+r;let s;return this.stateIsMapKey()&&((o=this.keyDecoder)!=null&&o.canBeCached(e))?s=this.keyDecoder.decode(this.bytes,a,e):s=Yv(this.bytes,a,e),this.pos+=r+e,s}stateIsMapKey(){return this.stack.length>0?this.stack.top().type===oo:!1}decodeBinary(e,r){if(e>this.maxBinLength)throw new zn(`Max length exceeded: bin length (${e}) > maxBinLength (${this.maxBinLength})`);if(!this.hasRemaining(e+r))throw rd;const a=this.pos+r,s=this.bytes.subarray(a,a+e);return this.pos+=r+e,s}decodeExtension(e,r){if(e>this.maxExtLength)throw new zn(`Max length exceeded: ext length (${e}) > maxExtLength (${this.maxExtLength})`);const a=this.view.getInt8(this.pos+r),s=this.decodeBinary(e,r+1);return this.extensionCodec.decode(s,a,this.context)}lookU8(){return this.view.getUint8(this.pos)}lookU16(){return this.view.getUint16(this.pos)}lookU32(){return this.view.getUint32(this.pos)}readU8(){const e=this.view.getUint8(this.pos);return this.pos++,e}readI8(){const e=this.view.getInt8(this.pos);return this.pos++,e}readU16(){const e=this.view.getUint16(this.pos);return this.pos+=2,e}readI16(){const e=this.view.getInt16(this.pos);return this.pos+=2,e}readU32(){const e=this.view.getUint32(this.pos);return this.pos+=4,e}readI32(){const e=this.view.getInt32(this.pos);return this.pos+=4,e}readU64(){const e=Xv(this.view,this.pos);return this.pos+=8,e}readI64(){const e=jc(this.view,this.pos);return this.pos+=8,e}readU64AsBigInt(){const e=this.view.getBigUint64(this.pos);return this.pos+=8,e}readI64AsBigInt(){const e=this.view.getBigInt64(this.pos);return this.pos+=8,e}readF32(){const e=this.view.getFloat32(this.pos);return this.pos+=4,e}readF64(){const e=this.view.getFloat64(this.pos);return this.pos+=8,e}}function hp(t,e){return new xl(e).decode(t)}const Or="";async function ri(t){const e=await fetch(t,{headers:{Accept:"application/msgpack"}});if(!e.ok)throw new Error(`요청 실패: ${e.status}`);if((e.headers.get("content-type")||"").includes("msgpack")){const a=await e.arrayBuffer();return hp(a)}return e.json()}async function mp(){const t=await fetch(`${Or}/api/status`);if(!t.ok)throw new Error("상태 확인 실패");return t.json()}async function xp(t,e=null,r=null){const a={provider:t};e&&(a.model=e),r&&(a.api_key=r);const s=await fetch(`${Or}/api/provider/validate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!s.ok)throw new Error("설정 실패");return s.json()}async function gp(t){const e=await fetch(`${Or}/api/models/${encodeURIComponent(t)}`);return e.ok?e.json():{models:[]}}function _p(t,{onProgress:e,onDone:r,onError:a}){const s=new AbortController;return fetch(`${Or}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:t}),signal:s.signal}).then(async o=>{if(!o.ok){a==null||a("다운로드 실패");return}const i=o.body.getReader(),l=new TextDecoder;let u="";for(;;){const{done:f,value:p}=await i.read();if(f)break;u+=l.decode(p,{stream:!0});const g=u.split(`
`);u=g.pop()||"";for(const x of g)if(x.startsWith("data:"))try{const b=JSON.parse(x.slice(5).trim());b.total&&b.completed!==void 0?e==null||e({total:b.total,completed:b.completed,status:b.status}):b.status&&(e==null||e({status:b.status}))}catch{}}r==null||r()}).catch(o=>{o.name!=="AbortError"&&(a==null||a(o.message))}),{abort:()=>s.abort()}}async function bp(){const t=await fetch(`${Or}/api/codex/logout`,{method:"POST"});if(!t.ok)throw new Error("Codex 로그아웃 실패");return t.json()}async function yp(t,e=null,r=null){let a=`${Or}/api/export/excel/${encodeURIComponent(t)}`;const s=new URLSearchParams;r?s.set("template_id",r):e&&e.length>0&&s.set("modules",e.join(","));const o=s.toString();o&&(a+=`?${o}`);const i=await fetch(a);if(!i.ok){const x=await i.json().catch(()=>({}));throw new Error(x.detail||"Excel 다운로드 실패")}const l=await i.blob(),f=(i.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),p=f?decodeURIComponent(f[1]):`${t}.xlsx`,g=document.createElement("a");return g.href=URL.createObjectURL(l),g.download=p,g.click(),URL.revokeObjectURL(g.href),p}async function gl(t){const e=await fetch(`${Or}/api/search?q=${encodeURIComponent(t)}`);if(!e.ok)throw new Error("검색 실패");return e.json()}async function wp(t,e){const r=await fetch(`${Or}/api/company/${t}/show/${encodeURIComponent(e)}/all`);if(!r.ok)throw new Error("company topic 일괄 조회 실패");return r.json()}async function kp(t){return ri(`${Or}/api/company/${t}/sections`)}async function Sp(t){return ri(`${Or}/api/company/${encodeURIComponent(t)}/init`)}async function Cp(t){const e=await fetch(`${Or}/api/company/${t}/toc`);if(!e.ok)throw new Error("목차 조회 실패");return e.json()}async function nd(t,e,r=null){const a=r?`?period=${encodeURIComponent(r)}`:"";return ri(`${Or}/api/company/${t}/viewer/${encodeURIComponent(e)}${a}`)}async function $p(t,e){const r=await fetch(`${Or}/api/company/${t}/diff/${encodeURIComponent(e)}/summary`);if(!r.ok)throw new Error("diff summary 조회 실패");return r.json()}async function Vc(t,e,r,a){const s=new URLSearchParams({from:r,to:a}),o=await fetch(`${Or}/api/company/${t}/diff/${encodeURIComponent(e)}?${s}`);if(!o.ok)throw new Error("topic diff 조회 실패");return o.json()}async function Mp(t,e){const r=new URLSearchParams({q:e}),a=await fetch(`${Or}/api/company/${encodeURIComponent(t)}/search?${r}`);if(!a.ok)throw new Error("검색 실패");return a.json()}async function Tp(t){return ri(`${Or}/api/company/${encodeURIComponent(t)}/searchIndex`)}async function zp(t){const e=await fetch(`${Or}/api/company/${encodeURIComponent(t)}/insights`);if(!e.ok)throw new Error("인사이트 조회 실패");return e.json()}async function Ep(t){const e=await fetch(`${Or}/api/company/${encodeURIComponent(t)}/network`);if(!e.ok)throw new Error("네트워크 조회 실패");return e.json()}function Ip(t,e,{onContext:r,onChunk:a,onDone:s,onError:o,provider:i,model:l}={}){const u=new AbortController,f=new URLSearchParams;i&&f.set("provider",i),l&&f.set("model",l);const p=f.toString(),g=`${Or}/api/company/${encodeURIComponent(t)}/summary/${encodeURIComponent(e)}${p?`?${p}`:""}`;return fetch(g,{signal:u.signal}).then(async x=>{if(!x.ok){o==null||o("요약 생성 실패");return}const b=x.body.getReader(),k=new TextDecoder;let S="",_=null;for(;;){const{done:w,value:E}=await b.read();if(w)break;S+=k.decode(E,{stream:!0});const D=S.split(`
`);S=D.pop()||"";for(const M of D)if(M.startsWith("event:"))_=M.slice(6).trim();else if(M.startsWith("data:")&&_){try{const Z=JSON.parse(M.slice(5).trim());_==="context"?r==null||r(Z):_==="chunk"?a==null||a(Z.text):_==="error"?o==null||o(Z.error):_==="done"&&(s==null||s())}catch{}_=null}}s==null||s()}).catch(x=>{x.name!=="AbortError"&&(o==null||o(x.message))}),{abort:()=>u.abort()}}function Ap(t,e,r={},{onMeta:a,onSnapshot:s,onContext:o,onSystemPrompt:i,onToolCall:l,onToolResult:u,onChart:f,onChunk:p,onDone:g,onError:x,onViewerNavigate:b},k=null){const S={question:e,stream:!0,...r};t&&(S.company=t),k&&k.length>0&&(S.history=k);const _=new AbortController;return fetch(`${Or}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(S),signal:_.signal}).then(async w=>{if(!w.ok){const P=await w.json().catch(()=>({}));x==null||x(P.detail||"스트리밍 실패");return}const E=w.body.getReader(),D=new TextDecoder;let M="",Z=!1,ce=null;for(;;){const{done:P,value:$}=await E.read();if(P)break;M+=D.decode($,{stream:!0});const X=M.split(`
`);M=X.pop()||"";for(const J of X)if(J.startsWith("event:"))ce=J.slice(6).trim();else if(J.startsWith("data:")&&ce){const me=J.slice(5).trim();try{const B=JSON.parse(me);ce==="meta"?a==null||a(B):ce==="snapshot"?s==null||s(B):ce==="context"?o==null||o(B):ce==="system_prompt"?i==null||i(B):ce==="tool_call"?l==null||l(B):ce==="tool_result"?u==null||u(B):ce==="chunk"?p==null||p(B.text):ce==="chart"?f==null||f(B):ce==="viewer_navigate"?b==null||b(B):ce==="error"?x==null||x(B.error,B.action,B.detail):ce==="done"&&(Z||(Z=!0,g==null||g()))}catch(B){console.warn("SSE JSON parse:",B)}ce=null}}Z||(Z=!0,g==null||g())}).catch(w=>{w.name!=="AbortError"&&(x==null||x(w.message))}),{abort:()=>_.abort()}}const Lp=(t,e)=>{const r=new Array(t.length+e.length);for(let a=0;a<t.length;a++)r[a]=t[a];for(let a=0;a<e.length;a++)r[t.length+a]=e[a];return r},Np=(t,e)=>({classGroupId:t,validator:e}),Uc=(t=new Map,e=null,r)=>({nextPart:t,validators:e,classGroupId:r}),Bo="-",ad=[],Pp="arbitrary..",Dp=t=>{const e=Rp(t),{conflictingClassGroups:r,conflictingClassGroupModifiers:a}=t;return{getClassGroupId:i=>{if(i.startsWith("[")&&i.endsWith("]"))return Op(i);const l=i.split(Bo),u=l[0]===""&&l.length>1?1:0;return Hc(l,u,e)},getConflictingClassGroupIds:(i,l)=>{if(l){const u=a[i],f=r[i];return u?f?Lp(f,u):u:f||ad}return r[i]||ad}}},Hc=(t,e,r)=>{if(t.length-e===0)return r.classGroupId;const s=t[e],o=r.nextPart.get(s);if(o){const f=Hc(t,e+1,o);if(f)return f}const i=r.validators;if(i===null)return;const l=e===0?t.join(Bo):t.slice(e).join(Bo),u=i.length;for(let f=0;f<u;f++){const p=i[f];if(p.validator(l))return p.classGroupId}},Op=t=>t.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const e=t.slice(1,-1),r=e.indexOf(":"),a=e.slice(0,r);return a?Pp+a:void 0})(),Rp=t=>{const{theme:e,classGroups:r}=t;return Fp(r,e)},Fp=(t,e)=>{const r=Uc();for(const a in t){const s=t[a];_l(s,r,a,e)}return r},_l=(t,e,r,a)=>{const s=t.length;for(let o=0;o<s;o++){const i=t[o];jp(i,e,r,a)}},jp=(t,e,r,a)=>{if(typeof t=="string"){Bp(t,e,r);return}if(typeof t=="function"){Vp(t,e,r,a);return}Up(t,e,r,a)},Bp=(t,e,r)=>{const a=t===""?e:qc(e,t);a.classGroupId=r},Vp=(t,e,r,a)=>{if(Hp(t)){_l(t(a),e,r,a);return}e.validators===null&&(e.validators=[]),e.validators.push(Np(r,t))},Up=(t,e,r,a)=>{const s=Object.entries(t),o=s.length;for(let i=0;i<o;i++){const[l,u]=s[i];_l(u,qc(e,l),r,a)}},qc=(t,e)=>{let r=t;const a=e.split(Bo),s=a.length;for(let o=0;o<s;o++){const i=a[o];let l=r.nextPart.get(i);l||(l=Uc(),r.nextPart.set(i,l)),r=l}return r},Hp=t=>"isThemeGetter"in t&&t.isThemeGetter===!0,qp=t=>{if(t<1)return{get:()=>{},set:()=>{}};let e=0,r=Object.create(null),a=Object.create(null);const s=(o,i)=>{r[o]=i,e++,e>t&&(e=0,a=r,r=Object.create(null))};return{get(o){let i=r[o];if(i!==void 0)return i;if((i=a[o])!==void 0)return s(o,i),i},set(o,i){o in r?r[o]=i:s(o,i)}}},Vi="!",sd=":",Kp=[],od=(t,e,r,a,s)=>({modifiers:t,hasImportantModifier:e,baseClassName:r,maybePostfixModifierPosition:a,isExternal:s}),Wp=t=>{const{prefix:e,experimentalParseClassName:r}=t;let a=s=>{const o=[];let i=0,l=0,u=0,f;const p=s.length;for(let S=0;S<p;S++){const _=s[S];if(i===0&&l===0){if(_===sd){o.push(s.slice(u,S)),u=S+1;continue}if(_==="/"){f=S;continue}}_==="["?i++:_==="]"?i--:_==="("?l++:_===")"&&l--}const g=o.length===0?s:s.slice(u);let x=g,b=!1;g.endsWith(Vi)?(x=g.slice(0,-1),b=!0):g.startsWith(Vi)&&(x=g.slice(1),b=!0);const k=f&&f>u?f-u:void 0;return od(o,b,x,k)};if(e){const s=e+sd,o=a;a=i=>i.startsWith(s)?o(i.slice(s.length)):od(Kp,!1,i,void 0,!0)}if(r){const s=a;a=o=>r({className:o,parseClassName:s})}return a},Gp=t=>{const e=new Map;return t.orderSensitiveModifiers.forEach((r,a)=>{e.set(r,1e6+a)}),r=>{const a=[];let s=[];for(let o=0;o<r.length;o++){const i=r[o],l=i[0]==="[",u=e.has(i);l||u?(s.length>0&&(s.sort(),a.push(...s),s=[]),a.push(i)):s.push(i)}return s.length>0&&(s.sort(),a.push(...s)),a}},Yp=t=>({cache:qp(t.cacheSize),parseClassName:Wp(t),sortModifiers:Gp(t),...Dp(t)}),Jp=/\s+/,Xp=(t,e)=>{const{parseClassName:r,getClassGroupId:a,getConflictingClassGroupIds:s,sortModifiers:o}=e,i=[],l=t.trim().split(Jp);let u="";for(let f=l.length-1;f>=0;f-=1){const p=l[f],{isExternal:g,modifiers:x,hasImportantModifier:b,baseClassName:k,maybePostfixModifierPosition:S}=r(p);if(g){u=p+(u.length>0?" "+u:u);continue}let _=!!S,w=a(_?k.substring(0,S):k);if(!w){if(!_){u=p+(u.length>0?" "+u:u);continue}if(w=a(k),!w){u=p+(u.length>0?" "+u:u);continue}_=!1}const E=x.length===0?"":x.length===1?x[0]:o(x).join(":"),D=b?E+Vi:E,M=D+w;if(i.indexOf(M)>-1)continue;i.push(M);const Z=s(w,_);for(let ce=0;ce<Z.length;++ce){const P=Z[ce];i.push(D+P)}u=p+(u.length>0?" "+u:u)}return u},Qp=(...t)=>{let e=0,r,a,s="";for(;e<t.length;)(r=t[e++])&&(a=Kc(r))&&(s&&(s+=" "),s+=a);return s},Kc=t=>{if(typeof t=="string")return t;let e,r="";for(let a=0;a<t.length;a++)t[a]&&(e=Kc(t[a]))&&(r&&(r+=" "),r+=e);return r},Zp=(t,...e)=>{let r,a,s,o;const i=u=>{const f=e.reduce((p,g)=>g(p),t());return r=Yp(f),a=r.cache.get,s=r.cache.set,o=l,l(u)},l=u=>{const f=a(u);if(f)return f;const p=Xp(u,r);return s(u,p),p};return o=i,(...u)=>o(Qp(...u))},eh=[],jr=t=>{const e=r=>r[t]||eh;return e.isThemeGetter=!0,e},Wc=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Gc=/^\((?:(\w[\w-]*):)?(.+)\)$/i,th=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,rh=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,nh=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,ah=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,sh=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,oh=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,Ma=t=>th.test(t),jt=t=>!!t&&!Number.isNaN(Number(t)),Ta=t=>!!t&&Number.isInteger(Number(t)),hi=t=>t.endsWith("%")&&jt(t.slice(0,-1)),ha=t=>rh.test(t),Yc=()=>!0,ih=t=>nh.test(t)&&!ah.test(t),bl=()=>!1,lh=t=>sh.test(t),dh=t=>oh.test(t),ch=t=>!We(t)&&!Xe(t),uh=t=>Ha(t,Qc,bl),We=t=>Wc.test(t),Ga=t=>Ha(t,Zc,ih),id=t=>Ha(t,_h,jt),fh=t=>Ha(t,tu,Yc),vh=t=>Ha(t,eu,bl),ld=t=>Ha(t,Jc,bl),ph=t=>Ha(t,Xc,dh),Mo=t=>Ha(t,ru,lh),Xe=t=>Gc.test(t),Js=t=>ps(t,Zc),hh=t=>ps(t,eu),dd=t=>ps(t,Jc),mh=t=>ps(t,Qc),xh=t=>ps(t,Xc),To=t=>ps(t,ru,!0),gh=t=>ps(t,tu,!0),Ha=(t,e,r)=>{const a=Wc.exec(t);return a?a[1]?e(a[1]):r(a[2]):!1},ps=(t,e,r=!1)=>{const a=Gc.exec(t);return a?a[1]?e(a[1]):r:!1},Jc=t=>t==="position"||t==="percentage",Xc=t=>t==="image"||t==="url",Qc=t=>t==="length"||t==="size"||t==="bg-size",Zc=t=>t==="length",_h=t=>t==="number",eu=t=>t==="family-name",tu=t=>t==="number"||t==="weight",ru=t=>t==="shadow",bh=()=>{const t=jr("color"),e=jr("font"),r=jr("text"),a=jr("font-weight"),s=jr("tracking"),o=jr("leading"),i=jr("breakpoint"),l=jr("container"),u=jr("spacing"),f=jr("radius"),p=jr("shadow"),g=jr("inset-shadow"),x=jr("text-shadow"),b=jr("drop-shadow"),k=jr("blur"),S=jr("perspective"),_=jr("aspect"),w=jr("ease"),E=jr("animate"),D=()=>["auto","avoid","all","avoid-page","page","left","right","column"],M=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],Z=()=>[...M(),Xe,We],ce=()=>["auto","hidden","clip","visible","scroll"],P=()=>["auto","contain","none"],$=()=>[Xe,We,u],X=()=>[Ma,"full","auto",...$()],J=()=>[Ta,"none","subgrid",Xe,We],me=()=>["auto",{span:["full",Ta,Xe,We]},Ta,Xe,We],B=()=>[Ta,"auto",Xe,We],Te=()=>["auto","min","max","fr",Xe,We],F=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],U=()=>["start","end","center","stretch","center-safe","end-safe"],le=()=>["auto",...$()],we=()=>[Ma,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...$()],W=()=>[Ma,"screen","full","dvw","lvw","svw","min","max","fit",...$()],ne=()=>[Ma,"screen","full","lh","dvh","lvh","svh","min","max","fit",...$()],A=()=>[t,Xe,We],G=()=>[...M(),dd,ld,{position:[Xe,We]}],q=()=>["no-repeat",{repeat:["","x","y","space","round"]}],L=()=>["auto","cover","contain",mh,uh,{size:[Xe,We]}],H=()=>[hi,Js,Ga],j=()=>["","none","full",f,Xe,We],K=()=>["",jt,Js,Ga],_e=()=>["solid","dashed","dotted","double"],$e=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],te=()=>[jt,hi,dd,ld],De=()=>["","none",k,Xe,We],tt=()=>["none",jt,Xe,We],st=()=>["none",jt,Xe,We],Ge=()=>[jt,Xe,We],rt=()=>[Ma,"full",...$()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[ha],breakpoint:[ha],color:[Yc],container:[ha],"drop-shadow":[ha],ease:["in","out","in-out"],font:[ch],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[ha],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[ha],shadow:[ha],spacing:["px",jt],text:[ha],"text-shadow":[ha],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",Ma,We,Xe,_]}],container:["container"],columns:[{columns:[jt,We,Xe,l]}],"break-after":[{"break-after":D()}],"break-before":[{"break-before":D()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:Z()}],overflow:[{overflow:ce()}],"overflow-x":[{"overflow-x":ce()}],"overflow-y":[{"overflow-y":ce()}],overscroll:[{overscroll:P()}],"overscroll-x":[{"overscroll-x":P()}],"overscroll-y":[{"overscroll-y":P()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:X()}],"inset-x":[{"inset-x":X()}],"inset-y":[{"inset-y":X()}],start:[{"inset-s":X(),start:X()}],end:[{"inset-e":X(),end:X()}],"inset-bs":[{"inset-bs":X()}],"inset-be":[{"inset-be":X()}],top:[{top:X()}],right:[{right:X()}],bottom:[{bottom:X()}],left:[{left:X()}],visibility:["visible","invisible","collapse"],z:[{z:[Ta,"auto",Xe,We]}],basis:[{basis:[Ma,"full","auto",l,...$()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[jt,Ma,"auto","initial","none",We]}],grow:[{grow:["",jt,Xe,We]}],shrink:[{shrink:["",jt,Xe,We]}],order:[{order:[Ta,"first","last","none",Xe,We]}],"grid-cols":[{"grid-cols":J()}],"col-start-end":[{col:me()}],"col-start":[{"col-start":B()}],"col-end":[{"col-end":B()}],"grid-rows":[{"grid-rows":J()}],"row-start-end":[{row:me()}],"row-start":[{"row-start":B()}],"row-end":[{"row-end":B()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":Te()}],"auto-rows":[{"auto-rows":Te()}],gap:[{gap:$()}],"gap-x":[{"gap-x":$()}],"gap-y":[{"gap-y":$()}],"justify-content":[{justify:[...F(),"normal"]}],"justify-items":[{"justify-items":[...U(),"normal"]}],"justify-self":[{"justify-self":["auto",...U()]}],"align-content":[{content:["normal",...F()]}],"align-items":[{items:[...U(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...U(),{baseline:["","last"]}]}],"place-content":[{"place-content":F()}],"place-items":[{"place-items":[...U(),"baseline"]}],"place-self":[{"place-self":["auto",...U()]}],p:[{p:$()}],px:[{px:$()}],py:[{py:$()}],ps:[{ps:$()}],pe:[{pe:$()}],pbs:[{pbs:$()}],pbe:[{pbe:$()}],pt:[{pt:$()}],pr:[{pr:$()}],pb:[{pb:$()}],pl:[{pl:$()}],m:[{m:le()}],mx:[{mx:le()}],my:[{my:le()}],ms:[{ms:le()}],me:[{me:le()}],mbs:[{mbs:le()}],mbe:[{mbe:le()}],mt:[{mt:le()}],mr:[{mr:le()}],mb:[{mb:le()}],ml:[{ml:le()}],"space-x":[{"space-x":$()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":$()}],"space-y-reverse":["space-y-reverse"],size:[{size:we()}],"inline-size":[{inline:["auto",...W()]}],"min-inline-size":[{"min-inline":["auto",...W()]}],"max-inline-size":[{"max-inline":["none",...W()]}],"block-size":[{block:["auto",...ne()]}],"min-block-size":[{"min-block":["auto",...ne()]}],"max-block-size":[{"max-block":["none",...ne()]}],w:[{w:[l,"screen",...we()]}],"min-w":[{"min-w":[l,"screen","none",...we()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[i]},...we()]}],h:[{h:["screen","lh",...we()]}],"min-h":[{"min-h":["screen","lh","none",...we()]}],"max-h":[{"max-h":["screen","lh",...we()]}],"font-size":[{text:["base",r,Js,Ga]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[a,gh,fh]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",hi,We]}],"font-family":[{font:[hh,vh,e]}],"font-features":[{"font-features":[We]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[s,Xe,We]}],"line-clamp":[{"line-clamp":[jt,"none",Xe,id]}],leading:[{leading:[o,...$()]}],"list-image":[{"list-image":["none",Xe,We]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",Xe,We]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:A()}],"text-color":[{text:A()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[..._e(),"wavy"]}],"text-decoration-thickness":[{decoration:[jt,"from-font","auto",Xe,Ga]}],"text-decoration-color":[{decoration:A()}],"underline-offset":[{"underline-offset":[jt,"auto",Xe,We]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:$()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",Xe,We]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",Xe,We]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:G()}],"bg-repeat":[{bg:q()}],"bg-size":[{bg:L()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},Ta,Xe,We],radial:["",Xe,We],conic:[Ta,Xe,We]},xh,ph]}],"bg-color":[{bg:A()}],"gradient-from-pos":[{from:H()}],"gradient-via-pos":[{via:H()}],"gradient-to-pos":[{to:H()}],"gradient-from":[{from:A()}],"gradient-via":[{via:A()}],"gradient-to":[{to:A()}],rounded:[{rounded:j()}],"rounded-s":[{"rounded-s":j()}],"rounded-e":[{"rounded-e":j()}],"rounded-t":[{"rounded-t":j()}],"rounded-r":[{"rounded-r":j()}],"rounded-b":[{"rounded-b":j()}],"rounded-l":[{"rounded-l":j()}],"rounded-ss":[{"rounded-ss":j()}],"rounded-se":[{"rounded-se":j()}],"rounded-ee":[{"rounded-ee":j()}],"rounded-es":[{"rounded-es":j()}],"rounded-tl":[{"rounded-tl":j()}],"rounded-tr":[{"rounded-tr":j()}],"rounded-br":[{"rounded-br":j()}],"rounded-bl":[{"rounded-bl":j()}],"border-w":[{border:K()}],"border-w-x":[{"border-x":K()}],"border-w-y":[{"border-y":K()}],"border-w-s":[{"border-s":K()}],"border-w-e":[{"border-e":K()}],"border-w-bs":[{"border-bs":K()}],"border-w-be":[{"border-be":K()}],"border-w-t":[{"border-t":K()}],"border-w-r":[{"border-r":K()}],"border-w-b":[{"border-b":K()}],"border-w-l":[{"border-l":K()}],"divide-x":[{"divide-x":K()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":K()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[..._e(),"hidden","none"]}],"divide-style":[{divide:[..._e(),"hidden","none"]}],"border-color":[{border:A()}],"border-color-x":[{"border-x":A()}],"border-color-y":[{"border-y":A()}],"border-color-s":[{"border-s":A()}],"border-color-e":[{"border-e":A()}],"border-color-bs":[{"border-bs":A()}],"border-color-be":[{"border-be":A()}],"border-color-t":[{"border-t":A()}],"border-color-r":[{"border-r":A()}],"border-color-b":[{"border-b":A()}],"border-color-l":[{"border-l":A()}],"divide-color":[{divide:A()}],"outline-style":[{outline:[..._e(),"none","hidden"]}],"outline-offset":[{"outline-offset":[jt,Xe,We]}],"outline-w":[{outline:["",jt,Js,Ga]}],"outline-color":[{outline:A()}],shadow:[{shadow:["","none",p,To,Mo]}],"shadow-color":[{shadow:A()}],"inset-shadow":[{"inset-shadow":["none",g,To,Mo]}],"inset-shadow-color":[{"inset-shadow":A()}],"ring-w":[{ring:K()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:A()}],"ring-offset-w":[{"ring-offset":[jt,Ga]}],"ring-offset-color":[{"ring-offset":A()}],"inset-ring-w":[{"inset-ring":K()}],"inset-ring-color":[{"inset-ring":A()}],"text-shadow":[{"text-shadow":["none",x,To,Mo]}],"text-shadow-color":[{"text-shadow":A()}],opacity:[{opacity:[jt,Xe,We]}],"mix-blend":[{"mix-blend":[...$e(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":$e()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[jt]}],"mask-image-linear-from-pos":[{"mask-linear-from":te()}],"mask-image-linear-to-pos":[{"mask-linear-to":te()}],"mask-image-linear-from-color":[{"mask-linear-from":A()}],"mask-image-linear-to-color":[{"mask-linear-to":A()}],"mask-image-t-from-pos":[{"mask-t-from":te()}],"mask-image-t-to-pos":[{"mask-t-to":te()}],"mask-image-t-from-color":[{"mask-t-from":A()}],"mask-image-t-to-color":[{"mask-t-to":A()}],"mask-image-r-from-pos":[{"mask-r-from":te()}],"mask-image-r-to-pos":[{"mask-r-to":te()}],"mask-image-r-from-color":[{"mask-r-from":A()}],"mask-image-r-to-color":[{"mask-r-to":A()}],"mask-image-b-from-pos":[{"mask-b-from":te()}],"mask-image-b-to-pos":[{"mask-b-to":te()}],"mask-image-b-from-color":[{"mask-b-from":A()}],"mask-image-b-to-color":[{"mask-b-to":A()}],"mask-image-l-from-pos":[{"mask-l-from":te()}],"mask-image-l-to-pos":[{"mask-l-to":te()}],"mask-image-l-from-color":[{"mask-l-from":A()}],"mask-image-l-to-color":[{"mask-l-to":A()}],"mask-image-x-from-pos":[{"mask-x-from":te()}],"mask-image-x-to-pos":[{"mask-x-to":te()}],"mask-image-x-from-color":[{"mask-x-from":A()}],"mask-image-x-to-color":[{"mask-x-to":A()}],"mask-image-y-from-pos":[{"mask-y-from":te()}],"mask-image-y-to-pos":[{"mask-y-to":te()}],"mask-image-y-from-color":[{"mask-y-from":A()}],"mask-image-y-to-color":[{"mask-y-to":A()}],"mask-image-radial":[{"mask-radial":[Xe,We]}],"mask-image-radial-from-pos":[{"mask-radial-from":te()}],"mask-image-radial-to-pos":[{"mask-radial-to":te()}],"mask-image-radial-from-color":[{"mask-radial-from":A()}],"mask-image-radial-to-color":[{"mask-radial-to":A()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":M()}],"mask-image-conic-pos":[{"mask-conic":[jt]}],"mask-image-conic-from-pos":[{"mask-conic-from":te()}],"mask-image-conic-to-pos":[{"mask-conic-to":te()}],"mask-image-conic-from-color":[{"mask-conic-from":A()}],"mask-image-conic-to-color":[{"mask-conic-to":A()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:G()}],"mask-repeat":[{mask:q()}],"mask-size":[{mask:L()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",Xe,We]}],filter:[{filter:["","none",Xe,We]}],blur:[{blur:De()}],brightness:[{brightness:[jt,Xe,We]}],contrast:[{contrast:[jt,Xe,We]}],"drop-shadow":[{"drop-shadow":["","none",b,To,Mo]}],"drop-shadow-color":[{"drop-shadow":A()}],grayscale:[{grayscale:["",jt,Xe,We]}],"hue-rotate":[{"hue-rotate":[jt,Xe,We]}],invert:[{invert:["",jt,Xe,We]}],saturate:[{saturate:[jt,Xe,We]}],sepia:[{sepia:["",jt,Xe,We]}],"backdrop-filter":[{"backdrop-filter":["","none",Xe,We]}],"backdrop-blur":[{"backdrop-blur":De()}],"backdrop-brightness":[{"backdrop-brightness":[jt,Xe,We]}],"backdrop-contrast":[{"backdrop-contrast":[jt,Xe,We]}],"backdrop-grayscale":[{"backdrop-grayscale":["",jt,Xe,We]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[jt,Xe,We]}],"backdrop-invert":[{"backdrop-invert":["",jt,Xe,We]}],"backdrop-opacity":[{"backdrop-opacity":[jt,Xe,We]}],"backdrop-saturate":[{"backdrop-saturate":[jt,Xe,We]}],"backdrop-sepia":[{"backdrop-sepia":["",jt,Xe,We]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":$()}],"border-spacing-x":[{"border-spacing-x":$()}],"border-spacing-y":[{"border-spacing-y":$()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",Xe,We]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[jt,"initial",Xe,We]}],ease:[{ease:["linear","initial",w,Xe,We]}],delay:[{delay:[jt,Xe,We]}],animate:[{animate:["none",E,Xe,We]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[S,Xe,We]}],"perspective-origin":[{"perspective-origin":Z()}],rotate:[{rotate:tt()}],"rotate-x":[{"rotate-x":tt()}],"rotate-y":[{"rotate-y":tt()}],"rotate-z":[{"rotate-z":tt()}],scale:[{scale:st()}],"scale-x":[{"scale-x":st()}],"scale-y":[{"scale-y":st()}],"scale-z":[{"scale-z":st()}],"scale-3d":["scale-3d"],skew:[{skew:Ge()}],"skew-x":[{"skew-x":Ge()}],"skew-y":[{"skew-y":Ge()}],transform:[{transform:[Xe,We,"","none","gpu","cpu"]}],"transform-origin":[{origin:Z()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:rt()}],"translate-x":[{"translate-x":rt()}],"translate-y":[{"translate-y":rt()}],"translate-z":[{"translate-z":rt()}],"translate-none":["translate-none"],accent:[{accent:A()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:A()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",Xe,We]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":$()}],"scroll-mx":[{"scroll-mx":$()}],"scroll-my":[{"scroll-my":$()}],"scroll-ms":[{"scroll-ms":$()}],"scroll-me":[{"scroll-me":$()}],"scroll-mbs":[{"scroll-mbs":$()}],"scroll-mbe":[{"scroll-mbe":$()}],"scroll-mt":[{"scroll-mt":$()}],"scroll-mr":[{"scroll-mr":$()}],"scroll-mb":[{"scroll-mb":$()}],"scroll-ml":[{"scroll-ml":$()}],"scroll-p":[{"scroll-p":$()}],"scroll-px":[{"scroll-px":$()}],"scroll-py":[{"scroll-py":$()}],"scroll-ps":[{"scroll-ps":$()}],"scroll-pe":[{"scroll-pe":$()}],"scroll-pbs":[{"scroll-pbs":$()}],"scroll-pbe":[{"scroll-pbe":$()}],"scroll-pt":[{"scroll-pt":$()}],"scroll-pr":[{"scroll-pr":$()}],"scroll-pb":[{"scroll-pb":$()}],"scroll-pl":[{"scroll-pl":$()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",Xe,We]}],fill:[{fill:["none",...A()]}],"stroke-w":[{stroke:[jt,Js,Ga,id]}],stroke:[{stroke:["none",...A()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},yh=Zp(bh);function wr(...t){return yh(Lc(t))}const Ui="dartlab-conversations",cd=50;function wh(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function kh(){try{const t=localStorage.getItem(Ui);return t?JSON.parse(t):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const Sh=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function ud(t){return t.map(e=>({...e,messages:e.messages.map(r=>{if(r.role!=="assistant")return r;const a={};for(const[s,o]of Object.entries(r))Sh.includes(s)||(a[s]=o);return a})}))}function fd(t){try{const e={conversations:ud(t.conversations),activeId:t.activeId};localStorage.setItem(Ui,JSON.stringify(e))}catch{if(t.conversations.length>5){t.conversations=t.conversations.slice(0,t.conversations.length-5);try{const e={conversations:ud(t.conversations),activeId:t.activeId};localStorage.setItem(Ui,JSON.stringify(e))}catch{}}}}function Ch(){const t=kh(),e=t.conversations||[],r=e.find(w=>w.id===t.activeId)?t.activeId:null;let a=Y(Ut(e)),s=Y(Ut(r)),o=null;function i(){o&&clearTimeout(o),o=setTimeout(()=>{fd({conversations:n(a),activeId:n(s)}),o=null},300)}function l(){o&&clearTimeout(o),o=null,fd({conversations:n(a),activeId:n(s)})}function u(){return n(a).find(w=>w.id===n(s))||null}function f(){const w={id:wh(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return v(a,[w,...n(a)],!0),n(a).length>cd&&v(a,n(a).slice(0,cd),!0),v(s,w.id,!0),l(),w.id}function p(w){n(a).find(E=>E.id===w)&&(v(s,w,!0),l())}function g(w,E,D=null){const M=u();if(!M)return;const Z={role:w,text:E};D&&(Z.meta=D),M.messages=[...M.messages,Z],M.updatedAt=Date.now(),M.title==="새 대화"&&w==="user"&&(M.title=E.length>30?E.slice(0,30)+"...":E),v(a,[...n(a)],!0),l()}function x(w){const E=u();if(!E||E.messages.length===0)return;const D=E.messages[E.messages.length-1];Object.assign(D,w),E.updatedAt=Date.now(),v(a,[...n(a)],!0),i()}function b(w){v(a,n(a).filter(E=>E.id!==w),!0),n(s)===w&&v(s,n(a).length>0?n(a)[0].id:null,!0),l()}function k(){const w=u();!w||w.messages.length===0||(w.messages=w.messages.slice(0,-1),w.updatedAt=Date.now(),v(a,[...n(a)],!0),l())}function S(w,E){const D=n(a).find(M=>M.id===w);D&&(D.title=E,v(a,[...n(a)],!0),l())}function _(){v(a,[],!0),v(s,null),l()}return{get conversations(){return n(a)},get activeId(){return n(s)},get active(){return u()},createConversation:f,setActive:p,addMessage:g,updateLastMessage:x,removeLastMessage:k,deleteConversation:b,updateTitle:S,clearAll:_,flush:l}}const nu="dartlab-workspace",$h=6;function au(){return typeof window<"u"&&typeof localStorage<"u"}function Mh(){if(!au())return{};try{const t=localStorage.getItem(nu);return t?JSON.parse(t):{}}catch{return{}}}function Th(t){au()&&localStorage.setItem(nu,JSON.stringify(t))}function zh(){const t=Mh();let e=Y("chat"),r=Y(!1),a=Y(null),s=Y(null),o=Y("explore"),i=Y(null),l=Y(null),u=Y(null),f=Y(null),p=Y(null),g=Y(Ut(t.selectedCompany||null)),x=Y(Ut(t.recentCompanies||[]));function b(){Th({selectedCompany:n(g),recentCompanies:n(x)})}function k(J){if(!(J!=null&&J.stockCode))return;const me={stockCode:J.stockCode,corpName:J.corpName||J.company||J.stockCode,company:J.company||J.corpName||J.stockCode,market:J.market||""};v(x,[me,...n(x).filter(B=>B.stockCode!==me.stockCode)].slice(0,$h),!0)}function S(J){v(e,J,!0)}function _(J){J&&(v(g,J,!0),k(J)),v(e,"viewer"),v(r,!1),b()}function w(J){v(a,"data"),v(s,J,!0),v(r,!0),$("explore")}function E(){v(r,!1)}function D(J){v(g,J,!0),J&&k(J),b()}function M(J,me){var B,Te,F,U;!(J!=null&&J.company)&&!(J!=null&&J.stockCode)||(v(g,{...n(g)||{},...me||{},corpName:J.company||((B=n(g))==null?void 0:B.corpName)||(me==null?void 0:me.corpName)||(me==null?void 0:me.company),company:J.company||((Te=n(g))==null?void 0:Te.company)||(me==null?void 0:me.company)||(me==null?void 0:me.corpName),stockCode:J.stockCode||((F=n(g))==null?void 0:F.stockCode)||(me==null?void 0:me.stockCode),market:((U=n(g))==null?void 0:U.market)||(me==null?void 0:me.market)||""},!0),k(n(g)),b())}function Z(J,me,B=null){v(u,J,!0),v(f,me||J,!0),v(p,B,!0)}function ce(J,me=null){v(a,"data"),v(r,!0),v(o,"evidence"),v(i,J,!0),v(l,Number.isInteger(me)?me:null,!0)}function P(){v(i,null),v(l,null)}function $(J){v(o,J||"explore",!0),n(o)!=="evidence"&&P()}function X(){return n(e)==="viewer"&&n(g)&&n(u)?{type:"viewer",company:n(g),topic:n(u),topicLabel:n(f),period:n(p)}:n(r)?n(a)==="viewer"&&n(g)?{type:"viewer",company:n(g),topic:n(u),topicLabel:n(f),period:n(p)}:n(a)==="data"&&n(s)?{type:"data",data:n(s)}:null:null}return{get activeView(){return n(e)},get panelOpen(){return n(r)},get panelMode(){return n(a)},get panelData(){return n(s)},get activeTab(){return n(o)},get activeEvidenceSection(){return n(i)},get selectedEvidenceIndex(){return n(l)},get selectedCompany(){return n(g)},get recentCompanies(){return n(x)},get viewerTopic(){return n(u)},get viewerTopicLabel(){return n(f)},get viewerPeriod(){return n(p)},switchView:S,openViewer:_,openData:w,openEvidence:ce,closePanel:E,selectCompany:D,setViewerTopic:Z,clearEvidenceSelection:P,setTab:$,syncCompanyFromMessage:M,getViewContext:X}}const Eh="ENTRIES",su="KEYS",ou="VALUES",Xr="";class mi{constructor(e,r){const a=e._tree,s=Array.from(a.keys());this.set=e,this._type=r,this._path=s.length>0?[{node:a,keys:s}]:[]}next(){const e=this.dive();return this.backtrack(),e}dive(){if(this._path.length===0)return{done:!0,value:void 0};const{node:e,keys:r}=ms(this._path);if(ms(r)===Xr)return{done:!1,value:this.result()};const a=e.get(ms(r));return this._path.push({node:a,keys:Array.from(a.keys())}),this.dive()}backtrack(){if(this._path.length===0)return;const e=ms(this._path).keys;e.pop(),!(e.length>0)&&(this._path.pop(),this.backtrack())}key(){return this.set._prefix+this._path.map(({keys:e})=>ms(e)).filter(e=>e!==Xr).join("")}value(){return ms(this._path).node.get(Xr)}result(){switch(this._type){case ou:return this.value();case su:return this.key();default:return[this.key(),this.value()]}}[Symbol.iterator](){return this}}const ms=t=>t[t.length-1],Ih=(t,e,r)=>{const a=new Map;if(e===void 0)return a;const s=e.length+1,o=s+r,i=new Uint8Array(o*s).fill(r+1);for(let l=0;l<s;++l)i[l]=l;for(let l=1;l<o;++l)i[l*s]=l;return iu(t,e,r,a,i,1,s,""),a},iu=(t,e,r,a,s,o,i,l)=>{const u=o*i;e:for(const f of t.keys())if(f===Xr){const p=s[u-1];p<=r&&a.set(l,[t.get(f),p])}else{let p=o;for(let g=0;g<f.length;++g,++p){const x=f[g],b=i*p,k=b-i;let S=s[b];const _=Math.max(0,p-r-1),w=Math.min(i-1,p+r);for(let E=_;E<w;++E){const D=x!==e[E],M=s[k+E]+ +D,Z=s[k+E+1]+1,ce=s[b+E]+1,P=s[b+E+1]=Math.min(M,Z,ce);P<S&&(S=P)}if(S>r)continue e}iu(t.get(f),e,r,a,s,p,i,l+f)}};class Na{constructor(e=new Map,r=""){this._size=void 0,this._tree=e,this._prefix=r}atPrefix(e){if(!e.startsWith(this._prefix))throw new Error("Mismatched prefix");const[r,a]=Vo(this._tree,e.slice(this._prefix.length));if(r===void 0){const[s,o]=yl(a);for(const i of s.keys())if(i!==Xr&&i.startsWith(o)){const l=new Map;return l.set(i.slice(o.length),s.get(i)),new Na(l,e)}}return new Na(r,e)}clear(){this._size=void 0,this._tree.clear()}delete(e){return this._size=void 0,Ah(this._tree,e)}entries(){return new mi(this,Eh)}forEach(e){for(const[r,a]of this)e(r,a,this)}fuzzyGet(e,r){return Ih(this._tree,e,r)}get(e){const r=Hi(this._tree,e);return r!==void 0?r.get(Xr):void 0}has(e){const r=Hi(this._tree,e);return r!==void 0&&r.has(Xr)}keys(){return new mi(this,su)}set(e,r){if(typeof e!="string")throw new Error("key must be a string");return this._size=void 0,xi(this._tree,e).set(Xr,r),this}get size(){if(this._size)return this._size;this._size=0;const e=this.entries();for(;!e.next().done;)this._size+=1;return this._size}update(e,r){if(typeof e!="string")throw new Error("key must be a string");this._size=void 0;const a=xi(this._tree,e);return a.set(Xr,r(a.get(Xr))),this}fetch(e,r){if(typeof e!="string")throw new Error("key must be a string");this._size=void 0;const a=xi(this._tree,e);let s=a.get(Xr);return s===void 0&&a.set(Xr,s=r()),s}values(){return new mi(this,ou)}[Symbol.iterator](){return this.entries()}static from(e){const r=new Na;for(const[a,s]of e)r.set(a,s);return r}static fromObject(e){return Na.from(Object.entries(e))}}const Vo=(t,e,r=[])=>{if(e.length===0||t==null)return[t,r];for(const a of t.keys())if(a!==Xr&&e.startsWith(a))return r.push([t,a]),Vo(t.get(a),e.slice(a.length),r);return r.push([t,e]),Vo(void 0,"",r)},Hi=(t,e)=>{if(e.length===0||t==null)return t;for(const r of t.keys())if(r!==Xr&&e.startsWith(r))return Hi(t.get(r),e.slice(r.length))},xi=(t,e)=>{const r=e.length;e:for(let a=0;t&&a<r;){for(const o of t.keys())if(o!==Xr&&e[a]===o[0]){const i=Math.min(r-a,o.length);let l=1;for(;l<i&&e[a+l]===o[l];)++l;const u=t.get(o);if(l===o.length)t=u;else{const f=new Map;f.set(o.slice(l),u),t.set(e.slice(a,a+l),f),t.delete(o),t=f}a+=l;continue e}const s=new Map;return t.set(e.slice(a),s),s}return t},Ah=(t,e)=>{const[r,a]=Vo(t,e);if(r!==void 0){if(r.delete(Xr),r.size===0)lu(a);else if(r.size===1){const[s,o]=r.entries().next().value;du(a,s,o)}}},lu=t=>{if(t.length===0)return;const[e,r]=yl(t);if(e.delete(r),e.size===0)lu(t.slice(0,-1));else if(e.size===1){const[a,s]=e.entries().next().value;a!==Xr&&du(t.slice(0,-1),a,s)}},du=(t,e,r)=>{if(t.length===0)return;const[a,s]=yl(t);a.set(s+e,r),a.delete(s)},yl=t=>t[t.length-1],wl="or",cu="and",Lh="and_not";class gs{constructor(e){if((e==null?void 0:e.fields)==null)throw new Error('MiniSearch: option "fields" must be provided');const r=e.autoVacuum==null||e.autoVacuum===!0?bi:e.autoVacuum;this._options={..._i,...e,autoVacuum:r,searchOptions:{...vd,...e.searchOptions||{}},autoSuggestOptions:{...Rh,...e.autoSuggestOptions||{}}},this._index=new Na,this._documentCount=0,this._documentIds=new Map,this._idToShortId=new Map,this._fieldIds={},this._fieldLength=new Map,this._avgFieldLength=[],this._nextId=0,this._storedFields=new Map,this._dirtCount=0,this._currentVacuum=null,this._enqueuedVacuum=null,this._enqueuedVacuumConditions=Ki,this.addFields(this._options.fields)}add(e){const{extractField:r,stringifyField:a,tokenize:s,processTerm:o,fields:i,idField:l}=this._options,u=r(e,l);if(u==null)throw new Error(`MiniSearch: document does not have ID field "${l}"`);if(this._idToShortId.has(u))throw new Error(`MiniSearch: duplicate ID ${u}`);const f=this.addDocumentId(u);this.saveStoredFields(f,e);for(const p of i){const g=r(e,p);if(g==null)continue;const x=s(a(g,p),p),b=this._fieldIds[p],k=new Set(x).size;this.addFieldLength(f,b,this._documentCount-1,k);for(const S of x){const _=o(S,p);if(Array.isArray(_))for(const w of _)this.addTerm(b,f,w);else _&&this.addTerm(b,f,_)}}}addAll(e){for(const r of e)this.add(r)}addAllAsync(e,r={}){const{chunkSize:a=10}=r,s={chunk:[],promise:Promise.resolve()},{chunk:o,promise:i}=e.reduce(({chunk:l,promise:u},f,p)=>(l.push(f),(p+1)%a===0?{chunk:[],promise:u.then(()=>new Promise(g=>setTimeout(g,0))).then(()=>this.addAll(l))}:{chunk:l,promise:u}),s);return i.then(()=>this.addAll(o))}remove(e){const{tokenize:r,processTerm:a,extractField:s,stringifyField:o,fields:i,idField:l}=this._options,u=s(e,l);if(u==null)throw new Error(`MiniSearch: document does not have ID field "${l}"`);const f=this._idToShortId.get(u);if(f==null)throw new Error(`MiniSearch: cannot remove document with ID ${u}: it is not in the index`);for(const p of i){const g=s(e,p);if(g==null)continue;const x=r(o(g,p),p),b=this._fieldIds[p],k=new Set(x).size;this.removeFieldLength(f,b,this._documentCount,k);for(const S of x){const _=a(S,p);if(Array.isArray(_))for(const w of _)this.removeTerm(b,f,w);else _&&this.removeTerm(b,f,_)}}this._storedFields.delete(f),this._documentIds.delete(f),this._idToShortId.delete(u),this._fieldLength.delete(f),this._documentCount-=1}removeAll(e){if(e)for(const r of e)this.remove(r);else{if(arguments.length>0)throw new Error("Expected documents to be present. Omit the argument to remove all documents.");this._index=new Na,this._documentCount=0,this._documentIds=new Map,this._idToShortId=new Map,this._fieldLength=new Map,this._avgFieldLength=[],this._storedFields=new Map,this._nextId=0}}discard(e){const r=this._idToShortId.get(e);if(r==null)throw new Error(`MiniSearch: cannot discard document with ID ${e}: it is not in the index`);this._idToShortId.delete(e),this._documentIds.delete(r),this._storedFields.delete(r),(this._fieldLength.get(r)||[]).forEach((a,s)=>{this.removeFieldLength(r,s,this._documentCount,a)}),this._fieldLength.delete(r),this._documentCount-=1,this._dirtCount+=1,this.maybeAutoVacuum()}maybeAutoVacuum(){if(this._options.autoVacuum===!1)return;const{minDirtFactor:e,minDirtCount:r,batchSize:a,batchWait:s}=this._options.autoVacuum;this.conditionalVacuum({batchSize:a,batchWait:s},{minDirtCount:r,minDirtFactor:e})}discardAll(e){const r=this._options.autoVacuum;try{this._options.autoVacuum=!1;for(const a of e)this.discard(a)}finally{this._options.autoVacuum=r}this.maybeAutoVacuum()}replace(e){const{idField:r,extractField:a}=this._options,s=a(e,r);this.discard(s),this.add(e)}vacuum(e={}){return this.conditionalVacuum(e)}conditionalVacuum(e,r){return this._currentVacuum?(this._enqueuedVacuumConditions=this._enqueuedVacuumConditions&&r,this._enqueuedVacuum!=null?this._enqueuedVacuum:(this._enqueuedVacuum=this._currentVacuum.then(()=>{const a=this._enqueuedVacuumConditions;return this._enqueuedVacuumConditions=Ki,this.performVacuuming(e,a)}),this._enqueuedVacuum)):this.vacuumConditionsMet(r)===!1?Promise.resolve():(this._currentVacuum=this.performVacuuming(e),this._currentVacuum)}async performVacuuming(e,r){const a=this._dirtCount;if(this.vacuumConditionsMet(r)){const s=e.batchSize||qi.batchSize,o=e.batchWait||qi.batchWait;let i=1;for(const[l,u]of this._index){for(const[f,p]of u)for(const[g]of p)this._documentIds.has(g)||(p.size<=1?u.delete(f):p.delete(g));this._index.get(l).size===0&&this._index.delete(l),i%s===0&&await new Promise(f=>setTimeout(f,o)),i+=1}this._dirtCount-=a}await null,this._currentVacuum=this._enqueuedVacuum,this._enqueuedVacuum=null}vacuumConditionsMet(e){if(e==null)return!0;let{minDirtCount:r,minDirtFactor:a}=e;return r=r||bi.minDirtCount,a=a||bi.minDirtFactor,this.dirtCount>=r&&this.dirtFactor>=a}get isVacuuming(){return this._currentVacuum!=null}get dirtCount(){return this._dirtCount}get dirtFactor(){return this._dirtCount/(1+this._documentCount+this._dirtCount)}has(e){return this._idToShortId.has(e)}getStoredFields(e){const r=this._idToShortId.get(e);if(r!=null)return this._storedFields.get(r)}search(e,r={}){const{searchOptions:a}=this._options,s={...a,...r},o=this.executeQuery(e,r),i=[];for(const[l,{score:u,terms:f,match:p}]of o){const g=f.length||1,x={id:this._documentIds.get(l),score:u*g,terms:Object.keys(p),queryTerms:f,match:p};Object.assign(x,this._storedFields.get(l)),(s.filter==null||s.filter(x))&&i.push(x)}return e===gs.wildcard&&s.boostDocument==null||i.sort(hd),i}autoSuggest(e,r={}){r={...this._options.autoSuggestOptions,...r};const a=new Map;for(const{score:o,terms:i}of this.search(e,r)){const l=i.join(" "),u=a.get(l);u!=null?(u.score+=o,u.count+=1):a.set(l,{score:o,terms:i,count:1})}const s=[];for(const[o,{score:i,terms:l,count:u}]of a)s.push({suggestion:o,terms:l,score:i/u});return s.sort(hd),s}get documentCount(){return this._documentCount}get termCount(){return this._index.size}static loadJSON(e,r){if(r==null)throw new Error("MiniSearch: loadJSON should be given the same options used when serializing the index");return this.loadJS(JSON.parse(e),r)}static async loadJSONAsync(e,r){if(r==null)throw new Error("MiniSearch: loadJSON should be given the same options used when serializing the index");return this.loadJSAsync(JSON.parse(e),r)}static getDefault(e){if(_i.hasOwnProperty(e))return gi(_i,e);throw new Error(`MiniSearch: unknown option "${e}"`)}static loadJS(e,r){const{index:a,documentIds:s,fieldLength:o,storedFields:i,serializationVersion:l}=e,u=this.instantiateMiniSearch(e,r);u._documentIds=zo(s),u._fieldLength=zo(o),u._storedFields=zo(i);for(const[f,p]of u._documentIds)u._idToShortId.set(p,f);for(const[f,p]of a){const g=new Map;for(const x of Object.keys(p)){let b=p[x];l===1&&(b=b.ds),g.set(parseInt(x,10),zo(b))}u._index.set(f,g)}return u}static async loadJSAsync(e,r){const{index:a,documentIds:s,fieldLength:o,storedFields:i,serializationVersion:l}=e,u=this.instantiateMiniSearch(e,r);u._documentIds=await Eo(s),u._fieldLength=await Eo(o),u._storedFields=await Eo(i);for(const[p,g]of u._documentIds)u._idToShortId.set(g,p);let f=0;for(const[p,g]of a){const x=new Map;for(const b of Object.keys(g)){let k=g[b];l===1&&(k=k.ds),x.set(parseInt(b,10),await Eo(k))}++f%1e3===0&&await uu(0),u._index.set(p,x)}return u}static instantiateMiniSearch(e,r){const{documentCount:a,nextId:s,fieldIds:o,averageFieldLength:i,dirtCount:l,serializationVersion:u}=e;if(u!==1&&u!==2)throw new Error("MiniSearch: cannot deserialize an index created with an incompatible version");const f=new gs(r);return f._documentCount=a,f._nextId=s,f._idToShortId=new Map,f._fieldIds=o,f._avgFieldLength=i,f._dirtCount=l||0,f._index=new Na,f}executeQuery(e,r={}){if(e===gs.wildcard)return this.executeWildcardQuery(r);if(typeof e!="string"){const x={...r,...e,queries:void 0},b=e.queries.map(k=>this.executeQuery(k,x));return this.combineResults(b,x.combineWith)}const{tokenize:a,processTerm:s,searchOptions:o}=this._options,i={tokenize:a,processTerm:s,...o,...r},{tokenize:l,processTerm:u}=i,g=l(e).flatMap(x=>u(x)).filter(x=>!!x).map(Oh(i)).map(x=>this.executeQuerySpec(x,i));return this.combineResults(g,i.combineWith)}executeQuerySpec(e,r){const a={...this._options.searchOptions,...r},s=(a.fields||this._options.fields).reduce((S,_)=>({...S,[_]:gi(a.boost,_)||1}),{}),{boostDocument:o,weights:i,maxFuzzy:l,bm25:u}=a,{fuzzy:f,prefix:p}={...vd.weights,...i},g=this._index.get(e.term),x=this.termResults(e.term,e.term,1,e.termBoost,g,s,o,u);let b,k;if(e.prefix&&(b=this._index.atPrefix(e.term)),e.fuzzy){const S=e.fuzzy===!0?.2:e.fuzzy,_=S<1?Math.min(l,Math.round(e.term.length*S)):S;_&&(k=this._index.fuzzyGet(e.term,_))}if(b)for(const[S,_]of b){const w=S.length-e.term.length;if(!w)continue;k==null||k.delete(S);const E=p*S.length/(S.length+.3*w);this.termResults(e.term,S,E,e.termBoost,_,s,o,u,x)}if(k)for(const S of k.keys()){const[_,w]=k.get(S);if(!w)continue;const E=f*S.length/(S.length+w);this.termResults(e.term,S,E,e.termBoost,_,s,o,u,x)}return x}executeWildcardQuery(e){const r=new Map,a={...this._options.searchOptions,...e};for(const[s,o]of this._documentIds){const i=a.boostDocument?a.boostDocument(o,"",this._storedFields.get(s)):1;r.set(s,{score:i,terms:[],match:{}})}return r}combineResults(e,r=wl){if(e.length===0)return new Map;const a=r.toLowerCase(),s=Nh[a];if(!s)throw new Error(`Invalid combination operator: ${r}`);return e.reduce(s)||new Map}toJSON(){const e=[];for(const[r,a]of this._index){const s={};for(const[o,i]of a)s[o]=Object.fromEntries(i);e.push([r,s])}return{documentCount:this._documentCount,nextId:this._nextId,documentIds:Object.fromEntries(this._documentIds),fieldIds:this._fieldIds,fieldLength:Object.fromEntries(this._fieldLength),averageFieldLength:this._avgFieldLength,storedFields:Object.fromEntries(this._storedFields),dirtCount:this._dirtCount,index:e,serializationVersion:2}}termResults(e,r,a,s,o,i,l,u,f=new Map){if(o==null)return f;for(const p of Object.keys(i)){const g=i[p],x=this._fieldIds[p],b=o.get(x);if(b==null)continue;let k=b.size;const S=this._avgFieldLength[x];for(const _ of b.keys()){if(!this._documentIds.has(_)){this.removeTerm(x,_,r),k-=1;continue}const w=l?l(this._documentIds.get(_),r,this._storedFields.get(_)):1;if(!w)continue;const E=b.get(_),D=this._fieldLength.get(_)[x],M=Dh(E,k,this._documentCount,D,S,u),Z=a*s*g*w*M,ce=f.get(_);if(ce){ce.score+=Z,Fh(ce.terms,e);const P=gi(ce.match,r);P?P.push(p):ce.match[r]=[p]}else f.set(_,{score:Z,terms:[e],match:{[r]:[p]}})}}return f}addTerm(e,r,a){const s=this._index.fetch(a,md);let o=s.get(e);if(o==null)o=new Map,o.set(r,1),s.set(e,o);else{const i=o.get(r);o.set(r,(i||0)+1)}}removeTerm(e,r,a){if(!this._index.has(a)){this.warnDocumentChanged(r,e,a);return}const s=this._index.fetch(a,md),o=s.get(e);o==null||o.get(r)==null?this.warnDocumentChanged(r,e,a):o.get(r)<=1?o.size<=1?s.delete(e):o.delete(r):o.set(r,o.get(r)-1),this._index.get(a).size===0&&this._index.delete(a)}warnDocumentChanged(e,r,a){for(const s of Object.keys(this._fieldIds))if(this._fieldIds[s]===r){this._options.logger("warn",`MiniSearch: document with ID ${this._documentIds.get(e)} has changed before removal: term "${a}" was not present in field "${s}". Removing a document after it has changed can corrupt the index!`,"version_conflict");return}}addDocumentId(e){const r=this._nextId;return this._idToShortId.set(e,r),this._documentIds.set(r,e),this._documentCount+=1,this._nextId+=1,r}addFields(e){for(let r=0;r<e.length;r++)this._fieldIds[e[r]]=r}addFieldLength(e,r,a,s){let o=this._fieldLength.get(e);o==null&&this._fieldLength.set(e,o=[]),o[r]=s;const l=(this._avgFieldLength[r]||0)*a+s;this._avgFieldLength[r]=l/(a+1)}removeFieldLength(e,r,a,s){if(a===1){this._avgFieldLength[r]=0;return}const o=this._avgFieldLength[r]*a-s;this._avgFieldLength[r]=o/(a-1)}saveStoredFields(e,r){const{storeFields:a,extractField:s}=this._options;if(a==null||a.length===0)return;let o=this._storedFields.get(e);o==null&&this._storedFields.set(e,o={});for(const i of a){const l=s(r,i);l!==void 0&&(o[i]=l)}}}gs.wildcard=Symbol("*");const gi=(t,e)=>Object.prototype.hasOwnProperty.call(t,e)?t[e]:void 0,Nh={[wl]:(t,e)=>{for(const r of e.keys()){const a=t.get(r);if(a==null)t.set(r,e.get(r));else{const{score:s,terms:o,match:i}=e.get(r);a.score=a.score+s,a.match=Object.assign(a.match,i),pd(a.terms,o)}}return t},[cu]:(t,e)=>{const r=new Map;for(const a of e.keys()){const s=t.get(a);if(s==null)continue;const{score:o,terms:i,match:l}=e.get(a);pd(s.terms,i),r.set(a,{score:s.score+o,terms:s.terms,match:Object.assign(s.match,l)})}return r},[Lh]:(t,e)=>{for(const r of e.keys())t.delete(r);return t}},Ph={k:1.2,b:.7,d:.5},Dh=(t,e,r,a,s,o)=>{const{k:i,b:l,d:u}=o;return Math.log(1+(r-e+.5)/(e+.5))*(u+t*(i+1)/(t+i*(1-l+l*a/s)))},Oh=t=>(e,r,a)=>{const s=typeof t.fuzzy=="function"?t.fuzzy(e,r,a):t.fuzzy||!1,o=typeof t.prefix=="function"?t.prefix(e,r,a):t.prefix===!0,i=typeof t.boostTerm=="function"?t.boostTerm(e,r,a):1;return{term:e,fuzzy:s,prefix:o,termBoost:i}},_i={idField:"id",extractField:(t,e)=>t[e],stringifyField:(t,e)=>t.toString(),tokenize:t=>t.split(jh),processTerm:t=>t.toLowerCase(),fields:void 0,searchOptions:void 0,storeFields:[],logger:(t,e)=>{typeof(console==null?void 0:console[t])=="function"&&console[t](e)},autoVacuum:!0},vd={combineWith:wl,prefix:!1,fuzzy:!1,maxFuzzy:6,boost:{},weights:{fuzzy:.45,prefix:.375},bm25:Ph},Rh={combineWith:cu,prefix:(t,e,r)=>e===r.length-1},qi={batchSize:1e3,batchWait:10},Ki={minDirtFactor:.1,minDirtCount:20},bi={...qi,...Ki},Fh=(t,e)=>{t.includes(e)||t.push(e)},pd=(t,e)=>{for(const r of e)t.includes(r)||t.push(r)},hd=({score:t},{score:e})=>e-t,md=()=>new Map,zo=t=>{const e=new Map;for(const r of Object.keys(t))e.set(parseInt(r,10),t[r]);return e},Eo=async t=>{const e=new Map;let r=0;for(const a of Object.keys(t))e.set(parseInt(a,10),t[a]),++r%1e3===0&&await uu(0);return e},uu=t=>new Promise(e=>setTimeout(e,t)),jh=/[\n\r\p{Z}\p{P}]+/u;function Bh(){try{const t=localStorage.getItem("dartlab-bookmarks");return t?JSON.parse(t):{}}catch{return{}}}function Vh(t){try{localStorage.setItem("dartlab-bookmarks",JSON.stringify(t))}catch{}}function Uh(){let t=Y(null),e=Y(null),r=Y(null),a=Y(!1),s=Y(null),o=Y(null),i=Y(Ut(new Set)),l=Y(null),u=Y(!1),f=Y(null),p=new Map,g=Y(null),x=Y(!1),b=Y(null),k=Y(!1),S=Y(Ut(new Map)),_=Y(null),w=null,E=Y(!1),D=Y(Ut(Bh()));async function M(A){var G,q,L,H;if(!(A===n(t)&&(n(r)||n(a)))){v(t,A,!0),v(e,null),v(r,null),v(s,null),v(o,null),v(l,null),v(f,null),p=new Map,v(i,new Set,!0),v(g,null),v(b,null),v(S,new Map,!0),w=null,v(E,!1),v(a,!0);try{const j=await Sp(A);v(r,j.toc,!0),v(e,j.corpName,!0),((q=(G=j.toc)==null?void 0:G.chapters)==null?void 0:q.length)>0&&v(i,new Set([j.toc.chapters[0].chapter]),!0),j.firstTopic&&j.viewer&&(v(s,j.firstTopic,!0),v(o,j.firstChapter,!0),v(l,j.viewer,!0),p.set(j.firstTopic,j.viewer),v(B,new Set([j.firstTopic]),!0)),j.diffSummary&&v(f,j.diffSummary,!0),Z(A),ce(A),P(A)}catch(j){console.error("초기 로드 실패:",j);try{const K=await Cp(A);if(v(r,K,!0),v(e,K.corpName,!0),((L=K.chapters)==null?void 0:L.length)>0&&(v(i,new Set([K.chapters[0].chapter]),!0),((H=K.chapters[0].topics)==null?void 0:H.length)>0)){const _e=K.chapters[0].topics[0];await J(_e.topic,K.chapters[0].chapter)}Z(A),ce(A),P(A)}catch(K){console.error("TOC 로드 실패:",K)}}v(a,!1)}}async function Z(A){var G;if(((G=n(g))==null?void 0:G.stockCode)!==A){v(x,!0);try{const q=await zp(A);q.available?v(g,q,!0):v(g,null)}catch{v(g,null)}v(x,!1)}}async function ce(A){v(k,!0);try{const G=await Ep(A);G.available?v(b,G,!0):v(b,null)}catch{v(b,null)}v(k,!1)}async function P(A){try{const G=await Tp(A);if(!G.documents||G.documents.length===0)return;const q=new gs({fields:["label","text"],storeFields:["topic","label","chapter","period","blockType"],searchOptions:{boost:{label:3},fuzzy:.2,prefix:!0}});q.addAll(G.documents),w=q,v(E,!0)}catch(G){console.error("SearchIndex 로드 실패:",G)}}function $(A){if(!w||!(A!=null&&A.trim()))return[];const G=w.search(A.trim(),{fuzzy:.2,prefix:!0,boost:{label:3}}),q=new Map;for(const L of G){const H=L.topic;(!q.has(H)||q.get(H).score<L.score)&&q.set(H,L)}return[...q.values()].sort((L,H)=>H.score-L.score).slice(0,20).map(L=>({topic:L.topic,label:L.label,chapter:L.chapter,period:L.period,blockType:L.blockType,score:L.score,source:"minisearch"}))}function X(A){v(_,A||null,!0)}async function J(A,G){if(A!==n(s)){if(v(s,A,!0),v(_,null),v(o,G,!0),G&&!n(i).has(G)&&v(i,new Set([...n(i),G]),!0),p.has(A)){v(l,p.get(A),!0),v(B,new Set([...n(B),A]),!0);return}v(u,!0),v(l,null),v(f,null);try{const[q,L]=await Promise.allSettled([nd(n(t),A),$p(n(t),A)]);q.status==="fulfilled"&&(v(l,q.value,!0),p.set(A,q.value)),L.status==="fulfilled"&&v(f,L.value,!0)}catch(q){console.error("Topic 로드 실패:",q)}v(u,!1)}}let me=new Set,B=Y(Ut(new Set));async function Te(A){if(!(!A||!n(t)||p.has(A)||me.has(A))){me.add(A);try{const G=await nd(n(t),A);p.set(A,G)}catch{}me.delete(A)}}function F(A){const G=new Set(n(i));G.has(A)?G.delete(A):G.add(A),v(i,G,!0)}function U(A){return n(S).get(A)??null}function le(A,G){const q=new Map(n(S));q.set(A,G),v(S,q,!0)}function we(){return n(D)[n(t)]||[]}function W(A){return(n(D)[n(t)]||[]).includes(A)}function ne(A){const G=n(D)[n(t)]||[],q=G.includes(A)?G.filter(L=>L!==A):[A,...G];v(D,{...n(D),[n(t)]:q},!0),Vh(n(D))}return{get stockCode(){return n(t)},get corpName(){return n(e)},get toc(){return n(r)},get tocLoading(){return n(a)},get selectedTopic(){return n(s)},get selectedChapter(){return n(o)},get expandedChapters(){return n(i)},get topicData(){return n(l)},get topicLoading(){return n(u)},get diffSummary(){return n(f)},get insightData(){return n(g)},get insightLoading(){return n(x)},get networkData(){return n(b)},get networkLoading(){return n(k)},get searchHighlight(){return n(_)},get searchIndexReady(){return n(E)},loadCompany:M,setSearchHighlight:X,searchSections:$,get visitedTopics(){return n(B)},selectTopic:J,prefetchTopic:Te,toggleChapter:F,getTopicSummary:U,setTopicSummary:le,getBookmarks:we,isBookmarked:W,toggleBookmark:ne}}var Hh=h("<a><!></a>"),qh=h("<button><!></button>");function Kh(t,e){Ir(e,!0);let r=Fe(e,"variant",3,"default"),a=Fe(e,"size",3,"default"),s=Bv(e,["$$slots","$$events","$$legacy","variant","size","class","children"]);const o={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},i={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=Se(),u=ae(l);{var f=g=>{var x=Hh();jo(x,k=>({class:k,...s}),[()=>wr("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",o[r()],i[a()],e.class)]);var b=d(x);Fi(b,()=>e.children),c(g,x)},p=g=>{var x=qh();jo(x,k=>({class:k,...s}),[()=>wr("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",o[r()],i[a()],e.class)]);var b=d(x);Fi(b,()=>e.children),c(g,x)};C(u,g=>{e.href?g(f):g(p,-1)})}c(t,l),Ar()}Of();/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Wh={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Gh=t=>{for(const e in t)if(e.startsWith("aria-")||e==="role"||e==="title")return!0;return!1};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const xd=(...t)=>t.filter((e,r,a)=>!!e&&e.trim()!==""&&a.indexOf(e)===r).join(" ").trim();var Yh=bo("<svg><!><!></svg>");function mt(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]),a=lt(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);Ir(e,!1);let s=Fe(e,"name",8,void 0),o=Fe(e,"color",8,"currentColor"),i=Fe(e,"size",8,24),l=Fe(e,"strokeWidth",8,2),u=Fe(e,"absoluteStrokeWidth",8,!1),f=Fe(e,"iconNode",24,()=>[]);Rv();var p=Yh();jo(p,(b,k,S)=>({...Wh,...b,...a,width:i(),height:i(),stroke:o(),"stroke-width":k,class:S}),[()=>Gh(a)?void 0:{"aria-hidden":"true"},()=>(Ya(u()),Ya(l()),Ya(i()),cs(()=>u()?Number(l())*24/Number(i()):l())),()=>(Ya(xd),Ya(s()),Ya(r),cs(()=>xd("lucide-icon","lucide",s()?`lucide-${s()}`:"",r.class)))]);var g=d(p);Ie(g,1,f,Le,(b,k)=>{var S=O(()=>sl(n(k),2));let _=()=>n(S)[0],w=()=>n(S)[1];var E=Se(),D=ae(E);Ev(D,_,!0,(M,Z)=>{jo(M,()=>({...w()}))}),c(b,E)});var x=m(g);pt(x,e,"default",{}),c(t,p),Ar()}function Jh(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];mt(t,ht({name:"activity"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function fu(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M8 3 4 7l4 4"}],["path",{d:"M4 7h16"}],["path",{d:"m16 21 4-4-4-4"}],["path",{d:"M20 17H4"}]];mt(t,ht({name:"arrow-left-right"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Xh(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"m12 5 7 7-7 7"}]];mt(t,ht({name:"arrow-right"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Qh(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];mt(t,ht({name:"arrow-up"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Wi(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 7v14"}],["path",{d:"M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"}]];mt(t,ht({name:"book-open"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function yi(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];mt(t,ht({name:"brain"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function gd(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 12h4"}],["path",{d:"M10 8h4"}],["path",{d:"M14 21v-3a2 2 0 0 0-4 0v3"}],["path",{d:"M6 10H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2"}],["path",{d:"M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"}]];mt(t,ht({name:"building-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Uo(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]];mt(t,ht({name:"chart-column"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Gi(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M20 6 9 17l-5-5"}]];mt(t,ht({name:"check"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function kl(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m6 9 6 6 6-6"}]];mt(t,ht({name:"chevron-down"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function vu(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m18 15-6-6-6 6"}]];mt(t,ht({name:"chevron-up"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function pu(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m9 18 6-6-6-6"}]];mt(t,ht({name:"chevron-right"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Ja(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];mt(t,ht({name:"circle-alert"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function io(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];mt(t,ht({name:"circle-check"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function fo(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];mt(t,ht({name:"clock"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Zh(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];mt(t,ht({name:"code"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function em(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];mt(t,ht({name:"coffee"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function _d(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]];mt(t,ht({name:"copy"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Xs(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];mt(t,ht({name:"database"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function lo(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];mt(t,ht({name:"download"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function tm(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["line",{x1:"5",x2:"19",y1:"9",y2:"9"}],["line",{x1:"5",x2:"19",y1:"15",y2:"15"}]];mt(t,ht({name:"equal"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function bd(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];mt(t,ht({name:"external-link"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function rm(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];mt(t,ht({name:"eye"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function En(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];mt(t,ht({name:"file-text"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function nm(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];mt(t,ht({name:"github"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function yd(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];mt(t,ht({name:"key"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function am(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 8h.01"}],["path",{d:"M12 12h.01"}],["path",{d:"M14 8h.01"}],["path",{d:"M16 12h.01"}],["path",{d:"M18 8h.01"}],["path",{d:"M6 8h.01"}],["path",{d:"M7 16h10"}],["path",{d:"M8 12h.01"}],["rect",{width:"20",height:"16",x:"2",y:"4",rx:"2"}]];mt(t,ht({name:"keyboard"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Kr(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];mt(t,ht({name:"loader-circle"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function sm(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];mt(t,ht({name:"log-out"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function hu(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"m21 3-7 7"}],["path",{d:"m3 21 7-7"}],["path",{d:"M9 21H3v-6"}]];mt(t,ht({name:"maximize-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function om(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];mt(t,ht({name:"menu"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Ho(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];mt(t,ht({name:"message-square"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function mu(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m14 10 7-7"}],["path",{d:"M20 10h-6V4"}],["path",{d:"m3 21 7-7"}],["path",{d:"M4 14h6v6"}]];mt(t,ht({name:"minimize-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function xu(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}]];mt(t,ht({name:"minus"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function gu(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];mt(t,ht({name:"panel-left-close"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function im(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m14 9 3 3-3 3"}]];mt(t,ht({name:"panel-left-open"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Yi(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];mt(t,ht({name:"plus"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function lm(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];mt(t,ht({name:"refresh-cw"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function ga(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];mt(t,ht({name:"search"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function dm(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];mt(t,ht({name:"settings"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function cm(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"}]];mt(t,ht({name:"shield"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function _u(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];mt(t,ht({name:"sparkles"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function um(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];mt(t,ht({name:"square"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Ji(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"}]];mt(t,ht({name:"star"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Xi(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];mt(t,ht({name:"table-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function fm(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];mt(t,ht({name:"terminal"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function vm(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];mt(t,ht({name:"trash-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function No(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M16 7h6v6"}],["path",{d:"m22 7-8.5 8.5-5-5L2 17"}]];mt(t,ht({name:"trending-up"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function co(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];mt(t,ht({name:"triangle-alert"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function bu(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["path",{d:"M16 3.128a4 4 0 0 1 0 7.744"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87"}],["circle",{cx:"9",cy:"7",r:"4"}]];mt(t,ht({name:"users"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function pm(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"}],["path",{d:"M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"}]];mt(t,ht({name:"wallet"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function wd(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];mt(t,ht({name:"wrench"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}function Ba(t,e){const r=lt(e,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];mt(t,ht({name:"x"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Se(),l=ae(i);pt(l,e,"default",{}),c(s,i)},$$slots:{default:!0}}))}var hm=h("<!> 새 대화",1),mm=h('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),xm=h('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),gm=h('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),_m=h('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40"><span class="text-[10px] text-dl-text-dim font-mono"> </span></div>'),bm=h('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),ym=h("<button><!></button>"),wm=h('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),km=h("<aside><!></aside>");function Sm(t,e){Ir(e,!0);let r=Fe(e,"conversations",19,()=>[]),a=Fe(e,"activeId",3,null),s=Fe(e,"open",3,!0),o=Fe(e,"version",3,""),i=Y("");function l(k){const S=new Date().setHours(0,0,0,0),_=S-864e5,w=S-7*864e5,E={오늘:[],어제:[],"이번 주":[],이전:[]};for(const M of k)M.updatedAt>=S?E.오늘.push(M):M.updatedAt>=_?E.어제.push(M):M.updatedAt>=w?E["이번 주"].push(M):E.이전.push(M);const D=[];for(const[M,Z]of Object.entries(E))Z.length>0&&D.push({label:M,items:Z});return D}let u=O(()=>n(i).trim()?r().filter(k=>k.title.toLowerCase().includes(n(i).toLowerCase())):r()),f=O(()=>l(n(u)));var p=km(),g=d(p);{var x=k=>{var S=bm(),_=m(d(S),2),w=d(_);Kh(w,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return e.onNewChat},children:(P,$)=>{var X=hm(),J=ae(X);Yi(J,{size:16}),c(P,X)},$$slots:{default:!0}});var E=m(_,2);{var D=P=>{var $=mm(),X=d($),J=d(X);ga(J,{size:12,class:"text-dl-text-dim flex-shrink-0"});var me=m(J,2);La(me,()=>n(i),B=>v(i,B)),c(P,$)};C(E,P=>{r().length>3&&P(D)})}var M=m(E,2);Ie(M,21,()=>n(f),Le,(P,$)=>{var X=gm(),J=d(X),me=d(J),B=m(J,2);Ie(B,17,()=>n($).items,Le,(Te,F)=>{var U=xm(),le=d(U),we=d(le);Ho(we,{size:14,class:"flex-shrink-0 opacity-50"});var W=m(we,2),ne=d(W),A=m(le,2),G=d(A);vm(G,{size:12}),T(q=>{qe(U,1,q),lr(le,"aria-current",n(F).id===a()?"true":void 0),z(ne,n(F).title),lr(A,"aria-label",`${n(F).title} 삭제`)},[()=>gr(wr("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",n(F).id===a()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),he("click",le,()=>{var q;return(q=e.onSelect)==null?void 0:q.call(e,n(F).id)}),he("click",A,q=>{var L;q.stopPropagation(),(L=e.onDelete)==null||L.call(e,n(F).id)}),c(Te,U)}),T(()=>z(me,n($).label)),c(P,X)});var Z=m(M,2);{var ce=P=>{var $=_m(),X=d($),J=d(X);T(()=>z(J,`v${o()??""}`)),c(P,$)};C(Z,P=>{o()&&P(ce)})}c(k,S)},b=k=>{var S=wm(),_=m(d(S),2),w=d(_);Yi(w,{size:18});var E=m(_,2);Ie(E,21,()=>r().slice(0,10),Le,(D,M)=>{var Z=ym(),ce=d(Z);Ho(ce,{size:16}),T(P=>{qe(Z,1,P),lr(Z,"title",n(M).title)},[()=>gr(wr("p-2 rounded-lg transition-colors w-full flex justify-center",n(M).id===a()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),he("click",Z,()=>{var P;return(P=e.onSelect)==null?void 0:P.call(e,n(M).id)}),c(D,Z)}),he("click",_,function(...D){var M;(M=e.onNewChat)==null||M.apply(this,D)}),c(k,S)};C(g,k=>{s()?k(x):k(b,-1)})}T(k=>qe(p,1,k),[()=>gr(wr("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",s()?"w-[260px]":"w-[52px]"))]),c(t,p),Ar()}Gr(["click"]);var Cm=h('<button class="send-btn active"><!></button>'),$m=h("<button><!></button>"),Mm=h('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),Tm=h('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),zm=h('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),Em=h('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function yu(t,e){Ir(e,!0);let r=Fe(e,"inputText",15,""),a=Fe(e,"isLoading",3,!1),s=Fe(e,"large",3,!1),o=Fe(e,"placeholder",3,"메시지를 입력하세요..."),i=Y(Ut([])),l=Y(!1),u=Y(-1),f=null,p=Y(void 0);function g($){var X;if(n(l)&&n(i).length>0){if($.key==="ArrowDown"){$.preventDefault(),v(u,(n(u)+1)%n(i).length);return}if($.key==="ArrowUp"){$.preventDefault(),v(u,n(u)<=0?n(i).length-1:n(u)-1,!0);return}if($.key==="Enter"&&n(u)>=0){$.preventDefault(),k(n(i)[n(u)]);return}if($.key==="Escape"){v(l,!1),v(u,-1);return}}$.key==="Enter"&&!$.shiftKey&&($.preventDefault(),v(l,!1),(X=e.onSend)==null||X.call(e))}function x($){$.target.style.height="auto",$.target.style.height=Math.min($.target.scrollHeight,200)+"px"}function b($){x($);const X=r();f&&clearTimeout(f),X.length>=2&&!/\s/.test(X.slice(-1))?f=setTimeout(async()=>{var J;try{const me=await gl(X.trim());((J=me.results)==null?void 0:J.length)>0?(v(i,me.results.slice(0,6),!0),v(l,!0),v(u,-1)):v(l,!1)}catch{v(l,!1)}},300):v(l,!1)}function k($){var X;r(`${$.corpName} `),v(l,!1),v(u,-1),(X=e.onCompanySelect)==null||X.call(e,$),n(p)&&n(p).focus()}function S(){setTimeout(()=>{v(l,!1)},200)}var _=Em(),w=d(_),E=d(w);Jn(E,$=>v(p,$),()=>n(p));var D=m(E,2);{var M=$=>{var X=Cm(),J=d(X);um(J,{size:14}),he("click",X,function(...me){var B;(B=e.onStop)==null||B.apply(this,me)}),c($,X)},Z=$=>{var X=$m(),J=d(X);{let me=O(()=>s()?18:16);Qh(J,{get size(){return n(me)},strokeWidth:2.5})}T((me,B)=>{qe(X,1,me),X.disabled=B},[()=>gr(wr("send-btn",r().trim()&&"active")),()=>!r().trim()]),he("click",X,()=>{var me;v(l,!1),(me=e.onSend)==null||me.call(e)}),c($,X)};C(D,$=>{a()&&e.onStop?$(M):$(Z,-1)})}var ce=m(w,2);{var P=$=>{var X=zm();Ie(X,21,()=>n(i),Le,(J,me,B)=>{var Te=Tm(),F=d(Te);ga(F,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var U=m(F,2),le=d(U),we=d(le),W=m(le,2),ne=d(W),A=m(U,2);{var G=q=>{var L=Mm(),H=d(L);T(()=>z(H,n(me).sector)),c(q,L)};C(A,q=>{n(me).sector&&q(G)})}T(q=>{qe(Te,1,q),z(we,n(me).corpName),z(ne,`${n(me).stockCode??""} · ${(n(me).market||"")??""}`)},[()=>gr(wr("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",B===n(u)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),he("mousedown",Te,()=>k(n(me))),gn("mouseenter",Te,()=>{v(u,B,!0)}),c(J,Te)}),c($,X)};C(ce,$=>{n(l)&&n(i).length>0&&$(P)})}T($=>{qe(w,1,$),lr(E,"placeholder",o())},[()=>gr(wr("input-box",s()&&"large"))]),he("keydown",E,g),he("input",E,b),gn("blur",E,S),La(E,r),c(t,_),Ar()}Gr(["keydown","input","click","mousedown"]);var Im=h('<button class="rounded-full border border-dl-border/60 bg-dl-bg-card/40 px-3 py-1.5 text-[12px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"> </button>'),Am=h(`<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[580px] flex flex-col items-center"><div class="relative mb-8"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p> <div class="mb-6 max-w-[520px] rounded-2xl border border-dl-border/50 bg-dl-bg-card/50 px-4 py-3 text-left"><div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">Evidence First</div> <div class="mt-2 text-[13px] leading-relaxed text-dl-text-muted">DartLab은 재무 수치와 서술 텍스트를 함께 읽고, 표준화된 계정과 원문 근거를 같은 흐름에서 확인하도록 설계되어 있습니다.
				DART와 EDGAR를 포함한 40개 모듈 이상의 기능 범위를 먼저 물어본 뒤 바로 탐색을 시작할 수 있습니다.</div></div> <div class="w-full"><!></div> <div class="mt-5 flex w-full flex-wrap justify-center gap-2"></div></div></div>`);function Lm(t,e){Ir(e,!0);let r=Fe(e,"inputText",15,"");const a=["지금 dartlab에서 할 수 있는 기능을 먼저 정리해줘","EDGAR에서 추가로 받을 수 있는 데이터와 방법을 알려줘","OpenDart와 OpenEdgar로 가능한 일을 비교해줘","GPT 연결 시 현재 UI에서 가능한 코딩 작업 범위를 알려줘"];var s=Am(),o=d(s),i=m(d(o),8),l=d(i);yu(l,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return e.onSend},get onCompanySelect(){return e.onCompanySelect},get inputText(){return r()},set inputText(f){r(f)}});var u=m(i,2);Ie(u,21,()=>a,Le,(f,p)=>{var g=Im(),x=d(g);T(()=>z(x,n(p))),he("click",g,()=>{var b;return(b=e.onSend)==null?void 0:b.call(e,n(p))}),c(f,g)}),c(t,s),Ar()}Gr(["click"]);var Nm=h("<span><!></span>");function Qs(t,e){Ir(e,!0);let r=Fe(e,"variant",3,"default");const a={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var s=Nm(),o=d(s);Fi(o,()=>e.children),T(i=>qe(s,1,i),[()=>gr(wr("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",a[r()],e.class))]),c(t,s),Ar()}function Pm(t){const e=t.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(e)||e==="-"||e==="0"}function Va(t){if(!t)return"";let e=[],r=[],a=t.replace(/```(\w*)\n([\s\S]*?)```/g,(o,i,l)=>{const u=e.length;return e.push(l.trimEnd()),`
%%CODE_${u}%%
`});a=a.replace(/((?:^\|.+\|$\n?)+)/gm,o=>{const i=o.trim().split(`
`).filter(x=>x.trim());let l=null,u=-1,f=[];for(let x=0;x<i.length;x++)if(i[x].slice(1,-1).split("|").map(k=>k.trim()).every(k=>/^[\-:]+$/.test(k))){u=x;break}u>0?(l=i[u-1],f=i.slice(u+1)):(u===0||(l=i[0]),f=i.slice(1));let p="<table>";if(l){const x=l.slice(1,-1).split("|").map(b=>b.trim());p+="<thead><tr>"+x.map(b=>`<th>${b.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(f.length>0){p+="<tbody>";for(const x of f){const b=x.slice(1,-1).split("|").map(k=>k.trim());p+="<tr>"+b.map(k=>{let S=k.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${Pm(k)?' class="num"':""}>${S}</td>`}).join("")+"</tr>"}p+="</tbody>"}p+="</table>";let g=r.length;return r.push(p),`
%%TABLE_${g}%%
`});let s=a.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");s=s.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,o=>"<ul>"+o.replace(/<br>/g,"")+"</ul>");for(let o=0;o<r.length;o++)s=s.replace(`%%TABLE_${o}%%`,r[o]);for(let o=0;o<e.length;o++){const i=e[o].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");s=s.replace(`%%CODE_${o}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${o}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${i}</code></pre></div>`)}return s=s.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(o,i)=>i.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+s+"</p>"}var Dm=h('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),Om=h('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),Rm=h('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),Fm=h('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),jm=h('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!> <!> <!> <!></div></div>'),Bm=h('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),Vm=h('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),Um=h('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),Hm=h("<span> </span>"),qm=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-bold border bg-red-500/10 text-red-400 border-red-500/20"> </span>'),Km=h('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-1.5"><!> <!></div>'),Wm=h('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!> <!></button>'),Gm=h("<button><!> </button>"),Ym=h('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),Jm=h('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),Xm=h('<!> <span class="text-dl-text-dim"> </span>',1),Qm=h('<div class="flex items-center gap-2 text-[11px]"><!></div>'),Zm=h('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),ex=h('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),tx=h('<div class="message-committed"><!></div>'),rx=h('<div><div class="message-live-label"> </div> <pre> </pre></div>'),nx=h('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),ax=h('<span class="text-dl-accent/60"> </span>'),sx=h('<span class="text-dl-success/60"> </span>'),ox=h('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),ix=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),lx=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),dx=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),cx=h('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),ux=h("<!>  <div><!> <!></div> <!>",1),fx=h('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),vx=h('<span class="text-[10px] text-dl-text-dim"> </span>'),px=h('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),hx=h("<button> </button>"),mx=h('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),xx=h("<button>시스템 프롬프트</button>"),gx=h("<button>LLM 입력</button>"),_x=h('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),bx=h('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),yx=h('<span class="text-dl-text"> </span>'),wx=h('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),kx=h('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),Sx=h('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Cx=h("<!> <!>",1);function $x(t,e){Ir(e,!0);let r=Y(null),a=Y("context"),s=Y("raw"),o=O(()=>{var L,H,j,K,_e,$e;if(!e.message.loading)return"";if(e.message.text)return"응답 작성 중";if(((L=e.message.toolEvents)==null?void 0:L.length)>0){const te=[...e.message.toolEvents].reverse().find(tt=>tt.type==="call"),De=((H=te==null?void 0:te.arguments)==null?void 0:H.module)||((j=te==null?void 0:te.arguments)==null?void 0:j.keyword)||"";return`도구 실행 중 — ${(te==null?void 0:te.name)||""}${De?` (${De})`:""}`}if(((K=e.message.contexts)==null?void 0:K.length)>0){const te=e.message.contexts[e.message.contexts.length-1];return`데이터 분석 중 — ${(te==null?void 0:te.label)||(te==null?void 0:te.module)||""}`}return e.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(_e=e.message.meta)!=null&&_e.company?`${e.message.meta.company} 데이터 검색 중`:($e=e.message.meta)!=null&&$e.includedModules?"분석 모듈 선택 완료":"생각 중"}),i=O(()=>{var L;return e.message.company||((L=e.message.meta)==null?void 0:L.company)||null});const l={capability:"기능 탐색",coding:"코딩 작업",company_explore:"회사 탐색",company_analysis:"회사 분석",follow_up:"후속 질문",general_chat:"일반 대화"};let u=O(()=>{var L;return(L=e.message.meta)!=null&&L.dialogueMode?l[e.message.meta.dialogueMode]||e.message.meta.dialogueMode:null}),f=O(()=>{var L,H,j;return e.message.systemPrompt||e.message.userContent||((L=e.message.contexts)==null?void 0:L.length)>0||((H=e.message.meta)==null?void 0:H.includedModules)||((j=e.message.toolEvents)==null?void 0:j.length)>0}),p=O(()=>{var H;const L=(H=e.message.meta)==null?void 0:H.dataYearRange;return L?typeof L=="string"?L:L.min_year&&L.max_year?`${L.min_year}~${L.max_year}년`:null:null});function g(L){if(!L)return 0;const H=(L.match(/[\uac00-\ud7af]/g)||[]).length,j=L.length-H;return Math.round(H*1.5+j/3.5)}function x(L){return L>=1e3?(L/1e3).toFixed(1)+"k":String(L)}let b=O(()=>{var H;let L=0;if(e.message.systemPrompt&&(L+=g(e.message.systemPrompt)),e.message.userContent)L+=g(e.message.userContent);else if(((H=e.message.contexts)==null?void 0:H.length)>0)for(const j of e.message.contexts)L+=g(j.text);return L}),k=O(()=>g(e.message.text)),S=Y(void 0);const _=/^\s*\|.+\|\s*$/;function w(L,H){if(!L)return{committed:"",draft:"",draftType:"none"};if(!H)return{committed:L,draft:"",draftType:"none"};const j=L.split(`
`);let K=j.length;L.endsWith(`
`)||(K=Math.min(K,j.length-1));let _e=0,$e=-1;for(let Ge=0;Ge<j.length;Ge++)j[Ge].trim().startsWith("```")&&(_e+=1,$e=Ge);_e%2===1&&$e>=0&&(K=Math.min(K,$e));let te=-1;for(let Ge=j.length-1;Ge>=0;Ge--){const rt=j[Ge];if(!rt.trim())break;if(_.test(rt))te=Ge;else{te=-1;break}}if(te>=0&&(K=Math.min(K,te)),K<=0)return{committed:"",draft:L,draftType:te===0?"table":_e%2===1?"code":"text"};const De=j.slice(0,K).join(`
`),tt=j.slice(K).join(`
`);let st="text";return tt&&te>=K?st="table":tt&&_e%2===1&&(st="code"),{committed:De,draft:tt,draftType:st}}const E='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',D='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function M(L){var _e;const H=L.target.closest(".code-copy-btn");if(!H)return;const j=H.closest(".code-block-wrap"),K=((_e=j==null?void 0:j.querySelector("code"))==null?void 0:_e.textContent)||"";navigator.clipboard.writeText(K).then(()=>{H.innerHTML=D,setTimeout(()=>{H.innerHTML=E},2e3)})}function Z(L){if(e.onOpenEvidence){e.onOpenEvidence("contexts",L);return}v(r,L,!0),v(a,"context"),v(s,"rendered")}function ce(){if(e.onOpenEvidence){e.onOpenEvidence("system");return}v(r,0),v(a,"system"),v(s,"raw")}function P(){if(e.onOpenEvidence){e.onOpenEvidence("snapshot");return}v(r,0),v(a,"snapshot")}function $(L){var H;if(e.onOpenEvidence){const j=(H=e.message.toolEvents)==null?void 0:H[L];e.onOpenEvidence((j==null?void 0:j.type)==="result"?"tool-results":"tool-calls",L);return}v(r,L,!0),v(a,"tool"),v(s,"raw")}function X(){if(e.onOpenEvidence){e.onOpenEvidence("input");return}v(r,0),v(a,"userContent"),v(s,"raw")}function J(){v(r,null)}function me(L){var H,j,K,_e;return L?L.type==="call"?((H=L.arguments)==null?void 0:H.module)||((j=L.arguments)==null?void 0:j.keyword)||((K=L.arguments)==null?void 0:K.engine)||((_e=L.arguments)==null?void 0:_e.name)||"":typeof L.result=="string"?L.result.slice(0,120):L.result&&typeof L.result=="object"&&(L.result.module||L.result.status||L.result.name)||"":""}let B=O(()=>(e.message.toolEvents||[]).filter(L=>L.type==="call")),Te=O(()=>(e.message.toolEvents||[]).filter(L=>L.type==="result")),F=O(()=>w(e.message.text||"",e.message.loading)),U=O(()=>{var H,j,K;const L=[];return((j=(H=e.message.meta)==null?void 0:H.includedModules)==null?void 0:j.length)>0&&L.push({label:`모듈 ${e.message.meta.includedModules.length}개`,icon:Xs}),((K=e.message.contexts)==null?void 0:K.length)>0&&L.push({label:`컨텍스트 ${e.message.contexts.length}건`,icon:rm}),n(B).length>0&&L.push({label:`툴 호출 ${n(B).length}건`,icon:wd}),n(Te).length>0&&L.push({label:`툴 결과 ${n(Te).length}건`,icon:io}),e.message.systemPrompt&&L.push({label:"시스템 프롬프트",icon:yi}),e.message.userContent&&L.push({label:"LLM 입력",icon:En}),L}),le=O(()=>{var H,j,K;if(!e.message.loading)return[];const L=[];return(H=e.message.meta)!=null&&H.company&&L.push({label:`${e.message.meta.company} 인식`,done:!0}),e.message.snapshot&&L.push({label:"핵심 수치 확인",done:!0}),(j=e.message.meta)!=null&&j.includedModules&&L.push({label:`모듈 ${e.message.meta.includedModules.length}개 선택`,done:!0}),((K=e.message.contexts)==null?void 0:K.length)>0&&L.push({label:`데이터 ${e.message.contexts.length}건 로드`,done:!0}),e.message.systemPrompt&&L.push({label:"프롬프트 조립",done:!0}),e.message.text?L.push({label:"응답 작성 중",done:!1}):L.push({label:n(o)||"준비 중",done:!1}),L});var we=Cx(),W=ae(we);{var ne=L=>{var H=Dm(),j=m(d(H),2),K=d(j),_e=d(K);T(()=>z(_e,e.message.text)),c(L,H)},A=L=>{var H=fx(),j=m(d(H),2),K=d(j);{var _e=dt=>{var nt=jm(),ot=d(nt),xt=d(ot);Jh(xt,{size:11});var $t=m(ot,4),Nt=d($t);{var dr=ve=>{Qs(ve,{variant:"muted",children:(ke,Ne)=>{var de=oa();T(()=>z(de,n(i))),c(ke,de)},$$slots:{default:!0}})};C(Nt,ve=>{n(i)&&ve(dr)})}var R=m(Nt,2);{var pe=ve=>{Qs(ve,{variant:"muted",children:(ke,Ne)=>{var de=oa();T(ze=>z(de,ze),[()=>e.message.meta.market.toUpperCase()]),c(ke,de)},$$slots:{default:!0}})};C(R,ve=>{var ke;(ke=e.message.meta)!=null&&ke.market&&ve(pe)})}var se=m(R,2);{var ue=ve=>{Qs(ve,{variant:"accent",children:(ke,Ne)=>{var de=oa();T(()=>z(de,n(u))),c(ke,de)},$$slots:{default:!0}})};C(se,ve=>{n(u)&&ve(ue)})}var y=m(se,2);{var V=ve=>{Qs(ve,{variant:"muted",children:(ke,Ne)=>{var de=oa();T(()=>z(de,e.message.meta.topicLabel)),c(ke,de)},$$slots:{default:!0}})};C(y,ve=>{var ke;(ke=e.message.meta)!=null&&ke.topicLabel&&ve(V)})}var re=m(y,2);{var ie=ve=>{Qs(ve,{variant:"accent",children:(ke,Ne)=>{var de=oa();T(()=>z(de,n(p))),c(ke,de)},$$slots:{default:!0}})};C(re,ve=>{n(p)&&ve(ie)})}var fe=m(re,2);{var N=ve=>{var ke=Se(),Ne=ae(ke);Ie(Ne,17,()=>e.message.contexts,Le,(de,ze,Re)=>{var He=Om(),be=d(He);Xs(be,{size:10,class:"flex-shrink-0"});var et=m(be);T(()=>z(et,` ${(n(ze).label||n(ze).module)??""}`)),he("click",He,()=>Z(Re)),c(de,He)}),c(ve,ke)},ee=ve=>{var ke=Rm(),Ne=d(ke);Xs(Ne,{size:10,class:"flex-shrink-0"});var de=m(Ne);T(()=>z(de,` 모듈 ${e.message.meta.includedModules.length??""}개`)),c(ve,ke)};C(fe,ve=>{var ke,Ne,de;((ke=e.message.contexts)==null?void 0:ke.length)>0?ve(N):((de=(Ne=e.message.meta)==null?void 0:Ne.includedModules)==null?void 0:de.length)>0&&ve(ee,1)})}var Ce=m(fe,2);Ie(Ce,17,()=>n(U),Le,(ve,ke)=>{var Ne=Fm(),de=d(Ne);Is(de,()=>n(ke).icon,(Re,He)=>{He(Re,{size:10,class:"flex-shrink-0"})});var ze=m(de);T(()=>z(ze,` ${n(ke).label??""}`)),he("click",Ne,()=>{n(ke).label.startsWith("컨텍스트")?Z(0):n(ke).label.startsWith("툴 호출")?e.onOpenEvidence?e.onOpenEvidence("tool-calls",0):$(0):n(ke).label.startsWith("툴 결과")?e.onOpenEvidence?e.onOpenEvidence("tool-results",0):$((e.message.toolEvents||[]).findIndex(Re=>Re.type==="result")):n(ke).label==="시스템 프롬프트"?ce():n(ke).label==="LLM 입력"&&X()}),c(ve,Ne)}),c(dt,nt)};C(K,dt=>{var nt,ot;(n(i)||n(p)||((nt=e.message.contexts)==null?void 0:nt.length)>0||(ot=e.message.meta)!=null&&ot.includedModules||n(U).length>0)&&dt(_e)})}var $e=m(K,2);{var te=dt=>{var nt=Wm(),ot=d(nt);Ie(ot,21,()=>e.message.snapshot.items,Le,(R,pe)=>{const se=O(()=>n(pe).status==="good"?"text-dl-success":n(pe).status==="danger"?"text-dl-primary-light":n(pe).status==="caution"?"text-amber-400":"text-dl-text");var ue=Bm(),y=d(ue),V=d(y),re=m(y,2),ie=d(re);T(fe=>{z(V,n(pe).label),qe(re,1,fe),z(ie,n(pe).value)},[()=>gr(wr("text-[14px] font-semibold leading-snug mt-0.5",n(se)))]),c(R,ue)});var xt=m(ot,2);{var $t=R=>{var pe=Um();Ie(pe,21,()=>e.message.snapshot.warnings,Le,(se,ue)=>{var y=Vm(),V=d(y);co(V,{size:10});var re=m(V);T(()=>z(re,` ${n(ue)??""}`)),c(se,y)}),c(R,pe)};C(xt,R=>{var pe;((pe=e.message.snapshot.warnings)==null?void 0:pe.length)>0&&R($t)})}var Nt=m(xt,2);{var dr=R=>{const pe=O(()=>({performance:"실적",profitability:"수익성",health:"건전성",cashflow:"현금흐름",governance:"지배구조",risk:"리스크",opportunity:"기회"}));var se=Km(),ue=d(se);Ie(ue,17,()=>Object.entries(e.message.snapshot.grades),Le,(re,ie)=>{var fe=O(()=>sl(n(ie),2));let N=()=>n(fe)[0],ee=()=>n(fe)[1];const Ce=O(()=>ee()==="A"?"bg-emerald-500/15 text-emerald-400 border-emerald-500/30":ee()==="B"?"bg-blue-500/15 text-blue-400 border-blue-500/30":ee()==="C"?"bg-amber-500/15 text-amber-400 border-amber-500/30":ee()==="D"?"bg-orange-500/15 text-orange-400 border-orange-500/30":ee()==="F"?"bg-red-500/15 text-red-400 border-red-500/30":"bg-dl-border/10 text-dl-text-dim border-dl-border/20");var ve=Hm(),ke=d(ve);T(()=>{qe(ve,1,`px-1.5 py-0.5 rounded text-[9px] font-bold border ${n(Ce)??""}`),z(ke,`${(n(pe)[N()]||N())??""} ${ee()??""}`)}),c(re,ve)});var y=m(ue,2);{var V=re=>{var ie=qm(),fe=d(ie);T(()=>z(fe,`이상치 ${e.message.snapshot.anomalyCount??""}건`)),c(re,ie)};C(y,re=>{e.message.snapshot.anomalyCount>0&&re(V)})}c(R,se)};C(Nt,R=>{e.message.snapshot.grades&&R(dr)})}he("click",nt,P),c(dt,nt)};C($e,dt=>{var nt,ot;((ot=(nt=e.message.snapshot)==null?void 0:nt.items)==null?void 0:ot.length)>0&&dt(te)})}var De=m($e,2);{var tt=dt=>{var nt=Ym(),ot=d(nt),xt=m(d(ot),4);Ie(xt,21,()=>e.message.toolEvents,Le,($t,Nt,dr)=>{const R=O(()=>me(n(Nt)));var pe=Gm(),se=d(pe);{var ue=re=>{wd(re,{size:11})},y=re=>{io(re,{size:11})};C(se,re=>{n(Nt).type==="call"?re(ue):re(y,-1)})}var V=m(se);T(re=>{qe(pe,1,re),z(V,` ${(n(Nt).type==="call"?n(Nt).name:`${n(Nt).name} 결과`)??""}${n(R)?`: ${n(R)}`:""}`)},[()=>gr(wr("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",n(Nt).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),he("click",pe,()=>$(dr)),c($t,pe)}),c(dt,nt)};C(De,dt=>{var nt;((nt=e.message.toolEvents)==null?void 0:nt.length)>0&&dt(tt)})}var st=m(De,2);{var Ge=dt=>{var nt=Zm(),ot=d(nt);Ie(ot,21,()=>n(le),Le,(xt,$t)=>{var Nt=Qm(),dr=d(Nt);{var R=se=>{var ue=Jm(),y=m(ae(ue),2),V=d(y);T(()=>z(V,n($t).label)),c(se,ue)},pe=se=>{var ue=Xm(),y=ae(ue);Kr(y,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var V=m(y,2),re=d(V);T(()=>z(re,n($t).label)),c(se,ue)};C(dr,se=>{n($t).done?se(R):se(pe,-1)})}c(xt,Nt)}),c(dt,nt)},rt=dt=>{var nt=ux(),ot=ae(nt);{var xt=y=>{var V=ex(),re=d(V);Kr(re,{size:12,class:"animate-spin flex-shrink-0"});var ie=m(re,2),fe=d(ie);T(()=>z(fe,n(o))),c(y,V)};C(ot,y=>{e.message.loading&&y(xt)})}var $t=m(ot,2),Nt=d($t);{var dr=y=>{var V=tx(),re=d(V);Gn(re,()=>Va(n(F).committed)),c(y,V)};C(Nt,y=>{n(F).committed&&y(dr)})}var R=m(Nt,2);{var pe=y=>{var V=rx(),re=d(V),ie=d(re),fe=m(re,2),N=d(fe);T(ee=>{qe(V,1,ee),z(ie,n(F).draftType==="table"?"표 구성 중":n(F).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),z(N,n(F).draft)},[()=>gr(wr("message-live-tail",n(F).draftType==="table"&&"message-draft-table",n(F).draftType==="code"&&"message-draft-code"))]),c(y,V)};C(R,y=>{n(F).draft&&y(pe)})}Jn($t,y=>v(S,y),()=>n(S));var se=m($t,2);{var ue=y=>{var V=cx(),re=d(V);{var ie=ze=>{var Re=nx(),He=d(Re);fo(He,{size:10});var be=m(He);T(()=>z(be,` ${e.message.duration??""}초`)),c(ze,Re)};C(re,ze=>{e.message.duration&&ze(ie)})}var fe=m(re,2);{var N=ze=>{var Re=ox(),He=d(Re);{var be=at=>{var Rt=ax(),Be=d(Rt);T(Ae=>z(Be,`↑${Ae??""}`),[()=>x(n(b))]),c(at,Rt)};C(He,at=>{n(b)>0&&at(be)})}var et=m(He,2);{var St=at=>{var Rt=sx(),Be=d(Rt);T(Ae=>z(Be,`↓${Ae??""}`),[()=>x(n(k))]),c(at,Rt)};C(et,at=>{n(k)>0&&at(St)})}c(ze,Re)};C(fe,ze=>{(n(b)>0||n(k)>0)&&ze(N)})}var ee=m(fe,2);{var Ce=ze=>{var Re=ix(),He=d(Re);lm(He,{size:10}),he("click",Re,()=>{var be;return(be=e.onRegenerate)==null?void 0:be.call(e)}),c(ze,Re)};C(ee,ze=>{e.onRegenerate&&ze(Ce)})}var ve=m(ee,2);{var ke=ze=>{var Re=lx(),He=d(Re);yi(He,{size:10}),he("click",Re,ce),c(ze,Re)};C(ve,ze=>{e.message.systemPrompt&&ze(ke)})}var Ne=m(ve,2);{var de=ze=>{var Re=dx(),He=d(Re);En(He,{size:10});var be=m(He);T((et,St)=>z(be,` LLM 입력 (${et??""}자 · ~${St??""}tok)`),[()=>e.message.userContent.length.toLocaleString(),()=>x(g(e.message.userContent))]),he("click",Re,X),c(ze,Re)};C(Ne,ze=>{e.message.userContent&&ze(de)})}c(y,V)};C(se,y=>{!e.message.loading&&(e.message.duration||n(f)||e.onRegenerate)&&y(ue)})}T(y=>qe($t,1,y),[()=>gr(wr("prose-dartlab message-body text-[15px] leading-[1.75]",e.message.error&&"text-dl-primary"))]),he("click",$t,M),c(dt,nt)};C(st,dt=>{e.message.loading&&!e.message.text?dt(Ge):dt(rt,-1)})}c(L,H)};C(W,L=>{e.message.role==="user"?L(ne):L(A,-1)})}var G=m(W,2);{var q=L=>{const H=O(()=>n(a)==="system"),j=O(()=>n(a)==="userContent"),K=O(()=>n(a)==="context"),_e=O(()=>n(a)==="snapshot"),$e=O(()=>n(a)==="tool"),te=O(()=>{var be;return n(K)?(be=e.message.contexts)==null?void 0:be[n(r)]:null}),De=O(()=>{var be;return n($e)?(be=e.message.toolEvents)==null?void 0:be[n(r)]:null}),tt=O(()=>{var be,et,St,at,Rt;return n(_e)?"핵심 수치 (원본 데이터)":n(H)?"시스템 프롬프트":n(j)?"LLM에 전달된 입력":n($e)?((be=n(De))==null?void 0:be.type)==="call"?`${(et=n(De))==null?void 0:et.name} 호출`:`${(St=n(De))==null?void 0:St.name} 결과`:((at=n(te))==null?void 0:at.label)||((Rt=n(te))==null?void 0:Rt.module)||""}),st=O(()=>{var be;return n(_e)?JSON.stringify(e.message.snapshot,null,2):n(H)?e.message.systemPrompt:n(j)?e.message.userContent:n($e)?JSON.stringify(n(De),null,2):(be=n(te))==null?void 0:be.text});var Ge=Sx(),rt=d(Ge),dt=d(rt),nt=d(dt),ot=d(nt),xt=d(ot);{var $t=be=>{Xs(be,{size:15,class:"text-dl-success flex-shrink-0"})},Nt=be=>{yi(be,{size:15,class:"text-dl-primary-light flex-shrink-0"})},dr=be=>{En(be,{size:15,class:"text-dl-accent flex-shrink-0"})},R=be=>{Xs(be,{size:15,class:"flex-shrink-0"})};C(xt,be=>{n(_e)?be($t):n(H)?be(Nt,1):n(j)?be(dr,2):be(R,-1)})}var pe=m(xt,2),se=d(pe),ue=m(pe,2);{var y=be=>{var et=vx(),St=d(et);T(at=>z(St,`(${at??""}자)`),[()=>{var at,Rt;return(Rt=(at=n(st))==null?void 0:at.length)==null?void 0:Rt.toLocaleString()}]),c(be,et)};C(ue,be=>{n(H)&&be(y)})}var V=m(ot,2),re=d(V);{var ie=be=>{var et=px(),St=d(et),at=d(St);En(at,{size:11});var Rt=m(St,2),Be=d(Rt);Zh(Be,{size:11}),T((Ae,Ee)=>{qe(St,1,Ae),qe(Rt,1,Ee)},[()=>gr(wr("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(s)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>gr(wr("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(s)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),he("click",St,()=>v(s,"rendered")),he("click",Rt,()=>v(s,"raw")),c(be,et)};C(re,be=>{n(K)&&be(ie)})}var fe=m(re,2),N=d(fe);Ba(N,{size:18});var ee=m(nt,2);{var Ce=be=>{var et=mx(),St=d(et);Ie(St,21,()=>e.message.contexts,Le,(at,Rt,Be)=>{var Ae=hx(),Ee=d(Ae);T(wt=>{qe(Ae,1,wt),z(Ee,e.message.contexts[Be].label||e.message.contexts[Be].module)},[()=>gr(wr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",Be===n(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),he("click",Ae,()=>{v(r,Be,!0)}),c(at,Ae)}),c(be,et)};C(ee,be=>{var et;n(K)&&((et=e.message.contexts)==null?void 0:et.length)>1&&be(Ce)})}var ve=m(ee,2);{var ke=be=>{var et=_x(),St=d(et),at=d(St);{var Rt=Ee=>{var wt=xx();T(Pt=>qe(wt,1,Pt),[()=>gr(wr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(H)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),he("click",wt,()=>{v(a,"system")}),c(Ee,wt)};C(at,Ee=>{e.message.systemPrompt&&Ee(Rt)})}var Be=m(at,2);{var Ae=Ee=>{var wt=gx();T(Pt=>qe(wt,1,Pt),[()=>gr(wr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(j)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),he("click",wt,()=>{v(a,"userContent")}),c(Ee,wt)};C(Be,Ee=>{e.message.userContent&&Ee(Ae)})}c(be,et)};C(ve,be=>{!n(K)&&!n(_e)&&!n($e)&&be(ke)})}var Ne=m(dt,2),de=d(Ne);{var ze=be=>{var et=bx(),St=d(et);Gn(St,()=>{var at;return Va((at=n(te))==null?void 0:at.text)}),c(be,et)},Re=be=>{var et=wx(),St=d(et),at=m(d(St),2),Rt=d(at),Be=m(Rt);{var Ae=Ye=>{var At=yx(),Ht=d(At);T(Ct=>z(Ht,Ct),[()=>me(n(De))]),c(Ye,At)},Ee=O(()=>me(n(De)));C(Be,Ye=>{n(Ee)&&Ye(Ae)})}var wt=m(St,2),Pt=d(wt);T(()=>{var Ye;z(Rt,`${((Ye=n(De))==null?void 0:Ye.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),z(Pt,n(st))}),c(be,et)},He=be=>{var et=kx(),St=d(et);T(()=>z(St,n(st))),c(be,et)};C(de,be=>{n(K)&&n(s)==="rendered"?be(ze):n($e)?be(Re,1):be(He,-1)})}T(()=>z(se,n(tt))),he("click",Ge,be=>{be.target===be.currentTarget&&J()}),he("keydown",Ge,be=>{be.key==="Escape"&&J()}),he("click",fe,J),c(L,Ge)};C(G,L=>{n(r)!==null&&L(q)})}c(t,we),Ar()}Gr(["click","keydown"]);var Mx=h('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),Tx=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),zx=h('<div class="flex justify-end gap-2 mb-1.5"><!></div>'),Ex=h('<div class="flex items-center gap-1.5 px-3 py-1 text-[10px] text-dl-text-dim"><span class="px-1.5 py-0.5 rounded bg-dl-accent/10 text-dl-accent-light border border-dl-accent/20 font-mono"> <!></span> <span>보는 중 — AI가 이 섹션을 참조합니다</span></div>'),Ix=h('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8"><!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!> <!></div></div></div>');function Ax(t,e){Ir(e,!0);function r(F){if(s())return!1;for(let U=a().length-1;U>=0;U--)if(a()[U].role==="assistant"&&!a()[U].error&&a()[U].text)return U===F;return!1}let a=Fe(e,"messages",19,()=>[]),s=Fe(e,"isLoading",3,!1),o=Fe(e,"inputText",15,""),i=Fe(e,"scrollTrigger",3,0);Fe(e,"selectedCompany",3,null);let l=Fe(e,"viewerContext",3,null);function u(F){return(U,le)=>{var W,ne,A,G;(W=e.onOpenEvidence)==null||W.call(e,U,le);let we;if(U==="contexts")we=(ne=F.contexts)==null?void 0:ne[le];else if(U==="snapshot")we={label:"핵심 수치",module:"snapshot",text:JSON.stringify(F.snapshot,null,2)};else if(U==="system")we={label:"시스템 프롬프트",module:"system",text:F.systemPrompt};else if(U==="input")we={label:"LLM 입력",module:"input",text:F.userContent};else if(U==="tool-calls"||U==="tool-results"){const q=(A=F.toolEvents)==null?void 0:A[le];we={label:`${(q==null?void 0:q.name)||"도구"} ${(q==null?void 0:q.type)==="call"?"호출":"결과"}`,module:"tool",text:JSON.stringify(q,null,2)}}we&&((G=e.onOpenData)==null||G.call(e,we))}}let f,p,g=Y(!0),x=Y(!1),b=Y(!0);function k(){if(!f)return;const{scrollTop:F,scrollHeight:U,clientHeight:le}=f;v(b,U-F-le<96),n(b)?(v(g,!0),v(x,!1)):(v(g,!1),v(x,!0))}function S(F="smooth"){p&&(p.scrollIntoView({block:"end",behavior:F}),v(g,!0),v(x,!1))}_r(()=>{i(),!(!f||!p)&&requestAnimationFrame(()=>{!f||!p||(n(g)||n(b)?(p.scrollIntoView({block:"end",behavior:s()?"auto":"smooth"}),v(x,!1)):v(x,!0))})});var _=Ix(),w=d(_),E=d(w),D=d(E);Ie(D,17,a,Le,(F,U,le)=>{{let we=O(()=>r(le)?e.onRegenerate:void 0),W=O(()=>e.onOpenData?u(n(U)):void 0);$x(F,{get message(){return n(U)},get onRegenerate(){return n(we)},get onOpenEvidence(){return n(W)}})}});var M=m(D,2);Jn(M,F=>p=F,()=>p),Jn(w,F=>f=F,()=>f);var Z=m(w,2);{var ce=F=>{var U=Mx(),le=d(U);he("click",le,()=>S("smooth")),c(F,U)};C(Z,F=>{n(x)&&F(ce)})}var P=m(Z,2),$=d(P),X=d($);{var J=F=>{var U=zx(),le=d(U);{var we=W=>{var ne=Tx(),A=d(ne);lo(A,{size:10}),he("click",ne,function(...G){var q;(q=e.onExport)==null||q.apply(this,G)}),c(W,ne)};C(le,W=>{a().length>1&&e.onExport&&W(we)})}c(F,U)};C(X,F=>{s()||F(J)})}var me=m(X,2);{var B=F=>{var U=Ex(),le=d(U),we=d(le),W=m(we);{var ne=A=>{var G=oa();T(()=>z(G,` (${l().period??""})`)),c(A,G)};C(W,A=>{l().period&&A(ne)})}T(()=>z(we,l().topicLabel||l().topic)),c(F,U)};C(me,F=>{var U;(U=l())!=null&&U.topic&&F(B)})}var Te=m(me,2);yu(Te,{get isLoading(){return s()},placeholder:"메시지를 입력하세요...",get onSend(){return e.onSend},get onStop(){return e.onStop},get onCompanySelect(){return e.onCompanySelect},get inputText(){return o()},set inputText(F){o(F)}}),gn("scroll",w,k),c(t,_),Ar()}Gr(["click"]);var Lx=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!> <span class="text-[13px]">공시 데이터 로딩 중...</span></div>'),Nx=h('<div class="text-[11px] text-dl-text-dim"> </div>'),Px=h('<button><!> <span class="truncate flex-1"> </span></button>'),Dx=h('<div class="py-0.5"></div>'),Ox=h('<div><button class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] opacity-30 font-normal"> </span></button> <!></div>'),Rx=h('<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50"><div class="px-3 py-2.5 border-b border-dl-border/20"><!></div> <!></nav>'),Fx=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim"><!> <p class="text-[13px]">좌측에서 섹션을 선택하세요</p></div>'),jx=h('<div class="text-[10px] text-dl-text-dim/50 mb-0.5"> </div>'),Bx=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!></div>'),Vx=h('<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>'),Ux=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Hx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),qx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Kx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Wx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Gx=h('<div class="vw-heading-node svelte-1l2nqwu"><!></div>'),Yx=h('<div class="vw-heading-block svelte-1l2nqwu"></div>'),Jx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Xx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Qx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Zx=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),eg=h('<button><span class="vw-timeline-label svelte-1l2nqwu"> </span></button>'),tg=h('<div class="vw-section-timeline svelte-1l2nqwu"></div>'),rg=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),ng=h('<span class="vw-meta-pill svelte-1l2nqwu">비교 없음</span>'),ag=h('<div class="vw-section-actions svelte-1l2nqwu"><span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span></div>'),sg=h('<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span> </div>'),og=h('<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),ig=h('<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),lg=h('<div class="text-[10px] text-dl-text-dim/35 mt-1"> </div>'),dg=h('<div class="vw-digest svelte-1l2nqwu"><div class="flex items-center gap-2 mb-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span></div> <div class="space-y-1"><!> <!> <!> <!></div></div>'),cg=h('<p class="vw-para"> </p>'),ug=h('<div class="vw-diff-added svelte-1l2nqwu"> </div>'),fg=h('<div class="vw-diff-deleted svelte-1l2nqwu"> </div>'),vg=h('<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow svelte-1l2nqwu"></div>'),pg=h('<div class="disclosure-text vw-section-body vw-body-frame svelte-1l2nqwu"><!></div>'),hg=h('<div><!> <div class="vw-section-meta svelte-1l2nqwu"><span> </span> <!> <!> <!> <!></div> <!> <!> <!> <!></div>'),mg=h('<section class="vw-report-shell svelte-1l2nqwu"><div class="vw-report-header svelte-1l2nqwu"><div class="vw-report-badges svelte-1l2nqwu"><!> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <!> <!></div></div> <!></section>'),xg=h('<div class="vw-data-divider svelte-1l2nqwu"><div class="vw-data-kicker svelte-1l2nqwu">Structured Data</div> <div class="vw-data-title svelte-1l2nqwu">표 / 정형 데이터</div></div>'),gg=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),_g=h("<th> </th>"),bg=h("<td> </td>"),yg=h("<tr></tr>"),wg=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),kg=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),Sg=h("<th> </th>"),Cg=h("<td> </td>"),$g=h("<tr></tr>"),Mg=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),Tg=h("<button> </button>"),zg=h('<span class="text-[9px] text-dl-text-dim/30"> </span>'),Eg=h('<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto"><!> <!></div>'),Ig=h('<div class="vw-table-wrap bg-dl-bg-card/10 svelte-1l2nqwu"><!> <div class="px-4 py-3"><div class="markdown-table overflow-x-auto svelte-1l2nqwu"><!></div></div></div>'),Ag=h("<th> </th>"),Lg=h("<td> </td>"),Ng=h("<tr></tr>"),Pg=h('<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02] svelte-1l2nqwu"><div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10"><!> <span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span></div> <div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Dg=h('<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card"> </th>'),Og=h('<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted"> </td>'),Rg=h("<tr></tr>"),Fg=h('<div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),jg=h('<article class="py-6 px-8"><!> <!> <!> <!></article>'),Bg=h('<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center"><div class="flex-1 min-w-0"><!> <h3 class="text-[16px] font-semibold text-dl-text"> </h3></div> <button class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"><!></button></div> <!>',1),Vg=h('<div class="flex flex-1 overflow-hidden min-h-0"><!> <main class="flex-1 overflow-y-auto min-w-0"><!></main></div>'),Ug=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8"><!> <p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p></div>'),Hg=h('<div class="flex flex-col h-full font-sans bg-dl-bg-dark"><!></div>');function qg(t,e){Ir(e,!0);let r=Fe(e,"stockCode",3,null),a=Fe(e,"onTopicChange",3,null),s=Y(null),o=Y(!1),i=Y(Ut(new Set)),l=Y(null),u=Y(null),f=Y(Ut([])),p=Y(null),g=Y(!1),x=Y(Ut([])),b=Y(Ut(new Map)),k=new Map,S=Y(!1),_=Y(Ut(new Map));const w={companyOverview:"회사 개요",companyHistory:"회사 연혁",articlesOfIncorporation:"정관 사항",capitalChange:"자본금 변동",shareCapital:"주식 현황",dividend:"배당",productService:"사업 내용",rawMaterial:"원재료",businessOverview:"사업 개요",salesOrder:"매출/수주",riskDerivative:"위험관리/파생",majorContractsAndRnd:"주요 계약/R&D",otherReferences:"기타 참고사항",consolidatedStatements:"연결 재무제표",fsSummary:"재무제표 요약",consolidatedNotes:"연결 주석",financialStatements:"개별 재무제표",financialNotes:"개별 주석",fundraising:"자금조달",BS:"재무상태표",IS:"손익계산서",CIS:"포괄손익계산서",CF:"현금흐름표",SCE:"자본변동표",ratios:"재무비율",audit:"감사 의견",mdna:"경영진 분석(MD&A)",internalControl:"내부통제",auditContract:"감사 계약",nonAuditContract:"비감사 계약",boardOfDirectors:"이사회",shareholderMeeting:"주주총회",auditSystem:"감사 체계",outsideDirector:"사외이사",majorHolder:"주요 주주",majorHolderChange:"주주 변동",minorityHolder:"소수주주",stockTotal:"주식 총수",treasuryStock:"자기주식",employee:"직원 현황",executivePay:"임원 보수",executive:"임원 현황",executivePayAllTotal:"전체 보수 총액",executivePayIndividual:"개인별 보수",topPay:"5억이상 상위 보수",unregisteredExecutivePay:"미등기임원 보수",affiliateGroup:"계열회사",investedCompany:"투자회사",relatedPartyTx:"특수관계 거래",corporateBond:"사채 관리",privateOfferingUsage:"사모자금 사용",publicOfferingUsage:"공모자금 사용",shortTermBond:"단기사채",investorProtection:"투자자 보호",disclosureChanges:"공시변경 사항",contingentLiability:"우발채무",sanction:"제재/조치",subsequentEvents:"후발사건",expertConfirmation:"전문가 확인",subsidiaryDetail:"종속회사 상세",affiliateGroupDetail:"계열회사 상세",investmentInOtherDetail:"타법인 출자 상세",rndDetail:"R&D 상세"},E={I:"I. 회사의 개요",II:"II. 사업의 내용",III:"III. 재무에 관한 사항",IV:"IV. 감사인의 감사의견 등",V:"V. 이사의 경영진단 및 분석의견",VI:"VI. 이사회 등 회사의 기관에 관한 사항",VII:"VII. 주주에 관한 사항",VIII:"VIII. 임원 및 직원 등에 관한 사항",IX:"IX. 계열회사 등에 관한 사항",X:"X. 대주주 등과의 거래내용",XI:"XI. 그 밖에 투자자 보호를 위하여 필요한 사항",XII:"XII. 상세표"},D={I:1,II:2,III:3,IV:4,V:5,VI:6,VII:7,VIII:8,IX:9,X:10,XI:11,XII:12};function M(R){return D[R]??99}function Z(R){return w[R]||R}function ce(R){return E[R]||R||"기타"}_r(()=>{r()&&P()});async function P(){var R,pe;v(o,!0),v(s,null),v(l,null),v(u,null),v(f,[],!0),v(p,null),k=new Map;try{const se=await kp(r());v(s,se.payload,!0),(R=n(s))!=null&&R.columns&&v(x,n(s).columns.filter(y=>/^\d{4}(Q[1-4])?$/.test(y)),!0);const ue=F((pe=n(s))==null?void 0:pe.rows);ue.length>0&&(v(i,new Set([ue[0].chapter]),!0),ue[0].topics.length>0&&$(ue[0].topics[0].topic,ue[0].chapter))}catch(se){console.error("viewer load error:",se)}v(o,!1)}async function $(R,pe){var se;if(n(l)!==R){if(v(l,R,!0),v(u,pe||null,!0),v(b,new Map,!0),v(_,new Map,!0),(se=a())==null||se(R,Z(R)),k.has(R)){const ue=k.get(R);v(f,ue.blocks||[],!0),v(p,ue.textDocument||null,!0);return}v(f,[],!0),v(p,null),v(g,!0);try{const ue=await wp(r(),R);v(f,ue.blocks||[],!0),v(p,ue.textDocument||null,!0),k.set(R,{blocks:n(f),textDocument:n(p)})}catch(ue){console.error("topic load error:",ue),v(f,[],!0),v(p,null)}v(g,!1)}}function X(R){const pe=new Set(n(i));pe.has(R)?pe.delete(R):pe.add(R),v(i,pe,!0)}function J(R,pe){const se=new Map(n(b));se.get(R)===pe?se.delete(R):se.set(R,pe),v(b,se,!0)}function me(R,pe){const se=new Map(n(_));se.set(R,pe),v(_,se,!0)}function B(R){return R==="updated"?"최근 수정":R==="new"?"신규":R==="stale"?"과거 유지":"유지"}function Te(R){return R==="updated"?"updated":R==="new"?"new":R==="stale"?"stale":"stable"}function F(R){if(!R)return[];const pe=new Map,se=new Set;for(const ue of R){const y=ue.chapter||"";pe.has(y)||pe.set(y,{chapter:y,topics:[]}),se.has(ue.topic)||(se.add(ue.topic),pe.get(y).topics.push({topic:ue.topic,source:ue.source||"docs"}))}return[...pe.values()].sort((ue,y)=>M(ue.chapter)-M(y.chapter))}function U(R){return String(R).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function le(R){return String(R||"").replaceAll(" "," ").replace(/\s+/g," ").trim()}function we(R){return!R||R.length>88?!1:/^\[.+\]$/.test(R)||/^【.+】$/.test(R)||/^[IVX]+\.\s/.test(R)||/^\d+\.\s/.test(R)||/^[가-힣]\.\s/.test(R)||/^\(\d+\)\s/.test(R)||/^\([가-힣]\)\s/.test(R)}function W(R){return/^\(\d+\)\s/.test(R)||/^\([가-힣]\)\s/.test(R)?"h5":"h4"}function ne(R){return/^\[.+\]$/.test(R)||/^【.+】$/.test(R)?"vw-h-bracket":/^\(\d+\)\s/.test(R)||/^\([가-힣]\)\s/.test(R)?"vw-h-sub":"vw-h-section"}function A(R){if(!R)return[];if(/^\|.+\|$/m.test(R)||/^#{1,3} /m.test(R)||/```/.test(R))return[{kind:"markdown",text:R}];const pe=[];let se=[];const ue=()=>{se.length!==0&&(pe.push({kind:"paragraph",text:se.join(" ")}),se=[])};for(const y of String(R).split(`
`)){const V=le(y);if(!V){ue();continue}if(we(V)){ue(),pe.push({kind:"heading",text:V,tag:W(V),className:ne(V)});continue}se.push(V)}return ue(),pe}function G(R){return R?R.kind==="annual"?`${R.year}Q4`:R.year&&R.quarter?`${R.year}Q${R.quarter}`:R.label||"":""}function q(R){var ue;const pe=A(R);if(pe.length===0)return"";if(((ue=pe[0])==null?void 0:ue.kind)==="markdown")return Va(R);let se="";for(const y of pe){if(y.kind==="heading"){se+=`<${y.tag} class="${y.className}">${U(y.text)}</${y.tag}>`;continue}se+=`<p class="vw-para">${U(y.text)}</p>`}return se}function L(R){if(!R)return"";const pe=R.trim().split(`
`).filter(ue=>ue.trim());let se="";for(const ue of pe){const y=ue.trim();/^[가-힣]\.\s/.test(y)||/^\d+[-.]/.test(y)?se+=`<h4 class="vw-h-section">${y}</h4>`:/^\(\d+\)\s/.test(y)||/^\([가-힣]\)\s/.test(y)?se+=`<h5 class="vw-h-sub">${y}</h5>`:/^\[.+\]$/.test(y)||/^【.+】$/.test(y)?se+=`<h4 class="vw-h-bracket">${y}</h4>`:se+=`<h5 class="vw-h-sub">${y}</h5>`}return se}function H(R){var se;const pe=n(b).get(R.id);return pe&&((se=R==null?void 0:R.views)!=null&&se[pe])?R.views[pe]:(R==null?void 0:R.latest)||null}function j(R,pe){var ue,y;const se=n(b).get(R.id);return se?se===pe:((y=(ue=R==null?void 0:R.latest)==null?void 0:ue.period)==null?void 0:y.label)===pe}function K(R){return n(b).has(R.id)}function _e(R){return R==="updated"?"변경 있음":R==="new"?"직전 없음":"직전과 동일"}function $e(R){var V,re,ie;if(!R)return[];const pe=A(R.body);if(pe.length===0||((V=pe[0])==null?void 0:V.kind)==="markdown"||!((re=R.prevPeriod)!=null&&re.label)||!((ie=R.diff)!=null&&ie.length))return pe;const se=[];for(const fe of R.diff)for(const N of fe.paragraphs||[])se.push({kind:fe.kind,text:le(N)});const ue=[];let y=0;for(const fe of pe){if(fe.kind!=="paragraph"){ue.push(fe);continue}for(;y<se.length&&se[y].kind==="removed";)ue.push({kind:"removed",text:se[y].text}),y+=1;y<se.length&&["same","added"].includes(se[y].kind)?(ue.push({kind:se[y].kind,text:se[y].text||fe.text}),y+=1):ue.push({kind:"same",text:fe.text})}for(;y<se.length;)ue.push({kind:se[y].kind,text:se[y].text}),y+=1;return ue}function te(R){return R==null?!1:/^-?[\d,.]+%?$/.test(String(R).trim().replace(/,/g,""))}function De(R){return R==null?!1:/^-[\d.]+/.test(String(R).trim().replace(/,/g,""))}function tt(R,pe){if(R==null||R==="")return"";const se=typeof R=="number"?R:Number(String(R).replace(/,/g,""));if(isNaN(se))return String(R);if(pe<=1)return se.toLocaleString("ko-KR");const ue=se/pe;return Number.isInteger(ue)?ue.toLocaleString("ko-KR"):ue.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g,",")}function st(R){if(R==null||R==="")return"";const pe=String(R).trim();if(pe.includes(","))return pe;const se=pe.match(/^(-?\d+)(\.\d+)?(%?)$/);return se?se[1].replace(/\B(?=(\d{3})+(?!\d))/g,",")+(se[2]||"")+(se[3]||""):pe}function Ge(R){var pe,se;return(pe=n(s))!=null&&pe.rows&&((se=n(s).rows.find(ue=>ue.topic===R))==null?void 0:se.chapter)||null}function rt(R){const pe=R.match(/^(\d{4})(Q([1-4]))?$/);if(!pe)return"0000_0";const se=pe[1],ue=pe[3]||"5";return`${se}_${ue}`}function dt(R){return[...R].sort((pe,se)=>rt(se).localeCompare(rt(pe)))}let nt=O(()=>n(f).filter(R=>R.kind!=="text"));var ot=Hg(),xt=d(ot);{var $t=R=>{var pe=Lx(),se=d(pe);Kr(se,{size:18,class:"animate-spin"}),c(R,pe)},Nt=R=>{var pe=Vg(),se=d(pe);{var ue=fe=>{var N=Rx(),ee=d(N),Ce=d(ee);{var ve=Ne=>{var de=Nx(),ze=d(de);T(()=>z(ze,`${n(x).length??""}개 기간 · ${n(x)[0]??""} ~ ${n(x)[n(x).length-1]??""}`)),c(Ne,de)};C(Ce,Ne=>{n(x).length>0&&Ne(ve)})}var ke=m(ee,2);Ie(ke,17,()=>F(n(s).rows),Le,(Ne,de)=>{var ze=Ox(),Re=d(ze),He=d(Re);{var be=Ye=>{kl(Ye,{size:11,class:"flex-shrink-0 opacity-40"})},et=O(()=>n(i).has(n(de).chapter)),St=Ye=>{pu(Ye,{size:11,class:"flex-shrink-0 opacity-40"})};C(He,Ye=>{n(et)?Ye(be):Ye(St,-1)})}var at=m(He,2),Rt=d(at),Be=m(at,2),Ae=d(Be),Ee=m(Re,2);{var wt=Ye=>{var At=Dx();Ie(At,21,()=>n(de).topics,Le,(Ht,Ct)=>{var Mt=Px(),ct=d(Mt);{var rr=_t=>{Uo(_t,{size:11,class:"flex-shrink-0 text-blue-400/40"})},Tr=_t=>{Wi(_t,{size:11,class:"flex-shrink-0 text-emerald-400/40"})},kr=_t=>{En(_t,{size:11,class:"flex-shrink-0 opacity-30"})};C(ct,_t=>{n(Ct).source==="finance"?_t(rr):n(Ct).source==="report"?_t(Tr,1):_t(kr,-1)})}var Ur=m(ct,2),zr=d(Ur);T(_t=>{qe(Mt,1,`group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											${n(l)===n(Ct).topic?"bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]":"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent"}`),z(zr,_t)},[()=>Z(n(Ct).topic)]),he("click",Mt,()=>$(n(Ct).topic,n(de).chapter)),c(Ht,Mt)}),c(Ye,At)},Pt=O(()=>n(i).has(n(de).chapter));C(Ee,Ye=>{n(Pt)&&Ye(wt)})}T(Ye=>{z(Rt,Ye),z(Ae,n(de).topics.length)},[()=>ce(n(de).chapter)]),he("click",Re,()=>X(n(de).chapter)),c(Ne,ze)}),c(fe,N)};C(se,fe=>{n(S)||fe(ue)})}var y=m(se,2),V=d(y);{var re=fe=>{var N=Fx(),ee=d(N);En(ee,{size:32,strokeWidth:1,class:"opacity-20"}),c(fe,N)},ie=fe=>{var N=Bg(),ee=ae(N),Ce=d(ee),ve=d(Ce);{var ke=Be=>{var Ae=jx(),Ee=d(Ae);T(wt=>z(Ee,wt),[()=>ce(n(u)||Ge(n(l)))]),c(Be,Ae)},Ne=O(()=>n(u)||Ge(n(l)));C(ve,Be=>{n(Ne)&&Be(ke)})}var de=m(ve,2),ze=d(de),Re=m(Ce,2),He=d(Re);{var be=Be=>{mu(Be,{size:15})},et=Be=>{hu(Be,{size:15})};C(He,Be=>{n(S)?Be(be):Be(et,-1)})}var St=m(ee,2);{var at=Be=>{var Ae=Bx(),Ee=d(Ae);Kr(Ee,{size:16,class:"animate-spin"}),c(Be,Ae)},Rt=Be=>{var Ae=jg(),Ee=d(Ae);{var wt=Mt=>{var ct=Vx();c(Mt,ct)};C(Ee,Mt=>{var ct,rr;n(f).length===0&&!(((rr=(ct=n(p))==null?void 0:ct.sections)==null?void 0:rr.length)>0)&&Mt(wt)})}var Pt=m(Ee,2);{var Ye=Mt=>{var ct=mg(),rr=d(ct),Tr=d(rr),kr=d(Tr);{var Ur=it=>{var Pe=Ux(),Qe=d(Pe);T(ut=>z(Qe,`최신 기준 ${ut??""}`),[()=>G(n(p).latestPeriod)]),c(it,Pe)};C(kr,it=>{n(p).latestPeriod&&it(Ur)})}var zr=m(kr,2);{var _t=it=>{var Pe=Hx(),Qe=d(Pe);T((ut,Ot)=>z(Qe,`커버리지 ${ut??""}~${Ot??""}`),[()=>G(n(p).firstPeriod),()=>G(n(p).latestPeriod)]),c(it,Pe)};C(zr,it=>{n(p).firstPeriod&&it(_t)})}var qt=m(zr,2),Tt=d(qt),Dt=m(qt,2);{var cr=it=>{var Pe=qx(),Qe=d(Pe);T(()=>z(Qe,`최근 수정 ${n(p).updatedCount??""}개`)),c(it,Pe)};C(Dt,it=>{n(p).updatedCount>0&&it(cr)})}var fr=m(Dt,2);{var bt=it=>{var Pe=Kx(),Qe=d(Pe);T(()=>z(Qe,`신규 ${n(p).newCount??""}개`)),c(it,Pe)};C(fr,it=>{n(p).newCount>0&&it(bt)})}var Ve=m(fr,2);{var nr=it=>{var Pe=Wx(),Qe=d(Pe);T(()=>z(Qe,`과거 유지 ${n(p).staleCount??""}개`)),c(it,Pe)};C(Ve,it=>{n(p).staleCount>0&&it(nr)})}var Cr=m(rr,2);Ie(Cr,17,()=>n(p).sections,Le,(it,Pe)=>{const Qe=O(()=>H(n(Pe))),ut=O(()=>K(n(Pe)));var Ot=hg(),zt=d(Ot);{var gt=Me=>{var ye=Yx();Ie(ye,21,()=>n(Pe).headingPath,Le,(Oe,Je)=>{var ft=Gx(),vt=d(ft);Gn(vt,()=>L(n(Je).text)),c(Oe,ft)}),c(Me,ye)};C(zt,Me=>{var ye;((ye=n(Pe).headingPath)==null?void 0:ye.length)>0&&Me(gt)})}var yt=m(zt,2),Bt=d(yt),Gt=d(Bt),Qt=m(Bt,2);{var br=Me=>{var ye=Jx(),Oe=d(ye);T(Je=>z(Oe,`최신 ${Je??""}`),[()=>G(n(Pe).latestPeriod)]),c(Me,ye)};C(Qt,Me=>{var ye;(ye=n(Pe).latestPeriod)!=null&&ye.label&&Me(br)})}var Rr=m(Qt,2);{var $r=Me=>{var ye=Xx(),Oe=d(ye);T(Je=>z(Oe,`최초 ${Je??""}`),[()=>G(n(Pe).firstPeriod)]),c(Me,ye)};C(Rr,Me=>{var ye,Oe;(ye=n(Pe).firstPeriod)!=null&&ye.label&&n(Pe).firstPeriod.label!==((Oe=n(Pe).latestPeriod)==null?void 0:Oe.label)&&Me($r)})}var sr=m(Rr,2);{var vr=Me=>{var ye=Qx(),Oe=d(ye);T(()=>z(Oe,`${n(Pe).periodCount??""}기간`)),c(Me,ye)};C(sr,Me=>{n(Pe).periodCount>0&&Me(vr)})}var Hr=m(sr,2);{var er=Me=>{var ye=Zx(),Oe=d(ye);T(()=>z(Oe,`최근 변경 ${n(Pe).latestChange??""}`)),c(Me,ye)};C(Hr,Me=>{n(Pe).latestChange&&Me(er)})}var mr=m(yt,2);{var pr=Me=>{var ye=tg();Ie(ye,21,()=>n(Pe).timeline,Le,(Oe,Je)=>{var ft=eg(),vt=d(ft),It=d(vt);T((Yt,Kt)=>{qe(ft,1,`vw-timeline-chip ${Yt??""}`,"svelte-1l2nqwu"),z(It,Kt)},[()=>j(n(Pe),n(Je).period.label)?"is-active":"",()=>G(n(Je).period)]),he("click",ft,()=>J(n(Pe).id,n(Je).period.label)),c(Oe,ft)}),c(Me,ye)};C(mr,Me=>{var ye;((ye=n(Pe).timeline)==null?void 0:ye.length)>0&&Me(pr)})}var bn=m(mr,2);{var sn=Me=>{var ye=ag(),Oe=d(ye),Je=d(Oe),ft=m(Oe,2);{var vt=Wt=>{var ur=rg(),kt=d(ur);T(Q=>z(kt,`비교 ${Q??""}`),[()=>G(n(Qe).prevPeriod)]),c(Wt,ur)},It=Wt=>{var ur=ng();c(Wt,ur)};C(ft,Wt=>{var ur;(ur=n(Qe).prevPeriod)!=null&&ur.label?Wt(vt):Wt(It,-1)})}var Yt=m(ft,2),Kt=d(Yt);T((Wt,ur)=>{z(Je,`선택 ${Wt??""}`),z(Kt,ur)},[()=>G(n(Qe).period),()=>_e(n(Qe).status)]),c(Me,ye)};C(bn,Me=>{n(ut)&&n(Qe)&&Me(sn)})}var In=m(bn,2);{var I=Me=>{const ye=O(()=>n(Qe).digest);var Oe=dg(),Je=d(Oe),ft=d(Je),vt=d(ft),It=m(Je,2),Yt=d(It);Ie(Yt,17,()=>n(ye).items.filter(Q=>Q.kind==="numeric"),Le,(Q,xe)=>{var je=sg(),Ue=m(d(je));T(()=>z(Ue,` ${n(xe).text??""}`)),c(Q,je)});var Kt=m(Yt,2);Ie(Kt,17,()=>n(ye).items.filter(Q=>Q.kind==="added"),Le,(Q,xe)=>{var je=og(),Ue=m(d(je),2),Ze=d(Ue);T(()=>z(Ze,n(xe).text)),c(Q,je)});var Wt=m(Kt,2);Ie(Wt,17,()=>n(ye).items.filter(Q=>Q.kind==="removed"),Le,(Q,xe)=>{var je=ig(),Ue=m(d(je),2),Ze=d(Ue);T(()=>z(Ze,n(xe).text)),c(Q,je)});var ur=m(Wt,2);{var kt=Q=>{var xe=lg(),je=d(xe);T(()=>z(je,`외 ${n(ye).wordingCount??""}건 문구 수정`)),c(Q,xe)};C(ur,Q=>{n(ye).wordingCount>0&&Q(kt)})}T(()=>z(vt,`${n(ye).to??""} vs ${n(ye).from??""}`)),c(Me,Oe)};C(In,Me=>{var ye,Oe,Je;n(ut)&&((Je=(Oe=(ye=n(Qe))==null?void 0:ye.digest)==null?void 0:Oe.items)==null?void 0:Je.length)>0&&Me(I)})}var ge=m(In,2);{var Ke=Me=>{var ye=Se(),Oe=ae(ye);{var Je=vt=>{var It=vg();Ie(It,21,()=>$e(n(Qe)),Le,(Yt,Kt)=>{var Wt=Se(),ur=ae(Wt);{var kt=Ue=>{var Ze=Se(),Ft=ae(Ze);Gn(Ft,()=>L(n(Kt).text)),c(Ue,Ze)},Q=Ue=>{var Ze=cg(),Ft=d(Ze);T(()=>z(Ft,n(Kt).text)),c(Ue,Ze)},xe=Ue=>{var Ze=ug(),Ft=d(Ze);T(()=>z(Ft,n(Kt).text)),c(Ue,Ze)},je=Ue=>{var Ze=fg(),Ft=d(Ze);T(()=>z(Ft,n(Kt).text)),c(Ue,Ze)};C(ur,Ue=>{n(Kt).kind==="heading"?Ue(kt):n(Kt).kind==="same"?Ue(Q,1):n(Kt).kind==="added"?Ue(xe,2):n(Kt).kind==="removed"&&Ue(je,3)})}c(Yt,Wt)}),c(vt,It)},ft=vt=>{var It=pg(),Yt=d(It);Gn(Yt,()=>q(n(Qe).body)),c(vt,It)};C(Oe,vt=>{var It,Yt;n(ut)&&((It=n(Qe).prevPeriod)!=null&&It.label)&&((Yt=n(Qe).diff)==null?void 0:Yt.length)>0?vt(Je):vt(ft,-1)})}c(Me,ye)};C(ge,Me=>{n(Qe)&&Me(Ke)})}T((Me,ye)=>{qe(Ot,1,`vw-text-section ${n(Pe).status==="stale"?"vw-text-section-stale":""}`,"svelte-1l2nqwu"),qe(Bt,1,`vw-status-pill ${Me??""}`,"svelte-1l2nqwu"),z(Gt,ye)},[()=>Te(n(Pe).status),()=>B(n(Pe).status)]),c(it,Ot)}),T(()=>z(Tt,`본문 ${n(p).sectionCount??""}개`)),c(Mt,ct)};C(Pt,Mt=>{var ct,rr;((rr=(ct=n(p))==null?void 0:ct.sections)==null?void 0:rr.length)>0&&Mt(Ye)})}var At=m(Pt,2);{var Ht=Mt=>{var ct=xg();c(Mt,ct)};C(At,Mt=>{n(nt).length>0&&Mt(Ht)})}var Ct=m(At,2);Ie(Ct,17,()=>n(nt),Le,(Mt,ct)=>{var rr=Se(),Tr=ae(rr);{var kr=Tt=>{const Dt=O(()=>{var gt;return((gt=n(ct).data)==null?void 0:gt.columns)||[]}),cr=O(()=>{var gt;return((gt=n(ct).data)==null?void 0:gt.rows)||[]}),fr=O(()=>n(ct).meta||{}),bt=O(()=>n(fr).scaleDivisor||1);var Ve=wg(),nr=ae(Ve);{var Cr=gt=>{var yt=gg(),Bt=d(yt);T(()=>z(Bt,`(단위: ${n(fr).scale??""})`)),c(gt,yt)};C(nr,gt=>{n(fr).scale&&gt(Cr)})}var it=m(nr,2),Pe=d(it),Qe=d(Pe),ut=d(Qe),Ot=d(ut);Ie(Ot,21,()=>n(Dt),Le,(gt,yt,Bt)=>{const Gt=O(()=>/^\d{4}/.test(n(yt)));var Qt=_g(),br=d(Qt);T(()=>{qe(Qt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(Gt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${Bt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),z(br,n(yt))}),c(gt,Qt)});var zt=m(ut);Ie(zt,21,()=>n(cr),Le,(gt,yt,Bt)=>{var Gt=yg();qe(Gt,1,`hover:bg-white/[0.03] ${Bt%2===1?"bg-white/[0.012]":""}`),Ie(Gt,21,()=>n(Dt),Le,(Qt,br,Rr)=>{const $r=O(()=>n(yt)[n(br)]??""),sr=O(()=>te(n($r))),vr=O(()=>De(n($r))),Hr=O(()=>n(sr)?tt(n($r),n(bt)):n($r));var er=bg(),mr=d(er);T(()=>{qe(er,1,`px-3 py-1.5 border-b border-white/[0.025]
																	${n(sr)?"text-right tabular-nums font-mono text-[11.5px]":"whitespace-nowrap"}
																	${n(vr)?"text-red-400/60":n(sr)?"text-dl-text/90":""}
																	${Rr===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]":"text-dl-text-muted"}
																	${Rr===0&&Bt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),z(mr,n(Hr))}),c(Qt,er)}),c(gt,Gt)}),c(Tt,Ve)},Ur=Tt=>{const Dt=O(()=>{var gt;return((gt=n(ct).data)==null?void 0:gt.columns)||[]}),cr=O(()=>{var gt;return((gt=n(ct).data)==null?void 0:gt.rows)||[]}),fr=O(()=>n(ct).meta||{}),bt=O(()=>n(fr).scaleDivisor||1);var Ve=Mg(),nr=ae(Ve);{var Cr=gt=>{var yt=kg(),Bt=d(yt);T(()=>z(Bt,`(단위: ${n(fr).scale??""})`)),c(gt,yt)};C(nr,gt=>{n(fr).scale&&gt(Cr)})}var it=m(nr,2),Pe=d(it),Qe=d(Pe),ut=d(Qe),Ot=d(ut);Ie(Ot,21,()=>n(Dt),Le,(gt,yt,Bt)=>{const Gt=O(()=>/^\d{4}/.test(n(yt)));var Qt=Sg(),br=d(Qt);T(()=>{qe(Qt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(Gt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${Bt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),z(br,n(yt))}),c(gt,Qt)});var zt=m(ut);Ie(zt,21,()=>n(cr),Le,(gt,yt,Bt)=>{var Gt=$g();qe(Gt,1,`hover:bg-white/[0.03] ${Bt%2===1?"bg-white/[0.012]":""}`),Ie(Gt,21,()=>n(Dt),Le,(Qt,br,Rr)=>{const $r=O(()=>n(yt)[n(br)]??""),sr=O(()=>te(n($r))),vr=O(()=>De(n($r))),Hr=O(()=>n(sr)?n(bt)>1?tt(n($r),n(bt)):st(n($r)):n($r));var er=Cg(),mr=d(er);T(()=>{qe(er,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(sr)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(vr)?"text-red-400/60":n(sr)?"text-dl-text/90":""}
																	${Rr===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Rr===0&&Bt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),z(mr,n(Hr))}),c(Qt,er)}),c(gt,Gt)}),c(Tt,Ve)},zr=Tt=>{const Dt=O(()=>dt(Object.keys(n(ct).rawMarkdown))),cr=O(()=>n(_).get(n(ct).block)??0),fr=O(()=>n(Dt)[n(cr)]||n(Dt)[0]);var bt=Ig(),Ve=d(bt);{var nr=Qe=>{var ut=Eg(),Ot=d(ut);Ie(Ot,17,()=>n(Dt).slice(0,8),Le,(yt,Bt,Gt)=>{var Qt=Tg(),br=d(Qt);T(()=>{qe(Qt,1,`px-2 py-0.5 rounded text-[10px] transition-colors
															${Gt===n(cr)?"bg-white/[0.08] text-dl-text font-medium":"text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]"}`),z(br,n(Bt))}),he("click",Qt,()=>me(n(ct).block,Gt)),c(yt,Qt)});var zt=m(Ot,2);{var gt=yt=>{var Bt=zg(),Gt=d(Bt);T(()=>z(Gt,`외 ${n(Dt).length-8}개`)),c(yt,Bt)};C(zt,yt=>{n(Dt).length>8&&yt(gt)})}c(Qe,ut)};C(Ve,Qe=>{n(Dt).length>1&&Qe(nr)})}var Cr=m(Ve,2),it=d(Cr),Pe=d(it);Gn(Pe,()=>Va(n(ct).rawMarkdown[n(fr)])),c(Tt,bt)},_t=Tt=>{const Dt=O(()=>{var ut;return((ut=n(ct).data)==null?void 0:ut.columns)||[]}),cr=O(()=>{var ut;return((ut=n(ct).data)==null?void 0:ut.rows)||[]});var fr=Pg(),bt=d(fr),Ve=d(bt);Wi(Ve,{size:12,class:"text-emerald-400/50"});var nr=m(bt,2),Cr=d(nr),it=d(Cr),Pe=d(it);Ie(Pe,21,()=>n(Dt),Le,(ut,Ot,zt)=>{const gt=O(()=>/^\d{4}/.test(n(Ot)));var yt=Ag(),Bt=d(yt);T(()=>{qe(yt,1,`px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															${n(gt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
															${zt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),z(Bt,n(Ot))}),c(ut,yt)});var Qe=m(it);Ie(Qe,21,()=>n(cr),Le,(ut,Ot,zt)=>{var gt=Ng();qe(gt,1,`hover:bg-white/[0.03] ${zt%2===1?"bg-white/[0.012]":""}`),Ie(gt,21,()=>n(Dt),Le,(yt,Bt,Gt)=>{const Qt=O(()=>n(Ot)[n(Bt)]??""),br=O(()=>te(n(Qt))),Rr=O(()=>De(n(Qt)));var $r=Lg(),sr=d($r);T(vr=>{qe($r,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(br)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(Rr)?"text-red-400/60":n(br)?"text-dl-text/90":""}
																	${Gt===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Gt===0&&zt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),z(sr,vr)},[()=>n(br)?st(n(Qt)):n(Qt)]),c(yt,$r)}),c(ut,gt)}),c(Tt,fr)},qt=Tt=>{const Dt=O(()=>n(ct).data.columns),cr=O(()=>n(ct).data.rows||[]);var fr=Fg(),bt=d(fr),Ve=d(bt),nr=d(Ve),Cr=d(nr);Ie(Cr,21,()=>n(Dt),Le,(Pe,Qe)=>{var ut=Dg(),Ot=d(ut);T(()=>z(Ot,n(Qe))),c(Pe,ut)});var it=m(nr);Ie(it,21,()=>n(cr),Le,(Pe,Qe,ut)=>{var Ot=Rg();qe(Ot,1,`hover:bg-white/[0.03] ${ut%2===1?"bg-white/[0.012]":""}`),Ie(Ot,21,()=>n(Dt),Le,(zt,gt)=>{var yt=Og(),Bt=d(yt);T(()=>z(Bt,n(Qe)[n(gt)]??"")),c(zt,yt)}),c(Pe,Ot)}),c(Tt,fr)};C(Tr,Tt=>{var Dt,cr;n(ct).kind==="finance"?Tt(kr):n(ct).kind==="structured"?Tt(Ur,1):n(ct).kind==="raw_markdown"&&n(ct).rawMarkdown?Tt(zr,2):n(ct).kind==="report"?Tt(_t,3):((cr=(Dt=n(ct).data)==null?void 0:Dt.columns)==null?void 0:cr.length)>0&&Tt(qt,4)})}c(Mt,rr)}),c(Be,Ae)};C(St,Be=>{n(g)?Be(at):Be(Rt,-1)})}T(Be=>{z(ze,Be),lr(Re,"title",n(S)?"목차 표시":"전체화면")},[()=>Z(n(l))]),he("click",Re,()=>v(S,!n(S))),c(fe,N)};C(V,fe=>{n(l)?fe(ie,-1):fe(re)})}c(R,pe)},dr=R=>{var pe=Ug(),se=d(pe);En(se,{size:36,strokeWidth:1,class:"opacity-20"}),c(R,pe)};C(xt,R=>{var pe;n(o)?R($t):(pe=n(s))!=null&&pe.rows?R(Nt,1):R(dr,-1)})}c(t,ot),Ar()}Gr(["click"]);var Kg=h('<span class="text-[12px] font-semibold text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim"> </span>',1),Wg=h('<span class="text-[12px] font-semibold text-dl-text"> </span>'),Gg=h('<span class="text-[12px] font-semibold text-dl-text">데이터</span>'),Yg=h('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" title="Excel 다운로드"><!></button> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button>',1),Jg=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Xg=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed"> </pre>'),Qg=h('<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2"> </div>'),Zg=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),e1=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),t1=h("<!> <!>",1),r1=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),n1=h('<div class="p-4"><!></div>'),a1=h('<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">표시할 내용이 없습니다</div>'),s1=h('<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark"><div class="flex items-center justify-between h-10 mt-8 px-4 border-b border-dl-border/40 flex-shrink-0"><div class="flex items-center gap-2 min-w-0"><!></div> <div class="flex items-center gap-1"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 overflow-auto min-h-0"><!></div></div>');function o1(t,e){Ir(e,!0);let r=Fe(e,"mode",3,null),a=Fe(e,"company",3,null),s=Fe(e,"data",3,null),o=Fe(e,"onTopicChange",3,null),i=Fe(e,"onFullscreen",3,null),l=Fe(e,"isFullscreen",3,!1),u=Y(!1);async function f(){var B;if(!(!((B=a())!=null&&B.stockCode)||n(u))){v(u,!0);try{await yp(a().stockCode)}catch(Te){console.error("Excel download error:",Te)}v(u,!1)}}function p(B){return B?/^\|.+\|$/m.test(B)||/^#{1,3} /m.test(B)||/\*\*[^*]+\*\*/m.test(B)||/```/.test(B):!1}var g=s1(),x=d(g),b=d(x),k=d(b);{var S=B=>{var Te=Kg(),F=ae(Te),U=d(F),le=m(F,2),we=d(le);T(()=>{z(U,a().corpName||a().company),z(we,a().stockCode)}),c(B,Te)},_=B=>{var Te=Wg(),F=d(Te);T(()=>z(F,s().label)),c(B,Te)},w=B=>{var Te=Gg();c(B,Te)};C(k,B=>{var Te;r()==="viewer"&&a()?B(S):r()==="data"&&((Te=s())!=null&&Te.label)?B(_,1):r()==="data"&&B(w,2)})}var E=m(b,2),D=d(E);{var M=B=>{var Te=Yg(),F=ae(Te),U=d(F);{var le=q=>{Kr(q,{size:14,class:"animate-spin"})},we=q=>{lo(q,{size:14})};C(U,q=>{n(u)?q(le):q(we,-1)})}var W=m(F,2),ne=d(W);{var A=q=>{mu(q,{size:14})},G=q=>{hu(q,{size:14})};C(ne,q=>{l()?q(A):q(G,-1)})}T(()=>{F.disabled=n(u),lr(W,"title",l()?"패널 모드로":"전체 화면")}),he("click",F,f),he("click",W,()=>{var q;return(q=i())==null?void 0:q()}),c(B,Te)};C(D,B=>{var Te;r()==="viewer"&&((Te=a())!=null&&Te.stockCode)&&B(M)})}var Z=m(D,2),ce=d(Z);Ba(ce,{size:15});var P=m(x,2),$=d(P);{var X=B=>{qg(B,{get stockCode(){return a().stockCode},get onTopicChange(){return o()}})},J=B=>{var Te=n1(),F=d(Te);{var U=W=>{var ne=Se(),A=ae(ne);{var G=H=>{var j=Jg(),K=d(j);Gn(K,()=>Va(s())),c(H,j)},q=O(()=>p(s())),L=H=>{var j=Xg(),K=d(j);T(()=>z(K,s())),c(H,j)};C(A,H=>{n(q)?H(G):H(L,-1)})}c(W,ne)},le=W=>{var ne=t1(),A=ae(ne);{var G=K=>{var _e=Qg(),$e=d(_e);T(()=>z($e,s().module)),c(K,_e)};C(A,K=>{s().module&&K(G)})}var q=m(A,2);{var L=K=>{var _e=Zg(),$e=d(_e);Gn($e,()=>Va(s().text)),c(K,_e)},H=O(()=>p(s().text)),j=K=>{var _e=e1(),$e=d(_e);T(()=>z($e,s().text)),c(K,_e)};C(q,K=>{n(H)?K(L):K(j,-1)})}c(W,ne)},we=W=>{var ne=r1(),A=d(ne);T(G=>z(A,G),[()=>JSON.stringify(s(),null,2)]),c(W,ne)};C(F,W=>{var ne;typeof s()=="string"?W(U):(ne=s())!=null&&ne.text?W(le,1):W(we,-1)})}c(B,Te)},me=B=>{var Te=a1();c(B,Te)};C($,B=>{r()==="viewer"&&a()?B(X):r()==="data"&&s()?B(J,1):B(me,-1)})}he("click",Z,()=>{var B;return(B=e.onClose)==null?void 0:B.call(e)}),c(t,g),Ar()}Gr(["click"]);var i1=h('<div class="flex flex-col items-center justify-center py-8 gap-2"><!> <span class="text-[11px] text-dl-text-dim">목차 로딩 중...</span></div>'),l1=h('<button><!> <span class="truncate"> </span></button>'),d1=h('<div class="mb-1 pb-1 border-b border-dl-border/15"><div class="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-amber-400/70 uppercase tracking-wider"><!> <span>즐겨찾기</span></div> <!></div>'),c1=h('<button class="flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors text-dl-text-dim hover:text-dl-text hover:bg-white/5"><!> <span class="truncate"> </span></button>'),u1=h('<div class="mb-1 pb-1 border-b border-dl-border/15"><div class="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-dl-text-dim/60 uppercase tracking-wider"><!> <span>최근</span></div> <!></div>'),f1=h('<span class="w-1.5 h-1.5 rounded-full bg-emerald-400/70" title="최근 변경"></span>'),v1=h('<span class="text-[9px] text-dl-text-dim/60 font-mono"> </span>'),p1=h('<button><!> <span class="truncate"> </span> <span class="ml-auto flex items-center gap-0.5"><!> <!> <!></span></button>'),h1=h('<div class="ml-2 border-l border-dl-border/20 pl-1"></div>'),m1=h('<div class="mb-0.5"><button class="flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-left text-[11px] font-semibold uppercase tracking-wider text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"><!> <span class="truncate"> </span> <span> </span></button> <!></div>'),x1=h("<!> <!> <!>",1),g1=h('<div class="px-3 py-6 text-center text-[12px] text-dl-text-dim">종목을 선택하면 목차가 표시됩니다</div>'),_1=h('<nav class="flex flex-col h-full min-h-0 overflow-y-auto py-2 px-1"><!></nav>');function b1(t,e){Ir(e,!0);let r=Fe(e,"toc",3,null),a=Fe(e,"loading",3,!1),s=Fe(e,"selectedTopic",3,null),o=Fe(e,"expandedChapters",19,()=>new Set),i=Fe(e,"bookmarks",19,()=>[]),l=Fe(e,"recentHistory",19,()=>[]),u=Fe(e,"visitedTopics",19,()=>new Set),f=Fe(e,"onSelectTopic",3,null),p=Fe(e,"onToggleChapter",3,null),g=Fe(e,"onPrefetch",3,null),x=null;function b(P){clearTimeout(x),x=setTimeout(()=>{var $;return($=g())==null?void 0:$(P)},300)}function k(){clearTimeout(x)}const S=new Set(["BS","IS","CIS","CF","SCE","ratios"]);function _(P){return S.has(P)?Uo:En}function w(P){return P.tableCount>0&&P.textCount>0?"both":P.tableCount>0?"table":P.textCount>0?"text":"empty"}_r(()=>{s()&&$c().then(()=>{const P=document.querySelector(".viewer-nav-active-item");P&&P.scrollIntoView({block:"nearest",behavior:"smooth"})})});var E=_1(),D=d(E);{var M=P=>{var $=i1(),X=d($);Kr(X,{size:18,class:"animate-spin text-dl-text-dim"}),c(P,$)},Z=P=>{var $=x1(),X=ae($);{var J=F=>{const U=O(()=>i().map(ne=>{for(const A of r().chapters){const G=A.topics.find(q=>q.topic===ne);if(G)return{...G,chapter:A.chapter}}return null}).filter(Boolean));var le=Se(),we=ae(le);{var W=ne=>{var A=d1(),G=d(A),q=d(G);Ji(q,{size:10,fill:"currentColor"});var L=m(G,2);Ie(L,17,()=>n(U),Le,(H,j)=>{const K=O(()=>s()===n(j).topic);var _e=l1(),$e=d(_e);Ji($e,{size:10,class:"text-amber-400/60 flex-shrink-0",fill:"currentColor"});var te=m($e,2),De=d(te);T(()=>{qe(_e,1,`flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors ${n(K)?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-muted hover:text-dl-text hover:bg-white/5"}`),z(De,n(j).label)}),he("click",_e,()=>{var tt;return(tt=f())==null?void 0:tt(n(j).topic,n(j).chapter)}),c(H,_e)}),c(ne,A)};C(we,ne=>{n(U).length>0&&ne(W)})}c(F,le)};C(X,F=>{i().length>0&&F(J)})}var me=m(X,2);{var B=F=>{const U=O(()=>new Set(i())),le=O(()=>l().slice(0,5).filter(A=>A.topic!==s()&&!n(U).has(A.topic)));var we=Se(),W=ae(we);{var ne=A=>{var G=u1(),q=d(G),L=d(q);fo(L,{size:10});var H=m(q,2);Ie(H,17,()=>n(le),Le,(j,K)=>{var _e=c1(),$e=d(_e);fo($e,{size:10,class:"text-dl-text-dim/30 flex-shrink-0"});var te=m($e,2),De=d(te);T(()=>z(De,n(K).label)),he("click",_e,()=>{var tt;return(tt=f())==null?void 0:tt(n(K).topic,null)}),c(j,_e)}),c(A,G)};C(W,A=>{n(le).length>0&&A(ne)})}c(F,we)};C(me,F=>{l().length>0&&F(B)})}var Te=m(me,2);Ie(Te,17,()=>r().chapters,Le,(F,U)=>{const le=O(()=>n(U).topics.filter(De=>u().has(De.topic)).length);var we=m1(),W=d(we),ne=d(W);{var A=De=>{kl(De,{size:12})},G=O(()=>o().has(n(U).chapter)),q=De=>{pu(De,{size:12})};C(ne,De=>{n(G)?De(A):De(q,-1)})}var L=m(ne,2),H=d(L),j=m(L,2),K=d(j),_e=m(W,2);{var $e=De=>{var tt=h1();Ie(tt,21,()=>n(U).topics,Le,(st,Ge)=>{const rt=O(()=>_(n(Ge).topic)),dt=O(()=>w(n(Ge))),nt=O(()=>s()===n(Ge).topic),ot=O(()=>u().has(n(Ge).topic));var xt=p1(),$t=d(xt);Is($t,()=>n(rt),(ie,fe)=>{fe(ie,{size:12,class:"flex-shrink-0 opacity-50"})});var Nt=m($t,2),dr=d(Nt),R=m(Nt,2),pe=d(R);{var se=ie=>{var fe=f1();c(ie,fe)};C(pe,ie=>{n(Ge).hasChanges&&ie(se)})}var ue=m(pe,2);{var y=ie=>{Xi(ie,{size:9,class:"text-dl-text-dim/40"})};C(ue,ie=>{(n(dt)==="table"||n(dt)==="both")&&ie(y)})}var V=m(ue,2);{var re=ie=>{var fe=v1(),N=d(fe);T(()=>z(N,n(Ge).tableCount)),c(ie,fe)};C(V,ie=>{n(Ge).tableCount>0&&ie(re)})}T(()=>{qe(xt,1,`${n(nt)?"viewer-nav-active-item":""} viewer-nav-active flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors ${n(nt)?"text-dl-text bg-dl-surface-active font-medium":n(ot)?"text-dl-text/70 hover:text-dl-text hover:bg-white/5":"text-dl-text-muted hover:text-dl-text hover:bg-white/5"}`),z(dr,n(Ge).label)}),he("click",xt,()=>{var ie;return(ie=f())==null?void 0:ie(n(Ge).topic,n(U).chapter)}),gn("mouseenter",xt,()=>b(n(Ge).topic)),gn("mouseleave",xt,k),c(st,xt)}),c(De,tt)},te=O(()=>o().has(n(U).chapter));C(_e,De=>{n(te)&&De($e)})}T(()=>{z(H,n(U).chapter),qe(j,1,`ml-auto text-[9px] font-mono ${n(le)===n(U).topics.length&&n(U).topics.length>0?"text-emerald-400/60":"text-dl-text-dim/60"}`),z(K,`${n(le)??""}/${n(U).topics.length??""}`)}),he("click",W,()=>{var De;return(De=p())==null?void 0:De(n(U).chapter)}),c(F,we)}),c(P,$)},ce=P=>{var $=g1();c(P,$)};C(D,P=>{var $;a()?P(M):($=r())!=null&&$.chapters?P(Z,1):P(ce,-1)})}c(t,E),Ar()}Gr(["click"]);const y1="modulepreload",w1=function(t){return"/"+t},kd={},Qi=function(e,r,a){let s=Promise.resolve();if(r&&r.length>0){let i=function(f){return Promise.all(f.map(p=>Promise.resolve(p).then(g=>({status:"fulfilled",value:g}),g=>({status:"rejected",reason:g}))))};document.getElementsByTagName("link");const l=document.querySelector("meta[property=csp-nonce]"),u=(l==null?void 0:l.nonce)||(l==null?void 0:l.getAttribute("nonce"));s=i(r.map(f=>{if(f=w1(f),f in kd)return;kd[f]=!0;const p=f.endsWith(".css"),g=p?'[rel="stylesheet"]':"";if(document.querySelector(`link[href="${f}"]${g}`))return;const x=document.createElement("link");if(x.rel=p?"stylesheet":y1,p||(x.as="script"),x.crossOrigin="",x.href=f,u&&x.setAttribute("nonce",u),document.head.appendChild(x),p)return new Promise((b,k)=>{x.addEventListener("load",b),x.addEventListener("error",()=>k(new Error(`Unable to preload CSS for ${f}`)))})}))}function o(i){const l=new Event("vite:preloadError",{cancelable:!0});if(l.payload=i,window.dispatchEvent(l),!l.defaultPrevented)throw i}return s.then(i=>{for(const l of i||[])l.status==="rejected"&&o(l.reason);return e().catch(o)})},Zi=["#ea4647","#fb923c","#3b82f6","#22c55e","#8b5cf6","#06b6d4","#f59e0b","#ec4899"],Sd={performance:"성과",profitability:"수익성",health:"건전성",cashflow:"현금흐름",governance:"지배구조",risk:"리스크",opportunity:"기회"},k1={A:5,B:4,C:3,D:2,F:0};function S1(t){var f,p;if(!((f=t==null?void 0:t.data)!=null&&f.rows)||!((p=t==null?void 0:t.data)!=null&&p.columns))return null;const{rows:e,columns:r}=t.data,a=t.meta||{},s=r.filter(g=>/^\d{4}/.test(g));if(s.length<2)return null;const o=r[0],i=[],l=["bar","line","line"];return e.slice(0,3).forEach((g,x)=>{const b=g[o]||`항목${x}`,k=s.map(S=>{const _=g[S];return _!=null?Number(_):0});k.some(S=>S!==0)&&i.push({name:b,data:k,color:Zi[x%Zi.length],type:l[x]||"line"})}),i.length===0?null:{chartType:"combo",title:a.title||"재무 추이",series:i,categories:s,options:{unit:a.unit||"백만원"}}}function C1(t,e=""){if(!t)return null;const r=Object.keys(Sd),a=r.map(o=>Sd[o]),s=r.map(o=>{var l;const i=((l=t[o])==null?void 0:l.grade)||t[o]||"F";return k1[i]??0});return{chartType:"radar",title:e?`${e} 투자 인사이트`:"투자 인사이트",series:[{name:e||"등급",data:s,color:Zi[0]}],categories:a,options:{maxValue:5}}}var $1=h("<button> </button>"),M1=h('<div class="flex items-center gap-0.5 overflow-x-auto py-1 scrollbar-thin"></div>');function wu(t,e){Ir(e,!0);let r=Fe(e,"periods",19,()=>[]),a=Fe(e,"selected",3,null),s=Fe(e,"onSelect",3,null);function o(p){return/^\d{4}$/.test(p)||/^\d{4}Q4$/.test(p)}function i(p){const g=p.match(/^(\d{4})(Q([1-4]))?$/);if(!g)return p;const x="'"+g[1].slice(2);return g[3]?`${x}.${g[3]}Q`:x}var l=Se(),u=ae(l);{var f=p=>{var g=M1();Ie(g,21,r,Le,(x,b)=>{var k=$1(),S=d(k);T((_,w)=>{qe(k,1,`flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] font-mono transition-colors
					${_??""}`),lr(k,"title",n(b)),z(S,w)},[()=>a()===n(b)?"bg-dl-primary/20 text-dl-primary-light font-medium":o(n(b))?"text-dl-text-muted hover:text-dl-text hover:bg-white/5":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5",()=>i(n(b))]),he("click",k,()=>{var _;return(_=s())==null?void 0:_(n(b))}),c(x,k)}),c(p,g)};C(u,p=>{r().length>0&&p(f)})}c(t,l),Ar()}Gr(["click"]);var T1=h('<div class="mb-1"><!></div>'),z1=h('<!> <div class="text-[10px] text-dl-text-dim mb-1 font-mono"> </div> <div class="prose-dartlab overflow-x-auto"><!></div>',1),E1=h('<th class="cursor-pointer select-none hover:text-dl-text"> </th>'),I1=h("<td> </td>"),A1=h("<tr></tr>"),L1=h('<button class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"> </button>'),N1=h('<div class="text-[10px] text-dl-text-dim mt-1"> </div>'),P1=h('<div class="overflow-x-auto rounded-lg border border-dl-border/10"><table class="finance-table"><thead><tr></tr></thead><tbody></tbody></table> <!></div> <!>',1),D1=h("<th> </th>"),O1=h("<td> </td>"),R1=h("<tr></tr>"),F1=h('<button class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"> </button>'),j1=h('<div class="text-[10px] text-dl-text-dim mt-1"> </div>'),B1=h('<div class="overflow-x-auto rounded-lg border border-dl-border/10"><table class="structured-table"><thead><tr></tr></thead><tbody></tbody></table> <!></div> <!>',1);function Cd(t,e){Ir(e,!0);let r=Fe(e,"block",3,null),a=Fe(e,"maxRows",3,100),s=Y(null),o=Y(!1),i=Y(null),l=Y("asc");function u(P){n(i)===P?v(l,n(l)==="asc"?"desc":"asc",!0):(v(i,P,!0),v(l,"asc"))}function f(P){return n(i)!==P?"":n(l)==="asc"?" ▲":" ▼"}const p=new Set(["매출액","revenue","영업이익","operating_income","당기순이익","net_income","자산총계","total_assets","부채총계","total_liabilities","자본총계","total_equity","영업활동현금흐름","operating_cash_flow","매출총이익","gross_profit","EBITDA"]);function g(P,$){if(!($!=null&&$.length))return!1;const X=String(P[$[0]]??"").trim();return p.has(X)}function x(P){if(P==null||P===""||P==="-")return P??"";if(typeof P=="number")return Math.abs(P)>=1?P.toLocaleString("ko-KR"):P.toString();const $=String(P).trim();if(/^-?[\d,]+(\.\d+)?$/.test($)){const X=parseFloat($.replace(/,/g,""));if(!isNaN(X))return Math.abs(X)>=1?X.toLocaleString("ko-KR"):X.toString()}return P}function b(P){if(typeof P=="number")return P<0;const $=String(P??"").trim().replace(/,/g,"");return/^-\d/.test($)}function k(P){return typeof P=="number"?!0:typeof P=="string"&&/^-?[\d,]+(\.\d+)?$/.test(P.trim())}function S(P){return(P==null?void 0:P.kind)==="finance"}function _(P){return P!=null&&P.rawMarkdown?Object.keys(P.rawMarkdown):[]}function w(P){const $=_(P);return n(s)&&$.includes(n(s))?n(s):$[0]??null}let E=O(()=>{var X,J;const P=((J=(X=r())==null?void 0:X.data)==null?void 0:J.rows)??[];return n(i)?[...P].sort((me,B)=>{let Te=me[n(i)],F=B[n(i)];const U=typeof Te=="number"?Te:parseFloat(String(Te??"").replace(/,/g,"")),le=typeof F=="number"?F:parseFloat(String(F??"").replace(/,/g,""));return!isNaN(U)&&!isNaN(le)?n(l)==="asc"?U-le:le-U:(Te=String(Te??""),F=String(F??""),n(l)==="asc"?Te.localeCompare(F):F.localeCompare(Te))}):P}),D=O(()=>n(o)?n(E):n(E).slice(0,a()));var M=Se(),Z=ae(M);{var ce=P=>{var $=Se(),X=ae($);{var J=F=>{const U=O(()=>_(r())),le=O(()=>w(r()));var we=Se(),W=ae(we);{var ne=A=>{var G=z1(),q=ae(G);{var L=$e=>{var te=T1(),De=d(te);wu(De,{get periods(){return n(U)},get selected(){return n(le)},onSelect:tt=>{v(s,tt,!0)}}),c($e,te)};C(q,$e=>{n(U).length>1&&$e(L)})}var H=m(q,2),j=d(H),K=m(H,2),_e=d(K);Gn(_e,()=>Va(r().rawMarkdown[n(le)])),T(()=>z(j,n(le))),c(A,G)};C(W,A=>{n(U).length>0&&A(ne)})}c(F,we)},me=F=>{var U=P1(),le=ae(U),we=d(le),W=d(we),ne=d(W);Ie(ne,21,()=>r().data.columns??[],Le,(j,K)=>{var _e=E1(),$e=d(_e);T(te=>z($e,`${n(K)??""}${te??""}`),[()=>f(n(K))]),he("click",_e,()=>u(n(K))),c(j,_e)});var A=m(W);Ie(A,21,()=>n(D),Le,(j,K)=>{const _e=O(()=>g(n(K),r().data.columns));var $e=A1();Ie($e,21,()=>r().data.columns??[],Le,(te,De,tt)=>{const st=O(()=>n(K)[n(De)]),Ge=O(()=>tt>0&&k(n(st)));var rt=I1(),dt=d(rt);T((nt,ot)=>{qe(rt,1,nt),z(dt,ot)},[()=>n(Ge)?b(n(st))?"val-neg":"val-pos":"",()=>n(Ge)?x(n(st)):n(st)??""]),c(te,rt)}),T(()=>qe($e,1,gr(n(_e)?"row-key":""))),c(j,$e)});var G=m(we,2);{var q=j=>{var K=L1(),_e=d(K);T(()=>z(_e,`외 ${r().data.rows.length-a()}행 더 보기`)),he("click",K,()=>{v(o,!0)}),c(j,K)};C(G,j=>{!n(o)&&r().data.rows.length>a()&&j(q)})}var L=m(le,2);{var H=j=>{var K=N1(),_e=d(K);T(()=>z(_e,`단위: ${(r().meta.unit||"")??""} ${r().meta.scale?`(${r().meta.scale})`:""}`)),c(j,K)};C(L,j=>{var K,_e;((K=r().meta)!=null&&K.scale||(_e=r().meta)!=null&&_e.unit)&&j(H)})}c(F,U)},B=O(()=>{var F;return S(r())&&((F=r().data)==null?void 0:F.rows)}),Te=F=>{var U=B1(),le=ae(U),we=d(le),W=d(we),ne=d(W);Ie(ne,21,()=>r().data.columns??[],Le,(j,K,_e)=>{var $e=D1();qe($e,1,`${_e===0?"col-sticky":""} cursor-pointer select-none hover:text-dl-text`);var te=d($e);T(De=>z(te,`${n(K)??""}${De??""}`),[()=>f(n(K))]),he("click",$e,()=>u(n(K))),c(j,$e)});var A=m(W);Ie(A,21,()=>n(D),Le,(j,K)=>{var _e=R1();Ie(_e,21,()=>r().data.columns??[],Le,($e,te,De)=>{const tt=O(()=>n(K)[n(te)]),st=O(()=>De>0&&k(n(tt)));var Ge=O1(),rt=d(Ge);T((dt,nt)=>{qe(Ge,1,`${De===0?"col-sticky":""} ${dt??""}`),z(rt,nt)},[()=>n(st)?b(n(tt))?"val-neg":"val-pos":"",()=>n(st)?x(n(tt)):n(tt)??""]),c($e,Ge)}),c(j,_e)});var G=m(we,2);{var q=j=>{var K=F1(),_e=d(K);T(()=>z(_e,`외 ${r().data.rows.length-a()}행 더 보기`)),he("click",K,()=>{v(o,!0)}),c(j,K)};C(G,j=>{!n(o)&&r().data.rows.length>a()&&j(q)})}var L=m(le,2);{var H=j=>{var K=j1(),_e=d(K);T(()=>z(_e,`단위: ${(r().meta.unit||"")??""} ${r().meta.scale?`(${r().meta.scale})`:""}`)),c(j,K)};C(L,j=>{var K;(K=r().meta)!=null&&K.scale&&j(H)})}c(F,U)};C(X,F=>{var U;r().kind==="raw_markdown"&&r().rawMarkdown?F(J):n(B)?F(me,1):(U=r().data)!=null&&U.rows&&F(Te,2)})}c(P,$)};C(Z,P=>{r()&&P(ce)})}c(t,M),Ar()}Gr(["click"]);var V1=h('<span class="flex items-center gap-1"><!> <span class="text-dl-accent"> </span> <span class="text-dl-text-dim/60"> </span></span>'),U1=h('<span class="flex items-center gap-1"><!> <span>변경 없음</span></span>'),H1=h('<span class="flex items-center gap-1 ml-auto"><span class="font-mono"> </span> <!> <span class="font-mono"> </span></span>'),q1=h('<div class="text-dl-success/80 truncate"> </div>'),K1=h('<div class="text-dl-primary-light/70 truncate"> </div>'),W1=h('<div class="text-[11px] leading-relaxed"><!> <!></div>'),G1=h('<div class="flex flex-col gap-1.5 p-2.5 rounded-lg bg-dl-surface-card border border-dl-border/20"><div class="flex items-center gap-3 text-[11px] text-dl-text-dim"><span class="font-mono"> </span> <!> <!></div> <!></div>');function Y1(t,e){Ir(e,!0);let r=Fe(e,"summary",3,null);var a=Se(),s=ae(a);{var o=i=>{var l=G1(),u=d(l),f=d(u),p=d(f),g=m(f,2);{var x=E=>{var D=V1(),M=d(D);No(M,{size:11,class:"text-dl-accent"});var Z=m(M,2),ce=d(Z),P=m(Z,2),$=d(P);T(X=>{z(ce,`변경 ${r().changedCount??""}회`),z($,`(${X??""}%)`)},[()=>(r().changeRate*100).toFixed(1)]),c(E,D)},b=E=>{var D=U1(),M=d(D);xu(M,{size:11}),c(E,D)};C(g,E=>{r().changedCount>0?E(x):E(b,-1)})}var k=m(g,2);{var S=E=>{var D=H1(),M=d(D),Z=d(M),ce=m(M,2);Xh(ce,{size:10});var P=m(ce,2),$=d(P);T(()=>{z(Z,r().latestFrom),z($,r().latestTo)}),c(E,D)};C(k,E=>{r().latestFrom&&r().latestTo&&E(S)})}var _=m(u,2);{var w=E=>{var D=W1(),M=d(D);Ie(M,17,()=>r().added.slice(0,2),Le,(ce,P)=>{var $=q1(),X=d($);T(()=>z(X,`+ ${n(P)??""}`)),c(ce,$)});var Z=m(M,2);Ie(Z,17,()=>r().removed.slice(0,2),Le,(ce,P)=>{var $=K1(),X=d($);T(()=>z(X,`- ${n(P)??""}`)),c(ce,$)}),c(E,D)};C(_,E=>{var D,M;(((D=r().added)==null?void 0:D.length)>0||((M=r().removed)==null?void 0:M.length)>0)&&E(w)})}T(()=>z(p,`${r().totalPeriods??""} periods`)),c(i,l)};C(s,i=>{r()&&i(o)})}c(t,a),Ar()}var J1=h("<option> </option>"),X1=h("<option> </option>"),Q1=h('<button class="p-1 ml-1 text-dl-text-dim hover:text-dl-text"><!></button>'),Z1=h('<span class="flex items-center gap-1 text-emerald-400"><!> <span> </span></span>'),e0=h('<span class="flex items-center gap-1 text-red-400"><!> <span> </span></span>'),t0=h('<span class="flex items-center gap-1 text-dl-text-dim"><!> <span> </span></span>'),r0=h('<div class="flex items-center gap-3 px-4 py-1.5 border-b border-dl-border/10 text-[10px]"><!> <!> <!></div>'),n0=h('<div class="flex items-center justify-center py-8 gap-2"><!> <span class="text-[12px] text-dl-text-dim">비교 로딩 중...</span></div>'),a0=h('<div class="text-[12px] text-red-400 py-4"> </div>'),s0=h('<mark class="bg-emerald-400/25 text-emerald-300 rounded-sm px-[1px]"> </mark>'),o0=h('<span class="text-dl-text/85"> </span>'),i0=h('<span class="text-dl-text/85"> </span>'),l0=h('<div class="pl-3 py-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-[13px] leading-[1.8] rounded-r"><span class="text-emerald-500/60 text-[10px] mr-1">+</span> <!></div>'),d0=h('<mark class="bg-red-400/25 text-red-300 line-through decoration-red-400/40 rounded-sm px-[1px]"> </mark>'),c0=h('<span class="text-dl-text/40"> </span>'),u0=h('<span class="text-dl-text/40 line-through decoration-red-400/30"> </span>'),f0=h('<div class="pl-3 py-1 border-l-2 border-red-400 bg-red-500/5 text-[13px] leading-[1.8] rounded-r"><span class="text-red-400/60 text-[10px] mr-1">-</span> <!></div>'),v0=h('<p class="text-[13px] leading-[1.8] text-dl-text/70 py-0.5"> </p>'),p0=h('<div class="space-y-0.5"></div>'),h0=h('<div class="text-[12px] text-dl-text-dim text-center py-4">비교할 기간을 선택하세요</div>'),m0=h('<div class="rounded-xl border border-dl-border/20 bg-dl-surface-card overflow-hidden"><div class="flex items-center gap-2 px-4 py-2 border-b border-dl-border/15 bg-dl-bg-darker/50"><!> <span class="text-[12px] font-semibold text-dl-text">기간 비교</span> <div class="flex items-center gap-1 ml-auto"><select class="px-2 py-0.5 rounded bg-dl-bg-darker border border-dl-border/20 text-[11px] text-dl-text outline-none"></select> <span class="text-[11px] text-dl-text-dim">→</span> <select class="px-2 py-0.5 rounded bg-dl-bg-darker border border-dl-border/20 text-[11px] text-dl-text outline-none"></select> <!></div></div> <!> <div class="max-h-[60vh] overflow-y-auto px-4 py-3"><!></div></div>');function x0(t,e){Ir(e,!0);let r=Fe(e,"stockCode",3,null),a=Fe(e,"topic",3,null),s=Fe(e,"periods",19,()=>[]),o=Fe(e,"onClose",3,null),i=Y(null),l=Y(null),u=Y(null),f=Y(!1),p=Y(null);_r(()=>{s().length>=2&&!n(i)&&!n(l)&&(v(l,s()[0],!0),v(i,s()[1],!0))});async function g(){if(!(!r()||!a()||!n(i)||!n(l))){v(f,!0),v(p,null);try{const F=await Vc(r(),a(),n(i),n(l));v(u,F,!0)}catch(F){v(p,F.message,!0)}v(f,!1)}}_r(()=>{n(i)&&n(l)&&n(i)!==n(l)&&g()});function x(F){if(!F)return"";const U=String(F).match(/^(\d{4})(Q([1-4]))?$/);return U?U[3]?`'${U[1].slice(2)}.${U[3]}Q`:`'${U[1].slice(2)}`:F}let b=O(()=>{var we;if(!((we=n(u))!=null&&we.diff))return{added:0,removed:0,same:0};let F=0,U=0,le=0;for(const W of n(u).diff)W.kind==="added"?F++:W.kind==="removed"?U++:le++;return{added:F,removed:U,same:le}});var k=m0(),S=d(k),_=d(S);fu(_,{size:14,class:"text-dl-accent"});var w=m(_,4),E=d(w);Ie(E,21,s,Le,(F,U)=>{var le=J1(),we=d(le),W={};T(ne=>{le.disabled=n(U)===n(l),z(we,ne),W!==(W=n(U))&&(le.value=(le.__value=n(U))??"")},[()=>x(n(U))]),c(F,le)});var D=m(E,4);Ie(D,21,s,Le,(F,U)=>{var le=X1(),we=d(le),W={};T(ne=>{le.disabled=n(U)===n(i),z(we,ne),W!==(W=n(U))&&(le.value=(le.__value=n(U))??"")},[()=>x(n(U))]),c(F,le)});var M=m(D,2);{var Z=F=>{var U=Q1(),le=d(U);Ba(le,{size:12}),he("click",U,function(...we){var W;(W=o())==null||W.apply(this,we)}),c(F,U)};C(M,F=>{o()&&F(Z)})}var ce=m(S,2);{var P=F=>{var U=r0(),le=d(U);{var we=q=>{var L=Z1(),H=d(L);Yi(H,{size:10});var j=m(H,2),K=d(j);T(()=>z(K,`추가 ${n(b).added??""}`)),c(q,L)};C(le,q=>{n(b).added>0&&q(we)})}var W=m(le,2);{var ne=q=>{var L=e0(),H=d(L);xu(H,{size:10});var j=m(H,2),K=d(j);T(()=>z(K,`삭제 ${n(b).removed??""}`)),c(q,L)};C(W,q=>{n(b).removed>0&&q(ne)})}var A=m(W,2);{var G=q=>{var L=t0(),H=d(L);tm(H,{size:10});var j=m(H,2),K=d(j);T(()=>z(K,`유지 ${n(b).same??""}`)),c(q,L)};C(A,q=>{n(b).same>0&&q(G)})}c(F,U)};C(ce,F=>{n(u)&&!n(f)&&F(P)})}var $=m(ce,2),X=d($);{var J=F=>{var U=n0(),le=d(U);Kr(le,{size:14,class:"animate-spin text-dl-text-dim"}),c(F,U)},me=F=>{var U=a0(),le=d(U);T(()=>z(le,n(p))),c(F,U)},B=F=>{var U=p0();Ie(U,21,()=>n(u).diff,Le,(le,we)=>{var W=Se(),ne=ae(W);{var A=L=>{var H=l0(),j=m(d(H),2);{var K=$e=>{var te=Se(),De=ae(te);Ie(De,17,()=>n(we).parts,Le,(tt,st)=>{var Ge=Se(),rt=ae(Ge);{var dt=ot=>{var xt=s0(),$t=d(xt);T(()=>z($t,n(st).text)),c(ot,xt)},nt=ot=>{var xt=o0(),$t=d(xt);T(()=>z($t,n(st).text)),c(ot,xt)};C(rt,ot=>{n(st).kind==="insert"?ot(dt):n(st).kind==="equal"&&ot(nt,1)})}c(tt,Ge)}),c($e,te)},_e=$e=>{var te=i0(),De=d(te);T(()=>z(De,n(we).text)),c($e,te)};C(j,$e=>{n(we).parts?$e(K):$e(_e,-1)})}c(L,H)},G=L=>{var H=f0(),j=m(d(H),2);{var K=$e=>{var te=Se(),De=ae(te);Ie(De,17,()=>n(we).parts,Le,(tt,st)=>{var Ge=Se(),rt=ae(Ge);{var dt=ot=>{var xt=d0(),$t=d(xt);T(()=>z($t,n(st).text)),c(ot,xt)},nt=ot=>{var xt=c0(),$t=d(xt);T(()=>z($t,n(st).text)),c(ot,xt)};C(rt,ot=>{n(st).kind==="delete"?ot(dt):n(st).kind==="equal"&&ot(nt,1)})}c(tt,Ge)}),c($e,te)},_e=$e=>{var te=u0(),De=d(te);T(()=>z(De,n(we).text)),c($e,te)};C(j,$e=>{n(we).parts?$e(K):$e(_e,-1)})}c(L,H)},q=L=>{var H=v0(),j=d(H);T(()=>z(j,n(we).text)),c(L,H)};C(ne,L=>{n(we).kind==="added"?L(A):n(we).kind==="removed"?L(G,1):L(q,-1)})}c(le,W)}),c(F,U)},Te=F=>{var U=h0();c(F,U)};C(X,F=>{var U;n(f)?F(J):n(p)?F(me,1):(U=n(u))!=null&&U.diff?F(B,2):F(Te,-1)})}Xl(E,()=>n(i),F=>v(i,F)),Xl(D,()=>n(l),F=>v(l,F)),c(t,k),Ar()}Gr(["click"]);var g0=h("<button><!></button>"),_0=h("<button><!> <span>기간 비교</span></button>"),b0=h("<button><!> <span>AI 요약</span></button>"),y0=h('<div class="text-red-400/80"> </div>'),w0=h('<span class="inline-block w-1.5 h-3 bg-dl-accent/60 animate-pulse ml-0.5"></span>'),k0=h('<div class="whitespace-pre-wrap"> <!></div>'),S0=h('<div class="px-3 py-2 rounded-lg bg-dl-accent/5 border border-dl-accent/15 text-[12px] text-dl-text-muted leading-relaxed"><!></div>'),C0=h('<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim"> </span>'),$0=h('<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim"> </span>'),M0=h('<span class="px-2 py-0.5 rounded-full border border-emerald-500/20 bg-emerald-500/8 text-emerald-400/80"> </span>'),T0=h('<span class="px-2 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/8 text-blue-400/80"> </span>'),z0=h("<div> </div>"),E0=h('<h4 class="text-[14px] font-semibold text-dl-text"> </h4>'),I0=h('<div class="mb-2 mt-2"></div>'),A0=h('<span class="text-[10px] text-dl-text-dim font-mono"> </span>'),L0=h('<span class="text-[10px] text-dl-text-dim"> </span>'),N0=h('<span class="ml-0.5 text-emerald-400/50">*</span>'),P0=h("<button> <!></button>"),D0=h('<div class="flex flex-wrap gap-1 mb-2"></div>'),O0=h('<div class="text-blue-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-blue-400/60 mt-1.5 shrink-0"></span> </div>'),R0=h('<div class="text-emerald-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-emerald-400/50 mt-1.5 shrink-0"></span> </div>'),F0=h('<div class="text-dl-text-dim/50 flex gap-1"><span class="w-1 h-1 rounded-full bg-red-400/40 mt-1.5 shrink-0"></span> </div>'),j0=h('<div class="mb-3 px-3 py-2 rounded-lg border border-dl-border/15 bg-dl-surface-card/50 text-[11px] space-y-0.5 max-w-2xl"><div class="text-dl-text-dim font-medium"> </div> <!> <!> <!></div>'),B0=h('<div class="mb-2 px-3 py-1.5 rounded-lg border border-dl-border/15 bg-dl-surface-card/30 text-[11px] text-dl-text-dim">이전 기간과 동일 — 변경 없음</div>'),V0=h('<mark class="bg-emerald-400/25 text-emerald-300 rounded-sm px-[1px]"> </mark>'),U0=h('<span class="text-dl-text/85"> </span>'),H0=h('<span class="text-dl-text/85"> </span>'),q0=h('<div class="pl-3 py-1 mb-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-[14px] leading-[1.85] rounded-r"><span class="text-emerald-500/50 text-[10px] mr-1">+</span> <!></div>'),K0=h('<mark class="bg-red-400/25 text-red-300 line-through decoration-red-400/40 rounded-sm px-[1px]"> </mark>'),W0=h('<span class="text-dl-text/40"> </span>'),G0=h('<span class="text-dl-text/40 line-through decoration-red-400/30"> </span>'),Y0=h('<div class="pl-3 py-1 mb-1 border-l-2 border-red-400 bg-red-500/5 text-[14px] leading-[1.85] rounded-r"><span class="text-red-400/60 text-[10px] mr-1">-</span> <!></div>'),J0=h('<p class="vw-para"> </p>'),X0=h('<div class="text-[10px] text-dl-text-dim/40 mb-1">글자 단위 비교 로딩 중...</div>'),Q0=h('<p class="vw-para"> </p>'),Z0=h('<div class="pl-3 py-1 mb-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-dl-text/85 text-[14px] leading-[1.85] rounded-r"><span class="text-emerald-500/50 text-[10px] mr-1">+</span> </div>'),e_=h('<div class="pl-3 py-1 mb-1 border-l-2 border-red-400 bg-red-500/5 text-dl-text/50 text-[14px] leading-[1.85] rounded-r line-through decoration-red-400/30"><span class="text-red-400/50 text-[10px] mr-1">-</span> </div>'),t_=h("<!> <!>",1),r_=h('<div class="flex flex-wrap items-center gap-1.5 mb-2"><span> </span> <!> <!></div> <!> <!> <!>  <div class="disclosure-text max-w-3xl"><!></div>',1),n_=h("<div><!> <!></div>"),a_=h("<button><!></button>"),s_=h('<button class="p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="테이블 복사"><!></button>'),o_=h('<div class="group relative"><div class="absolute top-1 right-1 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"><!> <!></div> <!></div>'),i_=h('<div class="h-16 flex items-center justify-center"><div class="text-[10px] text-dl-text-dim/40"> </div></div>'),l_=h('<div class="flex flex-wrap gap-1.5 text-[10px] max-w-4xl"><!> <!> <!> <!></div> <!> <!>',1),d_=h('<h3 class="text-[14px] font-semibold text-dl-text mt-4 mb-1"> </h3>'),c_=h('<div class="mb-1 opacity-0 group-hover:opacity-100 transition-opacity"><!></div>'),u_=h('<!> <div class="text-[10px] text-dl-text-dim mb-1 font-mono"> </div> <div class="disclosure-text"><!></div>',1),f_=h('<div class="group"><!></div>'),v_=h("<button><!></button>"),p_=h('<button class="p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="테이블 복사"><!></button>'),h_=h('<div class="group relative"><div class="absolute top-1 right-1 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"><!> <!></div> <!></div>'),m_=h('<div class="text-center py-12 text-[13px] text-dl-text-dim">이 topic에 표시할 데이터가 없습니다</div>'),x_=h('<div class="space-y-4"><div class="flex items-center gap-2"><h2 class="text-[16px] font-semibold text-dl-text flex-1"> </h2> <!> <!> <!></div> <!> <!> <!> <!> <!></div>'),g_=h('<button class="ask-ai-float"><span class="flex items-center gap-1"><!> AI에게 물어보기</span></button>'),__=h("<!> <!>",1);function b_(t,e){Ir(e,!0);let r=Fe(e,"topicData",3,null),a=Fe(e,"diffSummary",3,null),s=Fe(e,"viewer",3,null),o=Fe(e,"onAskAI",3,null),i=Fe(e,"searchHighlight",3,null),l=Y(Ut(new Map)),u=Y(Ut(new Map)),f=Y(null),p=Y(Ut(new Map)),g=Y(8),x=Y(null);_r(()=>{var y;(y=r())!=null&&y.topic&&v(g,8)}),_r(()=>{if(!n(x))return;const y=new IntersectionObserver(V=>{var re,ie,fe,N,ee,Ce,ve;(re=V[0])!=null&&re.isIntersecting&&v(g,Math.min(n(g)+10,((N=(fe=(ie=r())==null?void 0:ie.textDocument)==null?void 0:fe.entries)==null?void 0:N.length)||((ve=(Ce=(ee=r())==null?void 0:ee.textDocument)==null?void 0:Ce.sections)==null?void 0:ve.length)||999),!0)},{rootMargin:"200px"});return y.observe(n(x)),()=>y.disconnect()});let b=Y(Ut({show:!1,x:0,y:0,text:""})),k=Y(!1),S=Y(""),_=Y(null),w=Y(null);_r(()=>{var y,V,re;if((y=r())!=null&&y.topic){v(k,!1),v(_,null);const ie=(re=(V=s())==null?void 0:V.getTopicSummary)==null?void 0:re.call(V,r().topic);v(S,ie||"",!0),n(w)&&(n(w).abort(),v(w,null))}});function E(){var re,ie;if(!((re=s())!=null&&re.stockCode)||!((ie=r())!=null&&ie.topic))return;v(k,!0),v(S,""),v(_,null);const y=typeof localStorage<"u"?localStorage.getItem("dartlab-provider"):null,V=typeof localStorage<"u"?localStorage.getItem("dartlab-model"):null;v(w,Ip(s().stockCode,r().topic,{provider:y||void 0,model:V||void 0,onContext(){},onChunk(fe){v(S,n(S)+fe)},onDone(){var fe,N;v(k,!1),v(w,null),n(S)&&((N=(fe=s())==null?void 0:fe.setTopicSummary)==null||N.call(fe,r().topic,n(S)))},onError(fe){v(k,!1),v(w,null),v(_,fe,!0)}}),!0)}let D=O(()=>{var y,V,re;return((re=(y=s())==null?void 0:y.isBookmarked)==null?void 0:re.call(y,(V=r())==null?void 0:V.topic))??!1}),M=Y(Ut(new Map)),Z=Y(Ut(new Set));async function ce(y,V,re){var N,ee;if(!((N=s())!=null&&N.stockCode)||!((ee=r())!=null&&ee.topic)||!re||!V)return;const ie=`${y}:${V}`;if(n(M).has(ie)||n(Z).has(ie))return;v(Z,new Set([...n(Z),ie]),!0);try{const Ce=await Vc(s().stockCode,r().topic,re,V),ve=new Map(n(M));ve.set(ie,Ce),v(M,ve,!0)}catch{}const fe=new Set(n(Z));fe.delete(ie),v(Z,fe,!0)}let P=Y(!1);_r(()=>{var y;(y=r())!=null&&y.topic&&(v(P,!1),v(M,new Map,!0),v(Z,new Set,!0))}),_r(()=>{var V,re,ie,fe,N,ee,Ce,ve,ke,Ne;const y=(re=(V=r())==null?void 0:V.textDocument)==null?void 0:re.sections;if(!(!y||!((ie=s())!=null&&ie.stockCode)||!((fe=r())!=null&&fe.topic)))for(const de of y){if(de.status!=="updated"||!de.timeline||de.timeline.length<2)continue;const ze=((ee=(N=de.timeline[0])==null?void 0:N.period)==null?void 0:ee.label)||Te((Ce=de.timeline[0])==null?void 0:Ce.period),Re=((ke=(ve=de.timeline[1])==null?void 0:ve.period)==null?void 0:ke.label)||Te((Ne=de.timeline[1])==null?void 0:Ne.period);ze&&Re&&ce(de.id,ze,Re)}});let $=O(()=>{var V,re,ie,fe,N,ee;if(!((ie=(re=(V=r())==null?void 0:V.textDocument)==null?void 0:re.sections)!=null&&ie.length))return[];const y=new Set;for(const Ce of r().textDocument.sections)if(Ce.timeline)for(const ve of Ce.timeline){const ke=((fe=ve.period)==null?void 0:fe.label)||((N=ve.period)!=null&&N.year&&((ee=ve.period)!=null&&ee.quarter)?`${ve.period.year}Q${ve.period.quarter}`:null);ke&&y.add(ke)}return[...y].sort().reverse()}),X=O(()=>{var y,V,re;return((re=(V=(y=r())==null?void 0:y.textDocument)==null?void 0:V.sections)==null?void 0:re.length)>0}),J=O(()=>{var y,V;return new Map((((V=(y=r())==null?void 0:y.textDocument)==null?void 0:V.sections)??[]).map(re=>[re.id,re]))}),me=O(()=>{var y;return new Map((((y=r())==null?void 0:y.blocks)??[]).map(V=>[V.block,V]))}),B=O(()=>{var y,V;return((V=(y=r())==null?void 0:y.textDocument)==null?void 0:V.entries)??[]});function Te(y){if(!y)return"";if(typeof y=="string"){const V=y.match(/^(\d{4})(Q([1-4]))?$/);return V?V[3]?`${V[1]}Q${V[3]}`:V[1]:y}return y.kind==="annual"?`${y.year}`:y.year&&y.quarter?`${y.year}Q${y.quarter}`:y.label||""}function F(y){return y==="updated"?"수정됨":y==="new"?"신규":y==="stale"?"과거유지":"유지"}function U(y){return y==="updated"?"bg-emerald-500/10 text-emerald-400/80 border-emerald-500/20":y==="new"?"bg-blue-500/10 text-blue-400/80 border-blue-500/20":y==="stale"?"bg-amber-500/10 text-amber-400/80 border-amber-500/20":"bg-dl-border/10 text-dl-text-dim border-dl-border/20"}function le(y){var re;const V=n(u).get(y.id);return V&&((re=y.views)!=null&&re[V])?y.views[V]:y.latest||null}function we(y,V){var ie,fe;const re=n(u).get(y.id);return re?re===V:((fe=(ie=y.latest)==null?void 0:ie.period)==null?void 0:fe.label)===V}function W(y){return n(u).has(y.id)}function ne(y,V,re){var fe;const ie=new Map(n(u));if(ie.get(y)===V)ie.delete(y);else if(ie.set(y,V),((fe=re==null?void 0:re.timeline)==null?void 0:fe.length)>1){const N=re.timeline.map(ve=>{var ke;return((ke=ve.period)==null?void 0:ke.label)||Te(ve.period)}),ee=N.indexOf(V),Ce=ee>=0&&ee<N.length-1?N[ee+1]:null;Ce&&ce(y,V,Ce)}v(u,ie,!0)}function A(y){return y.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function G(y){return String(y||"").replace(/\u00a0/g," ").replace(/\s+/g," ").trim()}function q(y){return!y||y.length>88?!1:/^\[.+\]$/.test(y)||/^【.+】$/.test(y)||/^[IVX]+\.\s/.test(y)||/^\d+\.\s/.test(y)||/^[가-힣]\.\s/.test(y)||/^\(\d+\)\s/.test(y)||/^\([가-힣]\)\s/.test(y)||/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(y)}function L(y){return/^[가나다라마바사아자차카타파하]\.\s/.test(y)?1:/^\d+\.\s/.test(y)?2:/^\(\d+\)\s/.test(y)||/^\([가-힣]\)\s/.test(y)?3:/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(y)?4:/^\[.+\]$/.test(y)||/^【.+】$/.test(y)?1:2}function H(y){if(!y)return"";if(/^\|.+\|$/m.test(y))return Va(y);const V=y.split(`
`);let re="",ie=[];function fe(){ie.length!==0&&(re+=`<p class="vw-para">${A(ie.join(" "))}</p>`,ie=[])}for(const N of V){const ee=G(N);if(!ee){fe();continue}if(q(ee)){fe();const Ce=L(ee);re+=`<div class="ko-h${Ce}">${A(ee)}</div>`}else ie.push(ee)}return fe(),re}function j(y){var re;if(!((re=y==null?void 0:y.diff)!=null&&re.length))return null;const V=[];for(const ie of y.diff)for(const fe of ie.paragraphs||[])V.push({kind:ie.kind,text:G(fe)});return V}function K(y){return n(l).get(y)??null}function _e(y,V){const re=new Map(n(l));re.set(y,V),v(l,re,!0)}function $e(y,V){var re,ie;return(ie=(re=y==null?void 0:y.data)==null?void 0:re.rows)!=null&&ie[0]?y.data.rows[0][V]??null:null}function te(y){var re,ie,fe;if(!((ie=(re=y==null?void 0:y.data)==null?void 0:re.rows)!=null&&ie[0]))return null;const V=y.data.rows[0];for(const N of((fe=y.meta)==null?void 0:fe.periods)??[])if(V[N])return{period:N,text:V[N]};return null}function De(y){var re,ie,fe;if(!((ie=(re=y==null?void 0:y.data)==null?void 0:re.rows)!=null&&ie[0]))return[];const V=y.data.rows[0];return(((fe=y.meta)==null?void 0:fe.periods)??[]).filter(N=>V[N]!=null)}function tt(y){return y.kind==="text"}function st(y){return y.kind==="finance"||y.kind==="structured"||y.kind==="report"||y.kind==="raw_markdown"}function Ge(y){var V,re,ie,fe;return y.kind==="finance"&&((re=(V=y.data)==null?void 0:V.rows)==null?void 0:re.length)>0&&((fe=(ie=y.data)==null?void 0:ie.columns)==null?void 0:fe.length)>2}function rt(y){return S1(y)}function dt(y){const V=new Map(n(p));V.set(y,!V.get(y)),v(p,V,!0)}function nt(y,V){var fe,N;if(!((N=(fe=y==null?void 0:y.data)==null?void 0:fe.rows)!=null&&N.length))return;const re=y.data.columns||[],ie=[re.join("	")];for(const ee of y.data.rows)ie.push(re.map(Ce=>ee[Ce]??"").join("	"));navigator.clipboard.writeText(ie.join(`
`)).then(()=>{v(f,V,!0),setTimeout(()=>{v(f,null)},2e3)})}function ot(y){if(!o())return;const V=window.getSelection(),re=V==null?void 0:V.toString().trim();if(!re||re.length<5){v(b,{show:!1,x:0,y:0,text:""},!0);return}const fe=V.getRangeAt(0).getBoundingClientRect();v(b,{show:!0,x:fe.left+fe.width/2,y:fe.top-8,text:re.slice(0,500)},!0)}function xt(){n(b).text&&o()&&o()(n(b).text),v(b,{show:!1,x:0,y:0,text:""},!0)}function $t(){n(b).show&&v(b,{show:!1,x:0,y:0,text:""},!0)}function Nt(y){if(!i()||!y)return y;const V=i().replace(/[.*+?^${}()|[\]\\]/g,"\\$&"),re=new RegExp(`(${V})`,"gi");return y.replace(re,'<mark class="bg-amber-400/30 text-dl-text rounded-sm px-0.5">$1</mark>')}_r(()=>{var y;i()&&((y=r())!=null&&y.topic)&&requestAnimationFrame(()=>{const V=document.querySelector(".disclosure-text mark");V&&V.scrollIntoView({block:"center",behavior:"smooth"})})});var dr=__();gn("click",ic,$t);var R=ae(dr);{var pe=y=>{var V=x_(),re=d(V),ie=d(re),fe=d(ie),N=m(ie,2);{var ee=Ae=>{var Ee=g0(),wt=d(Ee);{let Pt=O(()=>n(D)?"currentColor":"none");Ji(wt,{size:14,get fill(){return n(Pt)}})}T(()=>{qe(Ee,1,`p-1 rounded transition-colors ${n(D)?"text-amber-400":"text-dl-text-dim/30 hover:text-amber-400/60"}`),lr(Ee,"title",n(D)?"북마크 해제":"북마크 추가")}),he("click",Ee,()=>s().toggleBookmark(r().topic)),c(Ae,Ee)};C(N,Ae=>{s()&&Ae(ee)})}var Ce=m(N,2);{var ve=Ae=>{var Ee=_0(),wt=d(Ee);fu(wt,{size:10}),T(()=>qe(Ee,1,`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors border
						${n(P)?"border-dl-accent/30 bg-dl-accent/10 text-dl-accent-light":"border-dl-border/20 text-dl-text-dim hover:text-dl-text hover:bg-white/5"}`)),he("click",Ee,()=>{v(P,!n(P))}),c(Ae,Ee)};C(Ce,Ae=>{n($).length>=2&&Ae(ve)})}var ke=m(Ce,2);{var Ne=Ae=>{var Ee=b0(),wt=d(Ee);{var Pt=At=>{Kr(At,{size:10,class:"animate-spin"})},Ye=At=>{_u(At,{size:10})};C(wt,At=>{n(k)?At(Pt):At(Ye,-1)})}T(()=>{qe(Ee,1,`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors border
						${n(k)?"border-dl-accent/30 bg-dl-accent/10 text-dl-accent-light":"border-dl-border/20 text-dl-text-dim hover:text-dl-text hover:bg-white/5"}`),Ee.disabled=n(k)}),he("click",Ee,E),c(Ae,Ee)};C(ke,Ae=>{var Ee;(Ee=s())!=null&&Ee.stockCode&&Ae(Ne)})}var de=m(re,2);{var ze=Ae=>{var Ee=S0(),wt=d(Ee);{var Pt=At=>{var Ht=y0(),Ct=d(Ht);T(()=>z(Ct,n(_))),c(At,Ht)},Ye=At=>{var Ht=k0(),Ct=d(Ht),Mt=m(Ct);{var ct=rr=>{var Tr=w0();c(rr,Tr)};C(Mt,rr=>{n(k)&&rr(ct)})}T(()=>z(Ct,n(S))),c(At,Ht)};C(wt,At=>{n(_)?At(Pt):At(Ye,-1)})}c(Ae,Ee)};C(de,Ae=>{(n(S)||n(k)||n(_))&&Ae(ze)})}var Re=m(de,2);Y1(Re,{get summary(){return a()}});var He=m(Re,2);{var be=Ae=>{x0(Ae,{get stockCode(){return s().stockCode},get topic(){return r().topic},get periods(){return n($)},onClose:()=>{v(P,!1)}})};C(He,Ae=>{var Ee;n(P)&&((Ee=s())!=null&&Ee.stockCode)&&Ae(be)})}var et=m(He,2);{var St=Ae=>{const Ee=O(()=>r().textDocument);var wt=l_(),Pt=ae(wt),Ye=d(Pt);{var At=_t=>{var qt=C0(),Tt=d(qt);T(Dt=>z(Tt,`최신 ${Dt??""}`),[()=>Te(n(Ee).latestPeriod)]),c(_t,qt)};C(Ye,_t=>{n(Ee).latestPeriod&&_t(At)})}var Ht=m(Ye,2);{var Ct=_t=>{var qt=$0(),Tt=d(qt);T(()=>z(Tt,`${n(Ee).sectionCount??""}개 섹션`)),c(_t,qt)};C(Ht,_t=>{n(Ee).sectionCount&&_t(Ct)})}var Mt=m(Ht,2);{var ct=_t=>{var qt=M0(),Tt=d(qt);T(()=>z(Tt,`${n(Ee).updatedCount??""}개 수정`)),c(_t,qt)};C(Mt,_t=>{n(Ee).updatedCount>0&&_t(ct)})}var rr=m(Mt,2);{var Tr=_t=>{var qt=T0(),Tt=d(qt);T(()=>z(Tt,`${n(Ee).newCount??""}개 신규`)),c(_t,qt)};C(rr,_t=>{n(Ee).newCount>0&&_t(Tr)})}var kr=m(Pt,2);Ie(kr,17,()=>n(B).slice(0,n(g)),_t=>_t.order,(_t,qt)=>{var Tt=Se(),Dt=ae(Tt);{var cr=bt=>{const Ve=O(()=>n(J).get(n(qt).sectionId));var nr=Se(),Cr=ae(nr);{var it=Pe=>{const Qe=O(()=>le(n(Ve))),ut=O(()=>W(n(Ve))),Ot=O(()=>j(n(Qe))),zt=O(()=>n(Ot)&&n(Ot).length>0),gt=O(()=>{var er,mr,pr;return`${n(Ve).id}:${n(u).get(n(Ve).id)||((pr=(mr=(er=n(Ve).timeline)==null?void 0:er[0])==null?void 0:mr.period)==null?void 0:pr.label)||""}`}),yt=O(()=>n(M).get(n(gt))),Bt=O(()=>n(Z).has(n(gt))),Gt=O(()=>{var er;return(n(zt)||((er=n(yt))==null?void 0:er.diff))&&(n(ut)||n(Ve).status==="updated")}),Qt=O(()=>n(ut)&&!n(zt)&&n(Ve).periodCount>1);var br=n_(),Rr=d(br);{var $r=er=>{var mr=I0();Ie(mr,21,()=>n(Ve).headingPath,Le,(pr,bn)=>{const sn=O(()=>{var Ke;return(Ke=n(bn).text)==null?void 0:Ke.trim()});var In=Se(),I=ae(In);{var ge=Ke=>{const Me=O(()=>n(bn).level||L(n(sn)));var ye=Se(),Oe=ae(ye);{var Je=It=>{var Yt=z0(),Kt=d(Yt);T(Wt=>{qe(Yt,1,`ko-h${Wt??""}`),z(Kt,n(sn))},[()=>n(Me)||L(n(sn))]),c(It,Yt)},ft=O(()=>n(Me)>0||q(n(sn))),vt=It=>{var Yt=E0(),Kt=d(Yt);T(()=>z(Kt,n(sn))),c(It,Yt)};C(Oe,It=>{n(ft)?It(Je):It(vt,-1)})}c(Ke,ye)};C(I,Ke=>{n(sn)&&Ke(ge)})}c(pr,In)}),c(er,mr)};C(Rr,er=>{var mr;((mr=n(Ve).headingPath)==null?void 0:mr.length)>0&&er($r)})}var sr=m(Rr,2);{var vr=er=>{},Hr=er=>{var mr=r_(),pr=ae(mr),bn=d(pr),sn=d(bn),In=m(bn,2);{var I=kt=>{var Q=A0(),xe=d(Q);T(()=>z(xe,n(Ve).latestChange)),c(kt,Q)};C(In,kt=>{n(Ve).latestChange&&kt(I)})}var ge=m(In,2);{var Ke=kt=>{var Q=L0(),xe=d(Q);T(()=>z(xe,`${n(Ve).periodCount??""}기간`)),c(kt,Q)};C(ge,kt=>{n(Ve).periodCount>1&&kt(Ke)})}var Me=m(pr,2);{var ye=kt=>{var Q=D0();Ie(Q,21,()=>n(Ve).timeline,Le,(xe,je,Ue,Ze)=>{const Ft=O(()=>{var tr;return((tr=n(je).period)==null?void 0:tr.label)||Te(n(je).period)});var yr=P0(),or=d(yr),Lr=m(or);{var ar=tr=>{var hr=N0();c(tr,hr)};C(Lr,tr=>{n(je).status==="updated"&&tr(ar)})}T((tr,hr)=>{qe(yr,1,`px-2 py-1 rounded-lg text-[10px] font-mono transition-colors border
											${tr??""}`),z(or,`${hr??""} `)},[()=>we(n(Ve),n(Ft))?"border-dl-accent/30 bg-dl-accent/8 text-dl-accent-light font-medium":n(je).status==="updated"?"border-emerald-500/15 text-emerald-400/60 hover:bg-emerald-500/5":"border-dl-border/15 text-dl-text-dim hover:bg-white/3",()=>Te(n(je).period)]),he("click",yr,()=>ne(n(Ve).id,n(Ft),n(Ve))),c(xe,yr)}),c(kt,Q)};C(Me,kt=>{var Q;((Q=n(Ve).timeline)==null?void 0:Q.length)>=1&&n(Ve).preview&&n(Ve).preview.length>=30&&kt(ye)})}var Oe=m(Me,2);{var Je=kt=>{const Q=O(()=>n(Qe).digest);var xe=j0(),je=d(xe),Ue=d(je),Ze=m(je,2);Ie(Ze,17,()=>n(Q).items.filter(or=>or.kind==="numeric"),Le,(or,Lr)=>{var ar=O0(),tr=m(d(ar),1,!0);T(()=>z(tr,n(Lr).text)),c(or,ar)});var Ft=m(Ze,2);Ie(Ft,17,()=>n(Q).items.filter(or=>or.kind==="added"),Le,(or,Lr)=>{var ar=R0(),tr=m(d(ar),1,!0);T(()=>z(tr,n(Lr).text)),c(or,ar)});var yr=m(Ft,2);Ie(yr,17,()=>n(Q).items.filter(or=>or.kind==="removed"),Le,(or,Lr)=>{var ar=F0(),tr=m(d(ar),1,!0);T(()=>z(tr,n(Lr).text)),c(or,ar)}),T(()=>z(Ue,`${n(Q).to??""} vs ${n(Q).from??""}`)),c(kt,xe)};C(Oe,kt=>{var Q,xe,je;((je=(xe=(Q=n(Qe))==null?void 0:Q.digest)==null?void 0:xe.items)==null?void 0:je.length)>0&&kt(Je)})}var ft=m(Oe,2);{var vt=kt=>{var Q=B0();c(kt,Q)};C(ft,kt=>{n(Qt)&&kt(vt)})}var It=m(ft,2),Yt=d(It);{var Kt=kt=>{var Q=Se(),xe=ae(Q);Ie(xe,17,()=>n(yt).diff,Le,(je,Ue)=>{var Ze=Se(),Ft=ae(Ze);{var yr=ar=>{var tr=q0(),hr=m(d(tr),2);{var Nr=Pr=>{var qr=Se(),An=ae(qr);Ie(An,17,()=>n(Ue).parts,Le,(qa,Bn)=>{var Ka=Se(),Rs=ae(Ka);{var Fs=on=>{var yn=V0(),va=d(yn);T(()=>z(va,n(Bn).text)),c(on,yn)},js=on=>{var yn=U0(),va=d(yn);T(()=>z(va,n(Bn).text)),c(on,yn)};C(Rs,on=>{n(Bn).kind==="insert"?on(Fs):n(Bn).kind==="equal"&&on(js,1)})}c(qa,Ka)}),c(Pr,qr)},nn=Pr=>{var qr=H0(),An=d(qr);T(()=>z(An,n(Ue).text)),c(Pr,qr)};C(hr,Pr=>{n(Ue).parts?Pr(Nr):Pr(nn,-1)})}c(ar,tr)},or=ar=>{var tr=Y0(),hr=m(d(tr),2);{var Nr=Pr=>{var qr=Se(),An=ae(qr);Ie(An,17,()=>n(Ue).parts,Le,(qa,Bn)=>{var Ka=Se(),Rs=ae(Ka);{var Fs=on=>{var yn=K0(),va=d(yn);T(()=>z(va,n(Bn).text)),c(on,yn)},js=on=>{var yn=W0(),va=d(yn);T(()=>z(va,n(Bn).text)),c(on,yn)};C(Rs,on=>{n(Bn).kind==="delete"?on(Fs):n(Bn).kind==="equal"&&on(js,1)})}c(qa,Ka)}),c(Pr,qr)},nn=Pr=>{var qr=G0(),An=d(qr);T(()=>z(An,n(Ue).text)),c(Pr,qr)};C(hr,Pr=>{n(Ue).parts?Pr(Nr):Pr(nn,-1)})}c(ar,tr)},Lr=ar=>{var tr=J0(),hr=d(tr);T(()=>z(hr,n(Ue).text)),c(ar,tr)};C(Ft,ar=>{n(Ue).kind==="added"?ar(yr):n(Ue).kind==="removed"?ar(or,1):ar(Lr,-1)})}c(je,Ze)}),c(kt,Q)},Wt=kt=>{var Q=t_(),xe=ae(Q);{var je=Ze=>{var Ft=X0();c(Ze,Ft)};C(xe,Ze=>{n(Bt)&&Ze(je)})}var Ue=m(xe,2);Ie(Ue,17,()=>n(Ot),Le,(Ze,Ft)=>{var yr=Se(),or=ae(yr);{var Lr=hr=>{var Nr=Q0(),nn=d(Nr);T(()=>z(nn,n(Ft).text)),c(hr,Nr)},ar=hr=>{var Nr=Z0(),nn=m(d(Nr),1,!0);T(()=>z(nn,n(Ft).text)),c(hr,Nr)},tr=hr=>{var Nr=e_(),nn=m(d(Nr),1,!0);T(()=>z(nn,n(Ft).text)),c(hr,Nr)};C(or,hr=>{n(Ft).kind==="same"?hr(Lr):n(Ft).kind==="added"?hr(ar,1):n(Ft).kind==="removed"&&hr(tr,2)})}c(Ze,yr)}),c(kt,Q)},ur=kt=>{var Q=Se(),xe=ae(Q);Gn(xe,()=>Nt(H(n(Qe).body))),c(kt,Q)};C(Yt,kt=>{var Q,xe;n(Gt)&&((Q=n(yt))!=null&&Q.diff)?kt(Kt):n(Gt)?kt(Wt,1):(xe=n(Qe))!=null&&xe.body&&kt(ur,2)})}T((kt,Q)=>{qe(bn,1,`px-1.5 py-0.5 rounded text-[9px] font-medium border ${kt??""}`),z(sn,Q)},[()=>U(n(Ve).status),()=>F(n(Ve).status)]),he("mouseup",It,ot),c(er,mr)};C(sr,er=>{!n(Ve).preview||n(Ve).preview.length<30?er(vr):er(Hr,-1)})}T(()=>qe(br,1,`max-w-4xl pt-2 pb-6 border-b border-dl-border/8 last:border-b-0 ${n(Ve).status==="stale"?"border-l-2 border-l-amber-400/40 pl-3":""}`)),c(Pe,br)};C(Cr,Pe=>{n(Ve)&&Pe(it)})}c(bt,nr)},fr=bt=>{const Ve=O(()=>n(me).get(n(qt).blockRef));var nr=Se(),Cr=ae(nr);{var it=Pe=>{const Qe=O(()=>Ge(n(Ve))),ut=O(()=>n(Qe)&&n(p).get(n(Ve).block)),Ot=O(()=>n(ut)?rt(n(Ve)):null);var zt=o_(),gt=d(zt),yt=d(gt);{var Bt=sr=>{var vr=a_(),Hr=d(vr);{var er=pr=>{Xi(pr,{size:12})},mr=pr=>{Uo(pr,{size:12})};C(Hr,pr=>{n(ut)?pr(er):pr(mr,-1)})}T(()=>{qe(vr,1,`p-1 rounded transition-colors ${n(ut)?"text-dl-accent-light bg-dl-accent/10":"text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5"}`),lr(vr,"title",n(ut)?"표로 보기":"차트로 보기")}),he("click",vr,()=>dt(n(Ve).block)),c(sr,vr)};C(yt,sr=>{n(Qe)&&sr(Bt)})}var Gt=m(yt,2);{var Qt=sr=>{var vr=s_(),Hr=d(vr);{var er=pr=>{Gi(pr,{size:12,class:"text-dl-success"})},mr=pr=>{_d(pr,{size:12})};C(Hr,pr=>{n(f)===n(Ve).block?pr(er):pr(mr,-1)})}he("click",vr,()=>nt(n(Ve),n(Ve).block)),c(sr,vr)};C(Gt,sr=>{var vr,Hr;((Hr=(vr=n(Ve).data)==null?void 0:vr.rows)==null?void 0:Hr.length)>0&&sr(Qt)})}var br=m(gt,2);{var Rr=sr=>{var vr=Se(),Hr=ae(vr);Oi(Hr,()=>Qi(()=>import("./ChartRenderer-DBJQ3K0G.js"),__vite__mapDeps([0,1])),null,(er,mr)=>{var pr=O(()=>{var{default:I}=n(mr);return{ChartRenderer:I}}),bn=O(()=>n(pr).ChartRenderer),sn=Se(),In=ae(sn);Is(In,()=>n(bn),(I,ge)=>{ge(I,{get spec(){return n(Ot)}})}),c(er,sn)}),c(sr,vr)},$r=sr=>{Cd(sr,{get block(){return n(Ve)}})};C(br,sr=>{n(ut)&&n(Ot)?sr(Rr):sr($r,-1)})}c(Pe,zt)};C(Cr,Pe=>{n(Ve)&&Pe(it)})}c(bt,nr)};C(Dt,bt=>{n(qt).kind==="section"?bt(cr):n(qt).kind==="block_ref"&&bt(fr,1)})}c(_t,Tt)});var Ur=m(kr,2);{var zr=_t=>{var qt=i_(),Tt=d(qt),Dt=d(Tt);Jn(qt,cr=>v(x,cr),()=>n(x)),T(()=>z(Dt,`더 불러오는 중... (${n(g)??""}/${n(B).length??""})`)),c(_t,qt)};C(Ur,_t=>{n(g)<n(B).length&&_t(zr)})}c(Ae,wt)},at=Ae=>{var Ee=Se(),wt=ae(Ee);Ie(wt,19,()=>r().blocks,Pt=>Pt.block,(Pt,Ye,At)=>{var Ht=Se(),Ct=ae(Ht);{var Mt=kr=>{const Ur=O(()=>K(n(At))),zr=O(()=>te(n(Ye))),_t=O(()=>De(n(Ye))),qt=O(()=>{var bt;return n(Ur)||((bt=n(zr))==null?void 0:bt.period)}),Tt=O(()=>{var bt;return n(qt)?$e(n(Ye),n(qt)):(bt=n(zr))==null?void 0:bt.text});var Dt=Se(),cr=ae(Dt);{var fr=bt=>{var Ve=f_(),nr=d(Ve);{var Cr=Pe=>{var Qe=d_(),ut=d(Qe);T(()=>z(ut,n(Tt))),c(Pe,Qe)},it=Pe=>{var Qe=u_(),ut=ae(Qe);{var Ot=Gt=>{var Qt=c_(),br=d(Qt);wu(br,{get periods(){return n(_t)},get selected(){return n(qt)},onSelect:Rr=>_e(n(At),Rr)}),c(Gt,Qt)};C(ut,Gt=>{n(_t).length>1&&Gt(Ot)})}var zt=m(ut,2),gt=d(zt),yt=m(zt,2),Bt=d(yt);Gn(Bt,()=>Nt(H(n(Tt)))),T(()=>z(gt,n(qt))),he("mouseup",yt,ot),c(Pe,Qe)};C(nr,Pe=>{n(Ye).textType==="heading"?Pe(Cr):Pe(it,-1)})}c(bt,Ve)};C(cr,bt=>{n(Tt)&&bt(fr)})}c(kr,Dt)},ct=O(()=>tt(n(Ye))),rr=kr=>{const Ur=O(()=>Ge(n(Ye))),zr=O(()=>n(Ur)&&n(p).get(n(Ye).block)),_t=O(()=>n(zr)?rt(n(Ye)):null);var qt=h_(),Tt=d(qt),Dt=d(Tt);{var cr=it=>{var Pe=v_(),Qe=d(Pe);{var ut=zt=>{Xi(zt,{size:12})},Ot=zt=>{Uo(zt,{size:12})};C(Qe,zt=>{n(zr)?zt(ut):zt(Ot,-1)})}T(()=>{qe(Pe,1,`p-1 rounded transition-colors ${n(zr)?"text-dl-accent-light bg-dl-accent/10":"text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5"}`),lr(Pe,"title",n(zr)?"표로 보기":"차트로 보기")}),he("click",Pe,()=>dt(n(Ye).block)),c(it,Pe)};C(Dt,it=>{n(Ur)&&it(cr)})}var fr=m(Dt,2);{var bt=it=>{var Pe=p_(),Qe=d(Pe);{var ut=zt=>{Gi(zt,{size:12,class:"text-dl-success"})},Ot=zt=>{_d(zt,{size:12})};C(Qe,zt=>{n(f)===n(Ye).block?zt(ut):zt(Ot,-1)})}he("click",Pe,()=>nt(n(Ye),n(Ye).block)),c(it,Pe)};C(fr,it=>{var Pe,Qe;((Qe=(Pe=n(Ye).data)==null?void 0:Pe.rows)==null?void 0:Qe.length)>0&&it(bt)})}var Ve=m(Tt,2);{var nr=it=>{var Pe=Se(),Qe=ae(Pe);Oi(Qe,()=>Qi(()=>import("./ChartRenderer-DBJQ3K0G.js"),__vite__mapDeps([0,1])),null,(ut,Ot)=>{var zt=O(()=>{var{default:Gt}=n(Ot);return{ChartRenderer:Gt}}),gt=O(()=>n(zt).ChartRenderer),yt=Se(),Bt=ae(yt);Is(Bt,()=>n(gt),(Gt,Qt)=>{Qt(Gt,{get spec(){return n(_t)}})}),c(ut,yt)}),c(it,Pe)},Cr=it=>{Cd(it,{get block(){return n(Ye)}})};C(Ve,it=>{n(zr)&&n(_t)?it(nr):it(Cr,-1)})}c(kr,qt)},Tr=O(()=>st(n(Ye)));C(Ct,kr=>{n(ct)?kr(Mt):n(Tr)&&kr(rr,1)})}c(Pt,Ht)}),c(Ae,Ee)};C(et,Ae=>{n(X)?Ae(St):Ae(at,-1)})}var Rt=m(et,2);{var Be=Ae=>{var Ee=m_();c(Ae,Ee)};C(Rt,Ae=>{var Ee;((Ee=r().blocks)==null?void 0:Ee.length)===0&&!n(X)&&Ae(Be)})}T(()=>z(fe,r().topicLabel||"")),c(y,V)};C(R,y=>{r()&&y(pe)})}var se=m(R,2);{var ue=y=>{var V=g_(),re=d(V),ie=d(re);Ho(ie,{size:10}),T(()=>As(V,`left: ${n(b).x??""}px; top: ${n(b).y??""}px; transform: translate(-50%, -100%)`)),he("click",V,xt),c(y,V)};C(se,y=>{n(b).show&&y(ue)})}c(t,dr),Ar()}Gr(["click","mouseup"]);var y_=h("<div> </div>"),w_=h('<div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20"><!> <div class="text-[11px] text-red-400/90 space-y-0.5"></div></div>'),k_=h("<div> </div>"),S_=h('<div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-500/8 border border-amber-500/20"><!> <div class="text-[11px] text-amber-400/80 space-y-0.5"></div></div>'),C_=h('<button><!> <span class="text-[10px] opacity-80"> </span> <span class="text-[14px] font-bold"> </span></button>'),$_=h('<div class="flex items-start gap-1.5"><span class="w-1 h-1 rounded-full bg-dl-text-dim/40 mt-1.5 flex-shrink-0"></span> <span> </span></div>'),M_=h('<div class="text-[11px] text-dl-text-muted space-y-0.5"></div>'),T_=h("<div><!> <span> </span></div>"),z_=h('<div class="text-[11px] space-y-0.5"></div>'),E_=h("<div><!> <span> </span></div>"),I_=h('<div class="text-[11px] space-y-0.5"></div>'),A_=h('<button class="text-[10px] px-1.5 py-0.5 rounded bg-dl-accent/8 text-dl-accent-light border border-dl-accent/20 hover:bg-dl-accent/15 transition-colors"> </button>'),L_=h('<div class="flex flex-wrap gap-1 pt-1 border-t border-dl-border/10"><span class="text-[10px] text-dl-text-dim mr-1">원문 보기:</span> <!></div>'),N_=h('<div class="px-3 py-2 rounded-lg bg-dl-surface-card border border-dl-border/20 space-y-2 animate-fadeIn"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><span> </span> <span class="text-[12px] font-medium text-dl-text"> </span> <span class="text-[11px] text-dl-text-muted"> </span></div> <button class="p-0.5 text-dl-text-dim hover:text-dl-text"><!></button></div> <!> <!> <!> <!></div>'),P_=h('<div class="text-[10px] text-dl-text-dim px-1"> </div>'),D_=h('<div class="space-y-2"><!> <!> <div class="grid grid-cols-4 sm:grid-cols-7 gap-1.5"></div> <!> <!> <!></div>');function O_(t,e){Ir(e,!0);let r=Fe(e,"data",3,null),a=Fe(e,"loading",3,!1),s=Fe(e,"corpName",3,""),o=Fe(e,"onNavigateTopic",3,null),i=Fe(e,"toc",3,null),l=Y(null);const u={performance:{label:"실적",icon:No},profitability:{label:"수익성",icon:_u},health:{label:"건전성",icon:cm},cashflow:{label:"현금흐름",icon:pm},governance:{label:"지배구조",icon:bu},risk:{label:"리스크",icon:co},opportunity:{label:"기회",icon:No}},f={performance:["salesOrder","businessOverview"],profitability:["IS","CIS","ratios"],health:["BS","contingentLiability","corporateBond"],cashflow:["CF","ratios"],governance:["majorShareholder","audit","dividend"],risk:["contingentLiability","riskFactors","corporateBond"],opportunity:["businessOverview","investmentOverview"]};function p($){return $==="A"?"bg-emerald-500/15 text-emerald-400 border-emerald-500/30":$==="B"?"bg-blue-500/15 text-blue-400 border-blue-500/30":$==="C"?"bg-amber-500/15 text-amber-400 border-amber-500/30":$==="D"?"bg-orange-500/15 text-orange-400 border-orange-500/30":$==="F"?"bg-red-500/15 text-red-400 border-red-500/30":"bg-dl-border/10 text-dl-text-dim border-dl-border/20"}function g($){return $==="A"?"bg-emerald-500 text-white":$==="B"?"bg-blue-500 text-white":$==="C"?"bg-amber-500 text-white":$==="D"?"bg-orange-500 text-white":$==="F"?"bg-red-500 text-white":"bg-dl-border text-dl-text-dim"}function x($){return $==="danger"?"text-red-400":$==="warning"?"text-amber-400":"text-dl-text-dim"}function b($){return $==="strong"?"text-emerald-400":"text-blue-400"}function k($){v(l,n(l)===$?null:$,!0)}let S=O(()=>{var X;if(!((X=i())!=null&&X.chapters))return null;const $=new Set;for(const J of i().chapters)for(const me of J.topics)$.add(me.topic);return $}),_=O(()=>{var $;return((($=r())==null?void 0:$.anomalies)??[]).filter(X=>X.severity==="danger")}),w=O(()=>{var $;return((($=r())==null?void 0:$.anomalies)??[]).filter(X=>X.severity==="warning")}),E=O(()=>{var $;return($=r())!=null&&$.areas?Object.keys(u).filter(X=>r().areas[X]):[]}),D=O(()=>{var X;if(!((X=r())!=null&&X.areas)||n(E).length<3)return null;const $={};for(const J of n(E))$[J]={grade:r().areas[J].grade};return C1($,s())});var M=Se(),Z=ae(M);{var ce=$=>{},P=$=>{var X=D_(),J=d(X);{var me=G=>{var q=w_(),L=d(q);Ja(L,{size:14,class:"text-red-400 mt-0.5 flex-shrink-0"});var H=m(L,2);Ie(H,21,()=>n(_),Le,(j,K)=>{var _e=y_(),$e=d(_e);T(()=>z($e,n(K).text)),c(j,_e)}),c(G,q)};C(J,G=>{n(_).length>0&&G(me)})}var B=m(J,2);{var Te=G=>{var q=S_(),L=d(q);co(L,{size:14,class:"text-amber-400 mt-0.5 flex-shrink-0"});var H=m(L,2);Ie(H,21,()=>n(w),Le,(j,K)=>{var _e=k_(),$e=d(_e);T(()=>z($e,n(K).text)),c(j,_e)}),c(G,q)};C(B,G=>{n(w).length>0&&G(Te)})}var F=m(B,2);Ie(F,21,()=>n(E),Le,(G,q)=>{const L=O(()=>u[n(q)]),H=O(()=>r().areas[n(q)]),j=O(()=>n(L).icon);var K=C_(),_e=d(K);Is(_e,()=>n(j),(st,Ge)=>{Ge(st,{size:13,class:"opacity-70"})});var $e=m(_e,2),te=d($e),De=m($e,2),tt=d(De);T(st=>{qe(K,1,`flex flex-col items-center gap-1 px-2 py-2 rounded-lg border transition-colors cursor-pointer ${st??""} ${n(l)===n(q)?"ring-1 ring-dl-accent/40":"hover:brightness-110"}`),z(te,n(L).label),z(tt,n(H).grade)},[()=>p(n(H).grade)]),he("click",K,()=>k(n(q))),c(G,K)});var U=m(F,2);{var le=G=>{var q=Se(),L=ae(q);Oi(L,()=>Qi(()=>import("./ChartRenderer-DBJQ3K0G.js"),__vite__mapDeps([0,1])),null,(H,j)=>{var K=O(()=>{var{default:De}=n(j);return{ChartRenderer:De}}),_e=O(()=>n(K).ChartRenderer),$e=Se(),te=ae($e);Is(te,()=>n(_e),(De,tt)=>{tt(De,{get spec(){return n(D)},class:"max-w-xs mx-auto"})}),c(H,$e)}),c(G,q)};C(U,G=>{n(D)&&G(le)})}var we=m(U,2);{var W=G=>{const q=O(()=>r().areas[n(l)]),L=O(()=>u[n(l)]),H=O(()=>(f[n(l)]||[]).filter(se=>!n(S)||n(S).has(se)));var j=N_(),K=d(j),_e=d(K),$e=d(_e),te=d($e),De=m($e,2),tt=d(De),st=m(De,2),Ge=d(st),rt=m(_e,2),dt=d(rt);vu(dt,{size:14});var nt=m(K,2);{var ot=se=>{var ue=M_();Ie(ue,21,()=>n(q).details,Le,(y,V)=>{var re=$_(),ie=m(d(re),2),fe=d(ie);T(()=>z(fe,n(V))),c(y,re)}),c(se,ue)};C(nt,se=>{var ue;((ue=n(q).details)==null?void 0:ue.length)>0&&se(ot)})}var xt=m(nt,2);{var $t=se=>{var ue=z_();Ie(ue,21,()=>n(q).risks,Le,(y,V)=>{var re=T_(),ie=d(re);co(ie,{size:10,class:"mt-0.5 flex-shrink-0"});var fe=m(ie,2),N=d(fe);T(ee=>{qe(re,1,`flex items-start gap-1.5 ${ee??""}`),z(N,n(V).text)},[()=>x(n(V).level)]),c(y,re)}),c(se,ue)};C(xt,se=>{var ue;((ue=n(q).risks)==null?void 0:ue.length)>0&&se($t)})}var Nt=m(xt,2);{var dr=se=>{var ue=I_();Ie(ue,21,()=>n(q).opportunities,Le,(y,V)=>{var re=E_(),ie=d(re);No(ie,{size:10,class:"mt-0.5 flex-shrink-0"});var fe=m(ie,2),N=d(fe);T(ee=>{qe(re,1,`flex items-start gap-1.5 ${ee??""}`),z(N,n(V).text)},[()=>b(n(V).level)]),c(y,re)}),c(se,ue)};C(Nt,se=>{var ue;((ue=n(q).opportunities)==null?void 0:ue.length)>0&&se(dr)})}var R=m(Nt,2);{var pe=se=>{var ue=L_(),y=m(d(ue),2);Ie(y,17,()=>n(H),Le,(V,re)=>{var ie=A_(),fe=d(ie);T(()=>z(fe,n(re))),he("click",ie,()=>o()(n(re))),c(V,ie)}),c(se,ue)};C(R,se=>{o()&&n(H).length>0&&se(pe)})}T(se=>{qe($e,1,`px-1.5 py-0.5 rounded text-[10px] font-bold ${se??""}`),z(te,n(q).grade),z(tt,n(L).label),z(Ge,`— ${n(q).summary??""}`)},[()=>g(n(q).grade)]),he("click",rt,()=>{v(l,null)}),c(G,j)};C(we,G=>{n(l)&&r().areas[n(l)]&&G(W)})}var ne=m(we,2);{var A=G=>{var q=P_(),L=d(q);T(()=>z(L,r().profile)),c(G,q)};C(ne,G=>{r().profile&&G(A)})}c($,X)};C(Z,$=>{a()?$(ce):r()&&$(P,1)})}c(t,M),Ar()}Gr(["click"]);function R_(t,e){var r,a=1;t==null&&(t=0),e==null&&(e=0);function s(){var o,i=r.length,l,u=0,f=0;for(o=0;o<i;++o)l=r[o],u+=l.x,f+=l.y;for(u=(u/i-t)*a,f=(f/i-e)*a,o=0;o<i;++o)l=r[o],l.x-=u,l.y-=f}return s.initialize=function(o){r=o},s.x=function(o){return arguments.length?(t=+o,s):t},s.y=function(o){return arguments.length?(e=+o,s):e},s.strength=function(o){return arguments.length?(a=+o,s):a},s}function F_(t){const e=+this._x.call(null,t),r=+this._y.call(null,t);return ku(this.cover(e,r),e,r,t)}function ku(t,e,r,a){if(isNaN(e)||isNaN(r))return t;var s,o=t._root,i={data:a},l=t._x0,u=t._y0,f=t._x1,p=t._y1,g,x,b,k,S,_,w,E;if(!o)return t._root=i,t;for(;o.length;)if((S=e>=(g=(l+f)/2))?l=g:f=g,(_=r>=(x=(u+p)/2))?u=x:p=x,s=o,!(o=o[w=_<<1|S]))return s[w]=i,t;if(b=+t._x.call(null,o.data),k=+t._y.call(null,o.data),e===b&&r===k)return i.next=o,s?s[w]=i:t._root=i,t;do s=s?s[w]=new Array(4):t._root=new Array(4),(S=e>=(g=(l+f)/2))?l=g:f=g,(_=r>=(x=(u+p)/2))?u=x:p=x;while((w=_<<1|S)===(E=(k>=x)<<1|b>=g));return s[E]=o,s[w]=i,t}function j_(t){var e,r,a=t.length,s,o,i=new Array(a),l=new Array(a),u=1/0,f=1/0,p=-1/0,g=-1/0;for(r=0;r<a;++r)isNaN(s=+this._x.call(null,e=t[r]))||isNaN(o=+this._y.call(null,e))||(i[r]=s,l[r]=o,s<u&&(u=s),s>p&&(p=s),o<f&&(f=o),o>g&&(g=o));if(u>p||f>g)return this;for(this.cover(u,f).cover(p,g),r=0;r<a;++r)ku(this,i[r],l[r],t[r]);return this}function B_(t,e){if(isNaN(t=+t)||isNaN(e=+e))return this;var r=this._x0,a=this._y0,s=this._x1,o=this._y1;if(isNaN(r))s=(r=Math.floor(t))+1,o=(a=Math.floor(e))+1;else{for(var i=s-r||1,l=this._root,u,f;r>t||t>=s||a>e||e>=o;)switch(f=(e<a)<<1|t<r,u=new Array(4),u[f]=l,l=u,i*=2,f){case 0:s=r+i,o=a+i;break;case 1:r=s-i,o=a+i;break;case 2:s=r+i,a=o-i;break;case 3:r=s-i,a=o-i;break}this._root&&this._root.length&&(this._root=l)}return this._x0=r,this._y0=a,this._x1=s,this._y1=o,this}function V_(){var t=[];return this.visit(function(e){if(!e.length)do t.push(e.data);while(e=e.next)}),t}function U_(t){return arguments.length?this.cover(+t[0][0],+t[0][1]).cover(+t[1][0],+t[1][1]):isNaN(this._x0)?void 0:[[this._x0,this._y0],[this._x1,this._y1]]}function cn(t,e,r,a,s){this.node=t,this.x0=e,this.y0=r,this.x1=a,this.y1=s}function H_(t,e,r){var a,s=this._x0,o=this._y0,i,l,u,f,p=this._x1,g=this._y1,x=[],b=this._root,k,S;for(b&&x.push(new cn(b,s,o,p,g)),r==null?r=1/0:(s=t-r,o=e-r,p=t+r,g=e+r,r*=r);k=x.pop();)if(!(!(b=k.node)||(i=k.x0)>p||(l=k.y0)>g||(u=k.x1)<s||(f=k.y1)<o))if(b.length){var _=(i+u)/2,w=(l+f)/2;x.push(new cn(b[3],_,w,u,f),new cn(b[2],i,w,_,f),new cn(b[1],_,l,u,w),new cn(b[0],i,l,_,w)),(S=(e>=w)<<1|t>=_)&&(k=x[x.length-1],x[x.length-1]=x[x.length-1-S],x[x.length-1-S]=k)}else{var E=t-+this._x.call(null,b.data),D=e-+this._y.call(null,b.data),M=E*E+D*D;if(M<r){var Z=Math.sqrt(r=M);s=t-Z,o=e-Z,p=t+Z,g=e+Z,a=b.data}}return a}function q_(t){if(isNaN(p=+this._x.call(null,t))||isNaN(g=+this._y.call(null,t)))return this;var e,r=this._root,a,s,o,i=this._x0,l=this._y0,u=this._x1,f=this._y1,p,g,x,b,k,S,_,w;if(!r)return this;if(r.length)for(;;){if((k=p>=(x=(i+u)/2))?i=x:u=x,(S=g>=(b=(l+f)/2))?l=b:f=b,e=r,!(r=r[_=S<<1|k]))return this;if(!r.length)break;(e[_+1&3]||e[_+2&3]||e[_+3&3])&&(a=e,w=_)}for(;r.data!==t;)if(s=r,!(r=r.next))return this;return(o=r.next)&&delete r.next,s?(o?s.next=o:delete s.next,this):e?(o?e[_]=o:delete e[_],(r=e[0]||e[1]||e[2]||e[3])&&r===(e[3]||e[2]||e[1]||e[0])&&!r.length&&(a?a[w]=r:this._root=r),this):(this._root=o,this)}function K_(t){for(var e=0,r=t.length;e<r;++e)this.remove(t[e]);return this}function W_(){return this._root}function G_(){var t=0;return this.visit(function(e){if(!e.length)do++t;while(e=e.next)}),t}function Y_(t){var e=[],r,a=this._root,s,o,i,l,u;for(a&&e.push(new cn(a,this._x0,this._y0,this._x1,this._y1));r=e.pop();)if(!t(a=r.node,o=r.x0,i=r.y0,l=r.x1,u=r.y1)&&a.length){var f=(o+l)/2,p=(i+u)/2;(s=a[3])&&e.push(new cn(s,f,p,l,u)),(s=a[2])&&e.push(new cn(s,o,p,f,u)),(s=a[1])&&e.push(new cn(s,f,i,l,p)),(s=a[0])&&e.push(new cn(s,o,i,f,p))}return this}function J_(t){var e=[],r=[],a;for(this._root&&e.push(new cn(this._root,this._x0,this._y0,this._x1,this._y1));a=e.pop();){var s=a.node;if(s.length){var o,i=a.x0,l=a.y0,u=a.x1,f=a.y1,p=(i+u)/2,g=(l+f)/2;(o=s[0])&&e.push(new cn(o,i,l,p,g)),(o=s[1])&&e.push(new cn(o,p,l,u,g)),(o=s[2])&&e.push(new cn(o,i,g,p,f)),(o=s[3])&&e.push(new cn(o,p,g,u,f))}r.push(a)}for(;a=r.pop();)t(a.node,a.x0,a.y0,a.x1,a.y1);return this}function X_(t){return t[0]}function Q_(t){return arguments.length?(this._x=t,this):this._x}function Z_(t){return t[1]}function eb(t){return arguments.length?(this._y=t,this):this._y}function Sl(t,e,r){var a=new Cl(e??X_,r??Z_,NaN,NaN,NaN,NaN);return t==null?a:a.addAll(t)}function Cl(t,e,r,a,s,o){this._x=t,this._y=e,this._x0=r,this._y0=a,this._x1=s,this._y1=o,this._root=void 0}function $d(t){for(var e={data:t.data},r=e;t=t.next;)r=r.next={data:t.data};return e}var fn=Sl.prototype=Cl.prototype;fn.copy=function(){var t=new Cl(this._x,this._y,this._x0,this._y0,this._x1,this._y1),e=this._root,r,a;if(!e)return t;if(!e.length)return t._root=$d(e),t;for(r=[{source:e,target:t._root=new Array(4)}];e=r.pop();)for(var s=0;s<4;++s)(a=e.source[s])&&(a.length?r.push({source:a,target:e.target[s]=new Array(4)}):e.target[s]=$d(a));return t};fn.add=F_;fn.addAll=j_;fn.cover=B_;fn.data=V_;fn.extent=U_;fn.find=H_;fn.remove=q_;fn.removeAll=K_;fn.root=W_;fn.size=G_;fn.visit=Y_;fn.visitAfter=J_;fn.x=Q_;fn.y=eb;function is(t){return function(){return t}}function Pa(t){return(t()-.5)*1e-6}function tb(t){return t.x+t.vx}function rb(t){return t.y+t.vy}function nb(t){var e,r,a,s=1,o=1;typeof t!="function"&&(t=is(t==null?1:+t));function i(){for(var f,p=e.length,g,x,b,k,S,_,w=0;w<o;++w)for(g=Sl(e,tb,rb).visitAfter(l),f=0;f<p;++f)x=e[f],S=r[x.index],_=S*S,b=x.x+x.vx,k=x.y+x.vy,g.visit(E);function E(D,M,Z,ce,P){var $=D.data,X=D.r,J=S+X;if($){if($.index>x.index){var me=b-$.x-$.vx,B=k-$.y-$.vy,Te=me*me+B*B;Te<J*J&&(me===0&&(me=Pa(a),Te+=me*me),B===0&&(B=Pa(a),Te+=B*B),Te=(J-(Te=Math.sqrt(Te)))/Te*s,x.vx+=(me*=Te)*(J=(X*=X)/(_+X)),x.vy+=(B*=Te)*J,$.vx-=me*(J=1-J),$.vy-=B*J)}return}return M>b+J||ce<b-J||Z>k+J||P<k-J}}function l(f){if(f.data)return f.r=r[f.data.index];for(var p=f.r=0;p<4;++p)f[p]&&f[p].r>f.r&&(f.r=f[p].r)}function u(){if(e){var f,p=e.length,g;for(r=new Array(p),f=0;f<p;++f)g=e[f],r[g.index]=+t(g,f,e)}}return i.initialize=function(f,p){e=f,a=p,u()},i.iterations=function(f){return arguments.length?(o=+f,i):o},i.strength=function(f){return arguments.length?(s=+f,i):s},i.radius=function(f){return arguments.length?(t=typeof f=="function"?f:is(+f),u(),i):t},i}function ab(t){return t.index}function Md(t,e){var r=t.get(e);if(!r)throw new Error("node not found: "+e);return r}function sb(t){var e=ab,r=g,a,s=is(30),o,i,l,u,f,p=1;t==null&&(t=[]);function g(_){return 1/Math.min(l[_.source.index],l[_.target.index])}function x(_){for(var w=0,E=t.length;w<p;++w)for(var D=0,M,Z,ce,P,$,X,J;D<E;++D)M=t[D],Z=M.source,ce=M.target,P=ce.x+ce.vx-Z.x-Z.vx||Pa(f),$=ce.y+ce.vy-Z.y-Z.vy||Pa(f),X=Math.sqrt(P*P+$*$),X=(X-o[D])/X*_*a[D],P*=X,$*=X,ce.vx-=P*(J=u[D]),ce.vy-=$*J,Z.vx+=P*(J=1-J),Z.vy+=$*J}function b(){if(i){var _,w=i.length,E=t.length,D=new Map(i.map((Z,ce)=>[e(Z,ce,i),Z])),M;for(_=0,l=new Array(w);_<E;++_)M=t[_],M.index=_,typeof M.source!="object"&&(M.source=Md(D,M.source)),typeof M.target!="object"&&(M.target=Md(D,M.target)),l[M.source.index]=(l[M.source.index]||0)+1,l[M.target.index]=(l[M.target.index]||0)+1;for(_=0,u=new Array(E);_<E;++_)M=t[_],u[_]=l[M.source.index]/(l[M.source.index]+l[M.target.index]);a=new Array(E),k(),o=new Array(E),S()}}function k(){if(i)for(var _=0,w=t.length;_<w;++_)a[_]=+r(t[_],_,t)}function S(){if(i)for(var _=0,w=t.length;_<w;++_)o[_]=+s(t[_],_,t)}return x.initialize=function(_,w){i=_,f=w,b()},x.links=function(_){return arguments.length?(t=_,b(),x):t},x.id=function(_){return arguments.length?(e=_,x):e},x.iterations=function(_){return arguments.length?(p=+_,x):p},x.strength=function(_){return arguments.length?(r=typeof _=="function"?_:is(+_),k(),x):r},x.distance=function(_){return arguments.length?(s=typeof _=="function"?_:is(+_),S(),x):s},x}var ob={value:()=>{}};function Su(){for(var t=0,e=arguments.length,r={},a;t<e;++t){if(!(a=arguments[t]+"")||a in r||/[\s.]/.test(a))throw new Error("illegal type: "+a);r[a]=[]}return new Po(r)}function Po(t){this._=t}function ib(t,e){return t.trim().split(/^|\s+/).map(function(r){var a="",s=r.indexOf(".");if(s>=0&&(a=r.slice(s+1),r=r.slice(0,s)),r&&!e.hasOwnProperty(r))throw new Error("unknown type: "+r);return{type:r,name:a}})}Po.prototype=Su.prototype={constructor:Po,on:function(t,e){var r=this._,a=ib(t+"",r),s,o=-1,i=a.length;if(arguments.length<2){for(;++o<i;)if((s=(t=a[o]).type)&&(s=lb(r[s],t.name)))return s;return}if(e!=null&&typeof e!="function")throw new Error("invalid callback: "+e);for(;++o<i;)if(s=(t=a[o]).type)r[s]=Td(r[s],t.name,e);else if(e==null)for(s in r)r[s]=Td(r[s],t.name,null);return this},copy:function(){var t={},e=this._;for(var r in e)t[r]=e[r].slice();return new Po(t)},call:function(t,e){if((s=arguments.length-2)>0)for(var r=new Array(s),a=0,s,o;a<s;++a)r[a]=arguments[a+2];if(!this._.hasOwnProperty(t))throw new Error("unknown type: "+t);for(o=this._[t],a=0,s=o.length;a<s;++a)o[a].value.apply(e,r)},apply:function(t,e,r){if(!this._.hasOwnProperty(t))throw new Error("unknown type: "+t);for(var a=this._[t],s=0,o=a.length;s<o;++s)a[s].value.apply(e,r)}};function lb(t,e){for(var r=0,a=t.length,s;r<a;++r)if((s=t[r]).name===e)return s.value}function Td(t,e,r){for(var a=0,s=t.length;a<s;++a)if(t[a].name===e){t[a]=ob,t=t.slice(0,a).concat(t.slice(a+1));break}return r!=null&&t.push({name:e,value:r}),t}var Ls=0,to=0,Zs=0,Cu=1e3,qo,ro,Ko=0,us=0,ni=0,vo=typeof performance=="object"&&performance.now?performance:Date,$u=typeof window=="object"&&window.requestAnimationFrame?window.requestAnimationFrame.bind(window):function(t){setTimeout(t,17)};function Mu(){return us||($u(db),us=vo.now()+ni)}function db(){us=0}function el(){this._call=this._time=this._next=null}el.prototype=Tu.prototype={constructor:el,restart:function(t,e,r){if(typeof t!="function")throw new TypeError("callback is not a function");r=(r==null?Mu():+r)+(e==null?0:+e),!this._next&&ro!==this&&(ro?ro._next=this:qo=this,ro=this),this._call=t,this._time=r,tl()},stop:function(){this._call&&(this._call=null,this._time=1/0,tl())}};function Tu(t,e,r){var a=new el;return a.restart(t,e,r),a}function cb(){Mu(),++Ls;for(var t=qo,e;t;)(e=us-t._time)>=0&&t._call.call(void 0,e),t=t._next;--Ls}function zd(){us=(Ko=vo.now())+ni,Ls=to=0;try{cb()}finally{Ls=0,fb(),us=0}}function ub(){var t=vo.now(),e=t-Ko;e>Cu&&(ni-=e,Ko=t)}function fb(){for(var t,e=qo,r,a=1/0;e;)e._call?(a>e._time&&(a=e._time),t=e,e=e._next):(r=e._next,e._next=null,e=t?t._next=r:qo=r);ro=t,tl(a)}function tl(t){if(!Ls){to&&(to=clearTimeout(to));var e=t-us;e>24?(t<1/0&&(to=setTimeout(zd,t-vo.now()-ni)),Zs&&(Zs=clearInterval(Zs))):(Zs||(Ko=vo.now(),Zs=setInterval(ub,Cu)),Ls=1,$u(zd))}}const vb=1664525,pb=1013904223,Ed=4294967296;function hb(){let t=1;return()=>(t=(vb*t+pb)%Ed)/Ed}function mb(t){return t.x}function xb(t){return t.y}var gb=10,_b=Math.PI*(3-Math.sqrt(5));function bb(t){var e,r=1,a=.001,s=1-Math.pow(a,1/300),o=0,i=.6,l=new Map,u=Tu(g),f=Su("tick","end"),p=hb();t==null&&(t=[]);function g(){x(),f.call("tick",e),r<a&&(u.stop(),f.call("end",e))}function x(S){var _,w=t.length,E;S===void 0&&(S=1);for(var D=0;D<S;++D)for(r+=(o-r)*s,l.forEach(function(M){M(r)}),_=0;_<w;++_)E=t[_],E.fx==null?E.x+=E.vx*=i:(E.x=E.fx,E.vx=0),E.fy==null?E.y+=E.vy*=i:(E.y=E.fy,E.vy=0);return e}function b(){for(var S=0,_=t.length,w;S<_;++S){if(w=t[S],w.index=S,w.fx!=null&&(w.x=w.fx),w.fy!=null&&(w.y=w.fy),isNaN(w.x)||isNaN(w.y)){var E=gb*Math.sqrt(.5+S),D=S*_b;w.x=E*Math.cos(D),w.y=E*Math.sin(D)}(isNaN(w.vx)||isNaN(w.vy))&&(w.vx=w.vy=0)}}function k(S){return S.initialize&&S.initialize(t,p),S}return b(),e={tick:x,restart:function(){return u.restart(g),e},stop:function(){return u.stop(),e},nodes:function(S){return arguments.length?(t=S,b(),l.forEach(k),e):t},alpha:function(S){return arguments.length?(r=+S,e):r},alphaMin:function(S){return arguments.length?(a=+S,e):a},alphaDecay:function(S){return arguments.length?(s=+S,e):+s},alphaTarget:function(S){return arguments.length?(o=+S,e):o},velocityDecay:function(S){return arguments.length?(i=1-S,e):1-i},randomSource:function(S){return arguments.length?(p=S,l.forEach(k),e):p},force:function(S,_){return arguments.length>1?(_==null?l.delete(S):l.set(S,k(_)),e):l.get(S)},find:function(S,_,w){var E=0,D=t.length,M,Z,ce,P,$;for(w==null?w=1/0:w*=w,E=0;E<D;++E)P=t[E],M=S-P.x,Z=_-P.y,ce=M*M+Z*Z,ce<w&&($=P,w=ce);return $},on:function(S,_){return arguments.length>1?(f.on(S,_),e):f.on(S)}}}function yb(){var t,e,r,a,s=is(-30),o,i=1,l=1/0,u=.81;function f(b){var k,S=t.length,_=Sl(t,mb,xb).visitAfter(g);for(a=b,k=0;k<S;++k)e=t[k],_.visit(x)}function p(){if(t){var b,k=t.length,S;for(o=new Array(k),b=0;b<k;++b)S=t[b],o[S.index]=+s(S,b,t)}}function g(b){var k=0,S,_,w=0,E,D,M;if(b.length){for(E=D=M=0;M<4;++M)(S=b[M])&&(_=Math.abs(S.value))&&(k+=S.value,w+=_,E+=_*S.x,D+=_*S.y);b.x=E/w,b.y=D/w}else{S=b,S.x=S.data.x,S.y=S.data.y;do k+=o[S.data.index];while(S=S.next)}b.value=k}function x(b,k,S,_){if(!b.value)return!0;var w=b.x-e.x,E=b.y-e.y,D=_-k,M=w*w+E*E;if(D*D/u<M)return M<l&&(w===0&&(w=Pa(r),M+=w*w),E===0&&(E=Pa(r),M+=E*E),M<i&&(M=Math.sqrt(i*M)),e.vx+=w*b.value*a/M,e.vy+=E*b.value*a/M),!0;if(b.length||M>=l)return;(b.data!==e||b.next)&&(w===0&&(w=Pa(r),M+=w*w),E===0&&(E=Pa(r),M+=E*E),M<i&&(M=Math.sqrt(i*M)));do b.data!==e&&(D=o[b.data.index]*a/M,e.vx+=w*D,e.vy+=E*D);while(b=b.next)}return f.initialize=function(b,k){t=b,r=k,p()},f.strength=function(b){return arguments.length?(s=typeof b=="function"?b:is(+b),p(),f):s},f.distanceMin=function(b){return arguments.length?(i=b*b,f):Math.sqrt(i)},f.distanceMax=function(b){return arguments.length?(l=b*b,f):Math.sqrt(l)},f.theta=function(b){return arguments.length?(u=b*b,f):Math.sqrt(u)},f}var wb=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-medium border border-dl-border/20 text-dl-text-dim bg-dl-surface-card"> </span>'),kb=h('<span class="flex items-center gap-1 text-amber-400/70"><!>순환출자 감지</span>'),Sb=bo('<line class="cursor-pointer hover:stroke-[#fff3]"></line>'),Cb=bo('<circle fill="none" stroke="#818cf860" stroke-width="2"></circle>'),$b=bo('<text text-anchor="middle" class="fill-dl-text-dim/50 text-[8px] pointer-events-none select-none"> </text>'),Mb=bo('<g class="cursor-pointer"><!><circle></circle><!></g>'),Tb=h('<div class="absolute z-10 px-2 py-1 rounded-md bg-dl-bg-card/95 border border-dl-border/30 text-[10px] text-dl-text-muted whitespace-pre-line pointer-events-none shadow-lg"> </div>'),zb=h('<div class="flex flex-wrap gap-3 px-1 text-[9px] text-dl-text-dim/60"><span class="flex items-center gap-1"><span class="w-2 h-0.5 bg-blue-400/40 inline-block"></span>출자</span> <span class="flex items-center gap-1"><span class="w-2 h-0.5 bg-amber-400/30 inline-block" style="border-bottom: 1px dashed"></span>지분</span> <span class="flex items-center gap-1"><span class="w-2 h-0.5 bg-slate-400/30 inline-block" style="border-bottom: 1px dotted"></span>인물</span> <!></div> <div class="relative rounded-lg border border-dl-border/15 bg-dl-bg-darker/50 overflow-hidden"><svg class="w-full h-full"><defs><marker id="arrow-inv" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="8" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,3 L0,6" fill="#60a5fa40"></path></marker><marker id="arrow-sh" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="8" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,3 L0,6" fill="#f59e0b30"></path></marker></defs><!><!></svg> <!></div>',1),Eb=h('<div class="space-y-2"><button class="flex items-center gap-2 w-full px-1 py-1 text-left rounded-md hover:bg-white/3 transition-colors"><!> <span class="text-[11px] font-semibold text-dl-text-dim uppercase tracking-wider flex-1">관계 네트워크</span> <!> <span class="text-[10px] text-dl-text-dim/50"> <!> </span> <!></button> <!></div>');function Ib(t,e){Ir(e,!0);let r=Fe(e,"data",3,null),a=Fe(e,"loading",3,!1),s=Fe(e,"centerCode",3,""),o=Fe(e,"onNavigate",3,null),i=Y(!1),l=Y(null),u=Y(640),f=400,p=Y(Ut({show:!1,x:0,y:0,text:""})),g=Y(Ut([])),x=Y(Ut([])),b=null;const k=["#60a5fa","#f59e0b","#10b981","#f472b6","#a78bfa","#14b8a6","#fb923c","#e879f9","#38bdf8","#fbbf24","#4ade80","#f87171","#818cf8","#2dd4bf","#fb7185"];let S=O(()=>{var A;if(!((A=r())!=null&&A.nodes))return{};const W=[...new Set(r().nodes.map(G=>G.group).filter(Boolean))],ne={};return W.forEach((G,q)=>{ne[G]=k[q%k.length]}),ne});function _(W){return W.id===s()?"#818cf8":W.type==="person"?"#94a3b8":n(S)[W.group]||"#475569"}function w(W){return W.id===s()?18:W.type==="person"?7:Math.max(6,Math.min(14,6+(W.degree||0)*.8))}function E(W){return W.type==="investment"?"#60a5fa40":W.type==="shareholder"?"#f59e0b30":"#94a3b830"}function D(W){return W.type==="person_shareholder"?"3,3":W.type==="shareholder"?"5,3":"none"}function M(W,ne=6){return W?W.length>ne?W.slice(0,ne)+"…":W:""}_r(()=>{if(!n(l))return;const W=new ResizeObserver(ne=>{for(const A of ne)v(u,A.contentRect.width||640,!0)});return W.observe(n(l).parentElement),()=>W.disconnect()}),_r(()=>{var q,L;if(!((L=(q=r())==null?void 0:q.nodes)!=null&&L.length)||!n(i)){b&&(b.stop(),b=null),v(g,[],!0),v(x,[],!0);return}const W=r().nodes.map(H=>({...H,x:H.id===s()?n(u)/2:void 0,y:H.id===s()?f/2:void 0,fx:H.id===s()?n(u)/2:void 0,fy:H.id===s()?f/2:void 0})),ne=new Map(W.map(H=>[H.id,H])),A=r().edges.filter(H=>ne.has(H.source)&&ne.has(H.target)).map(H=>({...H,source:H.source,target:H.target}));b&&b.stop();const G=bb(W).force("link",sb(A).id(H=>H.id).distance(80).strength(.4)).force("charge",yb().strength(-200)).force("center",R_(n(u)/2,f/2)).force("collide",nb().radius(H=>w(H)+4)).alphaDecay(.03);return G.on("tick",()=>{for(const H of W){const j=w(H);H.x=Math.max(j,Math.min(n(u)-j,H.x)),H.y=Math.max(j,Math.min(f-j,H.y))}v(g,[...W],!0),v(x,[...A],!0)}),b=G,()=>{G.stop()}});function Z(W,ne){const A=n(l).getBoundingClientRect(),G=[ne.label];ne.group&&G.push(`그룹: ${ne.group}`),ne.industry&&G.push(ne.industry),ne.type==="company"&&G.push(`연결: ${ne.degree||0}개`),v(p,{show:!0,x:W.clientX-A.left,y:W.clientY-A.top-10,text:G.join(`
`)},!0)}function ce(W,ne){const A=n(l).getBoundingClientRect(),G=[],q=typeof ne.source=="object"?ne.source.label:ne.source,L=typeof ne.target=="object"?ne.target.label:ne.target;G.push(`${q} → ${L}`),ne.type==="investment"?G.push(`출자 (${ne.purpose||""})`):ne.type==="shareholder"?G.push("지분 보유"):G.push("인물 지분"),ne.ownershipPct!=null&&G.push(`지분율: ${ne.ownershipPct.toFixed(1)}%`),v(p,{show:!0,x:W.clientX-A.left,y:W.clientY-A.top-10,text:G.join(`
`)},!0)}function P(){v(p,{show:!1,x:0,y:0,text:""},!0)}function $(W){W.type==="company"&&W.id!==s()&&o()&&o()(W.id)}let X=O(()=>{var W,ne,A;return((A=(ne=(W=r())==null?void 0:W.nodes)==null?void 0:ne.find(G=>G.id===s()))==null?void 0:A.group)||""}),J=O(()=>{var W;return(((W=r())==null?void 0:W.nodes)||[]).filter(ne=>ne.type==="company").length}),me=O(()=>{var W;return(((W=r())==null?void 0:W.nodes)||[]).filter(ne=>ne.type==="person").length}),B=O(()=>{var W;return(((W=r())==null?void 0:W.edges)||[]).length}),Te=O(()=>{var W,ne;return(((ne=(W=r())==null?void 0:W.meta)==null?void 0:ne.cycleCount)||0)>0});var F=Se(),U=ae(F);{var le=W=>{},we=W=>{var ne=Eb(),A=d(ne),G=d(A);bu(G,{size:13,class:"text-dl-text-dim/60"});var q=m(G,4);{var L=rt=>{var dt=wb(),nt=d(dt);T(()=>z(nt,n(X))),c(rt,dt)};C(q,rt=>{n(X)&&rt(L)})}var H=m(q,2),j=d(H),K=m(j);{var _e=rt=>{var dt=oa();T(()=>z(dt,`· ${n(me)??""}인`)),c(rt,dt)};C(K,rt=>{n(me)>0&&rt(_e)})}var $e=m(K),te=m(H,2);{var De=rt=>{vu(rt,{size:12,class:"text-dl-text-dim/40"})},tt=rt=>{kl(rt,{size:12,class:"text-dl-text-dim/40"})};C(te,rt=>{n(i)?rt(De):rt(tt,-1)})}var st=m(A,2);{var Ge=rt=>{var dt=zb(),nt=ae(dt),ot=m(d(nt),6);{var xt=ue=>{var y=kb(),V=d(y);co(V,{size:9}),c(ue,y)};C(ot,ue=>{n(Te)&&ue(xt)})}var $t=m(nt,2);As($t,"height: 400px;");var Nt=d($t),dr=m(d(Nt));Ie(dr,17,()=>n(x),Le,(ue,y)=>{const V=O(()=>typeof n(y).source=="object"?n(y).source.x:0),re=O(()=>typeof n(y).source=="object"?n(y).source.y:0),ie=O(()=>typeof n(y).target=="object"?n(y).target.x:0),fe=O(()=>typeof n(y).target=="object"?n(y).target.y:0);var N=Sb();T((ee,Ce)=>{lr(N,"x1",n(V)),lr(N,"y1",n(re)),lr(N,"x2",n(ie)),lr(N,"y2",n(fe)),lr(N,"stroke",ee),lr(N,"stroke-width",n(y).ownershipPct>20?2:1),lr(N,"stroke-dasharray",Ce),lr(N,"marker-end",n(y).type==="investment"?"url(#arrow-inv)":n(y).type==="shareholder"?"url(#arrow-sh)":"")},[()=>E(n(y)),()=>D(n(y))]),gn("mouseenter",N,ee=>ce(ee,n(y))),gn("mouseleave",N,P),c(ue,N)});var R=m(dr);Ie(R,17,()=>n(g),Le,(ue,y)=>{const V=O(()=>w(n(y))),re=O(()=>_(n(y))),ie=O(()=>n(y).id===s());var fe=Mb(),N=d(fe);{var ee=Ne=>{var de=Cb();T(()=>lr(de,"r",n(V)+3)),c(Ne,de)};C(N,Ne=>{n(ie)&&Ne(ee)})}var Ce=m(N),ve=m(Ce);{var ke=Ne=>{var de=$b(),ze=d(de);T(Re=>{lr(de,"y",n(V)+12),z(ze,Re)},[()=>M(n(y).label)]),c(Ne,de)};C(ve,Ne=>{n(V)>=8&&Ne(ke)})}T(()=>{lr(fe,"transform",`translate(${n(y).x??""},${n(y).y??""})`),lr(Ce,"r",n(V)),lr(Ce,"fill",n(re)),lr(Ce,"stroke",n(ie)?"#c4b5fd":"#ffffff10"),lr(Ce,"stroke-width",n(ie)?2:.5),lr(Ce,"opacity",n(y).type==="person"?.7:.85)}),gn("mouseenter",fe,Ne=>Z(Ne,n(y))),gn("mouseleave",fe,P),he("click",fe,()=>$(n(y))),c(ue,fe)}),Jn(Nt,ue=>v(l,ue),()=>n(l));var pe=m(Nt,2);{var se=ue=>{var y=Tb(),V=d(y);T(()=>{As(y,`left: ${n(p).x??""}px; top: ${n(p).y??""}px; transform: translate(-50%, -100%)`),z(V,n(p).text)}),c(ue,y)};C(pe,ue=>{n(p).show&&ue(se)})}T(()=>lr(Nt,"viewBox",`0 0 ${n(u)??""} 400`)),c(rt,dt)};C(st,rt=>{n(i)&&rt(Ge)})}T(()=>{z(j,`${n(J)??""}사`),z($e,` · ${n(B)??""}연결`)}),he("click",A,()=>{v(i,!n(i))}),c(W,ne)};C(U,W=>{var ne,A,G;a()?W(le):((ne=r())==null?void 0:ne.available)!==!1&&((G=(A=r())==null?void 0:A.nodes)==null?void 0:G.length)>0&&W(we,1)})}c(t,F),Ar()}Gr(["click"]);var Ab=h('<div class="flex items-center justify-between text-[12px]"><span class="text-dl-text-muted"> </span> <kbd class="px-1.5 py-0.5 rounded bg-dl-bg-darker border border-dl-border/30 text-[11px] font-mono text-dl-text-dim min-w-[32px] text-center"> </kbd></div>'),Lb=h('<div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"><div class="bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl w-80 max-w-[90vw] overflow-hidden"><div class="flex items-center justify-between px-4 py-3 border-b border-dl-border/20"><div class="flex items-center gap-2 text-dl-text"><!> <span class="text-[13px] font-semibold">단축키</span></div> <button class="p-1 rounded text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="px-4 py-3 space-y-1.5"></div></div></div>');function Nb(t,e){let r=Fe(e,"show",3,!1),a=Fe(e,"onClose",3,null);const s=[{key:"?",desc:"단축키 도움말"},{key:"1",desc:"Chat 탭"},{key:"2",desc:"Viewer 탭"},{key:"Ctrl+K",desc:"종목 검색"},{key:"Ctrl+F",desc:"뷰어 내 검색"},{key:"J / ↓",desc:"다음 topic"},{key:"K / ↑",desc:"이전 topic"},{key:"S",desc:"현재 topic AI 요약"},{key:"B",desc:"북마크 토글"},{key:"Esc",desc:"모달/검색 닫기"}];var o=Se(),i=ae(o);{var l=u=>{var f=Lb(),p=d(f),g=d(p),x=d(g),b=d(x);am(b,{size:16});var k=m(x,2),S=d(k);Ba(S,{size:14});var _=m(g,2);Ie(_,21,()=>s,Le,(w,E)=>{var D=Ab(),M=d(D),Z=d(M),ce=m(M,2),P=d(ce);T(()=>{z(Z,n(E).desc),z(P,n(E).key)}),c(w,D)}),he("click",f,function(...w){var E;(E=a())==null||E.apply(this,w)}),he("click",p,w=>w.stopPropagation()),he("click",k,function(...w){var E;(E=a())==null||E.apply(this,w)}),c(u,f)};C(i,u=>{r()&&u(l)})}c(t,o)}Gr(["click"]);var Pb=h('<div class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"></div>'),Db=h('<button class="p-1 rounded-md text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"><!></button>'),Ob=h('<div class="flex items-center justify-between"><div class="min-w-0"><div class="text-[12px] font-semibold text-dl-text truncate"> </div> <div class="text-[10px] font-mono text-dl-text-dim"> </div></div> <div class="flex items-center gap-0.5 flex-shrink-0"><!></div></div>'),Rb=h('<div class="text-[12px] text-dl-text-dim">종목 미선택</div>'),Fb=h('<button class="w-full text-left px-2 py-1.5 rounded-md text-[11px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-1.5"><!> <span class="truncate"> </span> <span class="text-[9px] font-mono text-dl-text-dim/40 ml-auto"> </span></button>'),jb=h('<div class="px-3 py-3 flex-1 overflow-y-auto"><div class="text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold mb-2">최근 종목</div> <!></div>'),Bb=h('<div class="sticky top-0 z-20 px-6 py-2 bg-dl-bg-dark/95 backdrop-blur-sm border-b border-dl-border/10"><div class="flex items-center gap-2 max-w-2xl mx-auto"><button class="flex-shrink-0 p-1.5 rounded-md text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <button class="flex items-center gap-2 flex-1 px-3 py-1.5 rounded-lg border border-dl-border/20 bg-dl-bg-darker/60 text-[12px] text-dl-text-dim hover:border-dl-border/40 hover:bg-dl-bg-darker transition-colors"><!> <span class="flex-1 text-left">공시 섹션 검색... <kbd class="ml-2 px-1 py-0.5 rounded bg-dl-border/15 text-[10px] font-mono">/</kbd></span></button></div></div>'),Vb=h('<button class="p-1 text-dl-text-dim hover:text-dl-text"><!></button>'),Ub=h('<div class="text-[10px] text-dl-text-dim/60 mt-0.5"> </div>'),Hb=h('<div class="text-[11px] text-dl-text-dim truncate mt-0.5"> </div>'),qb=h('<span class="text-[10px] text-dl-accent font-mono flex-shrink-0"> </span>'),Kb=h('<button class="w-full text-left px-4 py-2 text-[13px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-start gap-2 border-b border-dl-border/5"><div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/50 font-mono"> </span></div> <!> <!></div> <!></button>'),Wb=h('<button class="w-full py-2 text-[12px] text-dl-accent/70 hover:text-dl-accent hover:bg-white/3 transition-colors"> </button>'),Gb=h('<div class="flex items-center justify-center py-3"><!></div>'),Yb=h("<!> <!> <!>",1),Jb=h('<div class="flex items-center justify-center py-6 gap-2"><!> <span class="text-[12px] text-dl-text-dim">검색 중...</span></div>'),Xb=h('<div class="text-center py-6 text-[12px] text-dl-text-dim">결과 없음</div>'),Qb=h('<button class="w-full text-left px-4 py-2 text-[13px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-2"><!> <span> </span> <span class="text-[10px] text-dl-text-dim/40 font-mono ml-auto"> </span></button>'),Zb=h('<div class="px-4 py-2 text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold">최근 본 섹션</div> <!>',1),e2=h('<div class="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/50 backdrop-blur-sm"><div class="w-full max-w-xl bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl overflow-hidden"><div class="flex items-center gap-2 px-4 py-3 border-b border-dl-border/20"><!> <input placeholder="섹션, topic, 키워드 검색..." class="flex-1 bg-transparent text-[14px] text-dl-text outline-none placeholder:text-dl-text-dim"/> <!> <kbd class="px-1.5 py-0.5 rounded bg-dl-border/15 text-[10px] font-mono text-dl-text-dim">Esc</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div></div></div>'),t2=h('<span class="text-[11px] text-dl-text-muted truncate"> </span>'),r2=h('<div class="sticky top-0 z-30 flex items-center gap-2 px-3 py-1.5 bg-dl-bg-dark/95 border-b border-dl-border/20 backdrop-blur-sm"><button class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"><!> <span>목차</span></button> <button class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"><!> <span>검색</span></button> <!></div>'),n2=h('<span class="text-[9px] px-1 py-0.5 rounded bg-dl-border/10 text-dl-text-dim/60"> </span>'),a2=h('<button class="w-full text-left px-3 py-2 text-[13px] hover:bg-white/5 transition-colors flex items-center gap-2 border-b border-dl-border/5 last:border-b-0"><!> <span class="text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim ml-auto flex-shrink-0"> </span> <!></button>'),s2=h('<div class="absolute top-full mt-1 w-full bg-dl-bg-card border border-dl-border/30 rounded-lg shadow-xl overflow-hidden z-30 max-h-[300px] overflow-y-auto"></div>'),o2=h('<button class="w-full text-left px-3 py-2 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-2"><!> <span class="truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim/50 ml-auto"> </span></button>'),i2=h('<div class="w-full max-w-sm mt-6"><div class="text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold mb-2 text-left">최근 검색</div> <div class="space-y-0.5"></div></div>'),l2=h('<div class="flex flex-col items-center justify-center h-full text-center px-8 max-w-lg mx-auto"><!> <div class="text-[14px] text-dl-text-muted mb-2">공시 뷰어</div> <div class="text-[12px] text-dl-text-dim mb-6">종목을 검색하여 공시 문서를 살펴보세요</div> <div class="w-full max-w-sm relative"><div class="flex items-center gap-2 px-3 py-2 rounded-lg border border-dl-border/30 bg-dl-bg-darker/60 focus-within:border-dl-accent/40 transition-colors"><!> <input placeholder="종목명 또는 종목코드..." class="flex-1 bg-transparent text-[13px] text-dl-text outline-none placeholder:text-dl-text-dim"/> <!></div> <!></div> <!></div>'),d2=h('<div class="flex flex-col items-center justify-center h-full"><!> <div class="text-[12px] text-dl-text-dim">공시 데이터 로딩 중...</div></div>'),c2=h('<div class="max-w-7xl mx-auto px-6 py-4"><div class="animate-pulse space-y-4"><div class="h-5 bg-dl-surface-card/40 rounded w-2/3"></div> <div class="h-3 bg-dl-surface-card/30 rounded w-full"></div> <div class="h-3 bg-dl-surface-card/30 rounded w-5/6"></div> <div class="h-20 bg-dl-surface-card/20 rounded"></div> <div class="h-3 bg-dl-surface-card/30 rounded w-4/5"></div> <div class="h-3 bg-dl-surface-card/30 rounded w-full"></div> <div class="h-16 bg-dl-surface-card/20 rounded"></div></div></div>'),u2=h('<div class="absolute top-0 left-0 right-0 h-0.5 bg-dl-accent/20 overflow-hidden z-10"><div class="h-full bg-dl-accent/60 animate-progress-bar"></div></div>'),f2=h('<div class="animate-fadeIn"><!> <!></div>'),v2=h('<div class="mt-8 border-t border-dl-border/10 pt-4"><button class="flex items-center gap-2 text-[12px] text-dl-text-dim hover:text-dl-text transition-colors mb-3"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg> 투자 인사이트 · 관계도</button> <!></div>'),p2=h('<!> <div><div class="mt-0"><!></div> <!></div>',1),h2=h('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[13px] text-dl-text-dim">좌측 목차에서 항목을 선택하세요</div></div>'),m2=h('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[13px] text-dl-text-dim">이 종목의 공시 데이터가 없습니다</div></div>'),x2=h('<div class="flex h-full min-h-0 bg-dl-bg-dark relative"><!> <div><div class="h-full flex flex-col"><div class="px-3 py-2 border-b border-dl-border/20 flex-shrink-0"><!></div> <!> <!></div></div> <div class="flex-1 min-w-0 overflow-y-auto"><!> <!> <!> <!></div></div> <!>',1);function g2(t,e){Ir(e,!0);let r=Fe(e,"viewer",3,null),a=Fe(e,"company",3,null),s=Fe(e,"onAskAI",3,null),o=Fe(e,"onTopicChange",3,null),i=Fe(e,"recentCompanies",19,()=>[]),l=Fe(e,"onCompanySelect",3,null),u=Y(!1),f=Y(!1),p=Y(!1);function g(){v(f,typeof window<"u"&&window.innerWidth<=768,!0)}_r(()=>(g(),window.addEventListener("resize",g),()=>window.removeEventListener("resize",g)));let x=Y(!1),b=Y(""),k=Y(null);function S(){v(x,!n(x)),n(x)?requestAnimationFrame(()=>{var N;return(N=n(k))==null?void 0:N.focus()}):(v(b,""),v(U,null))}let _=Y(!1),w=Y(!1),E=null;_r(()=>{var ee;const N=(ee=a())==null?void 0:ee.stockCode;N&&N!==E&&r()&&(E=N,r().loadCompany(N))});let D=null;_r(()=>{var Ce,ve,ke,Ne;const N=(Ce=r())==null?void 0:Ce.selectedTopic,ee=((ke=(ve=r())==null?void 0:ve.topicData)==null?void 0:ke.topicLabel)||N;N&&N!==D&&(D=N,(Ne=o())==null||Ne(N,ee),$(N,ee))});let M=Y(Ut([]));const Z=8;function ce(){var N;try{const ee=localStorage.getItem("dartlab-viewer-history");return(ee?JSON.parse(ee):{})[(N=a())==null?void 0:N.stockCode]||[]}catch{return[]}}function P(N){var ee;try{const Ce=localStorage.getItem("dartlab-viewer-history"),ve=Ce?JSON.parse(Ce):{};ve[(ee=a())==null?void 0:ee.stockCode]=N,localStorage.setItem("dartlab-viewer-history",JSON.stringify(ve))}catch{}}function $(N,ee){var ve;if(!((ve=a())!=null&&ve.stockCode))return;const Ce=n(M).filter(ke=>ke.topic!==N);v(M,[{topic:N,label:ee,time:Date.now()},...Ce].slice(0,Z),!0),P(n(M))}_r(()=>{var N;(N=a())!=null&&N.stockCode&&v(M,ce(),!0)});let X=Y(""),J=Y(Ut([])),me=Y(!1),B=null,Te=Y(null);_r(()=>{const N=n(X).trim();if(!N||N.length<1){v(J,[],!0);return}clearTimeout(B),v(me,!0),B=setTimeout(async()=>{try{const ee=await gl(N);n(X).trim()===N&&v(J,ee||[],!0)}catch{v(J,[],!0)}v(me,!1)},200)});function F(N){var ee;v(X,""),v(J,[],!0),(ee=l())==null||ee(N)}let U=Y(null),le=Y(15),we=Y(!1),W=null;function ne(){var ee,Ce;if(!((Ce=(ee=r())==null?void 0:ee.toc)!=null&&Ce.chapters))return[];const N=[];for(const ve of r().toc.chapters)for(const ke of ve.topics)N.push({topic:ke.topic,chapter:ve.chapter});return N}function A(N){var ee,Ce;if((Ce=(ee=r())==null?void 0:ee.toc)!=null&&Ce.chapters){for(const ve of r().toc.chapters)if(ve.topics.find(Ne=>Ne.topic===N)){r().selectTopic(N,ve.chapter);return}}}function G(N){var ee,Ce,ve,ke;if((Ce=(ee=r())==null?void 0:ee.toc)!=null&&Ce.chapters){for(const Ne of r().toc.chapters)if(Ne.topics.find(ze=>ze.topic===N)){const ze=n(b).trim();r().selectTopic(N,Ne.chapter),ze&&((ke=(ve=r()).setSearchHighlight)==null||ke.call(ve,ze)),v(x,!1),v(b,""),v(U,null);return}}}function q(N){var ve,ke,Ne,de;const ee=(ve=N.target)==null?void 0:ve.tagName,Ce=ee==="INPUT"||ee==="TEXTAREA"||((ke=N.target)==null?void 0:ke.isContentEditable);if(N.key==="f"&&(N.ctrlKey||N.metaKey)&&a()){N.preventDefault(),S();return}if(N.key==="Escape"){if(n(p)){v(p,!1);return}if(n(x)){v(x,!1),v(b,""),v(U,null);return}return}if(!Ce){if(N.key==="?"){v(p,!n(p));return}if(N.key==="/"&&a()){N.preventDefault(),S();return}if(!n(x)&&(N.key==="ArrowUp"||N.key==="ArrowDown"||N.key==="j"||N.key==="k")&&((Ne=r())!=null&&Ne.selectedTopic)){const ze=ne(),Re=ze.findIndex(et=>et.topic===r().selectedTopic);if(Re<0)return;const be=N.key==="ArrowDown"||N.key==="j"?Re+1:Re-1;be>=0&&be<ze.length&&(N.preventDefault(),r().selectTopic(ze[be].topic,ze[be].chapter));return}if(N.key==="b"&&((de=r())!=null&&de.selectedTopic)){r().toggleBookmark(r().selectedTopic);return}}}_r(()=>{var Ce,ve,ke,Ne;const N=n(b).trim();if(v(le,15),!N||!((Ce=a())!=null&&Ce.stockCode)){v(U,null);return}if((ve=r())!=null&&ve.searchIndexReady){const de=r().searchSections(N);v(U,de.length>0?de:null,!0);return}const ee=[];if((Ne=(ke=r())==null?void 0:ke.toc)!=null&&Ne.chapters){const de=N.toLowerCase();for(const ze of r().toc.chapters)for(const Re of ze.topics)(Re.label.toLowerCase().includes(de)||Re.topic.toLowerCase().includes(de))&&ee.push({topic:Re.topic,label:Re.label,chapter:ze.chapter,snippet:"",matchCount:0,source:"toc"})}v(U,ee.length>0?ee:null,!0),clearTimeout(W),N.length>=2&&(v(we,!0),W=setTimeout(async()=>{try{const de=await Mp(a().stockCode,N);if(n(b).trim()!==N)return;const ze=(de.results||[]).map(be=>({...be,source:"text"})),Re=new Set(ee.map(be=>be.topic)),He=[...ee,...ze.filter(be=>!Re.has(be.topic))];v(U,He.length>0?He:null,!0)}catch{}v(we,!1)},300))});var L=x2();gn("keydown",Ro,q);var H=ae(L),j=d(H);{var K=N=>{var ee=Pb();he("click",ee,()=>{v(u,!1)}),c(N,ee)};C(j,N=>{n(f)&&n(u)&&N(K)})}var _e=m(j,2),$e=d(_e),te=d($e),De=d(te);{var tt=N=>{var ee=Ob(),Ce=d(ee),ve=d(Ce),ke=d(ve),Ne=m(ve,2),de=d(Ne),ze=m(Ce,2),Re=d(ze);{var He=be=>{var et=Db(),St=d(et);Ba(St,{size:12}),he("click",et,()=>{v(u,!1)}),c(be,et)};C(Re,be=>{n(f)&&be(He)})}T(()=>{z(ke,a().corpName||a().company),z(de,a().stockCode)}),c(N,ee)},st=N=>{var ee=Rb();c(N,ee)};C(De,N=>{a()?N(tt):N(st,-1)})}var Ge=m(te,2);{var rt=N=>{var ee=jb(),Ce=m(d(ee),2);Ie(Ce,17,i,Le,(ve,ke)=>{var Ne=Fb(),de=d(Ne);gd(de,{size:11,class:"text-dl-text-dim/30 flex-shrink-0"});var ze=m(de,2),Re=d(ze),He=m(ze,2),be=d(He);T(()=>{z(Re,n(ke).corpName||n(ke).company),z(be,n(ke).stockCode)}),he("click",Ne,()=>{var et;return(et=l())==null?void 0:et(n(ke))}),c(ve,Ne)}),c(N,ee)};C(Ge,N=>{!a()&&i().length>0&&N(rt)})}var dt=m(Ge,2);{let N=O(()=>{var de;return(de=r())==null?void 0:de.toc}),ee=O(()=>{var de;return(de=r())==null?void 0:de.tocLoading}),Ce=O(()=>{var de;return(de=r())==null?void 0:de.selectedTopic}),ve=O(()=>{var de;return(de=r())==null?void 0:de.expandedChapters}),ke=O(()=>{var de,ze;return((ze=(de=r())==null?void 0:de.getBookmarks)==null?void 0:ze.call(de))??[]}),Ne=O(()=>{var de;return((de=r())==null?void 0:de.visitedTopics)??new Set});b1(dt,{get toc(){return n(N)},get loading(){return n(ee)},get selectedTopic(){return n(Ce)},get expandedChapters(){return n(ve)},get bookmarks(){return n(ke)},get recentHistory(){return n(M)},onSelectTopic:(de,ze)=>{var Re;(Re=r())==null||Re.selectTopic(de,ze),n(f)&&v(u,!1)},get visitedTopics(){return n(Ne)},onToggleChapter:de=>{var ze;return(ze=r())==null?void 0:ze.toggleChapter(de)},onPrefetch:de=>{var ze;return(ze=r())==null?void 0:ze.prefetchTopic(de)}})}var nt=m(_e,2),ot=d(nt);{var xt=N=>{var ee=Bb(),Ce=d(ee),ve=d(Ce),ke=d(ve);{var Ne=He=>{im(He,{size:15})},de=He=>{gu(He,{size:15})};C(ke,He=>{n(w)?He(Ne):He(de,-1)})}var ze=m(ve,2),Re=d(ze);ga(Re,{size:13,class:"flex-shrink-0"}),T(()=>lr(ve,"title",n(w)?"목차 펼치기":"목차 접기")),he("click",ve,()=>{v(w,!n(w))}),he("click",ze,S),c(N,ee)};C(ot,N=>{a()&&!n(f)&&N(xt)})}var $t=m(ot,2);{var Nt=N=>{var ee=e2(),Ce=d(ee),ve=d(Ce),ke=d(ve);ga(ke,{size:16,class:"text-dl-text-dim flex-shrink-0"});var Ne=m(ke,2);Jn(Ne,Be=>v(k,Be),()=>n(k));var de=m(Ne,2);{var ze=Be=>{var Ae=Vb(),Ee=d(Ae);Ba(Ee,{size:14}),he("click",Ae,()=>{v(b,"")}),c(Be,Ae)};C(de,Be=>{n(b)&&Be(ze)})}var Re=m(ve,2),He=d(Re);{var be=Be=>{var Ae=Yb(),Ee=ae(Ae);Ie(Ee,17,()=>n(U).slice(0,n(le)),Le,(Ht,Ct)=>{var Mt=Kb(),ct=d(Mt),rr=d(ct),Tr=d(rr),kr=d(Tr),Ur=m(Tr,2),zr=d(Ur),_t=m(rr,2);{var qt=bt=>{var Ve=Ub(),nr=d(Ve);T(()=>z(nr,n(Ct).chapter)),c(bt,Ve)};C(_t,bt=>{n(Ct).chapter&&bt(qt)})}var Tt=m(_t,2);{var Dt=bt=>{var Ve=Hb(),nr=d(Ve);T(()=>z(nr,n(Ct).snippet)),c(bt,Ve)};C(Tt,bt=>{n(Ct).snippet&&bt(Dt)})}var cr=m(ct,2);{var fr=bt=>{var Ve=qb(),nr=d(Ve);T(()=>z(nr,`${n(Ct).matchCount??""}건`)),c(bt,Ve)};C(cr,bt=>{n(Ct).matchCount>0&&bt(fr)})}T(()=>{z(kr,n(Ct).label),z(zr,n(Ct).topic)}),he("click",Mt,()=>G(n(Ct).topic)),c(Ht,Mt)});var wt=m(Ee,2);{var Pt=Ht=>{var Ct=Wb(),Mt=d(Ct);T(()=>z(Mt,`더보기 (${n(U).length-n(le)}개 남음)`)),he("click",Ct,()=>{v(le,n(le)+15)}),c(Ht,Ct)};C(wt,Ht=>{n(U).length>n(le)&&Ht(Pt)})}var Ye=m(wt,2);{var At=Ht=>{var Ct=Gb(),Mt=d(Ct);Kr(Mt,{size:14,class:"animate-spin text-dl-text-dim"}),c(Ht,Ct)};C(Ye,Ht=>{n(we)&&Ht(At)})}c(Be,Ae)},et=Be=>{var Ae=Jb(),Ee=d(Ae);Kr(Ee,{size:14,class:"animate-spin text-dl-text-dim"}),c(Be,Ae)},St=Be=>{var Ae=Xb();c(Be,Ae)},at=O(()=>n(b).trim()),Rt=Be=>{var Ae=Se(),Ee=ae(Ae);{var wt=Pt=>{var Ye=Zb(),At=m(ae(Ye),2);Ie(At,17,()=>n(M),Le,(Ht,Ct)=>{var Mt=Qb(),ct=d(Mt);fo(ct,{size:12,class:"text-dl-text-dim/40 flex-shrink-0"});var rr=m(ct,2),Tr=d(rr),kr=m(rr,2),Ur=d(kr);T(()=>{z(Tr,n(Ct).label),z(Ur,n(Ct).topic)}),he("click",Mt,()=>G(n(Ct).topic)),c(Ht,Mt)}),c(Pt,Ye)};C(Ee,Pt=>{n(M).length>0&&Pt(wt)})}c(Be,Ae)};C(He,Be=>{n(U)?Be(be):n(we)?Be(et,1):n(at)?Be(St,2):Be(Rt,-1)})}he("click",ee,()=>{v(x,!1),v(b,""),v(U,null)}),he("click",Ce,Be=>Be.stopPropagation()),La(Ne,()=>n(b),Be=>v(b,Be)),c(N,ee)};C($t,N=>{n(x)&&N(Nt)})}var dr=m($t,2);{var R=N=>{var ee=r2(),Ce=d(ee),ve=d(Ce);En(ve,{size:11});var ke=m(Ce,2),Ne=d(ke);ga(Ne,{size:11});var de=m(ke,2);{var ze=Re=>{var He=t2(),be=d(He);T(()=>{var et,St,at;return z(be,((St=(et=r())==null?void 0:et.topicData)==null?void 0:St.topicLabel)||((at=r())==null?void 0:at.selectedTopic))}),c(Re,He)};C(de,Re=>{var He;(He=r())!=null&&He.selectedTopic&&Re(ze)})}he("click",Ce,()=>{v(u,!0)}),he("click",ke,S),c(N,ee)};C(dr,N=>{n(f)&&a()&&N(R)})}var pe=m(dr,2);{var se=N=>{var ee=l2(),Ce=d(ee);En(Ce,{size:32,class:"text-dl-text-dim/30 mb-3"});var ve=m(Ce,6),ke=d(ve),Ne=d(ke);ga(Ne,{size:14,class:"text-dl-text-dim flex-shrink-0"});var de=m(Ne,2);Jn(de,at=>v(Te,at),()=>n(Te));var ze=m(de,2);{var Re=at=>{Kr(at,{size:14,class:"animate-spin text-dl-text-dim flex-shrink-0"})};C(ze,at=>{n(me)&&at(Re)})}var He=m(ke,2);{var be=at=>{var Rt=s2();Ie(Rt,21,()=>n(J).slice(0,10),Le,(Be,Ae)=>{var Ee=a2(),wt=d(Ee);gd(wt,{size:13,class:"text-dl-text-dim/40 flex-shrink-0"});var Pt=m(wt,2),Ye=d(Pt),At=m(Pt,2),Ht=d(At),Ct=m(At,2);{var Mt=ct=>{var rr=n2(),Tr=d(rr);T(()=>z(Tr,n(Ae).market)),c(ct,rr)};C(Ct,ct=>{n(Ae).market&&ct(Mt)})}T(()=>{z(Ye,n(Ae).corpName||n(Ae).company),z(Ht,n(Ae).stockCode)}),he("click",Ee,()=>F(n(Ae))),c(Be,Ee)}),c(at,Rt)};C(He,at=>{n(J).length>0&&at(be)})}var et=m(ve,2);{var St=at=>{var Rt=i2(),Be=m(d(Rt),2);Ie(Be,21,i,Le,(Ae,Ee)=>{var wt=o2(),Pt=d(wt);fo(Pt,{size:12,class:"text-dl-text-dim/30 flex-shrink-0"});var Ye=m(Pt,2),At=d(Ye),Ht=m(Ye,2),Ct=d(Ht);T(()=>{z(At,n(Ee).corpName||n(Ee).company),z(Ct,n(Ee).stockCode)}),he("click",wt,()=>{var Mt;return(Mt=l())==null?void 0:Mt(n(Ee))}),c(Ae,wt)}),c(at,Rt)};C(et,at=>{i().length>0&&at(St)})}La(de,()=>n(X),at=>v(X,at)),c(N,ee)},ue=N=>{var ee=d2(),Ce=d(ee);Kr(Ce,{size:24,class:"animate-spin text-dl-text-dim/40 mb-3"}),c(N,ee)},y=N=>{var ee=c2();c(N,ee)},V=N=>{var ee=p2(),Ce=ae(ee);{var ve=He=>{var be=u2();c(He,be)};C(Ce,He=>{var be;(be=r())!=null&&be.topicLoading&&He(ve)})}var ke=m(Ce,2),Ne=d(ke),de=d(Ne);b_(de,{get topicData(){return r().topicData},get diffSummary(){return r().diffSummary},get viewer(){return r()},get onAskAI(){return s()},get searchHighlight(){return r().searchHighlight}});var ze=m(Ne,2);{var Re=He=>{var be=v2(),et=d(be),St=d(et),at=m(et,2);{var Rt=Be=>{var Ae=f2(),Ee=d(Ae);O_(Ee,{get data(){return r().insightData},get loading(){return r().insightLoading},get toc(){return r().toc},onNavigateTopic:A});var wt=m(Ee,2);{let Pt=O(()=>{var Ye;return(Ye=a())==null?void 0:Ye.stockCode});Ib(wt,{get data(){return r().networkData},get loading(){return r().networkLoading},get centerCode(){return n(Pt)},onNavigate:Ye=>{var At;r()&&Ye!==((At=a())==null?void 0:At.stockCode)&&r().loadCompany(Ye)}})}c(Be,Ae)};C(at,Be=>{n(_)&&Be(Rt)})}T(()=>qe(St,0,`w-3 h-3 transition-transform ${n(_)?"rotate-90":""}`)),he("click",et,()=>{v(_,!n(_))}),c(He,be)};C(ze,He=>{(r().insightData||r().networkData||r().insightLoading||r().networkLoading)&&He(Re)})}T(()=>{var He;return qe(ke,1,`max-w-7xl mx-auto px-6 py-4 ${(He=r())!=null&&He.topicLoading?"opacity-40 pointer-events-none":"animate-fadeIn"} transition-opacity duration-200`)}),c(N,ee)},re=N=>{var ee=h2(),Ce=d(ee);En(Ce,{size:28,class:"text-dl-text-dim/30 mb-3"}),c(N,ee)},ie=N=>{var ee=m2(),Ce=d(ee);Ja(Ce,{size:28,class:"text-dl-text-dim/30 mb-3"}),c(N,ee)};C(pe,N=>{var ee,Ce,ve,ke,Ne,de,ze,Re,He;a()?(ee=r())!=null&&ee.tocLoading?N(ue,1):(Ce=r())!=null&&Ce.topicLoading&&!((ve=r())!=null&&ve.topicData)?N(y,2):(ke=r())!=null&&ke.topicData?N(V,3):(Ne=r())!=null&&Ne.toc&&!((de=r())!=null&&de.selectedTopic)?N(re,4):((He=(Re=(ze=r())==null?void 0:ze.toc)==null?void 0:Re.chapters)==null?void 0:He.length)===0&&N(ie,5):N(se)})}var fe=m(H,2);Nb(fe,{get show(){return n(p)},onClose:()=>{v(p,!1)}}),T(()=>qe(_e,1,`${n(f)?`fixed top-0 left-0 bottom-0 z-50 w-64 transition-transform duration-200 ${n(u)?"translate-x-0":"-translate-x-full"}`:`flex-shrink-0 transition-all duration-200 ${n(w)?"w-0 overflow-hidden":"w-56"}`} border-r border-dl-border/30 overflow-hidden bg-dl-bg-dark`)),c(t,L),Ar()}Gr(["click"]);var _2=h('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),b2=h('<button><div class="font-medium"> </div> <div class="text-[10px] text-dl-text-dim"> </div></button>'),y2=h('<div class="px-3 py-4 text-[11px] text-dl-text-dim text-center">아직 조회한 종목이 없습니다</div>'),w2=h('<div class="border-t border-dl-border/30 px-4 py-2 text-[10px] text-dl-text-dim/50"> </div>'),k2=h('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-sm font-semibold text-dl-text">공시뷰어</div> <div class="text-[10px] text-dl-text-dim">Disclosure Viewer</div></div></div></div> <div class="flex-1 overflow-y-auto px-2 py-2"><div class="text-[10px] text-dl-text-dim uppercase tracking-widest font-semibold px-2 mb-2">최근 종목</div> <!></div> <!></div>'),S2=h('<div class="flex flex-col items-center py-4 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full opacity-60"/></div>'),C2=h("<aside><!></aside>"),$2=h("<!> <span>확인 중...</span>",1),M2=h("<!> <span>설정 필요</span>",1),T2=h('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),z2=h('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!>',1),E2=h('<div class="min-w-0 flex-1 pt-10"><!></div>'),I2=h('<div class="flex-shrink-0 border-l border-dl-border/30 transition-all duration-300"><!></div>'),A2=h('<div class="min-w-0 flex-1 flex flex-col"><!></div> <!>',1),L2=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),N2=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),P2=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),D2=h('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),O2=h('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),R2=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),F2=h('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),j2=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),B2=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),V2=h('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),U2=h('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),H2=h('<div class="text-[10px] text-dl-text-dim mt-2"> </div>'),q2=h('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex login</div></div></div></div> <!> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),K2=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2"> </div></div>'),W2=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 계정 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),G2=h('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),Y2=h("<button> <!></button>"),J2=h('<div class="flex flex-wrap gap-1.5"></div>'),X2=h('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),Q2=h('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),Z2=h('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),ey=h('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),ty=h('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),ry=h('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),ny=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),ay=h("<!> <!> <!> <!> <!> <!>",1),sy=h('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),oy=h('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),iy=h('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),ly=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><span class="text-[10px] text-dl-text-dim">공시 보기</span> <!></div></button>'),dy=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div></div> <!>',1),cy=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div></button>'),uy=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div></div> <!>',1),fy=h('<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),vy=h('<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim"><!> <div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div> <div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div></div>'),py=h('<div class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn" role="presentation"><div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"><div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"/> <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div> <div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim"><span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span></div></div></div>'),hy=h('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),my=h('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-2 left-3 z-20 pointer-events-auto flex items-center gap-1"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center ml-2 rounded-lg bg-dl-bg-card/60 border border-dl-border/20 p-0.5"><button><!> <span>Chat</span></button> <button><!> <span>Viewer</span></button></div></div> <div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="종목 검색 (Ctrl+K)"><!></button> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <button><!> <!></button></div> <div class="flex flex-1 min-h-0"><!></div></div></div>  <!> <!> <!> <!>',1);function xy(t,e){Ir(e,!0);let r=Y(""),a=Y(!1),s=Y(null),o=Y(Ut({})),i=Y(Ut({})),l=Y(null),u=Y(null),f=Y(Ut([])),p=Y(!1),g=Y(0),x=Y(!0),b=Y(""),k=Y(!1),S=Y(null),_=Y(Ut({})),w=Y(Ut({})),E=Y(""),D=Y(!1),M=Y(null),Z=Y(""),ce=Y(!1),P=Y(""),$=Y(0),X=Y(null),J=Y(null),me=Y(null);const B=zh(),Te=Uh();let F=Y(!1),U=O(()=>n(F)?"100%":B.panelMode==="viewer"?"65%":"50%"),le=Y(!1),we=Y(""),W=Y(Ut([])),ne=Y(-1),A=null,G=Y(null),q=Y(!1);function L(){v(q,window.innerWidth<=768),n(q)&&(v(p,!1),B.closePanel())}_r(()=>(L(),window.addEventListener("resize",L),()=>window.removeEventListener("resize",L))),_r(()=>{!n(k)||!n(J)||requestAnimationFrame(()=>{var I;return(I=n(J))==null?void 0:I.focus()})}),_r(()=>{!n(H)||!n(me)||requestAnimationFrame(()=>{var I;return(I=n(me))==null?void 0:I.focus()})}),_r(()=>{!n(le)||!n(G)||requestAnimationFrame(()=>{var I;return(I=n(G))==null?void 0:I.focus()})});let H=Y(null),j=Y(""),K=Y("error"),_e=Y(!1);function $e(I,ge="error",Ke=4e3){v(j,I,!0),v(K,ge,!0),v(_e,!0),setTimeout(()=>{v(_e,!1)},Ke)}const te=Ch();let De=!1;_r(()=>{De||(De=!0,ot())});let tt=Y(Ut({}));function st(I){return I==="chatgpt"?"codex":I}function Ge(I){return`dartlab-api-key:${st(I)}`}function rt(I){return typeof sessionStorage>"u"||!I?"":sessionStorage.getItem(Ge(I))||""}function dt(I,ge){typeof sessionStorage>"u"||!I||(ge?sessionStorage.setItem(Ge(I),ge):sessionStorage.removeItem(Ge(I)))}async function nt(I,ge=null,Ke=null){var ye;const Me=await xp(I,ge,Ke);if(Me!=null&&Me.provider){const Oe=st(Me.provider);v(o,{...n(o),[Oe]:{...n(o)[Oe]||{},available:!!Me.available,model:Me.model||((ye=n(o)[Oe])==null?void 0:ye.model)||ge||null}},!0)}return Me}async function ot(){var I,ge,Ke;v(x,!0);try{const Me=await mp();v(o,Me.providers||{},!0),v(i,Me.ollama||{},!0),v(tt,Me.codex||{},!0),Me.version&&v(b,Me.version,!0);const ye=st(localStorage.getItem("dartlab-provider")),Oe=localStorage.getItem("dartlab-model"),Je=rt(ye);if(ye&&((I=n(o)[ye])!=null&&I.available)){v(l,ye,!0),v(S,ye,!0),v(E,Je,!0),await xt(ye);const ft=n(_)[ye]||[];Oe&&ft.includes(Oe)?v(u,Oe,!0):ft.length>0&&(v(u,ft[0],!0),localStorage.setItem("dartlab-model",n(u))),v(f,ft,!0),v(x,!1);return}if(ye&&n(o)[ye]){if(v(l,ye,!0),v(S,ye,!0),v(E,Je,!0),Je)try{await nt(ye,Oe,Je)}catch(vt){console.warn("validateProvider:",vt)}await xt(ye);const ft=n(_)[ye]||[];v(f,ft,!0),Oe&&ft.includes(Oe)?v(u,Oe,!0):ft.length>0&&v(u,ft[0],!0),v(x,!1);return}for(const ft of["codex","ollama","openai"])if((ge=n(o)[ft])!=null&&ge.available){v(l,ft,!0),v(S,ft,!0),v(E,rt(ft),!0),await xt(ft);const vt=n(_)[ft]||[];v(f,vt,!0),v(u,((Ke=n(o)[ft])==null?void 0:Ke.model)||(vt.length>0?vt[0]:null),!0),n(u)&&localStorage.setItem("dartlab-model",n(u));break}}catch(Me){console.error("loadStatus:",Me)}v(x,!1)}async function xt(I){I=st(I),v(w,{...n(w),[I]:!0},!0);try{const ge=await gp(I);v(_,{...n(_),[I]:ge.models||[]},!0)}catch(ge){console.warn("loadModelsFor:",ge),v(_,{...n(_),[I]:[]},!0)}v(w,{...n(w),[I]:!1},!0)}async function $t(I){var Ke;I=st(I),v(l,I,!0),v(u,null),v(S,I,!0),localStorage.setItem("dartlab-provider",I),localStorage.removeItem("dartlab-model"),v(E,rt(I),!0),v(M,null),await xt(I);const ge=n(_)[I]||[];if(v(f,ge,!0),ge.length>0&&(v(u,((Ke=n(o)[I])==null?void 0:Ke.model)||ge[0],!0),localStorage.setItem("dartlab-model",n(u)),n(E)))try{await nt(I,n(u),n(E))}catch{}}async function Nt(I){v(u,I,!0),localStorage.setItem("dartlab-model",I);const ge=rt(n(l));if(ge)try{await nt(st(n(l)),I,ge)}catch{}}function dr(I){I=st(I),n(S)===I?v(S,null):(v(S,I,!0),xt(I))}async function R(){const I=n(E).trim();if(!(!I||!n(l))){v(D,!0),v(M,null);try{const ge=await nt(st(n(l)),n(u),I);ge.available?(dt(n(l),I),v(M,"success"),!n(u)&&ge.model&&v(u,ge.model,!0),await xt(n(l)),v(f,n(_)[n(l)]||[],!0),$e("API 키 인증 성공","success")):(dt(n(l),""),v(M,"error"))}catch{dt(n(l),""),v(M,"error")}v(D,!1)}}async function pe(){try{await bp(),n(l)==="codex"&&v(o,{...n(o),codex:{...n(o).codex,available:!1}},!0),$e("Codex 계정 로그아웃 완료","success"),await ot()}catch{$e("로그아웃 실패")}}function se(){const I=n(Z).trim();!I||n(ce)||(v(ce,!0),v(P,"준비 중..."),v($,0),v(X,_p(I,{onProgress(ge){ge.total&&ge.completed!==void 0?(v($,Math.round(ge.completed/ge.total*100),!0),v(P,`다운로드 중... ${n($)}%`)):ge.status&&v(P,ge.status,!0)},async onDone(){v(ce,!1),v(X,null),v(Z,""),v(P,""),v($,0),$e(`${I} 다운로드 완료`,"success"),await xt("ollama"),v(f,n(_).ollama||[],!0),n(f).includes(I)&&await Nt(I)},onError(ge){v(ce,!1),v(X,null),v(P,""),v($,0),$e(`다운로드 실패: ${ge}`)}}),!0))}function ue(){n(X)&&(n(X).abort(),v(X,null)),v(ce,!1),v(Z,""),v(P,""),v($,0)}function y(){v(p,!n(p))}function V(I){B.openData(I)}function re(I,ge=null){B.openEvidence(I,ge)}function ie(I){B.openViewer(I)}function fe(){if(v(E,""),v(M,null),n(l))v(S,n(l),!0);else{const I=Object.keys(n(o));v(S,I.length>0?I[0]:null,!0)}v(k,!0),n(S)&&xt(n(S))}function N(I){var ge,Ke,Me,ye;if(I)for(let Oe=I.messages.length-1;Oe>=0;Oe--){const Je=I.messages[Oe];if(Je.role==="assistant"&&((ge=Je.meta)!=null&&ge.stockCode||(Ke=Je.meta)!=null&&Ke.company||Je.company)){B.syncCompanyFromMessage({company:((Me=Je.meta)==null?void 0:Me.company)||Je.company,stockCode:(ye=Je.meta)==null?void 0:ye.stockCode},B.selectedCompany);return}}}function ee(){te.createConversation(),v(r,""),v(a,!1),n(s)&&(n(s).abort(),v(s,null))}function Ce(I){te.setActive(I),N(te.active),v(r,""),v(a,!1),n(s)&&(n(s).abort(),v(s,null))}function ve(I){v(H,I,!0)}function ke(){n(H)&&(te.deleteConversation(n(H)),v(H,null))}function Ne(){var ge;const I=te.active;if(!I)return null;for(let Ke=I.messages.length-1;Ke>=0;Ke--){const Me=I.messages[Ke];if(Me.role==="assistant"&&((ge=Me.meta)!=null&&ge.stockCode))return Me.meta.stockCode}return null}async function de(I=null){var Wt,ur,kt;const ge=(I??n(r)).trim();if(!ge||n(a))return;if(!n(l)||!((Wt=n(o)[n(l)])!=null&&Wt.available)){$e("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),fe();return}te.activeId||te.createConversation();const Ke=te.activeId;te.addMessage("user",ge),v(r,""),v(a,!0),te.addMessage("assistant",""),te.updateLastMessage({loading:!0,startedAt:Date.now()}),no(g);const Me=te.active,ye=[];let Oe=null;if(Me){const Q=Me.messages.slice(0,-2);for(const xe of Q)if((xe.role==="user"||xe.role==="assistant")&&xe.text&&xe.text.trim()&&!xe.error&&!xe.loading){const je={role:xe.role,text:xe.text};xe.role==="assistant"&&((ur=xe.meta)!=null&&ur.stockCode)&&(je.meta={company:xe.meta.company||xe.company,stockCode:xe.meta.stockCode,modules:xe.meta.includedModules||null,market:xe.meta.market||null,topic:xe.meta.topic||null,topicLabel:xe.meta.topicLabel||null,dialogueMode:xe.meta.dialogueMode||null,questionTypes:xe.meta.questionTypes||null,userGoal:xe.meta.userGoal||null},Oe=xe.meta.stockCode),ye.push(je)}}const Je=((kt=B.selectedCompany)==null?void 0:kt.stockCode)||Oe||Ne(),ft=B.getViewContext();function vt(){return te.activeId!==Ke}const It={provider:n(l),model:n(u),viewContext:ft},Yt=rt(n(l));Yt&&(It.api_key=Yt);const Kt=Ap(Je,ge,It,{onMeta(Q){var Ft;if(vt())return;const xe=te.active,je=xe==null?void 0:xe.messages[xe.messages.length-1],Ze={meta:{...(je==null?void 0:je.meta)||{},...Q}};Q.company&&(Ze.company=Q.company,te.activeId&&((Ft=te.active)==null?void 0:Ft.title)==="새 대화"&&te.updateTitle(te.activeId,Q.company)),Q.stockCode&&(Ze.stockCode=Q.stockCode),(Q.company||Q.stockCode)&&B.syncCompanyFromMessage(Q,B.selectedCompany),te.updateLastMessage(Ze)},onSnapshot(Q){vt()||te.updateLastMessage({snapshot:Q})},onContext(Q){if(vt())return;const xe=te.active;if(!xe)return;const je=xe.messages[xe.messages.length-1],Ue=(je==null?void 0:je.contexts)||[];te.updateLastMessage({contexts:[...Ue,{module:Q.module,label:Q.label,text:Q.text}]})},onSystemPrompt(Q){vt()||te.updateLastMessage({systemPrompt:Q.text,userContent:Q.userContent||null})},onToolCall(Q){if(vt())return;const xe=te.active;if(!xe)return;const je=xe.messages[xe.messages.length-1],Ue=(je==null?void 0:je.toolEvents)||[];te.updateLastMessage({toolEvents:[...Ue,{type:"call",name:Q.name,arguments:Q.arguments}]})},onToolResult(Q){if(vt())return;const xe=te.active;if(!xe)return;const je=xe.messages[xe.messages.length-1],Ue=(je==null?void 0:je.toolEvents)||[];te.updateLastMessage({toolEvents:[...Ue,{type:"result",name:Q.name,result:Q.result}]})},onChunk(Q){if(vt())return;const xe=te.active;if(!xe)return;const je=xe.messages[xe.messages.length-1];te.updateLastMessage({text:((je==null?void 0:je.text)||"")+Q}),no(g)},onDone(){if(vt())return;const Q=te.active,xe=Q==null?void 0:Q.messages[Q.messages.length-1],je=xe!=null&&xe.startedAt?((Date.now()-xe.startedAt)/1e3).toFixed(1):null;te.updateLastMessage({loading:!1,duration:je}),te.flush(),v(a,!1),v(s,null),no(g)},onViewerNavigate(Q){vt()||et(Q)},onError(Q,xe,je){vt()||(te.updateLastMessage({text:`오류: ${Q}`,loading:!1,error:!0}),te.flush(),$e(xe==="login"?`${Q} — 설정에서 Codex 로그인을 확인하세요`:xe==="install"?`${Q} — 설정에서 Codex 설치 안내를 확인하세요`:Q),v(a,!1),v(s,null))}},ye);v(s,Kt,!0)}function ze(){n(s)&&(n(s).abort(),v(s,null),v(a,!1),te.updateLastMessage({loading:!1}),te.flush())}function Re(){const I=te.active;if(!I||I.messages.length<2)return;let ge="";for(let Ke=I.messages.length-1;Ke>=0;Ke--)if(I.messages[Ke].role==="user"){ge=I.messages[Ke].text;break}ge&&(te.removeLastMessage(),te.removeLastMessage(),v(r,ge,!0),requestAnimationFrame(()=>{de()}))}function He(){const I=te.active;if(!I)return;let ge=`# ${I.title}

`;for(const Oe of I.messages)Oe.role==="user"?ge+=`## You

${Oe.text}

`:Oe.role==="assistant"&&Oe.text&&(ge+=`## DartLab

${Oe.text}

`);const Ke=new Blob([ge],{type:"text/markdown;charset=utf-8"}),Me=URL.createObjectURL(Ke),ye=document.createElement("a");ye.href=Me,ye.download=`${I.title||"dartlab-chat"}.md`,ye.click(),URL.revokeObjectURL(Me),$e("대화가 마크다운으로 내보내졌습니다","success")}function be(I){var Me;B.switchView("chat");const ge=((Me=Te.topicData)==null?void 0:Me.topicLabel)||"",Ke=ge?`[${ge}] `:"";v(r,`${Ke}"${I}" — 이 내용에 대해 설명해줘`),requestAnimationFrame(()=>{const ye=document.querySelector(".input-textarea");ye&&ye.focus()})}function et(I){I!=null&&I.topic&&(B.switchView("viewer"),I.chapter&&Te.selectTopic(I.topic,I.chapter))}function St(){v(le,!0),v(we,""),v(W,[],!0),v(ne,-1)}function at(I){var Me,ye;(I.metaKey||I.ctrlKey)&&I.key==="n"&&(I.preventDefault(),ee()),(I.metaKey||I.ctrlKey)&&I.key==="k"&&(I.preventDefault(),St()),(I.metaKey||I.ctrlKey)&&I.shiftKey&&I.key==="S"&&(I.preventDefault(),y()),I.key==="Escape"&&n(le)?v(le,!1):I.key==="Escape"&&n(k)?v(k,!1):I.key==="Escape"&&n(H)?v(H,null):I.key==="Escape"&&B.panelOpen&&B.closePanel();const ge=(Me=I.target)==null?void 0:Me.tagName;if(!(ge==="INPUT"||ge==="TEXTAREA"||((ye=I.target)==null?void 0:ye.isContentEditable))&&!I.ctrlKey&&!I.metaKey&&!I.altKey){if(I.key==="1"){B.switchView("chat");return}if(I.key==="2"){B.switchView("viewer");return}}}let Rt=O(()=>{var I;return((I=te.active)==null?void 0:I.messages)||[]}),Be=O(()=>te.active&&te.active.messages.length>0),Ae=O(()=>{var I;return!n(x)&&(!n(l)||!((I=n(o)[n(l)])!=null&&I.available))});const Ee=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var wt=my();gn("keydown",Ro,at);var Pt=ae(wt),Ye=d(Pt);{var At=I=>{var ge=_2();he("click",ge,()=>{v(p,!1)}),c(I,ge)};C(Ye,I=>{n(q)&&n(p)&&I(At)})}var Ht=m(Ye,2),Ct=d(Ht);{var Mt=I=>{var ge=C2(),Ke=d(ge);{var Me=Oe=>{var Je=k2(),ft=m(d(Je),2),vt=m(d(ft),2);Ie(vt,17,()=>B.recentCompanies||[],Le,(Kt,Wt)=>{var ur=b2(),kt=d(ur),Q=d(kt),xe=m(kt,2),je=d(xe);T(()=>{var Ue;qe(ur,1,`w-full text-left px-3 py-2 rounded-lg text-[12px] transition-colors mb-0.5
										${((Ue=B.selectedCompany)==null?void 0:Ue.stockCode)===n(Wt).stockCode?"bg-dl-accent/10 text-dl-accent-light border border-dl-accent/20":"text-dl-text-muted hover:bg-white/5 hover:text-dl-text"}`),z(Q,n(Wt).name),z(je,n(Wt).stockCode)}),he("click",ur,()=>{ie(n(Wt)),n(q)&&v(p,!1)}),c(Kt,ur)},Kt=>{var Wt=y2();c(Kt,Wt)});var It=m(ft,2);{var Yt=Kt=>{var Wt=w2(),ur=d(Wt);T(()=>z(ur,`v${n(b)??""}`)),c(Kt,Wt)};C(It,Kt=>{n(b)&&Kt(Yt)})}c(Oe,Je)},ye=Oe=>{var Je=S2();c(Oe,Je)};C(Ke,Oe=>{n(p)?Oe(Me):Oe(ye,-1)})}T(()=>qe(ge,1,`surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden ${n(p)?"w-[260px]":"w-[52px]"}`)),c(I,ge)},ct=I=>{{let ge=O(()=>n(q)?!0:n(p));Sm(I,{get conversations(){return te.conversations},get activeId(){return te.activeId},get open(){return n(ge)},get version(){return n(b)},onNewChat:()=>{ee(),n(q)&&v(p,!1)},onSelect:Ke=>{Ce(Ke),n(q)&&v(p,!1)},onDelete:ve,onOpenSearch:St})}};C(Ct,I=>{B.activeView==="viewer"?I(Mt):I(ct,-1)})}var rr=m(Ht,2),Tr=d(rr),kr=d(Tr),Ur=d(kr);{var zr=I=>{gu(I,{size:18})},_t=I=>{om(I,{size:18})};C(Ur,I=>{n(p)?I(zr):I(_t,-1)})}var qt=m(kr,2),Tt=d(qt),Dt=d(Tt);Ho(Dt,{size:12});var cr=m(Tt,2),fr=d(cr);Wi(fr,{size:12});var bt=m(Tr,2),Ve=d(bt),nr=d(Ve);ga(nr,{size:14});var Cr=m(Ve,2),it=d(Cr);En(it,{size:14});var Pe=m(Cr,2),Qe=d(Pe);nm(Qe,{size:14});var ut=m(Pe,2),Ot=d(ut);em(Ot,{size:14});var zt=m(ut,2),gt=d(zt);{var yt=I=>{var ge=$2(),Ke=ae(ge);Kr(Ke,{size:12,class:"animate-spin"}),c(I,ge)},Bt=I=>{var ge=M2(),Ke=ae(ge);Ja(Ke,{size:12}),c(I,ge)},Gt=I=>{var ge=z2(),Ke=m(ae(ge),2),Me=d(Ke),ye=m(Ke,2);{var Oe=Je=>{var ft=T2(),vt=m(ae(ft),2),It=d(vt);T(()=>z(It,n(u))),c(Je,ft)};C(ye,Je=>{n(u)&&Je(Oe)})}T(()=>z(Me,n(l))),c(I,ge)};C(gt,I=>{n(x)?I(yt):n(Ae)?I(Bt,1):I(Gt,-1)})}var Qt=m(gt,2);dm(Qt,{size:12});var br=m(bt,2),Rr=d(br);{var $r=I=>{var ge=E2(),Ke=d(ge);g2(Ke,{get viewer(){return Te},get company(){return B.selectedCompany},get recentCompanies(){return B.recentCompanies},onCompanySelect:ie,onAskAI:be,onTopicChange:(Me,ye)=>B.setViewerTopic(Me,ye)}),c(I,ge)},sr=I=>{var ge=A2(),Ke=ae(ge),Me=d(Ke);{var ye=vt=>{{let It=O(()=>B.viewerTopic?{topic:B.viewerTopic,topicLabel:B.viewerTopicLabel,period:B.viewerPeriod}:null);Ax(vt,{get messages(){return n(Rt)},get isLoading(){return n(a)},get scrollTrigger(){return n(g)},get selectedCompany(){return B.selectedCompany},get viewerContext(){return n(It)},onSend:de,onStop:ze,onRegenerate:Re,onExport:He,onOpenData:V,onOpenEvidence:re,onCompanySelect:ie,get inputText(){return n(r)},set inputText(Yt){v(r,Yt,!0)}})}},Oe=vt=>{Lm(vt,{onSend:de,onCompanySelect:ie,get inputText(){return n(r)},set inputText(It){v(r,It,!0)}})};C(Me,vt=>{n(Be)?vt(ye):vt(Oe,-1)})}var Je=m(Ke,2);{var ft=vt=>{var It=I2(),Yt=d(It);o1(Yt,{get mode(){return B.panelMode},get company(){return B.selectedCompany},get data(){return B.panelData},onClose:()=>{v(F,!1),B.closePanel()},onTopicChange:(Kt,Wt)=>B.setViewerTopic(Kt,Wt),onFullscreen:()=>{v(F,!n(F))},get isFullscreen(){return n(F)}}),T(()=>As(It,`width: ${n(U)??""}; min-width: 360px; ${n(F)?"":"max-width: 75vw;"}`)),c(vt,It)};C(Je,vt=>{!n(q)&&B.panelOpen&&vt(ft)})}c(I,ge)};C(Rr,I=>{B.activeView==="viewer"?I($r):I(sr,-1)})}var vr=m(Pt,2);{var Hr=I=>{var ge=oy(),Ke=d(ge),Me=d(Ke),ye=d(Me),Oe=m(d(ye),2),Je=d(Oe);Ba(Je,{size:18});var ft=m(Me,2),vt=d(ft);Ie(vt,21,()=>Object.entries(n(o)),Le,(Q,xe)=>{var je=O(()=>sl(n(xe),2));let Ue=()=>n(je)[0],Ze=()=>n(je)[1];const Ft=O(()=>Ue()===n(l)),yr=O(()=>n(S)===Ue()),or=O(()=>Ze().auth==="api_key"),Lr=O(()=>Ze().auth==="cli"),ar=O(()=>n(_)[Ue()]||[]),tr=O(()=>n(w)[Ue()]);var hr=sy(),Nr=d(hr),nn=d(Nr),Pr=m(nn,2),qr=d(Pr),An=d(qr),qa=d(An),Bn=m(An,2);{var Ka=Mr=>{var ln=L2();c(Mr,ln)};C(Bn,Mr=>{n(Ft)&&Mr(Ka)})}var Rs=m(qr,2),Fs=d(Rs),js=m(Pr,2),on=d(js);{var yn=Mr=>{io(Mr,{size:16,class:"text-dl-success"})},va=Mr=>{var ln=N2(),wa=ae(ln);yd(wa,{size:14,class:"text-amber-400"}),c(Mr,ln)},zu=Mr=>{var ln=P2(),wa=ae(ln);Ja(wa,{size:14,class:"text-amber-400"}),c(Mr,ln)},Eu=Mr=>{var ln=D2(),wa=ae(ln);fm(wa,{size:14,class:"text-dl-text-dim"}),c(Mr,ln)};C(on,Mr=>{Ze().available?Mr(yn):n(or)?Mr(va,1):n(Lr)&&Ue()==="codex"&&n(tt).installed?Mr(zu,2):n(Lr)&&!Ze().available&&Mr(Eu,3)})}var Iu=m(Nr,2);{var Au=Mr=>{var ln=ay(),wa=ae(ln);{var Lu=xr=>{var Dr=R2(),Yr=d(Dr),dn=d(Yr),Ln=m(Yr,2),an=d(Ln),wn=m(an,2),ka=d(wn);{var Sa=ir=>{Kr(ir,{size:12,class:"animate-spin"})},kn=ir=>{yd(ir,{size:12})};C(ka,ir=>{n(D)?ir(Sa):ir(kn,-1)})}var Vn=m(Ln,2);{var Sr=ir=>{var Sn=O2(),Jr=d(Sn);Ja(Jr,{size:12}),c(ir,Sn)};C(Vn,ir=>{n(M)==="error"&&ir(Sr)})}T(ir=>{z(dn,Ze().envKey?`환경변수 ${Ze().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),lr(an,"placeholder",Ue()==="openai"?"sk-...":Ue()==="claude"?"sk-ant-...":"API Key"),wn.disabled=ir},[()=>!n(E).trim()||n(D)]),he("keydown",an,ir=>{ir.key==="Enter"&&R()}),La(an,()=>n(E),ir=>v(E,ir)),he("click",wn,R),c(xr,Dr)};C(wa,xr=>{n(or)&&!Ze().available&&xr(Lu)})}var Ml=m(wa,2);{var Nu=xr=>{var Dr=j2(),Yr=d(Dr),dn=d(Yr);io(dn,{size:13,class:"text-dl-success"});var Ln=m(Yr,2),an=d(Ln),wn=m(an,2);{var ka=kn=>{var Vn=F2(),Sr=d(Vn);{var ir=Jr=>{Kr(Jr,{size:10,class:"animate-spin"})},Sn=Jr=>{var ea=oa("변경");c(Jr,ea)};C(Sr,Jr=>{n(D)?Jr(ir):Jr(Sn,-1)})}T(()=>Vn.disabled=n(D)),he("click",Vn,R),c(kn,Vn)},Sa=O(()=>n(E).trim());C(wn,kn=>{n(Sa)&&kn(ka)})}he("keydown",an,kn=>{kn.key==="Enter"&&R()}),La(an,()=>n(E),kn=>v(E,kn)),c(xr,Dr)};C(Ml,xr=>{n(or)&&Ze().available&&xr(Nu)})}var Tl=m(Ml,2);{var Pu=xr=>{var Dr=B2(),Yr=m(d(Dr),2),dn=d(Yr);lo(dn,{size:14});var Ln=m(dn,2);bd(Ln,{size:10,class:"ml-auto"}),c(xr,Dr)},Du=xr=>{var Dr=V2(),Yr=d(Dr),dn=d(Yr);Ja(dn,{size:14}),c(xr,Dr)};C(Tl,xr=>{Ue()==="ollama"&&!n(i).installed?xr(Pu):Ue()==="ollama"&&n(i).installed&&!n(i).running&&xr(Du,1)})}var zl=m(Tl,2);{var Ou=xr=>{var Dr=K2(),Yr=d(Dr);{var dn=wn=>{var ka=q2(),Sa=ae(ka),kn=d(Sa),Vn=m(Sa,2),Sr=d(Vn);{var ir=Cn=>{var ta=U2();c(Cn,ta)};C(Sr,Cn=>{n(tt).installed||Cn(ir)})}var Sn=m(Sr,2),Jr=d(Sn),ea=d(Jr),Wa=m(Vn,2);{var Bs=Cn=>{var ta=H2(),Ca=d(ta);T(()=>z(Ca,n(tt).loginStatus)),c(Cn,ta)};C(Wa,Cn=>{n(tt).loginStatus&&Cn(Bs)})}var Vs=m(Wa,2),vn=d(Vs);Ja(vn,{size:12,class:"text-amber-400 flex-shrink-0"}),T(()=>{z(kn,n(tt).installed?"Codex CLI가 설치되었지만 로그인이 필요합니다":"Codex CLI 설치가 필요합니다"),z(ea,n(tt).installed?"1.":"2.")}),c(wn,ka)};C(Yr,wn=>{Ue()==="codex"&&wn(dn)})}var Ln=m(Yr,2),an=d(Ln);T(()=>z(an,n(tt).installed?"로그인 완료 후 새로고침하세요":"설치 완료 후 새로고침하세요")),c(xr,Dr)};C(zl,xr=>{n(Lr)&&!Ze().available&&xr(Ou)})}var El=m(zl,2);{var Ru=xr=>{var Dr=W2(),Yr=d(Dr),dn=d(Yr),Ln=d(dn);io(Ln,{size:13,class:"text-dl-success"});var an=m(dn,2),wn=d(an);sm(wn,{size:11}),he("click",an,pe),c(xr,Dr)};C(El,xr=>{Ue()==="codex"&&Ze().available&&xr(Ru)})}var Fu=m(El,2);{var ju=xr=>{var Dr=ny(),Yr=d(Dr),dn=m(d(Yr),2);{var Ln=Sr=>{Kr(Sr,{size:12,class:"animate-spin text-dl-text-dim"})};C(dn,Sr=>{n(tr)&&Sr(Ln)})}var an=m(Yr,2);{var wn=Sr=>{var ir=G2(),Sn=d(ir);Kr(Sn,{size:14,class:"animate-spin"}),c(Sr,ir)},ka=Sr=>{var ir=J2();Ie(ir,21,()=>n(ar),Le,(Sn,Jr)=>{var ea=Y2(),Wa=d(ea),Bs=m(Wa);{var Vs=vn=>{Gi(vn,{size:10,class:"inline ml-1"})};C(Bs,vn=>{n(Jr)===n(u)&&n(Ft)&&vn(Vs)})}T(vn=>{qe(ea,1,vn),z(Wa,`${n(Jr)??""} `)},[()=>gr(wr("px-3 py-1.5 rounded-lg text-[11px] border transition-all",n(Jr)===n(u)&&n(Ft)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),he("click",ea,()=>{Ue()!==n(l)&&$t(Ue()),Nt(n(Jr))}),c(Sn,ea)}),c(Sr,ir)},Sa=Sr=>{var ir=X2();c(Sr,ir)};C(an,Sr=>{n(tr)&&n(ar).length===0?Sr(wn):n(ar).length>0?Sr(ka,1):Sr(Sa,-1)})}var kn=m(an,2);{var Vn=Sr=>{var ir=ry(),Sn=d(ir),Jr=m(d(Sn),2),ea=m(d(Jr));bd(ea,{size:9});var Wa=m(Sn,2);{var Bs=vn=>{var Cn=Q2(),ta=d(Cn),Ca=d(ta),Us=d(Ca);Kr(Us,{size:12,class:"animate-spin text-dl-primary-light"});var ai=m(Ca,2),wo=m(ta,2),pa=d(wo),Un=m(wo,2),si=d(Un);T(()=>{As(pa,`width: ${n($)??""}%`),z(si,n(P))}),he("click",ai,ue),c(vn,Cn)},Vs=vn=>{var Cn=ty(),ta=ae(Cn),Ca=d(ta),Us=m(Ca,2),ai=d(Us);lo(ai,{size:12});var wo=m(ta,2);Ie(wo,21,()=>Ee,Le,(pa,Un)=>{const si=O(()=>n(ar).some(hs=>hs===n(Un).name||hs===n(Un).name.split(":")[0]));var Il=Se(),Bu=ae(Il);{var Vu=hs=>{var oi=ey(),Al=d(oi),Ll=d(Al),Nl=d(Ll),Uu=d(Nl),Pl=m(Nl,2),Hu=d(Pl),qu=m(Pl,2);{var Ku=ii=>{var Ol=Z2(),Qu=d(Ol);T(()=>z(Qu,n(Un).tag)),c(ii,Ol)};C(qu,ii=>{n(Un).tag&&ii(Ku)})}var Wu=m(Ll,2),Gu=d(Wu),Yu=m(Al,2),Dl=d(Yu),Ju=d(Dl),Xu=m(Dl,2);lo(Xu,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),T(()=>{z(Uu,n(Un).name),z(Hu,n(Un).size),z(Gu,n(Un).desc),z(Ju,`${n(Un).gb??""} GB`)}),he("click",oi,()=>{v(Z,n(Un).name,!0),se()}),c(hs,oi)};C(Bu,hs=>{n(si)||hs(Vu)})}c(pa,Il)}),T(pa=>Us.disabled=pa,[()=>!n(Z).trim()]),he("keydown",Ca,pa=>{pa.key==="Enter"&&se()}),La(Ca,()=>n(Z),pa=>v(Z,pa)),he("click",Us,se),c(vn,Cn)};C(Wa,vn=>{n(ce)?vn(Bs):vn(Vs,-1)})}c(Sr,ir)};C(kn,Sr=>{Ue()==="ollama"&&Sr(Vn)})}c(xr,Dr)};C(Fu,xr=>{(Ze().available||n(or)||n(Lr))&&xr(ju)})}c(Mr,ln)};C(Iu,Mr=>{(n(yr)||n(Ft))&&Mr(Au)})}T((Mr,ln)=>{qe(hr,1,Mr),qe(nn,1,ln),z(qa,Ze().label||Ue()),z(Fs,Ze().desc||"")},[()=>gr(wr("rounded-xl border transition-all",n(Ft)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>gr(wr("w-2.5 h-2.5 rounded-full flex-shrink-0",Ze().available?"bg-dl-success":n(or)?"bg-amber-400":"bg-dl-text-dim"))]),he("click",Nr,()=>{Ze().available||n(or)?Ue()===n(l)?dr(Ue()):$t(Ue()):dr(Ue())}),c(Q,hr)});var It=m(ft,2),Yt=d(It),Kt=d(Yt);{var Wt=Q=>{var xe=oa();T(()=>{var je;return z(xe,`현재: ${(((je=n(o)[n(l)])==null?void 0:je.label)||n(l))??""} / ${n(u)??""}`)}),c(Q,xe)},ur=Q=>{var xe=oa();T(()=>{var je;return z(xe,`현재: ${(((je=n(o)[n(l)])==null?void 0:je.label)||n(l))??""}`)}),c(Q,xe)};C(Kt,Q=>{n(l)&&n(u)?Q(Wt):n(l)&&Q(ur,1)})}var kt=m(Yt,2);Jn(Ke,Q=>v(J,Q),()=>n(J)),he("click",ge,Q=>{Q.target===Q.currentTarget&&v(k,!1)}),he("click",Oe,()=>v(k,!1)),he("click",kt,()=>v(k,!1)),c(I,ge)};C(vr,I=>{n(k)&&I(Hr)})}var er=m(vr,2);{var mr=I=>{var ge=iy(),Ke=d(ge),Me=m(d(Ke),4),ye=d(Me),Oe=m(ye,2);Jn(Ke,Je=>v(me,Je),()=>n(me)),he("click",ge,Je=>{Je.target===Je.currentTarget&&v(H,null)}),he("click",ye,()=>v(H,null)),he("click",Oe,ke),c(I,ge)};C(er,I=>{n(H)&&I(mr)})}var pr=m(er,2);{var bn=I=>{const ge=O(()=>B.recentCompanies||[]);var Ke=py(),Me=d(Ke),ye=d(Me),Oe=d(ye);ga(Oe,{size:18,class:"text-dl-text-dim flex-shrink-0"});var Je=m(Oe,2);Jn(Je,Q=>v(G,Q),()=>n(G));var ft=m(ye,2),vt=d(ft);{var It=Q=>{var xe=dy(),je=m(ae(xe),2);Ie(je,17,()=>n(W),Le,(Ue,Ze,Ft)=>{var yr=ly(),or=d(yr),Lr=d(or),ar=m(or,2),tr=d(ar),hr=d(tr),Nr=m(tr,2),nn=d(Nr),Pr=m(ar,2),qr=m(d(Pr),2);En(qr,{size:14,class:"text-dl-text-dim"}),T((An,qa)=>{qe(yr,1,An),z(Lr,qa),z(hr,n(Ze).corpName),z(nn,`${n(Ze).stockCode??""} · ${(n(Ze).market||"")??""}${n(Ze).sector?` · ${n(Ze).sector}`:""}`)},[()=>gr(wr("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",Ft===n(ne)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(Ze).corpName||"?").charAt(0)]),he("click",yr,()=>{v(le,!1),v(we,""),v(W,[],!0),v(ne,-1),ie(n(Ze))}),gn("mouseenter",yr,()=>{v(ne,Ft,!0)}),c(Ue,yr)}),c(Q,xe)},Yt=Q=>{var xe=uy(),je=m(ae(xe),2);Ie(je,17,()=>n(ge),Le,(Ue,Ze,Ft)=>{var yr=cy(),or=d(yr),Lr=d(or),ar=m(or,2),tr=d(ar),hr=d(tr),Nr=m(tr,2),nn=d(Nr);T((Pr,qr)=>{qe(yr,1,Pr),z(Lr,qr),z(hr,n(Ze).corpName),z(nn,`${n(Ze).stockCode??""} · ${(n(Ze).market||"")??""}`)},[()=>gr(wr("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",Ft===n(ne)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(Ze).corpName||"?").charAt(0)]),he("click",yr,()=>{v(le,!1),v(we,""),v(ne,-1),ie(n(Ze))}),gn("mouseenter",yr,()=>{v(ne,Ft,!0)}),c(Ue,yr)}),c(Q,xe)},Kt=O(()=>n(we).trim().length===0&&n(ge).length>0),Wt=Q=>{var xe=fy();c(Q,xe)},ur=O(()=>n(we).trim().length>0),kt=Q=>{var xe=vy(),je=d(xe);ga(je,{size:24,class:"mb-2 opacity-40"}),c(Q,xe)};C(vt,Q=>{n(W).length>0?Q(It):n(Kt)?Q(Yt,1):n(ur)?Q(Wt,2):Q(kt,-1)})}he("click",Ke,Q=>{Q.target===Q.currentTarget&&v(le,!1)}),he("input",Je,()=>{A&&clearTimeout(A),n(we).trim().length>=1?A=setTimeout(async()=>{var Q;try{const xe=await gl(n(we).trim());v(W,((Q=xe.results)==null?void 0:Q.slice(0,8))||[],!0)}catch{v(W,[],!0)}},250):v(W,[],!0)}),he("keydown",Je,Q=>{const xe=n(W).length>0?n(W):n(ge);if(Q.key==="ArrowDown")Q.preventDefault(),v(ne,Math.min(n(ne)+1,xe.length-1),!0);else if(Q.key==="ArrowUp")Q.preventDefault(),v(ne,Math.max(n(ne)-1,-1),!0);else if(Q.key==="Enter"&&n(ne)>=0&&xe[n(ne)]){Q.preventDefault();const je=xe[n(ne)];v(le,!1),v(we,""),v(W,[],!0),v(ne,-1),ie(je)}else Q.key==="Escape"&&v(le,!1)}),La(Je,()=>n(we),Q=>v(we,Q)),c(I,Ke)};C(pr,I=>{n(le)&&I(bn)})}var sn=m(pr,2);{var In=I=>{var ge=hy(),Ke=d(ge),Me=d(Ke),ye=d(Me),Oe=m(Me,2),Je=d(Oe);Ba(Je,{size:14}),T(ft=>{qe(Ke,1,ft),z(ye,n(j))},[()=>gr(wr("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",n(K)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":n(K)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),he("click",Oe,()=>{v(_e,!1)}),c(I,ge)};C(sn,I=>{n(_e)&&I(In)})}T(I=>{qe(Ht,1,gr(n(q)?n(p)?"sidebar-mobile":"hidden":"")),qe(Tt,1,`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors ${B.activeView==="chat"?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-dim hover:text-dl-text-muted"}`),qe(cr,1,`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors ${B.activeView==="viewer"?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-dim hover:text-dl-text-muted"}`),qe(zt,1,I)},[()=>gr(wr("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",n(x)?"text-dl-text-dim":n(Ae)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),he("click",kr,y),he("click",Tt,()=>B.switchView("chat")),he("click",cr,()=>B.switchView("viewer")),he("click",Ve,St),he("click",zt,()=>fe()),c(t,wt),Ar()}Gr(["click","keydown","input"]);wv(xy,{target:document.getElementById("app")});export{Zi as C,Qi as _,Fe as a,c as b,Se as c,Ar as d,h as e,ae as f,d as g,Oi as h,C as i,Is as j,n as k,z as l,m,lr as n,Ie as o,Ir as p,Le as q,bo as r,qe as s,T as t,O as u,As as v};
