var Dd=Object.defineProperty;var oi=e=>{throw TypeError(e)};var jd=(e,t,r)=>t in e?Dd(e,t,{enumerable:!0,configurable:!0,writable:!0,value:r}):e[t]=r;var sn=(e,t,r)=>jd(e,typeof t!="symbol"?t+"":t,r),eo=(e,t,r)=>t.has(e)||oi("Cannot "+r);var M=(e,t,r)=>(eo(e,t,"read from private field"),r?r.call(e):t.get(e)),rt=(e,t,r)=>t.has(e)?oi("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,r),Be=(e,t,r,a)=>(eo(e,t,"write to private field"),a?a.call(e,r):t.set(e,r),r),rr=(e,t,r)=>(eo(e,t,"access private method"),r);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))a(s);new MutationObserver(s=>{for(const o of s)if(o.type==="childList")for(const i of o.addedNodes)i.tagName==="LINK"&&i.rel==="modulepreload"&&a(i)}).observe(document,{childList:!0,subtree:!0});function r(s){const o={};return s.integrity&&(o.integrity=s.integrity),s.referrerPolicy&&(o.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?o.credentials="include":s.crossOrigin==="anonymous"?o.credentials="omit":o.credentials="same-origin",o}function a(s){if(s.ep)return;s.ep=!0;const o=r(s);fetch(s.href,o)}})();const lo=!1;var No=Array.isArray,Vd=Array.prototype.indexOf,Wa=Array.prototype.includes,Gs=Array.from,qd=Object.defineProperty,sa=Object.getOwnPropertyDescriptor,qi=Object.getOwnPropertyDescriptors,Fd=Object.prototype,Bd=Array.prototype,$o=Object.getPrototypeOf,ii=Object.isExtensible;function is(e){return typeof e=="function"}const Gd=()=>{};function Hd(e){return e()}function co(e){for(var t=0;t<e.length;t++)e[t]()}function Fi(){var e,t,r=new Promise((a,s)=>{e=a,t=s});return{promise:r,resolve:e,reject:t}}function Bi(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const r=[];for(const a of e)if(r.push(a),r.length===t)break;return r}const br=2,es=4,za=8,Hs=1<<24,ua=16,vn=32,Pa=64,uo=128,Yr=512,hr=1024,gr=2048,fn=4096,zr=8192,Sn=16384,ts=32768,Fn=65536,li=1<<17,Ud=1<<18,rs=1<<19,Gi=1<<20,kn=1<<25,Aa=65536,fo=1<<21,Lo=1<<22,oa=1<<23,Mn=Symbol("$state"),Hi=Symbol("legacy props"),Wd=Symbol(""),xa=new class extends Error{constructor(){super(...arguments);sn(this,"name","StaleReactionError");sn(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var Di;const Ui=!!((Di=globalThis.document)!=null&&Di.contentType)&&globalThis.document.contentType.includes("xml");function Kd(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function Yd(e,t,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function Xd(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function Jd(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Qd(e){throw new Error("https://svelte.dev/e/effect_orphan")}function Zd(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function ec(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function tc(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function rc(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function nc(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function ac(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const sc=1,oc=2,Wi=4,ic=8,lc=16,dc=1,cc=2,Ki=4,uc=8,fc=16,vc=1,pc=2,ir=Symbol(),Yi="http://www.w3.org/1999/xhtml",Xi="http://www.w3.org/2000/svg",mc="http://www.w3.org/1998/Math/MathML",hc="@attach";function gc(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function xc(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Ji(e){return e===this.v}function bc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function Qi(e){return!bc(e,this.v)}let Ss=!1,_c=!1;function wc(){Ss=!0}let lr=null;function Ka(e){lr=e}function Zr(e,t=!1,r){lr={p:lr,i:!1,c:null,e:null,s:e,x:null,l:Ss&&!t?{s:null,u:null,$:[]}:null}}function en(e){var t=lr,r=t.e;if(r!==null){t.e=null;for(var a of r)xl(a)}return t.i=!0,lr=t.p,{}}function Ms(){return!Ss||lr!==null&&lr.l===null}let ba=[];function Zi(){var e=ba;ba=[],co(e)}function En(e){if(ba.length===0&&!hs){var t=ba;queueMicrotask(()=>{t===ba&&Zi()})}ba.push(e)}function yc(){for(;ba.length>0;)Zi()}function el(e){var t=Je;if(t===null)return Xe.f|=oa,e;if((t.f&ts)===0&&(t.f&es)===0)throw e;ra(e,t)}function ra(e,t){for(;t!==null;){if((t.f&uo)!==0){if((t.f&ts)===0)throw e;try{t.b.error(e);return}catch(r){e=r}}t=t.parent}throw e}const kc=-7169;function Wt(e,t){e.f=e.f&kc|t}function Oo(e){(e.f&Yr)!==0||e.deps===null?Wt(e,hr):Wt(e,fn)}function tl(e){if(e!==null)for(const t of e)(t.f&br)===0||(t.f&Aa)===0||(t.f^=Aa,tl(t.deps))}function rl(e,t,r){(e.f&gr)!==0?t.add(e):(e.f&fn)!==0&&r.add(e),tl(e.deps),Wt(e,hr)}const Is=new Set;let Ge=null,vo=null,mr=null,Ir=[],Us=null,hs=!1,Ya=null,Cc=1;var Zn,ja,ya,Va,qa,Fa,ea,bn,Ba,$r,po,mo,ho,go;const Ko=class Ko{constructor(){rt(this,$r);sn(this,"id",Cc++);sn(this,"current",new Map);sn(this,"previous",new Map);rt(this,Zn,new Set);rt(this,ja,new Set);rt(this,ya,0);rt(this,Va,0);rt(this,qa,null);rt(this,Fa,new Set);rt(this,ea,new Set);rt(this,bn,new Map);sn(this,"is_fork",!1);rt(this,Ba,!1)}skip_effect(t){M(this,bn).has(t)||M(this,bn).set(t,{d:[],m:[]})}unskip_effect(t){var r=M(this,bn).get(t);if(r){M(this,bn).delete(t);for(var a of r.d)Wt(a,gr),Cn(a);for(a of r.m)Wt(a,fn),Cn(a)}}process(t){var s;Ir=[],this.apply();var r=Ya=[],a=[];for(const o of t)rr(this,$r,mo).call(this,o,r,a);if(Ya=null,rr(this,$r,po).call(this)){rr(this,$r,ho).call(this,a),rr(this,$r,ho).call(this,r);for(const[o,i]of M(this,bn))ol(o,i)}else{vo=this,Ge=null;for(const o of M(this,Zn))o(this);M(this,Zn).clear(),M(this,ya)===0&&rr(this,$r,go).call(this),di(a),di(r),M(this,Fa).clear(),M(this,ea).clear(),vo=null,(s=M(this,qa))==null||s.resolve()}mr=null}capture(t,r){r!==ir&&!this.previous.has(t)&&this.previous.set(t,r),(t.f&oa)===0&&(this.current.set(t,t.v),mr==null||mr.set(t,t.v))}activate(){Ge=this,this.apply()}deactivate(){Ge===this&&(Ge=null,mr=null)}flush(){var t;if(Ir.length>0)Ge=this,nl();else if(M(this,ya)===0&&!this.is_fork){for(const r of M(this,Zn))r(this);M(this,Zn).clear(),rr(this,$r,go).call(this),(t=M(this,qa))==null||t.resolve()}this.deactivate()}discard(){for(const t of M(this,ja))t(this);M(this,ja).clear()}increment(t){Be(this,ya,M(this,ya)+1),t&&Be(this,Va,M(this,Va)+1)}decrement(t){Be(this,ya,M(this,ya)-1),t&&Be(this,Va,M(this,Va)-1),!M(this,Ba)&&(Be(this,Ba,!0),En(()=>{Be(this,Ba,!1),rr(this,$r,po).call(this)?Ir.length>0&&this.flush():this.revive()}))}revive(){for(const t of M(this,Fa))M(this,ea).delete(t),Wt(t,gr),Cn(t);for(const t of M(this,ea))Wt(t,fn),Cn(t);this.flush()}oncommit(t){M(this,Zn).add(t)}ondiscard(t){M(this,ja).add(t)}settled(){return(M(this,qa)??Be(this,qa,Fi())).promise}static ensure(){if(Ge===null){const t=Ge=new Ko;Is.add(Ge),hs||En(()=>{Ge===t&&t.flush()})}return Ge}apply(){}};Zn=new WeakMap,ja=new WeakMap,ya=new WeakMap,Va=new WeakMap,qa=new WeakMap,Fa=new WeakMap,ea=new WeakMap,bn=new WeakMap,Ba=new WeakMap,$r=new WeakSet,po=function(){return this.is_fork||M(this,Va)>0},mo=function(t,r,a){t.f^=hr;for(var s=t.first;s!==null;){var o=s.f,i=(o&(vn|Pa))!==0,l=i&&(o&hr)!==0,c=(o&zr)!==0,f=l||M(this,bn).has(s);if(!f&&s.fn!==null){i?c||(s.f^=hr):(o&es)!==0?r.push(s):(o&(za|Hs))!==0&&c?a.push(s):As(s)&&(Ja(s),(o&ua)!==0&&(M(this,ea).add(s),c&&Wt(s,gr)));var p=s.first;if(p!==null){s=p;continue}}for(;s!==null;){var b=s.next;if(b!==null){s=b;break}s=s.parent}}},ho=function(t){for(var r=0;r<t.length;r+=1)rl(t[r],M(this,Fa),M(this,ea))},go=function(){var o;if(Is.size>1){this.previous.clear();var t=Ge,r=mr,a=!0;for(const i of Is){if(i===this){a=!1;continue}const l=[];for(const[f,p]of this.current){if(i.current.has(f))if(a&&p!==i.current.get(f))i.current.set(f,p);else continue;l.push(f)}if(l.length===0)continue;const c=[...i.current.keys()].filter(f=>!this.current.has(f));if(c.length>0){var s=Ir;Ir=[];const f=new Set,p=new Map;for(const b of l)al(b,c,f,p);if(Ir.length>0){Ge=i,i.apply();for(const b of Ir)rr(o=i,$r,mo).call(o,b,[],[]);i.deactivate()}Ir=s}}Ge=t,mr=r}M(this,bn).clear(),Is.delete(this)};let ia=Ko;function Sc(e){var t=hs;hs=!0;try{for(var r;;){if(yc(),Ir.length===0&&(Ge==null||Ge.flush(),Ir.length===0))return Us=null,r;nl()}}finally{hs=t}}function nl(){var e=null;try{for(var t=0;Ir.length>0;){var r=ia.ensure();if(t++>1e3){var a,s;Mc()}r.process(Ir),la.clear()}}finally{Ir=[],Us=null,Ya=null}}function Mc(){try{Zd()}catch(e){ra(e,Us)}}let on=null;function di(e){var t=e.length;if(t!==0){for(var r=0;r<t;){var a=e[r++];if((a.f&(Sn|zr))===0&&As(a)&&(on=new Set,Ja(a),a.deps===null&&a.first===null&&a.nodes===null&&a.teardown===null&&a.ac===null&&yl(a),(on==null?void 0:on.size)>0)){la.clear();for(const s of on){if((s.f&(Sn|zr))!==0)continue;const o=[s];let i=s.parent;for(;i!==null;)on.has(i)&&(on.delete(i),o.push(i)),i=i.parent;for(let l=o.length-1;l>=0;l--){const c=o[l];(c.f&(Sn|zr))===0&&Ja(c)}}on.clear()}}on=null}}function al(e,t,r,a){if(!r.has(e)&&(r.add(e),e.reactions!==null))for(const s of e.reactions){const o=s.f;(o&br)!==0?al(s,t,r,a):(o&(Lo|ua))!==0&&(o&gr)===0&&sl(s,t,a)&&(Wt(s,gr),Cn(s))}}function sl(e,t,r){const a=r.get(e);if(a!==void 0)return a;if(e.deps!==null)for(const s of e.deps){if(Wa.call(t,s))return!0;if((s.f&br)!==0&&sl(s,t,r))return r.set(s,!0),!0}return r.set(e,!1),!1}function Cn(e){var t=Us=e,r=t.b;if(r!=null&&r.is_pending&&(e.f&(es|za|Hs))!==0&&(e.f&ts)===0){r.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var a=t.f;if(Ya!==null&&t===Je&&(e.f&za)===0)return;if((a&(Pa|vn))!==0){if((a&hr)===0)return;t.f^=hr}}Ir.push(t)}function ol(e,t){if(!((e.f&vn)!==0&&(e.f&hr)!==0)){(e.f&gr)!==0?t.d.push(e):(e.f&fn)!==0&&t.m.push(e),Wt(e,hr);for(var r=e.first;r!==null;)ol(r,t),r=r.next}}function Ec(e){let t=0,r=da(0),a;return()=>{Vo()&&(n(r),Fo(()=>(t===0&&(a=Ta(()=>e(()=>xs(r)))),t+=1,()=>{En(()=>{t-=1,t===0&&(a==null||a(),a=void 0,xs(r))})})))}}var zc=Fn|rs;function Ac(e,t,r,a){new Tc(e,t,r,a)}var Kr,Po,_n,ka,Tr,wn,Fr,ln,Rn,Ca,ta,Ga,Ha,Ua,Dn,Fs,ar,Ic,Pc,Nc,xo,Os,Rs,bo;class Tc{constructor(t,r,a,s){rt(this,ar);sn(this,"parent");sn(this,"is_pending",!1);sn(this,"transform_error");rt(this,Kr);rt(this,Po,null);rt(this,_n);rt(this,ka);rt(this,Tr);rt(this,wn,null);rt(this,Fr,null);rt(this,ln,null);rt(this,Rn,null);rt(this,Ca,0);rt(this,ta,0);rt(this,Ga,!1);rt(this,Ha,new Set);rt(this,Ua,new Set);rt(this,Dn,null);rt(this,Fs,Ec(()=>(Be(this,Dn,da(M(this,Ca))),()=>{Be(this,Dn,null)})));var o;Be(this,Kr,t),Be(this,_n,r),Be(this,ka,i=>{var l=Je;l.b=this,l.f|=uo,a(i)}),this.parent=Je.b,this.transform_error=s??((o=this.parent)==null?void 0:o.transform_error)??(i=>i),Be(this,Tr,ns(()=>{rr(this,ar,xo).call(this)},zc))}defer_effect(t){rl(t,M(this,Ha),M(this,Ua))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!M(this,_n).pending}update_pending_count(t){rr(this,ar,bo).call(this,t),Be(this,Ca,M(this,Ca)+t),!(!M(this,Dn)||M(this,Ga))&&(Be(this,Ga,!0),En(()=>{Be(this,Ga,!1),M(this,Dn)&&Xa(M(this,Dn),M(this,Ca))}))}get_effect_pending(){return M(this,Fs).call(this),n(M(this,Dn))}error(t){var r=M(this,_n).onerror;let a=M(this,_n).failed;if(!r&&!a)throw t;M(this,wn)&&(xr(M(this,wn)),Be(this,wn,null)),M(this,Fr)&&(xr(M(this,Fr)),Be(this,Fr,null)),M(this,ln)&&(xr(M(this,ln)),Be(this,ln,null));var s=!1,o=!1;const i=()=>{if(s){xc();return}s=!0,o&&ac(),M(this,ln)!==null&&Ma(M(this,ln),()=>{Be(this,ln,null)}),rr(this,ar,Rs).call(this,()=>{ia.ensure(),rr(this,ar,xo).call(this)})},l=c=>{try{o=!0,r==null||r(c,i),o=!1}catch(f){ra(f,M(this,Tr)&&M(this,Tr).parent)}a&&Be(this,ln,rr(this,ar,Rs).call(this,()=>{ia.ensure();try{return Nr(()=>{var f=Je;f.b=this,f.f|=uo,a(M(this,Kr),()=>c,()=>i)})}catch(f){return ra(f,M(this,Tr).parent),null}}))};En(()=>{var c;try{c=this.transform_error(t)}catch(f){ra(f,M(this,Tr)&&M(this,Tr).parent);return}c!==null&&typeof c=="object"&&typeof c.then=="function"?c.then(l,f=>ra(f,M(this,Tr)&&M(this,Tr).parent)):l(c)})}}Kr=new WeakMap,Po=new WeakMap,_n=new WeakMap,ka=new WeakMap,Tr=new WeakMap,wn=new WeakMap,Fr=new WeakMap,ln=new WeakMap,Rn=new WeakMap,Ca=new WeakMap,ta=new WeakMap,Ga=new WeakMap,Ha=new WeakMap,Ua=new WeakMap,Dn=new WeakMap,Fs=new WeakMap,ar=new WeakSet,Ic=function(){try{Be(this,wn,Nr(()=>M(this,ka).call(this,M(this,Kr))))}catch(t){this.error(t)}},Pc=function(t){const r=M(this,_n).failed;r&&Be(this,ln,Nr(()=>{r(M(this,Kr),()=>t,()=>()=>{})}))},Nc=function(){const t=M(this,_n).pending;t&&(this.is_pending=!0,Be(this,Fr,Nr(()=>t(M(this,Kr)))),En(()=>{var r=Be(this,Rn,document.createDocumentFragment()),a=zn();r.append(a),Be(this,wn,rr(this,ar,Rs).call(this,()=>(ia.ensure(),Nr(()=>M(this,ka).call(this,a))))),M(this,ta)===0&&(M(this,Kr).before(r),Be(this,Rn,null),Ma(M(this,Fr),()=>{Be(this,Fr,null)}),rr(this,ar,Os).call(this))}))},xo=function(){try{if(this.is_pending=this.has_pending_snippet(),Be(this,ta,0),Be(this,Ca,0),Be(this,wn,Nr(()=>{M(this,ka).call(this,M(this,Kr))})),M(this,ta)>0){var t=Be(this,Rn,document.createDocumentFragment());Ho(M(this,wn),t);const r=M(this,_n).pending;Be(this,Fr,Nr(()=>r(M(this,Kr))))}else rr(this,ar,Os).call(this)}catch(r){this.error(r)}},Os=function(){this.is_pending=!1;for(const t of M(this,Ha))Wt(t,gr),Cn(t);for(const t of M(this,Ua))Wt(t,fn),Cn(t);M(this,Ha).clear(),M(this,Ua).clear()},Rs=function(t){var r=Je,a=Xe,s=lr;Qr(M(this,Tr)),Jr(M(this,Tr)),Ka(M(this,Tr).ctx);try{return t()}catch(o){return el(o),null}finally{Qr(r),Jr(a),Ka(s)}},bo=function(t){var r;if(!this.has_pending_snippet()){this.parent&&rr(r=this.parent,ar,bo).call(r,t);return}Be(this,ta,M(this,ta)+t),M(this,ta)===0&&(rr(this,ar,Os).call(this),M(this,Fr)&&Ma(M(this,Fr),()=>{Be(this,Fr,null)}),M(this,Rn)&&(M(this,Kr).before(M(this,Rn)),Be(this,Rn,null)))};function il(e,t,r,a){const s=Ms()?Es:Ro;var o=e.filter(b=>!b.settled);if(r.length===0&&o.length===0){a(t.map(s));return}var i=Je,l=$c(),c=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(b=>b.promise)):null;function f(b){l();try{a(b)}catch(w){(i.f&Sn)===0&&ra(w,i)}_o()}if(r.length===0){c.then(()=>f(t.map(s)));return}function p(){l(),Promise.all(r.map(b=>Oc(b))).then(b=>f([...t.map(s),...b])).catch(b=>ra(b,i))}c?c.then(p):p()}function $c(){var e=Je,t=Xe,r=lr,a=Ge;return function(o=!0){Qr(e),Jr(t),Ka(r),o&&(a==null||a.activate())}}function _o(e=!0){Qr(null),Jr(null),Ka(null),e&&(Ge==null||Ge.deactivate())}function Lc(){var e=Je.b,t=Ge,r=e.is_rendered();return e.update_pending_count(1),t.increment(r),()=>{e.update_pending_count(-1),t.decrement(r)}}function Es(e){var t=br|gr,r=Xe!==null&&(Xe.f&br)!==0?Xe:null;return Je!==null&&(Je.f|=rs),{ctx:lr,deps:null,effects:null,equals:Ji,f:t,fn:e,reactions:null,rv:0,v:ir,wv:0,parent:r??Je,ac:null}}function Oc(e,t,r){Je===null&&Kd();var s=void 0,o=da(ir),i=!Xe,l=new Map;return Xc(()=>{var w;var c=Fi();s=c.promise;try{Promise.resolve(e()).then(c.resolve,c.reject).finally(_o)}catch(z){c.reject(z),_o()}var f=Ge;if(i){var p=Lc();(w=l.get(f))==null||w.reject(xa),l.delete(f),l.set(f,c)}const b=(z,y=void 0)=>{if(f.activate(),y)y!==xa&&(o.f|=oa,Xa(o,y));else{(o.f&oa)!==0&&(o.f^=oa),Xa(o,z);for(const[I,k]of l){if(l.delete(I),I===f)break;k.reject(xa)}}p&&p()};c.promise.then(b,z=>b(null,z||"unknown"))}),Ks(()=>{for(const c of l.values())c.reject(xa)}),new Promise(c=>{function f(p){function b(){p===s?c(o):f(s)}p.then(b,b)}f(s)})}function q(e){const t=Es(e);return Sl(t),t}function Ro(e){const t=Es(e);return t.equals=Qi,t}function Rc(e){var t=e.effects;if(t!==null){e.effects=null;for(var r=0;r<t.length;r+=1)xr(t[r])}}function Dc(e){for(var t=e.parent;t!==null;){if((t.f&br)===0)return(t.f&Sn)===0?t:null;t=t.parent}return null}function Do(e){var t,r=Je;Qr(Dc(e));try{e.f&=~Aa,Rc(e),t=Al(e)}finally{Qr(r)}return t}function ll(e){var t=Do(e);if(!e.equals(t)&&(e.wv=El(),(!(Ge!=null&&Ge.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){Wt(e,hr);return}ca||(mr!==null?(Vo()||Ge!=null&&Ge.is_fork)&&mr.set(e,t):Oo(e))}function jc(e){var t,r;if(e.effects!==null)for(const a of e.effects)(a.teardown||a.ac)&&((t=a.teardown)==null||t.call(a),(r=a.ac)==null||r.abort(xa),a.teardown=Gd,a.ac=null,ys(a,0),Bo(a))}function dl(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&Ja(t)}let wo=new Set;const la=new Map;let cl=!1;function da(e,t){var r={f:0,v:e,reactions:null,equals:Ji,rv:0,wv:0};return r}function B(e,t){const r=da(e);return Sl(r),r}function Vc(e,t=!1,r=!0){var s;const a=da(e);return t||(a.equals=Qi),Ss&&r&&lr!==null&&lr.l!==null&&((s=lr.l).s??(s.s=[])).push(a),a}function u(e,t,r=!1){Xe!==null&&(!un||(Xe.f&li)!==0)&&Ms()&&(Xe.f&(br|ua|Lo|li))!==0&&(Xr===null||!Wa.call(Xr,e))&&nc();let a=r?jt(t):t;return Xa(e,a)}function Xa(e,t){if(!e.equals(t)){var r=e.v;ca?la.set(e,t):la.set(e,r),e.v=t;var a=ia.ensure();if(a.capture(e,r),(e.f&br)!==0){const s=e;(e.f&gr)!==0&&Do(s),Oo(s)}e.wv=El(),ul(e,gr),Ms()&&Je!==null&&(Je.f&hr)!==0&&(Je.f&(vn|Pa))===0&&(Wr===null?Qc([e]):Wr.push(e)),!a.is_fork&&wo.size>0&&!cl&&qc()}return t}function qc(){cl=!1;for(const e of wo)(e.f&hr)!==0&&Wt(e,fn),As(e)&&Ja(e);wo.clear()}function gs(e,t=1){var r=n(e),a=t===1?r++:r--;return u(e,r),a}function xs(e){u(e,e.v+1)}function ul(e,t){var r=e.reactions;if(r!==null)for(var a=Ms(),s=r.length,o=0;o<s;o++){var i=r[o],l=i.f;if(!(!a&&i===Je)){var c=(l&gr)===0;if(c&&Wt(i,t),(l&br)!==0){var f=i;mr==null||mr.delete(f),(l&Aa)===0&&(l&Yr&&(i.f|=Aa),ul(f,fn))}else c&&((l&ua)!==0&&on!==null&&on.add(i),Cn(i))}}}function jt(e){if(typeof e!="object"||e===null||Mn in e)return e;const t=$o(e);if(t!==Fd&&t!==Bd)return e;var r=new Map,a=No(e),s=B(0),o=Ea,i=l=>{if(Ea===o)return l();var c=Xe,f=Ea;Jr(null),vi(o);var p=l();return Jr(c),vi(f),p};return a&&r.set("length",B(e.length)),new Proxy(e,{defineProperty(l,c,f){(!("value"in f)||f.configurable===!1||f.enumerable===!1||f.writable===!1)&&tc();var p=r.get(c);return p===void 0?i(()=>{var b=B(f.value);return r.set(c,b),b}):u(p,f.value,!0),!0},deleteProperty(l,c){var f=r.get(c);if(f===void 0){if(c in l){const p=i(()=>B(ir));r.set(c,p),xs(s)}}else u(f,ir),xs(s);return!0},get(l,c,f){var z;if(c===Mn)return e;var p=r.get(c),b=c in l;if(p===void 0&&(!b||(z=sa(l,c))!=null&&z.writable)&&(p=i(()=>{var y=jt(b?l[c]:ir),I=B(y);return I}),r.set(c,p)),p!==void 0){var w=n(p);return w===ir?void 0:w}return Reflect.get(l,c,f)},getOwnPropertyDescriptor(l,c){var f=Reflect.getOwnPropertyDescriptor(l,c);if(f&&"value"in f){var p=r.get(c);p&&(f.value=n(p))}else if(f===void 0){var b=r.get(c),w=b==null?void 0:b.v;if(b!==void 0&&w!==ir)return{enumerable:!0,configurable:!0,value:w,writable:!0}}return f},has(l,c){var w;if(c===Mn)return!0;var f=r.get(c),p=f!==void 0&&f.v!==ir||Reflect.has(l,c);if(f!==void 0||Je!==null&&(!p||(w=sa(l,c))!=null&&w.writable)){f===void 0&&(f=i(()=>{var z=p?jt(l[c]):ir,y=B(z);return y}),r.set(c,f));var b=n(f);if(b===ir)return!1}return p},set(l,c,f,p){var W;var b=r.get(c),w=c in l;if(a&&c==="length")for(var z=f;z<b.v;z+=1){var y=r.get(z+"");y!==void 0?u(y,ir):z in l&&(y=i(()=>B(ir)),r.set(z+"",y))}if(b===void 0)(!w||(W=sa(l,c))!=null&&W.writable)&&(b=i(()=>B(void 0)),u(b,jt(f)),r.set(c,b));else{w=b.v!==ir;var I=i(()=>jt(f));u(b,I)}var k=Reflect.getOwnPropertyDescriptor(l,c);if(k!=null&&k.set&&k.set.call(p,f),!w){if(a&&typeof c=="string"){var C=r.get("length"),D=Number(c);Number.isInteger(D)&&D>=C.v&&u(C,D+1)}xs(s)}return!0},ownKeys(l){n(s);var c=Reflect.ownKeys(l).filter(b=>{var w=r.get(b);return w===void 0||w.v!==ir});for(var[f,p]of r)p.v!==ir&&!(f in l)&&c.push(f);return c},setPrototypeOf(){rc()}})}function ci(e){try{if(e!==null&&typeof e=="object"&&Mn in e)return e[Mn]}catch{}return e}function Fc(e,t){return Object.is(ci(e),ci(t))}var yo,fl,vl,pl;function Bc(){if(yo===void 0){yo=window,fl=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,r=Text.prototype;vl=sa(t,"firstChild").get,pl=sa(t,"nextSibling").get,ii(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),ii(r)&&(r.__t=void 0)}}function zn(e=""){return document.createTextNode(e)}function Vn(e){return vl.call(e)}function zs(e){return pl.call(e)}function d(e,t){return Vn(e)}function Z(e,t=!1){{var r=Vn(e);return r instanceof Comment&&r.data===""?zs(r):r}}function m(e,t=1,r=!1){let a=e;for(;t--;)a=zs(a);return a}function Gc(e){e.textContent=""}function ml(){return!1}function jo(e,t,r){return document.createElementNS(t??Yi,e,void 0)}function hl(e,t){if(t){const r=document.body;e.autofocus=!0,En(()=>{document.activeElement===r&&e.focus()})}}let ui=!1;function Hc(){ui||(ui=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const r of e.target.elements)(t=r.__on_r)==null||t.call(r)})},{capture:!0}))}function Ws(e){var t=Xe,r=Je;Jr(null),Qr(null);try{return e()}finally{Jr(t),Qr(r)}}function Uc(e,t,r,a=r){e.addEventListener(t,()=>Ws(r));const s=e.__on_r;s?e.__on_r=()=>{s(),a(!0)}:e.__on_r=()=>a(!0),Hc()}function gl(e){Je===null&&(Xe===null&&Qd(),Jd()),ca&&Xd()}function Wc(e,t){var r=t.last;r===null?t.last=t.first=e:(r.next=e,e.prev=r,t.last=e)}function pn(e,t){var r=Je;r!==null&&(r.f&zr)!==0&&(e|=zr);var a={ctx:lr,deps:null,nodes:null,f:e|gr|Yr,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},s=a;if((e&es)!==0)Ya!==null?Ya.push(a):Cn(a);else if(t!==null){try{Ja(a)}catch(i){throw xr(a),i}s.deps===null&&s.teardown===null&&s.nodes===null&&s.first===s.last&&(s.f&rs)===0&&(s=s.first,(e&ua)!==0&&(e&Fn)!==0&&s!==null&&(s.f|=Fn))}if(s!==null&&(s.parent=r,r!==null&&Wc(s,r),Xe!==null&&(Xe.f&br)!==0&&(e&Pa)===0)){var o=Xe;(o.effects??(o.effects=[])).push(s)}return a}function Vo(){return Xe!==null&&!un}function Ks(e){const t=pn(za,null);return Wt(t,hr),t.teardown=e,t}function na(e){gl();var t=Je.f,r=!Xe&&(t&vn)!==0&&(t&ts)===0;if(r){var a=lr;(a.e??(a.e=[])).push(e)}else return xl(e)}function xl(e){return pn(es|Gi,e)}function Kc(e){return gl(),pn(za|Gi,e)}function Yc(e){ia.ensure();const t=pn(Pa|rs,e);return(r={})=>new Promise(a=>{r.outro?Ma(t,()=>{xr(t),a(void 0)}):(xr(t),a(void 0))})}function qo(e){return pn(es,e)}function Xc(e){return pn(Lo|rs,e)}function Fo(e,t=0){return pn(za|t,e)}function N(e,t=[],r=[],a=[]){il(a,t,r,s=>{pn(za,()=>e(...s.map(n)))})}function ns(e,t=0){var r=pn(ua|t,e);return r}function bl(e,t=0){var r=pn(Hs|t,e);return r}function Nr(e){return pn(vn|rs,e)}function _l(e){var t=e.teardown;if(t!==null){const r=ca,a=Xe;fi(!0),Jr(null);try{t.call(null)}finally{fi(r),Jr(a)}}}function Bo(e,t=!1){var r=e.first;for(e.first=e.last=null;r!==null;){const s=r.ac;s!==null&&Ws(()=>{s.abort(xa)});var a=r.next;(r.f&Pa)!==0?r.parent=null:xr(r,t),r=a}}function Jc(e){for(var t=e.first;t!==null;){var r=t.next;(t.f&vn)===0&&xr(t),t=r}}function xr(e,t=!0){var r=!1;(t||(e.f&Ud)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(wl(e.nodes.start,e.nodes.end),r=!0),Bo(e,t&&!r),ys(e,0),Wt(e,Sn);var a=e.nodes&&e.nodes.t;if(a!==null)for(const o of a)o.stop();_l(e);var s=e.parent;s!==null&&s.first!==null&&yl(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function wl(e,t){for(;e!==null;){var r=e===t?null:zs(e);e.remove(),e=r}}function yl(e){var t=e.parent,r=e.prev,a=e.next;r!==null&&(r.next=a),a!==null&&(a.prev=r),t!==null&&(t.first===e&&(t.first=a),t.last===e&&(t.last=r))}function Ma(e,t,r=!0){var a=[];kl(e,a,!0);var s=()=>{r&&xr(e),t&&t()},o=a.length;if(o>0){var i=()=>--o||s();for(var l of a)l.out(i)}else s()}function kl(e,t,r){if((e.f&zr)===0){e.f^=zr;var a=e.nodes&&e.nodes.t;if(a!==null)for(const l of a)(l.is_global||r)&&t.push(l);for(var s=e.first;s!==null;){var o=s.next,i=(s.f&Fn)!==0||(s.f&vn)!==0&&(e.f&ua)!==0;kl(s,t,i?r:!1),s=o}}}function Go(e){Cl(e,!0)}function Cl(e,t){if((e.f&zr)!==0){e.f^=zr;for(var r=e.first;r!==null;){var a=r.next,s=(r.f&Fn)!==0||(r.f&vn)!==0;Cl(r,s?t:!1),r=a}var o=e.nodes&&e.nodes.t;if(o!==null)for(const i of o)(i.is_global||t)&&i.in()}}function Ho(e,t){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end;r!==null;){var s=r===a?null:zs(r);t.append(r),r=s}}let Ds=!1,ca=!1;function fi(e){ca=e}let Xe=null,un=!1;function Jr(e){Xe=e}let Je=null;function Qr(e){Je=e}let Xr=null;function Sl(e){Xe!==null&&(Xr===null?Xr=[e]:Xr.push(e))}let Pr=null,qr=0,Wr=null;function Qc(e){Wr=e}let Ml=1,_a=0,Ea=_a;function vi(e){Ea=e}function El(){return++Ml}function As(e){var t=e.f;if((t&gr)!==0)return!0;if(t&br&&(e.f&=~Aa),(t&fn)!==0){for(var r=e.deps,a=r.length,s=0;s<a;s++){var o=r[s];if(As(o)&&ll(o),o.wv>e.wv)return!0}(t&Yr)!==0&&mr===null&&Wt(e,hr)}return!1}function zl(e,t,r=!0){var a=e.reactions;if(a!==null&&!(Xr!==null&&Wa.call(Xr,e)))for(var s=0;s<a.length;s++){var o=a[s];(o.f&br)!==0?zl(o,t,!1):t===o&&(r?Wt(o,gr):(o.f&hr)!==0&&Wt(o,fn),Cn(o))}}function Al(e){var I;var t=Pr,r=qr,a=Wr,s=Xe,o=Xr,i=lr,l=un,c=Ea,f=e.f;Pr=null,qr=0,Wr=null,Xe=(f&(vn|Pa))===0?e:null,Xr=null,Ka(e.ctx),un=!1,Ea=++_a,e.ac!==null&&(Ws(()=>{e.ac.abort(xa)}),e.ac=null);try{e.f|=fo;var p=e.fn,b=p();e.f|=ts;var w=e.deps,z=Ge==null?void 0:Ge.is_fork;if(Pr!==null){var y;if(z||ys(e,qr),w!==null&&qr>0)for(w.length=qr+Pr.length,y=0;y<Pr.length;y++)w[qr+y]=Pr[y];else e.deps=w=Pr;if(Vo()&&(e.f&Yr)!==0)for(y=qr;y<w.length;y++)((I=w[y]).reactions??(I.reactions=[])).push(e)}else!z&&w!==null&&qr<w.length&&(ys(e,qr),w.length=qr);if(Ms()&&Wr!==null&&!un&&w!==null&&(e.f&(br|fn|gr))===0)for(y=0;y<Wr.length;y++)zl(Wr[y],e);if(s!==null&&s!==e){if(_a++,s.deps!==null)for(let k=0;k<r;k+=1)s.deps[k].rv=_a;if(t!==null)for(const k of t)k.rv=_a;Wr!==null&&(a===null?a=Wr:a.push(...Wr))}return(e.f&oa)!==0&&(e.f^=oa),b}catch(k){return el(k)}finally{e.f^=fo,Pr=t,qr=r,Wr=a,Xe=s,Xr=o,Ka(i),un=l,Ea=c}}function Zc(e,t){let r=t.reactions;if(r!==null){var a=Vd.call(r,e);if(a!==-1){var s=r.length-1;s===0?r=t.reactions=null:(r[a]=r[s],r.pop())}}if(r===null&&(t.f&br)!==0&&(Pr===null||!Wa.call(Pr,t))){var o=t;(o.f&Yr)!==0&&(o.f^=Yr,o.f&=~Aa),Oo(o),jc(o),ys(o,0)}}function ys(e,t){var r=e.deps;if(r!==null)for(var a=t;a<r.length;a++)Zc(e,r[a])}function Ja(e){var t=e.f;if((t&Sn)===0){Wt(e,hr);var r=Je,a=Ds;Je=e,Ds=!0;try{(t&(ua|Hs))!==0?Jc(e):Bo(e),_l(e);var s=Al(e);e.teardown=typeof s=="function"?s:null,e.wv=Ml;var o;lo&&_c&&(e.f&gr)!==0&&e.deps}finally{Ds=a,Je=r}}}async function eu(){await Promise.resolve(),Sc()}function n(e){var t=e.f,r=(t&br)!==0;if(Xe!==null&&!un){var a=Je!==null&&(Je.f&Sn)!==0;if(!a&&(Xr===null||!Wa.call(Xr,e))){var s=Xe.deps;if((Xe.f&fo)!==0)e.rv<_a&&(e.rv=_a,Pr===null&&s!==null&&s[qr]===e?qr++:Pr===null?Pr=[e]:Pr.push(e));else{(Xe.deps??(Xe.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[Xe]:Wa.call(o,Xe)||o.push(Xe)}}}if(ca&&la.has(e))return la.get(e);if(r){var i=e;if(ca){var l=i.v;return((i.f&hr)===0&&i.reactions!==null||Il(i))&&(l=Do(i)),la.set(i,l),l}var c=(i.f&Yr)===0&&!un&&Xe!==null&&(Ds||(Xe.f&Yr)!==0),f=(i.f&ts)===0;As(i)&&(c&&(i.f|=Yr),ll(i)),c&&!f&&(dl(i),Tl(i))}if(mr!=null&&mr.has(e))return mr.get(e);if((e.f&oa)!==0)throw e.v;return e.v}function Tl(e){if(e.f|=Yr,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&br)!==0&&(t.f&Yr)===0&&(dl(t),Tl(t))}function Il(e){if(e.v===ir)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(la.has(t)||(t.f&br)!==0&&Il(t))return!0;return!1}function Ta(e){var t=un;try{return un=!0,e()}finally{un=t}}function ga(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(Mn in e)ko(e);else if(!Array.isArray(e))for(let t in e){const r=e[t];typeof r=="object"&&r&&Mn in r&&ko(r)}}}function ko(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let a in e)try{ko(e[a],t)}catch{}const r=$o(e);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const a=qi(r);for(let s in a){const o=a[s].get;if(o)try{o.call(e)}catch{}}}}}function tu(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const ru=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function nu(e){return ru.includes(e)}const au={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function su(e){return e=e.toLowerCase(),au[e]??e}const ou=["touchstart","touchmove"];function iu(e){return ou.includes(e)}const wa=Symbol("events"),Pl=new Set,Co=new Set;function Nl(e,t,r,a={}){function s(o){if(a.capture||So.call(t,o),!o.cancelBubble)return Ws(()=>r==null?void 0:r.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?En(()=>{t.addEventListener(e,s,a)}):t.addEventListener(e,s,a),s}function Da(e,t,r,a,s){var o={capture:a,passive:s},i=Nl(e,t,r,o);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&Ks(()=>{t.removeEventListener(e,i,o)})}function se(e,t,r){(t[wa]??(t[wa]={}))[e]=r}function Bn(e){for(var t=0;t<e.length;t++)Pl.add(e[t]);for(var r of Co)r(e)}let pi=null;function So(e){var k,C;var t=this,r=t.ownerDocument,a=e.type,s=((k=e.composedPath)==null?void 0:k.call(e))||[],o=s[0]||e.target;pi=e;var i=0,l=pi===e&&e[wa];if(l){var c=s.indexOf(l);if(c!==-1&&(t===document||t===window)){e[wa]=t;return}var f=s.indexOf(t);if(f===-1)return;c<=f&&(i=c)}if(o=s[i]||e.target,o!==t){qd(e,"currentTarget",{configurable:!0,get(){return o||r}});var p=Xe,b=Je;Jr(null),Qr(null);try{for(var w,z=[];o!==null;){var y=o.assignedSlot||o.parentNode||o.host||null;try{var I=(C=o[wa])==null?void 0:C[a];I!=null&&(!o.disabled||e.target===o)&&I.call(o,e)}catch(D){w?z.push(D):w=D}if(e.cancelBubble||y===t||y===null)break;o=y}if(w){for(let D of z)queueMicrotask(()=>{throw D});throw w}}finally{e[wa]=t,delete e.currentTarget,Jr(p),Qr(b)}}}var ji;const to=((ji=globalThis==null?void 0:globalThis.window)==null?void 0:ji.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function lu(e){return(to==null?void 0:to.createHTML(e))??e}function $l(e){var t=jo("template");return t.innerHTML=lu(e.replaceAll("<!>","<!---->")),t.content}function Ia(e,t){var r=Je;r.nodes===null&&(r.nodes={start:e,end:t,a:null,t:null})}function h(e,t){var r=(t&vc)!==0,a=(t&pc)!==0,s,o=!e.startsWith("<!>");return()=>{s===void 0&&(s=$l(o?e:"<!>"+e),r||(s=Vn(s)));var i=a||fl?document.importNode(s,!0):s.cloneNode(!0);if(r){var l=Vn(i),c=i.lastChild;Ia(l,c)}else Ia(i,i);return i}}function du(e,t,r="svg"){var a=!e.startsWith("<!>"),s=`<${r}>${a?e:"<!>"+e}</${r}>`,o;return()=>{if(!o){var i=$l(s),l=Vn(i);o=Vn(l)}var c=o.cloneNode(!0);return Ia(c,c),c}}function cu(e,t){return du(e,t,"svg")}function Qn(e=""){{var t=zn(e+"");return Ia(t,t),t}}function Ce(){var e=document.createDocumentFragment(),t=document.createComment(""),r=zn();return e.append(t,r),Ia(t,r),e}function v(e,t){e!==null&&e.before(t)}function P(e,t){var r=t==null?"":typeof t=="object"?`${t}`:t;r!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=r,e.nodeValue=`${r}`)}function uu(e,t){return fu(e,t)}const Ps=new Map;function fu(e,{target:t,anchor:r,props:a={},events:s,context:o,intro:i=!0,transformError:l}){Bc();var c=void 0,f=Yc(()=>{var p=r??t.appendChild(zn());Ac(p,{pending:()=>{}},z=>{Zr({});var y=lr;o&&(y.c=o),s&&(a.$$events=s),c=e(z,a)||{},en()},l);var b=new Set,w=z=>{for(var y=0;y<z.length;y++){var I=z[y];if(!b.has(I)){b.add(I);var k=iu(I);for(const W of[t,document]){var C=Ps.get(W);C===void 0&&(C=new Map,Ps.set(W,C));var D=C.get(I);D===void 0?(W.addEventListener(I,So,{passive:k}),C.set(I,1)):C.set(I,D+1)}}}};return w(Gs(Pl)),Co.add(w),()=>{var k;for(var z of b)for(const C of[t,document]){var y=Ps.get(C),I=y.get(z);--I==0?(C.removeEventListener(z,So),y.delete(z),y.size===0&&Ps.delete(C)):y.set(z,I)}Co.delete(w),p!==r&&((k=p.parentNode)==null||k.removeChild(p))}});return vu.set(c,f),c}let vu=new WeakMap;var dn,yn,Br,Sa,ks,Cs,Bs;class Ys{constructor(t,r=!0){sn(this,"anchor");rt(this,dn,new Map);rt(this,yn,new Map);rt(this,Br,new Map);rt(this,Sa,new Set);rt(this,ks,!0);rt(this,Cs,t=>{if(M(this,dn).has(t)){var r=M(this,dn).get(t),a=M(this,yn).get(r);if(a)Go(a),M(this,Sa).delete(r);else{var s=M(this,Br).get(r);s&&(s.effect.f&zr)===0&&(M(this,yn).set(r,s.effect),M(this,Br).delete(r),s.fragment.lastChild.remove(),this.anchor.before(s.fragment),a=s.effect)}for(const[o,i]of M(this,dn)){if(M(this,dn).delete(o),o===t)break;const l=M(this,Br).get(i);l&&(xr(l.effect),M(this,Br).delete(i))}for(const[o,i]of M(this,yn)){if(o===r||M(this,Sa).has(o)||(i.f&zr)!==0)continue;const l=()=>{if(Array.from(M(this,dn).values()).includes(o)){var f=document.createDocumentFragment();Ho(i,f),f.append(zn()),M(this,Br).set(o,{effect:i,fragment:f})}else xr(i);M(this,Sa).delete(o),M(this,yn).delete(o)};M(this,ks)||!a?(M(this,Sa).add(o),Ma(i,l,!1)):l()}}});rt(this,Bs,t=>{M(this,dn).delete(t);const r=Array.from(M(this,dn).values());for(const[a,s]of M(this,Br))r.includes(a)||(xr(s.effect),M(this,Br).delete(a))});this.anchor=t,Be(this,ks,r)}ensure(t,r){var a=Ge,s=ml();if(r&&!M(this,yn).has(t)&&!M(this,Br).has(t))if(s){var o=document.createDocumentFragment(),i=zn();o.append(i),M(this,Br).set(t,{effect:Nr(()=>r(i)),fragment:o})}else M(this,yn).set(t,Nr(()=>r(this.anchor)));if(M(this,dn).set(a,t),s){for(const[l,c]of M(this,yn))l===t?a.unskip_effect(c):a.skip_effect(c);for(const[l,c]of M(this,Br))l===t?a.unskip_effect(c.effect):a.skip_effect(c.effect);a.oncommit(M(this,Cs)),a.ondiscard(M(this,Bs))}else M(this,Cs).call(this,a)}}dn=new WeakMap,yn=new WeakMap,Br=new WeakMap,Sa=new WeakMap,ks=new WeakMap,Cs=new WeakMap,Bs=new WeakMap;function E(e,t,r=!1){var a=new Ys(e),s=r?Fn:0;function o(i,l){a.ensure(i,l)}ns(()=>{var i=!1;t((l,c=0)=>{i=!0,o(c,l)}),i||o(-1,null)},s)}function Ie(e,t){return t}function pu(e,t,r){for(var a=[],s=t.length,o,i=t.length,l=0;l<s;l++){let b=t[l];Ma(b,()=>{if(o){if(o.pending.delete(b),o.done.add(b),o.pending.size===0){var w=e.outrogroups;Mo(e,Gs(o.done)),w.delete(o),w.size===0&&(e.outrogroups=null)}}else i-=1},!1)}if(i===0){var c=a.length===0&&r!==null;if(c){var f=r,p=f.parentNode;Gc(p),p.append(f),e.items.clear()}Mo(e,t,!c)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function Mo(e,t,r=!0){var a;if(e.pending.size>0){a=new Set;for(const i of e.pending.values())for(const l of i)a.add(e.items.get(l).e)}for(var s=0;s<t.length;s++){var o=t[s];if(a!=null&&a.has(o)){o.f|=kn;const i=document.createDocumentFragment();Ho(o,i)}else xr(t[s],r)}}var mi;function Pe(e,t,r,a,s,o=null){var i=e,l=new Map,c=(t&Wi)!==0;if(c){var f=e;i=f.appendChild(zn())}var p=null,b=Ro(()=>{var W=r();return No(W)?W:W==null?[]:Gs(W)}),w,z=new Map,y=!0;function I(W){(D.effect.f&Sn)===0&&(D.pending.delete(W),D.fallback=p,mu(D,w,i,t,a),p!==null&&(w.length===0?(p.f&kn)===0?Go(p):(p.f^=kn,ms(p,null,i)):Ma(p,()=>{p=null})))}function k(W){D.pending.delete(W)}var C=ns(()=>{w=n(b);for(var W=w.length,S=new Set,j=Ge,de=ml(),$=0;$<W;$+=1){var x=w[$],H=a(x,$),ne=y?null:l.get(H);ne?(ne.v&&Xa(ne.v,x),ne.i&&Xa(ne.i,$),de&&j.unskip_effect(ne.e)):(ne=hu(l,y?i:mi??(mi=zn()),x,H,$,s,t,r),y||(ne.e.f|=kn),l.set(H,ne)),S.add(H)}if(W===0&&o&&!p&&(y?p=Nr(()=>o(i)):(p=Nr(()=>o(mi??(mi=zn()))),p.f|=kn)),W>S.size&&Yd(),!y)if(z.set(j,S),de){for(const[Y,A]of l)S.has(Y)||j.skip_effect(A.e);j.oncommit(I),j.ondiscard(k)}else I(j);n(b)}),D={effect:C,items:l,pending:z,outrogroups:null,fallback:p};y=!1}function ls(e){for(;e!==null&&(e.f&vn)===0;)e=e.next;return e}function mu(e,t,r,a,s){var ne,Y,A,ie,ve,ke,pe,Ee,ge;var o=(a&ic)!==0,i=t.length,l=e.items,c=ls(e.effect.first),f,p=null,b,w=[],z=[],y,I,k,C;if(o)for(C=0;C<i;C+=1)y=t[C],I=s(y,C),k=l.get(I).e,(k.f&kn)===0&&((Y=(ne=k.nodes)==null?void 0:ne.a)==null||Y.measure(),(b??(b=new Set)).add(k));for(C=0;C<i;C+=1){if(y=t[C],I=s(y,C),k=l.get(I).e,e.outrogroups!==null)for(const xe of e.outrogroups)xe.pending.delete(k),xe.done.delete(k);if((k.f&kn)!==0)if(k.f^=kn,k===c)ms(k,null,r);else{var D=p?p.next:c;k===e.effect.last&&(e.effect.last=k.prev),k.prev&&(k.prev.next=k.next),k.next&&(k.next.prev=k.prev),Yn(e,p,k),Yn(e,k,D),ms(k,D,r),p=k,w=[],z=[],c=ls(p.next);continue}if((k.f&zr)!==0&&(Go(k),o&&((ie=(A=k.nodes)==null?void 0:A.a)==null||ie.unfix(),(b??(b=new Set)).delete(k))),k!==c){if(f!==void 0&&f.has(k)){if(w.length<z.length){var W=z[0],S;p=W.prev;var j=w[0],de=w[w.length-1];for(S=0;S<w.length;S+=1)ms(w[S],W,r);for(S=0;S<z.length;S+=1)f.delete(z[S]);Yn(e,j.prev,de.next),Yn(e,p,j),Yn(e,de,W),c=W,p=de,C-=1,w=[],z=[]}else f.delete(k),ms(k,c,r),Yn(e,k.prev,k.next),Yn(e,k,p===null?e.effect.first:p.next),Yn(e,p,k),p=k;continue}for(w=[],z=[];c!==null&&c!==k;)(f??(f=new Set)).add(c),z.push(c),c=ls(c.next);if(c===null)continue}(k.f&kn)===0&&w.push(k),p=k,c=ls(k.next)}if(e.outrogroups!==null){for(const xe of e.outrogroups)xe.pending.size===0&&(Mo(e,Gs(xe.done)),(ve=e.outrogroups)==null||ve.delete(xe));e.outrogroups.size===0&&(e.outrogroups=null)}if(c!==null||f!==void 0){var $=[];if(f!==void 0)for(k of f)(k.f&zr)===0&&$.push(k);for(;c!==null;)(c.f&zr)===0&&c!==e.fallback&&$.push(c),c=ls(c.next);var x=$.length;if(x>0){var H=(a&Wi)!==0&&i===0?r:null;if(o){for(C=0;C<x;C+=1)(pe=(ke=$[C].nodes)==null?void 0:ke.a)==null||pe.measure();for(C=0;C<x;C+=1)(ge=(Ee=$[C].nodes)==null?void 0:Ee.a)==null||ge.fix()}pu(e,$,H)}}o&&En(()=>{var xe,G;if(b!==void 0)for(k of b)(G=(xe=k.nodes)==null?void 0:xe.a)==null||G.apply()})}function hu(e,t,r,a,s,o,i,l){var c=(i&sc)!==0?(i&lc)===0?Vc(r,!1,!1):da(r):null,f=(i&oc)!==0?da(s):null;return{v:c,i:f,e:Nr(()=>(o(t,c??r,f??s,l),()=>{e.delete(a)}))}}function ms(e,t,r){if(e.nodes)for(var a=e.nodes.start,s=e.nodes.end,o=t&&(t.f&kn)===0?t.nodes.start:r;a!==null;){var i=zs(a);if(o.before(a),a===s)return;a=i}}function Yn(e,t,r){t===null?e.effect.first=r:t.next=r,r===null?e.effect.last=t:r.prev=t}function aa(e,t,r=!1,a=!1,s=!1){var o=e,i="";N(()=>{var l=Je;if(i!==(i=t()??"")&&(l.nodes!==null&&(wl(l.nodes.start,l.nodes.end),l.nodes=null),i!=="")){var c=r?Xi:a?mc:void 0,f=jo(r?"svg":a?"math":"template",c);f.innerHTML=i;var p=r||a?f:f.content;if(Ia(Vn(p),p.lastChild),r||a)for(;Vn(p);)o.before(Vn(p));else o.before(p)}})}function He(e,t,r,a,s){var l;var o=(l=t.$$slots)==null?void 0:l[r],i=!1;o===!0&&(o=t.children,i=!0),o===void 0||o(e,i?()=>a:a)}function Eo(e,t,...r){var a=new Ys(e);ns(()=>{const s=t()??null;a.ensure(s,s&&(o=>s(o,...r)))},Fn)}function gu(e,t,r){var a=new Ys(e);ns(()=>{var s=t()??null;a.ensure(s,s&&(o=>r(o,s)))},Fn)}function xu(e,t,r,a,s,o){var i=null,l=e,c=new Ys(l,!1);ns(()=>{const f=t()||null;var p=Xi;if(f===null){c.ensure(null,null);return}return c.ensure(f,b=>{if(f){if(i=jo(f,p),Ia(i,i),a){var w=i.appendChild(zn());a(i,w)}Je.nodes.end=i,b.before(i)}}),()=>{}},Fn),Ks(()=>{})}function bu(e,t){var r=void 0,a;bl(()=>{r!==(r=t())&&(a&&(xr(a),a=null),r&&(a=Nr(()=>{qo(()=>r(e))})))})}function Ll(e){var t,r,a="";if(typeof e=="string"||typeof e=="number")a+=e;else if(typeof e=="object")if(Array.isArray(e)){var s=e.length;for(t=0;t<s;t++)e[t]&&(r=Ll(e[t]))&&(a&&(a+=" "),a+=r)}else for(r in e)e[r]&&(a&&(a+=" "),a+=r);return a}function Ol(){for(var e,t,r=0,a="",s=arguments.length;r<s;r++)(e=arguments[r])&&(t=Ll(e))&&(a&&(a+=" "),a+=t);return a}function Pt(e){return typeof e=="object"?Ol(e):e??""}const hi=[...` 	
\r\f \v\uFEFF`];function _u(e,t,r){var a=e==null?"":""+e;if(t&&(a=a?a+" "+t:t),r){for(var s of Object.keys(r))if(r[s])a=a?a+" "+s:s;else if(a.length)for(var o=s.length,i=0;(i=a.indexOf(s,i))>=0;){var l=i+o;(i===0||hi.includes(a[i-1]))&&(l===a.length||hi.includes(a[l]))?a=(i===0?"":a.substring(0,i))+a.substring(l+1):i=l}}return a===""?null:a}function gi(e,t=!1){var r=t?" !important;":";",a="";for(var s of Object.keys(e)){var o=e[s];o!=null&&o!==""&&(a+=" "+s+": "+o+r)}return a}function ro(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function wu(e,t){if(t){var r="",a,s;if(Array.isArray(t)?(a=t[0],s=t[1]):a=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,i=0,l=!1,c=[];a&&c.push(...Object.keys(a).map(ro)),s&&c.push(...Object.keys(s).map(ro));var f=0,p=-1;const I=e.length;for(var b=0;b<I;b++){var w=e[b];if(l?w==="/"&&e[b-1]==="*"&&(l=!1):o?o===w&&(o=!1):w==="/"&&e[b+1]==="*"?l=!0:w==='"'||w==="'"?o=w:w==="("?i++:w===")"&&i--,!l&&o===!1&&i===0){if(w===":"&&p===-1)p=b;else if(w===";"||b===I-1){if(p!==-1){var z=ro(e.substring(f,p).trim());if(!c.includes(z)){w!==";"&&b++;var y=e.substring(f,b).trim();r+=" "+y+";"}}f=b+1,p=-1}}}}return a&&(r+=gi(a)),s&&(r+=gi(s,!0)),r=r.trim(),r===""?null:r}return e==null?null:String(e)}function $e(e,t,r,a,s,o){var i=e.__className;if(i!==r||i===void 0){var l=_u(r,a,o);l==null?e.removeAttribute("class"):t?e.className=l:e.setAttribute("class",l),e.__className=r}else if(o&&s!==o)for(var c in o){var f=!!o[c];(s==null||f!==!!s[c])&&e.classList.toggle(c,f)}return o}function no(e,t={},r,a){for(var s in r){var o=r[s];t[s]!==o&&(r[s]==null?e.style.removeProperty(s):e.style.setProperty(s,o,a))}}function zo(e,t,r,a){var s=e.__style;if(s!==t){var o=wu(t,a);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else a&&(Array.isArray(a)?(no(e,r==null?void 0:r[0],a[0]),no(e,r==null?void 0:r[1],a[1],"important")):no(e,r,a));return a}function Ao(e,t,r=!1){if(e.multiple){if(t==null)return;if(!No(t))return gc();for(var a of e.options)a.selected=t.includes(xi(a));return}for(a of e.options){var s=xi(a);if(Fc(s,t)){a.selected=!0;return}}(!r||t!==void 0)&&(e.selectedIndex=-1)}function yu(e){var t=new MutationObserver(()=>{Ao(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Ks(()=>{t.disconnect()})}function xi(e){return"__value"in e?e.__value:e.value}const ds=Symbol("class"),cs=Symbol("style"),Rl=Symbol("is custom element"),Dl=Symbol("is html"),ku=Ui?"option":"OPTION",Cu=Ui?"select":"SELECT";function Su(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function qn(e,t,r,a){var s=jl(e);s[t]!==(s[t]=r)&&(t==="loading"&&(e[Wd]=r),r==null?e.removeAttribute(t):typeof r!="string"&&Vl(e).includes(t)?e[t]=r:e.setAttribute(t,r))}function Mu(e,t,r,a,s=!1,o=!1){var i=jl(e),l=i[Rl],c=!i[Dl],f=t||{},p=e.nodeName===ku;for(var b in t)b in r||(r[b]=null);r.class?r.class=Pt(r.class):r[ds]&&(r.class=null),r[cs]&&(r.style??(r.style=null));var w=Vl(e);for(const S in r){let j=r[S];if(p&&S==="value"&&j==null){e.value=e.__value="",f[S]=j;continue}if(S==="class"){var z=e.namespaceURI==="http://www.w3.org/1999/xhtml";$e(e,z,j,a,t==null?void 0:t[ds],r[ds]),f[S]=j,f[ds]=r[ds];continue}if(S==="style"){zo(e,j,t==null?void 0:t[cs],r[cs]),f[S]=j,f[cs]=r[cs];continue}var y=f[S];if(!(j===y&&!(j===void 0&&e.hasAttribute(S)))){f[S]=j;var I=S[0]+S[1];if(I!=="$$")if(I==="on"){const de={},$="$$"+S;let x=S.slice(2);var k=nu(x);if(tu(x)&&(x=x.slice(0,-7),de.capture=!0),!k&&y){if(j!=null)continue;e.removeEventListener(x,f[$],de),f[$]=null}if(k)se(x,e,j),Bn([x]);else if(j!=null){let H=function(ne){f[S].call(this,ne)};var W=H;f[$]=Nl(x,e,H,de)}}else if(S==="style")qn(e,S,j);else if(S==="autofocus")hl(e,!!j);else if(!l&&(S==="__value"||S==="value"&&j!=null))e.value=e.__value=j;else if(S==="selected"&&p)Su(e,j);else{var C=S;c||(C=su(C));var D=C==="defaultValue"||C==="defaultChecked";if(j==null&&!l&&!D)if(i[S]=null,C==="value"||C==="checked"){let de=e;const $=t===void 0;if(C==="value"){let x=de.defaultValue;de.removeAttribute(C),de.defaultValue=x,de.value=de.__value=$?x:null}else{let x=de.defaultChecked;de.removeAttribute(C),de.defaultChecked=x,de.checked=$?x:!1}}else e.removeAttribute(S);else D||w.includes(C)&&(l||typeof j!="string")?(e[C]=j,C in i&&(i[C]=ir)):typeof j!="function"&&qn(e,C,j)}}}return f}function js(e,t,r=[],a=[],s=[],o,i=!1,l=!1){il(s,r,a,c=>{var f=void 0,p={},b=e.nodeName===Cu,w=!1;if(bl(()=>{var y=t(...c.map(n)),I=Mu(e,f,y,o,i,l);w&&b&&"value"in y&&Ao(e,y.value);for(let C of Object.getOwnPropertySymbols(p))y[C]||xr(p[C]);for(let C of Object.getOwnPropertySymbols(y)){var k=y[C];C.description===hc&&(!f||k!==f[C])&&(p[C]&&xr(p[C]),p[C]=Nr(()=>bu(e,()=>k))),I[C]=k}f=I}),b){var z=e;qo(()=>{Ao(z,f.value,!0),yu(z)})}w=!0})}function jl(e){return e.__attributes??(e.__attributes={[Rl]:e.nodeName.includes("-"),[Dl]:e.namespaceURI===Yi})}var bi=new Map;function Vl(e){var t=e.getAttribute("is")||e.nodeName,r=bi.get(t);if(r)return r;bi.set(t,r=[]);for(var a,s=e,o=Element.prototype;o!==s;){a=qi(s);for(var i in a)a[i].set&&r.push(i);s=$o(s)}return r}function Ra(e,t,r=t){var a=new WeakSet;Uc(e,"input",async s=>{var o=s?e.defaultValue:e.value;if(o=ao(e)?so(o):o,r(o),Ge!==null&&a.add(Ge),await eu(),o!==(o=t())){var i=e.selectionStart,l=e.selectionEnd,c=e.value.length;if(e.value=o??"",l!==null){var f=e.value.length;i===l&&l===c&&f>c?(e.selectionStart=f,e.selectionEnd=f):(e.selectionStart=i,e.selectionEnd=Math.min(l,f))}}}),Ta(t)==null&&e.value&&(r(ao(e)?so(e.value):e.value),Ge!==null&&a.add(Ge)),Fo(()=>{var s=t();if(e===document.activeElement){var o=vo??Ge;if(a.has(o))return}ao(e)&&s===so(e.value)||e.type==="date"&&!s&&!e.value||s!==e.value&&(e.value=s??"")})}function ao(e){var t=e.type;return t==="number"||t==="range"}function so(e){return e===""?null:+e}function _i(e,t){return e===t||(e==null?void 0:e[Mn])===t}function Qa(e={},t,r,a){return qo(()=>{var s,o;return Fo(()=>{s=o,o=[],Ta(()=>{e!==r(...o)&&(t(e,...o),s&&_i(r(...s),e)&&t(null,...s))})}),()=>{En(()=>{o&&_i(r(...o),e)&&t(null,...o)})}}),e}function Eu(e=!1){const t=lr,r=t.l.u;if(!r)return;let a=()=>ga(t.s);if(e){let s=0,o={};const i=Es(()=>{let l=!1;const c=t.s;for(const f in c)c[f]!==o[f]&&(o[f]=c[f],l=!0);return l&&s++,s});a=()=>n(i)}r.b.length&&Kc(()=>{wi(t,a),co(r.b)}),na(()=>{const s=Ta(()=>r.m.map(Hd));return()=>{for(const o of s)typeof o=="function"&&o()}}),r.a.length&&na(()=>{wi(t,a),co(r.a)})}function wi(e,t){if(e.l.s)for(const r of e.l.s)n(r);t()}let Ns=!1;function zu(e){var t=Ns;try{return Ns=!1,[e(),Ns]}finally{Ns=t}}const Au={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Tu(e,t,r){return new Proxy({props:e,exclude:t},Au)}const Iu={get(e,t){if(!e.exclude.includes(t))return n(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,r){if(!(t in e.special)){var a=Je;try{Qr(e.parent_effect),e.special[t]=ot({get[t](){return e.props[t]}},t,Ki)}finally{Qr(a)}}return e.special[t](r),gs(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),gs(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function De(e,t){return new Proxy({props:e,exclude:t,special:{},version:da(0),parent_effect:Je},Iu)}const Pu={get(e,t){let r=e.props.length;for(;r--;){let a=e.props[r];if(is(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a)return a[t]}},set(e,t,r){let a=e.props.length;for(;a--;){let s=e.props[a];is(s)&&(s=s());const o=sa(s,t);if(o&&o.set)return o.set(r),!0}return!1},getOwnPropertyDescriptor(e,t){let r=e.props.length;for(;r--;){let a=e.props[r];if(is(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a){const s=sa(a,t);return s&&!s.configurable&&(s.configurable=!0),s}}},has(e,t){if(t===Mn||t===Hi)return!1;for(let r of e.props)if(is(r)&&(r=r()),r!=null&&t in r)return!0;return!1},ownKeys(e){const t=[];for(let r of e.props)if(is(r)&&(r=r()),!!r){for(const a in r)t.includes(a)||t.push(a);for(const a of Object.getOwnPropertySymbols(r))t.includes(a)||t.push(a)}return t}};function Ue(...e){return new Proxy({props:e},Pu)}function ot(e,t,r,a){var W;var s=!Ss||(r&cc)!==0,o=(r&uc)!==0,i=(r&fc)!==0,l=a,c=!0,f=()=>(c&&(c=!1,l=i?Ta(a):a),l),p;if(o){var b=Mn in e||Hi in e;p=((W=sa(e,t))==null?void 0:W.set)??(b&&t in e?S=>e[t]=S:void 0)}var w,z=!1;o?[w,z]=zu(()=>e[t]):w=e[t],w===void 0&&a!==void 0&&(w=f(),p&&(s&&ec(),p(w)));var y;if(s?y=()=>{var S=e[t];return S===void 0?f():(c=!0,S)}:y=()=>{var S=e[t];return S!==void 0&&(l=void 0),S===void 0?l:S},s&&(r&Ki)===0)return y;if(p){var I=e.$$legacy;return(function(S,j){return arguments.length>0?((!s||!j||I||z)&&p(j?y():S),S):y()})}var k=!1,C=((r&dc)!==0?Es:Ro)(()=>(k=!1,y()));o&&n(C);var D=Je;return(function(S,j){if(arguments.length>0){const de=j?n(C):s&&o?jt(S):S;return u(C,de),k=!0,l!==void 0&&(l=de),S}return ca&&k||(D.f&Sn)!==0?C.v:n(C)})}const Nu="5";var Vi;typeof window<"u"&&((Vi=window.__svelte??(window.__svelte={})).v??(Vi.v=new Set)).add(Nu);const An="";async function $u(){const e=await fetch(`${An}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function Oa(e,t=null,r=null){const a={provider:e};t&&(a.model=t),r&&(a.api_key=r);const s=await fetch(`${An}/api/configure`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!s.ok)throw new Error("설정 실패");return s.json()}async function Lu(e){const t=await fetch(`${An}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function Ou(e,{onProgress:t,onDone:r,onError:a}){const s=new AbortController;return fetch(`${An}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:s.signal}).then(async o=>{if(!o.ok){a==null||a("다운로드 실패");return}const i=o.body.getReader(),l=new TextDecoder;let c="";for(;;){const{done:f,value:p}=await i.read();if(f)break;c+=l.decode(p,{stream:!0});const b=c.split(`
`);c=b.pop()||"";for(const w of b)if(w.startsWith("data:"))try{const z=JSON.parse(w.slice(5).trim());z.total&&z.completed!==void 0?t==null||t({total:z.total,completed:z.completed,status:z.status}):z.status&&(t==null||t({status:z.status}))}catch{}}r==null||r()}).catch(o=>{o.name!=="AbortError"&&(a==null||a(o.message))}),{abort:()=>s.abort()}}async function Ru(){const e=await fetch(`${An}/api/codex/logout`,{method:"POST"});if(!e.ok)throw new Error("Codex 로그아웃 실패");return e.json()}async function Du(e,t=null,r=null){let a=`${An}/api/export/excel/${encodeURIComponent(e)}`;const s=new URLSearchParams;r?s.set("template_id",r):t&&t.length>0&&s.set("modules",t.join(","));const o=s.toString();o&&(a+=`?${o}`);const i=await fetch(a);if(!i.ok){const w=await i.json().catch(()=>({}));throw new Error(w.detail||"Excel 다운로드 실패")}const l=await i.blob(),f=(i.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),p=f?decodeURIComponent(f[1]):`${e}.xlsx`,b=document.createElement("a");return b.href=URL.createObjectURL(l),b.download=p,b.click(),URL.revokeObjectURL(b.href),p}async function ql(e){const t=await fetch(`${An}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}async function ju(e,t){const r=await fetch(`${An}/api/company/${e}/show/${encodeURIComponent(t)}/all`);if(!r.ok)throw new Error("company topic 일괄 조회 실패");return r.json()}async function Vu(e){const t=await fetch(`${An}/api/company/${e}/sections`);if(!t.ok)throw new Error("sections 조회 실패");return t.json()}function qu(e,t,r={},{onMeta:a,onSnapshot:s,onContext:o,onSystemPrompt:i,onToolCall:l,onToolResult:c,onChunk:f,onDone:p,onError:b},w=null){const z={question:t,stream:!0,...r};e&&(z.company=e),w&&w.length>0&&(z.history=w);const y=new AbortController;return fetch(`${An}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(z),signal:y.signal}).then(async I=>{if(!I.ok){const j=await I.json().catch(()=>({}));b==null||b(j.detail||"스트리밍 실패");return}const k=I.body.getReader(),C=new TextDecoder;let D="",W=!1,S=null;for(;;){const{done:j,value:de}=await k.read();if(j)break;D+=C.decode(de,{stream:!0});const $=D.split(`
`);D=$.pop()||"";for(const x of $)if(x.startsWith("event:"))S=x.slice(6).trim();else if(x.startsWith("data:")&&S){const H=x.slice(5).trim();try{const ne=JSON.parse(H);S==="meta"?a==null||a(ne):S==="snapshot"?s==null||s(ne):S==="context"?o==null||o(ne):S==="system_prompt"?i==null||i(ne):S==="tool_call"?l==null||l(ne):S==="tool_result"?c==null||c(ne):S==="chunk"?f==null||f(ne.text):S==="error"?b==null||b(ne.error,ne.action,ne.detail):S==="done"&&(W||(W=!0,p==null||p()))}catch{}S=null}}W||(W=!0,p==null||p())}).catch(I=>{I.name!=="AbortError"&&(b==null||b(I.message))}),{abort:()=>y.abort()}}const Fu=(e,t)=>{const r=new Array(e.length+t.length);for(let a=0;a<e.length;a++)r[a]=e[a];for(let a=0;a<t.length;a++)r[e.length+a]=t[a];return r},Bu=(e,t)=>({classGroupId:e,validator:t}),Fl=(e=new Map,t=null,r)=>({nextPart:e,validators:t,classGroupId:r}),Vs="-",yi=[],Gu="arbitrary..",Hu=e=>{const t=Wu(e),{conflictingClassGroups:r,conflictingClassGroupModifiers:a}=e;return{getClassGroupId:i=>{if(i.startsWith("[")&&i.endsWith("]"))return Uu(i);const l=i.split(Vs),c=l[0]===""&&l.length>1?1:0;return Bl(l,c,t)},getConflictingClassGroupIds:(i,l)=>{if(l){const c=a[i],f=r[i];return c?f?Fu(f,c):c:f||yi}return r[i]||yi}}},Bl=(e,t,r)=>{if(e.length-t===0)return r.classGroupId;const s=e[t],o=r.nextPart.get(s);if(o){const f=Bl(e,t+1,o);if(f)return f}const i=r.validators;if(i===null)return;const l=t===0?e.join(Vs):e.slice(t).join(Vs),c=i.length;for(let f=0;f<c;f++){const p=i[f];if(p.validator(l))return p.classGroupId}},Uu=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),r=t.indexOf(":"),a=t.slice(0,r);return a?Gu+a:void 0})(),Wu=e=>{const{theme:t,classGroups:r}=e;return Ku(r,t)},Ku=(e,t)=>{const r=Fl();for(const a in e){const s=e[a];Uo(s,r,a,t)}return r},Uo=(e,t,r,a)=>{const s=e.length;for(let o=0;o<s;o++){const i=e[o];Yu(i,t,r,a)}},Yu=(e,t,r,a)=>{if(typeof e=="string"){Xu(e,t,r);return}if(typeof e=="function"){Ju(e,t,r,a);return}Qu(e,t,r,a)},Xu=(e,t,r)=>{const a=e===""?t:Gl(t,e);a.classGroupId=r},Ju=(e,t,r,a)=>{if(Zu(e)){Uo(e(a),t,r,a);return}t.validators===null&&(t.validators=[]),t.validators.push(Bu(r,e))},Qu=(e,t,r,a)=>{const s=Object.entries(e),o=s.length;for(let i=0;i<o;i++){const[l,c]=s[i];Uo(c,Gl(t,l),r,a)}},Gl=(e,t)=>{let r=e;const a=t.split(Vs),s=a.length;for(let o=0;o<s;o++){const i=a[o];let l=r.nextPart.get(i);l||(l=Fl(),r.nextPart.set(i,l)),r=l}return r},Zu=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,ef=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,r=Object.create(null),a=Object.create(null);const s=(o,i)=>{r[o]=i,t++,t>e&&(t=0,a=r,r=Object.create(null))};return{get(o){let i=r[o];if(i!==void 0)return i;if((i=a[o])!==void 0)return s(o,i),i},set(o,i){o in r?r[o]=i:s(o,i)}}},To="!",ki=":",tf=[],Ci=(e,t,r,a,s)=>({modifiers:e,hasImportantModifier:t,baseClassName:r,maybePostfixModifierPosition:a,isExternal:s}),rf=e=>{const{prefix:t,experimentalParseClassName:r}=e;let a=s=>{const o=[];let i=0,l=0,c=0,f;const p=s.length;for(let I=0;I<p;I++){const k=s[I];if(i===0&&l===0){if(k===ki){o.push(s.slice(c,I)),c=I+1;continue}if(k==="/"){f=I;continue}}k==="["?i++:k==="]"?i--:k==="("?l++:k===")"&&l--}const b=o.length===0?s:s.slice(c);let w=b,z=!1;b.endsWith(To)?(w=b.slice(0,-1),z=!0):b.startsWith(To)&&(w=b.slice(1),z=!0);const y=f&&f>c?f-c:void 0;return Ci(o,z,w,y)};if(t){const s=t+ki,o=a;a=i=>i.startsWith(s)?o(i.slice(s.length)):Ci(tf,!1,i,void 0,!0)}if(r){const s=a;a=o=>r({className:o,parseClassName:s})}return a},nf=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((r,a)=>{t.set(r,1e6+a)}),r=>{const a=[];let s=[];for(let o=0;o<r.length;o++){const i=r[o],l=i[0]==="[",c=t.has(i);l||c?(s.length>0&&(s.sort(),a.push(...s),s=[]),a.push(i)):s.push(i)}return s.length>0&&(s.sort(),a.push(...s)),a}},af=e=>({cache:ef(e.cacheSize),parseClassName:rf(e),sortModifiers:nf(e),...Hu(e)}),sf=/\s+/,of=(e,t)=>{const{parseClassName:r,getClassGroupId:a,getConflictingClassGroupIds:s,sortModifiers:o}=t,i=[],l=e.trim().split(sf);let c="";for(let f=l.length-1;f>=0;f-=1){const p=l[f],{isExternal:b,modifiers:w,hasImportantModifier:z,baseClassName:y,maybePostfixModifierPosition:I}=r(p);if(b){c=p+(c.length>0?" "+c:c);continue}let k=!!I,C=a(k?y.substring(0,I):y);if(!C){if(!k){c=p+(c.length>0?" "+c:c);continue}if(C=a(y),!C){c=p+(c.length>0?" "+c:c);continue}k=!1}const D=w.length===0?"":w.length===1?w[0]:o(w).join(":"),W=z?D+To:D,S=W+C;if(i.indexOf(S)>-1)continue;i.push(S);const j=s(C,k);for(let de=0;de<j.length;++de){const $=j[de];i.push(W+$)}c=p+(c.length>0?" "+c:c)}return c},lf=(...e)=>{let t=0,r,a,s="";for(;t<e.length;)(r=e[t++])&&(a=Hl(r))&&(s&&(s+=" "),s+=a);return s},Hl=e=>{if(typeof e=="string")return e;let t,r="";for(let a=0;a<e.length;a++)e[a]&&(t=Hl(e[a]))&&(r&&(r+=" "),r+=t);return r},df=(e,...t)=>{let r,a,s,o;const i=c=>{const f=t.reduce((p,b)=>b(p),e());return r=af(f),a=r.cache.get,s=r.cache.set,o=l,l(c)},l=c=>{const f=a(c);if(f)return f;const p=of(c,r);return s(c,p),p};return o=i,(...c)=>o(lf(...c))},cf=[],nr=e=>{const t=r=>r[e]||cf;return t.isThemeGetter=!0,t},Ul=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Wl=/^\((?:(\w[\w-]*):)?(.+)\)$/i,uf=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,ff=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,vf=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,pf=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,mf=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,hf=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,Xn=e=>uf.test(e),Re=e=>!!e&&!Number.isNaN(Number(e)),Jn=e=>!!e&&Number.isInteger(Number(e)),oo=e=>e.endsWith("%")&&Re(e.slice(0,-1)),On=e=>ff.test(e),Kl=()=>!0,gf=e=>vf.test(e)&&!pf.test(e),Wo=()=>!1,xf=e=>mf.test(e),bf=e=>hf.test(e),_f=e=>!ae(e)&&!oe(e),wf=e=>fa(e,Jl,Wo),ae=e=>Ul.test(e),ha=e=>fa(e,Ql,gf),Si=e=>fa(e,Af,Re),yf=e=>fa(e,ed,Kl),kf=e=>fa(e,Zl,Wo),Mi=e=>fa(e,Yl,Wo),Cf=e=>fa(e,Xl,bf),$s=e=>fa(e,td,xf),oe=e=>Wl.test(e),us=e=>Na(e,Ql),Sf=e=>Na(e,Zl),Ei=e=>Na(e,Yl),Mf=e=>Na(e,Jl),Ef=e=>Na(e,Xl),Ls=e=>Na(e,td,!0),zf=e=>Na(e,ed,!0),fa=(e,t,r)=>{const a=Ul.exec(e);return a?a[1]?t(a[1]):r(a[2]):!1},Na=(e,t,r=!1)=>{const a=Wl.exec(e);return a?a[1]?t(a[1]):r:!1},Yl=e=>e==="position"||e==="percentage",Xl=e=>e==="image"||e==="url",Jl=e=>e==="length"||e==="size"||e==="bg-size",Ql=e=>e==="length",Af=e=>e==="number",Zl=e=>e==="family-name",ed=e=>e==="number"||e==="weight",td=e=>e==="shadow",Tf=()=>{const e=nr("color"),t=nr("font"),r=nr("text"),a=nr("font-weight"),s=nr("tracking"),o=nr("leading"),i=nr("breakpoint"),l=nr("container"),c=nr("spacing"),f=nr("radius"),p=nr("shadow"),b=nr("inset-shadow"),w=nr("text-shadow"),z=nr("drop-shadow"),y=nr("blur"),I=nr("perspective"),k=nr("aspect"),C=nr("ease"),D=nr("animate"),W=()=>["auto","avoid","all","avoid-page","page","left","right","column"],S=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],j=()=>[...S(),oe,ae],de=()=>["auto","hidden","clip","visible","scroll"],$=()=>["auto","contain","none"],x=()=>[oe,ae,c],H=()=>[Xn,"full","auto",...x()],ne=()=>[Jn,"none","subgrid",oe,ae],Y=()=>["auto",{span:["full",Jn,oe,ae]},Jn,oe,ae],A=()=>[Jn,"auto",oe,ae],ie=()=>["auto","min","max","fr",oe,ae],ve=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],ke=()=>["start","end","center","stretch","center-safe","end-safe"],pe=()=>["auto",...x()],Ee=()=>[Xn,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...x()],ge=()=>[Xn,"screen","full","dvw","lvw","svw","min","max","fit",...x()],xe=()=>[Xn,"screen","full","lh","dvh","lvh","svh","min","max","fit",...x()],G=()=>[e,oe,ae],ut=()=>[...S(),Ei,Mi,{position:[oe,ae]}],me=()=>["no-repeat",{repeat:["","x","y","space","round"]}],T=()=>["auto","cover","contain",Mf,wf,{size:[oe,ae]}],re=()=>[oo,us,ha],K=()=>["","none","full",f,oe,ae],U=()=>["",Re,us,ha],F=()=>["solid","dashed","dotted","double"],Qe=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],le=()=>[Re,oo,Ei,Mi],Et=()=>["","none",y,oe,ae],_t=()=>["none",Re,oe,ae],Gt=()=>["none",Re,oe,ae],wt=()=>[Re,oe,ae],sr=()=>[Xn,"full",...x()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[On],breakpoint:[On],color:[Kl],container:[On],"drop-shadow":[On],ease:["in","out","in-out"],font:[_f],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[On],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[On],shadow:[On],spacing:["px",Re],text:[On],"text-shadow":[On],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",Xn,ae,oe,k]}],container:["container"],columns:[{columns:[Re,ae,oe,l]}],"break-after":[{"break-after":W()}],"break-before":[{"break-before":W()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:j()}],overflow:[{overflow:de()}],"overflow-x":[{"overflow-x":de()}],"overflow-y":[{"overflow-y":de()}],overscroll:[{overscroll:$()}],"overscroll-x":[{"overscroll-x":$()}],"overscroll-y":[{"overscroll-y":$()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:H()}],"inset-x":[{"inset-x":H()}],"inset-y":[{"inset-y":H()}],start:[{"inset-s":H(),start:H()}],end:[{"inset-e":H(),end:H()}],"inset-bs":[{"inset-bs":H()}],"inset-be":[{"inset-be":H()}],top:[{top:H()}],right:[{right:H()}],bottom:[{bottom:H()}],left:[{left:H()}],visibility:["visible","invisible","collapse"],z:[{z:[Jn,"auto",oe,ae]}],basis:[{basis:[Xn,"full","auto",l,...x()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[Re,Xn,"auto","initial","none",ae]}],grow:[{grow:["",Re,oe,ae]}],shrink:[{shrink:["",Re,oe,ae]}],order:[{order:[Jn,"first","last","none",oe,ae]}],"grid-cols":[{"grid-cols":ne()}],"col-start-end":[{col:Y()}],"col-start":[{"col-start":A()}],"col-end":[{"col-end":A()}],"grid-rows":[{"grid-rows":ne()}],"row-start-end":[{row:Y()}],"row-start":[{"row-start":A()}],"row-end":[{"row-end":A()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":ie()}],"auto-rows":[{"auto-rows":ie()}],gap:[{gap:x()}],"gap-x":[{"gap-x":x()}],"gap-y":[{"gap-y":x()}],"justify-content":[{justify:[...ve(),"normal"]}],"justify-items":[{"justify-items":[...ke(),"normal"]}],"justify-self":[{"justify-self":["auto",...ke()]}],"align-content":[{content:["normal",...ve()]}],"align-items":[{items:[...ke(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...ke(),{baseline:["","last"]}]}],"place-content":[{"place-content":ve()}],"place-items":[{"place-items":[...ke(),"baseline"]}],"place-self":[{"place-self":["auto",...ke()]}],p:[{p:x()}],px:[{px:x()}],py:[{py:x()}],ps:[{ps:x()}],pe:[{pe:x()}],pbs:[{pbs:x()}],pbe:[{pbe:x()}],pt:[{pt:x()}],pr:[{pr:x()}],pb:[{pb:x()}],pl:[{pl:x()}],m:[{m:pe()}],mx:[{mx:pe()}],my:[{my:pe()}],ms:[{ms:pe()}],me:[{me:pe()}],mbs:[{mbs:pe()}],mbe:[{mbe:pe()}],mt:[{mt:pe()}],mr:[{mr:pe()}],mb:[{mb:pe()}],ml:[{ml:pe()}],"space-x":[{"space-x":x()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":x()}],"space-y-reverse":["space-y-reverse"],size:[{size:Ee()}],"inline-size":[{inline:["auto",...ge()]}],"min-inline-size":[{"min-inline":["auto",...ge()]}],"max-inline-size":[{"max-inline":["none",...ge()]}],"block-size":[{block:["auto",...xe()]}],"min-block-size":[{"min-block":["auto",...xe()]}],"max-block-size":[{"max-block":["none",...xe()]}],w:[{w:[l,"screen",...Ee()]}],"min-w":[{"min-w":[l,"screen","none",...Ee()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[i]},...Ee()]}],h:[{h:["screen","lh",...Ee()]}],"min-h":[{"min-h":["screen","lh","none",...Ee()]}],"max-h":[{"max-h":["screen","lh",...Ee()]}],"font-size":[{text:["base",r,us,ha]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[a,zf,yf]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",oo,ae]}],"font-family":[{font:[Sf,kf,t]}],"font-features":[{"font-features":[ae]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[s,oe,ae]}],"line-clamp":[{"line-clamp":[Re,"none",oe,Si]}],leading:[{leading:[o,...x()]}],"list-image":[{"list-image":["none",oe,ae]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",oe,ae]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:G()}],"text-color":[{text:G()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...F(),"wavy"]}],"text-decoration-thickness":[{decoration:[Re,"from-font","auto",oe,ha]}],"text-decoration-color":[{decoration:G()}],"underline-offset":[{"underline-offset":[Re,"auto",oe,ae]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:x()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",oe,ae]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",oe,ae]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:ut()}],"bg-repeat":[{bg:me()}],"bg-size":[{bg:T()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},Jn,oe,ae],radial:["",oe,ae],conic:[Jn,oe,ae]},Ef,Cf]}],"bg-color":[{bg:G()}],"gradient-from-pos":[{from:re()}],"gradient-via-pos":[{via:re()}],"gradient-to-pos":[{to:re()}],"gradient-from":[{from:G()}],"gradient-via":[{via:G()}],"gradient-to":[{to:G()}],rounded:[{rounded:K()}],"rounded-s":[{"rounded-s":K()}],"rounded-e":[{"rounded-e":K()}],"rounded-t":[{"rounded-t":K()}],"rounded-r":[{"rounded-r":K()}],"rounded-b":[{"rounded-b":K()}],"rounded-l":[{"rounded-l":K()}],"rounded-ss":[{"rounded-ss":K()}],"rounded-se":[{"rounded-se":K()}],"rounded-ee":[{"rounded-ee":K()}],"rounded-es":[{"rounded-es":K()}],"rounded-tl":[{"rounded-tl":K()}],"rounded-tr":[{"rounded-tr":K()}],"rounded-br":[{"rounded-br":K()}],"rounded-bl":[{"rounded-bl":K()}],"border-w":[{border:U()}],"border-w-x":[{"border-x":U()}],"border-w-y":[{"border-y":U()}],"border-w-s":[{"border-s":U()}],"border-w-e":[{"border-e":U()}],"border-w-bs":[{"border-bs":U()}],"border-w-be":[{"border-be":U()}],"border-w-t":[{"border-t":U()}],"border-w-r":[{"border-r":U()}],"border-w-b":[{"border-b":U()}],"border-w-l":[{"border-l":U()}],"divide-x":[{"divide-x":U()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":U()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...F(),"hidden","none"]}],"divide-style":[{divide:[...F(),"hidden","none"]}],"border-color":[{border:G()}],"border-color-x":[{"border-x":G()}],"border-color-y":[{"border-y":G()}],"border-color-s":[{"border-s":G()}],"border-color-e":[{"border-e":G()}],"border-color-bs":[{"border-bs":G()}],"border-color-be":[{"border-be":G()}],"border-color-t":[{"border-t":G()}],"border-color-r":[{"border-r":G()}],"border-color-b":[{"border-b":G()}],"border-color-l":[{"border-l":G()}],"divide-color":[{divide:G()}],"outline-style":[{outline:[...F(),"none","hidden"]}],"outline-offset":[{"outline-offset":[Re,oe,ae]}],"outline-w":[{outline:["",Re,us,ha]}],"outline-color":[{outline:G()}],shadow:[{shadow:["","none",p,Ls,$s]}],"shadow-color":[{shadow:G()}],"inset-shadow":[{"inset-shadow":["none",b,Ls,$s]}],"inset-shadow-color":[{"inset-shadow":G()}],"ring-w":[{ring:U()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:G()}],"ring-offset-w":[{"ring-offset":[Re,ha]}],"ring-offset-color":[{"ring-offset":G()}],"inset-ring-w":[{"inset-ring":U()}],"inset-ring-color":[{"inset-ring":G()}],"text-shadow":[{"text-shadow":["none",w,Ls,$s]}],"text-shadow-color":[{"text-shadow":G()}],opacity:[{opacity:[Re,oe,ae]}],"mix-blend":[{"mix-blend":[...Qe(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":Qe()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[Re]}],"mask-image-linear-from-pos":[{"mask-linear-from":le()}],"mask-image-linear-to-pos":[{"mask-linear-to":le()}],"mask-image-linear-from-color":[{"mask-linear-from":G()}],"mask-image-linear-to-color":[{"mask-linear-to":G()}],"mask-image-t-from-pos":[{"mask-t-from":le()}],"mask-image-t-to-pos":[{"mask-t-to":le()}],"mask-image-t-from-color":[{"mask-t-from":G()}],"mask-image-t-to-color":[{"mask-t-to":G()}],"mask-image-r-from-pos":[{"mask-r-from":le()}],"mask-image-r-to-pos":[{"mask-r-to":le()}],"mask-image-r-from-color":[{"mask-r-from":G()}],"mask-image-r-to-color":[{"mask-r-to":G()}],"mask-image-b-from-pos":[{"mask-b-from":le()}],"mask-image-b-to-pos":[{"mask-b-to":le()}],"mask-image-b-from-color":[{"mask-b-from":G()}],"mask-image-b-to-color":[{"mask-b-to":G()}],"mask-image-l-from-pos":[{"mask-l-from":le()}],"mask-image-l-to-pos":[{"mask-l-to":le()}],"mask-image-l-from-color":[{"mask-l-from":G()}],"mask-image-l-to-color":[{"mask-l-to":G()}],"mask-image-x-from-pos":[{"mask-x-from":le()}],"mask-image-x-to-pos":[{"mask-x-to":le()}],"mask-image-x-from-color":[{"mask-x-from":G()}],"mask-image-x-to-color":[{"mask-x-to":G()}],"mask-image-y-from-pos":[{"mask-y-from":le()}],"mask-image-y-to-pos":[{"mask-y-to":le()}],"mask-image-y-from-color":[{"mask-y-from":G()}],"mask-image-y-to-color":[{"mask-y-to":G()}],"mask-image-radial":[{"mask-radial":[oe,ae]}],"mask-image-radial-from-pos":[{"mask-radial-from":le()}],"mask-image-radial-to-pos":[{"mask-radial-to":le()}],"mask-image-radial-from-color":[{"mask-radial-from":G()}],"mask-image-radial-to-color":[{"mask-radial-to":G()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":S()}],"mask-image-conic-pos":[{"mask-conic":[Re]}],"mask-image-conic-from-pos":[{"mask-conic-from":le()}],"mask-image-conic-to-pos":[{"mask-conic-to":le()}],"mask-image-conic-from-color":[{"mask-conic-from":G()}],"mask-image-conic-to-color":[{"mask-conic-to":G()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:ut()}],"mask-repeat":[{mask:me()}],"mask-size":[{mask:T()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",oe,ae]}],filter:[{filter:["","none",oe,ae]}],blur:[{blur:Et()}],brightness:[{brightness:[Re,oe,ae]}],contrast:[{contrast:[Re,oe,ae]}],"drop-shadow":[{"drop-shadow":["","none",z,Ls,$s]}],"drop-shadow-color":[{"drop-shadow":G()}],grayscale:[{grayscale:["",Re,oe,ae]}],"hue-rotate":[{"hue-rotate":[Re,oe,ae]}],invert:[{invert:["",Re,oe,ae]}],saturate:[{saturate:[Re,oe,ae]}],sepia:[{sepia:["",Re,oe,ae]}],"backdrop-filter":[{"backdrop-filter":["","none",oe,ae]}],"backdrop-blur":[{"backdrop-blur":Et()}],"backdrop-brightness":[{"backdrop-brightness":[Re,oe,ae]}],"backdrop-contrast":[{"backdrop-contrast":[Re,oe,ae]}],"backdrop-grayscale":[{"backdrop-grayscale":["",Re,oe,ae]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[Re,oe,ae]}],"backdrop-invert":[{"backdrop-invert":["",Re,oe,ae]}],"backdrop-opacity":[{"backdrop-opacity":[Re,oe,ae]}],"backdrop-saturate":[{"backdrop-saturate":[Re,oe,ae]}],"backdrop-sepia":[{"backdrop-sepia":["",Re,oe,ae]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":x()}],"border-spacing-x":[{"border-spacing-x":x()}],"border-spacing-y":[{"border-spacing-y":x()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",oe,ae]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[Re,"initial",oe,ae]}],ease:[{ease:["linear","initial",C,oe,ae]}],delay:[{delay:[Re,oe,ae]}],animate:[{animate:["none",D,oe,ae]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[I,oe,ae]}],"perspective-origin":[{"perspective-origin":j()}],rotate:[{rotate:_t()}],"rotate-x":[{"rotate-x":_t()}],"rotate-y":[{"rotate-y":_t()}],"rotate-z":[{"rotate-z":_t()}],scale:[{scale:Gt()}],"scale-x":[{"scale-x":Gt()}],"scale-y":[{"scale-y":Gt()}],"scale-z":[{"scale-z":Gt()}],"scale-3d":["scale-3d"],skew:[{skew:wt()}],"skew-x":[{"skew-x":wt()}],"skew-y":[{"skew-y":wt()}],transform:[{transform:[oe,ae,"","none","gpu","cpu"]}],"transform-origin":[{origin:j()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:sr()}],"translate-x":[{"translate-x":sr()}],"translate-y":[{"translate-y":sr()}],"translate-z":[{"translate-z":sr()}],"translate-none":["translate-none"],accent:[{accent:G()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:G()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",oe,ae]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":x()}],"scroll-mx":[{"scroll-mx":x()}],"scroll-my":[{"scroll-my":x()}],"scroll-ms":[{"scroll-ms":x()}],"scroll-me":[{"scroll-me":x()}],"scroll-mbs":[{"scroll-mbs":x()}],"scroll-mbe":[{"scroll-mbe":x()}],"scroll-mt":[{"scroll-mt":x()}],"scroll-mr":[{"scroll-mr":x()}],"scroll-mb":[{"scroll-mb":x()}],"scroll-ml":[{"scroll-ml":x()}],"scroll-p":[{"scroll-p":x()}],"scroll-px":[{"scroll-px":x()}],"scroll-py":[{"scroll-py":x()}],"scroll-ps":[{"scroll-ps":x()}],"scroll-pe":[{"scroll-pe":x()}],"scroll-pbs":[{"scroll-pbs":x()}],"scroll-pbe":[{"scroll-pbe":x()}],"scroll-pt":[{"scroll-pt":x()}],"scroll-pr":[{"scroll-pr":x()}],"scroll-pb":[{"scroll-pb":x()}],"scroll-pl":[{"scroll-pl":x()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",oe,ae]}],fill:[{fill:["none",...G()]}],"stroke-w":[{stroke:[Re,us,ha,Si]}],stroke:[{stroke:["none",...G()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},If=df(Tf);function Nt(...e){return If(Ol(e))}const Io="dartlab-conversations",zi=50;function Pf(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function Nf(){try{const e=localStorage.getItem(Io);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const $f=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function Ai(e){return e.map(t=>({...t,messages:t.messages.map(r=>{if(r.role!=="assistant")return r;const a={};for(const[s,o]of Object.entries(r))$f.includes(s)||(a[s]=o);return a})}))}function Ti(e){try{const t={conversations:Ai(e.conversations),activeId:e.activeId};localStorage.setItem(Io,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:Ai(e.conversations),activeId:e.activeId};localStorage.setItem(Io,JSON.stringify(t))}catch{}}}}function Lf(){const e=Nf(),t=e.conversations||[],r=t.find(C=>C.id===e.activeId)?e.activeId:null;let a=B(jt(t)),s=B(jt(r)),o=null;function i(){o&&clearTimeout(o),o=setTimeout(()=>{Ti({conversations:n(a),activeId:n(s)}),o=null},300)}function l(){o&&clearTimeout(o),o=null,Ti({conversations:n(a),activeId:n(s)})}function c(){return n(a).find(C=>C.id===n(s))||null}function f(){const C={id:Pf(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return u(a,[C,...n(a)],!0),n(a).length>zi&&u(a,n(a).slice(0,zi),!0),u(s,C.id,!0),l(),C.id}function p(C){n(a).find(D=>D.id===C)&&(u(s,C,!0),l())}function b(C,D,W=null){const S=c();if(!S)return;const j={role:C,text:D};W&&(j.meta=W),S.messages=[...S.messages,j],S.updatedAt=Date.now(),S.title==="새 대화"&&C==="user"&&(S.title=D.length>30?D.slice(0,30)+"...":D),u(a,[...n(a)],!0),l()}function w(C){const D=c();if(!D||D.messages.length===0)return;const W=D.messages[D.messages.length-1];Object.assign(W,C),D.updatedAt=Date.now(),u(a,[...n(a)],!0),i()}function z(C){u(a,n(a).filter(D=>D.id!==C),!0),n(s)===C&&u(s,n(a).length>0?n(a)[0].id:null,!0),l()}function y(){const C=c();!C||C.messages.length===0||(C.messages=C.messages.slice(0,-1),C.updatedAt=Date.now(),u(a,[...n(a)],!0),l())}function I(C,D){const W=n(a).find(S=>S.id===C);W&&(W.title=D,u(a,[...n(a)],!0),l())}function k(){u(a,[],!0),u(s,null),l()}return{get conversations(){return n(a)},get activeId(){return n(s)},get active(){return c()},createConversation:f,setActive:p,addMessage:b,updateLastMessage:w,removeLastMessage:y,deleteConversation:z,updateTitle:I,clearAll:k,flush:l}}const rd="dartlab-workspace",Of=6;function nd(){return typeof window<"u"&&typeof localStorage<"u"}function Rf(){if(!nd())return{};try{const e=localStorage.getItem(rd);return e?JSON.parse(e):{}}catch{return{}}}function Df(e){nd()&&localStorage.setItem(rd,JSON.stringify(e))}function jf(){const e=Rf();let t=B(!1),r=B(null),a=B(null),s=B("explore"),o=B(null),i=B(null),l=B(null),c=B(null),f=B(jt(e.selectedCompany||null)),p=B(jt(e.recentCompanies||[]));function b(){Df({selectedCompany:n(f),recentCompanies:n(p)})}function w($){if(!($!=null&&$.stockCode))return;const x={stockCode:$.stockCode,corpName:$.corpName||$.company||$.stockCode,company:$.company||$.corpName||$.stockCode,market:$.market||""};u(p,[x,...n(p).filter(H=>H.stockCode!==x.stockCode)].slice(0,Of),!0)}function z($){$&&(u(f,$,!0),w($)),u(r,"viewer"),u(a,null),u(t,!0),b()}function y($){u(r,"data"),u(a,$,!0),u(t,!0),j("explore")}function I(){u(t,!1)}function k($){u(f,$,!0),$&&w($),b()}function C($,x){var H,ne,Y,A;!($!=null&&$.company)&&!($!=null&&$.stockCode)||(u(f,{...n(f)||{},...x||{},corpName:$.company||((H=n(f))==null?void 0:H.corpName)||(x==null?void 0:x.corpName)||(x==null?void 0:x.company),company:$.company||((ne=n(f))==null?void 0:ne.company)||(x==null?void 0:x.company)||(x==null?void 0:x.corpName),stockCode:$.stockCode||((Y=n(f))==null?void 0:Y.stockCode)||(x==null?void 0:x.stockCode),market:((A=n(f))==null?void 0:A.market)||(x==null?void 0:x.market)||""},!0),w(n(f)),b())}function D($,x){u(l,$,!0),u(c,x||$,!0)}function W($,x=null){u(r,"data"),u(t,!0),u(s,"evidence"),u(o,$,!0),u(i,Number.isInteger(x)?x:null,!0)}function S(){u(o,null),u(i,null)}function j($){u(s,$||"explore",!0),n(s)!=="evidence"&&S()}function de(){return n(t)?n(r)==="viewer"&&n(f)?{type:"viewer",company:n(f),topic:n(l),topicLabel:n(c)}:n(r)==="data"&&n(a)?{type:"data",data:n(a)}:null:null}return{get panelOpen(){return n(t)},get panelMode(){return n(r)},get panelData(){return n(a)},get activeTab(){return n(s)},get activeEvidenceSection(){return n(o)},get selectedEvidenceIndex(){return n(i)},get selectedCompany(){return n(f)},get recentCompanies(){return n(p)},get viewerTopic(){return n(l)},get viewerTopicLabel(){return n(c)},openViewer:z,openData:y,openEvidence:W,closePanel:I,selectCompany:k,setViewerTopic:D,clearEvidenceSelection:S,setTab:j,syncCompanyFromMessage:C,getViewContext:de}}var Vf=h("<a><!></a>"),qf=h("<button><!></button>");function Ff(e,t){Zr(t,!0);let r=ot(t,"variant",3,"default"),a=ot(t,"size",3,"default"),s=Tu(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const o={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},i={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=Ce(),c=Z(l);{var f=b=>{var w=Vf();js(w,y=>({class:y,...s}),[()=>Nt("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",o[r()],i[a()],t.class)]);var z=d(w);Eo(z,()=>t.children),v(b,w)},p=b=>{var w=qf();js(w,y=>({class:y,...s}),[()=>Nt("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",o[r()],i[a()],t.class)]);var z=d(w);Eo(z,()=>t.children),v(b,w)};E(c,b=>{t.href?b(f):b(p,-1)})}v(e,l),en()}wc();/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
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
 */const Ii=(...e)=>e.filter((t,r,a)=>!!t&&t.trim()!==""&&a.indexOf(t)===r).join(" ").trim();var Hf=cu("<svg><!><!></svg>");function We(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]),a=De(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);Zr(t,!1);let s=ot(t,"name",8,void 0),o=ot(t,"color",8,"currentColor"),i=ot(t,"size",8,24),l=ot(t,"strokeWidth",8,2),c=ot(t,"absoluteStrokeWidth",8,!1),f=ot(t,"iconNode",24,()=>[]);Eu();var p=Hf();js(p,(z,y,I)=>({...Bf,...z,...a,width:i(),height:i(),stroke:o(),"stroke-width":y,class:I}),[()=>Gf(a)?void 0:{"aria-hidden":"true"},()=>(ga(c()),ga(l()),ga(i()),Ta(()=>c()?Number(l())*24/Number(i()):l())),()=>(ga(Ii),ga(s()),ga(r),Ta(()=>Ii("lucide-icon","lucide",s()?`lucide-${s()}`:"",r.class)))]);var b=d(p);Pe(b,1,f,Ie,(z,y)=>{var I=q(()=>Bi(n(y),2));let k=()=>n(I)[0],C=()=>n(I)[1];var D=Ce(),W=Z(D);xu(W,k,!0,(S,j)=>{js(S,()=>({...C()}))}),v(z,D)});var w=m(b);He(w,t,"default",{}),v(e,p),en()}function Uf(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];We(e,Ue({name:"activity"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Wf(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];We(e,Ue({name:"arrow-up"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Pi(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 7v14"}],["path",{d:"M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"}]];We(e,Ue({name:"book-open"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function io(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];We(e,Ue({name:"brain"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Kf(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]];We(e,Ue({name:"chart-column"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Yf(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M20 6 9 17l-5-5"}]];We(e,Ue({name:"check"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Xf(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m6 9 6 6 6-6"}]];We(e,Ue({name:"chevron-down"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Jf(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m9 18 6-6-6-6"}]];We(e,Ue({name:"chevron-right"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function fs(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];We(e,Ue({name:"circle-alert"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function bs(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];We(e,Ue({name:"circle-check"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Qf(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];We(e,Ue({name:"clock"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Zf(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];We(e,Ue({name:"code"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ev(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];We(e,Ue({name:"coffee"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function vs(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];We(e,Ue({name:"database"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function _s(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];We(e,Ue({name:"download"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Ni(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];We(e,Ue({name:"external-link"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function tv(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];We(e,Ue({name:"eye"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function jn(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];We(e,Ue({name:"file-text"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function rv(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];We(e,Ue({name:"github"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function $i(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];We(e,Ue({name:"key"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function cn(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];We(e,Ue({name:"loader-circle"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function nv(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];We(e,Ue({name:"log-out"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ad(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"m21 3-7 7"}],["path",{d:"m3 21 7-7"}],["path",{d:"M9 21H3v-6"}]];We(e,Ue({name:"maximize-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function av(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];We(e,Ue({name:"menu"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Li(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];We(e,Ue({name:"message-square"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function sd(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m14 10 7-7"}],["path",{d:"M20 10h-6V4"}],["path",{d:"m3 21 7-7"}],["path",{d:"M4 14h6v6"}]];We(e,Ue({name:"minimize-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function sv(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];We(e,Ue({name:"panel-left-close"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Oi(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];We(e,Ue({name:"plus"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ov(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];We(e,Ue({name:"refresh-cw"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ws(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];We(e,Ue({name:"search"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function iv(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];We(e,Ue({name:"settings"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function lv(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];We(e,Ue({name:"square"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function dv(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];We(e,Ue({name:"terminal"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function cv(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];We(e,Ue({name:"trash-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function uv(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];We(e,Ue({name:"triangle-alert"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Ri(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];We(e,Ue({name:"wrench"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function qs(e,t){const r=De(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];We(e,Ue({name:"x"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=Ce(),l=Z(i);He(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}var fv=h("<!> 새 대화",1),vv=h('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),pv=h('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),mv=h('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),hv=h('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40"><span class="text-[10px] text-dl-text-dim font-mono"> </span></div>'),gv=h('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),xv=h("<button><!></button>"),bv=h('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),_v=h("<aside><!></aside>");function wv(e,t){Zr(t,!0);let r=ot(t,"conversations",19,()=>[]),a=ot(t,"activeId",3,null),s=ot(t,"open",3,!0),o=ot(t,"version",3,""),i=B("");function l(y){const I=new Date().setHours(0,0,0,0),k=I-864e5,C=I-7*864e5,D={오늘:[],어제:[],"이번 주":[],이전:[]};for(const S of y)S.updatedAt>=I?D.오늘.push(S):S.updatedAt>=k?D.어제.push(S):S.updatedAt>=C?D["이번 주"].push(S):D.이전.push(S);const W=[];for(const[S,j]of Object.entries(D))j.length>0&&W.push({label:S,items:j});return W}let c=q(()=>n(i).trim()?r().filter(y=>y.title.toLowerCase().includes(n(i).toLowerCase())):r()),f=q(()=>l(n(c)));var p=_v(),b=d(p);{var w=y=>{var I=gv(),k=m(d(I),2),C=d(k);Ff(C,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:($,x)=>{var H=fv(),ne=Z(H);Oi(ne,{size:16}),v($,H)},$$slots:{default:!0}});var D=m(k,2);{var W=$=>{var x=vv(),H=d(x),ne=d(H);ws(ne,{size:12,class:"text-dl-text-dim flex-shrink-0"});var Y=m(ne,2);Ra(Y,()=>n(i),A=>u(i,A)),v($,x)};E(D,$=>{r().length>3&&$(W)})}var S=m(D,2);Pe(S,21,()=>n(f),Ie,($,x)=>{var H=mv(),ne=d(H),Y=d(ne),A=m(ne,2);Pe(A,17,()=>n(x).items,Ie,(ie,ve)=>{var ke=pv(),pe=d(ke),Ee=d(pe);Li(Ee,{size:14,class:"flex-shrink-0 opacity-50"});var ge=m(Ee,2),xe=d(ge),G=m(pe,2),ut=d(G);cv(ut,{size:12}),N(me=>{$e(ke,1,me),qn(pe,"aria-current",n(ve).id===a()?"true":void 0),P(xe,n(ve).title),qn(G,"aria-label",`${n(ve).title} 삭제`)},[()=>Pt(Nt("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",n(ve).id===a()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),se("click",pe,()=>{var me;return(me=t.onSelect)==null?void 0:me.call(t,n(ve).id)}),se("click",G,me=>{var T;me.stopPropagation(),(T=t.onDelete)==null||T.call(t,n(ve).id)}),v(ie,ke)}),N(()=>P(Y,n(x).label)),v($,H)});var j=m(S,2);{var de=$=>{var x=hv(),H=d(x),ne=d(H);N(()=>P(ne,`v${o()??""}`)),v($,x)};E(j,$=>{o()&&$(de)})}v(y,I)},z=y=>{var I=bv(),k=m(d(I),2),C=d(k);Oi(C,{size:18});var D=m(k,2);Pe(D,21,()=>r().slice(0,10),Ie,(W,S)=>{var j=xv(),de=d(j);Li(de,{size:16}),N($=>{$e(j,1,$),qn(j,"title",n(S).title)},[()=>Pt(Nt("p-2 rounded-lg transition-colors w-full flex justify-center",n(S).id===a()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),se("click",j,()=>{var $;return($=t.onSelect)==null?void 0:$.call(t,n(S).id)}),v(W,j)}),se("click",k,function(...W){var S;(S=t.onNewChat)==null||S.apply(this,W)}),v(y,I)};E(b,y=>{s()?y(w):y(z,-1)})}N(y=>$e(p,1,y),[()=>Pt(Nt("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",s()?"w-[260px]":"w-[52px]"))]),v(e,p),en()}Bn(["click"]);var yv=h('<button class="send-btn active"><!></button>'),kv=h("<button><!></button>"),Cv=h('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),Sv=h('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),Mv=h('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),Ev=h('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function od(e,t){Zr(t,!0);let r=ot(t,"inputText",15,""),a=ot(t,"isLoading",3,!1),s=ot(t,"large",3,!1),o=ot(t,"placeholder",3,"메시지를 입력하세요..."),i=B(jt([])),l=B(!1),c=B(-1),f=null,p=B(void 0);function b(x){var H;if(n(l)&&n(i).length>0){if(x.key==="ArrowDown"){x.preventDefault(),u(c,(n(c)+1)%n(i).length);return}if(x.key==="ArrowUp"){x.preventDefault(),u(c,n(c)<=0?n(i).length-1:n(c)-1,!0);return}if(x.key==="Enter"&&n(c)>=0){x.preventDefault(),y(n(i)[n(c)]);return}if(x.key==="Escape"){u(l,!1),u(c,-1);return}}x.key==="Enter"&&!x.shiftKey&&(x.preventDefault(),u(l,!1),(H=t.onSend)==null||H.call(t))}function w(x){x.target.style.height="auto",x.target.style.height=Math.min(x.target.scrollHeight,200)+"px"}function z(x){w(x);const H=r();f&&clearTimeout(f),H.length>=2&&!/\s/.test(H.slice(-1))?f=setTimeout(async()=>{var ne;try{const Y=await ql(H.trim());((ne=Y.results)==null?void 0:ne.length)>0?(u(i,Y.results.slice(0,6),!0),u(l,!0),u(c,-1)):u(l,!1)}catch{u(l,!1)}},300):u(l,!1)}function y(x){var H;r(`${x.corpName} `),u(l,!1),u(c,-1),(H=t.onCompanySelect)==null||H.call(t,x),n(p)&&n(p).focus()}function I(){setTimeout(()=>{u(l,!1)},200)}var k=Ev(),C=d(k),D=d(C);Qa(D,x=>u(p,x),()=>n(p));var W=m(D,2);{var S=x=>{var H=yv(),ne=d(H);lv(ne,{size:14}),se("click",H,function(...Y){var A;(A=t.onStop)==null||A.apply(this,Y)}),v(x,H)},j=x=>{var H=kv(),ne=d(H);{let Y=q(()=>s()?18:16);Wf(ne,{get size(){return n(Y)},strokeWidth:2.5})}N((Y,A)=>{$e(H,1,Y),H.disabled=A},[()=>Pt(Nt("send-btn",r().trim()&&"active")),()=>!r().trim()]),se("click",H,()=>{var Y;u(l,!1),(Y=t.onSend)==null||Y.call(t)}),v(x,H)};E(W,x=>{a()&&t.onStop?x(S):x(j,-1)})}var de=m(C,2);{var $=x=>{var H=Mv();Pe(H,21,()=>n(i),Ie,(ne,Y,A)=>{var ie=Sv(),ve=d(ie);ws(ve,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var ke=m(ve,2),pe=d(ke),Ee=d(pe),ge=m(pe,2),xe=d(ge),G=m(ke,2);{var ut=me=>{var T=Cv(),re=d(T);N(()=>P(re,n(Y).sector)),v(me,T)};E(G,me=>{n(Y).sector&&me(ut)})}N(me=>{$e(ie,1,me),P(Ee,n(Y).corpName),P(xe,`${n(Y).stockCode??""} · ${(n(Y).market||"")??""}`)},[()=>Pt(Nt("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",A===n(c)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),se("mousedown",ie,()=>y(n(Y))),Da("mouseenter",ie,()=>{u(c,A,!0)}),v(ne,ie)}),v(x,H)};E(de,x=>{n(l)&&n(i).length>0&&x($)})}N(x=>{$e(C,1,x),qn(D,"placeholder",o())},[()=>Pt(Nt("input-box",s()&&"large"))]),se("keydown",D,b),se("input",D,z),Da("blur",D,I),Ra(D,r),v(e,k),en()}Bn(["keydown","input","click","mousedown"]);var zv=h('<button class="rounded-full border border-dl-border/60 bg-dl-bg-card/40 px-3 py-1.5 text-[12px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"> </button>'),Av=h(`<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[580px] flex flex-col items-center"><div class="relative mb-8"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p> <div class="mb-6 max-w-[520px] rounded-2xl border border-dl-border/50 bg-dl-bg-card/50 px-4 py-3 text-left"><div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">Evidence First</div> <div class="mt-2 text-[13px] leading-relaxed text-dl-text-muted">DartLab은 재무 수치와 서술 텍스트를 함께 읽고, 표준화된 계정과 원문 근거를 같은 흐름에서 확인하도록 설계되어 있습니다.
				DART와 EDGAR를 포함한 40개 모듈 이상의 기능 범위를 먼저 물어본 뒤 바로 탐색을 시작할 수 있습니다.</div></div> <div class="w-full"><!></div> <div class="mt-5 flex w-full flex-wrap justify-center gap-2"></div></div></div>`);function Tv(e,t){Zr(t,!0);let r=ot(t,"inputText",15,"");const a=["지금 dartlab에서 할 수 있는 기능을 먼저 정리해줘","EDGAR에서 추가로 받을 수 있는 데이터와 방법을 알려줘","OpenDart와 OpenEdgar로 가능한 일을 비교해줘","GPT 연결 시 현재 UI에서 가능한 코딩 작업 범위를 알려줘"];var s=Av(),o=d(s),i=m(d(o),8),l=d(i);od(l,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get onCompanySelect(){return t.onCompanySelect},get inputText(){return r()},set inputText(f){r(f)}});var c=m(i,2);Pe(c,21,()=>a,Ie,(f,p)=>{var b=zv(),w=d(b);N(()=>P(w,n(p))),se("click",b,()=>{var z;return(z=t.onSend)==null?void 0:z.call(t,n(p))}),v(f,b)}),v(e,s),en()}Bn(["click"]);var Iv=h("<span><!></span>");function ps(e,t){Zr(t,!0);let r=ot(t,"variant",3,"default");const a={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var s=Iv(),o=d(s);Eo(o,()=>t.children),N(i=>$e(s,1,i),[()=>Pt(Nt("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",a[r()],t.class))]),v(e,s),en()}function Pv(e){const t=e.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(t)||t==="-"||t==="0"}function Za(e){if(!e)return"";let t=[],r=[],a=e.replace(/```(\w*)\n([\s\S]*?)```/g,(o,i,l)=>{const c=t.length;return t.push(l.trimEnd()),`
%%CODE_${c}%%
`});a=a.replace(/((?:^\|.+\|$\n?)+)/gm,o=>{const i=o.trim().split(`
`).filter(w=>w.trim());let l=null,c=-1,f=[];for(let w=0;w<i.length;w++)if(i[w].slice(1,-1).split("|").map(y=>y.trim()).every(y=>/^[\-:]+$/.test(y))){c=w;break}c>0?(l=i[c-1],f=i.slice(c+1)):(c===0||(l=i[0]),f=i.slice(1));let p="<table>";if(l){const w=l.slice(1,-1).split("|").map(z=>z.trim());p+="<thead><tr>"+w.map(z=>`<th>${z.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(f.length>0){p+="<tbody>";for(const w of f){const z=w.slice(1,-1).split("|").map(y=>y.trim());p+="<tr>"+z.map(y=>{let I=y.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${Pv(y)?' class="num"':""}>${I}</td>`}).join("")+"</tr>"}p+="</tbody>"}p+="</table>";let b=r.length;return r.push(p),`
%%TABLE_${b}%%
`});let s=a.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");s=s.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,o=>"<ul>"+o.replace(/<br>/g,"")+"</ul>");for(let o=0;o<r.length;o++)s=s.replace(`%%TABLE_${o}%%`,r[o]);for(let o=0;o<t.length;o++){const i=t[o].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");s=s.replace(`%%CODE_${o}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${o}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${i}</code></pre></div>`)}return s=s.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(o,i)=>i.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+s+"</p>"}var Nv=h('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),$v=h('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),Lv=h('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),Ov=h('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),Rv=h('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!> <!> <!> <!></div></div>'),Dv=h('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),jv=h('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),Vv=h('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),qv=h('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),Fv=h("<button><!> </button>"),Bv=h('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),Gv=h('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),Hv=h('<!> <span class="text-dl-text-dim"> </span>',1),Uv=h('<div class="flex items-center gap-2 text-[11px]"><!></div>'),Wv=h('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),Kv=h('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),Yv=h('<div class="message-committed"><!></div>'),Xv=h('<div><div class="message-live-label"> </div> <pre> </pre></div>'),Jv=h('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),Qv=h('<span class="text-dl-accent/60"> </span>'),Zv=h('<span class="text-dl-success/60"> </span>'),ep=h('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),tp=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),rp=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),np=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),ap=h('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),sp=h("<!>  <div><!> <!></div> <!>",1),op=h('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),ip=h('<span class="text-[10px] text-dl-text-dim"> </span>'),lp=h('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),dp=h("<button> </button>"),cp=h('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),up=h("<button>시스템 프롬프트</button>"),fp=h("<button>LLM 입력</button>"),vp=h('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),pp=h('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),mp=h('<span class="text-dl-text"> </span>'),hp=h('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),gp=h('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),xp=h('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),bp=h("<!> <!>",1);function _p(e,t){Zr(t,!0);let r=B(null),a=B("context"),s=B("raw"),o=q(()=>{var T,re,K,U,F,Qe;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((T=t.message.toolEvents)==null?void 0:T.length)>0){const le=[...t.message.toolEvents].reverse().find(_t=>_t.type==="call"),Et=((re=le==null?void 0:le.arguments)==null?void 0:re.module)||((K=le==null?void 0:le.arguments)==null?void 0:K.keyword)||"";return`도구 실행 중 — ${(le==null?void 0:le.name)||""}${Et?` (${Et})`:""}`}if(((U=t.message.contexts)==null?void 0:U.length)>0){const le=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(le==null?void 0:le.label)||(le==null?void 0:le.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(F=t.message.meta)!=null&&F.company?`${t.message.meta.company} 데이터 검색 중`:(Qe=t.message.meta)!=null&&Qe.includedModules?"분석 모듈 선택 완료":"생각 중"}),i=q(()=>{var T;return t.message.company||((T=t.message.meta)==null?void 0:T.company)||null});const l={capability:"기능 탐색",coding:"코딩 작업",company_explore:"회사 탐색",company_analysis:"회사 분석",follow_up:"후속 질문",general_chat:"일반 대화"};let c=q(()=>{var T;return(T=t.message.meta)!=null&&T.dialogueMode?l[t.message.meta.dialogueMode]||t.message.meta.dialogueMode:null}),f=q(()=>{var T,re,K;return t.message.systemPrompt||t.message.userContent||((T=t.message.contexts)==null?void 0:T.length)>0||((re=t.message.meta)==null?void 0:re.includedModules)||((K=t.message.toolEvents)==null?void 0:K.length)>0}),p=q(()=>{var re;const T=(re=t.message.meta)==null?void 0:re.dataYearRange;return T?typeof T=="string"?T:T.min_year&&T.max_year?`${T.min_year}~${T.max_year}년`:null:null});function b(T){if(!T)return 0;const re=(T.match(/[\uac00-\ud7af]/g)||[]).length,K=T.length-re;return Math.round(re*1.5+K/3.5)}function w(T){return T>=1e3?(T/1e3).toFixed(1)+"k":String(T)}let z=q(()=>{var re;let T=0;if(t.message.systemPrompt&&(T+=b(t.message.systemPrompt)),t.message.userContent)T+=b(t.message.userContent);else if(((re=t.message.contexts)==null?void 0:re.length)>0)for(const K of t.message.contexts)T+=b(K.text);return T}),y=q(()=>b(t.message.text)),I=B(void 0);const k=/^\s*\|.+\|\s*$/;function C(T,re){if(!T)return{committed:"",draft:"",draftType:"none"};if(!re)return{committed:T,draft:"",draftType:"none"};const K=T.split(`
`);let U=K.length;T.endsWith(`
`)||(U=Math.min(U,K.length-1));let F=0,Qe=-1;for(let wt=0;wt<K.length;wt++)K[wt].trim().startsWith("```")&&(F+=1,Qe=wt);F%2===1&&Qe>=0&&(U=Math.min(U,Qe));let le=-1;for(let wt=K.length-1;wt>=0;wt--){const sr=K[wt];if(!sr.trim())break;if(k.test(sr))le=wt;else{le=-1;break}}if(le>=0&&(U=Math.min(U,le)),U<=0)return{committed:"",draft:T,draftType:le===0?"table":F%2===1?"code":"text"};const Et=K.slice(0,U).join(`
`),_t=K.slice(U).join(`
`);let Gt="text";return _t&&le>=U?Gt="table":_t&&F%2===1&&(Gt="code"),{committed:Et,draft:_t,draftType:Gt}}const D='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',W='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function S(T){var F;const re=T.target.closest(".code-copy-btn");if(!re)return;const K=re.closest(".code-block-wrap"),U=((F=K==null?void 0:K.querySelector("code"))==null?void 0:F.textContent)||"";navigator.clipboard.writeText(U).then(()=>{re.innerHTML=W,setTimeout(()=>{re.innerHTML=D},2e3)})}function j(T){if(t.onOpenEvidence){t.onOpenEvidence("contexts",T);return}u(r,T,!0),u(a,"context"),u(s,"rendered")}function de(){if(t.onOpenEvidence){t.onOpenEvidence("system");return}u(r,0),u(a,"system"),u(s,"raw")}function $(){if(t.onOpenEvidence){t.onOpenEvidence("snapshot");return}u(r,0),u(a,"snapshot")}function x(T){var re;if(t.onOpenEvidence){const K=(re=t.message.toolEvents)==null?void 0:re[T];t.onOpenEvidence((K==null?void 0:K.type)==="result"?"tool-results":"tool-calls",T);return}u(r,T,!0),u(a,"tool"),u(s,"raw")}function H(){if(t.onOpenEvidence){t.onOpenEvidence("input");return}u(r,0),u(a,"userContent"),u(s,"raw")}function ne(){u(r,null)}function Y(T){var re,K,U,F;return T?T.type==="call"?((re=T.arguments)==null?void 0:re.module)||((K=T.arguments)==null?void 0:K.keyword)||((U=T.arguments)==null?void 0:U.engine)||((F=T.arguments)==null?void 0:F.name)||"":typeof T.result=="string"?T.result.slice(0,120):T.result&&typeof T.result=="object"&&(T.result.module||T.result.status||T.result.name)||"":""}let A=q(()=>(t.message.toolEvents||[]).filter(T=>T.type==="call")),ie=q(()=>(t.message.toolEvents||[]).filter(T=>T.type==="result")),ve=q(()=>C(t.message.text||"",t.message.loading)),ke=q(()=>{var re,K,U;const T=[];return((K=(re=t.message.meta)==null?void 0:re.includedModules)==null?void 0:K.length)>0&&T.push({label:`모듈 ${t.message.meta.includedModules.length}개`,icon:vs}),((U=t.message.contexts)==null?void 0:U.length)>0&&T.push({label:`컨텍스트 ${t.message.contexts.length}건`,icon:tv}),n(A).length>0&&T.push({label:`툴 호출 ${n(A).length}건`,icon:Ri}),n(ie).length>0&&T.push({label:`툴 결과 ${n(ie).length}건`,icon:bs}),t.message.systemPrompt&&T.push({label:"시스템 프롬프트",icon:io}),t.message.userContent&&T.push({label:"LLM 입력",icon:jn}),T}),pe=q(()=>{var re,K,U;if(!t.message.loading)return[];const T=[];return(re=t.message.meta)!=null&&re.company&&T.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&T.push({label:"핵심 수치 확인",done:!0}),(K=t.message.meta)!=null&&K.includedModules&&T.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((U=t.message.contexts)==null?void 0:U.length)>0&&T.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&T.push({label:"프롬프트 조립",done:!0}),t.message.text?T.push({label:"응답 작성 중",done:!1}):T.push({label:n(o)||"준비 중",done:!1}),T});var Ee=bp(),ge=Z(Ee);{var xe=T=>{var re=Nv(),K=m(d(re),2),U=d(K),F=d(U);N(()=>P(F,t.message.text)),v(T,re)},G=T=>{var re=op(),K=m(d(re),2),U=d(K);{var F=ft=>{var st=Rv(),vt=d(st),_r=d(vt);Uf(_r,{size:11});var Vt=m(vt,4),gt=d(Vt);{var zt=ze=>{ps(ze,{variant:"muted",children:(Ae,lt)=>{var Me=Qn();N(()=>P(Me,n(i))),v(Ae,Me)},$$slots:{default:!0}})};E(gt,ze=>{n(i)&&ze(zt)})}var _=m(gt,2);{var R=ze=>{ps(ze,{variant:"muted",children:(Ae,lt)=>{var Me=Qn();N(Ve=>P(Me,Ve),[()=>t.message.meta.market.toUpperCase()]),v(Ae,Me)},$$slots:{default:!0}})};E(_,ze=>{var Ae;(Ae=t.message.meta)!=null&&Ae.market&&ze(R)})}var L=m(_,2);{var X=ze=>{ps(ze,{variant:"accent",children:(Ae,lt)=>{var Me=Qn();N(()=>P(Me,n(c))),v(Ae,Me)},$$slots:{default:!0}})};E(L,ze=>{n(c)&&ze(X)})}var V=m(L,2);{var je=ze=>{ps(ze,{variant:"muted",children:(Ae,lt)=>{var Me=Qn();N(()=>P(Me,t.message.meta.topicLabel)),v(Ae,Me)},$$slots:{default:!0}})};E(V,ze=>{var Ae;(Ae=t.message.meta)!=null&&Ae.topicLabel&&ze(je)})}var Ke=m(V,2);{var wr=ze=>{ps(ze,{variant:"accent",children:(Ae,lt)=>{var Me=Qn();N(()=>P(Me,n(p))),v(Ae,Me)},$$slots:{default:!0}})};E(Ke,ze=>{n(p)&&ze(wr)})}var Ze=m(Ke,2);{var Kt=ze=>{var Ae=Ce(),lt=Z(Ae);Pe(lt,17,()=>t.message.contexts,Ie,(Me,Ve,et)=>{var pt=$v(),J=d(pt);vs(J,{size:10,class:"flex-shrink-0"});var Le=m(J);N(()=>P(Le,` ${(n(Ve).label||n(Ve).module)??""}`)),se("click",pt,()=>j(et)),v(Me,pt)}),v(ze,Ae)},Jt=ze=>{var Ae=Lv(),lt=d(Ae);vs(lt,{size:10,class:"flex-shrink-0"});var Me=m(lt);N(()=>P(Me,` 모듈 ${t.message.meta.includedModules.length??""}개`)),v(ze,Ae)};E(Ze,ze=>{var Ae,lt,Me;((Ae=t.message.contexts)==null?void 0:Ae.length)>0?ze(Kt):((Me=(lt=t.message.meta)==null?void 0:lt.includedModules)==null?void 0:Me.length)>0&&ze(Jt,1)})}var Gr=m(Ze,2);Pe(Gr,17,()=>n(ke),Ie,(ze,Ae)=>{var lt=Ov(),Me=d(lt);gu(Me,()=>n(Ae).icon,(et,pt)=>{pt(et,{size:10,class:"flex-shrink-0"})});var Ve=m(Me);N(()=>P(Ve,` ${n(Ae).label??""}`)),se("click",lt,()=>{n(Ae).label.startsWith("컨텍스트")?j(0):n(Ae).label.startsWith("툴 호출")?t.onOpenEvidence?t.onOpenEvidence("tool-calls",0):x(0):n(Ae).label.startsWith("툴 결과")?t.onOpenEvidence?t.onOpenEvidence("tool-results",0):x((t.message.toolEvents||[]).findIndex(et=>et.type==="result")):n(Ae).label==="시스템 프롬프트"?de():n(Ae).label==="LLM 입력"&&H()}),v(ze,lt)}),v(ft,st)};E(U,ft=>{var st,vt;(n(i)||n(p)||((st=t.message.contexts)==null?void 0:st.length)>0||(vt=t.message.meta)!=null&&vt.includedModules||n(ke).length>0)&&ft(F)})}var Qe=m(U,2);{var le=ft=>{var st=qv(),vt=d(st);Pe(vt,21,()=>t.message.snapshot.items,Ie,(gt,zt)=>{const _=q(()=>n(zt).status==="good"?"text-dl-success":n(zt).status==="danger"?"text-dl-primary-light":n(zt).status==="caution"?"text-amber-400":"text-dl-text");var R=Dv(),L=d(R),X=d(L),V=m(L,2),je=d(V);N(Ke=>{P(X,n(zt).label),$e(V,1,Ke),P(je,n(zt).value)},[()=>Pt(Nt("text-[14px] font-semibold leading-snug mt-0.5",n(_)))]),v(gt,R)});var _r=m(vt,2);{var Vt=gt=>{var zt=Vv();Pe(zt,21,()=>t.message.snapshot.warnings,Ie,(_,R)=>{var L=jv(),X=d(L);uv(X,{size:10});var V=m(X);N(()=>P(V,` ${n(R)??""}`)),v(_,L)}),v(gt,zt)};E(_r,gt=>{var zt;((zt=t.message.snapshot.warnings)==null?void 0:zt.length)>0&&gt(Vt)})}se("click",st,$),v(ft,st)};E(Qe,ft=>{var st,vt;((vt=(st=t.message.snapshot)==null?void 0:st.items)==null?void 0:vt.length)>0&&ft(le)})}var Et=m(Qe,2);{var _t=ft=>{var st=Bv(),vt=d(st),_r=m(d(vt),4);Pe(_r,21,()=>t.message.toolEvents,Ie,(Vt,gt,zt)=>{const _=q(()=>Y(n(gt)));var R=Fv(),L=d(R);{var X=Ke=>{Ri(Ke,{size:11})},V=Ke=>{bs(Ke,{size:11})};E(L,Ke=>{n(gt).type==="call"?Ke(X):Ke(V,-1)})}var je=m(L);N(Ke=>{$e(R,1,Ke),P(je,` ${(n(gt).type==="call"?n(gt).name:`${n(gt).name} 결과`)??""}${n(_)?`: ${n(_)}`:""}`)},[()=>Pt(Nt("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",n(gt).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),se("click",R,()=>x(zt)),v(Vt,R)}),v(ft,st)};E(Et,ft=>{var st;((st=t.message.toolEvents)==null?void 0:st.length)>0&&ft(_t)})}var Gt=m(Et,2);{var wt=ft=>{var st=Wv(),vt=d(st);Pe(vt,21,()=>n(pe),Ie,(_r,Vt)=>{var gt=Uv(),zt=d(gt);{var _=L=>{var X=Gv(),V=m(Z(X),2),je=d(V);N(()=>P(je,n(Vt).label)),v(L,X)},R=L=>{var X=Hv(),V=Z(X);cn(V,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var je=m(V,2),Ke=d(je);N(()=>P(Ke,n(Vt).label)),v(L,X)};E(zt,L=>{n(Vt).done?L(_):L(R,-1)})}v(_r,gt)}),v(ft,st)},sr=ft=>{var st=sp(),vt=Z(st);{var _r=V=>{var je=Kv(),Ke=d(je);cn(Ke,{size:12,class:"animate-spin flex-shrink-0"});var wr=m(Ke,2),Ze=d(wr);N(()=>P(Ze,n(o))),v(V,je)};E(vt,V=>{t.message.loading&&V(_r)})}var Vt=m(vt,2),gt=d(Vt);{var zt=V=>{var je=Yv(),Ke=d(je);aa(Ke,()=>Za(n(ve).committed)),v(V,je)};E(gt,V=>{n(ve).committed&&V(zt)})}var _=m(gt,2);{var R=V=>{var je=Xv(),Ke=d(je),wr=d(Ke),Ze=m(Ke,2),Kt=d(Ze);N(Jt=>{$e(je,1,Jt),P(wr,n(ve).draftType==="table"?"표 구성 중":n(ve).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),P(Kt,n(ve).draft)},[()=>Pt(Nt("message-live-tail",n(ve).draftType==="table"&&"message-draft-table",n(ve).draftType==="code"&&"message-draft-code"))]),v(V,je)};E(_,V=>{n(ve).draft&&V(R)})}Qa(Vt,V=>u(I,V),()=>n(I));var L=m(Vt,2);{var X=V=>{var je=ap(),Ke=d(je);{var wr=Ve=>{var et=Jv(),pt=d(et);Qf(pt,{size:10});var J=m(pt);N(()=>P(J,` ${t.message.duration??""}초`)),v(Ve,et)};E(Ke,Ve=>{t.message.duration&&Ve(wr)})}var Ze=m(Ke,2);{var Kt=Ve=>{var et=ep(),pt=d(et);{var J=Ye=>{var xt=Qv(),qe=d(xt);N(mt=>P(qe,`↑${mt??""}`),[()=>w(n(z))]),v(Ye,xt)};E(pt,Ye=>{n(z)>0&&Ye(J)})}var Le=m(pt,2);{var dt=Ye=>{var xt=Zv(),qe=d(xt);N(mt=>P(qe,`↓${mt??""}`),[()=>w(n(y))]),v(Ye,xt)};E(Le,Ye=>{n(y)>0&&Ye(dt)})}v(Ve,et)};E(Ze,Ve=>{(n(z)>0||n(y)>0)&&Ve(Kt)})}var Jt=m(Ze,2);{var Gr=Ve=>{var et=tp(),pt=d(et);ov(pt,{size:10}),se("click",et,()=>{var J;return(J=t.onRegenerate)==null?void 0:J.call(t)}),v(Ve,et)};E(Jt,Ve=>{t.onRegenerate&&Ve(Gr)})}var ze=m(Jt,2);{var Ae=Ve=>{var et=rp(),pt=d(et);io(pt,{size:10}),se("click",et,de),v(Ve,et)};E(ze,Ve=>{t.message.systemPrompt&&Ve(Ae)})}var lt=m(ze,2);{var Me=Ve=>{var et=np(),pt=d(et);jn(pt,{size:10});var J=m(pt);N((Le,dt)=>P(J,` LLM 입력 (${Le??""}자 · ~${dt??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>w(b(t.message.userContent))]),se("click",et,H),v(Ve,et)};E(lt,Ve=>{t.message.userContent&&Ve(Me)})}v(V,je)};E(L,V=>{!t.message.loading&&(t.message.duration||n(f)||t.onRegenerate)&&V(X)})}N(V=>$e(Vt,1,V),[()=>Pt(Nt("prose-dartlab message-body text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),se("click",Vt,S),v(ft,st)};E(Gt,ft=>{t.message.loading&&!t.message.text?ft(wt):ft(sr,-1)})}v(T,re)};E(ge,T=>{t.message.role==="user"?T(xe):T(G,-1)})}var ut=m(ge,2);{var me=T=>{const re=q(()=>n(a)==="system"),K=q(()=>n(a)==="userContent"),U=q(()=>n(a)==="context"),F=q(()=>n(a)==="snapshot"),Qe=q(()=>n(a)==="tool"),le=q(()=>{var J;return n(U)?(J=t.message.contexts)==null?void 0:J[n(r)]:null}),Et=q(()=>{var J;return n(Qe)?(J=t.message.toolEvents)==null?void 0:J[n(r)]:null}),_t=q(()=>{var J,Le,dt,Ye,xt;return n(F)?"핵심 수치 (원본 데이터)":n(re)?"시스템 프롬프트":n(K)?"LLM에 전달된 입력":n(Qe)?((J=n(Et))==null?void 0:J.type)==="call"?`${(Le=n(Et))==null?void 0:Le.name} 호출`:`${(dt=n(Et))==null?void 0:dt.name} 결과`:((Ye=n(le))==null?void 0:Ye.label)||((xt=n(le))==null?void 0:xt.module)||""}),Gt=q(()=>{var J;return n(F)?JSON.stringify(t.message.snapshot,null,2):n(re)?t.message.systemPrompt:n(K)?t.message.userContent:n(Qe)?JSON.stringify(n(Et),null,2):(J=n(le))==null?void 0:J.text});var wt=xp(),sr=d(wt),ft=d(sr),st=d(ft),vt=d(st),_r=d(vt);{var Vt=J=>{vs(J,{size:15,class:"text-dl-success flex-shrink-0"})},gt=J=>{io(J,{size:15,class:"text-dl-primary-light flex-shrink-0"})},zt=J=>{jn(J,{size:15,class:"text-dl-accent flex-shrink-0"})},_=J=>{vs(J,{size:15,class:"flex-shrink-0"})};E(_r,J=>{n(F)?J(Vt):n(re)?J(gt,1):n(K)?J(zt,2):J(_,-1)})}var R=m(_r,2),L=d(R),X=m(R,2);{var V=J=>{var Le=ip(),dt=d(Le);N(Ye=>P(dt,`(${Ye??""}자)`),[()=>{var Ye,xt;return(xt=(Ye=n(Gt))==null?void 0:Ye.length)==null?void 0:xt.toLocaleString()}]),v(J,Le)};E(X,J=>{n(re)&&J(V)})}var je=m(vt,2),Ke=d(je);{var wr=J=>{var Le=lp(),dt=d(Le),Ye=d(dt);jn(Ye,{size:11});var xt=m(dt,2),qe=d(xt);Zf(qe,{size:11}),N((mt,At)=>{$e(dt,1,mt),$e(xt,1,At)},[()=>Pt(Nt("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(s)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>Pt(Nt("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(s)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),se("click",dt,()=>u(s,"rendered")),se("click",xt,()=>u(s,"raw")),v(J,Le)};E(Ke,J=>{n(U)&&J(wr)})}var Ze=m(Ke,2),Kt=d(Ze);qs(Kt,{size:18});var Jt=m(st,2);{var Gr=J=>{var Le=cp(),dt=d(Le);Pe(dt,21,()=>t.message.contexts,Ie,(Ye,xt,qe)=>{var mt=dp(),At=d(mt);N(Qt=>{$e(mt,1,Qt),P(At,t.message.contexts[qe].label||t.message.contexts[qe].module)},[()=>Pt(Nt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",qe===n(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),se("click",mt,()=>{u(r,qe,!0)}),v(Ye,mt)}),v(J,Le)};E(Jt,J=>{var Le;n(U)&&((Le=t.message.contexts)==null?void 0:Le.length)>1&&J(Gr)})}var ze=m(Jt,2);{var Ae=J=>{var Le=vp(),dt=d(Le),Ye=d(dt);{var xt=At=>{var Qt=up();N(Hr=>$e(Qt,1,Hr),[()=>Pt(Nt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(re)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),se("click",Qt,()=>{u(a,"system")}),v(At,Qt)};E(Ye,At=>{t.message.systemPrompt&&At(xt)})}var qe=m(Ye,2);{var mt=At=>{var Qt=fp();N(Hr=>$e(Qt,1,Hr),[()=>Pt(Nt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(K)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),se("click",Qt,()=>{u(a,"userContent")}),v(At,Qt)};E(qe,At=>{t.message.userContent&&At(mt)})}v(J,Le)};E(ze,J=>{!n(U)&&!n(F)&&!n(Qe)&&J(Ae)})}var lt=m(ft,2),Me=d(lt);{var Ve=J=>{var Le=pp(),dt=d(Le);aa(dt,()=>{var Ye;return Za((Ye=n(le))==null?void 0:Ye.text)}),v(J,Le)},et=J=>{var Le=hp(),dt=d(Le),Ye=m(d(dt),2),xt=d(Ye),qe=m(xt);{var mt=Lt=>{var tn=mp(),Tn=d(tn);N(rn=>P(Tn,rn),[()=>Y(n(Et))]),v(Lt,tn)},At=q(()=>Y(n(Et)));E(qe,Lt=>{n(At)&&Lt(mt)})}var Qt=m(dt,2),Hr=d(Qt);N(()=>{var Lt;P(xt,`${((Lt=n(Et))==null?void 0:Lt.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),P(Hr,n(Gt))}),v(J,Le)},pt=J=>{var Le=gp(),dt=d(Le);N(()=>P(dt,n(Gt))),v(J,Le)};E(Me,J=>{n(U)&&n(s)==="rendered"?J(Ve):n(Qe)?J(et,1):J(pt,-1)})}N(()=>P(L,n(_t))),se("click",wt,J=>{J.target===J.currentTarget&&ne()}),se("keydown",wt,J=>{J.key==="Escape"&&ne()}),se("click",Ze,ne),v(T,wt)};E(ut,T=>{n(r)!==null&&T(me)})}v(e,Ee),en()}Bn(["click","keydown"]);var wp=h('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),yp=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),kp=h('<div class="flex justify-end gap-2 mb-1.5"><!></div>'),Cp=h('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8"><!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function Sp(e,t){Zr(t,!0);function r(Y){if(s())return!1;for(let A=a().length-1;A>=0;A--)if(a()[A].role==="assistant"&&!a()[A].error&&a()[A].text)return A===Y;return!1}let a=ot(t,"messages",19,()=>[]),s=ot(t,"isLoading",3,!1),o=ot(t,"inputText",15,""),i=ot(t,"scrollTrigger",3,0);ot(t,"selectedCompany",3,null);function l(Y){return(A,ie)=>{var ke,pe,Ee,ge;(ke=t.onOpenEvidence)==null||ke.call(t,A,ie);let ve;if(A==="contexts")ve=(pe=Y.contexts)==null?void 0:pe[ie];else if(A==="snapshot")ve={label:"핵심 수치",module:"snapshot",text:JSON.stringify(Y.snapshot,null,2)};else if(A==="system")ve={label:"시스템 프롬프트",module:"system",text:Y.systemPrompt};else if(A==="input")ve={label:"LLM 입력",module:"input",text:Y.userContent};else if(A==="tool-calls"||A==="tool-results"){const xe=(Ee=Y.toolEvents)==null?void 0:Ee[ie];ve={label:`${(xe==null?void 0:xe.name)||"도구"} ${(xe==null?void 0:xe.type)==="call"?"호출":"결과"}`,module:"tool",text:JSON.stringify(xe,null,2)}}ve&&((ge=t.onOpenData)==null||ge.call(t,ve))}}let c,f,p=B(!0),b=B(!1),w=B(!0);function z(){if(!c)return;const{scrollTop:Y,scrollHeight:A,clientHeight:ie}=c;u(w,A-Y-ie<96),n(w)?(u(p,!0),u(b,!1)):(u(p,!1),u(b,!0))}function y(Y="smooth"){f&&(f.scrollIntoView({block:"end",behavior:Y}),u(p,!0),u(b,!1))}na(()=>{i(),!(!c||!f)&&requestAnimationFrame(()=>{!c||!f||(n(p)||n(w)?(f.scrollIntoView({block:"end",behavior:s()?"auto":"smooth"}),u(b,!1)):u(b,!0))})});var I=Cp(),k=d(I),C=d(k),D=d(C);Pe(D,17,a,Ie,(Y,A,ie)=>{{let ve=q(()=>r(ie)?t.onRegenerate:void 0),ke=q(()=>t.onOpenData?l(n(A)):void 0);_p(Y,{get message(){return n(A)},get onRegenerate(){return n(ve)},get onOpenEvidence(){return n(ke)}})}});var W=m(D,2);Qa(W,Y=>f=Y,()=>f),Qa(k,Y=>c=Y,()=>c);var S=m(k,2);{var j=Y=>{var A=wp(),ie=d(A);se("click",ie,()=>y("smooth")),v(Y,A)};E(S,Y=>{n(b)&&Y(j)})}var de=m(S,2),$=d(de),x=d($);{var H=Y=>{var A=kp(),ie=d(A);{var ve=ke=>{var pe=yp(),Ee=d(pe);_s(Ee,{size:10}),se("click",pe,function(...ge){var xe;(xe=t.onExport)==null||xe.apply(this,ge)}),v(ke,pe)};E(ie,ke=>{a().length>1&&t.onExport&&ke(ve)})}v(Y,A)};E(x,Y=>{s()||Y(H)})}var ne=m(x,2);od(ne,{get isLoading(){return s()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get onCompanySelect(){return t.onCompanySelect},get inputText(){return o()},set inputText(Y){o(Y)}}),Da("scroll",k,z),v(e,I),en()}Bn(["click"]);var Mp=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!> <span class="text-[13px]">공시 데이터 로딩 중...</span></div>'),Ep=h('<div class="text-[11px] text-dl-text-dim"> </div>'),zp=h('<button><!> <span class="truncate flex-1"> </span></button>'),Ap=h('<div class="py-0.5"></div>'),Tp=h('<div><button class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] opacity-30 font-normal"> </span></button> <!></div>'),Ip=h('<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50"><div class="px-3 py-2.5 border-b border-dl-border/20"><!></div> <!></nav>'),Pp=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim"><!> <p class="text-[13px]">좌측에서 섹션을 선택하세요</p></div>'),Np=h('<div class="text-[10px] text-dl-text-dim/50 mb-0.5"> </div>'),$p=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!></div>'),Lp=h('<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>'),Op=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Rp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Dp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),jp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Vp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),qp=h('<div class="vw-heading-node svelte-1l2nqwu"><!></div>'),Fp=h('<div class="vw-heading-block svelte-1l2nqwu"></div>'),Bp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Gp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Hp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Up=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Wp=h('<button><span class="vw-timeline-label svelte-1l2nqwu"> </span></button>'),Kp=h('<div class="vw-section-timeline svelte-1l2nqwu"></div>'),Yp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Xp=h('<span class="vw-meta-pill svelte-1l2nqwu">비교 없음</span>'),Jp=h('<div class="vw-section-actions svelte-1l2nqwu"><span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span></div>'),Qp=h('<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span> </div>'),Zp=h('<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),em=h('<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),tm=h('<div class="text-[10px] text-dl-text-dim/35 mt-1"> </div>'),rm=h('<div class="vw-digest svelte-1l2nqwu"><div class="flex items-center gap-2 mb-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span></div> <div class="space-y-1"><!> <!> <!> <!></div></div>'),nm=h('<p class="vw-para"> </p>'),am=h('<div class="vw-diff-added svelte-1l2nqwu"> </div>'),sm=h('<div class="vw-diff-deleted svelte-1l2nqwu"> </div>'),om=h('<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow svelte-1l2nqwu"></div>'),im=h('<div class="disclosure-text vw-section-body vw-body-frame svelte-1l2nqwu"><!></div>'),lm=h('<div><!> <div class="vw-section-meta svelte-1l2nqwu"><span> </span> <!> <!> <!> <!></div> <!> <!> <!> <!></div>'),dm=h('<section class="vw-report-shell svelte-1l2nqwu"><div class="vw-report-header svelte-1l2nqwu"><div class="vw-report-badges svelte-1l2nqwu"><!> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <!> <!></div></div> <!></section>'),cm=h('<div class="vw-data-divider svelte-1l2nqwu"><div class="vw-data-kicker svelte-1l2nqwu">Structured Data</div> <div class="vw-data-title svelte-1l2nqwu">표 / 정형 데이터</div></div>'),um=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),fm=h("<th> </th>"),vm=h("<td> </td>"),pm=h("<tr></tr>"),mm=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),hm=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),gm=h("<th> </th>"),xm=h("<td> </td>"),bm=h("<tr></tr>"),_m=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),wm=h("<button> </button>"),ym=h('<span class="text-[9px] text-dl-text-dim/30"> </span>'),km=h('<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto"><!> <!></div>'),Cm=h('<div class="vw-table-wrap bg-dl-bg-card/10 svelte-1l2nqwu"><!> <div class="px-4 py-3"><div class="markdown-table overflow-x-auto svelte-1l2nqwu"><!></div></div></div>'),Sm=h("<th> </th>"),Mm=h("<td> </td>"),Em=h("<tr></tr>"),zm=h('<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02] svelte-1l2nqwu"><div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10"><!> <span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span></div> <div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Am=h('<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card"> </th>'),Tm=h('<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted"> </td>'),Im=h("<tr></tr>"),Pm=h('<div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Nm=h('<article class="py-6 px-8"><!> <!> <!> <!></article>'),$m=h('<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center"><div class="flex-1 min-w-0"><!> <h3 class="text-[16px] font-semibold text-dl-text"> </h3></div> <button class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"><!></button></div> <!>',1),Lm=h('<div class="flex flex-1 overflow-hidden min-h-0"><!> <main class="flex-1 overflow-y-auto min-w-0"><!></main></div>'),Om=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8"><!> <p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p></div>'),Rm=h('<div class="flex flex-col h-full font-sans bg-dl-bg-dark"><!></div>');function Dm(e,t){Zr(t,!0);let r=ot(t,"stockCode",3,null),a=ot(t,"onTopicChange",3,null),s=B(null),o=B(!1),i=B(jt(new Set)),l=B(null),c=B(null),f=B(jt([])),p=B(null),b=B(!1),w=B(jt([])),z=B(jt(new Map)),y=new Map,I=B(!1),k=B(jt(new Map));const C={companyOverview:"회사 개요",companyHistory:"회사 연혁",articlesOfIncorporation:"정관 사항",capitalChange:"자본금 변동",shareCapital:"주식 현황",dividend:"배당",productService:"사업 내용",rawMaterial:"원재료",businessOverview:"사업 개요",salesOrder:"매출/수주",riskDerivative:"위험관리/파생",majorContractsAndRnd:"주요 계약/R&D",otherReferences:"기타 참고사항",consolidatedStatements:"연결 재무제표",fsSummary:"재무제표 요약",consolidatedNotes:"연결 주석",financialStatements:"개별 재무제표",financialNotes:"개별 주석",fundraising:"자금조달",BS:"재무상태표",IS:"손익계산서",CIS:"포괄손익계산서",CF:"현금흐름표",SCE:"자본변동표",ratios:"재무비율",audit:"감사 의견",mdna:"경영진 분석(MD&A)",internalControl:"내부통제",auditContract:"감사 계약",nonAuditContract:"비감사 계약",boardOfDirectors:"이사회",shareholderMeeting:"주주총회",auditSystem:"감사 체계",outsideDirector:"사외이사",majorHolder:"주요 주주",majorHolderChange:"주주 변동",minorityHolder:"소수주주",stockTotal:"주식 총수",treasuryStock:"자기주식",employee:"직원 현황",executivePay:"임원 보수",executive:"임원 현황",executivePayAllTotal:"전체 보수 총액",executivePayIndividual:"개인별 보수",topPay:"5억이상 상위 보수",unregisteredExecutivePay:"미등기임원 보수",affiliateGroup:"계열회사",investedCompany:"투자회사",relatedPartyTx:"특수관계 거래",corporateBond:"사채 관리",privateOfferingUsage:"사모자금 사용",publicOfferingUsage:"공모자금 사용",shortTermBond:"단기사채",investorProtection:"투자자 보호",disclosureChanges:"공시변경 사항",contingentLiability:"우발채무",sanction:"제재/조치",subsequentEvents:"후발사건",expertConfirmation:"전문가 확인",subsidiaryDetail:"종속회사 상세",affiliateGroupDetail:"계열회사 상세",investmentInOtherDetail:"타법인 출자 상세",rndDetail:"R&D 상세"},D={I:"I. 회사의 개요",II:"II. 사업의 내용",III:"III. 재무에 관한 사항",IV:"IV. 감사인의 감사의견 등",V:"V. 이사의 경영진단 및 분석의견",VI:"VI. 이사회 등 회사의 기관에 관한 사항",VII:"VII. 주주에 관한 사항",VIII:"VIII. 임원 및 직원 등에 관한 사항",IX:"IX. 계열회사 등에 관한 사항",X:"X. 대주주 등과의 거래내용",XI:"XI. 그 밖에 투자자 보호를 위하여 필요한 사항",XII:"XII. 상세표"},W={I:1,II:2,III:3,IV:4,V:5,VI:6,VII:7,VIII:8,IX:9,X:10,XI:11,XII:12};function S(_){return W[_]??99}function j(_){return C[_]||_}function de(_){return D[_]||_||"기타"}na(()=>{r()&&$()});async function $(){var _,R;u(o,!0),u(s,null),u(l,null),u(c,null),u(f,[],!0),u(p,null),y=new Map;try{const L=await Vu(r());u(s,L.payload,!0),(_=n(s))!=null&&_.columns&&u(w,n(s).columns.filter(V=>/^\d{4}(Q[1-4])?$/.test(V)),!0);const X=ve((R=n(s))==null?void 0:R.rows);X.length>0&&(u(i,new Set([X[0].chapter]),!0),X[0].topics.length>0&&x(X[0].topics[0].topic,X[0].chapter))}catch(L){console.error("viewer load error:",L)}u(o,!1)}async function x(_,R){var L;if(n(l)!==_){if(u(l,_,!0),u(c,R||null,!0),u(z,new Map,!0),u(k,new Map,!0),(L=a())==null||L(_,j(_)),y.has(_)){const X=y.get(_);u(f,X.blocks||[],!0),u(p,X.textDocument||null,!0);return}u(f,[],!0),u(p,null),u(b,!0);try{const X=await ju(r(),_);u(f,X.blocks||[],!0),u(p,X.textDocument||null,!0),y.set(_,{blocks:n(f),textDocument:n(p)})}catch(X){console.error("topic load error:",X),u(f,[],!0),u(p,null)}u(b,!1)}}function H(_){const R=new Set(n(i));R.has(_)?R.delete(_):R.add(_),u(i,R,!0)}function ne(_,R){const L=new Map(n(z));L.get(_)===R?L.delete(_):L.set(_,R),u(z,L,!0)}function Y(_,R){const L=new Map(n(k));L.set(_,R),u(k,L,!0)}function A(_){return _==="updated"?"최근 수정":_==="new"?"신규":_==="stale"?"과거 유지":"유지"}function ie(_){return _==="updated"?"updated":_==="new"?"new":_==="stale"?"stale":"stable"}function ve(_){if(!_)return[];const R=new Map,L=new Set;for(const X of _){const V=X.chapter||"";R.has(V)||R.set(V,{chapter:V,topics:[]}),L.has(X.topic)||(L.add(X.topic),R.get(V).topics.push({topic:X.topic,source:X.source||"docs"}))}return[...R.values()].sort((X,V)=>S(X.chapter)-S(V.chapter))}function ke(_){return String(_).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function pe(_){return String(_||"").replaceAll(" "," ").replace(/\s+/g," ").trim()}function Ee(_){return!_||_.length>88?!1:/^\[.+\]$/.test(_)||/^【.+】$/.test(_)||/^[IVX]+\.\s/.test(_)||/^\d+\.\s/.test(_)||/^[가-힣]\.\s/.test(_)||/^\(\d+\)\s/.test(_)||/^\([가-힣]\)\s/.test(_)}function ge(_){return/^\(\d+\)\s/.test(_)||/^\([가-힣]\)\s/.test(_)?"h5":"h4"}function xe(_){return/^\[.+\]$/.test(_)||/^【.+】$/.test(_)?"vw-h-bracket":/^\(\d+\)\s/.test(_)||/^\([가-힣]\)\s/.test(_)?"vw-h-sub":"vw-h-section"}function G(_){if(!_)return[];if(/^\|.+\|$/m.test(_)||/^#{1,3} /m.test(_)||/```/.test(_))return[{kind:"markdown",text:_}];const R=[];let L=[];const X=()=>{L.length!==0&&(R.push({kind:"paragraph",text:L.join(" ")}),L=[])};for(const V of String(_).split(`
`)){const je=pe(V);if(!je){X();continue}if(Ee(je)){X(),R.push({kind:"heading",text:je,tag:ge(je),className:xe(je)});continue}L.push(je)}return X(),R}function ut(_){return _?_.kind==="annual"?`${_.year}Q4`:_.year&&_.quarter?`${_.year}Q${_.quarter}`:_.label||"":""}function me(_){var X;const R=G(_);if(R.length===0)return"";if(((X=R[0])==null?void 0:X.kind)==="markdown")return Za(_);let L="";for(const V of R){if(V.kind==="heading"){L+=`<${V.tag} class="${V.className}">${ke(V.text)}</${V.tag}>`;continue}L+=`<p class="vw-para">${ke(V.text)}</p>`}return L}function T(_){if(!_)return"";const R=_.trim().split(`
`).filter(X=>X.trim());let L="";for(const X of R){const V=X.trim();/^[가-힣]\.\s/.test(V)||/^\d+[-.]/.test(V)?L+=`<h4 class="vw-h-section">${V}</h4>`:/^\(\d+\)\s/.test(V)||/^\([가-힣]\)\s/.test(V)?L+=`<h5 class="vw-h-sub">${V}</h5>`:/^\[.+\]$/.test(V)||/^【.+】$/.test(V)?L+=`<h4 class="vw-h-bracket">${V}</h4>`:L+=`<h5 class="vw-h-sub">${V}</h5>`}return L}function re(_){var L;const R=n(z).get(_.id);return R&&((L=_==null?void 0:_.views)!=null&&L[R])?_.views[R]:(_==null?void 0:_.latest)||null}function K(_,R){var X,V;const L=n(z).get(_.id);return L?L===R:((V=(X=_==null?void 0:_.latest)==null?void 0:X.period)==null?void 0:V.label)===R}function U(_){return n(z).has(_.id)}function F(_){return _==="updated"?"변경 있음":_==="new"?"직전 없음":"직전과 동일"}function Qe(_){var je,Ke,wr;if(!_)return[];const R=G(_.body);if(R.length===0||((je=R[0])==null?void 0:je.kind)==="markdown"||!((Ke=_.prevPeriod)!=null&&Ke.label)||!((wr=_.diff)!=null&&wr.length))return R;const L=[];for(const Ze of _.diff)for(const Kt of Ze.paragraphs||[])L.push({kind:Ze.kind,text:pe(Kt)});const X=[];let V=0;for(const Ze of R){if(Ze.kind!=="paragraph"){X.push(Ze);continue}for(;V<L.length&&L[V].kind==="removed";)X.push({kind:"removed",text:L[V].text}),V+=1;V<L.length&&["same","added"].includes(L[V].kind)?(X.push({kind:L[V].kind,text:L[V].text||Ze.text}),V+=1):X.push({kind:"same",text:Ze.text})}for(;V<L.length;)X.push({kind:L[V].kind,text:L[V].text}),V+=1;return X}function le(_){return _==null?!1:/^-?[\d,.]+%?$/.test(String(_).trim().replace(/,/g,""))}function Et(_){return _==null?!1:/^-[\d.]+/.test(String(_).trim().replace(/,/g,""))}function _t(_,R){if(_==null||_==="")return"";const L=typeof _=="number"?_:Number(String(_).replace(/,/g,""));if(isNaN(L))return String(_);if(R<=1)return L.toLocaleString("ko-KR");const X=L/R;return Number.isInteger(X)?X.toLocaleString("ko-KR"):X.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g,",")}function Gt(_){if(_==null||_==="")return"";const R=String(_).trim();if(R.includes(","))return R;const L=R.match(/^(-?\d+)(\.\d+)?(%?)$/);return L?L[1].replace(/\B(?=(\d{3})+(?!\d))/g,",")+(L[2]||"")+(L[3]||""):R}function wt(_){var R,L;return(R=n(s))!=null&&R.rows&&((L=n(s).rows.find(X=>X.topic===_))==null?void 0:L.chapter)||null}function sr(_){const R=_.match(/^(\d{4})(Q([1-4]))?$/);if(!R)return"0000_0";const L=R[1],X=R[3]||"5";return`${L}_${X}`}function ft(_){return[..._].sort((R,L)=>sr(L).localeCompare(sr(R)))}let st=q(()=>n(f).filter(_=>_.kind!=="text"));var vt=Rm(),_r=d(vt);{var Vt=_=>{var R=Mp(),L=d(R);cn(L,{size:18,class:"animate-spin"}),v(_,R)},gt=_=>{var R=Lm(),L=d(R);{var X=Ze=>{var Kt=Ip(),Jt=d(Kt),Gr=d(Jt);{var ze=lt=>{var Me=Ep(),Ve=d(Me);N(()=>P(Ve,`${n(w).length??""}개 기간 · ${n(w)[0]??""} ~ ${n(w)[n(w).length-1]??""}`)),v(lt,Me)};E(Gr,lt=>{n(w).length>0&&lt(ze)})}var Ae=m(Jt,2);Pe(Ae,17,()=>ve(n(s).rows),Ie,(lt,Me)=>{var Ve=Tp(),et=d(Ve),pt=d(et);{var J=Lt=>{Xf(Lt,{size:11,class:"flex-shrink-0 opacity-40"})},Le=q(()=>n(i).has(n(Me).chapter)),dt=Lt=>{Jf(Lt,{size:11,class:"flex-shrink-0 opacity-40"})};E(pt,Lt=>{n(Le)?Lt(J):Lt(dt,-1)})}var Ye=m(pt,2),xt=d(Ye),qe=m(Ye,2),mt=d(qe),At=m(et,2);{var Qt=Lt=>{var tn=Ap();Pe(tn,21,()=>n(Me).topics,Ie,(Tn,rn)=>{var Ht=zp(),Fe=d(Ht);{var yr=or=>{Kf(or,{size:11,class:"flex-shrink-0 text-blue-400/40"})},va=or=>{Pi(or,{size:11,class:"flex-shrink-0 text-emerald-400/40"})},In=or=>{jn(or,{size:11,class:"flex-shrink-0 opacity-30"})};E(Fe,or=>{n(rn).source==="finance"?or(yr):n(rn).source==="report"?or(va,1):or(In,-1)})}var pa=m(Fe,2),mn=d(pa);N(or=>{$e(Ht,1,`group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											${n(l)===n(rn).topic?"bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]":"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent"}`),P(mn,or)},[()=>j(n(rn).topic)]),se("click",Ht,()=>x(n(rn).topic,n(Me).chapter)),v(Tn,Ht)}),v(Lt,tn)},Hr=q(()=>n(i).has(n(Me).chapter));E(At,Lt=>{n(Hr)&&Lt(Qt)})}N(Lt=>{P(xt,Lt),P(mt,n(Me).topics.length)},[()=>de(n(Me).chapter)]),se("click",et,()=>H(n(Me).chapter)),v(lt,Ve)}),v(Ze,Kt)};E(L,Ze=>{n(I)||Ze(X)})}var V=m(L,2),je=d(V);{var Ke=Ze=>{var Kt=Pp(),Jt=d(Kt);jn(Jt,{size:32,strokeWidth:1,class:"opacity-20"}),v(Ze,Kt)},wr=Ze=>{var Kt=$m(),Jt=Z(Kt),Gr=d(Jt),ze=d(Gr);{var Ae=qe=>{var mt=Np(),At=d(mt);N(Qt=>P(At,Qt),[()=>de(n(c)||wt(n(l)))]),v(qe,mt)},lt=q(()=>n(c)||wt(n(l)));E(ze,qe=>{n(lt)&&qe(Ae)})}var Me=m(ze,2),Ve=d(Me),et=m(Gr,2),pt=d(et);{var J=qe=>{sd(qe,{size:15})},Le=qe=>{ad(qe,{size:15})};E(pt,qe=>{n(I)?qe(J):qe(Le,-1)})}var dt=m(Jt,2);{var Ye=qe=>{var mt=$p(),At=d(mt);cn(At,{size:16,class:"animate-spin"}),v(qe,mt)},xt=qe=>{var mt=Nm(),At=d(mt);{var Qt=Ht=>{var Fe=Lp();v(Ht,Fe)};E(At,Ht=>{var Fe,yr;n(f).length===0&&!(((yr=(Fe=n(p))==null?void 0:Fe.sections)==null?void 0:yr.length)>0)&&Ht(Qt)})}var Hr=m(At,2);{var Lt=Ht=>{var Fe=dm(),yr=d(Fe),va=d(yr),In=d(va);{var pa=nt=>{var be=Op(),Oe=d(be);N(at=>P(Oe,`최신 기준 ${at??""}`),[()=>ut(n(p).latestPeriod)]),v(nt,be)};E(In,nt=>{n(p).latestPeriod&&nt(pa)})}var mn=m(In,2);{var or=nt=>{var be=Rp(),Oe=d(be);N((at,kt)=>P(Oe,`커버리지 ${at??""}~${kt??""}`),[()=>ut(n(p).firstPeriod),()=>ut(n(p).latestPeriod)]),v(nt,be)};E(mn,nt=>{n(p).firstPeriod&&nt(or)})}var $a=m(mn,2),Zt=d($a),yt=m($a,2);{var dr=nt=>{var be=Dp(),Oe=d(be);N(()=>P(Oe,`최근 수정 ${n(p).updatedCount??""}개`)),v(nt,be)};E(yt,nt=>{n(p).updatedCount>0&&nt(dr)})}var Yt=m(yt,2);{var cr=nt=>{var be=jp(),Oe=d(be);N(()=>P(Oe,`신규 ${n(p).newCount??""}개`)),v(nt,be)};E(Yt,nt=>{n(p).newCount>0&&nt(cr)})}var kr=m(Yt,2);{var Cr=nt=>{var be=Vp(),Oe=d(be);N(()=>P(Oe,`과거 유지 ${n(p).staleCount??""}개`)),v(nt,be)};E(kr,nt=>{n(p).staleCount>0&&nt(Cr)})}var Lr=m(yr,2);Pe(Lr,17,()=>n(p).sections,Ie,(nt,be)=>{const Oe=q(()=>re(n(be))),at=q(()=>U(n(be)));var kt=lm(),ur=d(kt);{var Te=ee=>{var te=Fp();Pe(te,21,()=>n(be).headingPath,Ie,(fe,ye)=>{var Ct=qp(),ht=d(Ct);aa(ht,()=>T(n(ye).text)),v(fe,Ct)}),v(ee,te)};E(ur,ee=>{var te;((te=n(be).headingPath)==null?void 0:te.length)>0&&ee(Te)})}var tt=m(ur,2),ct=d(tt),Ot=d(ct),g=m(ct,2);{var O=ee=>{var te=Bp(),fe=d(te);N(ye=>P(fe,`최신 ${ye??""}`),[()=>ut(n(be).latestPeriod)]),v(ee,te)};E(g,ee=>{var te;(te=n(be).latestPeriod)!=null&&te.label&&ee(O)})}var ce=m(g,2);{var we=ee=>{var te=Gp(),fe=d(te);N(ye=>P(fe,`최초 ${ye??""}`),[()=>ut(n(be).firstPeriod)]),v(ee,te)};E(ce,ee=>{var te,fe;(te=n(be).firstPeriod)!=null&&te.label&&n(be).firstPeriod.label!==((fe=n(be).latestPeriod)==null?void 0:fe.label)&&ee(we)})}var _e=m(ce,2);{var Ne=ee=>{var te=Hp(),fe=d(te);N(()=>P(fe,`${n(be).periodCount??""}기간`)),v(ee,te)};E(_e,ee=>{n(be).periodCount>0&&ee(Ne)})}var he=m(_e,2);{var Tt=ee=>{var te=Up(),fe=d(te);N(()=>P(fe,`최근 변경 ${n(be).latestChange??""}`)),v(ee,te)};E(he,ee=>{n(be).latestChange&&ee(Tt)})}var qt=m(tt,2);{var Pn=ee=>{var te=Kp();Pe(te,21,()=>n(be).timeline,Ie,(fe,ye)=>{var Ct=Wp(),ht=d(Ct),bt=d(ht);N((Ft,It)=>{$e(Ct,1,`vw-timeline-chip ${Ft??""}`,"svelte-1l2nqwu"),P(bt,It)},[()=>K(n(be),n(ye).period.label)?"is-active":"",()=>ut(n(ye).period)]),se("click",Ct,()=>ne(n(be).id,n(ye).period.label)),v(fe,Ct)}),v(ee,te)};E(qt,ee=>{var te;((te=n(be).timeline)==null?void 0:te.length)>0&&ee(Pn)})}var hn=m(qt,2);{var Gn=ee=>{var te=Jp(),fe=d(te),ye=d(fe),Ct=m(fe,2);{var ht=Rt=>{var Ut=Yp(),Or=d(Ut);N(St=>P(Or,`비교 ${St??""}`),[()=>ut(n(Oe).prevPeriod)]),v(Rt,Ut)},bt=Rt=>{var Ut=Xp();v(Rt,Ut)};E(Ct,Rt=>{var Ut;(Ut=n(Oe).prevPeriod)!=null&&Ut.label?Rt(ht):Rt(bt,-1)})}var Ft=m(Ct,2),It=d(Ft);N((Rt,Ut)=>{P(ye,`선택 ${Rt??""}`),P(It,Ut)},[()=>ut(n(Oe).period),()=>F(n(Oe).status)]),v(ee,te)};E(hn,ee=>{n(at)&&n(Oe)&&ee(Gn)})}var Nn=m(hn,2);{var Se=ee=>{const te=q(()=>n(Oe).digest);var fe=rm(),ye=d(fe),Ct=d(ye),ht=d(Ct),bt=m(ye,2),Ft=d(bt);Pe(Ft,17,()=>n(te).items.filter(St=>St.kind==="numeric"),Ie,(St,fr)=>{var er=Qp(),Dt=m(d(er));N(()=>P(Dt,` ${n(fr).text??""}`)),v(St,er)});var It=m(Ft,2);Pe(It,17,()=>n(te).items.filter(St=>St.kind==="added"),Ie,(St,fr)=>{var er=Zp(),Dt=m(d(er),2),tr=d(Dt);N(()=>P(tr,n(fr).text)),v(St,er)});var Rt=m(It,2);Pe(Rt,17,()=>n(te).items.filter(St=>St.kind==="removed"),Ie,(St,fr)=>{var er=em(),Dt=m(d(er),2),tr=d(Dt);N(()=>P(tr,n(fr).text)),v(St,er)});var Ut=m(Rt,2);{var Or=St=>{var fr=tm(),er=d(fr);N(()=>P(er,`외 ${n(te).wordingCount??""}건 문구 수정`)),v(St,fr)};E(Ut,St=>{n(te).wordingCount>0&&St(Or)})}N(()=>P(ht,`${n(te).to??""} vs ${n(te).from??""}`)),v(ee,fe)};E(Nn,ee=>{var te,fe,ye;n(at)&&((ye=(fe=(te=n(Oe))==null?void 0:te.digest)==null?void 0:fe.items)==null?void 0:ye.length)>0&&ee(Se)})}var ue=m(Nn,2);{var Q=ee=>{var te=Ce(),fe=Z(te);{var ye=ht=>{var bt=om();Pe(bt,21,()=>Qe(n(Oe)),Ie,(Ft,It)=>{var Rt=Ce(),Ut=Z(Rt);{var Or=Dt=>{var tr=Ce(),$n=Z(tr);aa($n,()=>T(n(It).text)),v(Dt,tr)},St=Dt=>{var tr=nm(),$n=d(tr);N(()=>P($n,n(It).text)),v(Dt,tr)},fr=Dt=>{var tr=am(),$n=d(tr);N(()=>P($n,n(It).text)),v(Dt,tr)},er=Dt=>{var tr=sm(),$n=d(tr);N(()=>P($n,n(It).text)),v(Dt,tr)};E(Ut,Dt=>{n(It).kind==="heading"?Dt(Or):n(It).kind==="same"?Dt(St,1):n(It).kind==="added"?Dt(fr,2):n(It).kind==="removed"&&Dt(er,3)})}v(Ft,Rt)}),v(ht,bt)},Ct=ht=>{var bt=im(),Ft=d(bt);aa(Ft,()=>me(n(Oe).body)),v(ht,bt)};E(fe,ht=>{var bt,Ft;n(at)&&((bt=n(Oe).prevPeriod)!=null&&bt.label)&&((Ft=n(Oe).diff)==null?void 0:Ft.length)>0?ht(ye):ht(Ct,-1)})}v(ee,te)};E(ue,ee=>{n(Oe)&&ee(Q)})}N((ee,te)=>{$e(kt,1,`vw-text-section ${n(be).status==="stale"?"vw-text-section-stale":""}`,"svelte-1l2nqwu"),$e(ct,1,`vw-status-pill ${ee??""}`,"svelte-1l2nqwu"),P(Ot,te)},[()=>ie(n(be).status),()=>A(n(be).status)]),v(nt,kt)}),N(()=>P(Zt,`본문 ${n(p).sectionCount??""}개`)),v(Ht,Fe)};E(Hr,Ht=>{var Fe,yr;((yr=(Fe=n(p))==null?void 0:Fe.sections)==null?void 0:yr.length)>0&&Ht(Lt)})}var tn=m(Hr,2);{var Tn=Ht=>{var Fe=cm();v(Ht,Fe)};E(tn,Ht=>{n(st).length>0&&Ht(Tn)})}var rn=m(tn,2);Pe(rn,17,()=>n(st),Ie,(Ht,Fe)=>{var yr=Ce(),va=Z(yr);{var In=Zt=>{const yt=q(()=>{var Te;return((Te=n(Fe).data)==null?void 0:Te.columns)||[]}),dr=q(()=>{var Te;return((Te=n(Fe).data)==null?void 0:Te.rows)||[]}),Yt=q(()=>n(Fe).meta||{}),cr=q(()=>n(Yt).scaleDivisor||1);var kr=mm(),Cr=Z(kr);{var Lr=Te=>{var tt=um(),ct=d(tt);N(()=>P(ct,`(단위: ${n(Yt).scale??""})`)),v(Te,tt)};E(Cr,Te=>{n(Yt).scale&&Te(Lr)})}var nt=m(Cr,2),be=d(nt),Oe=d(be),at=d(Oe),kt=d(at);Pe(kt,21,()=>n(yt),Ie,(Te,tt,ct)=>{const Ot=q(()=>/^\d{4}/.test(n(tt)));var g=fm(),O=d(g);N(()=>{$e(g,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(Ot)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${ct===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),P(O,n(tt))}),v(Te,g)});var ur=m(at);Pe(ur,21,()=>n(dr),Ie,(Te,tt,ct)=>{var Ot=pm();$e(Ot,1,`hover:bg-white/[0.03] ${ct%2===1?"bg-white/[0.012]":""}`),Pe(Ot,21,()=>n(yt),Ie,(g,O,ce)=>{const we=q(()=>n(tt)[n(O)]??""),_e=q(()=>le(n(we))),Ne=q(()=>Et(n(we))),he=q(()=>n(_e)?_t(n(we),n(cr)):n(we));var Tt=vm(),qt=d(Tt);N(()=>{$e(Tt,1,`px-3 py-1.5 border-b border-white/[0.025]
																	${n(_e)?"text-right tabular-nums font-mono text-[11.5px]":"whitespace-nowrap"}
																	${n(Ne)?"text-red-400/60":n(_e)?"text-dl-text/90":""}
																	${ce===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]":"text-dl-text-muted"}
																	${ce===0&&ct%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),P(qt,n(he))}),v(g,Tt)}),v(Te,Ot)}),v(Zt,kr)},pa=Zt=>{const yt=q(()=>{var Te;return((Te=n(Fe).data)==null?void 0:Te.columns)||[]}),dr=q(()=>{var Te;return((Te=n(Fe).data)==null?void 0:Te.rows)||[]}),Yt=q(()=>n(Fe).meta||{}),cr=q(()=>n(Yt).scaleDivisor||1);var kr=_m(),Cr=Z(kr);{var Lr=Te=>{var tt=hm(),ct=d(tt);N(()=>P(ct,`(단위: ${n(Yt).scale??""})`)),v(Te,tt)};E(Cr,Te=>{n(Yt).scale&&Te(Lr)})}var nt=m(Cr,2),be=d(nt),Oe=d(be),at=d(Oe),kt=d(at);Pe(kt,21,()=>n(yt),Ie,(Te,tt,ct)=>{const Ot=q(()=>/^\d{4}/.test(n(tt)));var g=gm(),O=d(g);N(()=>{$e(g,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(Ot)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${ct===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),P(O,n(tt))}),v(Te,g)});var ur=m(at);Pe(ur,21,()=>n(dr),Ie,(Te,tt,ct)=>{var Ot=bm();$e(Ot,1,`hover:bg-white/[0.03] ${ct%2===1?"bg-white/[0.012]":""}`),Pe(Ot,21,()=>n(yt),Ie,(g,O,ce)=>{const we=q(()=>n(tt)[n(O)]??""),_e=q(()=>le(n(we))),Ne=q(()=>Et(n(we))),he=q(()=>n(_e)?n(cr)>1?_t(n(we),n(cr)):Gt(n(we)):n(we));var Tt=xm(),qt=d(Tt);N(()=>{$e(Tt,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(_e)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(Ne)?"text-red-400/60":n(_e)?"text-dl-text/90":""}
																	${ce===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${ce===0&&ct%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),P(qt,n(he))}),v(g,Tt)}),v(Te,Ot)}),v(Zt,kr)},mn=Zt=>{const yt=q(()=>ft(Object.keys(n(Fe).rawMarkdown))),dr=q(()=>n(k).get(n(Fe).block)??0),Yt=q(()=>n(yt)[n(dr)]||n(yt)[0]);var cr=Cm(),kr=d(cr);{var Cr=Oe=>{var at=km(),kt=d(at);Pe(kt,17,()=>n(yt).slice(0,8),Ie,(tt,ct,Ot)=>{var g=wm(),O=d(g);N(()=>{$e(g,1,`px-2 py-0.5 rounded text-[10px] transition-colors
															${Ot===n(dr)?"bg-white/[0.08] text-dl-text font-medium":"text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]"}`),P(O,n(ct))}),se("click",g,()=>Y(n(Fe).block,Ot)),v(tt,g)});var ur=m(kt,2);{var Te=tt=>{var ct=ym(),Ot=d(ct);N(()=>P(Ot,`외 ${n(yt).length-8}개`)),v(tt,ct)};E(ur,tt=>{n(yt).length>8&&tt(Te)})}v(Oe,at)};E(kr,Oe=>{n(yt).length>1&&Oe(Cr)})}var Lr=m(kr,2),nt=d(Lr),be=d(nt);aa(be,()=>Za(n(Fe).rawMarkdown[n(Yt)])),v(Zt,cr)},or=Zt=>{const yt=q(()=>{var at;return((at=n(Fe).data)==null?void 0:at.columns)||[]}),dr=q(()=>{var at;return((at=n(Fe).data)==null?void 0:at.rows)||[]});var Yt=zm(),cr=d(Yt),kr=d(cr);Pi(kr,{size:12,class:"text-emerald-400/50"});var Cr=m(cr,2),Lr=d(Cr),nt=d(Lr),be=d(nt);Pe(be,21,()=>n(yt),Ie,(at,kt,ur)=>{const Te=q(()=>/^\d{4}/.test(n(kt)));var tt=Sm(),ct=d(tt);N(()=>{$e(tt,1,`px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															${n(Te)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
															${ur===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),P(ct,n(kt))}),v(at,tt)});var Oe=m(nt);Pe(Oe,21,()=>n(dr),Ie,(at,kt,ur)=>{var Te=Em();$e(Te,1,`hover:bg-white/[0.03] ${ur%2===1?"bg-white/[0.012]":""}`),Pe(Te,21,()=>n(yt),Ie,(tt,ct,Ot)=>{const g=q(()=>n(kt)[n(ct)]??""),O=q(()=>le(n(g))),ce=q(()=>Et(n(g)));var we=Mm(),_e=d(we);N(Ne=>{$e(we,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(O)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(ce)?"text-red-400/60":n(O)?"text-dl-text/90":""}
																	${Ot===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Ot===0&&ur%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),P(_e,Ne)},[()=>n(O)?Gt(n(g)):n(g)]),v(tt,we)}),v(at,Te)}),v(Zt,Yt)},$a=Zt=>{const yt=q(()=>n(Fe).data.columns),dr=q(()=>n(Fe).data.rows||[]);var Yt=Pm(),cr=d(Yt),kr=d(cr),Cr=d(kr),Lr=d(Cr);Pe(Lr,21,()=>n(yt),Ie,(be,Oe)=>{var at=Am(),kt=d(at);N(()=>P(kt,n(Oe))),v(be,at)});var nt=m(Cr);Pe(nt,21,()=>n(dr),Ie,(be,Oe,at)=>{var kt=Im();$e(kt,1,`hover:bg-white/[0.03] ${at%2===1?"bg-white/[0.012]":""}`),Pe(kt,21,()=>n(yt),Ie,(ur,Te)=>{var tt=Tm(),ct=d(tt);N(()=>P(ct,n(Oe)[n(Te)]??"")),v(ur,tt)}),v(be,kt)}),v(Zt,Yt)};E(va,Zt=>{var yt,dr;n(Fe).kind==="finance"?Zt(In):n(Fe).kind==="structured"?Zt(pa,1):n(Fe).kind==="raw_markdown"&&n(Fe).rawMarkdown?Zt(mn,2):n(Fe).kind==="report"?Zt(or,3):((dr=(yt=n(Fe).data)==null?void 0:yt.columns)==null?void 0:dr.length)>0&&Zt($a,4)})}v(Ht,yr)}),v(qe,mt)};E(dt,qe=>{n(b)?qe(Ye):qe(xt,-1)})}N(qe=>{P(Ve,qe),qn(et,"title",n(I)?"목차 표시":"전체화면")},[()=>j(n(l))]),se("click",et,()=>u(I,!n(I))),v(Ze,Kt)};E(je,Ze=>{n(l)?Ze(wr,-1):Ze(Ke)})}v(_,R)},zt=_=>{var R=Om(),L=d(R);jn(L,{size:36,strokeWidth:1,class:"opacity-20"}),v(_,R)};E(_r,_=>{var R;n(o)?_(Vt):(R=n(s))!=null&&R.rows?_(gt,1):_(zt,-1)})}v(e,vt),en()}Bn(["click"]);var jm=h('<span class="text-[12px] font-semibold text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim"> </span>',1),Vm=h('<span class="text-[12px] font-semibold text-dl-text"> </span>'),qm=h('<span class="text-[12px] font-semibold text-dl-text">데이터</span>'),Fm=h('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" title="Excel 다운로드"><!></button> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button>',1),Bm=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Gm=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed"> </pre>'),Hm=h('<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2"> </div>'),Um=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Wm=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),Km=h("<!> <!>",1),Ym=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),Xm=h('<div class="p-4"><!></div>'),Jm=h('<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">표시할 내용이 없습니다</div>'),Qm=h('<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark"><div class="flex items-center justify-between h-10 mt-8 px-4 border-b border-dl-border/40 flex-shrink-0"><div class="flex items-center gap-2 min-w-0"><!></div> <div class="flex items-center gap-1"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 overflow-auto min-h-0"><!></div></div>');function Zm(e,t){Zr(t,!0);let r=ot(t,"mode",3,null),a=ot(t,"company",3,null),s=ot(t,"data",3,null),o=ot(t,"onTopicChange",3,null),i=ot(t,"onFullscreen",3,null),l=ot(t,"isFullscreen",3,!1),c=B(!1);async function f(){var A;if(!(!((A=a())!=null&&A.stockCode)||n(c))){u(c,!0);try{await Du(a().stockCode)}catch(ie){console.error("Excel download error:",ie)}u(c,!1)}}function p(A){return A?/^\|.+\|$/m.test(A)||/^#{1,3} /m.test(A)||/\*\*[^*]+\*\*/m.test(A)||/```/.test(A):!1}var b=Qm(),w=d(b),z=d(w),y=d(z);{var I=A=>{var ie=jm(),ve=Z(ie),ke=d(ve),pe=m(ve,2),Ee=d(pe);N(()=>{P(ke,a().corpName||a().company),P(Ee,a().stockCode)}),v(A,ie)},k=A=>{var ie=Vm(),ve=d(ie);N(()=>P(ve,s().label)),v(A,ie)},C=A=>{var ie=qm();v(A,ie)};E(y,A=>{var ie;r()==="viewer"&&a()?A(I):r()==="data"&&((ie=s())!=null&&ie.label)?A(k,1):r()==="data"&&A(C,2)})}var D=m(z,2),W=d(D);{var S=A=>{var ie=Fm(),ve=Z(ie),ke=d(ve);{var pe=me=>{cn(me,{size:14,class:"animate-spin"})},Ee=me=>{_s(me,{size:14})};E(ke,me=>{n(c)?me(pe):me(Ee,-1)})}var ge=m(ve,2),xe=d(ge);{var G=me=>{sd(me,{size:14})},ut=me=>{ad(me,{size:14})};E(xe,me=>{l()?me(G):me(ut,-1)})}N(()=>{ve.disabled=n(c),qn(ge,"title",l()?"패널 모드로":"전체 화면")}),se("click",ve,f),se("click",ge,()=>{var me;return(me=i())==null?void 0:me()}),v(A,ie)};E(W,A=>{var ie;r()==="viewer"&&((ie=a())!=null&&ie.stockCode)&&A(S)})}var j=m(W,2),de=d(j);qs(de,{size:15});var $=m(w,2),x=d($);{var H=A=>{Dm(A,{get stockCode(){return a().stockCode},get onTopicChange(){return o()}})},ne=A=>{var ie=Xm(),ve=d(ie);{var ke=ge=>{var xe=Ce(),G=Z(xe);{var ut=re=>{var K=Bm(),U=d(K);aa(U,()=>Za(s())),v(re,K)},me=q(()=>p(s())),T=re=>{var K=Gm(),U=d(K);N(()=>P(U,s())),v(re,K)};E(G,re=>{n(me)?re(ut):re(T,-1)})}v(ge,xe)},pe=ge=>{var xe=Km(),G=Z(xe);{var ut=U=>{var F=Hm(),Qe=d(F);N(()=>P(Qe,s().module)),v(U,F)};E(G,U=>{s().module&&U(ut)})}var me=m(G,2);{var T=U=>{var F=Um(),Qe=d(F);aa(Qe,()=>Za(s().text)),v(U,F)},re=q(()=>p(s().text)),K=U=>{var F=Wm(),Qe=d(F);N(()=>P(Qe,s().text)),v(U,F)};E(me,U=>{n(re)?U(T):U(K,-1)})}v(ge,xe)},Ee=ge=>{var xe=Ym(),G=d(xe);N(ut=>P(G,ut),[()=>JSON.stringify(s(),null,2)]),v(ge,xe)};E(ve,ge=>{var xe;typeof s()=="string"?ge(ke):(xe=s())!=null&&xe.text?ge(pe,1):ge(Ee,-1)})}v(A,ie)},Y=A=>{var ie=Jm();v(A,ie)};E(x,A=>{r()==="viewer"&&a()?A(H):r()==="data"&&s()?A(ne,1):A(Y,-1)})}se("click",j,()=>{var A;return(A=t.onClose)==null?void 0:A.call(t)}),v(e,b),en()}Bn(["click"]);var eh=h('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),th=h("<!> <span>확인 중...</span>",1),rh=h("<!> <span>설정 필요</span>",1),nh=h('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),ah=h('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!>',1),sh=h('<div class="flex-shrink-0 border-l border-dl-border/30 transition-all duration-300"><!></div>'),oh=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),ih=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),lh=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),dh=h('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),ch=h('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),uh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),fh=h('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),vh=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),ph=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),mh=h('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),hh=h('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),gh=h('<div class="text-[10px] text-dl-text-dim mt-2"> </div>'),xh=h('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex login</div></div></div></div> <!> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),bh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2"> </div></div>'),_h=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 계정 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),wh=h('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),yh=h("<button> <!></button>"),kh=h('<div class="flex flex-wrap gap-1.5"></div>'),Ch=h('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),Sh=h('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),Mh=h('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),Eh=h('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),zh=h('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),Ah=h('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),Th=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),Ih=h("<!> <!> <!> <!> <!> <!>",1),Ph=h('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),Nh=h('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),$h=h('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),Lh=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><span class="text-[10px] text-dl-text-dim">공시 보기</span> <!></div></button>'),Oh=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div></div> <!>',1),Rh=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div></button>'),Dh=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div></div> <!>',1),jh=h('<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),Vh=h('<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim"><!> <div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div> <div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div></div>'),qh=h('<div class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn" role="presentation"><div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"><div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"/> <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div> <div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim"><span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span></div></div></div>'),Fh=h('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),Bh=h('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-2 left-3 z-20 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="종목 검색 (Ctrl+K)"><!></button> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <button><!> <!></button></div> <div class="flex flex-1 min-h-0"><div class="min-w-0 flex-1 flex flex-col"><!></div> <!></div></div></div>  <!> <!> <!> <!>',1);function Gh(e,t){Zr(t,!0);let r=B(""),a=B(!1),s=B(null),o=B(jt({})),i=B(jt({})),l=B(null),c=B(null),f=B(jt([])),p=B(!1),b=B(0),w=B(!0),z=B(""),y=B(!1),I=B(null),k=B(jt({})),C=B(jt({})),D=B(""),W=B(!1),S=B(null),j=B(""),de=B(!1),$=B(""),x=B(0),H=B(null),ne=B(null),Y=B(null);const A=jf();let ie=B(!1),ve=q(()=>n(ie)?"100%":A.panelMode==="viewer"?"65%":"50%"),ke=B(!1),pe=B(""),Ee=B(jt([])),ge=B(-1),xe=null,G=B(!1);function ut(){u(G,window.innerWidth<=768),n(G)&&(u(p,!1),A.closePanel())}na(()=>(ut(),window.addEventListener("resize",ut),()=>window.removeEventListener("resize",ut))),na(()=>{!n(y)||!n(ne)||requestAnimationFrame(()=>{var g;return(g=n(ne))==null?void 0:g.focus()})}),na(()=>{!n(me)||!n(Y)||requestAnimationFrame(()=>{var g;return(g=n(Y))==null?void 0:g.focus()})});let me=B(null),T=B(""),re=B("error"),K=B(!1);function U(g,O="error",ce=4e3){u(T,g,!0),u(re,O,!0),u(K,!0),setTimeout(()=>{u(K,!1)},ce)}const F=Lf();na(()=>{Et()});let Qe=B(jt({}));function le(g){return g==="chatgpt"?"codex":g}async function Et(){var g,O,ce;u(w,!0);try{const we=await $u();u(o,we.providers||{},!0),u(i,we.ollama||{},!0),u(Qe,we.codex||{},!0),we.version&&u(z,we.version,!0);const _e=le(localStorage.getItem("dartlab-provider")),Ne=localStorage.getItem("dartlab-model");if(_e&&((g=n(o)[_e])!=null&&g.available)){u(l,_e,!0),u(I,_e,!0),await Oa(_e,Ne),await _t(_e);const he=n(k)[_e]||[];Ne&&he.includes(Ne)?u(c,Ne,!0):he.length>0&&(u(c,he[0],!0),localStorage.setItem("dartlab-model",n(c))),u(f,he,!0),u(w,!1);return}if(_e&&n(o)[_e]){u(l,_e,!0),u(I,_e,!0),await _t(_e);const he=n(k)[_e]||[];u(f,he,!0),Ne&&he.includes(Ne)?u(c,Ne,!0):he.length>0&&u(c,he[0],!0),u(w,!1);return}for(const he of["codex","ollama","openai"])if((O=n(o)[he])!=null&&O.available){u(l,he,!0),u(I,he,!0),await Oa(he),await _t(he);const Tt=n(k)[he]||[];u(f,Tt,!0),u(c,((ce=n(o)[he])==null?void 0:ce.model)||(Tt.length>0?Tt[0]:null),!0),n(c)&&localStorage.setItem("dartlab-model",n(c));break}}catch{}u(w,!1)}async function _t(g){g=le(g),u(C,{...n(C),[g]:!0},!0);try{const O=await Lu(g);u(k,{...n(k),[g]:O.models||[]},!0)}catch{u(k,{...n(k),[g]:[]},!0)}u(C,{...n(C),[g]:!1},!0)}async function Gt(g){var ce;g=le(g),u(l,g,!0),u(c,null),u(I,g,!0),localStorage.setItem("dartlab-provider",g),localStorage.removeItem("dartlab-model"),u(D,""),u(S,null);try{await Oa(g)}catch{}await _t(g);const O=n(k)[g]||[];if(u(f,O,!0),O.length>0){u(c,((ce=n(o)[g])==null?void 0:ce.model)||O[0],!0),localStorage.setItem("dartlab-model",n(c));try{await Oa(g,n(c))}catch{}}}async function wt(g){u(c,g,!0),localStorage.setItem("dartlab-model",g);try{await Oa(le(n(l)),g)}catch{}}function sr(g){g=le(g),n(I)===g?u(I,null):(u(I,g,!0),_t(g))}async function ft(){const g=n(D).trim();if(!(!g||!n(l))){u(W,!0),u(S,null);try{const O=await Oa(le(n(l)),n(c),g);O.available?(u(S,"success"),n(o)[n(l)]={...n(o)[n(l)],available:!0,model:O.model},!n(c)&&O.model&&u(c,O.model,!0),await _t(n(l)),u(f,n(k)[n(l)]||[],!0),U("API 키 인증 성공","success")):u(S,"error")}catch{u(S,"error")}u(W,!1)}}async function st(){try{await Ru(),n(l)==="codex"&&u(o,{...n(o),codex:{...n(o).codex,available:!1}},!0),U("Codex 계정 로그아웃 완료","success"),await Et()}catch{U("로그아웃 실패")}}function vt(){const g=n(j).trim();!g||n(de)||(u(de,!0),u($,"준비 중..."),u(x,0),u(H,Ou(g,{onProgress(O){O.total&&O.completed!==void 0?(u(x,Math.round(O.completed/O.total*100),!0),u($,`다운로드 중... ${n(x)}%`)):O.status&&u($,O.status,!0)},async onDone(){u(de,!1),u(H,null),u(j,""),u($,""),u(x,0),U(`${g} 다운로드 완료`,"success"),await _t("ollama"),u(f,n(k).ollama||[],!0),n(f).includes(g)&&await wt(g)},onError(O){u(de,!1),u(H,null),u($,""),u(x,0),U(`다운로드 실패: ${O}`)}}),!0))}function _r(){n(H)&&(n(H).abort(),u(H,null)),u(de,!1),u(j,""),u($,""),u(x,0)}function Vt(){u(p,!n(p))}function gt(g){A.openData(g)}function zt(g,O=null){A.openEvidence(g,O)}function _(g){A.openViewer(g)}function R(){if(u(D,""),u(S,null),n(l))u(I,n(l),!0);else{const g=Object.keys(n(o));u(I,g.length>0?g[0]:null,!0)}u(y,!0),n(I)&&_t(n(I))}function L(g){var O,ce,we,_e;if(g)for(let Ne=g.messages.length-1;Ne>=0;Ne--){const he=g.messages[Ne];if(he.role==="assistant"&&((O=he.meta)!=null&&O.stockCode||(ce=he.meta)!=null&&ce.company||he.company)){A.syncCompanyFromMessage({company:((we=he.meta)==null?void 0:we.company)||he.company,stockCode:(_e=he.meta)==null?void 0:_e.stockCode},A.selectedCompany);return}}}function X(){F.createConversation(),u(r,""),u(a,!1),n(s)&&(n(s).abort(),u(s,null))}function V(g){F.setActive(g),L(F.active),u(r,""),u(a,!1),n(s)&&(n(s).abort(),u(s,null))}function je(g){u(me,g,!0)}function Ke(){n(me)&&(F.deleteConversation(n(me)),u(me,null))}function wr(){var O;const g=F.active;if(!g)return null;for(let ce=g.messages.length-1;ce>=0;ce--){const we=g.messages[ce];if(we.role==="assistant"&&((O=we.meta)!=null&&O.stockCode))return we.meta.stockCode}return null}async function Ze(g=null){var hn,Gn,Nn;const O=(g??n(r)).trim();if(!O||n(a))return;if(!n(l)||!((hn=n(o)[n(l)])!=null&&hn.available)){U("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),R();return}F.activeId||F.createConversation();const ce=F.activeId;F.addMessage("user",O),u(r,""),u(a,!0),F.addMessage("assistant",""),F.updateLastMessage({loading:!0,startedAt:Date.now()}),gs(b);const we=F.active,_e=[];let Ne=null;if(we){const Se=we.messages.slice(0,-2);for(const ue of Se)if((ue.role==="user"||ue.role==="assistant")&&ue.text&&ue.text.trim()&&!ue.error&&!ue.loading){const Q={role:ue.role,text:ue.text};ue.role==="assistant"&&((Gn=ue.meta)!=null&&Gn.stockCode)&&(Q.meta={company:ue.meta.company||ue.company,stockCode:ue.meta.stockCode,modules:ue.meta.includedModules||null,market:ue.meta.market||null,topic:ue.meta.topic||null,topicLabel:ue.meta.topicLabel||null,dialogueMode:ue.meta.dialogueMode||null,questionTypes:ue.meta.questionTypes||null,userGoal:ue.meta.userGoal||null},Ne=ue.meta.stockCode),_e.push(Q)}}const he=((Nn=A.selectedCompany)==null?void 0:Nn.stockCode)||Ne||wr(),Tt=A.getViewContext();function qt(){return F.activeId!==ce}const Pn=qu(he,O,{provider:n(l),model:n(c),viewContext:Tt},{onMeta(Se){var fe;if(qt())return;const ue=F.active,Q=ue==null?void 0:ue.messages[ue.messages.length-1],te={meta:{...(Q==null?void 0:Q.meta)||{},...Se}};Se.company&&(te.company=Se.company,F.activeId&&((fe=F.active)==null?void 0:fe.title)==="새 대화"&&F.updateTitle(F.activeId,Se.company)),Se.stockCode&&(te.stockCode=Se.stockCode),(Se.company||Se.stockCode)&&A.syncCompanyFromMessage(Se,A.selectedCompany),F.updateLastMessage(te)},onSnapshot(Se){qt()||F.updateLastMessage({snapshot:Se})},onContext(Se){if(qt())return;const ue=F.active;if(!ue)return;const Q=ue.messages[ue.messages.length-1],ee=(Q==null?void 0:Q.contexts)||[];F.updateLastMessage({contexts:[...ee,{module:Se.module,label:Se.label,text:Se.text}]})},onSystemPrompt(Se){qt()||F.updateLastMessage({systemPrompt:Se.text,userContent:Se.userContent||null})},onToolCall(Se){if(qt())return;const ue=F.active;if(!ue)return;const Q=ue.messages[ue.messages.length-1],ee=(Q==null?void 0:Q.toolEvents)||[];F.updateLastMessage({toolEvents:[...ee,{type:"call",name:Se.name,arguments:Se.arguments}]})},onToolResult(Se){if(qt())return;const ue=F.active;if(!ue)return;const Q=ue.messages[ue.messages.length-1],ee=(Q==null?void 0:Q.toolEvents)||[];F.updateLastMessage({toolEvents:[...ee,{type:"result",name:Se.name,result:Se.result}]})},onChunk(Se){if(qt())return;const ue=F.active;if(!ue)return;const Q=ue.messages[ue.messages.length-1];F.updateLastMessage({text:((Q==null?void 0:Q.text)||"")+Se}),gs(b)},onDone(){if(qt())return;const Se=F.active,ue=Se==null?void 0:Se.messages[Se.messages.length-1],Q=ue!=null&&ue.startedAt?((Date.now()-ue.startedAt)/1e3).toFixed(1):null;F.updateLastMessage({loading:!1,duration:Q}),F.flush(),u(a,!1),u(s,null),gs(b)},onError(Se,ue,Q){qt()||(F.updateLastMessage({text:`오류: ${Se}`,loading:!1,error:!0}),F.flush(),ue==="login"?(U(`${Se} — 설정에서 Codex 로그인을 확인하세요`),R()):ue==="install"?(U(`${Se} — 설정에서 Codex 설치 안내를 확인하세요`),R()):U(Se),u(a,!1),u(s,null))}},_e);u(s,Pn,!0)}function Kt(){n(s)&&(n(s).abort(),u(s,null),u(a,!1),F.updateLastMessage({loading:!1}),F.flush())}function Jt(){const g=F.active;if(!g||g.messages.length<2)return;let O="";for(let ce=g.messages.length-1;ce>=0;ce--)if(g.messages[ce].role==="user"){O=g.messages[ce].text;break}O&&(F.removeLastMessage(),F.removeLastMessage(),u(r,O,!0),requestAnimationFrame(()=>{Ze()}))}function Gr(){const g=F.active;if(!g)return;let O=`# ${g.title}

`;for(const Ne of g.messages)Ne.role==="user"?O+=`## You

${Ne.text}

`:Ne.role==="assistant"&&Ne.text&&(O+=`## DartLab

${Ne.text}

`);const ce=new Blob([O],{type:"text/markdown;charset=utf-8"}),we=URL.createObjectURL(ce),_e=document.createElement("a");_e.href=we,_e.download=`${g.title||"dartlab-chat"}.md`,_e.click(),URL.revokeObjectURL(we),U("대화가 마크다운으로 내보내졌습니다","success")}function ze(){u(ke,!0),u(pe,""),u(Ee,[],!0),u(ge,-1)}function Ae(g){(g.metaKey||g.ctrlKey)&&g.key==="n"&&(g.preventDefault(),X()),(g.metaKey||g.ctrlKey)&&g.key==="k"&&(g.preventDefault(),ze()),(g.metaKey||g.ctrlKey)&&g.shiftKey&&g.key==="S"&&(g.preventDefault(),Vt()),g.key==="Escape"&&n(ke)?u(ke,!1):g.key==="Escape"&&n(y)?u(y,!1):g.key==="Escape"&&n(me)?u(me,null):g.key==="Escape"&&A.panelOpen&&A.closePanel()}let lt=q(()=>{var g;return((g=F.active)==null?void 0:g.messages)||[]}),Me=q(()=>F.active&&F.active.messages.length>0),Ve=q(()=>{var g;return!n(w)&&(!n(l)||!((g=n(o)[n(l)])!=null&&g.available))});const et=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var pt=Bh();Da("keydown",yo,Ae);var J=Z(pt),Le=d(J);{var dt=g=>{var O=eh();se("click",O,()=>{u(p,!1)}),v(g,O)};E(Le,g=>{n(G)&&n(p)&&g(dt)})}var Ye=m(Le,2),xt=d(Ye);{let g=q(()=>n(G)?!0:n(p));wv(xt,{get conversations(){return F.conversations},get activeId(){return F.activeId},get open(){return n(g)},get version(){return n(z)},onNewChat:()=>{X(),n(G)&&u(p,!1)},onSelect:O=>{V(O),n(G)&&u(p,!1)},onDelete:je,onOpenSearch:ze})}var qe=m(Ye,2),mt=d(qe),At=d(mt),Qt=d(At);{var Hr=g=>{sv(g,{size:18})},Lt=g=>{av(g,{size:18})};E(Qt,g=>{n(p)?g(Hr):g(Lt,-1)})}var tn=m(mt,2),Tn=d(tn),rn=d(Tn);ws(rn,{size:14});var Ht=m(Tn,2),Fe=d(Ht);jn(Fe,{size:14});var yr=m(Ht,2),va=d(yr);rv(va,{size:14});var In=m(yr,2),pa=d(In);ev(pa,{size:14});var mn=m(In,2),or=d(mn);{var $a=g=>{var O=th(),ce=Z(O);cn(ce,{size:12,class:"animate-spin"}),v(g,O)},Zt=g=>{var O=rh(),ce=Z(O);fs(ce,{size:12}),v(g,O)},yt=g=>{var O=ah(),ce=m(Z(O),2),we=d(ce),_e=m(ce,2);{var Ne=he=>{var Tt=nh(),qt=m(Z(Tt),2),Pn=d(qt);N(()=>P(Pn,n(c))),v(he,Tt)};E(_e,he=>{n(c)&&he(Ne)})}N(()=>P(we,n(l))),v(g,O)};E(or,g=>{n(w)?g($a):n(Ve)?g(Zt,1):g(yt,-1)})}var dr=m(or,2);iv(dr,{size:12});var Yt=m(tn,2),cr=d(Yt),kr=d(cr);{var Cr=g=>{Sp(g,{get messages(){return n(lt)},get isLoading(){return n(a)},get scrollTrigger(){return n(b)},get selectedCompany(){return A.selectedCompany},onSend:Ze,onStop:Kt,onRegenerate:Jt,onExport:Gr,onOpenData:gt,onOpenEvidence:zt,onCompanySelect:_,get inputText(){return n(r)},set inputText(O){u(r,O,!0)}})},Lr=g=>{Tv(g,{onSend:Ze,onCompanySelect:_,get inputText(){return n(r)},set inputText(O){u(r,O,!0)}})};E(kr,g=>{n(Me)?g(Cr):g(Lr,-1)})}var nt=m(cr,2);{var be=g=>{var O=sh(),ce=d(O);Zm(ce,{get mode(){return A.panelMode},get company(){return A.selectedCompany},get data(){return A.panelData},onClose:()=>{u(ie,!1),A.closePanel()},onTopicChange:(we,_e)=>A.setViewerTopic(we,_e),onFullscreen:()=>{u(ie,!n(ie))},get isFullscreen(){return n(ie)}}),N(()=>zo(O,`width: ${n(ve)??""}; min-width: 360px; ${n(ie)?"":"max-width: 75vw;"}`)),v(g,O)};E(nt,g=>{!n(G)&&A.panelOpen&&g(be)})}var Oe=m(J,2);{var at=g=>{var O=Nh(),ce=d(O),we=d(ce),_e=d(we),Ne=m(d(_e),2),he=d(Ne);qs(he,{size:18});var Tt=m(we,2),qt=d(Tt);Pe(qt,21,()=>Object.entries(n(o)),Ie,(Q,ee)=>{var te=q(()=>Bi(n(ee),2));let fe=()=>n(te)[0],ye=()=>n(te)[1];const Ct=q(()=>fe()===n(l)),ht=q(()=>n(I)===fe()),bt=q(()=>ye().auth==="api_key"),Ft=q(()=>ye().auth==="cli"),It=q(()=>n(k)[fe()]||[]),Rt=q(()=>n(C)[fe()]);var Ut=Ph(),Or=d(Ut),St=d(Or),fr=m(St,2),er=d(fr),Dt=d(er),tr=d(Dt),$n=m(Dt,2);{var id=Bt=>{var Mr=oh();v(Bt,Mr)};E($n,Bt=>{n(Ct)&&Bt(id)})}var ld=m(er,2),dd=d(ld),cd=m(fr,2),ud=d(cd);{var fd=Bt=>{bs(Bt,{size:16,class:"text-dl-success"})},vd=Bt=>{var Mr=ih(),Hn=Z(Mr);$i(Hn,{size:14,class:"text-amber-400"}),v(Bt,Mr)},pd=Bt=>{var Mr=lh(),Hn=Z(Mr);fs(Hn,{size:14,class:"text-amber-400"}),v(Bt,Mr)},md=Bt=>{var Mr=dh(),Hn=Z(Mr);dv(Hn,{size:14,class:"text-dl-text-dim"}),v(Bt,Mr)};E(ud,Bt=>{ye().available?Bt(fd):n(bt)?Bt(vd,1):n(Ft)&&fe()==="codex"&&n(Qe).installed?Bt(pd,2):n(Ft)&&!ye().available&&Bt(md,3)})}var hd=m(Or,2);{var gd=Bt=>{var Mr=Ih(),Hn=Z(Mr);{var xd=Mt=>{var Xt=uh(),vr=d(Xt),Er=d(vr),Ur=m(vr,2),Sr=d(Ur),Rr=m(Sr,2),Un=d(Rr);{var Wn=it=>{cn(it,{size:12,class:"animate-spin"})},Dr=it=>{$i(it,{size:12})};E(Un,it=>{n(W)?it(Wn):it(Dr,-1)})}var nn=m(Ur,2);{var $t=it=>{var jr=ch(),pr=d(jr);fs(pr,{size:12}),v(it,jr)};E(nn,it=>{n(S)==="error"&&it($t)})}N(it=>{P(Er,ye().envKey?`환경변수 ${ye().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),qn(Sr,"placeholder",fe()==="openai"?"sk-...":fe()==="claude"?"sk-ant-...":"API Key"),Rr.disabled=it},[()=>!n(D).trim()||n(W)]),se("keydown",Sr,it=>{it.key==="Enter"&&ft()}),Ra(Sr,()=>n(D),it=>u(D,it)),se("click",Rr,ft),v(Mt,Xt)};E(Hn,Mt=>{n(bt)&&!ye().available&&Mt(xd)})}var Yo=m(Hn,2);{var bd=Mt=>{var Xt=vh(),vr=d(Xt),Er=d(vr);bs(Er,{size:13,class:"text-dl-success"});var Ur=m(vr,2),Sr=d(Ur),Rr=m(Sr,2);{var Un=Dr=>{var nn=fh(),$t=d(nn);{var it=pr=>{cn(pr,{size:10,class:"animate-spin"})},jr=pr=>{var gn=Qn("변경");v(pr,gn)};E($t,pr=>{n(W)?pr(it):pr(jr,-1)})}N(()=>nn.disabled=n(W)),se("click",nn,ft),v(Dr,nn)},Wn=q(()=>n(D).trim());E(Rr,Dr=>{n(Wn)&&Dr(Un)})}se("keydown",Sr,Dr=>{Dr.key==="Enter"&&ft()}),Ra(Sr,()=>n(D),Dr=>u(D,Dr)),v(Mt,Xt)};E(Yo,Mt=>{n(bt)&&ye().available&&Mt(bd)})}var Xo=m(Yo,2);{var _d=Mt=>{var Xt=ph(),vr=m(d(Xt),2),Er=d(vr);_s(Er,{size:14});var Ur=m(Er,2);Ni(Ur,{size:10,class:"ml-auto"}),v(Mt,Xt)},wd=Mt=>{var Xt=mh(),vr=d(Xt),Er=d(vr);fs(Er,{size:14}),v(Mt,Xt)};E(Xo,Mt=>{fe()==="ollama"&&!n(i).installed?Mt(_d):fe()==="ollama"&&n(i).installed&&!n(i).running&&Mt(wd,1)})}var Jo=m(Xo,2);{var yd=Mt=>{var Xt=bh(),vr=d(Xt);{var Er=Rr=>{var Un=xh(),Wn=Z(Un),Dr=d(Wn),nn=m(Wn,2),$t=d(nn);{var it=Vr=>{var xn=hh();v(Vr,xn)};E($t,Vr=>{n(Qe).installed||Vr(it)})}var jr=m($t,2),pr=d(jr),gn=d(pr),ma=m(nn,2);{var as=Vr=>{var xn=gh(),Kn=d(xn);N(()=>P(Kn,n(Qe).loginStatus)),v(Vr,xn)};E(ma,Vr=>{n(Qe).loginStatus&&Vr(as)})}var ss=m(ma,2),Ar=d(ss);fs(Ar,{size:12,class:"text-amber-400 flex-shrink-0"}),N(()=>{P(Dr,n(Qe).installed?"Codex CLI가 설치되었지만 로그인이 필요합니다":"Codex CLI 설치가 필요합니다"),P(gn,n(Qe).installed?"1.":"2.")}),v(Rr,Un)};E(vr,Rr=>{fe()==="codex"&&Rr(Er)})}var Ur=m(vr,2),Sr=d(Ur);N(()=>P(Sr,n(Qe).installed?"로그인 완료 후 새로고침하세요":"설치 완료 후 새로고침하세요")),v(Mt,Xt)};E(Jo,Mt=>{n(Ft)&&!ye().available&&Mt(yd)})}var Qo=m(Jo,2);{var kd=Mt=>{var Xt=_h(),vr=d(Xt),Er=d(vr),Ur=d(Er);bs(Ur,{size:13,class:"text-dl-success"});var Sr=m(Er,2),Rr=d(Sr);nv(Rr,{size:11}),se("click",Sr,st),v(Mt,Xt)};E(Qo,Mt=>{fe()==="codex"&&ye().available&&Mt(kd)})}var Cd=m(Qo,2);{var Sd=Mt=>{var Xt=Th(),vr=d(Xt),Er=m(d(vr),2);{var Ur=$t=>{cn($t,{size:12,class:"animate-spin text-dl-text-dim"})};E(Er,$t=>{n(Rt)&&$t(Ur)})}var Sr=m(vr,2);{var Rr=$t=>{var it=wh(),jr=d(it);cn(jr,{size:14,class:"animate-spin"}),v($t,it)},Un=$t=>{var it=kh();Pe(it,21,()=>n(It),Ie,(jr,pr)=>{var gn=yh(),ma=d(gn),as=m(ma);{var ss=Ar=>{Yf(Ar,{size:10,class:"inline ml-1"})};E(as,Ar=>{n(pr)===n(c)&&n(Ct)&&Ar(ss)})}N(Ar=>{$e(gn,1,Ar),P(ma,`${n(pr)??""} `)},[()=>Pt(Nt("px-3 py-1.5 rounded-lg text-[11px] border transition-all",n(pr)===n(c)&&n(Ct)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),se("click",gn,()=>{fe()!==n(l)&&Gt(fe()),wt(n(pr))}),v(jr,gn)}),v($t,it)},Wn=$t=>{var it=Ch();v($t,it)};E(Sr,$t=>{n(Rt)&&n(It).length===0?$t(Rr):n(It).length>0?$t(Un,1):$t(Wn,-1)})}var Dr=m(Sr,2);{var nn=$t=>{var it=Ah(),jr=d(it),pr=m(d(jr),2),gn=m(d(pr));Ni(gn,{size:9});var ma=m(jr,2);{var as=Ar=>{var Vr=Sh(),xn=d(Vr),Kn=d(xn),os=d(Kn);cn(os,{size:12,class:"animate-spin text-dl-primary-light"});var Xs=m(Kn,2),Ts=m(xn,2),Ln=d(Ts),an=m(Ts,2),Js=d(an);N(()=>{zo(Ln,`width: ${n(x)??""}%`),P(Js,n($))}),se("click",Xs,_r),v(Ar,Vr)},ss=Ar=>{var Vr=zh(),xn=Z(Vr),Kn=d(xn),os=m(Kn,2),Xs=d(os);_s(Xs,{size:12});var Ts=m(xn,2);Pe(Ts,21,()=>et,Ie,(Ln,an)=>{const Js=q(()=>n(It).some(La=>La===n(an).name||La===n(an).name.split(":")[0]));var Zo=Ce(),Md=Z(Zo);{var Ed=La=>{var Qs=Eh(),ei=d(Qs),ti=d(ei),ri=d(ti),zd=d(ri),ni=m(ri,2),Ad=d(ni),Td=m(ni,2);{var Id=Zs=>{var si=Mh(),Rd=d(si);N(()=>P(Rd,n(an).tag)),v(Zs,si)};E(Td,Zs=>{n(an).tag&&Zs(Id)})}var Pd=m(ti,2),Nd=d(Pd),$d=m(ei,2),ai=d($d),Ld=d(ai),Od=m(ai,2);_s(Od,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),N(()=>{P(zd,n(an).name),P(Ad,n(an).size),P(Nd,n(an).desc),P(Ld,`${n(an).gb??""} GB`)}),se("click",Qs,()=>{u(j,n(an).name,!0),vt()}),v(La,Qs)};E(Md,La=>{n(Js)||La(Ed)})}v(Ln,Zo)}),N(Ln=>os.disabled=Ln,[()=>!n(j).trim()]),se("keydown",Kn,Ln=>{Ln.key==="Enter"&&vt()}),Ra(Kn,()=>n(j),Ln=>u(j,Ln)),se("click",os,vt),v(Ar,Vr)};E(ma,Ar=>{n(de)?Ar(as):Ar(ss,-1)})}v($t,it)};E(Dr,$t=>{fe()==="ollama"&&$t(nn)})}v(Mt,Xt)};E(Cd,Mt=>{(ye().available||n(bt)||n(Ft))&&Mt(Sd)})}v(Bt,Mr)};E(hd,Bt=>{(n(ht)||n(Ct))&&Bt(gd)})}N((Bt,Mr)=>{$e(Ut,1,Bt),$e(St,1,Mr),P(tr,ye().label||fe()),P(dd,ye().desc||"")},[()=>Pt(Nt("rounded-xl border transition-all",n(Ct)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>Pt(Nt("w-2.5 h-2.5 rounded-full flex-shrink-0",ye().available?"bg-dl-success":n(bt)?"bg-amber-400":"bg-dl-text-dim"))]),se("click",Or,()=>{ye().available||n(bt)?fe()===n(l)?sr(fe()):Gt(fe()):sr(fe())}),v(Q,Ut)});var Pn=m(Tt,2),hn=d(Pn),Gn=d(hn);{var Nn=Q=>{var ee=Qn();N(()=>{var te;return P(ee,`현재: ${(((te=n(o)[n(l)])==null?void 0:te.label)||n(l))??""} / ${n(c)??""}`)}),v(Q,ee)},Se=Q=>{var ee=Qn();N(()=>{var te;return P(ee,`현재: ${(((te=n(o)[n(l)])==null?void 0:te.label)||n(l))??""}`)}),v(Q,ee)};E(Gn,Q=>{n(l)&&n(c)?Q(Nn):n(l)&&Q(Se,1)})}var ue=m(hn,2);Qa(ce,Q=>u(ne,Q),()=>n(ne)),se("click",O,Q=>{Q.target===Q.currentTarget&&u(y,!1)}),se("click",Ne,()=>u(y,!1)),se("click",ue,()=>u(y,!1)),v(g,O)};E(Oe,g=>{n(y)&&g(at)})}var kt=m(Oe,2);{var ur=g=>{var O=$h(),ce=d(O),we=m(d(ce),4),_e=d(we),Ne=m(_e,2);Qa(ce,he=>u(Y,he),()=>n(Y)),se("click",O,he=>{he.target===he.currentTarget&&u(me,null)}),se("click",_e,()=>u(me,null)),se("click",Ne,Ke),v(g,O)};E(kt,g=>{n(me)&&g(ur)})}var Te=m(kt,2);{var tt=g=>{const O=q(()=>A.recentCompanies||[]);var ce=qh(),we=d(ce),_e=d(we),Ne=d(_e);ws(Ne,{size:18,class:"text-dl-text-dim flex-shrink-0"});var he=m(Ne,2);hl(he,!0);var Tt=m(_e,2),qt=d(Tt);{var Pn=Q=>{var ee=Oh(),te=m(Z(ee),2);Pe(te,17,()=>n(Ee),Ie,(fe,ye,Ct)=>{var ht=Lh(),bt=d(ht),Ft=d(bt),It=m(bt,2),Rt=d(It),Ut=d(Rt),Or=m(Rt,2),St=d(Or),fr=m(It,2),er=m(d(fr),2);jn(er,{size:14,class:"text-dl-text-dim"}),N((Dt,tr)=>{$e(ht,1,Dt),P(Ft,tr),P(Ut,n(ye).corpName),P(St,`${n(ye).stockCode??""} · ${(n(ye).market||"")??""}${n(ye).sector?` · ${n(ye).sector}`:""}`)},[()=>Pt(Nt("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",Ct===n(ge)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(ye).corpName||"?").charAt(0)]),se("click",ht,()=>{u(ke,!1),u(pe,""),u(Ee,[],!0),u(ge,-1),_(n(ye))}),Da("mouseenter",ht,()=>{u(ge,Ct,!0)}),v(fe,ht)}),v(Q,ee)},hn=Q=>{var ee=Dh(),te=m(Z(ee),2);Pe(te,17,()=>n(O),Ie,(fe,ye,Ct)=>{var ht=Rh(),bt=d(ht),Ft=d(bt),It=m(bt,2),Rt=d(It),Ut=d(Rt),Or=m(Rt,2),St=d(Or);N((fr,er)=>{$e(ht,1,fr),P(Ft,er),P(Ut,n(ye).corpName),P(St,`${n(ye).stockCode??""} · ${(n(ye).market||"")??""}`)},[()=>Pt(Nt("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",Ct===n(ge)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(ye).corpName||"?").charAt(0)]),se("click",ht,()=>{u(ke,!1),u(pe,""),u(ge,-1),_(n(ye))}),Da("mouseenter",ht,()=>{u(ge,Ct,!0)}),v(fe,ht)}),v(Q,ee)},Gn=q(()=>n(pe).trim().length===0&&n(O).length>0),Nn=Q=>{var ee=jh();v(Q,ee)},Se=q(()=>n(pe).trim().length>0),ue=Q=>{var ee=Vh(),te=d(ee);ws(te,{size:24,class:"mb-2 opacity-40"}),v(Q,ee)};E(qt,Q=>{n(Ee).length>0?Q(Pn):n(Gn)?Q(hn,1):n(Se)?Q(Nn,2):Q(ue,-1)})}se("click",ce,Q=>{Q.target===Q.currentTarget&&u(ke,!1)}),se("input",he,()=>{xe&&clearTimeout(xe),n(pe).trim().length>=1?xe=setTimeout(async()=>{var Q;try{const ee=await ql(n(pe).trim());u(Ee,((Q=ee.results)==null?void 0:Q.slice(0,8))||[],!0)}catch{u(Ee,[],!0)}},250):u(Ee,[],!0)}),se("keydown",he,Q=>{const ee=n(Ee).length>0?n(Ee):n(O);if(Q.key==="ArrowDown")Q.preventDefault(),u(ge,Math.min(n(ge)+1,ee.length-1),!0);else if(Q.key==="ArrowUp")Q.preventDefault(),u(ge,Math.max(n(ge)-1,-1),!0);else if(Q.key==="Enter"&&n(ge)>=0&&ee[n(ge)]){Q.preventDefault();const te=ee[n(ge)];u(ke,!1),u(pe,""),u(Ee,[],!0),u(ge,-1),_(te)}else Q.key==="Escape"&&u(ke,!1)}),Ra(he,()=>n(pe),Q=>u(pe,Q)),v(g,ce)};E(Te,g=>{n(ke)&&g(tt)})}var ct=m(Te,2);{var Ot=g=>{var O=Fh(),ce=d(O),we=d(ce),_e=d(we),Ne=m(we,2),he=d(Ne);qs(he,{size:14}),N(Tt=>{$e(ce,1,Tt),P(_e,n(T))},[()=>Pt(Nt("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",n(re)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":n(re)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),se("click",Ne,()=>{u(K,!1)}),v(g,O)};E(ct,g=>{n(K)&&g(Ot)})}N(g=>{$e(Ye,1,Pt(n(G)?n(p)?"sidebar-mobile":"hidden":"")),$e(mn,1,g)},[()=>Pt(Nt("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",n(w)?"text-dl-text-dim":n(Ve)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),se("click",At,Vt),se("click",Tn,ze),se("click",mn,()=>R()),v(e,pt),en()}Bn(["click","keydown","input"]);uu(Gh,{target:document.getElementById("app")});
