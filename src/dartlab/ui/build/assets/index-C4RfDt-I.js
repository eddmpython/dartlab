const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/ChartRenderer-rbWm3w3k.js","assets/ChartRenderer-DW5VYfwI.css"])))=>i.map(i=>d[i]);
var kc=Object.defineProperty;var Ei=e=>{throw TypeError(e)};var $c=(e,t,a)=>t in e?kc(e,t,{enumerable:!0,configurable:!0,writable:!0,value:a}):e[t]=a;var ka=(e,t,a)=>$c(e,typeof t!="symbol"?t+"":t,a),ys=(e,t,a)=>t.has(e)||Ei("Cannot "+a);var X=(e,t,a)=>(ys(e,t,"read from private field"),a?a.call(e):t.get(e)),Rt=(e,t,a)=>t.has(e)?Ei("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,a),It=(e,t,a,n)=>(ys(e,t,"write to private field"),n?n.call(e,a):t.set(e,a),a),Mr=(e,t,a)=>(ys(e,t,"access private method"),a);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const o of document.querySelectorAll('link[rel="modulepreload"]'))n(o);new MutationObserver(o=>{for(const l of o)if(l.type==="childList")for(const s of l.addedNodes)s.tagName==="LINK"&&s.rel==="modulepreload"&&n(s)}).observe(document,{childList:!0,subtree:!0});function a(o){const l={};return o.integrity&&(l.integrity=o.integrity),o.referrerPolicy&&(l.referrerPolicy=o.referrerPolicy),o.crossOrigin==="use-credentials"?l.credentials="include":o.crossOrigin==="anonymous"?l.credentials="omit":l.credentials="same-origin",l}function n(o){if(o.ep)return;o.ep=!0;const l=a(o);fetch(o.href,l)}})();const As=!1;var ni=Array.isArray,Cc=Array.prototype.indexOf,io=Array.prototype.includes,us=Array.from,Sc=Object.defineProperty,fn=Object.getOwnPropertyDescriptor,pl=Object.getOwnPropertyDescriptors,Tc=Object.prototype,Mc=Array.prototype,oi=Object.getPrototypeOf,Ii=Object.isExtensible;function _o(e){return typeof e=="function"}const zc=()=>{};function Ac(e){return typeof(e==null?void 0:e.then)=="function"}function Ec(e){return e()}function Es(e){for(var t=0;t<e.length;t++)e[t]()}function ml(){var e,t,a=new Promise((n,o)=>{e=n,t=o});return{promise:a,resolve:e,reject:t}}function si(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const a=[];for(const n of e)if(a.push(n),a.length===t)break;return a}const Fr=2,fo=4,Bn=8,vs=1<<24,kn=16,Ea=32,Un=64,Is=128,xa=512,Vr=1024,qr=2048,Aa=4096,Jr=8192,qa=16384,po=32768,Za=65536,Pi=1<<17,Ic=1<<18,mo=1<<19,xl=1<<20,ja=1<<25,Fn=65536,Ps=1<<21,ii=1<<22,pn=1<<23,Ba=Symbol("$state"),hl=Symbol("legacy props"),Pc=Symbol(""),En=new class extends Error{constructor(){super(...arguments);ka(this,"name","StaleReactionError");ka(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var ul;const gl=!!((ul=globalThis.document)!=null&&ul.contentType)&&globalThis.document.contentType.includes("xml");function Nc(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function Lc(e,t,a){throw new Error("https://svelte.dev/e/each_key_duplicate")}function Oc(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function Rc(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Dc(e){throw new Error("https://svelte.dev/e/effect_orphan")}function jc(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function Vc(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function qc(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function Bc(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function Fc(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function Hc(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const Uc=1,Kc=2,bl=4,Gc=8,Wc=16,Yc=1,Jc=2,_l=4,Xc=8,Qc=16,wl=1,Zc=2,Ar=Symbol(),yl="http://www.w3.org/1999/xhtml",kl="http://www.w3.org/2000/svg",eu="http://www.w3.org/1998/Math/MathML",tu="@attach";function ru(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function au(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function $l(e){return e===this.v}function nu(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function Cl(e){return!nu(e,this.v)}let Oo=!1,ou=!1;function su(){Oo=!0}let Lr=null;function lo(e){Lr=e}function Cr(e,t=!1,a){Lr={p:Lr,i:!1,c:null,e:null,s:e,x:null,l:Oo&&!t?{s:null,u:null,$:[]}:null}}function Sr(e){var t=Lr,a=t.e;if(a!==null){t.e=null;for(var n of a)Wl(n)}return t.i=!0,Lr=t.p,{}}function xo(){return!Oo||Lr!==null&&Lr.l===null}let In=[];function Sl(){var e=In;In=[],Es(e)}function za(e){if(In.length===0&&!Qn){var t=In;queueMicrotask(()=>{t===In&&Sl()})}In.push(e)}function iu(){for(;In.length>0;)Sl()}function Tl(e){var t=Nt;if(t===null)return Pt.f|=pn,e;if((t.f&po)===0&&(t.f&fo)===0)throw e;vn(e,t)}function vn(e,t){for(;t!==null;){if((t.f&Is)!==0){if((t.f&po)===0)throw e;try{t.b.error(e);return}catch(a){e=a}}t=t.parent}throw e}const lu=-7169;function wr(e,t){e.f=e.f&lu|t}function li(e){(e.f&xa)!==0||e.deps===null?wr(e,Vr):wr(e,Aa)}function Ml(e){if(e!==null)for(const t of e)(t.f&Fr)===0||(t.f&Fn)===0||(t.f^=Fn,Ml(t.deps))}function zl(e,t,a){(e.f&qr)!==0?t.add(e):(e.f&Aa)!==0&&a.add(e),Ml(e.deps),wr(e,Vr)}const Fo=new Set;let Ct=null,Zo=null,jr=null,Zr=[],fs=null,Qn=!1,co=null,du=1;var dn,Zn,On,eo,to,ro,cn,La,ao,ra,Ns,Ls,Os,Rs;const bi=class bi{constructor(){Rt(this,ra);ka(this,"id",du++);ka(this,"current",new Map);ka(this,"previous",new Map);Rt(this,dn,new Set);Rt(this,Zn,new Set);Rt(this,On,0);Rt(this,eo,0);Rt(this,to,null);Rt(this,ro,new Set);Rt(this,cn,new Set);Rt(this,La,new Map);ka(this,"is_fork",!1);Rt(this,ao,!1)}skip_effect(t){X(this,La).has(t)||X(this,La).set(t,{d:[],m:[]})}unskip_effect(t){var a=X(this,La).get(t);if(a){X(this,La).delete(t);for(var n of a.d)wr(n,qr),Va(n);for(n of a.m)wr(n,Aa),Va(n)}}process(t){var o;Zr=[],this.apply();var a=co=[],n=[];for(const l of t)Mr(this,ra,Ls).call(this,l,a,n);if(co=null,Mr(this,ra,Ns).call(this)){Mr(this,ra,Os).call(this,n),Mr(this,ra,Os).call(this,a);for(const[l,s]of X(this,La))Nl(l,s)}else{Zo=this,Ct=null;for(const l of X(this,dn))l(this);X(this,dn).clear(),X(this,On)===0&&Mr(this,ra,Rs).call(this),Ni(n),Ni(a),X(this,ro).clear(),X(this,cn).clear(),Zo=null,(o=X(this,to))==null||o.resolve()}jr=null}capture(t,a){a!==Ar&&!this.previous.has(t)&&this.previous.set(t,a),(t.f&pn)===0&&(this.current.set(t,t.v),jr==null||jr.set(t,t.v))}activate(){Ct=this,this.apply()}deactivate(){Ct===this&&(Ct=null,jr=null)}flush(){var t;if(Zr.length>0)Ct=this,El();else if(X(this,On)===0&&!this.is_fork){for(const a of X(this,dn))a(this);X(this,dn).clear(),Mr(this,ra,Rs).call(this),(t=X(this,to))==null||t.resolve()}this.deactivate()}discard(){for(const t of X(this,Zn))t(this);X(this,Zn).clear()}increment(t){It(this,On,X(this,On)+1),t&&It(this,eo,X(this,eo)+1)}decrement(t){It(this,On,X(this,On)-1),t&&It(this,eo,X(this,eo)-1),!X(this,ao)&&(It(this,ao,!0),za(()=>{It(this,ao,!1),Mr(this,ra,Ns).call(this)?Zr.length>0&&this.flush():this.revive()}))}revive(){for(const t of X(this,ro))X(this,cn).delete(t),wr(t,qr),Va(t);for(const t of X(this,cn))wr(t,Aa),Va(t);this.flush()}oncommit(t){X(this,dn).add(t)}ondiscard(t){X(this,Zn).add(t)}settled(){return(X(this,to)??It(this,to,ml())).promise}static ensure(){if(Ct===null){const t=Ct=new bi;Fo.add(Ct),Qn||za(()=>{Ct===t&&t.flush()})}return Ct}apply(){}};dn=new WeakMap,Zn=new WeakMap,On=new WeakMap,eo=new WeakMap,to=new WeakMap,ro=new WeakMap,cn=new WeakMap,La=new WeakMap,ao=new WeakMap,ra=new WeakSet,Ns=function(){return this.is_fork||X(this,eo)>0},Ls=function(t,a,n){t.f^=Vr;for(var o=t.first;o!==null;){var l=o.f,s=(l&(Ea|Un))!==0,d=s&&(l&Vr)!==0,v=(l&Jr)!==0,m=d||X(this,La).has(o);if(!m&&o.fn!==null){s?v||(o.f^=Vr):(l&fo)!==0?a.push(o):(l&(Bn|vs))!==0&&v?n.push(o):jo(o)&&(uo(o),(l&kn)!==0&&(X(this,cn).add(o),v&&wr(o,qr)));var x=o.first;if(x!==null){o=x;continue}}for(;o!==null;){var h=o.next;if(h!==null){o=h;break}o=o.parent}}},Os=function(t){for(var a=0;a<t.length;a+=1)zl(t[a],X(this,ro),X(this,cn))},Rs=function(){var l;if(Fo.size>1){this.previous.clear();var t=Ct,a=jr,n=!0;for(const s of Fo){if(s===this){n=!1;continue}const d=[];for(const[m,x]of this.current){if(s.current.has(m))if(n&&x!==s.current.get(m))s.current.set(m,x);else continue;d.push(m)}if(d.length===0)continue;const v=[...s.current.keys()].filter(m=>!this.current.has(m));if(v.length>0){var o=Zr;Zr=[];const m=new Set,x=new Map;for(const h of d)Il(h,v,m,x);if(Zr.length>0){Ct=s,s.apply();for(const h of Zr)Mr(l=s,ra,Ls).call(l,h,[],[]);s.deactivate()}Zr=o}}Ct=t,jr=a}X(this,La).clear(),Fo.delete(this)};let Xa=bi;function Al(e){var t=Qn;Qn=!0;try{for(var a;;){if(iu(),Zr.length===0&&(Ct==null||Ct.flush(),Zr.length===0))return fs=null,a;El()}}finally{Qn=t}}function El(){var e=null;try{for(var t=0;Zr.length>0;){var a=Xa.ensure();if(t++>1e3){var n,o;cu()}a.process(Zr),mn.clear()}}finally{Zr=[],fs=null,co=null}}function cu(){try{jc()}catch(e){vn(e,fs)}}let $a=null;function Ni(e){var t=e.length;if(t!==0){for(var a=0;a<t;){var n=e[a++];if((n.f&(qa|Jr))===0&&jo(n)&&($a=new Set,uo(n),n.deps===null&&n.first===null&&n.nodes===null&&n.teardown===null&&n.ac===null&&Ql(n),($a==null?void 0:$a.size)>0)){mn.clear();for(const o of $a){if((o.f&(qa|Jr))!==0)continue;const l=[o];let s=o.parent;for(;s!==null;)$a.has(s)&&($a.delete(s),l.push(s)),s=s.parent;for(let d=l.length-1;d>=0;d--){const v=l[d];(v.f&(qa|Jr))===0&&uo(v)}}$a.clear()}}$a=null}}function Il(e,t,a,n){if(!a.has(e)&&(a.add(e),e.reactions!==null))for(const o of e.reactions){const l=o.f;(l&Fr)!==0?Il(o,t,a,n):(l&(ii|kn))!==0&&(l&qr)===0&&Pl(o,t,n)&&(wr(o,qr),Va(o))}}function Pl(e,t,a){const n=a.get(e);if(n!==void 0)return n;if(e.deps!==null)for(const o of e.deps){if(io.call(t,o))return!0;if((o.f&Fr)!==0&&Pl(o,t,a))return a.set(o,!0),!0}return a.set(e,!1),!1}function Va(e){var t=fs=e,a=t.b;if(a!=null&&a.is_pending&&(e.f&(fo|Bn|vs))!==0&&(e.f&po)===0){a.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var n=t.f;if(co!==null&&t===Nt&&(e.f&Bn)===0)return;if((n&(Un|Ea))!==0){if((n&Vr)===0)return;t.f^=Vr}}Zr.push(t)}function Nl(e,t){if(!((e.f&Ea)!==0&&(e.f&Vr)!==0)){(e.f&qr)!==0?t.d.push(e):(e.f&Aa)!==0&&t.m.push(e),wr(e,Vr);for(var a=e.first;a!==null;)Nl(a,t),a=a.next}}function uu(e){let t=0,a=Ha(0),n;return()=>{vi()&&(r(a),fi(()=>(t===0&&(n=Hn(()=>e(()=>zo(a)))),t+=1,()=>{za(()=>{t-=1,t===0&&(n==null||n(),n=void 0,zo(a))})})))}}var vu=Za|mo;function fu(e,t,a,n){new pu(e,t,a,n)}var pa,ai,Oa,Rn,Qr,Ra,la,Ca,Wa,Dn,un,no,oo,so,Ya,ds,Er,mu,xu,hu,Ds,Wo,Yo,js;class pu{constructor(t,a,n,o){Rt(this,Er);ka(this,"parent");ka(this,"is_pending",!1);ka(this,"transform_error");Rt(this,pa);Rt(this,ai,null);Rt(this,Oa);Rt(this,Rn);Rt(this,Qr);Rt(this,Ra,null);Rt(this,la,null);Rt(this,Ca,null);Rt(this,Wa,null);Rt(this,Dn,0);Rt(this,un,0);Rt(this,no,!1);Rt(this,oo,new Set);Rt(this,so,new Set);Rt(this,Ya,null);Rt(this,ds,uu(()=>(It(this,Ya,Ha(X(this,Dn))),()=>{It(this,Ya,null)})));var l;It(this,pa,t),It(this,Oa,a),It(this,Rn,s=>{var d=Nt;d.b=this,d.f|=Is,n(s)}),this.parent=Nt.b,this.transform_error=o??((l=this.parent)==null?void 0:l.transform_error)??(s=>s),It(this,Qr,Kn(()=>{Mr(this,Er,Ds).call(this)},vu))}defer_effect(t){zl(t,X(this,oo),X(this,so))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!X(this,Oa).pending}update_pending_count(t){Mr(this,Er,js).call(this,t),It(this,Dn,X(this,Dn)+t),!(!X(this,Ya)||X(this,no))&&(It(this,no,!0),za(()=>{It(this,no,!1),X(this,Ya)&&Qa(X(this,Ya),X(this,Dn))}))}get_effect_pending(){return X(this,ds).call(this),r(X(this,Ya))}error(t){var a=X(this,Oa).onerror;let n=X(this,Oa).failed;if(!a&&!n)throw t;X(this,Ra)&&(Br(X(this,Ra)),It(this,Ra,null)),X(this,la)&&(Br(X(this,la)),It(this,la,null)),X(this,Ca)&&(Br(X(this,Ca)),It(this,Ca,null));var o=!1,l=!1;const s=()=>{if(o){au();return}o=!0,l&&Hc(),X(this,Ca)!==null&&Vn(X(this,Ca),()=>{It(this,Ca,null)}),Mr(this,Er,Yo).call(this,()=>{Xa.ensure(),Mr(this,Er,Ds).call(this)})},d=v=>{try{l=!0,a==null||a(v,s),l=!1}catch(m){vn(m,X(this,Qr)&&X(this,Qr).parent)}n&&It(this,Ca,Mr(this,Er,Yo).call(this,()=>{Xa.ensure();try{return ta(()=>{var m=Nt;m.b=this,m.f|=Is,n(X(this,pa),()=>v,()=>s)})}catch(m){return vn(m,X(this,Qr).parent),null}}))};za(()=>{var v;try{v=this.transform_error(t)}catch(m){vn(m,X(this,Qr)&&X(this,Qr).parent);return}v!==null&&typeof v=="object"&&typeof v.then=="function"?v.then(d,m=>vn(m,X(this,Qr)&&X(this,Qr).parent)):d(v)})}}pa=new WeakMap,ai=new WeakMap,Oa=new WeakMap,Rn=new WeakMap,Qr=new WeakMap,Ra=new WeakMap,la=new WeakMap,Ca=new WeakMap,Wa=new WeakMap,Dn=new WeakMap,un=new WeakMap,no=new WeakMap,oo=new WeakMap,so=new WeakMap,Ya=new WeakMap,ds=new WeakMap,Er=new WeakSet,mu=function(){try{It(this,Ra,ta(()=>X(this,Rn).call(this,X(this,pa))))}catch(t){this.error(t)}},xu=function(t){const a=X(this,Oa).failed;a&&It(this,Ca,ta(()=>{a(X(this,pa),()=>t,()=>()=>{})}))},hu=function(){const t=X(this,Oa).pending;t&&(this.is_pending=!0,It(this,la,ta(()=>t(X(this,pa)))),za(()=>{var a=It(this,Wa,document.createDocumentFragment()),n=Fa();a.append(n),It(this,Ra,Mr(this,Er,Yo).call(this,()=>(Xa.ensure(),ta(()=>X(this,Rn).call(this,n))))),X(this,un)===0&&(X(this,pa).before(a),It(this,Wa,null),Vn(X(this,la),()=>{It(this,la,null)}),Mr(this,Er,Wo).call(this))}))},Ds=function(){try{if(this.is_pending=this.has_pending_snippet(),It(this,un,0),It(this,Dn,0),It(this,Ra,ta(()=>{X(this,Rn).call(this,X(this,pa))})),X(this,un)>0){var t=It(this,Wa,document.createDocumentFragment());xi(X(this,Ra),t);const a=X(this,Oa).pending;It(this,la,ta(()=>a(X(this,pa))))}else Mr(this,Er,Wo).call(this)}catch(a){this.error(a)}},Wo=function(){this.is_pending=!1;for(const t of X(this,oo))wr(t,qr),Va(t);for(const t of X(this,so))wr(t,Aa),Va(t);X(this,oo).clear(),X(this,so).clear()},Yo=function(t){var a=Nt,n=Pt,o=Lr;ba(X(this,Qr)),ga(X(this,Qr)),lo(X(this,Qr).ctx);try{return t()}catch(l){return Tl(l),null}finally{ba(a),ga(n),lo(o)}},js=function(t){var a;if(!this.has_pending_snippet()){this.parent&&Mr(a=this.parent,Er,js).call(a,t);return}It(this,un,X(this,un)+t),X(this,un)===0&&(Mr(this,Er,Wo).call(this),X(this,la)&&Vn(X(this,la),()=>{It(this,la,null)}),X(this,Wa)&&(X(this,pa).before(X(this,Wa)),It(this,Wa,null)))};function Ll(e,t,a,n){const o=xo()?Ro:di;var l=e.filter(h=>!h.settled);if(a.length===0&&l.length===0){n(t.map(o));return}var s=Nt,d=Ol(),v=l.length===1?l[0].promise:l.length>1?Promise.all(l.map(h=>h.promise)):null;function m(h){d();try{n(h)}catch(_){(s.f&qa)===0&&vn(_,s)}es()}if(a.length===0){v.then(()=>m(t.map(o)));return}function x(){d(),Promise.all(a.map(h=>bu(h))).then(h=>m([...t.map(o),...h])).catch(h=>vn(h,s))}v?v.then(x):x()}function Ol(){var e=Nt,t=Pt,a=Lr,n=Ct;return function(l=!0){ba(e),ga(t),lo(a),l&&(n==null||n.activate())}}function es(e=!0){ba(null),ga(null),lo(null),e&&(Ct==null||Ct.deactivate())}function gu(){var e=Nt.b,t=Ct,a=e.is_rendered();return e.update_pending_count(1),t.increment(a),()=>{e.update_pending_count(-1),t.decrement(a)}}function Ro(e){var t=Fr|qr,a=Pt!==null&&(Pt.f&Fr)!==0?Pt:null;return Nt!==null&&(Nt.f|=mo),{ctx:Lr,deps:null,effects:null,equals:$l,f:t,fn:e,reactions:null,rv:0,v:Ar,wv:0,parent:a??Nt,ac:null}}function bu(e,t,a){Nt===null&&Nc();var o=void 0,l=Ha(Ar),s=!Pt,d=new Map;return Iu(()=>{var _;var v=ml();o=v.promise;try{Promise.resolve(e()).then(v.resolve,v.reject).finally(es)}catch(M){v.reject(M),es()}var m=Ct;if(s){var x=gu();(_=d.get(m))==null||_.reject(En),d.delete(m),d.set(m,v)}const h=(M,$=void 0)=>{if(m.activate(),$)$!==En&&(l.f|=pn,Qa(l,$));else{(l.f&pn)!==0&&(l.f^=pn),Qa(l,M);for(const[V,T]of d){if(d.delete(V),V===m)break;T.reject(En)}}x&&x()};v.promise.then(h,M=>h(null,M||"unknown"))}),ms(()=>{for(const v of d.values())v.reject(En)}),new Promise(v=>{function m(x){function h(){x===o?v(l):m(o)}x.then(h,h)}m(o)})}function L(e){const t=Ro(e);return td(t),t}function di(e){const t=Ro(e);return t.equals=Cl,t}function _u(e){var t=e.effects;if(t!==null){e.effects=null;for(var a=0;a<t.length;a+=1)Br(t[a])}}function wu(e){for(var t=e.parent;t!==null;){if((t.f&Fr)===0)return(t.f&qa)===0?t:null;t=t.parent}return null}function ci(e){var t,a=Nt;ba(wu(e));try{e.f&=~Fn,_u(e),t=od(e)}finally{ba(a)}return t}function Rl(e){var t=ci(e);if(!e.equals(t)&&(e.wv=ad(),(!(Ct!=null&&Ct.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){wr(e,Vr);return}bn||(jr!==null?(vi()||Ct!=null&&Ct.is_fork)&&jr.set(e,t):li(e))}function yu(e){var t,a;if(e.effects!==null)for(const n of e.effects)(n.teardown||n.ac)&&((t=n.teardown)==null||t.call(n),(a=n.ac)==null||a.abort(En),n.teardown=zc,n.ac=null,Po(n,0),pi(n))}function Dl(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&uo(t)}let Vs=new Set;const mn=new Map;let jl=!1;function Ha(e,t){var a={f:0,v:e,reactions:null,equals:$l,rv:0,wv:0};return a}function Y(e,t){const a=Ha(e);return td(a),a}function qs(e,t=!1,a=!0){var o;const n=Ha(e);return t||(n.equals=Cl),Oo&&a&&Lr!==null&&Lr.l!==null&&((o=Lr.l).s??(o.s=[])).push(n),n}function u(e,t,a=!1){Pt!==null&&(!Ta||(Pt.f&Pi)!==0)&&xo()&&(Pt.f&(Fr|kn|ii|Pi))!==0&&(ha===null||!io.call(ha,e))&&Fc();let n=a?Ut(t):t;return Qa(e,n)}function Qa(e,t){if(!e.equals(t)){var a=e.v;bn?mn.set(e,t):mn.set(e,a),e.v=t;var n=Xa.ensure();if(n.capture(e,a),(e.f&Fr)!==0){const o=e;(e.f&qr)!==0&&ci(o),li(o)}e.wv=ad(),Vl(e,qr),xo()&&Nt!==null&&(Nt.f&Vr)!==0&&(Nt.f&(Ea|Un))===0&&(fa===null?Nu([e]):fa.push(e)),!n.is_fork&&Vs.size>0&&!jl&&ku()}return t}function ku(){jl=!1;for(const e of Vs)(e.f&Vr)!==0&&wr(e,Aa),jo(e)&&uo(e);Vs.clear()}function Mo(e,t=1){var a=r(e),n=t===1?a++:a--;return u(e,a),n}function zo(e){u(e,e.v+1)}function Vl(e,t){var a=e.reactions;if(a!==null)for(var n=xo(),o=a.length,l=0;l<o;l++){var s=a[l],d=s.f;if(!(!n&&s===Nt)){var v=(d&qr)===0;if(v&&wr(s,t),(d&Fr)!==0){var m=s;jr==null||jr.delete(m),(d&Fn)===0&&(d&xa&&(s.f|=Fn),Vl(m,Aa))}else v&&((d&kn)!==0&&$a!==null&&$a.add(s),Va(s))}}}function Ut(e){if(typeof e!="object"||e===null||Ba in e)return e;const t=oi(e);if(t!==Tc&&t!==Mc)return e;var a=new Map,n=ni(e),o=Y(0),l=qn,s=d=>{if(qn===l)return d();var v=Pt,m=qn;ga(null),Di(l);var x=d();return ga(v),Di(m),x};return n&&a.set("length",Y(e.length)),new Proxy(e,{defineProperty(d,v,m){(!("value"in m)||m.configurable===!1||m.enumerable===!1||m.writable===!1)&&qc();var x=a.get(v);return x===void 0?s(()=>{var h=Y(m.value);return a.set(v,h),h}):u(x,m.value,!0),!0},deleteProperty(d,v){var m=a.get(v);if(m===void 0){if(v in d){const x=s(()=>Y(Ar));a.set(v,x),zo(o)}}else u(m,Ar),zo(o);return!0},get(d,v,m){var M;if(v===Ba)return e;var x=a.get(v),h=v in d;if(x===void 0&&(!h||(M=fn(d,v))!=null&&M.writable)&&(x=s(()=>{var $=Ut(h?d[v]:Ar),V=Y($);return V}),a.set(v,x)),x!==void 0){var _=r(x);return _===Ar?void 0:_}return Reflect.get(d,v,m)},getOwnPropertyDescriptor(d,v){var m=Reflect.getOwnPropertyDescriptor(d,v);if(m&&"value"in m){var x=a.get(v);x&&(m.value=r(x))}else if(m===void 0){var h=a.get(v),_=h==null?void 0:h.v;if(h!==void 0&&_!==Ar)return{enumerable:!0,configurable:!0,value:_,writable:!0}}return m},has(d,v){var _;if(v===Ba)return!0;var m=a.get(v),x=m!==void 0&&m.v!==Ar||Reflect.has(d,v);if(m!==void 0||Nt!==null&&(!x||(_=fn(d,v))!=null&&_.writable)){m===void 0&&(m=s(()=>{var M=x?Ut(d[v]):Ar,$=Y(M);return $}),a.set(v,m));var h=r(m);if(h===Ar)return!1}return x},set(d,v,m,x){var D;var h=a.get(v),_=v in d;if(n&&v==="length")for(var M=m;M<h.v;M+=1){var $=a.get(M+"");$!==void 0?u($,Ar):M in d&&($=s(()=>Y(Ar)),a.set(M+"",$))}if(h===void 0)(!_||(D=fn(d,v))!=null&&D.writable)&&(h=s(()=>Y(void 0)),u(h,Ut(m)),a.set(v,h));else{_=h.v!==Ar;var V=s(()=>Ut(m));u(h,V)}var T=Reflect.getOwnPropertyDescriptor(d,v);if(T!=null&&T.set&&T.set.call(x,m),!_){if(n&&typeof v=="string"){var z=a.get("length"),I=Number(v);Number.isInteger(I)&&I>=z.v&&u(z,I+1)}zo(o)}return!0},ownKeys(d){r(o);var v=Reflect.ownKeys(d).filter(h=>{var _=a.get(h);return _===void 0||_.v!==Ar});for(var[m,x]of a)x.v!==Ar&&!(m in d)&&v.push(m);return v},setPrototypeOf(){Bc()}})}function Li(e){try{if(e!==null&&typeof e=="object"&&Ba in e)return e[Ba]}catch{}return e}function $u(e,t){return Object.is(Li(e),Li(t))}var ts,ql,Bl,Fl,Hl;function Cu(){if(ts===void 0){ts=window,ql=document,Bl=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,a=Text.prototype;Fl=fn(t,"firstChild").get,Hl=fn(t,"nextSibling").get,Ii(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Ii(a)&&(a.__t=void 0)}}function Fa(e=""){return document.createTextNode(e)}function ma(e){return Fl.call(e)}function Do(e){return Hl.call(e)}function i(e,t){return ma(e)}function ae(e,t=!1){{var a=ma(e);return a instanceof Comment&&a.data===""?Do(a):a}}function p(e,t=1,a=!1){let n=e;for(;t--;)n=Do(n);return n}function Su(e){e.textContent=""}function Ul(){return!1}function ui(e,t,a){return document.createElementNS(t??yl,e,void 0)}function Tu(e,t){if(t){const a=document.body;e.autofocus=!0,za(()=>{document.activeElement===a&&e.focus()})}}let Oi=!1;function Mu(){Oi||(Oi=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const a of e.target.elements)(t=a.__on_r)==null||t.call(a)})},{capture:!0}))}function ps(e){var t=Pt,a=Nt;ga(null),ba(null);try{return e()}finally{ga(t),ba(a)}}function Kl(e,t,a,n=a){e.addEventListener(t,()=>ps(a));const o=e.__on_r;o?e.__on_r=()=>{o(),n(!0)}:e.__on_r=()=>n(!0),Mu()}function Gl(e){Nt===null&&(Pt===null&&Dc(),Rc()),bn&&Oc()}function zu(e,t){var a=t.last;a===null?t.last=t.first=e:(a.next=e,e.prev=a,t.last=e)}function Ia(e,t){var a=Nt;a!==null&&(a.f&Jr)!==0&&(e|=Jr);var n={ctx:Lr,deps:null,nodes:null,f:e|qr|xa,first:null,fn:t,last:null,next:null,parent:a,b:a&&a.b,prev:null,teardown:null,wv:0,ac:null},o=n;if((e&fo)!==0)co!==null?co.push(n):Va(n);else if(t!==null){try{uo(n)}catch(s){throw Br(n),s}o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&mo)===0&&(o=o.first,(e&kn)!==0&&(e&Za)!==0&&o!==null&&(o.f|=Za))}if(o!==null&&(o.parent=a,a!==null&&zu(o,a),Pt!==null&&(Pt.f&Fr)!==0&&(e&Un)===0)){var l=Pt;(l.effects??(l.effects=[])).push(o)}return n}function vi(){return Pt!==null&&!Ta}function ms(e){const t=Ia(Bn,null);return wr(t,Vr),t.teardown=e,t}function $r(e){Gl();var t=Nt.f,a=!Pt&&(t&Ea)!==0&&(t&po)===0;if(a){var n=Lr;(n.e??(n.e=[])).push(e)}else return Wl(e)}function Wl(e){return Ia(fo|xl,e)}function Au(e){return Gl(),Ia(Bn|xl,e)}function Eu(e){Xa.ensure();const t=Ia(Un|mo,e);return(a={})=>new Promise(n=>{a.outro?Vn(t,()=>{Br(t),n(void 0)}):(Br(t),n(void 0))})}function xs(e){return Ia(fo,e)}function Iu(e){return Ia(ii|mo,e)}function fi(e,t=0){return Ia(Bn|t,e)}function S(e,t=[],a=[],n=[]){Ll(n,t,a,o=>{Ia(Bn,()=>e(...o.map(r)))})}function Kn(e,t=0){var a=Ia(kn|t,e);return a}function Yl(e,t=0){var a=Ia(vs|t,e);return a}function ta(e){return Ia(Ea|mo,e)}function Jl(e){var t=e.teardown;if(t!==null){const a=bn,n=Pt;Ri(!0),ga(null);try{t.call(null)}finally{Ri(a),ga(n)}}}function pi(e,t=!1){var a=e.first;for(e.first=e.last=null;a!==null;){const o=a.ac;o!==null&&ps(()=>{o.abort(En)});var n=a.next;(a.f&Un)!==0?a.parent=null:Br(a,t),a=n}}function Pu(e){for(var t=e.first;t!==null;){var a=t.next;(t.f&Ea)===0&&Br(t),t=a}}function Br(e,t=!0){var a=!1;(t||(e.f&Ic)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(Xl(e.nodes.start,e.nodes.end),a=!0),pi(e,t&&!a),Po(e,0),wr(e,qa);var n=e.nodes&&e.nodes.t;if(n!==null)for(const l of n)l.stop();Jl(e);var o=e.parent;o!==null&&o.first!==null&&Ql(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function Xl(e,t){for(;e!==null;){var a=e===t?null:Do(e);e.remove(),e=a}}function Ql(e){var t=e.parent,a=e.prev,n=e.next;a!==null&&(a.next=n),n!==null&&(n.prev=a),t!==null&&(t.first===e&&(t.first=n),t.last===e&&(t.last=a))}function Vn(e,t,a=!0){var n=[];Zl(e,n,!0);var o=()=>{a&&Br(e),t&&t()},l=n.length;if(l>0){var s=()=>--l||o();for(var d of n)d.out(s)}else o()}function Zl(e,t,a){if((e.f&Jr)===0){e.f^=Jr;var n=e.nodes&&e.nodes.t;if(n!==null)for(const d of n)(d.is_global||a)&&t.push(d);for(var o=e.first;o!==null;){var l=o.next,s=(o.f&Za)!==0||(o.f&Ea)!==0&&(e.f&kn)!==0;Zl(o,t,s?a:!1),o=l}}}function mi(e){ed(e,!0)}function ed(e,t){if((e.f&Jr)!==0){e.f^=Jr;for(var a=e.first;a!==null;){var n=a.next,o=(a.f&Za)!==0||(a.f&Ea)!==0;ed(a,o?t:!1),a=n}var l=e.nodes&&e.nodes.t;if(l!==null)for(const s of l)(s.is_global||t)&&s.in()}}function xi(e,t){if(e.nodes)for(var a=e.nodes.start,n=e.nodes.end;a!==null;){var o=a===n?null:Do(a);t.append(a),a=o}}let Jo=!1,bn=!1;function Ri(e){bn=e}let Pt=null,Ta=!1;function ga(e){Pt=e}let Nt=null;function ba(e){Nt=e}let ha=null;function td(e){Pt!==null&&(ha===null?ha=[e]:ha.push(e))}let ea=null,ia=0,fa=null;function Nu(e){fa=e}let rd=1,Pn=0,qn=Pn;function Di(e){qn=e}function ad(){return++rd}function jo(e){var t=e.f;if((t&qr)!==0)return!0;if(t&Fr&&(e.f&=~Fn),(t&Aa)!==0){for(var a=e.deps,n=a.length,o=0;o<n;o++){var l=a[o];if(jo(l)&&Rl(l),l.wv>e.wv)return!0}(t&xa)!==0&&jr===null&&wr(e,Vr)}return!1}function nd(e,t,a=!0){var n=e.reactions;if(n!==null&&!(ha!==null&&io.call(ha,e)))for(var o=0;o<n.length;o++){var l=n[o];(l.f&Fr)!==0?nd(l,t,!1):t===l&&(a?wr(l,qr):(l.f&Vr)!==0&&wr(l,Aa),Va(l))}}function od(e){var V;var t=ea,a=ia,n=fa,o=Pt,l=ha,s=Lr,d=Ta,v=qn,m=e.f;ea=null,ia=0,fa=null,Pt=(m&(Ea|Un))===0?e:null,ha=null,lo(e.ctx),Ta=!1,qn=++Pn,e.ac!==null&&(ps(()=>{e.ac.abort(En)}),e.ac=null);try{e.f|=Ps;var x=e.fn,h=x();e.f|=po;var _=e.deps,M=Ct==null?void 0:Ct.is_fork;if(ea!==null){var $;if(M||Po(e,ia),_!==null&&ia>0)for(_.length=ia+ea.length,$=0;$<ea.length;$++)_[ia+$]=ea[$];else e.deps=_=ea;if(vi()&&(e.f&xa)!==0)for($=ia;$<_.length;$++)((V=_[$]).reactions??(V.reactions=[])).push(e)}else!M&&_!==null&&ia<_.length&&(Po(e,ia),_.length=ia);if(xo()&&fa!==null&&!Ta&&_!==null&&(e.f&(Fr|Aa|qr))===0)for($=0;$<fa.length;$++)nd(fa[$],e);if(o!==null&&o!==e){if(Pn++,o.deps!==null)for(let T=0;T<a;T+=1)o.deps[T].rv=Pn;if(t!==null)for(const T of t)T.rv=Pn;fa!==null&&(n===null?n=fa:n.push(...fa))}return(e.f&pn)!==0&&(e.f^=pn),h}catch(T){return Tl(T)}finally{e.f^=Ps,ea=t,ia=a,fa=n,Pt=o,ha=l,lo(s),Ta=d,qn=v}}function Lu(e,t){let a=t.reactions;if(a!==null){var n=Cc.call(a,e);if(n!==-1){var o=a.length-1;o===0?a=t.reactions=null:(a[n]=a[o],a.pop())}}if(a===null&&(t.f&Fr)!==0&&(ea===null||!io.call(ea,t))){var l=t;(l.f&xa)!==0&&(l.f^=xa,l.f&=~Fn),li(l),yu(l),Po(l,0)}}function Po(e,t){var a=e.deps;if(a!==null)for(var n=t;n<a.length;n++)Lu(e,a[n])}function uo(e){var t=e.f;if((t&qa)===0){wr(e,Vr);var a=Nt,n=Jo;Nt=e,Jo=!0;try{(t&(kn|vs))!==0?Pu(e):pi(e),Jl(e);var o=od(e);e.teardown=typeof o=="function"?o:null,e.wv=rd;var l;As&&ou&&(e.f&qr)!==0&&e.deps}finally{Jo=n,Nt=a}}}async function sd(){await Promise.resolve(),Al()}function r(e){var t=e.f,a=(t&Fr)!==0;if(Pt!==null&&!Ta){var n=Nt!==null&&(Nt.f&qa)!==0;if(!n&&(ha===null||!io.call(ha,e))){var o=Pt.deps;if((Pt.f&Ps)!==0)e.rv<Pn&&(e.rv=Pn,ea===null&&o!==null&&o[ia]===e?ia++:ea===null?ea=[e]:ea.push(e));else{(Pt.deps??(Pt.deps=[])).push(e);var l=e.reactions;l===null?e.reactions=[Pt]:io.call(l,Pt)||l.push(Pt)}}}if(bn&&mn.has(e))return mn.get(e);if(a){var s=e;if(bn){var d=s.v;return((s.f&Vr)===0&&s.reactions!==null||ld(s))&&(d=ci(s)),mn.set(s,d),d}var v=(s.f&xa)===0&&!Ta&&Pt!==null&&(Jo||(Pt.f&xa)!==0),m=(s.f&po)===0;jo(s)&&(v&&(s.f|=xa),Rl(s)),v&&!m&&(Dl(s),id(s))}if(jr!=null&&jr.has(e))return jr.get(e);if((e.f&pn)!==0)throw e.v;return e.v}function id(e){if(e.f|=xa,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&Fr)!==0&&(t.f&xa)===0&&(Dl(t),id(t))}function ld(e){if(e.v===Ar)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(mn.has(t)||(t.f&Fr)!==0&&ld(t))return!0;return!1}function Hn(e){var t=Ta;try{return Ta=!0,e()}finally{Ta=t}}function zn(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(Ba in e)Bs(e);else if(!Array.isArray(e))for(let t in e){const a=e[t];typeof a=="object"&&a&&Ba in a&&Bs(a)}}}function Bs(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let n in e)try{Bs(e[n],t)}catch{}const a=oi(e);if(a!==Object.prototype&&a!==Array.prototype&&a!==Map.prototype&&a!==Set.prototype&&a!==Date.prototype){const n=pl(a);for(let o in n){const l=n[o].get;if(l)try{l.call(e)}catch{}}}}}function Ou(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const Ru=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function Du(e){return Ru.includes(e)}const ju={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function Vu(e){return e=e.toLowerCase(),ju[e]??e}const qu=["touchstart","touchmove"];function Bu(e){return qu.includes(e)}const Nn=Symbol("events"),dd=new Set,Fs=new Set;function cd(e,t,a,n={}){function o(l){if(n.capture||Hs.call(t,l),!l.cancelBubble)return ps(()=>a==null?void 0:a.call(this,l))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?za(()=>{t.addEventListener(e,o,n)}):t.addEventListener(e,o,n),o}function xn(e,t,a,n,o){var l={capture:n,passive:o},s=cd(e,t,a,l);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&ms(()=>{t.removeEventListener(e,s,l)})}function ce(e,t,a){(t[Nn]??(t[Nn]={}))[e]=a}function Hr(e){for(var t=0;t<e.length;t++)dd.add(e[t]);for(var a of Fs)a(e)}let ji=null;function Hs(e){var T,z;var t=this,a=t.ownerDocument,n=e.type,o=((T=e.composedPath)==null?void 0:T.call(e))||[],l=o[0]||e.target;ji=e;var s=0,d=ji===e&&e[Nn];if(d){var v=o.indexOf(d);if(v!==-1&&(t===document||t===window)){e[Nn]=t;return}var m=o.indexOf(t);if(m===-1)return;v<=m&&(s=v)}if(l=o[s]||e.target,l!==t){Sc(e,"currentTarget",{configurable:!0,get(){return l||a}});var x=Pt,h=Nt;ga(null),ba(null);try{for(var _,M=[];l!==null;){var $=l.assignedSlot||l.parentNode||l.host||null;try{var V=(z=l[Nn])==null?void 0:z[n];V!=null&&(!l.disabled||e.target===l)&&V.call(l,e)}catch(I){_?M.push(I):_=I}if(e.cancelBubble||$===t||$===null)break;l=$}if(_){for(let I of M)queueMicrotask(()=>{throw I});throw _}}finally{e[Nn]=t,delete e.currentTarget,ga(x),ba(h)}}}var vl;const ks=((vl=globalThis==null?void 0:globalThis.window)==null?void 0:vl.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function Fu(e){return(ks==null?void 0:ks.createHTML(e))??e}function ud(e){var t=ui("template");return t.innerHTML=Fu(e.replaceAll("<!>","<!---->")),t.content}function _n(e,t){var a=Nt;a.nodes===null&&(a.nodes={start:e,end:t,a:null,t:null})}function f(e,t){var a=(t&wl)!==0,n=(t&Zc)!==0,o,l=!e.startsWith("<!>");return()=>{o===void 0&&(o=ud(l?e:"<!>"+e),a||(o=ma(o)));var s=n||Bl?document.importNode(o,!0):o.cloneNode(!0);if(a){var d=ma(s),v=s.lastChild;_n(d,v)}else _n(s,s);return s}}function Hu(e,t,a="svg"){var n=!e.startsWith("<!>"),o=(t&wl)!==0,l=`<${a}>${n?e:"<!>"+e}</${a}>`,s;return()=>{if(!s){var d=ud(l),v=ma(d);if(o)for(s=document.createDocumentFragment();ma(v);)s.appendChild(ma(v));else s=ma(v)}var m=s.cloneNode(!0);if(o){var x=ma(m),h=m.lastChild;_n(x,h)}else _n(m,m);return m}}function Uu(e,t){return Hu(e,t,"svg")}function Ja(e=""){{var t=Fa(e+"");return _n(t,t),t}}function _e(){var e=document.createDocumentFragment(),t=document.createComment(""),a=Fa();return e.append(t,a),_n(t,a),e}function c(e,t){e!==null&&e.before(t)}function C(e,t){var a=t==null?"":typeof t=="object"?`${t}`:t;a!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=a,e.nodeValue=`${a}`)}function Ku(e,t){return Gu(e,t)}const Ho=new Map;function Gu(e,{target:t,anchor:a,props:n={},events:o,context:l,intro:s=!0,transformError:d}){Cu();var v=void 0,m=Eu(()=>{var x=a??t.appendChild(Fa());fu(x,{pending:()=>{}},M=>{Cr({});var $=Lr;l&&($.c=l),o&&(n.$$events=o),v=e(M,n)||{},Sr()},d);var h=new Set,_=M=>{for(var $=0;$<M.length;$++){var V=M[$];if(!h.has(V)){h.add(V);var T=Bu(V);for(const D of[t,document]){var z=Ho.get(D);z===void 0&&(z=new Map,Ho.set(D,z));var I=z.get(V);I===void 0?(D.addEventListener(V,Hs,{passive:T}),z.set(V,1)):z.set(V,I+1)}}}};return _(us(dd)),Fs.add(_),()=>{var T;for(var M of h)for(const z of[t,document]){var $=Ho.get(z),V=$.get(M);--V==0?(z.removeEventListener(M,Hs),$.delete(M),$.size===0&&Ho.delete(z)):$.set(M,V)}Fs.delete(_),x!==a&&((T=x.parentNode)==null||T.removeChild(x))}});return Wu.set(v,m),v}let Wu=new WeakMap;var Sa,Da,da,jn,No,Lo,cs;class Vo{constructor(t,a=!0){ka(this,"anchor");Rt(this,Sa,new Map);Rt(this,Da,new Map);Rt(this,da,new Map);Rt(this,jn,new Set);Rt(this,No,!0);Rt(this,Lo,t=>{if(X(this,Sa).has(t)){var a=X(this,Sa).get(t),n=X(this,Da).get(a);if(n)mi(n),X(this,jn).delete(a);else{var o=X(this,da).get(a);o&&(o.effect.f&Jr)===0&&(X(this,Da).set(a,o.effect),X(this,da).delete(a),o.fragment.lastChild.remove(),this.anchor.before(o.fragment),n=o.effect)}for(const[l,s]of X(this,Sa)){if(X(this,Sa).delete(l),l===t)break;const d=X(this,da).get(s);d&&(Br(d.effect),X(this,da).delete(s))}for(const[l,s]of X(this,Da)){if(l===a||X(this,jn).has(l)||(s.f&Jr)!==0)continue;const d=()=>{if(Array.from(X(this,Sa).values()).includes(l)){var m=document.createDocumentFragment();xi(s,m),m.append(Fa()),X(this,da).set(l,{effect:s,fragment:m})}else Br(s);X(this,jn).delete(l),X(this,Da).delete(l)};X(this,No)||!n?(X(this,jn).add(l),Vn(s,d,!1)):d()}}});Rt(this,cs,t=>{X(this,Sa).delete(t);const a=Array.from(X(this,Sa).values());for(const[n,o]of X(this,da))a.includes(n)||(Br(o.effect),X(this,da).delete(n))});this.anchor=t,It(this,No,a)}ensure(t,a){var n=Ct,o=Ul();if(a&&!X(this,Da).has(t)&&!X(this,da).has(t))if(o){var l=document.createDocumentFragment(),s=Fa();l.append(s),X(this,da).set(t,{effect:ta(()=>a(s)),fragment:l})}else X(this,Da).set(t,ta(()=>a(this.anchor)));if(X(this,Sa).set(n,t),o){for(const[d,v]of X(this,Da))d===t?n.unskip_effect(v):n.skip_effect(v);for(const[d,v]of X(this,da))d===t?n.unskip_effect(v.effect):n.skip_effect(v.effect);n.oncommit(X(this,Lo)),n.ondiscard(X(this,cs))}else X(this,Lo).call(this,n)}}Sa=new WeakMap,Da=new WeakMap,da=new WeakMap,jn=new WeakMap,No=new WeakMap,Lo=new WeakMap,cs=new WeakMap;const Yu=0,Vi=1,Ju=2;function Us(e,t,a,n,o){var l=xo(),s=Ar,d=l?Ha(s):qs(s,!1,!1),v=l?Ha(s):qs(s,!1,!1),m=new Vo(e);Kn(()=>{var x=t(),h=!1;if(Ac(x)){var _=Ol(),M=!1;const $=V=>{if(!h){M=!0,_(!1),Xa.ensure();try{V()}finally{es(!1),Qn||Al()}}};x.then(V=>{$(()=>{Qa(d,V),m.ensure(Vi,n&&(T=>n(T,d)))})},V=>{$(()=>{if(Qa(v,V),m.ensure(Ju,o&&(T=>o(T,v))),!o)throw v.v})}),za(()=>{M||$(()=>{m.ensure(Yu,a)})})}else Qa(d,x),m.ensure(Vi,n&&($=>n($,d)));return()=>{h=!0}})}function b(e,t,a=!1){var n=new Vo(e),o=a?Za:0;function l(s,d){n.ensure(s,d)}Kn(()=>{var s=!1;t((d,v=0)=>{s=!0,l(v,d)}),s||l(-1,null)},o)}function Te(e,t){return t}function Xu(e,t,a){for(var n=[],o=t.length,l,s=t.length,d=0;d<o;d++){let h=t[d];Vn(h,()=>{if(l){if(l.pending.delete(h),l.done.add(h),l.pending.size===0){var _=e.outrogroups;Ks(e,us(l.done)),_.delete(l),_.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var v=n.length===0&&a!==null;if(v){var m=a,x=m.parentNode;Su(x),x.append(m),e.items.clear()}Ks(e,t,!v)}else l={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(l)}function Ks(e,t,a=!0){var n;if(e.pending.size>0){n=new Set;for(const s of e.pending.values())for(const d of s)n.add(e.items.get(d).e)}for(var o=0;o<t.length;o++){var l=t[o];if(n!=null&&n.has(l)){l.f|=ja;const s=document.createDocumentFragment();xi(l,s)}else Br(t[o],a)}}var qi;function Ce(e,t,a,n,o,l=null){var s=e,d=new Map,v=(t&bl)!==0;if(v){var m=e;s=m.appendChild(Fa())}var x=null,h=di(()=>{var D=a();return ni(D)?D:D==null?[]:us(D)}),_,M=new Map,$=!0;function V(D){(I.effect.f&qa)===0&&(I.pending.delete(D),I.fallback=x,Qu(I,_,s,t,n),x!==null&&(_.length===0?(x.f&ja)===0?mi(x):(x.f^=ja,To(x,null,s)):Vn(x,()=>{x=null})))}function T(D){I.pending.delete(D)}var z=Kn(()=>{_=r(h);for(var D=_.length,j=new Set,de=Ct,pe=Ul(),F=0;F<D;F+=1){var k=_[F],G=n(k,F),N=$?null:d.get(G);N?(N.v&&Qa(N.v,k),N.i&&Qa(N.i,F),pe&&de.unskip_effect(N.e)):(N=Zu(d,$?s:qi??(qi=Fa()),k,G,F,o,t,a),$||(N.e.f|=ja),d.set(G,N)),j.add(G)}if(D===0&&l&&!x&&($?x=ta(()=>l(s)):(x=ta(()=>l(qi??(qi=Fa()))),x.f|=ja)),D>j.size&&Lc(),!$)if(M.set(de,j),pe){for(const[re,P]of d)j.has(re)||de.skip_effect(P.e);de.oncommit(V),de.ondiscard(T)}else V(de);r(h)}),I={effect:z,items:d,pending:M,outrogroups:null,fallback:x};$=!1}function wo(e){for(;e!==null&&(e.f&Ea)===0;)e=e.next;return e}function Qu(e,t,a,n,o){var N,re,P,me,E,B,oe,fe,he;var l=(n&Gc)!==0,s=t.length,d=e.items,v=wo(e.effect.first),m,x=null,h,_=[],M=[],$,V,T,z;if(l)for(z=0;z<s;z+=1)$=t[z],V=o($,z),T=d.get(V).e,(T.f&ja)===0&&((re=(N=T.nodes)==null?void 0:N.a)==null||re.measure(),(h??(h=new Set)).add(T));for(z=0;z<s;z+=1){if($=t[z],V=o($,z),T=d.get(V).e,e.outrogroups!==null)for(const xe of e.outrogroups)xe.pending.delete(T),xe.done.delete(T);if((T.f&ja)!==0)if(T.f^=ja,T===v)To(T,null,a);else{var I=x?x.next:v;T===e.effect.last&&(e.effect.last=T.prev),T.prev&&(T.prev.next=T.next),T.next&&(T.next.prev=T.prev),on(e,x,T),on(e,T,I),To(T,I,a),x=T,_=[],M=[],v=wo(x.next);continue}if((T.f&Jr)!==0&&(mi(T),l&&((me=(P=T.nodes)==null?void 0:P.a)==null||me.unfix(),(h??(h=new Set)).delete(T))),T!==v){if(m!==void 0&&m.has(T)){if(_.length<M.length){var D=M[0],j;x=D.prev;var de=_[0],pe=_[_.length-1];for(j=0;j<_.length;j+=1)To(_[j],D,a);for(j=0;j<M.length;j+=1)m.delete(M[j]);on(e,de.prev,pe.next),on(e,x,de),on(e,pe,D),v=D,x=pe,z-=1,_=[],M=[]}else m.delete(T),To(T,v,a),on(e,T.prev,T.next),on(e,T,x===null?e.effect.first:x.next),on(e,x,T),x=T;continue}for(_=[],M=[];v!==null&&v!==T;)(m??(m=new Set)).add(v),M.push(v),v=wo(v.next);if(v===null)continue}(T.f&ja)===0&&_.push(T),x=T,v=wo(T.next)}if(e.outrogroups!==null){for(const xe of e.outrogroups)xe.pending.size===0&&(Ks(e,us(xe.done)),(E=e.outrogroups)==null||E.delete(xe));e.outrogroups.size===0&&(e.outrogroups=null)}if(v!==null||m!==void 0){var F=[];if(m!==void 0)for(T of m)(T.f&Jr)===0&&F.push(T);for(;v!==null;)(v.f&Jr)===0&&v!==e.fallback&&F.push(v),v=wo(v.next);var k=F.length;if(k>0){var G=(n&bl)!==0&&s===0?a:null;if(l){for(z=0;z<k;z+=1)(oe=(B=F[z].nodes)==null?void 0:B.a)==null||oe.measure();for(z=0;z<k;z+=1)(he=(fe=F[z].nodes)==null?void 0:fe.a)==null||he.fix()}Xu(e,F,G)}}l&&za(()=>{var xe,se;if(h!==void 0)for(T of h)(se=(xe=T.nodes)==null?void 0:xe.a)==null||se.apply()})}function Zu(e,t,a,n,o,l,s,d){var v=(s&Uc)!==0?(s&Wc)===0?qs(a,!1,!1):Ha(a):null,m=(s&Kc)!==0?Ha(o):null;return{v,i:m,e:ta(()=>(l(t,v??a,m??o,d),()=>{e.delete(n)}))}}function To(e,t,a){if(e.nodes)for(var n=e.nodes.start,o=e.nodes.end,l=t&&(t.f&ja)===0?t.nodes.start:a;n!==null;){var s=Do(n);if(l.before(n),n===o)return;n=s}}function on(e,t,a){t===null?e.effect.first=a:t.next=a,a===null?e.effect.last=t:a.prev=t}function Ma(e,t,a=!1,n=!1,o=!1){var l=e,s="";S(()=>{var d=Nt;if(s!==(s=t()??"")&&(d.nodes!==null&&(Xl(d.nodes.start,d.nodes.end),d.nodes=null),s!=="")){var v=a?kl:n?eu:void 0,m=ui(a?"svg":n?"math":"template",v);m.innerHTML=s;var x=a||n?m:m.content;if(_n(ma(x),x.lastChild),a||n)for(;ma(x);)l.before(ma(x));else l.before(x)}})}function at(e,t,a,n,o){var d;var l=(d=t.$$slots)==null?void 0:d[a],s=!1;l===!0&&(l=t.children,s=!0),l===void 0||l(e,s?()=>n:n)}function Gs(e,t,...a){var n=new Vo(e);Kn(()=>{const o=t()??null;n.ensure(o,o&&(l=>o(l,...a)))},Za)}function vo(e,t,a){var n=new Vo(e);Kn(()=>{var o=t()??null;n.ensure(o,o&&(l=>a(l,o)))},Za)}function ev(e,t,a,n,o,l){var s=null,d=e,v=new Vo(d,!1);Kn(()=>{const m=t()||null;var x=kl;if(m===null){v.ensure(null,null);return}return v.ensure(m,h=>{if(m){if(s=ui(m,x),_n(s,s),n){var _=s.appendChild(Fa());n(s,_)}Nt.nodes.end=s,h.before(s)}}),()=>{}},Za),ms(()=>{})}function tv(e,t){var a=void 0,n;Yl(()=>{a!==(a=t())&&(n&&(Br(n),n=null),a&&(n=ta(()=>{xs(()=>a(e))})))})}function vd(e){var t,a,n="";if(typeof e=="string"||typeof e=="number")n+=e;else if(typeof e=="object")if(Array.isArray(e)){var o=e.length;for(t=0;t<o;t++)e[t]&&(a=vd(e[t]))&&(n&&(n+=" "),n+=a)}else for(a in e)e[a]&&(n&&(n+=" "),n+=a);return n}function fd(){for(var e,t,a=0,n="",o=arguments.length;a<o;a++)(e=arguments[a])&&(t=vd(e))&&(n&&(n+=" "),n+=t);return n}function rr(e){return typeof e=="object"?fd(e):e??""}const Bi=[...` 	
\r\f \v\uFEFF`];function rv(e,t,a){var n=e==null?"":""+e;if(t&&(n=n?n+" "+t:t),a){for(var o of Object.keys(a))if(a[o])n=n?n+" "+o:o;else if(n.length)for(var l=o.length,s=0;(s=n.indexOf(o,s))>=0;){var d=s+l;(s===0||Bi.includes(n[s-1]))&&(d===n.length||Bi.includes(n[d]))?n=(s===0?"":n.substring(0,s))+n.substring(d+1):s=d}}return n===""?null:n}function Fi(e,t=!1){var a=t?" !important;":";",n="";for(var o of Object.keys(e)){var l=e[o];l!=null&&l!==""&&(n+=" "+o+": "+l+a)}return n}function $s(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function av(e,t){if(t){var a="",n,o;if(Array.isArray(t)?(n=t[0],o=t[1]):n=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var l=!1,s=0,d=!1,v=[];n&&v.push(...Object.keys(n).map($s)),o&&v.push(...Object.keys(o).map($s));var m=0,x=-1;const V=e.length;for(var h=0;h<V;h++){var _=e[h];if(d?_==="/"&&e[h-1]==="*"&&(d=!1):l?l===_&&(l=!1):_==="/"&&e[h+1]==="*"?d=!0:_==='"'||_==="'"?l=_:_==="("?s++:_===")"&&s--,!d&&l===!1&&s===0){if(_===":"&&x===-1)x=h;else if(_===";"||h===V-1){if(x!==-1){var M=$s(e.substring(m,x).trim());if(!v.includes(M)){_!==";"&&h++;var $=e.substring(m,h).trim();a+=" "+$+";"}}m=h+1,x=-1}}}}return n&&(a+=Fi(n)),o&&(a+=Fi(o,!0)),a=a.trim(),a===""?null:a}return e==null?null:String(e)}function Re(e,t,a,n,o,l){var s=e.__className;if(s!==a||s===void 0){var d=rv(a,n,l);d==null?e.removeAttribute("class"):t?e.className=d:e.setAttribute("class",d),e.__className=a}else if(l&&o!==l)for(var v in l){var m=!!l[v];(o==null||m!==!!o[v])&&e.classList.toggle(v,m)}return l}function Cs(e,t={},a,n){for(var o in a){var l=a[o];t[o]!==l&&(a[o]==null?e.style.removeProperty(o):e.style.setProperty(o,l,n))}}function rs(e,t,a,n){var o=e.__style;if(o!==t){var l=av(t,n);l==null?e.removeAttribute("style"):e.style.cssText=l,e.__style=t}else n&&(Array.isArray(n)?(Cs(e,a==null?void 0:a[0],n[0]),Cs(e,a==null?void 0:a[1],n[1],"important")):Cs(e,a,n));return n}function as(e,t,a=!1){if(e.multiple){if(t==null)return;if(!ni(t))return ru();for(var n of e.options)n.selected=t.includes(Ao(n));return}for(n of e.options){var o=Ao(n);if($u(o,t)){n.selected=!0;return}}(!a||t!==void 0)&&(e.selectedIndex=-1)}function pd(e){var t=new MutationObserver(()=>{as(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),ms(()=>{t.disconnect()})}function Hi(e,t,a=t){var n=new WeakSet,o=!0;Kl(e,"change",l=>{var s=l?"[selected]":":checked",d;if(e.multiple)d=[].map.call(e.querySelectorAll(s),Ao);else{var v=e.querySelector(s)??e.querySelector("option:not([disabled])");d=v&&Ao(v)}a(d),Ct!==null&&n.add(Ct)}),xs(()=>{var l=t();if(e===document.activeElement){var s=Zo??Ct;if(n.has(s))return}if(as(e,l,o),o&&l===void 0){var d=e.querySelector(":checked");d!==null&&(l=Ao(d),a(l))}e.__value=l,o=!1}),pd(e)}function Ao(e){return"__value"in e?e.__value:e.value}const yo=Symbol("class"),ko=Symbol("style"),md=Symbol("is custom element"),xd=Symbol("is html"),nv=gl?"option":"OPTION",ov=gl?"select":"SELECT";function sv(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function ua(e,t,a,n){var o=hd(e);o[t]!==(o[t]=a)&&(t==="loading"&&(e[Pc]=a),a==null?e.removeAttribute(t):typeof a!="string"&&gd(e).includes(t)?e[t]=a:e.setAttribute(t,a))}function iv(e,t,a,n,o=!1,l=!1){var s=hd(e),d=s[md],v=!s[xd],m=t||{},x=e.nodeName===nv;for(var h in t)h in a||(a[h]=null);a.class?a.class=rr(a.class):a[yo]&&(a.class=null),a[ko]&&(a.style??(a.style=null));var _=gd(e);for(const D in a){let j=a[D];if(x&&D==="value"&&j==null){e.value=e.__value="",m[D]=j;continue}if(D==="class"){var M=e.namespaceURI==="http://www.w3.org/1999/xhtml";Re(e,M,j,n,t==null?void 0:t[yo],a[yo]),m[D]=j,m[yo]=a[yo];continue}if(D==="style"){rs(e,j,t==null?void 0:t[ko],a[ko]),m[D]=j,m[ko]=a[ko];continue}var $=m[D];if(!(j===$&&!(j===void 0&&e.hasAttribute(D)))){m[D]=j;var V=D[0]+D[1];if(V!=="$$")if(V==="on"){const de={},pe="$$"+D;let F=D.slice(2);var T=Du(F);if(Ou(F)&&(F=F.slice(0,-7),de.capture=!0),!T&&$){if(j!=null)continue;e.removeEventListener(F,m[pe],de),m[pe]=null}if(T)ce(F,e,j),Hr([F]);else if(j!=null){let k=function(G){m[D].call(this,G)};m[pe]=cd(F,e,k,de)}}else if(D==="style")ua(e,D,j);else if(D==="autofocus")Tu(e,!!j);else if(!d&&(D==="__value"||D==="value"&&j!=null))e.value=e.__value=j;else if(D==="selected"&&x)sv(e,j);else{var z=D;v||(z=Vu(z));var I=z==="defaultValue"||z==="defaultChecked";if(j==null&&!d&&!I)if(s[D]=null,z==="value"||z==="checked"){let de=e;const pe=t===void 0;if(z==="value"){let F=de.defaultValue;de.removeAttribute(z),de.defaultValue=F,de.value=de.__value=pe?F:null}else{let F=de.defaultChecked;de.removeAttribute(z),de.defaultChecked=F,de.checked=pe?F:!1}}else e.removeAttribute(D);else I||_.includes(z)&&(d||typeof j!="string")?(e[z]=j,z in s&&(s[z]=Ar)):typeof j!="function"&&ua(e,z,j)}}}return m}function ns(e,t,a=[],n=[],o=[],l,s=!1,d=!1){Ll(o,a,n,v=>{var m=void 0,x={},h=e.nodeName===ov,_=!1;if(Yl(()=>{var $=t(...v.map(r)),V=iv(e,m,$,l,s,d);_&&h&&"value"in $&&as(e,$.value);for(let z of Object.getOwnPropertySymbols(x))$[z]||Br(x[z]);for(let z of Object.getOwnPropertySymbols($)){var T=$[z];z.description===tu&&(!m||T!==m[z])&&(x[z]&&Br(x[z]),x[z]=ta(()=>tv(e,()=>T))),V[z]=T}m=V}),h){var M=e;xs(()=>{as(M,m.value,!0),pd(M)})}_=!0})}function hd(e){return e.__attributes??(e.__attributes={[md]:e.nodeName.includes("-"),[xd]:e.namespaceURI===yl})}var Ui=new Map;function gd(e){var t=e.getAttribute("is")||e.nodeName,a=Ui.get(t);if(a)return a;Ui.set(t,a=[]);for(var n,o=e,l=Element.prototype;l!==o;){n=pl(o);for(var s in n)n[s].set&&a.push(s);o=oi(o)}return a}function Ln(e,t,a=t){var n=new WeakSet;Kl(e,"input",async o=>{var l=o?e.defaultValue:e.value;if(l=Ss(e)?Ts(l):l,a(l),Ct!==null&&n.add(Ct),await sd(),l!==(l=t())){var s=e.selectionStart,d=e.selectionEnd,v=e.value.length;if(e.value=l??"",d!==null){var m=e.value.length;s===d&&d===v&&m>v?(e.selectionStart=m,e.selectionEnd=m):(e.selectionStart=s,e.selectionEnd=Math.min(d,m))}}}),Hn(t)==null&&e.value&&(a(Ss(e)?Ts(e.value):e.value),Ct!==null&&n.add(Ct)),fi(()=>{var o=t();if(e===document.activeElement){var l=Zo??Ct;if(n.has(l))return}Ss(e)&&o===Ts(e.value)||e.type==="date"&&!o&&!e.value||o!==e.value&&(e.value=o??"")})}function Ss(e){var t=e.type;return t==="number"||t==="range"}function Ts(e){return e===""?null:+e}function Ki(e,t){return e===t||(e==null?void 0:e[Ba])===t}function hn(e={},t,a,n){return xs(()=>{var o,l;return fi(()=>{o=l,l=[],Hn(()=>{e!==a(...l)&&(t(e,...l),o&&Ki(a(...o),e)&&t(null,...o))})}),()=>{za(()=>{l&&Ki(a(...l),e)&&t(null,...l)})}}),e}function lv(e=!1){const t=Lr,a=t.l.u;if(!a)return;let n=()=>zn(t.s);if(e){let o=0,l={};const s=Ro(()=>{let d=!1;const v=t.s;for(const m in v)v[m]!==l[m]&&(l[m]=v[m],d=!0);return d&&o++,o});n=()=>r(s)}a.b.length&&Au(()=>{Gi(t,n),Es(a.b)}),$r(()=>{const o=Hn(()=>a.m.map(Ec));return()=>{for(const l of o)typeof l=="function"&&l()}}),a.a.length&&$r(()=>{Gi(t,n),Es(a.a)})}function Gi(e,t){if(e.l.s)for(const a of e.l.s)r(a);t()}let Uo=!1;function dv(e){var t=Uo;try{return Uo=!1,[e(),Uo]}finally{Uo=t}}const cv={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function uv(e,t,a){return new Proxy({props:e,exclude:t},cv)}const vv={get(e,t){if(!e.exclude.includes(t))return r(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,a){if(!(t in e.special)){var n=Nt;try{ba(e.parent_effect),e.special[t]=Ie({get[t](){return e.props[t]}},t,_l)}finally{ba(n)}}return e.special[t](a),Mo(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),Mo(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function tt(e,t){return new Proxy({props:e,exclude:t,special:{},version:Ha(0),parent_effect:Nt},vv)}const fv={get(e,t){let a=e.props.length;for(;a--;){let n=e.props[a];if(_o(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n)return n[t]}},set(e,t,a){let n=e.props.length;for(;n--;){let o=e.props[n];_o(o)&&(o=o());const l=fn(o,t);if(l&&l.set)return l.set(a),!0}return!1},getOwnPropertyDescriptor(e,t){let a=e.props.length;for(;a--;){let n=e.props[a];if(_o(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n){const o=fn(n,t);return o&&!o.configurable&&(o.configurable=!0),o}}},has(e,t){if(t===Ba||t===hl)return!1;for(let a of e.props)if(_o(a)&&(a=a()),a!=null&&t in a)return!0;return!1},ownKeys(e){const t=[];for(let a of e.props)if(_o(a)&&(a=a()),!!a){for(const n in a)t.includes(n)||t.push(n);for(const n of Object.getOwnPropertySymbols(a))t.includes(n)||t.push(n)}return t}};function st(...e){return new Proxy({props:e},fv)}function Ie(e,t,a,n){var D;var o=!Oo||(a&Jc)!==0,l=(a&Xc)!==0,s=(a&Qc)!==0,d=n,v=!0,m=()=>(v&&(v=!1,d=s?Hn(n):n),d),x;if(l){var h=Ba in e||hl in e;x=((D=fn(e,t))==null?void 0:D.set)??(h&&t in e?j=>e[t]=j:void 0)}var _,M=!1;l?[_,M]=dv(()=>e[t]):_=e[t],_===void 0&&n!==void 0&&(_=m(),x&&(o&&Vc(),x(_)));var $;if(o?$=()=>{var j=e[t];return j===void 0?m():(v=!0,j)}:$=()=>{var j=e[t];return j!==void 0&&(d=void 0),j===void 0?d:j},o&&(a&_l)===0)return $;if(x){var V=e.$$legacy;return(function(j,de){return arguments.length>0?((!o||!de||V||M)&&x(de?$():j),j):$()})}var T=!1,z=((a&Yc)!==0?Ro:di)(()=>(T=!1,$()));l&&r(z);var I=Nt;return(function(j,de){if(arguments.length>0){const pe=de?r(z):o&&l?Ut(j):j;return u(z,pe),T=!0,d!==void 0&&(d=pe),j}return bn&&T||(I.f&qa)!==0?z.v:r(z)})}const pv="5";var fl;typeof window<"u"&&((fl=window.__svelte??(window.__svelte={})).v??(fl.v=new Set)).add(pv);const Ur="";async function mv(){const e=await fetch(`${Ur}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function xv(e,t=null,a=null){const n={provider:e};t&&(n.model=t),a&&(n.api_key=a);const o=await fetch(`${Ur}/api/provider/validate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)});if(!o.ok)throw new Error("설정 실패");return o.json()}async function hv(e){const t=await fetch(`${Ur}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function gv(e,{onProgress:t,onDone:a,onError:n}){const o=new AbortController;return fetch(`${Ur}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:o.signal}).then(async l=>{if(!l.ok){n==null||n("다운로드 실패");return}const s=l.body.getReader(),d=new TextDecoder;let v="";for(;;){const{done:m,value:x}=await s.read();if(m)break;v+=d.decode(x,{stream:!0});const h=v.split(`
`);v=h.pop()||"";for(const _ of h)if(_.startsWith("data:"))try{const M=JSON.parse(_.slice(5).trim());M.total&&M.completed!==void 0?t==null||t({total:M.total,completed:M.completed,status:M.status}):M.status&&(t==null||t({status:M.status}))}catch{}}a==null||a()}).catch(l=>{l.name!=="AbortError"&&(n==null||n(l.message))}),{abort:()=>o.abort()}}async function bv(){const e=await fetch(`${Ur}/api/codex/logout`,{method:"POST"});if(!e.ok)throw new Error("Codex 로그아웃 실패");return e.json()}async function _v(e,t=null,a=null){let n=`${Ur}/api/export/excel/${encodeURIComponent(e)}`;const o=new URLSearchParams;a?o.set("template_id",a):t&&t.length>0&&o.set("modules",t.join(","));const l=o.toString();l&&(n+=`?${l}`);const s=await fetch(n);if(!s.ok){const _=await s.json().catch(()=>({}));throw new Error(_.detail||"Excel 다운로드 실패")}const d=await s.blob(),m=(s.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),x=m?decodeURIComponent(m[1]):`${e}.xlsx`,h=document.createElement("a");return h.href=URL.createObjectURL(d),h.download=x,h.click(),URL.revokeObjectURL(h.href),x}async function bd(e){const t=await fetch(`${Ur}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}async function wv(e,t){const a=await fetch(`${Ur}/api/company/${e}/show/${encodeURIComponent(t)}/all`);if(!a.ok)throw new Error("company topic 일괄 조회 실패");return a.json()}async function yv(e){const t=await fetch(`${Ur}/api/company/${e}/sections`);if(!t.ok)throw new Error("sections 조회 실패");return t.json()}async function kv(e){const t=await fetch(`${Ur}/api/company/${e}/toc`);if(!t.ok)throw new Error("목차 조회 실패");return t.json()}async function $v(e,t,a=null){const n=a?`?period=${encodeURIComponent(a)}`:"",o=await fetch(`${Ur}/api/company/${e}/viewer/${encodeURIComponent(t)}${n}`);if(!o.ok)throw new Error("viewer 조회 실패");return o.json()}async function Cv(e,t){const a=await fetch(`${Ur}/api/company/${e}/diff/${encodeURIComponent(t)}/summary`);if(!a.ok)throw new Error("diff summary 조회 실패");return a.json()}async function Sv(e,t,a,n){const o=new URLSearchParams({from:a,to:n}),l=await fetch(`${Ur}/api/company/${e}/diff/${encodeURIComponent(t)}?${o}`);if(!l.ok)throw new Error("topic diff 조회 실패");return l.json()}async function Tv(e,t){const a=new URLSearchParams({q:t}),n=await fetch(`${Ur}/api/company/${encodeURIComponent(e)}/search?${a}`);if(!n.ok)throw new Error("검색 실패");return n.json()}async function Mv(e){const t=await fetch(`${Ur}/api/company/${encodeURIComponent(e)}/insights`);if(!t.ok)throw new Error("인사이트 조회 실패");return t.json()}function zv(e,t,{onContext:a,onChunk:n,onDone:o,onError:l}){const s=new AbortController;return fetch(`${Ur}/api/company/${encodeURIComponent(e)}/summary/${encodeURIComponent(t)}`,{signal:s.signal}).then(async d=>{if(!d.ok){l==null||l("요약 생성 실패");return}const v=d.body.getReader(),m=new TextDecoder;let x="",h=null;for(;;){const{done:_,value:M}=await v.read();if(_)break;x+=m.decode(M,{stream:!0});const $=x.split(`
`);x=$.pop()||"";for(const V of $)if(V.startsWith("event:"))h=V.slice(6).trim();else if(V.startsWith("data:")&&h){try{const T=JSON.parse(V.slice(5).trim());h==="context"?a==null||a(T):h==="chunk"?n==null||n(T.text):h==="error"?l==null||l(T.error):h==="done"&&(o==null||o())}catch{}h=null}}o==null||o()}).catch(d=>{d.name!=="AbortError"&&(l==null||l(d.message))}),{abort:()=>s.abort()}}function Av(e,t,a={},{onMeta:n,onSnapshot:o,onContext:l,onSystemPrompt:s,onToolCall:d,onToolResult:v,onChart:m,onChunk:x,onDone:h,onError:_,onViewerNavigate:M},$=null){const V={question:t,stream:!0,...a};e&&(V.company=e),$&&$.length>0&&(V.history=$);const T=new AbortController;return fetch(`${Ur}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(V),signal:T.signal}).then(async z=>{if(!z.ok){const F=await z.json().catch(()=>({}));_==null||_(F.detail||"스트리밍 실패");return}const I=z.body.getReader(),D=new TextDecoder;let j="",de=!1,pe=null;for(;;){const{done:F,value:k}=await I.read();if(F)break;j+=D.decode(k,{stream:!0});const G=j.split(`
`);j=G.pop()||"";for(const N of G)if(N.startsWith("event:"))pe=N.slice(6).trim();else if(N.startsWith("data:")&&pe){const re=N.slice(5).trim();try{const P=JSON.parse(re);pe==="meta"?n==null||n(P):pe==="snapshot"?o==null||o(P):pe==="context"?l==null||l(P):pe==="system_prompt"?s==null||s(P):pe==="tool_call"?d==null||d(P):pe==="tool_result"?v==null||v(P):pe==="chunk"?x==null||x(P.text):pe==="chart"?m==null||m(P):pe==="viewer_navigate"?M==null||M(P):pe==="error"?_==null||_(P.error,P.action,P.detail):pe==="done"&&(de||(de=!0,h==null||h()))}catch{}pe=null}}de||(de=!0,h==null||h())}).catch(z=>{z.name!=="AbortError"&&(_==null||_(z.message))}),{abort:()=>T.abort()}}const Ev=(e,t)=>{const a=new Array(e.length+t.length);for(let n=0;n<e.length;n++)a[n]=e[n];for(let n=0;n<t.length;n++)a[e.length+n]=t[n];return a},Iv=(e,t)=>({classGroupId:e,validator:t}),_d=(e=new Map,t=null,a)=>({nextPart:e,validators:t,classGroupId:a}),os="-",Wi=[],Pv="arbitrary..",Nv=e=>{const t=Ov(e),{conflictingClassGroups:a,conflictingClassGroupModifiers:n}=e;return{getClassGroupId:s=>{if(s.startsWith("[")&&s.endsWith("]"))return Lv(s);const d=s.split(os),v=d[0]===""&&d.length>1?1:0;return wd(d,v,t)},getConflictingClassGroupIds:(s,d)=>{if(d){const v=n[s],m=a[s];return v?m?Ev(m,v):v:m||Wi}return a[s]||Wi}}},wd=(e,t,a)=>{if(e.length-t===0)return a.classGroupId;const o=e[t],l=a.nextPart.get(o);if(l){const m=wd(e,t+1,l);if(m)return m}const s=a.validators;if(s===null)return;const d=t===0?e.join(os):e.slice(t).join(os),v=s.length;for(let m=0;m<v;m++){const x=s[m];if(x.validator(d))return x.classGroupId}},Lv=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),a=t.indexOf(":"),n=t.slice(0,a);return n?Pv+n:void 0})(),Ov=e=>{const{theme:t,classGroups:a}=e;return Rv(a,t)},Rv=(e,t)=>{const a=_d();for(const n in e){const o=e[n];hi(o,a,n,t)}return a},hi=(e,t,a,n)=>{const o=e.length;for(let l=0;l<o;l++){const s=e[l];Dv(s,t,a,n)}},Dv=(e,t,a,n)=>{if(typeof e=="string"){jv(e,t,a);return}if(typeof e=="function"){Vv(e,t,a,n);return}qv(e,t,a,n)},jv=(e,t,a)=>{const n=e===""?t:yd(t,e);n.classGroupId=a},Vv=(e,t,a,n)=>{if(Bv(e)){hi(e(n),t,a,n);return}t.validators===null&&(t.validators=[]),t.validators.push(Iv(a,e))},qv=(e,t,a,n)=>{const o=Object.entries(e),l=o.length;for(let s=0;s<l;s++){const[d,v]=o[s];hi(v,yd(t,d),a,n)}},yd=(e,t)=>{let a=e;const n=t.split(os),o=n.length;for(let l=0;l<o;l++){const s=n[l];let d=a.nextPart.get(s);d||(d=_d(),a.nextPart.set(s,d)),a=d}return a},Bv=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,Fv=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,a=Object.create(null),n=Object.create(null);const o=(l,s)=>{a[l]=s,t++,t>e&&(t=0,n=a,a=Object.create(null))};return{get(l){let s=a[l];if(s!==void 0)return s;if((s=n[l])!==void 0)return o(l,s),s},set(l,s){l in a?a[l]=s:o(l,s)}}},Ws="!",Yi=":",Hv=[],Ji=(e,t,a,n,o)=>({modifiers:e,hasImportantModifier:t,baseClassName:a,maybePostfixModifierPosition:n,isExternal:o}),Uv=e=>{const{prefix:t,experimentalParseClassName:a}=e;let n=o=>{const l=[];let s=0,d=0,v=0,m;const x=o.length;for(let V=0;V<x;V++){const T=o[V];if(s===0&&d===0){if(T===Yi){l.push(o.slice(v,V)),v=V+1;continue}if(T==="/"){m=V;continue}}T==="["?s++:T==="]"?s--:T==="("?d++:T===")"&&d--}const h=l.length===0?o:o.slice(v);let _=h,M=!1;h.endsWith(Ws)?(_=h.slice(0,-1),M=!0):h.startsWith(Ws)&&(_=h.slice(1),M=!0);const $=m&&m>v?m-v:void 0;return Ji(l,M,_,$)};if(t){const o=t+Yi,l=n;n=s=>s.startsWith(o)?l(s.slice(o.length)):Ji(Hv,!1,s,void 0,!0)}if(a){const o=n;n=l=>a({className:l,parseClassName:o})}return n},Kv=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((a,n)=>{t.set(a,1e6+n)}),a=>{const n=[];let o=[];for(let l=0;l<a.length;l++){const s=a[l],d=s[0]==="[",v=t.has(s);d||v?(o.length>0&&(o.sort(),n.push(...o),o=[]),n.push(s)):o.push(s)}return o.length>0&&(o.sort(),n.push(...o)),n}},Gv=e=>({cache:Fv(e.cacheSize),parseClassName:Uv(e),sortModifiers:Kv(e),...Nv(e)}),Wv=/\s+/,Yv=(e,t)=>{const{parseClassName:a,getClassGroupId:n,getConflictingClassGroupIds:o,sortModifiers:l}=t,s=[],d=e.trim().split(Wv);let v="";for(let m=d.length-1;m>=0;m-=1){const x=d[m],{isExternal:h,modifiers:_,hasImportantModifier:M,baseClassName:$,maybePostfixModifierPosition:V}=a(x);if(h){v=x+(v.length>0?" "+v:v);continue}let T=!!V,z=n(T?$.substring(0,V):$);if(!z){if(!T){v=x+(v.length>0?" "+v:v);continue}if(z=n($),!z){v=x+(v.length>0?" "+v:v);continue}T=!1}const I=_.length===0?"":_.length===1?_[0]:l(_).join(":"),D=M?I+Ws:I,j=D+z;if(s.indexOf(j)>-1)continue;s.push(j);const de=o(z,T);for(let pe=0;pe<de.length;++pe){const F=de[pe];s.push(D+F)}v=x+(v.length>0?" "+v:v)}return v},Jv=(...e)=>{let t=0,a,n,o="";for(;t<e.length;)(a=e[t++])&&(n=kd(a))&&(o&&(o+=" "),o+=n);return o},kd=e=>{if(typeof e=="string")return e;let t,a="";for(let n=0;n<e.length;n++)e[n]&&(t=kd(e[n]))&&(a&&(a+=" "),a+=t);return a},Xv=(e,...t)=>{let a,n,o,l;const s=v=>{const m=t.reduce((x,h)=>h(x),e());return a=Gv(m),n=a.cache.get,o=a.cache.set,l=d,d(v)},d=v=>{const m=n(v);if(m)return m;const x=Yv(v,a);return o(v,x),x};return l=s,(...v)=>l(Jv(...v))},Qv=[],zr=e=>{const t=a=>a[e]||Qv;return t.isThemeGetter=!0,t},$d=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Cd=/^\((?:(\w[\w-]*):)?(.+)\)$/i,Zv=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,ef=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,tf=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,rf=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,af=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,nf=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,sn=e=>Zv.test(e),Mt=e=>!!e&&!Number.isNaN(Number(e)),ln=e=>!!e&&Number.isInteger(Number(e)),Ms=e=>e.endsWith("%")&&Mt(e.slice(0,-1)),Ga=e=>ef.test(e),Sd=()=>!0,of=e=>tf.test(e)&&!rf.test(e),gi=()=>!1,sf=e=>af.test(e),lf=e=>nf.test(e),df=e=>!Le(e)&&!Oe(e),cf=e=>$n(e,zd,gi),Le=e=>$d.test(e),Mn=e=>$n(e,Ad,of),Xi=e=>$n(e,gf,Mt),uf=e=>$n(e,Id,Sd),vf=e=>$n(e,Ed,gi),Qi=e=>$n(e,Td,gi),ff=e=>$n(e,Md,lf),Ko=e=>$n(e,Pd,sf),Oe=e=>Cd.test(e),$o=e=>Gn(e,Ad),pf=e=>Gn(e,Ed),Zi=e=>Gn(e,Td),mf=e=>Gn(e,zd),xf=e=>Gn(e,Md),Go=e=>Gn(e,Pd,!0),hf=e=>Gn(e,Id,!0),$n=(e,t,a)=>{const n=$d.exec(e);return n?n[1]?t(n[1]):a(n[2]):!1},Gn=(e,t,a=!1)=>{const n=Cd.exec(e);return n?n[1]?t(n[1]):a:!1},Td=e=>e==="position"||e==="percentage",Md=e=>e==="image"||e==="url",zd=e=>e==="length"||e==="size"||e==="bg-size",Ad=e=>e==="length",gf=e=>e==="number",Ed=e=>e==="family-name",Id=e=>e==="number"||e==="weight",Pd=e=>e==="shadow",bf=()=>{const e=zr("color"),t=zr("font"),a=zr("text"),n=zr("font-weight"),o=zr("tracking"),l=zr("leading"),s=zr("breakpoint"),d=zr("container"),v=zr("spacing"),m=zr("radius"),x=zr("shadow"),h=zr("inset-shadow"),_=zr("text-shadow"),M=zr("drop-shadow"),$=zr("blur"),V=zr("perspective"),T=zr("aspect"),z=zr("ease"),I=zr("animate"),D=()=>["auto","avoid","all","avoid-page","page","left","right","column"],j=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],de=()=>[...j(),Oe,Le],pe=()=>["auto","hidden","clip","visible","scroll"],F=()=>["auto","contain","none"],k=()=>[Oe,Le,v],G=()=>[sn,"full","auto",...k()],N=()=>[ln,"none","subgrid",Oe,Le],re=()=>["auto",{span:["full",ln,Oe,Le]},ln,Oe,Le],P=()=>[ln,"auto",Oe,Le],me=()=>["auto","min","max","fr",Oe,Le],E=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],B=()=>["start","end","center","stretch","center-safe","end-safe"],oe=()=>["auto",...k()],fe=()=>[sn,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...k()],he=()=>[sn,"screen","full","dvw","lvw","svw","min","max","fit",...k()],xe=()=>[sn,"screen","full","lh","dvh","lvh","svh","min","max","fit",...k()],se=()=>[e,Oe,Le],we=()=>[...j(),Zi,Qi,{position:[Oe,Le]}],Q=()=>["no-repeat",{repeat:["","x","y","space","round"]}],O=()=>["auto","cover","contain",mf,cf,{size:[Oe,Le]}],ee=()=>[Ms,$o,Mn],W=()=>["","none","full",m,Oe,Le],q=()=>["",Mt,$o,Mn],ue=()=>["solid","dashed","dotted","double"],ze=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],Z=()=>[Mt,Ms,Zi,Qi],Fe=()=>["","none",$,Oe,Le],dt=()=>["none",Mt,Oe,Le],nt=()=>["none",Mt,Oe,Le],Ye=()=>[Mt,Oe,Le],zt=()=>[sn,"full",...k()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Ga],breakpoint:[Ga],color:[Sd],container:[Ga],"drop-shadow":[Ga],ease:["in","out","in-out"],font:[df],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Ga],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Ga],shadow:[Ga],spacing:["px",Mt],text:[Ga],"text-shadow":[Ga],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",sn,Le,Oe,T]}],container:["container"],columns:[{columns:[Mt,Le,Oe,d]}],"break-after":[{"break-after":D()}],"break-before":[{"break-before":D()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:de()}],overflow:[{overflow:pe()}],"overflow-x":[{"overflow-x":pe()}],"overflow-y":[{"overflow-y":pe()}],overscroll:[{overscroll:F()}],"overscroll-x":[{"overscroll-x":F()}],"overscroll-y":[{"overscroll-y":F()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:G()}],"inset-x":[{"inset-x":G()}],"inset-y":[{"inset-y":G()}],start:[{"inset-s":G(),start:G()}],end:[{"inset-e":G(),end:G()}],"inset-bs":[{"inset-bs":G()}],"inset-be":[{"inset-be":G()}],top:[{top:G()}],right:[{right:G()}],bottom:[{bottom:G()}],left:[{left:G()}],visibility:["visible","invisible","collapse"],z:[{z:[ln,"auto",Oe,Le]}],basis:[{basis:[sn,"full","auto",d,...k()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[Mt,sn,"auto","initial","none",Le]}],grow:[{grow:["",Mt,Oe,Le]}],shrink:[{shrink:["",Mt,Oe,Le]}],order:[{order:[ln,"first","last","none",Oe,Le]}],"grid-cols":[{"grid-cols":N()}],"col-start-end":[{col:re()}],"col-start":[{"col-start":P()}],"col-end":[{"col-end":P()}],"grid-rows":[{"grid-rows":N()}],"row-start-end":[{row:re()}],"row-start":[{"row-start":P()}],"row-end":[{"row-end":P()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":me()}],"auto-rows":[{"auto-rows":me()}],gap:[{gap:k()}],"gap-x":[{"gap-x":k()}],"gap-y":[{"gap-y":k()}],"justify-content":[{justify:[...E(),"normal"]}],"justify-items":[{"justify-items":[...B(),"normal"]}],"justify-self":[{"justify-self":["auto",...B()]}],"align-content":[{content:["normal",...E()]}],"align-items":[{items:[...B(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...B(),{baseline:["","last"]}]}],"place-content":[{"place-content":E()}],"place-items":[{"place-items":[...B(),"baseline"]}],"place-self":[{"place-self":["auto",...B()]}],p:[{p:k()}],px:[{px:k()}],py:[{py:k()}],ps:[{ps:k()}],pe:[{pe:k()}],pbs:[{pbs:k()}],pbe:[{pbe:k()}],pt:[{pt:k()}],pr:[{pr:k()}],pb:[{pb:k()}],pl:[{pl:k()}],m:[{m:oe()}],mx:[{mx:oe()}],my:[{my:oe()}],ms:[{ms:oe()}],me:[{me:oe()}],mbs:[{mbs:oe()}],mbe:[{mbe:oe()}],mt:[{mt:oe()}],mr:[{mr:oe()}],mb:[{mb:oe()}],ml:[{ml:oe()}],"space-x":[{"space-x":k()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":k()}],"space-y-reverse":["space-y-reverse"],size:[{size:fe()}],"inline-size":[{inline:["auto",...he()]}],"min-inline-size":[{"min-inline":["auto",...he()]}],"max-inline-size":[{"max-inline":["none",...he()]}],"block-size":[{block:["auto",...xe()]}],"min-block-size":[{"min-block":["auto",...xe()]}],"max-block-size":[{"max-block":["none",...xe()]}],w:[{w:[d,"screen",...fe()]}],"min-w":[{"min-w":[d,"screen","none",...fe()]}],"max-w":[{"max-w":[d,"screen","none","prose",{screen:[s]},...fe()]}],h:[{h:["screen","lh",...fe()]}],"min-h":[{"min-h":["screen","lh","none",...fe()]}],"max-h":[{"max-h":["screen","lh",...fe()]}],"font-size":[{text:["base",a,$o,Mn]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[n,hf,uf]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",Ms,Le]}],"font-family":[{font:[pf,vf,t]}],"font-features":[{"font-features":[Le]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[o,Oe,Le]}],"line-clamp":[{"line-clamp":[Mt,"none",Oe,Xi]}],leading:[{leading:[l,...k()]}],"list-image":[{"list-image":["none",Oe,Le]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",Oe,Le]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:se()}],"text-color":[{text:se()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...ue(),"wavy"]}],"text-decoration-thickness":[{decoration:[Mt,"from-font","auto",Oe,Mn]}],"text-decoration-color":[{decoration:se()}],"underline-offset":[{"underline-offset":[Mt,"auto",Oe,Le]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:k()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",Oe,Le]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",Oe,Le]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:we()}],"bg-repeat":[{bg:Q()}],"bg-size":[{bg:O()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},ln,Oe,Le],radial:["",Oe,Le],conic:[ln,Oe,Le]},xf,ff]}],"bg-color":[{bg:se()}],"gradient-from-pos":[{from:ee()}],"gradient-via-pos":[{via:ee()}],"gradient-to-pos":[{to:ee()}],"gradient-from":[{from:se()}],"gradient-via":[{via:se()}],"gradient-to":[{to:se()}],rounded:[{rounded:W()}],"rounded-s":[{"rounded-s":W()}],"rounded-e":[{"rounded-e":W()}],"rounded-t":[{"rounded-t":W()}],"rounded-r":[{"rounded-r":W()}],"rounded-b":[{"rounded-b":W()}],"rounded-l":[{"rounded-l":W()}],"rounded-ss":[{"rounded-ss":W()}],"rounded-se":[{"rounded-se":W()}],"rounded-ee":[{"rounded-ee":W()}],"rounded-es":[{"rounded-es":W()}],"rounded-tl":[{"rounded-tl":W()}],"rounded-tr":[{"rounded-tr":W()}],"rounded-br":[{"rounded-br":W()}],"rounded-bl":[{"rounded-bl":W()}],"border-w":[{border:q()}],"border-w-x":[{"border-x":q()}],"border-w-y":[{"border-y":q()}],"border-w-s":[{"border-s":q()}],"border-w-e":[{"border-e":q()}],"border-w-bs":[{"border-bs":q()}],"border-w-be":[{"border-be":q()}],"border-w-t":[{"border-t":q()}],"border-w-r":[{"border-r":q()}],"border-w-b":[{"border-b":q()}],"border-w-l":[{"border-l":q()}],"divide-x":[{"divide-x":q()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":q()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...ue(),"hidden","none"]}],"divide-style":[{divide:[...ue(),"hidden","none"]}],"border-color":[{border:se()}],"border-color-x":[{"border-x":se()}],"border-color-y":[{"border-y":se()}],"border-color-s":[{"border-s":se()}],"border-color-e":[{"border-e":se()}],"border-color-bs":[{"border-bs":se()}],"border-color-be":[{"border-be":se()}],"border-color-t":[{"border-t":se()}],"border-color-r":[{"border-r":se()}],"border-color-b":[{"border-b":se()}],"border-color-l":[{"border-l":se()}],"divide-color":[{divide:se()}],"outline-style":[{outline:[...ue(),"none","hidden"]}],"outline-offset":[{"outline-offset":[Mt,Oe,Le]}],"outline-w":[{outline:["",Mt,$o,Mn]}],"outline-color":[{outline:se()}],shadow:[{shadow:["","none",x,Go,Ko]}],"shadow-color":[{shadow:se()}],"inset-shadow":[{"inset-shadow":["none",h,Go,Ko]}],"inset-shadow-color":[{"inset-shadow":se()}],"ring-w":[{ring:q()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:se()}],"ring-offset-w":[{"ring-offset":[Mt,Mn]}],"ring-offset-color":[{"ring-offset":se()}],"inset-ring-w":[{"inset-ring":q()}],"inset-ring-color":[{"inset-ring":se()}],"text-shadow":[{"text-shadow":["none",_,Go,Ko]}],"text-shadow-color":[{"text-shadow":se()}],opacity:[{opacity:[Mt,Oe,Le]}],"mix-blend":[{"mix-blend":[...ze(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":ze()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[Mt]}],"mask-image-linear-from-pos":[{"mask-linear-from":Z()}],"mask-image-linear-to-pos":[{"mask-linear-to":Z()}],"mask-image-linear-from-color":[{"mask-linear-from":se()}],"mask-image-linear-to-color":[{"mask-linear-to":se()}],"mask-image-t-from-pos":[{"mask-t-from":Z()}],"mask-image-t-to-pos":[{"mask-t-to":Z()}],"mask-image-t-from-color":[{"mask-t-from":se()}],"mask-image-t-to-color":[{"mask-t-to":se()}],"mask-image-r-from-pos":[{"mask-r-from":Z()}],"mask-image-r-to-pos":[{"mask-r-to":Z()}],"mask-image-r-from-color":[{"mask-r-from":se()}],"mask-image-r-to-color":[{"mask-r-to":se()}],"mask-image-b-from-pos":[{"mask-b-from":Z()}],"mask-image-b-to-pos":[{"mask-b-to":Z()}],"mask-image-b-from-color":[{"mask-b-from":se()}],"mask-image-b-to-color":[{"mask-b-to":se()}],"mask-image-l-from-pos":[{"mask-l-from":Z()}],"mask-image-l-to-pos":[{"mask-l-to":Z()}],"mask-image-l-from-color":[{"mask-l-from":se()}],"mask-image-l-to-color":[{"mask-l-to":se()}],"mask-image-x-from-pos":[{"mask-x-from":Z()}],"mask-image-x-to-pos":[{"mask-x-to":Z()}],"mask-image-x-from-color":[{"mask-x-from":se()}],"mask-image-x-to-color":[{"mask-x-to":se()}],"mask-image-y-from-pos":[{"mask-y-from":Z()}],"mask-image-y-to-pos":[{"mask-y-to":Z()}],"mask-image-y-from-color":[{"mask-y-from":se()}],"mask-image-y-to-color":[{"mask-y-to":se()}],"mask-image-radial":[{"mask-radial":[Oe,Le]}],"mask-image-radial-from-pos":[{"mask-radial-from":Z()}],"mask-image-radial-to-pos":[{"mask-radial-to":Z()}],"mask-image-radial-from-color":[{"mask-radial-from":se()}],"mask-image-radial-to-color":[{"mask-radial-to":se()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":j()}],"mask-image-conic-pos":[{"mask-conic":[Mt]}],"mask-image-conic-from-pos":[{"mask-conic-from":Z()}],"mask-image-conic-to-pos":[{"mask-conic-to":Z()}],"mask-image-conic-from-color":[{"mask-conic-from":se()}],"mask-image-conic-to-color":[{"mask-conic-to":se()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:we()}],"mask-repeat":[{mask:Q()}],"mask-size":[{mask:O()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",Oe,Le]}],filter:[{filter:["","none",Oe,Le]}],blur:[{blur:Fe()}],brightness:[{brightness:[Mt,Oe,Le]}],contrast:[{contrast:[Mt,Oe,Le]}],"drop-shadow":[{"drop-shadow":["","none",M,Go,Ko]}],"drop-shadow-color":[{"drop-shadow":se()}],grayscale:[{grayscale:["",Mt,Oe,Le]}],"hue-rotate":[{"hue-rotate":[Mt,Oe,Le]}],invert:[{invert:["",Mt,Oe,Le]}],saturate:[{saturate:[Mt,Oe,Le]}],sepia:[{sepia:["",Mt,Oe,Le]}],"backdrop-filter":[{"backdrop-filter":["","none",Oe,Le]}],"backdrop-blur":[{"backdrop-blur":Fe()}],"backdrop-brightness":[{"backdrop-brightness":[Mt,Oe,Le]}],"backdrop-contrast":[{"backdrop-contrast":[Mt,Oe,Le]}],"backdrop-grayscale":[{"backdrop-grayscale":["",Mt,Oe,Le]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[Mt,Oe,Le]}],"backdrop-invert":[{"backdrop-invert":["",Mt,Oe,Le]}],"backdrop-opacity":[{"backdrop-opacity":[Mt,Oe,Le]}],"backdrop-saturate":[{"backdrop-saturate":[Mt,Oe,Le]}],"backdrop-sepia":[{"backdrop-sepia":["",Mt,Oe,Le]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":k()}],"border-spacing-x":[{"border-spacing-x":k()}],"border-spacing-y":[{"border-spacing-y":k()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",Oe,Le]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[Mt,"initial",Oe,Le]}],ease:[{ease:["linear","initial",z,Oe,Le]}],delay:[{delay:[Mt,Oe,Le]}],animate:[{animate:["none",I,Oe,Le]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[V,Oe,Le]}],"perspective-origin":[{"perspective-origin":de()}],rotate:[{rotate:dt()}],"rotate-x":[{"rotate-x":dt()}],"rotate-y":[{"rotate-y":dt()}],"rotate-z":[{"rotate-z":dt()}],scale:[{scale:nt()}],"scale-x":[{"scale-x":nt()}],"scale-y":[{"scale-y":nt()}],"scale-z":[{"scale-z":nt()}],"scale-3d":["scale-3d"],skew:[{skew:Ye()}],"skew-x":[{"skew-x":Ye()}],"skew-y":[{"skew-y":Ye()}],transform:[{transform:[Oe,Le,"","none","gpu","cpu"]}],"transform-origin":[{origin:de()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:zt()}],"translate-x":[{"translate-x":zt()}],"translate-y":[{"translate-y":zt()}],"translate-z":[{"translate-z":zt()}],"translate-none":["translate-none"],accent:[{accent:se()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:se()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",Oe,Le]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":k()}],"scroll-mx":[{"scroll-mx":k()}],"scroll-my":[{"scroll-my":k()}],"scroll-ms":[{"scroll-ms":k()}],"scroll-me":[{"scroll-me":k()}],"scroll-mbs":[{"scroll-mbs":k()}],"scroll-mbe":[{"scroll-mbe":k()}],"scroll-mt":[{"scroll-mt":k()}],"scroll-mr":[{"scroll-mr":k()}],"scroll-mb":[{"scroll-mb":k()}],"scroll-ml":[{"scroll-ml":k()}],"scroll-p":[{"scroll-p":k()}],"scroll-px":[{"scroll-px":k()}],"scroll-py":[{"scroll-py":k()}],"scroll-ps":[{"scroll-ps":k()}],"scroll-pe":[{"scroll-pe":k()}],"scroll-pbs":[{"scroll-pbs":k()}],"scroll-pbe":[{"scroll-pbe":k()}],"scroll-pt":[{"scroll-pt":k()}],"scroll-pr":[{"scroll-pr":k()}],"scroll-pb":[{"scroll-pb":k()}],"scroll-pl":[{"scroll-pl":k()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",Oe,Le]}],fill:[{fill:["none",...se()]}],"stroke-w":[{stroke:[Mt,$o,Mn,Xi]}],stroke:[{stroke:["none",...se()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},_f=Xv(bf);function cr(...e){return _f(fd(e))}const Ys="dartlab-conversations",el=50;function wf(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function yf(){try{const e=localStorage.getItem(Ys);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const kf=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function tl(e){return e.map(t=>({...t,messages:t.messages.map(a=>{if(a.role!=="assistant")return a;const n={};for(const[o,l]of Object.entries(a))kf.includes(o)||(n[o]=l);return n})}))}function rl(e){try{const t={conversations:tl(e.conversations),activeId:e.activeId};localStorage.setItem(Ys,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:tl(e.conversations),activeId:e.activeId};localStorage.setItem(Ys,JSON.stringify(t))}catch{}}}}function $f(){const e=yf(),t=e.conversations||[],a=t.find(z=>z.id===e.activeId)?e.activeId:null;let n=Y(Ut(t)),o=Y(Ut(a)),l=null;function s(){l&&clearTimeout(l),l=setTimeout(()=>{rl({conversations:r(n),activeId:r(o)}),l=null},300)}function d(){l&&clearTimeout(l),l=null,rl({conversations:r(n),activeId:r(o)})}function v(){return r(n).find(z=>z.id===r(o))||null}function m(){const z={id:wf(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return u(n,[z,...r(n)],!0),r(n).length>el&&u(n,r(n).slice(0,el),!0),u(o,z.id,!0),d(),z.id}function x(z){r(n).find(I=>I.id===z)&&(u(o,z,!0),d())}function h(z,I,D=null){const j=v();if(!j)return;const de={role:z,text:I};D&&(de.meta=D),j.messages=[...j.messages,de],j.updatedAt=Date.now(),j.title==="새 대화"&&z==="user"&&(j.title=I.length>30?I.slice(0,30)+"...":I),u(n,[...r(n)],!0),d()}function _(z){const I=v();if(!I||I.messages.length===0)return;const D=I.messages[I.messages.length-1];Object.assign(D,z),I.updatedAt=Date.now(),u(n,[...r(n)],!0),s()}function M(z){u(n,r(n).filter(I=>I.id!==z),!0),r(o)===z&&u(o,r(n).length>0?r(n)[0].id:null,!0),d()}function $(){const z=v();!z||z.messages.length===0||(z.messages=z.messages.slice(0,-1),z.updatedAt=Date.now(),u(n,[...r(n)],!0),d())}function V(z,I){const D=r(n).find(j=>j.id===z);D&&(D.title=I,u(n,[...r(n)],!0),d())}function T(){u(n,[],!0),u(o,null),d()}return{get conversations(){return r(n)},get activeId(){return r(o)},get active(){return v()},createConversation:m,setActive:x,addMessage:h,updateLastMessage:_,removeLastMessage:$,deleteConversation:M,updateTitle:V,clearAll:T,flush:d}}const Nd="dartlab-workspace",Cf=6;function Ld(){return typeof window<"u"&&typeof localStorage<"u"}function Sf(){if(!Ld())return{};try{const e=localStorage.getItem(Nd);return e?JSON.parse(e):{}}catch{return{}}}function Tf(e){Ld()&&localStorage.setItem(Nd,JSON.stringify(e))}function Mf(){const e=Sf();let t=Y("chat"),a=Y(!1),n=Y(null),o=Y(null),l=Y("explore"),s=Y(null),d=Y(null),v=Y(null),m=Y(null),x=Y(null),h=Y(Ut(e.selectedCompany||null)),_=Y(Ut(e.recentCompanies||[]));function M(){Tf({selectedCompany:r(h),recentCompanies:r(_)})}function $(N){if(!(N!=null&&N.stockCode))return;const re={stockCode:N.stockCode,corpName:N.corpName||N.company||N.stockCode,company:N.company||N.corpName||N.stockCode,market:N.market||""};u(_,[re,...r(_).filter(P=>P.stockCode!==re.stockCode)].slice(0,Cf),!0)}function V(N){u(t,N,!0)}function T(N){N&&(u(h,N,!0),$(N)),u(t,"viewer"),u(a,!1),M()}function z(N){u(n,"data"),u(o,N,!0),u(a,!0),k("explore")}function I(){u(a,!1)}function D(N){u(h,N,!0),N&&$(N),M()}function j(N,re){var P,me,E,B;!(N!=null&&N.company)&&!(N!=null&&N.stockCode)||(u(h,{...r(h)||{},...re||{},corpName:N.company||((P=r(h))==null?void 0:P.corpName)||(re==null?void 0:re.corpName)||(re==null?void 0:re.company),company:N.company||((me=r(h))==null?void 0:me.company)||(re==null?void 0:re.company)||(re==null?void 0:re.corpName),stockCode:N.stockCode||((E=r(h))==null?void 0:E.stockCode)||(re==null?void 0:re.stockCode),market:((B=r(h))==null?void 0:B.market)||(re==null?void 0:re.market)||""},!0),$(r(h)),M())}function de(N,re,P=null){u(v,N,!0),u(m,re||N,!0),u(x,P,!0)}function pe(N,re=null){u(n,"data"),u(a,!0),u(l,"evidence"),u(s,N,!0),u(d,Number.isInteger(re)?re:null,!0)}function F(){u(s,null),u(d,null)}function k(N){u(l,N||"explore",!0),r(l)!=="evidence"&&F()}function G(){return r(t)==="viewer"&&r(h)&&r(v)?{type:"viewer",company:r(h),topic:r(v),topicLabel:r(m),period:r(x)}:r(a)?r(n)==="viewer"&&r(h)?{type:"viewer",company:r(h),topic:r(v),topicLabel:r(m),period:r(x)}:r(n)==="data"&&r(o)?{type:"data",data:r(o)}:null:null}return{get activeView(){return r(t)},get panelOpen(){return r(a)},get panelMode(){return r(n)},get panelData(){return r(o)},get activeTab(){return r(l)},get activeEvidenceSection(){return r(s)},get selectedEvidenceIndex(){return r(d)},get selectedCompany(){return r(h)},get recentCompanies(){return r(_)},get viewerTopic(){return r(v)},get viewerTopicLabel(){return r(m)},get viewerPeriod(){return r(x)},switchView:V,openViewer:T,openData:z,openEvidence:pe,closePanel:I,selectCompany:D,setViewerTopic:de,clearEvidenceSelection:F,setTab:k,syncCompanyFromMessage:j,getViewContext:G}}function zf(){try{const e=localStorage.getItem("dartlab-bookmarks");return e?JSON.parse(e):{}}catch{return{}}}function Af(e){try{localStorage.setItem("dartlab-bookmarks",JSON.stringify(e))}catch{}}function Ef(){let e=Y(null),t=Y(null),a=Y(null),n=Y(!1),o=Y(null),l=Y(null),s=Y(Ut(new Set)),d=Y(null),v=Y(!1),m=Y(null),x=new Map,h=Y(null),_=Y(!1),M=Y(Ut(new Map)),$=Y(null),V=Y(Ut(zf()));async function T(N){var re,P;if(!(N===r(e)&&r(a))){u(e,N,!0),u(t,null),u(a,null),u(o,null),u(l,null),u(d,null),u(m,null),x=new Map,u(s,new Set,!0),u(h,null),u(M,new Map,!0),u(n,!0);try{const me=await kv(N);if(u(a,me,!0),u(t,me.corpName,!0),((re=me.chapters)==null?void 0:re.length)>0&&(u(s,new Set([me.chapters[0].chapter]),!0),((P=me.chapters[0].topics)==null?void 0:P.length)>0)){const E=me.chapters[0].topics[0];await D(E.topic,me.chapters[0].chapter)}z(N)}catch(me){console.error("TOC 로드 실패:",me)}u(n,!1)}}async function z(N){var re;if(((re=r(h))==null?void 0:re.stockCode)!==N){u(_,!0);try{const P=await Mv(N);P.available?u(h,P,!0):u(h,null)}catch{u(h,null)}u(_,!1)}}function I(N){u($,N||null,!0)}async function D(N,re){if(N!==r(o)){if(u(o,N,!0),u($,null),u(l,re,!0),re&&!r(s).has(re)&&u(s,new Set([...r(s),re]),!0),x.has(N)){u(d,x.get(N),!0);return}u(v,!0),u(d,null),u(m,null);try{const[P,me]=await Promise.allSettled([$v(r(e),N),Cv(r(e),N)]);P.status==="fulfilled"&&(u(d,P.value,!0),x.set(N,P.value)),me.status==="fulfilled"&&u(m,me.value,!0)}catch(P){console.error("Topic 로드 실패:",P)}u(v,!1)}}function j(N){const re=new Set(r(s));re.has(N)?re.delete(N):re.add(N),u(s,re,!0)}function de(N){return r(M).get(N)??null}function pe(N,re){const P=new Map(r(M));P.set(N,re),u(M,P,!0)}function F(){return r(V)[r(e)]||[]}function k(N){return(r(V)[r(e)]||[]).includes(N)}function G(N){const re=r(V)[r(e)]||[],P=re.includes(N)?re.filter(me=>me!==N):[N,...re];u(V,{...r(V),[r(e)]:P},!0),Af(r(V))}return{get stockCode(){return r(e)},get corpName(){return r(t)},get toc(){return r(a)},get tocLoading(){return r(n)},get selectedTopic(){return r(o)},get selectedChapter(){return r(l)},get expandedChapters(){return r(s)},get topicData(){return r(d)},get topicLoading(){return r(v)},get diffSummary(){return r(m)},get insightData(){return r(h)},get insightLoading(){return r(_)},get searchHighlight(){return r($)},loadCompany:T,setSearchHighlight:I,selectTopic:D,toggleChapter:j,getTopicSummary:de,setTopicSummary:pe,getBookmarks:F,isBookmarked:k,toggleBookmark:G}}var If=f("<a><!></a>"),Pf=f("<button><!></button>");function Nf(e,t){Cr(t,!0);let a=Ie(t,"variant",3,"default"),n=Ie(t,"size",3,"default"),o=uv(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const l={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},s={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var d=_e(),v=ae(d);{var m=h=>{var _=If();ns(_,$=>({class:$,...o}),[()=>cr("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",l[a()],s[n()],t.class)]);var M=i(_);Gs(M,()=>t.children),c(h,_)},x=h=>{var _=Pf();ns(_,$=>({class:$,...o}),[()=>cr("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",l[a()],s[n()],t.class)]);var M=i(_);Gs(M,()=>t.children),c(h,_)};b(v,h=>{t.href?h(m):h(x,-1)})}c(e,d),Sr()}su();/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Lf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Of=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const al=(...e)=>e.filter((t,a,n)=>!!t&&t.trim()!==""&&n.indexOf(t)===a).join(" ").trim();var Rf=Uu("<svg><!><!></svg>");function it(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]),n=tt(a,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);Cr(t,!1);let o=Ie(t,"name",8,void 0),l=Ie(t,"color",8,"currentColor"),s=Ie(t,"size",8,24),d=Ie(t,"strokeWidth",8,2),v=Ie(t,"absoluteStrokeWidth",8,!1),m=Ie(t,"iconNode",24,()=>[]);lv();var x=Rf();ns(x,(M,$,V)=>({...Lf,...M,...n,width:s(),height:s(),stroke:l(),"stroke-width":$,class:V}),[()=>Of(n)?void 0:{"aria-hidden":"true"},()=>(zn(v()),zn(d()),zn(s()),Hn(()=>v()?Number(d())*24/Number(s()):d())),()=>(zn(al),zn(o()),zn(a),Hn(()=>al("lucide-icon","lucide",o()?`lucide-${o()}`:"",a.class)))]);var h=i(x);Ce(h,1,m,Te,(M,$)=>{var V=L(()=>si(r($),2));let T=()=>r(V)[0],z=()=>r(V)[1];var I=_e(),D=ae(I);ev(D,T,!0,(j,de)=>{ns(j,()=>({...z()}))}),c(M,I)});var _=p(h);at(_,t,"default",{}),c(e,x),Sr()}function Df(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];it(e,st({name:"activity"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Od(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M8 3 4 7l4 4"}],["path",{d:"M4 7h16"}],["path",{d:"m16 21 4-4-4-4"}],["path",{d:"M20 17H4"}]];it(e,st({name:"arrow-left-right"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function jf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M5 12h14"}],["path",{d:"m12 5 7 7-7 7"}]];it(e,st({name:"arrow-right"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Vf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];it(e,st({name:"arrow-up"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Js(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 7v14"}],["path",{d:"M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"}]];it(e,st({name:"book-open"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function zs(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];it(e,st({name:"brain"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ss(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]];it(e,st({name:"chart-column"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Xs(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M20 6 9 17l-5-5"}]];it(e,st({name:"check"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Rd(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m6 9 6 6 6-6"}]];it(e,st({name:"chevron-down"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function qf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m18 15-6-6-6 6"}]];it(e,st({name:"chevron-up"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Dd(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m9 18 6-6-6-6"}]];it(e,st({name:"chevron-right"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function An(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];it(e,st({name:"circle-alert"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Eo(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];it(e,st({name:"circle-check"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function is(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];it(e,st({name:"clock"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Bf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];it(e,st({name:"code"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ff(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];it(e,st({name:"coffee"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function nl(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]];it(e,st({name:"copy"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Co(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];it(e,st({name:"database"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Io(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];it(e,st({name:"download"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Hf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["line",{x1:"5",x2:"19",y1:"9",y2:"9"}],["line",{x1:"5",x2:"19",y1:"15",y2:"15"}]];it(e,st({name:"equal"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ol(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];it(e,st({name:"external-link"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Uf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];it(e,st({name:"eye"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ca(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];it(e,st({name:"file-text"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Kf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];it(e,st({name:"github"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function sl(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];it(e,st({name:"key"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Gf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 8h.01"}],["path",{d:"M12 12h.01"}],["path",{d:"M14 8h.01"}],["path",{d:"M16 12h.01"}],["path",{d:"M18 8h.01"}],["path",{d:"M6 8h.01"}],["path",{d:"M7 16h10"}],["path",{d:"M8 12h.01"}],["rect",{width:"20",height:"16",x:"2",y:"4",rx:"2"}]];it(e,st({name:"keyboard"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Nr(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];it(e,st({name:"loader-circle"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Wf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];it(e,st({name:"log-out"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function jd(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 3h6v6"}],["path",{d:"m21 3-7 7"}],["path",{d:"m3 21 7-7"}],["path",{d:"M9 21H3v-6"}]];it(e,st({name:"maximize-2"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Yf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];it(e,st({name:"menu"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ls(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];it(e,st({name:"message-square"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Vd(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m14 10 7-7"}],["path",{d:"M20 10h-6V4"}],["path",{d:"m3 21 7-7"}],["path",{d:"M4 14h6v6"}]];it(e,st({name:"minimize-2"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function qd(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M5 12h14"}]];it(e,st({name:"minus"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Jf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];it(e,st({name:"panel-left-close"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Qs(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];it(e,st({name:"plus"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Xf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];it(e,st({name:"refresh-cw"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function gn(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];it(e,st({name:"search"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Qf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];it(e,st({name:"settings"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Zf(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"}]];it(e,st({name:"shield"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Bd(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];it(e,st({name:"sparkles"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ep(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];it(e,st({name:"square"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Zs(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"}]];it(e,st({name:"star"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ei(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];it(e,st({name:"table-2"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function tp(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];it(e,st({name:"terminal"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function rp(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];it(e,st({name:"trash-2"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Xo(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M16 7h6v6"}],["path",{d:"m22 7-8.5 8.5-5-5L2 17"}]];it(e,st({name:"trending-up"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Qo(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];it(e,st({name:"triangle-alert"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ap(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["path",{d:"M16 3.128a4 4 0 0 1 0 7.744"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87"}],["circle",{cx:"9",cy:"7",r:"4"}]];it(e,st({name:"users"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function np(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"}],["path",{d:"M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"}]];it(e,st({name:"wallet"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function il(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];it(e,st({name:"wrench"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function wn(e,t){const a=tt(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];it(e,st({name:"x"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=_e(),d=ae(s);at(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}var op=f("<!> 새 대화",1),sp=f('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),ip=f('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),lp=f('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),dp=f('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40"><span class="text-[10px] text-dl-text-dim font-mono"> </span></div>'),cp=f('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),up=f("<button><!></button>"),vp=f('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),fp=f("<aside><!></aside>");function pp(e,t){Cr(t,!0);let a=Ie(t,"conversations",19,()=>[]),n=Ie(t,"activeId",3,null),o=Ie(t,"open",3,!0),l=Ie(t,"version",3,""),s=Y("");function d($){const V=new Date().setHours(0,0,0,0),T=V-864e5,z=V-7*864e5,I={오늘:[],어제:[],"이번 주":[],이전:[]};for(const j of $)j.updatedAt>=V?I.오늘.push(j):j.updatedAt>=T?I.어제.push(j):j.updatedAt>=z?I["이번 주"].push(j):I.이전.push(j);const D=[];for(const[j,de]of Object.entries(I))de.length>0&&D.push({label:j,items:de});return D}let v=L(()=>r(s).trim()?a().filter($=>$.title.toLowerCase().includes(r(s).toLowerCase())):a()),m=L(()=>d(r(v)));var x=fp(),h=i(x);{var _=$=>{var V=cp(),T=p(i(V),2),z=i(T);Nf(z,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(F,k)=>{var G=op(),N=ae(G);Qs(N,{size:16}),c(F,G)},$$slots:{default:!0}});var I=p(T,2);{var D=F=>{var k=sp(),G=i(k),N=i(G);gn(N,{size:12,class:"text-dl-text-dim flex-shrink-0"});var re=p(N,2);Ln(re,()=>r(s),P=>u(s,P)),c(F,k)};b(I,F=>{a().length>3&&F(D)})}var j=p(I,2);Ce(j,21,()=>r(m),Te,(F,k)=>{var G=lp(),N=i(G),re=i(N),P=p(N,2);Ce(P,17,()=>r(k).items,Te,(me,E)=>{var B=ip(),oe=i(B),fe=i(oe);ls(fe,{size:14,class:"flex-shrink-0 opacity-50"});var he=p(fe,2),xe=i(he),se=p(oe,2),we=i(se);rp(we,{size:12}),S(Q=>{Re(B,1,Q),ua(oe,"aria-current",r(E).id===n()?"true":void 0),C(xe,r(E).title),ua(se,"aria-label",`${r(E).title} 삭제`)},[()=>rr(cr("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",r(E).id===n()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),ce("click",oe,()=>{var Q;return(Q=t.onSelect)==null?void 0:Q.call(t,r(E).id)}),ce("click",se,Q=>{var O;Q.stopPropagation(),(O=t.onDelete)==null||O.call(t,r(E).id)}),c(me,B)}),S(()=>C(re,r(k).label)),c(F,G)});var de=p(j,2);{var pe=F=>{var k=dp(),G=i(k),N=i(G);S(()=>C(N,`v${l()??""}`)),c(F,k)};b(de,F=>{l()&&F(pe)})}c($,V)},M=$=>{var V=vp(),T=p(i(V),2),z=i(T);Qs(z,{size:18});var I=p(T,2);Ce(I,21,()=>a().slice(0,10),Te,(D,j)=>{var de=up(),pe=i(de);ls(pe,{size:16}),S(F=>{Re(de,1,F),ua(de,"title",r(j).title)},[()=>rr(cr("p-2 rounded-lg transition-colors w-full flex justify-center",r(j).id===n()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),ce("click",de,()=>{var F;return(F=t.onSelect)==null?void 0:F.call(t,r(j).id)}),c(D,de)}),ce("click",T,function(...D){var j;(j=t.onNewChat)==null||j.apply(this,D)}),c($,V)};b(h,$=>{o()?$(_):$(M,-1)})}S($=>Re(x,1,$),[()=>rr(cr("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",o()?"w-[260px]":"w-[52px]"))]),c(e,x),Sr()}Hr(["click"]);var mp=f('<button class="send-btn active"><!></button>'),xp=f("<button><!></button>"),hp=f('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),gp=f('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),bp=f('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),_p=f('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function Fd(e,t){Cr(t,!0);let a=Ie(t,"inputText",15,""),n=Ie(t,"isLoading",3,!1),o=Ie(t,"large",3,!1),l=Ie(t,"placeholder",3,"메시지를 입력하세요..."),s=Y(Ut([])),d=Y(!1),v=Y(-1),m=null,x=Y(void 0);function h(k){var G;if(r(d)&&r(s).length>0){if(k.key==="ArrowDown"){k.preventDefault(),u(v,(r(v)+1)%r(s).length);return}if(k.key==="ArrowUp"){k.preventDefault(),u(v,r(v)<=0?r(s).length-1:r(v)-1,!0);return}if(k.key==="Enter"&&r(v)>=0){k.preventDefault(),$(r(s)[r(v)]);return}if(k.key==="Escape"){u(d,!1),u(v,-1);return}}k.key==="Enter"&&!k.shiftKey&&(k.preventDefault(),u(d,!1),(G=t.onSend)==null||G.call(t))}function _(k){k.target.style.height="auto",k.target.style.height=Math.min(k.target.scrollHeight,200)+"px"}function M(k){_(k);const G=a();m&&clearTimeout(m),G.length>=2&&!/\s/.test(G.slice(-1))?m=setTimeout(async()=>{var N;try{const re=await bd(G.trim());((N=re.results)==null?void 0:N.length)>0?(u(s,re.results.slice(0,6),!0),u(d,!0),u(v,-1)):u(d,!1)}catch{u(d,!1)}},300):u(d,!1)}function $(k){var G;a(`${k.corpName} `),u(d,!1),u(v,-1),(G=t.onCompanySelect)==null||G.call(t,k),r(x)&&r(x).focus()}function V(){setTimeout(()=>{u(d,!1)},200)}var T=_p(),z=i(T),I=i(z);hn(I,k=>u(x,k),()=>r(x));var D=p(I,2);{var j=k=>{var G=mp(),N=i(G);ep(N,{size:14}),ce("click",G,function(...re){var P;(P=t.onStop)==null||P.apply(this,re)}),c(k,G)},de=k=>{var G=xp(),N=i(G);{let re=L(()=>o()?18:16);Vf(N,{get size(){return r(re)},strokeWidth:2.5})}S((re,P)=>{Re(G,1,re),G.disabled=P},[()=>rr(cr("send-btn",a().trim()&&"active")),()=>!a().trim()]),ce("click",G,()=>{var re;u(d,!1),(re=t.onSend)==null||re.call(t)}),c(k,G)};b(D,k=>{n()&&t.onStop?k(j):k(de,-1)})}var pe=p(z,2);{var F=k=>{var G=bp();Ce(G,21,()=>r(s),Te,(N,re,P)=>{var me=gp(),E=i(me);gn(E,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var B=p(E,2),oe=i(B),fe=i(oe),he=p(oe,2),xe=i(he),se=p(B,2);{var we=Q=>{var O=hp(),ee=i(O);S(()=>C(ee,r(re).sector)),c(Q,O)};b(se,Q=>{r(re).sector&&Q(we)})}S(Q=>{Re(me,1,Q),C(fe,r(re).corpName),C(xe,`${r(re).stockCode??""} · ${(r(re).market||"")??""}`)},[()=>rr(cr("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",P===r(v)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),ce("mousedown",me,()=>$(r(re))),xn("mouseenter",me,()=>{u(v,P,!0)}),c(N,me)}),c(k,G)};b(pe,k=>{r(d)&&r(s).length>0&&k(F)})}S(k=>{Re(z,1,k),ua(I,"placeholder",l())},[()=>rr(cr("input-box",o()&&"large"))]),ce("keydown",I,h),ce("input",I,M),xn("blur",I,V),Ln(I,a),c(e,T),Sr()}Hr(["keydown","input","click","mousedown"]);var wp=f('<button class="rounded-full border border-dl-border/60 bg-dl-bg-card/40 px-3 py-1.5 text-[12px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"> </button>'),yp=f(`<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[580px] flex flex-col items-center"><div class="relative mb-8"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p> <div class="mb-6 max-w-[520px] rounded-2xl border border-dl-border/50 bg-dl-bg-card/50 px-4 py-3 text-left"><div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">Evidence First</div> <div class="mt-2 text-[13px] leading-relaxed text-dl-text-muted">DartLab은 재무 수치와 서술 텍스트를 함께 읽고, 표준화된 계정과 원문 근거를 같은 흐름에서 확인하도록 설계되어 있습니다.
				DART와 EDGAR를 포함한 40개 모듈 이상의 기능 범위를 먼저 물어본 뒤 바로 탐색을 시작할 수 있습니다.</div></div> <div class="w-full"><!></div> <div class="mt-5 flex w-full flex-wrap justify-center gap-2"></div></div></div>`);function kp(e,t){Cr(t,!0);let a=Ie(t,"inputText",15,"");const n=["지금 dartlab에서 할 수 있는 기능을 먼저 정리해줘","EDGAR에서 추가로 받을 수 있는 데이터와 방법을 알려줘","OpenDart와 OpenEdgar로 가능한 일을 비교해줘","GPT 연결 시 현재 UI에서 가능한 코딩 작업 범위를 알려줘"];var o=yp(),l=i(o),s=p(i(l),8),d=i(s);Fd(d,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get onCompanySelect(){return t.onCompanySelect},get inputText(){return a()},set inputText(m){a(m)}});var v=p(s,2);Ce(v,21,()=>n,Te,(m,x)=>{var h=wp(),_=i(h);S(()=>C(_,r(x))),ce("click",h,()=>{var M;return(M=t.onSend)==null?void 0:M.call(t,r(x))}),c(m,h)}),c(e,o),Sr()}Hr(["click"]);var $p=f("<span><!></span>");function So(e,t){Cr(t,!0);let a=Ie(t,"variant",3,"default");const n={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var o=$p(),l=i(o);Gs(l,()=>t.children),S(s=>Re(o,1,s),[()=>rr(cr("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",n[a()],t.class))]),c(e,o),Sr()}function Cp(e){const t=e.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(t)||t==="-"||t==="0"}function yn(e){if(!e)return"";let t=[],a=[],n=e.replace(/```(\w*)\n([\s\S]*?)```/g,(l,s,d)=>{const v=t.length;return t.push(d.trimEnd()),`
%%CODE_${v}%%
`});n=n.replace(/((?:^\|.+\|$\n?)+)/gm,l=>{const s=l.trim().split(`
`).filter(_=>_.trim());let d=null,v=-1,m=[];for(let _=0;_<s.length;_++)if(s[_].slice(1,-1).split("|").map($=>$.trim()).every($=>/^[\-:]+$/.test($))){v=_;break}v>0?(d=s[v-1],m=s.slice(v+1)):(v===0||(d=s[0]),m=s.slice(1));let x="<table>";if(d){const _=d.slice(1,-1).split("|").map(M=>M.trim());x+="<thead><tr>"+_.map(M=>`<th>${M.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(m.length>0){x+="<tbody>";for(const _ of m){const M=_.slice(1,-1).split("|").map($=>$.trim());x+="<tr>"+M.map($=>{let V=$.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${Cp($)?' class="num"':""}>${V}</td>`}).join("")+"</tr>"}x+="</tbody>"}x+="</table>";let h=a.length;return a.push(x),`
%%TABLE_${h}%%
`});let o=n.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");o=o.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,l=>"<ul>"+l.replace(/<br>/g,"")+"</ul>");for(let l=0;l<a.length;l++)o=o.replace(`%%TABLE_${l}%%`,a[l]);for(let l=0;l<t.length;l++){const s=t[l].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");o=o.replace(`%%CODE_${l}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${l}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${s}</code></pre></div>`)}return o=o.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(l,s)=>s.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+o+"</p>"}var Sp=f('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),Tp=f('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),Mp=f('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),zp=f('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),Ap=f('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!> <!> <!> <!></div></div>'),Ep=f('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),Ip=f('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),Pp=f('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),Np=f("<span> </span>"),Lp=f('<span class="px-1.5 py-0.5 rounded text-[9px] font-bold border bg-red-500/10 text-red-400 border-red-500/20"> </span>'),Op=f('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-1.5"><!> <!></div>'),Rp=f('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!> <!></button>'),Dp=f("<button><!> </button>"),jp=f('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),Vp=f('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),qp=f('<!> <span class="text-dl-text-dim"> </span>',1),Bp=f('<div class="flex items-center gap-2 text-[11px]"><!></div>'),Fp=f('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),Hp=f('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),Up=f('<div class="message-committed"><!></div>'),Kp=f('<div><div class="message-live-label"> </div> <pre> </pre></div>'),Gp=f('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),Wp=f('<span class="text-dl-accent/60"> </span>'),Yp=f('<span class="text-dl-success/60"> </span>'),Jp=f('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),Xp=f('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),Qp=f('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),Zp=f('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),em=f('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),tm=f("<!>  <div><!> <!></div> <!>",1),rm=f('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),am=f('<span class="text-[10px] text-dl-text-dim"> </span>'),nm=f('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),om=f("<button> </button>"),sm=f('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),im=f("<button>시스템 프롬프트</button>"),lm=f("<button>LLM 입력</button>"),dm=f('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),cm=f('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),um=f('<span class="text-dl-text"> </span>'),vm=f('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),fm=f('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),pm=f('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),mm=f("<!> <!>",1);function xm(e,t){Cr(t,!0);let a=Y(null),n=Y("context"),o=Y("raw"),l=L(()=>{var O,ee,W,q,ue,ze;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((O=t.message.toolEvents)==null?void 0:O.length)>0){const Z=[...t.message.toolEvents].reverse().find(dt=>dt.type==="call"),Fe=((ee=Z==null?void 0:Z.arguments)==null?void 0:ee.module)||((W=Z==null?void 0:Z.arguments)==null?void 0:W.keyword)||"";return`도구 실행 중 — ${(Z==null?void 0:Z.name)||""}${Fe?` (${Fe})`:""}`}if(((q=t.message.contexts)==null?void 0:q.length)>0){const Z=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(Z==null?void 0:Z.label)||(Z==null?void 0:Z.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(ue=t.message.meta)!=null&&ue.company?`${t.message.meta.company} 데이터 검색 중`:(ze=t.message.meta)!=null&&ze.includedModules?"분석 모듈 선택 완료":"생각 중"}),s=L(()=>{var O;return t.message.company||((O=t.message.meta)==null?void 0:O.company)||null});const d={capability:"기능 탐색",coding:"코딩 작업",company_explore:"회사 탐색",company_analysis:"회사 분석",follow_up:"후속 질문",general_chat:"일반 대화"};let v=L(()=>{var O;return(O=t.message.meta)!=null&&O.dialogueMode?d[t.message.meta.dialogueMode]||t.message.meta.dialogueMode:null}),m=L(()=>{var O,ee,W;return t.message.systemPrompt||t.message.userContent||((O=t.message.contexts)==null?void 0:O.length)>0||((ee=t.message.meta)==null?void 0:ee.includedModules)||((W=t.message.toolEvents)==null?void 0:W.length)>0}),x=L(()=>{var ee;const O=(ee=t.message.meta)==null?void 0:ee.dataYearRange;return O?typeof O=="string"?O:O.min_year&&O.max_year?`${O.min_year}~${O.max_year}년`:null:null});function h(O){if(!O)return 0;const ee=(O.match(/[\uac00-\ud7af]/g)||[]).length,W=O.length-ee;return Math.round(ee*1.5+W/3.5)}function _(O){return O>=1e3?(O/1e3).toFixed(1)+"k":String(O)}let M=L(()=>{var ee;let O=0;if(t.message.systemPrompt&&(O+=h(t.message.systemPrompt)),t.message.userContent)O+=h(t.message.userContent);else if(((ee=t.message.contexts)==null?void 0:ee.length)>0)for(const W of t.message.contexts)O+=h(W.text);return O}),$=L(()=>h(t.message.text)),V=Y(void 0);const T=/^\s*\|.+\|\s*$/;function z(O,ee){if(!O)return{committed:"",draft:"",draftType:"none"};if(!ee)return{committed:O,draft:"",draftType:"none"};const W=O.split(`
`);let q=W.length;O.endsWith(`
`)||(q=Math.min(q,W.length-1));let ue=0,ze=-1;for(let Ye=0;Ye<W.length;Ye++)W[Ye].trim().startsWith("```")&&(ue+=1,ze=Ye);ue%2===1&&ze>=0&&(q=Math.min(q,ze));let Z=-1;for(let Ye=W.length-1;Ye>=0;Ye--){const zt=W[Ye];if(!zt.trim())break;if(T.test(zt))Z=Ye;else{Z=-1;break}}if(Z>=0&&(q=Math.min(q,Z)),q<=0)return{committed:"",draft:O,draftType:Z===0?"table":ue%2===1?"code":"text"};const Fe=W.slice(0,q).join(`
`),dt=W.slice(q).join(`
`);let nt="text";return dt&&Z>=q?nt="table":dt&&ue%2===1&&(nt="code"),{committed:Fe,draft:dt,draftType:nt}}const I='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',D='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function j(O){var ue;const ee=O.target.closest(".code-copy-btn");if(!ee)return;const W=ee.closest(".code-block-wrap"),q=((ue=W==null?void 0:W.querySelector("code"))==null?void 0:ue.textContent)||"";navigator.clipboard.writeText(q).then(()=>{ee.innerHTML=D,setTimeout(()=>{ee.innerHTML=I},2e3)})}function de(O){if(t.onOpenEvidence){t.onOpenEvidence("contexts",O);return}u(a,O,!0),u(n,"context"),u(o,"rendered")}function pe(){if(t.onOpenEvidence){t.onOpenEvidence("system");return}u(a,0),u(n,"system"),u(o,"raw")}function F(){if(t.onOpenEvidence){t.onOpenEvidence("snapshot");return}u(a,0),u(n,"snapshot")}function k(O){var ee;if(t.onOpenEvidence){const W=(ee=t.message.toolEvents)==null?void 0:ee[O];t.onOpenEvidence((W==null?void 0:W.type)==="result"?"tool-results":"tool-calls",O);return}u(a,O,!0),u(n,"tool"),u(o,"raw")}function G(){if(t.onOpenEvidence){t.onOpenEvidence("input");return}u(a,0),u(n,"userContent"),u(o,"raw")}function N(){u(a,null)}function re(O){var ee,W,q,ue;return O?O.type==="call"?((ee=O.arguments)==null?void 0:ee.module)||((W=O.arguments)==null?void 0:W.keyword)||((q=O.arguments)==null?void 0:q.engine)||((ue=O.arguments)==null?void 0:ue.name)||"":typeof O.result=="string"?O.result.slice(0,120):O.result&&typeof O.result=="object"&&(O.result.module||O.result.status||O.result.name)||"":""}let P=L(()=>(t.message.toolEvents||[]).filter(O=>O.type==="call")),me=L(()=>(t.message.toolEvents||[]).filter(O=>O.type==="result")),E=L(()=>z(t.message.text||"",t.message.loading)),B=L(()=>{var ee,W,q;const O=[];return((W=(ee=t.message.meta)==null?void 0:ee.includedModules)==null?void 0:W.length)>0&&O.push({label:`모듈 ${t.message.meta.includedModules.length}개`,icon:Co}),((q=t.message.contexts)==null?void 0:q.length)>0&&O.push({label:`컨텍스트 ${t.message.contexts.length}건`,icon:Uf}),r(P).length>0&&O.push({label:`툴 호출 ${r(P).length}건`,icon:il}),r(me).length>0&&O.push({label:`툴 결과 ${r(me).length}건`,icon:Eo}),t.message.systemPrompt&&O.push({label:"시스템 프롬프트",icon:zs}),t.message.userContent&&O.push({label:"LLM 입력",icon:ca}),O}),oe=L(()=>{var ee,W,q;if(!t.message.loading)return[];const O=[];return(ee=t.message.meta)!=null&&ee.company&&O.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&O.push({label:"핵심 수치 확인",done:!0}),(W=t.message.meta)!=null&&W.includedModules&&O.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((q=t.message.contexts)==null?void 0:q.length)>0&&O.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&O.push({label:"프롬프트 조립",done:!0}),t.message.text?O.push({label:"응답 작성 중",done:!1}):O.push({label:r(l)||"준비 중",done:!1}),O});var fe=mm(),he=ae(fe);{var xe=O=>{var ee=Sp(),W=p(i(ee),2),q=i(W),ue=i(q);S(()=>C(ue,t.message.text)),c(O,ee)},se=O=>{var ee=rm(),W=p(i(ee),2),q=i(W);{var ue=Tt=>{var H=Ap(),le=i(H),ke=i(le);Df(ke,{size:11});var w=p(le,4),U=i(w);{var K=lt=>{So(lt,{variant:"muted",children:(Qe,wt)=>{var qe=Ja();S(()=>C(qe,r(s))),c(Qe,qe)},$$slots:{default:!0}})};b(U,lt=>{r(s)&&lt(K)})}var g=p(U,2);{var A=lt=>{So(lt,{variant:"muted",children:(Qe,wt)=>{var qe=Ja();S(ft=>C(qe,ft),[()=>t.message.meta.market.toUpperCase()]),c(Qe,qe)},$$slots:{default:!0}})};b(g,lt=>{var Qe;(Qe=t.message.meta)!=null&&Qe.market&&lt(A)})}var R=p(g,2);{var J=lt=>{So(lt,{variant:"accent",children:(Qe,wt)=>{var qe=Ja();S(()=>C(qe,r(v))),c(Qe,qe)},$$slots:{default:!0}})};b(R,lt=>{r(v)&&lt(J)})}var ne=p(R,2);{var Ae=lt=>{So(lt,{variant:"muted",children:(Qe,wt)=>{var qe=Ja();S(()=>C(qe,t.message.meta.topicLabel)),c(Qe,qe)},$$slots:{default:!0}})};b(ne,lt=>{var Qe;(Qe=t.message.meta)!=null&&Qe.topicLabel&&lt(Ae)})}var Me=p(ne,2);{var gt=lt=>{So(lt,{variant:"accent",children:(Qe,wt)=>{var qe=Ja();S(()=>C(qe,r(x))),c(Qe,qe)},$$slots:{default:!0}})};b(Me,lt=>{r(x)&&lt(gt)})}var Je=p(Me,2);{var Xe=lt=>{var Qe=_e(),wt=ae(Qe);Ce(wt,17,()=>t.message.contexts,Te,(qe,ft,bt)=>{var Pe=Tp(),te=i(Pe);Co(te,{size:10,class:"flex-shrink-0"});var He=p(te);S(()=>C(He,` ${(r(ft).label||r(ft).module)??""}`)),ce("click",Pe,()=>de(bt)),c(qe,Pe)}),c(lt,Qe)},ut=lt=>{var Qe=Mp(),wt=i(Qe);Co(wt,{size:10,class:"flex-shrink-0"});var qe=p(wt);S(()=>C(qe,` 모듈 ${t.message.meta.includedModules.length??""}개`)),c(lt,Qe)};b(Je,lt=>{var Qe,wt,qe;((Qe=t.message.contexts)==null?void 0:Qe.length)>0?lt(Xe):((qe=(wt=t.message.meta)==null?void 0:wt.includedModules)==null?void 0:qe.length)>0&&lt(ut,1)})}var ar=p(Je,2);Ce(ar,17,()=>r(B),Te,(lt,Qe)=>{var wt=zp(),qe=i(wt);vo(qe,()=>r(Qe).icon,(bt,Pe)=>{Pe(bt,{size:10,class:"flex-shrink-0"})});var ft=p(qe);S(()=>C(ft,` ${r(Qe).label??""}`)),ce("click",wt,()=>{r(Qe).label.startsWith("컨텍스트")?de(0):r(Qe).label.startsWith("툴 호출")?t.onOpenEvidence?t.onOpenEvidence("tool-calls",0):k(0):r(Qe).label.startsWith("툴 결과")?t.onOpenEvidence?t.onOpenEvidence("tool-results",0):k((t.message.toolEvents||[]).findIndex(bt=>bt.type==="result")):r(Qe).label==="시스템 프롬프트"?pe():r(Qe).label==="LLM 입력"&&G()}),c(lt,wt)}),c(Tt,H)};b(q,Tt=>{var H,le;(r(s)||r(x)||((H=t.message.contexts)==null?void 0:H.length)>0||(le=t.message.meta)!=null&&le.includedModules||r(B).length>0)&&Tt(ue)})}var ze=p(q,2);{var Z=Tt=>{var H=Rp(),le=i(H);Ce(le,21,()=>t.message.snapshot.items,Te,(g,A)=>{const R=L(()=>r(A).status==="good"?"text-dl-success":r(A).status==="danger"?"text-dl-primary-light":r(A).status==="caution"?"text-amber-400":"text-dl-text");var J=Ep(),ne=i(J),Ae=i(ne),Me=p(ne,2),gt=i(Me);S(Je=>{C(Ae,r(A).label),Re(Me,1,Je),C(gt,r(A).value)},[()=>rr(cr("text-[14px] font-semibold leading-snug mt-0.5",r(R)))]),c(g,J)});var ke=p(le,2);{var w=g=>{var A=Pp();Ce(A,21,()=>t.message.snapshot.warnings,Te,(R,J)=>{var ne=Ip(),Ae=i(ne);Qo(Ae,{size:10});var Me=p(Ae);S(()=>C(Me,` ${r(J)??""}`)),c(R,ne)}),c(g,A)};b(ke,g=>{var A;((A=t.message.snapshot.warnings)==null?void 0:A.length)>0&&g(w)})}var U=p(ke,2);{var K=g=>{const A=L(()=>({performance:"실적",profitability:"수익성",health:"건전성",cashflow:"현금흐름",governance:"지배구조",risk:"리스크",opportunity:"기회"}));var R=Op(),J=i(R);Ce(J,17,()=>Object.entries(t.message.snapshot.grades),Te,(Me,gt)=>{var Je=L(()=>si(r(gt),2));let Xe=()=>r(Je)[0],ut=()=>r(Je)[1];const ar=L(()=>ut()==="A"?"bg-emerald-500/15 text-emerald-400 border-emerald-500/30":ut()==="B"?"bg-blue-500/15 text-blue-400 border-blue-500/30":ut()==="C"?"bg-amber-500/15 text-amber-400 border-amber-500/30":ut()==="D"?"bg-orange-500/15 text-orange-400 border-orange-500/30":ut()==="F"?"bg-red-500/15 text-red-400 border-red-500/30":"bg-dl-border/10 text-dl-text-dim border-dl-border/20");var lt=Np(),Qe=i(lt);S(()=>{Re(lt,1,`px-1.5 py-0.5 rounded text-[9px] font-bold border ${r(ar)??""}`),C(Qe,`${(r(A)[Xe()]||Xe())??""} ${ut()??""}`)}),c(Me,lt)});var ne=p(J,2);{var Ae=Me=>{var gt=Lp(),Je=i(gt);S(()=>C(Je,`이상치 ${t.message.snapshot.anomalyCount??""}건`)),c(Me,gt)};b(ne,Me=>{t.message.snapshot.anomalyCount>0&&Me(Ae)})}c(g,R)};b(U,g=>{t.message.snapshot.grades&&g(K)})}ce("click",H,F),c(Tt,H)};b(ze,Tt=>{var H,le;((le=(H=t.message.snapshot)==null?void 0:H.items)==null?void 0:le.length)>0&&Tt(Z)})}var Fe=p(ze,2);{var dt=Tt=>{var H=jp(),le=i(H),ke=p(i(le),4);Ce(ke,21,()=>t.message.toolEvents,Te,(w,U,K)=>{const g=L(()=>re(r(U)));var A=Dp(),R=i(A);{var J=Me=>{il(Me,{size:11})},ne=Me=>{Eo(Me,{size:11})};b(R,Me=>{r(U).type==="call"?Me(J):Me(ne,-1)})}var Ae=p(R);S(Me=>{Re(A,1,Me),C(Ae,` ${(r(U).type==="call"?r(U).name:`${r(U).name} 결과`)??""}${r(g)?`: ${r(g)}`:""}`)},[()=>rr(cr("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",r(U).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),ce("click",A,()=>k(K)),c(w,A)}),c(Tt,H)};b(Fe,Tt=>{var H;((H=t.message.toolEvents)==null?void 0:H.length)>0&&Tt(dt)})}var nt=p(Fe,2);{var Ye=Tt=>{var H=Fp(),le=i(H);Ce(le,21,()=>r(oe),Te,(ke,w)=>{var U=Bp(),K=i(U);{var g=R=>{var J=Vp(),ne=p(ae(J),2),Ae=i(ne);S(()=>C(Ae,r(w).label)),c(R,J)},A=R=>{var J=qp(),ne=ae(J);Nr(ne,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var Ae=p(ne,2),Me=i(Ae);S(()=>C(Me,r(w).label)),c(R,J)};b(K,R=>{r(w).done?R(g):R(A,-1)})}c(ke,U)}),c(Tt,H)},zt=Tt=>{var H=tm(),le=ae(H);{var ke=ne=>{var Ae=Hp(),Me=i(Ae);Nr(Me,{size:12,class:"animate-spin flex-shrink-0"});var gt=p(Me,2),Je=i(gt);S(()=>C(Je,r(l))),c(ne,Ae)};b(le,ne=>{t.message.loading&&ne(ke)})}var w=p(le,2),U=i(w);{var K=ne=>{var Ae=Up(),Me=i(Ae);Ma(Me,()=>yn(r(E).committed)),c(ne,Ae)};b(U,ne=>{r(E).committed&&ne(K)})}var g=p(U,2);{var A=ne=>{var Ae=Kp(),Me=i(Ae),gt=i(Me),Je=p(Me,2),Xe=i(Je);S(ut=>{Re(Ae,1,ut),C(gt,r(E).draftType==="table"?"표 구성 중":r(E).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),C(Xe,r(E).draft)},[()=>rr(cr("message-live-tail",r(E).draftType==="table"&&"message-draft-table",r(E).draftType==="code"&&"message-draft-code"))]),c(ne,Ae)};b(g,ne=>{r(E).draft&&ne(A)})}hn(w,ne=>u(V,ne),()=>r(V));var R=p(w,2);{var J=ne=>{var Ae=em(),Me=i(Ae);{var gt=ft=>{var bt=Gp(),Pe=i(bt);is(Pe,{size:10});var te=p(Pe);S(()=>C(te,` ${t.message.duration??""}초`)),c(ft,bt)};b(Me,ft=>{t.message.duration&&ft(gt)})}var Je=p(Me,2);{var Xe=ft=>{var bt=Jp(),Pe=i(bt);{var te=je=>{var ot=Wp(),Ze=i(ot);S(At=>C(Ze,`↑${At??""}`),[()=>_(r(M))]),c(je,ot)};b(Pe,je=>{r(M)>0&&je(te)})}var He=p(Pe,2);{var pt=je=>{var ot=Yp(),Ze=i(ot);S(At=>C(Ze,`↓${At??""}`),[()=>_(r($))]),c(je,ot)};b(He,je=>{r($)>0&&je(pt)})}c(ft,bt)};b(Je,ft=>{(r(M)>0||r($)>0)&&ft(Xe)})}var ut=p(Je,2);{var ar=ft=>{var bt=Xp(),Pe=i(bt);Xf(Pe,{size:10}),ce("click",bt,()=>{var te;return(te=t.onRegenerate)==null?void 0:te.call(t)}),c(ft,bt)};b(ut,ft=>{t.onRegenerate&&ft(ar)})}var lt=p(ut,2);{var Qe=ft=>{var bt=Qp(),Pe=i(bt);zs(Pe,{size:10}),ce("click",bt,pe),c(ft,bt)};b(lt,ft=>{t.message.systemPrompt&&ft(Qe)})}var wt=p(lt,2);{var qe=ft=>{var bt=Zp(),Pe=i(bt);ca(Pe,{size:10});var te=p(Pe);S((He,pt)=>C(te,` LLM 입력 (${He??""}자 · ~${pt??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>_(h(t.message.userContent))]),ce("click",bt,G),c(ft,bt)};b(wt,ft=>{t.message.userContent&&ft(qe)})}c(ne,Ae)};b(R,ne=>{!t.message.loading&&(t.message.duration||r(m)||t.onRegenerate)&&ne(J)})}S(ne=>Re(w,1,ne),[()=>rr(cr("prose-dartlab message-body text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),ce("click",w,j),c(Tt,H)};b(nt,Tt=>{t.message.loading&&!t.message.text?Tt(Ye):Tt(zt,-1)})}c(O,ee)};b(he,O=>{t.message.role==="user"?O(xe):O(se,-1)})}var we=p(he,2);{var Q=O=>{const ee=L(()=>r(n)==="system"),W=L(()=>r(n)==="userContent"),q=L(()=>r(n)==="context"),ue=L(()=>r(n)==="snapshot"),ze=L(()=>r(n)==="tool"),Z=L(()=>{var te;return r(q)?(te=t.message.contexts)==null?void 0:te[r(a)]:null}),Fe=L(()=>{var te;return r(ze)?(te=t.message.toolEvents)==null?void 0:te[r(a)]:null}),dt=L(()=>{var te,He,pt,je,ot;return r(ue)?"핵심 수치 (원본 데이터)":r(ee)?"시스템 프롬프트":r(W)?"LLM에 전달된 입력":r(ze)?((te=r(Fe))==null?void 0:te.type)==="call"?`${(He=r(Fe))==null?void 0:He.name} 호출`:`${(pt=r(Fe))==null?void 0:pt.name} 결과`:((je=r(Z))==null?void 0:je.label)||((ot=r(Z))==null?void 0:ot.module)||""}),nt=L(()=>{var te;return r(ue)?JSON.stringify(t.message.snapshot,null,2):r(ee)?t.message.systemPrompt:r(W)?t.message.userContent:r(ze)?JSON.stringify(r(Fe),null,2):(te=r(Z))==null?void 0:te.text});var Ye=pm(),zt=i(Ye),Tt=i(zt),H=i(Tt),le=i(H),ke=i(le);{var w=te=>{Co(te,{size:15,class:"text-dl-success flex-shrink-0"})},U=te=>{zs(te,{size:15,class:"text-dl-primary-light flex-shrink-0"})},K=te=>{ca(te,{size:15,class:"text-dl-accent flex-shrink-0"})},g=te=>{Co(te,{size:15,class:"flex-shrink-0"})};b(ke,te=>{r(ue)?te(w):r(ee)?te(U,1):r(W)?te(K,2):te(g,-1)})}var A=p(ke,2),R=i(A),J=p(A,2);{var ne=te=>{var He=am(),pt=i(He);S(je=>C(pt,`(${je??""}자)`),[()=>{var je,ot;return(ot=(je=r(nt))==null?void 0:je.length)==null?void 0:ot.toLocaleString()}]),c(te,He)};b(J,te=>{r(ee)&&te(ne)})}var Ae=p(le,2),Me=i(Ae);{var gt=te=>{var He=nm(),pt=i(He),je=i(pt);ca(je,{size:11});var ot=p(pt,2),Ze=i(ot);Bf(Ze,{size:11}),S((At,Dt)=>{Re(pt,1,At),Re(ot,1,Dt)},[()=>rr(cr("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",r(o)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>rr(cr("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",r(o)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),ce("click",pt,()=>u(o,"rendered")),ce("click",ot,()=>u(o,"raw")),c(te,He)};b(Me,te=>{r(q)&&te(gt)})}var Je=p(Me,2),Xe=i(Je);wn(Xe,{size:18});var ut=p(H,2);{var ar=te=>{var He=sm(),pt=i(He);Ce(pt,21,()=>t.message.contexts,Te,(je,ot,Ze)=>{var At=om(),Dt=i(At);S(Jt=>{Re(At,1,Jt),C(Dt,t.message.contexts[Ze].label||t.message.contexts[Ze].module)},[()=>rr(cr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",Ze===r(a)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),ce("click",At,()=>{u(a,Ze,!0)}),c(je,At)}),c(te,He)};b(ut,te=>{var He;r(q)&&((He=t.message.contexts)==null?void 0:He.length)>1&&te(ar)})}var lt=p(ut,2);{var Qe=te=>{var He=dm(),pt=i(He),je=i(pt);{var ot=Dt=>{var Jt=im();S(fr=>Re(Jt,1,fr),[()=>rr(cr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",r(ee)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),ce("click",Jt,()=>{u(n,"system")}),c(Dt,Jt)};b(je,Dt=>{t.message.systemPrompt&&Dt(ot)})}var Ze=p(je,2);{var At=Dt=>{var Jt=lm();S(fr=>Re(Jt,1,fr),[()=>rr(cr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",r(W)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),ce("click",Jt,()=>{u(n,"userContent")}),c(Dt,Jt)};b(Ze,Dt=>{t.message.userContent&&Dt(At)})}c(te,He)};b(lt,te=>{!r(q)&&!r(ue)&&!r(ze)&&te(Qe)})}var wt=p(Tt,2),qe=i(wt);{var ft=te=>{var He=cm(),pt=i(He);Ma(pt,()=>{var je;return yn((je=r(Z))==null?void 0:je.text)}),c(te,He)},bt=te=>{var He=vm(),pt=i(He),je=p(i(pt),2),ot=i(je),Ze=p(ot);{var At=kt=>{var Ft=um(),_r=i(Ft);S(xr=>C(_r,xr),[()=>re(r(Fe))]),c(kt,Ft)},Dt=L(()=>re(r(Fe)));b(Ze,kt=>{r(Dt)&&kt(At)})}var Jt=p(pt,2),fr=i(Jt);S(()=>{var kt;C(ot,`${((kt=r(Fe))==null?void 0:kt.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),C(fr,r(nt))}),c(te,He)},Pe=te=>{var He=fm(),pt=i(He);S(()=>C(pt,r(nt))),c(te,He)};b(qe,te=>{r(q)&&r(o)==="rendered"?te(ft):r(ze)?te(bt,1):te(Pe,-1)})}S(()=>C(R,r(dt))),ce("click",Ye,te=>{te.target===te.currentTarget&&N()}),ce("keydown",Ye,te=>{te.key==="Escape"&&N()}),ce("click",Je,N),c(O,Ye)};b(we,O=>{r(a)!==null&&O(Q)})}c(e,fe),Sr()}Hr(["click","keydown"]);var hm=f('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),gm=f('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),bm=f('<div class="flex justify-end gap-2 mb-1.5"><!></div>'),_m=f('<div class="flex items-center gap-1.5 px-3 py-1 text-[10px] text-dl-text-dim"><span class="px-1.5 py-0.5 rounded bg-dl-accent/10 text-dl-accent-light border border-dl-accent/20 font-mono"> <!></span> <span>보는 중 — AI가 이 섹션을 참조합니다</span></div>'),wm=f('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8"><!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!> <!></div></div></div>');function ym(e,t){Cr(t,!0);function a(E){if(o())return!1;for(let B=n().length-1;B>=0;B--)if(n()[B].role==="assistant"&&!n()[B].error&&n()[B].text)return B===E;return!1}let n=Ie(t,"messages",19,()=>[]),o=Ie(t,"isLoading",3,!1),l=Ie(t,"inputText",15,""),s=Ie(t,"scrollTrigger",3,0);Ie(t,"selectedCompany",3,null);let d=Ie(t,"viewerContext",3,null);function v(E){return(B,oe)=>{var he,xe,se,we;(he=t.onOpenEvidence)==null||he.call(t,B,oe);let fe;if(B==="contexts")fe=(xe=E.contexts)==null?void 0:xe[oe];else if(B==="snapshot")fe={label:"핵심 수치",module:"snapshot",text:JSON.stringify(E.snapshot,null,2)};else if(B==="system")fe={label:"시스템 프롬프트",module:"system",text:E.systemPrompt};else if(B==="input")fe={label:"LLM 입력",module:"input",text:E.userContent};else if(B==="tool-calls"||B==="tool-results"){const Q=(se=E.toolEvents)==null?void 0:se[oe];fe={label:`${(Q==null?void 0:Q.name)||"도구"} ${(Q==null?void 0:Q.type)==="call"?"호출":"결과"}`,module:"tool",text:JSON.stringify(Q,null,2)}}fe&&((we=t.onOpenData)==null||we.call(t,fe))}}let m,x,h=Y(!0),_=Y(!1),M=Y(!0);function $(){if(!m)return;const{scrollTop:E,scrollHeight:B,clientHeight:oe}=m;u(M,B-E-oe<96),r(M)?(u(h,!0),u(_,!1)):(u(h,!1),u(_,!0))}function V(E="smooth"){x&&(x.scrollIntoView({block:"end",behavior:E}),u(h,!0),u(_,!1))}$r(()=>{s(),!(!m||!x)&&requestAnimationFrame(()=>{!m||!x||(r(h)||r(M)?(x.scrollIntoView({block:"end",behavior:o()?"auto":"smooth"}),u(_,!1)):u(_,!0))})});var T=wm(),z=i(T),I=i(z),D=i(I);Ce(D,17,n,Te,(E,B,oe)=>{{let fe=L(()=>a(oe)?t.onRegenerate:void 0),he=L(()=>t.onOpenData?v(r(B)):void 0);xm(E,{get message(){return r(B)},get onRegenerate(){return r(fe)},get onOpenEvidence(){return r(he)}})}});var j=p(D,2);hn(j,E=>x=E,()=>x),hn(z,E=>m=E,()=>m);var de=p(z,2);{var pe=E=>{var B=hm(),oe=i(B);ce("click",oe,()=>V("smooth")),c(E,B)};b(de,E=>{r(_)&&E(pe)})}var F=p(de,2),k=i(F),G=i(k);{var N=E=>{var B=bm(),oe=i(B);{var fe=he=>{var xe=gm(),se=i(xe);Io(se,{size:10}),ce("click",xe,function(...we){var Q;(Q=t.onExport)==null||Q.apply(this,we)}),c(he,xe)};b(oe,he=>{n().length>1&&t.onExport&&he(fe)})}c(E,B)};b(G,E=>{o()||E(N)})}var re=p(G,2);{var P=E=>{var B=_m(),oe=i(B),fe=i(oe),he=p(fe);{var xe=se=>{var we=Ja();S(()=>C(we,` (${d().period??""})`)),c(se,we)};b(he,se=>{d().period&&se(xe)})}S(()=>C(fe,d().topicLabel||d().topic)),c(E,B)};b(re,E=>{var B;(B=d())!=null&&B.topic&&E(P)})}var me=p(re,2);Fd(me,{get isLoading(){return o()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get onCompanySelect(){return t.onCompanySelect},get inputText(){return l()},set inputText(E){l(E)}}),xn("scroll",z,$),c(e,T),Sr()}Hr(["click"]);var km=f('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!> <span class="text-[13px]">공시 데이터 로딩 중...</span></div>'),$m=f('<div class="text-[11px] text-dl-text-dim"> </div>'),Cm=f('<button><!> <span class="truncate flex-1"> </span></button>'),Sm=f('<div class="py-0.5"></div>'),Tm=f('<div><button class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] opacity-30 font-normal"> </span></button> <!></div>'),Mm=f('<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50"><div class="px-3 py-2.5 border-b border-dl-border/20"><!></div> <!></nav>'),zm=f('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim"><!> <p class="text-[13px]">좌측에서 섹션을 선택하세요</p></div>'),Am=f('<div class="text-[10px] text-dl-text-dim/50 mb-0.5"> </div>'),Em=f('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!></div>'),Im=f('<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>'),Pm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Nm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Lm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Om=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Rm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Dm=f('<div class="vw-heading-node svelte-1l2nqwu"><!></div>'),jm=f('<div class="vw-heading-block svelte-1l2nqwu"></div>'),Vm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),qm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Bm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Fm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Hm=f('<button><span class="vw-timeline-label svelte-1l2nqwu"> </span></button>'),Um=f('<div class="vw-section-timeline svelte-1l2nqwu"></div>'),Km=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Gm=f('<span class="vw-meta-pill svelte-1l2nqwu">비교 없음</span>'),Wm=f('<div class="vw-section-actions svelte-1l2nqwu"><span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span></div>'),Ym=f('<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span> </div>'),Jm=f('<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),Xm=f('<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),Qm=f('<div class="text-[10px] text-dl-text-dim/35 mt-1"> </div>'),Zm=f('<div class="vw-digest svelte-1l2nqwu"><div class="flex items-center gap-2 mb-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span></div> <div class="space-y-1"><!> <!> <!> <!></div></div>'),ex=f('<p class="vw-para"> </p>'),tx=f('<div class="vw-diff-added svelte-1l2nqwu"> </div>'),rx=f('<div class="vw-diff-deleted svelte-1l2nqwu"> </div>'),ax=f('<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow svelte-1l2nqwu"></div>'),nx=f('<div class="disclosure-text vw-section-body vw-body-frame svelte-1l2nqwu"><!></div>'),ox=f('<div><!> <div class="vw-section-meta svelte-1l2nqwu"><span> </span> <!> <!> <!> <!></div> <!> <!> <!> <!></div>'),sx=f('<section class="vw-report-shell svelte-1l2nqwu"><div class="vw-report-header svelte-1l2nqwu"><div class="vw-report-badges svelte-1l2nqwu"><!> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <!> <!></div></div> <!></section>'),ix=f('<div class="vw-data-divider svelte-1l2nqwu"><div class="vw-data-kicker svelte-1l2nqwu">Structured Data</div> <div class="vw-data-title svelte-1l2nqwu">표 / 정형 데이터</div></div>'),lx=f('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),dx=f("<th> </th>"),cx=f("<td> </td>"),ux=f("<tr></tr>"),vx=f('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),fx=f('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),px=f("<th> </th>"),mx=f("<td> </td>"),xx=f("<tr></tr>"),hx=f('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),gx=f("<button> </button>"),bx=f('<span class="text-[9px] text-dl-text-dim/30"> </span>'),_x=f('<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto"><!> <!></div>'),wx=f('<div class="vw-table-wrap bg-dl-bg-card/10 svelte-1l2nqwu"><!> <div class="px-4 py-3"><div class="markdown-table overflow-x-auto svelte-1l2nqwu"><!></div></div></div>'),yx=f("<th> </th>"),kx=f("<td> </td>"),$x=f("<tr></tr>"),Cx=f('<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02] svelte-1l2nqwu"><div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10"><!> <span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span></div> <div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Sx=f('<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card"> </th>'),Tx=f('<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted"> </td>'),Mx=f("<tr></tr>"),zx=f('<div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Ax=f('<article class="py-6 px-8"><!> <!> <!> <!></article>'),Ex=f('<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center"><div class="flex-1 min-w-0"><!> <h3 class="text-[16px] font-semibold text-dl-text"> </h3></div> <button class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"><!></button></div> <!>',1),Ix=f('<div class="flex flex-1 overflow-hidden min-h-0"><!> <main class="flex-1 overflow-y-auto min-w-0"><!></main></div>'),Px=f('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8"><!> <p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p></div>'),Nx=f('<div class="flex flex-col h-full font-sans bg-dl-bg-dark"><!></div>');function Lx(e,t){Cr(t,!0);let a=Ie(t,"stockCode",3,null),n=Ie(t,"onTopicChange",3,null),o=Y(null),l=Y(!1),s=Y(Ut(new Set)),d=Y(null),v=Y(null),m=Y(Ut([])),x=Y(null),h=Y(!1),_=Y(Ut([])),M=Y(Ut(new Map)),$=new Map,V=Y(!1),T=Y(Ut(new Map));const z={companyOverview:"회사 개요",companyHistory:"회사 연혁",articlesOfIncorporation:"정관 사항",capitalChange:"자본금 변동",shareCapital:"주식 현황",dividend:"배당",productService:"사업 내용",rawMaterial:"원재료",businessOverview:"사업 개요",salesOrder:"매출/수주",riskDerivative:"위험관리/파생",majorContractsAndRnd:"주요 계약/R&D",otherReferences:"기타 참고사항",consolidatedStatements:"연결 재무제표",fsSummary:"재무제표 요약",consolidatedNotes:"연결 주석",financialStatements:"개별 재무제표",financialNotes:"개별 주석",fundraising:"자금조달",BS:"재무상태표",IS:"손익계산서",CIS:"포괄손익계산서",CF:"현금흐름표",SCE:"자본변동표",ratios:"재무비율",audit:"감사 의견",mdna:"경영진 분석(MD&A)",internalControl:"내부통제",auditContract:"감사 계약",nonAuditContract:"비감사 계약",boardOfDirectors:"이사회",shareholderMeeting:"주주총회",auditSystem:"감사 체계",outsideDirector:"사외이사",majorHolder:"주요 주주",majorHolderChange:"주주 변동",minorityHolder:"소수주주",stockTotal:"주식 총수",treasuryStock:"자기주식",employee:"직원 현황",executivePay:"임원 보수",executive:"임원 현황",executivePayAllTotal:"전체 보수 총액",executivePayIndividual:"개인별 보수",topPay:"5억이상 상위 보수",unregisteredExecutivePay:"미등기임원 보수",affiliateGroup:"계열회사",investedCompany:"투자회사",relatedPartyTx:"특수관계 거래",corporateBond:"사채 관리",privateOfferingUsage:"사모자금 사용",publicOfferingUsage:"공모자금 사용",shortTermBond:"단기사채",investorProtection:"투자자 보호",disclosureChanges:"공시변경 사항",contingentLiability:"우발채무",sanction:"제재/조치",subsequentEvents:"후발사건",expertConfirmation:"전문가 확인",subsidiaryDetail:"종속회사 상세",affiliateGroupDetail:"계열회사 상세",investmentInOtherDetail:"타법인 출자 상세",rndDetail:"R&D 상세"},I={I:"I. 회사의 개요",II:"II. 사업의 내용",III:"III. 재무에 관한 사항",IV:"IV. 감사인의 감사의견 등",V:"V. 이사의 경영진단 및 분석의견",VI:"VI. 이사회 등 회사의 기관에 관한 사항",VII:"VII. 주주에 관한 사항",VIII:"VIII. 임원 및 직원 등에 관한 사항",IX:"IX. 계열회사 등에 관한 사항",X:"X. 대주주 등과의 거래내용",XI:"XI. 그 밖에 투자자 보호를 위하여 필요한 사항",XII:"XII. 상세표"},D={I:1,II:2,III:3,IV:4,V:5,VI:6,VII:7,VIII:8,IX:9,X:10,XI:11,XII:12};function j(g){return D[g]??99}function de(g){return z[g]||g}function pe(g){return I[g]||g||"기타"}$r(()=>{a()&&F()});async function F(){var g,A;u(l,!0),u(o,null),u(d,null),u(v,null),u(m,[],!0),u(x,null),$=new Map;try{const R=await yv(a());u(o,R.payload,!0),(g=r(o))!=null&&g.columns&&u(_,r(o).columns.filter(ne=>/^\d{4}(Q[1-4])?$/.test(ne)),!0);const J=E((A=r(o))==null?void 0:A.rows);J.length>0&&(u(s,new Set([J[0].chapter]),!0),J[0].topics.length>0&&k(J[0].topics[0].topic,J[0].chapter))}catch(R){console.error("viewer load error:",R)}u(l,!1)}async function k(g,A){var R;if(r(d)!==g){if(u(d,g,!0),u(v,A||null,!0),u(M,new Map,!0),u(T,new Map,!0),(R=n())==null||R(g,de(g)),$.has(g)){const J=$.get(g);u(m,J.blocks||[],!0),u(x,J.textDocument||null,!0);return}u(m,[],!0),u(x,null),u(h,!0);try{const J=await wv(a(),g);u(m,J.blocks||[],!0),u(x,J.textDocument||null,!0),$.set(g,{blocks:r(m),textDocument:r(x)})}catch(J){console.error("topic load error:",J),u(m,[],!0),u(x,null)}u(h,!1)}}function G(g){const A=new Set(r(s));A.has(g)?A.delete(g):A.add(g),u(s,A,!0)}function N(g,A){const R=new Map(r(M));R.get(g)===A?R.delete(g):R.set(g,A),u(M,R,!0)}function re(g,A){const R=new Map(r(T));R.set(g,A),u(T,R,!0)}function P(g){return g==="updated"?"최근 수정":g==="new"?"신규":g==="stale"?"과거 유지":"유지"}function me(g){return g==="updated"?"updated":g==="new"?"new":g==="stale"?"stale":"stable"}function E(g){if(!g)return[];const A=new Map,R=new Set;for(const J of g){const ne=J.chapter||"";A.has(ne)||A.set(ne,{chapter:ne,topics:[]}),R.has(J.topic)||(R.add(J.topic),A.get(ne).topics.push({topic:J.topic,source:J.source||"docs"}))}return[...A.values()].sort((J,ne)=>j(J.chapter)-j(ne.chapter))}function B(g){return String(g).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function oe(g){return String(g||"").replaceAll(" "," ").replace(/\s+/g," ").trim()}function fe(g){return!g||g.length>88?!1:/^\[.+\]$/.test(g)||/^【.+】$/.test(g)||/^[IVX]+\.\s/.test(g)||/^\d+\.\s/.test(g)||/^[가-힣]\.\s/.test(g)||/^\(\d+\)\s/.test(g)||/^\([가-힣]\)\s/.test(g)}function he(g){return/^\(\d+\)\s/.test(g)||/^\([가-힣]\)\s/.test(g)?"h5":"h4"}function xe(g){return/^\[.+\]$/.test(g)||/^【.+】$/.test(g)?"vw-h-bracket":/^\(\d+\)\s/.test(g)||/^\([가-힣]\)\s/.test(g)?"vw-h-sub":"vw-h-section"}function se(g){if(!g)return[];if(/^\|.+\|$/m.test(g)||/^#{1,3} /m.test(g)||/```/.test(g))return[{kind:"markdown",text:g}];const A=[];let R=[];const J=()=>{R.length!==0&&(A.push({kind:"paragraph",text:R.join(" ")}),R=[])};for(const ne of String(g).split(`
`)){const Ae=oe(ne);if(!Ae){J();continue}if(fe(Ae)){J(),A.push({kind:"heading",text:Ae,tag:he(Ae),className:xe(Ae)});continue}R.push(Ae)}return J(),A}function we(g){return g?g.kind==="annual"?`${g.year}Q4`:g.year&&g.quarter?`${g.year}Q${g.quarter}`:g.label||"":""}function Q(g){var J;const A=se(g);if(A.length===0)return"";if(((J=A[0])==null?void 0:J.kind)==="markdown")return yn(g);let R="";for(const ne of A){if(ne.kind==="heading"){R+=`<${ne.tag} class="${ne.className}">${B(ne.text)}</${ne.tag}>`;continue}R+=`<p class="vw-para">${B(ne.text)}</p>`}return R}function O(g){if(!g)return"";const A=g.trim().split(`
`).filter(J=>J.trim());let R="";for(const J of A){const ne=J.trim();/^[가-힣]\.\s/.test(ne)||/^\d+[-.]/.test(ne)?R+=`<h4 class="vw-h-section">${ne}</h4>`:/^\(\d+\)\s/.test(ne)||/^\([가-힣]\)\s/.test(ne)?R+=`<h5 class="vw-h-sub">${ne}</h5>`:/^\[.+\]$/.test(ne)||/^【.+】$/.test(ne)?R+=`<h4 class="vw-h-bracket">${ne}</h4>`:R+=`<h5 class="vw-h-sub">${ne}</h5>`}return R}function ee(g){var R;const A=r(M).get(g.id);return A&&((R=g==null?void 0:g.views)!=null&&R[A])?g.views[A]:(g==null?void 0:g.latest)||null}function W(g,A){var J,ne;const R=r(M).get(g.id);return R?R===A:((ne=(J=g==null?void 0:g.latest)==null?void 0:J.period)==null?void 0:ne.label)===A}function q(g){return r(M).has(g.id)}function ue(g){return g==="updated"?"변경 있음":g==="new"?"직전 없음":"직전과 동일"}function ze(g){var Ae,Me,gt;if(!g)return[];const A=se(g.body);if(A.length===0||((Ae=A[0])==null?void 0:Ae.kind)==="markdown"||!((Me=g.prevPeriod)!=null&&Me.label)||!((gt=g.diff)!=null&&gt.length))return A;const R=[];for(const Je of g.diff)for(const Xe of Je.paragraphs||[])R.push({kind:Je.kind,text:oe(Xe)});const J=[];let ne=0;for(const Je of A){if(Je.kind!=="paragraph"){J.push(Je);continue}for(;ne<R.length&&R[ne].kind==="removed";)J.push({kind:"removed",text:R[ne].text}),ne+=1;ne<R.length&&["same","added"].includes(R[ne].kind)?(J.push({kind:R[ne].kind,text:R[ne].text||Je.text}),ne+=1):J.push({kind:"same",text:Je.text})}for(;ne<R.length;)J.push({kind:R[ne].kind,text:R[ne].text}),ne+=1;return J}function Z(g){return g==null?!1:/^-?[\d,.]+%?$/.test(String(g).trim().replace(/,/g,""))}function Fe(g){return g==null?!1:/^-[\d.]+/.test(String(g).trim().replace(/,/g,""))}function dt(g,A){if(g==null||g==="")return"";const R=typeof g=="number"?g:Number(String(g).replace(/,/g,""));if(isNaN(R))return String(g);if(A<=1)return R.toLocaleString("ko-KR");const J=R/A;return Number.isInteger(J)?J.toLocaleString("ko-KR"):J.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g,",")}function nt(g){if(g==null||g==="")return"";const A=String(g).trim();if(A.includes(","))return A;const R=A.match(/^(-?\d+)(\.\d+)?(%?)$/);return R?R[1].replace(/\B(?=(\d{3})+(?!\d))/g,",")+(R[2]||"")+(R[3]||""):A}function Ye(g){var A,R;return(A=r(o))!=null&&A.rows&&((R=r(o).rows.find(J=>J.topic===g))==null?void 0:R.chapter)||null}function zt(g){const A=g.match(/^(\d{4})(Q([1-4]))?$/);if(!A)return"0000_0";const R=A[1],J=A[3]||"5";return`${R}_${J}`}function Tt(g){return[...g].sort((A,R)=>zt(R).localeCompare(zt(A)))}let H=L(()=>r(m).filter(g=>g.kind!=="text"));var le=Nx(),ke=i(le);{var w=g=>{var A=km(),R=i(A);Nr(R,{size:18,class:"animate-spin"}),c(g,A)},U=g=>{var A=Ix(),R=i(A);{var J=Je=>{var Xe=Mm(),ut=i(Xe),ar=i(ut);{var lt=wt=>{var qe=$m(),ft=i(qe);S(()=>C(ft,`${r(_).length??""}개 기간 · ${r(_)[0]??""} ~ ${r(_)[r(_).length-1]??""}`)),c(wt,qe)};b(ar,wt=>{r(_).length>0&&wt(lt)})}var Qe=p(ut,2);Ce(Qe,17,()=>E(r(o).rows),Te,(wt,qe)=>{var ft=Tm(),bt=i(ft),Pe=i(bt);{var te=kt=>{Rd(kt,{size:11,class:"flex-shrink-0 opacity-40"})},He=L(()=>r(s).has(r(qe).chapter)),pt=kt=>{Dd(kt,{size:11,class:"flex-shrink-0 opacity-40"})};b(Pe,kt=>{r(He)?kt(te):kt(pt,-1)})}var je=p(Pe,2),ot=i(je),Ze=p(je,2),At=i(Ze),Dt=p(bt,2);{var Jt=kt=>{var Ft=Sm();Ce(Ft,21,()=>r(qe).topics,Te,(_r,xr)=>{var Gt=Cm(),Se=i(Gt);{var Ne=er=>{ss(er,{size:11,class:"flex-shrink-0 text-blue-400/40"})},Kt=er=>{Js(er,{size:11,class:"flex-shrink-0 text-emerald-400/40"})},pr=er=>{ca(er,{size:11,class:"flex-shrink-0 opacity-30"})};b(Se,er=>{r(xr).source==="finance"?er(Ne):r(xr).source==="report"?er(Kt,1):er(pr,-1)})}var Ir=p(Se,2),Wt=i(Ir);S(er=>{Re(Gt,1,`group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											${r(d)===r(xr).topic?"bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]":"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent"}`),C(Wt,er)},[()=>de(r(xr).topic)]),ce("click",Gt,()=>k(r(xr).topic,r(qe).chapter)),c(_r,Gt)}),c(kt,Ft)},fr=L(()=>r(s).has(r(qe).chapter));b(Dt,kt=>{r(fr)&&kt(Jt)})}S(kt=>{C(ot,kt),C(At,r(qe).topics.length)},[()=>pe(r(qe).chapter)]),ce("click",bt,()=>G(r(qe).chapter)),c(wt,ft)}),c(Je,Xe)};b(R,Je=>{r(V)||Je(J)})}var ne=p(R,2),Ae=i(ne);{var Me=Je=>{var Xe=zm(),ut=i(Xe);ca(ut,{size:32,strokeWidth:1,class:"opacity-20"}),c(Je,Xe)},gt=Je=>{var Xe=Ex(),ut=ae(Xe),ar=i(ut),lt=i(ar);{var Qe=Ze=>{var At=Am(),Dt=i(At);S(Jt=>C(Dt,Jt),[()=>pe(r(v)||Ye(r(d)))]),c(Ze,At)},wt=L(()=>r(v)||Ye(r(d)));b(lt,Ze=>{r(wt)&&Ze(Qe)})}var qe=p(lt,2),ft=i(qe),bt=p(ar,2),Pe=i(bt);{var te=Ze=>{Vd(Ze,{size:15})},He=Ze=>{jd(Ze,{size:15})};b(Pe,Ze=>{r(V)?Ze(te):Ze(He,-1)})}var pt=p(ut,2);{var je=Ze=>{var At=Em(),Dt=i(At);Nr(Dt,{size:16,class:"animate-spin"}),c(Ze,At)},ot=Ze=>{var At=Ax(),Dt=i(At);{var Jt=Gt=>{var Se=Im();c(Gt,Se)};b(Dt,Gt=>{var Se,Ne;r(m).length===0&&!(((Ne=(Se=r(x))==null?void 0:Se.sections)==null?void 0:Ne.length)>0)&&Gt(Jt)})}var fr=p(Dt,2);{var kt=Gt=>{var Se=sx(),Ne=i(Se),Kt=i(Ne),pr=i(Kt);{var Ir=rt=>{var De=Pm(),Ke=i(De);S(Ge=>C(Ke,`최신 기준 ${Ge??""}`),[()=>we(r(x).latestPeriod)]),c(rt,De)};b(pr,rt=>{r(x).latestPeriod&&rt(Ir)})}var Wt=p(pr,2);{var er=rt=>{var De=Nm(),Ke=i(De);S((Ge,qt)=>C(Ke,`커버리지 ${Ge??""}~${qt??""}`),[()=>we(r(x).firstPeriod),()=>we(r(x).latestPeriod)]),c(rt,De)};b(Wt,rt=>{r(x).firstPeriod&&rt(er)})}var Or=p(Wt,2),Yt=i(Or),ct=p(Or,2);{var mt=rt=>{var De=Lm(),Ke=i(De);S(()=>C(Ke,`최근 수정 ${r(x).updatedCount??""}개`)),c(rt,De)};b(ct,rt=>{r(x).updatedCount>0&&rt(mt)})}var St=p(ct,2);{var jt=rt=>{var De=Om(),Ke=i(De);S(()=>C(Ke,`신규 ${r(x).newCount??""}개`)),c(rt,De)};b(St,rt=>{r(x).newCount>0&&rt(jt)})}var Xt=p(St,2);{var We=rt=>{var De=Rm(),Ke=i(De);S(()=>C(Ke,`과거 유지 ${r(x).staleCount??""}개`)),c(rt,De)};b(Xt,rt=>{r(x).staleCount>0&&rt(We)})}var Lt=p(Ne,2);Ce(Lt,17,()=>r(x).sections,Te,(rt,De)=>{const Ke=L(()=>ee(r(De))),Ge=L(()=>q(r(De)));var qt=ox(),ur=i(qt);{var xt=$e=>{var be=jm();Ce(be,21,()=>r(De).headingPath,Te,(Ve,Et)=>{var or=Dm(),hr=i(or);Ma(hr,()=>O(r(Et).text)),c(Ve,or)}),c($e,be)};b(ur,$e=>{var be;((be=r(De).headingPath)==null?void 0:be.length)>0&&$e(xt)})}var $t=p(ur,2),Ot=i($t),ir=i(Ot),Qt=p(Ot,2);{var Tr=$e=>{var be=Vm(),Ve=i(be);S(Et=>C(Ve,`최신 ${Et??""}`),[()=>we(r(De).latestPeriod)]),c($e,be)};b(Qt,$e=>{var be;(be=r(De).latestPeriod)!=null&&be.label&&$e(Tr)})}var ht=p(Qt,2);{var Ue=$e=>{var be=qm(),Ve=i(be);S(Et=>C(Ve,`최초 ${Et??""}`),[()=>we(r(De).firstPeriod)]),c($e,be)};b(ht,$e=>{var be,Ve;(be=r(De).firstPeriod)!=null&&be.label&&r(De).firstPeriod.label!==((Ve=r(De).latestPeriod)==null?void 0:Ve.label)&&$e(Ue)})}var Vt=p(ht,2);{var lr=$e=>{var be=Bm(),Ve=i(be);S(()=>C(Ve,`${r(De).periodCount??""}기간`)),c($e,be)};b(Vt,$e=>{r(De).periodCount>0&&$e(lr)})}var nr=p(Vt,2);{var dr=$e=>{var be=Fm(),Ve=i(be);S(()=>C(Ve,`최근 변경 ${r(De).latestChange??""}`)),c($e,be)};b(nr,$e=>{r(De).latestChange&&$e(dr)})}var Pr=p($t,2);{var _a=$e=>{var be=Um();Ce(be,21,()=>r(De).timeline,Te,(Ve,Et)=>{var or=Hm(),hr=i(or),mr=i(hr);S((yr,gr)=>{Re(or,1,`vw-timeline-chip ${yr??""}`,"svelte-1l2nqwu"),C(mr,gr)},[()=>W(r(De),r(Et).period.label)?"is-active":"",()=>we(r(Et).period)]),ce("click",or,()=>N(r(De).id,r(Et).period.label)),c(Ve,or)}),c($e,be)};b(Pr,$e=>{var be;((be=r(De).timeline)==null?void 0:be.length)>0&&$e(_a)})}var y=p(Pr,2);{var ie=$e=>{var be=Wm(),Ve=i(be),Et=i(Ve),or=p(Ve,2);{var hr=ve=>{var ge=Km(),vt=i(ge);S(et=>C(vt,`비교 ${et??""}`),[()=>we(r(Ke).prevPeriod)]),c(ve,ge)},mr=ve=>{var ge=Gm();c(ve,ge)};b(or,ve=>{var ge;(ge=r(Ke).prevPeriod)!=null&&ge.label?ve(hr):ve(mr,-1)})}var yr=p(or,2),gr=i(yr);S((ve,ge)=>{C(Et,`선택 ${ve??""}`),C(gr,ge)},[()=>we(r(Ke).period),()=>ue(r(Ke).status)]),c($e,be)};b(y,$e=>{r(Ge)&&r(Ke)&&$e(ie)})}var ye=p(y,2);{var Ee=$e=>{const be=L(()=>r(Ke).digest);var Ve=Zm(),Et=i(Ve),or=i(Et),hr=i(or),mr=p(Et,2),yr=i(mr);Ce(yr,17,()=>r(be).items.filter(et=>et.kind==="numeric"),Te,(et,_t)=>{var tr=Ym(),Bt=p(i(tr));S(()=>C(Bt,` ${r(_t).text??""}`)),c(et,tr)});var gr=p(yr,2);Ce(gr,17,()=>r(be).items.filter(et=>et.kind==="added"),Te,(et,_t)=>{var tr=Jm(),Bt=p(i(tr),2),Zt=i(Bt);S(()=>C(Zt,r(_t).text)),c(et,tr)});var ve=p(gr,2);Ce(ve,17,()=>r(be).items.filter(et=>et.kind==="removed"),Te,(et,_t)=>{var tr=Xm(),Bt=p(i(tr),2),Zt=i(Bt);S(()=>C(Zt,r(_t).text)),c(et,tr)});var ge=p(ve,2);{var vt=et=>{var _t=Qm(),tr=i(_t);S(()=>C(tr,`외 ${r(be).wordingCount??""}건 문구 수정`)),c(et,_t)};b(ge,et=>{r(be).wordingCount>0&&et(vt)})}S(()=>C(hr,`${r(be).to??""} vs ${r(be).from??""}`)),c($e,Ve)};b(ye,$e=>{var be,Ve,Et;r(Ge)&&((Et=(Ve=(be=r(Ke))==null?void 0:be.digest)==null?void 0:Ve.items)==null?void 0:Et.length)>0&&$e(Ee)})}var Be=p(ye,2);{var yt=$e=>{var be=_e(),Ve=ae(be);{var Et=hr=>{var mr=ax();Ce(mr,21,()=>ze(r(Ke)),Te,(yr,gr)=>{var ve=_e(),ge=ae(ve);{var vt=Bt=>{var Zt=_e(),Kr=ae(Zt);Ma(Kr,()=>O(r(gr).text)),c(Bt,Zt)},et=Bt=>{var Zt=ex(),Kr=i(Zt);S(()=>C(Kr,r(gr).text)),c(Bt,Zt)},_t=Bt=>{var Zt=tx(),Kr=i(Zt);S(()=>C(Kr,r(gr).text)),c(Bt,Zt)},tr=Bt=>{var Zt=rx(),Kr=i(Zt);S(()=>C(Kr,r(gr).text)),c(Bt,Zt)};b(ge,Bt=>{r(gr).kind==="heading"?Bt(vt):r(gr).kind==="same"?Bt(et,1):r(gr).kind==="added"?Bt(_t,2):r(gr).kind==="removed"&&Bt(tr,3)})}c(yr,ve)}),c(hr,mr)},or=hr=>{var mr=nx(),yr=i(mr);Ma(yr,()=>Q(r(Ke).body)),c(hr,mr)};b(Ve,hr=>{var mr,yr;r(Ge)&&((mr=r(Ke).prevPeriod)!=null&&mr.label)&&((yr=r(Ke).diff)==null?void 0:yr.length)>0?hr(Et):hr(or,-1)})}c($e,be)};b(Be,$e=>{r(Ke)&&$e(yt)})}S(($e,be)=>{Re(qt,1,`vw-text-section ${r(De).status==="stale"?"vw-text-section-stale":""}`,"svelte-1l2nqwu"),Re(Ot,1,`vw-status-pill ${$e??""}`,"svelte-1l2nqwu"),C(ir,be)},[()=>me(r(De).status),()=>P(r(De).status)]),c(rt,qt)}),S(()=>C(Yt,`본문 ${r(x).sectionCount??""}개`)),c(Gt,Se)};b(fr,Gt=>{var Se,Ne;((Ne=(Se=r(x))==null?void 0:Se.sections)==null?void 0:Ne.length)>0&&Gt(kt)})}var Ft=p(fr,2);{var _r=Gt=>{var Se=ix();c(Gt,Se)};b(Ft,Gt=>{r(H).length>0&&Gt(_r)})}var xr=p(Ft,2);Ce(xr,17,()=>r(H),Te,(Gt,Se)=>{var Ne=_e(),Kt=ae(Ne);{var pr=Yt=>{const ct=L(()=>{var xt;return((xt=r(Se).data)==null?void 0:xt.columns)||[]}),mt=L(()=>{var xt;return((xt=r(Se).data)==null?void 0:xt.rows)||[]}),St=L(()=>r(Se).meta||{}),jt=L(()=>r(St).scaleDivisor||1);var Xt=vx(),We=ae(Xt);{var Lt=xt=>{var $t=lx(),Ot=i($t);S(()=>C(Ot,`(단위: ${r(St).scale??""})`)),c(xt,$t)};b(We,xt=>{r(St).scale&&xt(Lt)})}var rt=p(We,2),De=i(rt),Ke=i(De),Ge=i(Ke),qt=i(Ge);Ce(qt,21,()=>r(ct),Te,(xt,$t,Ot)=>{const ir=L(()=>/^\d{4}/.test(r($t)));var Qt=dx(),Tr=i(Qt);S(()=>{Re(Qt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${r(ir)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${Ot===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),C(Tr,r($t))}),c(xt,Qt)});var ur=p(Ge);Ce(ur,21,()=>r(mt),Te,(xt,$t,Ot)=>{var ir=ux();Re(ir,1,`hover:bg-white/[0.03] ${Ot%2===1?"bg-white/[0.012]":""}`),Ce(ir,21,()=>r(ct),Te,(Qt,Tr,ht)=>{const Ue=L(()=>r($t)[r(Tr)]??""),Vt=L(()=>Z(r(Ue))),lr=L(()=>Fe(r(Ue))),nr=L(()=>r(Vt)?dt(r(Ue),r(jt)):r(Ue));var dr=cx(),Pr=i(dr);S(()=>{Re(dr,1,`px-3 py-1.5 border-b border-white/[0.025]
																	${r(Vt)?"text-right tabular-nums font-mono text-[11.5px]":"whitespace-nowrap"}
																	${r(lr)?"text-red-400/60":r(Vt)?"text-dl-text/90":""}
																	${ht===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]":"text-dl-text-muted"}
																	${ht===0&&Ot%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),C(Pr,r(nr))}),c(Qt,dr)}),c(xt,ir)}),c(Yt,Xt)},Ir=Yt=>{const ct=L(()=>{var xt;return((xt=r(Se).data)==null?void 0:xt.columns)||[]}),mt=L(()=>{var xt;return((xt=r(Se).data)==null?void 0:xt.rows)||[]}),St=L(()=>r(Se).meta||{}),jt=L(()=>r(St).scaleDivisor||1);var Xt=hx(),We=ae(Xt);{var Lt=xt=>{var $t=fx(),Ot=i($t);S(()=>C(Ot,`(단위: ${r(St).scale??""})`)),c(xt,$t)};b(We,xt=>{r(St).scale&&xt(Lt)})}var rt=p(We,2),De=i(rt),Ke=i(De),Ge=i(Ke),qt=i(Ge);Ce(qt,21,()=>r(ct),Te,(xt,$t,Ot)=>{const ir=L(()=>/^\d{4}/.test(r($t)));var Qt=px(),Tr=i(Qt);S(()=>{Re(Qt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${r(ir)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${Ot===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),C(Tr,r($t))}),c(xt,Qt)});var ur=p(Ge);Ce(ur,21,()=>r(mt),Te,(xt,$t,Ot)=>{var ir=xx();Re(ir,1,`hover:bg-white/[0.03] ${Ot%2===1?"bg-white/[0.012]":""}`),Ce(ir,21,()=>r(ct),Te,(Qt,Tr,ht)=>{const Ue=L(()=>r($t)[r(Tr)]??""),Vt=L(()=>Z(r(Ue))),lr=L(()=>Fe(r(Ue))),nr=L(()=>r(Vt)?r(jt)>1?dt(r(Ue),r(jt)):nt(r(Ue)):r(Ue));var dr=mx(),Pr=i(dr);S(()=>{Re(dr,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${r(Vt)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${r(lr)?"text-red-400/60":r(Vt)?"text-dl-text/90":""}
																	${ht===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${ht===0&&Ot%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),C(Pr,r(nr))}),c(Qt,dr)}),c(xt,ir)}),c(Yt,Xt)},Wt=Yt=>{const ct=L(()=>Tt(Object.keys(r(Se).rawMarkdown))),mt=L(()=>r(T).get(r(Se).block)??0),St=L(()=>r(ct)[r(mt)]||r(ct)[0]);var jt=wx(),Xt=i(jt);{var We=Ke=>{var Ge=_x(),qt=i(Ge);Ce(qt,17,()=>r(ct).slice(0,8),Te,($t,Ot,ir)=>{var Qt=gx(),Tr=i(Qt);S(()=>{Re(Qt,1,`px-2 py-0.5 rounded text-[10px] transition-colors
															${ir===r(mt)?"bg-white/[0.08] text-dl-text font-medium":"text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]"}`),C(Tr,r(Ot))}),ce("click",Qt,()=>re(r(Se).block,ir)),c($t,Qt)});var ur=p(qt,2);{var xt=$t=>{var Ot=bx(),ir=i(Ot);S(()=>C(ir,`외 ${r(ct).length-8}개`)),c($t,Ot)};b(ur,$t=>{r(ct).length>8&&$t(xt)})}c(Ke,Ge)};b(Xt,Ke=>{r(ct).length>1&&Ke(We)})}var Lt=p(Xt,2),rt=i(Lt),De=i(rt);Ma(De,()=>yn(r(Se).rawMarkdown[r(St)])),c(Yt,jt)},er=Yt=>{const ct=L(()=>{var Ge;return((Ge=r(Se).data)==null?void 0:Ge.columns)||[]}),mt=L(()=>{var Ge;return((Ge=r(Se).data)==null?void 0:Ge.rows)||[]});var St=Cx(),jt=i(St),Xt=i(jt);Js(Xt,{size:12,class:"text-emerald-400/50"});var We=p(jt,2),Lt=i(We),rt=i(Lt),De=i(rt);Ce(De,21,()=>r(ct),Te,(Ge,qt,ur)=>{const xt=L(()=>/^\d{4}/.test(r(qt)));var $t=yx(),Ot=i($t);S(()=>{Re($t,1,`px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															${r(xt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
															${ur===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),C(Ot,r(qt))}),c(Ge,$t)});var Ke=p(rt);Ce(Ke,21,()=>r(mt),Te,(Ge,qt,ur)=>{var xt=$x();Re(xt,1,`hover:bg-white/[0.03] ${ur%2===1?"bg-white/[0.012]":""}`),Ce(xt,21,()=>r(ct),Te,($t,Ot,ir)=>{const Qt=L(()=>r(qt)[r(Ot)]??""),Tr=L(()=>Z(r(Qt))),ht=L(()=>Fe(r(Qt)));var Ue=kx(),Vt=i(Ue);S(lr=>{Re(Ue,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${r(Tr)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${r(ht)?"text-red-400/60":r(Tr)?"text-dl-text/90":""}
																	${ir===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${ir===0&&ur%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),C(Vt,lr)},[()=>r(Tr)?nt(r(Qt)):r(Qt)]),c($t,Ue)}),c(Ge,xt)}),c(Yt,St)},Or=Yt=>{const ct=L(()=>r(Se).data.columns),mt=L(()=>r(Se).data.rows||[]);var St=zx(),jt=i(St),Xt=i(jt),We=i(Xt),Lt=i(We);Ce(Lt,21,()=>r(ct),Te,(De,Ke)=>{var Ge=Sx(),qt=i(Ge);S(()=>C(qt,r(Ke))),c(De,Ge)});var rt=p(We);Ce(rt,21,()=>r(mt),Te,(De,Ke,Ge)=>{var qt=Mx();Re(qt,1,`hover:bg-white/[0.03] ${Ge%2===1?"bg-white/[0.012]":""}`),Ce(qt,21,()=>r(ct),Te,(ur,xt)=>{var $t=Tx(),Ot=i($t);S(()=>C(Ot,r(Ke)[r(xt)]??"")),c(ur,$t)}),c(De,qt)}),c(Yt,St)};b(Kt,Yt=>{var ct,mt;r(Se).kind==="finance"?Yt(pr):r(Se).kind==="structured"?Yt(Ir,1):r(Se).kind==="raw_markdown"&&r(Se).rawMarkdown?Yt(Wt,2):r(Se).kind==="report"?Yt(er,3):((mt=(ct=r(Se).data)==null?void 0:ct.columns)==null?void 0:mt.length)>0&&Yt(Or,4)})}c(Gt,Ne)}),c(Ze,At)};b(pt,Ze=>{r(h)?Ze(je):Ze(ot,-1)})}S(Ze=>{C(ft,Ze),ua(bt,"title",r(V)?"목차 표시":"전체화면")},[()=>de(r(d))]),ce("click",bt,()=>u(V,!r(V))),c(Je,Xe)};b(Ae,Je=>{r(d)?Je(gt,-1):Je(Me)})}c(g,A)},K=g=>{var A=Px(),R=i(A);ca(R,{size:36,strokeWidth:1,class:"opacity-20"}),c(g,A)};b(ke,g=>{var A;r(l)?g(w):(A=r(o))!=null&&A.rows?g(U,1):g(K,-1)})}c(e,le),Sr()}Hr(["click"]);var Ox=f('<span class="text-[12px] font-semibold text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim"> </span>',1),Rx=f('<span class="text-[12px] font-semibold text-dl-text"> </span>'),Dx=f('<span class="text-[12px] font-semibold text-dl-text">데이터</span>'),jx=f('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" title="Excel 다운로드"><!></button> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button>',1),Vx=f('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),qx=f('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed"> </pre>'),Bx=f('<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2"> </div>'),Fx=f('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Hx=f('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),Ux=f("<!> <!>",1),Kx=f('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),Gx=f('<div class="p-4"><!></div>'),Wx=f('<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">표시할 내용이 없습니다</div>'),Yx=f('<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark"><div class="flex items-center justify-between h-10 mt-8 px-4 border-b border-dl-border/40 flex-shrink-0"><div class="flex items-center gap-2 min-w-0"><!></div> <div class="flex items-center gap-1"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 overflow-auto min-h-0"><!></div></div>');function Jx(e,t){Cr(t,!0);let a=Ie(t,"mode",3,null),n=Ie(t,"company",3,null),o=Ie(t,"data",3,null),l=Ie(t,"onTopicChange",3,null),s=Ie(t,"onFullscreen",3,null),d=Ie(t,"isFullscreen",3,!1),v=Y(!1);async function m(){var P;if(!(!((P=n())!=null&&P.stockCode)||r(v))){u(v,!0);try{await _v(n().stockCode)}catch(me){console.error("Excel download error:",me)}u(v,!1)}}function x(P){return P?/^\|.+\|$/m.test(P)||/^#{1,3} /m.test(P)||/\*\*[^*]+\*\*/m.test(P)||/```/.test(P):!1}var h=Yx(),_=i(h),M=i(_),$=i(M);{var V=P=>{var me=Ox(),E=ae(me),B=i(E),oe=p(E,2),fe=i(oe);S(()=>{C(B,n().corpName||n().company),C(fe,n().stockCode)}),c(P,me)},T=P=>{var me=Rx(),E=i(me);S(()=>C(E,o().label)),c(P,me)},z=P=>{var me=Dx();c(P,me)};b($,P=>{var me;a()==="viewer"&&n()?P(V):a()==="data"&&((me=o())!=null&&me.label)?P(T,1):a()==="data"&&P(z,2)})}var I=p(M,2),D=i(I);{var j=P=>{var me=jx(),E=ae(me),B=i(E);{var oe=Q=>{Nr(Q,{size:14,class:"animate-spin"})},fe=Q=>{Io(Q,{size:14})};b(B,Q=>{r(v)?Q(oe):Q(fe,-1)})}var he=p(E,2),xe=i(he);{var se=Q=>{Vd(Q,{size:14})},we=Q=>{jd(Q,{size:14})};b(xe,Q=>{d()?Q(se):Q(we,-1)})}S(()=>{E.disabled=r(v),ua(he,"title",d()?"패널 모드로":"전체 화면")}),ce("click",E,m),ce("click",he,()=>{var Q;return(Q=s())==null?void 0:Q()}),c(P,me)};b(D,P=>{var me;a()==="viewer"&&((me=n())!=null&&me.stockCode)&&P(j)})}var de=p(D,2),pe=i(de);wn(pe,{size:15});var F=p(_,2),k=i(F);{var G=P=>{Lx(P,{get stockCode(){return n().stockCode},get onTopicChange(){return l()}})},N=P=>{var me=Gx(),E=i(me);{var B=he=>{var xe=_e(),se=ae(xe);{var we=ee=>{var W=Vx(),q=i(W);Ma(q,()=>yn(o())),c(ee,W)},Q=L(()=>x(o())),O=ee=>{var W=qx(),q=i(W);S(()=>C(q,o())),c(ee,W)};b(se,ee=>{r(Q)?ee(we):ee(O,-1)})}c(he,xe)},oe=he=>{var xe=Ux(),se=ae(xe);{var we=q=>{var ue=Bx(),ze=i(ue);S(()=>C(ze,o().module)),c(q,ue)};b(se,q=>{o().module&&q(we)})}var Q=p(se,2);{var O=q=>{var ue=Fx(),ze=i(ue);Ma(ze,()=>yn(o().text)),c(q,ue)},ee=L(()=>x(o().text)),W=q=>{var ue=Hx(),ze=i(ue);S(()=>C(ze,o().text)),c(q,ue)};b(Q,q=>{r(ee)?q(O):q(W,-1)})}c(he,xe)},fe=he=>{var xe=Kx(),se=i(xe);S(we=>C(se,we),[()=>JSON.stringify(o(),null,2)]),c(he,xe)};b(E,he=>{var xe;typeof o()=="string"?he(B):(xe=o())!=null&&xe.text?he(oe,1):he(fe,-1)})}c(P,me)},re=P=>{var me=Wx();c(P,me)};b(k,P=>{a()==="viewer"&&n()?P(G):a()==="data"&&o()?P(N,1):P(re,-1)})}ce("click",de,()=>{var P;return(P=t.onClose)==null?void 0:P.call(t)}),c(e,h),Sr()}Hr(["click"]);var Xx=f('<div class="flex flex-col items-center justify-center py-8 gap-2"><!> <span class="text-[11px] text-dl-text-dim">목차 로딩 중...</span></div>'),Qx=f('<button><!> <span class="truncate"> </span></button>'),Zx=f('<div class="mb-1 pb-1 border-b border-dl-border/15"><div class="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-amber-400/70 uppercase tracking-wider"><!> <span>즐겨찾기</span></div> <!></div>'),e1=f('<button class="flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors text-dl-text-dim hover:text-dl-text hover:bg-white/5"><!> <span class="truncate"> </span></button>'),t1=f('<div class="mb-1 pb-1 border-b border-dl-border/15"><div class="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-dl-text-dim/60 uppercase tracking-wider"><!> <span>최근</span></div> <!></div>'),r1=f('<span class="w-1.5 h-1.5 rounded-full bg-emerald-400/70" title="최근 변경"></span>'),a1=f('<span class="text-[9px] text-dl-text-dim/60 font-mono"> </span>'),n1=f('<button><!> <span class="truncate"> </span> <span class="ml-auto flex items-center gap-0.5"><!> <!> <!></span></button>'),o1=f('<div class="ml-2 border-l border-dl-border/20 pl-1"></div>'),s1=f('<div class="mb-0.5"><button class="flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-left text-[11px] font-semibold uppercase tracking-wider text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] text-dl-text-dim/60 font-mono"> </span></button> <!></div>'),i1=f("<!> <!> <!>",1),l1=f('<div class="px-3 py-6 text-center text-[12px] text-dl-text-dim">종목을 선택하면 목차가 표시됩니다</div>'),d1=f('<nav class="flex flex-col h-full min-h-0 overflow-y-auto py-2 px-1"><!></nav>');function c1(e,t){Cr(t,!0);let a=Ie(t,"toc",3,null),n=Ie(t,"loading",3,!1),o=Ie(t,"selectedTopic",3,null),l=Ie(t,"expandedChapters",19,()=>new Set),s=Ie(t,"bookmarks",19,()=>[]),d=Ie(t,"recentHistory",19,()=>[]),v=Ie(t,"onSelectTopic",3,null),m=Ie(t,"onToggleChapter",3,null);const x=new Set(["BS","IS","CIS","CF","SCE","ratios"]);function h(I){return x.has(I)?ss:ca}function _(I){return I.tableCount>0&&I.textCount>0?"both":I.tableCount>0?"table":I.textCount>0?"text":"empty"}$r(()=>{o()&&sd().then(()=>{const I=document.querySelector(".viewer-nav-active-item");I&&I.scrollIntoView({block:"nearest",behavior:"smooth"})})});var M=d1(),$=i(M);{var V=I=>{var D=Xx(),j=i(D);Nr(j,{size:18,class:"animate-spin text-dl-text-dim"}),c(I,D)},T=I=>{var D=i1(),j=ae(D);{var de=G=>{const N=L(()=>s().map(E=>{for(const B of a().chapters){const oe=B.topics.find(fe=>fe.topic===E);if(oe)return{...oe,chapter:B.chapter}}return null}).filter(Boolean));var re=_e(),P=ae(re);{var me=E=>{var B=Zx(),oe=i(B),fe=i(oe);Zs(fe,{size:10,fill:"currentColor"});var he=p(oe,2);Ce(he,17,()=>r(N),Te,(xe,se)=>{const we=L(()=>o()===r(se).topic);var Q=Qx(),O=i(Q);Zs(O,{size:10,class:"text-amber-400/60 flex-shrink-0",fill:"currentColor"});var ee=p(O,2),W=i(ee);S(()=>{Re(Q,1,`flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors ${r(we)?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-muted hover:text-dl-text hover:bg-white/5"}`),C(W,r(se).label)}),ce("click",Q,()=>{var q;return(q=v())==null?void 0:q(r(se).topic,r(se).chapter)}),c(xe,Q)}),c(E,B)};b(P,E=>{r(N).length>0&&E(me)})}c(G,re)};b(j,G=>{s().length>0&&G(de)})}var pe=p(j,2);{var F=G=>{const N=L(()=>new Set(s())),re=L(()=>d().slice(0,5).filter(B=>B.topic!==o()&&!r(N).has(B.topic)));var P=_e(),me=ae(P);{var E=B=>{var oe=t1(),fe=i(oe),he=i(fe);is(he,{size:10});var xe=p(fe,2);Ce(xe,17,()=>r(re),Te,(se,we)=>{var Q=e1(),O=i(Q);is(O,{size:10,class:"text-dl-text-dim/30 flex-shrink-0"});var ee=p(O,2),W=i(ee);S(()=>C(W,r(we).label)),ce("click",Q,()=>{var q;return(q=v())==null?void 0:q(r(we).topic,null)}),c(se,Q)}),c(B,oe)};b(me,B=>{r(re).length>0&&B(E)})}c(G,P)};b(pe,G=>{d().length>0&&G(F)})}var k=p(pe,2);Ce(k,17,()=>a().chapters,Te,(G,N)=>{var re=s1(),P=i(re),me=i(P);{var E=ee=>{Rd(ee,{size:12})},B=L(()=>l().has(r(N).chapter)),oe=ee=>{Dd(ee,{size:12})};b(me,ee=>{r(B)?ee(E):ee(oe,-1)})}var fe=p(me,2),he=i(fe),xe=p(fe,2),se=i(xe),we=p(P,2);{var Q=ee=>{var W=o1();Ce(W,21,()=>r(N).topics,Te,(q,ue)=>{const ze=L(()=>h(r(ue).topic)),Z=L(()=>_(r(ue))),Fe=L(()=>o()===r(ue).topic);var dt=n1(),nt=i(dt);vo(nt,()=>r(ze),(g,A)=>{A(g,{size:12,class:"flex-shrink-0 opacity-50"})});var Ye=p(nt,2),zt=i(Ye),Tt=p(Ye,2),H=i(Tt);{var le=g=>{var A=r1();c(g,A)};b(H,g=>{r(ue).hasChanges&&g(le)})}var ke=p(H,2);{var w=g=>{ei(g,{size:9,class:"text-dl-text-dim/40"})};b(ke,g=>{(r(Z)==="table"||r(Z)==="both")&&g(w)})}var U=p(ke,2);{var K=g=>{var A=a1(),R=i(A);S(()=>C(R,r(ue).tableCount)),c(g,A)};b(U,g=>{r(ue).tableCount>0&&g(K)})}S(()=>{Re(dt,1,`${r(Fe)?"viewer-nav-active-item":""} viewer-nav-active flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors ${r(Fe)?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-muted hover:text-dl-text hover:bg-white/5"}`),C(zt,r(ue).label)}),ce("click",dt,()=>{var g;return(g=v())==null?void 0:g(r(ue).topic,r(N).chapter)}),c(q,dt)}),c(ee,W)},O=L(()=>l().has(r(N).chapter));b(we,ee=>{r(O)&&ee(Q)})}S(()=>{C(he,r(N).chapter),C(se,r(N).topics.length)}),ce("click",P,()=>{var ee;return(ee=m())==null?void 0:ee(r(N).chapter)}),c(G,re)}),c(I,D)},z=I=>{var D=l1();c(I,D)};b($,I=>{var D;n()?I(V):(D=a())!=null&&D.chapters?I(T,1):I(z,-1)})}c(e,M),Sr()}Hr(["click"]);const u1="modulepreload",v1=function(e){return"/"+e},ll={},ti=function(t,a,n){let o=Promise.resolve();if(a&&a.length>0){let s=function(m){return Promise.all(m.map(x=>Promise.resolve(x).then(h=>({status:"fulfilled",value:h}),h=>({status:"rejected",reason:h}))))};document.getElementsByTagName("link");const d=document.querySelector("meta[property=csp-nonce]"),v=(d==null?void 0:d.nonce)||(d==null?void 0:d.getAttribute("nonce"));o=s(a.map(m=>{if(m=v1(m),m in ll)return;ll[m]=!0;const x=m.endsWith(".css"),h=x?'[rel="stylesheet"]':"";if(document.querySelector(`link[href="${m}"]${h}`))return;const _=document.createElement("link");if(_.rel=x?"stylesheet":u1,x||(_.as="script"),_.crossOrigin="",_.href=m,v&&_.setAttribute("nonce",v),document.head.appendChild(_),x)return new Promise((M,$)=>{_.addEventListener("load",M),_.addEventListener("error",()=>$(new Error(`Unable to preload CSS for ${m}`)))})}))}function l(s){const d=new Event("vite:preloadError",{cancelable:!0});if(d.payload=s,window.dispatchEvent(d),!d.defaultPrevented)throw s}return o.then(s=>{for(const d of s||[])d.status==="rejected"&&l(d.reason);return t().catch(l)})},ri=["#ea4647","#fb923c","#3b82f6","#22c55e","#8b5cf6","#06b6d4","#f59e0b","#ec4899"],dl={performance:"성과",profitability:"수익성",health:"건전성",cashflow:"현금흐름",governance:"지배구조",risk:"리스크",opportunity:"기회"},f1={A:5,B:4,C:3,D:2,F:0};function p1(e){var m,x;if(!((m=e==null?void 0:e.data)!=null&&m.rows)||!((x=e==null?void 0:e.data)!=null&&x.columns))return null;const{rows:t,columns:a}=e.data,n=e.meta||{},o=a.filter(h=>/^\d{4}/.test(h));if(o.length<2)return null;const l=a[0],s=[],d=["bar","line","line"];return t.slice(0,3).forEach((h,_)=>{const M=h[l]||`항목${_}`,$=o.map(V=>{const T=h[V];return T!=null?Number(T):0});$.some(V=>V!==0)&&s.push({name:M,data:$,color:ri[_%ri.length],type:d[_]||"line"})}),s.length===0?null:{chartType:"combo",title:n.title||"재무 추이",series:s,categories:o,options:{unit:n.unit||"백만원"}}}function m1(e,t=""){if(!e)return null;const a=Object.keys(dl),n=a.map(l=>dl[l]),o=a.map(l=>{var d;const s=((d=e[l])==null?void 0:d.grade)||e[l]||"F";return f1[s]??0});return{chartType:"radar",title:t?`${t} 투자 인사이트`:"투자 인사이트",series:[{name:t||"등급",data:o,color:ri[0]}],categories:n,options:{maxValue:5}}}var x1=f("<button> </button>"),h1=f('<div class="flex items-center gap-0.5 overflow-x-auto py-1 scrollbar-thin"></div>');function Hd(e,t){Cr(t,!0);let a=Ie(t,"periods",19,()=>[]),n=Ie(t,"selected",3,null),o=Ie(t,"onSelect",3,null);function l(x){return/^\d{4}$/.test(x)||/^\d{4}Q4$/.test(x)}function s(x){const h=x.match(/^(\d{4})(Q([1-4]))?$/);if(!h)return x;const _="'"+h[1].slice(2);return h[3]?`${_}.${h[3]}Q`:_}var d=_e(),v=ae(d);{var m=x=>{var h=h1();Ce(h,21,a,Te,(_,M)=>{var $=x1(),V=i($);S((T,z)=>{Re($,1,`flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] font-mono transition-colors
					${T??""}`),ua($,"title",r(M)),C(V,z)},[()=>n()===r(M)?"bg-dl-primary/20 text-dl-primary-light font-medium":l(r(M))?"text-dl-text-muted hover:text-dl-text hover:bg-white/5":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5",()=>s(r(M))]),ce("click",$,()=>{var T;return(T=o())==null?void 0:T(r(M))}),c(_,$)}),c(x,h)};b(v,x=>{a().length>0&&x(m)})}c(e,d),Sr()}Hr(["click"]);var g1=f('<div class="mb-1"><!></div>'),b1=f('<!> <div class="text-[10px] text-dl-text-dim mb-1 font-mono"> </div> <div class="prose-dartlab overflow-x-auto"><!></div>',1),_1=f('<th class="cursor-pointer select-none hover:text-dl-text"> </th>'),w1=f("<td> </td>"),y1=f("<tr></tr>"),k1=f('<button class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"> </button>'),$1=f('<div class="text-[10px] text-dl-text-dim mt-1"> </div>'),C1=f('<div class="overflow-x-auto rounded-lg border border-dl-border/10"><table class="finance-table"><thead><tr></tr></thead><tbody></tbody></table> <!></div> <!>',1),S1=f('<th class="cursor-pointer select-none hover:text-dl-text"> </th>'),T1=f("<td> </td>"),M1=f("<tr></tr>"),z1=f('<button class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"> </button>'),A1=f('<div class="text-[10px] text-dl-text-dim mt-1"> </div>'),E1=f('<div class="overflow-x-auto rounded-lg border border-dl-border/10"><table class="prose-dartlab w-full text-[12px]"><thead><tr></tr></thead><tbody></tbody></table> <!></div> <!>',1);function cl(e,t){Cr(t,!0);let a=Ie(t,"block",3,null),n=Ie(t,"maxRows",3,100),o=Y(null),l=Y(!1),s=Y(null),d=Y("asc");function v(F){r(s)===F?u(d,r(d)==="asc"?"desc":"asc",!0):(u(s,F,!0),u(d,"asc"))}function m(F){return r(s)!==F?"":r(d)==="asc"?" ▲":" ▼"}const x=new Set(["매출액","revenue","영업이익","operating_income","당기순이익","net_income","자산총계","total_assets","부채총계","total_liabilities","자본총계","total_equity","영업활동현금흐름","operating_cash_flow","매출총이익","gross_profit","EBITDA"]);function h(F,k){if(!(k!=null&&k.length))return!1;const G=String(F[k[0]]??"").trim();return x.has(G)}function _(F){if(F==null||F===""||F==="-")return F??"";if(typeof F=="number")return Math.abs(F)>=1?F.toLocaleString("ko-KR"):F.toString();const k=String(F).trim();if(/^-?[\d,]+(\.\d+)?$/.test(k)){const G=parseFloat(k.replace(/,/g,""));if(!isNaN(G))return Math.abs(G)>=1?G.toLocaleString("ko-KR"):G.toString()}return F}function M(F){if(typeof F=="number")return F<0;const k=String(F??"").trim().replace(/,/g,"");return/^-\d/.test(k)}function $(F){return typeof F=="number"?!0:typeof F=="string"&&/^-?[\d,]+(\.\d+)?$/.test(F.trim())}function V(F){return(F==null?void 0:F.kind)==="finance"}function T(F){return F!=null&&F.rawMarkdown?Object.keys(F.rawMarkdown):[]}function z(F){const k=T(F);return r(o)&&k.includes(r(o))?r(o):k[0]??null}let I=L(()=>{var G,N;const F=((N=(G=a())==null?void 0:G.data)==null?void 0:N.rows)??[];return r(s)?[...F].sort((re,P)=>{let me=re[r(s)],E=P[r(s)];const B=typeof me=="number"?me:parseFloat(String(me??"").replace(/,/g,"")),oe=typeof E=="number"?E:parseFloat(String(E??"").replace(/,/g,""));return!isNaN(B)&&!isNaN(oe)?r(d)==="asc"?B-oe:oe-B:(me=String(me??""),E=String(E??""),r(d)==="asc"?me.localeCompare(E):E.localeCompare(me))}):F}),D=L(()=>r(l)?r(I):r(I).slice(0,n()));var j=_e(),de=ae(j);{var pe=F=>{var k=_e(),G=ae(k);{var N=E=>{const B=L(()=>T(a())),oe=L(()=>z(a()));var fe=_e(),he=ae(fe);{var xe=se=>{var we=b1(),Q=ae(we);{var O=ze=>{var Z=g1(),Fe=i(Z);Hd(Fe,{get periods(){return r(B)},get selected(){return r(oe)},onSelect:dt=>{u(o,dt,!0)}}),c(ze,Z)};b(Q,ze=>{r(B).length>1&&ze(O)})}var ee=p(Q,2),W=i(ee),q=p(ee,2),ue=i(q);Ma(ue,()=>yn(a().rawMarkdown[r(oe)])),S(()=>C(W,r(oe))),c(se,we)};b(he,se=>{r(B).length>0&&se(xe)})}c(E,fe)},re=E=>{var B=C1(),oe=ae(B),fe=i(oe),he=i(fe),xe=i(he);Ce(xe,21,()=>a().data.columns??[],Te,(W,q)=>{var ue=_1(),ze=i(ue);S(Z=>C(ze,`${r(q)??""}${Z??""}`),[()=>m(r(q))]),ce("click",ue,()=>v(r(q))),c(W,ue)});var se=p(he);Ce(se,21,()=>r(D),Te,(W,q)=>{const ue=L(()=>h(r(q),a().data.columns));var ze=y1();Ce(ze,21,()=>a().data.columns??[],Te,(Z,Fe,dt)=>{const nt=L(()=>r(q)[r(Fe)]),Ye=L(()=>dt>0&&$(r(nt)));var zt=w1(),Tt=i(zt);S((H,le)=>{Re(zt,1,H),C(Tt,le)},[()=>r(Ye)?M(r(nt))?"val-neg":"val-pos":"",()=>r(Ye)?_(r(nt)):r(nt)??""]),c(Z,zt)}),S(()=>Re(ze,1,rr(r(ue)?"row-key":""))),c(W,ze)});var we=p(fe,2);{var Q=W=>{var q=k1(),ue=i(q);S(()=>C(ue,`외 ${a().data.rows.length-n()}행 더 보기`)),ce("click",q,()=>{u(l,!0)}),c(W,q)};b(we,W=>{!r(l)&&a().data.rows.length>n()&&W(Q)})}var O=p(oe,2);{var ee=W=>{var q=$1(),ue=i(q);S(()=>C(ue,`단위: ${(a().meta.unit||"")??""} ${a().meta.scale?`(${a().meta.scale})`:""}`)),c(W,q)};b(O,W=>{var q,ue;((q=a().meta)!=null&&q.scale||(ue=a().meta)!=null&&ue.unit)&&W(ee)})}c(E,B)},P=L(()=>{var E;return V(a())&&((E=a().data)==null?void 0:E.rows)}),me=E=>{var B=E1(),oe=ae(B),fe=i(oe),he=i(fe),xe=i(he);Ce(xe,21,()=>a().data.columns??[],Te,(W,q)=>{var ue=S1(),ze=i(ue);S(Z=>C(ze,`${r(q)??""}${Z??""}`),[()=>m(r(q))]),ce("click",ue,()=>v(r(q))),c(W,ue)});var se=p(he);Ce(se,21,()=>r(D),Te,(W,q)=>{var ue=M1();Ce(ue,21,()=>a().data.columns??[],Te,(ze,Z)=>{var Fe=T1(),dt=i(Fe);S(nt=>{Re(Fe,1,nt),C(dt,r(q)[r(Z)]??"")},[()=>rr($(r(q)[r(Z)])?"num":"")]),c(ze,Fe)}),c(W,ue)});var we=p(fe,2);{var Q=W=>{var q=z1(),ue=i(q);S(()=>C(ue,`외 ${a().data.rows.length-n()}행 더 보기`)),ce("click",q,()=>{u(l,!0)}),c(W,q)};b(we,W=>{!r(l)&&a().data.rows.length>n()&&W(Q)})}var O=p(oe,2);{var ee=W=>{var q=A1(),ue=i(q);S(()=>C(ue,`단위: ${(a().meta.unit||"")??""} ${a().meta.scale?`(${a().meta.scale})`:""}`)),c(W,q)};b(O,W=>{var q;(q=a().meta)!=null&&q.scale&&W(ee)})}c(E,B)};b(G,E=>{var B;a().kind==="raw_markdown"&&a().rawMarkdown?E(N):r(P)?E(re,1):(B=a().data)!=null&&B.rows&&E(me,2)})}c(F,k)};b(de,F=>{a()&&F(pe)})}c(e,j),Sr()}Hr(["click"]);var I1=f('<span class="flex items-center gap-1"><!> <span class="text-dl-accent"> </span> <span class="text-dl-text-dim/60"> </span></span>'),P1=f('<span class="flex items-center gap-1"><!> <span>변경 없음</span></span>'),N1=f('<span class="flex items-center gap-1 ml-auto"><span class="font-mono"> </span> <!> <span class="font-mono"> </span></span>'),L1=f('<div class="text-dl-success/80 truncate"> </div>'),O1=f('<div class="text-dl-primary-light/70 truncate"> </div>'),R1=f('<div class="text-[11px] leading-relaxed"><!> <!></div>'),D1=f('<div class="flex flex-col gap-1.5 p-2.5 rounded-lg bg-dl-surface-card border border-dl-border/20"><div class="flex items-center gap-3 text-[11px] text-dl-text-dim"><span class="font-mono"> </span> <!> <!></div> <!></div>');function j1(e,t){Cr(t,!0);let a=Ie(t,"summary",3,null);var n=_e(),o=ae(n);{var l=s=>{var d=D1(),v=i(d),m=i(v),x=i(m),h=p(m,2);{var _=I=>{var D=I1(),j=i(D);Xo(j,{size:11,class:"text-dl-accent"});var de=p(j,2),pe=i(de),F=p(de,2),k=i(F);S(G=>{C(pe,`변경 ${a().changedCount??""}회`),C(k,`(${G??""}%)`)},[()=>(a().changeRate*100).toFixed(1)]),c(I,D)},M=I=>{var D=P1(),j=i(D);qd(j,{size:11}),c(I,D)};b(h,I=>{a().changedCount>0?I(_):I(M,-1)})}var $=p(h,2);{var V=I=>{var D=N1(),j=i(D),de=i(j),pe=p(j,2);jf(pe,{size:10});var F=p(pe,2),k=i(F);S(()=>{C(de,a().latestFrom),C(k,a().latestTo)}),c(I,D)};b($,I=>{a().latestFrom&&a().latestTo&&I(V)})}var T=p(v,2);{var z=I=>{var D=R1(),j=i(D);Ce(j,17,()=>a().added.slice(0,2),Te,(pe,F)=>{var k=L1(),G=i(k);S(()=>C(G,`+ ${r(F)??""}`)),c(pe,k)});var de=p(j,2);Ce(de,17,()=>a().removed.slice(0,2),Te,(pe,F)=>{var k=O1(),G=i(k);S(()=>C(G,`- ${r(F)??""}`)),c(pe,k)}),c(I,D)};b(T,I=>{var D,j;(((D=a().added)==null?void 0:D.length)>0||((j=a().removed)==null?void 0:j.length)>0)&&I(z)})}S(()=>C(x,`${a().totalPeriods??""} periods`)),c(s,d)};b(o,s=>{a()&&s(l)})}c(e,n),Sr()}var V1=f("<option> </option>"),q1=f("<option> </option>"),B1=f('<button class="p-1 ml-1 text-dl-text-dim hover:text-dl-text"><!></button>'),F1=f('<span class="flex items-center gap-1 text-emerald-400"><!> <span> </span></span>'),H1=f('<span class="flex items-center gap-1 text-red-400"><!> <span> </span></span>'),U1=f('<span class="flex items-center gap-1 text-dl-text-dim"><!> <span> </span></span>'),K1=f('<div class="flex items-center gap-3 px-4 py-1.5 border-b border-dl-border/10 text-[10px]"><!> <!> <!></div>'),G1=f('<div class="flex items-center justify-center py-8 gap-2"><!> <span class="text-[12px] text-dl-text-dim">비교 로딩 중...</span></div>'),W1=f('<div class="text-[12px] text-red-400 py-4"> </div>'),Y1=f('<div class="pl-3 py-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-dl-text/85 text-[13px] leading-[1.8] rounded-r"><span class="text-emerald-500/60 text-[10px] mr-1">+</span> </div>'),J1=f('<div class="pl-3 py-1 border-l-2 border-red-400 bg-red-500/5 text-dl-text/40 text-[13px] leading-[1.8] rounded-r line-through decoration-red-400/30"><span class="text-red-400/60 text-[10px] mr-1">-</span> </div>'),X1=f('<p class="text-[13px] leading-[1.8] text-dl-text/70 py-0.5"> </p>'),Q1=f('<div class="space-y-0.5"></div>'),Z1=f('<div class="text-[12px] text-dl-text-dim text-center py-4">비교할 기간을 선택하세요</div>'),eh=f('<div class="rounded-xl border border-dl-border/20 bg-dl-surface-card overflow-hidden"><div class="flex items-center gap-2 px-4 py-2 border-b border-dl-border/15 bg-dl-bg-darker/50"><!> <span class="text-[12px] font-semibold text-dl-text">기간 비교</span> <div class="flex items-center gap-1 ml-auto"><select class="px-2 py-0.5 rounded bg-dl-bg-darker border border-dl-border/20 text-[11px] text-dl-text outline-none"></select> <span class="text-[11px] text-dl-text-dim">→</span> <select class="px-2 py-0.5 rounded bg-dl-bg-darker border border-dl-border/20 text-[11px] text-dl-text outline-none"></select> <!></div></div> <!> <div class="max-h-[60vh] overflow-y-auto px-4 py-3"><!></div></div>');function th(e,t){Cr(t,!0);let a=Ie(t,"stockCode",3,null),n=Ie(t,"topic",3,null),o=Ie(t,"periods",19,()=>[]),l=Ie(t,"onClose",3,null),s=Y(null),d=Y(null),v=Y(null),m=Y(!1),x=Y(null);$r(()=>{o().length>=2&&!r(s)&&!r(d)&&(u(d,o()[0],!0),u(s,o()[1],!0))});async function h(){if(!(!a()||!n()||!r(s)||!r(d))){u(m,!0),u(x,null);try{const E=await Sv(a(),n(),r(s),r(d));u(v,E,!0)}catch(E){u(x,E.message,!0)}u(m,!1)}}$r(()=>{r(s)&&r(d)&&r(s)!==r(d)&&h()});function _(E){if(!E)return"";const B=String(E).match(/^(\d{4})(Q([1-4]))?$/);return B?B[3]?`'${B[1].slice(2)}.${B[3]}Q`:`'${B[1].slice(2)}`:E}let M=L(()=>{var fe,he;if(!((fe=r(v))!=null&&fe.diff))return{added:0,removed:0,same:0};let E=0,B=0,oe=0;for(const xe of r(v).diff){const se=((he=xe.paragraphs)==null?void 0:he.length)||1;xe.kind==="added"?E+=se:xe.kind==="removed"?B+=se:oe+=se}return{added:E,removed:B,same:oe}});var $=eh(),V=i($),T=i(V);Od(T,{size:14,class:"text-dl-accent"});var z=p(T,4),I=i(z);Ce(I,21,o,Te,(E,B)=>{var oe=V1(),fe=i(oe),he={};S(xe=>{oe.disabled=r(B)===r(d),C(fe,xe),he!==(he=r(B))&&(oe.value=(oe.__value=r(B))??"")},[()=>_(r(B))]),c(E,oe)});var D=p(I,4);Ce(D,21,o,Te,(E,B)=>{var oe=q1(),fe=i(oe),he={};S(xe=>{oe.disabled=r(B)===r(s),C(fe,xe),he!==(he=r(B))&&(oe.value=(oe.__value=r(B))??"")},[()=>_(r(B))]),c(E,oe)});var j=p(D,2);{var de=E=>{var B=B1(),oe=i(B);wn(oe,{size:12}),ce("click",B,function(...fe){var he;(he=l())==null||he.apply(this,fe)}),c(E,B)};b(j,E=>{l()&&E(de)})}var pe=p(V,2);{var F=E=>{var B=K1(),oe=i(B);{var fe=Q=>{var O=F1(),ee=i(O);Qs(ee,{size:10});var W=p(ee,2),q=i(W);S(()=>C(q,`추가 ${r(M).added??""}`)),c(Q,O)};b(oe,Q=>{r(M).added>0&&Q(fe)})}var he=p(oe,2);{var xe=Q=>{var O=H1(),ee=i(O);qd(ee,{size:10});var W=p(ee,2),q=i(W);S(()=>C(q,`삭제 ${r(M).removed??""}`)),c(Q,O)};b(he,Q=>{r(M).removed>0&&Q(xe)})}var se=p(he,2);{var we=Q=>{var O=U1(),ee=i(O);Hf(ee,{size:10});var W=p(ee,2),q=i(W);S(()=>C(q,`유지 ${r(M).same??""}`)),c(Q,O)};b(se,Q=>{r(M).same>0&&Q(we)})}c(E,B)};b(pe,E=>{r(v)&&!r(m)&&E(F)})}var k=p(pe,2),G=i(k);{var N=E=>{var B=G1(),oe=i(B);Nr(oe,{size:14,class:"animate-spin text-dl-text-dim"}),c(E,B)},re=E=>{var B=W1(),oe=i(B);S(()=>C(oe,r(x))),c(E,B)},P=E=>{var B=Q1();Ce(B,21,()=>r(v).diff,Te,(oe,fe)=>{var he=_e(),xe=ae(he);Ce(xe,17,()=>r(fe).paragraphs||[r(fe).text||""],Te,(se,we)=>{const Q=L(()=>String(r(we)||"").trim());var O=_e(),ee=ae(O);{var W=q=>{var ue=_e(),ze=ae(ue);{var Z=nt=>{var Ye=Y1(),zt=p(i(Ye),1,!0);S(()=>C(zt,r(Q))),c(nt,Ye)},Fe=nt=>{var Ye=J1(),zt=p(i(Ye),1,!0);S(()=>C(zt,r(Q))),c(nt,Ye)},dt=nt=>{var Ye=X1(),zt=i(Ye);S(()=>C(zt,r(Q))),c(nt,Ye)};b(ze,nt=>{r(fe).kind==="added"?nt(Z):r(fe).kind==="removed"?nt(Fe,1):nt(dt,-1)})}c(q,ue)};b(ee,q=>{r(Q)&&q(W)})}c(se,O)}),c(oe,he)}),c(E,B)},me=E=>{var B=Z1();c(E,B)};b(G,E=>{var B;r(m)?E(N):r(x)?E(re,1):(B=r(v))!=null&&B.diff?E(P,2):E(me,-1)})}Hi(I,()=>r(s),E=>u(s,E)),Hi(D,()=>r(d),E=>u(d,E)),c(e,$),Sr()}Hr(["click"]);var rh=f("<button><!></button>"),ah=f("<button><!> <span>기간 비교</span></button>"),nh=f("<button><!> <span>AI 요약</span></button>"),oh=f('<div class="text-red-400/80"> </div>'),sh=f('<span class="inline-block w-1.5 h-3 bg-dl-accent/60 animate-pulse ml-0.5"></span>'),ih=f('<div class="whitespace-pre-wrap"> <!></div>'),lh=f('<div class="px-3 py-2 rounded-lg bg-dl-accent/5 border border-dl-accent/15 text-[12px] text-dl-text-muted leading-relaxed"><!></div>'),dh=f('<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim"> </span>'),ch=f('<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim"> </span>'),uh=f('<span class="px-2 py-0.5 rounded-full border border-emerald-500/20 bg-emerald-500/8 text-emerald-400/80"> </span>'),vh=f('<span class="px-2 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/8 text-blue-400/80"> </span>'),fh=f("<div> </div>"),ph=f('<h4 class="text-[14px] font-semibold text-dl-text"> </h4>'),mh=f('<div class="mb-2 mt-2"></div>'),xh=f('<span class="text-[10px] text-dl-text-dim font-mono"> </span>'),hh=f('<span class="text-[10px] text-dl-text-dim"> </span>'),gh=f('<span class="ml-0.5 text-emerald-400/50">*</span>'),bh=f("<button> <!></button>"),_h=f('<div class="flex flex-wrap gap-1 mb-2"></div>'),wh=f('<div class="text-blue-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-blue-400/60 mt-1.5 shrink-0"></span> </div>'),yh=f('<div class="text-emerald-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-emerald-400/50 mt-1.5 shrink-0"></span> </div>'),kh=f('<div class="text-dl-text-dim/50 flex gap-1"><span class="w-1 h-1 rounded-full bg-red-400/40 mt-1.5 shrink-0"></span> </div>'),$h=f('<div class="mb-3 px-3 py-2 rounded-lg border border-dl-border/15 bg-dl-surface-card/50 text-[11px] space-y-0.5 max-w-2xl"><div class="text-dl-text-dim font-medium"> </div> <!> <!> <!></div>'),Ch=f('<div class="mb-2 px-3 py-1.5 rounded-lg border border-dl-border/15 bg-dl-surface-card/30 text-[11px] text-dl-text-dim">이전 기간과 동일 — 변경 없음</div>'),Sh=f('<p class="vw-para"> </p>'),Th=f('<div class="pl-3 py-1 mb-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-dl-text/85 text-[14px] leading-[1.85] rounded-r"><span class="text-emerald-500/50 text-[10px] mr-1">+</span> </div>'),Mh=f('<div class="pl-3 py-1 mb-1 border-l-2 border-red-400 bg-red-500/5 text-dl-text/50 text-[14px] leading-[1.85] rounded-r line-through decoration-red-400/30"><span class="text-red-400/50 text-[10px] mr-1">-</span> </div>'),zh=f('<div><!> <div class="flex flex-wrap items-center gap-1.5 mb-2"><span> </span> <!> <!></div> <!> <!> <!>  <div class="disclosure-text max-w-3xl"><!></div></div>'),Ah=f('<div class="mt-6 pt-4 border-t border-dl-border/10"><div class="text-[10px] text-dl-text-dim uppercase tracking-widest font-semibold mb-3">표 · 정형 데이터</div></div>'),Eh=f("<button><!></button>"),Ih=f('<button class="p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="테이블 복사"><!></button>'),Ph=f('<div class="group relative"><div class="absolute top-1 right-1 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"><!> <!></div> <!></div>'),Nh=f('<div class="flex flex-wrap gap-1.5 text-[10px]"><!> <!> <!> <!></div> <!> <!> <!>',1),Lh=f('<h3 class="text-[14px] font-semibold text-dl-text mt-4 mb-1"> </h3>'),Oh=f('<div class="mb-1 opacity-0 group-hover:opacity-100 transition-opacity"><!></div>'),Rh=f('<!> <div class="text-[10px] text-dl-text-dim mb-1 font-mono"> </div> <div class="disclosure-text"><!></div>',1),Dh=f('<div class="group"><!></div>'),jh=f("<button><!></button>"),Vh=f('<button class="p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="테이블 복사"><!></button>'),qh=f('<div class="group relative"><div class="absolute top-1 right-1 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"><!> <!></div> <!></div>'),Bh=f('<div class="text-center py-12 text-[13px] text-dl-text-dim">이 topic에 표시할 데이터가 없습니다</div>'),Fh=f('<div class="space-y-4"><div class="flex items-center gap-2"><h2 class="text-[16px] font-semibold text-dl-text flex-1"> </h2> <!> <!> <!></div> <!> <!> <!> <!> <!></div>'),Hh=f('<button class="ask-ai-float"><span class="flex items-center gap-1"><!> AI에게 물어보기</span></button>'),Uh=f("<!> <!>",1);function Kh(e,t){Cr(t,!0);let a=Ie(t,"topicData",3,null),n=Ie(t,"diffSummary",3,null),o=Ie(t,"viewer",3,null),l=Ie(t,"onAskAI",3,null),s=Ie(t,"searchHighlight",3,null),d=Y(Ut(new Map)),v=Y(Ut(new Map)),m=Y(null),x=Y(Ut(new Map)),h=Y(Ut({show:!1,x:0,y:0,text:""})),_=Y(!1),M=Y(""),$=Y(null),V=Y(null);$r(()=>{var w,U,K;if((w=a())!=null&&w.topic){u(_,!1),u($,null);const g=(K=(U=o())==null?void 0:U.getTopicSummary)==null?void 0:K.call(U,a().topic);u(M,g||"",!0),r(V)&&(r(V).abort(),u(V,null))}});function T(){var w,U;!((w=o())!=null&&w.stockCode)||!((U=a())!=null&&U.topic)||(u(_,!0),u(M,""),u($,null),u(V,zv(o().stockCode,a().topic,{onContext(){},onChunk(K){u(M,r(M)+K)},onDone(){var K,g;u(_,!1),u(V,null),r(M)&&((g=(K=o())==null?void 0:K.setTopicSummary)==null||g.call(K,a().topic,r(M)))},onError(K){u(_,!1),u(V,null),u($,K,!0)}}),!0))}let z=L(()=>{var w,U,K;return((K=(w=o())==null?void 0:w.isBookmarked)==null?void 0:K.call(w,(U=a())==null?void 0:U.topic))??!1}),I=Y(!1);$r(()=>{var w;(w=a())!=null&&w.topic&&u(I,!1)});let D=L(()=>{var U,K,g,A,R,J;if(!((g=(K=(U=a())==null?void 0:U.textDocument)==null?void 0:K.sections)!=null&&g.length))return[];const w=new Set;for(const ne of a().textDocument.sections)if(ne.timeline)for(const Ae of ne.timeline){const Me=((A=Ae.period)==null?void 0:A.label)||((R=Ae.period)!=null&&R.year&&((J=Ae.period)!=null&&J.quarter)?`${Ae.period.year}Q${Ae.period.quarter}`:null);Me&&w.add(Me)}return[...w].sort().reverse()}),j=L(()=>{var w,U,K;return((K=(U=(w=a())==null?void 0:w.textDocument)==null?void 0:U.sections)==null?void 0:K.length)>0}),de=L(()=>{var w;return(((w=a())==null?void 0:w.blocks)??[]).filter(U=>U.kind!=="text")});function pe(w){if(!w)return"";if(typeof w=="string"){const U=w.match(/^(\d{4})(Q([1-4]))?$/);return U?U[3]?`${U[1]}Q${U[3]}`:U[1]:w}return w.kind==="annual"?`${w.year}Q4`:w.year&&w.quarter?`${w.year}Q${w.quarter}`:w.label||""}function F(w){return w==="updated"?"수정됨":w==="new"?"신규":w==="stale"?"과거유지":"유지"}function k(w){return w==="updated"?"bg-emerald-500/10 text-emerald-400/80 border-emerald-500/20":w==="new"?"bg-blue-500/10 text-blue-400/80 border-blue-500/20":w==="stale"?"bg-amber-500/10 text-amber-400/80 border-amber-500/20":"bg-dl-border/10 text-dl-text-dim border-dl-border/20"}function G(w){var K;const U=r(v).get(w.id);return U&&((K=w.views)!=null&&K[U])?w.views[U]:w.latest||null}function N(w,U){var g,A;const K=r(v).get(w.id);return K?K===U:((A=(g=w.latest)==null?void 0:g.period)==null?void 0:A.label)===U}function re(w){return r(v).has(w.id)}function P(w,U){const K=new Map(r(v));K.get(w)===U?K.delete(w):K.set(w,U),u(v,K,!0)}function me(w){return w.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function E(w){return String(w||"").replace(/\u00a0/g," ").replace(/\s+/g," ").trim()}function B(w){return!w||w.length>88?!1:/^\[.+\]$/.test(w)||/^【.+】$/.test(w)||/^[IVX]+\.\s/.test(w)||/^\d+\.\s/.test(w)||/^[가-힣]\.\s/.test(w)||/^\(\d+\)\s/.test(w)||/^\([가-힣]\)\s/.test(w)||/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(w)}function oe(w){return/^[가나다라마바사아자차카타파하]\.\s/.test(w)?1:/^\d+\.\s/.test(w)?2:/^\(\d+\)\s/.test(w)||/^\([가-힣]\)\s/.test(w)?3:/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(w)?4:/^\[.+\]$/.test(w)||/^【.+】$/.test(w)?1:2}function fe(w){if(!w)return"";if(/^\|.+\|$/m.test(w))return yn(w);const U=w.split(`
`);let K="",g=[];function A(){g.length!==0&&(K+=`<p class="vw-para">${me(g.join(" "))}</p>`,g=[])}for(const R of U){const J=E(R);if(!J){A();continue}if(B(J)){A();const ne=oe(J);K+=`<div class="ko-h${ne}">${me(J)}</div>`}else g.push(J)}return A(),K}function he(w){var K;if(!((K=w==null?void 0:w.diff)!=null&&K.length))return null;const U=[];for(const g of w.diff)for(const A of g.paragraphs||[])U.push({kind:g.kind,text:E(A)});return U}function xe(w){return r(d).get(w)??null}function se(w,U){const K=new Map(r(d));K.set(w,U),u(d,K,!0)}function we(w,U){var K,g;return(g=(K=w==null?void 0:w.data)==null?void 0:K.rows)!=null&&g[0]?w.data.rows[0][U]??null:null}function Q(w){var K,g,A;if(!((g=(K=w==null?void 0:w.data)==null?void 0:K.rows)!=null&&g[0]))return null;const U=w.data.rows[0];for(const R of((A=w.meta)==null?void 0:A.periods)??[])if(U[R])return{period:R,text:U[R]};return null}function O(w){var K,g,A;if(!((g=(K=w==null?void 0:w.data)==null?void 0:K.rows)!=null&&g[0]))return[];const U=w.data.rows[0];return(((A=w.meta)==null?void 0:A.periods)??[]).filter(R=>U[R]!=null)}function ee(w){return w.kind==="text"}function W(w){return w.kind==="finance"||w.kind==="structured"||w.kind==="report"||w.kind==="raw_markdown"}function q(w){var U,K,g,A;return w.kind==="finance"&&((K=(U=w.data)==null?void 0:U.rows)==null?void 0:K.length)>0&&((A=(g=w.data)==null?void 0:g.columns)==null?void 0:A.length)>2}function ue(w){return p1(w)}function ze(w){const U=new Map(r(x));U.set(w,!U.get(w)),u(x,U,!0)}function Z(w,U){var A,R;if(!((R=(A=w==null?void 0:w.data)==null?void 0:A.rows)!=null&&R.length))return;const K=w.data.columns||[],g=[K.join("	")];for(const J of w.data.rows)g.push(K.map(ne=>J[ne]??"").join("	"));navigator.clipboard.writeText(g.join(`
`)).then(()=>{u(m,U,!0),setTimeout(()=>{u(m,null)},2e3)})}function Fe(w){if(!l())return;const U=window.getSelection(),K=U==null?void 0:U.toString().trim();if(!K||K.length<5){u(h,{show:!1,x:0,y:0,text:""},!0);return}const A=U.getRangeAt(0).getBoundingClientRect();u(h,{show:!0,x:A.left+A.width/2,y:A.top-8,text:K.slice(0,500)},!0)}function dt(){r(h).text&&l()&&l()(r(h).text),u(h,{show:!1,x:0,y:0,text:""},!0)}function nt(){r(h).show&&u(h,{show:!1,x:0,y:0,text:""},!0)}function Ye(w){if(!s()||!w)return w;const U=s().replace(/[.*+?^${}()|[\]\\]/g,"\\$&"),K=new RegExp(`(${U})`,"gi");return w.replace(K,'<mark class="bg-amber-400/30 text-dl-text rounded-sm px-0.5">$1</mark>')}$r(()=>{var w;s()&&((w=a())!=null&&w.topic)&&requestAnimationFrame(()=>{const U=document.querySelector(".disclosure-text mark");U&&U.scrollIntoView({block:"center",behavior:"smooth"})})});var zt=Uh();xn("click",ql,nt);var Tt=ae(zt);{var H=w=>{var U=Fh(),K=i(U),g=i(K),A=i(g),R=p(g,2);{var J=Pe=>{var te=rh(),He=i(te);{let pt=L(()=>r(z)?"currentColor":"none");Zs(He,{size:14,get fill(){return r(pt)}})}S(()=>{Re(te,1,`p-1 rounded transition-colors ${r(z)?"text-amber-400":"text-dl-text-dim/30 hover:text-amber-400/60"}`),ua(te,"title",r(z)?"북마크 해제":"북마크 추가")}),ce("click",te,()=>o().toggleBookmark(a().topic)),c(Pe,te)};b(R,Pe=>{o()&&Pe(J)})}var ne=p(R,2);{var Ae=Pe=>{var te=ah(),He=i(te);Od(He,{size:10}),S(()=>Re(te,1,`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors border
						${r(I)?"border-dl-accent/30 bg-dl-accent/10 text-dl-accent-light":"border-dl-border/20 text-dl-text-dim hover:text-dl-text hover:bg-white/5"}`)),ce("click",te,()=>{u(I,!r(I))}),c(Pe,te)};b(ne,Pe=>{r(D).length>=2&&Pe(Ae)})}var Me=p(ne,2);{var gt=Pe=>{var te=nh(),He=i(te);{var pt=ot=>{Nr(ot,{size:10,class:"animate-spin"})},je=ot=>{Bd(ot,{size:10})};b(He,ot=>{r(_)?ot(pt):ot(je,-1)})}S(()=>{Re(te,1,`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors border
						${r(_)?"border-dl-accent/30 bg-dl-accent/10 text-dl-accent-light":"border-dl-border/20 text-dl-text-dim hover:text-dl-text hover:bg-white/5"}`),te.disabled=r(_)}),ce("click",te,T),c(Pe,te)};b(Me,Pe=>{var te;(te=o())!=null&&te.stockCode&&Pe(gt)})}var Je=p(K,2);{var Xe=Pe=>{var te=lh(),He=i(te);{var pt=ot=>{var Ze=oh(),At=i(Ze);S(()=>C(At,r($))),c(ot,Ze)},je=ot=>{var Ze=ih(),At=i(Ze),Dt=p(At);{var Jt=fr=>{var kt=sh();c(fr,kt)};b(Dt,fr=>{r(_)&&fr(Jt)})}S(()=>C(At,r(M))),c(ot,Ze)};b(He,ot=>{r($)?ot(pt):ot(je,-1)})}c(Pe,te)};b(Je,Pe=>{(r(M)||r(_)||r($))&&Pe(Xe)})}var ut=p(Je,2);j1(ut,{get summary(){return n()}});var ar=p(ut,2);{var lt=Pe=>{th(Pe,{get stockCode(){return o().stockCode},get topic(){return a().topic},get periods(){return r(D)},onClose:()=>{u(I,!1)}})};b(ar,Pe=>{var te;r(I)&&((te=o())!=null&&te.stockCode)&&Pe(lt)})}var Qe=p(ar,2);{var wt=Pe=>{const te=L(()=>a().textDocument);var He=Nh(),pt=ae(He),je=i(pt);{var ot=Se=>{var Ne=dh(),Kt=i(Ne);S(pr=>C(Kt,`최신 ${pr??""}`),[()=>pe(r(te).latestPeriod)]),c(Se,Ne)};b(je,Se=>{r(te).latestPeriod&&Se(ot)})}var Ze=p(je,2);{var At=Se=>{var Ne=ch(),Kt=i(Ne);S(()=>C(Kt,`${r(te).sectionCount??""}개 섹션`)),c(Se,Ne)};b(Ze,Se=>{r(te).sectionCount&&Se(At)})}var Dt=p(Ze,2);{var Jt=Se=>{var Ne=uh(),Kt=i(Ne);S(()=>C(Kt,`${r(te).updatedCount??""}개 수정`)),c(Se,Ne)};b(Dt,Se=>{r(te).updatedCount>0&&Se(Jt)})}var fr=p(Dt,2);{var kt=Se=>{var Ne=vh(),Kt=i(Ne);S(()=>C(Kt,`${r(te).newCount??""}개 신규`)),c(Se,Ne)};b(fr,Se=>{r(te).newCount>0&&Se(kt)})}var Ft=p(pt,2);Ce(Ft,17,()=>r(te).sections,Se=>Se.id,(Se,Ne)=>{const Kt=L(()=>G(r(Ne))),pr=L(()=>re(r(Ne))),Ir=L(()=>he(r(Kt))),Wt=L(()=>r(Ir)&&r(Ir).length>0),er=L(()=>r(Wt)&&(r(pr)||r(Ne).status==="updated")),Or=L(()=>r(pr)&&!r(Wt)&&r(Ne).periodCount>1);var Yt=zh(),ct=i(Yt);{var mt=ht=>{var Ue=mh();Ce(Ue,21,()=>r(Ne).headingPath,Te,(Vt,lr)=>{const nr=L(()=>{var y;return(y=r(lr).text)==null?void 0:y.trim()});var dr=_e(),Pr=ae(dr);{var _a=y=>{var ie=_e(),ye=ae(ie);{var Ee=$e=>{var be=fh(),Ve=i(be);S(Et=>{Re(be,1,`ko-h${Et??""}`),C(Ve,r(nr))},[()=>oe(r(nr))]),c($e,be)},Be=L(()=>B(r(nr))),yt=$e=>{var be=ph(),Ve=i(be);S(()=>C(Ve,r(nr))),c($e,be)};b(ye,$e=>{r(Be)?$e(Ee):$e(yt,-1)})}c(y,ie)};b(Pr,y=>{r(nr)&&y(_a)})}c(Vt,dr)}),c(ht,Ue)};b(ct,ht=>{var Ue;((Ue=r(Ne).headingPath)==null?void 0:Ue.length)>0&&ht(mt)})}var St=p(ct,2),jt=i(St),Xt=i(jt),We=p(jt,2);{var Lt=ht=>{var Ue=xh(),Vt=i(Ue);S(()=>C(Vt,r(Ne).latestChange)),c(ht,Ue)};b(We,ht=>{r(Ne).latestChange&&ht(Lt)})}var rt=p(We,2);{var De=ht=>{var Ue=hh(),Vt=i(Ue);S(()=>C(Vt,`${r(Ne).periodCount??""}기간`)),c(ht,Ue)};b(rt,ht=>{r(Ne).periodCount>1&&ht(De)})}var Ke=p(St,2);{var Ge=ht=>{var Ue=_h();Ce(Ue,21,()=>r(Ne).timeline,Te,(Vt,lr)=>{const nr=L(()=>{var ie;return((ie=r(lr).period)==null?void 0:ie.label)||pe(r(lr).period)});var dr=bh(),Pr=i(dr),_a=p(Pr);{var y=ie=>{var ye=gh();c(ie,ye)};b(_a,ie=>{r(lr).status==="updated"&&ie(y)})}S((ie,ye)=>{Re(dr,1,`px-2 py-1 rounded-lg text-[10px] font-mono transition-colors border
										${ie??""}`),C(Pr,`${ye??""} `)},[()=>N(r(Ne),r(nr))?"border-dl-accent/30 bg-dl-accent/8 text-dl-accent-light font-medium":r(lr).status==="updated"?"border-emerald-500/15 text-emerald-400/60 hover:bg-emerald-500/5":"border-dl-border/15 text-dl-text-dim hover:bg-white/3",()=>pe(r(lr).period)]),ce("click",dr,()=>P(r(Ne).id,r(nr))),c(Vt,dr)}),c(ht,Ue)};b(Ke,ht=>{var Ue;((Ue=r(Ne).timeline)==null?void 0:Ue.length)>1&&ht(Ge)})}var qt=p(Ke,2);{var ur=ht=>{const Ue=L(()=>r(Kt).digest);var Vt=$h(),lr=i(Vt),nr=i(lr),dr=p(lr,2);Ce(dr,17,()=>r(Ue).items.filter(y=>y.kind==="numeric"),Te,(y,ie)=>{var ye=wh(),Ee=p(i(ye),1,!0);S(()=>C(Ee,r(ie).text)),c(y,ye)});var Pr=p(dr,2);Ce(Pr,17,()=>r(Ue).items.filter(y=>y.kind==="added"),Te,(y,ie)=>{var ye=yh(),Ee=p(i(ye),1,!0);S(()=>C(Ee,r(ie).text)),c(y,ye)});var _a=p(Pr,2);Ce(_a,17,()=>r(Ue).items.filter(y=>y.kind==="removed"),Te,(y,ie)=>{var ye=kh(),Ee=p(i(ye),1,!0);S(()=>C(Ee,r(ie).text)),c(y,ye)}),S(()=>C(nr,`${r(Ue).to??""} vs ${r(Ue).from??""}`)),c(ht,Vt)};b(qt,ht=>{var Ue,Vt,lr;((lr=(Vt=(Ue=r(Kt))==null?void 0:Ue.digest)==null?void 0:Vt.items)==null?void 0:lr.length)>0&&ht(ur)})}var xt=p(qt,2);{var $t=ht=>{var Ue=Ch();c(ht,Ue)};b(xt,ht=>{r(Or)&&ht($t)})}var Ot=p(xt,2),ir=i(Ot);{var Qt=ht=>{var Ue=_e(),Vt=ae(Ue);Ce(Vt,17,()=>r(Ir),Te,(lr,nr)=>{var dr=_e(),Pr=ae(dr);{var _a=ye=>{var Ee=Sh(),Be=i(Ee);S(()=>C(Be,r(nr).text)),c(ye,Ee)},y=ye=>{var Ee=Th(),Be=p(i(Ee),1,!0);S(()=>C(Be,r(nr).text)),c(ye,Ee)},ie=ye=>{var Ee=Mh(),Be=p(i(Ee),1,!0);S(()=>C(Be,r(nr).text)),c(ye,Ee)};b(Pr,ye=>{r(nr).kind==="same"?ye(_a):r(nr).kind==="added"?ye(y,1):r(nr).kind==="removed"&&ye(ie,2)})}c(lr,dr)}),c(ht,Ue)},Tr=ht=>{var Ue=_e(),Vt=ae(Ue);Ma(Vt,()=>Ye(fe(r(Kt).body))),c(ht,Ue)};b(ir,ht=>{var Ue;r(er)?ht(Qt):(Ue=r(Kt))!=null&&Ue.body&&ht(Tr,1)})}S((ht,Ue)=>{Re(Yt,1,`pt-2 pb-6 border-b border-dl-border/8 last:border-b-0 ${r(Ne).status==="stale"?"border-l-2 border-l-amber-400/40 pl-3":""}`),Re(jt,1,`px-1.5 py-0.5 rounded text-[9px] font-medium border ${ht??""}`),C(Xt,Ue)},[()=>k(r(Ne).status),()=>F(r(Ne).status)]),ce("mouseup",Ot,Fe),c(Se,Yt)});var _r=p(Ft,2);{var xr=Se=>{var Ne=Ah();c(Se,Ne)};b(_r,Se=>{r(de).length>0&&Se(xr)})}var Gt=p(_r,2);Ce(Gt,19,()=>r(de),Se=>Se.block,(Se,Ne)=>{const Kt=L(()=>q(r(Ne))),pr=L(()=>r(Kt)&&r(x).get(r(Ne).block)),Ir=L(()=>r(pr)?ue(r(Ne)):null);var Wt=Ph(),er=i(Wt),Or=i(er);{var Yt=We=>{var Lt=Eh(),rt=i(Lt);{var De=Ge=>{ei(Ge,{size:12})},Ke=Ge=>{ss(Ge,{size:12})};b(rt,Ge=>{r(pr)?Ge(De):Ge(Ke,-1)})}S(()=>{Re(Lt,1,`p-1 rounded transition-colors ${r(pr)?"text-dl-accent-light bg-dl-accent/10":"text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5"}`),ua(Lt,"title",r(pr)?"표로 보기":"차트로 보기")}),ce("click",Lt,()=>ze(r(Ne).block)),c(We,Lt)};b(Or,We=>{r(Kt)&&We(Yt)})}var ct=p(Or,2);{var mt=We=>{var Lt=Ih(),rt=i(Lt);{var De=Ge=>{Xs(Ge,{size:12,class:"text-dl-success"})},Ke=Ge=>{nl(Ge,{size:12})};b(rt,Ge=>{r(m)===r(Ne).block?Ge(De):Ge(Ke,-1)})}ce("click",Lt,()=>Z(r(Ne),r(Ne).block)),c(We,Lt)};b(ct,We=>{var Lt,rt;((rt=(Lt=r(Ne).data)==null?void 0:Lt.rows)==null?void 0:rt.length)>0&&We(mt)})}var St=p(er,2);{var jt=We=>{var Lt=_e(),rt=ae(Lt);Us(rt,()=>ti(()=>import("./ChartRenderer-rbWm3w3k.js"),__vite__mapDeps([0,1])),null,(De,Ke)=>{var Ge=L(()=>{var{default:$t}=r(Ke);return{ChartRenderer:$t}}),qt=L(()=>r(Ge).ChartRenderer),ur=_e(),xt=ae(ur);vo(xt,()=>r(qt),($t,Ot)=>{Ot($t,{get spec(){return r(Ir)}})}),c(De,ur)}),c(We,Lt)},Xt=We=>{cl(We,{get block(){return r(Ne)}})};b(St,We=>{r(pr)&&r(Ir)?We(jt):We(Xt,-1)})}c(Se,Wt)}),c(Pe,He)},qe=Pe=>{var te=_e(),He=ae(te);Ce(He,19,()=>a().blocks,pt=>pt.block,(pt,je,ot)=>{var Ze=_e(),At=ae(Ze);{var Dt=Ft=>{const _r=L(()=>xe(r(ot))),xr=L(()=>Q(r(je))),Gt=L(()=>O(r(je))),Se=L(()=>{var Wt;return r(_r)||((Wt=r(xr))==null?void 0:Wt.period)}),Ne=L(()=>{var Wt;return r(Se)?we(r(je),r(Se)):(Wt=r(xr))==null?void 0:Wt.text});var Kt=_e(),pr=ae(Kt);{var Ir=Wt=>{var er=Dh(),Or=i(er);{var Yt=mt=>{var St=Lh(),jt=i(St);S(()=>C(jt,r(Ne))),c(mt,St)},ct=mt=>{var St=Rh(),jt=ae(St);{var Xt=Ke=>{var Ge=Oh(),qt=i(Ge);Hd(qt,{get periods(){return r(Gt)},get selected(){return r(Se)},onSelect:ur=>se(r(ot),ur)}),c(Ke,Ge)};b(jt,Ke=>{r(Gt).length>1&&Ke(Xt)})}var We=p(jt,2),Lt=i(We),rt=p(We,2),De=i(rt);Ma(De,()=>Ye(fe(r(Ne)))),S(()=>C(Lt,r(Se))),ce("mouseup",rt,Fe),c(mt,St)};b(Or,mt=>{r(je).textType==="heading"?mt(Yt):mt(ct,-1)})}c(Wt,er)};b(pr,Wt=>{r(Ne)&&Wt(Ir)})}c(Ft,Kt)},Jt=L(()=>ee(r(je))),fr=Ft=>{const _r=L(()=>q(r(je))),xr=L(()=>r(_r)&&r(x).get(r(je).block)),Gt=L(()=>r(xr)?ue(r(je)):null);var Se=qh(),Ne=i(Se),Kt=i(Ne);{var pr=ct=>{var mt=jh(),St=i(mt);{var jt=We=>{ei(We,{size:12})},Xt=We=>{ss(We,{size:12})};b(St,We=>{r(xr)?We(jt):We(Xt,-1)})}S(()=>{Re(mt,1,`p-1 rounded transition-colors ${r(xr)?"text-dl-accent-light bg-dl-accent/10":"text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5"}`),ua(mt,"title",r(xr)?"표로 보기":"차트로 보기")}),ce("click",mt,()=>ze(r(je).block)),c(ct,mt)};b(Kt,ct=>{r(_r)&&ct(pr)})}var Ir=p(Kt,2);{var Wt=ct=>{var mt=Vh(),St=i(mt);{var jt=We=>{Xs(We,{size:12,class:"text-dl-success"})},Xt=We=>{nl(We,{size:12})};b(St,We=>{r(m)===r(je).block?We(jt):We(Xt,-1)})}ce("click",mt,()=>Z(r(je),r(je).block)),c(ct,mt)};b(Ir,ct=>{var mt,St;((St=(mt=r(je).data)==null?void 0:mt.rows)==null?void 0:St.length)>0&&ct(Wt)})}var er=p(Ne,2);{var Or=ct=>{var mt=_e(),St=ae(mt);Us(St,()=>ti(()=>import("./ChartRenderer-rbWm3w3k.js"),__vite__mapDeps([0,1])),null,(jt,Xt)=>{var We=L(()=>{var{default:Ke}=r(Xt);return{ChartRenderer:Ke}}),Lt=L(()=>r(We).ChartRenderer),rt=_e(),De=ae(rt);vo(De,()=>r(Lt),(Ke,Ge)=>{Ge(Ke,{get spec(){return r(Gt)}})}),c(jt,rt)}),c(ct,mt)},Yt=ct=>{cl(ct,{get block(){return r(je)}})};b(er,ct=>{r(xr)&&r(Gt)?ct(Or):ct(Yt,-1)})}c(Ft,Se)},kt=L(()=>W(r(je)));b(At,Ft=>{r(Jt)?Ft(Dt):r(kt)&&Ft(fr,1)})}c(pt,Ze)}),c(Pe,te)};b(Qe,Pe=>{r(j)?Pe(wt):Pe(qe,-1)})}var ft=p(Qe,2);{var bt=Pe=>{var te=Bh();c(Pe,te)};b(ft,Pe=>{var te;((te=a().blocks)==null?void 0:te.length)===0&&!r(j)&&Pe(bt)})}S(()=>C(A,a().topicLabel||"")),c(w,U)};b(Tt,w=>{a()&&w(H)})}var le=p(Tt,2);{var ke=w=>{var U=Hh(),K=i(U),g=i(K);ls(g,{size:10}),S(()=>rs(U,`left: ${r(h).x??""}px; top: ${r(h).y??""}px; transform: translate(-50%, -100%)`)),ce("click",U,dt),c(w,U)};b(le,w=>{r(h).show&&w(ke)})}c(e,zt),Sr()}Hr(["click","mouseup"]);var Gh=f("<div> </div>"),Wh=f('<div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20"><!> <div class="text-[11px] text-red-400/90 space-y-0.5"></div></div>'),Yh=f("<div> </div>"),Jh=f('<div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-500/8 border border-amber-500/20"><!> <div class="text-[11px] text-amber-400/80 space-y-0.5"></div></div>'),Xh=f('<button><!> <span class="text-[10px] opacity-80"> </span> <span class="text-[14px] font-bold"> </span></button>'),Qh=f('<div class="flex items-start gap-1.5"><span class="w-1 h-1 rounded-full bg-dl-text-dim/40 mt-1.5 flex-shrink-0"></span> <span> </span></div>'),Zh=f('<div class="text-[11px] text-dl-text-muted space-y-0.5"></div>'),eg=f("<div><!> <span> </span></div>"),tg=f('<div class="text-[11px] space-y-0.5"></div>'),rg=f("<div><!> <span> </span></div>"),ag=f('<div class="text-[11px] space-y-0.5"></div>'),ng=f('<button class="text-[10px] px-1.5 py-0.5 rounded bg-dl-accent/8 text-dl-accent-light border border-dl-accent/20 hover:bg-dl-accent/15 transition-colors"> </button>'),og=f('<div class="flex flex-wrap gap-1 pt-1 border-t border-dl-border/10"><span class="text-[10px] text-dl-text-dim mr-1">원문 보기:</span> <!></div>'),sg=f('<div class="px-3 py-2 rounded-lg bg-dl-surface-card border border-dl-border/20 space-y-2 animate-fadeIn"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><span> </span> <span class="text-[12px] font-medium text-dl-text"> </span> <span class="text-[11px] text-dl-text-muted"> </span></div> <button class="p-0.5 text-dl-text-dim hover:text-dl-text"><!></button></div> <!> <!> <!> <!></div>'),ig=f('<div class="text-[10px] text-dl-text-dim px-1"> </div>'),lg=f('<div class="space-y-2"><!> <!> <div class="grid grid-cols-4 sm:grid-cols-7 gap-1.5"></div> <!> <!> <!></div>');function dg(e,t){Cr(t,!0);let a=Ie(t,"data",3,null),n=Ie(t,"loading",3,!1),o=Ie(t,"corpName",3,""),l=Ie(t,"onNavigateTopic",3,null),s=Ie(t,"toc",3,null),d=Y(null);const v={performance:{label:"실적",icon:Xo},profitability:{label:"수익성",icon:Bd},health:{label:"건전성",icon:Zf},cashflow:{label:"현금흐름",icon:np},governance:{label:"지배구조",icon:ap},risk:{label:"리스크",icon:Qo},opportunity:{label:"기회",icon:Xo}},m={performance:["salesOrder","businessOverview"],profitability:["IS","CIS","ratios"],health:["BS","contingentLiability","corporateBond"],cashflow:["CF","ratios"],governance:["majorShareholder","audit","dividend"],risk:["contingentLiability","riskFactors","corporateBond"],opportunity:["businessOverview","investmentOverview"]};function x(k){return k==="A"?"bg-emerald-500/15 text-emerald-400 border-emerald-500/30":k==="B"?"bg-blue-500/15 text-blue-400 border-blue-500/30":k==="C"?"bg-amber-500/15 text-amber-400 border-amber-500/30":k==="D"?"bg-orange-500/15 text-orange-400 border-orange-500/30":k==="F"?"bg-red-500/15 text-red-400 border-red-500/30":"bg-dl-border/10 text-dl-text-dim border-dl-border/20"}function h(k){return k==="A"?"bg-emerald-500 text-white":k==="B"?"bg-blue-500 text-white":k==="C"?"bg-amber-500 text-white":k==="D"?"bg-orange-500 text-white":k==="F"?"bg-red-500 text-white":"bg-dl-border text-dl-text-dim"}function _(k){return k==="danger"?"text-red-400":k==="warning"?"text-amber-400":"text-dl-text-dim"}function M(k){return k==="strong"?"text-emerald-400":"text-blue-400"}function $(k){u(d,r(d)===k?null:k,!0)}let V=L(()=>{var G;if(!((G=s())!=null&&G.chapters))return null;const k=new Set;for(const N of s().chapters)for(const re of N.topics)k.add(re.topic);return k}),T=L(()=>{var k;return(((k=a())==null?void 0:k.anomalies)??[]).filter(G=>G.severity==="danger")}),z=L(()=>{var k;return(((k=a())==null?void 0:k.anomalies)??[]).filter(G=>G.severity==="warning")}),I=L(()=>{var k;return(k=a())!=null&&k.areas?Object.keys(v).filter(G=>a().areas[G]):[]}),D=L(()=>{var G;if(!((G=a())!=null&&G.areas)||r(I).length<3)return null;const k={};for(const N of r(I))k[N]={grade:a().areas[N].grade};return m1(k,o())});var j=_e(),de=ae(j);{var pe=k=>{},F=k=>{var G=lg(),N=i(G);{var re=we=>{var Q=Wh(),O=i(Q);An(O,{size:14,class:"text-red-400 mt-0.5 flex-shrink-0"});var ee=p(O,2);Ce(ee,21,()=>r(T),Te,(W,q)=>{var ue=Gh(),ze=i(ue);S(()=>C(ze,r(q).text)),c(W,ue)}),c(we,Q)};b(N,we=>{r(T).length>0&&we(re)})}var P=p(N,2);{var me=we=>{var Q=Jh(),O=i(Q);Qo(O,{size:14,class:"text-amber-400 mt-0.5 flex-shrink-0"});var ee=p(O,2);Ce(ee,21,()=>r(z),Te,(W,q)=>{var ue=Yh(),ze=i(ue);S(()=>C(ze,r(q).text)),c(W,ue)}),c(we,Q)};b(P,we=>{r(z).length>0&&we(me)})}var E=p(P,2);Ce(E,21,()=>r(I),Te,(we,Q)=>{const O=L(()=>v[r(Q)]),ee=L(()=>a().areas[r(Q)]),W=L(()=>r(O).icon);var q=Xh(),ue=i(q);vo(ue,()=>r(W),(nt,Ye)=>{Ye(nt,{size:13,class:"opacity-70"})});var ze=p(ue,2),Z=i(ze),Fe=p(ze,2),dt=i(Fe);S(nt=>{Re(q,1,`flex flex-col items-center gap-1 px-2 py-2 rounded-lg border transition-colors cursor-pointer ${nt??""} ${r(d)===r(Q)?"ring-1 ring-dl-accent/40":"hover:brightness-110"}`),C(Z,r(O).label),C(dt,r(ee).grade)},[()=>x(r(ee).grade)]),ce("click",q,()=>$(r(Q))),c(we,q)});var B=p(E,2);{var oe=we=>{var Q=_e(),O=ae(Q);Us(O,()=>ti(()=>import("./ChartRenderer-rbWm3w3k.js"),__vite__mapDeps([0,1])),null,(ee,W)=>{var q=L(()=>{var{default:Fe}=r(W);return{ChartRenderer:Fe}}),ue=L(()=>r(q).ChartRenderer),ze=_e(),Z=ae(ze);vo(Z,()=>r(ue),(Fe,dt)=>{dt(Fe,{get spec(){return r(D)},class:"max-w-xs mx-auto"})}),c(ee,ze)}),c(we,Q)};b(B,we=>{r(D)&&we(oe)})}var fe=p(B,2);{var he=we=>{const Q=L(()=>a().areas[r(d)]),O=L(()=>v[r(d)]),ee=L(()=>(m[r(d)]||[]).filter(R=>!r(V)||r(V).has(R)));var W=sg(),q=i(W),ue=i(q),ze=i(ue),Z=i(ze),Fe=p(ze,2),dt=i(Fe),nt=p(Fe,2),Ye=i(nt),zt=p(ue,2),Tt=i(zt);qf(Tt,{size:14});var H=p(q,2);{var le=R=>{var J=Zh();Ce(J,21,()=>r(Q).details,Te,(ne,Ae)=>{var Me=Qh(),gt=p(i(Me),2),Je=i(gt);S(()=>C(Je,r(Ae))),c(ne,Me)}),c(R,J)};b(H,R=>{var J;((J=r(Q).details)==null?void 0:J.length)>0&&R(le)})}var ke=p(H,2);{var w=R=>{var J=tg();Ce(J,21,()=>r(Q).risks,Te,(ne,Ae)=>{var Me=eg(),gt=i(Me);Qo(gt,{size:10,class:"mt-0.5 flex-shrink-0"});var Je=p(gt,2),Xe=i(Je);S(ut=>{Re(Me,1,`flex items-start gap-1.5 ${ut??""}`),C(Xe,r(Ae).text)},[()=>_(r(Ae).level)]),c(ne,Me)}),c(R,J)};b(ke,R=>{var J;((J=r(Q).risks)==null?void 0:J.length)>0&&R(w)})}var U=p(ke,2);{var K=R=>{var J=ag();Ce(J,21,()=>r(Q).opportunities,Te,(ne,Ae)=>{var Me=rg(),gt=i(Me);Xo(gt,{size:10,class:"mt-0.5 flex-shrink-0"});var Je=p(gt,2),Xe=i(Je);S(ut=>{Re(Me,1,`flex items-start gap-1.5 ${ut??""}`),C(Xe,r(Ae).text)},[()=>M(r(Ae).level)]),c(ne,Me)}),c(R,J)};b(U,R=>{var J;((J=r(Q).opportunities)==null?void 0:J.length)>0&&R(K)})}var g=p(U,2);{var A=R=>{var J=og(),ne=p(i(J),2);Ce(ne,17,()=>r(ee),Te,(Ae,Me)=>{var gt=ng(),Je=i(gt);S(()=>C(Je,r(Me))),ce("click",gt,()=>l()(r(Me))),c(Ae,gt)}),c(R,J)};b(g,R=>{l()&&r(ee).length>0&&R(A)})}S(R=>{Re(ze,1,`px-1.5 py-0.5 rounded text-[10px] font-bold ${R??""}`),C(Z,r(Q).grade),C(dt,r(O).label),C(Ye,`— ${r(Q).summary??""}`)},[()=>h(r(Q).grade)]),ce("click",zt,()=>{u(d,null)}),c(we,W)};b(fe,we=>{r(d)&&a().areas[r(d)]&&we(he)})}var xe=p(fe,2);{var se=we=>{var Q=ig(),O=i(Q);S(()=>C(O,a().profile)),c(we,Q)};b(xe,we=>{a().profile&&we(se)})}c(k,G)};b(de,k=>{n()?k(pe):a()&&k(F,1)})}c(e,j),Sr()}Hr(["click"]);var cg=f('<div class="flex items-center justify-between text-[12px]"><span class="text-dl-text-muted"> </span> <kbd class="px-1.5 py-0.5 rounded bg-dl-bg-darker border border-dl-border/30 text-[11px] font-mono text-dl-text-dim min-w-[32px] text-center"> </kbd></div>'),ug=f('<div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"><div class="bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl w-80 max-w-[90vw] overflow-hidden"><div class="flex items-center justify-between px-4 py-3 border-b border-dl-border/20"><div class="flex items-center gap-2 text-dl-text"><!> <span class="text-[13px] font-semibold">단축키</span></div> <button class="p-1 rounded text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="px-4 py-3 space-y-1.5"></div></div></div>');function vg(e,t){let a=Ie(t,"show",3,!1),n=Ie(t,"onClose",3,null);const o=[{key:"?",desc:"단축키 도움말"},{key:"1",desc:"Chat 탭"},{key:"2",desc:"Viewer 탭"},{key:"Ctrl+K",desc:"종목 검색"},{key:"Ctrl+F",desc:"뷰어 내 검색"},{key:"J / ↓",desc:"다음 topic"},{key:"K / ↑",desc:"이전 topic"},{key:"S",desc:"현재 topic AI 요약"},{key:"B",desc:"북마크 토글"},{key:"Esc",desc:"모달/검색 닫기"}];var l=_e(),s=ae(l);{var d=v=>{var m=ug(),x=i(m),h=i(x),_=i(h),M=i(_);Gf(M,{size:16});var $=p(_,2),V=i($);wn(V,{size:14});var T=p(h,2);Ce(T,21,()=>o,Te,(z,I)=>{var D=cg(),j=i(D),de=i(j),pe=p(j,2),F=i(pe);S(()=>{C(de,r(I).desc),C(F,r(I).key)}),c(z,D)}),ce("click",m,function(...z){var I;(I=n())==null||I.apply(this,z)}),ce("click",x,z=>z.stopPropagation()),ce("click",$,function(...z){var I;(I=n())==null||I.apply(this,z)}),c(v,m)};b(s,v=>{a()&&v(d)})}c(e,l)}Hr(["click"]);var fg=f('<div class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"></div>'),pg=f('<button class="p-1 rounded-md text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"><!></button>'),mg=f('<div class="flex items-center justify-between"><div class="min-w-0"><div class="text-[12px] font-semibold text-dl-text truncate"> </div> <div class="text-[10px] font-mono text-dl-text-dim"> </div></div> <div class="flex items-center gap-0.5 flex-shrink-0"><!></div></div>'),xg=f('<div class="text-[12px] text-dl-text-dim">종목 미선택</div>'),hg=f('<div class="sticky top-0 z-20 px-6 py-2 bg-dl-bg-dark/95 backdrop-blur-sm border-b border-dl-border/10"><div class="max-w-2xl mx-auto"><button class="flex items-center gap-2 w-full px-3 py-1.5 rounded-lg border border-dl-border/20 bg-dl-bg-darker/60 text-[12px] text-dl-text-dim hover:border-dl-border/40 hover:bg-dl-bg-darker transition-colors"><!> <span class="flex-1 text-left">공시 섹션 검색... <kbd class="ml-2 px-1 py-0.5 rounded bg-dl-border/15 text-[10px] font-mono">/</kbd></span></button></div></div>'),gg=f('<button class="p-1 text-dl-text-dim hover:text-dl-text"><!></button>'),bg=f('<div class="text-[10px] text-dl-text-dim/60 mt-0.5"> </div>'),_g=f('<div class="text-[11px] text-dl-text-dim truncate mt-0.5"> </div>'),wg=f('<span class="text-[10px] text-dl-accent font-mono flex-shrink-0"> </span>'),yg=f('<button class="w-full text-left px-4 py-2 text-[13px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-start gap-2 border-b border-dl-border/5"><div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/50 font-mono"> </span></div> <!> <!></div> <!></button>'),kg=f('<div class="flex items-center justify-center py-3"><!></div>'),$g=f("<!> <!>",1),Cg=f('<div class="flex items-center justify-center py-6 gap-2"><!> <span class="text-[12px] text-dl-text-dim">검색 중...</span></div>'),Sg=f('<div class="text-center py-6 text-[12px] text-dl-text-dim">결과 없음</div>'),Tg=f('<button class="w-full text-left px-4 py-2 text-[13px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-2"><!> <span> </span> <span class="text-[10px] text-dl-text-dim/40 font-mono ml-auto"> </span></button>'),Mg=f('<div class="px-4 py-2 text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold">최근 본 섹션</div> <!>',1),zg=f('<div class="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/50 backdrop-blur-sm"><div class="w-full max-w-xl bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl overflow-hidden"><div class="flex items-center gap-2 px-4 py-3 border-b border-dl-border/20"><!> <input placeholder="섹션, topic, 키워드 검색..." class="flex-1 bg-transparent text-[14px] text-dl-text outline-none placeholder:text-dl-text-dim"/> <!> <kbd class="px-1.5 py-0.5 rounded bg-dl-border/15 text-[10px] font-mono text-dl-text-dim">Esc</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div></div></div>'),Ag=f('<span class="text-[11px] text-dl-text-muted truncate"> </span>'),Eg=f('<div class="sticky top-0 z-30 flex items-center gap-2 px-3 py-1.5 bg-dl-bg-dark/95 border-b border-dl-border/20 backdrop-blur-sm"><button class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"><!> <span>목차</span></button> <button class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"><!> <span>검색</span></button> <!></div>'),Ig=f('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[14px] text-dl-text-muted mb-1">공시 뷰어</div> <div class="text-[12px] text-dl-text-dim">종목을 검색하여 공시 문서를 살펴보세요</div></div>'),Pg=f('<div class="flex flex-col items-center justify-center h-full"><!> <div class="text-[12px] text-dl-text-dim">공시 데이터 로딩 중...</div></div>'),Ng=f('<div class="flex flex-col items-center justify-center h-full"><!> <div class="text-[11px] text-dl-text-dim">섹션 로딩 중...</div></div>'),Lg=f('<div class="max-w-4xl mx-auto px-6 py-4 animate-fadeIn"><!> <div class="mt-4"><!></div></div>'),Og=f('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[13px] text-dl-text-dim">좌측 목차에서 항목을 선택하세요</div></div>'),Rg=f('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[13px] text-dl-text-dim">이 종목의 공시 데이터가 없습니다</div></div>'),Dg=f('<div class="flex h-full min-h-0 bg-dl-bg-dark relative"><!> <div><div class="h-full flex flex-col"><div class="px-3 py-2 border-b border-dl-border/20 flex-shrink-0"><!></div> <!></div></div> <div class="flex-1 min-w-0 overflow-y-auto"><!> <!> <!> <!></div></div> <!>',1);function jg(e,t){Cr(t,!0);let a=Ie(t,"viewer",3,null),n=Ie(t,"company",3,null),o=Ie(t,"onAskAI",3,null),l=Ie(t,"onTopicChange",3,null),s=Y(!1),d=Y(!1),v=Y(!1);function m(){u(d,typeof window<"u"&&window.innerWidth<=768,!0)}$r(()=>(m(),window.addEventListener("resize",m),()=>window.removeEventListener("resize",m)));let x=Y(!1),h=Y(""),_=Y(null);function M(){u(x,!r(x)),r(x)?requestAnimationFrame(()=>{var H;return(H=r(_))==null?void 0:H.focus()}):(u(h,""),u(D,null))}$r(()=>{var H;(H=n())!=null&&H.stockCode&&a()&&a().loadCompany(n().stockCode)}),$r(()=>{var H,le,ke;(H=a())!=null&&H.selectedTopic&&((le=a())!=null&&le.topicData)&&((ke=l())==null||ke(a().selectedTopic,a().topicData.topicLabel||a().selectedTopic),I(a().selectedTopic,a().topicData.topicLabel||a().selectedTopic))});let $=Y(Ut([]));const V=8;function T(){var H;try{const le=localStorage.getItem("dartlab-viewer-history");return(le?JSON.parse(le):{})[(H=n())==null?void 0:H.stockCode]||[]}catch{return[]}}function z(H){var le;try{const ke=localStorage.getItem("dartlab-viewer-history"),w=ke?JSON.parse(ke):{};w[(le=n())==null?void 0:le.stockCode]=H,localStorage.setItem("dartlab-viewer-history",JSON.stringify(w))}catch{}}function I(H,le){var w;if(!((w=n())!=null&&w.stockCode))return;const ke=r($).filter(U=>U.topic!==H);u($,[{topic:H,label:le,time:Date.now()},...ke].slice(0,V),!0),z(r($))}$r(()=>{var H;(H=n())!=null&&H.stockCode&&u($,T(),!0)});let D=Y(null),j=Y(!1),de=null;function pe(){var le,ke;if(!((ke=(le=a())==null?void 0:le.toc)!=null&&ke.chapters))return[];const H=[];for(const w of a().toc.chapters)for(const U of w.topics)H.push({topic:U.topic,chapter:w.chapter});return H}function F(H){var le,ke;if((ke=(le=a())==null?void 0:le.toc)!=null&&ke.chapters){for(const w of a().toc.chapters)if(w.topics.find(K=>K.topic===H)){a().selectTopic(H,w.chapter);return}}}function k(H){var le,ke,w,U;if((ke=(le=a())==null?void 0:le.toc)!=null&&ke.chapters){for(const K of a().toc.chapters)if(K.topics.find(A=>A.topic===H)){const A=r(h).trim();a().selectTopic(H,K.chapter),A&&((U=(w=a()).setSearchHighlight)==null||U.call(w,A)),u(x,!1),u(h,""),u(D,null);return}}}function G(H){var w,U,K,g;const le=(w=H.target)==null?void 0:w.tagName,ke=le==="INPUT"||le==="TEXTAREA"||((U=H.target)==null?void 0:U.isContentEditable);if(H.key==="f"&&(H.ctrlKey||H.metaKey)&&n()){H.preventDefault(),M();return}if(H.key==="Escape"){if(r(v)){u(v,!1);return}if(r(x)){u(x,!1),u(h,""),u(D,null);return}return}if(!ke){if(H.key==="?"){u(v,!r(v));return}if(H.key==="/"&&n()){H.preventDefault(),M();return}if(!r(x)&&(H.key==="ArrowUp"||H.key==="ArrowDown"||H.key==="j"||H.key==="k")&&((K=a())!=null&&K.selectedTopic)){const A=pe(),R=A.findIndex(Ae=>Ae.topic===a().selectedTopic);if(R<0)return;const ne=H.key==="ArrowDown"||H.key==="j"?R+1:R-1;ne>=0&&ne<A.length&&(H.preventDefault(),a().selectTopic(A[ne].topic,A[ne].chapter));return}if(H.key==="b"&&((g=a())!=null&&g.selectedTopic)){a().toggleBookmark(a().selectedTopic);return}}}$r(()=>{var ke,w,U;const H=r(h).trim();if(!H||!((ke=n())!=null&&ke.stockCode)){u(D,null);return}const le=[];if((U=(w=a())==null?void 0:w.toc)!=null&&U.chapters){const K=H.toLowerCase();for(const g of a().toc.chapters)for(const A of g.topics)(A.label.toLowerCase().includes(K)||A.topic.toLowerCase().includes(K))&&le.push({topic:A.topic,label:A.label,chapter:g.chapter,snippet:"",matchCount:0,source:"toc"})}u(D,le.length>0?le:null,!0),clearTimeout(de),H.length>=2&&(u(j,!0),de=setTimeout(async()=>{try{const K=await Tv(n().stockCode,H);if(r(h).trim()!==H)return;const g=(K.results||[]).map(J=>({...J,source:"text"})),A=new Set(le.map(J=>J.topic)),R=[...le,...g.filter(J=>!A.has(J.topic))];u(D,R.length>0?R:null,!0)}catch{}u(j,!1)},300))});var N=Dg();xn("keydown",ts,G);var re=ae(N),P=i(re);{var me=H=>{var le=fg();ce("click",le,()=>{u(s,!1)}),c(H,le)};b(P,H=>{r(d)&&r(s)&&H(me)})}var E=p(P,2),B=i(E),oe=i(B),fe=i(oe);{var he=H=>{var le=mg(),ke=i(le),w=i(ke),U=i(w),K=p(w,2),g=i(K),A=p(ke,2),R=i(A);{var J=ne=>{var Ae=pg(),Me=i(Ae);wn(Me,{size:12}),ce("click",Ae,()=>{u(s,!1)}),c(ne,Ae)};b(R,ne=>{r(d)&&ne(J)})}S(()=>{C(U,n().corpName||n().company),C(g,n().stockCode)}),c(H,le)},xe=H=>{var le=xg();c(H,le)};b(fe,H=>{n()?H(he):H(xe,-1)})}var se=p(oe,2);{let H=L(()=>{var K;return(K=a())==null?void 0:K.toc}),le=L(()=>{var K;return(K=a())==null?void 0:K.tocLoading}),ke=L(()=>{var K;return(K=a())==null?void 0:K.selectedTopic}),w=L(()=>{var K;return(K=a())==null?void 0:K.expandedChapters}),U=L(()=>{var K,g;return((g=(K=a())==null?void 0:K.getBookmarks)==null?void 0:g.call(K))??[]});c1(se,{get toc(){return r(H)},get loading(){return r(le)},get selectedTopic(){return r(ke)},get expandedChapters(){return r(w)},get bookmarks(){return r(U)},get recentHistory(){return r($)},onSelectTopic:(K,g)=>{var A;(A=a())==null||A.selectTopic(K,g),r(d)&&u(s,!1)},onToggleChapter:K=>{var g;return(g=a())==null?void 0:g.toggleChapter(K)}})}var we=p(E,2),Q=i(we);{var O=H=>{var le=hg(),ke=i(le),w=i(ke),U=i(w);gn(U,{size:13,class:"flex-shrink-0"}),ce("click",w,M),c(H,le)};b(Q,H=>{n()&&!r(d)&&H(O)})}var ee=p(Q,2);{var W=H=>{var le=zg(),ke=i(le),w=i(ke),U=i(w);gn(U,{size:16,class:"text-dl-text-dim flex-shrink-0"});var K=p(U,2);hn(K,Xe=>u(_,Xe),()=>r(_));var g=p(K,2);{var A=Xe=>{var ut=gg(),ar=i(ut);wn(ar,{size:14}),ce("click",ut,()=>{u(h,"")}),c(Xe,ut)};b(g,Xe=>{r(h)&&Xe(A)})}var R=p(w,2),J=i(R);{var ne=Xe=>{var ut=$g(),ar=ae(ut);Ce(ar,17,()=>r(D).slice(0,15),Te,(wt,qe)=>{var ft=yg(),bt=i(ft),Pe=i(bt),te=i(Pe),He=i(te),pt=p(te,2),je=i(pt),ot=p(Pe,2);{var Ze=kt=>{var Ft=bg(),_r=i(Ft);S(()=>C(_r,r(qe).chapter)),c(kt,Ft)};b(ot,kt=>{r(qe).chapter&&kt(Ze)})}var At=p(ot,2);{var Dt=kt=>{var Ft=_g(),_r=i(Ft);S(()=>C(_r,r(qe).snippet)),c(kt,Ft)};b(At,kt=>{r(qe).snippet&&kt(Dt)})}var Jt=p(bt,2);{var fr=kt=>{var Ft=wg(),_r=i(Ft);S(()=>C(_r,`${r(qe).matchCount??""}건`)),c(kt,Ft)};b(Jt,kt=>{r(qe).matchCount>0&&kt(fr)})}S(()=>{C(He,r(qe).label),C(je,r(qe).topic)}),ce("click",ft,()=>k(r(qe).topic)),c(wt,ft)});var lt=p(ar,2);{var Qe=wt=>{var qe=kg(),ft=i(qe);Nr(ft,{size:14,class:"animate-spin text-dl-text-dim"}),c(wt,qe)};b(lt,wt=>{r(j)&&wt(Qe)})}c(Xe,ut)},Ae=Xe=>{var ut=Cg(),ar=i(ut);Nr(ar,{size:14,class:"animate-spin text-dl-text-dim"}),c(Xe,ut)},Me=Xe=>{var ut=Sg();c(Xe,ut)},gt=L(()=>r(h).trim()),Je=Xe=>{var ut=_e(),ar=ae(ut);{var lt=Qe=>{var wt=Mg(),qe=p(ae(wt),2);Ce(qe,17,()=>r($),Te,(ft,bt)=>{var Pe=Tg(),te=i(Pe);is(te,{size:12,class:"text-dl-text-dim/40 flex-shrink-0"});var He=p(te,2),pt=i(He),je=p(He,2),ot=i(je);S(()=>{C(pt,r(bt).label),C(ot,r(bt).topic)}),ce("click",Pe,()=>k(r(bt).topic)),c(ft,Pe)}),c(Qe,wt)};b(ar,Qe=>{r($).length>0&&Qe(lt)})}c(Xe,ut)};b(J,Xe=>{r(D)?Xe(ne):r(j)?Xe(Ae,1):r(gt)?Xe(Me,2):Xe(Je,-1)})}ce("click",le,()=>{u(x,!1),u(h,""),u(D,null)}),ce("click",ke,Xe=>Xe.stopPropagation()),Ln(K,()=>r(h),Xe=>u(h,Xe)),c(H,le)};b(ee,H=>{r(x)&&H(W)})}var q=p(ee,2);{var ue=H=>{var le=Eg(),ke=i(le),w=i(ke);ca(w,{size:11});var U=p(ke,2),K=i(U);gn(K,{size:11});var g=p(U,2);{var A=R=>{var J=Ag(),ne=i(J);S(()=>{var Ae,Me,gt;return C(ne,((Me=(Ae=a())==null?void 0:Ae.topicData)==null?void 0:Me.topicLabel)||((gt=a())==null?void 0:gt.selectedTopic))}),c(R,J)};b(g,R=>{var J;(J=a())!=null&&J.selectedTopic&&R(A)})}ce("click",ke,()=>{u(s,!0)}),ce("click",U,M),c(H,le)};b(q,H=>{r(d)&&n()&&H(ue)})}var ze=p(q,2);{var Z=H=>{var le=Ig(),ke=i(le);ca(ke,{size:32,class:"text-dl-text-dim/30 mb-3"}),c(H,le)},Fe=H=>{var le=Pg(),ke=i(le);Nr(ke,{size:24,class:"animate-spin text-dl-text-dim/40 mb-3"}),c(H,le)},dt=H=>{var le=Ng(),ke=i(le);Nr(ke,{size:20,class:"animate-spin text-dl-text-dim/40 mb-2"}),c(H,le)},nt=H=>{var le=Lg(),ke=i(le);dg(ke,{get data(){return a().insightData},get loading(){return a().insightLoading},get toc(){return a().toc},onNavigateTopic:F});var w=p(ke,2),U=i(w);Kh(U,{get topicData(){return a().topicData},get diffSummary(){return a().diffSummary},get viewer(){return a()},get onAskAI(){return o()},get searchHighlight(){return a().searchHighlight}}),c(H,le)},Ye=H=>{var le=Og(),ke=i(le);ca(ke,{size:28,class:"text-dl-text-dim/30 mb-3"}),c(H,le)},zt=H=>{var le=Rg(),ke=i(le);An(ke,{size:28,class:"text-dl-text-dim/30 mb-3"}),c(H,le)};b(ze,H=>{var le,ke,w,U,K,g,A,R;n()?(le=a())!=null&&le.tocLoading?H(Fe,1):(ke=a())!=null&&ke.topicLoading?H(dt,2):(w=a())!=null&&w.topicData?H(nt,3):(U=a())!=null&&U.toc&&!((K=a())!=null&&K.selectedTopic)?H(Ye,4):((R=(A=(g=a())==null?void 0:g.toc)==null?void 0:A.chapters)==null?void 0:R.length)===0&&H(zt,5):H(Z)})}var Tt=p(re,2);vg(Tt,{get show(){return r(v)},onClose:()=>{u(v,!1)}}),S(()=>Re(E,1,`${r(d)?`fixed top-0 left-0 bottom-0 z-50 w-64 transition-transform duration-200 ${r(s)?"translate-x-0":"-translate-x-full"}`:"flex-shrink-0 w-56"} border-r border-dl-border/30 overflow-hidden bg-dl-bg-dark`)),c(e,N),Sr()}Hr(["click"]);var Vg=f('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),qg=f("<!> <span>확인 중...</span>",1),Bg=f("<!> <span>설정 필요</span>",1),Fg=f('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),Hg=f('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!>',1),Ug=f('<div class="min-w-0 flex-1 pt-10"><!></div>'),Kg=f('<div class="flex-shrink-0 border-l border-dl-border/30 transition-all duration-300"><!></div>'),Gg=f('<div class="min-w-0 flex-1 flex flex-col"><!></div> <!>',1),Wg=f('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),Yg=f('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),Jg=f('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),Xg=f('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),Qg=f('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),Zg=f('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),eb=f('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),tb=f('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),rb=f('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),ab=f('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),nb=f('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),ob=f('<div class="text-[10px] text-dl-text-dim mt-2"> </div>'),sb=f('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex login</div></div></div></div> <!> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),ib=f('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2"> </div></div>'),lb=f('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 계정 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),db=f('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),cb=f("<button> <!></button>"),ub=f('<div class="flex flex-wrap gap-1.5"></div>'),vb=f('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),fb=f('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),pb=f('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),mb=f('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),xb=f('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),hb=f('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),gb=f('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),bb=f("<!> <!> <!> <!> <!> <!>",1),_b=f('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),wb=f('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),yb=f('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),kb=f('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><span class="text-[10px] text-dl-text-dim">공시 보기</span> <!></div></button>'),$b=f('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div></div> <!>',1),Cb=f('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div></button>'),Sb=f('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div></div> <!>',1),Tb=f('<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),Mb=f('<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim"><!> <div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div> <div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div></div>'),zb=f('<div class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn" role="presentation"><div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"><div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"/> <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div> <div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim"><span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span></div></div></div>'),Ab=f('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),Eb=f('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-2 left-3 z-20 pointer-events-auto flex items-center gap-1"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center ml-2 rounded-lg bg-dl-bg-card/60 border border-dl-border/20 p-0.5"><button><!> <span>Chat</span></button> <button><!> <span>Viewer</span></button></div></div> <div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="종목 검색 (Ctrl+K)"><!></button> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <button><!> <!></button></div> <div class="flex flex-1 min-h-0"><!></div></div></div>  <!> <!> <!> <!>',1);function Ib(e,t){Cr(t,!0);let a=Y(""),n=Y(!1),o=Y(null),l=Y(Ut({})),s=Y(Ut({})),d=Y(null),v=Y(null),m=Y(Ut([])),x=Y(!1),h=Y(0),_=Y(!0),M=Y(""),$=Y(!1),V=Y(null),T=Y(Ut({})),z=Y(Ut({})),I=Y(""),D=Y(!1),j=Y(null),de=Y(""),pe=Y(!1),F=Y(""),k=Y(0),G=Y(null),N=Y(null),re=Y(null);const P=Mf(),me=Ef();let E=Y(!1),B=L(()=>r(E)?"100%":P.panelMode==="viewer"?"65%":"50%"),oe=Y(!1),fe=Y(""),he=Y(Ut([])),xe=Y(-1),se=null,we=Y(null),Q=Y(!1);function O(){u(Q,window.innerWidth<=768),r(Q)&&(u(x,!1),P.closePanel())}$r(()=>(O(),window.addEventListener("resize",O),()=>window.removeEventListener("resize",O))),$r(()=>{!r($)||!r(N)||requestAnimationFrame(()=>{var y;return(y=r(N))==null?void 0:y.focus()})}),$r(()=>{!r(ee)||!r(re)||requestAnimationFrame(()=>{var y;return(y=r(re))==null?void 0:y.focus()})}),$r(()=>{!r(oe)||!r(we)||requestAnimationFrame(()=>{var y;return(y=r(we))==null?void 0:y.focus()})});let ee=Y(null),W=Y(""),q=Y("error"),ue=Y(!1);function ze(y,ie="error",ye=4e3){u(W,y,!0),u(q,ie,!0),u(ue,!0),setTimeout(()=>{u(ue,!1)},ye)}const Z=$f();$r(()=>{H()});let Fe=Y(Ut({}));function dt(y){return y==="chatgpt"?"codex":y}function nt(y){return`dartlab-api-key:${dt(y)}`}function Ye(y){return typeof sessionStorage>"u"||!y?"":sessionStorage.getItem(nt(y))||""}function zt(y,ie){typeof sessionStorage>"u"||!y||(ie?sessionStorage.setItem(nt(y),ie):sessionStorage.removeItem(nt(y)))}async function Tt(y,ie=null,ye=null){var Be;const Ee=await xv(y,ie,ye);if(Ee!=null&&Ee.provider){const yt=dt(Ee.provider);u(l,{...r(l),[yt]:{...r(l)[yt]||{},available:!!Ee.available,model:Ee.model||((Be=r(l)[yt])==null?void 0:Be.model)||ie||null}},!0)}return Ee}async function H(){var y,ie,ye;u(_,!0);try{const Ee=await mv();u(l,Ee.providers||{},!0),u(s,Ee.ollama||{},!0),u(Fe,Ee.codex||{},!0),Ee.version&&u(M,Ee.version,!0);const Be=dt(localStorage.getItem("dartlab-provider")),yt=localStorage.getItem("dartlab-model"),$e=Ye(Be);if(Be&&((y=r(l)[Be])!=null&&y.available)){u(d,Be,!0),u(V,Be,!0),u(I,$e,!0),await le(Be);const be=r(T)[Be]||[];yt&&be.includes(yt)?u(v,yt,!0):be.length>0&&(u(v,be[0],!0),localStorage.setItem("dartlab-model",r(v))),u(m,be,!0),u(_,!1);return}if(Be&&r(l)[Be]){if(u(d,Be,!0),u(V,Be,!0),u(I,$e,!0),$e)try{await Tt(Be,yt,$e)}catch{}await le(Be);const be=r(T)[Be]||[];u(m,be,!0),yt&&be.includes(yt)?u(v,yt,!0):be.length>0&&u(v,be[0],!0),u(_,!1);return}for(const be of["codex","ollama","openai"])if((ie=r(l)[be])!=null&&ie.available){u(d,be,!0),u(V,be,!0),u(I,Ye(be),!0),await le(be);const Ve=r(T)[be]||[];u(m,Ve,!0),u(v,((ye=r(l)[be])==null?void 0:ye.model)||(Ve.length>0?Ve[0]:null),!0),r(v)&&localStorage.setItem("dartlab-model",r(v));break}}catch{}u(_,!1)}async function le(y){y=dt(y),u(z,{...r(z),[y]:!0},!0);try{const ie=await hv(y);u(T,{...r(T),[y]:ie.models||[]},!0)}catch{u(T,{...r(T),[y]:[]},!0)}u(z,{...r(z),[y]:!1},!0)}async function ke(y){var ye;y=dt(y),u(d,y,!0),u(v,null),u(V,y,!0),localStorage.setItem("dartlab-provider",y),localStorage.removeItem("dartlab-model"),u(I,Ye(y),!0),u(j,null),await le(y);const ie=r(T)[y]||[];if(u(m,ie,!0),ie.length>0&&(u(v,((ye=r(l)[y])==null?void 0:ye.model)||ie[0],!0),localStorage.setItem("dartlab-model",r(v)),r(I)))try{await Tt(y,r(v),r(I))}catch{}}async function w(y){u(v,y,!0),localStorage.setItem("dartlab-model",y);const ie=Ye(r(d));if(ie)try{await Tt(dt(r(d)),y,ie)}catch{}}function U(y){y=dt(y),r(V)===y?u(V,null):(u(V,y,!0),le(y))}async function K(){const y=r(I).trim();if(!(!y||!r(d))){u(D,!0),u(j,null);try{const ie=await Tt(dt(r(d)),r(v),y);ie.available?(zt(r(d),y),u(j,"success"),!r(v)&&ie.model&&u(v,ie.model,!0),await le(r(d)),u(m,r(T)[r(d)]||[],!0),ze("API 키 인증 성공","success")):(zt(r(d),""),u(j,"error"))}catch{zt(r(d),""),u(j,"error")}u(D,!1)}}async function g(){try{await bv(),r(d)==="codex"&&u(l,{...r(l),codex:{...r(l).codex,available:!1}},!0),ze("Codex 계정 로그아웃 완료","success"),await H()}catch{ze("로그아웃 실패")}}function A(){const y=r(de).trim();!y||r(pe)||(u(pe,!0),u(F,"준비 중..."),u(k,0),u(G,gv(y,{onProgress(ie){ie.total&&ie.completed!==void 0?(u(k,Math.round(ie.completed/ie.total*100),!0),u(F,`다운로드 중... ${r(k)}%`)):ie.status&&u(F,ie.status,!0)},async onDone(){u(pe,!1),u(G,null),u(de,""),u(F,""),u(k,0),ze(`${y} 다운로드 완료`,"success"),await le("ollama"),u(m,r(T).ollama||[],!0),r(m).includes(y)&&await w(y)},onError(ie){u(pe,!1),u(G,null),u(F,""),u(k,0),ze(`다운로드 실패: ${ie}`)}}),!0))}function R(){r(G)&&(r(G).abort(),u(G,null)),u(pe,!1),u(de,""),u(F,""),u(k,0)}function J(){u(x,!r(x))}function ne(y){P.openData(y)}function Ae(y,ie=null){P.openEvidence(y,ie)}function Me(y){P.openViewer(y)}function gt(){if(u(I,""),u(j,null),r(d))u(V,r(d),!0);else{const y=Object.keys(r(l));u(V,y.length>0?y[0]:null,!0)}u($,!0),r(V)&&le(r(V))}function Je(y){var ie,ye,Ee,Be;if(y)for(let yt=y.messages.length-1;yt>=0;yt--){const $e=y.messages[yt];if($e.role==="assistant"&&((ie=$e.meta)!=null&&ie.stockCode||(ye=$e.meta)!=null&&ye.company||$e.company)){P.syncCompanyFromMessage({company:((Ee=$e.meta)==null?void 0:Ee.company)||$e.company,stockCode:(Be=$e.meta)==null?void 0:Be.stockCode},P.selectedCompany);return}}}function Xe(){Z.createConversation(),u(a,""),u(n,!1),r(o)&&(r(o).abort(),u(o,null))}function ut(y){Z.setActive(y),Je(Z.active),u(a,""),u(n,!1),r(o)&&(r(o).abort(),u(o,null))}function ar(y){u(ee,y,!0)}function lt(){r(ee)&&(Z.deleteConversation(r(ee)),u(ee,null))}function Qe(){var ie;const y=Z.active;if(!y)return null;for(let ye=y.messages.length-1;ye>=0;ye--){const Ee=y.messages[ye];if(Ee.role==="assistant"&&((ie=Ee.meta)!=null&&ie.stockCode))return Ee.meta.stockCode}return null}async function wt(y=null){var mr,yr,gr;const ie=(y??r(a)).trim();if(!ie||r(n))return;if(!r(d)||!((mr=r(l)[r(d)])!=null&&mr.available)){ze("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),gt();return}Z.activeId||Z.createConversation();const ye=Z.activeId;Z.addMessage("user",ie),u(a,""),u(n,!0),Z.addMessage("assistant",""),Z.updateLastMessage({loading:!0,startedAt:Date.now()}),Mo(h);const Ee=Z.active,Be=[];let yt=null;if(Ee){const ve=Ee.messages.slice(0,-2);for(const ge of ve)if((ge.role==="user"||ge.role==="assistant")&&ge.text&&ge.text.trim()&&!ge.error&&!ge.loading){const vt={role:ge.role,text:ge.text};ge.role==="assistant"&&((yr=ge.meta)!=null&&yr.stockCode)&&(vt.meta={company:ge.meta.company||ge.company,stockCode:ge.meta.stockCode,modules:ge.meta.includedModules||null,market:ge.meta.market||null,topic:ge.meta.topic||null,topicLabel:ge.meta.topicLabel||null,dialogueMode:ge.meta.dialogueMode||null,questionTypes:ge.meta.questionTypes||null,userGoal:ge.meta.userGoal||null},yt=ge.meta.stockCode),Be.push(vt)}}const $e=((gr=P.selectedCompany)==null?void 0:gr.stockCode)||yt||Qe(),be=P.getViewContext();function Ve(){return Z.activeId!==ye}const Et={provider:r(d),model:r(v),viewContext:be},or=Ye(r(d));or&&(Et.api_key=or);const hr=Av($e,ie,Et,{onMeta(ve){var tr;if(Ve())return;const ge=Z.active,vt=ge==null?void 0:ge.messages[ge.messages.length-1],_t={meta:{...(vt==null?void 0:vt.meta)||{},...ve}};ve.company&&(_t.company=ve.company,Z.activeId&&((tr=Z.active)==null?void 0:tr.title)==="새 대화"&&Z.updateTitle(Z.activeId,ve.company)),ve.stockCode&&(_t.stockCode=ve.stockCode),(ve.company||ve.stockCode)&&P.syncCompanyFromMessage(ve,P.selectedCompany),Z.updateLastMessage(_t)},onSnapshot(ve){Ve()||Z.updateLastMessage({snapshot:ve})},onContext(ve){if(Ve())return;const ge=Z.active;if(!ge)return;const vt=ge.messages[ge.messages.length-1],et=(vt==null?void 0:vt.contexts)||[];Z.updateLastMessage({contexts:[...et,{module:ve.module,label:ve.label,text:ve.text}]})},onSystemPrompt(ve){Ve()||Z.updateLastMessage({systemPrompt:ve.text,userContent:ve.userContent||null})},onToolCall(ve){if(Ve())return;const ge=Z.active;if(!ge)return;const vt=ge.messages[ge.messages.length-1],et=(vt==null?void 0:vt.toolEvents)||[];Z.updateLastMessage({toolEvents:[...et,{type:"call",name:ve.name,arguments:ve.arguments}]})},onToolResult(ve){if(Ve())return;const ge=Z.active;if(!ge)return;const vt=ge.messages[ge.messages.length-1],et=(vt==null?void 0:vt.toolEvents)||[];Z.updateLastMessage({toolEvents:[...et,{type:"result",name:ve.name,result:ve.result}]})},onChunk(ve){if(Ve())return;const ge=Z.active;if(!ge)return;const vt=ge.messages[ge.messages.length-1];Z.updateLastMessage({text:((vt==null?void 0:vt.text)||"")+ve}),Mo(h)},onDone(){if(Ve())return;const ve=Z.active,ge=ve==null?void 0:ve.messages[ve.messages.length-1],vt=ge!=null&&ge.startedAt?((Date.now()-ge.startedAt)/1e3).toFixed(1):null;Z.updateLastMessage({loading:!1,duration:vt}),Z.flush(),u(n,!1),u(o,null),Mo(h)},onViewerNavigate(ve){Ve()||te(ve)},onError(ve,ge,vt){Ve()||(Z.updateLastMessage({text:`오류: ${ve}`,loading:!1,error:!0}),Z.flush(),ge==="login"?(ze(`${ve} — 설정에서 Codex 로그인을 확인하세요`),gt()):ge==="install"?(ze(`${ve} — 설정에서 Codex 설치 안내를 확인하세요`),gt()):ze(ve),u(n,!1),u(o,null))}},Be);u(o,hr,!0)}function qe(){r(o)&&(r(o).abort(),u(o,null),u(n,!1),Z.updateLastMessage({loading:!1}),Z.flush())}function ft(){const y=Z.active;if(!y||y.messages.length<2)return;let ie="";for(let ye=y.messages.length-1;ye>=0;ye--)if(y.messages[ye].role==="user"){ie=y.messages[ye].text;break}ie&&(Z.removeLastMessage(),Z.removeLastMessage(),u(a,ie,!0),requestAnimationFrame(()=>{wt()}))}function bt(){const y=Z.active;if(!y)return;let ie=`# ${y.title}

`;for(const yt of y.messages)yt.role==="user"?ie+=`## You

${yt.text}

`:yt.role==="assistant"&&yt.text&&(ie+=`## DartLab

${yt.text}

`);const ye=new Blob([ie],{type:"text/markdown;charset=utf-8"}),Ee=URL.createObjectURL(ye),Be=document.createElement("a");Be.href=Ee,Be.download=`${y.title||"dartlab-chat"}.md`,Be.click(),URL.revokeObjectURL(Ee),ze("대화가 마크다운으로 내보내졌습니다","success")}function Pe(y){var Ee;P.switchView("chat");const ie=((Ee=me.topicData)==null?void 0:Ee.topicLabel)||"",ye=ie?`[${ie}] `:"";u(a,`${ye}"${y}" — 이 내용에 대해 설명해줘`),requestAnimationFrame(()=>{const Be=document.querySelector(".input-textarea");Be&&Be.focus()})}function te(y){y!=null&&y.topic&&(P.switchView("viewer"),y.chapter&&me.selectTopic(y.topic,y.chapter))}function He(){u(oe,!0),u(fe,""),u(he,[],!0),u(xe,-1)}function pt(y){var Ee,Be;(y.metaKey||y.ctrlKey)&&y.key==="n"&&(y.preventDefault(),Xe()),(y.metaKey||y.ctrlKey)&&y.key==="k"&&(y.preventDefault(),He()),(y.metaKey||y.ctrlKey)&&y.shiftKey&&y.key==="S"&&(y.preventDefault(),J()),y.key==="Escape"&&r(oe)?u(oe,!1):y.key==="Escape"&&r($)?u($,!1):y.key==="Escape"&&r(ee)?u(ee,null):y.key==="Escape"&&P.panelOpen&&P.closePanel();const ie=(Ee=y.target)==null?void 0:Ee.tagName;if(!(ie==="INPUT"||ie==="TEXTAREA"||((Be=y.target)==null?void 0:Be.isContentEditable))&&!y.ctrlKey&&!y.metaKey&&!y.altKey){if(y.key==="1"){P.switchView("chat");return}if(y.key==="2"){P.switchView("viewer");return}}}let je=L(()=>{var y;return((y=Z.active)==null?void 0:y.messages)||[]}),ot=L(()=>Z.active&&Z.active.messages.length>0),Ze=L(()=>{var y;return!r(_)&&(!r(d)||!((y=r(l)[r(d)])!=null&&y.available))});const At=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var Dt=Eb();xn("keydown",ts,pt);var Jt=ae(Dt),fr=i(Jt);{var kt=y=>{var ie=Vg();ce("click",ie,()=>{u(x,!1)}),c(y,ie)};b(fr,y=>{r(Q)&&r(x)&&y(kt)})}var Ft=p(fr,2),_r=i(Ft);{let y=L(()=>r(Q)?!0:r(x));pp(_r,{get conversations(){return Z.conversations},get activeId(){return Z.activeId},get open(){return r(y)},get version(){return r(M)},onNewChat:()=>{Xe(),r(Q)&&u(x,!1)},onSelect:ie=>{ut(ie),r(Q)&&u(x,!1)},onDelete:ar,onOpenSearch:He})}var xr=p(Ft,2),Gt=i(xr),Se=i(Gt),Ne=i(Se);{var Kt=y=>{Jf(y,{size:18})},pr=y=>{Yf(y,{size:18})};b(Ne,y=>{r(x)?y(Kt):y(pr,-1)})}var Ir=p(Se,2),Wt=i(Ir),er=i(Wt);ls(er,{size:12});var Or=p(Wt,2),Yt=i(Or);Js(Yt,{size:12});var ct=p(Gt,2),mt=i(ct),St=i(mt);gn(St,{size:14});var jt=p(mt,2),Xt=i(jt);ca(Xt,{size:14});var We=p(jt,2),Lt=i(We);Kf(Lt,{size:14});var rt=p(We,2),De=i(rt);Ff(De,{size:14});var Ke=p(rt,2),Ge=i(Ke);{var qt=y=>{var ie=qg(),ye=ae(ie);Nr(ye,{size:12,class:"animate-spin"}),c(y,ie)},ur=y=>{var ie=Bg(),ye=ae(ie);An(ye,{size:12}),c(y,ie)},xt=y=>{var ie=Hg(),ye=p(ae(ie),2),Ee=i(ye),Be=p(ye,2);{var yt=$e=>{var be=Fg(),Ve=p(ae(be),2),Et=i(Ve);S(()=>C(Et,r(v))),c($e,be)};b(Be,$e=>{r(v)&&$e(yt)})}S(()=>C(Ee,r(d))),c(y,ie)};b(Ge,y=>{r(_)?y(qt):r(Ze)?y(ur,1):y(xt,-1)})}var $t=p(Ge,2);Qf($t,{size:12});var Ot=p(ct,2),ir=i(Ot);{var Qt=y=>{var ie=Ug(),ye=i(ie);jg(ye,{get viewer(){return me},get company(){return P.selectedCompany},onAskAI:Pe,onTopicChange:(Ee,Be)=>P.setViewerTopic(Ee,Be)}),c(y,ie)},Tr=y=>{var ie=Gg(),ye=ae(ie),Ee=i(ye);{var Be=Ve=>{{let Et=L(()=>P.viewerTopic?{topic:P.viewerTopic,topicLabel:P.viewerTopicLabel,period:P.viewerPeriod}:null);ym(Ve,{get messages(){return r(je)},get isLoading(){return r(n)},get scrollTrigger(){return r(h)},get selectedCompany(){return P.selectedCompany},get viewerContext(){return r(Et)},onSend:wt,onStop:qe,onRegenerate:ft,onExport:bt,onOpenData:ne,onOpenEvidence:Ae,onCompanySelect:Me,get inputText(){return r(a)},set inputText(or){u(a,or,!0)}})}},yt=Ve=>{kp(Ve,{onSend:wt,onCompanySelect:Me,get inputText(){return r(a)},set inputText(Et){u(a,Et,!0)}})};b(Ee,Ve=>{r(ot)?Ve(Be):Ve(yt,-1)})}var $e=p(ye,2);{var be=Ve=>{var Et=Kg(),or=i(Et);Jx(or,{get mode(){return P.panelMode},get company(){return P.selectedCompany},get data(){return P.panelData},onClose:()=>{u(E,!1),P.closePanel()},onTopicChange:(hr,mr)=>P.setViewerTopic(hr,mr),onFullscreen:()=>{u(E,!r(E))},get isFullscreen(){return r(E)}}),S(()=>rs(Et,`width: ${r(B)??""}; min-width: 360px; ${r(E)?"":"max-width: 75vw;"}`)),c(Ve,Et)};b($e,Ve=>{!r(Q)&&P.panelOpen&&Ve(be)})}c(y,ie)};b(ir,y=>{P.activeView==="viewer"?y(Qt):y(Tr,-1)})}var ht=p(Jt,2);{var Ue=y=>{var ie=wb(),ye=i(ie),Ee=i(ye),Be=i(Ee),yt=p(i(Be),2),$e=i(yt);wn($e,{size:18});var be=p(Ee,2),Ve=i(be);Ce(Ve,21,()=>Object.entries(r(l)),Te,(ve,ge)=>{var vt=L(()=>si(r(ge),2));let et=()=>r(vt)[0],_t=()=>r(vt)[1];const tr=L(()=>et()===r(d)),Bt=L(()=>r(V)===et()),Zt=L(()=>_t().auth==="api_key"),Kr=L(()=>_t().auth==="cli"),Ua=L(()=>r(T)[et()]||[]),en=L(()=>r(z)[et()]);var Cn=_b(),Sn=i(Cn),Wn=i(Sn),Yn=p(Wn,2),Jn=i(Yn),qo=i(Jn),hs=i(qo),Ud=p(qo,2);{var Kd=br=>{var Wr=Wg();c(br,Wr)};b(Ud,br=>{r(tr)&&br(Kd)})}var Gd=p(Jn,2),Wd=i(Gd),Yd=p(Yn,2),Jd=i(Yd);{var Xd=br=>{Eo(br,{size:16,class:"text-dl-success"})},Qd=br=>{var Wr=Yg(),tn=ae(Wr);sl(tn,{size:14,class:"text-amber-400"}),c(br,Wr)},Zd=br=>{var Wr=Jg(),tn=ae(Wr);An(tn,{size:14,class:"text-amber-400"}),c(br,Wr)},ec=br=>{var Wr=Xg(),tn=ae(Wr);tp(tn,{size:14,class:"text-dl-text-dim"}),c(br,Wr)};b(Jd,br=>{_t().available?br(Xd):r(Zt)?br(Qd,1):r(Kr)&&et()==="codex"&&r(Fe).installed?br(Zd,2):r(Kr)&&!_t().available&&br(ec,3)})}var tc=p(Sn,2);{var rc=br=>{var Wr=bb(),tn=ae(Wr);{var ac=sr=>{var kr=Zg(),Rr=i(kr),Yr=i(Rr),va=p(Rr,2),Gr=i(va),aa=p(Gr,2),rn=i(aa);{var an=Ht=>{Nr(Ht,{size:12,class:"animate-spin"})},na=Ht=>{sl(Ht,{size:12})};b(rn,Ht=>{r(D)?Ht(an):Ht(na,-1)})}var wa=p(va,2);{var vr=Ht=>{var oa=Qg(),Dr=i(oa);An(Dr,{size:12}),c(Ht,oa)};b(wa,Ht=>{r(j)==="error"&&Ht(vr)})}S(Ht=>{C(Yr,_t().envKey?`환경변수 ${_t().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),ua(Gr,"placeholder",et()==="openai"?"sk-...":et()==="claude"?"sk-ant-...":"API Key"),aa.disabled=Ht},[()=>!r(I).trim()||r(D)]),ce("keydown",Gr,Ht=>{Ht.key==="Enter"&&K()}),Ln(Gr,()=>r(I),Ht=>u(I,Ht)),ce("click",aa,K),c(sr,kr)};b(tn,sr=>{r(Zt)&&!_t().available&&sr(ac)})}var _i=p(tn,2);{var nc=sr=>{var kr=tb(),Rr=i(kr),Yr=i(Rr);Eo(Yr,{size:13,class:"text-dl-success"});var va=p(Rr,2),Gr=i(va),aa=p(Gr,2);{var rn=na=>{var wa=eb(),vr=i(wa);{var Ht=Dr=>{Nr(Dr,{size:10,class:"animate-spin"})},oa=Dr=>{var Pa=Ja("변경");c(Dr,Pa)};b(vr,Dr=>{r(D)?Dr(Ht):Dr(oa,-1)})}S(()=>wa.disabled=r(D)),ce("click",wa,K),c(na,wa)},an=L(()=>r(I).trim());b(aa,na=>{r(an)&&na(rn)})}ce("keydown",Gr,na=>{na.key==="Enter"&&K()}),Ln(Gr,()=>r(I),na=>u(I,na)),c(sr,kr)};b(_i,sr=>{r(Zt)&&_t().available&&sr(nc)})}var wi=p(_i,2);{var oc=sr=>{var kr=rb(),Rr=p(i(kr),2),Yr=i(Rr);Io(Yr,{size:14});var va=p(Yr,2);ol(va,{size:10,class:"ml-auto"}),c(sr,kr)},sc=sr=>{var kr=ab(),Rr=i(kr),Yr=i(Rr);An(Yr,{size:14}),c(sr,kr)};b(wi,sr=>{et()==="ollama"&&!r(s).installed?sr(oc):et()==="ollama"&&r(s).installed&&!r(s).running&&sr(sc,1)})}var yi=p(wi,2);{var ic=sr=>{var kr=ib(),Rr=i(kr);{var Yr=aa=>{var rn=sb(),an=ae(rn),na=i(an),wa=p(an,2),vr=i(wa);{var Ht=sa=>{var Na=nb();c(sa,Na)};b(vr,sa=>{r(Fe).installed||sa(Ht)})}var oa=p(vr,2),Dr=i(oa),Pa=i(Dr),Tn=p(wa,2);{var ho=sa=>{var Na=ob(),nn=i(Na);S(()=>C(nn,r(Fe).loginStatus)),c(sa,Na)};b(Tn,sa=>{r(Fe).loginStatus&&sa(ho)})}var go=p(Tn,2),Xr=i(go);An(Xr,{size:12,class:"text-amber-400 flex-shrink-0"}),S(()=>{C(na,r(Fe).installed?"Codex CLI가 설치되었지만 로그인이 필요합니다":"Codex CLI 설치가 필요합니다"),C(Pa,r(Fe).installed?"1.":"2.")}),c(aa,rn)};b(Rr,aa=>{et()==="codex"&&aa(Yr)})}var va=p(Rr,2),Gr=i(va);S(()=>C(Gr,r(Fe).installed?"로그인 완료 후 새로고침하세요":"설치 완료 후 새로고침하세요")),c(sr,kr)};b(yi,sr=>{r(Kr)&&!_t().available&&sr(ic)})}var ki=p(yi,2);{var lc=sr=>{var kr=lb(),Rr=i(kr),Yr=i(Rr),va=i(Yr);Eo(va,{size:13,class:"text-dl-success"});var Gr=p(Yr,2),aa=i(Gr);Wf(aa,{size:11}),ce("click",Gr,g),c(sr,kr)};b(ki,sr=>{et()==="codex"&&_t().available&&sr(lc)})}var dc=p(ki,2);{var cc=sr=>{var kr=gb(),Rr=i(kr),Yr=p(i(Rr),2);{var va=vr=>{Nr(vr,{size:12,class:"animate-spin text-dl-text-dim"})};b(Yr,vr=>{r(en)&&vr(va)})}var Gr=p(Rr,2);{var aa=vr=>{var Ht=db(),oa=i(Ht);Nr(oa,{size:14,class:"animate-spin"}),c(vr,Ht)},rn=vr=>{var Ht=ub();Ce(Ht,21,()=>r(Ua),Te,(oa,Dr)=>{var Pa=cb(),Tn=i(Pa),ho=p(Tn);{var go=Xr=>{Xs(Xr,{size:10,class:"inline ml-1"})};b(ho,Xr=>{r(Dr)===r(v)&&r(tr)&&Xr(go)})}S(Xr=>{Re(Pa,1,Xr),C(Tn,`${r(Dr)??""} `)},[()=>rr(cr("px-3 py-1.5 rounded-lg text-[11px] border transition-all",r(Dr)===r(v)&&r(tr)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),ce("click",Pa,()=>{et()!==r(d)&&ke(et()),w(r(Dr))}),c(oa,Pa)}),c(vr,Ht)},an=vr=>{var Ht=vb();c(vr,Ht)};b(Gr,vr=>{r(en)&&r(Ua).length===0?vr(aa):r(Ua).length>0?vr(rn,1):vr(an,-1)})}var na=p(Gr,2);{var wa=vr=>{var Ht=hb(),oa=i(Ht),Dr=p(i(oa),2),Pa=p(i(Dr));ol(Pa,{size:9});var Tn=p(oa,2);{var ho=Xr=>{var sa=fb(),Na=i(sa),nn=i(Na),bo=i(nn);Nr(bo,{size:12,class:"animate-spin text-dl-primary-light"});var gs=p(nn,2),Bo=p(Na,2),Ka=i(Bo),ya=p(Bo,2),bs=i(ya);S(()=>{rs(Ka,`width: ${r(k)??""}%`),C(bs,r(F))}),ce("click",gs,R),c(Xr,sa)},go=Xr=>{var sa=xb(),Na=ae(sa),nn=i(Na),bo=p(nn,2),gs=i(bo);Io(gs,{size:12});var Bo=p(Na,2);Ce(Bo,21,()=>At,Te,(Ka,ya)=>{const bs=L(()=>r(Ua).some(Xn=>Xn===r(ya).name||Xn===r(ya).name.split(":")[0]));var $i=_e(),uc=ae($i);{var vc=Xn=>{var _s=mb(),Ci=i(_s),Si=i(Ci),Ti=i(Si),fc=i(Ti),Mi=p(Ti,2),pc=i(Mi),mc=p(Mi,2);{var xc=ws=>{var Ai=pb(),yc=i(Ai);S(()=>C(yc,r(ya).tag)),c(ws,Ai)};b(mc,ws=>{r(ya).tag&&ws(xc)})}var hc=p(Si,2),gc=i(hc),bc=p(Ci,2),zi=i(bc),_c=i(zi),wc=p(zi,2);Io(wc,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),S(()=>{C(fc,r(ya).name),C(pc,r(ya).size),C(gc,r(ya).desc),C(_c,`${r(ya).gb??""} GB`)}),ce("click",_s,()=>{u(de,r(ya).name,!0),A()}),c(Xn,_s)};b(uc,Xn=>{r(bs)||Xn(vc)})}c(Ka,$i)}),S(Ka=>bo.disabled=Ka,[()=>!r(de).trim()]),ce("keydown",nn,Ka=>{Ka.key==="Enter"&&A()}),Ln(nn,()=>r(de),Ka=>u(de,Ka)),ce("click",bo,A),c(Xr,sa)};b(Tn,Xr=>{r(pe)?Xr(ho):Xr(go,-1)})}c(vr,Ht)};b(na,vr=>{et()==="ollama"&&vr(wa)})}c(sr,kr)};b(dc,sr=>{(_t().available||r(Zt)||r(Kr))&&sr(cc)})}c(br,Wr)};b(tc,br=>{(r(Bt)||r(tr))&&br(rc)})}S((br,Wr)=>{Re(Cn,1,br),Re(Wn,1,Wr),C(hs,_t().label||et()),C(Wd,_t().desc||"")},[()=>rr(cr("rounded-xl border transition-all",r(tr)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>rr(cr("w-2.5 h-2.5 rounded-full flex-shrink-0",_t().available?"bg-dl-success":r(Zt)?"bg-amber-400":"bg-dl-text-dim"))]),ce("click",Sn,()=>{_t().available||r(Zt)?et()===r(d)?U(et()):ke(et()):U(et())}),c(ve,Cn)});var Et=p(be,2),or=i(Et),hr=i(or);{var mr=ve=>{var ge=Ja();S(()=>{var vt;return C(ge,`현재: ${(((vt=r(l)[r(d)])==null?void 0:vt.label)||r(d))??""} / ${r(v)??""}`)}),c(ve,ge)},yr=ve=>{var ge=Ja();S(()=>{var vt;return C(ge,`현재: ${(((vt=r(l)[r(d)])==null?void 0:vt.label)||r(d))??""}`)}),c(ve,ge)};b(hr,ve=>{r(d)&&r(v)?ve(mr):r(d)&&ve(yr,1)})}var gr=p(or,2);hn(ye,ve=>u(N,ve),()=>r(N)),ce("click",ie,ve=>{ve.target===ve.currentTarget&&u($,!1)}),ce("click",yt,()=>u($,!1)),ce("click",gr,()=>u($,!1)),c(y,ie)};b(ht,y=>{r($)&&y(Ue)})}var Vt=p(ht,2);{var lr=y=>{var ie=yb(),ye=i(ie),Ee=p(i(ye),4),Be=i(Ee),yt=p(Be,2);hn(ye,$e=>u(re,$e),()=>r(re)),ce("click",ie,$e=>{$e.target===$e.currentTarget&&u(ee,null)}),ce("click",Be,()=>u(ee,null)),ce("click",yt,lt),c(y,ie)};b(Vt,y=>{r(ee)&&y(lr)})}var nr=p(Vt,2);{var dr=y=>{const ie=L(()=>P.recentCompanies||[]);var ye=zb(),Ee=i(ye),Be=i(Ee),yt=i(Be);gn(yt,{size:18,class:"text-dl-text-dim flex-shrink-0"});var $e=p(yt,2);hn($e,ve=>u(we,ve),()=>r(we));var be=p(Be,2),Ve=i(be);{var Et=ve=>{var ge=$b(),vt=p(ae(ge),2);Ce(vt,17,()=>r(he),Te,(et,_t,tr)=>{var Bt=kb(),Zt=i(Bt),Kr=i(Zt),Ua=p(Zt,2),en=i(Ua),Cn=i(en),Sn=p(en,2),Wn=i(Sn),Yn=p(Ua,2),Jn=p(i(Yn),2);ca(Jn,{size:14,class:"text-dl-text-dim"}),S((qo,hs)=>{Re(Bt,1,qo),C(Kr,hs),C(Cn,r(_t).corpName),C(Wn,`${r(_t).stockCode??""} · ${(r(_t).market||"")??""}${r(_t).sector?` · ${r(_t).sector}`:""}`)},[()=>rr(cr("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",tr===r(xe)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(r(_t).corpName||"?").charAt(0)]),ce("click",Bt,()=>{u(oe,!1),u(fe,""),u(he,[],!0),u(xe,-1),Me(r(_t))}),xn("mouseenter",Bt,()=>{u(xe,tr,!0)}),c(et,Bt)}),c(ve,ge)},or=ve=>{var ge=Sb(),vt=p(ae(ge),2);Ce(vt,17,()=>r(ie),Te,(et,_t,tr)=>{var Bt=Cb(),Zt=i(Bt),Kr=i(Zt),Ua=p(Zt,2),en=i(Ua),Cn=i(en),Sn=p(en,2),Wn=i(Sn);S((Yn,Jn)=>{Re(Bt,1,Yn),C(Kr,Jn),C(Cn,r(_t).corpName),C(Wn,`${r(_t).stockCode??""} · ${(r(_t).market||"")??""}`)},[()=>rr(cr("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",tr===r(xe)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(r(_t).corpName||"?").charAt(0)]),ce("click",Bt,()=>{u(oe,!1),u(fe,""),u(xe,-1),Me(r(_t))}),xn("mouseenter",Bt,()=>{u(xe,tr,!0)}),c(et,Bt)}),c(ve,ge)},hr=L(()=>r(fe).trim().length===0&&r(ie).length>0),mr=ve=>{var ge=Tb();c(ve,ge)},yr=L(()=>r(fe).trim().length>0),gr=ve=>{var ge=Mb(),vt=i(ge);gn(vt,{size:24,class:"mb-2 opacity-40"}),c(ve,ge)};b(Ve,ve=>{r(he).length>0?ve(Et):r(hr)?ve(or,1):r(yr)?ve(mr,2):ve(gr,-1)})}ce("click",ye,ve=>{ve.target===ve.currentTarget&&u(oe,!1)}),ce("input",$e,()=>{se&&clearTimeout(se),r(fe).trim().length>=1?se=setTimeout(async()=>{var ve;try{const ge=await bd(r(fe).trim());u(he,((ve=ge.results)==null?void 0:ve.slice(0,8))||[],!0)}catch{u(he,[],!0)}},250):u(he,[],!0)}),ce("keydown",$e,ve=>{const ge=r(he).length>0?r(he):r(ie);if(ve.key==="ArrowDown")ve.preventDefault(),u(xe,Math.min(r(xe)+1,ge.length-1),!0);else if(ve.key==="ArrowUp")ve.preventDefault(),u(xe,Math.max(r(xe)-1,-1),!0);else if(ve.key==="Enter"&&r(xe)>=0&&ge[r(xe)]){ve.preventDefault();const vt=ge[r(xe)];u(oe,!1),u(fe,""),u(he,[],!0),u(xe,-1),Me(vt)}else ve.key==="Escape"&&u(oe,!1)}),Ln($e,()=>r(fe),ve=>u(fe,ve)),c(y,ye)};b(nr,y=>{r(oe)&&y(dr)})}var Pr=p(nr,2);{var _a=y=>{var ie=Ab(),ye=i(ie),Ee=i(ye),Be=i(Ee),yt=p(Ee,2),$e=i(yt);wn($e,{size:14}),S(be=>{Re(ye,1,be),C(Be,r(W))},[()=>rr(cr("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",r(q)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":r(q)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),ce("click",yt,()=>{u(ue,!1)}),c(y,ie)};b(Pr,y=>{r(ue)&&y(_a)})}S(y=>{Re(Ft,1,rr(r(Q)?r(x)?"sidebar-mobile":"hidden":"")),Re(Wt,1,`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors ${P.activeView==="chat"?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-dim hover:text-dl-text-muted"}`),Re(Or,1,`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors ${P.activeView==="viewer"?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-dim hover:text-dl-text-muted"}`),Re(Ke,1,y)},[()=>rr(cr("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",r(_)?"text-dl-text-dim":r(Ze)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),ce("click",Se,J),ce("click",Wt,()=>P.switchView("chat")),ce("click",Or,()=>P.switchView("viewer")),ce("click",mt,He),ce("click",Ke,()=>gt()),c(e,Dt),Sr()}Hr(["click","keydown","input"]);Ku(Ib,{target:document.getElementById("app")});export{ri as C,ti as _,Ie as a,c as b,_e as c,Sr as d,f as e,ae as f,i as g,Us as h,b as i,vo as j,r as k,C as l,p as m,ua as n,Ce as o,Cr as p,Te as q,Uu as r,Re as s,S as t,L as u,rs as v};
