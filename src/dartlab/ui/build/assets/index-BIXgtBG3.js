var Gl=Object.defineProperty;var Vs=e=>{throw TypeError(e)};var Wl=(e,t,r)=>t in e?Gl(e,t,{enumerable:!0,configurable:!0,writable:!0,value:r}):e[t]=r;var St=(e,t,r)=>Wl(e,typeof t!="symbol"?t+"":t,r),xa=(e,t,r)=>t.has(e)||Vs("Cannot "+r);var x=(e,t,r)=>(xa(e,t,"read from private field"),r?r.call(e):t.get(e)),re=(e,t,r)=>t.has(e)?Vs("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,r),J=(e,t,r,n)=>(xa(e,t,"write to private field"),n?n.call(e,r):t.set(e,r),r),Te=(e,t,r)=>(xa(e,t,"access private method"),r);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const a of document.querySelectorAll('link[rel="modulepreload"]'))n(a);new MutationObserver(a=>{for(const s of a)if(s.type==="childList")for(const o of s.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&n(o)}).observe(document,{childList:!0,subtree:!0});function r(a){const s={};return a.integrity&&(s.integrity=a.integrity),a.referrerPolicy&&(s.referrerPolicy=a.referrerPolicy),a.crossOrigin==="use-credentials"?s.credentials="include":a.crossOrigin==="anonymous"?s.credentials="omit":s.credentials="same-origin",s}function n(a){if(a.ep)return;a.ep=!0;const s=r(a);fetch(a.href,s)}})();const Ea=!1;var Xa=Array.isArray,Hl=Array.prototype.indexOf,tn=Array.prototype.includes,ra=Array.from,Kl=Object.defineProperty,dr=Object.getOwnPropertyDescriptor,wo=Object.getOwnPropertyDescriptors,ql=Object.prototype,Ul=Array.prototype,Za=Object.getPrototypeOf,Bs=Object.isExtensible;function bn(e){return typeof e=="function"}const Yl=()=>{};function Jl(e){return e()}function Ta(e){for(var t=0;t<e.length;t++)e[t]()}function ko(){var e,t,r=new Promise((n,a)=>{e=n,t=a});return{promise:r,resolve:e,reject:t}}function So(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const r=[];for(const n of e)if(r.push(n),r.length===t)break;return r}const We=2,on=4,Cr=8,na=1<<24,mr=16,Nt=32,Lr=64,Na=128,pt=512,Ve=1024,Be=2048,Tt=4096,Ye=8192,Dt=16384,ln=32768,vr=65536,Gs=1<<17,Xl=1<<18,dn=1<<19,Ao=1<<20,Rt=1<<25,$r=65536,Pa=1<<21,Qa=1<<22,cr=1<<23,Ft=Symbol("$state"),zo=Symbol("legacy props"),Zl=Symbol(""),wr=new class extends Error{constructor(){super(...arguments);St(this,"name","StaleReactionError");St(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var xo;const Mo=!!((xo=globalThis.document)!=null&&xo.contentType)&&globalThis.document.contentType.includes("xml");function Ql(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function ed(e,t,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function td(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function rd(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function nd(e){throw new Error("https://svelte.dev/e/effect_orphan")}function ad(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function sd(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function od(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function id(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function ld(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function dd(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const cd=1,fd=2,Eo=4,ud=8,vd=16,pd=1,hd=2,To=4,md=8,gd=16,bd=1,xd=2,$e=Symbol(),No="http://www.w3.org/1999/xhtml",Po="http://www.w3.org/2000/svg",_d="http://www.w3.org/1998/Math/MathML",yd="@attach";function wd(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function kd(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Co(e){return e===this.v}function Sd(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function $o(e){return!Sd(e,this.v)}let Nn=!1,Ad=!1;function zd(){Nn=!0}let Le=null;function rn(e){Le=e}function Jt(e,t=!1,r){Le={p:Le,i:!1,c:null,e:null,s:e,x:null,l:Nn&&!t?{s:null,u:null,$:[]}:null}}function Xt(e){var t=Le,r=t.e;if(r!==null){t.e=null;for(var n of r)Zo(n)}return t.i=!0,Le=t.p,{}}function Pn(){return!Nn||Le!==null&&Le.l===null}let kr=[];function Io(){var e=kr;kr=[],Ta(e)}function Vt(e){if(kr.length===0&&!Sn){var t=kr;queueMicrotask(()=>{t===kr&&Io()})}kr.push(e)}function Md(){for(;kr.length>0;)Io()}function Oo(e){var t=te;if(t===null)return ee.f|=cr,e;if((t.f&ln)===0&&(t.f&on)===0)throw e;lr(e,t)}function lr(e,t){for(;t!==null;){if((t.f&Na)!==0){if((t.f&ln)===0)throw e;try{t.b.error(e);return}catch(r){e=r}}t=t.parent}throw e}const Ed=-7169;function Me(e,t){e.f=e.f&Ed|t}function es(e){(e.f&pt)!==0||e.deps===null?Me(e,Ve):Me(e,Tt)}function Lo(e){if(e!==null)for(const t of e)(t.f&We)===0||(t.f&$r)===0||(t.f^=$r,Lo(t.deps))}function Ro(e,t,r){(e.f&Be)!==0?t.add(e):(e.f&Tt)!==0&&r.add(e),Lo(e.deps),Me(e,Ve)}const Fn=new Set;let Z=null,Ca=null,je=null,Ze=[],aa=null,Sn=!1,nn=null,Td=1;var sr,qr,zr,Ur,Yr,Jr,or,$t,Xr,nt,$a,Ia,Oa,La;const vs=class vs{constructor(){re(this,nt);St(this,"id",Td++);St(this,"current",new Map);St(this,"previous",new Map);re(this,sr,new Set);re(this,qr,new Set);re(this,zr,0);re(this,Ur,0);re(this,Yr,null);re(this,Jr,new Set);re(this,or,new Set);re(this,$t,new Map);St(this,"is_fork",!1);re(this,Xr,!1)}skip_effect(t){x(this,$t).has(t)||x(this,$t).set(t,{d:[],m:[]})}unskip_effect(t){var r=x(this,$t).get(t);if(r){x(this,$t).delete(t);for(var n of r.d)Me(n,Be),jt(n);for(n of r.m)Me(n,Tt),jt(n)}}process(t){var a;Ze=[],this.apply();var r=nn=[],n=[];for(const s of t)Te(this,nt,Ia).call(this,s,r,n);if(nn=null,Te(this,nt,$a).call(this)){Te(this,nt,Oa).call(this,n),Te(this,nt,Oa).call(this,r);for(const[s,o]of x(this,$t))Vo(s,o)}else{Ca=this,Z=null;for(const s of x(this,sr))s(this);x(this,sr).clear(),x(this,zr)===0&&Te(this,nt,La).call(this),Ws(n),Ws(r),x(this,Jr).clear(),x(this,or).clear(),Ca=null,(a=x(this,Yr))==null||a.resolve()}je=null}capture(t,r){r!==$e&&!this.previous.has(t)&&this.previous.set(t,r),(t.f&cr)===0&&(this.current.set(t,t.v),je==null||je.set(t,t.v))}activate(){Z=this,this.apply()}deactivate(){Z===this&&(Z=null,je=null)}flush(){var t;if(Ze.length>0)Z=this,jo();else if(x(this,zr)===0&&!this.is_fork){for(const r of x(this,sr))r(this);x(this,sr).clear(),Te(this,nt,La).call(this),(t=x(this,Yr))==null||t.resolve()}this.deactivate()}discard(){for(const t of x(this,qr))t(this);x(this,qr).clear()}increment(t){J(this,zr,x(this,zr)+1),t&&J(this,Ur,x(this,Ur)+1)}decrement(t){J(this,zr,x(this,zr)-1),t&&J(this,Ur,x(this,Ur)-1),!x(this,Xr)&&(J(this,Xr,!0),Vt(()=>{J(this,Xr,!1),Te(this,nt,$a).call(this)?Ze.length>0&&this.flush():this.revive()}))}revive(){for(const t of x(this,Jr))x(this,or).delete(t),Me(t,Be),jt(t);for(const t of x(this,or))Me(t,Tt),jt(t);this.flush()}oncommit(t){x(this,sr).add(t)}ondiscard(t){x(this,qr).add(t)}settled(){return(x(this,Yr)??J(this,Yr,ko())).promise}static ensure(){if(Z===null){const t=Z=new vs;Fn.add(Z),Sn||Vt(()=>{Z===t&&t.flush()})}return Z}apply(){}};sr=new WeakMap,qr=new WeakMap,zr=new WeakMap,Ur=new WeakMap,Yr=new WeakMap,Jr=new WeakMap,or=new WeakMap,$t=new WeakMap,Xr=new WeakMap,nt=new WeakSet,$a=function(){return this.is_fork||x(this,Ur)>0},Ia=function(t,r,n){t.f^=Ve;for(var a=t.first;a!==null;){var s=a.f,o=(s&(Nt|Lr))!==0,i=o&&(s&Ve)!==0,l=(s&Ye)!==0,c=i||x(this,$t).has(a);if(!c&&a.fn!==null){o?l||(a.f^=Ve):(s&on)!==0?r.push(a):(s&(Cr|na))!==0&&l?n.push(a):On(a)&&(sn(a),(s&mr)!==0&&(x(this,or).add(a),l&&Me(a,Be)));var f=a.first;if(f!==null){a=f;continue}}for(;a!==null;){var g=a.next;if(g!==null){a=g;break}a=a.parent}}},Oa=function(t){for(var r=0;r<t.length;r+=1)Ro(t[r],x(this,Jr),x(this,or))},La=function(){var s;if(Fn.size>1){this.previous.clear();var t=Z,r=je,n=!0;for(const o of Fn){if(o===this){n=!1;continue}const i=[];for(const[c,f]of this.current){if(o.current.has(c))if(n&&f!==o.current.get(c))o.current.set(c,f);else continue;i.push(c)}if(i.length===0)continue;const l=[...o.current.keys()].filter(c=>!this.current.has(c));if(l.length>0){var a=Ze;Ze=[];const c=new Set,f=new Map;for(const g of i)Do(g,l,c,f);if(Ze.length>0){Z=o,o.apply();for(const g of Ze)Te(s=o,nt,Ia).call(s,g,[],[]);o.deactivate()}Ze=a}}Z=t,je=r}x(this,$t).clear(),Fn.delete(this)};let fr=vs;function Nd(e){var t=Sn;Sn=!0;try{for(var r;;){if(Md(),Ze.length===0&&(Z==null||Z.flush(),Ze.length===0))return aa=null,r;jo()}}finally{Sn=t}}function jo(){var e=null;try{for(var t=0;Ze.length>0;){var r=fr.ensure();if(t++>1e3){var n,a;Pd()}r.process(Ze),ur.clear()}}finally{Ze=[],aa=null,nn=null}}function Pd(){try{ad()}catch(e){lr(e,aa)}}let At=null;function Ws(e){var t=e.length;if(t!==0){for(var r=0;r<t;){var n=e[r++];if((n.f&(Dt|Ye))===0&&On(n)&&(At=new Set,sn(n),n.deps===null&&n.first===null&&n.nodes===null&&n.teardown===null&&n.ac===null&&ri(n),(At==null?void 0:At.size)>0)){ur.clear();for(const a of At){if((a.f&(Dt|Ye))!==0)continue;const s=[a];let o=a.parent;for(;o!==null;)At.has(o)&&(At.delete(o),s.push(o)),o=o.parent;for(let i=s.length-1;i>=0;i--){const l=s[i];(l.f&(Dt|Ye))===0&&sn(l)}}At.clear()}}At=null}}function Do(e,t,r,n){if(!r.has(e)&&(r.add(e),e.reactions!==null))for(const a of e.reactions){const s=a.f;(s&We)!==0?Do(a,t,r,n):(s&(Qa|mr))!==0&&(s&Be)===0&&Fo(a,t,n)&&(Me(a,Be),jt(a))}}function Fo(e,t,r){const n=r.get(e);if(n!==void 0)return n;if(e.deps!==null)for(const a of e.deps){if(tn.call(t,a))return!0;if((a.f&We)!==0&&Fo(a,t,r))return r.set(a,!0),!0}return r.set(e,!1),!1}function jt(e){var t=aa=e,r=t.b;if(r!=null&&r.is_pending&&(e.f&(on|Cr|na))!==0&&(e.f&ln)===0){r.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var n=t.f;if(nn!==null&&t===te&&(e.f&Cr)===0)return;if((n&(Lr|Nt))!==0){if((n&Ve)===0)return;t.f^=Ve}}Ze.push(t)}function Vo(e,t){if(!((e.f&Nt)!==0&&(e.f&Ve)!==0)){(e.f&Be)!==0?t.d.push(e):(e.f&Tt)!==0&&t.m.push(e),Me(e,Ve);for(var r=e.first;r!==null;)Vo(r,t),r=r.next}}function Cd(e){let t=0,r=pr(0),n;return()=>{as()&&(d(r),os(()=>(t===0&&(n=Ir(()=>e(()=>zn(r)))),t+=1,()=>{Vt(()=>{t-=1,t===0&&(n==null||n(),n=void 0,zn(r))})})))}}var $d=vr|dn;function Id(e,t,r,n){new Od(e,t,r,n)}var vt,Ja,It,Mr,Xe,Ot,ot,zt,qt,Er,ir,Zr,Qr,en,Ut,ea,Ce,Ld,Rd,jd,Ra,Kn,qn,ja;class Od{constructor(t,r,n,a){re(this,Ce);St(this,"parent");St(this,"is_pending",!1);St(this,"transform_error");re(this,vt);re(this,Ja,null);re(this,It);re(this,Mr);re(this,Xe);re(this,Ot,null);re(this,ot,null);re(this,zt,null);re(this,qt,null);re(this,Er,0);re(this,ir,0);re(this,Zr,!1);re(this,Qr,new Set);re(this,en,new Set);re(this,Ut,null);re(this,ea,Cd(()=>(J(this,Ut,pr(x(this,Er))),()=>{J(this,Ut,null)})));var s;J(this,vt,t),J(this,It,r),J(this,Mr,o=>{var i=te;i.b=this,i.f|=Na,n(o)}),this.parent=te.b,this.transform_error=a??((s=this.parent)==null?void 0:s.transform_error)??(o=>o),J(this,Xe,In(()=>{Te(this,Ce,Ra).call(this)},$d))}defer_effect(t){Ro(t,x(this,Qr),x(this,en))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!x(this,It).pending}update_pending_count(t){Te(this,Ce,ja).call(this,t),J(this,Er,x(this,Er)+t),!(!x(this,Ut)||x(this,Zr))&&(J(this,Zr,!0),Vt(()=>{J(this,Zr,!1),x(this,Ut)&&an(x(this,Ut),x(this,Er))}))}get_effect_pending(){return x(this,ea).call(this),d(x(this,Ut))}error(t){var r=x(this,It).onerror;let n=x(this,It).failed;if(!r&&!n)throw t;x(this,Ot)&&(Ge(x(this,Ot)),J(this,Ot,null)),x(this,ot)&&(Ge(x(this,ot)),J(this,ot,null)),x(this,zt)&&(Ge(x(this,zt)),J(this,zt,null));var a=!1,s=!1;const o=()=>{if(a){kd();return}a=!0,s&&dd(),x(this,zt)!==null&&Nr(x(this,zt),()=>{J(this,zt,null)}),Te(this,Ce,qn).call(this,()=>{fr.ensure(),Te(this,Ce,Ra).call(this)})},i=l=>{try{s=!0,r==null||r(l,o),s=!1}catch(c){lr(c,x(this,Xe)&&x(this,Xe).parent)}n&&J(this,zt,Te(this,Ce,qn).call(this,()=>{fr.ensure();try{return et(()=>{var c=te;c.b=this,c.f|=Na,n(x(this,vt),()=>l,()=>o)})}catch(c){return lr(c,x(this,Xe).parent),null}}))};Vt(()=>{var l;try{l=this.transform_error(t)}catch(c){lr(c,x(this,Xe)&&x(this,Xe).parent);return}l!==null&&typeof l=="object"&&typeof l.then=="function"?l.then(i,c=>lr(c,x(this,Xe)&&x(this,Xe).parent)):i(l)})}}vt=new WeakMap,Ja=new WeakMap,It=new WeakMap,Mr=new WeakMap,Xe=new WeakMap,Ot=new WeakMap,ot=new WeakMap,zt=new WeakMap,qt=new WeakMap,Er=new WeakMap,ir=new WeakMap,Zr=new WeakMap,Qr=new WeakMap,en=new WeakMap,Ut=new WeakMap,ea=new WeakMap,Ce=new WeakSet,Ld=function(){try{J(this,Ot,et(()=>x(this,Mr).call(this,x(this,vt))))}catch(t){this.error(t)}},Rd=function(t){const r=x(this,It).failed;r&&J(this,zt,et(()=>{r(x(this,vt),()=>t,()=>()=>{})}))},jd=function(){const t=x(this,It).pending;t&&(this.is_pending=!0,J(this,ot,et(()=>t(x(this,vt)))),Vt(()=>{var r=J(this,qt,document.createDocumentFragment()),n=Bt();r.append(n),J(this,Ot,Te(this,Ce,qn).call(this,()=>(fr.ensure(),et(()=>x(this,Mr).call(this,n))))),x(this,ir)===0&&(x(this,vt).before(r),J(this,qt,null),Nr(x(this,ot),()=>{J(this,ot,null)}),Te(this,Ce,Kn).call(this))}))},Ra=function(){try{if(this.is_pending=this.has_pending_snippet(),J(this,ir,0),J(this,Er,0),J(this,Ot,et(()=>{x(this,Mr).call(this,x(this,vt))})),x(this,ir)>0){var t=J(this,qt,document.createDocumentFragment());ds(x(this,Ot),t);const r=x(this,It).pending;J(this,ot,et(()=>r(x(this,vt))))}else Te(this,Ce,Kn).call(this)}catch(r){this.error(r)}},Kn=function(){this.is_pending=!1;for(const t of x(this,Qr))Me(t,Be),jt(t);for(const t of x(this,en))Me(t,Tt),jt(t);x(this,Qr).clear(),x(this,en).clear()},qn=function(t){var r=te,n=ee,a=Le;gt(x(this,Xe)),mt(x(this,Xe)),rn(x(this,Xe).ctx);try{return t()}catch(s){return Oo(s),null}finally{gt(r),mt(n),rn(a)}},ja=function(t){var r;if(!this.has_pending_snippet()){this.parent&&Te(r=this.parent,Ce,ja).call(r,t);return}J(this,ir,x(this,ir)+t),x(this,ir)===0&&(Te(this,Ce,Kn).call(this),x(this,ot)&&Nr(x(this,ot),()=>{J(this,ot,null)}),x(this,qt)&&(x(this,vt).before(x(this,qt)),J(this,qt,null)))};function Bo(e,t,r,n){const a=Pn()?Cn:ts;var s=e.filter(g=>!g.settled);if(r.length===0&&s.length===0){n(t.map(a));return}var o=te,i=Dd(),l=s.length===1?s[0].promise:s.length>1?Promise.all(s.map(g=>g.promise)):null;function c(g){i();try{n(g)}catch(v){(o.f&Dt)===0&&lr(v,o)}Da()}if(r.length===0){l.then(()=>c(t.map(a)));return}function f(){i(),Promise.all(r.map(g=>Vd(g))).then(g=>c([...t.map(a),...g])).catch(g=>lr(g,o))}l?l.then(f):f()}function Dd(){var e=te,t=ee,r=Le,n=Z;return function(s=!0){gt(e),mt(t),rn(r),s&&(n==null||n.activate())}}function Da(e=!0){gt(null),mt(null),rn(null),e&&(Z==null||Z.deactivate())}function Fd(){var e=te.b,t=Z,r=e.is_rendered();return e.update_pending_count(1),t.increment(r),()=>{e.update_pending_count(-1),t.decrement(r)}}function Cn(e){var t=We|Be,r=ee!==null&&(ee.f&We)!==0?ee:null;return te!==null&&(te.f|=dn),{ctx:Le,deps:null,effects:null,equals:Co,f:t,fn:e,reactions:null,rv:0,v:$e,wv:0,parent:r??te,ac:null}}function Vd(e,t,r){te===null&&Ql();var a=void 0,s=pr($e),o=!ee,i=new Map;return rc(()=>{var v;var l=ko();a=l.promise;try{Promise.resolve(e()).then(l.resolve,l.reject).finally(Da)}catch(_){l.reject(_),Da()}var c=Z;if(o){var f=Fd();(v=i.get(c))==null||v.reject(wr),i.delete(c),i.set(c,l)}const g=(_,u=void 0)=>{if(c.activate(),u)u!==wr&&(s.f|=cr,an(s,u));else{(s.f&cr)!==0&&(s.f^=cr),an(s,_);for(const[m,p]of i){if(i.delete(m),m===c)break;p.reject(wr)}}f&&f()};l.promise.then(g,_=>g(null,_||"unknown"))}),oa(()=>{for(const l of i.values())l.reject(wr)}),new Promise(l=>{function c(f){function g(){f===a?l(s):c(a)}f.then(g,g)}c(a)})}function Pe(e){const t=Cn(e);return si(t),t}function ts(e){const t=Cn(e);return t.equals=$o,t}function Bd(e){var t=e.effects;if(t!==null){e.effects=null;for(var r=0;r<t.length;r+=1)Ge(t[r])}}function Gd(e){for(var t=e.parent;t!==null;){if((t.f&We)===0)return(t.f&Dt)===0?t:null;t=t.parent}return null}function rs(e){var t,r=te;gt(Gd(e));try{e.f&=~$r,Bd(e),t=di(e)}finally{gt(r)}return t}function Go(e){var t=rs(e);if(!e.equals(t)&&(e.wv=ii(),(!(Z!=null&&Z.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){Me(e,Ve);return}hr||(je!==null?(as()||Z!=null&&Z.is_fork)&&je.set(e,t):es(e))}function Wd(e){var t,r;if(e.effects!==null)for(const n of e.effects)(n.teardown||n.ac)&&((t=n.teardown)==null||t.call(n),(r=n.ac)==null||r.abort(wr),n.teardown=Yl,n.ac=null,Mn(n,0),is(n))}function Wo(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&sn(t)}let Fa=new Set;const ur=new Map;let Ho=!1;function pr(e,t){var r={f:0,v:e,reactions:null,equals:Co,rv:0,wv:0};return r}function q(e,t){const r=pr(e);return si(r),r}function Hd(e,t=!1,r=!0){var a;const n=pr(e);return t||(n.equals=$o),Nn&&r&&Le!==null&&Le.l!==null&&((a=Le.l).s??(a.s=[])).push(n),n}function b(e,t,r=!1){ee!==null&&(!Et||(ee.f&Gs)!==0)&&Pn()&&(ee.f&(We|mr|Qa|Gs))!==0&&(ht===null||!tn.call(ht,e))&&ld();let n=r?lt(t):t;return an(e,n)}function an(e,t){if(!e.equals(t)){var r=e.v;hr?ur.set(e,t):ur.set(e,r),e.v=t;var n=fr.ensure();if(n.capture(e,r),(e.f&We)!==0){const a=e;(e.f&Be)!==0&&rs(a),es(a)}e.wv=ii(),Ko(e,Be),Pn()&&te!==null&&(te.f&Ve)!==0&&(te.f&(Nt|Lr))===0&&(ut===null?ac([e]):ut.push(e)),!n.is_fork&&Fa.size>0&&!Ho&&Kd()}return t}function Kd(){Ho=!1;for(const e of Fa)(e.f&Ve)!==0&&Me(e,Tt),On(e)&&sn(e);Fa.clear()}function An(e,t=1){var r=d(e),n=t===1?r++:r--;return b(e,r),n}function zn(e){b(e,e.v+1)}function Ko(e,t){var r=e.reactions;if(r!==null)for(var n=Pn(),a=r.length,s=0;s<a;s++){var o=r[s],i=o.f;if(!(!n&&o===te)){var l=(i&Be)===0;if(l&&Me(o,t),(i&We)!==0){var c=o;je==null||je.delete(c),(i&$r)===0&&(i&pt&&(o.f|=$r),Ko(c,Tt))}else l&&((i&mr)!==0&&At!==null&&At.add(o),jt(o))}}}function lt(e){if(typeof e!="object"||e===null||Ft in e)return e;const t=Za(e);if(t!==ql&&t!==Ul)return e;var r=new Map,n=Xa(e),a=q(0),s=Pr,o=i=>{if(Pr===s)return i();var l=ee,c=Pr;mt(null),Us(s);var f=i();return mt(l),Us(c),f};return n&&r.set("length",q(e.length)),new Proxy(e,{defineProperty(i,l,c){(!("value"in c)||c.configurable===!1||c.enumerable===!1||c.writable===!1)&&od();var f=r.get(l);return f===void 0?o(()=>{var g=q(c.value);return r.set(l,g),g}):b(f,c.value,!0),!0},deleteProperty(i,l){var c=r.get(l);if(c===void 0){if(l in i){const f=o(()=>q($e));r.set(l,f),zn(a)}}else b(c,$e),zn(a);return!0},get(i,l,c){var _;if(l===Ft)return e;var f=r.get(l),g=l in i;if(f===void 0&&(!g||(_=dr(i,l))!=null&&_.writable)&&(f=o(()=>{var u=lt(g?i[l]:$e),m=q(u);return m}),r.set(l,f)),f!==void 0){var v=d(f);return v===$e?void 0:v}return Reflect.get(i,l,c)},getOwnPropertyDescriptor(i,l){var c=Reflect.getOwnPropertyDescriptor(i,l);if(c&&"value"in c){var f=r.get(l);f&&(c.value=d(f))}else if(c===void 0){var g=r.get(l),v=g==null?void 0:g.v;if(g!==void 0&&v!==$e)return{enumerable:!0,configurable:!0,value:v,writable:!0}}return c},has(i,l){var v;if(l===Ft)return!0;var c=r.get(l),f=c!==void 0&&c.v!==$e||Reflect.has(i,l);if(c!==void 0||te!==null&&(!f||(v=dr(i,l))!=null&&v.writable)){c===void 0&&(c=o(()=>{var _=f?lt(i[l]):$e,u=q(_);return u}),r.set(l,c));var g=d(c);if(g===$e)return!1}return f},set(i,l,c,f){var A;var g=r.get(l),v=l in i;if(n&&l==="length")for(var _=c;_<g.v;_+=1){var u=r.get(_+"");u!==void 0?b(u,$e):_ in i&&(u=o(()=>q($e)),r.set(_+"",u))}if(g===void 0)(!v||(A=dr(i,l))!=null&&A.writable)&&(g=o(()=>q(void 0)),b(g,lt(c)),r.set(l,g));else{v=g.v!==$e;var m=o(()=>lt(c));b(g,m)}var p=Reflect.getOwnPropertyDescriptor(i,l);if(p!=null&&p.set&&p.set.call(f,c),!v){if(n&&typeof l=="string"){var y=r.get("length"),N=Number(l);Number.isInteger(N)&&N>=y.v&&b(y,N+1)}zn(a)}return!0},ownKeys(i){d(a);var l=Reflect.ownKeys(i).filter(g=>{var v=r.get(g);return v===void 0||v.v!==$e});for(var[c,f]of r)f.v!==$e&&!(c in i)&&l.push(c);return l},setPrototypeOf(){id()}})}function Hs(e){try{if(e!==null&&typeof e=="object"&&Ft in e)return e[Ft]}catch{}return e}function qd(e,t){return Object.is(Hs(e),Hs(t))}var Va,qo,Uo,Yo;function Ud(){if(Va===void 0){Va=window,qo=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,r=Text.prototype;Uo=dr(t,"firstChild").get,Yo=dr(t,"nextSibling").get,Bs(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Bs(r)&&(r.__t=void 0)}}function Bt(e=""){return document.createTextNode(e)}function Yt(e){return Uo.call(e)}function $n(e){return Yo.call(e)}function h(e,t){return Yt(e)}function H(e,t=!1){{var r=Yt(e);return r instanceof Comment&&r.data===""?$n(r):r}}function z(e,t=1,r=!1){let n=e;for(;t--;)n=$n(n);return n}function Yd(e){e.textContent=""}function Jo(){return!1}function ns(e,t,r){return document.createElementNS(t??No,e,void 0)}function Jd(e,t){if(t){const r=document.body;e.autofocus=!0,Vt(()=>{document.activeElement===r&&e.focus()})}}let Ks=!1;function Xd(){Ks||(Ks=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const r of e.target.elements)(t=r.__on_r)==null||t.call(r)})},{capture:!0}))}function sa(e){var t=ee,r=te;mt(null),gt(null);try{return e()}finally{mt(t),gt(r)}}function Zd(e,t,r,n=r){e.addEventListener(t,()=>sa(r));const a=e.__on_r;a?e.__on_r=()=>{a(),n(!0)}:e.__on_r=()=>n(!0),Xd()}function Xo(e){te===null&&(ee===null&&nd(),rd()),hr&&td()}function Qd(e,t){var r=t.last;r===null?t.last=t.first=e:(r.next=e,e.prev=r,t.last=e)}function Pt(e,t){var r=te;r!==null&&(r.f&Ye)!==0&&(e|=Ye);var n={ctx:Le,deps:null,nodes:null,f:e|Be|pt,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},a=n;if((e&on)!==0)nn!==null?nn.push(n):jt(n);else if(t!==null){try{sn(n)}catch(o){throw Ge(n),o}a.deps===null&&a.teardown===null&&a.nodes===null&&a.first===a.last&&(a.f&dn)===0&&(a=a.first,(e&mr)!==0&&(e&vr)!==0&&a!==null&&(a.f|=vr))}if(a!==null&&(a.parent=r,r!==null&&Qd(a,r),ee!==null&&(ee.f&We)!==0&&(e&Lr)===0)){var s=ee;(s.effects??(s.effects=[])).push(a)}return n}function as(){return ee!==null&&!Et}function oa(e){const t=Pt(Cr,null);return Me(t,Ve),t.teardown=e,t}function Jn(e){Xo();var t=te.f,r=!ee&&(t&Nt)!==0&&(t&ln)===0;if(r){var n=Le;(n.e??(n.e=[])).push(e)}else return Zo(e)}function Zo(e){return Pt(on|Ao,e)}function ec(e){return Xo(),Pt(Cr|Ao,e)}function tc(e){fr.ensure();const t=Pt(Lr|dn,e);return(r={})=>new Promise(n=>{r.outro?Nr(t,()=>{Ge(t),n(void 0)}):(Ge(t),n(void 0))})}function ss(e){return Pt(on,e)}function rc(e){return Pt(Qa|dn,e)}function os(e,t=0){return Pt(Cr|t,e)}function X(e,t=[],r=[],n=[]){Bo(n,t,r,a=>{Pt(Cr,()=>e(...a.map(d)))})}function In(e,t=0){var r=Pt(mr|t,e);return r}function Qo(e,t=0){var r=Pt(na|t,e);return r}function et(e){return Pt(Nt|dn,e)}function ei(e){var t=e.teardown;if(t!==null){const r=hr,n=ee;qs(!0),mt(null);try{t.call(null)}finally{qs(r),mt(n)}}}function is(e,t=!1){var r=e.first;for(e.first=e.last=null;r!==null;){const a=r.ac;a!==null&&sa(()=>{a.abort(wr)});var n=r.next;(r.f&Lr)!==0?r.parent=null:Ge(r,t),r=n}}function nc(e){for(var t=e.first;t!==null;){var r=t.next;(t.f&Nt)===0&&Ge(t),t=r}}function Ge(e,t=!0){var r=!1;(t||(e.f&Xl)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(ti(e.nodes.start,e.nodes.end),r=!0),is(e,t&&!r),Mn(e,0),Me(e,Dt);var n=e.nodes&&e.nodes.t;if(n!==null)for(const s of n)s.stop();ei(e);var a=e.parent;a!==null&&a.first!==null&&ri(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function ti(e,t){for(;e!==null;){var r=e===t?null:$n(e);e.remove(),e=r}}function ri(e){var t=e.parent,r=e.prev,n=e.next;r!==null&&(r.next=n),n!==null&&(n.prev=r),t!==null&&(t.first===e&&(t.first=n),t.last===e&&(t.last=r))}function Nr(e,t,r=!0){var n=[];ni(e,n,!0);var a=()=>{r&&Ge(e),t&&t()},s=n.length;if(s>0){var o=()=>--s||a();for(var i of n)i.out(o)}else a()}function ni(e,t,r){if((e.f&Ye)===0){e.f^=Ye;var n=e.nodes&&e.nodes.t;if(n!==null)for(const i of n)(i.is_global||r)&&t.push(i);for(var a=e.first;a!==null;){var s=a.next,o=(a.f&vr)!==0||(a.f&Nt)!==0&&(e.f&mr)!==0;ni(a,t,o?r:!1),a=s}}}function ls(e){ai(e,!0)}function ai(e,t){if((e.f&Ye)!==0){e.f^=Ye;for(var r=e.first;r!==null;){var n=r.next,a=(r.f&vr)!==0||(r.f&Nt)!==0;ai(r,a?t:!1),r=n}var s=e.nodes&&e.nodes.t;if(s!==null)for(const o of s)(o.is_global||t)&&o.in()}}function ds(e,t){if(e.nodes)for(var r=e.nodes.start,n=e.nodes.end;r!==null;){var a=r===n?null:$n(r);t.append(r),r=a}}let Un=!1,hr=!1;function qs(e){hr=e}let ee=null,Et=!1;function mt(e){ee=e}let te=null;function gt(e){te=e}let ht=null;function si(e){ee!==null&&(ht===null?ht=[e]:ht.push(e))}let Qe=null,st=0,ut=null;function ac(e){ut=e}let oi=1,Sr=0,Pr=Sr;function Us(e){Pr=e}function ii(){return++oi}function On(e){var t=e.f;if((t&Be)!==0)return!0;if(t&We&&(e.f&=~$r),(t&Tt)!==0){for(var r=e.deps,n=r.length,a=0;a<n;a++){var s=r[a];if(On(s)&&Go(s),s.wv>e.wv)return!0}(t&pt)!==0&&je===null&&Me(e,Ve)}return!1}function li(e,t,r=!0){var n=e.reactions;if(n!==null&&!(ht!==null&&tn.call(ht,e)))for(var a=0;a<n.length;a++){var s=n[a];(s.f&We)!==0?li(s,t,!1):t===s&&(r?Me(s,Be):(s.f&Ve)!==0&&Me(s,Tt),jt(s))}}function di(e){var m;var t=Qe,r=st,n=ut,a=ee,s=ht,o=Le,i=Et,l=Pr,c=e.f;Qe=null,st=0,ut=null,ee=(c&(Nt|Lr))===0?e:null,ht=null,rn(e.ctx),Et=!1,Pr=++Sr,e.ac!==null&&(sa(()=>{e.ac.abort(wr)}),e.ac=null);try{e.f|=Pa;var f=e.fn,g=f();e.f|=ln;var v=e.deps,_=Z==null?void 0:Z.is_fork;if(Qe!==null){var u;if(_||Mn(e,st),v!==null&&st>0)for(v.length=st+Qe.length,u=0;u<Qe.length;u++)v[st+u]=Qe[u];else e.deps=v=Qe;if(as()&&(e.f&pt)!==0)for(u=st;u<v.length;u++)((m=v[u]).reactions??(m.reactions=[])).push(e)}else!_&&v!==null&&st<v.length&&(Mn(e,st),v.length=st);if(Pn()&&ut!==null&&!Et&&v!==null&&(e.f&(We|Tt|Be))===0)for(u=0;u<ut.length;u++)li(ut[u],e);if(a!==null&&a!==e){if(Sr++,a.deps!==null)for(let p=0;p<r;p+=1)a.deps[p].rv=Sr;if(t!==null)for(const p of t)p.rv=Sr;ut!==null&&(n===null?n=ut:n.push(...ut))}return(e.f&cr)!==0&&(e.f^=cr),g}catch(p){return Oo(p)}finally{e.f^=Pa,Qe=t,st=r,ut=n,ee=a,ht=s,rn(o),Et=i,Pr=l}}function sc(e,t){let r=t.reactions;if(r!==null){var n=Hl.call(r,e);if(n!==-1){var a=r.length-1;a===0?r=t.reactions=null:(r[n]=r[a],r.pop())}}if(r===null&&(t.f&We)!==0&&(Qe===null||!tn.call(Qe,t))){var s=t;(s.f&pt)!==0&&(s.f^=pt,s.f&=~$r),es(s),Wd(s),Mn(s,0)}}function Mn(e,t){var r=e.deps;if(r!==null)for(var n=t;n<r.length;n++)sc(e,r[n])}function sn(e){var t=e.f;if((t&Dt)===0){Me(e,Ve);var r=te,n=Un;te=e,Un=!0;try{(t&(mr|na))!==0?nc(e):is(e),ei(e);var a=di(e);e.teardown=typeof a=="function"?a:null,e.wv=oi;var s;Ea&&Ad&&(e.f&Be)!==0&&e.deps}finally{Un=n,te=r}}}async function oc(){await Promise.resolve(),Nd()}function d(e){var t=e.f,r=(t&We)!==0;if(ee!==null&&!Et){var n=te!==null&&(te.f&Dt)!==0;if(!n&&(ht===null||!tn.call(ht,e))){var a=ee.deps;if((ee.f&Pa)!==0)e.rv<Sr&&(e.rv=Sr,Qe===null&&a!==null&&a[st]===e?st++:Qe===null?Qe=[e]:Qe.push(e));else{(ee.deps??(ee.deps=[])).push(e);var s=e.reactions;s===null?e.reactions=[ee]:tn.call(s,ee)||s.push(ee)}}}if(hr&&ur.has(e))return ur.get(e);if(r){var o=e;if(hr){var i=o.v;return((o.f&Ve)===0&&o.reactions!==null||fi(o))&&(i=rs(o)),ur.set(o,i),i}var l=(o.f&pt)===0&&!Et&&ee!==null&&(Un||(ee.f&pt)!==0),c=(o.f&ln)===0;On(o)&&(l&&(o.f|=pt),Go(o)),l&&!c&&(Wo(o),ci(o))}if(je!=null&&je.has(e))return je.get(e);if((e.f&cr)!==0)throw e.v;return e.v}function ci(e){if(e.f|=pt,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&We)!==0&&(t.f&pt)===0&&(Wo(t),ci(t))}function fi(e){if(e.v===$e)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(ur.has(t)||(t.f&We)!==0&&fi(t))return!0;return!1}function Ir(e){var t=Et;try{return Et=!0,e()}finally{Et=t}}function yr(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(Ft in e)Ba(e);else if(!Array.isArray(e))for(let t in e){const r=e[t];typeof r=="object"&&r&&Ft in r&&Ba(r)}}}function Ba(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let n in e)try{Ba(e[n],t)}catch{}const r=Za(e);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const n=wo(r);for(let a in n){const s=n[a].get;if(s)try{s.call(e)}catch{}}}}}function ic(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const lc=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function dc(e){return lc.includes(e)}const cc={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function fc(e){return e=e.toLowerCase(),cc[e]??e}const uc=["touchstart","touchmove"];function vc(e){return uc.includes(e)}const Ar=Symbol("events"),ui=new Set,Ga=new Set;function vi(e,t,r,n={}){function a(s){if(n.capture||Wa.call(t,s),!s.cancelBubble)return sa(()=>r==null?void 0:r.call(this,s))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Vt(()=>{t.addEventListener(e,a,n)}):t.addEventListener(e,a,n),a}function pc(e,t,r,n,a){var s={capture:n,passive:a},o=vi(e,t,r,s);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&oa(()=>{t.removeEventListener(e,o,s)})}function W(e,t,r){(t[Ar]??(t[Ar]={}))[e]=r}function cn(e){for(var t=0;t<e.length;t++)ui.add(e[t]);for(var r of Ga)r(e)}let Ys=null;function Wa(e){var p,y;var t=this,r=t.ownerDocument,n=e.type,a=((p=e.composedPath)==null?void 0:p.call(e))||[],s=a[0]||e.target;Ys=e;var o=0,i=Ys===e&&e[Ar];if(i){var l=a.indexOf(i);if(l!==-1&&(t===document||t===window)){e[Ar]=t;return}var c=a.indexOf(t);if(c===-1)return;l<=c&&(o=l)}if(s=a[o]||e.target,s!==t){Kl(e,"currentTarget",{configurable:!0,get(){return s||r}});var f=ee,g=te;mt(null),gt(null);try{for(var v,_=[];s!==null;){var u=s.assignedSlot||s.parentNode||s.host||null;try{var m=(y=s[Ar])==null?void 0:y[n];m!=null&&(!s.disabled||e.target===s)&&m.call(s,e)}catch(N){v?_.push(N):v=N}if(e.cancelBubble||u===t||u===null)break;s=u}if(v){for(let N of _)queueMicrotask(()=>{throw N});throw v}}finally{e[Ar]=t,delete e.currentTarget,mt(f),gt(g)}}}var _o;const _a=((_o=globalThis==null?void 0:globalThis.window)==null?void 0:_o.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function hc(e){return(_a==null?void 0:_a.createHTML(e))??e}function pi(e){var t=ns("template");return t.innerHTML=hc(e.replaceAll("<!>","<!---->")),t.content}function Or(e,t){var r=te;r.nodes===null&&(r.nodes={start:e,end:t,a:null,t:null})}function C(e,t){var r=(t&bd)!==0,n=(t&xd)!==0,a,s=!e.startsWith("<!>");return()=>{a===void 0&&(a=pi(s?e:"<!>"+e),r||(a=Yt(a)));var o=n||qo?document.importNode(a,!0):a.cloneNode(!0);if(r){var i=Yt(o),l=o.lastChild;Or(i,l)}else Or(o,o);return o}}function mc(e,t,r="svg"){var n=!e.startsWith("<!>"),a=`<${r}>${n?e:"<!>"+e}</${r}>`,s;return()=>{if(!s){var o=pi(a),i=Yt(o);s=Yt(i)}var l=s.cloneNode(!0);return Or(l,l),l}}function gc(e,t){return mc(e,t,"svg")}function Yn(e=""){{var t=Bt(e+"");return Or(t,t),t}}function oe(){var e=document.createDocumentFragment(),t=document.createComment(""),r=Bt();return e.append(t,r),Or(t,r),e}function S(e,t){e!==null&&e.before(t)}function ne(e,t){var r=t==null?"":typeof t=="object"?`${t}`:t;r!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=r,e.nodeValue=`${r}`)}function bc(e,t){return xc(e,t)}const Vn=new Map;function xc(e,{target:t,anchor:r,props:n={},events:a,context:s,intro:o=!0,transformError:i}){Ud();var l=void 0,c=tc(()=>{var f=r??t.appendChild(Bt());Id(f,{pending:()=>{}},_=>{Jt({});var u=Le;s&&(u.c=s),a&&(n.$$events=a),l=e(_,n)||{},Xt()},i);var g=new Set,v=_=>{for(var u=0;u<_.length;u++){var m=_[u];if(!g.has(m)){g.add(m);var p=vc(m);for(const A of[t,document]){var y=Vn.get(A);y===void 0&&(y=new Map,Vn.set(A,y));var N=y.get(m);N===void 0?(A.addEventListener(m,Wa,{passive:p}),y.set(m,1)):y.set(m,N+1)}}}};return v(ra(ui)),Ga.add(v),()=>{var p;for(var _ of g)for(const y of[t,document]){var u=Vn.get(y),m=u.get(_);--m==0?(y.removeEventListener(_,Wa),u.delete(_),u.size===0&&Vn.delete(y)):u.set(_,m)}Ga.delete(v),f!==r&&((p=f.parentNode)==null||p.removeChild(f))}});return _c.set(l,c),l}let _c=new WeakMap;var Mt,Lt,it,Tr,En,Tn,ta;class cs{constructor(t,r=!0){St(this,"anchor");re(this,Mt,new Map);re(this,Lt,new Map);re(this,it,new Map);re(this,Tr,new Set);re(this,En,!0);re(this,Tn,t=>{if(x(this,Mt).has(t)){var r=x(this,Mt).get(t),n=x(this,Lt).get(r);if(n)ls(n),x(this,Tr).delete(r);else{var a=x(this,it).get(r);a&&(a.effect.f&Ye)===0&&(x(this,Lt).set(r,a.effect),x(this,it).delete(r),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),n=a.effect)}for(const[s,o]of x(this,Mt)){if(x(this,Mt).delete(s),s===t)break;const i=x(this,it).get(o);i&&(Ge(i.effect),x(this,it).delete(o))}for(const[s,o]of x(this,Lt)){if(s===r||x(this,Tr).has(s)||(o.f&Ye)!==0)continue;const i=()=>{if(Array.from(x(this,Mt).values()).includes(s)){var c=document.createDocumentFragment();ds(o,c),c.append(Bt()),x(this,it).set(s,{effect:o,fragment:c})}else Ge(o);x(this,Tr).delete(s),x(this,Lt).delete(s)};x(this,En)||!n?(x(this,Tr).add(s),Nr(o,i,!1)):i()}}});re(this,ta,t=>{x(this,Mt).delete(t);const r=Array.from(x(this,Mt).values());for(const[n,a]of x(this,it))r.includes(n)||(Ge(a.effect),x(this,it).delete(n))});this.anchor=t,J(this,En,r)}ensure(t,r){var n=Z,a=Jo();if(r&&!x(this,Lt).has(t)&&!x(this,it).has(t))if(a){var s=document.createDocumentFragment(),o=Bt();s.append(o),x(this,it).set(t,{effect:et(()=>r(o)),fragment:s})}else x(this,Lt).set(t,et(()=>r(this.anchor)));if(x(this,Mt).set(n,t),a){for(const[i,l]of x(this,Lt))i===t?n.unskip_effect(l):n.skip_effect(l);for(const[i,l]of x(this,it))i===t?n.unskip_effect(l.effect):n.skip_effect(l.effect);n.oncommit(x(this,Tn)),n.ondiscard(x(this,ta))}else x(this,Tn).call(this,n)}}Mt=new WeakMap,Lt=new WeakMap,it=new WeakMap,Tr=new WeakMap,En=new WeakMap,Tn=new WeakMap,ta=new WeakMap;function V(e,t,r=!1){var n=new cs(e),a=r?vr:0;function s(o,i){n.ensure(o,i)}In(()=>{var o=!1;t((i,l=0)=>{o=!0,s(l,i)}),o||s(-1,null)},a)}function tt(e,t){return t}function yc(e,t,r){for(var n=[],a=t.length,s,o=t.length,i=0;i<a;i++){let g=t[i];Nr(g,()=>{if(s){if(s.pending.delete(g),s.done.add(g),s.pending.size===0){var v=e.outrogroups;Ha(e,ra(s.done)),v.delete(s),v.size===0&&(e.outrogroups=null)}}else o-=1},!1)}if(o===0){var l=n.length===0&&r!==null;if(l){var c=r,f=c.parentNode;Yd(f),f.append(c),e.items.clear()}Ha(e,t,!l)}else s={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(s)}function Ha(e,t,r=!0){var n;if(e.pending.size>0){n=new Set;for(const o of e.pending.values())for(const i of o)n.add(e.items.get(i).e)}for(var a=0;a<t.length;a++){var s=t[a];if(n!=null&&n.has(s)){s.f|=Rt;const o=document.createDocumentFragment();ds(s,o)}else Ge(t[a],r)}}var Js;function rt(e,t,r,n,a,s=null){var o=e,i=new Map,l=(t&Eo)!==0;if(l){var c=e;o=c.appendChild(Bt())}var f=null,g=ts(()=>{var A=r();return Xa(A)?A:A==null?[]:ra(A)}),v,_=new Map,u=!0;function m(A){(N.effect.f&Dt)===0&&(N.pending.delete(A),N.fallback=f,wc(N,v,o,t,n),f!==null&&(v.length===0?(f.f&Rt)===0?ls(f):(f.f^=Rt,kn(f,null,o)):Nr(f,()=>{f=null})))}function p(A){N.pending.delete(A)}var y=In(()=>{v=d(g);for(var A=v.length,w=new Set,T=Z,$=Jo(),L=0;L<A;L+=1){var M=v[L],F=n(M,L),ie=u?null:i.get(F);ie?(ie.v&&an(ie.v,M),ie.i&&an(ie.i,L),$&&T.unskip_effect(ie.e)):(ie=kc(i,u?o:Js??(Js=Bt()),M,F,L,a,t,r),u||(ie.e.f|=Rt),i.set(F,ie)),w.add(F)}if(A===0&&s&&!f&&(u?f=et(()=>s(o)):(f=et(()=>s(Js??(Js=Bt()))),f.f|=Rt)),A>w.size&&ed(),!u)if(_.set(T,w),$){for(const[Ae,me]of i)w.has(Ae)||T.skip_effect(me.e);T.oncommit(m),T.ondiscard(p)}else m(T);d(g)}),N={effect:y,items:i,pending:_,outrogroups:null,fallback:f};u=!1}function xn(e){for(;e!==null&&(e.f&Nt)===0;)e=e.next;return e}function wc(e,t,r,n,a){var ie,Ae,me,G,P,Y,B,se,ae;var s=(n&ud)!==0,o=t.length,i=e.items,l=xn(e.effect.first),c,f=null,g,v=[],_=[],u,m,p,y;if(s)for(y=0;y<o;y+=1)u=t[y],m=a(u,y),p=i.get(m).e,(p.f&Rt)===0&&((Ae=(ie=p.nodes)==null?void 0:ie.a)==null||Ae.measure(),(g??(g=new Set)).add(p));for(y=0;y<o;y+=1){if(u=t[y],m=a(u,y),p=i.get(m).e,e.outrogroups!==null)for(const D of e.outrogroups)D.pending.delete(p),D.done.delete(p);if((p.f&Rt)!==0)if(p.f^=Rt,p===l)kn(p,null,r);else{var N=f?f.next:l;p===e.effect.last&&(e.effect.last=p.prev),p.prev&&(p.prev.next=p.next),p.next&&(p.next.prev=p.prev),rr(e,f,p),rr(e,p,N),kn(p,N,r),f=p,v=[],_=[],l=xn(f.next);continue}if((p.f&Ye)!==0&&(ls(p),s&&((G=(me=p.nodes)==null?void 0:me.a)==null||G.unfix(),(g??(g=new Set)).delete(p))),p!==l){if(c!==void 0&&c.has(p)){if(v.length<_.length){var A=_[0],w;f=A.prev;var T=v[0],$=v[v.length-1];for(w=0;w<v.length;w+=1)kn(v[w],A,r);for(w=0;w<_.length;w+=1)c.delete(_[w]);rr(e,T.prev,$.next),rr(e,f,T),rr(e,$,A),l=A,f=$,y-=1,v=[],_=[]}else c.delete(p),kn(p,l,r),rr(e,p.prev,p.next),rr(e,p,f===null?e.effect.first:f.next),rr(e,f,p),f=p;continue}for(v=[],_=[];l!==null&&l!==p;)(c??(c=new Set)).add(l),_.push(l),l=xn(l.next);if(l===null)continue}(p.f&Rt)===0&&v.push(p),f=p,l=xn(p.next)}if(e.outrogroups!==null){for(const D of e.outrogroups)D.pending.size===0&&(Ha(e,ra(D.done)),(P=e.outrogroups)==null||P.delete(D));e.outrogroups.size===0&&(e.outrogroups=null)}if(l!==null||c!==void 0){var L=[];if(c!==void 0)for(p of c)(p.f&Ye)===0&&L.push(p);for(;l!==null;)(l.f&Ye)===0&&l!==e.fallback&&L.push(l),l=xn(l.next);var M=L.length;if(M>0){var F=(n&Eo)!==0&&o===0?r:null;if(s){for(y=0;y<M;y+=1)(B=(Y=L[y].nodes)==null?void 0:Y.a)==null||B.measure();for(y=0;y<M;y+=1)(ae=(se=L[y].nodes)==null?void 0:se.a)==null||ae.fix()}yc(e,L,F)}}s&&Vt(()=>{var D,E;if(g!==void 0)for(p of g)(E=(D=p.nodes)==null?void 0:D.a)==null||E.apply()})}function kc(e,t,r,n,a,s,o,i){var l=(o&cd)!==0?(o&vd)===0?Hd(r,!1,!1):pr(r):null,c=(o&fd)!==0?pr(a):null;return{v:l,i:c,e:et(()=>(s(t,l??r,c??a,i),()=>{e.delete(n)}))}}function kn(e,t,r){if(e.nodes)for(var n=e.nodes.start,a=e.nodes.end,s=t&&(t.f&Rt)===0?t.nodes.start:r;n!==null;){var o=$n(n);if(s.before(n),n===a)return;n=o}}function rr(e,t,r){t===null?e.effect.first=r:t.next=r,r===null?e.effect.last=t:r.prev=t}function Xs(e,t,r=!1,n=!1,a=!1){var s=e,o="";X(()=>{var i=te;if(o!==(o=t()??"")&&(i.nodes!==null&&(ti(i.nodes.start,i.nodes.end),i.nodes=null),o!=="")){var l=r?Po:n?_d:void 0,c=ns(r?"svg":n?"math":"template",l);c.innerHTML=o;var f=r||n?c:c.content;if(Or(Yt(f),f.lastChild),r||n)for(;Yt(f);)s.before(Yt(f));else s.before(f)}})}function ve(e,t,r,n,a){var i;var s=(i=t.$$slots)==null?void 0:i[r],o=!1;s===!0&&(s=t.children,o=!0),s===void 0||s(e,o?()=>n:n)}function Ka(e,t,...r){var n=new cs(e);In(()=>{const a=t()??null;n.ensure(a,a&&(s=>a(s,...r)))},vr)}function Sc(e,t,r,n,a,s){var o=null,i=e,l=new cs(i,!1);In(()=>{const c=t()||null;var f=Po;if(c===null){l.ensure(null,null);return}return l.ensure(c,g=>{if(c){if(o=ns(c,f),Or(o,o),n){var v=o.appendChild(Bt());n(o,v)}te.nodes.end=o,g.before(o)}}),()=>{}},vr),oa(()=>{})}function Ac(e,t){var r=void 0,n;Qo(()=>{r!==(r=t())&&(n&&(Ge(n),n=null),r&&(n=et(()=>{ss(()=>r(e))})))})}function hi(e){var t,r,n="";if(typeof e=="string"||typeof e=="number")n+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(r=hi(e[t]))&&(n&&(n+=" "),n+=r)}else for(r in e)e[r]&&(n&&(n+=" "),n+=r);return n}function mi(){for(var e,t,r=0,n="",a=arguments.length;r<a;r++)(e=arguments[r])&&(t=hi(e))&&(n&&(n+=" "),n+=t);return n}function De(e){return typeof e=="object"?mi(e):e??""}const Zs=[...` 	
\r\f \v\uFEFF`];function zc(e,t,r){var n=e==null?"":""+e;if(r){for(var a of Object.keys(r))if(r[a])n=n?n+" "+a:a;else if(n.length)for(var s=a.length,o=0;(o=n.indexOf(a,o))>=0;){var i=o+s;(o===0||Zs.includes(n[o-1]))&&(i===n.length||Zs.includes(n[i]))?n=(o===0?"":n.substring(0,o))+n.substring(i+1):o=i}}return n===""?null:n}function Qs(e,t=!1){var r=t?" !important;":";",n="";for(var a of Object.keys(e)){var s=e[a];s!=null&&s!==""&&(n+=" "+a+": "+s+r)}return n}function ya(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Mc(e,t){if(t){var r="",n,a;if(Array.isArray(t)?(n=t[0],a=t[1]):n=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var s=!1,o=0,i=!1,l=[];n&&l.push(...Object.keys(n).map(ya)),a&&l.push(...Object.keys(a).map(ya));var c=0,f=-1;const m=e.length;for(var g=0;g<m;g++){var v=e[g];if(i?v==="/"&&e[g-1]==="*"&&(i=!1):s?s===v&&(s=!1):v==="/"&&e[g+1]==="*"?i=!0:v==='"'||v==="'"?s=v:v==="("?o++:v===")"&&o--,!i&&s===!1&&o===0){if(v===":"&&f===-1)f=g;else if(v===";"||g===m-1){if(f!==-1){var _=ya(e.substring(c,f).trim());if(!l.includes(_)){v!==";"&&g++;var u=e.substring(c,g).trim();r+=" "+u+";"}}c=g+1,f=-1}}}}return n&&(r+=Qs(n)),a&&(r+=Qs(a,!0)),r=r.trim(),r===""?null:r}return e==null?null:String(e)}function Fe(e,t,r,n,a,s){var o=e.__className;if(o!==r||o===void 0){var i=zc(r,n,s);i==null?e.removeAttribute("class"):t?e.className=i:e.setAttribute("class",i),e.__className=r}else if(s&&a!==s)for(var l in s){var c=!!s[l];(a==null||c!==!!a[l])&&e.classList.toggle(l,c)}return s}function wa(e,t={},r,n){for(var a in r){var s=r[a];t[a]!==s&&(r[a]==null?e.style.removeProperty(a):e.style.setProperty(a,s,n))}}function gi(e,t,r,n){var a=e.__style;if(a!==t){var s=Mc(t,n);s==null?e.removeAttribute("style"):e.style.cssText=s,e.__style=t}else n&&(Array.isArray(n)?(wa(e,r==null?void 0:r[0],n[0]),wa(e,r==null?void 0:r[1],n[1],"important")):wa(e,r,n));return n}function qa(e,t,r=!1){if(e.multiple){if(t==null)return;if(!Xa(t))return wd();for(var n of e.options)n.selected=t.includes(eo(n));return}for(n of e.options){var a=eo(n);if(qd(a,t)){n.selected=!0;return}}(!r||t!==void 0)&&(e.selectedIndex=-1)}function Ec(e){var t=new MutationObserver(()=>{qa(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),oa(()=>{t.disconnect()})}function eo(e){return"__value"in e?e.__value:e.value}const _n=Symbol("class"),yn=Symbol("style"),bi=Symbol("is custom element"),xi=Symbol("is html"),Tc=Mo?"option":"OPTION",Nc=Mo?"select":"SELECT";function Pc(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function Xn(e,t,r,n){var a=_i(e);a[t]!==(a[t]=r)&&(t==="loading"&&(e[Zl]=r),r==null?e.removeAttribute(t):typeof r!="string"&&yi(e).includes(t)?e[t]=r:e.setAttribute(t,r))}function Cc(e,t,r,n,a=!1,s=!1){var o=_i(e),i=o[bi],l=!o[xi],c=t||{},f=e.nodeName===Tc;for(var g in t)g in r||(r[g]=null);r.class?r.class=De(r.class):r[_n]&&(r.class=null),r[yn]&&(r.style??(r.style=null));var v=yi(e);for(const w in r){let T=r[w];if(f&&w==="value"&&T==null){e.value=e.__value="",c[w]=T;continue}if(w==="class"){var _=e.namespaceURI==="http://www.w3.org/1999/xhtml";Fe(e,_,T,n,t==null?void 0:t[_n],r[_n]),c[w]=T,c[_n]=r[_n];continue}if(w==="style"){gi(e,T,t==null?void 0:t[yn],r[yn]),c[w]=T,c[yn]=r[yn];continue}var u=c[w];if(!(T===u&&!(T===void 0&&e.hasAttribute(w)))){c[w]=T;var m=w[0]+w[1];if(m!=="$$")if(m==="on"){const $={},L="$$"+w;let M=w.slice(2);var p=dc(M);if(ic(M)&&(M=M.slice(0,-7),$.capture=!0),!p&&u){if(T!=null)continue;e.removeEventListener(M,c[L],$),c[L]=null}if(p)W(M,e,T),cn([M]);else if(T!=null){let F=function(ie){c[w].call(this,ie)};var A=F;c[L]=vi(M,e,F,$)}}else if(w==="style")Xn(e,w,T);else if(w==="autofocus")Jd(e,!!T);else if(!i&&(w==="__value"||w==="value"&&T!=null))e.value=e.__value=T;else if(w==="selected"&&f)Pc(e,T);else{var y=w;l||(y=fc(y));var N=y==="defaultValue"||y==="defaultChecked";if(T==null&&!i&&!N)if(o[w]=null,y==="value"||y==="checked"){let $=e;const L=t===void 0;if(y==="value"){let M=$.defaultValue;$.removeAttribute(y),$.defaultValue=M,$.value=$.__value=L?M:null}else{let M=$.defaultChecked;$.removeAttribute(y),$.defaultChecked=M,$.checked=L?M:!1}}else e.removeAttribute(w);else N||v.includes(y)&&(i||typeof T!="string")?(e[y]=T,y in o&&(o[y]=$e)):typeof T!="function"&&Xn(e,y,T)}}}return c}function Zn(e,t,r=[],n=[],a=[],s,o=!1,i=!1){Bo(a,r,n,l=>{var c=void 0,f={},g=e.nodeName===Nc,v=!1;if(Qo(()=>{var u=t(...l.map(d)),m=Cc(e,c,u,s,o,i);v&&g&&"value"in u&&qa(e,u.value);for(let y of Object.getOwnPropertySymbols(f))u[y]||Ge(f[y]);for(let y of Object.getOwnPropertySymbols(u)){var p=u[y];y.description===yd&&(!c||p!==c[y])&&(f[y]&&Ge(f[y]),f[y]=et(()=>Ac(e,()=>p))),m[y]=p}c=m}),g){var _=e;ss(()=>{qa(_,c.value,!0),Ec(_)})}v=!0})}function _i(e){return e.__attributes??(e.__attributes={[bi]:e.nodeName.includes("-"),[xi]:e.namespaceURI===No})}var to=new Map;function yi(e){var t=e.getAttribute("is")||e.nodeName,r=to.get(t);if(r)return r;to.set(t,r=[]);for(var n,a=e,s=Element.prototype;s!==a;){n=wo(a);for(var o in n)n[o].set&&r.push(o);a=Za(a)}return r}function Kr(e,t,r=t){var n=new WeakSet;Zd(e,"input",async a=>{var s=a?e.defaultValue:e.value;if(s=ka(e)?Sa(s):s,r(s),Z!==null&&n.add(Z),await oc(),s!==(s=t())){var o=e.selectionStart,i=e.selectionEnd,l=e.value.length;if(e.value=s??"",i!==null){var c=e.value.length;o===i&&i===l&&c>l?(e.selectionStart=c,e.selectionEnd=c):(e.selectionStart=o,e.selectionEnd=Math.min(i,c))}}}),Ir(t)==null&&e.value&&(r(ka(e)?Sa(e.value):e.value),Z!==null&&n.add(Z)),os(()=>{var a=t();if(e===document.activeElement){var s=Ca??Z;if(n.has(s))return}ka(e)&&a===Sa(e.value)||e.type==="date"&&!a&&!e.value||a!==e.value&&(e.value=a??"")})}function ka(e){var t=e.type;return t==="number"||t==="range"}function Sa(e){return e===""?null:+e}function ro(e,t){return e===t||(e==null?void 0:e[Ft])===t}function wi(e={},t,r,n){return ss(()=>{var a,s;return os(()=>{a=s,s=[],Ir(()=>{e!==r(...s)&&(t(e,...s),a&&ro(r(...a),e)&&t(null,...a))})}),()=>{Vt(()=>{s&&ro(r(...s),e)&&t(null,...s)})}}),e}function $c(e=!1){const t=Le,r=t.l.u;if(!r)return;let n=()=>yr(t.s);if(e){let a=0,s={};const o=Cn(()=>{let i=!1;const l=t.s;for(const c in l)l[c]!==s[c]&&(s[c]=l[c],i=!0);return i&&a++,a});n=()=>d(o)}r.b.length&&ec(()=>{no(t,n),Ta(r.b)}),Jn(()=>{const a=Ir(()=>r.m.map(Jl));return()=>{for(const s of a)typeof s=="function"&&s()}}),r.a.length&&Jn(()=>{no(t,n),Ta(r.a)})}function no(e,t){if(e.l.s)for(const r of e.l.s)d(r);t()}let Bn=!1;function Ic(e){var t=Bn;try{return Bn=!1,[e(),Bn]}finally{Bn=t}}const Oc={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Lc(e,t,r){return new Proxy({props:e,exclude:t},Oc)}const Rc={get(e,t){if(!e.exclude.includes(t))return d(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,r){if(!(t in e.special)){var n=te;try{gt(e.parent_effect),e.special[t]=Ie({get[t](){return e.props[t]}},t,To)}finally{gt(n)}}return e.special[t](r),An(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),An(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function fe(e,t){return new Proxy({props:e,exclude:t,special:{},version:pr(0),parent_effect:te},Rc)}const jc={get(e,t){let r=e.props.length;for(;r--;){let n=e.props[r];if(bn(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n)return n[t]}},set(e,t,r){let n=e.props.length;for(;n--;){let a=e.props[n];bn(a)&&(a=a());const s=dr(a,t);if(s&&s.set)return s.set(r),!0}return!1},getOwnPropertyDescriptor(e,t){let r=e.props.length;for(;r--;){let n=e.props[r];if(bn(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n){const a=dr(n,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===Ft||t===zo)return!1;for(let r of e.props)if(bn(r)&&(r=r()),r!=null&&t in r)return!0;return!1},ownKeys(e){const t=[];for(let r of e.props)if(bn(r)&&(r=r()),!!r){for(const n in r)t.includes(n)||t.push(n);for(const n of Object.getOwnPropertySymbols(r))t.includes(n)||t.push(n)}return t}};function pe(...e){return new Proxy({props:e},jc)}function Ie(e,t,r,n){var A;var a=!Nn||(r&hd)!==0,s=(r&md)!==0,o=(r&gd)!==0,i=n,l=!0,c=()=>(l&&(l=!1,i=o?Ir(n):n),i),f;if(s){var g=Ft in e||zo in e;f=((A=dr(e,t))==null?void 0:A.set)??(g&&t in e?w=>e[t]=w:void 0)}var v,_=!1;s?[v,_]=Ic(()=>e[t]):v=e[t],v===void 0&&n!==void 0&&(v=c(),f&&(a&&sd(),f(v)));var u;if(a?u=()=>{var w=e[t];return w===void 0?c():(l=!0,w)}:u=()=>{var w=e[t];return w!==void 0&&(i=void 0),w===void 0?i:w},a&&(r&To)===0)return u;if(f){var m=e.$$legacy;return(function(w,T){return arguments.length>0?((!a||!T||m||_)&&f(T?u():w),w):u()})}var p=!1,y=((r&pd)!==0?Cn:ts)(()=>(p=!1,u()));s&&d(y);var N=te;return(function(w,T){if(arguments.length>0){const $=T?d(y):a&&s?lt(w):w;return b(y,$),p=!0,i!==void 0&&(i=$),w}return hr&&p||(N.f&Dt)!==0?y.v:d(y)})}const Dc="5";var yo;typeof window<"u"&&((yo=window.__svelte??(window.__svelte={})).v??(yo.v=new Set)).add(Dc);const Ln="";async function Fc(){const e=await fetch(`${Ln}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function Hr(e,t=null,r=null){const n={provider:e};t&&(n.model=t),r&&(n.api_key=r);const a=await fetch(`${Ln}/api/configure`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)});if(!a.ok)throw new Error("설정 실패");return a.json()}async function Vc(e){const t=await fetch(`${Ln}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function Bc(e,{onProgress:t,onDone:r,onError:n}){const a=new AbortController;return fetch(`${Ln}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:a.signal}).then(async s=>{if(!s.ok){n==null||n("다운로드 실패");return}const o=s.body.getReader(),i=new TextDecoder;let l="";for(;;){const{done:c,value:f}=await o.read();if(c)break;l+=i.decode(f,{stream:!0});const g=l.split(`
`);l=g.pop()||"";for(const v of g)if(v.startsWith("data:"))try{const _=JSON.parse(v.slice(5).trim());_.total&&_.completed!==void 0?t==null||t({total:_.total,completed:_.completed,status:_.status}):_.status&&(t==null||t({status:_.status}))}catch{}}r==null||r()}).catch(s=>{s.name!=="AbortError"&&(n==null||n(s.message))}),{abort:()=>a.abort()}}function Gc(e,t,r={},{onMeta:n,onSnapshot:a,onContext:s,onToolCall:o,onToolResult:i,onChunk:l,onDone:c,onError:f},g=null){const v={question:t,stream:!0,...r};g&&g.length>0&&(v.history=g);const _=new AbortController;return fetch(`${Ln}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(v),signal:_.signal}).then(async u=>{if(!u.ok){const w=await u.json().catch(()=>({}));f==null||f(w.detail||"스트리밍 실패");return}const m=u.body.getReader(),p=new TextDecoder;let y="",N=!1;for(;;){const{done:w,value:T}=await m.read();if(w)break;y+=p.decode(T,{stream:!0});const $=y.split(`
`);y=$.pop()||"";for(const L of $)if(L.startsWith("event:"))var A=L.slice(6).trim();else if(L.startsWith("data:")&&A){const M=L.slice(5).trim();try{const F=JSON.parse(M);A==="meta"?n==null||n(F):A==="snapshot"?a==null||a(F):A==="context"?s==null||s(F):A==="tool_call"?o==null||o(F):A==="tool_result"?i==null||i(F):A==="chunk"?l==null||l(F.text):A==="error"?f==null||f(F.error):A==="done"&&(N||(N=!0,c==null||c()))}catch{}A=null}}N||(N=!0,c==null||c())}).catch(u=>{u.name!=="AbortError"&&(f==null||f(u.message))}),{abort:()=>_.abort()}}const Wc=(e,t)=>{const r=new Array(e.length+t.length);for(let n=0;n<e.length;n++)r[n]=e[n];for(let n=0;n<t.length;n++)r[e.length+n]=t[n];return r},Hc=(e,t)=>({classGroupId:e,validator:t}),ki=(e=new Map,t=null,r)=>({nextPart:e,validators:t,classGroupId:r}),Qn="-",ao=[],Kc="arbitrary..",qc=e=>{const t=Yc(e),{conflictingClassGroups:r,conflictingClassGroupModifiers:n}=e;return{getClassGroupId:o=>{if(o.startsWith("[")&&o.endsWith("]"))return Uc(o);const i=o.split(Qn),l=i[0]===""&&i.length>1?1:0;return Si(i,l,t)},getConflictingClassGroupIds:(o,i)=>{if(i){const l=n[o],c=r[o];return l?c?Wc(c,l):l:c||ao}return r[o]||ao}}},Si=(e,t,r)=>{if(e.length-t===0)return r.classGroupId;const a=e[t],s=r.nextPart.get(a);if(s){const c=Si(e,t+1,s);if(c)return c}const o=r.validators;if(o===null)return;const i=t===0?e.join(Qn):e.slice(t).join(Qn),l=o.length;for(let c=0;c<l;c++){const f=o[c];if(f.validator(i))return f.classGroupId}},Uc=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),r=t.indexOf(":"),n=t.slice(0,r);return n?Kc+n:void 0})(),Yc=e=>{const{theme:t,classGroups:r}=e;return Jc(r,t)},Jc=(e,t)=>{const r=ki();for(const n in e){const a=e[n];fs(a,r,n,t)}return r},fs=(e,t,r,n)=>{const a=e.length;for(let s=0;s<a;s++){const o=e[s];Xc(o,t,r,n)}},Xc=(e,t,r,n)=>{if(typeof e=="string"){Zc(e,t,r);return}if(typeof e=="function"){Qc(e,t,r,n);return}ef(e,t,r,n)},Zc=(e,t,r)=>{const n=e===""?t:Ai(t,e);n.classGroupId=r},Qc=(e,t,r,n)=>{if(tf(e)){fs(e(n),t,r,n);return}t.validators===null&&(t.validators=[]),t.validators.push(Hc(r,e))},ef=(e,t,r,n)=>{const a=Object.entries(e),s=a.length;for(let o=0;o<s;o++){const[i,l]=a[o];fs(l,Ai(t,i),r,n)}},Ai=(e,t)=>{let r=e;const n=t.split(Qn),a=n.length;for(let s=0;s<a;s++){const o=n[s];let i=r.nextPart.get(o);i||(i=ki(),r.nextPart.set(o,i)),r=i}return r},tf=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,rf=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,r=Object.create(null),n=Object.create(null);const a=(s,o)=>{r[s]=o,t++,t>e&&(t=0,n=r,r=Object.create(null))};return{get(s){let o=r[s];if(o!==void 0)return o;if((o=n[s])!==void 0)return a(s,o),o},set(s,o){s in r?r[s]=o:a(s,o)}}},Ua="!",so=":",nf=[],oo=(e,t,r,n,a)=>({modifiers:e,hasImportantModifier:t,baseClassName:r,maybePostfixModifierPosition:n,isExternal:a}),af=e=>{const{prefix:t,experimentalParseClassName:r}=e;let n=a=>{const s=[];let o=0,i=0,l=0,c;const f=a.length;for(let m=0;m<f;m++){const p=a[m];if(o===0&&i===0){if(p===so){s.push(a.slice(l,m)),l=m+1;continue}if(p==="/"){c=m;continue}}p==="["?o++:p==="]"?o--:p==="("?i++:p===")"&&i--}const g=s.length===0?a:a.slice(l);let v=g,_=!1;g.endsWith(Ua)?(v=g.slice(0,-1),_=!0):g.startsWith(Ua)&&(v=g.slice(1),_=!0);const u=c&&c>l?c-l:void 0;return oo(s,_,v,u)};if(t){const a=t+so,s=n;n=o=>o.startsWith(a)?s(o.slice(a.length)):oo(nf,!1,o,void 0,!0)}if(r){const a=n;n=s=>r({className:s,parseClassName:a})}return n},sf=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((r,n)=>{t.set(r,1e6+n)}),r=>{const n=[];let a=[];for(let s=0;s<r.length;s++){const o=r[s],i=o[0]==="[",l=t.has(o);i||l?(a.length>0&&(a.sort(),n.push(...a),a=[]),n.push(o)):a.push(o)}return a.length>0&&(a.sort(),n.push(...a)),n}},of=e=>({cache:rf(e.cacheSize),parseClassName:af(e),sortModifiers:sf(e),...qc(e)}),lf=/\s+/,df=(e,t)=>{const{parseClassName:r,getClassGroupId:n,getConflictingClassGroupIds:a,sortModifiers:s}=t,o=[],i=e.trim().split(lf);let l="";for(let c=i.length-1;c>=0;c-=1){const f=i[c],{isExternal:g,modifiers:v,hasImportantModifier:_,baseClassName:u,maybePostfixModifierPosition:m}=r(f);if(g){l=f+(l.length>0?" "+l:l);continue}let p=!!m,y=n(p?u.substring(0,m):u);if(!y){if(!p){l=f+(l.length>0?" "+l:l);continue}if(y=n(u),!y){l=f+(l.length>0?" "+l:l);continue}p=!1}const N=v.length===0?"":v.length===1?v[0]:s(v).join(":"),A=_?N+Ua:N,w=A+y;if(o.indexOf(w)>-1)continue;o.push(w);const T=a(y,p);for(let $=0;$<T.length;++$){const L=T[$];o.push(A+L)}l=f+(l.length>0?" "+l:l)}return l},cf=(...e)=>{let t=0,r,n,a="";for(;t<e.length;)(r=e[t++])&&(n=zi(r))&&(a&&(a+=" "),a+=n);return a},zi=e=>{if(typeof e=="string")return e;let t,r="";for(let n=0;n<e.length;n++)e[n]&&(t=zi(e[n]))&&(r&&(r+=" "),r+=t);return r},ff=(e,...t)=>{let r,n,a,s;const o=l=>{const c=t.reduce((f,g)=>g(f),e());return r=of(c),n=r.cache.get,a=r.cache.set,s=i,i(l)},i=l=>{const c=n(l);if(c)return c;const f=df(l,r);return a(l,f),f};return s=o,(...l)=>s(cf(...l))},uf=[],Ne=e=>{const t=r=>r[e]||uf;return t.isThemeGetter=!0,t},Mi=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Ei=/^\((?:(\w[\w-]*):)?(.+)\)$/i,vf=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,pf=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,hf=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,mf=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,gf=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,bf=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,nr=e=>vf.test(e),U=e=>!!e&&!Number.isNaN(Number(e)),ar=e=>!!e&&Number.isInteger(Number(e)),Aa=e=>e.endsWith("%")&&U(e.slice(0,-1)),Kt=e=>pf.test(e),Ti=()=>!0,xf=e=>hf.test(e)&&!mf.test(e),us=()=>!1,_f=e=>gf.test(e),yf=e=>bf.test(e),wf=e=>!I(e)&&!O(e),kf=e=>gr(e,Ci,us),I=e=>Mi.test(e),_r=e=>gr(e,$i,xf),io=e=>gr(e,Pf,U),Sf=e=>gr(e,Oi,Ti),Af=e=>gr(e,Ii,us),lo=e=>gr(e,Ni,us),zf=e=>gr(e,Pi,yf),Gn=e=>gr(e,Li,_f),O=e=>Ei.test(e),wn=e=>Rr(e,$i),Mf=e=>Rr(e,Ii),co=e=>Rr(e,Ni),Ef=e=>Rr(e,Ci),Tf=e=>Rr(e,Pi),Wn=e=>Rr(e,Li,!0),Nf=e=>Rr(e,Oi,!0),gr=(e,t,r)=>{const n=Mi.exec(e);return n?n[1]?t(n[1]):r(n[2]):!1},Rr=(e,t,r=!1)=>{const n=Ei.exec(e);return n?n[1]?t(n[1]):r:!1},Ni=e=>e==="position"||e==="percentage",Pi=e=>e==="image"||e==="url",Ci=e=>e==="length"||e==="size"||e==="bg-size",$i=e=>e==="length",Pf=e=>e==="number",Ii=e=>e==="family-name",Oi=e=>e==="number"||e==="weight",Li=e=>e==="shadow",Cf=()=>{const e=Ne("color"),t=Ne("font"),r=Ne("text"),n=Ne("font-weight"),a=Ne("tracking"),s=Ne("leading"),o=Ne("breakpoint"),i=Ne("container"),l=Ne("spacing"),c=Ne("radius"),f=Ne("shadow"),g=Ne("inset-shadow"),v=Ne("text-shadow"),_=Ne("drop-shadow"),u=Ne("blur"),m=Ne("perspective"),p=Ne("aspect"),y=Ne("ease"),N=Ne("animate"),A=()=>["auto","avoid","all","avoid-page","page","left","right","column"],w=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],T=()=>[...w(),O,I],$=()=>["auto","hidden","clip","visible","scroll"],L=()=>["auto","contain","none"],M=()=>[O,I,l],F=()=>[nr,"full","auto",...M()],ie=()=>[ar,"none","subgrid",O,I],Ae=()=>["auto",{span:["full",ar,O,I]},ar,O,I],me=()=>[ar,"auto",O,I],G=()=>["auto","min","max","fr",O,I],P=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],Y=()=>["start","end","center","stretch","center-safe","end-safe"],B=()=>["auto",...M()],se=()=>[nr,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...M()],ae=()=>[nr,"screen","full","dvw","lvw","svw","min","max","fit",...M()],D=()=>[nr,"screen","full","lh","dvh","lvh","svh","min","max","fit",...M()],E=()=>[e,O,I],ge=()=>[...w(),co,lo,{position:[O,I]}],Q=()=>["no-repeat",{repeat:["","x","y","space","round"]}],le=()=>["auto","cover","contain",Ef,kf,{size:[O,I]}],_e=()=>[Aa,wn,_r],be=()=>["","none","full",c,O,I],we=()=>["",U,wn,_r],bt=()=>["solid","dashed","dotted","double"],Gt=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],ye=()=>[U,Aa,co,lo],jr=()=>["","none",u,O,I],Dr=()=>["none",U,O,I],Fr=()=>["none",U,O,I],fn=()=>[U,O,I],Zt=()=>[nr,"full",...M()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Kt],breakpoint:[Kt],color:[Ti],container:[Kt],"drop-shadow":[Kt],ease:["in","out","in-out"],font:[wf],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Kt],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Kt],shadow:[Kt],spacing:["px",U],text:[Kt],"text-shadow":[Kt],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",nr,I,O,p]}],container:["container"],columns:[{columns:[U,I,O,i]}],"break-after":[{"break-after":A()}],"break-before":[{"break-before":A()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:T()}],overflow:[{overflow:$()}],"overflow-x":[{"overflow-x":$()}],"overflow-y":[{"overflow-y":$()}],overscroll:[{overscroll:L()}],"overscroll-x":[{"overscroll-x":L()}],"overscroll-y":[{"overscroll-y":L()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:F()}],"inset-x":[{"inset-x":F()}],"inset-y":[{"inset-y":F()}],start:[{"inset-s":F(),start:F()}],end:[{"inset-e":F(),end:F()}],"inset-bs":[{"inset-bs":F()}],"inset-be":[{"inset-be":F()}],top:[{top:F()}],right:[{right:F()}],bottom:[{bottom:F()}],left:[{left:F()}],visibility:["visible","invisible","collapse"],z:[{z:[ar,"auto",O,I]}],basis:[{basis:[nr,"full","auto",i,...M()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[U,nr,"auto","initial","none",I]}],grow:[{grow:["",U,O,I]}],shrink:[{shrink:["",U,O,I]}],order:[{order:[ar,"first","last","none",O,I]}],"grid-cols":[{"grid-cols":ie()}],"col-start-end":[{col:Ae()}],"col-start":[{"col-start":me()}],"col-end":[{"col-end":me()}],"grid-rows":[{"grid-rows":ie()}],"row-start-end":[{row:Ae()}],"row-start":[{"row-start":me()}],"row-end":[{"row-end":me()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":G()}],"auto-rows":[{"auto-rows":G()}],gap:[{gap:M()}],"gap-x":[{"gap-x":M()}],"gap-y":[{"gap-y":M()}],"justify-content":[{justify:[...P(),"normal"]}],"justify-items":[{"justify-items":[...Y(),"normal"]}],"justify-self":[{"justify-self":["auto",...Y()]}],"align-content":[{content:["normal",...P()]}],"align-items":[{items:[...Y(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...Y(),{baseline:["","last"]}]}],"place-content":[{"place-content":P()}],"place-items":[{"place-items":[...Y(),"baseline"]}],"place-self":[{"place-self":["auto",...Y()]}],p:[{p:M()}],px:[{px:M()}],py:[{py:M()}],ps:[{ps:M()}],pe:[{pe:M()}],pbs:[{pbs:M()}],pbe:[{pbe:M()}],pt:[{pt:M()}],pr:[{pr:M()}],pb:[{pb:M()}],pl:[{pl:M()}],m:[{m:B()}],mx:[{mx:B()}],my:[{my:B()}],ms:[{ms:B()}],me:[{me:B()}],mbs:[{mbs:B()}],mbe:[{mbe:B()}],mt:[{mt:B()}],mr:[{mr:B()}],mb:[{mb:B()}],ml:[{ml:B()}],"space-x":[{"space-x":M()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":M()}],"space-y-reverse":["space-y-reverse"],size:[{size:se()}],"inline-size":[{inline:["auto",...ae()]}],"min-inline-size":[{"min-inline":["auto",...ae()]}],"max-inline-size":[{"max-inline":["none",...ae()]}],"block-size":[{block:["auto",...D()]}],"min-block-size":[{"min-block":["auto",...D()]}],"max-block-size":[{"max-block":["none",...D()]}],w:[{w:[i,"screen",...se()]}],"min-w":[{"min-w":[i,"screen","none",...se()]}],"max-w":[{"max-w":[i,"screen","none","prose",{screen:[o]},...se()]}],h:[{h:["screen","lh",...se()]}],"min-h":[{"min-h":["screen","lh","none",...se()]}],"max-h":[{"max-h":["screen","lh",...se()]}],"font-size":[{text:["base",r,wn,_r]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[n,Nf,Sf]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",Aa,I]}],"font-family":[{font:[Mf,Af,t]}],"font-features":[{"font-features":[I]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[a,O,I]}],"line-clamp":[{"line-clamp":[U,"none",O,io]}],leading:[{leading:[s,...M()]}],"list-image":[{"list-image":["none",O,I]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",O,I]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:E()}],"text-color":[{text:E()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...bt(),"wavy"]}],"text-decoration-thickness":[{decoration:[U,"from-font","auto",O,_r]}],"text-decoration-color":[{decoration:E()}],"underline-offset":[{"underline-offset":[U,"auto",O,I]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:M()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",O,I]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",O,I]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:ge()}],"bg-repeat":[{bg:Q()}],"bg-size":[{bg:le()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},ar,O,I],radial:["",O,I],conic:[ar,O,I]},Tf,zf]}],"bg-color":[{bg:E()}],"gradient-from-pos":[{from:_e()}],"gradient-via-pos":[{via:_e()}],"gradient-to-pos":[{to:_e()}],"gradient-from":[{from:E()}],"gradient-via":[{via:E()}],"gradient-to":[{to:E()}],rounded:[{rounded:be()}],"rounded-s":[{"rounded-s":be()}],"rounded-e":[{"rounded-e":be()}],"rounded-t":[{"rounded-t":be()}],"rounded-r":[{"rounded-r":be()}],"rounded-b":[{"rounded-b":be()}],"rounded-l":[{"rounded-l":be()}],"rounded-ss":[{"rounded-ss":be()}],"rounded-se":[{"rounded-se":be()}],"rounded-ee":[{"rounded-ee":be()}],"rounded-es":[{"rounded-es":be()}],"rounded-tl":[{"rounded-tl":be()}],"rounded-tr":[{"rounded-tr":be()}],"rounded-br":[{"rounded-br":be()}],"rounded-bl":[{"rounded-bl":be()}],"border-w":[{border:we()}],"border-w-x":[{"border-x":we()}],"border-w-y":[{"border-y":we()}],"border-w-s":[{"border-s":we()}],"border-w-e":[{"border-e":we()}],"border-w-bs":[{"border-bs":we()}],"border-w-be":[{"border-be":we()}],"border-w-t":[{"border-t":we()}],"border-w-r":[{"border-r":we()}],"border-w-b":[{"border-b":we()}],"border-w-l":[{"border-l":we()}],"divide-x":[{"divide-x":we()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":we()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...bt(),"hidden","none"]}],"divide-style":[{divide:[...bt(),"hidden","none"]}],"border-color":[{border:E()}],"border-color-x":[{"border-x":E()}],"border-color-y":[{"border-y":E()}],"border-color-s":[{"border-s":E()}],"border-color-e":[{"border-e":E()}],"border-color-bs":[{"border-bs":E()}],"border-color-be":[{"border-be":E()}],"border-color-t":[{"border-t":E()}],"border-color-r":[{"border-r":E()}],"border-color-b":[{"border-b":E()}],"border-color-l":[{"border-l":E()}],"divide-color":[{divide:E()}],"outline-style":[{outline:[...bt(),"none","hidden"]}],"outline-offset":[{"outline-offset":[U,O,I]}],"outline-w":[{outline:["",U,wn,_r]}],"outline-color":[{outline:E()}],shadow:[{shadow:["","none",f,Wn,Gn]}],"shadow-color":[{shadow:E()}],"inset-shadow":[{"inset-shadow":["none",g,Wn,Gn]}],"inset-shadow-color":[{"inset-shadow":E()}],"ring-w":[{ring:we()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:E()}],"ring-offset-w":[{"ring-offset":[U,_r]}],"ring-offset-color":[{"ring-offset":E()}],"inset-ring-w":[{"inset-ring":we()}],"inset-ring-color":[{"inset-ring":E()}],"text-shadow":[{"text-shadow":["none",v,Wn,Gn]}],"text-shadow-color":[{"text-shadow":E()}],opacity:[{opacity:[U,O,I]}],"mix-blend":[{"mix-blend":[...Gt(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":Gt()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[U]}],"mask-image-linear-from-pos":[{"mask-linear-from":ye()}],"mask-image-linear-to-pos":[{"mask-linear-to":ye()}],"mask-image-linear-from-color":[{"mask-linear-from":E()}],"mask-image-linear-to-color":[{"mask-linear-to":E()}],"mask-image-t-from-pos":[{"mask-t-from":ye()}],"mask-image-t-to-pos":[{"mask-t-to":ye()}],"mask-image-t-from-color":[{"mask-t-from":E()}],"mask-image-t-to-color":[{"mask-t-to":E()}],"mask-image-r-from-pos":[{"mask-r-from":ye()}],"mask-image-r-to-pos":[{"mask-r-to":ye()}],"mask-image-r-from-color":[{"mask-r-from":E()}],"mask-image-r-to-color":[{"mask-r-to":E()}],"mask-image-b-from-pos":[{"mask-b-from":ye()}],"mask-image-b-to-pos":[{"mask-b-to":ye()}],"mask-image-b-from-color":[{"mask-b-from":E()}],"mask-image-b-to-color":[{"mask-b-to":E()}],"mask-image-l-from-pos":[{"mask-l-from":ye()}],"mask-image-l-to-pos":[{"mask-l-to":ye()}],"mask-image-l-from-color":[{"mask-l-from":E()}],"mask-image-l-to-color":[{"mask-l-to":E()}],"mask-image-x-from-pos":[{"mask-x-from":ye()}],"mask-image-x-to-pos":[{"mask-x-to":ye()}],"mask-image-x-from-color":[{"mask-x-from":E()}],"mask-image-x-to-color":[{"mask-x-to":E()}],"mask-image-y-from-pos":[{"mask-y-from":ye()}],"mask-image-y-to-pos":[{"mask-y-to":ye()}],"mask-image-y-from-color":[{"mask-y-from":E()}],"mask-image-y-to-color":[{"mask-y-to":E()}],"mask-image-radial":[{"mask-radial":[O,I]}],"mask-image-radial-from-pos":[{"mask-radial-from":ye()}],"mask-image-radial-to-pos":[{"mask-radial-to":ye()}],"mask-image-radial-from-color":[{"mask-radial-from":E()}],"mask-image-radial-to-color":[{"mask-radial-to":E()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":w()}],"mask-image-conic-pos":[{"mask-conic":[U]}],"mask-image-conic-from-pos":[{"mask-conic-from":ye()}],"mask-image-conic-to-pos":[{"mask-conic-to":ye()}],"mask-image-conic-from-color":[{"mask-conic-from":E()}],"mask-image-conic-to-color":[{"mask-conic-to":E()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:ge()}],"mask-repeat":[{mask:Q()}],"mask-size":[{mask:le()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",O,I]}],filter:[{filter:["","none",O,I]}],blur:[{blur:jr()}],brightness:[{brightness:[U,O,I]}],contrast:[{contrast:[U,O,I]}],"drop-shadow":[{"drop-shadow":["","none",_,Wn,Gn]}],"drop-shadow-color":[{"drop-shadow":E()}],grayscale:[{grayscale:["",U,O,I]}],"hue-rotate":[{"hue-rotate":[U,O,I]}],invert:[{invert:["",U,O,I]}],saturate:[{saturate:[U,O,I]}],sepia:[{sepia:["",U,O,I]}],"backdrop-filter":[{"backdrop-filter":["","none",O,I]}],"backdrop-blur":[{"backdrop-blur":jr()}],"backdrop-brightness":[{"backdrop-brightness":[U,O,I]}],"backdrop-contrast":[{"backdrop-contrast":[U,O,I]}],"backdrop-grayscale":[{"backdrop-grayscale":["",U,O,I]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[U,O,I]}],"backdrop-invert":[{"backdrop-invert":["",U,O,I]}],"backdrop-opacity":[{"backdrop-opacity":[U,O,I]}],"backdrop-saturate":[{"backdrop-saturate":[U,O,I]}],"backdrop-sepia":[{"backdrop-sepia":["",U,O,I]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":M()}],"border-spacing-x":[{"border-spacing-x":M()}],"border-spacing-y":[{"border-spacing-y":M()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",O,I]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[U,"initial",O,I]}],ease:[{ease:["linear","initial",y,O,I]}],delay:[{delay:[U,O,I]}],animate:[{animate:["none",N,O,I]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[m,O,I]}],"perspective-origin":[{"perspective-origin":T()}],rotate:[{rotate:Dr()}],"rotate-x":[{"rotate-x":Dr()}],"rotate-y":[{"rotate-y":Dr()}],"rotate-z":[{"rotate-z":Dr()}],scale:[{scale:Fr()}],"scale-x":[{"scale-x":Fr()}],"scale-y":[{"scale-y":Fr()}],"scale-z":[{"scale-z":Fr()}],"scale-3d":["scale-3d"],skew:[{skew:fn()}],"skew-x":[{"skew-x":fn()}],"skew-y":[{"skew-y":fn()}],transform:[{transform:[O,I,"","none","gpu","cpu"]}],"transform-origin":[{origin:T()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:Zt()}],"translate-x":[{"translate-x":Zt()}],"translate-y":[{"translate-y":Zt()}],"translate-z":[{"translate-z":Zt()}],"translate-none":["translate-none"],accent:[{accent:E()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:E()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",O,I]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":M()}],"scroll-mx":[{"scroll-mx":M()}],"scroll-my":[{"scroll-my":M()}],"scroll-ms":[{"scroll-ms":M()}],"scroll-me":[{"scroll-me":M()}],"scroll-mbs":[{"scroll-mbs":M()}],"scroll-mbe":[{"scroll-mbe":M()}],"scroll-mt":[{"scroll-mt":M()}],"scroll-mr":[{"scroll-mr":M()}],"scroll-mb":[{"scroll-mb":M()}],"scroll-ml":[{"scroll-ml":M()}],"scroll-p":[{"scroll-p":M()}],"scroll-px":[{"scroll-px":M()}],"scroll-py":[{"scroll-py":M()}],"scroll-ps":[{"scroll-ps":M()}],"scroll-pe":[{"scroll-pe":M()}],"scroll-pbs":[{"scroll-pbs":M()}],"scroll-pbe":[{"scroll-pbe":M()}],"scroll-pt":[{"scroll-pt":M()}],"scroll-pr":[{"scroll-pr":M()}],"scroll-pb":[{"scroll-pb":M()}],"scroll-pl":[{"scroll-pl":M()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",O,I]}],fill:[{fill:["none",...E()]}],"stroke-w":[{stroke:[U,wn,_r,io]}],stroke:[{stroke:["none",...E()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},$f=ff(Cf);function Oe(...e){return $f(mi(e))}const Ya="dartlab-conversations",fo=50;function If(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function Of(){try{const e=localStorage.getItem(Ya);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}function Lf(e){try{localStorage.setItem(Ya,JSON.stringify(e))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{localStorage.setItem(Ya,JSON.stringify(e))}catch{}}}}function Rf(){const e=Of();let t=q(lt(e.conversations)),r=q(lt(e.activeId));d(r)&&!d(t).find(v=>v.id===d(r))&&b(r,null);function n(){Lf({conversations:d(t),activeId:d(r)})}function a(){return d(t).find(v=>v.id===d(r))||null}function s(){const v={id:If(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return b(t,[v,...d(t)],!0),d(t).length>fo&&b(t,d(t).slice(0,fo),!0),b(r,v.id,!0),n(),v.id}function o(v){d(t).find(_=>_.id===v)&&(b(r,v,!0),n())}function i(v,_,u=null){const m=a();if(!m)return;const p={role:v,text:_};u&&(p.meta=u),m.messages=[...m.messages,p],m.updatedAt=Date.now(),m.title==="새 대화"&&v==="user"&&(m.title=_.length>30?_.slice(0,30)+"...":_),b(t,[...d(t)],!0),n()}function l(v){const _=a();if(!_||_.messages.length===0)return;const u=_.messages[_.messages.length-1];Object.assign(u,v),_.updatedAt=Date.now(),b(t,[...d(t)],!0),n()}function c(v){b(t,d(t).filter(_=>_.id!==v),!0),d(r)===v&&b(r,d(t).length>0?d(t)[0].id:null,!0),n()}function f(v,_){const u=d(t).find(m=>m.id===v);u&&(u.title=_,b(t,[...d(t)],!0),n())}function g(){b(t,[],!0),b(r,null),n()}return{get conversations(){return d(t)},get activeId(){return d(r)},get active(){return a()},createConversation:s,setActive:o,addMessage:i,updateLastMessage:l,deleteConversation:c,updateTitle:f,clearAll:g}}var jf=C("<a><!></a>"),Df=C("<button><!></button>");function Ff(e,t){Jt(t,!0);let r=Ie(t,"variant",3,"default"),n=Ie(t,"size",3,"default"),a=Lc(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const s={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},o={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var i=oe(),l=H(i);{var c=g=>{var v=jf();Zn(v,u=>({class:u,...a}),[()=>Oe("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",s[r()],o[n()],t.class)]);var _=h(v);Ka(_,()=>t.children),S(g,v)},f=g=>{var v=Df();Zn(v,u=>({class:u,...a}),[()=>Oe("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",s[r()],o[n()],t.class)]);var _=h(v);Ka(_,()=>t.children),S(g,v)};V(l,g=>{t.href?g(c):g(f,-1)})}S(e,i),Xt()}zd();/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Vf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Bf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const uo=(...e)=>e.filter((t,r,n)=>!!t&&t.trim()!==""&&n.indexOf(t)===r).join(" ").trim();var Gf=gc("<svg><!><!></svg>");function he(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]),n=fe(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);Jt(t,!1);let a=Ie(t,"name",8,void 0),s=Ie(t,"color",8,"currentColor"),o=Ie(t,"size",8,24),i=Ie(t,"strokeWidth",8,2),l=Ie(t,"absoluteStrokeWidth",8,!1),c=Ie(t,"iconNode",24,()=>[]);$c();var f=Gf();Zn(f,(_,u,m)=>({...Vf,..._,...n,width:o(),height:o(),stroke:s(),"stroke-width":u,class:m}),[()=>Bf(n)?void 0:{"aria-hidden":"true"},()=>(yr(l()),yr(i()),yr(o()),Ir(()=>l()?Number(i())*24/Number(o()):i())),()=>(yr(uo),yr(a()),yr(r),Ir(()=>uo("lucide-icon","lucide",a()?`lucide-${a()}`:"",r.class)))]);var g=h(f);rt(g,1,c,tt,(_,u)=>{var m=Pe(()=>So(d(u),2));let p=()=>d(m)[0],y=()=>d(m)[1];var N=oe(),A=H(N);Sc(A,p,!0,(w,T)=>{Zn(w,()=>({...y()}))}),S(_,N)});var v=z(g);ve(v,t,"default",{}),S(e,f),Xt()}function Ri(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];he(e,pe({name:"arrow-up"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Wf(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M20 6 9 17l-5-5"}]];he(e,pe({name:"check"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Hn(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];he(e,pe({name:"circle-alert"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function vo(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];he(e,pe({name:"circle-check"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Hf(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];he(e,pe({name:"clock"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Kf(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];he(e,pe({name:"code"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function qf(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];he(e,pe({name:"coffee"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function za(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];he(e,pe({name:"database"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Ma(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];he(e,pe({name:"download"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function po(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];he(e,pe({name:"external-link"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function ji(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];he(e,pe({name:"file-text"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Uf(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];he(e,pe({name:"github"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function ho(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];he(e,pe({name:"key"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Ct(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];he(e,pe({name:"loader-circle"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Yf(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];he(e,pe({name:"menu"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function mo(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];he(e,pe({name:"message-square"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Jf(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];he(e,pe({name:"panel-left-close"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function go(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];he(e,pe({name:"plus"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Xf(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];he(e,pe({name:"search"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Zf(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];he(e,pe({name:"settings"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Qf(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];he(e,pe({name:"square"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function eu(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];he(e,pe({name:"terminal"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function tu(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];he(e,pe({name:"trash-2"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function ru(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];he(e,pe({name:"triangle-alert"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function bo(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];he(e,pe({name:"wrench"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}function Di(e,t){const r=fe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];he(e,pe({name:"x"},()=>r,{get iconNode(){return n},children:(a,s)=>{var o=oe(),i=H(o);ve(i,t,"default",{}),S(a,o)},$$slots:{default:!0}}))}var nu=C("<!> 새 대화",1),au=C('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-dl-bg-card border border-dl-border"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),su=C('<div role="button" tabindex="0"><!> <span class="flex-1 truncate"> </span> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),ou=C('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),iu=C('<div class="flex flex-col h-full min-w-[260px]"><div class="flex items-center gap-2.5 px-4 pt-4 pb-2"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <span class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</span></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 space-y-4"></div></div>'),lu=C("<button><!></button>"),du=C('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),cu=C("<aside><!></aside>");function fu(e,t){Jt(t,!0);let r=Ie(t,"conversations",19,()=>[]),n=Ie(t,"activeId",3,null),a=Ie(t,"open",3,!0),s=q("");function o(_){const u=new Date().setHours(0,0,0,0),m=u-864e5,p=u-7*864e5,y={오늘:[],어제:[],"이번 주":[],이전:[]};for(const A of _)A.updatedAt>=u?y.오늘.push(A):A.updatedAt>=m?y.어제.push(A):A.updatedAt>=p?y["이번 주"].push(A):y.이전.push(A);const N=[];for(const[A,w]of Object.entries(y))w.length>0&&N.push({label:A,items:w});return N}let i=Pe(()=>d(s).trim()?r().filter(_=>_.title.toLowerCase().includes(d(s).toLowerCase())):r()),l=Pe(()=>o(d(i)));var c=cu(),f=h(c);{var g=_=>{var u=iu(),m=z(h(u),2),p=h(m);Ff(p,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(w,T)=>{var $=nu(),L=H($);go(L,{size:16}),S(w,$)},$$slots:{default:!0}});var y=z(m,2);{var N=w=>{var T=au(),$=h(T),L=h($);Xf(L,{size:12,class:"text-dl-text-dim flex-shrink-0"});var M=z(L,2);Kr(M,()=>d(s),F=>b(s,F)),S(w,T)};V(y,w=>{r().length>3&&w(N)})}var A=z(y,2);rt(A,21,()=>d(l),tt,(w,T)=>{var $=ou(),L=h($),M=h(L),F=z(L,2);rt(F,17,()=>d(T).items,tt,(ie,Ae)=>{var me=su(),G=h(me);mo(G,{size:14,class:"flex-shrink-0 opacity-50"});var P=z(G,2),Y=h(P),B=z(P,2),se=h(B);tu(se,{size:12}),X(ae=>{Fe(me,1,ae),ne(Y,d(Ae).title)},[()=>De(Oe("w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-[13px] transition-colors group cursor-pointer",d(Ae).id===n()?"bg-dl-bg-card text-dl-text border-l-2 border-dl-primary":"text-dl-text-muted hover:bg-dl-bg-card/50 hover:text-dl-text border-l-2 border-transparent"))]),W("click",me,()=>{var ae;return(ae=t.onSelect)==null?void 0:ae.call(t,d(Ae).id)}),W("keydown",me,ae=>{var D;ae.key==="Enter"&&((D=t.onSelect)==null||D.call(t,d(Ae).id))}),W("click",B,ae=>{var D;ae.stopPropagation(),(D=t.onDelete)==null||D.call(t,d(Ae).id)}),S(ie,me)}),X(()=>ne(M,d(T).label)),S(w,$)}),S(_,u)},v=_=>{var u=du(),m=z(h(u),2),p=h(m);go(p,{size:18});var y=z(m,2);rt(y,21,()=>r().slice(0,10),tt,(N,A)=>{var w=lu(),T=h(w);mo(T,{size:16}),X($=>{Fe(w,1,$),Xn(w,"title",d(A).title)},[()=>De(Oe("p-2 rounded-lg transition-colors w-full flex justify-center",d(A).id===n()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),W("click",w,()=>{var $;return($=t.onSelect)==null?void 0:$.call(t,d(A).id)}),S(N,w)}),W("click",m,function(...N){var A;(A=t.onNewChat)==null||A.apply(this,N)}),S(_,u)};V(f,_=>{a()?_(g):_(v,-1)})}X(_=>Fe(c,1,_),[()=>De(Oe("flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",a()?"w-[260px]":"w-[52px]"))]),S(e,c),Xt()}cn(["click","keydown"]);var uu=C('<button class="text-left px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/50 text-[13px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 hover:bg-dl-bg-card transition-all duration-200 cursor-pointer"> </button>'),vu=C('<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[620px] flex flex-col items-center"><img src="/avatar.png" alt="DartLab" class="w-16 h-16 rounded-full mb-5 shadow-lg shadow-dl-primary/10"/> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-8">종목명과 질문을 입력하거나, 자유롭게 대화하세요</p> <div class="input-box large"><textarea placeholder="삼성전자 재무 건전성을 분석해줘..." rows="1" class="input-textarea"></textarea> <button><!></button></div> <div class="grid grid-cols-2 gap-2.5 mt-6 w-full max-w-[520px]"></div></div></div>');function pu(e,t){Jt(t,!0);let r=Ie(t,"inputText",15,""),n;const a=["삼성전자 재무 건전성 분석해줘","LG에너지솔루션 배당 추세는?","카카오 부채 리스크 평가해줘","현대차 영업이익률 추이 분석"];function s(m){var p;m.key==="Enter"&&!m.shiftKey&&(m.preventDefault(),(p=t.onSend)==null||p.call(t))}function o(m){m.target.style.height="auto",m.target.style.height=Math.min(m.target.scrollHeight,200)+"px"}function i(m){r(m),n&&n.focus()}var l=vu(),c=h(l),f=z(h(c),6),g=h(f);wi(g,m=>n=m,()=>n);var v=z(g,2),_=h(v);Ri(_,{size:18,strokeWidth:2.5});var u=z(f,2);rt(u,21,()=>a,tt,(m,p)=>{var y=uu(),N=h(y);X(()=>ne(N,d(p))),W("click",y,()=>i(d(p))),S(m,y)}),X((m,p)=>{Fe(v,1,m),v.disabled=p},[()=>De(Oe("send-btn",r().trim()&&"active")),()=>!r().trim()]),W("keydown",g,s),W("input",g,o),Kr(g,r),W("click",v,function(...m){var p;(p=t.onSend)==null||p.apply(this,m)}),S(e,l),Xt()}cn(["keydown","input","click"]);var hu=C("<span><!></span>");function mu(e,t){Jt(t,!0);let r=Ie(t,"variant",3,"default");const n={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border"};var a=hu(),s=h(a);Ka(s,()=>t.children),X(o=>Fe(a,1,o),[()=>De(Oe("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",n[r()],t.class))]),S(e,a),Xt()}var gu=C('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),bu=C('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),xu=C('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),_u=C('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),yu=C('<div class="mb-3 rounded-xl border border-dl-border/50 bg-dl-bg-card/30 overflow-hidden animate-fadeIn"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></div>'),wu=C('<button class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dl-border/60 bg-dl-bg-card/60 text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all"><!> <span> </span></button>'),ku=C('<div class="mb-3"><div class="flex items-center gap-1.5 mb-1.5 text-[11px] text-dl-text-dim"><!> <span>분석에 사용된 데이터</span></div> <div class="flex flex-wrap items-center gap-2"></div></div>'),Su=C('<div class="flex items-center gap-1.5 mb-3 text-[12px] text-dl-text-dim"><!> <span> </span></div>'),Au=C('<span class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dl-accent/30 bg-dl-accent/5 text-[12px] text-dl-accent"><!> </span>'),zu=C('<div class="mb-3"><div class="flex items-center gap-1.5 mb-1.5 text-[11px] text-dl-text-dim"><!> <span>사용된 도구</span></div> <div class="flex flex-wrap items-center gap-2"></div></div>'),Mu=C('<span class="text-dl-text-muted"> </span>'),Eu=C('<div class="flex items-center gap-2 h-6 text-[12px] text-dl-text-dim"><!> <span> </span> <!></div>'),Tu=C('<div class="flex items-center gap-1 mt-2 text-[10px] text-dl-text-dim"><!> <span> </span></div>'),Nu=C("<div><!></div> <!>",1),Pu=C('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="flex-1 pt-0.5 min-w-0"><!> <!> <!> <!> <!></div></div>'),Cu=C("<button> </button>"),$u=C('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),Iu=C('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Ou=C('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),Lu=C('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-1.5 text-[14px] font-medium text-dl-text"><!> <span> </span></div> <div class="flex items-center gap-2"><div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Ru=C("<!> <!>",1);function ju(e,t){Jt(t,!0);let r=q(null),n=q("rendered"),a=Pe(()=>{var u;return t.message.loading?t.message.text?"응답 생성 중...":((u=t.message.contexts)==null?void 0:u.length)>0?"분석 중...":t.message.snapshot?"데이터 확인 중...":t.message.meta?"기업 데이터 로딩 중...":"생각 중...":""}),s=Pe(()=>{var m;if(!t.message.loading||!((m=t.message.contexts)!=null&&m.length))return"";const u=t.message.contexts[t.message.contexts.length-1];return(u==null?void 0:u.label)||(u==null?void 0:u.module)||""});function o(u){if(!u)return"";let m=u.replace(/```(\w*)\n([\s\S]*?)```/g,"<pre><code>$2</code></pre>").replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^\|(.+)\|$/gm,p=>{const y=p.slice(1,-1).split("|").map(N=>N.trim());return y.every(N=>/^[\-:]+$/.test(N))?"":"<tr>"+y.map(N=>`<td>${N}</td>`).join("")+"</tr>"}).replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");return m=m.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,p=>"<ul>"+p.replace(/<br>/g,"")+"</ul>"),m=m.replace(/(<tr>.*?<\/tr>(\s*<br>)?)+/g,p=>"<table>"+p.replace(/<br>/g,"")+"</table>"),"<p>"+m+"</p>"}function i(u){b(r,u,!0),b(n,"rendered")}var l=Ru(),c=H(l);{var f=u=>{var m=gu(),p=z(h(m),2),y=h(p),N=h(y);X(()=>ne(N,t.message.text)),S(u,m)},g=u=>{var m=Pu(),p=z(h(m),2),y=h(p);{var N=G=>{mu(G,{variant:"muted",class:"mb-2",children:(P,Y)=>{var B=Yn();X(()=>ne(B,t.message.company)),S(P,B)},$$slots:{default:!0}})};V(y,G=>{t.message.company&&G(N)})}var A=z(y,2);{var w=G=>{var P=yu(),Y=h(P);rt(Y,21,()=>t.message.snapshot.items,tt,(ae,D)=>{const E=Pe(()=>d(D).status==="good"?"text-dl-success":d(D).status==="danger"?"text-dl-primary-light":d(D).status==="caution"?"text-amber-400":"text-dl-text");var ge=bu(),Q=h(ge),le=h(Q),_e=z(Q,2),be=h(_e);X(we=>{ne(le,d(D).label),Fe(_e,1,we),ne(be,d(D).value)},[()=>De(Oe("text-[14px] font-semibold leading-snug mt-0.5",d(E)))]),S(ae,ge)});var B=z(Y,2);{var se=ae=>{var D=_u();rt(D,21,()=>t.message.snapshot.warnings,tt,(E,ge)=>{var Q=xu(),le=h(Q);ru(le,{size:10});var _e=z(le);X(()=>ne(_e,` ${d(ge)??""}`)),S(E,Q)}),S(ae,D)};V(B,ae=>{var D;((D=t.message.snapshot.warnings)==null?void 0:D.length)>0&&ae(se)})}S(G,P)};V(A,G=>{var P,Y;((Y=(P=t.message.snapshot)==null?void 0:P.items)==null?void 0:Y.length)>0&&G(w)})}var T=z(A,2);{var $=G=>{var P=ku(),Y=h(P),B=h(Y);za(B,{size:11});var se=z(Y,2);rt(se,21,()=>t.message.contexts,tt,(ae,D,E)=>{var ge=wu(),Q=h(ge);za(Q,{size:13,class:"flex-shrink-0"});var le=z(Q,2),_e=h(le);X(()=>ne(_e,d(D).label||d(D).module)),W("click",ge,()=>i(E)),S(ae,ge)}),S(G,P)},L=G=>{var P=Su(),Y=h(P);Ct(Y,{size:13,class:"animate-spin"});var B=z(Y,2),se=h(B);X(()=>ne(se,d(a))),S(G,P)};V(T,G=>{var P;((P=t.message.contexts)==null?void 0:P.length)>0?G($):t.message.loading&&!t.message.text&&G(L,1)})}var M=z(T,2);{var F=G=>{var P=zu(),Y=h(P),B=h(Y);bo(B,{size:11});var se=z(Y,2);rt(se,21,()=>t.message.toolEvents,tt,(ae,D)=>{var E=oe(),ge=H(E);{var Q=le=>{var _e=Au(),be=h(_e);bo(be,{size:13});var we=z(be);X(()=>ne(we,` ${d(D).name??""}`)),S(le,_e)};V(ge,le=>{d(D).type==="call"&&le(Q)})}S(ae,E)}),S(G,P)};V(M,G=>{var P;((P=t.message.toolEvents)==null?void 0:P.length)>0&&G(F)})}var ie=z(M,2);{var Ae=G=>{var P=Eu(),Y=h(P);Ct(Y,{size:14,class:"animate-spin flex-shrink-0"});var B=z(Y,2),se=h(B),ae=z(B,2);{var D=E=>{var ge=Mu(),Q=h(ge);X(()=>ne(Q,`— ${d(s)??""}`)),S(E,ge)};V(ae,E=>{d(s)&&E(D)})}X(()=>ne(se,d(a))),S(G,P)},me=G=>{var P=Nu(),Y=H(P),B=h(Y);Xs(B,()=>o(t.message.text));var se=z(Y,2);{var ae=D=>{var E=Tu(),ge=h(E);Hf(ge,{size:10});var Q=z(ge,2),le=h(Q);X(()=>ne(le,`${t.message.duration??""}초`)),S(D,E)};V(se,D=>{t.message.duration&&!t.message.loading&&D(ae)})}X(D=>Fe(Y,1,D),[()=>De(Oe("prose-dartlab text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),S(G,P)};V(ie,G=>{t.message.loading&&!t.message.text?G(Ae):G(me,-1)})}S(u,m)};V(c,u=>{t.message.role==="user"?u(f):u(g,-1)})}var v=z(c,2);{var _=u=>{const m=Pe(()=>t.message.contexts[d(r)]);var p=Lu(),y=h(p),N=h(y),A=h(N),w=h(A),T=h(w);za(T,{size:15,class:"flex-shrink-0"});var $=z(T,2),L=h($),M=z(w,2),F=h(M),ie=h(F),Ae=h(ie);ji(Ae,{size:11});var me=z(ie,2),G=h(me);Kf(G,{size:11});var P=z(F,2),Y=h(P);Di(Y,{size:18});var B=z(A,2);{var se=Q=>{var le=$u(),_e=h(le);rt(_e,21,()=>t.message.contexts,tt,(be,we,bt)=>{var Gt=Cu(),ye=h(Gt);X(jr=>{Fe(Gt,1,jr),ne(ye,t.message.contexts[bt].label||t.message.contexts[bt].module)},[()=>De(Oe("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",bt===d(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),W("click",Gt,()=>{b(r,bt,!0)}),S(be,Gt)}),S(Q,le)};V(B,Q=>{t.message.contexts.length>1&&Q(se)})}var ae=z(N,2),D=h(ae);{var E=Q=>{var le=Iu(),_e=h(le);Xs(_e,()=>o(d(m).text)),S(Q,le)},ge=Q=>{var le=Ou(),_e=h(le);X(()=>ne(_e,d(m).text)),S(Q,le)};V(D,Q=>{d(n)==="rendered"?Q(E):Q(ge,-1)})}X((Q,le)=>{ne(L,d(m).label||d(m).module),Fe(ie,1,Q),Fe(me,1,le)},[()=>De(Oe("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",d(n)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>De(Oe("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",d(n)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),W("click",p,Q=>{Q.target===Q.currentTarget&&b(r,null)}),W("keydown",p,Q=>{Q.key==="Escape"&&b(r,null)}),W("click",ie,()=>b(n,"rendered")),W("click",me,()=>b(n,"raw")),W("click",P,()=>b(r,null)),S(u,p)};V(v,u=>{var m;d(r)!==null&&((m=t.message.contexts)!=null&&m[d(r)])&&u(_)})}S(e,l),Xt()}cn(["click","keydown"]);var Du=C('<button class="send-btn active"><!></button>'),Fu=C("<button><!></button>"),Vu=C('<div class="flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="max-w-[720px] mx-auto px-5 pt-14 pb-8 space-y-8"></div></div> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><div class="input-box"><textarea placeholder="메시지를 입력하세요..." rows="1" class="input-textarea"></textarea> <!></div></div></div></div>');function Bu(e,t){Jt(t,!0);let r=Ie(t,"messages",19,()=>[]),n=Ie(t,"isLoading",3,!1),a=Ie(t,"inputText",15,""),s=Ie(t,"scrollTrigger",3,0),o;Jn(()=>{s(),o&&setTimeout(()=>{o.scrollTop=o.scrollHeight},10)});function i(A){var w;A.key==="Enter"&&!A.shiftKey&&(A.preventDefault(),(w=t.onSend)==null||w.call(t))}function l(A){A.target.style.height="auto",A.target.style.height=Math.min(A.target.scrollHeight,200)+"px"}var c=Vu(),f=h(c),g=h(f);rt(g,21,r,tt,(A,w)=>{ju(A,{get message(){return d(w)}})}),wi(f,A=>o=A,()=>o);var v=z(f,2),_=h(v),u=h(_),m=h(u),p=z(m,2);{var y=A=>{var w=Du(),T=h(w);Qf(T,{size:14}),W("click",w,function(...$){var L;(L=t.onStop)==null||L.apply(this,$)}),S(A,w)},N=A=>{var w=Fu(),T=h(w);Ri(T,{size:16,strokeWidth:2.5}),X(($,L)=>{Fe(w,1,$),w.disabled=L},[()=>De(Oe("send-btn",a().trim()&&"active")),()=>!a().trim()]),W("click",w,function(...$){var L;(L=t.onSend)==null||L.apply(this,$)}),S(A,w)};V(p,A=>{n()?A(y):A(N,-1)})}W("keydown",m,i),W("input",m,l),Kr(m,a),S(e,c),Xt()}cn(["keydown","input","click"]);var Gu=C("<!> <span>확인 중...</span>",1),Wu=C("<!> <span>설정 필요</span>",1),Hu=C('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),Ku=C('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!> <!>',1),qu=C('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/80 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text-muted">AI Provider 확인 중...</div></div></div>'),Uu=C('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-primary/30 bg-dl-primary/5 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text">AI Provider가 설정되지 않았습니다</div> <div class="text-[11px] text-dl-text-muted mt-0.5">대화를 시작하려면 Provider를 설정해주세요</div></div> <button class="px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors flex-shrink-0">설정하기</button></div>'),Yu=C('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),Ju=C('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),Xu=C('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),Zu=C('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),Qu=C('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),ev=C('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),tv=C('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),rv=C('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),nv=C('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),av=C('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2"> </div> <div class="p-2.5 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono"> </div> <div class="text-[10px] text-dl-text-dim mt-2"> </div></div>'),sv=C('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),ov=C("<button> <!></button>"),iv=C('<div class="flex flex-wrap gap-1.5"></div>'),lv=C('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),dv=C('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),cv=C('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),fv=C('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),uv=C('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),vv=C('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),pv=C('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),hv=C("<!> <!> <!> <!> <!>",1),mv=C('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),gv=C('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden"><div class="flex items-center justify-between px-6 pt-5 pb-3"><div class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),bv=C('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5"><div class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),xv=C('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn"><div> </div></div>'),_v=C('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div class="relative flex flex-col flex-1 min-w-0 min-h-0"><div class="absolute top-0 left-0 right-0 z-10 pointer-events-none"><div class="flex items-center justify-between px-3 h-11 pointer-events-auto" style="background: linear-gradient(to bottom, var(--color-dl-bg-dark) 60%, transparent);"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center gap-1"><a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <div class="w-px h-4 bg-dl-border mx-1"></div> <button><!> <!></button></div></div> <!></div> <!></div></div>  <!> <!> <!>',1);function yv(e,t){Jt(t,!0);let r=q(""),n=q(!1),a=q(null),s=q(lt({})),o=q(lt({})),i=q(null),l=q(null),c=q(lt([])),f=q(!0),g=q(0),v=q(!0),_=q(!1),u=q(null),m=q(lt({})),p=q(lt({})),y=q(""),N=q(!1),A=q(null),w=q(""),T=q(!1),$=q(""),L=q(0),M=q(null),F=q(null),ie=q(""),Ae=q("error"),me=q(!1);function G(k,R="error",de=4e3){b(ie,k,!0),b(Ae,R,!0),b(me,!0),setTimeout(()=>{b(me,!1)},de)}const P=Rf();Jn(()=>{Y()});async function Y(){var k,R,de;b(v,!0);try{const He=await Fc();b(s,He.providers||{},!0),b(o,He.ollama||{},!0);const ue=localStorage.getItem("dartlab-provider"),K=localStorage.getItem("dartlab-model");if(ue&&((k=d(s)[ue])!=null&&k.available)){b(i,ue,!0),b(u,ue,!0),await Hr(ue,K),await B(ue);const j=d(m)[ue]||[];K&&j.includes(K)?b(l,K,!0):j.length>0&&(b(l,j[0],!0),localStorage.setItem("dartlab-model",d(l))),b(c,j,!0),b(v,!1);return}if(ue&&d(s)[ue]){b(i,ue,!0),b(u,ue,!0),await B(ue);const j=d(m)[ue]||[];b(c,j,!0),K&&j.includes(K)?b(l,K,!0):j.length>0&&b(l,j[0],!0),b(v,!1);return}for(const j of["ollama"])if((R=d(s)[j])!=null&&R.available){b(i,j,!0),b(u,j,!0),await Hr(j),await B(j);const xe=d(m)[j]||[];b(c,xe,!0),b(l,((de=d(s)[j])==null?void 0:de.model)||(xe.length>0?xe[0]:null),!0),d(l)&&localStorage.setItem("dartlab-model",d(l));break}}catch{}b(v,!1)}async function B(k){b(p,{...d(p),[k]:!0},!0);try{const R=await Vc(k);b(m,{...d(m),[k]:R.models||[]},!0)}catch{b(m,{...d(m),[k]:[]},!0)}b(p,{...d(p),[k]:!1},!0)}async function se(k){var de;b(i,k,!0),b(l,null),b(u,k,!0),localStorage.setItem("dartlab-provider",k),localStorage.removeItem("dartlab-model"),b(y,""),b(A,null);try{await Hr(k)}catch{}await B(k);const R=d(m)[k]||[];if(b(c,R,!0),R.length>0){b(l,((de=d(s)[k])==null?void 0:de.model)||R[0],!0),localStorage.setItem("dartlab-model",d(l));try{await Hr(k,d(l))}catch{}}}async function ae(k){b(l,k,!0),localStorage.setItem("dartlab-model",k);try{await Hr(d(i),k)}catch{}}function D(k){d(u)===k?b(u,null):(b(u,k,!0),B(k))}async function E(){const k=d(y).trim();if(!(!k||!d(i))){b(N,!0),b(A,null);try{const R=await Hr(d(i),d(l),k);R.available?(b(A,"success"),d(s)[d(i)]={...d(s)[d(i)],available:!0,model:R.model},!d(l)&&R.model&&b(l,R.model,!0),await B(d(i)),b(c,d(m)[d(i)]||[],!0),G("API 키 인증 성공","success")):b(A,"error")}catch{b(A,"error")}b(N,!1)}}function ge(){const k=d(w).trim();!k||d(T)||(b(T,!0),b($,"준비 중..."),b(L,0),b(M,Bc(k,{onProgress(R){R.total&&R.completed!==void 0?(b(L,Math.round(R.completed/R.total*100),!0),b($,`다운로드 중... ${d(L)}%`)):R.status&&b($,R.status,!0)},async onDone(){b(T,!1),b(M,null),b(w,""),b($,""),b(L,0),G(`${k} 다운로드 완료`,"success"),await B("ollama"),b(c,d(m).ollama||[],!0),d(c).includes(k)&&await ae(k)},onError(R){b(T,!1),b(M,null),b($,""),b(L,0),G(`다운로드 실패: ${R}`)}}),!0))}function Q(){d(M)&&(d(M).abort(),b(M,null)),b(T,!1),b(w,""),b($,""),b(L,0)}function le(){b(f,!d(f))}function _e(){if(b(y,""),b(A,null),d(i))b(u,d(i),!0);else{const k=Object.keys(d(s));b(u,k.length>0?k[0]:null,!0)}b(_,!0),d(u)&&B(d(u))}function be(){P.createConversation(),b(r,""),b(n,!1),d(a)&&(d(a).abort(),b(a,null))}function we(k){P.setActive(k),b(r,""),b(n,!1),d(a)&&(d(a).abort(),b(a,null))}function bt(k){b(F,k,!0)}function Gt(){d(F)&&(P.deleteConversation(d(F)),b(F,null))}async function ye(){var ue;const k=d(r).trim();if(!k||d(n))return;if(!d(i)||!((ue=d(s)[d(i)])!=null&&ue.available)){G("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),_e();return}P.activeId||P.createConversation(),P.addMessage("user",k),b(r,""),b(n,!0),P.addMessage("assistant",""),P.updateLastMessage({loading:!0,startedAt:Date.now()}),An(g);const R=P.active,de=[];if(R){const K=R.messages.slice(0,-2);for(const j of K)(j.role==="user"||j.role==="assistant")&&j.text&&j.text.trim()&&!j.error&&!j.loading&&de.push({role:j.role,text:j.text})}const He=Gc(null,k,{provider:d(i),model:d(l)},{onMeta(K){const j={meta:K};K.company&&(j.company=K.company),P.updateLastMessage(j)},onSnapshot(K){P.updateLastMessage({snapshot:K})},onContext(K){const j=P.active;if(!j)return;const xe=j.messages[j.messages.length-1],Ke=(xe==null?void 0:xe.contexts)||[];P.updateLastMessage({contexts:[...Ke,{module:K.module,label:K.label,text:K.text}]})},onToolCall(K){const j=P.active;if(!j)return;const xe=j.messages[j.messages.length-1],Ke=(xe==null?void 0:xe.toolEvents)||[];P.updateLastMessage({toolEvents:[...Ke,{type:"call",name:K.name,arguments:K.arguments}]})},onToolResult(K){const j=P.active;if(!j)return;const xe=j.messages[j.messages.length-1],Ke=(xe==null?void 0:xe.toolEvents)||[];P.updateLastMessage({toolEvents:[...Ke,{type:"result",name:K.name,result:K.result}]})},onChunk(K){const j=P.active;if(!j)return;const xe=j.messages[j.messages.length-1];P.updateLastMessage({text:((xe==null?void 0:xe.text)||"")+K}),An(g)},onDone(){const K=P.active,j=K==null?void 0:K.messages[K.messages.length-1],xe=j!=null&&j.startedAt?((Date.now()-j.startedAt)/1e3).toFixed(1):null;P.updateLastMessage({loading:!1,duration:xe}),b(n,!1),b(a,null),An(g)},onError(K){P.updateLastMessage({text:`오류: ${K}`,loading:!1,error:!0}),G(K),b(n,!1),b(a,null)}},de);b(a,He,!0)}function jr(){d(a)&&(d(a).abort(),b(a,null),b(n,!1),P.updateLastMessage({loading:!1}))}function Dr(k){(k.metaKey||k.ctrlKey)&&k.key==="n"&&(k.preventDefault(),be()),(k.metaKey||k.ctrlKey)&&k.shiftKey&&k.key==="S"&&(k.preventDefault(),le()),k.key==="Escape"&&d(F)?b(F,null):k.key==="Escape"&&d(_)&&b(_,!1)}let Fr=Pe(()=>{var k;return((k=P.active)==null?void 0:k.messages)||[]}),fn=Pe(()=>P.active&&P.active.messages.length>0),Zt=Pe(()=>{var k;return!d(v)&&(!d(i)||!((k=d(s)[d(i)])!=null&&k.available))});const Fi=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var ps=_v();pc("keydown",Va,Dr);var hs=H(ps),ms=h(hs);fu(ms,{get conversations(){return P.conversations},get activeId(){return P.activeId},get open(){return d(f)},onNewChat:be,onSelect:we,onDelete:bt});var Vi=z(ms,2),gs=h(Vi),bs=h(gs),ia=h(bs),Bi=h(ia);{var Gi=k=>{Jf(k,{size:18})},Wi=k=>{Yf(k,{size:18})};V(Bi,k=>{d(f)?k(Gi):k(Wi,-1)})}var Hi=z(ia,2),xs=h(Hi),Ki=h(xs);qf(Ki,{size:15});var _s=z(xs,2),qi=h(_s);ji(qi,{size:15});var ys=z(_s,2),Ui=h(ys);Uf(Ui,{size:15});var la=z(ys,4),ws=h(la);{var Yi=k=>{var R=Gu(),de=H(R);Ct(de,{size:12,class:"animate-spin"}),S(k,R)},Ji=k=>{var R=Wu(),de=H(R);Hn(de,{size:12}),S(k,R)},Xi=k=>{var R=Ku(),de=z(H(R),2),He=h(de),ue=z(de,2);{var K=Ke=>{var un=Hu(),da=z(H(un),2),ca=h(da);X(()=>ne(ca,d(l))),S(Ke,un)};V(ue,Ke=>{d(l)&&Ke(K)})}var j=z(ue,2);{var xe=Ke=>{Ct(Ke,{size:10,class:"animate-spin text-dl-primary-light"})};V(j,Ke=>{d(T)&&Ke(xe)})}X(()=>ne(He,d(i))),S(k,R)};V(ws,k=>{d(v)?k(Yi):d(Zt)?k(Ji,1):k(Xi,-1)})}var Zi=z(ws,2);Zf(Zi,{size:12});var Qi=z(bs,2);{var el=k=>{var R=qu(),de=h(R);Ct(de,{size:16,class:"text-dl-text-dim animate-spin flex-shrink-0"}),S(k,R)},tl=k=>{var R=Uu(),de=h(R);Hn(de,{size:16,class:"text-dl-primary-light flex-shrink-0"});var He=z(de,4);W("click",He,()=>_e()),S(k,R)};V(Qi,k=>{d(v)&&!d(_)?k(el):d(Zt)&&!d(_)&&k(tl,1)})}var rl=z(gs,2);{var nl=k=>{Bu(k,{get messages(){return d(Fr)},get isLoading(){return d(n)},get scrollTrigger(){return d(g)},onSend:ye,onStop:jr,get inputText(){return d(r)},set inputText(R){b(r,R,!0)}})},al=k=>{pu(k,{onSend:ye,get inputText(){return d(r)},set inputText(R){b(r,R,!0)}})};V(rl,k=>{d(fn)?k(nl):k(al,-1)})}var ks=z(hs,2);{var sl=k=>{var R=gv(),de=h(R),He=h(de),ue=z(h(He),2),K=h(ue);Di(K,{size:18});var j=z(He,2),xe=h(j);rt(xe,21,()=>Object.entries(d(s)),tt,(xt,br)=>{var Qt=Pe(()=>So(d(br),2));let ke=()=>d(Qt)[0],Je=()=>d(Qt)[1];const vn=Pe(()=>ke()===d(i)),fl=Pe(()=>d(u)===ke()),Vr=Pe(()=>Je().auth==="api_key"),As=Pe(()=>Je().auth==="cli"),Rn=Pe(()=>d(m)[ke()]||[]),zs=Pe(()=>d(p)[ke()]);var fa=mv(),ua=h(fa),Ms=h(ua),Es=z(Ms,2),Ts=h(Es),Ns=h(Ts),ul=h(Ns),vl=z(Ns,2);{var pl=Ee=>{var dt=Yu();S(Ee,dt)};V(vl,Ee=>{d(vn)&&Ee(pl)})}var hl=z(Ts,2),ml=h(hl),gl=z(Es,2),bl=h(gl);{var xl=Ee=>{vo(Ee,{size:16,class:"text-dl-success"})},_l=Ee=>{var dt=Ju(),Br=H(dt);ho(Br,{size:14,class:"text-amber-400"}),S(Ee,dt)},yl=Ee=>{var dt=Xu(),Br=H(dt);eu(Br,{size:14,class:"text-dl-text-dim"}),S(Ee,dt)};V(bl,Ee=>{Je().available?Ee(xl):d(Vr)?Ee(_l,1):d(As)&&!Je().available&&Ee(yl,2)})}var wl=z(ua,2);{var kl=Ee=>{var dt=hv(),Br=H(dt);{var Sl=Se=>{var Re=Qu(),qe=h(Re),ct=h(qe),_t=z(qe,2),at=h(_t),Wt=z(at,2),xr=h(Wt);{var pn=ce=>{Ct(ce,{size:12,class:"animate-spin"})},yt=ce=>{ho(ce,{size:12})};V(xr,ce=>{d(N)?ce(pn):ce(yt,-1)})}var er=z(_t,2);{var ze=ce=>{var wt=Zu(),Ue=h(wt);Hn(Ue,{size:12}),S(ce,wt)};V(er,ce=>{d(A)==="error"&&ce(ze)})}X(ce=>{ne(ct,Je().envKey?`환경변수 ${Je().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),Xn(at,"placeholder",ke()==="openai"?"sk-...":ke()==="claude"?"sk-ant-...":"API Key"),Wt.disabled=ce},[()=>!d(y).trim()||d(N)]),W("keydown",at,ce=>{ce.key==="Enter"&&E()}),Kr(at,()=>d(y),ce=>b(y,ce)),W("click",Wt,E),S(Se,Re)};V(Br,Se=>{d(Vr)&&!Je().available&&Se(Sl)})}var Ps=z(Br,2);{var Al=Se=>{var Re=tv(),qe=h(Re),ct=h(qe);vo(ct,{size:13,class:"text-dl-success"});var _t=z(qe,2),at=h(_t),Wt=z(at,2);{var xr=yt=>{var er=ev(),ze=h(er);{var ce=Ue=>{Ct(Ue,{size:10,class:"animate-spin"})},wt=Ue=>{var tr=Yn("변경");S(Ue,tr)};V(ze,Ue=>{d(N)?Ue(ce):Ue(wt,-1)})}X(()=>er.disabled=d(N)),W("click",er,E),S(yt,er)},pn=Pe(()=>d(y).trim());V(Wt,yt=>{d(pn)&&yt(xr)})}W("keydown",at,yt=>{yt.key==="Enter"&&E()}),Kr(at,()=>d(y),yt=>b(y,yt)),S(Se,Re)};V(Ps,Se=>{d(Vr)&&Je().available&&Se(Al)})}var Cs=z(Ps,2);{var zl=Se=>{var Re=rv(),qe=z(h(Re),2),ct=h(qe);Ma(ct,{size:14});var _t=z(ct,2);po(_t,{size:10,class:"ml-auto"}),S(Se,Re)},Ml=Se=>{var Re=nv(),qe=h(Re),ct=h(qe);Hn(ct,{size:14}),S(Se,Re)};V(Cs,Se=>{ke()==="ollama"&&!d(o).installed?Se(zl):ke()==="ollama"&&d(o).installed&&!d(o).running&&Se(Ml,1)})}var $s=z(Cs,2);{var El=Se=>{var Re=av(),qe=h(Re),ct=h(qe),_t=z(qe,2),at=h(_t),Wt=z(_t,2),xr=h(Wt);X(()=>{ne(ct,ke()==="claude-code"?"Claude Code CLI가 설치되어 있지 않습니다":"Codex CLI가 설치되어 있지 않습니다"),ne(at,ke()==="claude-code"?"npm install -g @anthropic-ai/claude-code":"npm install -g @openai/codex"),ne(xr,ke()==="claude-code"?"설치 후 `claude auth login`으로 인증하세요":"설치 후 브라우저 인증이 필요합니다")}),S(Se,Re)};V($s,Se=>{d(As)&&!Je().available&&Se(El)})}var Tl=z($s,2);{var Nl=Se=>{var Re=pv(),qe=h(Re),ct=z(h(qe),2);{var _t=ze=>{Ct(ze,{size:12,class:"animate-spin text-dl-text-dim"})};V(ct,ze=>{d(zs)&&ze(_t)})}var at=z(qe,2);{var Wt=ze=>{var ce=sv(),wt=h(ce);Ct(wt,{size:14,class:"animate-spin"}),S(ze,ce)},xr=ze=>{var ce=iv();rt(ce,21,()=>d(Rn),tt,(wt,Ue)=>{var tr=ov(),jn=h(tr),va=z(jn);{var pa=ft=>{Wf(ft,{size:10,class:"inline ml-1"})};V(va,ft=>{d(Ue)===d(l)&&d(vn)&&ft(pa)})}X(ft=>{Fe(tr,1,ft),ne(jn,`${d(Ue)??""} `)},[()=>De(Oe("px-3 py-1.5 rounded-lg text-[11px] border transition-all",d(Ue)===d(l)&&d(vn)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),W("click",tr,()=>{ke()!==d(i)&&se(ke()),ae(d(Ue))}),S(wt,tr)}),S(ze,ce)},pn=ze=>{var ce=lv();S(ze,ce)};V(at,ze=>{d(zs)&&d(Rn).length===0?ze(Wt):d(Rn).length>0?ze(xr,1):ze(pn,-1)})}var yt=z(at,2);{var er=ze=>{var ce=vv(),wt=h(ce),Ue=z(h(wt),2),tr=z(h(Ue));po(tr,{size:9});var jn=z(wt,2);{var va=ft=>{var hn=dv(),mn=h(hn),Gr=h(mn),gn=h(Gr);Ct(gn,{size:12,class:"animate-spin text-dl-primary-light"});var ha=z(Gr,2),Dn=z(mn,2),Ht=h(Dn),kt=z(Dn,2),ma=h(kt);X(()=>{gi(Ht,`width: ${d(L)??""}%`),ne(ma,d($))}),W("click",ha,Q),S(ft,hn)},pa=ft=>{var hn=uv(),mn=H(hn),Gr=h(mn),gn=z(Gr,2),ha=h(gn);Ma(ha,{size:12});var Dn=z(mn,2);rt(Dn,21,()=>Fi,tt,(Ht,kt)=>{const ma=Pe(()=>d(Rn).some(Wr=>Wr===d(kt).name||Wr===d(kt).name.split(":")[0]));var Is=oe(),Pl=H(Is);{var Cl=Wr=>{var ga=fv(),Os=h(ga),Ls=h(Os),Rs=h(Ls),$l=h(Rs),js=z(Rs,2),Il=h(js),Ol=z(js,2);{var Ll=ba=>{var Fs=cv(),Bl=h(Fs);X(()=>ne(Bl,d(kt).tag)),S(ba,Fs)};V(Ol,ba=>{d(kt).tag&&ba(Ll)})}var Rl=z(Ls,2),jl=h(Rl),Dl=z(Os,2),Ds=h(Dl),Fl=h(Ds),Vl=z(Ds,2);Ma(Vl,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),X(()=>{ne($l,d(kt).name),ne(Il,d(kt).size),ne(jl,d(kt).desc),ne(Fl,`${d(kt).gb??""} GB`)}),W("click",ga,()=>{b(w,d(kt).name,!0),ge()}),S(Wr,ga)};V(Pl,Wr=>{d(ma)||Wr(Cl)})}S(Ht,Is)}),X(Ht=>gn.disabled=Ht,[()=>!d(w).trim()]),W("keydown",Gr,Ht=>{Ht.key==="Enter"&&ge()}),Kr(Gr,()=>d(w),Ht=>b(w,Ht)),W("click",gn,ge),S(ft,hn)};V(jn,ft=>{d(T)?ft(va):ft(pa,-1)})}S(ze,ce)};V(yt,ze=>{ke()==="ollama"&&ze(er)})}S(Se,Re)};V(Tl,Se=>{(Je().available||d(Vr))&&Se(Nl)})}S(Ee,dt)};V(wl,Ee=>{(d(fl)||d(vn))&&Ee(kl)})}X((Ee,dt)=>{Fe(fa,1,Ee),Fe(Ms,1,dt),ne(ul,Je().label||ke()),ne(ml,Je().desc||"")},[()=>De(Oe("rounded-xl border transition-all",d(vn)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>De(Oe("w-2.5 h-2.5 rounded-full flex-shrink-0",Je().available?"bg-dl-success":d(Vr)?"bg-amber-400":"bg-dl-text-dim"))]),W("click",ua,()=>{Je().available||d(Vr)?ke()===d(i)?D(ke()):se(ke()):D(ke())}),S(xt,fa)});var Ke=z(j,2),un=h(Ke),da=h(un);{var ca=xt=>{var br=Yn();X(()=>{var Qt;return ne(br,`현재: ${(((Qt=d(s)[d(i)])==null?void 0:Qt.label)||d(i))??""} / ${d(l)??""}`)}),S(xt,br)},dl=xt=>{var br=Yn();X(()=>{var Qt;return ne(br,`현재: ${(((Qt=d(s)[d(i)])==null?void 0:Qt.label)||d(i))??""}`)}),S(xt,br)};V(da,xt=>{d(i)&&d(l)?xt(ca):d(i)&&xt(dl,1)})}var cl=z(un,2);W("click",R,xt=>{xt.target===xt.currentTarget&&b(_,!1)}),W("keydown",R,()=>{}),W("click",ue,()=>b(_,!1)),W("click",cl,()=>b(_,!1)),S(k,R)};V(ks,k=>{d(_)&&k(sl)})}var Ss=z(ks,2);{var ol=k=>{var R=bv(),de=h(R),He=z(h(de),4),ue=h(He),K=z(ue,2);W("click",R,j=>{j.target===j.currentTarget&&b(F,null)}),W("keydown",R,()=>{}),W("click",ue,()=>b(F,null)),W("click",K,Gt),S(k,R)};V(Ss,k=>{d(F)&&k(ol)})}var il=z(Ss,2);{var ll=k=>{var R=xv(),de=h(R),He=h(de);X(ue=>{Fe(de,1,ue),ne(He,d(ie))},[()=>De(Oe("px-4 py-3 rounded-xl border text-[13px] shadow-2xl max-w-sm",d(Ae)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":d(Ae)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),S(k,R)};V(il,k=>{d(me)&&k(ll)})}X(k=>Fe(la,1,k),[()=>De(Oe("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",d(v)?"text-dl-text-dim":d(Zt)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),W("click",ia,le),W("click",la,()=>_e()),S(e,ps),Xt()}cn(["click","keydown"]);bc(yv,{target:document.getElementById("app")});
