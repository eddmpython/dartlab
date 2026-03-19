var vc=Object.defineProperty;var Ci=e=>{throw TypeError(e)};var fc=(e,t,a)=>t in e?vc(e,t,{enumerable:!0,configurable:!0,writable:!0,value:a}):e[t]=a;var ba=(e,t,a)=>fc(e,typeof t!="symbol"?t+"":t,a),bs=(e,t,a)=>t.has(e)||Ci("Cannot "+a);var W=(e,t,a)=>(bs(e,t,"read from private field"),a?a.call(e):t.get(e)),Ot=(e,t,a)=>t.has(e)?Ci("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,a),Tt=(e,t,a,n)=>(bs(e,t,"write to private field"),n?n.call(e,a):t.set(e,a),a),wr=(e,t,a)=>(bs(e,t,"access private method"),a);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const o of document.querySelectorAll('link[rel="modulepreload"]'))n(o);new MutationObserver(o=>{for(const l of o)if(l.type==="childList")for(const s of l.addedNodes)s.tagName==="LINK"&&s.rel==="modulepreload"&&n(s)}).observe(document,{childList:!0,subtree:!0});function a(o){const l={};return o.integrity&&(l.integrity=o.integrity),o.referrerPolicy&&(l.referrerPolicy=o.referrerPolicy),o.crossOrigin==="use-credentials"?l.credentials="include":o.crossOrigin==="anonymous"?l.credentials="omit":l.credentials="same-origin",l}function n(o){if(o.ep)return;o.ep=!0;const l=a(o);fetch(o.href,l)}})();const Ts=!1;var Xs=Array.isArray,pc=Array.prototype.indexOf,no=Array.prototype.includes,is=Array.from,mc=Object.defineProperty,dn=Object.getOwnPropertyDescriptor,ol=Object.getOwnPropertyDescriptors,xc=Object.prototype,hc=Array.prototype,Qs=Object.getPrototypeOf,Si=Object.isExtensible;function ho(e){return typeof e=="function"}const gc=()=>{};function bc(e){return e()}function Ms(e){for(var t=0;t<e.length;t++)e[t]()}function sl(){var e,t,a=new Promise((n,o)=>{e=n,t=o});return{promise:a,resolve:e,reject:t}}function Zs(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const a=[];for(const n of e)if(a.push(n),a.length===t)break;return a}const jr=2,co=4,Vn=8,ls=1<<24,_n=16,Ta=32,Hn=64,zs=128,fa=512,Or=1024,Rr=2048,Sa=4096,Gr=8192,Da=16384,uo=32768,Wa=65536,Ti=1<<17,_c=1<<18,vo=1<<19,il=1<<20,Oa=1<<25,qn=65536,As=1<<21,ei=1<<22,cn=1<<23,ja=Symbol("$state"),ll=Symbol("legacy props"),yc=Symbol(""),zn=new class extends Error{constructor(){super(...arguments);ba(this,"name","StaleReactionError");ba(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var rl;const dl=!!((rl=globalThis.document)!=null&&rl.contentType)&&globalThis.document.contentType.includes("xml");function wc(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function kc(e,t,a){throw new Error("https://svelte.dev/e/each_key_duplicate")}function $c(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function Cc(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Sc(e){throw new Error("https://svelte.dev/e/effect_orphan")}function Tc(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function Mc(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function zc(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function Ac(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function Ec(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function Ic(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const Nc=1,Pc=2,cl=4,Lc=8,Oc=16,Rc=1,Dc=2,ul=4,jc=8,Vc=16,qc=1,Bc=2,Mr=Symbol(),vl="http://www.w3.org/1999/xhtml",fl="http://www.w3.org/2000/svg",Fc="http://www.w3.org/1998/Math/MathML",Hc="@attach";function Uc(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function Kc(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function pl(e){return e===this.v}function Gc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function ml(e){return!Gc(e,this.v)}let Po=!1,Wc=!1;function Yc(){Po=!0}let Ar=null;function oo(e){Ar=e}function br(e,t=!1,a){Ar={p:Ar,i:!1,c:null,e:null,s:e,x:null,l:Po&&!t?{s:null,u:null,$:[]}:null}}function _r(e){var t=Ar,a=t.e;if(a!==null){t.e=null;for(var n of a)Ol(n)}return t.i=!0,Ar=t.p,{}}function Lo(){return!Po||Ar!==null&&Ar.l===null}let An=[];function xl(){var e=An;An=[],Ms(e)}function Va(e){if(An.length===0&&!Co){var t=An;queueMicrotask(()=>{t===An&&xl()})}An.push(e)}function Jc(){for(;An.length>0;)xl()}function hl(e){var t=Nt;if(t===null)return It.f|=cn,e;if((t.f&uo)===0&&(t.f&co)===0)throw e;ln(e,t)}function ln(e,t){for(;t!==null;){if((t.f&zs)!==0){if((t.f&uo)===0)throw e;try{t.b.error(e);return}catch(a){e=a}}t=t.parent}throw e}const Xc=-7169;function xr(e,t){e.f=e.f&Xc|t}function ti(e){(e.f&fa)!==0||e.deps===null?xr(e,Or):xr(e,Sa)}function gl(e){if(e!==null)for(const t of e)(t.f&jr)===0||(t.f&qn)===0||(t.f^=qn,gl(t.deps))}function bl(e,t,a){(e.f&Rr)!==0?t.add(e):(e.f&Sa)!==0&&a.add(e),gl(e.deps),xr(e,Or)}const qo=new Set;let wt=null,Xo=null,Lr=null,Xr=[],ds=null,Co=!1,so=null,Qc=1;var nn,Jn,Pn,Xn,Qn,Zn,on,Ia,eo,ea,Es,Is,Ns,Ps;const fi=class fi{constructor(){Ot(this,ea);ba(this,"id",Qc++);ba(this,"current",new Map);ba(this,"previous",new Map);Ot(this,nn,new Set);Ot(this,Jn,new Set);Ot(this,Pn,0);Ot(this,Xn,0);Ot(this,Qn,null);Ot(this,Zn,new Set);Ot(this,on,new Set);Ot(this,Ia,new Map);ba(this,"is_fork",!1);Ot(this,eo,!1)}skip_effect(t){W(this,Ia).has(t)||W(this,Ia).set(t,{d:[],m:[]})}unskip_effect(t){var a=W(this,Ia).get(t);if(a){W(this,Ia).delete(t);for(var n of a.d)xr(n,Rr),Ra(n);for(n of a.m)xr(n,Sa),Ra(n)}}process(t){var o;Xr=[],this.apply();var a=so=[],n=[];for(const l of t)wr(this,ea,Is).call(this,l,a,n);if(so=null,wr(this,ea,Es).call(this)){wr(this,ea,Ns).call(this,n),wr(this,ea,Ns).call(this,a);for(const[l,s]of W(this,Ia))kl(l,s)}else{Xo=this,wt=null;for(const l of W(this,nn))l(this);W(this,nn).clear(),W(this,Pn)===0&&wr(this,ea,Ps).call(this),Mi(n),Mi(a),W(this,Zn).clear(),W(this,on).clear(),Xo=null,(o=W(this,Qn))==null||o.resolve()}Lr=null}capture(t,a){a!==Mr&&!this.previous.has(t)&&this.previous.set(t,a),(t.f&cn)===0&&(this.current.set(t,t.v),Lr==null||Lr.set(t,t.v))}activate(){wt=this,this.apply()}deactivate(){wt===this&&(wt=null,Lr=null)}flush(){var t;if(Xr.length>0)wt=this,_l();else if(W(this,Pn)===0&&!this.is_fork){for(const a of W(this,nn))a(this);W(this,nn).clear(),wr(this,ea,Ps).call(this),(t=W(this,Qn))==null||t.resolve()}this.deactivate()}discard(){for(const t of W(this,Jn))t(this);W(this,Jn).clear()}increment(t){Tt(this,Pn,W(this,Pn)+1),t&&Tt(this,Xn,W(this,Xn)+1)}decrement(t){Tt(this,Pn,W(this,Pn)-1),t&&Tt(this,Xn,W(this,Xn)-1),!W(this,eo)&&(Tt(this,eo,!0),Va(()=>{Tt(this,eo,!1),wr(this,ea,Es).call(this)?Xr.length>0&&this.flush():this.revive()}))}revive(){for(const t of W(this,Zn))W(this,on).delete(t),xr(t,Rr),Ra(t);for(const t of W(this,on))xr(t,Sa),Ra(t);this.flush()}oncommit(t){W(this,nn).add(t)}ondiscard(t){W(this,Jn).add(t)}settled(){return(W(this,Qn)??Tt(this,Qn,sl())).promise}static ensure(){if(wt===null){const t=wt=new fi;qo.add(wt),Co||Va(()=>{wt===t&&t.flush()})}return wt}apply(){}};nn=new WeakMap,Jn=new WeakMap,Pn=new WeakMap,Xn=new WeakMap,Qn=new WeakMap,Zn=new WeakMap,on=new WeakMap,Ia=new WeakMap,eo=new WeakMap,ea=new WeakSet,Es=function(){return this.is_fork||W(this,Xn)>0},Is=function(t,a,n){t.f^=Or;for(var o=t.first;o!==null;){var l=o.f,s=(l&(Ta|Hn))!==0,d=s&&(l&Or)!==0,v=(l&Gr)!==0,m=d||W(this,Ia).has(o);if(!m&&o.fn!==null){s?v||(o.f^=Or):(l&co)!==0?a.push(o):(l&(Vn|ls))!==0&&v?n.push(o):Do(o)&&(lo(o),(l&_n)!==0&&(W(this,on).add(o),v&&xr(o,Rr)));var x=o.first;if(x!==null){o=x;continue}}for(;o!==null;){var g=o.next;if(g!==null){o=g;break}o=o.parent}}},Ns=function(t){for(var a=0;a<t.length;a+=1)bl(t[a],W(this,Zn),W(this,on))},Ps=function(){var l;if(qo.size>1){this.previous.clear();var t=wt,a=Lr,n=!0;for(const s of qo){if(s===this){n=!1;continue}const d=[];for(const[m,x]of this.current){if(s.current.has(m))if(n&&x!==s.current.get(m))s.current.set(m,x);else continue;d.push(m)}if(d.length===0)continue;const v=[...s.current.keys()].filter(m=>!this.current.has(m));if(v.length>0){var o=Xr;Xr=[];const m=new Set,x=new Map;for(const g of d)yl(g,v,m,x);if(Xr.length>0){wt=s,s.apply();for(const g of Xr)wr(l=s,ea,Is).call(l,g,[],[]);s.deactivate()}Xr=o}}wt=t,Lr=a}W(this,Ia).clear(),qo.delete(this)};let un=fi;function Zc(e){var t=Co;Co=!0;try{for(var a;;){if(Jc(),Xr.length===0&&(wt==null||wt.flush(),Xr.length===0))return ds=null,a;_l()}}finally{Co=t}}function _l(){var e=null;try{for(var t=0;Xr.length>0;){var a=un.ensure();if(t++>1e3){var n,o;eu()}a.process(Xr),vn.clear()}}finally{Xr=[],ds=null,so=null}}function eu(){try{Tc()}catch(e){ln(e,ds)}}let _a=null;function Mi(e){var t=e.length;if(t!==0){for(var a=0;a<t;){var n=e[a++];if((n.f&(Da|Gr))===0&&Do(n)&&(_a=new Set,lo(n),n.deps===null&&n.first===null&&n.nodes===null&&n.teardown===null&&n.ac===null&&Vl(n),(_a==null?void 0:_a.size)>0)){vn.clear();for(const o of _a){if((o.f&(Da|Gr))!==0)continue;const l=[o];let s=o.parent;for(;s!==null;)_a.has(s)&&(_a.delete(s),l.push(s)),s=s.parent;for(let d=l.length-1;d>=0;d--){const v=l[d];(v.f&(Da|Gr))===0&&lo(v)}}_a.clear()}}_a=null}}function yl(e,t,a,n){if(!a.has(e)&&(a.add(e),e.reactions!==null))for(const o of e.reactions){const l=o.f;(l&jr)!==0?yl(o,t,a,n):(l&(ei|_n))!==0&&(l&Rr)===0&&wl(o,t,n)&&(xr(o,Rr),Ra(o))}}function wl(e,t,a){const n=a.get(e);if(n!==void 0)return n;if(e.deps!==null)for(const o of e.deps){if(no.call(t,o))return!0;if((o.f&jr)!==0&&wl(o,t,a))return a.set(o,!0),!0}return a.set(e,!1),!1}function Ra(e){var t=ds=e,a=t.b;if(a!=null&&a.is_pending&&(e.f&(co|Vn|ls))!==0&&(e.f&uo)===0){a.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var n=t.f;if(so!==null&&t===Nt&&(e.f&Vn)===0)return;if((n&(Hn|Ta))!==0){if((n&Or)===0)return;t.f^=Or}}Xr.push(t)}function kl(e,t){if(!((e.f&Ta)!==0&&(e.f&Or)!==0)){(e.f&Rr)!==0?t.d.push(e):(e.f&Sa)!==0&&t.m.push(e),xr(e,Or);for(var a=e.first;a!==null;)kl(a,t),a=a.next}}function tu(e){let t=0,a=xn(0),n;return()=>{oi()&&(r(a),si(()=>(t===0&&(n=Bn(()=>e(()=>To(a)))),t+=1,()=>{Va(()=>{t-=1,t===0&&(n==null||n(),n=void 0,To(a))})})))}}var ru=Wa|vo;function au(e,t,a,n){new nu(e,t,a,n)}var va,Js,Na,Ln,Jr,Pa,ia,ya,Ua,On,sn,to,ro,ao,Ka,os,Cr,ou,su,iu,Ls,Ko,Go,Os;class nu{constructor(t,a,n,o){Ot(this,Cr);ba(this,"parent");ba(this,"is_pending",!1);ba(this,"transform_error");Ot(this,va);Ot(this,Js,null);Ot(this,Na);Ot(this,Ln);Ot(this,Jr);Ot(this,Pa,null);Ot(this,ia,null);Ot(this,ya,null);Ot(this,Ua,null);Ot(this,On,0);Ot(this,sn,0);Ot(this,to,!1);Ot(this,ro,new Set);Ot(this,ao,new Set);Ot(this,Ka,null);Ot(this,os,tu(()=>(Tt(this,Ka,xn(W(this,On))),()=>{Tt(this,Ka,null)})));var l;Tt(this,va,t),Tt(this,Na,a),Tt(this,Ln,s=>{var d=Nt;d.b=this,d.f|=zs,n(s)}),this.parent=Nt.b,this.transform_error=o??((l=this.parent)==null?void 0:l.transform_error)??(s=>s),Tt(this,Jr,fo(()=>{wr(this,Cr,Ls).call(this)},ru))}defer_effect(t){bl(t,W(this,ro),W(this,ao))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!W(this,Na).pending}update_pending_count(t){wr(this,Cr,Os).call(this,t),Tt(this,On,W(this,On)+t),!(!W(this,Ka)||W(this,to))&&(Tt(this,to,!0),Va(()=>{Tt(this,to,!1),W(this,Ka)&&io(W(this,Ka),W(this,On))}))}get_effect_pending(){return W(this,os).call(this),r(W(this,Ka))}error(t){var a=W(this,Na).onerror;let n=W(this,Na).failed;if(!a&&!n)throw t;W(this,Pa)&&(Dr(W(this,Pa)),Tt(this,Pa,null)),W(this,ia)&&(Dr(W(this,ia)),Tt(this,ia,null)),W(this,ya)&&(Dr(W(this,ya)),Tt(this,ya,null));var o=!1,l=!1;const s=()=>{if(o){Kc();return}o=!0,l&&Ic(),W(this,ya)!==null&&Dn(W(this,ya),()=>{Tt(this,ya,null)}),wr(this,Cr,Go).call(this,()=>{un.ensure(),wr(this,Cr,Ls).call(this)})},d=v=>{try{l=!0,a==null||a(v,s),l=!1}catch(m){ln(m,W(this,Jr)&&W(this,Jr).parent)}n&&Tt(this,ya,wr(this,Cr,Go).call(this,()=>{un.ensure();try{return Zr(()=>{var m=Nt;m.b=this,m.f|=zs,n(W(this,va),()=>v,()=>s)})}catch(m){return ln(m,W(this,Jr).parent),null}}))};Va(()=>{var v;try{v=this.transform_error(t)}catch(m){ln(m,W(this,Jr)&&W(this,Jr).parent);return}v!==null&&typeof v=="object"&&typeof v.then=="function"?v.then(d,m=>ln(m,W(this,Jr)&&W(this,Jr).parent)):d(v)})}}va=new WeakMap,Js=new WeakMap,Na=new WeakMap,Ln=new WeakMap,Jr=new WeakMap,Pa=new WeakMap,ia=new WeakMap,ya=new WeakMap,Ua=new WeakMap,On=new WeakMap,sn=new WeakMap,to=new WeakMap,ro=new WeakMap,ao=new WeakMap,Ka=new WeakMap,os=new WeakMap,Cr=new WeakSet,ou=function(){try{Tt(this,Pa,Zr(()=>W(this,Ln).call(this,W(this,va))))}catch(t){this.error(t)}},su=function(t){const a=W(this,Na).failed;a&&Tt(this,ya,Zr(()=>{a(W(this,va),()=>t,()=>()=>{})}))},iu=function(){const t=W(this,Na).pending;t&&(this.is_pending=!0,Tt(this,ia,Zr(()=>t(W(this,va)))),Va(()=>{var a=Tt(this,Ua,document.createDocumentFragment()),n=qa();a.append(n),Tt(this,Pa,wr(this,Cr,Go).call(this,()=>(un.ensure(),Zr(()=>W(this,Ln).call(this,n))))),W(this,sn)===0&&(W(this,va).before(a),Tt(this,Ua,null),Dn(W(this,ia),()=>{Tt(this,ia,null)}),wr(this,Cr,Ko).call(this))}))},Ls=function(){try{if(this.is_pending=this.has_pending_snippet(),Tt(this,sn,0),Tt(this,On,0),Tt(this,Pa,Zr(()=>{W(this,Ln).call(this,W(this,va))})),W(this,sn)>0){var t=Tt(this,Ua,document.createDocumentFragment());di(W(this,Pa),t);const a=W(this,Na).pending;Tt(this,ia,Zr(()=>a(W(this,va))))}else wr(this,Cr,Ko).call(this)}catch(a){this.error(a)}},Ko=function(){this.is_pending=!1;for(const t of W(this,ro))xr(t,Rr),Ra(t);for(const t of W(this,ao))xr(t,Sa),Ra(t);W(this,ro).clear(),W(this,ao).clear()},Go=function(t){var a=Nt,n=It,o=Ar;xa(W(this,Jr)),ma(W(this,Jr)),oo(W(this,Jr).ctx);try{return t()}catch(l){return hl(l),null}finally{xa(a),ma(n),oo(o)}},Os=function(t){var a;if(!this.has_pending_snippet()){this.parent&&wr(a=this.parent,Cr,Os).call(a,t);return}Tt(this,sn,W(this,sn)+t),W(this,sn)===0&&(wr(this,Cr,Ko).call(this),W(this,ia)&&Dn(W(this,ia),()=>{Tt(this,ia,null)}),W(this,Ua)&&(W(this,va).before(W(this,Ua)),Tt(this,Ua,null)))};function $l(e,t,a,n){const o=Lo()?Oo:ri;var l=e.filter(g=>!g.settled);if(a.length===0&&l.length===0){n(t.map(o));return}var s=Nt,d=lu(),v=l.length===1?l[0].promise:l.length>1?Promise.all(l.map(g=>g.promise)):null;function m(g){d();try{n(g)}catch(y){(s.f&Da)===0&&ln(y,s)}Rs()}if(a.length===0){v.then(()=>m(t.map(o)));return}function x(){d(),Promise.all(a.map(g=>cu(g))).then(g=>m([...t.map(o),...g])).catch(g=>ln(g,s))}v?v.then(x):x()}function lu(){var e=Nt,t=It,a=Ar,n=wt;return function(l=!0){xa(e),ma(t),oo(a),l&&(n==null||n.activate())}}function Rs(e=!0){xa(null),ma(null),oo(null),e&&(wt==null||wt.deactivate())}function du(){var e=Nt.b,t=wt,a=e.is_rendered();return e.update_pending_count(1),t.increment(a),()=>{e.update_pending_count(-1),t.decrement(a)}}function Oo(e){var t=jr|Rr,a=It!==null&&(It.f&jr)!==0?It:null;return Nt!==null&&(Nt.f|=vo),{ctx:Ar,deps:null,effects:null,equals:pl,f:t,fn:e,reactions:null,rv:0,v:Mr,wv:0,parent:a??Nt,ac:null}}function cu(e,t,a){Nt===null&&wc();var o=void 0,l=xn(Mr),s=!It,d=new Map;return $u(()=>{var y;var v=sl();o=v.promise;try{Promise.resolve(e()).then(v.resolve,v.reject).finally(Rs)}catch(E){v.reject(E),Rs()}var m=wt;if(s){var x=du();(y=d.get(m))==null||y.reject(zn),d.delete(m),d.set(m,v)}const g=(E,C=void 0)=>{if(m.activate(),C)C!==zn&&(l.f|=cn,io(l,C));else{(l.f&cn)!==0&&(l.f^=cn),io(l,E);for(const[V,T]of d){if(d.delete(V),V===m)break;T.reject(zn)}}x&&x()};v.promise.then(g,E=>g(null,E||"unknown"))}),us(()=>{for(const v of d.values())v.reject(zn)}),new Promise(v=>{function m(x){function g(){x===o?v(l):m(o)}x.then(g,g)}m(o)})}function D(e){const t=Oo(e);return Fl(t),t}function ri(e){const t=Oo(e);return t.equals=ml,t}function uu(e){var t=e.effects;if(t!==null){e.effects=null;for(var a=0;a<t.length;a+=1)Dr(t[a])}}function vu(e){for(var t=e.parent;t!==null;){if((t.f&jr)===0)return(t.f&Da)===0?t:null;t=t.parent}return null}function ai(e){var t,a=Nt;xa(vu(e));try{e.f&=~qn,uu(e),t=Gl(e)}finally{xa(a)}return t}function Cl(e){var t=ai(e);if(!e.equals(t)&&(e.wv=Ul(),(!(wt!=null&&wt.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){xr(e,Or);return}hn||(Lr!==null?(oi()||wt!=null&&wt.is_fork)&&Lr.set(e,t):ti(e))}function fu(e){var t,a;if(e.effects!==null)for(const n of e.effects)(n.teardown||n.ac)&&((t=n.teardown)==null||t.call(n),(a=n.ac)==null||a.abort(zn),n.teardown=gc,n.ac=null,Eo(n,0),ii(n))}function Sl(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&lo(t)}let Ds=new Set;const vn=new Map;let Tl=!1;function xn(e,t){var a={f:0,v:e,reactions:null,equals:pl,rv:0,wv:0};return a}function X(e,t){const a=xn(e);return Fl(a),a}function pu(e,t=!1,a=!0){var o;const n=xn(e);return t||(n.equals=ml),Po&&a&&Ar!==null&&Ar.l!==null&&((o=Ar.l).s??(o.s=[])).push(n),n}function u(e,t,a=!1){It!==null&&(!ka||(It.f&Ti)!==0)&&Lo()&&(It.f&(jr|_n|ei|Ti))!==0&&(pa===null||!no.call(pa,e))&&Ec();let n=a?Ut(t):t;return io(e,n)}function io(e,t){if(!e.equals(t)){var a=e.v;hn?vn.set(e,t):vn.set(e,a),e.v=t;var n=un.ensure();if(n.capture(e,a),(e.f&jr)!==0){const o=e;(e.f&Rr)!==0&&ai(o),ti(o)}e.wv=Ul(),Ml(e,Rr),Lo()&&Nt!==null&&(Nt.f&Or)!==0&&(Nt.f&(Ta|Hn))===0&&(ua===null?Su([e]):ua.push(e)),!n.is_fork&&Ds.size>0&&!Tl&&mu()}return t}function mu(){Tl=!1;for(const e of Ds)(e.f&Or)!==0&&xr(e,Sa),Do(e)&&lo(e);Ds.clear()}function So(e,t=1){var a=r(e),n=t===1?a++:a--;return u(e,a),n}function To(e){u(e,e.v+1)}function Ml(e,t){var a=e.reactions;if(a!==null)for(var n=Lo(),o=a.length,l=0;l<o;l++){var s=a[l],d=s.f;if(!(!n&&s===Nt)){var v=(d&Rr)===0;if(v&&xr(s,t),(d&jr)!==0){var m=s;Lr==null||Lr.delete(m),(d&qn)===0&&(d&fa&&(s.f|=qn),Ml(m,Sa))}else v&&((d&_n)!==0&&_a!==null&&_a.add(s),Ra(s))}}}function Ut(e){if(typeof e!="object"||e===null||ja in e)return e;const t=Qs(e);if(t!==xc&&t!==hc)return e;var a=new Map,n=Xs(e),o=X(0),l=jn,s=d=>{if(jn===l)return d();var v=It,m=jn;ma(null),Ii(l);var x=d();return ma(v),Ii(m),x};return n&&a.set("length",X(e.length)),new Proxy(e,{defineProperty(d,v,m){(!("value"in m)||m.configurable===!1||m.enumerable===!1||m.writable===!1)&&zc();var x=a.get(v);return x===void 0?s(()=>{var g=X(m.value);return a.set(v,g),g}):u(x,m.value,!0),!0},deleteProperty(d,v){var m=a.get(v);if(m===void 0){if(v in d){const x=s(()=>X(Mr));a.set(v,x),To(o)}}else u(m,Mr),To(o);return!0},get(d,v,m){var E;if(v===ja)return e;var x=a.get(v),g=v in d;if(x===void 0&&(!g||(E=dn(d,v))!=null&&E.writable)&&(x=s(()=>{var C=Ut(g?d[v]:Mr),V=X(C);return V}),a.set(v,x)),x!==void 0){var y=r(x);return y===Mr?void 0:y}return Reflect.get(d,v,m)},getOwnPropertyDescriptor(d,v){var m=Reflect.getOwnPropertyDescriptor(d,v);if(m&&"value"in m){var x=a.get(v);x&&(m.value=r(x))}else if(m===void 0){var g=a.get(v),y=g==null?void 0:g.v;if(g!==void 0&&y!==Mr)return{enumerable:!0,configurable:!0,value:y,writable:!0}}return m},has(d,v){var y;if(v===ja)return!0;var m=a.get(v),x=m!==void 0&&m.v!==Mr||Reflect.has(d,v);if(m!==void 0||Nt!==null&&(!x||(y=dn(d,v))!=null&&y.writable)){m===void 0&&(m=s(()=>{var E=x?Ut(d[v]):Mr,C=X(E);return C}),a.set(v,m));var g=r(m);if(g===Mr)return!1}return x},set(d,v,m,x){var H;var g=a.get(v),y=v in d;if(n&&v==="length")for(var E=m;E<g.v;E+=1){var C=a.get(E+"");C!==void 0?u(C,Mr):E in d&&(C=s(()=>X(Mr)),a.set(E+"",C))}if(g===void 0)(!y||(H=dn(d,v))!=null&&H.writable)&&(g=s(()=>X(void 0)),u(g,Ut(m)),a.set(v,g));else{y=g.v!==Mr;var V=s(()=>Ut(m));u(g,V)}var T=Reflect.getOwnPropertyDescriptor(d,v);if(T!=null&&T.set&&T.set.call(x,m),!y){if(n&&typeof v=="string"){var I=a.get("length"),N=Number(v);Number.isInteger(N)&&N>=I.v&&u(I,N+1)}To(o)}return!0},ownKeys(d){r(o);var v=Reflect.ownKeys(d).filter(g=>{var y=a.get(g);return y===void 0||y.v!==Mr});for(var[m,x]of a)x.v!==Mr&&!(m in d)&&v.push(m);return v},setPrototypeOf(){Ac()}})}function zi(e){try{if(e!==null&&typeof e=="object"&&ja in e)return e[ja]}catch{}return e}function xu(e,t){return Object.is(zi(e),zi(t))}var Qo,zl,Al,El,Il;function hu(){if(Qo===void 0){Qo=window,zl=document,Al=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,a=Text.prototype;El=dn(t,"firstChild").get,Il=dn(t,"nextSibling").get,Si(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Si(a)&&(a.__t=void 0)}}function qa(e=""){return document.createTextNode(e)}function Ga(e){return El.call(e)}function Ro(e){return Il.call(e)}function i(e,t){return Ga(e)}function re(e,t=!1){{var a=Ga(e);return a instanceof Comment&&a.data===""?Ro(a):a}}function p(e,t=1,a=!1){let n=e;for(;t--;)n=Ro(n);return n}function gu(e){e.textContent=""}function Nl(){return!1}function ni(e,t,a){return document.createElementNS(t??vl,e,void 0)}function bu(e,t){if(t){const a=document.body;e.autofocus=!0,Va(()=>{document.activeElement===a&&e.focus()})}}let Ai=!1;function _u(){Ai||(Ai=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const a of e.target.elements)(t=a.__on_r)==null||t.call(a)})},{capture:!0}))}function cs(e){var t=It,a=Nt;ma(null),xa(null);try{return e()}finally{ma(t),xa(a)}}function Pl(e,t,a,n=a){e.addEventListener(t,()=>cs(a));const o=e.__on_r;o?e.__on_r=()=>{o(),n(!0)}:e.__on_r=()=>n(!0),_u()}function Ll(e){Nt===null&&(It===null&&Sc(),Cc()),hn&&$c()}function yu(e,t){var a=t.last;a===null?t.last=t.first=e:(a.next=e,e.prev=a,t.last=e)}function Ma(e,t){var a=Nt;a!==null&&(a.f&Gr)!==0&&(e|=Gr);var n={ctx:Ar,deps:null,nodes:null,f:e|Rr|fa,first:null,fn:t,last:null,next:null,parent:a,b:a&&a.b,prev:null,teardown:null,wv:0,ac:null},o=n;if((e&co)!==0)so!==null?so.push(n):Ra(n);else if(t!==null){try{lo(n)}catch(s){throw Dr(n),s}o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&vo)===0&&(o=o.first,(e&_n)!==0&&(e&Wa)!==0&&o!==null&&(o.f|=Wa))}if(o!==null&&(o.parent=a,a!==null&&yu(o,a),It!==null&&(It.f&jr)!==0&&(e&Hn)===0)){var l=It;(l.effects??(l.effects=[])).push(o)}return n}function oi(){return It!==null&&!ka}function us(e){const t=Ma(Vn,null);return xr(t,Or),t.teardown=e,t}function $r(e){Ll();var t=Nt.f,a=!It&&(t&Ta)!==0&&(t&uo)===0;if(a){var n=Ar;(n.e??(n.e=[])).push(e)}else return Ol(e)}function Ol(e){return Ma(co|il,e)}function wu(e){return Ll(),Ma(Vn|il,e)}function ku(e){un.ensure();const t=Ma(Hn|vo,e);return(a={})=>new Promise(n=>{a.outro?Dn(t,()=>{Dr(t),n(void 0)}):(Dr(t),n(void 0))})}function vs(e){return Ma(co,e)}function $u(e){return Ma(ei|vo,e)}function si(e,t=0){return Ma(Vn|t,e)}function S(e,t=[],a=[],n=[]){$l(n,t,a,o=>{Ma(Vn,()=>e(...o.map(r)))})}function fo(e,t=0){var a=Ma(_n|t,e);return a}function Rl(e,t=0){var a=Ma(ls|t,e);return a}function Zr(e){return Ma(Ta|vo,e)}function Dl(e){var t=e.teardown;if(t!==null){const a=hn,n=It;Ei(!0),ma(null);try{t.call(null)}finally{Ei(a),ma(n)}}}function ii(e,t=!1){var a=e.first;for(e.first=e.last=null;a!==null;){const o=a.ac;o!==null&&cs(()=>{o.abort(zn)});var n=a.next;(a.f&Hn)!==0?a.parent=null:Dr(a,t),a=n}}function Cu(e){for(var t=e.first;t!==null;){var a=t.next;(t.f&Ta)===0&&Dr(t),t=a}}function Dr(e,t=!0){var a=!1;(t||(e.f&_c)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(jl(e.nodes.start,e.nodes.end),a=!0),ii(e,t&&!a),Eo(e,0),xr(e,Da);var n=e.nodes&&e.nodes.t;if(n!==null)for(const l of n)l.stop();Dl(e);var o=e.parent;o!==null&&o.first!==null&&Vl(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function jl(e,t){for(;e!==null;){var a=e===t?null:Ro(e);e.remove(),e=a}}function Vl(e){var t=e.parent,a=e.prev,n=e.next;a!==null&&(a.next=n),n!==null&&(n.prev=a),t!==null&&(t.first===e&&(t.first=n),t.last===e&&(t.last=a))}function Dn(e,t,a=!0){var n=[];ql(e,n,!0);var o=()=>{a&&Dr(e),t&&t()},l=n.length;if(l>0){var s=()=>--l||o();for(var d of n)d.out(s)}else o()}function ql(e,t,a){if((e.f&Gr)===0){e.f^=Gr;var n=e.nodes&&e.nodes.t;if(n!==null)for(const d of n)(d.is_global||a)&&t.push(d);for(var o=e.first;o!==null;){var l=o.next,s=(o.f&Wa)!==0||(o.f&Ta)!==0&&(e.f&_n)!==0;ql(o,t,s?a:!1),o=l}}}function li(e){Bl(e,!0)}function Bl(e,t){if((e.f&Gr)!==0){e.f^=Gr;for(var a=e.first;a!==null;){var n=a.next,o=(a.f&Wa)!==0||(a.f&Ta)!==0;Bl(a,o?t:!1),a=n}var l=e.nodes&&e.nodes.t;if(l!==null)for(const s of l)(s.is_global||t)&&s.in()}}function di(e,t){if(e.nodes)for(var a=e.nodes.start,n=e.nodes.end;a!==null;){var o=a===n?null:Ro(a);t.append(a),a=o}}let Wo=!1,hn=!1;function Ei(e){hn=e}let It=null,ka=!1;function ma(e){It=e}let Nt=null;function xa(e){Nt=e}let pa=null;function Fl(e){It!==null&&(pa===null?pa=[e]:pa.push(e))}let Qr=null,sa=0,ua=null;function Su(e){ua=e}let Hl=1,En=0,jn=En;function Ii(e){jn=e}function Ul(){return++Hl}function Do(e){var t=e.f;if((t&Rr)!==0)return!0;if(t&jr&&(e.f&=~qn),(t&Sa)!==0){for(var a=e.deps,n=a.length,o=0;o<n;o++){var l=a[o];if(Do(l)&&Cl(l),l.wv>e.wv)return!0}(t&fa)!==0&&Lr===null&&xr(e,Or)}return!1}function Kl(e,t,a=!0){var n=e.reactions;if(n!==null&&!(pa!==null&&no.call(pa,e)))for(var o=0;o<n.length;o++){var l=n[o];(l.f&jr)!==0?Kl(l,t,!1):t===l&&(a?xr(l,Rr):(l.f&Or)!==0&&xr(l,Sa),Ra(l))}}function Gl(e){var V;var t=Qr,a=sa,n=ua,o=It,l=pa,s=Ar,d=ka,v=jn,m=e.f;Qr=null,sa=0,ua=null,It=(m&(Ta|Hn))===0?e:null,pa=null,oo(e.ctx),ka=!1,jn=++En,e.ac!==null&&(cs(()=>{e.ac.abort(zn)}),e.ac=null);try{e.f|=As;var x=e.fn,g=x();e.f|=uo;var y=e.deps,E=wt==null?void 0:wt.is_fork;if(Qr!==null){var C;if(E||Eo(e,sa),y!==null&&sa>0)for(y.length=sa+Qr.length,C=0;C<Qr.length;C++)y[sa+C]=Qr[C];else e.deps=y=Qr;if(oi()&&(e.f&fa)!==0)for(C=sa;C<y.length;C++)((V=y[C]).reactions??(V.reactions=[])).push(e)}else!E&&y!==null&&sa<y.length&&(Eo(e,sa),y.length=sa);if(Lo()&&ua!==null&&!ka&&y!==null&&(e.f&(jr|Sa|Rr))===0)for(C=0;C<ua.length;C++)Kl(ua[C],e);if(o!==null&&o!==e){if(En++,o.deps!==null)for(let T=0;T<a;T+=1)o.deps[T].rv=En;if(t!==null)for(const T of t)T.rv=En;ua!==null&&(n===null?n=ua:n.push(...ua))}return(e.f&cn)!==0&&(e.f^=cn),g}catch(T){return hl(T)}finally{e.f^=As,Qr=t,sa=a,ua=n,It=o,pa=l,oo(s),ka=d,jn=v}}function Tu(e,t){let a=t.reactions;if(a!==null){var n=pc.call(a,e);if(n!==-1){var o=a.length-1;o===0?a=t.reactions=null:(a[n]=a[o],a.pop())}}if(a===null&&(t.f&jr)!==0&&(Qr===null||!no.call(Qr,t))){var l=t;(l.f&fa)!==0&&(l.f^=fa,l.f&=~qn),ti(l),fu(l),Eo(l,0)}}function Eo(e,t){var a=e.deps;if(a!==null)for(var n=t;n<a.length;n++)Tu(e,a[n])}function lo(e){var t=e.f;if((t&Da)===0){xr(e,Or);var a=Nt,n=Wo;Nt=e,Wo=!0;try{(t&(_n|ls))!==0?Cu(e):ii(e),Dl(e);var o=Gl(e);e.teardown=typeof o=="function"?o:null,e.wv=Hl;var l;Ts&&Wc&&(e.f&Rr)!==0&&e.deps}finally{Wo=n,Nt=a}}}async function Wl(){await Promise.resolve(),Zc()}function r(e){var t=e.f,a=(t&jr)!==0;if(It!==null&&!ka){var n=Nt!==null&&(Nt.f&Da)!==0;if(!n&&(pa===null||!no.call(pa,e))){var o=It.deps;if((It.f&As)!==0)e.rv<En&&(e.rv=En,Qr===null&&o!==null&&o[sa]===e?sa++:Qr===null?Qr=[e]:Qr.push(e));else{(It.deps??(It.deps=[])).push(e);var l=e.reactions;l===null?e.reactions=[It]:no.call(l,It)||l.push(It)}}}if(hn&&vn.has(e))return vn.get(e);if(a){var s=e;if(hn){var d=s.v;return((s.f&Or)===0&&s.reactions!==null||Jl(s))&&(d=ai(s)),vn.set(s,d),d}var v=(s.f&fa)===0&&!ka&&It!==null&&(Wo||(It.f&fa)!==0),m=(s.f&uo)===0;Do(s)&&(v&&(s.f|=fa),Cl(s)),v&&!m&&(Sl(s),Yl(s))}if(Lr!=null&&Lr.has(e))return Lr.get(e);if((e.f&cn)!==0)throw e.v;return e.v}function Yl(e){if(e.f|=fa,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&jr)!==0&&(t.f&fa)===0&&(Sl(t),Yl(t))}function Jl(e){if(e.v===Mr)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(vn.has(t)||(t.f&jr)!==0&&Jl(t))return!0;return!1}function Bn(e){var t=ka;try{return ka=!0,e()}finally{ka=t}}function Tn(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(ja in e)js(e);else if(!Array.isArray(e))for(let t in e){const a=e[t];typeof a=="object"&&a&&ja in a&&js(a)}}}function js(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let n in e)try{js(e[n],t)}catch{}const a=Qs(e);if(a!==Object.prototype&&a!==Array.prototype&&a!==Map.prototype&&a!==Set.prototype&&a!==Date.prototype){const n=ol(a);for(let o in n){const l=n[o].get;if(l)try{l.call(e)}catch{}}}}}function Mu(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const zu=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function Au(e){return zu.includes(e)}const Eu={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function Iu(e){return e=e.toLowerCase(),Eu[e]??e}const Nu=["touchstart","touchmove"];function Pu(e){return Nu.includes(e)}const In=Symbol("events"),Xl=new Set,Vs=new Set;function Ql(e,t,a,n={}){function o(l){if(n.capture||qs.call(t,l),!l.cancelBubble)return cs(()=>a==null?void 0:a.call(this,l))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Va(()=>{t.addEventListener(e,o,n)}):t.addEventListener(e,o,n),o}function fn(e,t,a,n,o){var l={capture:n,passive:o},s=Ql(e,t,a,l);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&us(()=>{t.removeEventListener(e,s,l)})}function oe(e,t,a){(t[In]??(t[In]={}))[e]=a}function Vr(e){for(var t=0;t<e.length;t++)Xl.add(e[t]);for(var a of Vs)a(e)}let Ni=null;function qs(e){var T,I;var t=this,a=t.ownerDocument,n=e.type,o=((T=e.composedPath)==null?void 0:T.call(e))||[],l=o[0]||e.target;Ni=e;var s=0,d=Ni===e&&e[In];if(d){var v=o.indexOf(d);if(v!==-1&&(t===document||t===window)){e[In]=t;return}var m=o.indexOf(t);if(m===-1)return;v<=m&&(s=v)}if(l=o[s]||e.target,l!==t){mc(e,"currentTarget",{configurable:!0,get(){return l||a}});var x=It,g=Nt;ma(null),xa(null);try{for(var y,E=[];l!==null;){var C=l.assignedSlot||l.parentNode||l.host||null;try{var V=(I=l[In])==null?void 0:I[n];V!=null&&(!l.disabled||e.target===l)&&V.call(l,e)}catch(N){y?E.push(N):y=N}if(e.cancelBubble||C===t||C===null)break;l=C}if(y){for(let N of E)queueMicrotask(()=>{throw N});throw y}}finally{e[In]=t,delete e.currentTarget,ma(x),xa(g)}}}var al;const _s=((al=globalThis==null?void 0:globalThis.window)==null?void 0:al.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function Lu(e){return(_s==null?void 0:_s.createHTML(e))??e}function Zl(e){var t=ni("template");return t.innerHTML=Lu(e.replaceAll("<!>","<!---->")),t.content}function Fn(e,t){var a=Nt;a.nodes===null&&(a.nodes={start:e,end:t,a:null,t:null})}function f(e,t){var a=(t&qc)!==0,n=(t&Bc)!==0,o,l=!e.startsWith("<!>");return()=>{o===void 0&&(o=Zl(l?e:"<!>"+e),a||(o=Ga(o)));var s=n||Al?document.importNode(o,!0):o.cloneNode(!0);if(a){var d=Ga(s),v=s.lastChild;Fn(d,v)}else Fn(s,s);return s}}function Ou(e,t,a="svg"){var n=!e.startsWith("<!>"),o=`<${a}>${n?e:"<!>"+e}</${a}>`,l;return()=>{if(!l){var s=Zl(o),d=Ga(s);l=Ga(d)}var v=l.cloneNode(!0);return Fn(v,v),v}}function Ru(e,t){return Ou(e,t,"svg")}function an(e=""){{var t=qa(e+"");return Fn(t,t),t}}function ke(){var e=document.createDocumentFragment(),t=document.createComment(""),a=qa();return e.append(t,a),Fn(t,a),e}function c(e,t){e!==null&&e.before(t)}function $(e,t){var a=t==null?"":typeof t=="object"?`${t}`:t;a!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=a,e.nodeValue=`${a}`)}function Du(e,t){return ju(e,t)}const Bo=new Map;function ju(e,{target:t,anchor:a,props:n={},events:o,context:l,intro:s=!0,transformError:d}){hu();var v=void 0,m=ku(()=>{var x=a??t.appendChild(qa());au(x,{pending:()=>{}},E=>{br({});var C=Ar;l&&(C.c=l),o&&(n.$$events=o),v=e(E,n)||{},_r()},d);var g=new Set,y=E=>{for(var C=0;C<E.length;C++){var V=E[C];if(!g.has(V)){g.add(V);var T=Pu(V);for(const H of[t,document]){var I=Bo.get(H);I===void 0&&(I=new Map,Bo.set(H,I));var N=I.get(V);N===void 0?(H.addEventListener(V,qs,{passive:T}),I.set(V,1)):I.set(V,N+1)}}}};return y(is(Xl)),Vs.add(y),()=>{var T;for(var E of g)for(const I of[t,document]){var C=Bo.get(I),V=C.get(E);--V==0?(I.removeEventListener(E,qs),C.delete(E),C.size===0&&Bo.delete(I)):C.set(E,V)}Vs.delete(y),x!==a&&((T=x.parentNode)==null||T.removeChild(x))}});return Vu.set(v,m),v}let Vu=new WeakMap;var wa,La,la,Rn,Io,No,ss;class fs{constructor(t,a=!0){ba(this,"anchor");Ot(this,wa,new Map);Ot(this,La,new Map);Ot(this,la,new Map);Ot(this,Rn,new Set);Ot(this,Io,!0);Ot(this,No,t=>{if(W(this,wa).has(t)){var a=W(this,wa).get(t),n=W(this,La).get(a);if(n)li(n),W(this,Rn).delete(a);else{var o=W(this,la).get(a);o&&(o.effect.f&Gr)===0&&(W(this,La).set(a,o.effect),W(this,la).delete(a),o.fragment.lastChild.remove(),this.anchor.before(o.fragment),n=o.effect)}for(const[l,s]of W(this,wa)){if(W(this,wa).delete(l),l===t)break;const d=W(this,la).get(s);d&&(Dr(d.effect),W(this,la).delete(s))}for(const[l,s]of W(this,La)){if(l===a||W(this,Rn).has(l)||(s.f&Gr)!==0)continue;const d=()=>{if(Array.from(W(this,wa).values()).includes(l)){var m=document.createDocumentFragment();di(s,m),m.append(qa()),W(this,la).set(l,{effect:s,fragment:m})}else Dr(s);W(this,Rn).delete(l),W(this,La).delete(l)};W(this,Io)||!n?(W(this,Rn).add(l),Dn(s,d,!1)):d()}}});Ot(this,ss,t=>{W(this,wa).delete(t);const a=Array.from(W(this,wa).values());for(const[n,o]of W(this,la))a.includes(n)||(Dr(o.effect),W(this,la).delete(n))});this.anchor=t,Tt(this,Io,a)}ensure(t,a){var n=wt,o=Nl();if(a&&!W(this,La).has(t)&&!W(this,la).has(t))if(o){var l=document.createDocumentFragment(),s=qa();l.append(s),W(this,la).set(t,{effect:Zr(()=>a(s)),fragment:l})}else W(this,La).set(t,Zr(()=>a(this.anchor)));if(W(this,wa).set(n,t),o){for(const[d,v]of W(this,La))d===t?n.unskip_effect(v):n.skip_effect(v);for(const[d,v]of W(this,la))d===t?n.unskip_effect(v.effect):n.skip_effect(v.effect);n.oncommit(W(this,No)),n.ondiscard(W(this,ss))}else W(this,No).call(this,n)}}wa=new WeakMap,La=new WeakMap,la=new WeakMap,Rn=new WeakMap,Io=new WeakMap,No=new WeakMap,ss=new WeakMap;function b(e,t,a=!1){var n=new fs(e),o=a?Wa:0;function l(s,d){n.ensure(s,d)}fo(()=>{var s=!1;t((d,v=0)=>{s=!0,l(v,d)}),s||l(-1,null)},o)}function Me(e,t){return t}function qu(e,t,a){for(var n=[],o=t.length,l,s=t.length,d=0;d<o;d++){let g=t[d];Dn(g,()=>{if(l){if(l.pending.delete(g),l.done.add(g),l.pending.size===0){var y=e.outrogroups;Bs(e,is(l.done)),y.delete(l),y.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var v=n.length===0&&a!==null;if(v){var m=a,x=m.parentNode;gu(x),x.append(m),e.items.clear()}Bs(e,t,!v)}else l={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(l)}function Bs(e,t,a=!0){var n;if(e.pending.size>0){n=new Set;for(const s of e.pending.values())for(const d of s)n.add(e.items.get(d).e)}for(var o=0;o<t.length;o++){var l=t[o];if(n!=null&&n.has(l)){l.f|=Oa;const s=document.createDocumentFragment();di(l,s)}else Dr(t[o],a)}}var Pi;function Te(e,t,a,n,o,l=null){var s=e,d=new Map,v=(t&cl)!==0;if(v){var m=e;s=m.appendChild(qa())}var x=null,g=ri(()=>{var H=a();return Xs(H)?H:H==null?[]:is(H)}),y,E=new Map,C=!0;function V(H){(N.effect.f&Da)===0&&(N.pending.delete(H),N.fallback=x,Bu(N,y,s,t,n),x!==null&&(y.length===0?(x.f&Oa)===0?li(x):(x.f^=Oa,$o(x,null,s)):Dn(x,()=>{x=null})))}function T(H){N.pending.delete(H)}var I=fo(()=>{y=r(g);for(var H=y.length,k=new Set,G=wt,he=Nl(),B=0;B<H;B+=1){var _=y[B],z=n(_,B),Y=C?null:d.get(z);Y?(Y.v&&io(Y.v,_),Y.i&&io(Y.i,B),he&&G.unskip_effect(Y.e)):(Y=Fu(d,C?s:Pi??(Pi=qa()),_,z,B,o,t,a),C||(Y.e.f|=Oa),d.set(z,Y)),k.add(z)}if(H===0&&l&&!x&&(C?x=Zr(()=>l(s)):(x=Zr(()=>l(Pi??(Pi=qa()))),x.f|=Oa)),H>k.size&&kc(),!C)if(E.set(G,k),he){for(const[J,P]of d)k.has(J)||G.skip_effect(P.e);G.oncommit(V),G.ondiscard(T)}else V(G);r(g)}),N={effect:I,items:d,pending:E,outrogroups:null,fallback:x};C=!1}function go(e){for(;e!==null&&(e.f&Ta)===0;)e=e.next;return e}function Bu(e,t,a,n,o){var Y,J,P,ye,O,U,F,me,xe;var l=(n&Lc)!==0,s=t.length,d=e.items,v=go(e.effect.first),m,x=null,g,y=[],E=[],C,V,T,I;if(l)for(I=0;I<s;I+=1)C=t[I],V=o(C,I),T=d.get(V).e,(T.f&Oa)===0&&((J=(Y=T.nodes)==null?void 0:Y.a)==null||J.measure(),(g??(g=new Set)).add(T));for(I=0;I<s;I+=1){if(C=t[I],V=o(C,I),T=d.get(V).e,e.outrogroups!==null)for(const le of e.outrogroups)le.pending.delete(T),le.done.delete(T);if((T.f&Oa)!==0)if(T.f^=Oa,T===v)$o(T,null,a);else{var N=x?x.next:v;T===e.effect.last&&(e.effect.last=T.prev),T.prev&&(T.prev.next=T.next),T.next&&(T.next.prev=T.prev),en(e,x,T),en(e,T,N),$o(T,N,a),x=T,y=[],E=[],v=go(x.next);continue}if((T.f&Gr)!==0&&(li(T),l&&((ye=(P=T.nodes)==null?void 0:P.a)==null||ye.unfix(),(g??(g=new Set)).delete(T))),T!==v){if(m!==void 0&&m.has(T)){if(y.length<E.length){var H=E[0],k;x=H.prev;var G=y[0],he=y[y.length-1];for(k=0;k<y.length;k+=1)$o(y[k],H,a);for(k=0;k<E.length;k+=1)m.delete(E[k]);en(e,G.prev,he.next),en(e,x,G),en(e,he,H),v=H,x=he,I-=1,y=[],E=[]}else m.delete(T),$o(T,v,a),en(e,T.prev,T.next),en(e,T,x===null?e.effect.first:x.next),en(e,x,T),x=T;continue}for(y=[],E=[];v!==null&&v!==T;)(m??(m=new Set)).add(v),E.push(v),v=go(v.next);if(v===null)continue}(T.f&Oa)===0&&y.push(T),x=T,v=go(T.next)}if(e.outrogroups!==null){for(const le of e.outrogroups)le.pending.size===0&&(Bs(e,is(le.done)),(O=e.outrogroups)==null||O.delete(le));e.outrogroups.size===0&&(e.outrogroups=null)}if(v!==null||m!==void 0){var B=[];if(m!==void 0)for(T of m)(T.f&Gr)===0&&B.push(T);for(;v!==null;)(v.f&Gr)===0&&v!==e.fallback&&B.push(v),v=go(v.next);var _=B.length;if(_>0){var z=(n&cl)!==0&&s===0?a:null;if(l){for(I=0;I<_;I+=1)(F=(U=B[I].nodes)==null?void 0:U.a)==null||F.measure();for(I=0;I<_;I+=1)(xe=(me=B[I].nodes)==null?void 0:me.a)==null||xe.fix()}qu(e,B,z)}}l&&Va(()=>{var le,te;if(g!==void 0)for(T of g)(te=(le=T.nodes)==null?void 0:le.a)==null||te.apply()})}function Fu(e,t,a,n,o,l,s,d){var v=(s&Nc)!==0?(s&Oc)===0?pu(a,!1,!1):xn(a):null,m=(s&Pc)!==0?xn(o):null;return{v,i:m,e:Zr(()=>(l(t,v??a,m??o,d),()=>{e.delete(n)}))}}function $o(e,t,a){if(e.nodes)for(var n=e.nodes.start,o=e.nodes.end,l=t&&(t.f&Oa)===0?t.nodes.start:a;n!==null;){var s=Ro(n);if(l.before(n),n===o)return;n=s}}function en(e,t,a){t===null?e.effect.first=a:t.next=a,a===null?e.effect.last=t:a.prev=t}function $a(e,t,a=!1,n=!1,o=!1){var l=e,s="";S(()=>{var d=Nt;if(s!==(s=t()??"")&&(d.nodes!==null&&(jl(d.nodes.start,d.nodes.end),d.nodes=null),s!=="")){var v=a?fl:n?Fc:void 0,m=ni(a?"svg":n?"math":"template",v);m.innerHTML=s;var x=a||n?m:m.content;if(Fn(Ga(x),x.lastChild),a||n)for(;Ga(x);)l.before(Ga(x));else l.before(x)}})}function et(e,t,a,n,o){var d;var l=(d=t.$$slots)==null?void 0:d[a],s=!1;l===!0&&(l=t.children,s=!0),l===void 0||l(e,s?()=>n:n)}function Fs(e,t,...a){var n=new fs(e);fo(()=>{const o=t()??null;n.ensure(o,o&&(l=>o(l,...a)))},Wa)}function ci(e,t,a){var n=new fs(e);fo(()=>{var o=t()??null;n.ensure(o,o&&(l=>a(l,o)))},Wa)}function Hu(e,t,a,n,o,l){var s=null,d=e,v=new fs(d,!1);fo(()=>{const m=t()||null;var x=fl;if(m===null){v.ensure(null,null);return}return v.ensure(m,g=>{if(m){if(s=ni(m,x),Fn(s,s),n){var y=s.appendChild(qa());n(s,y)}Nt.nodes.end=s,g.before(s)}}),()=>{}},Wa),us(()=>{})}function Uu(e,t){var a=void 0,n;Rl(()=>{a!==(a=t())&&(n&&(Dr(n),n=null),a&&(n=Zr(()=>{vs(()=>a(e))})))})}function ed(e){var t,a,n="";if(typeof e=="string"||typeof e=="number")n+=e;else if(typeof e=="object")if(Array.isArray(e)){var o=e.length;for(t=0;t<o;t++)e[t]&&(a=ed(e[t]))&&(n&&(n+=" "),n+=a)}else for(a in e)e[a]&&(n&&(n+=" "),n+=a);return n}function td(){for(var e,t,a=0,n="",o=arguments.length;a<o;a++)(e=arguments[a])&&(t=ed(e))&&(n&&(n+=" "),n+=t);return n}function Qt(e){return typeof e=="object"?td(e):e??""}const Li=[...` 	
\r\f \v\uFEFF`];function Ku(e,t,a){var n=e==null?"":""+e;if(t&&(n=n?n+" "+t:t),a){for(var o of Object.keys(a))if(a[o])n=n?n+" "+o:o;else if(n.length)for(var l=o.length,s=0;(s=n.indexOf(o,s))>=0;){var d=s+l;(s===0||Li.includes(n[s-1]))&&(d===n.length||Li.includes(n[d]))?n=(s===0?"":n.substring(0,s))+n.substring(d+1):s=d}}return n===""?null:n}function Oi(e,t=!1){var a=t?" !important;":";",n="";for(var o of Object.keys(e)){var l=e[o];l!=null&&l!==""&&(n+=" "+o+": "+l+a)}return n}function ys(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Gu(e,t){if(t){var a="",n,o;if(Array.isArray(t)?(n=t[0],o=t[1]):n=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var l=!1,s=0,d=!1,v=[];n&&v.push(...Object.keys(n).map(ys)),o&&v.push(...Object.keys(o).map(ys));var m=0,x=-1;const V=e.length;for(var g=0;g<V;g++){var y=e[g];if(d?y==="/"&&e[g-1]==="*"&&(d=!1):l?l===y&&(l=!1):y==="/"&&e[g+1]==="*"?d=!0:y==='"'||y==="'"?l=y:y==="("?s++:y===")"&&s--,!d&&l===!1&&s===0){if(y===":"&&x===-1)x=g;else if(y===";"||g===V-1){if(x!==-1){var E=ys(e.substring(m,x).trim());if(!v.includes(E)){y!==";"&&g++;var C=e.substring(m,g).trim();a+=" "+C+";"}}m=g+1,x=-1}}}}return n&&(a+=Oi(n)),o&&(a+=Oi(o,!0)),a=a.trim(),a===""?null:a}return e==null?null:String(e)}function qe(e,t,a,n,o,l){var s=e.__className;if(s!==a||s===void 0){var d=Ku(a,n,l);d==null?e.removeAttribute("class"):t?e.className=d:e.setAttribute("class",d),e.__className=a}else if(l&&o!==l)for(var v in l){var m=!!l[v];(o==null||m!==!!o[v])&&e.classList.toggle(v,m)}return l}function ws(e,t={},a,n){for(var o in a){var l=a[o];t[o]!==l&&(a[o]==null?e.style.removeProperty(o):e.style.setProperty(o,l,n))}}function Zo(e,t,a,n){var o=e.__style;if(o!==t){var l=Gu(t,n);l==null?e.removeAttribute("style"):e.style.cssText=l,e.__style=t}else n&&(Array.isArray(n)?(ws(e,a==null?void 0:a[0],n[0]),ws(e,a==null?void 0:a[1],n[1],"important")):ws(e,a,n));return n}function es(e,t,a=!1){if(e.multiple){if(t==null)return;if(!Xs(t))return Uc();for(var n of e.options)n.selected=t.includes(Mo(n));return}for(n of e.options){var o=Mo(n);if(xu(o,t)){n.selected=!0;return}}(!a||t!==void 0)&&(e.selectedIndex=-1)}function rd(e){var t=new MutationObserver(()=>{es(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),us(()=>{t.disconnect()})}function Ri(e,t,a=t){var n=new WeakSet,o=!0;Pl(e,"change",l=>{var s=l?"[selected]":":checked",d;if(e.multiple)d=[].map.call(e.querySelectorAll(s),Mo);else{var v=e.querySelector(s)??e.querySelector("option:not([disabled])");d=v&&Mo(v)}a(d),wt!==null&&n.add(wt)}),vs(()=>{var l=t();if(e===document.activeElement){var s=Xo??wt;if(n.has(s))return}if(es(e,l,o),o&&l===void 0){var d=e.querySelector(":checked");d!==null&&(l=Mo(d),a(l))}e.__value=l,o=!1}),rd(e)}function Mo(e){return"__value"in e?e.__value:e.value}const bo=Symbol("class"),_o=Symbol("style"),ad=Symbol("is custom element"),nd=Symbol("is html"),Wu=dl?"option":"OPTION",Yu=dl?"select":"SELECT";function Ju(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function Ca(e,t,a,n){var o=od(e);o[t]!==(o[t]=a)&&(t==="loading"&&(e[yc]=a),a==null?e.removeAttribute(t):typeof a!="string"&&sd(e).includes(t)?e[t]=a:e.setAttribute(t,a))}function Xu(e,t,a,n,o=!1,l=!1){var s=od(e),d=s[ad],v=!s[nd],m=t||{},x=e.nodeName===Wu;for(var g in t)g in a||(a[g]=null);a.class?a.class=Qt(a.class):a[bo]&&(a.class=null),a[_o]&&(a.style??(a.style=null));var y=sd(e);for(const k in a){let G=a[k];if(x&&k==="value"&&G==null){e.value=e.__value="",m[k]=G;continue}if(k==="class"){var E=e.namespaceURI==="http://www.w3.org/1999/xhtml";qe(e,E,G,n,t==null?void 0:t[bo],a[bo]),m[k]=G,m[bo]=a[bo];continue}if(k==="style"){Zo(e,G,t==null?void 0:t[_o],a[_o]),m[k]=G,m[_o]=a[_o];continue}var C=m[k];if(!(G===C&&!(G===void 0&&e.hasAttribute(k)))){m[k]=G;var V=k[0]+k[1];if(V!=="$$")if(V==="on"){const he={},B="$$"+k;let _=k.slice(2);var T=Au(_);if(Mu(_)&&(_=_.slice(0,-7),he.capture=!0),!T&&C){if(G!=null)continue;e.removeEventListener(_,m[B],he),m[B]=null}if(T)oe(_,e,G),Vr([_]);else if(G!=null){let z=function(Y){m[k].call(this,Y)};var H=z;m[B]=Ql(_,e,z,he)}}else if(k==="style")Ca(e,k,G);else if(k==="autofocus")bu(e,!!G);else if(!d&&(k==="__value"||k==="value"&&G!=null))e.value=e.__value=G;else if(k==="selected"&&x)Ju(e,G);else{var I=k;v||(I=Iu(I));var N=I==="defaultValue"||I==="defaultChecked";if(G==null&&!d&&!N)if(s[k]=null,I==="value"||I==="checked"){let he=e;const B=t===void 0;if(I==="value"){let _=he.defaultValue;he.removeAttribute(I),he.defaultValue=_,he.value=he.__value=B?_:null}else{let _=he.defaultChecked;he.removeAttribute(I),he.defaultChecked=_,he.checked=B?_:!1}}else e.removeAttribute(k);else N||y.includes(I)&&(d||typeof G!="string")?(e[I]=G,I in s&&(s[I]=Mr)):typeof G!="function"&&Ca(e,I,G)}}}return m}function ts(e,t,a=[],n=[],o=[],l,s=!1,d=!1){$l(o,a,n,v=>{var m=void 0,x={},g=e.nodeName===Yu,y=!1;if(Rl(()=>{var C=t(...v.map(r)),V=Xu(e,m,C,l,s,d);y&&g&&"value"in C&&es(e,C.value);for(let I of Object.getOwnPropertySymbols(x))C[I]||Dr(x[I]);for(let I of Object.getOwnPropertySymbols(C)){var T=C[I];I.description===Hc&&(!m||T!==m[I])&&(x[I]&&Dr(x[I]),x[I]=Zr(()=>Uu(e,()=>T))),V[I]=T}m=V}),g){var E=e;vs(()=>{es(E,m.value,!0),rd(E)})}y=!0})}function od(e){return e.__attributes??(e.__attributes={[ad]:e.nodeName.includes("-"),[nd]:e.namespaceURI===vl})}var Di=new Map;function sd(e){var t=e.getAttribute("is")||e.nodeName,a=Di.get(t);if(a)return a;Di.set(t,a=[]);for(var n,o=e,l=Element.prototype;l!==o;){n=ol(o);for(var s in n)n[s].set&&a.push(s);o=Qs(o)}return a}function Nn(e,t,a=t){var n=new WeakSet;Pl(e,"input",async o=>{var l=o?e.defaultValue:e.value;if(l=ks(e)?$s(l):l,a(l),wt!==null&&n.add(wt),await Wl(),l!==(l=t())){var s=e.selectionStart,d=e.selectionEnd,v=e.value.length;if(e.value=l??"",d!==null){var m=e.value.length;s===d&&d===v&&m>v?(e.selectionStart=m,e.selectionEnd=m):(e.selectionStart=s,e.selectionEnd=Math.min(d,m))}}}),Bn(t)==null&&e.value&&(a(ks(e)?$s(e.value):e.value),wt!==null&&n.add(wt)),si(()=>{var o=t();if(e===document.activeElement){var l=Xo??wt;if(n.has(l))return}ks(e)&&o===$s(e.value)||e.type==="date"&&!o&&!e.value||o!==e.value&&(e.value=o??"")})}function ks(e){var t=e.type;return t==="number"||t==="range"}function $s(e){return e===""?null:+e}function ji(e,t){return e===t||(e==null?void 0:e[ja])===t}function pn(e={},t,a,n){return vs(()=>{var o,l;return si(()=>{o=l,l=[],Bn(()=>{e!==a(...l)&&(t(e,...l),o&&ji(a(...o),e)&&t(null,...o))})}),()=>{Va(()=>{l&&ji(a(...l),e)&&t(null,...l)})}}),e}function Qu(e=!1){const t=Ar,a=t.l.u;if(!a)return;let n=()=>Tn(t.s);if(e){let o=0,l={};const s=Oo(()=>{let d=!1;const v=t.s;for(const m in v)v[m]!==l[m]&&(l[m]=v[m],d=!0);return d&&o++,o});n=()=>r(s)}a.b.length&&wu(()=>{Vi(t,n),Ms(a.b)}),$r(()=>{const o=Bn(()=>a.m.map(bc));return()=>{for(const l of o)typeof l=="function"&&l()}}),a.a.length&&$r(()=>{Vi(t,n),Ms(a.a)})}function Vi(e,t){if(e.l.s)for(const a of e.l.s)r(a);t()}let Fo=!1;function Zu(e){var t=Fo;try{return Fo=!1,[e(),Fo]}finally{Fo=t}}const ev={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function tv(e,t,a){return new Proxy({props:e,exclude:t},ev)}const rv={get(e,t){if(!e.exclude.includes(t))return r(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,a){if(!(t in e.special)){var n=Nt;try{xa(e.parent_effect),e.special[t]=je({get[t](){return e.props[t]}},t,ul)}finally{xa(n)}}return e.special[t](a),So(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),So(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Xe(e,t){return new Proxy({props:e,exclude:t,special:{},version:xn(0),parent_effect:Nt},rv)}const av={get(e,t){let a=e.props.length;for(;a--;){let n=e.props[a];if(ho(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n)return n[t]}},set(e,t,a){let n=e.props.length;for(;n--;){let o=e.props[n];ho(o)&&(o=o());const l=dn(o,t);if(l&&l.set)return l.set(a),!0}return!1},getOwnPropertyDescriptor(e,t){let a=e.props.length;for(;a--;){let n=e.props[a];if(ho(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n){const o=dn(n,t);return o&&!o.configurable&&(o.configurable=!0),o}}},has(e,t){if(t===ja||t===ll)return!1;for(let a of e.props)if(ho(a)&&(a=a()),a!=null&&t in a)return!0;return!1},ownKeys(e){const t=[];for(let a of e.props)if(ho(a)&&(a=a()),!!a){for(const n in a)t.includes(n)||t.push(n);for(const n of Object.getOwnPropertySymbols(a))t.includes(n)||t.push(n)}return t}};function nt(...e){return new Proxy({props:e},av)}function je(e,t,a,n){var H;var o=!Po||(a&Dc)!==0,l=(a&jc)!==0,s=(a&Vc)!==0,d=n,v=!0,m=()=>(v&&(v=!1,d=s?Bn(n):n),d),x;if(l){var g=ja in e||ll in e;x=((H=dn(e,t))==null?void 0:H.set)??(g&&t in e?k=>e[t]=k:void 0)}var y,E=!1;l?[y,E]=Zu(()=>e[t]):y=e[t],y===void 0&&n!==void 0&&(y=m(),x&&(o&&Mc(),x(y)));var C;if(o?C=()=>{var k=e[t];return k===void 0?m():(v=!0,k)}:C=()=>{var k=e[t];return k!==void 0&&(d=void 0),k===void 0?d:k},o&&(a&ul)===0)return C;if(x){var V=e.$$legacy;return(function(k,G){return arguments.length>0?((!o||!G||V||E)&&x(G?C():k),k):C()})}var T=!1,I=((a&Rc)!==0?Oo:ri)(()=>(T=!1,C()));l&&r(I);var N=Nt;return(function(k,G){if(arguments.length>0){const he=G?r(I):o&&l?Ut(k):k;return u(I,he),T=!0,d!==void 0&&(d=he),k}return hn&&T||(N.f&Da)!==0?I.v:r(I)})}const nv="5";var nl;typeof window<"u"&&((nl=window.__svelte??(window.__svelte={})).v??(nl.v=new Set)).add(nv);const qr="";async function ov(){const e=await fetch(`${qr}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function sv(e,t=null,a=null){const n={provider:e};t&&(n.model=t),a&&(n.api_key=a);const o=await fetch(`${qr}/api/provider/validate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)});if(!o.ok)throw new Error("설정 실패");return o.json()}async function iv(e){const t=await fetch(`${qr}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function lv(e,{onProgress:t,onDone:a,onError:n}){const o=new AbortController;return fetch(`${qr}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:o.signal}).then(async l=>{if(!l.ok){n==null||n("다운로드 실패");return}const s=l.body.getReader(),d=new TextDecoder;let v="";for(;;){const{done:m,value:x}=await s.read();if(m)break;v+=d.decode(x,{stream:!0});const g=v.split(`
`);v=g.pop()||"";for(const y of g)if(y.startsWith("data:"))try{const E=JSON.parse(y.slice(5).trim());E.total&&E.completed!==void 0?t==null||t({total:E.total,completed:E.completed,status:E.status}):E.status&&(t==null||t({status:E.status}))}catch{}}a==null||a()}).catch(l=>{l.name!=="AbortError"&&(n==null||n(l.message))}),{abort:()=>o.abort()}}async function dv(){const e=await fetch(`${qr}/api/codex/logout`,{method:"POST"});if(!e.ok)throw new Error("Codex 로그아웃 실패");return e.json()}async function cv(e,t=null,a=null){let n=`${qr}/api/export/excel/${encodeURIComponent(e)}`;const o=new URLSearchParams;a?o.set("template_id",a):t&&t.length>0&&o.set("modules",t.join(","));const l=o.toString();l&&(n+=`?${l}`);const s=await fetch(n);if(!s.ok){const y=await s.json().catch(()=>({}));throw new Error(y.detail||"Excel 다운로드 실패")}const d=await s.blob(),m=(s.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),x=m?decodeURIComponent(m[1]):`${e}.xlsx`,g=document.createElement("a");return g.href=URL.createObjectURL(d),g.download=x,g.click(),URL.revokeObjectURL(g.href),x}async function id(e){const t=await fetch(`${qr}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}async function uv(e,t){const a=await fetch(`${qr}/api/company/${e}/show/${encodeURIComponent(t)}/all`);if(!a.ok)throw new Error("company topic 일괄 조회 실패");return a.json()}async function vv(e){const t=await fetch(`${qr}/api/company/${e}/sections`);if(!t.ok)throw new Error("sections 조회 실패");return t.json()}async function fv(e){const t=await fetch(`${qr}/api/company/${e}/toc`);if(!t.ok)throw new Error("목차 조회 실패");return t.json()}async function pv(e,t,a=null){const n=a?`?period=${encodeURIComponent(a)}`:"",o=await fetch(`${qr}/api/company/${e}/viewer/${encodeURIComponent(t)}${n}`);if(!o.ok)throw new Error("viewer 조회 실패");return o.json()}async function mv(e,t){const a=await fetch(`${qr}/api/company/${e}/diff/${encodeURIComponent(t)}/summary`);if(!a.ok)throw new Error("diff summary 조회 실패");return a.json()}async function xv(e,t,a,n){const o=new URLSearchParams({from:a,to:n}),l=await fetch(`${qr}/api/company/${e}/diff/${encodeURIComponent(t)}?${o}`);if(!l.ok)throw new Error("topic diff 조회 실패");return l.json()}async function hv(e,t){const a=new URLSearchParams({q:t}),n=await fetch(`${qr}/api/company/${encodeURIComponent(e)}/search?${a}`);if(!n.ok)throw new Error("검색 실패");return n.json()}async function gv(e){const t=await fetch(`${qr}/api/company/${encodeURIComponent(e)}/insights`);if(!t.ok)throw new Error("인사이트 조회 실패");return t.json()}function bv(e,t,{onContext:a,onChunk:n,onDone:o,onError:l}){const s=new AbortController;return fetch(`${qr}/api/company/${encodeURIComponent(e)}/summary/${encodeURIComponent(t)}`,{signal:s.signal}).then(async d=>{if(!d.ok){l==null||l("요약 생성 실패");return}const v=d.body.getReader(),m=new TextDecoder;let x="",g=null;for(;;){const{done:y,value:E}=await v.read();if(y)break;x+=m.decode(E,{stream:!0});const C=x.split(`
`);x=C.pop()||"";for(const V of C)if(V.startsWith("event:"))g=V.slice(6).trim();else if(V.startsWith("data:")&&g){try{const T=JSON.parse(V.slice(5).trim());g==="context"?a==null||a(T):g==="chunk"?n==null||n(T.text):g==="error"?l==null||l(T.error):g==="done"&&(o==null||o())}catch{}g=null}}o==null||o()}).catch(d=>{d.name!=="AbortError"&&(l==null||l(d.message))}),{abort:()=>s.abort()}}function _v(e,t,a={},{onMeta:n,onSnapshot:o,onContext:l,onSystemPrompt:s,onToolCall:d,onToolResult:v,onChunk:m,onDone:x,onError:g,onViewerNavigate:y},E=null){const C={question:t,stream:!0,...a};e&&(C.company=e),E&&E.length>0&&(C.history=E);const V=new AbortController;return fetch(`${qr}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(C),signal:V.signal}).then(async T=>{if(!T.ok){const he=await T.json().catch(()=>({}));g==null||g(he.detail||"스트리밍 실패");return}const I=T.body.getReader(),N=new TextDecoder;let H="",k=!1,G=null;for(;;){const{done:he,value:B}=await I.read();if(he)break;H+=N.decode(B,{stream:!0});const _=H.split(`
`);H=_.pop()||"";for(const z of _)if(z.startsWith("event:"))G=z.slice(6).trim();else if(z.startsWith("data:")&&G){const Y=z.slice(5).trim();try{const J=JSON.parse(Y);G==="meta"?n==null||n(J):G==="snapshot"?o==null||o(J):G==="context"?l==null||l(J):G==="system_prompt"?s==null||s(J):G==="tool_call"?d==null||d(J):G==="tool_result"?v==null||v(J):G==="chunk"?m==null||m(J.text):G==="viewer_navigate"?y==null||y(J):G==="error"?g==null||g(J.error,J.action,J.detail):G==="done"&&(k||(k=!0,x==null||x()))}catch{}G=null}}k||(k=!0,x==null||x())}).catch(T=>{T.name!=="AbortError"&&(g==null||g(T.message))}),{abort:()=>V.abort()}}const yv=(e,t)=>{const a=new Array(e.length+t.length);for(let n=0;n<e.length;n++)a[n]=e[n];for(let n=0;n<t.length;n++)a[e.length+n]=t[n];return a},wv=(e,t)=>({classGroupId:e,validator:t}),ld=(e=new Map,t=null,a)=>({nextPart:e,validators:t,classGroupId:a}),rs="-",qi=[],kv="arbitrary..",$v=e=>{const t=Sv(e),{conflictingClassGroups:a,conflictingClassGroupModifiers:n}=e;return{getClassGroupId:s=>{if(s.startsWith("[")&&s.endsWith("]"))return Cv(s);const d=s.split(rs),v=d[0]===""&&d.length>1?1:0;return dd(d,v,t)},getConflictingClassGroupIds:(s,d)=>{if(d){const v=n[s],m=a[s];return v?m?yv(m,v):v:m||qi}return a[s]||qi}}},dd=(e,t,a)=>{if(e.length-t===0)return a.classGroupId;const o=e[t],l=a.nextPart.get(o);if(l){const m=dd(e,t+1,l);if(m)return m}const s=a.validators;if(s===null)return;const d=t===0?e.join(rs):e.slice(t).join(rs),v=s.length;for(let m=0;m<v;m++){const x=s[m];if(x.validator(d))return x.classGroupId}},Cv=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),a=t.indexOf(":"),n=t.slice(0,a);return n?kv+n:void 0})(),Sv=e=>{const{theme:t,classGroups:a}=e;return Tv(a,t)},Tv=(e,t)=>{const a=ld();for(const n in e){const o=e[n];ui(o,a,n,t)}return a},ui=(e,t,a,n)=>{const o=e.length;for(let l=0;l<o;l++){const s=e[l];Mv(s,t,a,n)}},Mv=(e,t,a,n)=>{if(typeof e=="string"){zv(e,t,a);return}if(typeof e=="function"){Av(e,t,a,n);return}Ev(e,t,a,n)},zv=(e,t,a)=>{const n=e===""?t:cd(t,e);n.classGroupId=a},Av=(e,t,a,n)=>{if(Iv(e)){ui(e(n),t,a,n);return}t.validators===null&&(t.validators=[]),t.validators.push(wv(a,e))},Ev=(e,t,a,n)=>{const o=Object.entries(e),l=o.length;for(let s=0;s<l;s++){const[d,v]=o[s];ui(v,cd(t,d),a,n)}},cd=(e,t)=>{let a=e;const n=t.split(rs),o=n.length;for(let l=0;l<o;l++){const s=n[l];let d=a.nextPart.get(s);d||(d=ld(),a.nextPart.set(s,d)),a=d}return a},Iv=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,Nv=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,a=Object.create(null),n=Object.create(null);const o=(l,s)=>{a[l]=s,t++,t>e&&(t=0,n=a,a=Object.create(null))};return{get(l){let s=a[l];if(s!==void 0)return s;if((s=n[l])!==void 0)return o(l,s),s},set(l,s){l in a?a[l]=s:o(l,s)}}},Hs="!",Bi=":",Pv=[],Fi=(e,t,a,n,o)=>({modifiers:e,hasImportantModifier:t,baseClassName:a,maybePostfixModifierPosition:n,isExternal:o}),Lv=e=>{const{prefix:t,experimentalParseClassName:a}=e;let n=o=>{const l=[];let s=0,d=0,v=0,m;const x=o.length;for(let V=0;V<x;V++){const T=o[V];if(s===0&&d===0){if(T===Bi){l.push(o.slice(v,V)),v=V+1;continue}if(T==="/"){m=V;continue}}T==="["?s++:T==="]"?s--:T==="("?d++:T===")"&&d--}const g=l.length===0?o:o.slice(v);let y=g,E=!1;g.endsWith(Hs)?(y=g.slice(0,-1),E=!0):g.startsWith(Hs)&&(y=g.slice(1),E=!0);const C=m&&m>v?m-v:void 0;return Fi(l,E,y,C)};if(t){const o=t+Bi,l=n;n=s=>s.startsWith(o)?l(s.slice(o.length)):Fi(Pv,!1,s,void 0,!0)}if(a){const o=n;n=l=>a({className:l,parseClassName:o})}return n},Ov=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((a,n)=>{t.set(a,1e6+n)}),a=>{const n=[];let o=[];for(let l=0;l<a.length;l++){const s=a[l],d=s[0]==="[",v=t.has(s);d||v?(o.length>0&&(o.sort(),n.push(...o),o=[]),n.push(s)):o.push(s)}return o.length>0&&(o.sort(),n.push(...o)),n}},Rv=e=>({cache:Nv(e.cacheSize),parseClassName:Lv(e),sortModifiers:Ov(e),...$v(e)}),Dv=/\s+/,jv=(e,t)=>{const{parseClassName:a,getClassGroupId:n,getConflictingClassGroupIds:o,sortModifiers:l}=t,s=[],d=e.trim().split(Dv);let v="";for(let m=d.length-1;m>=0;m-=1){const x=d[m],{isExternal:g,modifiers:y,hasImportantModifier:E,baseClassName:C,maybePostfixModifierPosition:V}=a(x);if(g){v=x+(v.length>0?" "+v:v);continue}let T=!!V,I=n(T?C.substring(0,V):C);if(!I){if(!T){v=x+(v.length>0?" "+v:v);continue}if(I=n(C),!I){v=x+(v.length>0?" "+v:v);continue}T=!1}const N=y.length===0?"":y.length===1?y[0]:l(y).join(":"),H=E?N+Hs:N,k=H+I;if(s.indexOf(k)>-1)continue;s.push(k);const G=o(I,T);for(let he=0;he<G.length;++he){const B=G[he];s.push(H+B)}v=x+(v.length>0?" "+v:v)}return v},Vv=(...e)=>{let t=0,a,n,o="";for(;t<e.length;)(a=e[t++])&&(n=ud(a))&&(o&&(o+=" "),o+=n);return o},ud=e=>{if(typeof e=="string")return e;let t,a="";for(let n=0;n<e.length;n++)e[n]&&(t=ud(e[n]))&&(a&&(a+=" "),a+=t);return a},qv=(e,...t)=>{let a,n,o,l;const s=v=>{const m=t.reduce((x,g)=>g(x),e());return a=Rv(m),n=a.cache.get,o=a.cache.set,l=d,d(v)},d=v=>{const m=n(v);if(m)return m;const x=jv(v,a);return o(v,x),x};return l=s,(...v)=>l(Vv(...v))},Bv=[],kr=e=>{const t=a=>a[e]||Bv;return t.isThemeGetter=!0,t},vd=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,fd=/^\((?:(\w[\w-]*):)?(.+)\)$/i,Fv=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,Hv=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,Uv=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,Kv=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,Gv=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,Wv=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,tn=e=>Fv.test(e),Ct=e=>!!e&&!Number.isNaN(Number(e)),rn=e=>!!e&&Number.isInteger(Number(e)),Cs=e=>e.endsWith("%")&&Ct(e.slice(0,-1)),Ha=e=>Hv.test(e),pd=()=>!0,Yv=e=>Uv.test(e)&&!Kv.test(e),vi=()=>!1,Jv=e=>Gv.test(e),Xv=e=>Wv.test(e),Qv=e=>!Pe(e)&&!De(e),Zv=e=>yn(e,hd,vi),Pe=e=>vd.test(e),Sn=e=>yn(e,gd,Yv),Hi=e=>yn(e,lf,Ct),ef=e=>yn(e,_d,pd),tf=e=>yn(e,bd,vi),Ui=e=>yn(e,md,vi),rf=e=>yn(e,xd,Xv),Ho=e=>yn(e,yd,Jv),De=e=>fd.test(e),yo=e=>Un(e,gd),af=e=>Un(e,bd),Ki=e=>Un(e,md),nf=e=>Un(e,hd),of=e=>Un(e,xd),Uo=e=>Un(e,yd,!0),sf=e=>Un(e,_d,!0),yn=(e,t,a)=>{const n=vd.exec(e);return n?n[1]?t(n[1]):a(n[2]):!1},Un=(e,t,a=!1)=>{const n=fd.exec(e);return n?n[1]?t(n[1]):a:!1},md=e=>e==="position"||e==="percentage",xd=e=>e==="image"||e==="url",hd=e=>e==="length"||e==="size"||e==="bg-size",gd=e=>e==="length",lf=e=>e==="number",bd=e=>e==="family-name",_d=e=>e==="number"||e==="weight",yd=e=>e==="shadow",df=()=>{const e=kr("color"),t=kr("font"),a=kr("text"),n=kr("font-weight"),o=kr("tracking"),l=kr("leading"),s=kr("breakpoint"),d=kr("container"),v=kr("spacing"),m=kr("radius"),x=kr("shadow"),g=kr("inset-shadow"),y=kr("text-shadow"),E=kr("drop-shadow"),C=kr("blur"),V=kr("perspective"),T=kr("aspect"),I=kr("ease"),N=kr("animate"),H=()=>["auto","avoid","all","avoid-page","page","left","right","column"],k=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],G=()=>[...k(),De,Pe],he=()=>["auto","hidden","clip","visible","scroll"],B=()=>["auto","contain","none"],_=()=>[De,Pe,v],z=()=>[tn,"full","auto",..._()],Y=()=>[rn,"none","subgrid",De,Pe],J=()=>["auto",{span:["full",rn,De,Pe]},rn,De,Pe],P=()=>[rn,"auto",De,Pe],ye=()=>["auto","min","max","fr",De,Pe],O=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],U=()=>["start","end","center","stretch","center-safe","end-safe"],F=()=>["auto",..._()],me=()=>[tn,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",..._()],xe=()=>[tn,"screen","full","dvw","lvw","svw","min","max","fit",..._()],le=()=>[tn,"screen","full","lh","dvh","lvh","svh","min","max","fit",..._()],te=()=>[e,De,Pe],Ie=()=>[...k(),Ki,Ui,{position:[De,Pe]}],de=()=>["no-repeat",{repeat:["","x","y","space","round"]}],R=()=>["auto","cover","contain",nf,Zv,{size:[De,Pe]}],ee=()=>[Cs,yo,Sn],Q=()=>["","none","full",m,De,Pe],q=()=>["",Ct,yo,Sn],ge=()=>["solid","dashed","dotted","double"],Le=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],Z=()=>[Ct,Cs,Ki,Ui],tt=()=>["","none",C,De,Pe],pt=()=>["none",Ct,De,Pe],dt=()=>["none",Ct,De,Pe],M=()=>[Ct,De,Pe],ce=()=>[tn,"full",..._()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Ha],breakpoint:[Ha],color:[pd],container:[Ha],"drop-shadow":[Ha],ease:["in","out","in-out"],font:[Qv],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Ha],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Ha],shadow:[Ha],spacing:["px",Ct],text:[Ha],"text-shadow":[Ha],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",tn,Pe,De,T]}],container:["container"],columns:[{columns:[Ct,Pe,De,d]}],"break-after":[{"break-after":H()}],"break-before":[{"break-before":H()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:G()}],overflow:[{overflow:he()}],"overflow-x":[{"overflow-x":he()}],"overflow-y":[{"overflow-y":he()}],overscroll:[{overscroll:B()}],"overscroll-x":[{"overscroll-x":B()}],"overscroll-y":[{"overscroll-y":B()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:z()}],"inset-x":[{"inset-x":z()}],"inset-y":[{"inset-y":z()}],start:[{"inset-s":z(),start:z()}],end:[{"inset-e":z(),end:z()}],"inset-bs":[{"inset-bs":z()}],"inset-be":[{"inset-be":z()}],top:[{top:z()}],right:[{right:z()}],bottom:[{bottom:z()}],left:[{left:z()}],visibility:["visible","invisible","collapse"],z:[{z:[rn,"auto",De,Pe]}],basis:[{basis:[tn,"full","auto",d,..._()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[Ct,tn,"auto","initial","none",Pe]}],grow:[{grow:["",Ct,De,Pe]}],shrink:[{shrink:["",Ct,De,Pe]}],order:[{order:[rn,"first","last","none",De,Pe]}],"grid-cols":[{"grid-cols":Y()}],"col-start-end":[{col:J()}],"col-start":[{"col-start":P()}],"col-end":[{"col-end":P()}],"grid-rows":[{"grid-rows":Y()}],"row-start-end":[{row:J()}],"row-start":[{"row-start":P()}],"row-end":[{"row-end":P()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":ye()}],"auto-rows":[{"auto-rows":ye()}],gap:[{gap:_()}],"gap-x":[{"gap-x":_()}],"gap-y":[{"gap-y":_()}],"justify-content":[{justify:[...O(),"normal"]}],"justify-items":[{"justify-items":[...U(),"normal"]}],"justify-self":[{"justify-self":["auto",...U()]}],"align-content":[{content:["normal",...O()]}],"align-items":[{items:[...U(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...U(),{baseline:["","last"]}]}],"place-content":[{"place-content":O()}],"place-items":[{"place-items":[...U(),"baseline"]}],"place-self":[{"place-self":["auto",...U()]}],p:[{p:_()}],px:[{px:_()}],py:[{py:_()}],ps:[{ps:_()}],pe:[{pe:_()}],pbs:[{pbs:_()}],pbe:[{pbe:_()}],pt:[{pt:_()}],pr:[{pr:_()}],pb:[{pb:_()}],pl:[{pl:_()}],m:[{m:F()}],mx:[{mx:F()}],my:[{my:F()}],ms:[{ms:F()}],me:[{me:F()}],mbs:[{mbs:F()}],mbe:[{mbe:F()}],mt:[{mt:F()}],mr:[{mr:F()}],mb:[{mb:F()}],ml:[{ml:F()}],"space-x":[{"space-x":_()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":_()}],"space-y-reverse":["space-y-reverse"],size:[{size:me()}],"inline-size":[{inline:["auto",...xe()]}],"min-inline-size":[{"min-inline":["auto",...xe()]}],"max-inline-size":[{"max-inline":["none",...xe()]}],"block-size":[{block:["auto",...le()]}],"min-block-size":[{"min-block":["auto",...le()]}],"max-block-size":[{"max-block":["none",...le()]}],w:[{w:[d,"screen",...me()]}],"min-w":[{"min-w":[d,"screen","none",...me()]}],"max-w":[{"max-w":[d,"screen","none","prose",{screen:[s]},...me()]}],h:[{h:["screen","lh",...me()]}],"min-h":[{"min-h":["screen","lh","none",...me()]}],"max-h":[{"max-h":["screen","lh",...me()]}],"font-size":[{text:["base",a,yo,Sn]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[n,sf,ef]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",Cs,Pe]}],"font-family":[{font:[af,tf,t]}],"font-features":[{"font-features":[Pe]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[o,De,Pe]}],"line-clamp":[{"line-clamp":[Ct,"none",De,Hi]}],leading:[{leading:[l,..._()]}],"list-image":[{"list-image":["none",De,Pe]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",De,Pe]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:te()}],"text-color":[{text:te()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...ge(),"wavy"]}],"text-decoration-thickness":[{decoration:[Ct,"from-font","auto",De,Sn]}],"text-decoration-color":[{decoration:te()}],"underline-offset":[{"underline-offset":[Ct,"auto",De,Pe]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:_()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",De,Pe]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",De,Pe]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:Ie()}],"bg-repeat":[{bg:de()}],"bg-size":[{bg:R()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},rn,De,Pe],radial:["",De,Pe],conic:[rn,De,Pe]},of,rf]}],"bg-color":[{bg:te()}],"gradient-from-pos":[{from:ee()}],"gradient-via-pos":[{via:ee()}],"gradient-to-pos":[{to:ee()}],"gradient-from":[{from:te()}],"gradient-via":[{via:te()}],"gradient-to":[{to:te()}],rounded:[{rounded:Q()}],"rounded-s":[{"rounded-s":Q()}],"rounded-e":[{"rounded-e":Q()}],"rounded-t":[{"rounded-t":Q()}],"rounded-r":[{"rounded-r":Q()}],"rounded-b":[{"rounded-b":Q()}],"rounded-l":[{"rounded-l":Q()}],"rounded-ss":[{"rounded-ss":Q()}],"rounded-se":[{"rounded-se":Q()}],"rounded-ee":[{"rounded-ee":Q()}],"rounded-es":[{"rounded-es":Q()}],"rounded-tl":[{"rounded-tl":Q()}],"rounded-tr":[{"rounded-tr":Q()}],"rounded-br":[{"rounded-br":Q()}],"rounded-bl":[{"rounded-bl":Q()}],"border-w":[{border:q()}],"border-w-x":[{"border-x":q()}],"border-w-y":[{"border-y":q()}],"border-w-s":[{"border-s":q()}],"border-w-e":[{"border-e":q()}],"border-w-bs":[{"border-bs":q()}],"border-w-be":[{"border-be":q()}],"border-w-t":[{"border-t":q()}],"border-w-r":[{"border-r":q()}],"border-w-b":[{"border-b":q()}],"border-w-l":[{"border-l":q()}],"divide-x":[{"divide-x":q()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":q()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...ge(),"hidden","none"]}],"divide-style":[{divide:[...ge(),"hidden","none"]}],"border-color":[{border:te()}],"border-color-x":[{"border-x":te()}],"border-color-y":[{"border-y":te()}],"border-color-s":[{"border-s":te()}],"border-color-e":[{"border-e":te()}],"border-color-bs":[{"border-bs":te()}],"border-color-be":[{"border-be":te()}],"border-color-t":[{"border-t":te()}],"border-color-r":[{"border-r":te()}],"border-color-b":[{"border-b":te()}],"border-color-l":[{"border-l":te()}],"divide-color":[{divide:te()}],"outline-style":[{outline:[...ge(),"none","hidden"]}],"outline-offset":[{"outline-offset":[Ct,De,Pe]}],"outline-w":[{outline:["",Ct,yo,Sn]}],"outline-color":[{outline:te()}],shadow:[{shadow:["","none",x,Uo,Ho]}],"shadow-color":[{shadow:te()}],"inset-shadow":[{"inset-shadow":["none",g,Uo,Ho]}],"inset-shadow-color":[{"inset-shadow":te()}],"ring-w":[{ring:q()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:te()}],"ring-offset-w":[{"ring-offset":[Ct,Sn]}],"ring-offset-color":[{"ring-offset":te()}],"inset-ring-w":[{"inset-ring":q()}],"inset-ring-color":[{"inset-ring":te()}],"text-shadow":[{"text-shadow":["none",y,Uo,Ho]}],"text-shadow-color":[{"text-shadow":te()}],opacity:[{opacity:[Ct,De,Pe]}],"mix-blend":[{"mix-blend":[...Le(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":Le()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[Ct]}],"mask-image-linear-from-pos":[{"mask-linear-from":Z()}],"mask-image-linear-to-pos":[{"mask-linear-to":Z()}],"mask-image-linear-from-color":[{"mask-linear-from":te()}],"mask-image-linear-to-color":[{"mask-linear-to":te()}],"mask-image-t-from-pos":[{"mask-t-from":Z()}],"mask-image-t-to-pos":[{"mask-t-to":Z()}],"mask-image-t-from-color":[{"mask-t-from":te()}],"mask-image-t-to-color":[{"mask-t-to":te()}],"mask-image-r-from-pos":[{"mask-r-from":Z()}],"mask-image-r-to-pos":[{"mask-r-to":Z()}],"mask-image-r-from-color":[{"mask-r-from":te()}],"mask-image-r-to-color":[{"mask-r-to":te()}],"mask-image-b-from-pos":[{"mask-b-from":Z()}],"mask-image-b-to-pos":[{"mask-b-to":Z()}],"mask-image-b-from-color":[{"mask-b-from":te()}],"mask-image-b-to-color":[{"mask-b-to":te()}],"mask-image-l-from-pos":[{"mask-l-from":Z()}],"mask-image-l-to-pos":[{"mask-l-to":Z()}],"mask-image-l-from-color":[{"mask-l-from":te()}],"mask-image-l-to-color":[{"mask-l-to":te()}],"mask-image-x-from-pos":[{"mask-x-from":Z()}],"mask-image-x-to-pos":[{"mask-x-to":Z()}],"mask-image-x-from-color":[{"mask-x-from":te()}],"mask-image-x-to-color":[{"mask-x-to":te()}],"mask-image-y-from-pos":[{"mask-y-from":Z()}],"mask-image-y-to-pos":[{"mask-y-to":Z()}],"mask-image-y-from-color":[{"mask-y-from":te()}],"mask-image-y-to-color":[{"mask-y-to":te()}],"mask-image-radial":[{"mask-radial":[De,Pe]}],"mask-image-radial-from-pos":[{"mask-radial-from":Z()}],"mask-image-radial-to-pos":[{"mask-radial-to":Z()}],"mask-image-radial-from-color":[{"mask-radial-from":te()}],"mask-image-radial-to-color":[{"mask-radial-to":te()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":k()}],"mask-image-conic-pos":[{"mask-conic":[Ct]}],"mask-image-conic-from-pos":[{"mask-conic-from":Z()}],"mask-image-conic-to-pos":[{"mask-conic-to":Z()}],"mask-image-conic-from-color":[{"mask-conic-from":te()}],"mask-image-conic-to-color":[{"mask-conic-to":te()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:Ie()}],"mask-repeat":[{mask:de()}],"mask-size":[{mask:R()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",De,Pe]}],filter:[{filter:["","none",De,Pe]}],blur:[{blur:tt()}],brightness:[{brightness:[Ct,De,Pe]}],contrast:[{contrast:[Ct,De,Pe]}],"drop-shadow":[{"drop-shadow":["","none",E,Uo,Ho]}],"drop-shadow-color":[{"drop-shadow":te()}],grayscale:[{grayscale:["",Ct,De,Pe]}],"hue-rotate":[{"hue-rotate":[Ct,De,Pe]}],invert:[{invert:["",Ct,De,Pe]}],saturate:[{saturate:[Ct,De,Pe]}],sepia:[{sepia:["",Ct,De,Pe]}],"backdrop-filter":[{"backdrop-filter":["","none",De,Pe]}],"backdrop-blur":[{"backdrop-blur":tt()}],"backdrop-brightness":[{"backdrop-brightness":[Ct,De,Pe]}],"backdrop-contrast":[{"backdrop-contrast":[Ct,De,Pe]}],"backdrop-grayscale":[{"backdrop-grayscale":["",Ct,De,Pe]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[Ct,De,Pe]}],"backdrop-invert":[{"backdrop-invert":["",Ct,De,Pe]}],"backdrop-opacity":[{"backdrop-opacity":[Ct,De,Pe]}],"backdrop-saturate":[{"backdrop-saturate":[Ct,De,Pe]}],"backdrop-sepia":[{"backdrop-sepia":["",Ct,De,Pe]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":_()}],"border-spacing-x":[{"border-spacing-x":_()}],"border-spacing-y":[{"border-spacing-y":_()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",De,Pe]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[Ct,"initial",De,Pe]}],ease:[{ease:["linear","initial",I,De,Pe]}],delay:[{delay:[Ct,De,Pe]}],animate:[{animate:["none",N,De,Pe]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[V,De,Pe]}],"perspective-origin":[{"perspective-origin":G()}],rotate:[{rotate:pt()}],"rotate-x":[{"rotate-x":pt()}],"rotate-y":[{"rotate-y":pt()}],"rotate-z":[{"rotate-z":pt()}],scale:[{scale:dt()}],"scale-x":[{"scale-x":dt()}],"scale-y":[{"scale-y":dt()}],"scale-z":[{"scale-z":dt()}],"scale-3d":["scale-3d"],skew:[{skew:M()}],"skew-x":[{"skew-x":M()}],"skew-y":[{"skew-y":M()}],transform:[{transform:[De,Pe,"","none","gpu","cpu"]}],"transform-origin":[{origin:G()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:ce()}],"translate-x":[{"translate-x":ce()}],"translate-y":[{"translate-y":ce()}],"translate-z":[{"translate-z":ce()}],"translate-none":["translate-none"],accent:[{accent:te()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:te()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",De,Pe]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":_()}],"scroll-mx":[{"scroll-mx":_()}],"scroll-my":[{"scroll-my":_()}],"scroll-ms":[{"scroll-ms":_()}],"scroll-me":[{"scroll-me":_()}],"scroll-mbs":[{"scroll-mbs":_()}],"scroll-mbe":[{"scroll-mbe":_()}],"scroll-mt":[{"scroll-mt":_()}],"scroll-mr":[{"scroll-mr":_()}],"scroll-mb":[{"scroll-mb":_()}],"scroll-ml":[{"scroll-ml":_()}],"scroll-p":[{"scroll-p":_()}],"scroll-px":[{"scroll-px":_()}],"scroll-py":[{"scroll-py":_()}],"scroll-ps":[{"scroll-ps":_()}],"scroll-pe":[{"scroll-pe":_()}],"scroll-pbs":[{"scroll-pbs":_()}],"scroll-pbe":[{"scroll-pbe":_()}],"scroll-pt":[{"scroll-pt":_()}],"scroll-pr":[{"scroll-pr":_()}],"scroll-pb":[{"scroll-pb":_()}],"scroll-pl":[{"scroll-pl":_()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",De,Pe]}],fill:[{fill:["none",...te()]}],"stroke-w":[{stroke:[Ct,yo,Sn,Hi]}],stroke:[{stroke:["none",...te()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},cf=qv(df);function rr(...e){return cf(td(e))}const Us="dartlab-conversations",Gi=50;function uf(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function vf(){try{const e=localStorage.getItem(Us);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const ff=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function Wi(e){return e.map(t=>({...t,messages:t.messages.map(a=>{if(a.role!=="assistant")return a;const n={};for(const[o,l]of Object.entries(a))ff.includes(o)||(n[o]=l);return n})}))}function Yi(e){try{const t={conversations:Wi(e.conversations),activeId:e.activeId};localStorage.setItem(Us,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:Wi(e.conversations),activeId:e.activeId};localStorage.setItem(Us,JSON.stringify(t))}catch{}}}}function pf(){const e=vf(),t=e.conversations||[],a=t.find(I=>I.id===e.activeId)?e.activeId:null;let n=X(Ut(t)),o=X(Ut(a)),l=null;function s(){l&&clearTimeout(l),l=setTimeout(()=>{Yi({conversations:r(n),activeId:r(o)}),l=null},300)}function d(){l&&clearTimeout(l),l=null,Yi({conversations:r(n),activeId:r(o)})}function v(){return r(n).find(I=>I.id===r(o))||null}function m(){const I={id:uf(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return u(n,[I,...r(n)],!0),r(n).length>Gi&&u(n,r(n).slice(0,Gi),!0),u(o,I.id,!0),d(),I.id}function x(I){r(n).find(N=>N.id===I)&&(u(o,I,!0),d())}function g(I,N,H=null){const k=v();if(!k)return;const G={role:I,text:N};H&&(G.meta=H),k.messages=[...k.messages,G],k.updatedAt=Date.now(),k.title==="새 대화"&&I==="user"&&(k.title=N.length>30?N.slice(0,30)+"...":N),u(n,[...r(n)],!0),d()}function y(I){const N=v();if(!N||N.messages.length===0)return;const H=N.messages[N.messages.length-1];Object.assign(H,I),N.updatedAt=Date.now(),u(n,[...r(n)],!0),s()}function E(I){u(n,r(n).filter(N=>N.id!==I),!0),r(o)===I&&u(o,r(n).length>0?r(n)[0].id:null,!0),d()}function C(){const I=v();!I||I.messages.length===0||(I.messages=I.messages.slice(0,-1),I.updatedAt=Date.now(),u(n,[...r(n)],!0),d())}function V(I,N){const H=r(n).find(k=>k.id===I);H&&(H.title=N,u(n,[...r(n)],!0),d())}function T(){u(n,[],!0),u(o,null),d()}return{get conversations(){return r(n)},get activeId(){return r(o)},get active(){return v()},createConversation:m,setActive:x,addMessage:g,updateLastMessage:y,removeLastMessage:C,deleteConversation:E,updateTitle:V,clearAll:T,flush:d}}const wd="dartlab-workspace",mf=6;function kd(){return typeof window<"u"&&typeof localStorage<"u"}function xf(){if(!kd())return{};try{const e=localStorage.getItem(wd);return e?JSON.parse(e):{}}catch{return{}}}function hf(e){kd()&&localStorage.setItem(wd,JSON.stringify(e))}function gf(){const e=xf();let t=X("chat"),a=X(!1),n=X(null),o=X(null),l=X("explore"),s=X(null),d=X(null),v=X(null),m=X(null),x=X(Ut(e.selectedCompany||null)),g=X(Ut(e.recentCompanies||[]));function y(){hf({selectedCompany:r(x),recentCompanies:r(g)})}function E(z){if(!(z!=null&&z.stockCode))return;const Y={stockCode:z.stockCode,corpName:z.corpName||z.company||z.stockCode,company:z.company||z.corpName||z.stockCode,market:z.market||""};u(g,[Y,...r(g).filter(J=>J.stockCode!==Y.stockCode)].slice(0,mf),!0)}function C(z){u(t,z,!0)}function V(z){z&&(u(x,z,!0),E(z)),u(t,"viewer"),u(a,!1),y()}function T(z){u(n,"data"),u(o,z,!0),u(a,!0),B("explore")}function I(){u(a,!1)}function N(z){u(x,z,!0),z&&E(z),y()}function H(z,Y){var J,P,ye,O;!(z!=null&&z.company)&&!(z!=null&&z.stockCode)||(u(x,{...r(x)||{},...Y||{},corpName:z.company||((J=r(x))==null?void 0:J.corpName)||(Y==null?void 0:Y.corpName)||(Y==null?void 0:Y.company),company:z.company||((P=r(x))==null?void 0:P.company)||(Y==null?void 0:Y.company)||(Y==null?void 0:Y.corpName),stockCode:z.stockCode||((ye=r(x))==null?void 0:ye.stockCode)||(Y==null?void 0:Y.stockCode),market:((O=r(x))==null?void 0:O.market)||(Y==null?void 0:Y.market)||""},!0),E(r(x)),y())}function k(z,Y){u(v,z,!0),u(m,Y||z,!0)}function G(z,Y=null){u(n,"data"),u(a,!0),u(l,"evidence"),u(s,z,!0),u(d,Number.isInteger(Y)?Y:null,!0)}function he(){u(s,null),u(d,null)}function B(z){u(l,z||"explore",!0),r(l)!=="evidence"&&he()}function _(){return r(t)==="viewer"&&r(x)&&r(v)?{type:"viewer",company:r(x),topic:r(v),topicLabel:r(m)}:r(a)?r(n)==="viewer"&&r(x)?{type:"viewer",company:r(x),topic:r(v),topicLabel:r(m)}:r(n)==="data"&&r(o)?{type:"data",data:r(o)}:null:null}return{get activeView(){return r(t)},get panelOpen(){return r(a)},get panelMode(){return r(n)},get panelData(){return r(o)},get activeTab(){return r(l)},get activeEvidenceSection(){return r(s)},get selectedEvidenceIndex(){return r(d)},get selectedCompany(){return r(x)},get recentCompanies(){return r(g)},get viewerTopic(){return r(v)},get viewerTopicLabel(){return r(m)},switchView:C,openViewer:V,openData:T,openEvidence:G,closePanel:I,selectCompany:N,setViewerTopic:k,clearEvidenceSelection:he,setTab:B,syncCompanyFromMessage:H,getViewContext:_}}function bf(){try{const e=localStorage.getItem("dartlab-bookmarks");return e?JSON.parse(e):{}}catch{return{}}}function _f(e){try{localStorage.setItem("dartlab-bookmarks",JSON.stringify(e))}catch{}}function yf(){let e=X(null),t=X(null),a=X(null),n=X(!1),o=X(null),l=X(null),s=X(Ut(new Set)),d=X(null),v=X(!1),m=X(null),x=new Map,g=X(null),y=X(!1),E=X(Ut(new Map)),C=X(Ut(bf()));async function V(_){var z,Y;if(!(_===r(e)&&r(a))){u(e,_,!0),u(t,null),u(a,null),u(o,null),u(l,null),u(d,null),u(m,null),x=new Map,u(s,new Set,!0),u(g,null),u(E,new Map,!0),u(n,!0);try{const J=await fv(_);if(u(a,J,!0),u(t,J.corpName,!0),((z=J.chapters)==null?void 0:z.length)>0&&(u(s,new Set([J.chapters[0].chapter]),!0),((Y=J.chapters[0].topics)==null?void 0:Y.length)>0)){const P=J.chapters[0].topics[0];await I(P.topic,J.chapters[0].chapter)}T(_)}catch(J){console.error("TOC 로드 실패:",J)}u(n,!1)}}async function T(_){var z;if(((z=r(g))==null?void 0:z.stockCode)!==_){u(y,!0);try{const Y=await gv(_);Y.available?u(g,Y,!0):u(g,null)}catch{u(g,null)}u(y,!1)}}async function I(_,z){if(_!==r(o)){if(u(o,_,!0),u(l,z,!0),z&&!r(s).has(z)&&u(s,new Set([...r(s),z]),!0),x.has(_)){u(d,x.get(_),!0);return}u(v,!0),u(d,null),u(m,null);try{const[Y,J]=await Promise.allSettled([pv(r(e),_),mv(r(e),_)]);Y.status==="fulfilled"&&(u(d,Y.value,!0),x.set(_,Y.value)),J.status==="fulfilled"&&u(m,J.value,!0)}catch(Y){console.error("Topic 로드 실패:",Y)}u(v,!1)}}function N(_){const z=new Set(r(s));z.has(_)?z.delete(_):z.add(_),u(s,z,!0)}function H(_){return r(E).get(_)??null}function k(_,z){const Y=new Map(r(E));Y.set(_,z),u(E,Y,!0)}function G(){return r(C)[r(e)]||[]}function he(_){return(r(C)[r(e)]||[]).includes(_)}function B(_){const z=r(C)[r(e)]||[],Y=z.includes(_)?z.filter(J=>J!==_):[_,...z];u(C,{...r(C),[r(e)]:Y},!0),_f(r(C))}return{get stockCode(){return r(e)},get corpName(){return r(t)},get toc(){return r(a)},get tocLoading(){return r(n)},get selectedTopic(){return r(o)},get selectedChapter(){return r(l)},get expandedChapters(){return r(s)},get topicData(){return r(d)},get topicLoading(){return r(v)},get diffSummary(){return r(m)},get insightData(){return r(g)},get insightLoading(){return r(y)},loadCompany:V,selectTopic:I,toggleChapter:N,getTopicSummary:H,setTopicSummary:k,getBookmarks:G,isBookmarked:he,toggleBookmark:B}}var wf=f("<a><!></a>"),kf=f("<button><!></button>");function $f(e,t){br(t,!0);let a=je(t,"variant",3,"default"),n=je(t,"size",3,"default"),o=tv(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const l={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},s={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var d=ke(),v=re(d);{var m=g=>{var y=wf();ts(y,C=>({class:C,...o}),[()=>rr("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",l[a()],s[n()],t.class)]);var E=i(y);Fs(E,()=>t.children),c(g,y)},x=g=>{var y=kf();ts(y,C=>({class:C,...o}),[()=>rr("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",l[a()],s[n()],t.class)]);var E=i(y);Fs(E,()=>t.children),c(g,y)};b(v,g=>{t.href?g(m):g(x,-1)})}c(e,d),_r()}Yc();/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Cf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Sf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Ji=(...e)=>e.filter((t,a,n)=>!!t&&t.trim()!==""&&n.indexOf(t)===a).join(" ").trim();var Tf=Ru("<svg><!><!></svg>");function ot(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]),n=Xe(a,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);br(t,!1);let o=je(t,"name",8,void 0),l=je(t,"color",8,"currentColor"),s=je(t,"size",8,24),d=je(t,"strokeWidth",8,2),v=je(t,"absoluteStrokeWidth",8,!1),m=je(t,"iconNode",24,()=>[]);Qu();var x=Tf();ts(x,(E,C,V)=>({...Cf,...E,...n,width:s(),height:s(),stroke:l(),"stroke-width":C,class:V}),[()=>Sf(n)?void 0:{"aria-hidden":"true"},()=>(Tn(v()),Tn(d()),Tn(s()),Bn(()=>v()?Number(d())*24/Number(s()):d())),()=>(Tn(Ji),Tn(o()),Tn(a),Bn(()=>Ji("lucide-icon","lucide",o()?`lucide-${o()}`:"",a.class)))]);var g=i(x);Te(g,1,m,Me,(E,C)=>{var V=D(()=>Zs(r(C),2));let T=()=>r(V)[0],I=()=>r(V)[1];var N=ke(),H=re(N);Hu(H,T,!0,(k,G)=>{ts(k,()=>({...I()}))}),c(E,N)});var y=p(g);et(y,t,"default",{}),c(e,x),_r()}function Mf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];ot(e,nt({name:"activity"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function $d(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M8 3 4 7l4 4"}],["path",{d:"M4 7h16"}],["path",{d:"m16 21 4-4-4-4"}],["path",{d:"M20 17H4"}]];ot(e,nt({name:"arrow-left-right"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function zf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M5 12h14"}],["path",{d:"m12 5 7 7-7 7"}]];ot(e,nt({name:"arrow-right"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Af(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];ot(e,nt({name:"arrow-up"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ks(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 7v14"}],["path",{d:"M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"}]];ot(e,nt({name:"book-open"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ss(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];ot(e,nt({name:"brain"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Cd(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]];ot(e,nt({name:"chart-column"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Gs(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M20 6 9 17l-5-5"}]];ot(e,nt({name:"check"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Sd(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m6 9 6 6 6-6"}]];ot(e,nt({name:"chevron-down"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ef(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m18 15-6-6-6 6"}]];ot(e,nt({name:"chevron-up"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Td(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m9 18 6-6-6-6"}]];ot(e,nt({name:"chevron-right"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Mn(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];ot(e,nt({name:"circle-alert"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function zo(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];ot(e,nt({name:"circle-check"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function as(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];ot(e,nt({name:"clock"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function If(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];ot(e,nt({name:"code"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Nf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];ot(e,nt({name:"coffee"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Xi(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]];ot(e,nt({name:"copy"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function wo(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];ot(e,nt({name:"database"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ao(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];ot(e,nt({name:"download"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Pf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["line",{x1:"5",x2:"19",y1:"9",y2:"9"}],["line",{x1:"5",x2:"19",y1:"15",y2:"15"}]];ot(e,nt({name:"equal"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Qi(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];ot(e,nt({name:"external-link"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Lf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];ot(e,nt({name:"eye"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function da(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];ot(e,nt({name:"file-text"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Of(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];ot(e,nt({name:"github"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Zi(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];ot(e,nt({name:"key"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Rf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 8h.01"}],["path",{d:"M12 12h.01"}],["path",{d:"M14 8h.01"}],["path",{d:"M16 12h.01"}],["path",{d:"M18 8h.01"}],["path",{d:"M6 8h.01"}],["path",{d:"M7 16h10"}],["path",{d:"M8 12h.01"}],["rect",{width:"20",height:"16",x:"2",y:"4",rx:"2"}]];ot(e,nt({name:"keyboard"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function zr(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];ot(e,nt({name:"loader-circle"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Df(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];ot(e,nt({name:"log-out"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Md(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 3h6v6"}],["path",{d:"m21 3-7 7"}],["path",{d:"m3 21 7-7"}],["path",{d:"M9 21H3v-6"}]];ot(e,nt({name:"maximize-2"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function jf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];ot(e,nt({name:"menu"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function ns(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];ot(e,nt({name:"message-square"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function zd(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m14 10 7-7"}],["path",{d:"M20 10h-6V4"}],["path",{d:"m3 21 7-7"}],["path",{d:"M4 14h6v6"}]];ot(e,nt({name:"minimize-2"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ad(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M5 12h14"}]];ot(e,nt({name:"minus"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Vf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];ot(e,nt({name:"panel-left-close"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ws(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];ot(e,nt({name:"plus"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function qf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];ot(e,nt({name:"refresh-cw"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function mn(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];ot(e,nt({name:"search"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Bf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];ot(e,nt({name:"settings"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ff(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"}]];ot(e,nt({name:"shield"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ed(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];ot(e,nt({name:"sparkles"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Hf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];ot(e,nt({name:"square"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Ys(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"}]];ot(e,nt({name:"star"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Uf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];ot(e,nt({name:"table-2"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Kf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];ot(e,nt({name:"terminal"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Gf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];ot(e,nt({name:"trash-2"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Yo(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M16 7h6v6"}],["path",{d:"m22 7-8.5 8.5-5-5L2 17"}]];ot(e,nt({name:"trending-up"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Jo(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];ot(e,nt({name:"triangle-alert"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Wf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["path",{d:"M16 3.128a4 4 0 0 1 0 7.744"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87"}],["circle",{cx:"9",cy:"7",r:"4"}]];ot(e,nt({name:"users"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function Yf(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"}],["path",{d:"M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"}]];ot(e,nt({name:"wallet"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function el(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];ot(e,nt({name:"wrench"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}function gn(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];ot(e,nt({name:"x"},()=>a,{get iconNode(){return n},children:(o,l)=>{var s=ke(),d=re(s);et(d,t,"default",{}),c(o,s)},$$slots:{default:!0}}))}var Jf=f("<!> 새 대화",1),Xf=f('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),Qf=f('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),Zf=f('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),ep=f('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40"><span class="text-[10px] text-dl-text-dim font-mono"> </span></div>'),tp=f('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),rp=f("<button><!></button>"),ap=f('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),np=f("<aside><!></aside>");function op(e,t){br(t,!0);let a=je(t,"conversations",19,()=>[]),n=je(t,"activeId",3,null),o=je(t,"open",3,!0),l=je(t,"version",3,""),s=X("");function d(C){const V=new Date().setHours(0,0,0,0),T=V-864e5,I=V-7*864e5,N={오늘:[],어제:[],"이번 주":[],이전:[]};for(const k of C)k.updatedAt>=V?N.오늘.push(k):k.updatedAt>=T?N.어제.push(k):k.updatedAt>=I?N["이번 주"].push(k):N.이전.push(k);const H=[];for(const[k,G]of Object.entries(N))G.length>0&&H.push({label:k,items:G});return H}let v=D(()=>r(s).trim()?a().filter(C=>C.title.toLowerCase().includes(r(s).toLowerCase())):a()),m=D(()=>d(r(v)));var x=np(),g=i(x);{var y=C=>{var V=tp(),T=p(i(V),2),I=i(T);$f(I,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(B,_)=>{var z=Jf(),Y=re(z);Ws(Y,{size:16}),c(B,z)},$$slots:{default:!0}});var N=p(T,2);{var H=B=>{var _=Xf(),z=i(_),Y=i(z);mn(Y,{size:12,class:"text-dl-text-dim flex-shrink-0"});var J=p(Y,2);Nn(J,()=>r(s),P=>u(s,P)),c(B,_)};b(N,B=>{a().length>3&&B(H)})}var k=p(N,2);Te(k,21,()=>r(m),Me,(B,_)=>{var z=Zf(),Y=i(z),J=i(Y),P=p(Y,2);Te(P,17,()=>r(_).items,Me,(ye,O)=>{var U=Qf(),F=i(U),me=i(F);ns(me,{size:14,class:"flex-shrink-0 opacity-50"});var xe=p(me,2),le=i(xe),te=p(F,2),Ie=i(te);Gf(Ie,{size:12}),S(de=>{qe(U,1,de),Ca(F,"aria-current",r(O).id===n()?"true":void 0),$(le,r(O).title),Ca(te,"aria-label",`${r(O).title} 삭제`)},[()=>Qt(rr("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",r(O).id===n()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),oe("click",F,()=>{var de;return(de=t.onSelect)==null?void 0:de.call(t,r(O).id)}),oe("click",te,de=>{var R;de.stopPropagation(),(R=t.onDelete)==null||R.call(t,r(O).id)}),c(ye,U)}),S(()=>$(J,r(_).label)),c(B,z)});var G=p(k,2);{var he=B=>{var _=ep(),z=i(_),Y=i(z);S(()=>$(Y,`v${l()??""}`)),c(B,_)};b(G,B=>{l()&&B(he)})}c(C,V)},E=C=>{var V=ap(),T=p(i(V),2),I=i(T);Ws(I,{size:18});var N=p(T,2);Te(N,21,()=>a().slice(0,10),Me,(H,k)=>{var G=rp(),he=i(G);ns(he,{size:16}),S(B=>{qe(G,1,B),Ca(G,"title",r(k).title)},[()=>Qt(rr("p-2 rounded-lg transition-colors w-full flex justify-center",r(k).id===n()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),oe("click",G,()=>{var B;return(B=t.onSelect)==null?void 0:B.call(t,r(k).id)}),c(H,G)}),oe("click",T,function(...H){var k;(k=t.onNewChat)==null||k.apply(this,H)}),c(C,V)};b(g,C=>{o()?C(y):C(E,-1)})}S(C=>qe(x,1,C),[()=>Qt(rr("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",o()?"w-[260px]":"w-[52px]"))]),c(e,x),_r()}Vr(["click"]);var sp=f('<button class="send-btn active"><!></button>'),ip=f("<button><!></button>"),lp=f('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),dp=f('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),cp=f('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),up=f('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function Id(e,t){br(t,!0);let a=je(t,"inputText",15,""),n=je(t,"isLoading",3,!1),o=je(t,"large",3,!1),l=je(t,"placeholder",3,"메시지를 입력하세요..."),s=X(Ut([])),d=X(!1),v=X(-1),m=null,x=X(void 0);function g(_){var z;if(r(d)&&r(s).length>0){if(_.key==="ArrowDown"){_.preventDefault(),u(v,(r(v)+1)%r(s).length);return}if(_.key==="ArrowUp"){_.preventDefault(),u(v,r(v)<=0?r(s).length-1:r(v)-1,!0);return}if(_.key==="Enter"&&r(v)>=0){_.preventDefault(),C(r(s)[r(v)]);return}if(_.key==="Escape"){u(d,!1),u(v,-1);return}}_.key==="Enter"&&!_.shiftKey&&(_.preventDefault(),u(d,!1),(z=t.onSend)==null||z.call(t))}function y(_){_.target.style.height="auto",_.target.style.height=Math.min(_.target.scrollHeight,200)+"px"}function E(_){y(_);const z=a();m&&clearTimeout(m),z.length>=2&&!/\s/.test(z.slice(-1))?m=setTimeout(async()=>{var Y;try{const J=await id(z.trim());((Y=J.results)==null?void 0:Y.length)>0?(u(s,J.results.slice(0,6),!0),u(d,!0),u(v,-1)):u(d,!1)}catch{u(d,!1)}},300):u(d,!1)}function C(_){var z;a(`${_.corpName} `),u(d,!1),u(v,-1),(z=t.onCompanySelect)==null||z.call(t,_),r(x)&&r(x).focus()}function V(){setTimeout(()=>{u(d,!1)},200)}var T=up(),I=i(T),N=i(I);pn(N,_=>u(x,_),()=>r(x));var H=p(N,2);{var k=_=>{var z=sp(),Y=i(z);Hf(Y,{size:14}),oe("click",z,function(...J){var P;(P=t.onStop)==null||P.apply(this,J)}),c(_,z)},G=_=>{var z=ip(),Y=i(z);{let J=D(()=>o()?18:16);Af(Y,{get size(){return r(J)},strokeWidth:2.5})}S((J,P)=>{qe(z,1,J),z.disabled=P},[()=>Qt(rr("send-btn",a().trim()&&"active")),()=>!a().trim()]),oe("click",z,()=>{var J;u(d,!1),(J=t.onSend)==null||J.call(t)}),c(_,z)};b(H,_=>{n()&&t.onStop?_(k):_(G,-1)})}var he=p(I,2);{var B=_=>{var z=cp();Te(z,21,()=>r(s),Me,(Y,J,P)=>{var ye=dp(),O=i(ye);mn(O,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var U=p(O,2),F=i(U),me=i(F),xe=p(F,2),le=i(xe),te=p(U,2);{var Ie=de=>{var R=lp(),ee=i(R);S(()=>$(ee,r(J).sector)),c(de,R)};b(te,de=>{r(J).sector&&de(Ie)})}S(de=>{qe(ye,1,de),$(me,r(J).corpName),$(le,`${r(J).stockCode??""} · ${(r(J).market||"")??""}`)},[()=>Qt(rr("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",P===r(v)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),oe("mousedown",ye,()=>C(r(J))),fn("mouseenter",ye,()=>{u(v,P,!0)}),c(Y,ye)}),c(_,z)};b(he,_=>{r(d)&&r(s).length>0&&_(B)})}S(_=>{qe(I,1,_),Ca(N,"placeholder",l())},[()=>Qt(rr("input-box",o()&&"large"))]),oe("keydown",N,g),oe("input",N,E),fn("blur",N,V),Nn(N,a),c(e,T),_r()}Vr(["keydown","input","click","mousedown"]);var vp=f('<button class="rounded-full border border-dl-border/60 bg-dl-bg-card/40 px-3 py-1.5 text-[12px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"> </button>'),fp=f(`<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[580px] flex flex-col items-center"><div class="relative mb-8"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p> <div class="mb-6 max-w-[520px] rounded-2xl border border-dl-border/50 bg-dl-bg-card/50 px-4 py-3 text-left"><div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">Evidence First</div> <div class="mt-2 text-[13px] leading-relaxed text-dl-text-muted">DartLab은 재무 수치와 서술 텍스트를 함께 읽고, 표준화된 계정과 원문 근거를 같은 흐름에서 확인하도록 설계되어 있습니다.
				DART와 EDGAR를 포함한 40개 모듈 이상의 기능 범위를 먼저 물어본 뒤 바로 탐색을 시작할 수 있습니다.</div></div> <div class="w-full"><!></div> <div class="mt-5 flex w-full flex-wrap justify-center gap-2"></div></div></div>`);function pp(e,t){br(t,!0);let a=je(t,"inputText",15,"");const n=["지금 dartlab에서 할 수 있는 기능을 먼저 정리해줘","EDGAR에서 추가로 받을 수 있는 데이터와 방법을 알려줘","OpenDart와 OpenEdgar로 가능한 일을 비교해줘","GPT 연결 시 현재 UI에서 가능한 코딩 작업 범위를 알려줘"];var o=fp(),l=i(o),s=p(i(l),8),d=i(s);Id(d,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get onCompanySelect(){return t.onCompanySelect},get inputText(){return a()},set inputText(m){a(m)}});var v=p(s,2);Te(v,21,()=>n,Me,(m,x)=>{var g=vp(),y=i(g);S(()=>$(y,r(x))),oe("click",g,()=>{var E;return(E=t.onSend)==null?void 0:E.call(t,r(x))}),c(m,g)}),c(e,o),_r()}Vr(["click"]);var mp=f("<span><!></span>");function ko(e,t){br(t,!0);let a=je(t,"variant",3,"default");const n={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var o=mp(),l=i(o);Fs(l,()=>t.children),S(s=>qe(o,1,s),[()=>Qt(rr("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",n[a()],t.class))]),c(e,o),_r()}function xp(e){const t=e.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(t)||t==="-"||t==="0"}function bn(e){if(!e)return"";let t=[],a=[],n=e.replace(/```(\w*)\n([\s\S]*?)```/g,(l,s,d)=>{const v=t.length;return t.push(d.trimEnd()),`
%%CODE_${v}%%
`});n=n.replace(/((?:^\|.+\|$\n?)+)/gm,l=>{const s=l.trim().split(`
`).filter(y=>y.trim());let d=null,v=-1,m=[];for(let y=0;y<s.length;y++)if(s[y].slice(1,-1).split("|").map(C=>C.trim()).every(C=>/^[\-:]+$/.test(C))){v=y;break}v>0?(d=s[v-1],m=s.slice(v+1)):(v===0||(d=s[0]),m=s.slice(1));let x="<table>";if(d){const y=d.slice(1,-1).split("|").map(E=>E.trim());x+="<thead><tr>"+y.map(E=>`<th>${E.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(m.length>0){x+="<tbody>";for(const y of m){const E=y.slice(1,-1).split("|").map(C=>C.trim());x+="<tr>"+E.map(C=>{let V=C.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${xp(C)?' class="num"':""}>${V}</td>`}).join("")+"</tr>"}x+="</tbody>"}x+="</table>";let g=a.length;return a.push(x),`
%%TABLE_${g}%%
`});let o=n.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");o=o.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,l=>"<ul>"+l.replace(/<br>/g,"")+"</ul>");for(let l=0;l<a.length;l++)o=o.replace(`%%TABLE_${l}%%`,a[l]);for(let l=0;l<t.length;l++){const s=t[l].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");o=o.replace(`%%CODE_${l}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${l}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${s}</code></pre></div>`)}return o=o.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(l,s)=>s.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+o+"</p>"}var hp=f('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),gp=f('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),bp=f('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),_p=f('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),yp=f('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!> <!> <!> <!></div></div>'),wp=f('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),kp=f('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),$p=f('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),Cp=f("<span> </span>"),Sp=f('<span class="px-1.5 py-0.5 rounded text-[9px] font-bold border bg-red-500/10 text-red-400 border-red-500/20"> </span>'),Tp=f('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-1.5"><!> <!></div>'),Mp=f('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!> <!></button>'),zp=f("<button><!> </button>"),Ap=f('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),Ep=f('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),Ip=f('<!> <span class="text-dl-text-dim"> </span>',1),Np=f('<div class="flex items-center gap-2 text-[11px]"><!></div>'),Pp=f('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),Lp=f('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),Op=f('<div class="message-committed"><!></div>'),Rp=f('<div><div class="message-live-label"> </div> <pre> </pre></div>'),Dp=f('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),jp=f('<span class="text-dl-accent/60"> </span>'),Vp=f('<span class="text-dl-success/60"> </span>'),qp=f('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),Bp=f('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),Fp=f('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),Hp=f('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),Up=f('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),Kp=f("<!>  <div><!> <!></div> <!>",1),Gp=f('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),Wp=f('<span class="text-[10px] text-dl-text-dim"> </span>'),Yp=f('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),Jp=f("<button> </button>"),Xp=f('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),Qp=f("<button>시스템 프롬프트</button>"),Zp=f("<button>LLM 입력</button>"),em=f('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),tm=f('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),rm=f('<span class="text-dl-text"> </span>'),am=f('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),nm=f('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),om=f('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),sm=f("<!> <!>",1);function im(e,t){br(t,!0);let a=X(null),n=X("context"),o=X("raw"),l=D(()=>{var R,ee,Q,q,ge,Le;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((R=t.message.toolEvents)==null?void 0:R.length)>0){const Z=[...t.message.toolEvents].reverse().find(pt=>pt.type==="call"),tt=((ee=Z==null?void 0:Z.arguments)==null?void 0:ee.module)||((Q=Z==null?void 0:Z.arguments)==null?void 0:Q.keyword)||"";return`도구 실행 중 — ${(Z==null?void 0:Z.name)||""}${tt?` (${tt})`:""}`}if(((q=t.message.contexts)==null?void 0:q.length)>0){const Z=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(Z==null?void 0:Z.label)||(Z==null?void 0:Z.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(ge=t.message.meta)!=null&&ge.company?`${t.message.meta.company} 데이터 검색 중`:(Le=t.message.meta)!=null&&Le.includedModules?"분석 모듈 선택 완료":"생각 중"}),s=D(()=>{var R;return t.message.company||((R=t.message.meta)==null?void 0:R.company)||null});const d={capability:"기능 탐색",coding:"코딩 작업",company_explore:"회사 탐색",company_analysis:"회사 분석",follow_up:"후속 질문",general_chat:"일반 대화"};let v=D(()=>{var R;return(R=t.message.meta)!=null&&R.dialogueMode?d[t.message.meta.dialogueMode]||t.message.meta.dialogueMode:null}),m=D(()=>{var R,ee,Q;return t.message.systemPrompt||t.message.userContent||((R=t.message.contexts)==null?void 0:R.length)>0||((ee=t.message.meta)==null?void 0:ee.includedModules)||((Q=t.message.toolEvents)==null?void 0:Q.length)>0}),x=D(()=>{var ee;const R=(ee=t.message.meta)==null?void 0:ee.dataYearRange;return R?typeof R=="string"?R:R.min_year&&R.max_year?`${R.min_year}~${R.max_year}년`:null:null});function g(R){if(!R)return 0;const ee=(R.match(/[\uac00-\ud7af]/g)||[]).length,Q=R.length-ee;return Math.round(ee*1.5+Q/3.5)}function y(R){return R>=1e3?(R/1e3).toFixed(1)+"k":String(R)}let E=D(()=>{var ee;let R=0;if(t.message.systemPrompt&&(R+=g(t.message.systemPrompt)),t.message.userContent)R+=g(t.message.userContent);else if(((ee=t.message.contexts)==null?void 0:ee.length)>0)for(const Q of t.message.contexts)R+=g(Q.text);return R}),C=D(()=>g(t.message.text)),V=X(void 0);const T=/^\s*\|.+\|\s*$/;function I(R,ee){if(!R)return{committed:"",draft:"",draftType:"none"};if(!ee)return{committed:R,draft:"",draftType:"none"};const Q=R.split(`
`);let q=Q.length;R.endsWith(`
`)||(q=Math.min(q,Q.length-1));let ge=0,Le=-1;for(let M=0;M<Q.length;M++)Q[M].trim().startsWith("```")&&(ge+=1,Le=M);ge%2===1&&Le>=0&&(q=Math.min(q,Le));let Z=-1;for(let M=Q.length-1;M>=0;M--){const ce=Q[M];if(!ce.trim())break;if(T.test(ce))Z=M;else{Z=-1;break}}if(Z>=0&&(q=Math.min(q,Z)),q<=0)return{committed:"",draft:R,draftType:Z===0?"table":ge%2===1?"code":"text"};const tt=Q.slice(0,q).join(`
`),pt=Q.slice(q).join(`
`);let dt="text";return pt&&Z>=q?dt="table":pt&&ge%2===1&&(dt="code"),{committed:tt,draft:pt,draftType:dt}}const N='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',H='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function k(R){var ge;const ee=R.target.closest(".code-copy-btn");if(!ee)return;const Q=ee.closest(".code-block-wrap"),q=((ge=Q==null?void 0:Q.querySelector("code"))==null?void 0:ge.textContent)||"";navigator.clipboard.writeText(q).then(()=>{ee.innerHTML=H,setTimeout(()=>{ee.innerHTML=N},2e3)})}function G(R){if(t.onOpenEvidence){t.onOpenEvidence("contexts",R);return}u(a,R,!0),u(n,"context"),u(o,"rendered")}function he(){if(t.onOpenEvidence){t.onOpenEvidence("system");return}u(a,0),u(n,"system"),u(o,"raw")}function B(){if(t.onOpenEvidence){t.onOpenEvidence("snapshot");return}u(a,0),u(n,"snapshot")}function _(R){var ee;if(t.onOpenEvidence){const Q=(ee=t.message.toolEvents)==null?void 0:ee[R];t.onOpenEvidence((Q==null?void 0:Q.type)==="result"?"tool-results":"tool-calls",R);return}u(a,R,!0),u(n,"tool"),u(o,"raw")}function z(){if(t.onOpenEvidence){t.onOpenEvidence("input");return}u(a,0),u(n,"userContent"),u(o,"raw")}function Y(){u(a,null)}function J(R){var ee,Q,q,ge;return R?R.type==="call"?((ee=R.arguments)==null?void 0:ee.module)||((Q=R.arguments)==null?void 0:Q.keyword)||((q=R.arguments)==null?void 0:q.engine)||((ge=R.arguments)==null?void 0:ge.name)||"":typeof R.result=="string"?R.result.slice(0,120):R.result&&typeof R.result=="object"&&(R.result.module||R.result.status||R.result.name)||"":""}let P=D(()=>(t.message.toolEvents||[]).filter(R=>R.type==="call")),ye=D(()=>(t.message.toolEvents||[]).filter(R=>R.type==="result")),O=D(()=>I(t.message.text||"",t.message.loading)),U=D(()=>{var ee,Q,q;const R=[];return((Q=(ee=t.message.meta)==null?void 0:ee.includedModules)==null?void 0:Q.length)>0&&R.push({label:`모듈 ${t.message.meta.includedModules.length}개`,icon:wo}),((q=t.message.contexts)==null?void 0:q.length)>0&&R.push({label:`컨텍스트 ${t.message.contexts.length}건`,icon:Lf}),r(P).length>0&&R.push({label:`툴 호출 ${r(P).length}건`,icon:el}),r(ye).length>0&&R.push({label:`툴 결과 ${r(ye).length}건`,icon:zo}),t.message.systemPrompt&&R.push({label:"시스템 프롬프트",icon:Ss}),t.message.userContent&&R.push({label:"LLM 입력",icon:da}),R}),F=D(()=>{var ee,Q,q;if(!t.message.loading)return[];const R=[];return(ee=t.message.meta)!=null&&ee.company&&R.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&R.push({label:"핵심 수치 확인",done:!0}),(Q=t.message.meta)!=null&&Q.includedModules&&R.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((q=t.message.contexts)==null?void 0:q.length)>0&&R.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&R.push({label:"프롬프트 조립",done:!0}),t.message.text?R.push({label:"응답 작성 중",done:!1}):R.push({label:r(l)||"준비 중",done:!1}),R});var me=sm(),xe=re(me);{var le=R=>{var ee=hp(),Q=p(i(ee),2),q=i(Q),ge=i(q);S(()=>$(ge,t.message.text)),c(R,ee)},te=R=>{var ee=Gp(),Q=p(i(ee),2),q=i(Q);{var ge=ue=>{var A=yp(),j=i(A),ae=i(j);Mf(ae,{size:11});var ve=p(j,4),ze=i(ve);{var we=Se=>{ko(Se,{variant:"muted",children:(pe,We)=>{var Ee=an();S(()=>$(Ee,r(s))),c(pe,Ee)},$$slots:{default:!0}})};b(ze,Se=>{r(s)&&Se(we)})}var h=p(ze,2);{var L=Se=>{ko(Se,{variant:"muted",children:(pe,We)=>{var Ee=an();S(Ne=>$(Ee,Ne),[()=>t.message.meta.market.toUpperCase()]),c(pe,Ee)},$$slots:{default:!0}})};b(h,Se=>{var pe;(pe=t.message.meta)!=null&&pe.market&&Se(L)})}var K=p(h,2);{var se=Se=>{ko(Se,{variant:"accent",children:(pe,We)=>{var Ee=an();S(()=>$(Ee,r(v))),c(pe,Ee)},$$slots:{default:!0}})};b(K,Se=>{r(v)&&Se(se)})}var ne=p(K,2);{var Fe=Se=>{ko(Se,{variant:"muted",children:(pe,We)=>{var Ee=an();S(()=>$(Ee,t.message.meta.topicLabel)),c(pe,Ee)},$$slots:{default:!0}})};b(ne,Se=>{var pe;(pe=t.message.meta)!=null&&pe.topicLabel&&Se(Fe)})}var Be=p(ne,2);{var Rt=Se=>{ko(Se,{variant:"accent",children:(pe,We)=>{var Ee=an();S(()=>$(Ee,r(x))),c(pe,Ee)},$$slots:{default:!0}})};b(Be,Se=>{r(x)&&Se(Rt)})}var mt=p(Be,2);{var lt=Se=>{var pe=ke(),We=re(pe);Te(We,17,()=>t.message.contexts,Me,(Ee,Ne,Ve)=>{var vt=gp(),_e=i(vt);wo(_e,{size:10,class:"flex-shrink-0"});var Qe=p(_e);S(()=>$(Qe,` ${(r(Ne).label||r(Ne).module)??""}`)),oe("click",vt,()=>G(Ve)),c(Ee,vt)}),c(Se,pe)},gt=Se=>{var pe=bp(),We=i(pe);wo(We,{size:10,class:"flex-shrink-0"});var Ee=p(We);S(()=>$(Ee,` 모듈 ${t.message.meta.includedModules.length??""}개`)),c(Se,pe)};b(mt,Se=>{var pe,We,Ee;((pe=t.message.contexts)==null?void 0:pe.length)>0?Se(lt):((Ee=(We=t.message.meta)==null?void 0:We.includedModules)==null?void 0:Ee.length)>0&&Se(gt,1)})}var er=p(mt,2);Te(er,17,()=>r(U),Me,(Se,pe)=>{var We=_p(),Ee=i(We);ci(Ee,()=>r(pe).icon,(Ve,vt)=>{vt(Ve,{size:10,class:"flex-shrink-0"})});var Ne=p(Ee);S(()=>$(Ne,` ${r(pe).label??""}`)),oe("click",We,()=>{r(pe).label.startsWith("컨텍스트")?G(0):r(pe).label.startsWith("툴 호출")?t.onOpenEvidence?t.onOpenEvidence("tool-calls",0):_(0):r(pe).label.startsWith("툴 결과")?t.onOpenEvidence?t.onOpenEvidence("tool-results",0):_((t.message.toolEvents||[]).findIndex(Ve=>Ve.type==="result")):r(pe).label==="시스템 프롬프트"?he():r(pe).label==="LLM 입력"&&z()}),c(Se,We)}),c(ue,A)};b(q,ue=>{var A,j;(r(s)||r(x)||((A=t.message.contexts)==null?void 0:A.length)>0||(j=t.message.meta)!=null&&j.includedModules||r(U).length>0)&&ue(ge)})}var Le=p(q,2);{var Z=ue=>{var A=Mp(),j=i(A);Te(j,21,()=>t.message.snapshot.items,Me,(h,L)=>{const K=D(()=>r(L).status==="good"?"text-dl-success":r(L).status==="danger"?"text-dl-primary-light":r(L).status==="caution"?"text-amber-400":"text-dl-text");var se=wp(),ne=i(se),Fe=i(ne),Be=p(ne,2),Rt=i(Be);S(mt=>{$(Fe,r(L).label),qe(Be,1,mt),$(Rt,r(L).value)},[()=>Qt(rr("text-[14px] font-semibold leading-snug mt-0.5",r(K)))]),c(h,se)});var ae=p(j,2);{var ve=h=>{var L=$p();Te(L,21,()=>t.message.snapshot.warnings,Me,(K,se)=>{var ne=kp(),Fe=i(ne);Jo(Fe,{size:10});var Be=p(Fe);S(()=>$(Be,` ${r(se)??""}`)),c(K,ne)}),c(h,L)};b(ae,h=>{var L;((L=t.message.snapshot.warnings)==null?void 0:L.length)>0&&h(ve)})}var ze=p(ae,2);{var we=h=>{const L=D(()=>({performance:"실적",profitability:"수익성",health:"건전성",cashflow:"현금흐름",governance:"지배구조",risk:"리스크",opportunity:"기회"}));var K=Tp(),se=i(K);Te(se,17,()=>Object.entries(t.message.snapshot.grades),Me,(Be,Rt)=>{var mt=D(()=>Zs(r(Rt),2));let lt=()=>r(mt)[0],gt=()=>r(mt)[1];const er=D(()=>gt()==="A"?"bg-emerald-500/15 text-emerald-400 border-emerald-500/30":gt()==="B"?"bg-blue-500/15 text-blue-400 border-blue-500/30":gt()==="C"?"bg-amber-500/15 text-amber-400 border-amber-500/30":gt()==="D"?"bg-orange-500/15 text-orange-400 border-orange-500/30":gt()==="F"?"bg-red-500/15 text-red-400 border-red-500/30":"bg-dl-border/10 text-dl-text-dim border-dl-border/20");var Se=Cp(),pe=i(Se);S(()=>{qe(Se,1,`px-1.5 py-0.5 rounded text-[9px] font-bold border ${r(er)??""}`),$(pe,`${(r(L)[lt()]||lt())??""} ${gt()??""}`)}),c(Be,Se)});var ne=p(se,2);{var Fe=Be=>{var Rt=Sp(),mt=i(Rt);S(()=>$(mt,`이상치 ${t.message.snapshot.anomalyCount??""}건`)),c(Be,Rt)};b(ne,Be=>{t.message.snapshot.anomalyCount>0&&Be(Fe)})}c(h,K)};b(ze,h=>{t.message.snapshot.grades&&h(we)})}oe("click",A,B),c(ue,A)};b(Le,ue=>{var A,j;((j=(A=t.message.snapshot)==null?void 0:A.items)==null?void 0:j.length)>0&&ue(Z)})}var tt=p(Le,2);{var pt=ue=>{var A=Ap(),j=i(A),ae=p(i(j),4);Te(ae,21,()=>t.message.toolEvents,Me,(ve,ze,we)=>{const h=D(()=>J(r(ze)));var L=zp(),K=i(L);{var se=Be=>{el(Be,{size:11})},ne=Be=>{zo(Be,{size:11})};b(K,Be=>{r(ze).type==="call"?Be(se):Be(ne,-1)})}var Fe=p(K);S(Be=>{qe(L,1,Be),$(Fe,` ${(r(ze).type==="call"?r(ze).name:`${r(ze).name} 결과`)??""}${r(h)?`: ${r(h)}`:""}`)},[()=>Qt(rr("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",r(ze).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),oe("click",L,()=>_(we)),c(ve,L)}),c(ue,A)};b(tt,ue=>{var A;((A=t.message.toolEvents)==null?void 0:A.length)>0&&ue(pt)})}var dt=p(tt,2);{var M=ue=>{var A=Pp(),j=i(A);Te(j,21,()=>r(F),Me,(ae,ve)=>{var ze=Np(),we=i(ze);{var h=K=>{var se=Ep(),ne=p(re(se),2),Fe=i(ne);S(()=>$(Fe,r(ve).label)),c(K,se)},L=K=>{var se=Ip(),ne=re(se);zr(ne,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var Fe=p(ne,2),Be=i(Fe);S(()=>$(Be,r(ve).label)),c(K,se)};b(we,K=>{r(ve).done?K(h):K(L,-1)})}c(ae,ze)}),c(ue,A)},ce=ue=>{var A=Kp(),j=re(A);{var ae=ne=>{var Fe=Lp(),Be=i(Fe);zr(Be,{size:12,class:"animate-spin flex-shrink-0"});var Rt=p(Be,2),mt=i(Rt);S(()=>$(mt,r(l))),c(ne,Fe)};b(j,ne=>{t.message.loading&&ne(ae)})}var ve=p(j,2),ze=i(ve);{var we=ne=>{var Fe=Op(),Be=i(Fe);$a(Be,()=>bn(r(O).committed)),c(ne,Fe)};b(ze,ne=>{r(O).committed&&ne(we)})}var h=p(ze,2);{var L=ne=>{var Fe=Rp(),Be=i(Fe),Rt=i(Be),mt=p(Be,2),lt=i(mt);S(gt=>{qe(Fe,1,gt),$(Rt,r(O).draftType==="table"?"표 구성 중":r(O).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),$(lt,r(O).draft)},[()=>Qt(rr("message-live-tail",r(O).draftType==="table"&&"message-draft-table",r(O).draftType==="code"&&"message-draft-code"))]),c(ne,Fe)};b(h,ne=>{r(O).draft&&ne(L)})}pn(ve,ne=>u(V,ne),()=>r(V));var K=p(ve,2);{var se=ne=>{var Fe=Up(),Be=i(Fe);{var Rt=Ne=>{var Ve=Dp(),vt=i(Ve);as(vt,{size:10});var _e=p(vt);S(()=>$(_e,` ${t.message.duration??""}초`)),c(Ne,Ve)};b(Be,Ne=>{t.message.duration&&Ne(Rt)})}var mt=p(Be,2);{var lt=Ne=>{var Ve=qp(),vt=i(Ve);{var _e=ft=>{var St=jp(),rt=i(St);S(Mt=>$(rt,`↑${Mt??""}`),[()=>y(r(E))]),c(ft,St)};b(vt,ft=>{r(E)>0&&ft(_e)})}var Qe=p(vt,2);{var kt=ft=>{var St=Vp(),rt=i(St);S(Mt=>$(rt,`↓${Mt??""}`),[()=>y(r(C))]),c(ft,St)};b(Qe,ft=>{r(C)>0&&ft(kt)})}c(Ne,Ve)};b(mt,Ne=>{(r(E)>0||r(C)>0)&&Ne(lt)})}var gt=p(mt,2);{var er=Ne=>{var Ve=Bp(),vt=i(Ve);qf(vt,{size:10}),oe("click",Ve,()=>{var _e;return(_e=t.onRegenerate)==null?void 0:_e.call(t)}),c(Ne,Ve)};b(gt,Ne=>{t.onRegenerate&&Ne(er)})}var Se=p(gt,2);{var pe=Ne=>{var Ve=Fp(),vt=i(Ve);Ss(vt,{size:10}),oe("click",Ve,he),c(Ne,Ve)};b(Se,Ne=>{t.message.systemPrompt&&Ne(pe)})}var We=p(Se,2);{var Ee=Ne=>{var Ve=Hp(),vt=i(Ve);da(vt,{size:10});var _e=p(vt);S((Qe,kt)=>$(_e,` LLM 입력 (${Qe??""}자 · ~${kt??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>y(g(t.message.userContent))]),oe("click",Ve,z),c(Ne,Ve)};b(We,Ne=>{t.message.userContent&&Ne(Ee)})}c(ne,Fe)};b(K,ne=>{!t.message.loading&&(t.message.duration||r(m)||t.onRegenerate)&&ne(se)})}S(ne=>qe(ve,1,ne),[()=>Qt(rr("prose-dartlab message-body text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),oe("click",ve,k),c(ue,A)};b(dt,ue=>{t.message.loading&&!t.message.text?ue(M):ue(ce,-1)})}c(R,ee)};b(xe,R=>{t.message.role==="user"?R(le):R(te,-1)})}var Ie=p(xe,2);{var de=R=>{const ee=D(()=>r(n)==="system"),Q=D(()=>r(n)==="userContent"),q=D(()=>r(n)==="context"),ge=D(()=>r(n)==="snapshot"),Le=D(()=>r(n)==="tool"),Z=D(()=>{var _e;return r(q)?(_e=t.message.contexts)==null?void 0:_e[r(a)]:null}),tt=D(()=>{var _e;return r(Le)?(_e=t.message.toolEvents)==null?void 0:_e[r(a)]:null}),pt=D(()=>{var _e,Qe,kt,ft,St;return r(ge)?"핵심 수치 (원본 데이터)":r(ee)?"시스템 프롬프트":r(Q)?"LLM에 전달된 입력":r(Le)?((_e=r(tt))==null?void 0:_e.type)==="call"?`${(Qe=r(tt))==null?void 0:Qe.name} 호출`:`${(kt=r(tt))==null?void 0:kt.name} 결과`:((ft=r(Z))==null?void 0:ft.label)||((St=r(Z))==null?void 0:St.module)||""}),dt=D(()=>{var _e;return r(ge)?JSON.stringify(t.message.snapshot,null,2):r(ee)?t.message.systemPrompt:r(Q)?t.message.userContent:r(Le)?JSON.stringify(r(tt),null,2):(_e=r(Z))==null?void 0:_e.text});var M=om(),ce=i(M),ue=i(ce),A=i(ue),j=i(A),ae=i(j);{var ve=_e=>{wo(_e,{size:15,class:"text-dl-success flex-shrink-0"})},ze=_e=>{Ss(_e,{size:15,class:"text-dl-primary-light flex-shrink-0"})},we=_e=>{da(_e,{size:15,class:"text-dl-accent flex-shrink-0"})},h=_e=>{wo(_e,{size:15,class:"flex-shrink-0"})};b(ae,_e=>{r(ge)?_e(ve):r(ee)?_e(ze,1):r(Q)?_e(we,2):_e(h,-1)})}var L=p(ae,2),K=i(L),se=p(L,2);{var ne=_e=>{var Qe=Wp(),kt=i(Qe);S(ft=>$(kt,`(${ft??""}자)`),[()=>{var ft,St;return(St=(ft=r(dt))==null?void 0:ft.length)==null?void 0:St.toLocaleString()}]),c(_e,Qe)};b(se,_e=>{r(ee)&&_e(ne)})}var Fe=p(j,2),Be=i(Fe);{var Rt=_e=>{var Qe=Yp(),kt=i(Qe),ft=i(kt);da(ft,{size:11});var St=p(kt,2),rt=i(St);If(rt,{size:11}),S((Mt,Pt)=>{qe(kt,1,Mt),qe(St,1,Pt)},[()=>Qt(rr("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",r(o)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>Qt(rr("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",r(o)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),oe("click",kt,()=>u(o,"rendered")),oe("click",St,()=>u(o,"raw")),c(_e,Qe)};b(Be,_e=>{r(q)&&_e(Rt)})}var mt=p(Be,2),lt=i(mt);gn(lt,{size:18});var gt=p(A,2);{var er=_e=>{var Qe=Xp(),kt=i(Qe);Te(kt,21,()=>t.message.contexts,Me,(ft,St,rt)=>{var Mt=Jp(),Pt=i(Mt);S(Kt=>{qe(Mt,1,Kt),$(Pt,t.message.contexts[rt].label||t.message.contexts[rt].module)},[()=>Qt(rr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",rt===r(a)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),oe("click",Mt,()=>{u(a,rt,!0)}),c(ft,Mt)}),c(_e,Qe)};b(gt,_e=>{var Qe;r(q)&&((Qe=t.message.contexts)==null?void 0:Qe.length)>1&&_e(er)})}var Se=p(gt,2);{var pe=_e=>{var Qe=em(),kt=i(Qe),ft=i(kt);{var St=Pt=>{var Kt=Qp();S(st=>qe(Kt,1,st),[()=>Qt(rr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",r(ee)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),oe("click",Kt,()=>{u(n,"system")}),c(Pt,Kt)};b(ft,Pt=>{t.message.systemPrompt&&Pt(St)})}var rt=p(ft,2);{var Mt=Pt=>{var Kt=Zp();S(st=>qe(Kt,1,st),[()=>Qt(rr("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",r(Q)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),oe("click",Kt,()=>{u(n,"userContent")}),c(Pt,Kt)};b(rt,Pt=>{t.message.userContent&&Pt(Mt)})}c(_e,Qe)};b(Se,_e=>{!r(q)&&!r(ge)&&!r(Le)&&_e(pe)})}var We=p(ue,2),Ee=i(We);{var Ne=_e=>{var Qe=tm(),kt=i(Qe);$a(kt,()=>{var ft;return bn((ft=r(Z))==null?void 0:ft.text)}),c(_e,Qe)},Ve=_e=>{var Qe=am(),kt=i(Qe),ft=p(i(kt),2),St=i(ft),rt=p(St);{var Mt=$e=>{var ct=rm(),Jt=i(ct);S(pr=>$(Jt,pr),[()=>J(r(tt))]),c($e,ct)},Pt=D(()=>J(r(tt)));b(rt,$e=>{r(Pt)&&$e(Mt)})}var Kt=p(kt,2),st=i(Kt);S(()=>{var $e;$(St,`${(($e=r(tt))==null?void 0:$e.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),$(st,r(dt))}),c(_e,Qe)},vt=_e=>{var Qe=nm(),kt=i(Qe);S(()=>$(kt,r(dt))),c(_e,Qe)};b(Ee,_e=>{r(q)&&r(o)==="rendered"?_e(Ne):r(Le)?_e(Ve,1):_e(vt,-1)})}S(()=>$(K,r(pt))),oe("click",M,_e=>{_e.target===_e.currentTarget&&Y()}),oe("keydown",M,_e=>{_e.key==="Escape"&&Y()}),oe("click",mt,Y),c(R,M)};b(Ie,R=>{r(a)!==null&&R(de)})}c(e,me),_r()}Vr(["click","keydown"]);var lm=f('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),dm=f('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),cm=f('<div class="flex justify-end gap-2 mb-1.5"><!></div>'),um=f('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8"><!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function vm(e,t){br(t,!0);function a(J){if(o())return!1;for(let P=n().length-1;P>=0;P--)if(n()[P].role==="assistant"&&!n()[P].error&&n()[P].text)return P===J;return!1}let n=je(t,"messages",19,()=>[]),o=je(t,"isLoading",3,!1),l=je(t,"inputText",15,""),s=je(t,"scrollTrigger",3,0);je(t,"selectedCompany",3,null);function d(J){return(P,ye)=>{var U,F,me,xe;(U=t.onOpenEvidence)==null||U.call(t,P,ye);let O;if(P==="contexts")O=(F=J.contexts)==null?void 0:F[ye];else if(P==="snapshot")O={label:"핵심 수치",module:"snapshot",text:JSON.stringify(J.snapshot,null,2)};else if(P==="system")O={label:"시스템 프롬프트",module:"system",text:J.systemPrompt};else if(P==="input")O={label:"LLM 입력",module:"input",text:J.userContent};else if(P==="tool-calls"||P==="tool-results"){const le=(me=J.toolEvents)==null?void 0:me[ye];O={label:`${(le==null?void 0:le.name)||"도구"} ${(le==null?void 0:le.type)==="call"?"호출":"결과"}`,module:"tool",text:JSON.stringify(le,null,2)}}O&&((xe=t.onOpenData)==null||xe.call(t,O))}}let v,m,x=X(!0),g=X(!1),y=X(!0);function E(){if(!v)return;const{scrollTop:J,scrollHeight:P,clientHeight:ye}=v;u(y,P-J-ye<96),r(y)?(u(x,!0),u(g,!1)):(u(x,!1),u(g,!0))}function C(J="smooth"){m&&(m.scrollIntoView({block:"end",behavior:J}),u(x,!0),u(g,!1))}$r(()=>{s(),!(!v||!m)&&requestAnimationFrame(()=>{!v||!m||(r(x)||r(y)?(m.scrollIntoView({block:"end",behavior:o()?"auto":"smooth"}),u(g,!1)):u(g,!0))})});var V=um(),T=i(V),I=i(T),N=i(I);Te(N,17,n,Me,(J,P,ye)=>{{let O=D(()=>a(ye)?t.onRegenerate:void 0),U=D(()=>t.onOpenData?d(r(P)):void 0);im(J,{get message(){return r(P)},get onRegenerate(){return r(O)},get onOpenEvidence(){return r(U)}})}});var H=p(N,2);pn(H,J=>m=J,()=>m),pn(T,J=>v=J,()=>v);var k=p(T,2);{var G=J=>{var P=lm(),ye=i(P);oe("click",ye,()=>C("smooth")),c(J,P)};b(k,J=>{r(g)&&J(G)})}var he=p(k,2),B=i(he),_=i(B);{var z=J=>{var P=cm(),ye=i(P);{var O=U=>{var F=dm(),me=i(F);Ao(me,{size:10}),oe("click",F,function(...xe){var le;(le=t.onExport)==null||le.apply(this,xe)}),c(U,F)};b(ye,U=>{n().length>1&&t.onExport&&U(O)})}c(J,P)};b(_,J=>{o()||J(z)})}var Y=p(_,2);Id(Y,{get isLoading(){return o()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get onCompanySelect(){return t.onCompanySelect},get inputText(){return l()},set inputText(J){l(J)}}),fn("scroll",T,E),c(e,V),_r()}Vr(["click"]);var fm=f('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!> <span class="text-[13px]">공시 데이터 로딩 중...</span></div>'),pm=f('<div class="text-[11px] text-dl-text-dim"> </div>'),mm=f('<button><!> <span class="truncate flex-1"> </span></button>'),xm=f('<div class="py-0.5"></div>'),hm=f('<div><button class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] opacity-30 font-normal"> </span></button> <!></div>'),gm=f('<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50"><div class="px-3 py-2.5 border-b border-dl-border/20"><!></div> <!></nav>'),bm=f('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim"><!> <p class="text-[13px]">좌측에서 섹션을 선택하세요</p></div>'),_m=f('<div class="text-[10px] text-dl-text-dim/50 mb-0.5"> </div>'),ym=f('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!></div>'),wm=f('<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>'),km=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),$m=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Cm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Sm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Tm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Mm=f('<div class="vw-heading-node svelte-1l2nqwu"><!></div>'),zm=f('<div class="vw-heading-block svelte-1l2nqwu"></div>'),Am=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Em=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Im=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Nm=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Pm=f('<button><span class="vw-timeline-label svelte-1l2nqwu"> </span></button>'),Lm=f('<div class="vw-section-timeline svelte-1l2nqwu"></div>'),Om=f('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Rm=f('<span class="vw-meta-pill svelte-1l2nqwu">비교 없음</span>'),Dm=f('<div class="vw-section-actions svelte-1l2nqwu"><span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span></div>'),jm=f('<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span> </div>'),Vm=f('<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),qm=f('<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),Bm=f('<div class="text-[10px] text-dl-text-dim/35 mt-1"> </div>'),Fm=f('<div class="vw-digest svelte-1l2nqwu"><div class="flex items-center gap-2 mb-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span></div> <div class="space-y-1"><!> <!> <!> <!></div></div>'),Hm=f('<p class="vw-para"> </p>'),Um=f('<div class="vw-diff-added svelte-1l2nqwu"> </div>'),Km=f('<div class="vw-diff-deleted svelte-1l2nqwu"> </div>'),Gm=f('<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow svelte-1l2nqwu"></div>'),Wm=f('<div class="disclosure-text vw-section-body vw-body-frame svelte-1l2nqwu"><!></div>'),Ym=f('<div><!> <div class="vw-section-meta svelte-1l2nqwu"><span> </span> <!> <!> <!> <!></div> <!> <!> <!> <!></div>'),Jm=f('<section class="vw-report-shell svelte-1l2nqwu"><div class="vw-report-header svelte-1l2nqwu"><div class="vw-report-badges svelte-1l2nqwu"><!> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <!> <!></div></div> <!></section>'),Xm=f('<div class="vw-data-divider svelte-1l2nqwu"><div class="vw-data-kicker svelte-1l2nqwu">Structured Data</div> <div class="vw-data-title svelte-1l2nqwu">표 / 정형 데이터</div></div>'),Qm=f('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),Zm=f("<th> </th>"),ex=f("<td> </td>"),tx=f("<tr></tr>"),rx=f('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),ax=f('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),nx=f("<th> </th>"),ox=f("<td> </td>"),sx=f("<tr></tr>"),ix=f('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),lx=f("<button> </button>"),dx=f('<span class="text-[9px] text-dl-text-dim/30"> </span>'),cx=f('<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto"><!> <!></div>'),ux=f('<div class="vw-table-wrap bg-dl-bg-card/10 svelte-1l2nqwu"><!> <div class="px-4 py-3"><div class="markdown-table overflow-x-auto svelte-1l2nqwu"><!></div></div></div>'),vx=f("<th> </th>"),fx=f("<td> </td>"),px=f("<tr></tr>"),mx=f('<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02] svelte-1l2nqwu"><div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10"><!> <span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span></div> <div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),xx=f('<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card"> </th>'),hx=f('<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted"> </td>'),gx=f("<tr></tr>"),bx=f('<div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),_x=f('<article class="py-6 px-8"><!> <!> <!> <!></article>'),yx=f('<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center"><div class="flex-1 min-w-0"><!> <h3 class="text-[16px] font-semibold text-dl-text"> </h3></div> <button class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"><!></button></div> <!>',1),wx=f('<div class="flex flex-1 overflow-hidden min-h-0"><!> <main class="flex-1 overflow-y-auto min-w-0"><!></main></div>'),kx=f('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8"><!> <p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p></div>'),$x=f('<div class="flex flex-col h-full font-sans bg-dl-bg-dark"><!></div>');function Cx(e,t){br(t,!0);let a=je(t,"stockCode",3,null),n=je(t,"onTopicChange",3,null),o=X(null),l=X(!1),s=X(Ut(new Set)),d=X(null),v=X(null),m=X(Ut([])),x=X(null),g=X(!1),y=X(Ut([])),E=X(Ut(new Map)),C=new Map,V=X(!1),T=X(Ut(new Map));const I={companyOverview:"회사 개요",companyHistory:"회사 연혁",articlesOfIncorporation:"정관 사항",capitalChange:"자본금 변동",shareCapital:"주식 현황",dividend:"배당",productService:"사업 내용",rawMaterial:"원재료",businessOverview:"사업 개요",salesOrder:"매출/수주",riskDerivative:"위험관리/파생",majorContractsAndRnd:"주요 계약/R&D",otherReferences:"기타 참고사항",consolidatedStatements:"연결 재무제표",fsSummary:"재무제표 요약",consolidatedNotes:"연결 주석",financialStatements:"개별 재무제표",financialNotes:"개별 주석",fundraising:"자금조달",BS:"재무상태표",IS:"손익계산서",CIS:"포괄손익계산서",CF:"현금흐름표",SCE:"자본변동표",ratios:"재무비율",audit:"감사 의견",mdna:"경영진 분석(MD&A)",internalControl:"내부통제",auditContract:"감사 계약",nonAuditContract:"비감사 계약",boardOfDirectors:"이사회",shareholderMeeting:"주주총회",auditSystem:"감사 체계",outsideDirector:"사외이사",majorHolder:"주요 주주",majorHolderChange:"주주 변동",minorityHolder:"소수주주",stockTotal:"주식 총수",treasuryStock:"자기주식",employee:"직원 현황",executivePay:"임원 보수",executive:"임원 현황",executivePayAllTotal:"전체 보수 총액",executivePayIndividual:"개인별 보수",topPay:"5억이상 상위 보수",unregisteredExecutivePay:"미등기임원 보수",affiliateGroup:"계열회사",investedCompany:"투자회사",relatedPartyTx:"특수관계 거래",corporateBond:"사채 관리",privateOfferingUsage:"사모자금 사용",publicOfferingUsage:"공모자금 사용",shortTermBond:"단기사채",investorProtection:"투자자 보호",disclosureChanges:"공시변경 사항",contingentLiability:"우발채무",sanction:"제재/조치",subsequentEvents:"후발사건",expertConfirmation:"전문가 확인",subsidiaryDetail:"종속회사 상세",affiliateGroupDetail:"계열회사 상세",investmentInOtherDetail:"타법인 출자 상세",rndDetail:"R&D 상세"},N={I:"I. 회사의 개요",II:"II. 사업의 내용",III:"III. 재무에 관한 사항",IV:"IV. 감사인의 감사의견 등",V:"V. 이사의 경영진단 및 분석의견",VI:"VI. 이사회 등 회사의 기관에 관한 사항",VII:"VII. 주주에 관한 사항",VIII:"VIII. 임원 및 직원 등에 관한 사항",IX:"IX. 계열회사 등에 관한 사항",X:"X. 대주주 등과의 거래내용",XI:"XI. 그 밖에 투자자 보호를 위하여 필요한 사항",XII:"XII. 상세표"},H={I:1,II:2,III:3,IV:4,V:5,VI:6,VII:7,VIII:8,IX:9,X:10,XI:11,XII:12};function k(h){return H[h]??99}function G(h){return I[h]||h}function he(h){return N[h]||h||"기타"}$r(()=>{a()&&B()});async function B(){var h,L;u(l,!0),u(o,null),u(d,null),u(v,null),u(m,[],!0),u(x,null),C=new Map;try{const K=await vv(a());u(o,K.payload,!0),(h=r(o))!=null&&h.columns&&u(y,r(o).columns.filter(ne=>/^\d{4}(Q[1-4])?$/.test(ne)),!0);const se=O((L=r(o))==null?void 0:L.rows);se.length>0&&(u(s,new Set([se[0].chapter]),!0),se[0].topics.length>0&&_(se[0].topics[0].topic,se[0].chapter))}catch(K){console.error("viewer load error:",K)}u(l,!1)}async function _(h,L){var K;if(r(d)!==h){if(u(d,h,!0),u(v,L||null,!0),u(E,new Map,!0),u(T,new Map,!0),(K=n())==null||K(h,G(h)),C.has(h)){const se=C.get(h);u(m,se.blocks||[],!0),u(x,se.textDocument||null,!0);return}u(m,[],!0),u(x,null),u(g,!0);try{const se=await uv(a(),h);u(m,se.blocks||[],!0),u(x,se.textDocument||null,!0),C.set(h,{blocks:r(m),textDocument:r(x)})}catch(se){console.error("topic load error:",se),u(m,[],!0),u(x,null)}u(g,!1)}}function z(h){const L=new Set(r(s));L.has(h)?L.delete(h):L.add(h),u(s,L,!0)}function Y(h,L){const K=new Map(r(E));K.get(h)===L?K.delete(h):K.set(h,L),u(E,K,!0)}function J(h,L){const K=new Map(r(T));K.set(h,L),u(T,K,!0)}function P(h){return h==="updated"?"최근 수정":h==="new"?"신규":h==="stale"?"과거 유지":"유지"}function ye(h){return h==="updated"?"updated":h==="new"?"new":h==="stale"?"stale":"stable"}function O(h){if(!h)return[];const L=new Map,K=new Set;for(const se of h){const ne=se.chapter||"";L.has(ne)||L.set(ne,{chapter:ne,topics:[]}),K.has(se.topic)||(K.add(se.topic),L.get(ne).topics.push({topic:se.topic,source:se.source||"docs"}))}return[...L.values()].sort((se,ne)=>k(se.chapter)-k(ne.chapter))}function U(h){return String(h).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function F(h){return String(h||"").replaceAll(" "," ").replace(/\s+/g," ").trim()}function me(h){return!h||h.length>88?!1:/^\[.+\]$/.test(h)||/^【.+】$/.test(h)||/^[IVX]+\.\s/.test(h)||/^\d+\.\s/.test(h)||/^[가-힣]\.\s/.test(h)||/^\(\d+\)\s/.test(h)||/^\([가-힣]\)\s/.test(h)}function xe(h){return/^\(\d+\)\s/.test(h)||/^\([가-힣]\)\s/.test(h)?"h5":"h4"}function le(h){return/^\[.+\]$/.test(h)||/^【.+】$/.test(h)?"vw-h-bracket":/^\(\d+\)\s/.test(h)||/^\([가-힣]\)\s/.test(h)?"vw-h-sub":"vw-h-section"}function te(h){if(!h)return[];if(/^\|.+\|$/m.test(h)||/^#{1,3} /m.test(h)||/```/.test(h))return[{kind:"markdown",text:h}];const L=[];let K=[];const se=()=>{K.length!==0&&(L.push({kind:"paragraph",text:K.join(" ")}),K=[])};for(const ne of String(h).split(`
`)){const Fe=F(ne);if(!Fe){se();continue}if(me(Fe)){se(),L.push({kind:"heading",text:Fe,tag:xe(Fe),className:le(Fe)});continue}K.push(Fe)}return se(),L}function Ie(h){return h?h.kind==="annual"?`${h.year}Q4`:h.year&&h.quarter?`${h.year}Q${h.quarter}`:h.label||"":""}function de(h){var se;const L=te(h);if(L.length===0)return"";if(((se=L[0])==null?void 0:se.kind)==="markdown")return bn(h);let K="";for(const ne of L){if(ne.kind==="heading"){K+=`<${ne.tag} class="${ne.className}">${U(ne.text)}</${ne.tag}>`;continue}K+=`<p class="vw-para">${U(ne.text)}</p>`}return K}function R(h){if(!h)return"";const L=h.trim().split(`
`).filter(se=>se.trim());let K="";for(const se of L){const ne=se.trim();/^[가-힣]\.\s/.test(ne)||/^\d+[-.]/.test(ne)?K+=`<h4 class="vw-h-section">${ne}</h4>`:/^\(\d+\)\s/.test(ne)||/^\([가-힣]\)\s/.test(ne)?K+=`<h5 class="vw-h-sub">${ne}</h5>`:/^\[.+\]$/.test(ne)||/^【.+】$/.test(ne)?K+=`<h4 class="vw-h-bracket">${ne}</h4>`:K+=`<h5 class="vw-h-sub">${ne}</h5>`}return K}function ee(h){var K;const L=r(E).get(h.id);return L&&((K=h==null?void 0:h.views)!=null&&K[L])?h.views[L]:(h==null?void 0:h.latest)||null}function Q(h,L){var se,ne;const K=r(E).get(h.id);return K?K===L:((ne=(se=h==null?void 0:h.latest)==null?void 0:se.period)==null?void 0:ne.label)===L}function q(h){return r(E).has(h.id)}function ge(h){return h==="updated"?"변경 있음":h==="new"?"직전 없음":"직전과 동일"}function Le(h){var Fe,Be,Rt;if(!h)return[];const L=te(h.body);if(L.length===0||((Fe=L[0])==null?void 0:Fe.kind)==="markdown"||!((Be=h.prevPeriod)!=null&&Be.label)||!((Rt=h.diff)!=null&&Rt.length))return L;const K=[];for(const mt of h.diff)for(const lt of mt.paragraphs||[])K.push({kind:mt.kind,text:F(lt)});const se=[];let ne=0;for(const mt of L){if(mt.kind!=="paragraph"){se.push(mt);continue}for(;ne<K.length&&K[ne].kind==="removed";)se.push({kind:"removed",text:K[ne].text}),ne+=1;ne<K.length&&["same","added"].includes(K[ne].kind)?(se.push({kind:K[ne].kind,text:K[ne].text||mt.text}),ne+=1):se.push({kind:"same",text:mt.text})}for(;ne<K.length;)se.push({kind:K[ne].kind,text:K[ne].text}),ne+=1;return se}function Z(h){return h==null?!1:/^-?[\d,.]+%?$/.test(String(h).trim().replace(/,/g,""))}function tt(h){return h==null?!1:/^-[\d.]+/.test(String(h).trim().replace(/,/g,""))}function pt(h,L){if(h==null||h==="")return"";const K=typeof h=="number"?h:Number(String(h).replace(/,/g,""));if(isNaN(K))return String(h);if(L<=1)return K.toLocaleString("ko-KR");const se=K/L;return Number.isInteger(se)?se.toLocaleString("ko-KR"):se.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g,",")}function dt(h){if(h==null||h==="")return"";const L=String(h).trim();if(L.includes(","))return L;const K=L.match(/^(-?\d+)(\.\d+)?(%?)$/);return K?K[1].replace(/\B(?=(\d{3})+(?!\d))/g,",")+(K[2]||"")+(K[3]||""):L}function M(h){var L,K;return(L=r(o))!=null&&L.rows&&((K=r(o).rows.find(se=>se.topic===h))==null?void 0:K.chapter)||null}function ce(h){const L=h.match(/^(\d{4})(Q([1-4]))?$/);if(!L)return"0000_0";const K=L[1],se=L[3]||"5";return`${K}_${se}`}function ue(h){return[...h].sort((L,K)=>ce(K).localeCompare(ce(L)))}let A=D(()=>r(m).filter(h=>h.kind!=="text"));var j=$x(),ae=i(j);{var ve=h=>{var L=fm(),K=i(L);zr(K,{size:18,class:"animate-spin"}),c(h,L)},ze=h=>{var L=wx(),K=i(L);{var se=mt=>{var lt=gm(),gt=i(lt),er=i(gt);{var Se=We=>{var Ee=pm(),Ne=i(Ee);S(()=>$(Ne,`${r(y).length??""}개 기간 · ${r(y)[0]??""} ~ ${r(y)[r(y).length-1]??""}`)),c(We,Ee)};b(er,We=>{r(y).length>0&&We(Se)})}var pe=p(gt,2);Te(pe,17,()=>O(r(o).rows),Me,(We,Ee)=>{var Ne=hm(),Ve=i(Ne),vt=i(Ve);{var _e=$e=>{Sd($e,{size:11,class:"flex-shrink-0 opacity-40"})},Qe=D(()=>r(s).has(r(Ee).chapter)),kt=$e=>{Td($e,{size:11,class:"flex-shrink-0 opacity-40"})};b(vt,$e=>{r(Qe)?$e(_e):$e(kt,-1)})}var ft=p(vt,2),St=i(ft),rt=p(ft,2),Mt=i(rt),Pt=p(Ve,2);{var Kt=$e=>{var ct=xm();Te(ct,21,()=>r(Ee).topics,Me,(Jt,pr)=>{var zt=mm(),Ke=i(zt);{var Gt=ar=>{Cd(ar,{size:11,class:"flex-shrink-0 text-blue-400/40"})},Er=ar=>{Ks(ar,{size:11,class:"flex-shrink-0 text-emerald-400/40"})},Wr=ar=>{da(ar,{size:11,class:"flex-shrink-0 opacity-30"})};b(Ke,ar=>{r(pr).source==="finance"?ar(Gt):r(pr).source==="report"?ar(Er,1):ar(Wr,-1)})}var yr=p(Ke,2),Wt=i(yr);S(ar=>{qe(zt,1,`group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											${r(d)===r(pr).topic?"bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]":"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent"}`),$(Wt,ar)},[()=>G(r(pr).topic)]),oe("click",zt,()=>_(r(pr).topic,r(Ee).chapter)),c(Jt,zt)}),c($e,ct)},st=D(()=>r(s).has(r(Ee).chapter));b(Pt,$e=>{r(st)&&$e(Kt)})}S($e=>{$(St,$e),$(Mt,r(Ee).topics.length)},[()=>he(r(Ee).chapter)]),oe("click",Ve,()=>z(r(Ee).chapter)),c(We,Ne)}),c(mt,lt)};b(K,mt=>{r(V)||mt(se)})}var ne=p(K,2),Fe=i(ne);{var Be=mt=>{var lt=bm(),gt=i(lt);da(gt,{size:32,strokeWidth:1,class:"opacity-20"}),c(mt,lt)},Rt=mt=>{var lt=yx(),gt=re(lt),er=i(gt),Se=i(er);{var pe=rt=>{var Mt=_m(),Pt=i(Mt);S(Kt=>$(Pt,Kt),[()=>he(r(v)||M(r(d)))]),c(rt,Mt)},We=D(()=>r(v)||M(r(d)));b(Se,rt=>{r(We)&&rt(pe)})}var Ee=p(Se,2),Ne=i(Ee),Ve=p(er,2),vt=i(Ve);{var _e=rt=>{zd(rt,{size:15})},Qe=rt=>{Md(rt,{size:15})};b(vt,rt=>{r(V)?rt(_e):rt(Qe,-1)})}var kt=p(gt,2);{var ft=rt=>{var Mt=ym(),Pt=i(Mt);zr(Pt,{size:16,class:"animate-spin"}),c(rt,Mt)},St=rt=>{var Mt=_x(),Pt=i(Mt);{var Kt=zt=>{var Ke=wm();c(zt,Ke)};b(Pt,zt=>{var Ke,Gt;r(m).length===0&&!(((Gt=(Ke=r(x))==null?void 0:Ke.sections)==null?void 0:Gt.length)>0)&&zt(Kt)})}var st=p(Pt,2);{var $e=zt=>{var Ke=Jm(),Gt=i(Ke),Er=i(Gt),Wr=i(Er);{var yr=At=>{var Ze=km(),_t=i(Ze);S(Oe=>$(_t,`최신 기준 ${Oe??""}`),[()=>Ie(r(x).latestPeriod)]),c(At,Ze)};b(Wr,At=>{r(x).latestPeriod&&At(yr)})}var Wt=p(Wr,2);{var ar=At=>{var Ze=$m(),_t=i(Ze);S((Oe,Re)=>$(_t,`커버리지 ${Oe??""}~${Re??""}`),[()=>Ie(r(x).firstPeriod),()=>Ie(r(x).latestPeriod)]),c(At,Ze)};b(Wt,At=>{r(x).firstPeriod&&At(ar)})}var ta=p(Wt,2),nr=i(ta),Ft=p(ta,2);{var or=At=>{var Ze=Cm(),_t=i(Ze);S(()=>$(_t,`최근 수정 ${r(x).updatedCount??""}개`)),c(At,Ze)};b(Ft,At=>{r(x).updatedCount>0&&At(or)})}var tr=p(Ft,2);{var lr=At=>{var Ze=Sm(),_t=i(Ze);S(()=>$(_t,`신규 ${r(x).newCount??""}개`)),c(At,Ze)};b(tr,At=>{r(x).newCount>0&&At(lr)})}var cr=p(tr,2);{var mr=At=>{var Ze=Tm(),_t=i(Ze);S(()=>$(_t,`과거 유지 ${r(x).staleCount??""}개`)),c(At,Ze)};b(cr,At=>{r(x).staleCount>0&&At(mr)})}var Sr=p(Gt,2);Te(Sr,17,()=>r(x).sections,Me,(At,Ze)=>{const _t=D(()=>ee(r(Ze))),Oe=D(()=>q(r(Ze)));var Re=Ym(),Lt=i(Re);{var He=Ae=>{var Ce=zm();Te(Ce,21,()=>r(Ze).headingPath,Me,(Ue,Et)=>{var sr=Mm(),ur=i(sr);$a(ur,()=>R(r(Et).text)),c(Ue,sr)}),c(Ae,Ce)};b(Lt,Ae=>{var Ce;((Ce=r(Ze).headingPath)==null?void 0:Ce.length)>0&&Ae(He)})}var Ye=p(Lt,2),xt=i(Ye),jt=i(xt),Dt=p(xt,2);{var $t=Ae=>{var Ce=Am(),Ue=i(Ce);S(Et=>$(Ue,`최신 ${Et??""}`),[()=>Ie(r(Ze).latestPeriod)]),c(Ae,Ce)};b(Dt,Ae=>{var Ce;(Ce=r(Ze).latestPeriod)!=null&&Ce.label&&Ae($t)})}var Vt=p(Dt,2);{var bt=Ae=>{var Ce=Em(),Ue=i(Ce);S(Et=>$(Ue,`최초 ${Et??""}`),[()=>Ie(r(Ze).firstPeriod)]),c(Ae,Ce)};b(Vt,Ae=>{var Ce,Ue;(Ce=r(Ze).firstPeriod)!=null&&Ce.label&&r(Ze).firstPeriod.label!==((Ue=r(Ze).latestPeriod)==null?void 0:Ue.label)&&Ae(bt)})}var qt=p(Vt,2);{var Ir=Ae=>{var Ce=Im(),Ue=i(Ce);S(()=>$(Ue,`${r(Ze).periodCount??""}기간`)),c(Ae,Ce)};b(qt,Ae=>{r(Ze).periodCount>0&&Ae(Ir)})}var za=p(qt,2);{var Tr=Ae=>{var Ce=Nm(),Ue=i(Ce);S(()=>$(Ue,`최근 변경 ${r(Ze).latestChange??""}`)),c(Ae,Ce)};b(za,Ae=>{r(Ze).latestChange&&Ae(Tr)})}var Hr=p(Ye,2);{var wn=Ae=>{var Ce=Lm();Te(Ce,21,()=>r(Ze).timeline,Me,(Ue,Et)=>{var sr=Pm(),ur=i(sr),dr=i(ur);S((hr,vr)=>{qe(sr,1,`vw-timeline-chip ${hr??""}`,"svelte-1l2nqwu"),$(dr,vr)},[()=>Q(r(Ze),r(Et).period.label)?"is-active":"",()=>Ie(r(Et).period)]),oe("click",sr,()=>Y(r(Ze).id,r(Et).period.label)),c(Ue,sr)}),c(Ae,Ce)};b(Hr,Ae=>{var Ce;((Ce=r(Ze).timeline)==null?void 0:Ce.length)>0&&Ae(wn)})}var w=p(Hr,2);{var fe=Ae=>{var Ce=Dm(),Ue=i(Ce),Et=i(Ue),sr=p(Ue,2);{var ur=ie=>{var be=Om(),ut=i(be);S(Je=>$(ut,`비교 ${Je??""}`),[()=>Ie(r(_t).prevPeriod)]),c(ie,be)},dr=ie=>{var be=Rm();c(ie,be)};b(sr,ie=>{var be;(be=r(_t).prevPeriod)!=null&&be.label?ie(ur):ie(dr,-1)})}var hr=p(sr,2),vr=i(hr);S((ie,be)=>{$(Et,`선택 ${ie??""}`),$(vr,be)},[()=>Ie(r(_t).period),()=>ge(r(_t).status)]),c(Ae,Ce)};b(w,Ae=>{r(Oe)&&r(_t)&&Ae(fe)})}var Ge=p(w,2);{var it=Ae=>{const Ce=D(()=>r(_t).digest);var Ue=Fm(),Et=i(Ue),sr=i(Et),ur=i(sr),dr=p(Et,2),hr=i(dr);Te(hr,17,()=>r(Ce).items.filter(Je=>Je.kind==="numeric"),Me,(Je,ht)=>{var Xt=jm(),Bt=p(i(Xt));S(()=>$(Bt,` ${r(ht).text??""}`)),c(Je,Xt)});var vr=p(hr,2);Te(vr,17,()=>r(Ce).items.filter(Je=>Je.kind==="added"),Me,(Je,ht)=>{var Xt=Vm(),Bt=p(i(Xt),2),Yt=i(Bt);S(()=>$(Yt,r(ht).text)),c(Je,Xt)});var ie=p(vr,2);Te(ie,17,()=>r(Ce).items.filter(Je=>Je.kind==="removed"),Me,(Je,ht)=>{var Xt=qm(),Bt=p(i(Xt),2),Yt=i(Bt);S(()=>$(Yt,r(ht).text)),c(Je,Xt)});var be=p(ie,2);{var ut=Je=>{var ht=Bm(),Xt=i(ht);S(()=>$(Xt,`외 ${r(Ce).wordingCount??""}건 문구 수정`)),c(Je,ht)};b(be,Je=>{r(Ce).wordingCount>0&&Je(ut)})}S(()=>$(ur,`${r(Ce).to??""} vs ${r(Ce).from??""}`)),c(Ae,Ue)};b(Ge,Ae=>{var Ce,Ue,Et;r(Oe)&&((Et=(Ue=(Ce=r(_t))==null?void 0:Ce.digest)==null?void 0:Ue.items)==null?void 0:Et.length)>0&&Ae(it)})}var at=p(Ge,2);{var yt=Ae=>{var Ce=ke(),Ue=re(Ce);{var Et=ur=>{var dr=Gm();Te(dr,21,()=>Le(r(_t)),Me,(hr,vr)=>{var ie=ke(),be=re(ie);{var ut=Bt=>{var Yt=ke(),Br=re(Yt);$a(Br,()=>R(r(vr).text)),c(Bt,Yt)},Je=Bt=>{var Yt=Hm(),Br=i(Yt);S(()=>$(Br,r(vr).text)),c(Bt,Yt)},ht=Bt=>{var Yt=Um(),Br=i(Yt);S(()=>$(Br,r(vr).text)),c(Bt,Yt)},Xt=Bt=>{var Yt=Km(),Br=i(Yt);S(()=>$(Br,r(vr).text)),c(Bt,Yt)};b(be,Bt=>{r(vr).kind==="heading"?Bt(ut):r(vr).kind==="same"?Bt(Je,1):r(vr).kind==="added"?Bt(ht,2):r(vr).kind==="removed"&&Bt(Xt,3)})}c(hr,ie)}),c(ur,dr)},sr=ur=>{var dr=Wm(),hr=i(dr);$a(hr,()=>de(r(_t).body)),c(ur,dr)};b(Ue,ur=>{var dr,hr;r(Oe)&&((dr=r(_t).prevPeriod)!=null&&dr.label)&&((hr=r(_t).diff)==null?void 0:hr.length)>0?ur(Et):ur(sr,-1)})}c(Ae,Ce)};b(at,Ae=>{r(_t)&&Ae(yt)})}S((Ae,Ce)=>{qe(Re,1,`vw-text-section ${r(Ze).status==="stale"?"vw-text-section-stale":""}`,"svelte-1l2nqwu"),qe(xt,1,`vw-status-pill ${Ae??""}`,"svelte-1l2nqwu"),$(jt,Ce)},[()=>ye(r(Ze).status),()=>P(r(Ze).status)]),c(At,Re)}),S(()=>$(nr,`본문 ${r(x).sectionCount??""}개`)),c(zt,Ke)};b(st,zt=>{var Ke,Gt;((Gt=(Ke=r(x))==null?void 0:Ke.sections)==null?void 0:Gt.length)>0&&zt($e)})}var ct=p(st,2);{var Jt=zt=>{var Ke=Xm();c(zt,Ke)};b(ct,zt=>{r(A).length>0&&zt(Jt)})}var pr=p(ct,2);Te(pr,17,()=>r(A),Me,(zt,Ke)=>{var Gt=ke(),Er=re(Gt);{var Wr=nr=>{const Ft=D(()=>{var He;return((He=r(Ke).data)==null?void 0:He.columns)||[]}),or=D(()=>{var He;return((He=r(Ke).data)==null?void 0:He.rows)||[]}),tr=D(()=>r(Ke).meta||{}),lr=D(()=>r(tr).scaleDivisor||1);var cr=rx(),mr=re(cr);{var Sr=He=>{var Ye=Qm(),xt=i(Ye);S(()=>$(xt,`(단위: ${r(tr).scale??""})`)),c(He,Ye)};b(mr,He=>{r(tr).scale&&He(Sr)})}var At=p(mr,2),Ze=i(At),_t=i(Ze),Oe=i(_t),Re=i(Oe);Te(Re,21,()=>r(Ft),Me,(He,Ye,xt)=>{const jt=D(()=>/^\d{4}/.test(r(Ye)));var Dt=Zm(),$t=i(Dt);S(()=>{qe(Dt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${r(jt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${xt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),$($t,r(Ye))}),c(He,Dt)});var Lt=p(Oe);Te(Lt,21,()=>r(or),Me,(He,Ye,xt)=>{var jt=tx();qe(jt,1,`hover:bg-white/[0.03] ${xt%2===1?"bg-white/[0.012]":""}`),Te(jt,21,()=>r(Ft),Me,(Dt,$t,Vt)=>{const bt=D(()=>r(Ye)[r($t)]??""),qt=D(()=>Z(r(bt))),Ir=D(()=>tt(r(bt))),za=D(()=>r(qt)?pt(r(bt),r(lr)):r(bt));var Tr=ex(),Hr=i(Tr);S(()=>{qe(Tr,1,`px-3 py-1.5 border-b border-white/[0.025]
																	${r(qt)?"text-right tabular-nums font-mono text-[11.5px]":"whitespace-nowrap"}
																	${r(Ir)?"text-red-400/60":r(qt)?"text-dl-text/90":""}
																	${Vt===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]":"text-dl-text-muted"}
																	${Vt===0&&xt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),$(Hr,r(za))}),c(Dt,Tr)}),c(He,jt)}),c(nr,cr)},yr=nr=>{const Ft=D(()=>{var He;return((He=r(Ke).data)==null?void 0:He.columns)||[]}),or=D(()=>{var He;return((He=r(Ke).data)==null?void 0:He.rows)||[]}),tr=D(()=>r(Ke).meta||{}),lr=D(()=>r(tr).scaleDivisor||1);var cr=ix(),mr=re(cr);{var Sr=He=>{var Ye=ax(),xt=i(Ye);S(()=>$(xt,`(단위: ${r(tr).scale??""})`)),c(He,Ye)};b(mr,He=>{r(tr).scale&&He(Sr)})}var At=p(mr,2),Ze=i(At),_t=i(Ze),Oe=i(_t),Re=i(Oe);Te(Re,21,()=>r(Ft),Me,(He,Ye,xt)=>{const jt=D(()=>/^\d{4}/.test(r(Ye)));var Dt=nx(),$t=i(Dt);S(()=>{qe(Dt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${r(jt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${xt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),$($t,r(Ye))}),c(He,Dt)});var Lt=p(Oe);Te(Lt,21,()=>r(or),Me,(He,Ye,xt)=>{var jt=sx();qe(jt,1,`hover:bg-white/[0.03] ${xt%2===1?"bg-white/[0.012]":""}`),Te(jt,21,()=>r(Ft),Me,(Dt,$t,Vt)=>{const bt=D(()=>r(Ye)[r($t)]??""),qt=D(()=>Z(r(bt))),Ir=D(()=>tt(r(bt))),za=D(()=>r(qt)?r(lr)>1?pt(r(bt),r(lr)):dt(r(bt)):r(bt));var Tr=ox(),Hr=i(Tr);S(()=>{qe(Tr,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${r(qt)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${r(Ir)?"text-red-400/60":r(qt)?"text-dl-text/90":""}
																	${Vt===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Vt===0&&xt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),$(Hr,r(za))}),c(Dt,Tr)}),c(He,jt)}),c(nr,cr)},Wt=nr=>{const Ft=D(()=>ue(Object.keys(r(Ke).rawMarkdown))),or=D(()=>r(T).get(r(Ke).block)??0),tr=D(()=>r(Ft)[r(or)]||r(Ft)[0]);var lr=ux(),cr=i(lr);{var mr=_t=>{var Oe=cx(),Re=i(Oe);Te(Re,17,()=>r(Ft).slice(0,8),Me,(Ye,xt,jt)=>{var Dt=lx(),$t=i(Dt);S(()=>{qe(Dt,1,`px-2 py-0.5 rounded text-[10px] transition-colors
															${jt===r(or)?"bg-white/[0.08] text-dl-text font-medium":"text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]"}`),$($t,r(xt))}),oe("click",Dt,()=>J(r(Ke).block,jt)),c(Ye,Dt)});var Lt=p(Re,2);{var He=Ye=>{var xt=dx(),jt=i(xt);S(()=>$(jt,`외 ${r(Ft).length-8}개`)),c(Ye,xt)};b(Lt,Ye=>{r(Ft).length>8&&Ye(He)})}c(_t,Oe)};b(cr,_t=>{r(Ft).length>1&&_t(mr)})}var Sr=p(cr,2),At=i(Sr),Ze=i(At);$a(Ze,()=>bn(r(Ke).rawMarkdown[r(tr)])),c(nr,lr)},ar=nr=>{const Ft=D(()=>{var Oe;return((Oe=r(Ke).data)==null?void 0:Oe.columns)||[]}),or=D(()=>{var Oe;return((Oe=r(Ke).data)==null?void 0:Oe.rows)||[]});var tr=mx(),lr=i(tr),cr=i(lr);Ks(cr,{size:12,class:"text-emerald-400/50"});var mr=p(lr,2),Sr=i(mr),At=i(Sr),Ze=i(At);Te(Ze,21,()=>r(Ft),Me,(Oe,Re,Lt)=>{const He=D(()=>/^\d{4}/.test(r(Re)));var Ye=vx(),xt=i(Ye);S(()=>{qe(Ye,1,`px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															${r(He)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
															${Lt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),$(xt,r(Re))}),c(Oe,Ye)});var _t=p(At);Te(_t,21,()=>r(or),Me,(Oe,Re,Lt)=>{var He=px();qe(He,1,`hover:bg-white/[0.03] ${Lt%2===1?"bg-white/[0.012]":""}`),Te(He,21,()=>r(Ft),Me,(Ye,xt,jt)=>{const Dt=D(()=>r(Re)[r(xt)]??""),$t=D(()=>Z(r(Dt))),Vt=D(()=>tt(r(Dt)));var bt=fx(),qt=i(bt);S(Ir=>{qe(bt,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${r($t)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${r(Vt)?"text-red-400/60":r($t)?"text-dl-text/90":""}
																	${jt===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${jt===0&&Lt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),$(qt,Ir)},[()=>r($t)?dt(r(Dt)):r(Dt)]),c(Ye,bt)}),c(Oe,He)}),c(nr,tr)},ta=nr=>{const Ft=D(()=>r(Ke).data.columns),or=D(()=>r(Ke).data.rows||[]);var tr=bx(),lr=i(tr),cr=i(lr),mr=i(cr),Sr=i(mr);Te(Sr,21,()=>r(Ft),Me,(Ze,_t)=>{var Oe=xx(),Re=i(Oe);S(()=>$(Re,r(_t))),c(Ze,Oe)});var At=p(mr);Te(At,21,()=>r(or),Me,(Ze,_t,Oe)=>{var Re=gx();qe(Re,1,`hover:bg-white/[0.03] ${Oe%2===1?"bg-white/[0.012]":""}`),Te(Re,21,()=>r(Ft),Me,(Lt,He)=>{var Ye=hx(),xt=i(Ye);S(()=>$(xt,r(_t)[r(He)]??"")),c(Lt,Ye)}),c(Ze,Re)}),c(nr,tr)};b(Er,nr=>{var Ft,or;r(Ke).kind==="finance"?nr(Wr):r(Ke).kind==="structured"?nr(yr,1):r(Ke).kind==="raw_markdown"&&r(Ke).rawMarkdown?nr(Wt,2):r(Ke).kind==="report"?nr(ar,3):((or=(Ft=r(Ke).data)==null?void 0:Ft.columns)==null?void 0:or.length)>0&&nr(ta,4)})}c(zt,Gt)}),c(rt,Mt)};b(kt,rt=>{r(g)?rt(ft):rt(St,-1)})}S(rt=>{$(Ne,rt),Ca(Ve,"title",r(V)?"목차 표시":"전체화면")},[()=>G(r(d))]),oe("click",Ve,()=>u(V,!r(V))),c(mt,lt)};b(Fe,mt=>{r(d)?mt(Rt,-1):mt(Be)})}c(h,L)},we=h=>{var L=kx(),K=i(L);da(K,{size:36,strokeWidth:1,class:"opacity-20"}),c(h,L)};b(ae,h=>{var L;r(l)?h(ve):(L=r(o))!=null&&L.rows?h(ze,1):h(we,-1)})}c(e,j),_r()}Vr(["click"]);var Sx=f('<span class="text-[12px] font-semibold text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim"> </span>',1),Tx=f('<span class="text-[12px] font-semibold text-dl-text"> </span>'),Mx=f('<span class="text-[12px] font-semibold text-dl-text">데이터</span>'),zx=f('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" title="Excel 다운로드"><!></button> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button>',1),Ax=f('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Ex=f('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed"> </pre>'),Ix=f('<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2"> </div>'),Nx=f('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Px=f('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),Lx=f("<!> <!>",1),Ox=f('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),Rx=f('<div class="p-4"><!></div>'),Dx=f('<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">표시할 내용이 없습니다</div>'),jx=f('<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark"><div class="flex items-center justify-between h-10 mt-8 px-4 border-b border-dl-border/40 flex-shrink-0"><div class="flex items-center gap-2 min-w-0"><!></div> <div class="flex items-center gap-1"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 overflow-auto min-h-0"><!></div></div>');function Vx(e,t){br(t,!0);let a=je(t,"mode",3,null),n=je(t,"company",3,null),o=je(t,"data",3,null),l=je(t,"onTopicChange",3,null),s=je(t,"onFullscreen",3,null),d=je(t,"isFullscreen",3,!1),v=X(!1);async function m(){var P;if(!(!((P=n())!=null&&P.stockCode)||r(v))){u(v,!0);try{await cv(n().stockCode)}catch(ye){console.error("Excel download error:",ye)}u(v,!1)}}function x(P){return P?/^\|.+\|$/m.test(P)||/^#{1,3} /m.test(P)||/\*\*[^*]+\*\*/m.test(P)||/```/.test(P):!1}var g=jx(),y=i(g),E=i(y),C=i(E);{var V=P=>{var ye=Sx(),O=re(ye),U=i(O),F=p(O,2),me=i(F);S(()=>{$(U,n().corpName||n().company),$(me,n().stockCode)}),c(P,ye)},T=P=>{var ye=Tx(),O=i(ye);S(()=>$(O,o().label)),c(P,ye)},I=P=>{var ye=Mx();c(P,ye)};b(C,P=>{var ye;a()==="viewer"&&n()?P(V):a()==="data"&&((ye=o())!=null&&ye.label)?P(T,1):a()==="data"&&P(I,2)})}var N=p(E,2),H=i(N);{var k=P=>{var ye=zx(),O=re(ye),U=i(O);{var F=de=>{zr(de,{size:14,class:"animate-spin"})},me=de=>{Ao(de,{size:14})};b(U,de=>{r(v)?de(F):de(me,-1)})}var xe=p(O,2),le=i(xe);{var te=de=>{zd(de,{size:14})},Ie=de=>{Md(de,{size:14})};b(le,de=>{d()?de(te):de(Ie,-1)})}S(()=>{O.disabled=r(v),Ca(xe,"title",d()?"패널 모드로":"전체 화면")}),oe("click",O,m),oe("click",xe,()=>{var de;return(de=s())==null?void 0:de()}),c(P,ye)};b(H,P=>{var ye;a()==="viewer"&&((ye=n())!=null&&ye.stockCode)&&P(k)})}var G=p(H,2),he=i(G);gn(he,{size:15});var B=p(y,2),_=i(B);{var z=P=>{Cx(P,{get stockCode(){return n().stockCode},get onTopicChange(){return l()}})},Y=P=>{var ye=Rx(),O=i(ye);{var U=xe=>{var le=ke(),te=re(le);{var Ie=ee=>{var Q=Ax(),q=i(Q);$a(q,()=>bn(o())),c(ee,Q)},de=D(()=>x(o())),R=ee=>{var Q=Ex(),q=i(Q);S(()=>$(q,o())),c(ee,Q)};b(te,ee=>{r(de)?ee(Ie):ee(R,-1)})}c(xe,le)},F=xe=>{var le=Lx(),te=re(le);{var Ie=q=>{var ge=Ix(),Le=i(ge);S(()=>$(Le,o().module)),c(q,ge)};b(te,q=>{o().module&&q(Ie)})}var de=p(te,2);{var R=q=>{var ge=Nx(),Le=i(ge);$a(Le,()=>bn(o().text)),c(q,ge)},ee=D(()=>x(o().text)),Q=q=>{var ge=Px(),Le=i(ge);S(()=>$(Le,o().text)),c(q,ge)};b(de,q=>{r(ee)?q(R):q(Q,-1)})}c(xe,le)},me=xe=>{var le=Ox(),te=i(le);S(Ie=>$(te,Ie),[()=>JSON.stringify(o(),null,2)]),c(xe,le)};b(O,xe=>{var le;typeof o()=="string"?xe(U):(le=o())!=null&&le.text?xe(F,1):xe(me,-1)})}c(P,ye)},J=P=>{var ye=Dx();c(P,ye)};b(_,P=>{a()==="viewer"&&n()?P(z):a()==="data"&&o()?P(Y,1):P(J,-1)})}oe("click",G,()=>{var P;return(P=t.onClose)==null?void 0:P.call(t)}),c(e,g),_r()}Vr(["click"]);var qx=f('<div class="flex flex-col items-center justify-center py-8 gap-2"><!> <span class="text-[11px] text-dl-text-dim">목차 로딩 중...</span></div>'),Bx=f('<button><!> <span class="truncate"> </span></button>'),Fx=f('<div class="mb-1 pb-1 border-b border-dl-border/15"><div class="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-amber-400/70 uppercase tracking-wider"><!> <span>즐겨찾기</span></div> <!></div>'),Hx=f('<button class="flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors text-dl-text-dim hover:text-dl-text hover:bg-white/5"><!> <span class="truncate"> </span></button>'),Ux=f('<div class="mb-1 pb-1 border-b border-dl-border/15"><div class="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-dl-text-dim/60 uppercase tracking-wider"><!> <span>최근</span></div> <!></div>'),Kx=f('<span class="w-1.5 h-1.5 rounded-full bg-emerald-400/70" title="최근 변경"></span>'),Gx=f('<span class="text-[9px] text-dl-text-dim/60 font-mono"> </span>'),Wx=f('<button><!> <span class="truncate"> </span> <span class="ml-auto flex items-center gap-0.5"><!> <!> <!></span></button>'),Yx=f('<div class="ml-2 border-l border-dl-border/20 pl-1"></div>'),Jx=f('<div class="mb-0.5"><button class="flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-left text-[11px] font-semibold uppercase tracking-wider text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] text-dl-text-dim/60 font-mono"> </span></button> <!></div>'),Xx=f("<!> <!> <!>",1),Qx=f('<div class="px-3 py-6 text-center text-[12px] text-dl-text-dim">종목을 선택하면 목차가 표시됩니다</div>'),Zx=f('<nav class="flex flex-col h-full min-h-0 overflow-y-auto py-2 px-1"><!></nav>');function e1(e,t){br(t,!0);let a=je(t,"toc",3,null),n=je(t,"loading",3,!1),o=je(t,"selectedTopic",3,null),l=je(t,"expandedChapters",19,()=>new Set),s=je(t,"bookmarks",19,()=>[]),d=je(t,"recentHistory",19,()=>[]),v=je(t,"onSelectTopic",3,null),m=je(t,"onToggleChapter",3,null);const x=new Set(["BS","IS","CIS","CF","SCE","ratios"]);function g(N){return x.has(N)?Cd:da}function y(N){return N.tableCount>0&&N.textCount>0?"both":N.tableCount>0?"table":N.textCount>0?"text":"empty"}$r(()=>{o()&&Wl().then(()=>{const N=document.querySelector(".viewer-nav-active-item");N&&N.scrollIntoView({block:"nearest",behavior:"smooth"})})});var E=Zx(),C=i(E);{var V=N=>{var H=qx(),k=i(H);zr(k,{size:18,class:"animate-spin text-dl-text-dim"}),c(N,H)},T=N=>{var H=Xx(),k=re(H);{var G=z=>{const Y=D(()=>s().map(O=>{for(const U of a().chapters){const F=U.topics.find(me=>me.topic===O);if(F)return{...F,chapter:U.chapter}}return null}).filter(Boolean));var J=ke(),P=re(J);{var ye=O=>{var U=Fx(),F=i(U),me=i(F);Ys(me,{size:10,fill:"currentColor"});var xe=p(F,2);Te(xe,17,()=>r(Y),Me,(le,te)=>{const Ie=D(()=>o()===r(te).topic);var de=Bx(),R=i(de);Ys(R,{size:10,class:"text-amber-400/60 flex-shrink-0",fill:"currentColor"});var ee=p(R,2),Q=i(ee);S(()=>{qe(de,1,`flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors ${r(Ie)?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-muted hover:text-dl-text hover:bg-white/5"}`),$(Q,r(te).label)}),oe("click",de,()=>{var q;return(q=v())==null?void 0:q(r(te).topic,r(te).chapter)}),c(le,de)}),c(O,U)};b(P,O=>{r(Y).length>0&&O(ye)})}c(z,J)};b(k,z=>{s().length>0&&z(G)})}var he=p(k,2);{var B=z=>{const Y=D(()=>d().slice(0,5).filter(O=>O.topic!==o()));var J=ke(),P=re(J);{var ye=O=>{var U=Ux(),F=i(U),me=i(F);as(me,{size:10});var xe=p(F,2);Te(xe,17,()=>r(Y),Me,(le,te)=>{var Ie=Hx(),de=i(Ie);as(de,{size:10,class:"text-dl-text-dim/30 flex-shrink-0"});var R=p(de,2),ee=i(R);S(()=>$(ee,r(te).label)),oe("click",Ie,()=>{var Q;return(Q=v())==null?void 0:Q(r(te).topic,null)}),c(le,Ie)}),c(O,U)};b(P,O=>{r(Y).length>0&&O(ye)})}c(z,J)};b(he,z=>{d().length>0&&s().length===0&&z(B)})}var _=p(he,2);Te(_,17,()=>a().chapters,Me,(z,Y)=>{var J=Jx(),P=i(J),ye=i(P);{var O=ee=>{Sd(ee,{size:12})},U=D(()=>l().has(r(Y).chapter)),F=ee=>{Td(ee,{size:12})};b(ye,ee=>{r(U)?ee(O):ee(F,-1)})}var me=p(ye,2),xe=i(me),le=p(me,2),te=i(le),Ie=p(P,2);{var de=ee=>{var Q=Yx();Te(Q,21,()=>r(Y).topics,Me,(q,ge)=>{const Le=D(()=>g(r(ge).topic)),Z=D(()=>y(r(ge))),tt=D(()=>o()===r(ge).topic);var pt=Wx(),dt=i(pt);ci(dt,()=>r(Le),(h,L)=>{L(h,{size:12,class:"flex-shrink-0 opacity-50"})});var M=p(dt,2),ce=i(M),ue=p(M,2),A=i(ue);{var j=h=>{var L=Kx();c(h,L)};b(A,h=>{r(ge).hasChanges&&h(j)})}var ae=p(A,2);{var ve=h=>{Uf(h,{size:9,class:"text-dl-text-dim/40"})};b(ae,h=>{(r(Z)==="table"||r(Z)==="both")&&h(ve)})}var ze=p(ae,2);{var we=h=>{var L=Gx(),K=i(L);S(()=>$(K,r(ge).tableCount)),c(h,L)};b(ze,h=>{r(ge).tableCount>0&&h(we)})}S(()=>{qe(pt,1,`${r(tt)?"viewer-nav-active-item":""} viewer-nav-active flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors ${r(tt)?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-muted hover:text-dl-text hover:bg-white/5"}`),$(ce,r(ge).label)}),oe("click",pt,()=>{var h;return(h=v())==null?void 0:h(r(ge).topic,r(Y).chapter)}),c(q,pt)}),c(ee,Q)},R=D(()=>l().has(r(Y).chapter));b(Ie,ee=>{r(R)&&ee(de)})}S(()=>{$(xe,r(Y).chapter),$(te,r(Y).topics.length)}),oe("click",P,()=>{var ee;return(ee=m())==null?void 0:ee(r(Y).chapter)}),c(z,J)}),c(N,H)},I=N=>{var H=Qx();c(N,H)};b(C,N=>{var H;n()?N(V):(H=a())!=null&&H.chapters?N(T,1):N(I,-1)})}c(e,E),_r()}Vr(["click"]);var t1=f("<button> </button>"),r1=f('<div class="flex items-center gap-0.5 overflow-x-auto py-1 scrollbar-thin"></div>');function Nd(e,t){br(t,!0);let a=je(t,"periods",19,()=>[]),n=je(t,"selected",3,null),o=je(t,"onSelect",3,null);function l(x){return/^\d{4}$/.test(x)||/^\d{4}Q4$/.test(x)}function s(x){const g=x.match(/^(\d{4})(Q([1-4]))?$/);if(!g)return x;const y="'"+g[1].slice(2);return g[3]?`${y}.${g[3]}Q`:y}var d=ke(),v=re(d);{var m=x=>{var g=r1();Te(g,21,a,Me,(y,E)=>{var C=t1(),V=i(C);S((T,I)=>{qe(C,1,`flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] font-mono transition-colors
					${T??""}`),Ca(C,"title",r(E)),$(V,I)},[()=>n()===r(E)?"bg-dl-primary/20 text-dl-primary-light font-medium":l(r(E))?"text-dl-text-muted hover:text-dl-text hover:bg-white/5":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5",()=>s(r(E))]),oe("click",C,()=>{var T;return(T=o())==null?void 0:T(r(E))}),c(y,C)}),c(x,g)};b(v,x=>{a().length>0&&x(m)})}c(e,d),_r()}Vr(["click"]);var a1=f('<div class="mb-1"><!></div>'),n1=f('<!> <div class="text-[10px] text-dl-text-dim mb-1 font-mono"> </div> <div class="prose-dartlab overflow-x-auto"><!></div>',1),o1=f('<th class="cursor-pointer select-none hover:text-dl-text"> </th>'),s1=f("<td> </td>"),i1=f("<tr></tr>"),l1=f('<button class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"> </button>'),d1=f('<div class="text-[10px] text-dl-text-dim mt-1"> </div>'),c1=f('<div class="overflow-x-auto rounded-lg border border-dl-border/10"><table class="finance-table"><thead><tr></tr></thead><tbody></tbody></table> <!></div> <!>',1),u1=f('<th class="cursor-pointer select-none hover:text-dl-text"> </th>'),v1=f("<td> </td>"),f1=f("<tr></tr>"),p1=f('<button class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"> </button>'),m1=f('<div class="text-[10px] text-dl-text-dim mt-1"> </div>'),x1=f('<div class="overflow-x-auto rounded-lg border border-dl-border/10"><table class="prose-dartlab w-full text-[12px]"><thead><tr></tr></thead><tbody></tbody></table> <!></div> <!>',1);function tl(e,t){br(t,!0);let a=je(t,"block",3,null),n=je(t,"maxRows",3,100),o=X(null),l=X(!1),s=X(null),d=X("asc");function v(B){r(s)===B?u(d,r(d)==="asc"?"desc":"asc",!0):(u(s,B,!0),u(d,"asc"))}function m(B){return r(s)!==B?"":r(d)==="asc"?" ▲":" ▼"}const x=new Set(["매출액","revenue","영업이익","operating_income","당기순이익","net_income","자산총계","total_assets","부채총계","total_liabilities","자본총계","total_equity","영업활동현금흐름","operating_cash_flow","매출총이익","gross_profit","EBITDA"]);function g(B,_){if(!(_!=null&&_.length))return!1;const z=String(B[_[0]]??"").trim();return x.has(z)}function y(B){if(B==null||B===""||B==="-")return B??"";if(typeof B=="number")return Math.abs(B)>=1?B.toLocaleString("ko-KR"):B.toString();const _=String(B).trim();if(/^-?[\d,]+(\.\d+)?$/.test(_)){const z=parseFloat(_.replace(/,/g,""));if(!isNaN(z))return Math.abs(z)>=1?z.toLocaleString("ko-KR"):z.toString()}return B}function E(B){if(typeof B=="number")return B<0;const _=String(B??"").trim().replace(/,/g,"");return/^-\d/.test(_)}function C(B){return typeof B=="number"?!0:typeof B=="string"&&/^-?[\d,]+(\.\d+)?$/.test(B.trim())}function V(B){return(B==null?void 0:B.kind)==="finance"}function T(B){return B!=null&&B.rawMarkdown?Object.keys(B.rawMarkdown):[]}function I(B){const _=T(B);return r(o)&&_.includes(r(o))?r(o):_[0]??null}let N=D(()=>{var z,Y;const B=((Y=(z=a())==null?void 0:z.data)==null?void 0:Y.rows)??[];return r(s)?[...B].sort((J,P)=>{let ye=J[r(s)],O=P[r(s)];const U=typeof ye=="number"?ye:parseFloat(String(ye??"").replace(/,/g,"")),F=typeof O=="number"?O:parseFloat(String(O??"").replace(/,/g,""));return!isNaN(U)&&!isNaN(F)?r(d)==="asc"?U-F:F-U:(ye=String(ye??""),O=String(O??""),r(d)==="asc"?ye.localeCompare(O):O.localeCompare(ye))}):B}),H=D(()=>r(l)?r(N):r(N).slice(0,n()));var k=ke(),G=re(k);{var he=B=>{var _=ke(),z=re(_);{var Y=O=>{const U=D(()=>T(a())),F=D(()=>I(a()));var me=ke(),xe=re(me);{var le=te=>{var Ie=n1(),de=re(Ie);{var R=Le=>{var Z=a1(),tt=i(Z);Nd(tt,{get periods(){return r(U)},get selected(){return r(F)},onSelect:pt=>{u(o,pt,!0)}}),c(Le,Z)};b(de,Le=>{r(U).length>1&&Le(R)})}var ee=p(de,2),Q=i(ee),q=p(ee,2),ge=i(q);$a(ge,()=>bn(a().rawMarkdown[r(F)])),S(()=>$(Q,r(F))),c(te,Ie)};b(xe,te=>{r(U).length>0&&te(le)})}c(O,me)},J=O=>{var U=c1(),F=re(U),me=i(F),xe=i(me),le=i(xe);Te(le,21,()=>a().data.columns??[],Me,(Q,q)=>{var ge=o1(),Le=i(ge);S(Z=>$(Le,`${r(q)??""}${Z??""}`),[()=>m(r(q))]),oe("click",ge,()=>v(r(q))),c(Q,ge)});var te=p(xe);Te(te,21,()=>r(H),Me,(Q,q)=>{const ge=D(()=>g(r(q),a().data.columns));var Le=i1();Te(Le,21,()=>a().data.columns??[],Me,(Z,tt,pt)=>{const dt=D(()=>r(q)[r(tt)]),M=D(()=>pt>0&&C(r(dt)));var ce=s1(),ue=i(ce);S((A,j)=>{qe(ce,1,A),$(ue,j)},[()=>r(M)?E(r(dt))?"val-neg":"val-pos":"",()=>r(M)?y(r(dt)):r(dt)??""]),c(Z,ce)}),S(()=>qe(Le,1,Qt(r(ge)?"row-key":""))),c(Q,Le)});var Ie=p(me,2);{var de=Q=>{var q=l1(),ge=i(q);S(()=>$(ge,`외 ${a().data.rows.length-n()}행 더 보기`)),oe("click",q,()=>{u(l,!0)}),c(Q,q)};b(Ie,Q=>{!r(l)&&a().data.rows.length>n()&&Q(de)})}var R=p(F,2);{var ee=Q=>{var q=d1(),ge=i(q);S(()=>$(ge,`단위: ${(a().meta.unit||"")??""} ${a().meta.scale?`(${a().meta.scale})`:""}`)),c(Q,q)};b(R,Q=>{var q,ge;((q=a().meta)!=null&&q.scale||(ge=a().meta)!=null&&ge.unit)&&Q(ee)})}c(O,U)},P=D(()=>{var O;return V(a())&&((O=a().data)==null?void 0:O.rows)}),ye=O=>{var U=x1(),F=re(U),me=i(F),xe=i(me),le=i(xe);Te(le,21,()=>a().data.columns??[],Me,(Q,q)=>{var ge=u1(),Le=i(ge);S(Z=>$(Le,`${r(q)??""}${Z??""}`),[()=>m(r(q))]),oe("click",ge,()=>v(r(q))),c(Q,ge)});var te=p(xe);Te(te,21,()=>r(H),Me,(Q,q)=>{var ge=f1();Te(ge,21,()=>a().data.columns??[],Me,(Le,Z)=>{var tt=v1(),pt=i(tt);S(dt=>{qe(tt,1,dt),$(pt,r(q)[r(Z)]??"")},[()=>Qt(C(r(q)[r(Z)])?"num":"")]),c(Le,tt)}),c(Q,ge)});var Ie=p(me,2);{var de=Q=>{var q=p1(),ge=i(q);S(()=>$(ge,`외 ${a().data.rows.length-n()}행 더 보기`)),oe("click",q,()=>{u(l,!0)}),c(Q,q)};b(Ie,Q=>{!r(l)&&a().data.rows.length>n()&&Q(de)})}var R=p(F,2);{var ee=Q=>{var q=m1(),ge=i(q);S(()=>$(ge,`단위: ${(a().meta.unit||"")??""} ${a().meta.scale?`(${a().meta.scale})`:""}`)),c(Q,q)};b(R,Q=>{var q;(q=a().meta)!=null&&q.scale&&Q(ee)})}c(O,U)};b(z,O=>{var U;a().kind==="raw_markdown"&&a().rawMarkdown?O(Y):r(P)?O(J,1):(U=a().data)!=null&&U.rows&&O(ye,2)})}c(B,_)};b(G,B=>{a()&&B(he)})}c(e,k),_r()}Vr(["click"]);var h1=f('<span class="flex items-center gap-1"><!> <span class="text-dl-accent"> </span> <span class="text-dl-text-dim/60"> </span></span>'),g1=f('<span class="flex items-center gap-1"><!> <span>변경 없음</span></span>'),b1=f('<span class="flex items-center gap-1 ml-auto"><span class="font-mono"> </span> <!> <span class="font-mono"> </span></span>'),_1=f('<div class="text-dl-success/80 truncate"> </div>'),y1=f('<div class="text-dl-primary-light/70 truncate"> </div>'),w1=f('<div class="text-[11px] leading-relaxed"><!> <!></div>'),k1=f('<div class="flex flex-col gap-1.5 p-2.5 rounded-lg bg-dl-surface-card border border-dl-border/20"><div class="flex items-center gap-3 text-[11px] text-dl-text-dim"><span class="font-mono"> </span> <!> <!></div> <!></div>');function $1(e,t){br(t,!0);let a=je(t,"summary",3,null);var n=ke(),o=re(n);{var l=s=>{var d=k1(),v=i(d),m=i(v),x=i(m),g=p(m,2);{var y=N=>{var H=h1(),k=i(H);Yo(k,{size:11,class:"text-dl-accent"});var G=p(k,2),he=i(G),B=p(G,2),_=i(B);S(z=>{$(he,`변경 ${a().changedCount??""}회`),$(_,`(${z??""}%)`)},[()=>(a().changeRate*100).toFixed(1)]),c(N,H)},E=N=>{var H=g1(),k=i(H);Ad(k,{size:11}),c(N,H)};b(g,N=>{a().changedCount>0?N(y):N(E,-1)})}var C=p(g,2);{var V=N=>{var H=b1(),k=i(H),G=i(k),he=p(k,2);zf(he,{size:10});var B=p(he,2),_=i(B);S(()=>{$(G,a().latestFrom),$(_,a().latestTo)}),c(N,H)};b(C,N=>{a().latestFrom&&a().latestTo&&N(V)})}var T=p(v,2);{var I=N=>{var H=w1(),k=i(H);Te(k,17,()=>a().added.slice(0,2),Me,(he,B)=>{var _=_1(),z=i(_);S(()=>$(z,`+ ${r(B)??""}`)),c(he,_)});var G=p(k,2);Te(G,17,()=>a().removed.slice(0,2),Me,(he,B)=>{var _=y1(),z=i(_);S(()=>$(z,`- ${r(B)??""}`)),c(he,_)}),c(N,H)};b(T,N=>{var H,k;(((H=a().added)==null?void 0:H.length)>0||((k=a().removed)==null?void 0:k.length)>0)&&N(I)})}S(()=>$(x,`${a().totalPeriods??""} periods`)),c(s,d)};b(o,s=>{a()&&s(l)})}c(e,n),_r()}var C1=f("<option> </option>"),S1=f("<option> </option>"),T1=f('<button class="p-1 ml-1 text-dl-text-dim hover:text-dl-text"><!></button>'),M1=f('<span class="flex items-center gap-1 text-emerald-400"><!> <span> </span></span>'),z1=f('<span class="flex items-center gap-1 text-red-400"><!> <span> </span></span>'),A1=f('<span class="flex items-center gap-1 text-dl-text-dim"><!> <span> </span></span>'),E1=f('<div class="flex items-center gap-3 px-4 py-1.5 border-b border-dl-border/10 text-[10px]"><!> <!> <!></div>'),I1=f('<div class="flex items-center justify-center py-8 gap-2"><!> <span class="text-[12px] text-dl-text-dim">비교 로딩 중...</span></div>'),N1=f('<div class="text-[12px] text-red-400 py-4"> </div>'),P1=f('<div class="pl-3 py-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-dl-text/85 text-[13px] leading-[1.8] rounded-r"><span class="text-emerald-500/60 text-[10px] mr-1">+</span> </div>'),L1=f('<div class="pl-3 py-1 border-l-2 border-red-400 bg-red-500/5 text-dl-text/40 text-[13px] leading-[1.8] rounded-r line-through decoration-red-400/30"><span class="text-red-400/60 text-[10px] mr-1">-</span> </div>'),O1=f('<p class="text-[13px] leading-[1.8] text-dl-text/70 py-0.5"> </p>'),R1=f('<div class="space-y-0.5"></div>'),D1=f('<div class="text-[12px] text-dl-text-dim text-center py-4">비교할 기간을 선택하세요</div>'),j1=f('<div class="rounded-xl border border-dl-border/20 bg-dl-surface-card overflow-hidden"><div class="flex items-center gap-2 px-4 py-2 border-b border-dl-border/15 bg-dl-bg-darker/50"><!> <span class="text-[12px] font-semibold text-dl-text">기간 비교</span> <div class="flex items-center gap-1 ml-auto"><select class="px-2 py-0.5 rounded bg-dl-bg-darker border border-dl-border/20 text-[11px] text-dl-text outline-none"></select> <span class="text-[11px] text-dl-text-dim">→</span> <select class="px-2 py-0.5 rounded bg-dl-bg-darker border border-dl-border/20 text-[11px] text-dl-text outline-none"></select> <!></div></div> <!> <div class="max-h-[60vh] overflow-y-auto px-4 py-3"><!></div></div>');function V1(e,t){br(t,!0);let a=je(t,"stockCode",3,null),n=je(t,"topic",3,null),o=je(t,"periods",19,()=>[]),l=je(t,"onClose",3,null),s=X(null),d=X(null),v=X(null),m=X(!1),x=X(null);$r(()=>{o().length>=2&&!r(s)&&!r(d)&&(u(d,o()[0],!0),u(s,o()[1],!0))});async function g(){if(!(!a()||!n()||!r(s)||!r(d))){u(m,!0),u(x,null);try{const O=await xv(a(),n(),r(s),r(d));u(v,O,!0)}catch(O){u(x,O.message,!0)}u(m,!1)}}$r(()=>{r(s)&&r(d)&&r(s)!==r(d)&&g()});function y(O){if(!O)return"";const U=String(O).match(/^(\d{4})(Q([1-4]))?$/);return U?U[3]?`'${U[1].slice(2)}.${U[3]}Q`:`'${U[1].slice(2)}`:O}let E=D(()=>{var me,xe;if(!((me=r(v))!=null&&me.diff))return{added:0,removed:0,same:0};let O=0,U=0,F=0;for(const le of r(v).diff){const te=((xe=le.paragraphs)==null?void 0:xe.length)||1;le.kind==="added"?O+=te:le.kind==="removed"?U+=te:F+=te}return{added:O,removed:U,same:F}});var C=j1(),V=i(C),T=i(V);$d(T,{size:14,class:"text-dl-accent"});var I=p(T,4),N=i(I);Te(N,21,o,Me,(O,U)=>{var F=C1(),me=i(F),xe={};S(le=>{F.disabled=r(U)===r(d),$(me,le),xe!==(xe=r(U))&&(F.value=(F.__value=r(U))??"")},[()=>y(r(U))]),c(O,F)});var H=p(N,4);Te(H,21,o,Me,(O,U)=>{var F=S1(),me=i(F),xe={};S(le=>{F.disabled=r(U)===r(s),$(me,le),xe!==(xe=r(U))&&(F.value=(F.__value=r(U))??"")},[()=>y(r(U))]),c(O,F)});var k=p(H,2);{var G=O=>{var U=T1(),F=i(U);gn(F,{size:12}),oe("click",U,function(...me){var xe;(xe=l())==null||xe.apply(this,me)}),c(O,U)};b(k,O=>{l()&&O(G)})}var he=p(V,2);{var B=O=>{var U=E1(),F=i(U);{var me=de=>{var R=M1(),ee=i(R);Ws(ee,{size:10});var Q=p(ee,2),q=i(Q);S(()=>$(q,`추가 ${r(E).added??""}`)),c(de,R)};b(F,de=>{r(E).added>0&&de(me)})}var xe=p(F,2);{var le=de=>{var R=z1(),ee=i(R);Ad(ee,{size:10});var Q=p(ee,2),q=i(Q);S(()=>$(q,`삭제 ${r(E).removed??""}`)),c(de,R)};b(xe,de=>{r(E).removed>0&&de(le)})}var te=p(xe,2);{var Ie=de=>{var R=A1(),ee=i(R);Pf(ee,{size:10});var Q=p(ee,2),q=i(Q);S(()=>$(q,`유지 ${r(E).same??""}`)),c(de,R)};b(te,de=>{r(E).same>0&&de(Ie)})}c(O,U)};b(he,O=>{r(v)&&!r(m)&&O(B)})}var _=p(he,2),z=i(_);{var Y=O=>{var U=I1(),F=i(U);zr(F,{size:14,class:"animate-spin text-dl-text-dim"}),c(O,U)},J=O=>{var U=N1(),F=i(U);S(()=>$(F,r(x))),c(O,U)},P=O=>{var U=R1();Te(U,21,()=>r(v).diff,Me,(F,me)=>{var xe=ke(),le=re(xe);Te(le,17,()=>r(me).paragraphs||[r(me).text||""],Me,(te,Ie)=>{const de=D(()=>String(r(Ie)||"").trim());var R=ke(),ee=re(R);{var Q=q=>{var ge=ke(),Le=re(ge);{var Z=dt=>{var M=P1(),ce=p(i(M),1,!0);S(()=>$(ce,r(de))),c(dt,M)},tt=dt=>{var M=L1(),ce=p(i(M),1,!0);S(()=>$(ce,r(de))),c(dt,M)},pt=dt=>{var M=O1(),ce=i(M);S(()=>$(ce,r(de))),c(dt,M)};b(Le,dt=>{r(me).kind==="added"?dt(Z):r(me).kind==="removed"?dt(tt,1):dt(pt,-1)})}c(q,ge)};b(ee,q=>{r(de)&&q(Q)})}c(te,R)}),c(F,xe)}),c(O,U)},ye=O=>{var U=D1();c(O,U)};b(z,O=>{var U;r(m)?O(Y):r(x)?O(J,1):(U=r(v))!=null&&U.diff?O(P,2):O(ye,-1)})}Ri(N,()=>r(s),O=>u(s,O)),Ri(H,()=>r(d),O=>u(d,O)),c(e,C),_r()}Vr(["click"]);var q1=f("<button><!></button>"),B1=f("<button><!> <span>기간 비교</span></button>"),F1=f("<button><!> <span>AI 요약</span></button>"),H1=f('<div class="text-red-400/80"> </div>'),U1=f('<span class="inline-block w-1.5 h-3 bg-dl-accent/60 animate-pulse ml-0.5"></span>'),K1=f('<div class="whitespace-pre-wrap"> <!></div>'),G1=f('<div class="px-3 py-2 rounded-lg bg-dl-accent/5 border border-dl-accent/15 text-[12px] text-dl-text-muted leading-relaxed"><!></div>'),W1=f('<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim"> </span>'),Y1=f('<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim"> </span>'),J1=f('<span class="px-2 py-0.5 rounded-full border border-emerald-500/20 bg-emerald-500/8 text-emerald-400/80"> </span>'),X1=f('<span class="px-2 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/8 text-blue-400/80"> </span>'),Q1=f("<div> </div>"),Z1=f('<h4 class="text-[14px] font-semibold text-dl-text"> </h4>'),eh=f('<div class="mb-2 mt-2"></div>'),th=f('<span class="text-[10px] text-dl-text-dim font-mono"> </span>'),rh=f('<span class="text-[10px] text-dl-text-dim"> </span>'),ah=f('<span class="ml-0.5 text-emerald-400/50">*</span>'),nh=f("<button> <!></button>"),oh=f('<div class="flex flex-wrap gap-1 mb-2"></div>'),sh=f('<div class="text-blue-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-blue-400/60 mt-1.5 shrink-0"></span> </div>'),ih=f('<div class="text-emerald-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-emerald-400/50 mt-1.5 shrink-0"></span> </div>'),lh=f('<div class="text-dl-text-dim/50 flex gap-1"><span class="w-1 h-1 rounded-full bg-red-400/40 mt-1.5 shrink-0"></span> </div>'),dh=f('<div class="mb-3 px-3 py-2 rounded-lg border border-dl-border/15 bg-dl-surface-card/50 text-[11px] space-y-0.5 max-w-2xl"><div class="text-dl-text-dim font-medium"> </div> <!> <!> <!></div>'),ch=f('<p class="vw-para"> </p>'),uh=f('<div class="pl-3 py-1 mb-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-dl-text/85 text-[14px] leading-[1.85] rounded-r"><span class="text-emerald-500/50 text-[10px] mr-1">+</span> </div>'),vh=f('<div class="pl-3 py-1 mb-1 border-l-2 border-red-400 bg-red-500/5 text-dl-text/50 text-[14px] leading-[1.85] rounded-r line-through decoration-red-400/30"><span class="text-red-400/50 text-[10px] mr-1">-</span> </div>'),fh=f('<div><!> <div class="flex flex-wrap items-center gap-1.5 mb-2"><span> </span> <!> <!></div> <!> <!>  <div class="disclosure-text max-w-3xl"><!></div></div>'),ph=f('<div class="mt-6 pt-4 border-t border-dl-border/10"><div class="text-[10px] text-dl-text-dim uppercase tracking-widest font-semibold mb-3">표 · 정형 데이터</div></div>'),mh=f('<button class="absolute top-1 right-1 z-10 p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors opacity-0 group-hover:opacity-100" title="테이블 복사"><!></button>'),xh=f('<div class="group relative"><!> <!></div>'),hh=f('<div class="flex flex-wrap gap-1.5 text-[10px]"><!> <!> <!> <!></div> <!> <!> <!>',1),gh=f('<h3 class="text-[14px] font-semibold text-dl-text mt-4 mb-1"> </h3>'),bh=f('<div class="mb-1 opacity-0 group-hover:opacity-100 transition-opacity"><!></div>'),_h=f('<!> <div class="text-[10px] text-dl-text-dim mb-1 font-mono"> </div> <div class="disclosure-text"><!></div>',1),yh=f('<div class="group"><!></div>'),wh=f('<button class="absolute top-1 right-1 z-10 p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors opacity-0 group-hover:opacity-100" title="테이블 복사"><!></button>'),kh=f('<div class="group relative"><!> <!></div>'),$h=f('<div class="text-center py-12 text-[13px] text-dl-text-dim">이 topic에 표시할 데이터가 없습니다</div>'),Ch=f('<div class="space-y-4"><div class="flex items-center gap-2"><h2 class="text-[16px] font-semibold text-dl-text flex-1"> </h2> <!> <!> <!></div> <!> <!> <!> <!> <!></div>'),Sh=f('<button class="ask-ai-float"><span class="flex items-center gap-1"><!> AI에게 물어보기</span></button>'),Th=f("<!> <!>",1);function Mh(e,t){br(t,!0);let a=je(t,"topicData",3,null),n=je(t,"diffSummary",3,null),o=je(t,"viewer",3,null),l=je(t,"onAskAI",3,null),s=X(Ut(new Map)),d=X(Ut(new Map)),v=X(null),m=X(Ut({show:!1,x:0,y:0,text:""})),x=X(!1),g=X(""),y=X(null),E=X(null);$r(()=>{var M,ce,ue;if((M=a())!=null&&M.topic){u(x,!1),u(y,null);const A=(ue=(ce=o())==null?void 0:ce.getTopicSummary)==null?void 0:ue.call(ce,a().topic);u(g,A||"",!0),r(E)&&(r(E).abort(),u(E,null))}});function C(){var M,ce;!((M=o())!=null&&M.stockCode)||!((ce=a())!=null&&ce.topic)||(u(x,!0),u(g,""),u(y,null),u(E,bv(o().stockCode,a().topic,{onContext(){},onChunk(ue){u(g,r(g)+ue)},onDone(){var ue,A;u(x,!1),u(E,null),r(g)&&((A=(ue=o())==null?void 0:ue.setTopicSummary)==null||A.call(ue,a().topic,r(g)))},onError(ue){u(x,!1),u(E,null),u(y,ue,!0)}}),!0))}let V=D(()=>{var M,ce,ue;return((ue=(M=o())==null?void 0:M.isBookmarked)==null?void 0:ue.call(M,(ce=a())==null?void 0:ce.topic))??!1}),T=X(!1);$r(()=>{var M;(M=a())!=null&&M.topic&&u(T,!1)});let I=D(()=>{var ce,ue,A,j,ae,ve;if(!((A=(ue=(ce=a())==null?void 0:ce.textDocument)==null?void 0:ue.sections)!=null&&A.length))return[];const M=new Set;for(const ze of a().textDocument.sections)if(ze.timeline)for(const we of ze.timeline){const h=((j=we.period)==null?void 0:j.label)||((ae=we.period)!=null&&ae.year&&((ve=we.period)!=null&&ve.quarter)?`${we.period.year}Q${we.period.quarter}`:null);h&&M.add(h)}return[...M].sort().reverse()}),N=D(()=>{var M,ce,ue;return((ue=(ce=(M=a())==null?void 0:M.textDocument)==null?void 0:ce.sections)==null?void 0:ue.length)>0}),H=D(()=>{var M;return(((M=a())==null?void 0:M.blocks)??[]).filter(ce=>ce.kind!=="text")});function k(M){if(!M)return"";if(typeof M=="string"){const ce=M.match(/^(\d{4})(Q([1-4]))?$/);return ce?ce[3]?`${ce[1]}Q${ce[3]}`:ce[1]:M}return M.kind==="annual"?`${M.year}Q4`:M.year&&M.quarter?`${M.year}Q${M.quarter}`:M.label||""}function G(M){return M==="updated"?"수정됨":M==="new"?"신규":M==="stale"?"과거유지":"유지"}function he(M){return M==="updated"?"bg-emerald-500/10 text-emerald-400/80 border-emerald-500/20":M==="new"?"bg-blue-500/10 text-blue-400/80 border-blue-500/20":M==="stale"?"bg-amber-500/10 text-amber-400/80 border-amber-500/20":"bg-dl-border/10 text-dl-text-dim border-dl-border/20"}function B(M){var ue;const ce=r(d).get(M.id);return ce&&((ue=M.views)!=null&&ue[ce])?M.views[ce]:M.latest||null}function _(M,ce){var A,j;const ue=r(d).get(M.id);return ue?ue===ce:((j=(A=M.latest)==null?void 0:A.period)==null?void 0:j.label)===ce}function z(M){return r(d).has(M.id)}function Y(M,ce){const ue=new Map(r(d));ue.get(M)===ce?ue.delete(M):ue.set(M,ce),u(d,ue,!0)}function J(M){return M.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function P(M){return String(M||"").replace(/\u00a0/g," ").replace(/\s+/g," ").trim()}function ye(M){return!M||M.length>88?!1:/^\[.+\]$/.test(M)||/^【.+】$/.test(M)||/^[IVX]+\.\s/.test(M)||/^\d+\.\s/.test(M)||/^[가-힣]\.\s/.test(M)||/^\(\d+\)\s/.test(M)||/^\([가-힣]\)\s/.test(M)||/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(M)}function O(M){return/^[가나다라마바사아자차카타파하]\.\s/.test(M)?1:/^\d+\.\s/.test(M)?2:/^\(\d+\)\s/.test(M)||/^\([가-힣]\)\s/.test(M)?3:/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(M)?4:/^\[.+\]$/.test(M)||/^【.+】$/.test(M)?1:2}function U(M){if(!M)return"";if(/^\|.+\|$/m.test(M))return bn(M);const ce=M.split(`
`);let ue="",A=[];function j(){A.length!==0&&(ue+=`<p class="vw-para">${J(A.join(" "))}</p>`,A=[])}for(const ae of ce){const ve=P(ae);if(!ve){j();continue}if(ye(ve)){j();const ze=O(ve);ue+=`<div class="ko-h${ze}">${J(ve)}</div>`}else A.push(ve)}return j(),ue}function F(M){var ue;if(!((ue=M==null?void 0:M.diff)!=null&&ue.length))return null;const ce=[];for(const A of M.diff)for(const j of A.paragraphs||[])ce.push({kind:A.kind,text:P(j)});return ce}function me(M){return r(s).get(M)??null}function xe(M,ce){const ue=new Map(r(s));ue.set(M,ce),u(s,ue,!0)}function le(M,ce){var ue,A;return(A=(ue=M==null?void 0:M.data)==null?void 0:ue.rows)!=null&&A[0]?M.data.rows[0][ce]??null:null}function te(M){var ue,A,j;if(!((A=(ue=M==null?void 0:M.data)==null?void 0:ue.rows)!=null&&A[0]))return null;const ce=M.data.rows[0];for(const ae of((j=M.meta)==null?void 0:j.periods)??[])if(ce[ae])return{period:ae,text:ce[ae]};return null}function Ie(M){var ue,A,j;if(!((A=(ue=M==null?void 0:M.data)==null?void 0:ue.rows)!=null&&A[0]))return[];const ce=M.data.rows[0];return(((j=M.meta)==null?void 0:j.periods)??[]).filter(ae=>ce[ae]!=null)}function de(M){return M.kind==="text"}function R(M){return M.kind==="finance"||M.kind==="structured"||M.kind==="report"||M.kind==="raw_markdown"}function ee(M,ce){var j,ae;if(!((ae=(j=M==null?void 0:M.data)==null?void 0:j.rows)!=null&&ae.length))return;const ue=M.data.columns||[],A=[ue.join("	")];for(const ve of M.data.rows)A.push(ue.map(ze=>ve[ze]??"").join("	"));navigator.clipboard.writeText(A.join(`
`)).then(()=>{u(v,ce,!0),setTimeout(()=>{u(v,null)},2e3)})}function Q(M){if(!l())return;const ce=window.getSelection(),ue=ce==null?void 0:ce.toString().trim();if(!ue||ue.length<5){u(m,{show:!1,x:0,y:0,text:""},!0);return}const j=ce.getRangeAt(0).getBoundingClientRect();u(m,{show:!0,x:j.left+j.width/2,y:j.top-8,text:ue.slice(0,500)},!0)}function q(){r(m).text&&l()&&l()(r(m).text),u(m,{show:!1,x:0,y:0,text:""},!0)}function ge(){r(m).show&&u(m,{show:!1,x:0,y:0,text:""},!0)}var Le=Th();fn("click",zl,ge);var Z=re(Le);{var tt=M=>{var ce=Ch(),ue=i(ce),A=i(ue),j=i(A),ae=p(A,2);{var ve=Se=>{var pe=q1(),We=i(pe);{let Ee=D(()=>r(V)?"currentColor":"none");Ys(We,{size:14,get fill(){return r(Ee)}})}S(()=>{qe(pe,1,`p-1 rounded transition-colors ${r(V)?"text-amber-400":"text-dl-text-dim/30 hover:text-amber-400/60"}`),Ca(pe,"title",r(V)?"북마크 해제":"북마크 추가")}),oe("click",pe,()=>o().toggleBookmark(a().topic)),c(Se,pe)};b(ae,Se=>{o()&&Se(ve)})}var ze=p(ae,2);{var we=Se=>{var pe=B1(),We=i(pe);$d(We,{size:10}),S(()=>qe(pe,1,`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors border
						${r(T)?"border-dl-accent/30 bg-dl-accent/10 text-dl-accent-light":"border-dl-border/20 text-dl-text-dim hover:text-dl-text hover:bg-white/5"}`)),oe("click",pe,()=>{u(T,!r(T))}),c(Se,pe)};b(ze,Se=>{r(I).length>=2&&Se(we)})}var h=p(ze,2);{var L=Se=>{var pe=F1(),We=i(pe);{var Ee=Ve=>{zr(Ve,{size:10,class:"animate-spin"})},Ne=Ve=>{Ed(Ve,{size:10})};b(We,Ve=>{r(x)?Ve(Ee):Ve(Ne,-1)})}S(()=>{qe(pe,1,`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors border
						${r(x)?"border-dl-accent/30 bg-dl-accent/10 text-dl-accent-light":"border-dl-border/20 text-dl-text-dim hover:text-dl-text hover:bg-white/5"}`),pe.disabled=r(x)}),oe("click",pe,C),c(Se,pe)};b(h,Se=>{var pe;(pe=o())!=null&&pe.stockCode&&Se(L)})}var K=p(ue,2);{var se=Se=>{var pe=G1(),We=i(pe);{var Ee=Ve=>{var vt=H1(),_e=i(vt);S(()=>$(_e,r(y))),c(Ve,vt)},Ne=Ve=>{var vt=K1(),_e=i(vt),Qe=p(_e);{var kt=ft=>{var St=U1();c(ft,St)};b(Qe,ft=>{r(x)&&ft(kt)})}S(()=>$(_e,r(g))),c(Ve,vt)};b(We,Ve=>{r(y)?Ve(Ee):Ve(Ne,-1)})}c(Se,pe)};b(K,Se=>{(r(g)||r(x)||r(y))&&Se(se)})}var ne=p(K,2);$1(ne,{get summary(){return n()}});var Fe=p(ne,2);{var Be=Se=>{V1(Se,{get stockCode(){return o().stockCode},get topic(){return a().topic},get periods(){return r(I)},onClose:()=>{u(T,!1)}})};b(Fe,Se=>{var pe;r(T)&&((pe=o())!=null&&pe.stockCode)&&Se(Be)})}var Rt=p(Fe,2);{var mt=Se=>{const pe=D(()=>a().textDocument);var We=hh(),Ee=re(We),Ne=i(Ee);{var Ve=st=>{var $e=W1(),ct=i($e);S(Jt=>$(ct,`최신 ${Jt??""}`),[()=>k(r(pe).latestPeriod)]),c(st,$e)};b(Ne,st=>{r(pe).latestPeriod&&st(Ve)})}var vt=p(Ne,2);{var _e=st=>{var $e=Y1(),ct=i($e);S(()=>$(ct,`${r(pe).sectionCount??""}개 섹션`)),c(st,$e)};b(vt,st=>{r(pe).sectionCount&&st(_e)})}var Qe=p(vt,2);{var kt=st=>{var $e=J1(),ct=i($e);S(()=>$(ct,`${r(pe).updatedCount??""}개 수정`)),c(st,$e)};b(Qe,st=>{r(pe).updatedCount>0&&st(kt)})}var ft=p(Qe,2);{var St=st=>{var $e=X1(),ct=i($e);S(()=>$(ct,`${r(pe).newCount??""}개 신규`)),c(st,$e)};b(ft,st=>{r(pe).newCount>0&&st(St)})}var rt=p(Ee,2);Te(rt,17,()=>r(pe).sections,st=>st.id,(st,$e)=>{const ct=D(()=>B(r($e))),Jt=D(()=>z(r($e))),pr=D(()=>F(r(ct))),zt=D(()=>r(pr)&&r(pr).length>0),Ke=D(()=>r(zt)&&(r(Jt)||r($e).status==="updated"));var Gt=fh(),Er=i(Gt);{var Wr=Oe=>{var Re=eh();Te(Re,21,()=>r($e).headingPath,Me,(Lt,He)=>{const Ye=D(()=>{var $t;return($t=r(He).text)==null?void 0:$t.trim()});var xt=ke(),jt=re(xt);{var Dt=$t=>{var Vt=ke(),bt=re(Vt);{var qt=Tr=>{var Hr=Q1(),wn=i(Hr);S(w=>{qe(Hr,1,`ko-h${w??""}`),$(wn,r(Ye))},[()=>O(r(Ye))]),c(Tr,Hr)},Ir=D(()=>ye(r(Ye))),za=Tr=>{var Hr=Z1(),wn=i(Hr);S(()=>$(wn,r(Ye))),c(Tr,Hr)};b(bt,Tr=>{r(Ir)?Tr(qt):Tr(za,-1)})}c($t,Vt)};b(jt,$t=>{r(Ye)&&$t(Dt)})}c(Lt,xt)}),c(Oe,Re)};b(Er,Oe=>{var Re;((Re=r($e).headingPath)==null?void 0:Re.length)>0&&Oe(Wr)})}var yr=p(Er,2),Wt=i(yr),ar=i(Wt),ta=p(Wt,2);{var nr=Oe=>{var Re=th(),Lt=i(Re);S(()=>$(Lt,r($e).latestChange)),c(Oe,Re)};b(ta,Oe=>{r($e).latestChange&&Oe(nr)})}var Ft=p(ta,2);{var or=Oe=>{var Re=rh(),Lt=i(Re);S(()=>$(Lt,`${r($e).periodCount??""}기간`)),c(Oe,Re)};b(Ft,Oe=>{r($e).periodCount>1&&Oe(or)})}var tr=p(yr,2);{var lr=Oe=>{var Re=oh();Te(Re,21,()=>r($e).timeline,Me,(Lt,He)=>{const Ye=D(()=>{var Vt;return((Vt=r(He).period)==null?void 0:Vt.label)||k(r(He).period)});var xt=nh(),jt=i(xt),Dt=p(jt);{var $t=Vt=>{var bt=ah();c(Vt,bt)};b(Dt,Vt=>{r(He).status==="updated"&&Vt($t)})}S((Vt,bt)=>{qe(xt,1,`px-2 py-1 rounded-lg text-[10px] font-mono transition-colors border
										${Vt??""}`),$(jt,`${bt??""} `)},[()=>_(r($e),r(Ye))?"border-dl-accent/30 bg-dl-accent/8 text-dl-accent-light font-medium":r(He).status==="updated"?"border-emerald-500/15 text-emerald-400/60 hover:bg-emerald-500/5":"border-dl-border/15 text-dl-text-dim hover:bg-white/3",()=>k(r(He).period)]),oe("click",xt,()=>Y(r($e).id,r(Ye))),c(Lt,xt)}),c(Oe,Re)};b(tr,Oe=>{var Re;((Re=r($e).timeline)==null?void 0:Re.length)>1&&Oe(lr)})}var cr=p(tr,2);{var mr=Oe=>{const Re=D(()=>r(ct).digest);var Lt=dh(),He=i(Lt),Ye=i(He),xt=p(He,2);Te(xt,17,()=>r(Re).items.filter($t=>$t.kind==="numeric"),Me,($t,Vt)=>{var bt=sh(),qt=p(i(bt),1,!0);S(()=>$(qt,r(Vt).text)),c($t,bt)});var jt=p(xt,2);Te(jt,17,()=>r(Re).items.filter($t=>$t.kind==="added"),Me,($t,Vt)=>{var bt=ih(),qt=p(i(bt),1,!0);S(()=>$(qt,r(Vt).text)),c($t,bt)});var Dt=p(jt,2);Te(Dt,17,()=>r(Re).items.filter($t=>$t.kind==="removed"),Me,($t,Vt)=>{var bt=lh(),qt=p(i(bt),1,!0);S(()=>$(qt,r(Vt).text)),c($t,bt)}),S(()=>$(Ye,`${r(Re).to??""} vs ${r(Re).from??""}`)),c(Oe,Lt)};b(cr,Oe=>{var Re,Lt,He;((He=(Lt=(Re=r(ct))==null?void 0:Re.digest)==null?void 0:Lt.items)==null?void 0:He.length)>0&&Oe(mr)})}var Sr=p(cr,2),At=i(Sr);{var Ze=Oe=>{var Re=ke(),Lt=re(Re);Te(Lt,17,()=>r(pr),Me,(He,Ye)=>{var xt=ke(),jt=re(xt);{var Dt=bt=>{var qt=ch(),Ir=i(qt);S(()=>$(Ir,r(Ye).text)),c(bt,qt)},$t=bt=>{var qt=uh(),Ir=p(i(qt),1,!0);S(()=>$(Ir,r(Ye).text)),c(bt,qt)},Vt=bt=>{var qt=vh(),Ir=p(i(qt),1,!0);S(()=>$(Ir,r(Ye).text)),c(bt,qt)};b(jt,bt=>{r(Ye).kind==="same"?bt(Dt):r(Ye).kind==="added"?bt($t,1):r(Ye).kind==="removed"&&bt(Vt,2)})}c(He,xt)}),c(Oe,Re)},_t=Oe=>{var Re=ke(),Lt=re(Re);$a(Lt,()=>U(r(ct).body)),c(Oe,Re)};b(At,Oe=>{var Re;r(Ke)?Oe(Ze):(Re=r(ct))!=null&&Re.body&&Oe(_t,1)})}S((Oe,Re)=>{qe(Gt,1,`pt-2 pb-6 border-b border-dl-border/8 last:border-b-0 ${r($e).status==="stale"?"border-l-2 border-l-amber-400/40 pl-3":""}`),qe(Wt,1,`px-1.5 py-0.5 rounded text-[9px] font-medium border ${Oe??""}`),$(ar,Re)},[()=>he(r($e).status),()=>G(r($e).status)]),oe("mouseup",Sr,Q),c(st,Gt)});var Mt=p(rt,2);{var Pt=st=>{var $e=ph();c(st,$e)};b(Mt,st=>{r(H).length>0&&st(Pt)})}var Kt=p(Mt,2);Te(Kt,19,()=>r(H),st=>st.block,(st,$e)=>{var ct=xh(),Jt=i(ct);{var pr=Ke=>{var Gt=mh(),Er=i(Gt);{var Wr=Wt=>{Gs(Wt,{size:12,class:"text-dl-success"})},yr=Wt=>{Xi(Wt,{size:12})};b(Er,Wt=>{r(v)===r($e).block?Wt(Wr):Wt(yr,-1)})}oe("click",Gt,()=>ee(r($e),r($e).block)),c(Ke,Gt)};b(Jt,Ke=>{var Gt,Er;((Er=(Gt=r($e).data)==null?void 0:Gt.rows)==null?void 0:Er.length)>0&&Ke(pr)})}var zt=p(Jt,2);tl(zt,{get block(){return r($e)}}),c(st,ct)}),c(Se,We)},lt=Se=>{var pe=ke(),We=re(pe);Te(We,19,()=>a().blocks,Ee=>Ee.block,(Ee,Ne,Ve)=>{var vt=ke(),_e=re(vt);{var Qe=rt=>{const Mt=D(()=>me(r(Ve))),Pt=D(()=>te(r(Ne))),Kt=D(()=>Ie(r(Ne))),st=D(()=>{var zt;return r(Mt)||((zt=r(Pt))==null?void 0:zt.period)}),$e=D(()=>{var zt;return r(st)?le(r(Ne),r(st)):(zt=r(Pt))==null?void 0:zt.text});var ct=ke(),Jt=re(ct);{var pr=zt=>{var Ke=yh(),Gt=i(Ke);{var Er=yr=>{var Wt=gh(),ar=i(Wt);S(()=>$(ar,r($e))),c(yr,Wt)},Wr=yr=>{var Wt=_h(),ar=re(Wt);{var ta=lr=>{var cr=bh(),mr=i(cr);Nd(mr,{get periods(){return r(Kt)},get selected(){return r(st)},onSelect:Sr=>xe(r(Ve),Sr)}),c(lr,cr)};b(ar,lr=>{r(Kt).length>1&&lr(ta)})}var nr=p(ar,2),Ft=i(nr),or=p(nr,2),tr=i(or);$a(tr,()=>U(r($e))),S(()=>$(Ft,r(st))),oe("mouseup",or,Q),c(yr,Wt)};b(Gt,yr=>{r(Ne).textType==="heading"?yr(Er):yr(Wr,-1)})}c(zt,Ke)};b(Jt,zt=>{r($e)&&zt(pr)})}c(rt,ct)},kt=D(()=>de(r(Ne))),ft=rt=>{var Mt=kh(),Pt=i(Mt);{var Kt=$e=>{var ct=wh(),Jt=i(ct);{var pr=Ke=>{Gs(Ke,{size:12,class:"text-dl-success"})},zt=Ke=>{Xi(Ke,{size:12})};b(Jt,Ke=>{r(v)===r(Ne).block?Ke(pr):Ke(zt,-1)})}oe("click",ct,()=>ee(r(Ne),r(Ne).block)),c($e,ct)};b(Pt,$e=>{var ct,Jt;((Jt=(ct=r(Ne).data)==null?void 0:ct.rows)==null?void 0:Jt.length)>0&&$e(Kt)})}var st=p(Pt,2);tl(st,{get block(){return r(Ne)}}),c(rt,Mt)},St=D(()=>R(r(Ne)));b(_e,rt=>{r(kt)?rt(Qe):r(St)&&rt(ft,1)})}c(Ee,vt)}),c(Se,pe)};b(Rt,Se=>{r(N)?Se(mt):Se(lt,-1)})}var gt=p(Rt,2);{var er=Se=>{var pe=$h();c(Se,pe)};b(gt,Se=>{var pe;((pe=a().blocks)==null?void 0:pe.length)===0&&!r(N)&&Se(er)})}S(()=>$(j,a().topicLabel||"")),c(M,ce)};b(Z,M=>{a()&&M(tt)})}var pt=p(Z,2);{var dt=M=>{var ce=Sh(),ue=i(ce),A=i(ue);ns(A,{size:10}),S(()=>Zo(ce,`left: ${r(m).x??""}px; top: ${r(m).y??""}px; transform: translate(-50%, -100%)`)),oe("click",ce,q),c(M,ce)};b(pt,M=>{r(m).show&&M(dt)})}c(e,Le),_r()}Vr(["click","mouseup"]);var zh=f("<div> </div>"),Ah=f('<div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20"><!> <div class="text-[11px] text-red-400/90 space-y-0.5"></div></div>'),Eh=f("<div> </div>"),Ih=f('<div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-500/8 border border-amber-500/20"><!> <div class="text-[11px] text-amber-400/80 space-y-0.5"></div></div>'),Nh=f('<button><!> <span class="text-[10px] opacity-80"> </span> <span class="text-[14px] font-bold"> </span></button>'),Ph=f('<div class="flex items-start gap-1.5"><span class="w-1 h-1 rounded-full bg-dl-text-dim/40 mt-1.5 flex-shrink-0"></span> <span> </span></div>'),Lh=f('<div class="text-[11px] text-dl-text-muted space-y-0.5"></div>'),Oh=f("<div><!> <span> </span></div>"),Rh=f('<div class="text-[11px] space-y-0.5"></div>'),Dh=f("<div><!> <span> </span></div>"),jh=f('<div class="text-[11px] space-y-0.5"></div>'),Vh=f('<button class="text-[10px] px-1.5 py-0.5 rounded bg-dl-accent/8 text-dl-accent-light border border-dl-accent/20 hover:bg-dl-accent/15 transition-colors"> </button>'),qh=f('<div class="flex flex-wrap gap-1 pt-1 border-t border-dl-border/10"><span class="text-[10px] text-dl-text-dim mr-1">원문 보기:</span> <!></div>'),Bh=f('<div class="px-3 py-2 rounded-lg bg-dl-surface-card border border-dl-border/20 space-y-2 animate-fadeIn"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><span> </span> <span class="text-[12px] font-medium text-dl-text"> </span> <span class="text-[11px] text-dl-text-muted"> </span></div> <button class="p-0.5 text-dl-text-dim hover:text-dl-text"><!></button></div> <!> <!> <!> <!></div>'),Fh=f('<div class="text-[10px] text-dl-text-dim px-1"> </div>'),Hh=f('<div class="space-y-2"><!> <!> <div class="grid grid-cols-4 sm:grid-cols-7 gap-1.5"></div> <!> <!></div>');function Uh(e,t){br(t,!0);let a=je(t,"data",3,null),n=je(t,"loading",3,!1),o=je(t,"onNavigateTopic",3,null),l=X(null);const s={performance:{label:"실적",icon:Yo},profitability:{label:"수익성",icon:Ed},health:{label:"건전성",icon:Ff},cashflow:{label:"현금흐름",icon:Yf},governance:{label:"지배구조",icon:Wf},risk:{label:"리스크",icon:Jo},opportunity:{label:"기회",icon:Yo}},d={performance:["salesOrder","businessOverview"],profitability:["IS","CIS","ratios"],health:["BS","contingentLiability","corporateBond"],cashflow:["CF","ratios"],governance:["majorShareholder","audit","dividend"],risk:["contingentLiability","riskFactors","corporateBond"],opportunity:["businessOverview","investmentOverview"]};function v(k){return k==="A"?"bg-emerald-500/15 text-emerald-400 border-emerald-500/30":k==="B"?"bg-blue-500/15 text-blue-400 border-blue-500/30":k==="C"?"bg-amber-500/15 text-amber-400 border-amber-500/30":k==="D"?"bg-orange-500/15 text-orange-400 border-orange-500/30":k==="F"?"bg-red-500/15 text-red-400 border-red-500/30":"bg-dl-border/10 text-dl-text-dim border-dl-border/20"}function m(k){return k==="A"?"bg-emerald-500 text-white":k==="B"?"bg-blue-500 text-white":k==="C"?"bg-amber-500 text-white":k==="D"?"bg-orange-500 text-white":k==="F"?"bg-red-500 text-white":"bg-dl-border text-dl-text-dim"}function x(k){return k==="danger"?"text-red-400":k==="warning"?"text-amber-400":"text-dl-text-dim"}function g(k){return k==="strong"?"text-emerald-400":"text-blue-400"}function y(k){u(l,r(l)===k?null:k,!0)}let E=D(()=>{var k;return(((k=a())==null?void 0:k.anomalies)??[]).filter(G=>G.severity==="danger")}),C=D(()=>{var k;return(((k=a())==null?void 0:k.anomalies)??[]).filter(G=>G.severity==="warning")}),V=D(()=>{var k;return(k=a())!=null&&k.areas?Object.keys(s).filter(G=>a().areas[G]):[]});var T=ke(),I=re(T);{var N=k=>{},H=k=>{var G=Hh(),he=i(G);{var B=U=>{var F=Ah(),me=i(F);Mn(me,{size:14,class:"text-red-400 mt-0.5 flex-shrink-0"});var xe=p(me,2);Te(xe,21,()=>r(E),Me,(le,te)=>{var Ie=zh(),de=i(Ie);S(()=>$(de,r(te).text)),c(le,Ie)}),c(U,F)};b(he,U=>{r(E).length>0&&U(B)})}var _=p(he,2);{var z=U=>{var F=Ih(),me=i(F);Jo(me,{size:14,class:"text-amber-400 mt-0.5 flex-shrink-0"});var xe=p(me,2);Te(xe,21,()=>r(C),Me,(le,te)=>{var Ie=Eh(),de=i(Ie);S(()=>$(de,r(te).text)),c(le,Ie)}),c(U,F)};b(_,U=>{r(C).length>0&&U(z)})}var Y=p(_,2);Te(Y,21,()=>r(V),Me,(U,F)=>{const me=D(()=>s[r(F)]),xe=D(()=>a().areas[r(F)]),le=D(()=>r(me).icon);var te=Nh(),Ie=i(te);ci(Ie,()=>r(le),(q,ge)=>{ge(q,{size:13,class:"opacity-70"})});var de=p(Ie,2),R=i(de),ee=p(de,2),Q=i(ee);S(q=>{qe(te,1,`flex flex-col items-center gap-1 px-2 py-2 rounded-lg border transition-colors cursor-pointer ${q??""} ${r(l)===r(F)?"ring-1 ring-dl-accent/40":"hover:brightness-110"}`),$(R,r(me).label),$(Q,r(xe).grade)},[()=>v(r(xe).grade)]),oe("click",te,()=>y(r(F))),c(U,te)});var J=p(Y,2);{var P=U=>{const F=D(()=>a().areas[r(l)]),me=D(()=>s[r(l)]),xe=D(()=>d[r(l)]||[]);var le=Bh(),te=i(le),Ie=i(te),de=i(Ie),R=i(de),ee=p(de,2),Q=i(ee),q=p(ee,2),ge=i(q),Le=p(Ie,2),Z=i(Le);Ef(Z,{size:14});var tt=p(te,2);{var pt=ae=>{var ve=Lh();Te(ve,21,()=>r(F).details,Me,(ze,we)=>{var h=Ph(),L=p(i(h),2),K=i(L);S(()=>$(K,r(we))),c(ze,h)}),c(ae,ve)};b(tt,ae=>{var ve;((ve=r(F).details)==null?void 0:ve.length)>0&&ae(pt)})}var dt=p(tt,2);{var M=ae=>{var ve=Rh();Te(ve,21,()=>r(F).risks,Me,(ze,we)=>{var h=Oh(),L=i(h);Jo(L,{size:10,class:"mt-0.5 flex-shrink-0"});var K=p(L,2),se=i(K);S(ne=>{qe(h,1,`flex items-start gap-1.5 ${ne??""}`),$(se,r(we).text)},[()=>x(r(we).level)]),c(ze,h)}),c(ae,ve)};b(dt,ae=>{var ve;((ve=r(F).risks)==null?void 0:ve.length)>0&&ae(M)})}var ce=p(dt,2);{var ue=ae=>{var ve=jh();Te(ve,21,()=>r(F).opportunities,Me,(ze,we)=>{var h=Dh(),L=i(h);Yo(L,{size:10,class:"mt-0.5 flex-shrink-0"});var K=p(L,2),se=i(K);S(ne=>{qe(h,1,`flex items-start gap-1.5 ${ne??""}`),$(se,r(we).text)},[()=>g(r(we).level)]),c(ze,h)}),c(ae,ve)};b(ce,ae=>{var ve;((ve=r(F).opportunities)==null?void 0:ve.length)>0&&ae(ue)})}var A=p(ce,2);{var j=ae=>{var ve=qh(),ze=p(i(ve),2);Te(ze,17,()=>r(xe),Me,(we,h)=>{var L=Vh(),K=i(L);S(()=>$(K,r(h))),oe("click",L,()=>o()(r(h))),c(we,L)}),c(ae,ve)};b(A,ae=>{o()&&r(xe).length>0&&ae(j)})}S(ae=>{qe(de,1,`px-1.5 py-0.5 rounded text-[10px] font-bold ${ae??""}`),$(R,r(F).grade),$(Q,r(me).label),$(ge,`— ${r(F).summary??""}`)},[()=>m(r(F).grade)]),oe("click",Le,()=>{u(l,null)}),c(U,le)};b(J,U=>{r(l)&&a().areas[r(l)]&&U(P)})}var ye=p(J,2);{var O=U=>{var F=Fh(),me=i(F);S(()=>$(me,a().profile)),c(U,F)};b(ye,U=>{a().profile&&U(O)})}c(k,G)};b(I,k=>{n()?k(N):a()&&k(H,1)})}c(e,T),_r()}Vr(["click"]);var Kh=f('<div class="flex items-center justify-between text-[12px]"><span class="text-dl-text-muted"> </span> <kbd class="px-1.5 py-0.5 rounded bg-dl-bg-darker border border-dl-border/30 text-[11px] font-mono text-dl-text-dim min-w-[32px] text-center"> </kbd></div>'),Gh=f('<div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"><div class="bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl w-80 max-w-[90vw] overflow-hidden"><div class="flex items-center justify-between px-4 py-3 border-b border-dl-border/20"><div class="flex items-center gap-2 text-dl-text"><!> <span class="text-[13px] font-semibold">단축키</span></div> <button class="p-1 rounded text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="px-4 py-3 space-y-1.5"></div></div></div>');function Wh(e,t){let a=je(t,"show",3,!1),n=je(t,"onClose",3,null);const o=[{key:"?",desc:"단축키 도움말"},{key:"1",desc:"Chat 탭"},{key:"2",desc:"Viewer 탭"},{key:"Ctrl+K",desc:"종목 검색"},{key:"Ctrl+F",desc:"뷰어 내 검색"},{key:"J / ↓",desc:"다음 topic"},{key:"K / ↑",desc:"이전 topic"},{key:"S",desc:"현재 topic AI 요약"},{key:"B",desc:"북마크 토글"},{key:"Esc",desc:"모달/검색 닫기"}];var l=ke(),s=re(l);{var d=v=>{var m=Gh(),x=i(m),g=i(x),y=i(g),E=i(y);Rf(E,{size:16});var C=p(y,2),V=i(C);gn(V,{size:14});var T=p(g,2);Te(T,21,()=>o,Me,(I,N)=>{var H=Kh(),k=i(H),G=i(k),he=p(k,2),B=i(he);S(()=>{$(G,r(N).desc),$(B,r(N).key)}),c(I,H)}),oe("click",m,function(...I){var N;(N=n())==null||N.apply(this,I)}),oe("click",x,I=>I.stopPropagation()),oe("click",C,function(...I){var N;(N=n())==null||N.apply(this,I)}),c(v,m)};b(s,v=>{a()&&v(d)})}c(e,l)}Vr(["click"]);var Yh=f('<div class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"></div>'),Jh=f('<button class="p-1 rounded-md text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"><!></button>'),Xh=f('<div class="flex items-center justify-between"><div class="min-w-0"><div class="text-[12px] font-semibold text-dl-text truncate"> </div> <div class="text-[10px] font-mono text-dl-text-dim"> </div></div> <div class="flex items-center gap-0.5 flex-shrink-0"><!></div></div>'),Qh=f('<div class="text-[12px] text-dl-text-dim">종목 미선택</div>'),Zh=f('<div class="sticky top-0 z-20 px-6 py-2 bg-dl-bg-dark/95 backdrop-blur-sm border-b border-dl-border/10"><div class="max-w-2xl mx-auto"><button class="flex items-center gap-2 w-full px-3 py-1.5 rounded-lg border border-dl-border/20 bg-dl-bg-darker/60 text-[12px] text-dl-text-dim hover:border-dl-border/40 hover:bg-dl-bg-darker transition-colors"><!> <span class="flex-1 text-left">공시 섹션 검색... <kbd class="ml-2 px-1 py-0.5 rounded bg-dl-border/15 text-[10px] font-mono">/</kbd></span></button></div></div>'),eg=f('<button class="p-1 text-dl-text-dim hover:text-dl-text"><!></button>'),tg=f('<div class="text-[10px] text-dl-text-dim/60 mt-0.5"> </div>'),rg=f('<div class="text-[11px] text-dl-text-dim truncate mt-0.5"> </div>'),ag=f('<span class="text-[10px] text-dl-accent font-mono flex-shrink-0"> </span>'),ng=f('<button class="w-full text-left px-4 py-2 text-[13px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-start gap-2 border-b border-dl-border/5"><div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/50 font-mono"> </span></div> <!> <!></div> <!></button>'),og=f('<div class="flex items-center justify-center py-3"><!></div>'),sg=f("<!> <!>",1),ig=f('<div class="flex items-center justify-center py-6 gap-2"><!> <span class="text-[12px] text-dl-text-dim">검색 중...</span></div>'),lg=f('<div class="text-center py-6 text-[12px] text-dl-text-dim">결과 없음</div>'),dg=f('<button class="w-full text-left px-4 py-2 text-[13px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-2"><!> <span> </span> <span class="text-[10px] text-dl-text-dim/40 font-mono ml-auto"> </span></button>'),cg=f('<div class="px-4 py-2 text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold">최근 본 섹션</div> <!>',1),ug=f('<div class="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/50 backdrop-blur-sm"><div class="w-full max-w-xl bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl overflow-hidden"><div class="flex items-center gap-2 px-4 py-3 border-b border-dl-border/20"><!> <input placeholder="섹션, topic, 키워드 검색..." class="flex-1 bg-transparent text-[14px] text-dl-text outline-none placeholder:text-dl-text-dim"/> <!> <kbd class="px-1.5 py-0.5 rounded bg-dl-border/15 text-[10px] font-mono text-dl-text-dim">Esc</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div></div></div>'),vg=f('<span class="text-[11px] text-dl-text-muted truncate"> </span>'),fg=f('<div class="sticky top-0 z-30 flex items-center gap-2 px-3 py-1.5 bg-dl-bg-dark/95 border-b border-dl-border/20 backdrop-blur-sm"><button class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"><!> <span>목차</span></button> <button class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"><!> <span>검색</span></button> <!></div>'),pg=f('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[14px] text-dl-text-muted mb-1">공시 뷰어</div> <div class="text-[12px] text-dl-text-dim">종목을 검색하여 공시 문서를 살펴보세요</div></div>'),mg=f('<div class="flex flex-col items-center justify-center h-full"><!> <div class="text-[12px] text-dl-text-dim">공시 데이터 로딩 중...</div></div>'),xg=f('<div class="flex flex-col items-center justify-center h-full"><!> <div class="text-[11px] text-dl-text-dim">섹션 로딩 중...</div></div>'),hg=f('<div class="max-w-4xl mx-auto px-6 py-4 animate-fadeIn"><!> <div class="mt-4"><!></div></div>'),gg=f('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[13px] text-dl-text-dim">좌측 목차에서 항목을 선택하세요</div></div>'),bg=f('<div class="flex flex-col items-center justify-center h-full text-center px-8"><!> <div class="text-[13px] text-dl-text-dim">이 종목의 공시 데이터가 없습니다</div></div>'),_g=f('<div class="flex h-full min-h-0 bg-dl-bg-dark relative"><!> <div><div class="h-full flex flex-col"><div class="px-3 py-2 border-b border-dl-border/20 flex-shrink-0"><!></div> <!></div></div> <div class="flex-1 min-w-0 overflow-y-auto"><!> <!> <!> <!></div></div> <!>',1);function yg(e,t){br(t,!0);let a=je(t,"viewer",3,null),n=je(t,"company",3,null),o=je(t,"onAskAI",3,null),l=je(t,"onTopicChange",3,null),s=X(!1),d=X(!1),v=X(!1);function m(){u(d,typeof window<"u"&&window.innerWidth<=768,!0)}$r(()=>(m(),window.addEventListener("resize",m),()=>window.removeEventListener("resize",m)));let x=X(!1),g=X(""),y=X(null);function E(){u(x,!r(x)),r(x)?requestAnimationFrame(()=>{var A;return(A=r(y))==null?void 0:A.focus()}):(u(g,""),u(H,null))}$r(()=>{var A;(A=n())!=null&&A.stockCode&&a()&&a().loadCompany(n().stockCode)}),$r(()=>{var A,j,ae;(A=a())!=null&&A.selectedTopic&&((j=a())!=null&&j.topicData)&&((ae=l())==null||ae(a().selectedTopic,a().topicData.topicLabel||a().selectedTopic),N(a().selectedTopic,a().topicData.topicLabel||a().selectedTopic))});let C=X(Ut([]));const V=8;function T(){var A;try{const j=localStorage.getItem("dartlab-viewer-history");return(j?JSON.parse(j):{})[(A=n())==null?void 0:A.stockCode]||[]}catch{return[]}}function I(A){var j;try{const ae=localStorage.getItem("dartlab-viewer-history"),ve=ae?JSON.parse(ae):{};ve[(j=n())==null?void 0:j.stockCode]=A,localStorage.setItem("dartlab-viewer-history",JSON.stringify(ve))}catch{}}function N(A,j){var ve;if(!((ve=n())!=null&&ve.stockCode))return;const ae=r(C).filter(ze=>ze.topic!==A);u(C,[{topic:A,label:j,time:Date.now()},...ae].slice(0,V),!0),I(r(C))}$r(()=>{var A;(A=n())!=null&&A.stockCode&&u(C,T(),!0)});let H=X(null),k=X(!1),G=null;function he(){var j,ae;if(!((ae=(j=a())==null?void 0:j.toc)!=null&&ae.chapters))return[];const A=[];for(const ve of a().toc.chapters)for(const ze of ve.topics)A.push({topic:ze.topic,chapter:ve.chapter});return A}function B(A){var j,ae;if((ae=(j=a())==null?void 0:j.toc)!=null&&ae.chapters){for(const ve of a().toc.chapters)if(ve.topics.find(we=>we.topic===A)){a().selectTopic(A,ve.chapter);return}}}function _(A){var j,ae;if((ae=(j=a())==null?void 0:j.toc)!=null&&ae.chapters){for(const ve of a().toc.chapters)if(ve.topics.find(we=>we.topic===A)){a().selectTopic(A,ve.chapter),u(x,!1),u(g,""),u(H,null);return}}}function z(A){var ve,ze,we,h;const j=(ve=A.target)==null?void 0:ve.tagName,ae=j==="INPUT"||j==="TEXTAREA"||((ze=A.target)==null?void 0:ze.isContentEditable);if(A.key==="f"&&(A.ctrlKey||A.metaKey)&&n()){A.preventDefault(),E();return}if(A.key==="Escape"){if(r(v)){u(v,!1);return}if(r(x)){u(x,!1),u(g,""),u(H,null);return}return}if(!ae){if(A.key==="?"){u(v,!r(v));return}if(A.key==="/"&&n()){A.preventDefault(),E();return}if(!r(x)&&(A.key==="ArrowUp"||A.key==="ArrowDown"||A.key==="j"||A.key==="k")&&((we=a())!=null&&we.selectedTopic)){const L=he(),K=L.findIndex(Fe=>Fe.topic===a().selectedTopic);if(K<0)return;const ne=A.key==="ArrowDown"||A.key==="j"?K+1:K-1;ne>=0&&ne<L.length&&(A.preventDefault(),a().selectTopic(L[ne].topic,L[ne].chapter));return}if(A.key==="b"&&((h=a())!=null&&h.selectedTopic)){a().toggleBookmark(a().selectedTopic);return}}}$r(()=>{var ae,ve,ze;const A=r(g).trim();if(!A||!((ae=n())!=null&&ae.stockCode)){u(H,null);return}const j=[];if((ze=(ve=a())==null?void 0:ve.toc)!=null&&ze.chapters){const we=A.toLowerCase();for(const h of a().toc.chapters)for(const L of h.topics)(L.label.toLowerCase().includes(we)||L.topic.toLowerCase().includes(we))&&j.push({topic:L.topic,label:L.label,chapter:h.chapter,snippet:"",matchCount:0,source:"toc"})}u(H,j.length>0?j:null,!0),clearTimeout(G),A.length>=2&&(u(k,!0),G=setTimeout(async()=>{try{const we=await hv(n().stockCode,A);if(r(g).trim()!==A)return;const h=(we.results||[]).map(se=>({...se,source:"text"})),L=new Set(j.map(se=>se.topic)),K=[...j,...h.filter(se=>!L.has(se.topic))];u(H,K.length>0?K:null,!0)}catch{}u(k,!1)},300))});var Y=_g();fn("keydown",Qo,z);var J=re(Y),P=i(J);{var ye=A=>{var j=Yh();oe("click",j,()=>{u(s,!1)}),c(A,j)};b(P,A=>{r(d)&&r(s)&&A(ye)})}var O=p(P,2),U=i(O),F=i(U),me=i(F);{var xe=A=>{var j=Xh(),ae=i(j),ve=i(ae),ze=i(ve),we=p(ve,2),h=i(we),L=p(ae,2),K=i(L);{var se=ne=>{var Fe=Jh(),Be=i(Fe);gn(Be,{size:12}),oe("click",Fe,()=>{u(s,!1)}),c(ne,Fe)};b(K,ne=>{r(d)&&ne(se)})}S(()=>{$(ze,n().corpName||n().company),$(h,n().stockCode)}),c(A,j)},le=A=>{var j=Qh();c(A,j)};b(me,A=>{n()?A(xe):A(le,-1)})}var te=p(F,2);{let A=D(()=>{var we;return(we=a())==null?void 0:we.toc}),j=D(()=>{var we;return(we=a())==null?void 0:we.tocLoading}),ae=D(()=>{var we;return(we=a())==null?void 0:we.selectedTopic}),ve=D(()=>{var we;return(we=a())==null?void 0:we.expandedChapters}),ze=D(()=>{var we,h;return((h=(we=a())==null?void 0:we.getBookmarks)==null?void 0:h.call(we))??[]});e1(te,{get toc(){return r(A)},get loading(){return r(j)},get selectedTopic(){return r(ae)},get expandedChapters(){return r(ve)},get bookmarks(){return r(ze)},get recentHistory(){return r(C)},onSelectTopic:(we,h)=>{var L;(L=a())==null||L.selectTopic(we,h),r(d)&&u(s,!1)},onToggleChapter:we=>{var h;return(h=a())==null?void 0:h.toggleChapter(we)}})}var Ie=p(O,2),de=i(Ie);{var R=A=>{var j=Zh(),ae=i(j),ve=i(ae),ze=i(ve);mn(ze,{size:13,class:"flex-shrink-0"}),oe("click",ve,E),c(A,j)};b(de,A=>{n()&&!r(d)&&A(R)})}var ee=p(de,2);{var Q=A=>{var j=ug(),ae=i(j),ve=i(ae),ze=i(ve);mn(ze,{size:16,class:"text-dl-text-dim flex-shrink-0"});var we=p(ze,2);pn(we,lt=>u(y,lt),()=>r(y));var h=p(we,2);{var L=lt=>{var gt=eg(),er=i(gt);gn(er,{size:14}),oe("click",gt,()=>{u(g,"")}),c(lt,gt)};b(h,lt=>{r(g)&&lt(L)})}var K=p(ve,2),se=i(K);{var ne=lt=>{var gt=sg(),er=re(gt);Te(er,17,()=>r(H).slice(0,15),Me,(We,Ee)=>{var Ne=ng(),Ve=i(Ne),vt=i(Ve),_e=i(vt),Qe=i(_e),kt=p(_e,2),ft=i(kt),St=p(vt,2);{var rt=$e=>{var ct=tg(),Jt=i(ct);S(()=>$(Jt,r(Ee).chapter)),c($e,ct)};b(St,$e=>{r(Ee).chapter&&$e(rt)})}var Mt=p(St,2);{var Pt=$e=>{var ct=rg(),Jt=i(ct);S(()=>$(Jt,r(Ee).snippet)),c($e,ct)};b(Mt,$e=>{r(Ee).snippet&&$e(Pt)})}var Kt=p(Ve,2);{var st=$e=>{var ct=ag(),Jt=i(ct);S(()=>$(Jt,`${r(Ee).matchCount??""}건`)),c($e,ct)};b(Kt,$e=>{r(Ee).matchCount>0&&$e(st)})}S(()=>{$(Qe,r(Ee).label),$(ft,r(Ee).topic)}),oe("click",Ne,()=>_(r(Ee).topic)),c(We,Ne)});var Se=p(er,2);{var pe=We=>{var Ee=og(),Ne=i(Ee);zr(Ne,{size:14,class:"animate-spin text-dl-text-dim"}),c(We,Ee)};b(Se,We=>{r(k)&&We(pe)})}c(lt,gt)},Fe=lt=>{var gt=ig(),er=i(gt);zr(er,{size:14,class:"animate-spin text-dl-text-dim"}),c(lt,gt)},Be=lt=>{var gt=lg();c(lt,gt)},Rt=D(()=>r(g).trim()),mt=lt=>{var gt=ke(),er=re(gt);{var Se=pe=>{var We=cg(),Ee=p(re(We),2);Te(Ee,17,()=>r(C),Me,(Ne,Ve)=>{var vt=dg(),_e=i(vt);as(_e,{size:12,class:"text-dl-text-dim/40 flex-shrink-0"});var Qe=p(_e,2),kt=i(Qe),ft=p(Qe,2),St=i(ft);S(()=>{$(kt,r(Ve).label),$(St,r(Ve).topic)}),oe("click",vt,()=>_(r(Ve).topic)),c(Ne,vt)}),c(pe,We)};b(er,pe=>{r(C).length>0&&pe(Se)})}c(lt,gt)};b(se,lt=>{r(H)?lt(ne):r(k)?lt(Fe,1):r(Rt)?lt(Be,2):lt(mt,-1)})}oe("click",j,()=>{u(x,!1),u(g,""),u(H,null)}),oe("click",ae,lt=>lt.stopPropagation()),Nn(we,()=>r(g),lt=>u(g,lt)),c(A,j)};b(ee,A=>{r(x)&&A(Q)})}var q=p(ee,2);{var ge=A=>{var j=fg(),ae=i(j),ve=i(ae);da(ve,{size:11});var ze=p(ae,2),we=i(ze);mn(we,{size:11});var h=p(ze,2);{var L=K=>{var se=vg(),ne=i(se);S(()=>{var Fe,Be,Rt;return $(ne,((Be=(Fe=a())==null?void 0:Fe.topicData)==null?void 0:Be.topicLabel)||((Rt=a())==null?void 0:Rt.selectedTopic))}),c(K,se)};b(h,K=>{var se;(se=a())!=null&&se.selectedTopic&&K(L)})}oe("click",ae,()=>{u(s,!0)}),oe("click",ze,E),c(A,j)};b(q,A=>{r(d)&&n()&&A(ge)})}var Le=p(q,2);{var Z=A=>{var j=pg(),ae=i(j);da(ae,{size:32,class:"text-dl-text-dim/30 mb-3"}),c(A,j)},tt=A=>{var j=mg(),ae=i(j);zr(ae,{size:24,class:"animate-spin text-dl-text-dim/40 mb-3"}),c(A,j)},pt=A=>{var j=xg(),ae=i(j);zr(ae,{size:20,class:"animate-spin text-dl-text-dim/40 mb-2"}),c(A,j)},dt=A=>{var j=hg(),ae=i(j);Uh(ae,{get data(){return a().insightData},get loading(){return a().insightLoading},onNavigateTopic:B});var ve=p(ae,2),ze=i(ve);Mh(ze,{get topicData(){return a().topicData},get diffSummary(){return a().diffSummary},get viewer(){return a()},get onAskAI(){return o()}}),c(A,j)},M=A=>{var j=gg(),ae=i(j);da(ae,{size:28,class:"text-dl-text-dim/30 mb-3"}),c(A,j)},ce=A=>{var j=bg(),ae=i(j);Mn(ae,{size:28,class:"text-dl-text-dim/30 mb-3"}),c(A,j)};b(Le,A=>{var j,ae,ve,ze,we,h,L,K;n()?(j=a())!=null&&j.tocLoading?A(tt,1):(ae=a())!=null&&ae.topicLoading?A(pt,2):(ve=a())!=null&&ve.topicData?A(dt,3):(ze=a())!=null&&ze.toc&&!((we=a())!=null&&we.selectedTopic)?A(M,4):((K=(L=(h=a())==null?void 0:h.toc)==null?void 0:L.chapters)==null?void 0:K.length)===0&&A(ce,5):A(Z)})}var ue=p(J,2);Wh(ue,{get show(){return r(v)},onClose:()=>{u(v,!1)}}),S(()=>qe(O,1,`${r(d)?`fixed top-0 left-0 bottom-0 z-50 w-64 transition-transform duration-200 ${r(s)?"translate-x-0":"-translate-x-full"}`:"flex-shrink-0 w-56"} border-r border-dl-border/30 overflow-hidden bg-dl-bg-dark`)),c(e,Y),_r()}Vr(["click"]);var wg=f('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),kg=f("<!> <span>확인 중...</span>",1),$g=f("<!> <span>설정 필요</span>",1),Cg=f('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),Sg=f('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!>',1),Tg=f('<div class="min-w-0 flex-1 pt-10"><!></div>'),Mg=f('<div class="flex-shrink-0 border-l border-dl-border/30 transition-all duration-300"><!></div>'),zg=f('<div class="min-w-0 flex-1 flex flex-col"><!></div> <!>',1),Ag=f('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),Eg=f('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),Ig=f('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),Ng=f('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),Pg=f('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),Lg=f('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),Og=f('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),Rg=f('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),Dg=f('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),jg=f('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),Vg=f('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),qg=f('<div class="text-[10px] text-dl-text-dim mt-2"> </div>'),Bg=f('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex login</div></div></div></div> <!> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),Fg=f('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2"> </div></div>'),Hg=f('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 계정 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),Ug=f('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),Kg=f("<button> <!></button>"),Gg=f('<div class="flex flex-wrap gap-1.5"></div>'),Wg=f('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),Yg=f('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),Jg=f('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),Xg=f('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),Qg=f('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),Zg=f('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),eb=f('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),tb=f("<!> <!> <!> <!> <!> <!>",1),rb=f('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),ab=f('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),nb=f('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),ob=f('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><span class="text-[10px] text-dl-text-dim">공시 보기</span> <!></div></button>'),sb=f('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div></div> <!>',1),ib=f('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div></button>'),lb=f('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div></div> <!>',1),db=f('<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),cb=f('<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim"><!> <div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div> <div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div></div>'),ub=f('<div class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn" role="presentation"><div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"><div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"/> <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div> <div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim"><span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span></div></div></div>'),vb=f('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),fb=f('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-2 left-3 z-20 pointer-events-auto flex items-center gap-1"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center ml-2 rounded-lg bg-dl-bg-card/60 border border-dl-border/20 p-0.5"><button><!> <span>Chat</span></button> <button><!> <span>Viewer</span></button></div></div> <div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="종목 검색 (Ctrl+K)"><!></button> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <button><!> <!></button></div> <div class="flex flex-1 min-h-0"><!></div></div></div>  <!> <!> <!> <!>',1);function pb(e,t){br(t,!0);let a=X(""),n=X(!1),o=X(null),l=X(Ut({})),s=X(Ut({})),d=X(null),v=X(null),m=X(Ut([])),x=X(!1),g=X(0),y=X(!0),E=X(""),C=X(!1),V=X(null),T=X(Ut({})),I=X(Ut({})),N=X(""),H=X(!1),k=X(null),G=X(""),he=X(!1),B=X(""),_=X(0),z=X(null),Y=X(null),J=X(null);const P=gf(),ye=yf();let O=X(!1),U=D(()=>r(O)?"100%":P.panelMode==="viewer"?"65%":"50%"),F=X(!1),me=X(""),xe=X(Ut([])),le=X(-1),te=null,Ie=X(null),de=X(!1);function R(){u(de,window.innerWidth<=768),r(de)&&(u(x,!1),P.closePanel())}$r(()=>(R(),window.addEventListener("resize",R),()=>window.removeEventListener("resize",R))),$r(()=>{!r(C)||!r(Y)||requestAnimationFrame(()=>{var w;return(w=r(Y))==null?void 0:w.focus()})}),$r(()=>{!r(ee)||!r(J)||requestAnimationFrame(()=>{var w;return(w=r(J))==null?void 0:w.focus()})}),$r(()=>{!r(F)||!r(Ie)||requestAnimationFrame(()=>{var w;return(w=r(Ie))==null?void 0:w.focus()})});let ee=X(null),Q=X(""),q=X("error"),ge=X(!1);function Le(w,fe="error",Ge=4e3){u(Q,w,!0),u(q,fe,!0),u(ge,!0),setTimeout(()=>{u(ge,!1)},Ge)}const Z=pf();$r(()=>{A()});let tt=X(Ut({}));function pt(w){return w==="chatgpt"?"codex":w}function dt(w){return`dartlab-api-key:${pt(w)}`}function M(w){return typeof sessionStorage>"u"||!w?"":sessionStorage.getItem(dt(w))||""}function ce(w,fe){typeof sessionStorage>"u"||!w||(fe?sessionStorage.setItem(dt(w),fe):sessionStorage.removeItem(dt(w)))}async function ue(w,fe=null,Ge=null){var at;const it=await sv(w,fe,Ge);if(it!=null&&it.provider){const yt=pt(it.provider);u(l,{...r(l),[yt]:{...r(l)[yt]||{},available:!!it.available,model:it.model||((at=r(l)[yt])==null?void 0:at.model)||fe||null}},!0)}return it}async function A(){var w,fe,Ge;u(y,!0);try{const it=await ov();u(l,it.providers||{},!0),u(s,it.ollama||{},!0),u(tt,it.codex||{},!0),it.version&&u(E,it.version,!0);const at=pt(localStorage.getItem("dartlab-provider")),yt=localStorage.getItem("dartlab-model"),Ae=M(at);if(at&&((w=r(l)[at])!=null&&w.available)){u(d,at,!0),u(V,at,!0),u(N,Ae,!0),await j(at);const Ce=r(T)[at]||[];yt&&Ce.includes(yt)?u(v,yt,!0):Ce.length>0&&(u(v,Ce[0],!0),localStorage.setItem("dartlab-model",r(v))),u(m,Ce,!0),u(y,!1);return}if(at&&r(l)[at]){if(u(d,at,!0),u(V,at,!0),u(N,Ae,!0),Ae)try{await ue(at,yt,Ae)}catch{}await j(at);const Ce=r(T)[at]||[];u(m,Ce,!0),yt&&Ce.includes(yt)?u(v,yt,!0):Ce.length>0&&u(v,Ce[0],!0),u(y,!1);return}for(const Ce of["codex","ollama","openai"])if((fe=r(l)[Ce])!=null&&fe.available){u(d,Ce,!0),u(V,Ce,!0),u(N,M(Ce),!0),await j(Ce);const Ue=r(T)[Ce]||[];u(m,Ue,!0),u(v,((Ge=r(l)[Ce])==null?void 0:Ge.model)||(Ue.length>0?Ue[0]:null),!0),r(v)&&localStorage.setItem("dartlab-model",r(v));break}}catch{}u(y,!1)}async function j(w){w=pt(w),u(I,{...r(I),[w]:!0},!0);try{const fe=await iv(w);u(T,{...r(T),[w]:fe.models||[]},!0)}catch{u(T,{...r(T),[w]:[]},!0)}u(I,{...r(I),[w]:!1},!0)}async function ae(w){var Ge;w=pt(w),u(d,w,!0),u(v,null),u(V,w,!0),localStorage.setItem("dartlab-provider",w),localStorage.removeItem("dartlab-model"),u(N,M(w),!0),u(k,null),await j(w);const fe=r(T)[w]||[];if(u(m,fe,!0),fe.length>0&&(u(v,((Ge=r(l)[w])==null?void 0:Ge.model)||fe[0],!0),localStorage.setItem("dartlab-model",r(v)),r(N)))try{await ue(w,r(v),r(N))}catch{}}async function ve(w){u(v,w,!0),localStorage.setItem("dartlab-model",w);const fe=M(r(d));if(fe)try{await ue(pt(r(d)),w,fe)}catch{}}function ze(w){w=pt(w),r(V)===w?u(V,null):(u(V,w,!0),j(w))}async function we(){const w=r(N).trim();if(!(!w||!r(d))){u(H,!0),u(k,null);try{const fe=await ue(pt(r(d)),r(v),w);fe.available?(ce(r(d),w),u(k,"success"),!r(v)&&fe.model&&u(v,fe.model,!0),await j(r(d)),u(m,r(T)[r(d)]||[],!0),Le("API 키 인증 성공","success")):(ce(r(d),""),u(k,"error"))}catch{ce(r(d),""),u(k,"error")}u(H,!1)}}async function h(){try{await dv(),r(d)==="codex"&&u(l,{...r(l),codex:{...r(l).codex,available:!1}},!0),Le("Codex 계정 로그아웃 완료","success"),await A()}catch{Le("로그아웃 실패")}}function L(){const w=r(G).trim();!w||r(he)||(u(he,!0),u(B,"준비 중..."),u(_,0),u(z,lv(w,{onProgress(fe){fe.total&&fe.completed!==void 0?(u(_,Math.round(fe.completed/fe.total*100),!0),u(B,`다운로드 중... ${r(_)}%`)):fe.status&&u(B,fe.status,!0)},async onDone(){u(he,!1),u(z,null),u(G,""),u(B,""),u(_,0),Le(`${w} 다운로드 완료`,"success"),await j("ollama"),u(m,r(T).ollama||[],!0),r(m).includes(w)&&await ve(w)},onError(fe){u(he,!1),u(z,null),u(B,""),u(_,0),Le(`다운로드 실패: ${fe}`)}}),!0))}function K(){r(z)&&(r(z).abort(),u(z,null)),u(he,!1),u(G,""),u(B,""),u(_,0)}function se(){u(x,!r(x))}function ne(w){P.openData(w)}function Fe(w,fe=null){P.openEvidence(w,fe)}function Be(w){P.openViewer(w)}function Rt(){if(u(N,""),u(k,null),r(d))u(V,r(d),!0);else{const w=Object.keys(r(l));u(V,w.length>0?w[0]:null,!0)}u(C,!0),r(V)&&j(r(V))}function mt(w){var fe,Ge,it,at;if(w)for(let yt=w.messages.length-1;yt>=0;yt--){const Ae=w.messages[yt];if(Ae.role==="assistant"&&((fe=Ae.meta)!=null&&fe.stockCode||(Ge=Ae.meta)!=null&&Ge.company||Ae.company)){P.syncCompanyFromMessage({company:((it=Ae.meta)==null?void 0:it.company)||Ae.company,stockCode:(at=Ae.meta)==null?void 0:at.stockCode},P.selectedCompany);return}}}function lt(){Z.createConversation(),u(a,""),u(n,!1),r(o)&&(r(o).abort(),u(o,null))}function gt(w){Z.setActive(w),mt(Z.active),u(a,""),u(n,!1),r(o)&&(r(o).abort(),u(o,null))}function er(w){u(ee,w,!0)}function Se(){r(ee)&&(Z.deleteConversation(r(ee)),u(ee,null))}function pe(){var fe;const w=Z.active;if(!w)return null;for(let Ge=w.messages.length-1;Ge>=0;Ge--){const it=w.messages[Ge];if(it.role==="assistant"&&((fe=it.meta)!=null&&fe.stockCode))return it.meta.stockCode}return null}async function We(w=null){var dr,hr,vr;const fe=(w??r(a)).trim();if(!fe||r(n))return;if(!r(d)||!((dr=r(l)[r(d)])!=null&&dr.available)){Le("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),Rt();return}Z.activeId||Z.createConversation();const Ge=Z.activeId;Z.addMessage("user",fe),u(a,""),u(n,!0),Z.addMessage("assistant",""),Z.updateLastMessage({loading:!0,startedAt:Date.now()}),So(g);const it=Z.active,at=[];let yt=null;if(it){const ie=it.messages.slice(0,-2);for(const be of ie)if((be.role==="user"||be.role==="assistant")&&be.text&&be.text.trim()&&!be.error&&!be.loading){const ut={role:be.role,text:be.text};be.role==="assistant"&&((hr=be.meta)!=null&&hr.stockCode)&&(ut.meta={company:be.meta.company||be.company,stockCode:be.meta.stockCode,modules:be.meta.includedModules||null,market:be.meta.market||null,topic:be.meta.topic||null,topicLabel:be.meta.topicLabel||null,dialogueMode:be.meta.dialogueMode||null,questionTypes:be.meta.questionTypes||null,userGoal:be.meta.userGoal||null},yt=be.meta.stockCode),at.push(ut)}}const Ae=((vr=P.selectedCompany)==null?void 0:vr.stockCode)||yt||pe(),Ce=P.getViewContext();function Ue(){return Z.activeId!==Ge}const Et={provider:r(d),model:r(v),viewContext:Ce},sr=M(r(d));sr&&(Et.api_key=sr);const ur=_v(Ae,fe,Et,{onMeta(ie){var Xt;if(Ue())return;const be=Z.active,ut=be==null?void 0:be.messages[be.messages.length-1],ht={meta:{...(ut==null?void 0:ut.meta)||{},...ie}};ie.company&&(ht.company=ie.company,Z.activeId&&((Xt=Z.active)==null?void 0:Xt.title)==="새 대화"&&Z.updateTitle(Z.activeId,ie.company)),ie.stockCode&&(ht.stockCode=ie.stockCode),(ie.company||ie.stockCode)&&P.syncCompanyFromMessage(ie,P.selectedCompany),Z.updateLastMessage(ht)},onSnapshot(ie){Ue()||Z.updateLastMessage({snapshot:ie})},onContext(ie){if(Ue())return;const be=Z.active;if(!be)return;const ut=be.messages[be.messages.length-1],Je=(ut==null?void 0:ut.contexts)||[];Z.updateLastMessage({contexts:[...Je,{module:ie.module,label:ie.label,text:ie.text}]})},onSystemPrompt(ie){Ue()||Z.updateLastMessage({systemPrompt:ie.text,userContent:ie.userContent||null})},onToolCall(ie){if(Ue())return;const be=Z.active;if(!be)return;const ut=be.messages[be.messages.length-1],Je=(ut==null?void 0:ut.toolEvents)||[];Z.updateLastMessage({toolEvents:[...Je,{type:"call",name:ie.name,arguments:ie.arguments}]})},onToolResult(ie){if(Ue())return;const be=Z.active;if(!be)return;const ut=be.messages[be.messages.length-1],Je=(ut==null?void 0:ut.toolEvents)||[];Z.updateLastMessage({toolEvents:[...Je,{type:"result",name:ie.name,result:ie.result}]})},onChunk(ie){if(Ue())return;const be=Z.active;if(!be)return;const ut=be.messages[be.messages.length-1];Z.updateLastMessage({text:((ut==null?void 0:ut.text)||"")+ie}),So(g)},onDone(){if(Ue())return;const ie=Z.active,be=ie==null?void 0:ie.messages[ie.messages.length-1],ut=be!=null&&be.startedAt?((Date.now()-be.startedAt)/1e3).toFixed(1):null;Z.updateLastMessage({loading:!1,duration:ut}),Z.flush(),u(n,!1),u(o,null),So(g)},onViewerNavigate(ie){Ue()||_e(ie)},onError(ie,be,ut){Ue()||(Z.updateLastMessage({text:`오류: ${ie}`,loading:!1,error:!0}),Z.flush(),be==="login"?(Le(`${ie} — 설정에서 Codex 로그인을 확인하세요`),Rt()):be==="install"?(Le(`${ie} — 설정에서 Codex 설치 안내를 확인하세요`),Rt()):Le(ie),u(n,!1),u(o,null))}},at);u(o,ur,!0)}function Ee(){r(o)&&(r(o).abort(),u(o,null),u(n,!1),Z.updateLastMessage({loading:!1}),Z.flush())}function Ne(){const w=Z.active;if(!w||w.messages.length<2)return;let fe="";for(let Ge=w.messages.length-1;Ge>=0;Ge--)if(w.messages[Ge].role==="user"){fe=w.messages[Ge].text;break}fe&&(Z.removeLastMessage(),Z.removeLastMessage(),u(a,fe,!0),requestAnimationFrame(()=>{We()}))}function Ve(){const w=Z.active;if(!w)return;let fe=`# ${w.title}

`;for(const yt of w.messages)yt.role==="user"?fe+=`## You

${yt.text}

`:yt.role==="assistant"&&yt.text&&(fe+=`## DartLab

${yt.text}

`);const Ge=new Blob([fe],{type:"text/markdown;charset=utf-8"}),it=URL.createObjectURL(Ge),at=document.createElement("a");at.href=it,at.download=`${w.title||"dartlab-chat"}.md`,at.click(),URL.revokeObjectURL(it),Le("대화가 마크다운으로 내보내졌습니다","success")}function vt(w){var it;P.switchView("chat");const fe=((it=ye.topicData)==null?void 0:it.topicLabel)||"",Ge=fe?`[${fe}] `:"";u(a,`${Ge}"${w}" — 이 내용에 대해 설명해줘`),requestAnimationFrame(()=>{const at=document.querySelector(".input-textarea");at&&at.focus()})}function _e(w){w!=null&&w.topic&&(P.switchView("viewer"),w.chapter&&ye.selectTopic(w.topic,w.chapter))}function Qe(){u(F,!0),u(me,""),u(xe,[],!0),u(le,-1)}function kt(w){var it,at;(w.metaKey||w.ctrlKey)&&w.key==="n"&&(w.preventDefault(),lt()),(w.metaKey||w.ctrlKey)&&w.key==="k"&&(w.preventDefault(),Qe()),(w.metaKey||w.ctrlKey)&&w.shiftKey&&w.key==="S"&&(w.preventDefault(),se()),w.key==="Escape"&&r(F)?u(F,!1):w.key==="Escape"&&r(C)?u(C,!1):w.key==="Escape"&&r(ee)?u(ee,null):w.key==="Escape"&&P.panelOpen&&P.closePanel();const fe=(it=w.target)==null?void 0:it.tagName;if(!(fe==="INPUT"||fe==="TEXTAREA"||((at=w.target)==null?void 0:at.isContentEditable))&&!w.ctrlKey&&!w.metaKey&&!w.altKey){if(w.key==="1"){P.switchView("chat");return}if(w.key==="2"){P.switchView("viewer");return}}}let ft=D(()=>{var w;return((w=Z.active)==null?void 0:w.messages)||[]}),St=D(()=>Z.active&&Z.active.messages.length>0),rt=D(()=>{var w;return!r(y)&&(!r(d)||!((w=r(l)[r(d)])!=null&&w.available))});const Mt=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var Pt=fb();fn("keydown",Qo,kt);var Kt=re(Pt),st=i(Kt);{var $e=w=>{var fe=wg();oe("click",fe,()=>{u(x,!1)}),c(w,fe)};b(st,w=>{r(de)&&r(x)&&w($e)})}var ct=p(st,2),Jt=i(ct);{let w=D(()=>r(de)?!0:r(x));op(Jt,{get conversations(){return Z.conversations},get activeId(){return Z.activeId},get open(){return r(w)},get version(){return r(E)},onNewChat:()=>{lt(),r(de)&&u(x,!1)},onSelect:fe=>{gt(fe),r(de)&&u(x,!1)},onDelete:er,onOpenSearch:Qe})}var pr=p(ct,2),zt=i(pr),Ke=i(zt),Gt=i(Ke);{var Er=w=>{Vf(w,{size:18})},Wr=w=>{jf(w,{size:18})};b(Gt,w=>{r(x)?w(Er):w(Wr,-1)})}var yr=p(Ke,2),Wt=i(yr),ar=i(Wt);ns(ar,{size:12});var ta=p(Wt,2),nr=i(ta);Ks(nr,{size:12});var Ft=p(zt,2),or=i(Ft),tr=i(or);mn(tr,{size:14});var lr=p(or,2),cr=i(lr);da(cr,{size:14});var mr=p(lr,2),Sr=i(mr);Of(Sr,{size:14});var At=p(mr,2),Ze=i(At);Nf(Ze,{size:14});var _t=p(At,2),Oe=i(_t);{var Re=w=>{var fe=kg(),Ge=re(fe);zr(Ge,{size:12,class:"animate-spin"}),c(w,fe)},Lt=w=>{var fe=$g(),Ge=re(fe);Mn(Ge,{size:12}),c(w,fe)},He=w=>{var fe=Sg(),Ge=p(re(fe),2),it=i(Ge),at=p(Ge,2);{var yt=Ae=>{var Ce=Cg(),Ue=p(re(Ce),2),Et=i(Ue);S(()=>$(Et,r(v))),c(Ae,Ce)};b(at,Ae=>{r(v)&&Ae(yt)})}S(()=>$(it,r(d))),c(w,fe)};b(Oe,w=>{r(y)?w(Re):r(rt)?w(Lt,1):w(He,-1)})}var Ye=p(Oe,2);Bf(Ye,{size:12});var xt=p(Ft,2),jt=i(xt);{var Dt=w=>{var fe=Tg(),Ge=i(fe);yg(Ge,{get viewer(){return ye},get company(){return P.selectedCompany},onAskAI:vt,onTopicChange:(it,at)=>P.setViewerTopic(it,at)}),c(w,fe)},$t=w=>{var fe=zg(),Ge=re(fe),it=i(Ge);{var at=Ue=>{vm(Ue,{get messages(){return r(ft)},get isLoading(){return r(n)},get scrollTrigger(){return r(g)},get selectedCompany(){return P.selectedCompany},onSend:We,onStop:Ee,onRegenerate:Ne,onExport:Ve,onOpenData:ne,onOpenEvidence:Fe,onCompanySelect:Be,get inputText(){return r(a)},set inputText(Et){u(a,Et,!0)}})},yt=Ue=>{pp(Ue,{onSend:We,onCompanySelect:Be,get inputText(){return r(a)},set inputText(Et){u(a,Et,!0)}})};b(it,Ue=>{r(St)?Ue(at):Ue(yt,-1)})}var Ae=p(Ge,2);{var Ce=Ue=>{var Et=Mg(),sr=i(Et);Vx(sr,{get mode(){return P.panelMode},get company(){return P.selectedCompany},get data(){return P.panelData},onClose:()=>{u(O,!1),P.closePanel()},onTopicChange:(ur,dr)=>P.setViewerTopic(ur,dr),onFullscreen:()=>{u(O,!r(O))},get isFullscreen(){return r(O)}}),S(()=>Zo(Et,`width: ${r(U)??""}; min-width: 360px; ${r(O)?"":"max-width: 75vw;"}`)),c(Ue,Et)};b(Ae,Ue=>{!r(de)&&P.panelOpen&&Ue(Ce)})}c(w,fe)};b(jt,w=>{P.activeView==="viewer"?w(Dt):w($t,-1)})}var Vt=p(Kt,2);{var bt=w=>{var fe=ab(),Ge=i(fe),it=i(Ge),at=i(it),yt=p(i(at),2),Ae=i(yt);gn(Ae,{size:18});var Ce=p(it,2),Ue=i(Ce);Te(Ue,21,()=>Object.entries(r(l)),Me,(ie,be)=>{var ut=D(()=>Zs(r(be),2));let Je=()=>r(ut)[0],ht=()=>r(ut)[1];const Xt=D(()=>Je()===r(d)),Bt=D(()=>r(V)===Je()),Yt=D(()=>ht().auth==="api_key"),Br=D(()=>ht().auth==="cli"),Ba=D(()=>r(T)[Je()]||[]),Ya=D(()=>r(I)[Je()]);var kn=rb(),$n=i(kn),Kn=i($n),Gn=p(Kn,2),Wn=i(Gn),jo=i(Wn),ps=i(jo),Pd=p(jo,2);{var Ld=fr=>{var Ur=Ag();c(fr,Ur)};b(Pd,fr=>{r(Xt)&&fr(Ld)})}var Od=p(Wn,2),Rd=i(Od),Dd=p(Gn,2),jd=i(Dd);{var Vd=fr=>{zo(fr,{size:16,class:"text-dl-success"})},qd=fr=>{var Ur=Eg(),Ja=re(Ur);Zi(Ja,{size:14,class:"text-amber-400"}),c(fr,Ur)},Bd=fr=>{var Ur=Ig(),Ja=re(Ur);Mn(Ja,{size:14,class:"text-amber-400"}),c(fr,Ur)},Fd=fr=>{var Ur=Ng(),Ja=re(Ur);Kf(Ja,{size:14,class:"text-dl-text-dim"}),c(fr,Ur)};b(jd,fr=>{ht().available?fr(Vd):r(Yt)?fr(qd,1):r(Br)&&Je()==="codex"&&r(tt).installed?fr(Bd,2):r(Br)&&!ht().available&&fr(Fd,3)})}var Hd=p($n,2);{var Ud=fr=>{var Ur=tb(),Ja=re(Ur);{var Kd=Zt=>{var gr=Lg(),Nr=i(gr),Kr=i(Nr),ca=p(Nr,2),Fr=i(ca),ra=p(Fr,2),Xa=i(ra);{var Qa=Ht=>{zr(Ht,{size:12,class:"animate-spin"})},aa=Ht=>{Zi(Ht,{size:12})};b(Xa,Ht=>{r(H)?Ht(Qa):Ht(aa,-1)})}var ha=p(ca,2);{var ir=Ht=>{var na=Pg(),Pr=i(na);Mn(Pr,{size:12}),c(Ht,na)};b(ha,Ht=>{r(k)==="error"&&Ht(ir)})}S(Ht=>{$(Kr,ht().envKey?`환경변수 ${ht().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),Ca(Fr,"placeholder",Je()==="openai"?"sk-...":Je()==="claude"?"sk-ant-...":"API Key"),ra.disabled=Ht},[()=>!r(N).trim()||r(H)]),oe("keydown",Fr,Ht=>{Ht.key==="Enter"&&we()}),Nn(Fr,()=>r(N),Ht=>u(N,Ht)),oe("click",ra,we),c(Zt,gr)};b(Ja,Zt=>{r(Yt)&&!ht().available&&Zt(Kd)})}var pi=p(Ja,2);{var Gd=Zt=>{var gr=Rg(),Nr=i(gr),Kr=i(Nr);zo(Kr,{size:13,class:"text-dl-success"});var ca=p(Nr,2),Fr=i(ca),ra=p(Fr,2);{var Xa=aa=>{var ha=Og(),ir=i(ha);{var Ht=Pr=>{zr(Pr,{size:10,class:"animate-spin"})},na=Pr=>{var Aa=an("변경");c(Pr,Aa)};b(ir,Pr=>{r(H)?Pr(Ht):Pr(na,-1)})}S(()=>ha.disabled=r(H)),oe("click",ha,we),c(aa,ha)},Qa=D(()=>r(N).trim());b(ra,aa=>{r(Qa)&&aa(Xa)})}oe("keydown",Fr,aa=>{aa.key==="Enter"&&we()}),Nn(Fr,()=>r(N),aa=>u(N,aa)),c(Zt,gr)};b(pi,Zt=>{r(Yt)&&ht().available&&Zt(Gd)})}var mi=p(pi,2);{var Wd=Zt=>{var gr=Dg(),Nr=p(i(gr),2),Kr=i(Nr);Ao(Kr,{size:14});var ca=p(Kr,2);Qi(ca,{size:10,class:"ml-auto"}),c(Zt,gr)},Yd=Zt=>{var gr=jg(),Nr=i(gr),Kr=i(Nr);Mn(Kr,{size:14}),c(Zt,gr)};b(mi,Zt=>{Je()==="ollama"&&!r(s).installed?Zt(Wd):Je()==="ollama"&&r(s).installed&&!r(s).running&&Zt(Yd,1)})}var xi=p(mi,2);{var Jd=Zt=>{var gr=Fg(),Nr=i(gr);{var Kr=ra=>{var Xa=Bg(),Qa=re(Xa),aa=i(Qa),ha=p(Qa,2),ir=i(ha);{var Ht=oa=>{var Ea=Vg();c(oa,Ea)};b(ir,oa=>{r(tt).installed||oa(Ht)})}var na=p(ir,2),Pr=i(na),Aa=i(Pr),Cn=p(ha,2);{var po=oa=>{var Ea=qg(),Za=i(Ea);S(()=>$(Za,r(tt).loginStatus)),c(oa,Ea)};b(Cn,oa=>{r(tt).loginStatus&&oa(po)})}var mo=p(Cn,2),Yr=i(mo);Mn(Yr,{size:12,class:"text-amber-400 flex-shrink-0"}),S(()=>{$(aa,r(tt).installed?"Codex CLI가 설치되었지만 로그인이 필요합니다":"Codex CLI 설치가 필요합니다"),$(Aa,r(tt).installed?"1.":"2.")}),c(ra,Xa)};b(Nr,ra=>{Je()==="codex"&&ra(Kr)})}var ca=p(Nr,2),Fr=i(ca);S(()=>$(Fr,r(tt).installed?"로그인 완료 후 새로고침하세요":"설치 완료 후 새로고침하세요")),c(Zt,gr)};b(xi,Zt=>{r(Br)&&!ht().available&&Zt(Jd)})}var hi=p(xi,2);{var Xd=Zt=>{var gr=Hg(),Nr=i(gr),Kr=i(Nr),ca=i(Kr);zo(ca,{size:13,class:"text-dl-success"});var Fr=p(Kr,2),ra=i(Fr);Df(ra,{size:11}),oe("click",Fr,h),c(Zt,gr)};b(hi,Zt=>{Je()==="codex"&&ht().available&&Zt(Xd)})}var Qd=p(hi,2);{var Zd=Zt=>{var gr=eb(),Nr=i(gr),Kr=p(i(Nr),2);{var ca=ir=>{zr(ir,{size:12,class:"animate-spin text-dl-text-dim"})};b(Kr,ir=>{r(Ya)&&ir(ca)})}var Fr=p(Nr,2);{var ra=ir=>{var Ht=Ug(),na=i(Ht);zr(na,{size:14,class:"animate-spin"}),c(ir,Ht)},Xa=ir=>{var Ht=Gg();Te(Ht,21,()=>r(Ba),Me,(na,Pr)=>{var Aa=Kg(),Cn=i(Aa),po=p(Cn);{var mo=Yr=>{Gs(Yr,{size:10,class:"inline ml-1"})};b(po,Yr=>{r(Pr)===r(v)&&r(Xt)&&Yr(mo)})}S(Yr=>{qe(Aa,1,Yr),$(Cn,`${r(Pr)??""} `)},[()=>Qt(rr("px-3 py-1.5 rounded-lg text-[11px] border transition-all",r(Pr)===r(v)&&r(Xt)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),oe("click",Aa,()=>{Je()!==r(d)&&ae(Je()),ve(r(Pr))}),c(na,Aa)}),c(ir,Ht)},Qa=ir=>{var Ht=Wg();c(ir,Ht)};b(Fr,ir=>{r(Ya)&&r(Ba).length===0?ir(ra):r(Ba).length>0?ir(Xa,1):ir(Qa,-1)})}var aa=p(Fr,2);{var ha=ir=>{var Ht=Zg(),na=i(Ht),Pr=p(i(na),2),Aa=p(i(Pr));Qi(Aa,{size:9});var Cn=p(na,2);{var po=Yr=>{var oa=Yg(),Ea=i(oa),Za=i(Ea),xo=i(Za);zr(xo,{size:12,class:"animate-spin text-dl-primary-light"});var ms=p(Za,2),Vo=p(Ea,2),Fa=i(Vo),ga=p(Vo,2),xs=i(ga);S(()=>{Zo(Fa,`width: ${r(_)??""}%`),$(xs,r(B))}),oe("click",ms,K),c(Yr,oa)},mo=Yr=>{var oa=Qg(),Ea=re(oa),Za=i(Ea),xo=p(Za,2),ms=i(xo);Ao(ms,{size:12});var Vo=p(Ea,2);Te(Vo,21,()=>Mt,Me,(Fa,ga)=>{const xs=D(()=>r(Ba).some(Yn=>Yn===r(ga).name||Yn===r(ga).name.split(":")[0]));var gi=ke(),ec=re(gi);{var tc=Yn=>{var hs=Xg(),bi=i(hs),_i=i(bi),yi=i(_i),rc=i(yi),wi=p(yi,2),ac=i(wi),nc=p(wi,2);{var oc=gs=>{var $i=Jg(),uc=i($i);S(()=>$(uc,r(ga).tag)),c(gs,$i)};b(nc,gs=>{r(ga).tag&&gs(oc)})}var sc=p(_i,2),ic=i(sc),lc=p(bi,2),ki=i(lc),dc=i(ki),cc=p(ki,2);Ao(cc,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),S(()=>{$(rc,r(ga).name),$(ac,r(ga).size),$(ic,r(ga).desc),$(dc,`${r(ga).gb??""} GB`)}),oe("click",hs,()=>{u(G,r(ga).name,!0),L()}),c(Yn,hs)};b(ec,Yn=>{r(xs)||Yn(tc)})}c(Fa,gi)}),S(Fa=>xo.disabled=Fa,[()=>!r(G).trim()]),oe("keydown",Za,Fa=>{Fa.key==="Enter"&&L()}),Nn(Za,()=>r(G),Fa=>u(G,Fa)),oe("click",xo,L),c(Yr,oa)};b(Cn,Yr=>{r(he)?Yr(po):Yr(mo,-1)})}c(ir,Ht)};b(aa,ir=>{Je()==="ollama"&&ir(ha)})}c(Zt,gr)};b(Qd,Zt=>{(ht().available||r(Yt)||r(Br))&&Zt(Zd)})}c(fr,Ur)};b(Hd,fr=>{(r(Bt)||r(Xt))&&fr(Ud)})}S((fr,Ur)=>{qe(kn,1,fr),qe(Kn,1,Ur),$(ps,ht().label||Je()),$(Rd,ht().desc||"")},[()=>Qt(rr("rounded-xl border transition-all",r(Xt)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>Qt(rr("w-2.5 h-2.5 rounded-full flex-shrink-0",ht().available?"bg-dl-success":r(Yt)?"bg-amber-400":"bg-dl-text-dim"))]),oe("click",$n,()=>{ht().available||r(Yt)?Je()===r(d)?ze(Je()):ae(Je()):ze(Je())}),c(ie,kn)});var Et=p(Ce,2),sr=i(Et),ur=i(sr);{var dr=ie=>{var be=an();S(()=>{var ut;return $(be,`현재: ${(((ut=r(l)[r(d)])==null?void 0:ut.label)||r(d))??""} / ${r(v)??""}`)}),c(ie,be)},hr=ie=>{var be=an();S(()=>{var ut;return $(be,`현재: ${(((ut=r(l)[r(d)])==null?void 0:ut.label)||r(d))??""}`)}),c(ie,be)};b(ur,ie=>{r(d)&&r(v)?ie(dr):r(d)&&ie(hr,1)})}var vr=p(sr,2);pn(Ge,ie=>u(Y,ie),()=>r(Y)),oe("click",fe,ie=>{ie.target===ie.currentTarget&&u(C,!1)}),oe("click",yt,()=>u(C,!1)),oe("click",vr,()=>u(C,!1)),c(w,fe)};b(Vt,w=>{r(C)&&w(bt)})}var qt=p(Vt,2);{var Ir=w=>{var fe=nb(),Ge=i(fe),it=p(i(Ge),4),at=i(it),yt=p(at,2);pn(Ge,Ae=>u(J,Ae),()=>r(J)),oe("click",fe,Ae=>{Ae.target===Ae.currentTarget&&u(ee,null)}),oe("click",at,()=>u(ee,null)),oe("click",yt,Se),c(w,fe)};b(qt,w=>{r(ee)&&w(Ir)})}var za=p(qt,2);{var Tr=w=>{const fe=D(()=>P.recentCompanies||[]);var Ge=ub(),it=i(Ge),at=i(it),yt=i(at);mn(yt,{size:18,class:"text-dl-text-dim flex-shrink-0"});var Ae=p(yt,2);pn(Ae,ie=>u(Ie,ie),()=>r(Ie));var Ce=p(at,2),Ue=i(Ce);{var Et=ie=>{var be=sb(),ut=p(re(be),2);Te(ut,17,()=>r(xe),Me,(Je,ht,Xt)=>{var Bt=ob(),Yt=i(Bt),Br=i(Yt),Ba=p(Yt,2),Ya=i(Ba),kn=i(Ya),$n=p(Ya,2),Kn=i($n),Gn=p(Ba,2),Wn=p(i(Gn),2);da(Wn,{size:14,class:"text-dl-text-dim"}),S((jo,ps)=>{qe(Bt,1,jo),$(Br,ps),$(kn,r(ht).corpName),$(Kn,`${r(ht).stockCode??""} · ${(r(ht).market||"")??""}${r(ht).sector?` · ${r(ht).sector}`:""}`)},[()=>Qt(rr("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",Xt===r(le)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(r(ht).corpName||"?").charAt(0)]),oe("click",Bt,()=>{u(F,!1),u(me,""),u(xe,[],!0),u(le,-1),Be(r(ht))}),fn("mouseenter",Bt,()=>{u(le,Xt,!0)}),c(Je,Bt)}),c(ie,be)},sr=ie=>{var be=lb(),ut=p(re(be),2);Te(ut,17,()=>r(fe),Me,(Je,ht,Xt)=>{var Bt=ib(),Yt=i(Bt),Br=i(Yt),Ba=p(Yt,2),Ya=i(Ba),kn=i(Ya),$n=p(Ya,2),Kn=i($n);S((Gn,Wn)=>{qe(Bt,1,Gn),$(Br,Wn),$(kn,r(ht).corpName),$(Kn,`${r(ht).stockCode??""} · ${(r(ht).market||"")??""}`)},[()=>Qt(rr("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",Xt===r(le)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(r(ht).corpName||"?").charAt(0)]),oe("click",Bt,()=>{u(F,!1),u(me,""),u(le,-1),Be(r(ht))}),fn("mouseenter",Bt,()=>{u(le,Xt,!0)}),c(Je,Bt)}),c(ie,be)},ur=D(()=>r(me).trim().length===0&&r(fe).length>0),dr=ie=>{var be=db();c(ie,be)},hr=D(()=>r(me).trim().length>0),vr=ie=>{var be=cb(),ut=i(be);mn(ut,{size:24,class:"mb-2 opacity-40"}),c(ie,be)};b(Ue,ie=>{r(xe).length>0?ie(Et):r(ur)?ie(sr,1):r(hr)?ie(dr,2):ie(vr,-1)})}oe("click",Ge,ie=>{ie.target===ie.currentTarget&&u(F,!1)}),oe("input",Ae,()=>{te&&clearTimeout(te),r(me).trim().length>=1?te=setTimeout(async()=>{var ie;try{const be=await id(r(me).trim());u(xe,((ie=be.results)==null?void 0:ie.slice(0,8))||[],!0)}catch{u(xe,[],!0)}},250):u(xe,[],!0)}),oe("keydown",Ae,ie=>{const be=r(xe).length>0?r(xe):r(fe);if(ie.key==="ArrowDown")ie.preventDefault(),u(le,Math.min(r(le)+1,be.length-1),!0);else if(ie.key==="ArrowUp")ie.preventDefault(),u(le,Math.max(r(le)-1,-1),!0);else if(ie.key==="Enter"&&r(le)>=0&&be[r(le)]){ie.preventDefault();const ut=be[r(le)];u(F,!1),u(me,""),u(xe,[],!0),u(le,-1),Be(ut)}else ie.key==="Escape"&&u(F,!1)}),Nn(Ae,()=>r(me),ie=>u(me,ie)),c(w,Ge)};b(za,w=>{r(F)&&w(Tr)})}var Hr=p(za,2);{var wn=w=>{var fe=vb(),Ge=i(fe),it=i(Ge),at=i(it),yt=p(it,2),Ae=i(yt);gn(Ae,{size:14}),S(Ce=>{qe(Ge,1,Ce),$(at,r(Q))},[()=>Qt(rr("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",r(q)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":r(q)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),oe("click",yt,()=>{u(ge,!1)}),c(w,fe)};b(Hr,w=>{r(ge)&&w(wn)})}S(w=>{qe(ct,1,Qt(r(de)?r(x)?"sidebar-mobile":"hidden":"")),qe(Wt,1,`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors ${P.activeView==="chat"?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-dim hover:text-dl-text-muted"}`),qe(ta,1,`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors ${P.activeView==="viewer"?"text-dl-text bg-dl-surface-active font-medium":"text-dl-text-dim hover:text-dl-text-muted"}`),qe(_t,1,w)},[()=>Qt(rr("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",r(y)?"text-dl-text-dim":r(rt)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),oe("click",Ke,se),oe("click",Wt,()=>P.switchView("chat")),oe("click",ta,()=>P.switchView("viewer")),oe("click",or,Qe),oe("click",_t,()=>Rt()),c(e,Pt),_r()}Vr(["click","keydown","input"]);Du(pb,{target:document.getElementById("app")});
