var _d=Object.defineProperty;var zo=e=>{throw TypeError(e)};var yd=(e,t,r)=>t in e?_d(e,t,{enumerable:!0,configurable:!0,writable:!0,value:r}):e[t]=r;var hr=(e,t,r)=>yd(e,typeof t!="symbol"?t+"":t,r),os=(e,t,r)=>t.has(e)||zo("Cannot "+r);var k=(e,t,r)=>(os(e,t,"read from private field"),r?r.call(e):t.get(e)),Pe=(e,t,r)=>t.has(e)?zo("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,r),_e=(e,t,r,n)=>(os(e,t,"write to private field"),n?n.call(e,r):t.set(e,r),r),_t=(e,t,r)=>(os(e,t,"access private method"),r);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const a of document.querySelectorAll('link[rel="modulepreload"]'))n(a);new MutationObserver(a=>{for(const i of a)if(i.type==="childList")for(const o of i.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&n(o)}).observe(document,{childList:!0,subtree:!0});function r(a){const i={};return a.integrity&&(i.integrity=a.integrity),a.referrerPolicy&&(i.referrerPolicy=a.referrerPolicy),a.crossOrigin==="use-credentials"?i.credentials="include":a.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function n(a){if(a.ep)return;a.ep=!0;const i=r(a);fetch(a.href,i)}})();const ps=!1;var Rs=Array.isArray,wd=Array.prototype.indexOf,Xn=Array.prototype.includes,Ka=Array.from,kd=Object.defineProperty,tn=Object.getOwnPropertyDescriptor,ci=Object.getOwnPropertyDescriptors,Sd=Object.prototype,zd=Array.prototype,js=Object.getPrototypeOf,Mo=Object.isExtensible;function ca(e){return typeof e=="function"}const Md=()=>{};function Ad(e){return e()}function ms(e){for(var t=0;t<e.length;t++)e[t]()}function ui(){var e,t,r=new Promise((n,a)=>{e=n,t=a});return{promise:r,resolve:e,reject:t}}function Va(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const r=[];for(const n of e)if(r.push(n),r.length===t)break;return r}const It=2,ra=4,Cn=8,Ya=1<<24,dn=16,wr=32,Nn=64,hs=128,dr=512,Pt=1024,Nt=2048,yr=4096,Vt=8192,$r=16384,na=32768,sn=65536,Ao=1<<17,Cd=1<<18,aa=1<<19,fi=1<<20,Pr=1<<25,En=65536,gs=1<<21,Ds=1<<22,rn=1<<23,Ir=Symbol("$state"),vi=Symbol("legacy props"),Ed=Symbol(""),xn=new class extends Error{constructor(){super(...arguments);hr(this,"name","StaleReactionError");hr(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var ii;const pi=!!((ii=globalThis.document)!=null&&ii.contentType)&&globalThis.document.contentType.includes("xml");function Td(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function Pd(e,t,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function Nd(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function $d(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Id(e){throw new Error("https://svelte.dev/e/effect_orphan")}function Ld(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function Od(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function Rd(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function jd(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function Dd(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function Fd(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const Bd=1,Vd=2,mi=4,Gd=8,Hd=16,Ud=1,Wd=2,hi=4,qd=8,Kd=16,Yd=1,Jd=2,zt=Symbol(),gi="http://www.w3.org/1999/xhtml",xi="http://www.w3.org/2000/svg",Xd="http://www.w3.org/1998/Math/MathML",Zd="@attach";function Qd(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function ec(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function bi(e){return e===this.v}function tc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function _i(e){return!tc(e,this.v)}let Ma=!1,rc=!1;function nc(){Ma=!0}let Mt=null;function Zn(e){Mt=e}function kr(e,t=!1,r){Mt={p:Mt,i:!1,c:null,e:null,s:e,x:null,l:Ma&&!t?{s:null,u:null,$:[]}:null}}function Sr(e){var t=Mt,r=t.e;if(r!==null){t.e=null;for(var n of r)Di(n)}return t.i=!0,Mt=t.p,{}}function Aa(){return!Ma||Mt!==null&&Mt.l===null}let bn=[];function yi(){var e=bn;bn=[],ms(e)}function Lr(e){if(bn.length===0&&!ha){var t=bn;queueMicrotask(()=>{t===bn&&yi()})}bn.push(e)}function ac(){for(;bn.length>0;)yi()}function wi(e){var t=ze;if(t===null)return Se.f|=rn,e;if((t.f&na)===0&&(t.f&ra)===0)throw e;Qr(e,t)}function Qr(e,t){for(;t!==null;){if((t.f&hs)!==0){if((t.f&na)===0)throw e;try{t.b.error(e);return}catch(r){e=r}}t=t.parent}throw e}const sc=-7169;function pt(e,t){e.f=e.f&sc|t}function Fs(e){(e.f&dr)!==0||e.deps===null?pt(e,Pt):pt(e,yr)}function ki(e){if(e!==null)for(const t of e)(t.f&It)===0||(t.f&En)===0||(t.f^=En,ki(t.deps))}function Si(e,t,r){(e.f&Nt)!==0?t.add(e):(e.f&yr)!==0&&r.add(e),ki(e.deps),pt(e,Pt)}const Ia=new Set;let ye=null,xs=null,Tt=null,Wt=[],Ja=null,ha=!1,Qn=null,oc=1;var Jr,Gn,wn,Hn,Un,Wn,Xr,Ar,qn,Yt,bs,_s,ys,ws;const ro=class ro{constructor(){Pe(this,Yt);hr(this,"id",oc++);hr(this,"current",new Map);hr(this,"previous",new Map);Pe(this,Jr,new Set);Pe(this,Gn,new Set);Pe(this,wn,0);Pe(this,Hn,0);Pe(this,Un,null);Pe(this,Wn,new Set);Pe(this,Xr,new Set);Pe(this,Ar,new Map);hr(this,"is_fork",!1);Pe(this,qn,!1)}skip_effect(t){k(this,Ar).has(t)||k(this,Ar).set(t,{d:[],m:[]})}unskip_effect(t){var r=k(this,Ar).get(t);if(r){k(this,Ar).delete(t);for(var n of r.d)pt(n,Nt),Nr(n);for(n of r.m)pt(n,yr),Nr(n)}}process(t){var a;Wt=[],this.apply();var r=Qn=[],n=[];for(const i of t)_t(this,Yt,_s).call(this,i,r,n);if(Qn=null,_t(this,Yt,bs).call(this)){_t(this,Yt,ys).call(this,n),_t(this,Yt,ys).call(this,r);for(const[i,o]of k(this,Ar))Ci(i,o)}else{xs=this,ye=null;for(const i of k(this,Jr))i(this);k(this,Jr).clear(),k(this,wn)===0&&_t(this,Yt,ws).call(this),Co(n),Co(r),k(this,Wn).clear(),k(this,Xr).clear(),xs=null,(a=k(this,Un))==null||a.resolve()}Tt=null}capture(t,r){r!==zt&&!this.previous.has(t)&&this.previous.set(t,r),(t.f&rn)===0&&(this.current.set(t,t.v),Tt==null||Tt.set(t,t.v))}activate(){ye=this,this.apply()}deactivate(){ye===this&&(ye=null,Tt=null)}flush(){var t;if(Wt.length>0)ye=this,zi();else if(k(this,wn)===0&&!this.is_fork){for(const r of k(this,Jr))r(this);k(this,Jr).clear(),_t(this,Yt,ws).call(this),(t=k(this,Un))==null||t.resolve()}this.deactivate()}discard(){for(const t of k(this,Gn))t(this);k(this,Gn).clear()}increment(t){_e(this,wn,k(this,wn)+1),t&&_e(this,Hn,k(this,Hn)+1)}decrement(t){_e(this,wn,k(this,wn)-1),t&&_e(this,Hn,k(this,Hn)-1),!k(this,qn)&&(_e(this,qn,!0),Lr(()=>{_e(this,qn,!1),_t(this,Yt,bs).call(this)?Wt.length>0&&this.flush():this.revive()}))}revive(){for(const t of k(this,Wn))k(this,Xr).delete(t),pt(t,Nt),Nr(t);for(const t of k(this,Xr))pt(t,yr),Nr(t);this.flush()}oncommit(t){k(this,Jr).add(t)}ondiscard(t){k(this,Gn).add(t)}settled(){return(k(this,Un)??_e(this,Un,ui())).promise}static ensure(){if(ye===null){const t=ye=new ro;Ia.add(ye),ha||Lr(()=>{ye===t&&t.flush()})}return ye}apply(){}};Jr=new WeakMap,Gn=new WeakMap,wn=new WeakMap,Hn=new WeakMap,Un=new WeakMap,Wn=new WeakMap,Xr=new WeakMap,Ar=new WeakMap,qn=new WeakMap,Yt=new WeakSet,bs=function(){return this.is_fork||k(this,Hn)>0},_s=function(t,r,n){t.f^=Pt;for(var a=t.first;a!==null;){var i=a.f,o=(i&(wr|Nn))!==0,l=o&&(i&Pt)!==0,d=(i&Vt)!==0,u=l||k(this,Ar).has(a);if(!u&&a.fn!==null){o?d||(a.f^=Pt):(i&ra)!==0?r.push(a):(i&(Cn|Ya))!==0&&d?n.push(a):Pa(a)&&(ta(a),(i&dn)!==0&&(k(this,Xr).add(a),d&&pt(a,Nt)));var v=a.first;if(v!==null){a=v;continue}}for(;a!==null;){var m=a.next;if(m!==null){a=m;break}a=a.parent}}},ys=function(t){for(var r=0;r<t.length;r+=1)Si(t[r],k(this,Wn),k(this,Xr))},ws=function(){var i;if(Ia.size>1){this.previous.clear();var t=ye,r=Tt,n=!0;for(const o of Ia){if(o===this){n=!1;continue}const l=[];for(const[u,v]of this.current){if(o.current.has(u))if(n&&v!==o.current.get(u))o.current.set(u,v);else continue;l.push(u)}if(l.length===0)continue;const d=[...o.current.keys()].filter(u=>!this.current.has(u));if(d.length>0){var a=Wt;Wt=[];const u=new Set,v=new Map;for(const m of l)Mi(m,d,u,v);if(Wt.length>0){ye=o,o.apply();for(const m of Wt)_t(i=o,Yt,_s).call(i,m,[],[]);o.deactivate()}Wt=a}}ye=t,Tt=r}k(this,Ar).clear(),Ia.delete(this)};let nn=ro;function ic(e){var t=ha;ha=!0;try{for(var r;;){if(ac(),Wt.length===0&&(ye==null||ye.flush(),Wt.length===0))return Ja=null,r;zi()}}finally{ha=t}}function zi(){var e=null;try{for(var t=0;Wt.length>0;){var r=nn.ensure();if(t++>1e3){var n,a;lc()}r.process(Wt),an.clear()}}finally{Wt=[],Ja=null,Qn=null}}function lc(){try{Ld()}catch(e){Qr(e,Ja)}}let gr=null;function Co(e){var t=e.length;if(t!==0){for(var r=0;r<t;){var n=e[r++];if((n.f&($r|Vt))===0&&Pa(n)&&(gr=new Set,ta(n),n.deps===null&&n.first===null&&n.nodes===null&&n.teardown===null&&n.ac===null&&Gi(n),(gr==null?void 0:gr.size)>0)){an.clear();for(const a of gr){if((a.f&($r|Vt))!==0)continue;const i=[a];let o=a.parent;for(;o!==null;)gr.has(o)&&(gr.delete(o),i.push(o)),o=o.parent;for(let l=i.length-1;l>=0;l--){const d=i[l];(d.f&($r|Vt))===0&&ta(d)}}gr.clear()}}gr=null}}function Mi(e,t,r,n){if(!r.has(e)&&(r.add(e),e.reactions!==null))for(const a of e.reactions){const i=a.f;(i&It)!==0?Mi(a,t,r,n):(i&(Ds|dn))!==0&&(i&Nt)===0&&Ai(a,t,n)&&(pt(a,Nt),Nr(a))}}function Ai(e,t,r){const n=r.get(e);if(n!==void 0)return n;if(e.deps!==null)for(const a of e.deps){if(Xn.call(t,a))return!0;if((a.f&It)!==0&&Ai(a,t,r))return r.set(a,!0),!0}return r.set(e,!1),!1}function Nr(e){var t=Ja=e,r=t.b;if(r!=null&&r.is_pending&&(e.f&(ra|Cn|Ya))!==0&&(e.f&na)===0){r.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var n=t.f;if(Qn!==null&&t===ze&&(e.f&Cn)===0)return;if((n&(Nn|wr))!==0){if((n&Pt)===0)return;t.f^=Pt}}Wt.push(t)}function Ci(e,t){if(!((e.f&wr)!==0&&(e.f&Pt)!==0)){(e.f&Nt)!==0?t.d.push(e):(e.f&yr)!==0&&t.m.push(e),pt(e,Pt);for(var r=e.first;r!==null;)Ci(r,t),r=r.next}}function dc(e){let t=0,r=on(0),n;return()=>{Hs()&&(s(r),Ws(()=>(t===0&&(n=Tn(()=>e(()=>xa(r)))),t+=1,()=>{Lr(()=>{t-=1,t===0&&(n==null||n(),n=void 0,xa(r))})})))}}var cc=sn|aa;function uc(e,t,r,n){new fc(e,t,r,n)}var lr,Os,Cr,kn,Ut,Er,Zt,xr,Fr,Sn,Zr,Kn,Yn,Jn,Br,Wa,kt,vc,pc,mc,ks,Da,Fa,Ss;class fc{constructor(t,r,n,a){Pe(this,kt);hr(this,"parent");hr(this,"is_pending",!1);hr(this,"transform_error");Pe(this,lr);Pe(this,Os,null);Pe(this,Cr);Pe(this,kn);Pe(this,Ut);Pe(this,Er,null);Pe(this,Zt,null);Pe(this,xr,null);Pe(this,Fr,null);Pe(this,Sn,0);Pe(this,Zr,0);Pe(this,Kn,!1);Pe(this,Yn,new Set);Pe(this,Jn,new Set);Pe(this,Br,null);Pe(this,Wa,dc(()=>(_e(this,Br,on(k(this,Sn))),()=>{_e(this,Br,null)})));var i;_e(this,lr,t),_e(this,Cr,r),_e(this,kn,o=>{var l=ze;l.b=this,l.f|=hs,n(o)}),this.parent=ze.b,this.transform_error=a??((i=this.parent)==null?void 0:i.transform_error)??(o=>o),_e(this,Ut,Ta(()=>{_t(this,kt,ks).call(this)},cc))}defer_effect(t){Si(t,k(this,Yn),k(this,Jn))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!k(this,Cr).pending}update_pending_count(t){_t(this,kt,Ss).call(this,t),_e(this,Sn,k(this,Sn)+t),!(!k(this,Br)||k(this,Kn))&&(_e(this,Kn,!0),Lr(()=>{_e(this,Kn,!1),k(this,Br)&&ea(k(this,Br),k(this,Sn))}))}get_effect_pending(){return k(this,Wa).call(this),s(k(this,Br))}error(t){var r=k(this,Cr).onerror;let n=k(this,Cr).failed;if(!r&&!n)throw t;k(this,Er)&&($t(k(this,Er)),_e(this,Er,null)),k(this,Zt)&&($t(k(this,Zt)),_e(this,Zt,null)),k(this,xr)&&($t(k(this,xr)),_e(this,xr,null));var a=!1,i=!1;const o=()=>{if(a){ec();return}a=!0,i&&Fd(),k(this,xr)!==null&&Mn(k(this,xr),()=>{_e(this,xr,null)}),_t(this,kt,Fa).call(this,()=>{nn.ensure(),_t(this,kt,ks).call(this)})},l=d=>{try{i=!0,r==null||r(d,o),i=!1}catch(u){Qr(u,k(this,Ut)&&k(this,Ut).parent)}n&&_e(this,xr,_t(this,kt,Fa).call(this,()=>{nn.ensure();try{return Kt(()=>{var u=ze;u.b=this,u.f|=hs,n(k(this,lr),()=>d,()=>o)})}catch(u){return Qr(u,k(this,Ut).parent),null}}))};Lr(()=>{var d;try{d=this.transform_error(t)}catch(u){Qr(u,k(this,Ut)&&k(this,Ut).parent);return}d!==null&&typeof d=="object"&&typeof d.then=="function"?d.then(l,u=>Qr(u,k(this,Ut)&&k(this,Ut).parent)):l(d)})}}lr=new WeakMap,Os=new WeakMap,Cr=new WeakMap,kn=new WeakMap,Ut=new WeakMap,Er=new WeakMap,Zt=new WeakMap,xr=new WeakMap,Fr=new WeakMap,Sn=new WeakMap,Zr=new WeakMap,Kn=new WeakMap,Yn=new WeakMap,Jn=new WeakMap,Br=new WeakMap,Wa=new WeakMap,kt=new WeakSet,vc=function(){try{_e(this,Er,Kt(()=>k(this,kn).call(this,k(this,lr))))}catch(t){this.error(t)}},pc=function(t){const r=k(this,Cr).failed;r&&_e(this,xr,Kt(()=>{r(k(this,lr),()=>t,()=>()=>{})}))},mc=function(){const t=k(this,Cr).pending;t&&(this.is_pending=!0,_e(this,Zt,Kt(()=>t(k(this,lr)))),Lr(()=>{var r=_e(this,Fr,document.createDocumentFragment()),n=Or();r.append(n),_e(this,Er,_t(this,kt,Fa).call(this,()=>(nn.ensure(),Kt(()=>k(this,kn).call(this,n))))),k(this,Zr)===0&&(k(this,lr).before(r),_e(this,Fr,null),Mn(k(this,Zt),()=>{_e(this,Zt,null)}),_t(this,kt,Da).call(this))}))},ks=function(){try{if(this.is_pending=this.has_pending_snippet(),_e(this,Zr,0),_e(this,Sn,0),_e(this,Er,Kt(()=>{k(this,kn).call(this,k(this,lr))})),k(this,Zr)>0){var t=_e(this,Fr,document.createDocumentFragment());Ys(k(this,Er),t);const r=k(this,Cr).pending;_e(this,Zt,Kt(()=>r(k(this,lr))))}else _t(this,kt,Da).call(this)}catch(r){this.error(r)}},Da=function(){this.is_pending=!1;for(const t of k(this,Yn))pt(t,Nt),Nr(t);for(const t of k(this,Jn))pt(t,yr),Nr(t);k(this,Yn).clear(),k(this,Jn).clear()},Fa=function(t){var r=ze,n=Se,a=Mt;fr(k(this,Ut)),ur(k(this,Ut)),Zn(k(this,Ut).ctx);try{return t()}catch(i){return wi(i),null}finally{fr(r),ur(n),Zn(a)}},Ss=function(t){var r;if(!this.has_pending_snippet()){this.parent&&_t(r=this.parent,kt,Ss).call(r,t);return}_e(this,Zr,k(this,Zr)+t),k(this,Zr)===0&&(_t(this,kt,Da).call(this),k(this,Zt)&&Mn(k(this,Zt),()=>{_e(this,Zt,null)}),k(this,Fr)&&(k(this,lr).before(k(this,Fr)),_e(this,Fr,null)))};function Ei(e,t,r,n){const a=Aa()?Ca:Bs;var i=e.filter(m=>!m.settled);if(r.length===0&&i.length===0){n(t.map(a));return}var o=ze,l=hc(),d=i.length===1?i[0].promise:i.length>1?Promise.all(i.map(m=>m.promise)):null;function u(m){l();try{n(m)}catch(b){(o.f&$r)===0&&Qr(b,o)}zs()}if(r.length===0){d.then(()=>u(t.map(a)));return}function v(){l(),Promise.all(r.map(m=>xc(m))).then(m=>u([...t.map(a),...m])).catch(m=>Qr(m,o))}d?d.then(v):v()}function hc(){var e=ze,t=Se,r=Mt,n=ye;return function(i=!0){fr(e),ur(t),Zn(r),i&&(n==null||n.activate())}}function zs(e=!0){fr(null),ur(null),Zn(null),e&&(ye==null||ye.deactivate())}function gc(){var e=ze.b,t=ye,r=e.is_rendered();return e.update_pending_count(1),t.increment(r),()=>{e.update_pending_count(-1),t.decrement(r)}}function Ca(e){var t=It|Nt,r=Se!==null&&(Se.f&It)!==0?Se:null;return ze!==null&&(ze.f|=aa),{ctx:Mt,deps:null,effects:null,equals:bi,f:t,fn:e,reactions:null,rv:0,v:zt,wv:0,parent:r??ze,ac:null}}function xc(e,t,r){ze===null&&Td();var a=void 0,i=on(zt),o=!Se,l=new Map;return $c(()=>{var b;var d=ui();a=d.promise;try{Promise.resolve(e()).then(d.resolve,d.reject).finally(zs)}catch(C){d.reject(C),zs()}var u=ye;if(o){var v=gc();(b=l.get(u))==null||b.reject(xn),l.delete(u),l.set(u,d)}const m=(C,S=void 0)=>{if(u.activate(),S)S!==xn&&(i.f|=rn,ea(i,S));else{(i.f&rn)!==0&&(i.f^=rn),ea(i,C);for(const[z,g]of l){if(l.delete(z),z===u)break;g.reject(xn)}}v&&v()};d.promise.then(m,C=>m(null,C||"unknown"))}),Za(()=>{for(const d of l.values())d.reject(xn)}),new Promise(d=>{function u(v){function m(){v===a?d(i):u(a)}v.then(m,m)}u(a)})}function pe(e){const t=Ca(e);return Wi(t),t}function Bs(e){const t=Ca(e);return t.equals=_i,t}function bc(e){var t=e.effects;if(t!==null){e.effects=null;for(var r=0;r<t.length;r+=1)$t(t[r])}}function _c(e){for(var t=e.parent;t!==null;){if((t.f&It)===0)return(t.f&$r)===0?t:null;t=t.parent}return null}function Vs(e){var t,r=ze;fr(_c(e));try{e.f&=~En,bc(e),t=Ji(e)}finally{fr(r)}return t}function Ti(e){var t=Vs(e);if(!e.equals(t)&&(e.wv=Ki(),(!(ye!=null&&ye.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){pt(e,Pt);return}ln||(Tt!==null?(Hs()||ye!=null&&ye.is_fork)&&Tt.set(e,t):Fs(e))}function yc(e){var t,r;if(e.effects!==null)for(const n of e.effects)(n.teardown||n.ac)&&((t=n.teardown)==null||t.call(n),(r=n.ac)==null||r.abort(xn),n.teardown=Md,n.ac=null,wa(n,0),qs(n))}function Pi(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&ta(t)}let Ms=new Set;const an=new Map;let Ni=!1;function on(e,t){var r={f:0,v:e,reactions:null,equals:bi,rv:0,wv:0};return r}function H(e,t){const r=on(e);return Wi(r),r}function wc(e,t=!1,r=!0){var a;const n=on(e);return t||(n.equals=_i),Ma&&r&&Mt!==null&&Mt.l!==null&&((a=Mt.l).s??(a.s=[])).push(n),n}function f(e,t,r=!1){Se!==null&&(!_r||(Se.f&Ao)!==0)&&Aa()&&(Se.f&(It|dn|Ds|Ao))!==0&&(cr===null||!Xn.call(cr,e))&&Dd();let n=r?wt(t):t;return ea(e,n)}function ea(e,t){if(!e.equals(t)){var r=e.v;ln?an.set(e,t):an.set(e,r),e.v=t;var n=nn.ensure();if(n.capture(e,r),(e.f&It)!==0){const a=e;(e.f&Nt)!==0&&Vs(a),Fs(a)}e.wv=Ki(),$i(e,Nt),Aa()&&ze!==null&&(ze.f&Pt)!==0&&(ze.f&(wr|Nn))===0&&(ir===null?Lc([e]):ir.push(e)),!n.is_fork&&Ms.size>0&&!Ni&&kc()}return t}function kc(){Ni=!1;for(const e of Ms)(e.f&Pt)!==0&&pt(e,yr),Pa(e)&&ta(e);Ms.clear()}function ga(e,t=1){var r=s(e),n=t===1?r++:r--;return f(e,r),n}function xa(e){f(e,e.v+1)}function $i(e,t){var r=e.reactions;if(r!==null)for(var n=Aa(),a=r.length,i=0;i<a;i++){var o=r[i],l=o.f;if(!(!n&&o===ze)){var d=(l&Nt)===0;if(d&&pt(o,t),(l&It)!==0){var u=o;Tt==null||Tt.delete(u),(l&En)===0&&(l&dr&&(o.f|=En),$i(u,yr))}else d&&((l&dn)!==0&&gr!==null&&gr.add(o),Nr(o))}}}function wt(e){if(typeof e!="object"||e===null||Ir in e)return e;const t=js(e);if(t!==Sd&&t!==zd)return e;var r=new Map,n=Rs(e),a=H(0),i=An,o=l=>{if(An===i)return l();var d=Se,u=An;ur(null),No(i);var v=l();return ur(d),No(u),v};return n&&r.set("length",H(e.length)),new Proxy(e,{defineProperty(l,d,u){(!("value"in u)||u.configurable===!1||u.enumerable===!1||u.writable===!1)&&Rd();var v=r.get(d);return v===void 0?o(()=>{var m=H(u.value);return r.set(d,m),m}):f(v,u.value,!0),!0},deleteProperty(l,d){var u=r.get(d);if(u===void 0){if(d in l){const v=o(()=>H(zt));r.set(d,v),xa(a)}}else f(u,zt),xa(a);return!0},get(l,d,u){var C;if(d===Ir)return e;var v=r.get(d),m=d in l;if(v===void 0&&(!m||(C=tn(l,d))!=null&&C.writable)&&(v=o(()=>{var S=wt(m?l[d]:zt),z=H(S);return z}),r.set(d,v)),v!==void 0){var b=s(v);return b===zt?void 0:b}return Reflect.get(l,d,u)},getOwnPropertyDescriptor(l,d){var u=Reflect.getOwnPropertyDescriptor(l,d);if(u&&"value"in u){var v=r.get(d);v&&(u.value=s(v))}else if(u===void 0){var m=r.get(d),b=m==null?void 0:m.v;if(m!==void 0&&b!==zt)return{enumerable:!0,configurable:!0,value:b,writable:!0}}return u},has(l,d){var b;if(d===Ir)return!0;var u=r.get(d),v=u!==void 0&&u.v!==zt||Reflect.has(l,d);if(u!==void 0||ze!==null&&(!v||(b=tn(l,d))!=null&&b.writable)){u===void 0&&(u=o(()=>{var C=v?wt(l[d]):zt,S=H(C);return S}),r.set(d,u));var m=s(u);if(m===zt)return!1}return v},set(l,d,u,v){var P;var m=r.get(d),b=d in l;if(n&&d==="length")for(var C=u;C<m.v;C+=1){var S=r.get(C+"");S!==void 0?f(S,zt):C in l&&(S=o(()=>H(zt)),r.set(C+"",S))}if(m===void 0)(!b||(P=tn(l,d))!=null&&P.writable)&&(m=o(()=>H(void 0)),f(m,wt(u)),r.set(d,m));else{b=m.v!==zt;var z=o(()=>wt(u));f(m,z)}var g=Reflect.getOwnPropertyDescriptor(l,d);if(g!=null&&g.set&&g.set.call(v,u),!b){if(n&&typeof d=="string"){var A=r.get("length"),E=Number(d);Number.isInteger(E)&&E>=A.v&&f(A,E+1)}xa(a)}return!0},ownKeys(l){s(a);var d=Reflect.ownKeys(l).filter(m=>{var b=r.get(m);return b===void 0||b.v!==zt});for(var[u,v]of r)v.v!==zt&&!(u in l)&&d.push(u);return d},setPrototypeOf(){jd()}})}function Eo(e){try{if(e!==null&&typeof e=="object"&&Ir in e)return e[Ir]}catch{}return e}function Sc(e,t){return Object.is(Eo(e),Eo(t))}var As,Ii,Li,Oi;function zc(){if(As===void 0){As=window,Ii=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,r=Text.prototype;Li=tn(t,"firstChild").get,Oi=tn(t,"nextSibling").get,Mo(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Mo(r)&&(r.__t=void 0)}}function Or(e=""){return document.createTextNode(e)}function Vr(e){return Li.call(e)}function Ea(e){return Oi.call(e)}function c(e,t){return Vr(e)}function q(e,t=!1){{var r=Vr(e);return r instanceof Comment&&r.data===""?Ea(r):r}}function h(e,t=1,r=!1){let n=e;for(;t--;)n=Ea(n);return n}function Mc(e){e.textContent=""}function Ri(){return!1}function Gs(e,t,r){return document.createElementNS(t??gi,e,void 0)}function Ac(e,t){if(t){const r=document.body;e.autofocus=!0,Lr(()=>{document.activeElement===r&&e.focus()})}}let To=!1;function Cc(){To||(To=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const r of e.target.elements)(t=r.__on_r)==null||t.call(r)})},{capture:!0}))}function Xa(e){var t=Se,r=ze;ur(null),fr(null);try{return e()}finally{ur(t),fr(r)}}function Ec(e,t,r,n=r){e.addEventListener(t,()=>Xa(r));const a=e.__on_r;a?e.__on_r=()=>{a(),n(!0)}:e.__on_r=()=>n(!0),Cc()}function ji(e){ze===null&&(Se===null&&Id(),$d()),ln&&Nd()}function Tc(e,t){var r=t.last;r===null?t.last=t.first=e:(r.next=e,e.prev=r,t.last=e)}function zr(e,t){var r=ze;r!==null&&(r.f&Vt)!==0&&(e|=Vt);var n={ctx:Mt,deps:null,nodes:null,f:e|Nt|dr,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},a=n;if((e&ra)!==0)Qn!==null?Qn.push(n):Nr(n);else if(t!==null){try{ta(n)}catch(o){throw $t(n),o}a.deps===null&&a.teardown===null&&a.nodes===null&&a.first===a.last&&(a.f&aa)===0&&(a=a.first,(e&dn)!==0&&(e&sn)!==0&&a!==null&&(a.f|=sn))}if(a!==null&&(a.parent=r,r!==null&&Tc(a,r),Se!==null&&(Se.f&It)!==0&&(e&Nn)===0)){var i=Se;(i.effects??(i.effects=[])).push(a)}return n}function Hs(){return Se!==null&&!_r}function Za(e){const t=zr(Cn,null);return pt(t,Pt),t.teardown=e,t}function ya(e){ji();var t=ze.f,r=!Se&&(t&wr)!==0&&(t&na)===0;if(r){var n=Mt;(n.e??(n.e=[])).push(e)}else return Di(e)}function Di(e){return zr(ra|fi,e)}function Pc(e){return ji(),zr(Cn|fi,e)}function Nc(e){nn.ensure();const t=zr(Nn|aa,e);return(r={})=>new Promise(n=>{r.outro?Mn(t,()=>{$t(t),n(void 0)}):($t(t),n(void 0))})}function Us(e){return zr(ra,e)}function $c(e){return zr(Ds|aa,e)}function Ws(e,t=0){return zr(Cn|t,e)}function D(e,t=[],r=[],n=[]){Ei(n,t,r,a=>{zr(Cn,()=>e(...a.map(s)))})}function Ta(e,t=0){var r=zr(dn|t,e);return r}function Fi(e,t=0){var r=zr(Ya|t,e);return r}function Kt(e){return zr(wr|aa,e)}function Bi(e){var t=e.teardown;if(t!==null){const r=ln,n=Se;Po(!0),ur(null);try{t.call(null)}finally{Po(r),ur(n)}}}function qs(e,t=!1){var r=e.first;for(e.first=e.last=null;r!==null;){const a=r.ac;a!==null&&Xa(()=>{a.abort(xn)});var n=r.next;(r.f&Nn)!==0?r.parent=null:$t(r,t),r=n}}function Ic(e){for(var t=e.first;t!==null;){var r=t.next;(t.f&wr)===0&&$t(t),t=r}}function $t(e,t=!0){var r=!1;(t||(e.f&Cd)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(Vi(e.nodes.start,e.nodes.end),r=!0),qs(e,t&&!r),wa(e,0),pt(e,$r);var n=e.nodes&&e.nodes.t;if(n!==null)for(const i of n)i.stop();Bi(e);var a=e.parent;a!==null&&a.first!==null&&Gi(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function Vi(e,t){for(;e!==null;){var r=e===t?null:Ea(e);e.remove(),e=r}}function Gi(e){var t=e.parent,r=e.prev,n=e.next;r!==null&&(r.next=n),n!==null&&(n.prev=r),t!==null&&(t.first===e&&(t.first=n),t.last===e&&(t.last=r))}function Mn(e,t,r=!0){var n=[];Hi(e,n,!0);var a=()=>{r&&$t(e),t&&t()},i=n.length;if(i>0){var o=()=>--i||a();for(var l of n)l.out(o)}else a()}function Hi(e,t,r){if((e.f&Vt)===0){e.f^=Vt;var n=e.nodes&&e.nodes.t;if(n!==null)for(const l of n)(l.is_global||r)&&t.push(l);for(var a=e.first;a!==null;){var i=a.next,o=(a.f&sn)!==0||(a.f&wr)!==0&&(e.f&dn)!==0;Hi(a,t,o?r:!1),a=i}}}function Ks(e){Ui(e,!0)}function Ui(e,t){if((e.f&Vt)!==0){e.f^=Vt;for(var r=e.first;r!==null;){var n=r.next,a=(r.f&sn)!==0||(r.f&wr)!==0;Ui(r,a?t:!1),r=n}var i=e.nodes&&e.nodes.t;if(i!==null)for(const o of i)(o.is_global||t)&&o.in()}}function Ys(e,t){if(e.nodes)for(var r=e.nodes.start,n=e.nodes.end;r!==null;){var a=r===n?null:Ea(r);t.append(r),r=a}}let Ba=!1,ln=!1;function Po(e){ln=e}let Se=null,_r=!1;function ur(e){Se=e}let ze=null;function fr(e){ze=e}let cr=null;function Wi(e){Se!==null&&(cr===null?cr=[e]:cr.push(e))}let qt=null,Xt=0,ir=null;function Lc(e){ir=e}let qi=1,_n=0,An=_n;function No(e){An=e}function Ki(){return++qi}function Pa(e){var t=e.f;if((t&Nt)!==0)return!0;if(t&It&&(e.f&=~En),(t&yr)!==0){for(var r=e.deps,n=r.length,a=0;a<n;a++){var i=r[a];if(Pa(i)&&Ti(i),i.wv>e.wv)return!0}(t&dr)!==0&&Tt===null&&pt(e,Pt)}return!1}function Yi(e,t,r=!0){var n=e.reactions;if(n!==null&&!(cr!==null&&Xn.call(cr,e)))for(var a=0;a<n.length;a++){var i=n[a];(i.f&It)!==0?Yi(i,t,!1):t===i&&(r?pt(i,Nt):(i.f&Pt)!==0&&pt(i,yr),Nr(i))}}function Ji(e){var z;var t=qt,r=Xt,n=ir,a=Se,i=cr,o=Mt,l=_r,d=An,u=e.f;qt=null,Xt=0,ir=null,Se=(u&(wr|Nn))===0?e:null,cr=null,Zn(e.ctx),_r=!1,An=++_n,e.ac!==null&&(Xa(()=>{e.ac.abort(xn)}),e.ac=null);try{e.f|=gs;var v=e.fn,m=v();e.f|=na;var b=e.deps,C=ye==null?void 0:ye.is_fork;if(qt!==null){var S;if(C||wa(e,Xt),b!==null&&Xt>0)for(b.length=Xt+qt.length,S=0;S<qt.length;S++)b[Xt+S]=qt[S];else e.deps=b=qt;if(Hs()&&(e.f&dr)!==0)for(S=Xt;S<b.length;S++)((z=b[S]).reactions??(z.reactions=[])).push(e)}else!C&&b!==null&&Xt<b.length&&(wa(e,Xt),b.length=Xt);if(Aa()&&ir!==null&&!_r&&b!==null&&(e.f&(It|yr|Nt))===0)for(S=0;S<ir.length;S++)Yi(ir[S],e);if(a!==null&&a!==e){if(_n++,a.deps!==null)for(let g=0;g<r;g+=1)a.deps[g].rv=_n;if(t!==null)for(const g of t)g.rv=_n;ir!==null&&(n===null?n=ir:n.push(...ir))}return(e.f&rn)!==0&&(e.f^=rn),m}catch(g){return wi(g)}finally{e.f^=gs,qt=t,Xt=r,ir=n,Se=a,cr=i,Zn(o),_r=l,An=d}}function Oc(e,t){let r=t.reactions;if(r!==null){var n=wd.call(r,e);if(n!==-1){var a=r.length-1;a===0?r=t.reactions=null:(r[n]=r[a],r.pop())}}if(r===null&&(t.f&It)!==0&&(qt===null||!Xn.call(qt,t))){var i=t;(i.f&dr)!==0&&(i.f^=dr,i.f&=~En),Fs(i),yc(i),wa(i,0)}}function wa(e,t){var r=e.deps;if(r!==null)for(var n=t;n<r.length;n++)Oc(e,r[n])}function ta(e){var t=e.f;if((t&$r)===0){pt(e,Pt);var r=ze,n=Ba;ze=e,Ba=!0;try{(t&(dn|Ya))!==0?Ic(e):qs(e),Bi(e);var a=Ji(e);e.teardown=typeof a=="function"?a:null,e.wv=qi;var i;ps&&rc&&(e.f&Nt)!==0&&e.deps}finally{Ba=n,ze=r}}}async function Rc(){await Promise.resolve(),ic()}function s(e){var t=e.f,r=(t&It)!==0;if(Se!==null&&!_r){var n=ze!==null&&(ze.f&$r)!==0;if(!n&&(cr===null||!Xn.call(cr,e))){var a=Se.deps;if((Se.f&gs)!==0)e.rv<_n&&(e.rv=_n,qt===null&&a!==null&&a[Xt]===e?Xt++:qt===null?qt=[e]:qt.push(e));else{(Se.deps??(Se.deps=[])).push(e);var i=e.reactions;i===null?e.reactions=[Se]:Xn.call(i,Se)||i.push(Se)}}}if(ln&&an.has(e))return an.get(e);if(r){var o=e;if(ln){var l=o.v;return((o.f&Pt)===0&&o.reactions!==null||Zi(o))&&(l=Vs(o)),an.set(o,l),l}var d=(o.f&dr)===0&&!_r&&Se!==null&&(Ba||(Se.f&dr)!==0),u=(o.f&na)===0;Pa(o)&&(d&&(o.f|=dr),Ti(o)),d&&!u&&(Pi(o),Xi(o))}if(Tt!=null&&Tt.has(e))return Tt.get(e);if((e.f&rn)!==0)throw e.v;return e.v}function Xi(e){if(e.f|=dr,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&It)!==0&&(t.f&dr)===0&&(Pi(t),Xi(t))}function Zi(e){if(e.v===zt)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(an.has(t)||(t.f&It)!==0&&Zi(t))return!0;return!1}function Tn(e){var t=_r;try{return _r=!0,e()}finally{_r=t}}function gn(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(Ir in e)Cs(e);else if(!Array.isArray(e))for(let t in e){const r=e[t];typeof r=="object"&&r&&Ir in r&&Cs(r)}}}function Cs(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let n in e)try{Cs(e[n],t)}catch{}const r=js(e);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const n=ci(r);for(let a in n){const i=n[a].get;if(i)try{i.call(e)}catch{}}}}}function jc(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const Dc=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function Fc(e){return Dc.includes(e)}const Bc={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function Vc(e){return e=e.toLowerCase(),Bc[e]??e}const Gc=["touchstart","touchmove"];function Hc(e){return Gc.includes(e)}const yn=Symbol("events"),Qi=new Set,Es=new Set;function el(e,t,r,n={}){function a(i){if(n.capture||Ts.call(t,i),!i.cancelBubble)return Xa(()=>r==null?void 0:r.call(this,i))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Lr(()=>{t.addEventListener(e,a,n)}):t.addEventListener(e,a,n),a}function Ga(e,t,r,n,a){var i={capture:n,passive:a},o=el(e,t,r,i);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&Za(()=>{t.removeEventListener(e,o,i)})}function W(e,t,r){(t[yn]??(t[yn]={}))[e]=r}function cn(e){for(var t=0;t<e.length;t++)Qi.add(e[t]);for(var r of Es)r(e)}let $o=null;function Ts(e){var g,A;var t=this,r=t.ownerDocument,n=e.type,a=((g=e.composedPath)==null?void 0:g.call(e))||[],i=a[0]||e.target;$o=e;var o=0,l=$o===e&&e[yn];if(l){var d=a.indexOf(l);if(d!==-1&&(t===document||t===window)){e[yn]=t;return}var u=a.indexOf(t);if(u===-1)return;d<=u&&(o=d)}if(i=a[o]||e.target,i!==t){kd(e,"currentTarget",{configurable:!0,get(){return i||r}});var v=Se,m=ze;ur(null),fr(null);try{for(var b,C=[];i!==null;){var S=i.assignedSlot||i.parentNode||i.host||null;try{var z=(A=i[yn])==null?void 0:A[n];z!=null&&(!i.disabled||e.target===i)&&z.call(i,e)}catch(E){b?C.push(E):b=E}if(e.cancelBubble||S===t||S===null)break;i=S}if(b){for(let E of C)queueMicrotask(()=>{throw E});throw b}}finally{e[yn]=t,delete e.currentTarget,ur(v),fr(m)}}}var li;const is=((li=globalThis==null?void 0:globalThis.window)==null?void 0:li.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function Uc(e){return(is==null?void 0:is.createHTML(e))??e}function tl(e){var t=Gs("template");return t.innerHTML=Uc(e.replaceAll("<!>","<!---->")),t.content}function Pn(e,t){var r=ze;r.nodes===null&&(r.nodes={start:e,end:t,a:null,t:null})}function w(e,t){var r=(t&Yd)!==0,n=(t&Jd)!==0,a,i=!e.startsWith("<!>");return()=>{a===void 0&&(a=tl(i?e:"<!>"+e),r||(a=Vr(a)));var o=n||Ii?document.importNode(a,!0):a.cloneNode(!0);if(r){var l=Vr(o),d=o.lastChild;Pn(l,d)}else Pn(o,o);return o}}function Wc(e,t,r="svg"){var n=!e.startsWith("<!>"),a=`<${r}>${n?e:"<!>"+e}</${r}>`,i;return()=>{if(!i){var o=tl(a),l=Vr(o);i=Vr(l)}var d=i.cloneNode(!0);return Pn(d,d),d}}function qc(e,t){return Wc(e,t,"svg")}function ba(e=""){{var t=Or(e+"");return Pn(t,t),t}}function xe(){var e=document.createDocumentFragment(),t=document.createComment(""),r=Or();return e.append(t,r),Pn(t,r),e}function p(e,t){e!==null&&e.before(t)}function B(e,t){var r=t==null?"":typeof t=="object"?`${t}`:t;r!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=r,e.nodeValue=`${r}`)}function Kc(e,t){return Yc(e,t)}const La=new Map;function Yc(e,{target:t,anchor:r,props:n={},events:a,context:i,intro:o=!0,transformError:l}){zc();var d=void 0,u=Nc(()=>{var v=r??t.appendChild(Or());uc(v,{pending:()=>{}},C=>{kr({});var S=Mt;i&&(S.c=i),a&&(n.$$events=a),d=e(C,n)||{},Sr()},l);var m=new Set,b=C=>{for(var S=0;S<C.length;S++){var z=C[S];if(!m.has(z)){m.add(z);var g=Hc(z);for(const P of[t,document]){var A=La.get(P);A===void 0&&(A=new Map,La.set(P,A));var E=A.get(z);E===void 0?(P.addEventListener(z,Ts,{passive:g}),A.set(z,1)):A.set(z,E+1)}}}};return b(Ka(Qi)),Es.add(b),()=>{var g;for(var C of m)for(const A of[t,document]){var S=La.get(A),z=S.get(C);--z==0?(A.removeEventListener(C,Ts),S.delete(C),S.size===0&&La.delete(A)):S.set(C,z)}Es.delete(b),v!==r&&((g=v.parentNode)==null||g.removeChild(v))}});return Jc.set(d,u),d}let Jc=new WeakMap;var br,Tr,Qt,zn,Sa,za,qa;class Js{constructor(t,r=!0){hr(this,"anchor");Pe(this,br,new Map);Pe(this,Tr,new Map);Pe(this,Qt,new Map);Pe(this,zn,new Set);Pe(this,Sa,!0);Pe(this,za,t=>{if(k(this,br).has(t)){var r=k(this,br).get(t),n=k(this,Tr).get(r);if(n)Ks(n),k(this,zn).delete(r);else{var a=k(this,Qt).get(r);a&&(a.effect.f&Vt)===0&&(k(this,Tr).set(r,a.effect),k(this,Qt).delete(r),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),n=a.effect)}for(const[i,o]of k(this,br)){if(k(this,br).delete(i),i===t)break;const l=k(this,Qt).get(o);l&&($t(l.effect),k(this,Qt).delete(o))}for(const[i,o]of k(this,Tr)){if(i===r||k(this,zn).has(i)||(o.f&Vt)!==0)continue;const l=()=>{if(Array.from(k(this,br).values()).includes(i)){var u=document.createDocumentFragment();Ys(o,u),u.append(Or()),k(this,Qt).set(i,{effect:o,fragment:u})}else $t(o);k(this,zn).delete(i),k(this,Tr).delete(i)};k(this,Sa)||!n?(k(this,zn).add(i),Mn(o,l,!1)):l()}}});Pe(this,qa,t=>{k(this,br).delete(t);const r=Array.from(k(this,br).values());for(const[n,a]of k(this,Qt))r.includes(n)||($t(a.effect),k(this,Qt).delete(n))});this.anchor=t,_e(this,Sa,r)}ensure(t,r){var n=ye,a=Ri();if(r&&!k(this,Tr).has(t)&&!k(this,Qt).has(t))if(a){var i=document.createDocumentFragment(),o=Or();i.append(o),k(this,Qt).set(t,{effect:Kt(()=>r(o)),fragment:i})}else k(this,Tr).set(t,Kt(()=>r(this.anchor)));if(k(this,br).set(n,t),a){for(const[l,d]of k(this,Tr))l===t?n.unskip_effect(d):n.skip_effect(d);for(const[l,d]of k(this,Qt))l===t?n.unskip_effect(d.effect):n.skip_effect(d.effect);n.oncommit(k(this,za)),n.ondiscard(k(this,qa))}else k(this,za).call(this,n)}}br=new WeakMap,Tr=new WeakMap,Qt=new WeakMap,zn=new WeakMap,Sa=new WeakMap,za=new WeakMap,qa=new WeakMap;function T(e,t,r=!1){var n=new Js(e),a=r?sn:0;function i(o,l){n.ensure(o,l)}Ta(()=>{var o=!1;t((l,d=0)=>{o=!0,i(d,l)}),o||i(-1,null)},a)}function ot(e,t){return t}function Xc(e,t,r){for(var n=[],a=t.length,i,o=t.length,l=0;l<a;l++){let m=t[l];Mn(m,()=>{if(i){if(i.pending.delete(m),i.done.add(m),i.pending.size===0){var b=e.outrogroups;Ps(e,Ka(i.done)),b.delete(i),b.size===0&&(e.outrogroups=null)}}else o-=1},!1)}if(o===0){var d=n.length===0&&r!==null;if(d){var u=r,v=u.parentNode;Mc(v),v.append(u),e.items.clear()}Ps(e,t,!d)}else i={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(i)}function Ps(e,t,r=!0){var n;if(e.pending.size>0){n=new Set;for(const o of e.pending.values())for(const l of o)n.add(e.items.get(l).e)}for(var a=0;a<t.length;a++){var i=t[a];if(n!=null&&n.has(i)){i.f|=Pr;const o=document.createDocumentFragment();Ys(i,o)}else $t(t[a],r)}}var Io;function it(e,t,r,n,a,i=null){var o=e,l=new Map,d=(t&mi)!==0;if(d){var u=e;o=u.appendChild(Or())}var v=null,m=Bs(()=>{var P=r();return Rs(P)?P:P==null?[]:Ka(P)}),b,C=new Map,S=!0;function z(P){(E.effect.f&$r)===0&&(E.pending.delete(P),E.fallback=v,Zc(E,b,o,t,n),v!==null&&(b.length===0?(v.f&Pr)===0?Ks(v):(v.f^=Pr,ma(v,null,o)):Mn(v,()=>{v=null})))}function g(P){E.pending.delete(P)}var A=Ta(()=>{b=s(m);for(var P=b.length,M=new Set,L=ye,Q=Ri(),K=0;K<P;K+=1){var x=b[K],R=n(x,K),Y=S?null:l.get(R);Y?(Y.v&&ea(Y.v,x),Y.i&&ea(Y.i,K),Q&&L.unskip_effect(Y.e)):(Y=Qc(l,S?o:Io??(Io=Or()),x,R,K,a,t,r),S||(Y.e.f|=Pr),l.set(R,Y)),M.add(R)}if(P===0&&i&&!v&&(S?v=Kt(()=>i(o)):(v=Kt(()=>i(Io??(Io=Or()))),v.f|=Pr)),P>M.size&&Pd(),!S)if(C.set(L,M),Q){for(const[fe,Ae]of l)M.has(fe)||L.skip_effect(Ae.e);L.oncommit(z),L.ondiscard(g)}else z(L);s(m)}),E={effect:A,items:l,pending:C,outrogroups:null,fallback:v};S=!1}function ua(e){for(;e!==null&&(e.f&wr)===0;)e=e.next;return e}function Zc(e,t,r,n,a){var Y,fe,Ae,He,N,O,ee,de,ue;var i=(n&Gd)!==0,o=t.length,l=e.items,d=ua(e.effect.first),u,v=null,m,b=[],C=[],S,z,g,A;if(i)for(A=0;A<o;A+=1)S=t[A],z=a(S,A),g=l.get(z).e,(g.f&Pr)===0&&((fe=(Y=g.nodes)==null?void 0:Y.a)==null||fe.measure(),(m??(m=new Set)).add(g));for(A=0;A<o;A+=1){if(S=t[A],z=a(S,A),g=l.get(z).e,e.outrogroups!==null)for(const V of e.outrogroups)V.pending.delete(g),V.done.delete(g);if((g.f&Pr)!==0)if(g.f^=Pr,g===d)ma(g,null,r);else{var E=v?v.next:d;g===e.effect.last&&(e.effect.last=g.prev),g.prev&&(g.prev.next=g.next),g.next&&(g.next.prev=g.prev),qr(e,v,g),qr(e,g,E),ma(g,E,r),v=g,b=[],C=[],d=ua(v.next);continue}if((g.f&Vt)!==0&&(Ks(g),i&&((He=(Ae=g.nodes)==null?void 0:Ae.a)==null||He.unfix(),(m??(m=new Set)).delete(g))),g!==d){if(u!==void 0&&u.has(g)){if(b.length<C.length){var P=C[0],M;v=P.prev;var L=b[0],Q=b[b.length-1];for(M=0;M<b.length;M+=1)ma(b[M],P,r);for(M=0;M<C.length;M+=1)u.delete(C[M]);qr(e,L.prev,Q.next),qr(e,v,L),qr(e,Q,P),d=P,v=Q,A-=1,b=[],C=[]}else u.delete(g),ma(g,d,r),qr(e,g.prev,g.next),qr(e,g,v===null?e.effect.first:v.next),qr(e,v,g),v=g;continue}for(b=[],C=[];d!==null&&d!==g;)(u??(u=new Set)).add(d),C.push(d),d=ua(d.next);if(d===null)continue}(g.f&Pr)===0&&b.push(g),v=g,d=ua(g.next)}if(e.outrogroups!==null){for(const V of e.outrogroups)V.pending.size===0&&(Ps(e,Ka(V.done)),(N=e.outrogroups)==null||N.delete(V));e.outrogroups.size===0&&(e.outrogroups=null)}if(d!==null||u!==void 0){var K=[];if(u!==void 0)for(g of u)(g.f&Vt)===0&&K.push(g);for(;d!==null;)(d.f&Vt)===0&&d!==e.fallback&&K.push(d),d=ua(d.next);var x=K.length;if(x>0){var R=(n&mi)!==0&&o===0?r:null;if(i){for(A=0;A<x;A+=1)(ee=(O=K[A].nodes)==null?void 0:O.a)==null||ee.measure();for(A=0;A<x;A+=1)(ue=(de=K[A].nodes)==null?void 0:de.a)==null||ue.fix()}Xc(e,K,R)}}i&&Lr(()=>{var V,y;if(m!==void 0)for(g of m)(y=(V=g.nodes)==null?void 0:V.a)==null||y.apply()})}function Qc(e,t,r,n,a,i,o,l){var d=(o&Bd)!==0?(o&Hd)===0?wc(r,!1,!1):on(r):null,u=(o&Vd)!==0?on(a):null;return{v:d,i:u,e:Kt(()=>(i(t,d??r,u??a,l),()=>{e.delete(n)}))}}function ma(e,t,r){if(e.nodes)for(var n=e.nodes.start,a=e.nodes.end,i=t&&(t.f&Pr)===0?t.nodes.start:r;n!==null;){var o=Ea(n);if(i.before(n),n===a)return;n=o}}function qr(e,t,r){t===null?e.effect.first=r:t.next=r,r===null?e.effect.last=t:r.prev=t}function Lo(e,t,r=!1,n=!1,a=!1){var i=e,o="";D(()=>{var l=ze;if(o!==(o=t()??"")&&(l.nodes!==null&&(Vi(l.nodes.start,l.nodes.end),l.nodes=null),o!=="")){var d=r?xi:n?Xd:void 0,u=Gs(r?"svg":n?"math":"template",d);u.innerHTML=o;var v=r||n?u:u.content;if(Pn(Vr(v),v.lastChild),r||n)for(;Vr(v);)i.before(Vr(v));else i.before(v)}})}function Ne(e,t,r,n,a){var l;var i=(l=t.$$slots)==null?void 0:l[r],o=!1;i===!0&&(i=t.children,o=!0),i===void 0||i(e,o?()=>n:n)}function Ns(e,t,...r){var n=new Js(e);Ta(()=>{const a=t()??null;n.ensure(a,a&&(i=>a(i,...r)))},sn)}function eu(e,t,r,n,a,i){var o=null,l=e,d=new Js(l,!1);Ta(()=>{const u=t()||null;var v=xi;if(u===null){d.ensure(null,null);return}return d.ensure(u,m=>{if(u){if(o=Gs(u,v),Pn(o,o),n){var b=o.appendChild(Or());n(o,b)}ze.nodes.end=o,m.before(o)}}),()=>{}},sn),Za(()=>{})}function tu(e,t){var r=void 0,n;Fi(()=>{r!==(r=t())&&(n&&($t(n),n=null),r&&(n=Kt(()=>{Us(()=>r(e))})))})}function rl(e){var t,r,n="";if(typeof e=="string"||typeof e=="number")n+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(r=rl(e[t]))&&(n&&(n+=" "),n+=r)}else for(r in e)e[r]&&(n&&(n+=" "),n+=r);return n}function nl(){for(var e,t,r=0,n="",a=arguments.length;r<a;r++)(e=arguments[r])&&(t=rl(e))&&(n&&(n+=" "),n+=t);return n}function et(e){return typeof e=="object"?nl(e):e??""}const Oo=[...` 	
\r\f \v\uFEFF`];function ru(e,t,r){var n=e==null?"":""+e;if(r){for(var a of Object.keys(r))if(r[a])n=n?n+" "+a:a;else if(n.length)for(var i=a.length,o=0;(o=n.indexOf(a,o))>=0;){var l=o+i;(o===0||Oo.includes(n[o-1]))&&(l===n.length||Oo.includes(n[l]))?n=(o===0?"":n.substring(0,o))+n.substring(l+1):o=l}}return n===""?null:n}function Ro(e,t=!1){var r=t?" !important;":";",n="";for(var a of Object.keys(e)){var i=e[a];i!=null&&i!==""&&(n+=" "+a+": "+i+r)}return n}function ls(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function nu(e,t){if(t){var r="",n,a;if(Array.isArray(t)?(n=t[0],a=t[1]):n=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var i=!1,o=0,l=!1,d=[];n&&d.push(...Object.keys(n).map(ls)),a&&d.push(...Object.keys(a).map(ls));var u=0,v=-1;const z=e.length;for(var m=0;m<z;m++){var b=e[m];if(l?b==="/"&&e[m-1]==="*"&&(l=!1):i?i===b&&(i=!1):b==="/"&&e[m+1]==="*"?l=!0:b==='"'||b==="'"?i=b:b==="("?o++:b===")"&&o--,!l&&i===!1&&o===0){if(b===":"&&v===-1)v=m;else if(b===";"||m===z-1){if(v!==-1){var C=ls(e.substring(u,v).trim());if(!d.includes(C)){b!==";"&&m++;var S=e.substring(u,m).trim();r+=" "+S+";"}}u=m+1,v=-1}}}}return n&&(r+=Ro(n)),a&&(r+=Ro(a,!0)),r=r.trim(),r===""?null:r}return e==null?null:String(e)}function tt(e,t,r,n,a,i){var o=e.__className;if(o!==r||o===void 0){var l=ru(r,n,i);l==null?e.removeAttribute("class"):t?e.className=l:e.setAttribute("class",l),e.__className=r}else if(i&&a!==i)for(var d in i){var u=!!i[d];(a==null||u!==!!a[d])&&e.classList.toggle(d,u)}return i}function ds(e,t={},r,n){for(var a in r){var i=r[a];t[a]!==i&&(r[a]==null?e.style.removeProperty(a):e.style.setProperty(a,i,n))}}function al(e,t,r,n){var a=e.__style;if(a!==t){var i=nu(t,n);i==null?e.removeAttribute("style"):e.style.cssText=i,e.__style=t}else n&&(Array.isArray(n)?(ds(e,r==null?void 0:r[0],n[0]),ds(e,r==null?void 0:r[1],n[1],"important")):ds(e,r,n));return n}function $s(e,t,r=!1){if(e.multiple){if(t==null)return;if(!Rs(t))return Qd();for(var n of e.options)n.selected=t.includes(jo(n));return}for(n of e.options){var a=jo(n);if(Sc(a,t)){n.selected=!0;return}}(!r||t!==void 0)&&(e.selectedIndex=-1)}function au(e){var t=new MutationObserver(()=>{$s(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Za(()=>{t.disconnect()})}function jo(e){return"__value"in e?e.__value:e.value}const fa=Symbol("class"),va=Symbol("style"),sl=Symbol("is custom element"),ol=Symbol("is html"),su=pi?"option":"OPTION",ou=pi?"select":"SELECT";function iu(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function ka(e,t,r,n){var a=il(e);a[t]!==(a[t]=r)&&(t==="loading"&&(e[Ed]=r),r==null?e.removeAttribute(t):typeof r!="string"&&ll(e).includes(t)?e[t]=r:e.setAttribute(t,r))}function lu(e,t,r,n,a=!1,i=!1){var o=il(e),l=o[sl],d=!o[ol],u=t||{},v=e.nodeName===su;for(var m in t)m in r||(r[m]=null);r.class?r.class=et(r.class):r[fa]&&(r.class=null),r[va]&&(r.style??(r.style=null));var b=ll(e);for(const M in r){let L=r[M];if(v&&M==="value"&&L==null){e.value=e.__value="",u[M]=L;continue}if(M==="class"){var C=e.namespaceURI==="http://www.w3.org/1999/xhtml";tt(e,C,L,n,t==null?void 0:t[fa],r[fa]),u[M]=L,u[fa]=r[fa];continue}if(M==="style"){al(e,L,t==null?void 0:t[va],r[va]),u[M]=L,u[va]=r[va];continue}var S=u[M];if(!(L===S&&!(L===void 0&&e.hasAttribute(M)))){u[M]=L;var z=M[0]+M[1];if(z!=="$$")if(z==="on"){const Q={},K="$$"+M;let x=M.slice(2);var g=Fc(x);if(jc(x)&&(x=x.slice(0,-7),Q.capture=!0),!g&&S){if(L!=null)continue;e.removeEventListener(x,u[K],Q),u[K]=null}if(g)W(x,e,L),cn([x]);else if(L!=null){let R=function(Y){u[M].call(this,Y)};var P=R;u[K]=el(x,e,R,Q)}}else if(M==="style")ka(e,M,L);else if(M==="autofocus")Ac(e,!!L);else if(!l&&(M==="__value"||M==="value"&&L!=null))e.value=e.__value=L;else if(M==="selected"&&v)iu(e,L);else{var A=M;d||(A=Vc(A));var E=A==="defaultValue"||A==="defaultChecked";if(L==null&&!l&&!E)if(o[M]=null,A==="value"||A==="checked"){let Q=e;const K=t===void 0;if(A==="value"){let x=Q.defaultValue;Q.removeAttribute(A),Q.defaultValue=x,Q.value=Q.__value=K?x:null}else{let x=Q.defaultChecked;Q.removeAttribute(A),Q.defaultChecked=x,Q.checked=K?x:!1}}else e.removeAttribute(M);else E||b.includes(A)&&(l||typeof L!="string")?(e[A]=L,A in o&&(o[A]=zt)):typeof L!="function"&&ka(e,A,L)}}}return u}function Ha(e,t,r=[],n=[],a=[],i,o=!1,l=!1){Ei(a,r,n,d=>{var u=void 0,v={},m=e.nodeName===ou,b=!1;if(Fi(()=>{var S=t(...d.map(s)),z=lu(e,u,S,i,o,l);b&&m&&"value"in S&&$s(e,S.value);for(let A of Object.getOwnPropertySymbols(v))S[A]||$t(v[A]);for(let A of Object.getOwnPropertySymbols(S)){var g=S[A];A.description===Zd&&(!u||g!==u[A])&&(v[A]&&$t(v[A]),v[A]=Kt(()=>tu(e,()=>g))),z[A]=g}u=z}),m){var C=e;Us(()=>{$s(C,u.value,!0),au(C)})}b=!0})}function il(e){return e.__attributes??(e.__attributes={[sl]:e.nodeName.includes("-"),[ol]:e.namespaceURI===gi})}var Do=new Map;function ll(e){var t=e.getAttribute("is")||e.nodeName,r=Do.get(t);if(r)return r;Do.set(t,r=[]);for(var n,a=e,i=Element.prototype;i!==a;){n=ci(a);for(var o in n)n[o].set&&r.push(o);a=js(a)}return r}function Bn(e,t,r=t){var n=new WeakSet;Ec(e,"input",async a=>{var i=a?e.defaultValue:e.value;if(i=cs(e)?us(i):i,r(i),ye!==null&&n.add(ye),await Rc(),i!==(i=t())){var o=e.selectionStart,l=e.selectionEnd,d=e.value.length;if(e.value=i??"",l!==null){var u=e.value.length;o===l&&l===d&&u>d?(e.selectionStart=u,e.selectionEnd=u):(e.selectionStart=o,e.selectionEnd=Math.min(l,u))}}}),Tn(t)==null&&e.value&&(r(cs(e)?us(e.value):e.value),ye!==null&&n.add(ye)),Ws(()=>{var a=t();if(e===document.activeElement){var i=xs??ye;if(n.has(i))return}cs(e)&&a===us(e.value)||e.type==="date"&&!a&&!e.value||a!==e.value&&(e.value=a??"")})}function cs(e){var t=e.type;return t==="number"||t==="range"}function us(e){return e===""?null:+e}function Fo(e,t){return e===t||(e==null?void 0:e[Ir])===t}function Xs(e={},t,r,n){return Us(()=>{var a,i;return Ws(()=>{a=i,i=[],Tn(()=>{e!==r(...i)&&(t(e,...i),a&&Fo(r(...a),e)&&t(null,...a))})}),()=>{Lr(()=>{i&&Fo(r(...i),e)&&t(null,...i)})}}),e}function du(e=!1){const t=Mt,r=t.l.u;if(!r)return;let n=()=>gn(t.s);if(e){let a=0,i={};const o=Ca(()=>{let l=!1;const d=t.s;for(const u in d)d[u]!==i[u]&&(i[u]=d[u],l=!0);return l&&a++,a});n=()=>s(o)}r.b.length&&Pc(()=>{Bo(t,n),ms(r.b)}),ya(()=>{const a=Tn(()=>r.m.map(Ad));return()=>{for(const i of a)typeof i=="function"&&i()}}),r.a.length&&ya(()=>{Bo(t,n),ms(r.a)})}function Bo(e,t){if(e.l.s)for(const r of e.l.s)s(r);t()}let Oa=!1;function cu(e){var t=Oa;try{return Oa=!1,[e(),Oa]}finally{Oa=t}}const uu={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function fu(e,t,r){return new Proxy({props:e,exclude:t},uu)}const vu={get(e,t){if(!e.exclude.includes(t))return s(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,r){if(!(t in e.special)){var n=ze;try{fr(e.parent_effect),e.special[t]=nt({get[t](){return e.props[t]}},t,hi)}finally{fr(n)}}return e.special[t](r),ga(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),ga(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Me(e,t){return new Proxy({props:e,exclude:t,special:{},version:on(0),parent_effect:ze},vu)}const pu={get(e,t){let r=e.props.length;for(;r--;){let n=e.props[r];if(ca(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n)return n[t]}},set(e,t,r){let n=e.props.length;for(;n--;){let a=e.props[n];ca(a)&&(a=a());const i=tn(a,t);if(i&&i.set)return i.set(r),!0}return!1},getOwnPropertyDescriptor(e,t){let r=e.props.length;for(;r--;){let n=e.props[r];if(ca(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n){const a=tn(n,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===Ir||t===vi)return!1;for(let r of e.props)if(ca(r)&&(r=r()),r!=null&&t in r)return!0;return!1},ownKeys(e){const t=[];for(let r of e.props)if(ca(r)&&(r=r()),!!r){for(const n in r)t.includes(n)||t.push(n);for(const n of Object.getOwnPropertySymbols(r))t.includes(n)||t.push(n)}return t}};function $e(...e){return new Proxy({props:e},pu)}function nt(e,t,r,n){var P;var a=!Ma||(r&Wd)!==0,i=(r&qd)!==0,o=(r&Kd)!==0,l=n,d=!0,u=()=>(d&&(d=!1,l=o?Tn(n):n),l),v;if(i){var m=Ir in e||vi in e;v=((P=tn(e,t))==null?void 0:P.set)??(m&&t in e?M=>e[t]=M:void 0)}var b,C=!1;i?[b,C]=cu(()=>e[t]):b=e[t],b===void 0&&n!==void 0&&(b=u(),v&&(a&&Od(),v(b)));var S;if(a?S=()=>{var M=e[t];return M===void 0?u():(d=!0,M)}:S=()=>{var M=e[t];return M!==void 0&&(l=void 0),M===void 0?l:M},a&&(r&hi)===0)return S;if(v){var z=e.$$legacy;return(function(M,L){return arguments.length>0?((!a||!L||z||C)&&v(L?S():M),M):S()})}var g=!1,A=((r&Ud)!==0?Ca:Bs)(()=>(g=!1,S()));i&&s(A);var E=ze;return(function(M,L){if(arguments.length>0){const Q=L?s(A):a&&i?wt(M):M;return f(A,Q),g=!0,l!==void 0&&(l=Q),M}return ln&&g||(E.f&$r)!==0?A.v:s(A)})}const mu="5";var di;typeof window<"u"&&((di=window.__svelte??(window.__svelte={})).v??(di.v=new Set)).add(mu);const vr="";async function hu(){const e=await fetch(`${vr}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function Fn(e,t=null,r=null){const n={provider:e};t&&(n.model=t),r&&(n.api_key=r);const a=await fetch(`${vr}/api/configure`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)});if(!a.ok)throw new Error("설정 실패");return a.json()}async function gu(e){const t=await fetch(`${vr}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function xu(e,{onProgress:t,onDone:r,onError:n}){const a=new AbortController;return fetch(`${vr}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:a.signal}).then(async i=>{if(!i.ok){n==null||n("다운로드 실패");return}const o=i.body.getReader(),l=new TextDecoder;let d="";for(;;){const{done:u,value:v}=await o.read();if(u)break;d+=l.decode(v,{stream:!0});const m=d.split(`
`);d=m.pop()||"";for(const b of m)if(b.startsWith("data:"))try{const C=JSON.parse(b.slice(5).trim());C.total&&C.completed!==void 0?t==null||t({total:C.total,completed:C.completed,status:C.status}):C.status&&(t==null||t({status:C.status}))}catch{}}r==null||r()}).catch(i=>{i.name!=="AbortError"&&(n==null||n(i.message))}),{abort:()=>a.abort()}}async function bu(){const e=await fetch(`${vr}/api/oauth/authorize`);if(!e.ok)throw new Error("OAuth 인증 시작 실패");return e.json()}async function _u(){const e=await fetch(`${vr}/api/oauth/status`);return e.ok?e.json():{done:!1}}async function yu(){const e=await fetch(`${vr}/api/oauth/logout`,{method:"POST"});if(!e.ok)throw new Error("로그아웃 실패");return e.json()}async function Vo(e,t=null,r=null){let n=`${vr}/api/export/excel/${encodeURIComponent(e)}`;const a=new URLSearchParams;r?a.set("template_id",r):t&&t.length>0&&a.set("modules",t.join(","));const i=a.toString();i&&(n+=`?${i}`);const o=await fetch(n);if(!o.ok){const b=await o.json().catch(()=>({}));throw new Error(b.detail||"Excel 다운로드 실패")}const l=await o.blob(),u=(o.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),v=u?decodeURIComponent(u[1]):`${e}.xlsx`,m=document.createElement("a");return m.href=URL.createObjectURL(l),m.download=v,m.click(),URL.revokeObjectURL(m.href),v}async function wu(e){const t=await fetch(`${vr}/api/data/sources/${encodeURIComponent(e)}`);if(!t.ok)throw new Error("소스 목록 조회 실패");return t.json()}async function ku(e,t,r=50){const n=new URLSearchParams;r!==50&&n.set("max_rows",String(r));const a=n.toString(),i=`${vr}/api/data/preview/${encodeURIComponent(e)}/${encodeURIComponent(t)}${a?"?"+a:""}`,o=await fetch(i);if(!o.ok){const l=await o.json().catch(()=>({}));throw new Error(l.detail||"미리보기 실패")}return o.json()}async function dl(e){const t=await fetch(`${vr}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}function Su(e,t,r={},{onMeta:n,onSnapshot:a,onContext:i,onSystemPrompt:o,onToolCall:l,onToolResult:d,onChunk:u,onDone:v,onError:m},b=null){const C={question:t,stream:!0,...r};e&&(C.company=e),b&&b.length>0&&(C.history=b);const S=new AbortController;return fetch(`${vr}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(C),signal:S.signal}).then(async z=>{if(!z.ok){const L=await z.json().catch(()=>({}));m==null||m(L.detail||"스트리밍 실패");return}const g=z.body.getReader(),A=new TextDecoder;let E="",P=!1,M=null;for(;;){const{done:L,value:Q}=await g.read();if(L)break;E+=A.decode(Q,{stream:!0});const K=E.split(`
`);E=K.pop()||"";for(const x of K)if(x.startsWith("event:"))M=x.slice(6).trim();else if(x.startsWith("data:")&&M){const R=x.slice(5).trim();try{const Y=JSON.parse(R);M==="meta"?n==null||n(Y):M==="snapshot"?a==null||a(Y):M==="context"?i==null||i(Y):M==="system_prompt"?o==null||o(Y):M==="tool_call"?l==null||l(Y):M==="tool_result"?d==null||d(Y):M==="chunk"?u==null||u(Y.text):M==="error"?m==null||m(Y.error,Y.action,Y.detail):M==="done"&&(P||(P=!0,v==null||v()))}catch{}M=null}}P||(P=!0,v==null||v())}).catch(z=>{z.name!=="AbortError"&&(m==null||m(z.message))}),{abort:()=>S.abort()}}const zu=(e,t)=>{const r=new Array(e.length+t.length);for(let n=0;n<e.length;n++)r[n]=e[n];for(let n=0;n<t.length;n++)r[e.length+n]=t[n];return r},Mu=(e,t)=>({classGroupId:e,validator:t}),cl=(e=new Map,t=null,r)=>({nextPart:e,validators:t,classGroupId:r}),Ua="-",Go=[],Au="arbitrary..",Cu=e=>{const t=Tu(e),{conflictingClassGroups:r,conflictingClassGroupModifiers:n}=e;return{getClassGroupId:o=>{if(o.startsWith("[")&&o.endsWith("]"))return Eu(o);const l=o.split(Ua),d=l[0]===""&&l.length>1?1:0;return ul(l,d,t)},getConflictingClassGroupIds:(o,l)=>{if(l){const d=n[o],u=r[o];return d?u?zu(u,d):d:u||Go}return r[o]||Go}}},ul=(e,t,r)=>{if(e.length-t===0)return r.classGroupId;const a=e[t],i=r.nextPart.get(a);if(i){const u=ul(e,t+1,i);if(u)return u}const o=r.validators;if(o===null)return;const l=t===0?e.join(Ua):e.slice(t).join(Ua),d=o.length;for(let u=0;u<d;u++){const v=o[u];if(v.validator(l))return v.classGroupId}},Eu=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),r=t.indexOf(":"),n=t.slice(0,r);return n?Au+n:void 0})(),Tu=e=>{const{theme:t,classGroups:r}=e;return Pu(r,t)},Pu=(e,t)=>{const r=cl();for(const n in e){const a=e[n];Zs(a,r,n,t)}return r},Zs=(e,t,r,n)=>{const a=e.length;for(let i=0;i<a;i++){const o=e[i];Nu(o,t,r,n)}},Nu=(e,t,r,n)=>{if(typeof e=="string"){$u(e,t,r);return}if(typeof e=="function"){Iu(e,t,r,n);return}Lu(e,t,r,n)},$u=(e,t,r)=>{const n=e===""?t:fl(t,e);n.classGroupId=r},Iu=(e,t,r,n)=>{if(Ou(e)){Zs(e(n),t,r,n);return}t.validators===null&&(t.validators=[]),t.validators.push(Mu(r,e))},Lu=(e,t,r,n)=>{const a=Object.entries(e),i=a.length;for(let o=0;o<i;o++){const[l,d]=a[o];Zs(d,fl(t,l),r,n)}},fl=(e,t)=>{let r=e;const n=t.split(Ua),a=n.length;for(let i=0;i<a;i++){const o=n[i];let l=r.nextPart.get(o);l||(l=cl(),r.nextPart.set(o,l)),r=l}return r},Ou=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,Ru=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,r=Object.create(null),n=Object.create(null);const a=(i,o)=>{r[i]=o,t++,t>e&&(t=0,n=r,r=Object.create(null))};return{get(i){let o=r[i];if(o!==void 0)return o;if((o=n[i])!==void 0)return a(i,o),o},set(i,o){i in r?r[i]=o:a(i,o)}}},Is="!",Ho=":",ju=[],Uo=(e,t,r,n,a)=>({modifiers:e,hasImportantModifier:t,baseClassName:r,maybePostfixModifierPosition:n,isExternal:a}),Du=e=>{const{prefix:t,experimentalParseClassName:r}=e;let n=a=>{const i=[];let o=0,l=0,d=0,u;const v=a.length;for(let z=0;z<v;z++){const g=a[z];if(o===0&&l===0){if(g===Ho){i.push(a.slice(d,z)),d=z+1;continue}if(g==="/"){u=z;continue}}g==="["?o++:g==="]"?o--:g==="("?l++:g===")"&&l--}const m=i.length===0?a:a.slice(d);let b=m,C=!1;m.endsWith(Is)?(b=m.slice(0,-1),C=!0):m.startsWith(Is)&&(b=m.slice(1),C=!0);const S=u&&u>d?u-d:void 0;return Uo(i,C,b,S)};if(t){const a=t+Ho,i=n;n=o=>o.startsWith(a)?i(o.slice(a.length)):Uo(ju,!1,o,void 0,!0)}if(r){const a=n;n=i=>r({className:i,parseClassName:a})}return n},Fu=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((r,n)=>{t.set(r,1e6+n)}),r=>{const n=[];let a=[];for(let i=0;i<r.length;i++){const o=r[i],l=o[0]==="[",d=t.has(o);l||d?(a.length>0&&(a.sort(),n.push(...a),a=[]),n.push(o)):a.push(o)}return a.length>0&&(a.sort(),n.push(...a)),n}},Bu=e=>({cache:Ru(e.cacheSize),parseClassName:Du(e),sortModifiers:Fu(e),...Cu(e)}),Vu=/\s+/,Gu=(e,t)=>{const{parseClassName:r,getClassGroupId:n,getConflictingClassGroupIds:a,sortModifiers:i}=t,o=[],l=e.trim().split(Vu);let d="";for(let u=l.length-1;u>=0;u-=1){const v=l[u],{isExternal:m,modifiers:b,hasImportantModifier:C,baseClassName:S,maybePostfixModifierPosition:z}=r(v);if(m){d=v+(d.length>0?" "+d:d);continue}let g=!!z,A=n(g?S.substring(0,z):S);if(!A){if(!g){d=v+(d.length>0?" "+d:d);continue}if(A=n(S),!A){d=v+(d.length>0?" "+d:d);continue}g=!1}const E=b.length===0?"":b.length===1?b[0]:i(b).join(":"),P=C?E+Is:E,M=P+A;if(o.indexOf(M)>-1)continue;o.push(M);const L=a(A,g);for(let Q=0;Q<L.length;++Q){const K=L[Q];o.push(P+K)}d=v+(d.length>0?" "+d:d)}return d},Hu=(...e)=>{let t=0,r,n,a="";for(;t<e.length;)(r=e[t++])&&(n=vl(r))&&(a&&(a+=" "),a+=n);return a},vl=e=>{if(typeof e=="string")return e;let t,r="";for(let n=0;n<e.length;n++)e[n]&&(t=vl(e[n]))&&(r&&(r+=" "),r+=t);return r},Uu=(e,...t)=>{let r,n,a,i;const o=d=>{const u=t.reduce((v,m)=>m(v),e());return r=Bu(u),n=r.cache.get,a=r.cache.set,i=l,l(d)},l=d=>{const u=n(d);if(u)return u;const v=Gu(d,r);return a(d,v),v};return i=o,(...d)=>i(Hu(...d))},Wu=[],yt=e=>{const t=r=>r[e]||Wu;return t.isThemeGetter=!0,t},pl=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,ml=/^\((?:(\w[\w-]*):)?(.+)\)$/i,qu=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,Ku=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,Yu=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,Ju=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,Xu=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,Zu=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,Kr=e=>qu.test(e),ge=e=>!!e&&!Number.isNaN(Number(e)),Yr=e=>!!e&&Number.isInteger(Number(e)),fs=e=>e.endsWith("%")&&ge(e.slice(0,-1)),Dr=e=>Ku.test(e),hl=()=>!0,Qu=e=>Yu.test(e)&&!Ju.test(e),Qs=()=>!1,ef=e=>Xu.test(e),tf=e=>Zu.test(e),rf=e=>!G(e)&&!U(e),nf=e=>un(e,bl,Qs),G=e=>pl.test(e),mn=e=>un(e,_l,Qu),Wo=e=>un(e,ff,ge),af=e=>un(e,wl,hl),sf=e=>un(e,yl,Qs),qo=e=>un(e,gl,Qs),of=e=>un(e,xl,tf),Ra=e=>un(e,kl,ef),U=e=>ml.test(e),pa=e=>$n(e,_l),lf=e=>$n(e,yl),Ko=e=>$n(e,gl),df=e=>$n(e,bl),cf=e=>$n(e,xl),ja=e=>$n(e,kl,!0),uf=e=>$n(e,wl,!0),un=(e,t,r)=>{const n=pl.exec(e);return n?n[1]?t(n[1]):r(n[2]):!1},$n=(e,t,r=!1)=>{const n=ml.exec(e);return n?n[1]?t(n[1]):r:!1},gl=e=>e==="position"||e==="percentage",xl=e=>e==="image"||e==="url",bl=e=>e==="length"||e==="size"||e==="bg-size",_l=e=>e==="length",ff=e=>e==="number",yl=e=>e==="family-name",wl=e=>e==="number"||e==="weight",kl=e=>e==="shadow",vf=()=>{const e=yt("color"),t=yt("font"),r=yt("text"),n=yt("font-weight"),a=yt("tracking"),i=yt("leading"),o=yt("breakpoint"),l=yt("container"),d=yt("spacing"),u=yt("radius"),v=yt("shadow"),m=yt("inset-shadow"),b=yt("text-shadow"),C=yt("drop-shadow"),S=yt("blur"),z=yt("perspective"),g=yt("aspect"),A=yt("ease"),E=yt("animate"),P=()=>["auto","avoid","all","avoid-page","page","left","right","column"],M=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],L=()=>[...M(),U,G],Q=()=>["auto","hidden","clip","visible","scroll"],K=()=>["auto","contain","none"],x=()=>[U,G,d],R=()=>[Kr,"full","auto",...x()],Y=()=>[Yr,"none","subgrid",U,G],fe=()=>["auto",{span:["full",Yr,U,G]},Yr,U,G],Ae=()=>[Yr,"auto",U,G],He=()=>["auto","min","max","fr",U,G],N=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],O=()=>["start","end","center","stretch","center-safe","end-safe"],ee=()=>["auto",...x()],de=()=>[Kr,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...x()],ue=()=>[Kr,"screen","full","dvw","lvw","svw","min","max","fit",...x()],V=()=>[Kr,"screen","full","lh","dvh","lvh","svh","min","max","fit",...x()],y=()=>[e,U,G],ke=()=>[...M(),Ko,qo,{position:[U,G]}],me=()=>["no-repeat",{repeat:["","x","y","space","round"]}],lt=()=>["auto","cover","contain",df,nf,{size:[U,G]}],$=()=>[fs,pa,mn],J=()=>["","none","full",u,U,G],j=()=>["",ge,pa,mn],re=()=>["solid","dashed","dotted","double"],ie=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],se=()=>[ge,fs,Ko,qo],Ce=()=>["","none",S,U,G],Oe=()=>["none",ge,U,G],Ee=()=>["none",ge,U,G],qe=()=>[ge,U,G],ve=()=>[Kr,"full",...x()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Dr],breakpoint:[Dr],color:[hl],container:[Dr],"drop-shadow":[Dr],ease:["in","out","in-out"],font:[rf],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Dr],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Dr],shadow:[Dr],spacing:["px",ge],text:[Dr],"text-shadow":[Dr],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",Kr,G,U,g]}],container:["container"],columns:[{columns:[ge,G,U,l]}],"break-after":[{"break-after":P()}],"break-before":[{"break-before":P()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:L()}],overflow:[{overflow:Q()}],"overflow-x":[{"overflow-x":Q()}],"overflow-y":[{"overflow-y":Q()}],overscroll:[{overscroll:K()}],"overscroll-x":[{"overscroll-x":K()}],"overscroll-y":[{"overscroll-y":K()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:R()}],"inset-x":[{"inset-x":R()}],"inset-y":[{"inset-y":R()}],start:[{"inset-s":R(),start:R()}],end:[{"inset-e":R(),end:R()}],"inset-bs":[{"inset-bs":R()}],"inset-be":[{"inset-be":R()}],top:[{top:R()}],right:[{right:R()}],bottom:[{bottom:R()}],left:[{left:R()}],visibility:["visible","invisible","collapse"],z:[{z:[Yr,"auto",U,G]}],basis:[{basis:[Kr,"full","auto",l,...x()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[ge,Kr,"auto","initial","none",G]}],grow:[{grow:["",ge,U,G]}],shrink:[{shrink:["",ge,U,G]}],order:[{order:[Yr,"first","last","none",U,G]}],"grid-cols":[{"grid-cols":Y()}],"col-start-end":[{col:fe()}],"col-start":[{"col-start":Ae()}],"col-end":[{"col-end":Ae()}],"grid-rows":[{"grid-rows":Y()}],"row-start-end":[{row:fe()}],"row-start":[{"row-start":Ae()}],"row-end":[{"row-end":Ae()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":He()}],"auto-rows":[{"auto-rows":He()}],gap:[{gap:x()}],"gap-x":[{"gap-x":x()}],"gap-y":[{"gap-y":x()}],"justify-content":[{justify:[...N(),"normal"]}],"justify-items":[{"justify-items":[...O(),"normal"]}],"justify-self":[{"justify-self":["auto",...O()]}],"align-content":[{content:["normal",...N()]}],"align-items":[{items:[...O(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...O(),{baseline:["","last"]}]}],"place-content":[{"place-content":N()}],"place-items":[{"place-items":[...O(),"baseline"]}],"place-self":[{"place-self":["auto",...O()]}],p:[{p:x()}],px:[{px:x()}],py:[{py:x()}],ps:[{ps:x()}],pe:[{pe:x()}],pbs:[{pbs:x()}],pbe:[{pbe:x()}],pt:[{pt:x()}],pr:[{pr:x()}],pb:[{pb:x()}],pl:[{pl:x()}],m:[{m:ee()}],mx:[{mx:ee()}],my:[{my:ee()}],ms:[{ms:ee()}],me:[{me:ee()}],mbs:[{mbs:ee()}],mbe:[{mbe:ee()}],mt:[{mt:ee()}],mr:[{mr:ee()}],mb:[{mb:ee()}],ml:[{ml:ee()}],"space-x":[{"space-x":x()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":x()}],"space-y-reverse":["space-y-reverse"],size:[{size:de()}],"inline-size":[{inline:["auto",...ue()]}],"min-inline-size":[{"min-inline":["auto",...ue()]}],"max-inline-size":[{"max-inline":["none",...ue()]}],"block-size":[{block:["auto",...V()]}],"min-block-size":[{"min-block":["auto",...V()]}],"max-block-size":[{"max-block":["none",...V()]}],w:[{w:[l,"screen",...de()]}],"min-w":[{"min-w":[l,"screen","none",...de()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[o]},...de()]}],h:[{h:["screen","lh",...de()]}],"min-h":[{"min-h":["screen","lh","none",...de()]}],"max-h":[{"max-h":["screen","lh",...de()]}],"font-size":[{text:["base",r,pa,mn]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[n,uf,af]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",fs,G]}],"font-family":[{font:[lf,sf,t]}],"font-features":[{"font-features":[G]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[a,U,G]}],"line-clamp":[{"line-clamp":[ge,"none",U,Wo]}],leading:[{leading:[i,...x()]}],"list-image":[{"list-image":["none",U,G]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",U,G]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:y()}],"text-color":[{text:y()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...re(),"wavy"]}],"text-decoration-thickness":[{decoration:[ge,"from-font","auto",U,mn]}],"text-decoration-color":[{decoration:y()}],"underline-offset":[{"underline-offset":[ge,"auto",U,G]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:x()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",U,G]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",U,G]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:ke()}],"bg-repeat":[{bg:me()}],"bg-size":[{bg:lt()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},Yr,U,G],radial:["",U,G],conic:[Yr,U,G]},cf,of]}],"bg-color":[{bg:y()}],"gradient-from-pos":[{from:$()}],"gradient-via-pos":[{via:$()}],"gradient-to-pos":[{to:$()}],"gradient-from":[{from:y()}],"gradient-via":[{via:y()}],"gradient-to":[{to:y()}],rounded:[{rounded:J()}],"rounded-s":[{"rounded-s":J()}],"rounded-e":[{"rounded-e":J()}],"rounded-t":[{"rounded-t":J()}],"rounded-r":[{"rounded-r":J()}],"rounded-b":[{"rounded-b":J()}],"rounded-l":[{"rounded-l":J()}],"rounded-ss":[{"rounded-ss":J()}],"rounded-se":[{"rounded-se":J()}],"rounded-ee":[{"rounded-ee":J()}],"rounded-es":[{"rounded-es":J()}],"rounded-tl":[{"rounded-tl":J()}],"rounded-tr":[{"rounded-tr":J()}],"rounded-br":[{"rounded-br":J()}],"rounded-bl":[{"rounded-bl":J()}],"border-w":[{border:j()}],"border-w-x":[{"border-x":j()}],"border-w-y":[{"border-y":j()}],"border-w-s":[{"border-s":j()}],"border-w-e":[{"border-e":j()}],"border-w-bs":[{"border-bs":j()}],"border-w-be":[{"border-be":j()}],"border-w-t":[{"border-t":j()}],"border-w-r":[{"border-r":j()}],"border-w-b":[{"border-b":j()}],"border-w-l":[{"border-l":j()}],"divide-x":[{"divide-x":j()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":j()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...re(),"hidden","none"]}],"divide-style":[{divide:[...re(),"hidden","none"]}],"border-color":[{border:y()}],"border-color-x":[{"border-x":y()}],"border-color-y":[{"border-y":y()}],"border-color-s":[{"border-s":y()}],"border-color-e":[{"border-e":y()}],"border-color-bs":[{"border-bs":y()}],"border-color-be":[{"border-be":y()}],"border-color-t":[{"border-t":y()}],"border-color-r":[{"border-r":y()}],"border-color-b":[{"border-b":y()}],"border-color-l":[{"border-l":y()}],"divide-color":[{divide:y()}],"outline-style":[{outline:[...re(),"none","hidden"]}],"outline-offset":[{"outline-offset":[ge,U,G]}],"outline-w":[{outline:["",ge,pa,mn]}],"outline-color":[{outline:y()}],shadow:[{shadow:["","none",v,ja,Ra]}],"shadow-color":[{shadow:y()}],"inset-shadow":[{"inset-shadow":["none",m,ja,Ra]}],"inset-shadow-color":[{"inset-shadow":y()}],"ring-w":[{ring:j()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:y()}],"ring-offset-w":[{"ring-offset":[ge,mn]}],"ring-offset-color":[{"ring-offset":y()}],"inset-ring-w":[{"inset-ring":j()}],"inset-ring-color":[{"inset-ring":y()}],"text-shadow":[{"text-shadow":["none",b,ja,Ra]}],"text-shadow-color":[{"text-shadow":y()}],opacity:[{opacity:[ge,U,G]}],"mix-blend":[{"mix-blend":[...ie(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":ie()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[ge]}],"mask-image-linear-from-pos":[{"mask-linear-from":se()}],"mask-image-linear-to-pos":[{"mask-linear-to":se()}],"mask-image-linear-from-color":[{"mask-linear-from":y()}],"mask-image-linear-to-color":[{"mask-linear-to":y()}],"mask-image-t-from-pos":[{"mask-t-from":se()}],"mask-image-t-to-pos":[{"mask-t-to":se()}],"mask-image-t-from-color":[{"mask-t-from":y()}],"mask-image-t-to-color":[{"mask-t-to":y()}],"mask-image-r-from-pos":[{"mask-r-from":se()}],"mask-image-r-to-pos":[{"mask-r-to":se()}],"mask-image-r-from-color":[{"mask-r-from":y()}],"mask-image-r-to-color":[{"mask-r-to":y()}],"mask-image-b-from-pos":[{"mask-b-from":se()}],"mask-image-b-to-pos":[{"mask-b-to":se()}],"mask-image-b-from-color":[{"mask-b-from":y()}],"mask-image-b-to-color":[{"mask-b-to":y()}],"mask-image-l-from-pos":[{"mask-l-from":se()}],"mask-image-l-to-pos":[{"mask-l-to":se()}],"mask-image-l-from-color":[{"mask-l-from":y()}],"mask-image-l-to-color":[{"mask-l-to":y()}],"mask-image-x-from-pos":[{"mask-x-from":se()}],"mask-image-x-to-pos":[{"mask-x-to":se()}],"mask-image-x-from-color":[{"mask-x-from":y()}],"mask-image-x-to-color":[{"mask-x-to":y()}],"mask-image-y-from-pos":[{"mask-y-from":se()}],"mask-image-y-to-pos":[{"mask-y-to":se()}],"mask-image-y-from-color":[{"mask-y-from":y()}],"mask-image-y-to-color":[{"mask-y-to":y()}],"mask-image-radial":[{"mask-radial":[U,G]}],"mask-image-radial-from-pos":[{"mask-radial-from":se()}],"mask-image-radial-to-pos":[{"mask-radial-to":se()}],"mask-image-radial-from-color":[{"mask-radial-from":y()}],"mask-image-radial-to-color":[{"mask-radial-to":y()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":M()}],"mask-image-conic-pos":[{"mask-conic":[ge]}],"mask-image-conic-from-pos":[{"mask-conic-from":se()}],"mask-image-conic-to-pos":[{"mask-conic-to":se()}],"mask-image-conic-from-color":[{"mask-conic-from":y()}],"mask-image-conic-to-color":[{"mask-conic-to":y()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:ke()}],"mask-repeat":[{mask:me()}],"mask-size":[{mask:lt()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",U,G]}],filter:[{filter:["","none",U,G]}],blur:[{blur:Ce()}],brightness:[{brightness:[ge,U,G]}],contrast:[{contrast:[ge,U,G]}],"drop-shadow":[{"drop-shadow":["","none",C,ja,Ra]}],"drop-shadow-color":[{"drop-shadow":y()}],grayscale:[{grayscale:["",ge,U,G]}],"hue-rotate":[{"hue-rotate":[ge,U,G]}],invert:[{invert:["",ge,U,G]}],saturate:[{saturate:[ge,U,G]}],sepia:[{sepia:["",ge,U,G]}],"backdrop-filter":[{"backdrop-filter":["","none",U,G]}],"backdrop-blur":[{"backdrop-blur":Ce()}],"backdrop-brightness":[{"backdrop-brightness":[ge,U,G]}],"backdrop-contrast":[{"backdrop-contrast":[ge,U,G]}],"backdrop-grayscale":[{"backdrop-grayscale":["",ge,U,G]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[ge,U,G]}],"backdrop-invert":[{"backdrop-invert":["",ge,U,G]}],"backdrop-opacity":[{"backdrop-opacity":[ge,U,G]}],"backdrop-saturate":[{"backdrop-saturate":[ge,U,G]}],"backdrop-sepia":[{"backdrop-sepia":["",ge,U,G]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":x()}],"border-spacing-x":[{"border-spacing-x":x()}],"border-spacing-y":[{"border-spacing-y":x()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",U,G]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[ge,"initial",U,G]}],ease:[{ease:["linear","initial",A,U,G]}],delay:[{delay:[ge,U,G]}],animate:[{animate:["none",E,U,G]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[z,U,G]}],"perspective-origin":[{"perspective-origin":L()}],rotate:[{rotate:Oe()}],"rotate-x":[{"rotate-x":Oe()}],"rotate-y":[{"rotate-y":Oe()}],"rotate-z":[{"rotate-z":Oe()}],scale:[{scale:Ee()}],"scale-x":[{"scale-x":Ee()}],"scale-y":[{"scale-y":Ee()}],"scale-z":[{"scale-z":Ee()}],"scale-3d":["scale-3d"],skew:[{skew:qe()}],"skew-x":[{"skew-x":qe()}],"skew-y":[{"skew-y":qe()}],transform:[{transform:[U,G,"","none","gpu","cpu"]}],"transform-origin":[{origin:L()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:ve()}],"translate-x":[{"translate-x":ve()}],"translate-y":[{"translate-y":ve()}],"translate-z":[{"translate-z":ve()}],"translate-none":["translate-none"],accent:[{accent:y()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:y()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",U,G]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":x()}],"scroll-mx":[{"scroll-mx":x()}],"scroll-my":[{"scroll-my":x()}],"scroll-ms":[{"scroll-ms":x()}],"scroll-me":[{"scroll-me":x()}],"scroll-mbs":[{"scroll-mbs":x()}],"scroll-mbe":[{"scroll-mbe":x()}],"scroll-mt":[{"scroll-mt":x()}],"scroll-mr":[{"scroll-mr":x()}],"scroll-mb":[{"scroll-mb":x()}],"scroll-ml":[{"scroll-ml":x()}],"scroll-p":[{"scroll-p":x()}],"scroll-px":[{"scroll-px":x()}],"scroll-py":[{"scroll-py":x()}],"scroll-ps":[{"scroll-ps":x()}],"scroll-pe":[{"scroll-pe":x()}],"scroll-pbs":[{"scroll-pbs":x()}],"scroll-pbe":[{"scroll-pbe":x()}],"scroll-pt":[{"scroll-pt":x()}],"scroll-pr":[{"scroll-pr":x()}],"scroll-pb":[{"scroll-pb":x()}],"scroll-pl":[{"scroll-pl":x()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",U,G]}],fill:[{fill:["none",...y()]}],"stroke-w":[{stroke:[ge,pa,mn,Wo]}],stroke:[{stroke:["none",...y()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},pf=Uu(vf);function rt(...e){return pf(nl(e))}const Ls="dartlab-conversations",Yo=50;function mf(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function hf(){try{const e=localStorage.getItem(Ls);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const gf=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function Jo(e){return e.map(t=>({...t,messages:t.messages.map(r=>{if(r.role!=="assistant")return r;const n={};for(const[a,i]of Object.entries(r))gf.includes(a)||(n[a]=i);return n})}))}function Xo(e){try{const t={conversations:Jo(e.conversations),activeId:e.activeId};localStorage.setItem(Ls,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:Jo(e.conversations),activeId:e.activeId};localStorage.setItem(Ls,JSON.stringify(t))}catch{}}}}function xf(){const e=hf();let t=H(wt(e.conversations)),r=H(wt(e.activeId));s(r)&&!s(t).find(z=>z.id===s(r))&&f(r,null);let n=null;function a(){n&&clearTimeout(n),n=setTimeout(()=>{Xo({conversations:s(t),activeId:s(r)}),n=null},300)}function i(){n&&clearTimeout(n),n=null,Xo({conversations:s(t),activeId:s(r)})}function o(){return s(t).find(z=>z.id===s(r))||null}function l(){const z={id:mf(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return f(t,[z,...s(t)],!0),s(t).length>Yo&&f(t,s(t).slice(0,Yo),!0),f(r,z.id,!0),i(),z.id}function d(z){s(t).find(g=>g.id===z)&&(f(r,z,!0),i())}function u(z,g,A=null){const E=o();if(!E)return;const P={role:z,text:g};A&&(P.meta=A),E.messages=[...E.messages,P],E.updatedAt=Date.now(),E.title==="새 대화"&&z==="user"&&(E.title=g.length>30?g.slice(0,30)+"...":g),f(t,[...s(t)],!0),i()}function v(z){const g=o();if(!g||g.messages.length===0)return;const A=g.messages[g.messages.length-1];Object.assign(A,z),g.updatedAt=Date.now(),f(t,[...s(t)],!0),a()}function m(z){f(t,s(t).filter(g=>g.id!==z),!0),s(r)===z&&f(r,s(t).length>0?s(t)[0].id:null,!0),i()}function b(){const z=o();!z||z.messages.length===0||(z.messages=z.messages.slice(0,-1),z.updatedAt=Date.now(),f(t,[...s(t)],!0),i())}function C(z,g){const A=s(t).find(E=>E.id===z);A&&(A.title=g,f(t,[...s(t)],!0),i())}function S(){f(t,[],!0),f(r,null),i()}return{get conversations(){return s(t)},get activeId(){return s(r)},get active(){return o()},createConversation:l,setActive:d,addMessage:u,updateLastMessage:v,removeLastMessage:b,deleteConversation:m,updateTitle:C,clearAll:S,flush:i}}var bf=w("<a><!></a>"),_f=w("<button><!></button>");function yf(e,t){kr(t,!0);let r=nt(t,"variant",3,"default"),n=nt(t,"size",3,"default"),a=fu(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const i={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},o={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=xe(),d=q(l);{var u=m=>{var b=bf();Ha(b,S=>({class:S,...a}),[()=>rt("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",i[r()],o[n()],t.class)]);var C=c(b);Ns(C,()=>t.children),p(m,b)},v=m=>{var b=_f();Ha(b,S=>({class:S,...a}),[()=>rt("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",i[r()],o[n()],t.class)]);var C=c(b);Ns(C,()=>t.children),p(m,b)};T(d,m=>{t.href?m(u):m(v,-1)})}p(e,l),Sr()}nc();/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
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
 */const Zo=(...e)=>e.filter((t,r,n)=>!!t&&t.trim()!==""&&n.indexOf(t)===r).join(" ").trim();var Sf=qc("<svg><!><!></svg>");function Ie(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]),n=Me(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);kr(t,!1);let a=nt(t,"name",8,void 0),i=nt(t,"color",8,"currentColor"),o=nt(t,"size",8,24),l=nt(t,"strokeWidth",8,2),d=nt(t,"absoluteStrokeWidth",8,!1),u=nt(t,"iconNode",24,()=>[]);du();var v=Sf();Ha(v,(C,S,z)=>({...wf,...C,...n,width:o(),height:o(),stroke:i(),"stroke-width":S,class:z}),[()=>kf(n)?void 0:{"aria-hidden":"true"},()=>(gn(d()),gn(l()),gn(o()),Tn(()=>d()?Number(l())*24/Number(o()):l())),()=>(gn(Zo),gn(a()),gn(r),Tn(()=>Zo("lucide-icon","lucide",a()?`lucide-${a()}`:"",r.class)))]);var m=c(v);it(m,1,u,ot,(C,S)=>{var z=pe(()=>Va(s(S),2));let g=()=>s(z)[0],A=()=>s(z)[1];var E=xe(),P=q(E);eu(P,g,!0,(M,L)=>{Ha(M,()=>({...A()}))}),p(C,E)});var b=h(m);Ne(b,t,"default",{}),p(e,v),Sr()}function zf(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m12 19-7-7 7-7"}],["path",{d:"M19 12H5"}]];Ie(e,$e({name:"arrow-left"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Mf(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];Ie(e,$e({name:"arrow-up"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Qo(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];Ie(e,$e({name:"brain"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Af(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M20 6 9 17l-5-5"}]];Ie(e,$e({name:"check"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Cf(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m6 9 6 6 6-6"}]];Ie(e,$e({name:"chevron-down"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function ei(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m9 18 6-6-6-6"}]];Ie(e,$e({name:"chevron-right"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function hn(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];Ie(e,$e({name:"circle-alert"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function vs(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];Ie(e,$e({name:"circle-check"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Ef(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];Ie(e,$e({name:"clock"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Tf(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];Ie(e,$e({name:"code"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Pf(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];Ie(e,$e({name:"coffee"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function en(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];Ie(e,$e({name:"database"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Vn(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];Ie(e,$e({name:"download"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function ti(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];Ie(e,$e({name:"external-link"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function _a(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];Ie(e,$e({name:"file-text"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Nf(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];Ie(e,$e({name:"github"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function ri(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];Ie(e,$e({name:"key"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Bt(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];Ie(e,$e({name:"loader-circle"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function $f(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m10 17 5-5-5-5"}],["path",{d:"M15 12H3"}],["path",{d:"M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"}]];Ie(e,$e({name:"log-in"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function If(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];Ie(e,$e({name:"log-out"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Lf(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];Ie(e,$e({name:"menu"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function ni(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];Ie(e,$e({name:"message-square"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Of(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];Ie(e,$e({name:"panel-left-close"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function ai(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];Ie(e,$e({name:"plus"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Rf(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];Ie(e,$e({name:"refresh-cw"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function eo(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];Ie(e,$e({name:"search"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function jf(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];Ie(e,$e({name:"settings"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Df(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];Ie(e,$e({name:"square"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function si(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];Ie(e,$e({name:"table-2"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Ff(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];Ie(e,$e({name:"terminal"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Bf(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];Ie(e,$e({name:"trash-2"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Vf(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];Ie(e,$e({name:"triangle-alert"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function Gf(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];Ie(e,$e({name:"wrench"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}function to(e,t){const r=Me(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];Ie(e,$e({name:"x"},()=>r,{get iconNode(){return n},children:(a,i)=>{var o=xe(),l=q(o);Ne(l,t,"default",{}),p(a,o)},$$slots:{default:!0}}))}var Hf=w("<!> 새 대화",1),Uf=w('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-dl-bg-card border border-dl-border"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),Wf=w('<div role="button" tabindex="0"><!> <span class="flex-1 truncate"> </span> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),qf=w('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),Kf=w('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/50 text-[10px] text-dl-text-dim"> </div>'),Yf=w('<div class="flex flex-col h-full min-w-[260px]"><div class="flex items-center gap-2.5 px-4 pt-4 pb-2"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <span class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</span></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 space-y-4"></div> <!></div>'),Jf=w("<button><!></button>"),Xf=w('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),Zf=w("<aside><!></aside>");function Qf(e,t){kr(t,!0);let r=nt(t,"conversations",19,()=>[]),n=nt(t,"activeId",3,null),a=nt(t,"open",3,!0),i=nt(t,"version",3,""),o=H("");function l(S){const z=new Date().setHours(0,0,0,0),g=z-864e5,A=z-7*864e5,E={오늘:[],어제:[],"이번 주":[],이전:[]};for(const M of S)M.updatedAt>=z?E.오늘.push(M):M.updatedAt>=g?E.어제.push(M):M.updatedAt>=A?E["이번 주"].push(M):E.이전.push(M);const P=[];for(const[M,L]of Object.entries(E))L.length>0&&P.push({label:M,items:L});return P}let d=pe(()=>s(o).trim()?r().filter(S=>S.title.toLowerCase().includes(s(o).toLowerCase())):r()),u=pe(()=>l(s(d)));var v=Zf(),m=c(v);{var b=S=>{var z=Yf(),g=h(c(z),2),A=c(g);yf(A,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(K,x)=>{var R=Hf(),Y=q(R);ai(Y,{size:16}),p(K,R)},$$slots:{default:!0}});var E=h(g,2);{var P=K=>{var x=Uf(),R=c(x),Y=c(R);eo(Y,{size:12,class:"text-dl-text-dim flex-shrink-0"});var fe=h(Y,2);Bn(fe,()=>s(o),Ae=>f(o,Ae)),p(K,x)};T(E,K=>{r().length>3&&K(P)})}var M=h(E,2);it(M,21,()=>s(u),ot,(K,x)=>{var R=qf(),Y=c(R),fe=c(Y),Ae=h(Y,2);it(Ae,17,()=>s(x).items,ot,(He,N)=>{var O=Wf(),ee=c(O);ni(ee,{size:14,class:"flex-shrink-0 opacity-50"});var de=h(ee,2),ue=c(de),V=h(de,2),y=c(V);Bf(y,{size:12}),D(ke=>{tt(O,1,ke),B(ue,s(N).title)},[()=>et(rt("w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-[13px] transition-colors group cursor-pointer",s(N).id===n()?"bg-dl-bg-card text-dl-text border-l-2 border-dl-primary":"text-dl-text-muted hover:bg-dl-bg-card/50 hover:text-dl-text border-l-2 border-transparent"))]),W("click",O,()=>{var ke;return(ke=t.onSelect)==null?void 0:ke.call(t,s(N).id)}),W("keydown",O,ke=>{var me;ke.key==="Enter"&&((me=t.onSelect)==null||me.call(t,s(N).id))}),W("click",V,ke=>{var me;ke.stopPropagation(),(me=t.onDelete)==null||me.call(t,s(N).id)}),p(He,O)}),D(()=>B(fe,s(x).label)),p(K,R)});var L=h(M,2);{var Q=K=>{var x=Kf(),R=c(x);D(()=>B(R,`DartLab v${i()??""}`)),p(K,x)};T(L,K=>{i()&&K(Q)})}p(S,z)},C=S=>{var z=Xf(),g=h(c(z),2),A=c(g);ai(A,{size:18});var E=h(g,2);it(E,21,()=>r().slice(0,10),ot,(P,M)=>{var L=Jf(),Q=c(L);ni(Q,{size:16}),D(K=>{tt(L,1,K),ka(L,"title",s(M).title)},[()=>et(rt("p-2 rounded-lg transition-colors w-full flex justify-center",s(M).id===n()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),W("click",L,()=>{var K;return(K=t.onSelect)==null?void 0:K.call(t,s(M).id)}),p(P,L)}),W("click",g,function(...P){var M;(M=t.onNewChat)==null||M.apply(this,P)}),p(S,z)};T(m,S=>{a()?S(b):S(C,-1)})}D(S=>tt(v,1,S),[()=>et(rt("flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",a()?"w-[260px]":"w-[52px]"))]),p(e,v),Sr()}cn(["click","keydown"]);var ev=w('<button class="send-btn active"><!></button>'),tv=w("<button><!></button>"),rv=w('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),nv=w('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),av=w('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),sv=w('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function Sl(e,t){kr(t,!0);let r=nt(t,"inputText",15,""),n=nt(t,"isLoading",3,!1),a=nt(t,"large",3,!1),i=nt(t,"placeholder",3,"메시지를 입력하세요..."),o=H(wt([])),l=H(!1),d=H(-1),u=null,v=H(void 0);function m(x){var R;if(s(l)&&s(o).length>0){if(x.key==="ArrowDown"){x.preventDefault(),f(d,(s(d)+1)%s(o).length);return}if(x.key==="ArrowUp"){x.preventDefault(),f(d,s(d)<=0?s(o).length-1:s(d)-1,!0);return}if(x.key==="Enter"&&s(d)>=0){x.preventDefault(),S(s(o)[s(d)]);return}if(x.key==="Escape"){f(l,!1),f(d,-1);return}}x.key==="Enter"&&!x.shiftKey&&(x.preventDefault(),f(l,!1),(R=t.onSend)==null||R.call(t))}function b(x){x.target.style.height="auto",x.target.style.height=Math.min(x.target.scrollHeight,200)+"px"}function C(x){b(x);const R=r();u&&clearTimeout(u),R.length>=2&&!/\s/.test(R.slice(-1))?u=setTimeout(async()=>{var Y;try{const fe=await dl(R.trim());((Y=fe.results)==null?void 0:Y.length)>0?(f(o,fe.results.slice(0,6),!0),f(l,!0),f(d,-1)):f(l,!1)}catch{f(l,!1)}},300):f(l,!1)}function S(x){r(`${x.corpName} `),f(l,!1),f(d,-1),s(v)&&s(v).focus()}function z(){setTimeout(()=>{f(l,!1)},200)}var g=sv(),A=c(g),E=c(A);Xs(E,x=>f(v,x),()=>s(v));var P=h(E,2);{var M=x=>{var R=ev(),Y=c(R);Df(Y,{size:14}),W("click",R,function(...fe){var Ae;(Ae=t.onStop)==null||Ae.apply(this,fe)}),p(x,R)},L=x=>{var R=tv(),Y=c(R);{let fe=pe(()=>a()?18:16);Mf(Y,{get size(){return s(fe)},strokeWidth:2.5})}D((fe,Ae)=>{tt(R,1,fe),R.disabled=Ae},[()=>et(rt("send-btn",r().trim()&&"active")),()=>!r().trim()]),W("click",R,()=>{var fe;f(l,!1),(fe=t.onSend)==null||fe.call(t)}),p(x,R)};T(P,x=>{n()&&t.onStop?x(M):x(L,-1)})}var Q=h(A,2);{var K=x=>{var R=av();it(R,21,()=>s(o),ot,(Y,fe,Ae)=>{var He=nv(),N=c(He);eo(N,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var O=h(N,2),ee=c(O),de=c(ee),ue=h(ee,2),V=c(ue),y=h(O,2);{var ke=me=>{var lt=rv(),$=c(lt);D(()=>B($,s(fe).sector)),p(me,lt)};T(y,me=>{s(fe).sector&&me(ke)})}D(me=>{tt(He,1,me),B(de,s(fe).corpName),B(V,`${s(fe).stockCode??""} · ${(s(fe).market||"")??""}`)},[()=>et(rt("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",Ae===s(d)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),W("mousedown",He,()=>S(s(fe))),Ga("mouseenter",He,()=>{f(d,Ae,!0)}),p(Y,He)}),p(x,R)};T(Q,x=>{s(l)&&s(o).length>0&&x(K)})}D(x=>{tt(A,1,x),ka(E,"placeholder",i())},[()=>et(rt("input-box",a()&&"large"))]),W("keydown",E,m),W("input",E,C),Ga("blur",E,z),Bn(E,r),p(e,g),Sr()}cn(["keydown","input","click","mousedown"]);var ov=w('<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[720px] flex flex-col items-center"><div class="relative mb-6"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-8">종목명과 질문을 입력하거나, 자유롭게 대화하세요</p> <div class="w-full"><!></div> <div class="mt-5 w-full"><button class="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/30 text-[13px] text-dl-text-dim hover:text-dl-text-muted hover:border-dl-primary/30 hover:bg-dl-bg-card/50 transition-all duration-200"><!> 데이터 탐색</button></div></div></div>');function iv(e,t){kr(t,!0);let r=nt(t,"inputText",15,"");var n=ov(),a=c(n),i=h(c(a),6),o=c(i);Sl(o,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get inputText(){return r()},set inputText(v){r(v)}});var l=h(i,2),d=c(l),u=c(d);en(u,{size:14}),W("click",d,()=>{var v;return(v=t.onOpenExplorer)==null?void 0:v.call(t)}),p(e,n),Sr()}cn(["click"]);var lv=w("<span><!></span>");function oi(e,t){kr(t,!0);let r=nt(t,"variant",3,"default");const n={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var a=lv(),i=c(a);Ns(i,()=>t.children),D(o=>tt(a,1,o),[()=>et(rt("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",n[r()],t.class))]),p(e,a),Sr()}var dv=w('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),cv=w('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),uv=w('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),fv=w('<div class="flex flex-wrap items-center gap-1.5 mb-2"><!> <!> <!></div>'),vv=w('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),pv=w('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),mv=w('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),hv=w('<button class="mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),gv=w('<span class="flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-dl-accent/30 bg-dl-accent/[0.06] text-[11px] text-dl-accent"><!> </span>'),xv=w('<div class="mb-3"><div class="flex flex-wrap items-center gap-1.5"></div></div>'),bv=w('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),_v=w('<!> <span class="text-dl-text-dim"> </span>',1),yv=w('<div class="flex items-center gap-2 text-[11px]"><!></div>'),wv=w('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),kv=w('<div class="flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),Sv=w('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),zv=w('<span class="text-dl-accent/60"> </span>'),Mv=w('<span class="text-dl-success/60"> </span>'),Av=w('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),Cv=w('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),Ev=w('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),Tv=w('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),Pv=w('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),Nv=w("<!>  <div><!></div> <!>",1),$v=w('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),Iv=w('<span class="text-[10px] text-dl-text-dim"> </span>'),Lv=w('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),Ov=w("<button> </button>"),Rv=w('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),jv=w("<button>시스템 프롬프트</button>"),Dv=w("<button>LLM 입력</button>"),Fv=w('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),Bv=w('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),Vv=w('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),Gv=w('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Hv=w("<!> <!>",1);function Uv(e,t){kr(t,!0);let r=H(null),n=H("context"),a=H("raw"),i=pe(()=>{var N,O,ee,de,ue,V;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((N=t.message.toolEvents)==null?void 0:N.length)>0){const y=[...t.message.toolEvents].reverse().find(me=>me.type==="call"),ke=((O=y==null?void 0:y.arguments)==null?void 0:O.module)||((ee=y==null?void 0:y.arguments)==null?void 0:ee.keyword)||"";return`도구 실행 중 — ${(y==null?void 0:y.name)||""}${ke?` (${ke})`:""}`}if(((de=t.message.contexts)==null?void 0:de.length)>0){const y=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(y==null?void 0:y.label)||(y==null?void 0:y.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(ue=t.message.meta)!=null&&ue.company?`${t.message.meta.company} 데이터 검색 중`:(V=t.message.meta)!=null&&V.includedModules?"분석 모듈 선택 완료":"생각 중"}),o=pe(()=>{var N;return t.message.company||((N=t.message.meta)==null?void 0:N.company)||null}),l=pe(()=>{var N,O;return t.message.systemPrompt||((N=t.message.contexts)==null?void 0:N.length)>0||((O=t.message.meta)==null?void 0:O.includedModules)}),d=pe(()=>{var O;const N=(O=t.message.meta)==null?void 0:O.dataYearRange;return N?typeof N=="string"?N:N.min_year&&N.max_year?`${N.min_year}~${N.max_year}년`:null:null});function u(N){if(!N)return 0;const O=(N.match(/[\uac00-\ud7af]/g)||[]).length,ee=N.length-O;return Math.round(O*1.5+ee/3.5)}function v(N){return N>=1e3?(N/1e3).toFixed(1)+"k":String(N)}let m=pe(()=>{var O;let N=0;if(t.message.systemPrompt&&(N+=u(t.message.systemPrompt)),t.message.userContent)N+=u(t.message.userContent);else if(((O=t.message.contexts)==null?void 0:O.length)>0)for(const ee of t.message.contexts)N+=u(ee.text);return N}),b=pe(()=>u(t.message.text));function C(N){const O=N.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(O)||O==="-"||O==="0"}function S(N){if(!N)return"";let O=[],ee=[],de=N.replace(/```(\w*)\n([\s\S]*?)```/g,(V,y,ke)=>{const me=O.length;return O.push(ke.trimEnd()),`
%%CODE_${me}%%
`});de=de.replace(/((?:^\|.+\|$\n?)+)/gm,V=>{const y=V.trim().split(`
`).filter(j=>j.trim());let ke=null,me=-1,lt=[];for(let j=0;j<y.length;j++)if(y[j].slice(1,-1).split("|").map(ie=>ie.trim()).every(ie=>/^[\-:]+$/.test(ie))){me=j;break}me>0?(ke=y[me-1],lt=y.slice(me+1)):(me===0||(ke=y[0]),lt=y.slice(1));let $="<table>";if(ke){const j=ke.slice(1,-1).split("|").map(re=>re.trim());$+="<thead><tr>"+j.map(re=>`<th>${re.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(lt.length>0){$+="<tbody>";for(const j of lt){const re=j.slice(1,-1).split("|").map(ie=>ie.trim());$+="<tr>"+re.map(ie=>{let se=ie.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${C(ie)?' class="num"':""}>${se}</td>`}).join("")+"</tr>"}$+="</tbody>"}$+="</table>";let J=ee.length;return ee.push($),`
%%TABLE_${J}%%
`});let ue=de.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");ue=ue.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,V=>"<ul>"+V.replace(/<br>/g,"")+"</ul>");for(let V=0;V<ee.length;V++)ue=ue.replace(`%%TABLE_${V}%%`,ee[V]);for(let V=0;V<O.length;V++){const y=O[V].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");ue=ue.replace(`%%CODE_${V}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${V}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${y}</code></pre></div>`)}return ue=ue.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(V,y)=>y.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+ue+"</p>"}let z=H(void 0);const g='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',A='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function E(N){var ue;const O=N.target.closest(".code-copy-btn");if(!O)return;const ee=O.closest(".code-block-wrap"),de=((ue=ee==null?void 0:ee.querySelector("code"))==null?void 0:ue.textContent)||"";navigator.clipboard.writeText(de).then(()=>{O.innerHTML=A,setTimeout(()=>{O.innerHTML=g},2e3)})}function P(N){f(r,N,!0),f(n,"context"),f(a,"rendered")}function M(){f(r,0),f(n,"system"),f(a,"raw")}function L(){f(r,0),f(n,"snapshot")}function Q(){f(r,null)}let K=pe(()=>{var O,ee,de;if(!t.message.loading)return[];const N=[];return(O=t.message.meta)!=null&&O.company&&N.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&N.push({label:"핵심 수치 확인",done:!0}),(ee=t.message.meta)!=null&&ee.includedModules&&N.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((de=t.message.contexts)==null?void 0:de.length)>0&&N.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&N.push({label:"프롬프트 조립",done:!0}),t.message.text?N.push({label:"응답 작성 중",done:!1}):N.push({label:s(i)||"준비 중",done:!1}),N});var x=Hv(),R=q(x);{var Y=N=>{var O=dv(),ee=h(c(O),2),de=c(ee),ue=c(de);D(()=>B(ue,t.message.text)),p(N,O)},fe=N=>{var O=$v(),ee=h(c(O),2),de=c(ee);{var ue=j=>{var re=fv(),ie=c(re);{var se=X=>{oi(X,{variant:"muted",children:(te,Z)=>{var le=ba();D(()=>B(le,s(o))),p(te,le)},$$slots:{default:!0}})};T(ie,X=>{s(o)&&X(se)})}var Ce=h(ie,2);{var Oe=X=>{oi(X,{variant:"accent",children:(te,Z)=>{var le=ba();D(()=>B(le,s(d))),p(te,le)},$$slots:{default:!0}})};T(Ce,X=>{s(d)&&X(Oe)})}var Ee=h(Ce,2);{var qe=X=>{var te=xe(),Z=q(te);it(Z,17,()=>t.message.contexts,ot,(le,Ue,Ke)=>{var dt=cv(),mt=c(dt);en(mt,{size:10,class:"flex-shrink-0"});var jt=h(mt);D(()=>B(jt,` ${(s(Ue).label||s(Ue).module)??""}`)),W("click",dt,()=>P(Ke)),p(le,dt)}),p(X,te)},ve=X=>{var te=uv(),Z=c(te);en(Z,{size:10,class:"flex-shrink-0"});var le=h(Z);D(()=>B(le,` 모듈 ${t.message.meta.includedModules.length??""}개`)),p(X,te)};T(Ee,X=>{var te,Z,le;((te=t.message.contexts)==null?void 0:te.length)>0?X(qe):((le=(Z=t.message.meta)==null?void 0:Z.includedModules)==null?void 0:le.length)>0&&X(ve,1)})}p(j,re)};T(de,j=>{var re,ie;(s(o)||s(d)||((re=t.message.contexts)==null?void 0:re.length)>0||(ie=t.message.meta)!=null&&ie.includedModules)&&j(ue)})}var V=h(de,2);{var y=j=>{var re=hv(),ie=c(re);it(ie,21,()=>t.message.snapshot.items,ot,(Oe,Ee)=>{const qe=pe(()=>s(Ee).status==="good"?"text-dl-success":s(Ee).status==="danger"?"text-dl-primary-light":s(Ee).status==="caution"?"text-amber-400":"text-dl-text");var ve=vv(),X=c(ve),te=c(X),Z=h(X,2),le=c(Z);D(Ue=>{B(te,s(Ee).label),tt(Z,1,Ue),B(le,s(Ee).value)},[()=>et(rt("text-[14px] font-semibold leading-snug mt-0.5",s(qe)))]),p(Oe,ve)});var se=h(ie,2);{var Ce=Oe=>{var Ee=mv();it(Ee,21,()=>t.message.snapshot.warnings,ot,(qe,ve)=>{var X=pv(),te=c(X);Vf(te,{size:10});var Z=h(te);D(()=>B(Z,` ${s(ve)??""}`)),p(qe,X)}),p(Oe,Ee)};T(se,Oe=>{var Ee;((Ee=t.message.snapshot.warnings)==null?void 0:Ee.length)>0&&Oe(Ce)})}W("click",re,L),p(j,re)};T(V,j=>{var re,ie;((ie=(re=t.message.snapshot)==null?void 0:re.items)==null?void 0:ie.length)>0&&j(y)})}var ke=h(V,2);{var me=j=>{var re=xv(),ie=c(re);it(ie,21,()=>t.message.toolEvents,ot,(se,Ce)=>{var Oe=xe(),Ee=q(Oe);{var qe=ve=>{const X=pe(()=>{var Ue,Ke,dt,mt;return((Ue=s(Ce).arguments)==null?void 0:Ue.module)||((Ke=s(Ce).arguments)==null?void 0:Ke.keyword)||((dt=s(Ce).arguments)==null?void 0:dt.engine)||((mt=s(Ce).arguments)==null?void 0:mt.name)||""});var te=gv(),Z=c(te);Gf(Z,{size:11});var le=h(Z);D(()=>B(le,` ${s(Ce).name??""}${s(X)?`: ${s(X)}`:""}`)),p(ve,te)};T(Ee,ve=>{s(Ce).type==="call"&&ve(qe)})}p(se,Oe)}),p(j,re)};T(ke,j=>{var re;((re=t.message.toolEvents)==null?void 0:re.length)>0&&j(me)})}var lt=h(ke,2);{var $=j=>{var re=wv(),ie=c(re);it(ie,21,()=>s(K),ot,(se,Ce)=>{var Oe=yv(),Ee=c(Oe);{var qe=X=>{var te=bv(),Z=h(q(te),2),le=c(Z);D(()=>B(le,s(Ce).label)),p(X,te)},ve=X=>{var te=_v(),Z=q(te);Bt(Z,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var le=h(Z,2),Ue=c(le);D(()=>B(Ue,s(Ce).label)),p(X,te)};T(Ee,X=>{s(Ce).done?X(qe):X(ve,-1)})}p(se,Oe)}),p(j,re)},J=j=>{var re=Nv(),ie=q(re);{var se=ve=>{var X=kv(),te=c(X);Bt(te,{size:12,class:"animate-spin flex-shrink-0"});var Z=h(te,2),le=c(Z);D(()=>B(le,s(i))),p(ve,X)};T(ie,ve=>{t.message.loading&&ve(se)})}var Ce=h(ie,2),Oe=c(Ce);Lo(Oe,()=>S(t.message.text)),Xs(Ce,ve=>f(z,ve),()=>s(z));var Ee=h(Ce,2);{var qe=ve=>{var X=Pv(),te=c(X);{var Z=Fe=>{var Re=Sv(),Je=c(Re);Ef(Je,{size:10});var F=h(Je);D(()=>B(F,` ${t.message.duration??""}초`)),p(Fe,Re)};T(te,Fe=>{t.message.duration&&Fe(Z)})}var le=h(te,2);{var Ue=Fe=>{var Re=Av(),Je=c(Re);{var F=ae=>{var we=zv(),Ye=c(we);D(Ge=>B(Ye,`↑${Ge??""}`),[()=>v(s(m))]),p(ae,we)};T(Je,ae=>{s(m)>0&&ae(F)})}var be=h(Je,2);{var oe=ae=>{var we=Mv(),Ye=c(we);D(Ge=>B(Ye,`↓${Ge??""}`),[()=>v(s(b))]),p(ae,we)};T(be,ae=>{s(b)>0&&ae(oe)})}p(Fe,Re)};T(le,Fe=>{(s(m)>0||s(b)>0)&&Fe(Ue)})}var Ke=h(le,2);{var dt=Fe=>{var Re=Cv(),Je=c(Re);Rf(Je,{size:10}),W("click",Re,()=>{var F;return(F=t.onRegenerate)==null?void 0:F.call(t)}),p(Fe,Re)};T(Ke,Fe=>{t.onRegenerate&&Fe(dt)})}var mt=h(Ke,2);{var jt=Fe=>{var Re=Ev(),Je=c(Re);Qo(Je,{size:10}),W("click",Re,M),p(Fe,Re)};T(mt,Fe=>{t.message.systemPrompt&&Fe(jt)})}var Gt=h(mt,2);{var er=Fe=>{var Re=Tv(),Je=c(Re);_a(Je,{size:10});var F=h(Je);D((be,oe)=>B(F,` LLM 입력 (${be??""}자 · ~${oe??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>v(u(t.message.userContent))]),W("click",Re,()=>{f(r,0),f(n,"userContent"),f(a,"raw")}),p(Fe,Re)};T(Gt,Fe=>{t.message.userContent&&Fe(er)})}p(ve,X)};T(Ee,ve=>{!t.message.loading&&(t.message.duration||s(l)||t.onRegenerate)&&ve(qe)})}D(ve=>tt(Ce,1,ve),[()=>et(rt("prose-dartlab text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),W("click",Ce,E),p(j,re)};T(lt,j=>{t.message.loading&&!t.message.text?j($):j(J,-1)})}p(N,O)};T(R,N=>{t.message.role==="user"?N(Y):N(fe,-1)})}var Ae=h(R,2);{var He=N=>{const O=pe(()=>s(n)==="system"),ee=pe(()=>s(n)==="userContent"),de=pe(()=>s(n)==="context"),ue=pe(()=>s(n)==="snapshot"),V=pe(()=>{var F;return s(de)?(F=t.message.contexts)==null?void 0:F[s(r)]:null}),y=pe(()=>{var F,be;return s(ue)?"핵심 수치 (원본 데이터)":s(O)?"시스템 프롬프트":s(ee)?"LLM에 전달된 입력":((F=s(V))==null?void 0:F.label)||((be=s(V))==null?void 0:be.module)||""}),ke=pe(()=>{var F;return s(ue)?JSON.stringify(t.message.snapshot,null,2):s(O)?t.message.systemPrompt:s(ee)?t.message.userContent:(F=s(V))==null?void 0:F.text});var me=Gv(),lt=c(me),$=c(lt),J=c($),j=c(J),re=c(j);{var ie=F=>{en(F,{size:15,class:"text-dl-success flex-shrink-0"})},se=F=>{Qo(F,{size:15,class:"text-dl-primary-light flex-shrink-0"})},Ce=F=>{_a(F,{size:15,class:"text-dl-accent flex-shrink-0"})},Oe=F=>{en(F,{size:15,class:"flex-shrink-0"})};T(re,F=>{s(ue)?F(ie):s(O)?F(se,1):s(ee)?F(Ce,2):F(Oe,-1)})}var Ee=h(re,2),qe=c(Ee),ve=h(Ee,2);{var X=F=>{var be=Iv(),oe=c(be);D(ae=>B(oe,`(${ae??""}자)`),[()=>{var ae,we;return(we=(ae=s(ke))==null?void 0:ae.length)==null?void 0:we.toLocaleString()}]),p(F,be)};T(ve,F=>{s(O)&&F(X)})}var te=h(j,2),Z=c(te);{var le=F=>{var be=Lv(),oe=c(be),ae=c(oe);_a(ae,{size:11});var we=h(oe,2),Ye=c(we);Tf(Ye,{size:11}),D((Ge,at)=>{tt(oe,1,Ge),tt(we,1,at)},[()=>et(rt("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",s(a)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>et(rt("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",s(a)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),W("click",oe,()=>f(a,"rendered")),W("click",we,()=>f(a,"raw")),p(F,be)};T(Z,F=>{s(de)&&F(le)})}var Ue=h(Z,2),Ke=c(Ue);to(Ke,{size:18});var dt=h(J,2);{var mt=F=>{var be=Rv(),oe=c(be);it(oe,21,()=>t.message.contexts,ot,(ae,we,Ye)=>{var Ge=Ov(),at=c(Ge);D(st=>{tt(Ge,1,st),B(at,t.message.contexts[Ye].label||t.message.contexts[Ye].module)},[()=>et(rt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",Ye===s(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),W("click",Ge,()=>{f(r,Ye,!0)}),p(ae,Ge)}),p(F,be)};T(dt,F=>{var be;s(de)&&((be=t.message.contexts)==null?void 0:be.length)>1&&F(mt)})}var jt=h(dt,2);{var Gt=F=>{var be=Fv(),oe=c(be),ae=c(oe);{var we=at=>{var st=jv();D(Lt=>tt(st,1,Lt),[()=>et(rt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",s(O)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),W("click",st,()=>{f(n,"system")}),p(at,st)};T(ae,at=>{t.message.systemPrompt&&at(we)})}var Ye=h(ae,2);{var Ge=at=>{var st=Dv();D(Lt=>tt(st,1,Lt),[()=>et(rt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",s(ee)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),W("click",st,()=>{f(n,"userContent")}),p(at,st)};T(Ye,at=>{t.message.userContent&&at(Ge)})}p(F,be)};T(jt,F=>{!s(de)&&!s(ue)&&F(Gt)})}var er=h($,2),Fe=c(er);{var Re=F=>{var be=Bv(),oe=c(be);Lo(oe,()=>{var ae;return S((ae=s(V))==null?void 0:ae.text)}),p(F,be)},Je=F=>{var be=Vv(),oe=c(be);D(()=>B(oe,s(ke))),p(F,be)};T(Fe,F=>{s(de)&&s(a)==="rendered"?F(Re):F(Je,-1)})}D(()=>B(qe,s(y))),W("click",me,F=>{F.target===F.currentTarget&&Q()}),W("keydown",me,F=>{F.key==="Escape"&&Q()}),W("click",Ue,Q),p(N,me)};T(Ae,N=>{s(r)!==null&&N(He)})}p(e,x),Sr()}cn(["click","keydown"]);var Wv=w('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),qv=w('<div class="flex justify-end gap-2 mb-1.5"><button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 데이터</button> <!></div>'),Kv=w('<div class="flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="max-w-[720px] mx-auto px-5 pt-14 pb-8 space-y-8"></div></div> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function Yv(e,t){kr(t,!0);function r(E){if(a())return!1;for(let P=n().length-1;P>=0;P--)if(n()[P].role==="assistant"&&!n()[P].error&&n()[P].text)return P===E;return!1}let n=nt(t,"messages",19,()=>[]),a=nt(t,"isLoading",3,!1),i=nt(t,"inputText",15,""),o=nt(t,"scrollTrigger",3,0),l,d=!1;function u(){if(!l)return;const{scrollTop:E,scrollHeight:P,clientHeight:M}=l;d=P-E-M>80}ya(()=>{o(),!(!l||d)&&requestAnimationFrame(()=>{l&&(l.scrollTop=l.scrollHeight)})});var v=Kv(),m=c(v),b=c(m);it(b,21,n,ot,(E,P,M)=>{{let L=pe(()=>r(M)?t.onRegenerate:void 0);Uv(E,{get message(){return s(P)},get onRegenerate(){return s(L)}})}}),Xs(m,E=>l=E,()=>l);var C=h(m,2),S=c(C),z=c(S);{var g=E=>{var P=qv(),M=c(P),L=c(M);en(L,{size:10});var Q=h(M,2);{var K=x=>{var R=Wv(),Y=c(R);Vn(Y,{size:10}),W("click",R,function(...fe){var Ae;(Ae=t.onExport)==null||Ae.apply(this,fe)}),p(x,R)};T(Q,x=>{n().length>1&&t.onExport&&x(K)})}W("click",M,()=>{var x;return(x=t.onOpenExplorer)==null?void 0:x.call(t)}),p(E,P)};T(z,E=>{a()||E(g)})}var A=h(z,2);Sl(A,{get isLoading(){return a()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get inputText(){return i()},set inputText(E){i(E)}}),Ga("scroll",m,u),p(e,v),Sr()}cn(["click"]);var Jv=w('<button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div><div class="text-[14px] font-semibold text-dl-text"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div>',1),Xv=w('<!> <div class="text-[14px] font-semibold text-dl-text">데이터 탐색</div>',1),Zv=w('<button class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-dl-success/15 text-dl-success text-[11px] font-medium hover:bg-dl-success/25 transition-colors disabled:opacity-40"><!> 전체 Excel</button>'),Qv=w('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),ep=w('<button class="flex items-center gap-3 w-full px-4 py-3 rounded-xl border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all"><div class="flex-1 min-w-0"><div class="text-[13px] font-medium text-dl-text"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!> <!></button>'),tp=w('<div class="space-y-1"></div>'),rp=w('<div class="text-center py-16 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),np=w('<div class="text-center py-16"><!> <div class="text-[13px] text-dl-text-dim mb-1">종목을 검색하여 데이터를 탐색하세요</div> <div class="text-[11px] text-dl-text-dim/70">재무제표, 정기보고서, 공시 데이터를 직접 확인하고 Excel로 내보낼 수 있습니다</div></div>'),ap=w('<div class="flex-1 overflow-y-auto px-5 py-4"><div class="max-w-lg mx-auto"><div class="relative mb-4"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="w-full pl-9 pr-4 py-3 bg-dl-bg-darker border border-dl-border rounded-xl text-[13px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/40 transition-colors"/> <!></div> <!></div></div>'),sp=w('<div class="flex items-center justify-center py-12 gap-2 text-[12px] text-dl-text-dim"><!> 탐색 중...</div>'),op=w('<button><!> <span class="flex-1 min-w-0 truncate"> </span></button>'),ip=w('<div class="ml-2 border-l border-dl-border/30 pl-1"></div>'),lp=w('<div class="mx-2 mb-1"><button class="flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-left hover:bg-white/[0.03] transition-colors"><!> <span class="text-[11px] font-medium text-dl-text-muted flex-1"> </span> <span class="text-[9px] text-dl-text-dim"> </span></button> <!></div>'),dp=w('<div class="px-3 pt-3 pb-1"><div class="text-[10px] text-dl-text-dim"> </div></div> <!>',1),cp=w('<div class="flex items-center justify-center h-full text-center"><div><!> <div class="text-[13px] text-dl-text-dim">좌측에서 모듈을 선택하세요</div> <div class="text-[11px] text-dl-text-dim/60 mt-1">데이터를 바로 확인할 수 있습니다</div></div></div>'),up=w('<div class="flex items-center justify-center h-full gap-2 text-[13px] text-dl-text-dim"><!> </div>'),fp=w('<span class="text-[10px] text-dl-text-dim ml-2"> </span>'),vp=w('<button class="flex items-center gap-1 px-2 py-1 rounded-lg bg-dl-success/10 text-dl-success text-[10px] hover:bg-dl-success/20 transition-colors"><!> Excel</button>'),pp=w('<th class="px-3 py-2 text-left text-dl-text-muted font-medium bg-dl-bg-darker border-b border-dl-border/30 whitespace-nowrap text-[10px]"> </th>'),mp=w("<td> </td>"),hp=w('<tr class="hover:bg-white/[0.02]"></tr>'),gp=w('<div class="px-4 py-2 text-[10px] text-dl-warning border-t border-dl-border/20"> </div>'),xp=w('<div class="overflow-x-auto"><table class="w-full text-[11px] border-collapse"><thead class="sticky top-[41px] z-[5]"><tr></tr></thead><tbody></tbody></table></div> <!>',1),bp=w('<div class="flex gap-3 px-3 py-2 rounded-lg bg-dl-bg-darker/50"><span class="text-[11px] text-dl-text-muted font-medium min-w-[140px] flex-shrink-0"> </span> <span class="text-[11px] text-dl-text-dim break-all"> </span></div>'),_p=w('<div class="p-4 space-y-1.5"></div>'),yp=w('<div class="mt-2 text-[10px] text-dl-warning">내용이 잘려서 표시됩니다</div>'),wp=w('<div class="p-4"><pre class="text-[11px] text-dl-text-muted whitespace-pre-wrap leading-relaxed"> </pre> <!></div>'),kp=w('<div class="flex items-center justify-center h-full text-[13px] text-dl-primary-light"> </div>'),Sp=w('<div class="p-4"><pre class="text-[11px] text-dl-text-muted whitespace-pre-wrap"> </pre></div>'),zp=w('<div class="sticky top-0 z-10 flex items-center justify-between px-4 py-2.5 bg-dl-bg-card/95 backdrop-blur-sm border-b border-dl-border/30"><div><span class="text-[12px] font-medium text-dl-text"> </span> <!></div> <!></div> <!>',1),Mp=w('<div class="w-[260px] flex-shrink-0 border-r border-dl-border/50 overflow-y-auto"><!></div> <div class="flex-1 overflow-auto min-w-0"><!></div>',1),Ap=w('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-5xl max-h-[88vh] bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden flex flex-col"><div class="flex items-center justify-between px-5 pt-4 pb-3 flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center gap-3"><!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 flex min-h-0"><!></div></div></div>');function Cp(e,t){kr(t,!0);let r=H(""),n=H(wt([])),a=H(!1),i=null,o=H(null),l=H(null),d=H(!1),u=H(wt(new Set)),v=H(null),m=H(null),b=H(!1),C=H(!1);function S(){const $=s(r).trim();if(i&&clearTimeout(i),$.length<2){f(n,[],!0);return}f(a,!0),i=setTimeout(async()=>{var J;try{const j=await dl($);f(n,((J=j.results)==null?void 0:J.slice(0,8))||[],!0)}catch{f(n,[],!0)}f(a,!1)},300)}async function z($){f(o,$,!0),f(r,""),f(n,[],!0),f(d,!0),f(v,null),f(m,null);try{f(l,await wu($.stockCode),!0);const J=Object.keys(s(l).categories||{});f(u,new Set(J.slice(0,2)),!0)}catch{f(l,null)}f(d,!1)}function g(){f(o,null),f(l,null),f(v,null),f(m,null)}async function A($){if($.available){f(v,$,!0),f(b,!0),f(m,null);try{f(m,await ku(s(o).stockCode,$.name,100),!0)}catch(J){f(m,{type:"error",error:J.message},!0)}f(b,!1)}}function E($){const J=new Set(s(u));J.has($)?J.delete($):J.add($),f(u,J,!0)}async function P(){if(s(o)){f(C,!0);try{await Vo(s(o).stockCode)}catch{}f(C,!1)}}const M={finance:"재무제표",report:"정기보고서",disclosure:"공시 서술",notes:"K-IFRS 주석",analysis:"분석",raw:"원본 데이터"};function L($){return M[$]||$}function Q($){return`${$.filter(j=>j.available).length}/${$.length}`}function K($){if($==null)return"-";if(typeof $=="number"){if(Number.isInteger($)&&Math.abs($)>=1e3)return $.toLocaleString("ko-KR");if(!Number.isInteger($))return $.toLocaleString("ko-KR",{maximumFractionDigits:2})}return String($)}var x=Ap(),R=c(x),Y=c(R),fe=c(Y),Ae=c(fe);{var He=$=>{var J=Jv(),j=q(J),re=c(j);zf(re,{size:16});var ie=h(j,2),se=c(ie),Ce=c(se),Oe=h(se,2),Ee=c(Oe);D(()=>{B(Ce,s(o).corpName),B(Ee,s(o).stockCode)}),W("click",j,g),p($,J)},N=$=>{var J=Xv(),j=q(J);en(j,{size:16,class:"text-dl-text-muted"}),p($,J)};T(Ae,$=>{s(o)?$(He):$(N,-1)})}var O=h(fe,2),ee=c(O);{var de=$=>{var J=Zv(),j=c(J);{var re=se=>{Bt(se,{size:12,class:"animate-spin"})},ie=se=>{Vn(se,{size:12})};T(j,se=>{s(C)?se(re):se(ie,-1)})}D(()=>J.disabled=s(C)),W("click",J,P),p($,J)};T(ee,$=>{s(o)&&$(de)})}var ue=h(ee,2),V=c(ue);to(V,{size:16});var y=h(Y,2),ke=c(y);{var me=$=>{var J=ap(),j=c(J),re=c(j),ie=c(re);eo(ie,{size:14,class:"absolute left-3 top-1/2 -translate-y-1/2 text-dl-text-dim pointer-events-none"});var se=h(ie,2),Ce=h(se,2);{var Oe=Z=>{Bt(Z,{size:14,class:"absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-dl-text-dim"})};T(Ce,Z=>{s(a)&&Z(Oe)})}var Ee=h(re,2);{var qe=Z=>{var le=tp();it(le,21,()=>s(n),ot,(Ue,Ke)=>{var dt=ep(),mt=c(dt),jt=c(mt),Gt=c(jt),er=h(jt,2),Fe=c(er),Re=h(mt,2);{var Je=be=>{var oe=Qv(),ae=c(oe);D(()=>B(ae,s(Ke).sector)),p(be,oe)};T(Re,be=>{s(Ke).sector&&be(Je)})}var F=h(Re,2);ei(F,{size:14,class:"text-dl-text-dim flex-shrink-0"}),D(()=>{B(Gt,s(Ke).corpName),B(Fe,`${s(Ke).stockCode??""} · ${(s(Ke).market||"")??""}`)}),W("click",dt,()=>z(s(Ke))),p(Ue,dt)}),p(Z,le)},ve=Z=>{var le=rp();p(Z,le)},X=pe(()=>s(r).trim().length>=2&&!s(a)),te=Z=>{var le=np(),Ue=c(le);en(Ue,{size:32,class:"mx-auto mb-3 text-dl-text-dim/50"}),p(Z,le)};T(Ee,Z=>{s(n).length>0?Z(qe):s(X)?Z(ve,1):Z(te,-1)})}W("input",se,S),Bn(se,()=>s(r),Z=>f(r,Z)),p($,J)},lt=$=>{var J=Mp(),j=q(J),re=c(j);{var ie=X=>{var te=sp(),Z=c(te);Bt(Z,{size:14,class:"animate-spin"}),p(X,te)},se=X=>{var te=dp(),Z=q(te),le=c(Z),Ue=c(le),Ke=h(Z,2);it(Ke,17,()=>Object.entries(s(l).categories),ot,(dt,mt)=>{var jt=pe(()=>Va(s(mt),2));let Gt=()=>s(jt)[0],er=()=>s(jt)[1];var Fe=lp(),Re=c(Fe),Je=c(Re);{var F=ht=>{Cf(ht,{size:12,class:"text-dl-text-dim flex-shrink-0"})},be=pe(()=>s(u).has(Gt())),oe=ht=>{ei(ht,{size:12,class:"text-dl-text-dim flex-shrink-0"})};T(Je,ht=>{s(be)?ht(F):ht(oe,-1)})}var ae=h(Je,2),we=c(ae),Ye=h(ae,2),Ge=c(Ye),at=h(Re,2);{var st=ht=>{var Ot=ip();it(Ot,21,er,ot,(tr,ct)=>{var rr=op(),In=c(rr);{var fn=At=>{si(At,{size:10,class:"flex-shrink-0"})},vn=At=>{_a(At,{size:10,class:"flex-shrink-0"})};T(In,At=>{s(ct).dataType==="timeseries"||s(ct).dataType==="table"?At(fn):At(vn,-1)})}var Ln=h(In,2),sa=c(Ln);D(At=>{tt(rr,1,At),rr.disabled=!s(ct).available,B(sa,s(ct).label)},[()=>{var At;return et(rt("flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-left text-[11px] transition-colors",!s(ct).available&&"opacity-30 cursor-default",s(ct).available&&((At=s(v))==null?void 0:At.name)===s(ct).name?"bg-dl-primary/10 text-dl-primary-light":s(ct).available?"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text":""))}]),W("click",rr,()=>A(s(ct))),p(tr,rr)}),p(ht,Ot)},Lt=pe(()=>s(u).has(Gt()));T(at,ht=>{s(Lt)&&ht(st)})}D((ht,Ot)=>{B(we,ht),B(Ge,Ot)},[()=>L(Gt()),()=>Q(er())]),W("click",Re,()=>E(Gt())),p(dt,Fe)}),D(()=>B(Ue,`${s(l).availableSources??""}개 사용 가능`)),p(X,te)};T(re,X=>{s(d)?X(ie):s(l)&&X(se,1)})}var Ce=h(j,2),Oe=c(Ce);{var Ee=X=>{var te=cp(),Z=c(te),le=c(Z);si(le,{size:32,class:"mx-auto mb-3 text-dl-text-dim/30"}),p(X,te)},qe=X=>{var te=up(),Z=c(te);Bt(Z,{size:16,class:"animate-spin"});var le=h(Z);D(()=>B(le,` ${s(v).label??""} 로딩 중...`)),p(X,te)},ve=X=>{var te=zp(),Z=q(te),le=c(Z),Ue=c(le),Ke=c(Ue),dt=h(Ue,2);{var mt=oe=>{var ae=fp(),we=c(ae);D(()=>B(we,`${s(m).totalRows??""}행 × ${s(m).columns.length??""}열`)),p(oe,ae)};T(dt,oe=>{s(m).type==="table"&&oe(mt)})}var jt=h(le,2);{var Gt=oe=>{var ae=vp(),we=c(ae);Vn(we,{size:10}),W("click",ae,async()=>{try{await Vo(s(o).stockCode,[s(v).name])}catch{}}),p(oe,ae)};T(jt,oe=>{s(o)&&oe(Gt)})}var er=h(Z,2);{var Fe=oe=>{var ae=xp(),we=q(ae),Ye=c(we),Ge=c(Ye),at=c(Ge);it(at,21,()=>s(m).columns,ot,(Ot,tr)=>{var ct=pp(),rr=c(ct);D(()=>B(rr,s(tr))),p(Ot,ct)});var st=h(Ge);it(st,21,()=>s(m).rows,ot,(Ot,tr)=>{var ct=hp();it(ct,21,()=>s(m).columns,ot,(rr,In)=>{const fn=pe(()=>s(tr)[s(In)]);var vn=mp(),Ln=c(vn);D((sa,At)=>{tt(vn,1,sa),B(Ln,At)},[()=>et(rt("px-3 py-1.5 border-b border-dl-border/10 whitespace-nowrap",typeof s(fn)=="number"?"text-right font-mono text-dl-accent-light text-[10px]":"text-dl-text-muted")),()=>K(s(fn))]),p(rr,vn)}),p(Ot,ct)});var Lt=h(we,2);{var ht=Ot=>{var tr=gp(),ct=c(tr);D(()=>B(ct,`상위 ${s(m).rows.length??""}행만 표시 (전체 ${s(m).totalRows??""}행)`)),p(Ot,tr)};T(Lt,Ot=>{s(m).truncated&&Ot(ht)})}p(oe,ae)},Re=oe=>{var ae=_p();it(ae,21,()=>Object.entries(s(m).data),ot,(we,Ye)=>{var Ge=pe(()=>Va(s(Ye),2));let at=()=>s(Ge)[0],st=()=>s(Ge)[1];var Lt=bp(),ht=c(Lt),Ot=c(ht),tr=h(ht,2),ct=c(tr);D(()=>{B(Ot,at()),B(ct,st()??"-")}),p(we,Lt)}),p(oe,ae)},Je=oe=>{var ae=wp(),we=c(ae),Ye=c(we),Ge=h(we,2);{var at=st=>{var Lt=yp();p(st,Lt)};T(Ge,st=>{s(m).truncated&&st(at)})}D(()=>B(Ye,s(m).text)),p(oe,ae)},F=oe=>{var ae=kp(),we=c(ae);D(()=>B(we,s(m).error||"데이터를 불러올 수 없습니다")),p(oe,ae)},be=oe=>{var ae=Sp(),we=c(ae),Ye=c(we);D(Ge=>B(Ye,Ge),[()=>s(m).data||JSON.stringify(s(m),null,2)]),p(oe,ae)};T(er,oe=>{s(m).type==="table"?oe(Fe):s(m).type==="dict"?oe(Re,1):s(m).type==="text"?oe(Je,2):s(m).type==="error"?oe(F,3):oe(be,-1)})}D(()=>B(Ke,s(v).label)),p(X,te)};T(Oe,X=>{s(v)?s(b)?X(qe,1):s(m)&&X(ve,2):X(Ee)})}p($,J)};T(ke,$=>{s(o)?$(lt,-1):$(me)})}W("click",x,$=>{var J;$.target===$.currentTarget&&((J=t.onClose)==null||J.call(t))}),W("keydown",x,()=>{}),W("click",ue,()=>{var $;return($=t.onClose)==null?void 0:$.call(t)}),p(e,x),Sr()}cn(["click","keydown","input"]);var Ep=w('<div class="sidebar-overlay"></div>'),Tp=w("<!> <span>확인 중...</span>",1),Pp=w("<!> <span>설정 필요</span>",1),Np=w('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),$p=w('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!> <!>',1),Ip=w('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/80 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text-muted">AI Provider 확인 중...</div></div></div>'),Lp=w('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-primary/30 bg-dl-primary/5 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text">AI Provider가 설정되지 않았습니다</div> <div class="text-[11px] text-dl-text-muted mt-0.5">대화를 시작하려면 Provider를 설정해주세요</div></div> <button class="px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors flex-shrink-0">설정하기</button></div>'),Op=w('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),Rp=w('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),jp=w('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),Dp=w('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),Fp=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),Bp=w('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),Vp=w('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),Gp=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),Hp=w('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),Up=w('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),Wp=w('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),qp=w('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @anthropic-ai/claude-code</div></div></div>'),Kp=w('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">인증</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">claude auth login</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">Claude Pro 또는 Max 구독이 필요합니다</span></div>',1),Yp=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2">설치 완료 후 새로고침하세요</div></div>'),Jp=w("<!> 브라우저에서 로그인 중...",1),Xp=w("<!> OpenAI 계정으로 로그인",1),Zp=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2.5">ChatGPT 계정으로 로그인하여 사용하세요</div> <button class="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div></div>'),Qp=w('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),em=w('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),tm=w("<button> <!></button>"),rm=w('<div class="flex flex-wrap gap-1.5"></div>'),nm=w('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),am=w('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),sm=w('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),om=w('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),im=w('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),lm=w('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),dm=w('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),cm=w("<!> <!> <!> <!> <!> <!> <!>",1),um=w('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),fm=w('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden"><div class="flex items-center justify-between px-6 pt-5 pb-3"><div class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),vm=w('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5"><div class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),pm=w('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn"><div> </div></div>'),mm=w('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-0 left-0 right-0 z-10 pointer-events-none"><div class="flex items-center justify-between px-3 h-11 pointer-events-auto" style="background: linear-gradient(to bottom, rgba(5,8,17,0.92) 40%, transparent);"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center gap-1"><a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <div class="w-px h-4 bg-dl-border mx-1"></div> <button><!> <!></button></div></div> <!></div> <!></div></div>  <!> <!> <!> <!>',1);function hm(e,t){kr(t,!0);let r=H(""),n=H(!1),a=H(null),i=H(wt({})),o=H(wt({})),l=H(null),d=H(null),u=H(wt([])),v=H(!0),m=H(0),b=H(!0),C=H(""),S=H(!1),z=H(null),g=H(wt({})),A=H(wt({})),E=H(""),P=H(!1),M=H(null),L=H(""),Q=H(!1),K=H(""),x=H(0),R=H(null),Y=H(!1),fe=H(wt({})),Ae=H(!1),He=H(!1);function N(){f(He,window.innerWidth<=768),s(He)&&f(v,!1)}ya(()=>(N(),window.addEventListener("resize",N),()=>window.removeEventListener("resize",N)));let O=H(null),ee=H(""),de=H("error"),ue=H(!1);function V(_,I="error",ce=4e3){f(ee,_,!0),f(de,I,!0),f(ue,!0),setTimeout(()=>{f(ue,!1)},ce)}const y=xf();ya(()=>{lt()});let ke=H(wt({})),me=H(wt({}));async function lt(){var _,I,ce;f(b,!0);try{const je=await hu();f(i,je.providers||{},!0),f(o,je.ollama||{},!0),f(ke,je.codex||{},!0),f(me,je.claudeCode||{},!0),f(fe,je.chatgpt||{},!0),je.version&&f(C,je.version,!0);const De=localStorage.getItem("dartlab-provider"),ut=localStorage.getItem("dartlab-model");if(De&&((_=s(i)[De])!=null&&_.available)){f(l,De,!0),f(z,De,!0),await Fn(De,ut),await $(De);const Te=s(g)[De]||[];ut&&Te.includes(ut)?f(d,ut,!0):Te.length>0&&(f(d,Te[0],!0),localStorage.setItem("dartlab-model",s(d))),f(u,Te,!0),f(b,!1);return}if(De&&s(i)[De]){f(l,De,!0),f(z,De,!0),await $(De);const Te=s(g)[De]||[];f(u,Te,!0),ut&&Te.includes(ut)?f(d,ut,!0):Te.length>0&&f(d,Te[0],!0),f(b,!1);return}for(const Te of["chatgpt","codex","ollama"])if((I=s(i)[Te])!=null&&I.available){f(l,Te,!0),f(z,Te,!0),await Fn(Te),await $(Te);const Rr=s(g)[Te]||[];f(u,Rr,!0),f(d,((ce=s(i)[Te])==null?void 0:ce.model)||(Rr.length>0?Rr[0]:null),!0),s(d)&&localStorage.setItem("dartlab-model",s(d));break}}catch{}f(b,!1)}async function $(_){f(A,{...s(A),[_]:!0},!0);try{const I=await gu(_);f(g,{...s(g),[_]:I.models||[]},!0)}catch{f(g,{...s(g),[_]:[]},!0)}f(A,{...s(A),[_]:!1},!0)}async function J(_){var ce;f(l,_,!0),f(d,null),f(z,_,!0),localStorage.setItem("dartlab-provider",_),localStorage.removeItem("dartlab-model"),f(E,""),f(M,null);try{await Fn(_)}catch{}await $(_);const I=s(g)[_]||[];if(f(u,I,!0),I.length>0){f(d,((ce=s(i)[_])==null?void 0:ce.model)||I[0],!0),localStorage.setItem("dartlab-model",s(d));try{await Fn(_,s(d))}catch{}}}async function j(_){f(d,_,!0),localStorage.setItem("dartlab-model",_);try{await Fn(s(l),_)}catch{}}function re(_){s(z)===_?f(z,null):(f(z,_,!0),$(_))}async function ie(){const _=s(E).trim();if(!(!_||!s(l))){f(P,!0),f(M,null);try{const I=await Fn(s(l),s(d),_);I.available?(f(M,"success"),s(i)[s(l)]={...s(i)[s(l)],available:!0,model:I.model},!s(d)&&I.model&&f(d,I.model,!0),await $(s(l)),f(u,s(g)[s(l)]||[],!0),V("API 키 인증 성공","success")):f(M,"error")}catch{f(M,"error")}f(P,!1)}}async function se(){if(!s(Y)){f(Y,!0);try{const{authUrl:_}=await bu();window.open(_,"dartlab-oauth","width=600,height=700");const I=setInterval(async()=>{var ce;try{const je=await _u();je.done&&(clearInterval(I),f(Y,!1),je.error?V(`인증 실패: ${je.error}`):(V("ChatGPT 인증 성공","success"),await lt(),(ce=s(i).chatgpt)!=null&&ce.available&&await J("chatgpt")))}catch{clearInterval(I),f(Y,!1)}},2e3);setTimeout(()=>{clearInterval(I),s(Y)&&(f(Y,!1),V("인증 시간이 초과되었습니다. 다시 시도해주세요."))},12e4)}catch(_){f(Y,!1),V(`OAuth 시작 실패: ${_.message}`)}}}async function Ce(){try{await yu(),f(fe,{authenticated:!1},!0),s(l)==="chatgpt"&&f(i,{...s(i),chatgpt:{...s(i).chatgpt,available:!1}},!0),V("ChatGPT 로그아웃 완료","success"),await lt()}catch{V("로그아웃 실패")}}function Oe(){const _=s(L).trim();!_||s(Q)||(f(Q,!0),f(K,"준비 중..."),f(x,0),f(R,xu(_,{onProgress(I){I.total&&I.completed!==void 0?(f(x,Math.round(I.completed/I.total*100),!0),f(K,`다운로드 중... ${s(x)}%`)):I.status&&f(K,I.status,!0)},async onDone(){f(Q,!1),f(R,null),f(L,""),f(K,""),f(x,0),V(`${_} 다운로드 완료`,"success"),await $("ollama"),f(u,s(g).ollama||[],!0),s(u).includes(_)&&await j(_)},onError(I){f(Q,!1),f(R,null),f(K,""),f(x,0),V(`다운로드 실패: ${I}`)}}),!0))}function Ee(){s(R)&&(s(R).abort(),f(R,null)),f(Q,!1),f(L,""),f(K,""),f(x,0)}function qe(){f(v,!s(v))}function ve(){if(f(E,""),f(M,null),s(l))f(z,s(l),!0);else{const _=Object.keys(s(i));f(z,_.length>0?_[0]:null,!0)}f(S,!0),s(z)&&$(s(z))}function X(){y.createConversation(),f(r,""),f(n,!1),s(a)&&(s(a).abort(),f(a,null))}function te(_){y.setActive(_),f(r,""),f(n,!1),s(a)&&(s(a).abort(),f(a,null))}function Z(_){f(O,_,!0)}function le(){s(O)&&(y.deleteConversation(s(O)),f(O,null))}function Ue(){var I;const _=y.active;if(!_)return null;for(let ce=_.messages.length-1;ce>=0;ce--){const je=_.messages[ce];if(je.role==="assistant"&&((I=je.meta)!=null&&I.stockCode))return je.meta.stockCode}return null}async function Ke(){var nr,Gr;const _=s(r).trim();if(!_||s(n))return;if(!s(l)||!((nr=s(i)[s(l)])!=null&&nr.available)){V("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),ve();return}y.activeId||y.createConversation();const I=y.activeId;y.addMessage("user",_),f(r,""),f(n,!0),y.addMessage("assistant",""),y.updateLastMessage({loading:!0,startedAt:Date.now()}),ga(m);const ce=y.active,je=[];let De=null;if(ce){const he=ce.messages.slice(0,-2);for(const ne of he)if((ne.role==="user"||ne.role==="assistant")&&ne.text&&ne.text.trim()&&!ne.error&&!ne.loading){const Ve={role:ne.role,text:ne.text};ne.role==="assistant"&&((Gr=ne.meta)!=null&&Gr.stockCode)&&(Ve.meta={company:ne.meta.company||ne.company,stockCode:ne.meta.stockCode,modules:ne.meta.includedModules||null},De=ne.meta.stockCode),je.push(Ve)}}const ut=De||Ue();function Te(){return y.activeId!==I}const Rr=Su(ut,_,{provider:s(l),model:s(d)},{onMeta(he){var Mr;if(Te())return;const ne=y.active,Ve=ne==null?void 0:ne.messages[ne.messages.length-1],Dt={meta:{...(Ve==null?void 0:Ve.meta)||{},...he}};he.company&&(Dt.company=he.company,y.activeId&&((Mr=y.active)==null?void 0:Mr.title)==="새 대화"&&y.updateTitle(y.activeId,he.company)),he.stockCode&&(Dt.stockCode=he.stockCode),y.updateLastMessage(Dt)},onSnapshot(he){Te()||y.updateLastMessage({snapshot:he})},onContext(he){if(Te())return;const ne=y.active;if(!ne)return;const Ve=ne.messages[ne.messages.length-1],Hr=(Ve==null?void 0:Ve.contexts)||[];y.updateLastMessage({contexts:[...Hr,{module:he.module,label:he.label,text:he.text}]})},onSystemPrompt(he){Te()||y.updateLastMessage({systemPrompt:he.text,userContent:he.userContent||null})},onToolCall(he){if(Te())return;const ne=y.active;if(!ne)return;const Ve=ne.messages[ne.messages.length-1],Hr=(Ve==null?void 0:Ve.toolEvents)||[];y.updateLastMessage({toolEvents:[...Hr,{type:"call",name:he.name,arguments:he.arguments}]})},onToolResult(he){if(Te())return;const ne=y.active;if(!ne)return;const Ve=ne.messages[ne.messages.length-1],Hr=(Ve==null?void 0:Ve.toolEvents)||[];y.updateLastMessage({toolEvents:[...Hr,{type:"result",name:he.name,result:he.result}]})},onChunk(he){if(Te())return;const ne=y.active;if(!ne)return;const Ve=ne.messages[ne.messages.length-1];y.updateLastMessage({text:((Ve==null?void 0:Ve.text)||"")+he}),ga(m)},onDone(){if(Te())return;const he=y.active,ne=he==null?void 0:he.messages[he.messages.length-1],Ve=ne!=null&&ne.startedAt?((Date.now()-ne.startedAt)/1e3).toFixed(1):null;y.updateLastMessage({loading:!1,duration:Ve}),y.flush(),f(n,!1),f(a,null),ga(m)},onError(he,ne,Ve){Te()||(y.updateLastMessage({text:`오류: ${he}`,loading:!1,error:!0}),y.flush(),ne==="relogin"||ne==="login"?(V(`${he} — 설정에서 재로그인하세요`),ve()):V(ne==="check_headers"||ne==="check_endpoint"||ne==="check_client_id"?`${he} — ChatGPT API 변경 감지. 업데이트를 확인하세요`:ne==="rate_limit"?"요청이 너무 많습니다. 잠시 후 다시 시도해주세요":he),f(n,!1),f(a,null))}},je);f(a,Rr,!0)}function dt(){s(a)&&(s(a).abort(),f(a,null),f(n,!1),y.updateLastMessage({loading:!1}),y.flush())}function mt(){const _=y.active;if(!_||_.messages.length<2)return;let I="";for(let ce=_.messages.length-1;ce>=0;ce--)if(_.messages[ce].role==="user"){I=_.messages[ce].text;break}I&&(y.removeLastMessage(),y.removeLastMessage(),f(r,I,!0),requestAnimationFrame(()=>{Ke()}))}function jt(){const _=y.active;if(!_)return;let I=`# ${_.title}

`;for(const ut of _.messages)ut.role==="user"?I+=`## You

${ut.text}

`:ut.role==="assistant"&&ut.text&&(I+=`## DartLab

${ut.text}

`);const ce=new Blob([I],{type:"text/markdown;charset=utf-8"}),je=URL.createObjectURL(ce),De=document.createElement("a");De.href=je,De.download=`${_.title||"dartlab-chat"}.md`,De.click(),URL.revokeObjectURL(je),V("대화가 마크다운으로 내보내졌습니다","success")}function Gt(_){(_.metaKey||_.ctrlKey)&&_.key==="n"&&(_.preventDefault(),X()),(_.metaKey||_.ctrlKey)&&_.shiftKey&&_.key==="S"&&(_.preventDefault(),qe()),_.key==="Escape"&&s(O)?f(O,null):_.key==="Escape"&&s(Ae)?f(Ae,!1):_.key==="Escape"&&s(S)&&f(S,!1)}let er=pe(()=>{var _;return((_=y.active)==null?void 0:_.messages)||[]}),Fe=pe(()=>y.active&&y.active.messages.length>0),Re=pe(()=>{var _;return!s(b)&&(!s(l)||!((_=s(i)[s(l)])!=null&&_.available))});const Je=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var F=mm();Ga("keydown",As,Gt);var be=q(F),oe=c(be);{var ae=_=>{var I=Ep();W("click",I,()=>{f(v,!1)}),W("keydown",I,()=>{}),p(_,I)};T(oe,_=>{s(He)&&s(v)&&_(ae)})}var we=h(oe,2),Ye=c(we);{let _=pe(()=>s(He)?!0:s(v));Qf(Ye,{get conversations(){return y.conversations},get activeId(){return y.activeId},get open(){return s(_)},get version(){return s(C)},onNewChat:()=>{X(),s(He)&&f(v,!1)},onSelect:I=>{te(I),s(He)&&f(v,!1)},onDelete:Z})}var Ge=h(we,2),at=c(Ge),st=c(at),Lt=c(st),ht=c(Lt);{var Ot=_=>{Of(_,{size:18})},tr=_=>{Lf(_,{size:18})};T(ht,_=>{s(v)?_(Ot):_(tr,-1)})}var ct=h(Lt,2),rr=c(ct),In=c(rr);Pf(In,{size:15});var fn=h(rr,2),vn=c(fn);_a(vn,{size:15});var Ln=h(fn,2),sa=c(Ln);Nf(sa,{size:15});var At=h(Ln,4),no=c(At);{var zl=_=>{var I=Tp(),ce=q(I);Bt(ce,{size:12,class:"animate-spin"}),p(_,I)},Ml=_=>{var I=Pp(),ce=q(I);hn(ce,{size:12}),p(_,I)},Al=_=>{var I=$p(),ce=h(q(I),2),je=c(ce),De=h(ce,2);{var ut=nr=>{var Gr=Np(),he=h(q(Gr),2),ne=c(he);D(()=>B(ne,s(d))),p(nr,Gr)};T(De,nr=>{s(d)&&nr(ut)})}var Te=h(De,2);{var Rr=nr=>{Bt(nr,{size:10,class:"animate-spin text-dl-primary-light"})};T(Te,nr=>{s(Q)&&nr(Rr)})}D(()=>B(je,s(l))),p(_,I)};T(no,_=>{s(b)?_(zl):s(Re)?_(Ml,1):_(Al,-1)})}var Cl=h(no,2);jf(Cl,{size:12});var El=h(st,2);{var Tl=_=>{var I=Ip(),ce=c(I);Bt(ce,{size:16,class:"text-dl-text-dim animate-spin flex-shrink-0"}),p(_,I)},Pl=_=>{var I=Lp(),ce=c(I);hn(ce,{size:16,class:"text-dl-primary-light flex-shrink-0"});var je=h(ce,4);W("click",je,()=>ve()),p(_,I)};T(El,_=>{s(b)&&!s(S)?_(Tl):s(Re)&&!s(S)&&_(Pl,1)})}var Nl=h(at,2);{var $l=_=>{Yv(_,{get messages(){return s(er)},get isLoading(){return s(n)},get scrollTrigger(){return s(m)},onSend:Ke,onStop:dt,onRegenerate:mt,onExport:jt,onOpenExplorer:()=>f(Ae,!0),get inputText(){return s(r)},set inputText(I){f(r,I,!0)}})},Il=_=>{iv(_,{onSend:Ke,onOpenExplorer:()=>f(Ae,!0),get inputText(){return s(r)},set inputText(I){f(r,I,!0)}})};T(Nl,_=>{s(Fe)?_($l):_(Il,-1)})}var ao=h(be,2);{var Ll=_=>{var I=fm(),ce=c(I),je=c(ce),De=h(c(je),2),ut=c(De);to(ut,{size:18});var Te=h(je,2),Rr=c(Te);it(Rr,21,()=>Object.entries(s(i)),ot,(Dt,Mr)=>{var Ur=pe(()=>Va(s(Mr),2));let ft=()=>s(Ur)[0],gt=()=>s(Ur)[1];const oa=pe(()=>ft()===s(l)),Fl=pe(()=>s(z)===ft()),On=pe(()=>gt().auth==="api_key"),Qa=pe(()=>gt().auth==="cli"),Na=pe(()=>s(g)[ft()]||[]),io=pe(()=>s(A)[ft()]);var es=um(),ts=c(es),lo=c(ts),co=h(lo,2),uo=c(co),fo=c(uo),Bl=c(fo),Vl=h(fo,2);{var Gl=xt=>{var ar=Op();p(xt,ar)};T(Vl,xt=>{s(oa)&&xt(Gl)})}var Hl=h(uo,2),Ul=c(Hl),Wl=h(co,2),ql=c(Wl);{var Kl=xt=>{vs(xt,{size:16,class:"text-dl-success"})},Yl=xt=>{var ar=Rp(),Rn=q(ar);ri(Rn,{size:14,class:"text-amber-400"}),p(xt,ar)},Jl=xt=>{var ar=jp(),Rn=q(ar);Ff(Rn,{size:14,class:"text-dl-text-dim"}),p(xt,ar)};T(ql,xt=>{gt().available?xt(Kl):s(On)?xt(Yl,1):s(Qa)&&!gt().available&&xt(Jl,2)})}var Xl=h(ts,2);{var Zl=xt=>{var ar=cm(),Rn=q(ar);{var Ql=Be=>{var Xe=Fp(),vt=c(Xe),Ct=c(vt),Ht=h(vt,2),Ze=c(Ht),Et=h(Ze,2),Jt=c(Et);{var Rt=Le=>{Bt(Le,{size:12,class:"animate-spin"})},Qe=Le=>{ri(Le,{size:12})};T(Jt,Le=>{s(P)?Le(Rt):Le(Qe,-1)})}var St=h(Ht,2);{var We=Le=>{var Ft=Dp(),bt=c(Ft);hn(bt,{size:12}),p(Le,Ft)};T(St,Le=>{s(M)==="error"&&Le(We)})}D(Le=>{B(Ct,gt().envKey?`환경변수 ${gt().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),ka(Ze,"placeholder",ft()==="openai"?"sk-...":ft()==="claude"?"sk-ant-...":"API Key"),Et.disabled=Le},[()=>!s(E).trim()||s(P)]),W("keydown",Ze,Le=>{Le.key==="Enter"&&ie()}),Bn(Ze,()=>s(E),Le=>f(E,Le)),W("click",Et,ie),p(Be,Xe)};T(Rn,Be=>{s(On)&&!gt().available&&Be(Ql)})}var vo=h(Rn,2);{var ed=Be=>{var Xe=Vp(),vt=c(Xe),Ct=c(vt);vs(Ct,{size:13,class:"text-dl-success"});var Ht=h(vt,2),Ze=c(Ht),Et=h(Ze,2);{var Jt=Qe=>{var St=Bp(),We=c(St);{var Le=bt=>{Bt(bt,{size:10,class:"animate-spin"})},Ft=bt=>{var sr=ba("변경");p(bt,sr)};T(We,bt=>{s(P)?bt(Le):bt(Ft,-1)})}D(()=>St.disabled=s(P)),W("click",St,ie),p(Qe,St)},Rt=pe(()=>s(E).trim());T(Et,Qe=>{s(Rt)&&Qe(Jt)})}W("keydown",Ze,Qe=>{Qe.key==="Enter"&&ie()}),Bn(Ze,()=>s(E),Qe=>f(E,Qe)),p(Be,Xe)};T(vo,Be=>{s(On)&&gt().available&&Be(ed)})}var po=h(vo,2);{var td=Be=>{var Xe=Gp(),vt=h(c(Xe),2),Ct=c(vt);Vn(Ct,{size:14});var Ht=h(Ct,2);ti(Ht,{size:10,class:"ml-auto"}),p(Be,Xe)},rd=Be=>{var Xe=Hp(),vt=c(Xe),Ct=c(vt);hn(Ct,{size:14}),p(Be,Xe)};T(po,Be=>{ft()==="ollama"&&!s(o).installed?Be(td):ft()==="ollama"&&s(o).installed&&!s(o).running&&Be(rd,1)})}var mo=h(po,2);{var nd=Be=>{var Xe=Yp(),vt=c(Xe);{var Ct=Ze=>{var Et=Wp(),Jt=q(Et),Rt=c(Jt),Qe=h(Jt,2),St=c(Qe);{var We=pr=>{var pn=Up();p(pr,pn)};T(St,pr=>{s(ke).installed||pr(We)})}var Le=h(St,2),Ft=c(Le),bt=c(Ft),sr=h(Qe,2),Wr=c(sr);hn(Wr,{size:12,class:"text-amber-400 flex-shrink-0"}),D(()=>{B(Rt,s(ke).installed?"Codex CLI가 설치되었지만 인증이 필요합니다":"Codex CLI 설치가 필요합니다"),B(bt,s(ke).installed?"1.":"2.")}),p(Ze,Et)},Ht=Ze=>{var Et=Kp(),Jt=q(Et),Rt=c(Jt),Qe=h(Jt,2),St=c(Qe);{var We=pr=>{var pn=qp();p(pr,pn)};T(St,pr=>{s(me).installed||pr(We)})}var Le=h(St,2),Ft=c(Le),bt=c(Ft),sr=h(Qe,2),Wr=c(sr);hn(Wr,{size:12,class:"text-amber-400 flex-shrink-0"}),D(()=>{B(Rt,s(me).installed&&!s(me).authenticated?"Claude Code가 설치되었지만 인증이 필요합니다":"Claude Code CLI 설치가 필요합니다"),B(bt,s(me).installed?"1.":"2.")}),p(Ze,Et)};T(vt,Ze=>{ft()==="codex"?Ze(Ct):ft()==="claude-code"&&Ze(Ht,1)})}p(Be,Xe)};T(mo,Be=>{s(Qa)&&!gt().available&&Be(nd)})}var ho=h(mo,2);{var ad=Be=>{var Xe=Zp(),vt=h(c(Xe),2),Ct=c(vt);{var Ht=Rt=>{var Qe=Jp(),St=q(Qe);Bt(St,{size:14,class:"animate-spin"}),p(Rt,Qe)},Ze=Rt=>{var Qe=Xp(),St=q(Qe);$f(St,{size:14}),p(Rt,Qe)};T(Ct,Rt=>{s(Y)?Rt(Ht):Rt(Ze,-1)})}var Et=h(vt,2),Jt=c(Et);hn(Jt,{size:12,class:"text-amber-400 flex-shrink-0"}),D(()=>vt.disabled=s(Y)),W("click",vt,se),p(Be,Xe)};T(ho,Be=>{gt().auth==="oauth"&&!gt().available&&Be(ad)})}var go=h(ho,2);{var sd=Be=>{var Xe=Qp(),vt=c(Xe),Ct=c(vt),Ht=c(Ct);vs(Ht,{size:13,class:"text-dl-success"});var Ze=h(Ct,2),Et=c(Ze);If(Et,{size:11}),W("click",Ze,Ce),p(Be,Xe)};T(go,Be=>{gt().auth==="oauth"&&gt().available&&Be(sd)})}var od=h(go,2);{var id=Be=>{var Xe=dm(),vt=c(Xe),Ct=h(c(vt),2);{var Ht=We=>{Bt(We,{size:12,class:"animate-spin text-dl-text-dim"})};T(Ct,We=>{s(io)&&We(Ht)})}var Ze=h(vt,2);{var Et=We=>{var Le=em(),Ft=c(Le);Bt(Ft,{size:14,class:"animate-spin"}),p(We,Le)},Jt=We=>{var Le=rm();it(Le,21,()=>s(Na),ot,(Ft,bt)=>{var sr=tm(),Wr=c(sr),pr=h(Wr);{var pn=or=>{Af(or,{size:10,class:"inline ml-1"})};T(pr,or=>{s(bt)===s(d)&&s(oa)&&or(pn)})}D(or=>{tt(sr,1,or),B(Wr,`${s(bt)??""} `)},[()=>et(rt("px-3 py-1.5 rounded-lg text-[11px] border transition-all",s(bt)===s(d)&&s(oa)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),W("click",sr,()=>{ft()!==s(l)&&J(ft()),j(s(bt))}),p(Ft,sr)}),p(We,Le)},Rt=We=>{var Le=nm();p(We,Le)};T(Ze,We=>{s(io)&&s(Na).length===0?We(Et):s(Na).length>0?We(Jt,1):We(Rt,-1)})}var Qe=h(Ze,2);{var St=We=>{var Le=lm(),Ft=c(Le),bt=h(c(Ft),2),sr=h(c(bt));ti(sr,{size:9});var Wr=h(Ft,2);{var pr=or=>{var ia=am(),la=c(ia),jn=c(la),da=c(jn);Bt(da,{size:12,class:"animate-spin text-dl-primary-light"});var rs=h(jn,2),$a=h(la,2),jr=c($a),mr=h($a,2),ns=c(mr);D(()=>{al(jr,`width: ${s(x)??""}%`),B(ns,s(K))}),W("click",rs,Ee),p(or,ia)},pn=or=>{var ia=im(),la=q(ia),jn=c(la),da=h(jn,2),rs=c(da);Vn(rs,{size:12});var $a=h(la,2);it($a,21,()=>Je,ot,(jr,mr)=>{const ns=pe(()=>s(Na).some(Dn=>Dn===s(mr).name||Dn===s(mr).name.split(":")[0]));var xo=xe(),ld=q(xo);{var dd=Dn=>{var as=om(),bo=c(as),_o=c(bo),yo=c(_o),cd=c(yo),wo=h(yo,2),ud=c(wo),fd=h(wo,2);{var vd=ss=>{var So=sm(),bd=c(So);D(()=>B(bd,s(mr).tag)),p(ss,So)};T(fd,ss=>{s(mr).tag&&ss(vd)})}var pd=h(_o,2),md=c(pd),hd=h(bo,2),ko=c(hd),gd=c(ko),xd=h(ko,2);Vn(xd,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),D(()=>{B(cd,s(mr).name),B(ud,s(mr).size),B(md,s(mr).desc),B(gd,`${s(mr).gb??""} GB`)}),W("click",as,()=>{f(L,s(mr).name,!0),Oe()}),p(Dn,as)};T(ld,Dn=>{s(ns)||Dn(dd)})}p(jr,xo)}),D(jr=>da.disabled=jr,[()=>!s(L).trim()]),W("keydown",jn,jr=>{jr.key==="Enter"&&Oe()}),Bn(jn,()=>s(L),jr=>f(L,jr)),W("click",da,Oe),p(or,ia)};T(Wr,or=>{s(Q)?or(pr):or(pn,-1)})}p(We,Le)};T(Qe,We=>{ft()==="ollama"&&We(St)})}p(Be,Xe)};T(od,Be=>{(gt().available||s(On)||s(Qa)||gt().auth==="oauth")&&Be(id)})}p(xt,ar)};T(Xl,xt=>{(s(Fl)||s(oa))&&xt(Zl)})}D((xt,ar)=>{tt(es,1,xt),tt(lo,1,ar),B(Bl,gt().label||ft()),B(Ul,gt().desc||"")},[()=>et(rt("rounded-xl border transition-all",s(oa)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>et(rt("w-2.5 h-2.5 rounded-full flex-shrink-0",gt().available?"bg-dl-success":s(On)?"bg-amber-400":"bg-dl-text-dim"))]),W("click",ts,()=>{gt().available||s(On)?ft()===s(l)?re(ft()):J(ft()):re(ft())}),p(Dt,es)});var nr=h(Te,2),Gr=c(nr),he=c(Gr);{var ne=Dt=>{var Mr=ba();D(()=>{var Ur;return B(Mr,`현재: ${(((Ur=s(i)[s(l)])==null?void 0:Ur.label)||s(l))??""} / ${s(d)??""}`)}),p(Dt,Mr)},Ve=Dt=>{var Mr=ba();D(()=>{var Ur;return B(Mr,`현재: ${(((Ur=s(i)[s(l)])==null?void 0:Ur.label)||s(l))??""}`)}),p(Dt,Mr)};T(he,Dt=>{s(l)&&s(d)?Dt(ne):s(l)&&Dt(Ve,1)})}var Hr=h(Gr,2);W("click",I,Dt=>{Dt.target===Dt.currentTarget&&f(S,!1)}),W("keydown",I,()=>{}),W("click",De,()=>f(S,!1)),W("click",Hr,()=>f(S,!1)),p(_,I)};T(ao,_=>{s(S)&&_(Ll)})}var so=h(ao,2);{var Ol=_=>{Cp(_,{onClose:()=>f(Ae,!1)})};T(so,_=>{s(Ae)&&_(Ol)})}var oo=h(so,2);{var Rl=_=>{var I=vm(),ce=c(I),je=h(c(ce),4),De=c(je),ut=h(De,2);W("click",I,Te=>{Te.target===Te.currentTarget&&f(O,null)}),W("keydown",I,()=>{}),W("click",De,()=>f(O,null)),W("click",ut,le),p(_,I)};T(oo,_=>{s(O)&&_(Rl)})}var jl=h(oo,2);{var Dl=_=>{var I=pm(),ce=c(I),je=c(ce);D(De=>{tt(ce,1,De),B(je,s(ee))},[()=>et(rt("px-4 py-3 rounded-xl border text-[13px] shadow-2xl max-w-sm",s(de)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":s(de)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),p(_,I)};T(jl,_=>{s(ue)&&_(Dl)})}D(_=>{tt(we,1,et(s(He)?s(v)?"sidebar-mobile":"hidden":"")),tt(At,1,_)},[()=>et(rt("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",s(b)?"text-dl-text-dim":s(Re)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),W("click",Lt,qe),W("click",At,()=>ve()),p(e,F),Sr()}cn(["click","keydown"]);Kc(hm,{target:document.getElementById("app")});
